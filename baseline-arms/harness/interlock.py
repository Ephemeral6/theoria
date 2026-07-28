"""Refuse to start an envelope cell while another campaign is spending.

`INCIDENTS.md` INC-BA-003: while the P-7 variance envelope was running, a second
session started the approved S1 full run in the same track. Two campaigns, one
ARC quota, one Anthropic bill, and two gates that could not see each other. The
envelope's first game degraded by every measure -- action success 0.713 -> 0.595,
HTTP per action 7.11 -> 9.66, dollars per action +68% (`BUDGET_REPORT.md` 11.2)
-- and `BUDGET_REPORT.md` 11.5 made serialising the two campaigns a precondition
for re-running: under contention what a variance envelope measures is the
contention, not the arm.

That precondition was a sentence in a report, which is to say it was whatever
the next session happened to remember. This module makes it a check.

Two independent signals, because either one alone has a blind spot:

  * **The process table.** Exact while a campaign is running, and it sees
    processes started from a different worktree of the same repository -- which
    is precisely how INC-BA-003 happened. Blind if the other campaign runs
    somewhere this process cannot enumerate.
  * **Checkpoint freshness.** `harness/campaign.py` writes `campaign_<game>.json`
    after every episode and every fifth step, so a live campaign leaves a trail
    with a timestamp on it. This survives the process scan being unavailable,
    and it self-heals: a campaign whose process was killed goes stale and stops
    blocking after `STALE_AFTER_SECONDS` rather than wedging the track forever.

**Fail closed.** If neither signal can be obtained, `check()` blocks. Not being
able to tell whether another campaign is running is not the same as knowing that
none is, and the cheap error here (waiting) costs an hour while the expensive one
costs a campaign's worth of contaminated measurements.

There is no override flag, for the reason `DECISIONS.md` D-008 gives about the
pilot's scope: a flag is a thing a session under pressure sets, and this exists
to constrain exactly that session. Overriding it is a code change with a diff.
"""

import calendar
import json
import os
import re
import subprocess
import sys
import time
from typing import Any, Callable, Dict, List, Optional, Tuple

TRACK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(TRACK)

# A campaign checkpoint older than this is treated as abandoned, so a campaign
# whose process was killed stops blocking instead of wedging the track forever.
#
# The window is not as generous as it looks. `campaign.py`'s in-episode callback
# runs from `bare_cc`'s `on_step`, which sits *after* the `continue` that handles
# a refused action -- so the checkpoint advances on successful actions only, and
# under the API degradation this interlock exists to protect against it can go
# quiet for a long time while the episode is very much alive. That is tolerable
# because the checkpoint scan is the *secondary* signal: the process table sees a
# live campaign regardless of whether it is making progress, and a process-table
# failure blocks outright rather than falling through to this one.
STALE_AFTER_SECONDS = 30 * 60

# Module invocations that spend money in this track.
CAMPAIGN_MODULES = ("harness.campaign", "harness.run_campaign",
                    "harness.run_pilot", "harness.bare_cc")

# ...except with this flag, which makes the invocation read-only. `--gate-only`
# re-adjudicates the recorded cells and buys nothing. Treating it as live spend
# is not a harmless over-count: the obvious way to ask "is it safe to start?" is
# to evaluate the gate, and an interlock that blocks on its own diagnostic is one
# nobody can clear. Observed for real -- three concurrent `--gate-only` readers
# showed up as three live campaigns.
#
# One flag, matched as a whole argument, and only against the modules that can
# spend. An earlier version listed four and tested them as substrings of the
# whole command line: three named no option any spending module has, and a
# substring test would have been silenced by a path or a prompt that happened to
# contain the text. A too-eager exclusion here is the failure that costs money.
READ_ONLY_FLAGS = ("--gate-only",)

# This track's read-only tools take `--game` too, so they would otherwise look
# like foreign ARC players by the rule below.
OUR_READ_ONLY_MODULES = ("harness.audit_cells", "harness.campaign_status",
                         "harness.summarise_campaign", "harness.summarise_pilot",
                         "harness.merge_ledger", "harness.interlock",
                         "harness.archive_runs", "harness.migrate_ledger",
                         "harness.validate_canon", "harness.probe_api",
                         "harness.fetch_schema_traces")

