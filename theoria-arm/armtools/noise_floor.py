"""The noise floor: how far apart do two legs land when NOTHING changed?

`Theoria.md:336` forbids reading a single leg's difference as evidence. That
rule cannot be obeyed without a number: *smaller than what* is not evidence?
This module measures that number the only way it can be measured for free --
by running the offline campaign repeatedly against a mock world and a scratch
pool, and reporting, per scoreboard column, the mean / min / max and whether
the column moved at all.

## Two modes, because the offline path has two halves and only one of them runs

`python -m harness.campaign --mock --pool ... --out-dir ...` -- the rehearsal
command the CLI's own help prints -- sets `offline=True`, and `inner/loop.py`
line 856 then *skips the theorize beat entirely*. No desk call, so no manual;
no manual, so `books.load_predictor()` returns nothing; no predictor, so plan,
certify, probe design and the engine dispatch are all unreachable and every
turn falls through to `_probe_or_explore`'s exploration branch. Every column
downstream of the desk is therefore structurally zero, and a zero that is zero
because the code never ran is not a noise floor -- it is a dead column reading
zero. Measuring only that would produce a table of confident zeros about
machinery this campaign never touched.

So:

* `--mode cli` runs the documented command verbatim, as a subprocess, N times.
  This is the honest measurement of what the published rehearsal actually does.
* `--mode stub-desk` runs the same `Campaign` in-process with
  `ModelDesk._invoke` replaced by a **canned envelope** -- a fixed reply
  replayed from a real archived leg's books. The desk is thereby held exactly
  constant while everything else (engines, compile, certify, plan, probe,
  replay) runs for real. Any spread that survives that is the framework's own,
  which is precisely the quantity `Theoria.md:336` needs and the quantity the
  `cli` mode cannot see.

`stub-desk` is offline in the strong sense: `_invoke` is the only method that
starts a subprocess, and it is replaced, so no CLI is launched. As a belt,
`harness.modelcall.claude_bin` is replaced by a function that raises -- see
`install_stub_desk`. That guard is a negative control and it is exercised:
`--negative-control` installs the raiser *without* the `_invoke` stub and shows
the run refusing rather than spending.

## What gets cleaned up, and why that is not optional

`Campaign.run_leg` hardcodes `leg_dir = <arm>/runs/<slug>` and never forwards
`play(runs_root=...)`, so every rehearsal leg lands in the tracked archive --
the same archive `harness/run.py` warns a smoke must stay out of, because
"`armtools.verify_provenance` refuses a fixture found under it". Twelve
repetitions would deposit up to thirty-six such directories. This module
snapshots `runs/` before each repetition and removes exactly the directories
that repetition created, after reading the numbers out of them.

Usage:

    python -m armtools.noise_floor --mode cli        --reps 12 --out <dir>
    python -m armtools.noise_floor --mode stub-desk  --reps 12 --out <dir>
    python -m armtools.noise_floor --negative-control --out <dir>
"""

import argparse
import json
import os
import shutil
import statistics
import subprocess
import sys
import time
from typing import Any, Dict, List, Optional

import _bootstrap                                     # noqa: F401  (sys.path)

HERE = os.path.dirname(os.path.abspath(__file__))
ARM = os.path.dirname(HERE)
RUNS = os.path.join(ARM, "runs")

#: The seven surprise kinds, in `inner/surprise.py`'s order. Written out rather
#: than discovered from a run, so a repetition in which a kind never fires is
#: still a *column* reading zero and not a missing key.
SURPRISE_KINDS = ("execution_mismatch", "heuristic_miss", "probe_refutation",
                  "proof_failure", "render_mismatch", "replay_mismatch",
                  "search_timeout")

#: The scoreboard, in the order the report prints it.
COLUMNS = (tuple("surprise.%s" % k for k in SURPRISE_KINDS)
           + ("surprise.total", "theorize_rounds", "certify_rounds",
              "engine_dispatches", "actions_ok", "commands_sent",
              "levels_boundaries", "desk_calls", "turns", "steps",
              "legs_played", "legs_failed", "usd"))


