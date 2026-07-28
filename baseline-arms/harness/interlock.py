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

# A campaign checkpoint older than this is treated as abandoned. Episodes in the
# S1 run take 30-40 minutes and the in-episode checkpoint fires every fifth step
# (a few minutes), so 30 minutes is many checkpoint periods -- long enough that a
# live campaign is never mistaken for a dead one.
STALE_AFTER_SECONDS = 30 * 60

# Module invocations that spend money in this track.
CAMPAIGN_MODULES = ("harness.campaign", "harness.run_campaign",
                    "harness.run_pilot", "harness.bare_cc")

# ...except with these flags, which make the invocation read-only. `--gate-only`
# re-adjudicates the recorded cells and buys nothing; `--dry-run` lists and
# fetches nothing. Treating them as live spend is not a harmless over-count: the
# obvious way to ask "is it safe to start?" is to evaluate the gate, and an
# interlock that blocks on its own diagnostic is one nobody can clear. Observed
# for real -- three concurrent `--gate-only` readers showed up as three live
# campaigns.
READ_ONLY_FLAGS = ("--gate-only", "--dry-run", "--report-only", "--verify")

_TS = "%Y-%m-%dT%H:%M:%SZ"


def _parse_ts(value: Any) -> Optional[float]:
    if not isinstance(value, str):
        return None
    try:
        return calendar.timegm(time.strptime(value, _TS))
    except ValueError:
        return None


# ------------------------------------------------------------ process table
def list_processes() -> Tuple[List[Tuple[int, str]], Optional[str]]:
    """`([(pid, command_line)], error)`. `error` non-None means unavailable."""
    if os.name == "nt":
        cmd = ["powershell", "-NoProfile", "-NonInteractive", "-Command",
               "Get-CimInstance Win32_Process | "
               "Select-Object ProcessId,CommandLine | ConvertTo-Json -Compress"]
    else:
        cmd = ["ps", "-eo", "pid=,args="]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    except Exception as exc:                       # no shell, no ps, no policy
        return [], "%s: %s" % (type(exc).__name__, exc)
    if proc.returncode != 0:
        return [], "exit %d: %s" % (proc.returncode, (proc.stderr or "")[:200])

    out: List[Tuple[int, str]] = []
    if os.name == "nt":
        try:
            rows = json.loads(proc.stdout or "[]")
        except json.JSONDecodeError as exc:
            return [], "unparseable process list: %s" % exc
        if isinstance(rows, dict):
            rows = [rows]
        for row in rows:
            pid = row.get("ProcessId")
            if isinstance(pid, int):
                out.append((pid, row.get("CommandLine") or ""))
    else:
        for line in (proc.stdout or "").splitlines():
            m = re.match(r"\s*(\d+)\s+(.*)$", line)
            if m:
                out.append((int(m.group(1)), m.group(2)))
    return out, None


def live_processes(lister: Callable[[], Tuple[List[Tuple[int, str]], Optional[str]]] = list_processes,
                   own_pid: Optional[int] = None) -> Tuple[List[Dict[str, Any]], Optional[str]]:
    own_pid = os.getpid() if own_pid is None else own_pid
    rows, error = lister()
    if error is not None:
        return [], error
    found = []
    for pid, cmdline in rows:
        if pid == own_pid:
            continue
        if any(flag in cmdline for flag in READ_ONLY_FLAGS):
            continue
        for module in CAMPAIGN_MODULES:
            # `-m harness.campaign`, and not `harness.campaign_status`, which is
            # a read-only status printer and spends nothing.
            if re.search(r"-m\s+%s(\s|$)" % re.escape(module), cmdline):
                found.append({"pid": pid, "module": module,
                              "cmdline": cmdline[:300]})
                break
    return found, None


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

    blockers: List[str] = []
    for p in procs:
        blockers.append("pid %d is running %s" % (p["pid"], p["module"]))
    for c in checkpoints:
        if c.get("live"):
            blockers.append("checkpoint %s is status=running, last written %.0f s ago"
                            % (os.path.basename(c["path"]), c["age_seconds"]))

    if proc_error is not None and not checkpoints:
        # Neither signal available. Fail closed: unknown is not the same as clear.
        blockers.append("cannot determine whether another campaign is running "
                        "(process table unavailable: %s; no campaign checkpoints "
                        "found to fall back on)" % proc_error)

    return {
        "clear": not blockers,
        "blockers": blockers,
        "process_scan_error": proc_error,
        "processes": procs,
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
    other_usd = sum(float(c.get("cost_usd") or 0.0) for c in checkpoints)
    other_http = sum(int(c.get("http_calls") or 0) for c in checkpoints)
    return {
        "other_campaigns_usd": round(other_usd, 4),
        "other_campaigns_http": other_http,
        "other_campaign_count": len(checkpoints),
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
    for reason in state["blockers"]:
        print("  BLOCKED: %s" % reason)
    return 0 if state["clear"] else 3


if __name__ == "__main__":
    sys.exit(main())