_TS = "%Y-%m-%dT%H:%M:%SZ"


def _parse_ts(value: Any) -> Optional[float]:
    if not isinstance(value, str):
        return None
    try:
        return calendar.timegm(time.strptime(value, _TS))
    except ValueError:
        return None


# ------------------------------------------------------------ process table
def list_processes() -> Tuple[List[Tuple[int, int, str]], Optional[str]]:
    """`([(pid, ppid, command_line)], error)`. `error` non-None means unavailable.

    The parent id is not decoration. A campaign started from a shell leaves the
    shell holding a command line that contains the module name, so without the
    ancestry the check counts its own launcher as a rival campaign -- which it
    did, on the first real run, blocking the very command it was protecting.
    """
    if os.name == "nt":
        cmd = ["powershell", "-NoProfile", "-NonInteractive", "-Command",
               "[Console]::OutputEncoding = [Text.Encoding]::UTF8; "
               "Get-CimInstance Win32_Process | "
               "Select-Object ProcessId,ParentProcessId,CommandLine | "
               "ConvertTo-Json -Compress"]
    else:
        cmd = ["ps", "-eo", "pid=,ppid=,args="]
    try:
        # Bytes, not text=True. Some process on this machine has a command line
        # that is not valid UTF-8, and with text=True the decode blows up inside
        # subprocess's reader thread: the exception is printed to stderr, stdout
        # comes back EMPTY, and returncode is 0. The scan then reported zero
        # processes with no error -- which reads as "no campaign is running".
        # A decode failure must never be able to clear this check.
        proc = subprocess.run(cmd, capture_output=True, timeout=60)
    except Exception as exc:                       # no shell, no ps, no policy
        return [], "%s: %s" % (type(exc).__name__, exc)
    if proc.returncode != 0:
        return [], "exit %d: %s" % (
            proc.returncode, (proc.stderr or b"").decode("utf-8", "replace")[:200])
    stdout = (proc.stdout or b"").decode("utf-8", "replace")

    out: List[Tuple[int, int, str]] = []
    if os.name == "nt":
        try:
            rows = json.loads(stdout or "[]")
        except json.JSONDecodeError as exc:
            return [], "unparseable process list: %s" % exc
        if isinstance(rows, dict):
            rows = [rows]                      # ConvertTo-Json unwraps a single row
        for row in rows:
            pid = row.get("ProcessId")
            if isinstance(pid, int):
                ppid = row.get("ParentProcessId")
                out.append((pid, ppid if isinstance(ppid, int) else 0,
                            row.get("CommandLine") or ""))
    else:
        for line in stdout.splitlines():
            m = re.match(r"\s*(\d+)\s+(\d+)\s+(.*)$", line)
            if m:
                out.append((int(m.group(1)), int(m.group(2)), m.group(3)))
    if not out:
        # A running machine always has processes. An empty list means the scan
        # failed in a way that did not raise -- an unparseable shape, a policy
        # that returned nothing, a decode that ate the output -- and treating it
        # as "nothing is running" is the one way this check can fail open.
        return [], "the process table came back empty, which cannot be true"
    return out, None


def ancestors(pid: int, parent_of: Dict[int, int], limit: int = 64) -> set:
    """`pid` and every process above it, so a launcher is never a rival.

    Bounded, because a corrupt or recycled parent map can contain a cycle and
    this runs before anything else the interlock does.
    """
    chain = {pid}
    seen = 0
    while pid in parent_of and seen < limit:
        pid = parent_of[pid]
        if pid in chain or pid <= 0:
            break
        chain.add(pid)
        seen += 1
    return chain