# ---------------------------------------------------------------- the stub desk
def canned_reply(books_dir: str) -> str:
    """A real desk answer, replayed.

    `inner/theorize.py:BLOCK` parses `=== THEORY ===` / `=== PLAYBOOK ===` /
    `=== LOG ===` fenced blocks out of the reply text. Rather than invent a
    manual -- which would measure the variance of a manual nobody has ever run
    -- this reassembles the reply from an archived leg's own `theory.dsl` and
    `playbook.dsl`. The desk is then a constant whose value is a thing that
    actually happened.
    """
    with open(os.path.join(books_dir, "theory.dsl"), encoding="utf-8") as fh:
        theory = fh.read()
    with open(os.path.join(books_dir, "playbook.dsl"), encoding="utf-8") as fh:
        playbook = fh.read()
    return ("=== THEORY ===\n\n```\n%s\n```\n\n"
            "=== PLAYBOOK ===\n\n```\n%s\n```\n\n"
            "=== LOG ===\n\n```\nreplayed from an archived leg by "
            "armtools/noise_floor.py; the desk is held constant on purpose\n"
            "```\n" % (theory, playbook))


class DeskWasNotStubbed(RuntimeError):
    """The belt fired: something tried to start the real CLI.

    Its own class so the negative control can assert on it. If this is ever
    raised in anger it means a code path reached `claude_bin()` that
    `install_stub_desk` did not cover, and the correct reading is that the run
    was about to spend real money.
    """