def foreign_players(rows: List[Tuple[int, int, str]], mine: set,
                    ours: set) -> List[Dict[str, Any]]:
    """Processes outside this track that are playing the same ARC games.

    INC-BA-003's hazard is a shared quota and a shared bill, not a module name.
    This repository now carries some twenty-five concurrent worktrees, and other
    tracks run their own arms against the same four development-pile games -- so
    a check that only knew `baseline-arms.harness.*` was blind to most of the
    contention that can spoil a variance measurement.

    The rule is deliberately module-agnostic: **anything invoking a Python
    module with a development-pile game id on its command line is playing the
    API we are playing.** That catches a track whose entry point this module has
    never heard of, which is the point.

    These are *reported, not blocked.* Serialising across tracks is not this
    track's to impose -- every track doing so would deadlock the repository, and
    the tickets are written to run concurrently. What is this track's job is to
    make sure a number measured under contention is never mistaken for one
    measured without it: BUDGET_REPORT.md 11.2 is what happens otherwise.
    """
    dev = tuple(_dev_ids())
    out = []
    for pid, _ppid, cmdline in rows:
        if pid in mine or pid in ours:
            continue
        if " -m " not in cmdline and "-m" not in cmdline.split():
            continue
        if any(re.search(r"-m\s*%s(\s|$)" % re.escape(m), cmdline)
               for m in OUR_READ_ONLY_MODULES):
            continue
        hit = [g for g in dev if g in cmdline]
        if hit:
            out.append({"pid": pid, "games": hit, "cmdline": cmdline[:300]})
    return out


def _dev_ids() -> List[str]:
    try:
        from . import arc_client
        return list(arc_client.dev_pile())
    except Exception:
        return []


def live_processes(lister: Callable[[], Tuple[List[Tuple[int, int, str]], Optional[str]]] = list_processes,
                   own_pid: Optional[int] = None) -> Tuple[List[Dict[str, Any]], Optional[str]]:
    own_pid = os.getpid() if own_pid is None else own_pid
    rows, error = lister()
    if error is not None:
        return [], error
    if not rows:
        # Checked here as well as in list_processes, because this is the layer
        # every caller goes through: an empty table is the one shape that reads
        # as "nothing is running" while actually meaning "the scan failed".
        return [], "the process table came back empty, which cannot be true"
    # Self and every ancestor. `python -m harness.run_campaign` started from a
    # shell leaves that shell -- and any wrapper above it -- holding a command
    # line containing the module name, so all of them match the module regex.
    # On the first real run this blocked the command it was meant to protect,
    # reporting three live campaigns when there was one and it was us.
    mine = ancestors(own_pid, {pid: ppid for pid, ppid, _ in rows})
    found = []
    for pid, _ppid, cmdline in rows:
        if pid in mine:
            continue
        for module in CAMPAIGN_MODULES:
            # `-m harness.campaign`, and not `harness.campaign_status`, which is
            # a read-only status printer and spends nothing. `-m` with or
            # without a space, since `python -mharness.campaign` is legal.
            if not re.search(r"-m\s*%s(\s|$)" % re.escape(module), cmdline):
                continue
            if _is_read_only(module, cmdline):
                break
            found.append({"pid": pid, "module": module,
                          "cmdline": cmdline[:300]})
            break
    return found, None


def _is_read_only(module: str, cmdline: str) -> bool:
    """Is this invocation of `module` one that cannot spend?

    Narrow on purpose. `--gate-only` belongs to `run_campaign` and nowhere else,
    and `run_campaign` refuses to run without `--game`, so an invocation with
    `--gate-only` and no `--game` provably buys nothing. Requiring both
    conditions matters because a process table gives one flat string, not an
    argv: a `--gate-only` token can appear inside somebody's quoted argument,
    and a bare token test would let that excuse a live campaign. The failure
    that costs money is the over-eager exclusion, so it gets the tight rule.
    """
    if module != "harness.run_campaign":
        return False
    args = cmdline.split()
    return any(f in args for f in READ_ONLY_FLAGS) and "--game" not in args


# -------------------------------------------------------------- checkpoints
def worktree_roots(repo: str = REPO) -> List[str]:
    """Every checkout of this repository, so a campaign started from a sibling
    worktree is visible. Falls back to this checkout alone."""
    roots = [repo]
    try:
        proc = subprocess.run(["git", "worktree", "list", "--porcelain"],
                              cwd=repo, capture_output=True, text=True, timeout=30)
    except Exception:
        return roots
    if proc.returncode != 0:
        return roots
    for line in (proc.stdout or "").splitlines():
        if line.startswith("worktree "):
            path = line[len("worktree "):].strip()
            if path and path not in roots:
                roots.append(path)
    return roots


def scan_checkpoints(roots: Optional[List[str]] = None,
                     now: Optional[float] = None,
                     stale_after: int = STALE_AFTER_SECONDS) -> List[Dict[str, Any]]:
    """Every `campaign_<game>.json` found, with a live/stale verdict."""
    now = time.time() if now is None else now
    roots = worktree_roots() if roots is None else roots
    seen: Dict[str, Dict[str, Any]] = {}
    for root in roots:
        directory = os.path.join(root, "baseline-arms", "out", "campaign")
        if not os.path.isdir(directory):
            continue
        for name in sorted(os.listdir(directory)):
            if not (name.startswith("campaign_") and name.endswith(".json")):
                continue
            path = os.path.join(directory, name)
            real = os.path.realpath(path)
            if real in seen:
                continue
            try:
                with open(path, encoding="utf-8") as fh:
                    state = json.load(fh)
            except Exception as exc:
                seen[real] = {"path": path, "unreadable": "%s: %s"
                              % (type(exc).__name__, exc), "live": False}
                continue
            stamps = [_parse_ts(state.get(k)) for k in
                      ("ended", "resumed_at", "started")]
            live_ep = state.get("live_episode") or {}
            stamps.append(_parse_ts(live_ep.get("at")))
            for ep in state.get("episodes") or []:
                stamps.append(_parse_ts(ep.get("ended")))
            newest = max([s for s in stamps if s is not None], default=None)
            age = None if newest is None else now - newest
            running = state.get("status") == "running"
            seen[real] = {
                "path": path,
                "game_id": state.get("game_id"),
                "status": state.get("status"),
                "cost_usd": state.get("cost_usd"),
                "http_calls": state.get("http_calls"),
                "actions_ok": state.get("actions_ok"),
                "live_episode": state.get("live_episode"),
                "age_seconds": None if age is None else round(age, 1),
                "live": bool(running and age is not None and age <= stale_after),
                "stale_running": bool(running and (age is None or age > stale_after)),
            }
    return [seen[k] for k in sorted(seen)]


# --------------------------------------------------------------- the check
def check(lister: Callable[[], Tuple[List[Tuple[int, str]], Optional[str]]] = list_processes,
          roots: Optional[List[str]] = None,
          now: Optional[float] = None,
          own_pid: Optional[int] = None,
          stale_after: int = STALE_AFTER_SECONDS) -> Dict[str, Any]:
    """`{"clear": bool, "blockers": [...], "processes": [...], "checkpoints": [...]}`."""
    procs, proc_error = live_processes(lister=lister, own_pid=own_pid)
    checkpoints = scan_checkpoints(roots=roots, now=now, stale_after=stale_after)

    foreign: List[Dict[str, Any]] = []
    if proc_error is None:
        rows, _ = lister()
        mine = ancestors(os.getpid() if own_pid is None else own_pid,
                         {pid: ppid for pid, ppid, _ in rows})
        foreign = foreign_players(rows, mine, {p["pid"] for p in procs})

    blockers: List[str] = []
    for p in procs:
        blockers.append("pid %d is running %s" % (p["pid"], p["module"]))
    for c in checkpoints:
        if c.get("live"):
            blockers.append("checkpoint %s is status=running, last written %.0f s ago"
                            % (os.path.basename(c["path"]), c["age_seconds"]))
        if "unreadable" in c:
            # A file that could not be parsed is an unknown state, not an
            # answered one. Counting it as "the checkpoint signal replied" would
            # turn a corrupt file into a clearance.
            blockers.append("checkpoint %s could not be read (%s); its campaign's "
                            "state is unknown" % (os.path.basename(c["path"]),
                                                  c["unreadable"]))

    if proc_error is not None:
        # Fail closed, without exception. An earlier version cleared this when
        # *any* checkpoint file existed, on the theory that the checkpoint scan
        # had answered instead -- but only `harness/campaign.py` writes a
        # checkpoint at all. `run_campaign`, `bare_cc` and `run_pilot` write
        # none, so for three of the four modules that can spend, the checkpoint
        # signal can never say yes, and four permanently-finished checkpoints
        # were already sitting on disk. The fallback therefore silenced the
        # fail-closed branch in every real situation while looking like a
        # second opinion. The process table is the only signal that sees an
        # envelope run; if it is unavailable, we do not know.
        blockers.append("cannot determine whether another campaign is running: "
                        "the process table is unavailable (%s), and it is the "
                        "only signal that can see a run_campaign / bare_cc / "
                        "run_pilot process -- those write no checkpoint"
                        % proc_error)

    return {
        "clear": not blockers,
        "blockers": blockers,
        "process_scan_error": proc_error,
        "processes": procs,
        # Reported, never a blocker -- see foreign_players. A caller that is
        # about to *measure* something rather than just spend should read this
        # and record it alongside the measurement.
        "foreign_players": foreign,
        "checkpoints": checkpoints,
        "stale_after_seconds": stale_after,
    }