def install_stub_desk(reply: Optional[str]) -> None:
    """Replace the desk's transport, and forbid the real one.

    Two independent edits, and the second is the one that makes the first
    trustworthy:

    * `ModelDesk._invoke` returns `(envelope, elapsed_ms, stderr)` -- the same
      triple the CLI path returns -- carrying `reply` and a zero price. Zero,
      not a plausible fake: a stub that invents dollars puts fiction into the
      cost columns, and cost is not what this measurement is about.
    * `claude_bin` is replaced by a raiser. `_invoke` is the only caller, so
      after the first edit it is unreachable -- which is exactly why it is
      worth installing. A guard that can only fire when the other guard has
      already failed is the only kind worth having, and passing `reply=None`
      installs the raiser *alone* so it can be seen to fire.
    """
    from harness import modelcall                      # noqa: PLC0415

    def _refuse(*_a, **_kw):
        raise DeskWasNotStubbed(
            "armtools.noise_floor forbids starting the real `claude` CLI: this "
            "measurement is offline and must not spend. Reaching claude_bin() "
            "means a desk call escaped the stub.")

    modelcall.claude_bin = _refuse

    if reply is None:
        return

    def _invoke(self, prompt: str, model: str):        # noqa: ARG001
        envelope = {
            "type": "result",
            "subtype": "success",
            "is_error": False,
            "result": reply,
            "total_cost_usd": 0.0,
            "usage": {"input_tokens": len(prompt) // 4,
                      "output_tokens": len(reply) // 4},
        }
        return envelope, 0, ""

    modelcall.ModelDesk._invoke = _invoke


# ---------------------------------------------------------- reading a campaign
def _leg_run_json(leg: Dict[str, Any]) -> Dict[str, Any]:
    path = os.path.join(leg.get("run_dir") or "", "run.json")
    if not os.path.exists(path):
        return {}
    try:
        with open(path, encoding="utf-8") as fh:
            return (json.load(fh) or {}).get("summary") or {}
    except Exception:                                  # noqa: BLE001
        return {}


def columns_of(campaign: Dict[str, Any]) -> Dict[str, float]:
    """One campaign's scoreboard, summed over its legs.

    Summed rather than averaged: the campaign is the unit a round compares, and
    a mean over a varying number of legs hides the case where the *count of
    legs* is what moved.
    """
    out: Dict[str, float] = {c: 0 for c in COLUMNS}
    for leg in campaign.get("legs") or []:
        if leg.get("event") == "leg_failed":
            out["legs_failed"] += 1
            out["usd"] += float(leg.get("usd") or 0.0)
            continue
        if not leg.get("slug"):
            continue                                   # a game_end marker
        out["legs_played"] += 1
        out["usd"] += float(leg.get("usd") or 0.0)
        by_kind = ((leg.get("surprises") or {}).get("by_kind") or {})
        for kind in SURPRISE_KINDS:
            out["surprise.%s" % kind] += int(by_kind.get(kind) or 0)
        out["surprise.total"] += int((leg.get("surprises") or {}).get("total")
                                     or 0)
        out["theorize_rounds"] += int(leg.get("theorize_rounds") or 0)
        out["actions_ok"] += int(leg.get("actions_ok") or 0)
        out["levels_boundaries"] += int((leg.get("levels") or {})
                                        .get("boundaries") or 0)
        summary = _leg_run_json(leg)
        out["desk_calls"] += int((summary.get("desk") or {}).get("calls") or 0)
        out["certify_rounds"] += int(summary.get("certify_rounds") or 0)
        out["engine_dispatches"] += int(summary.get("engine_dispatches") or 0)
        out["turns"] += int(summary.get("turns") or 0)
        out["steps"] += int(summary.get("steps") or 0)
        out["commands_sent"] += int((summary.get("budget") or {})
                                    .get("commands_sent") or 0)
    return out


def desk_failures_of(campaign: Dict[str, Any]) -> List[str]:
    """Every desk failure the legs recorded, flattened.

    The negative control needs this and nothing else does. `inner/loop.py`
    catches a raising desk and files it under `desk_failures` rather than
    letting it end the leg -- which is right, and which is also why the guard
    firing does NOT show up as an exception anywhere the campaign report can
    see. A negative control that looked only at `campaign.json` would have
    concluded the guard never fired, when in fact it fired and the arm handled
    it exactly as designed.
    """
    out: List[str] = []
    for leg in campaign.get("legs") or []:
        if not leg.get("slug"):
            continue
        for failure in (_leg_run_json(leg).get("desk_failures") or []):
            out.append(json.dumps(failure, sort_keys=True, default=str)
                       if not isinstance(failure, str) else failure)
    return out


def stop_signature(campaign: Dict[str, Any]) -> str:
    """Why the campaign ended, with the volatile parts filed off.

    The reason string embeds absolute run paths, so two identical campaigns
    produce two different strings. The *shape* is what a noise floor cares
    about, so paths and timestamps are replaced by a token.
    """
    stopped = campaign.get("stopped")
    if not stopped:
        return "ran-to-completion"
    reason = str(stopped.get("reason") or "")
    import re                                          # noqa: PLC0415
    reason = re.sub(r"[A-Za-z]:\\[^\s'\"]+", "<path>", reason)
    reason = re.sub(r"/[^\s'\"]*/runs/[^\s'\"]+", "<path>", reason)
    reason = re.sub(r"\d{8}T\d{6}Z", "<utc>", reason)
    return reason[:400]


# ------------------------------------------------------------------ one rep
def _snapshot_runs() -> set:
    return set(os.listdir(RUNS)) if os.path.isdir(RUNS) else set()


def _sweep_runs(before: set, keep: str) -> List[str]:
    """Delete the run directories this repetition created.

    Copied out to `keep` first. `Campaign` has no `--runs-root`, so a rehearsal
    lands in the tracked archive; leaving twelve repetitions' worth there would
    make a directory listing of `runs/` unable to tell a rehearsal from an
    experiment that cost money, which is the exact failure `harness/run.py`
    documents for smoke runs.
    """
    made = sorted(_snapshot_runs() - before)
    os.makedirs(keep, exist_ok=True)
    for name in made:
        src = os.path.join(RUNS, name)
        if not os.path.isdir(src):
            continue
        for wanted in ("run.json", "turn_series.json", "curves.json",
                       "surprises.jsonl", "levels.jsonl", "turns.json"):
            path = os.path.join(src, wanted)
            if os.path.exists(path):
                dst = os.path.join(keep, name)
                os.makedirs(dst, exist_ok=True)
                shutil.copy2(path, os.path.join(dst, wanted))
        shutil.rmtree(src, ignore_errors=True)
    return made


def rep_cli(index: int, workdir: str) -> Dict[str, Any]:
    """One repetition of the command the CLI's help prints, as a subprocess."""
    out_dir = os.path.join(workdir, "rep%02d" % index)
    pool = os.path.join(workdir, "rep%02d-pool.jsonl" % index)
    cmd = [sys.executable, "-m", "harness.campaign", "--mock",
           "--pool", pool, "--out-dir", out_dir]
    before = _snapshot_runs()
    started = time.time()
    proc = subprocess.run(cmd, cwd=ARM, capture_output=True,
                          encoding="utf-8", errors="replace", timeout=3600)
    elapsed = time.time() - started
    campaign = _read(os.path.join(out_dir, "campaign.json"))
    # Read the columns BEFORE the sweep. `columns_of` reaches into each leg's
    # `run.json` for the four fields `campaign.json` does not carry (desk
    # calls, certify rounds, engine dispatches, turns), and the sweep is about
    # to delete those directories.
    scoreboard = columns_of(campaign)
    made = _sweep_runs(before, os.path.join(out_dir, "legs"))
    return {"index": index, "mode": "cli", "exit_code": proc.returncode,
            "elapsed_s": round(elapsed, 3), "leg_dirs_created": made,
            "columns": scoreboard, "stop": stop_signature(campaign),
            "stderr_tail": (proc.stderr or "")[-800:]}


def rep_stub(index: int, workdir: str, reply: str) -> Dict[str, Any]:
    """One repetition with the desk held constant, in this process."""
    from harness import spend as spend_mod             # noqa: PLC0415
    from harness.campaign import Campaign              # noqa: PLC0415
    from harness.run import _scratch_policy            # noqa: PLC0415
    from proxy.mock.arc_mock import DEFAULT_KEY, MockArc   # noqa: PLC0415

    out_dir = os.path.join(workdir, "rep%02d" % index)
    pool = os.path.join(workdir, "rep%02d-pool.jsonl" % index)
    gate = spend_mod.SpendGate(_scratch_policy(pool))
    expect_pool = {"pool": gate.policy.pool,
                   "ledger_abspath": os.path.abspath(gate.ledger_path)}

    before = _snapshot_runs()
    started = time.time()
    error = None
    from harness.campaign import DEV_PILE              # noqa: PLC0415
    games = list(DEV_PILE)
    try:
        with MockArc(api_key=DEFAULT_KEY, games=games) as arc:
            camp = Campaign(prompt_id="A3-noise-floor", out_dir=out_dir,
                            games=games, model="claude-opus-5",
                            offline=False,                # the desk runs...
                            env_upstream=arc.base_url,    # ...against a mock world
                            env_key=DEFAULT_KEY, require_key=False,
                            spend_gate=gate, expect_pool=expect_pool)
            camp.run(max_legs_per_game=3)
    except BaseException as exc:                       # noqa: BLE001
        error = "%s: %s" % (type(exc).__name__, exc)
    elapsed = time.time() - started
    campaign = _read(os.path.join(out_dir, "campaign.json"))
    scoreboard = columns_of(campaign)                  # before the sweep
    failures = desk_failures_of(campaign)              # likewise
    made = _sweep_runs(before, os.path.join(out_dir, "legs"))
    return {"index": index, "mode": "stub-desk", "exit_code": 0 if not error else 1,
            "elapsed_s": round(elapsed, 3), "leg_dirs_created": made,
            "columns": scoreboard, "stop": stop_signature(campaign),
            "desk_failures": failures,
            "leg_errors": [leg.get("error") for leg in (campaign.get("legs") or [])
                           if leg.get("error")],
            "error": error}


def _read(path: str) -> Dict[str, Any]:
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


# --------------------------------------------------- where the variation lives
#: Fields that are *expected* to differ between two identical repetitions and
#: whose difference says nothing about the scoreboard. Naming them explicitly is
#: the point of the audit: everything not on this list that still moves is a
#: finding, and a normaliser that quietly smoothed away an unnamed field would
#: turn the audit into a tautology.
VOLATILE_KEYS = frozenset({
    "utc", "elapsed_s", "elapsed_ms", "started", "started_at", "ts", "t_utc",
    "run_id", "slug", "campaign", "reservation", "reservation_id", "ledger",
    "run_dir", "books_dir", "curves_path", "seed_books", "seed_from",
    "port", "base_url", "env_base", "pid", "ledger_abspath", "path",
    "out_path", "candidates_path", "transcript_dir", "dir", "work_dir",
})

_SLUG = None


def _normalise(node, volatile: List[str], prefix: str = ""):
    """Strip the fields whose motion is uninteresting, and say which ones moved.

    Returns the normalised tree; appends to `volatile` every path it blanked, so
    the audit can report what it chose not to look at rather than hiding it.
    """
    import re                                          # noqa: PLC0415
    global _SLUG                                       # noqa: PLW0603
    if _SLUG is None:
        _SLUG = re.compile(r"\d{8}T\d{6}Z-leg\d+|[A-Za-z]:\\\\?[^\s\"']+"
                           r"|r-[0-9a-f]{16}|\d{8}T\d{6}Z")
    if isinstance(node, dict):
        out = {}
        for key, value in node.items():
            path = "%s.%s" % (prefix, key) if prefix else key
            if key in VOLATILE_KEYS:
                volatile.append(path)
                out[key] = "<volatile>"
            else:
                out[key] = _normalise(value, volatile, path)
        return out
    if isinstance(node, list):
        return [_normalise(v, volatile, "%s[]" % prefix) for v in node]
    if isinstance(node, str):
        return _SLUG.sub("<volatile>", node)
    if isinstance(node, float):
        # Wall-clock-derived floats appear all over the turn rows. Rounding to
        # the nearest whole unit is not a fudge: it is the statement that this
        # audit is looking for structural difference, not for the third decimal
        # place of a duration. Anything that moves by a whole unit still shows.
        return round(node, 0)
    return node


def diff_paths(a, b, prefix: str = "", out: Optional[List[str]] = None,
               limit: int = 40) -> List[str]:
    """Where two normalised trees disagree, by path, capped."""
    out = [] if out is None else out
    if len(out) >= limit:
        return out
    if type(a) is not type(b):
        out.append("%s <type>" % (prefix or "<root>"))
        return out
    if isinstance(a, dict):
        for key in sorted(set(a) | set(b)):
            path = "%s.%s" % (prefix, key) if prefix else key
            if key not in a or key not in b:
                out.append("%s <present in one>" % path)
            else:
                diff_paths(a[key], b[key], path, out, limit)
        return out
    if isinstance(a, list):
        if len(a) != len(b):
            out.append("%s <len %d vs %d>" % (prefix or "<root>", len(a), len(b)))
            return out
        for i, (x, y) in enumerate(zip(a, b)):
            diff_paths(x, y, "%s[%d]" % (prefix, i), out, limit)
        return out
    if a != b:
        out.append("%s <%r vs %r>" % (prefix or "<root>", a, b))
    return out


def audit_variation(reps: List[Dict[str, Any]], workdir: str) -> Dict[str, Any]:
    """Compare repetition 1's artefacts, leg by leg, against every other.

    Legs are matched by **ordinal**, not by slug: the slug is a timestamp and
    can never match. A rep with a different number of legs is itself reported,
    because that is the largest possible difference and a per-file diff would
    miss it entirely.
    """
    findings: Dict[str, Any] = {"leg_count": {}, "files": {}, "volatile_seen": []}
    legs_per_rep = [len(r["leg_dirs_created"]) for r in reps]
    findings["leg_count"] = {"values": legs_per_rep,
                             "deterministic": len(set(legs_per_rep)) == 1}
    if not reps:
        return findings

    volatile: List[str] = []
    base = reps[0]
    for ordinal, name in enumerate(base["leg_dirs_created"]):
        for fname in ("run.json", "turn_series.json", "curves.json",
                      "surprises.jsonl", "turns.json"):
            key = "leg%02d/%s" % (ordinal + 1, fname)
            docs = []
            raws = []
            for rep in reps:
                names = rep["leg_dirs_created"]
                if ordinal >= len(names):
                    docs.append(None)
                    raws.append(None)
                    continue
                path = os.path.join(workdir, "rep%02d" % rep["index"], "legs",
                                    names[ordinal], fname)
                if not os.path.exists(path):
                    docs.append(None)
                    raws.append(None)
                    continue
                with open(path, "rb") as fh:
                    raw = fh.read()
                raws.append(raw)
                try:
                    docs.append(_normalise(json.loads(raw.decode("utf-8")),
                                           volatile))
                except Exception:                      # noqa: BLE001
                    docs.append(raw.decode("utf-8", "replace").splitlines())
            present = [d for d in docs if d is not None]
            if len(present) < 2:
                continue
            byte_identical = len({r for r in raws if r is not None}) == 1
            differing = []
            for other in present[1:]:
                differing = diff_paths(present[0], other)
                if differing:
                    break
            findings["files"][key] = {
                "reps_with_file": len(present),
                "byte_identical_raw": byte_identical,
                "identical_after_normalising": not differing,
                "differing_paths": differing[:40],
            }
    findings["volatile_seen"] = sorted(set(volatile))[:200]
    findings["surprise_placement"] = placement_histogram(reps, workdir)
    return findings


def placement_histogram(reps: List[Dict[str, Any]],
                        workdir: str) -> Dict[str, Any]:
    """Which turn each surprise was attributed to, across repetitions.

    Separate from the file diff because it answers a different question and is
    the one the figures actually depend on. The scoreboard columns are *totals*
    -- how many surprises fired -- and a total can be perfectly stable while
    the curve underneath it moves. `battery/metrics/economy.py`'s front-load
    index and figure 2 both read the per-turn series, so a per-turn column with
    a noise floor of its own is a fact those two need and the column table
    cannot show.

    Reported as the histogram of row indices carrying a surprise, pooled over
    every (repetition, leg) pair, plus the fraction that landed anywhere other
    than the modal row. That fraction is the number the round-to-round rule is
    written from.
    """
    import collections                                # noqa: PLC0415
    pooled: "collections.Counter[int]" = collections.Counter()
    per_leg: Dict[str, Dict[str, int]] = {}
    observations = 0
    for rep in reps:
        for ordinal, name in enumerate(rep["leg_dirs_created"]):
            path = os.path.join(workdir, "rep%02d" % rep["index"], "legs",
                                name, "curves.json")
            if not os.path.exists(path):
                continue
            with open(path, encoding="utf-8") as fh:
                doc = json.load(fh)
            rows = doc.get("rows") or []
            where = tuple(i for i, row in enumerate(rows)
                          if row.get("surprise_total"))
            if not where:
                continue
            observations += 1
            pooled.update(where)
            key = "leg%02d" % (ordinal + 1)
            per_leg.setdefault(key, {})
            per_leg[key][repr(where)] = per_leg[key].get(repr(where), 0) + 1
    total = sum(pooled.values())
    mode = max(pooled, key=lambda k: pooled[k]) if pooled else None
    return {
        "leg_observations_with_a_surprise": observations,
        "surprises_placed": total,
        "row_index_histogram": {str(k): v for k, v in sorted(pooled.items())},
        "modal_row": mode,
        "off_mode_fraction": (round(1 - pooled[mode] / total, 4)
                              if total else None),
        "max_displacement_rows": ((max(pooled) - min(pooled)) if pooled
                                  else None),
        "per_leg_ordinal": per_leg,
        "reading": (
            "the campaign-level surprise TOTALS can be perfectly deterministic "
            "while these move: armtools/archive.py joins a surprise to a turn "
            "by wall-clock containment, and `Surprise.ts` is truncated to the "
            "second while the turn edges are millisecond ledger stamps. Any "
            "turn shorter than a second is therefore a coin toss, and the "
            "written record calls the join `exact` anyway."),
    }


# ------------------------------------------------------------------- the table
def summarise(reps: List[Dict[str, Any]]) -> Dict[str, Any]:
    rows = [r["columns"] for r in reps]
    table: Dict[str, Any] = {}
    for column in COLUMNS:
        values = [row[column] for row in rows]
        table[column] = {
            "mean": round(statistics.fmean(values), 4) if values else None,
            "min": min(values) if values else None,
            "max": max(values) if values else None,
            "spread": (max(values) - min(values)) if values else None,
            "stdev": (round(statistics.pstdev(values), 4)
                      if len(values) > 1 else 0.0),
            "deterministic": len(set(values)) == 1,
            "values": values,
        }
    return {
        "reps": len(reps),
        "columns": table,
        "moved": sorted(c for c in COLUMNS if not table[c]["deterministic"]),
        "stop_signatures": sorted({r["stop"] for r in reps}),
        "elapsed_s": {"min": min((r["elapsed_s"] for r in reps), default=None),
                      "max": max((r["elapsed_s"] for r in reps), default=None)},
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--mode", choices=("cli", "stub-desk"), default="cli")
    ap.add_argument("--reps", type=int, default=12)
    ap.add_argument("--out", required=True, help="where noise.json is written")
    ap.add_argument("--books", default=None,
                    help="stub-desk only: an archived leg's books/ directory, "
                         "replayed as the desk's constant answer")
    ap.add_argument("--negative-control", action="store_true",
                    help="install the claude_bin raiser WITHOUT the _invoke "
                         "stub and run one repetition. A guard that has never "
                         "been seen to say no has not been shown to check "
                         "anything; this is where it says no.")
    args = ap.parse_args(argv)

    os.makedirs(args.out, exist_ok=True)
    work = os.path.join(args.out, "work")
    os.makedirs(work, exist_ok=True)

    if args.negative_control:
        install_stub_desk(None)
        # Two assertions, and the second is the one that matters. The first is
        # direct: after installation, the function that finds the real CLI
        # refuses. The second runs a whole leg and shows the refusal actually
        # reaching the desk -- which surfaces as a recorded `desk_failure` and
        # NOT as an exception, because `inner/loop.py` handles a raising desk
        # rather than dying of one.
        from harness import modelcall                  # noqa: PLC0415
        try:
            modelcall.claude_bin()
            direct = "claude_bin() returned instead of raising"
        except DeskWasNotStubbed as exc:
            direct = "DeskWasNotStubbed: %s" % exc
        result = rep_stub(0, work, reply="")
        evidence = json.dumps(
            {"error": result.get("error"),
             "leg_errors": result.get("leg_errors"),
             "desk_failures": result.get("desk_failures")}, default=str)
        doc = {"mode": "negative-control", "utc": _utc(),
               "expected": "a run that reaches the desk must refuse, not spend",
               "direct_call": direct,
               "error": result.get("error"),
               "leg_errors": result.get("leg_errors"),
               "desk_failures": result.get("desk_failures"),
               "refused": ("DeskWasNotStubbed" in direct
                           and "DeskWasNotStubbed" in evidence),
               "campaign_stop": result.get("stop"),
               "columns": result.get("columns")}
        _write(os.path.join(args.out, "negative_control.json"), doc)
        print(json.dumps(doc, indent=1, sort_keys=True))
        return 0 if doc["refused"] else 1

    reply = None
    if args.mode == "stub-desk":
        if not args.books:
            ap.error("--books is required for --mode stub-desk")
        reply = canned_reply(args.books)
        install_stub_desk(reply)

    reps: List[Dict[str, Any]] = []
    for index in range(1, args.reps + 1):
        rep = (rep_cli(index, work) if args.mode == "cli"
               else rep_stub(index, work, reply))
        reps.append(rep)
        print("rep %02d/%d  %s  %.1fs  legs=%d"
              % (index, args.reps, args.mode, rep["elapsed_s"],
                 len(rep["leg_dirs_created"])), file=sys.stderr)

    doc = {
        "schema": "theoria-noise-floor/v1",
        "mode": args.mode,
        "utc": _utc(),
        "books_replayed": args.books,
        "summary": summarise(reps),
        "variation_audit": audit_variation(reps, work),
        "reps": reps,
    }
    _write(os.path.join(args.out, "noise-%s.json" % args.mode), doc)
    print(json.dumps(doc["summary"], indent=1, sort_keys=True))
    return 0


def _utc() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _write(path: str, payload: Dict[str, Any]) -> None:
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(payload, fh, indent=1, sort_keys=True, default=str)
        fh.write("\n")


if __name__ == "__main__":
    sys.exit(main())