def combined_exposure(checkpoints: List[Dict[str, Any]],
                      envelope_usd: float = 0.0,
                      envelope_http: int = 0) -> Dict[str, Any]:
    """The number INC-BA-003 says nobody could see: both campaigns' spend, added.

    Advisory, and deliberately so. It is reported next to the gate rather than
    turned into a threshold, because the S1 run's ceiling was approved
    separately and this session does not get to re-set another campaign's caps
    by folding them into its own. What was missing was visibility, not a cap.
    """
    # `cost_usd` on the checkpoint is what completed episodes cost. An episode
    # in flight has spent money that is only in `live_episode`, and leaving it
    # out understates the other campaign by exactly the episode running right
    # now -- which is the moment anyone reads this number.
    other_usd = sum(float(c.get("cost_usd") or 0.0)
                    + float((c.get("live_episode") or {}).get("cost_usd") or 0.0)
                    for c in checkpoints)
    other_http = sum(int(c.get("http_calls") or 0) for c in checkpoints)
    return {
        "other_campaigns_usd": round(other_usd, 4),
        "other_campaigns_http": other_http,
        "other_campaign_count": len(checkpoints),
        "other_campaigns_live": sum(1 for c in checkpoints if c.get("live")),
        "envelope_usd": round(envelope_usd, 4),
        "envelope_http": envelope_http,
        "combined_usd": round(other_usd + envelope_usd, 4),
        "combined_http": other_http + envelope_http,
    }


def main(argv=None) -> int:
    state = check()
    print("interlock: %s" % ("CLEAR" if state["clear"] else "BLOCKED"))
    if state["process_scan_error"]:
        print("  process scan unavailable: %s" % state["process_scan_error"])
    for p in state["processes"]:
        print("  live process: pid %d  %s" % (p["pid"], p["cmdline"]))
    for c in state["checkpoints"]:
        if "unreadable" in c:
            print("  checkpoint %s UNREADABLE (%s)" % (c["path"], c["unreadable"]))
            continue
        mark = "LIVE " if c["live"] else ("stale" if c["stale_running"] else "done ")
        print("  %s %-16s status=%-18s $%-8.2f age=%ss"
              % (mark, c.get("game_id"), c.get("status"), c.get("cost_usd") or 0.0,
                 c.get("age_seconds")))
    exposure = combined_exposure(state["checkpoints"])
    print("  other campaigns: $%.2f over %d HTTP calls"
          % (exposure["other_campaigns_usd"], exposure["other_campaigns_http"]))
    for f in state["foreign_players"]:
        print("  FOREIGN: pid %d is playing %s from outside this track: %s"
              % (f["pid"], ", ".join(f["games"]), f["cmdline"][:120]))
    if state["foreign_players"]:
        print("  (reported, not blocking -- cross-track serialisation is not "
              "this track's to impose. A measurement taken now must record it.)")
    for reason in state["blockers"]:
        print("  BLOCKED: %s" % reason)
    return 0 if state["clear"] else 3


if __name__ == "__main__":
    sys.exit(main())
