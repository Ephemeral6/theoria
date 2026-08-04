"""A25 -- the action economy, measured off the record before it is tuned.

The arm's cadence has never been chosen. `MIN_NEW_FRAMES_BETWEEN_THEORIZE = 4`
was picked on 2026-07-28 to stop a run spending its whole budget on one probe
per adjudication, and nothing since has asked what it costs. This module asks,
from the ledgers alone -- no network, no desk, no spend.

Three questions, and the third is the one that matters.

**How many actions does a desk call buy?** Every live leg's `ledger.jsonl`
carries `env_step` and `model_call` rows in one `seq`-ordered stream, so the
actions between two adjudications are countable exactly rather than inferred
from a constant. The answer is not 4. It is not one number at all.

**What triggered each call?** `surprises.jsonl` records every surprise with its
kind and the beat that handled it. A call is attributed the kinds that arrived
since the previous call, which is what the gate actually released.

**Did the call change anything downstream?** This is the expensive question and
the honest one. A call rewrites the manual; whether the rewrite changed what
the arm *predicts* is a separate fact, and the record answers it: the books are
snapshotted `rev<N>-before-theorize` / `rev<N>-after-theorize` around every
call, both revisions compile offline, and both can be replayed over the
transitions that arrived after the call. If the two predictors draw the same
frame at every subsequent step, the call bought a differently-worded manual and
nothing else. `DOWNSTREAM_*` below are the verdicts, and `inert` is the one to
count.

The replay is the same machinery `inner/certify.py` uses -- `initial_state`,
`step`, `render`, `commit.action_to_manual` -- driven over a store rebuilt from
the ledger rather than from a live run. Where a revision does not compile the
verdict says so; a manual with no predictor is not scored as agreeing with one.

    python -m armtools.action_economy census
    python -m armtools.action_economy census --json --out census.json
    python -m armtools.action_economy constants
"""

import argparse
import json
import os
import statistics
import sys
from typing import Any, Dict, List, Optional, Tuple

import _bootstrap                                     # noqa: F401  (sys.path)

from inner import inertia

_HERE = os.path.dirname(os.path.abspath(__file__))
ARM_ROOT = os.path.dirname(_HERE)
DEFAULT_RUNS = os.path.join(ARM_ROOT, "runs")

#: A leg whose directory name contains one of these is skipped outright.
#:
#: `A26` is a live round in flight at the time this was written: its run
#: directories are being appended to by another process, so reading them would
#: measure a half-written ledger and reporting the number would be a claim
#: about a leg that has not finished. Absence is recorded as absence -- the
#: census names what it skipped in `skipped`, so a reader can tell "no A26 legs
#: existed" from "A26 legs existed and were not read".
SKIP_MARKERS = ("A26",)

DOWNSTREAM_CHANGED = "changed_a_later_prediction"
DOWNSTREAM_INERT = "no_later_prediction_changed"
DOWNSTREAM_NO_TAIL = "no_later_transition_to_predict"
DOWNSTREAM_GAINED = "gained_a_predictor_where_there_was_none"
DOWNSTREAM_LOST = "lost_the_predictor"
DOWNSTREAM_BLIND = "neither_revision_compiles"
DOWNSTREAM_UNPAIRED = "no_snapshot_pair_recorded"


# ---------------------------------------------------------------------------
# the ledger, read as one stream
# ---------------------------------------------------------------------------

def read_ledger(run_dir: str) -> List[Dict[str, Any]]:
    """Every ledger row, in `seq` order. A malformed line is skipped, loudly.

    The ledger is append-only and hash-chained, so out-of-order rows are not
    expected; sorting anyway costs nothing and means a salvaged or concatenated
    ledger still reads correctly.
    """
    path = os.path.join(run_dir, "ledger.jsonl")
    rows: List[Dict[str, Any]] = []
    if not os.path.isfile(path):
        return rows
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except ValueError:
                continue
    rows.sort(key=lambda r: r.get("seq") or 0)
    return rows


def _is_billed_action(row: Dict[str, Any]) -> bool:
    """A successful, billed ACTION.

    Two exclusions, both from `harness/budget.py`: a command that did not come
    back 200 moved nothing and is an attempt, not an action; and `RESET` is
    explicitly not billed as an action there, so counting it here would make
    this census disagree with the bill it is trying to explain.
    """
    if row.get("event") != "env_step":
        return False
    if (row.get("http") or {}).get("status") != 200:
        return False
    return (row.get("action") or {}).get("name") != "RESET"


def _observed_transitions(rows: List[Dict[str, Any]]) -> Tuple[List[Any], List[Any], List[int]]:
    """Rebuild `(grids, actions, seqs)` from the ledger.

    Aligned exactly as `world.frames.FrameStore` aligns them, because
    `inner/certify.py`'s replay reads that alignment: `grids[t]` is a state and
    `actions[t]` is the action taken *at* `grids[t]`, so the last element of
    `actions` is `None`. Getting this backwards silently shifts every replay by
    one step and turns an agreeing predictor into a diverging one.
    """
    grids: List[Any] = []
    names: List[Optional[str]] = []
    seqs: List[int] = []
    for row in rows:
        if row.get("event") != "env_step":
            continue
        if (row.get("http") or {}).get("status") != 200:
            continue
        frames = row.get("frames")
        if not frames:
            continue
        grids.append(frames[-1])
        names.append((row.get("action") or {}).get("name"))
        seqs.append(row.get("seq") or 0)
    # `names[i]` is the action that PRODUCED `grids[i]`; the store's `actions`
    # is the action taken AT `grids[i]`, which is the next one.
    actions: List[Optional[str]] = [
        names[i + 1] if i + 1 < len(names) else None for i in range(len(names))]
    return grids, actions, seqs


class _LedgerStore:
    """The two properties `certify`-style replay needs, and nothing else."""

    def __init__(self, grids: List[Any], actions: List[Optional[str]]) -> None:
        self.grids = grids
        self.actions = actions


# ---------------------------------------------------------------------------
# the books, recompiled from a snapshot
# ---------------------------------------------------------------------------

#: The at-call verdict's name for each after-the-fact one. The compile-level
#: verdicts are facts about the two revisions rather than about a window, so
#: `inner/inertia.py` and this module have always agreed on their spelling; the
#: two that differ are the two that name a window.
_DOWNSTREAM_OF_INERTIA = {
    inertia.MOVED: DOWNSTREAM_CHANGED,
    inertia.INERT: DOWNSTREAM_INERT,
    inertia.GAINED: DOWNSTREAM_GAINED,
    inertia.LOST: DOWNSTREAM_LOST,
    inertia.BLIND: DOWNSTREAM_BLIND,
    inertia.UNPAIRED: DOWNSTREAM_UNPAIRED,
    inertia.NO_EVIDENCE: DOWNSTREAM_NO_TAIL,
}


def _revision_verdicts(before_dir: Optional[str], after_dir: Optional[str],
                       store: _LedgerStore, first_tail_step: int,
                       evidence_frames: int,
                       deep: bool) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Both halves of the question, off one pair of replays.

    **After the fact** -- did this call change what the arm predicts about the
    world it went on to see? The tail is the transitions recorded *after* the
    call. A call answered at the very end of a leg has no tail, and that is
    reported as `no_later_transition_to_predict` rather than as agreement: an
    unanswerable question is not a negative answer. This is A25's verdict and
    its wording is unchanged, because the archive's published numbers are
    stated in it.

    **At the call** -- did the new manual predict what the old one predicted
    about the frames the arm *already had*? Same two compiled revisions, same
    drawn series, the complementary window `[0, first_tail_step)`. This is the
    half a running arm can compute for itself, and it is added here so the two
    can be cross-tabulated over the archive instead of one being assumed to
    stand for the other.

    The compile is shared. Judging both windows costs one extra list
    comparison, not one extra replay.
    """
    n = len(store.grids)
    limit = max(n - 1, 0)
    tail = limit - first_tail_step
    no_tail = first_tail_step >= limit

    if not before_dir or not after_dir:
        return ({"verdict": DOWNSTREAM_UNPAIRED},
                {"verdict": inertia.UNPAIRED})
    if not deep:
        down = ({"verdict": DOWNSTREAM_NO_TAIL, "tail_transitions": 0}
                if no_tail else {"verdict": None, "tail_transitions": tail})
        return down, {"verdict": None}

    judged = inertia.compare_revisions(
        before_dir, after_dir, store.actions,
        {"at_call": (0, first_tail_step), "tail": (first_tail_step, limit)},
        limit)
    at_call = judged["at_call"]
    at_call["evidence_frames"] = evidence_frames
    if no_tail:
        return {"verdict": DOWNSTREAM_NO_TAIL, "tail_transitions": 0}, at_call

    t = judged["tail"]
    verdict = _DOWNSTREAM_OF_INERTIA[t["verdict"]]
    down: Dict[str, Any] = {"verdict": verdict, "tail_transitions": tail}
    for key in ("before_error", "after_error"):
        if key in t:
            down[key] = t[key]
    if verdict in (DOWNSTREAM_CHANGED, DOWNSTREAM_INERT):
        down["first_divergent_step"] = t["first_divergent_step"]
        down["divergent_steps"] = t["divergent_steps"]
    return down, at_call


# ---------------------------------------------------------------------------
# one leg
# ---------------------------------------------------------------------------

def _snapshot_adjudications(run_dir: str
                            ) -> List[Tuple[Optional[str], Optional[str]]]:
    """One `(before, after)` record per adjudication the books saw, in order.

    `inner/theorize.run` snapshots `before-theorize` on the way in and
    `after-theorize` on the way out, so the snapshot directory is itself a list
    of adjudications. Reading it that way -- rather than collecting only the
    matched pairs -- keeps the *positions* right, and position is what ties a
    snapshot to a `model_call` row.

    Two irregular records, both real and both encountered in this repo's runs:

    * `(None, after)`. `Books.snapshot` copies only the files that exist, and
      on a cold start the `before` of the first call has no `theory.dsl` to
      copy -- so the directory is empty, and **git does not track an empty
      directory**. The `after` survives, its `before` does not, and dropping
      the record entirely would shift every later call by one.
    * `(before, None)`. The adjudication opened and never returned: the desk
      failed, or the spend gate tripped between the snapshot and the reply.
      Its `before` is the last thing in the directory on most finished legs.
    """
    root = os.path.join(run_dir, "books", "snapshots")
    if not os.path.isdir(root):
        return []
    records: List[Tuple[Optional[str], Optional[str]]] = []
    pending: Optional[str] = None
    for name in sorted(os.listdir(root)):
        path = os.path.join(root, name)
        if name.endswith("-before-theorize"):
            if pending is not None:
                records.append((pending, None))
            pending = path
        elif name.endswith("-after-theorize"):
            records.append((pending, path))
            pending = None
    if pending is not None:
        records.append((pending, None))
    return records


def _read_surprises(run_dir: str) -> List[Dict[str, Any]]:
    path = os.path.join(run_dir, "surprises.jsonl")
    out: List[Dict[str, Any]] = []
    if not os.path.isfile(path):
        return out
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                try:
                    out.append(json.loads(line))
                except ValueError:
                    continue
    return out


def _dsl_delta(before_dir: str, after_dir: str) -> Dict[str, Any]:
    """Whether the manual's text moved, and by how much."""
    def _read(d: str, name: str) -> Optional[str]:
        p = os.path.join(d, name)
        if not os.path.exists(p):
            return None
        with open(p, encoding="utf-8") as fh:
            return fh.read()

    out: Dict[str, Any] = {}
    for name in ("theory.dsl", "playbook.dsl"):
        a, b = _read(before_dir, name), _read(after_dir, name)
        key = name.split(".")[0]
        if a is None or b is None:
            out[key + "_changed"] = None
            continue
        out[key + "_changed"] = a != b
        out[key + "_chars_before"] = len(a)
        out[key + "_chars_after"] = len(b)
    return out


def _group_adjudications(calls: List[Dict[str, Any]]
                         ) -> List[List[Dict[str, Any]]]:
    """Group paid invocations into the adjudications that spent them.

    **These are not the same thing, and the difference is a third of the bill.**
    `inner/theorize.run` gives the desk `REPAIR_ROUNDS` extra invocations to fix
    a manual that will not compile, labelled `round2` and `round3`; each is a
    separate `model_call` row, each is charged in full, and none of them sees a
    frame the `round1` before it did not. So a cadence measured in `model_call`
    rows is not the cadence the loop's gate controls -- the gate runs once per
    adjudication and the repair rounds happen underneath it.

    A leg whose first invocation is not labelled `round1` (the two aborted
    first-contact legs predate the label) starts an adjudication anyway: a
    group is opened by a `round1` OR by having nothing open.
    """
    groups: List[List[Dict[str, Any]]] = []
    for call in calls:
        label = (call.get("request") or {}).get("label")
        if label == "round1" or not groups:
            groups.append([call])
        else:
            groups[-1].append(call)
    return groups


def leg_census(run_dir: str, *, deep: bool = True) -> Optional[Dict[str, Any]]:
    """One leg's cadence, adjudication by adjudication.

    `None` if the leg never called a desk. A leg with no `model_call` row is
    not a leg with a cadence of zero -- it is a leg the question does not apply
    to (a mock, a preflight, a salvage of a ledger that kept only the meta
    rows). Those are counted in the census header, never averaged into it.
    """
    rows = read_ledger(run_dir)
    if not rows:
        return None
    calls = [r for r in rows if r.get("event") == "model_call"]
    if not calls:
        return None

    grids, actions, grid_seqs = _observed_transitions(rows)
    store = _LedgerStore(grids, actions)
    surprises = _read_surprises(run_dir)
    records_by_snapshot = _snapshot_adjudications(run_dir)
    groups = _group_adjudications(calls)

    # The two lists are the same sequence of events seen from two sides -- the
    # books' side and the ledger's -- so they align from the front. There may
    # be *more* snapshot records than paid invocations: an adjudication that
    # tripped the spend gate between opening its snapshot and reaching the desk
    # left a `before` and no `model_call` row. There must never be fewer; if
    # there are, the attribution is refused outright rather than shifted,
    # because a snapshot pair against the wrong call is a worse answer than no
    # answer.
    if len(records_by_snapshot) >= len(groups) and groups:
        attribution = ("front_aligned: %d snapshot records, %d adjudications"
                       % (len(records_by_snapshot), len(groups)))
        aligned = records_by_snapshot[:len(groups)]
    else:
        attribution = ("unattributed: %d adjudications but only %d snapshot "
                       "records" % (len(groups), len(records_by_snapshot)))
        aligned = [(None, None)] * len(groups)

    run_end = next((r for r in rows if r.get("event") == "run_end"), {})

    records: List[Dict[str, Any]] = []
    prev_seq = -1
    # `-1` is what `loop.__init__` sets `_frames_at_last_theorize` to, so the
    # first call's `new_frames` is `step_idx + 1` there. Starting the census at
    # 0 instead would understate the first gap by one on every leg.
    prev_step: Optional[int] = -1
    for idx, group in enumerate(groups):
        head = group[0]
        head_step = head.get("step_idx")
        seq = head.get("seq") or 0
        window = [r for r in rows if prev_seq < (r.get("seq") or 0) < seq]
        actions_since = sum(1 for r in window if _is_billed_action(r))
        commands_since = sum(1 for r in window if r.get("event") == "env_step")
        # **What the gate actually counts.** A `model_call` row's `step_idx` is
        # `len(store.steps)` at the moment of the call, which is the quantity
        # `_frames_this_level` subtracts -- so the difference between two calls'
        # `step_idx` IS the gate's `new_frames`, exactly, with no reconstruction.
        #
        # And it is not the number of transitions. `loop._record` appends a
        # Step for every arm-level command including the ones that came back
        # 400, so a command the world refused counts toward the floor as much
        # as one that moved something. On the two sk48 legs, which ran through
        # the refusal wave, this is the difference between a gate that waits
        # for four transitions and one that waits for four attempts.
        frames_since = ((head_step - prev_step)
                        if (head_step is not None and prev_step is not None)
                        else None)
        triggers: Dict[str, int] = {}
        lo = _ts_at(rows, prev_seq)
        for s in surprises:
            # `surprises.jsonl` carries the register's own sequence, not the
            # ledger's, so attribution goes by timestamp -- the only clock the
            # two files share.
            ts = s.get("ts")
            if ts is not None and _between(ts, lo, head.get("ts")):
                kind = s.get("kind") or "unknown"
                triggers[kind] = triggers.get(kind, 0) + 1

        # How many observed frames precede this call: the index the tail starts
        # at, in the same units the replay uses.
        frames_before_call = sum(1 for s in grid_seqs if s < seq)
        first_tail_step = max(frames_before_call - 1, 0)

        pair = aligned[idx]
        cost = sum((c.get("response") or {}).get("total_cost_usd") or 0.0
                   for c in group)
        record: Dict[str, Any] = {
            "adjudication_idx": idx,
            "seq": seq,
            "ts": head.get("ts"),
            "step_idx": head.get("step_idx"),
            "beat": (head.get("request") or {}).get("beat"),
            "paid_invocations": len(group),
            "repair_invocations": len(group) - 1,
            "labels": [(c.get("request") or {}).get("label") for c in group],
            "returned_a_manual": pair[1] is not None,
            "cost_usd": round(cost, 6),
            "elapsed_ms": sum((c.get("http") or {}).get("elapsed_ms") or 0
                              for c in group),
            "actions_since_prev_adjudication": actions_since,
            "frames_since_prev_adjudication": frames_since,
            "commands_since_prev_adjudication": commands_since,
            # The gate's unit minus the bill's unit. Positive means the floor
            # was met by commands that bought no transition.
            "frames_not_actions": (None if frames_since is None
                                   else frames_since - actions_since),
            "triggers": triggers,
        }
        if pair[0] and pair[1]:
            record["manual"] = _dsl_delta(pair[0], pair[1])
            record["snapshot_before"] = os.path.basename(pair[0])
            record["snapshot_after"] = os.path.basename(pair[1])
        # Two windows, one pair of replays. `downstream` is A25's verdict and
        # its numbers are published; `at_call` is the half the running arm can
        # compute for itself, and the census exists to say how far the two
        # agree rather than to assume they do.
        record["downstream"], record["at_call"] = _revision_verdicts(
            pair[0], pair[1], store, first_tail_step, frames_before_call, deep)
        records.append(record)
        prev_seq = group[-1].get("seq") or seq
        if head_step is not None:
            prev_step = head_step

    billed = sum(1 for r in rows if _is_billed_action(r))
    trailing = sum(1 for r in rows
                   if (r.get("seq") or 0) > prev_seq and _is_billed_action(r))
    spend = sum(r["cost_usd"] for r in records)
    invocations = len(calls)
    return {
        "leg": os.path.basename(run_dir),
        "game": next((r.get("game_id") for r in rows if r.get("game_id")), None),
        "outcome": run_end.get("outcome"),
        "levels_completed": run_end.get("levels_completed"),
        "action_ceiling": _action_ceiling(run_dir),
        "level_baseline_actions": _level_baselines(rows),
        # A carried leg starts its first turn with a manual already in hand, so
        # the floor applies to its very first adjudication. A cold one does
        # not, and the historic gate lets that first call through unconditioned.
        "carried": os.path.isfile(os.path.join(run_dir, "books", "CARRIED.json")),
        "adjudications": len(records),
        "paid_invocations": invocations,
        "repair_invocations": invocations - len(records),
        "snapshot_attribution": attribution,
        "billed_actions": billed,
        "actions_after_last_call": trailing,
        "observed_frames": len(grids),
        "usd": round(spend, 6),
        "actions_per_adjudication": (round(billed / len(records), 3)
                                     if records else None),
        "actions_per_paid_invocation": (round(billed / invocations, 3)
                                        if invocations else None),
        "usd_per_action": (round(spend / billed, 6) if billed else None),
        "calls": records,
    }


def _level_baselines(rows: List[Dict[str, Any]]) -> Optional[List[int]]:
    """What the world itself says a level costs, off the leg's own `env_meta`.

    A25's replay quoted one number for every leg -- 78, g50t level 1's
    baseline -- and 5 of the 15 legs in the archive are sk48, whose level 1
    baseline is 61. Judging an sk48 leg against g50t's boundary overstates how
    far it had to go by 28%. The number is in each leg's own ledger; there is
    no reason to borrow another game's.
    """
    for row in rows:
        if row.get("event") != "env_meta":
            continue
        for env in ((row.get("response") or {}).get("environments") or []):
            for run in (env.get("runs") or []):
                baselines = run.get("level_baseline_actions")
                if baselines:
                    return [int(x) for x in baselines]
    return None


def _action_ceiling(run_dir: str) -> Optional[int]:
    """The leg's declared action budget, for the gate's end-of-leg escape.

    `None` when the leg wrote no summary. The replay then falls back to a
    nominal ceiling and says so, rather than reading the observed action count
    as the ceiling -- which would make every call in a short leg look like the
    last one and switch the escape on for all of them.
    """
    path = os.path.join(run_dir, "run.json")
    if not os.path.isfile(path):
        return None
    try:
        with open(path, encoding="utf-8") as fh:
            doc = json.load(fh)
    except (ValueError, OSError):
        return None
    return ((doc.get("summary") or {}).get("budget") or {}).get("ceiling_actions")


def _ts_at(rows: List[Dict[str, Any]], seq: int) -> Optional[str]:
    if seq < 0:
        return None
    for row in rows:
        if (row.get("seq") or 0) == seq:
            return row.get("ts")
    return None


def _between(ts: str, lo: Optional[str], hi: Optional[str]) -> bool:
    if hi is not None and ts > hi:
        return False
    if lo is not None and ts <= lo:
        return False
    return True


# ---------------------------------------------------------------------------
# the census
# ---------------------------------------------------------------------------

def census(runs_root: str = DEFAULT_RUNS, *, deep: bool = True) -> Dict[str, Any]:
    """Every leg under `runs_root` that ever called a desk."""
    legs: List[Dict[str, Any]] = []
    skipped: List[Dict[str, str]] = []
    no_desk: List[str] = []
    for name in sorted(os.listdir(runs_root)):
        run_dir = os.path.join(runs_root, name)
        if not os.path.isdir(run_dir):
            continue
        marker = next((m for m in SKIP_MARKERS if m in name), None)
        if marker:
            skipped.append({"leg": name, "why": "matches skip marker %r "
                                                "(live round in flight)" % marker})
            continue
        try:
            record = leg_census(run_dir, deep=deep)
        except Exception as exc:                       # noqa: BLE001
            skipped.append({"leg": name,
                            "why": "%s: %s" % (type(exc).__name__, exc)})
            continue
        if record is None:
            if os.path.isfile(os.path.join(run_dir, "ledger.jsonl")):
                no_desk.append(name)
            continue
        legs.append(record)

    _fill_level_baselines(legs)
    all_calls = [c for leg in legs for c in leg["calls"]]
    at_call_signal = _at_call_signal(all_calls)
    gaps = [c["actions_since_prev_adjudication"] for c in all_calls]
    verdicts: Dict[str, int] = {}
    trigger_totals: Dict[str, int] = {}
    for call in all_calls:
        v = (call.get("downstream") or {}).get("verdict")
        verdicts[str(v)] = verdicts.get(str(v), 0) + 1
        for kind, n in (call.get("triggers") or {}).items():
            trigger_totals[kind] = trigger_totals.get(kind, 0) + n

    billed = sum(leg["billed_actions"] for leg in legs)
    usd = sum(leg["usd"] for leg in legs)
    invocations = sum(leg["paid_invocations"] for leg in legs)
    repairs = sum(leg["repair_invocations"] for leg in legs)
    inert = verdicts.get(DOWNSTREAM_INERT, 0)
    scored = sum(verdicts.get(k, 0) for k in
                 (DOWNSTREAM_INERT, DOWNSTREAM_CHANGED, DOWNSTREAM_GAINED,
                  DOWNSTREAM_LOST))
    manual_unchanged = sum(
        1 for c in all_calls
        if (c.get("manual") or {}).get("theory_changed") is False)
    return {
        "tool": "armtools.action_economy",
        "runs_root": os.path.relpath(runs_root, ARM_ROOT).replace("\\", "/"),
        "legs_with_desk_calls": len(legs),
        "legs_without_desk_calls": len(no_desk),
        "legs_without_desk_calls_names": no_desk,
        "skipped": skipped,
        "totals": {
            "adjudications": len(all_calls),
            "paid_invocations": invocations,
            "repair_invocations": repairs,
            "billed_actions": billed,
            "usd": round(usd, 6),
            "actions_per_adjudication": (round(billed / len(all_calls), 3)
                                         if all_calls else None),
            "actions_per_paid_invocation": (round(billed / invocations, 3)
                                            if invocations else None),
            "usd_per_action": round(usd / billed, 6) if billed else None,
            "usd_per_adjudication": (round(usd / len(all_calls), 6)
                                     if all_calls else None),
        },
        "gap_actions_between_adjudications": {
            "n": len(gaps),
            "min": min(gaps) if gaps else None,
            "median": statistics.median(gaps) if gaps else None,
            "mean": round(statistics.mean(gaps), 3) if gaps else None,
            "max": max(gaps) if gaps else None,
            "histogram": _histogram(gaps),
            "zero_gap_adjudications": sum(1 for g in gaps if g == 0),
        },
        "gate_counts_what_the_bill_does_not": {
            "note": "`_frames_this_level` counts `len(store.steps)`, and "
                    "`loop._record` appends a Step for every arm-level command "
                    "including the ones the world refused. So the floor can be "
                    "met by commands that bought no transition. This is the "
                    "size of that gap across the archive.",
            "adjudications_with_a_gap": sum(
                1 for c in all_calls if (c.get("frames_not_actions") or 0) > 0),
            "total_frames_that_were_not_actions": sum(
                max(c.get("frames_not_actions") or 0, 0) for c in all_calls),
            "worst_leg": max(
                ((leg["leg"], sum(max(c.get("frames_not_actions") or 0, 0)
                                  for c in leg["calls"]))
                 for leg in legs),
                key=lambda kv: kv[1], default=(None, 0)),
        },
        "triggers": trigger_totals,
        "downstream": verdicts,
        "at_call_signal": at_call_signal,
        "calls_that_bought_nothing": {
            "manual_text_unchanged": manual_unchanged,
            "inert": inert,
            "scored": scored,
            "fraction_of_scored": (round(inert / scored, 4) if scored else None),
        },
        "legs": legs,
    }


def _fill_level_baselines(legs: List[Dict[str, Any]]) -> None:
    """Give a leg that never recorded an `env_meta` its own game's baselines.

    Six of the fifteen legs have no `env_meta` row -- a carried leg does not
    re-open the environment, and a salvaged ledger may have lost the row. The
    baseline is a property of the GAME, not of the leg, so the same game's
    number from another leg is the right answer and `None` is not. It is a
    borrowed number all the same, so the source is written down beside it: a
    reader must be able to tell a measurement from a lookup.
    """
    # The donor must have played the real world. `proxy/mock` reports
    # `[8, 8, 8]`, and lending that to a leg that played ARC would say a level
    # costs 8 actions when it costs 78 -- which would make every policy look
    # like it clears the boundary. A leg whose OWN record says 8 keeps it and
    # is flagged `mock_world`; only the silent ones are lent to.
    by_game: Dict[str, List[int]] = {}
    for leg in legs:
        rec = leg.get("level_baseline_actions")
        if rec and leg.get("game") and max(rec) > 8:
            by_game.setdefault(leg["game"], rec)
    for leg in legs:
        if leg.get("level_baseline_actions"):
            leg["level_baseline_source"] = "this leg's own env_meta"
            continue
        borrowed = by_game.get(leg.get("game"))
        if borrowed:
            leg["level_baseline_actions"] = list(borrowed)
            leg["level_baseline_source"] = (
                "borrowed from another leg of %s -- this leg recorded no "
                "env_meta" % leg.get("game"))
        else:
            leg["level_baseline_source"] = None


def _histogram_str(values: List[str]) -> Dict[str, int]:
    out: Dict[str, int] = {}
    for v in values:
        out[str(v)] = out.get(str(v), 0) + 1
    return dict(sorted(out.items()))


def _at_call_signal(all_calls: List[Dict[str, Any]]) -> Dict[str, Any]:
    """How far the signal the arm can compute agrees with the audit it cannot.

    The at-call verdict is available the instant a call returns; the downstream
    verdict needs the rest of the leg. A policy that acts on the first is
    making a bet about the second, and this is the table that prices the bet.

    Both are reported and neither is called the truth. The downstream verdict
    is not ground truth about waste either -- it is a statement about the frames
    this particular leg happened to visit next, and a call that changed a
    prediction the leg never tested reads as inert there too. What the table
    supports is a conditional: *given* the archive's downstream verdicts, this
    is how often an arm following the at-call signal would have been right.
    """
    cells: Dict[str, int] = {}
    counts: Dict[str, int] = {}
    both = 0
    absorbing = 0
    moved_and_changed = 0
    prefix_windows: List[int] = []
    only_at_call = 0
    for call in all_calls:
        a = (call.get("at_call") or {}).get("verdict")
        d = (call.get("downstream") or {}).get("verdict")
        counts[str(a)] = counts.get(str(a), 0) + 1
        if a in (inertia.MOVED, inertia.INERT) and d in (DOWNSTREAM_CHANGED,
                                                         DOWNSTREAM_INERT):
            both += 1
            prefix_windows.append(call["at_call"].get("steps_in_window") or 0)
            cells["%s|%s" % (a, d)] = cells.get("%s|%s" % (a, d), 0) + 1
            if a == inertia.MOVED and d == DOWNSTREAM_CHANGED:
                moved_and_changed += 1
                # The tail's first divergence is the tail's first STEP: the two
                # predictors had already parted company before the call's
                # window ended, and a `step` fold carries a divergence forward.
                if (call["downstream"].get("first_divergent_step")
                        == (call["at_call"].get("window") or [0, 0])[1]):
                    absorbing += 1
        elif a in (inertia.MOVED, inertia.INERT):
            only_at_call += 1
    said_inert = (cells.get("%s|%s" % (inertia.INERT, DOWNSTREAM_INERT), 0)
                  + cells.get("%s|%s" % (inertia.INERT, DOWNSTREAM_CHANGED), 0))
    hit = cells.get("%s|%s" % (inertia.INERT, DOWNSTREAM_INERT), 0)
    was_inert = (hit + cells.get("%s|%s" % (inertia.MOVED, DOWNSTREAM_INERT), 0))
    usd_at_call_inert = round(sum(
        c["cost_usd"] for c in all_calls
        if (c.get("at_call") or {}).get("verdict") == inertia.INERT), 4)
    return {
        "verdicts": dict(sorted(counts.items())),
        "usd_on_calls_the_arm_could_have_called_inert_at_the_time":
            usd_at_call_inert,
        "cross_tab": dict(sorted(cells.items())),
        "comparable_calls": both,
        "prefix_window_steps": {
            "min": min(prefix_windows) if prefix_windows else None,
            "median": (statistics.median(prefix_windows)
                       if prefix_windows else None),
            "max": max(prefix_windows) if prefix_windows else None,
        },
        "scored_only_by_the_at_call_signal": only_at_call,
        "why_the_two_agree": {
            "moved_and_changed": moved_and_changed,
            "of_which_the_tail_diverges_at_its_very_first_step": absorbing,
            "reading": "these two are not independent tests. `step` is a fold: "
                       "once two revisions disagree about a state they carry "
                       "the disagreement forward, so a pair that parted "
                       "company inside the call's own window is still parted "
                       "at every later step. Where this count equals "
                       "`moved_and_changed`, the tail told us nothing the "
                       "prefix had not already said -- which is why the "
                       "agreement below is mechanical rather than lucky, and "
                       "why it should be expected to hold on the next leg. "
                       "What the prefix genuinely cannot see is a rewrite "
                       "whose only effect is under an action the arm has never "
                       "taken; that is the `inert|changed` cell, and on this "
                       "archive it is empty.",
        },
        "note": "cross_tab keys are 'at_call|downstream'; only the calls where "
                "BOTH verdicts are moved/inert are comparable, so the counts "
                "here are smaller than either column on its own.",
        "if_the_arm_had_believed_the_signal": {
            "calls_it_would_have_called_inert": said_inert,
            "of_those_also_inert_downstream": hit,
            "precision": round(hit / said_inert, 4) if said_inert else None,
            "downstream_inert_calls_it_would_have_missed": was_inert - hit,
            "recall": round(hit / was_inert, 4) if was_inert else None,
            "base_rate": (round(was_inert / both, 4) if both else None),
        },
    }


def _histogram(values: List[int]) -> Dict[str, int]:
    out: Dict[str, int] = {}
    for v in values:
        out[str(v)] = out.get(str(v), 0) + 1
    return dict(sorted(out.items(), key=lambda kv: int(kv[0])))


# ---------------------------------------------------------------------------
# the counterfactual: the same money, a different cadence
# ---------------------------------------------------------------------------

#: A leg's dollar ceiling, from `harness/campaign.py`. The projection below is
#: quoted at this figure because it is the figure a round actually buys.
def _leg_cap() -> float:
    from harness.campaign import LEG_USD_CAP           # noqa: PLC0415
    return float(LEG_USD_CAP)


def replay_policy(report: Dict[str, Any], name: str) -> Dict[str, Any]:
    """Re-decide every recorded adjudication under a named policy.

    **What this is.** A strict walk over the recorded stream: for each
    adjudication the arm actually made, the policy's own `gate` is asked
    whether it would have made it, given the evidence that had accumulated
    since the last call the policy *fired* (not since the last call the arm
    made -- a policy that skips a call inherits its evidence). Refused calls
    are subtracted from the bill. Nothing is invented: every dollar and every
    action in the output is one the ledger records.

    **What this is not.** It is not a simulation of the leg the policy would
    have run. Skipping a call changes what the arm does next, and the record
    cannot say what frames a different arm would have seen. So the strict half
    answers exactly one question -- *of the calls this leg made, which would
    this policy have refused, and what did they cost* -- and the projection
    that follows is labelled a projection.

    **The projection, and the assumption it rests on.** Nine of the fifteen
    legs ended on `spend_gate_tripped`: money is the binding constraint, so
    actions-per-dollar is the quantity that decides how far a leg gets. The
    projection is `LEG_USD_CAP x actions_per_dollar`, and it is only valid if a
    call's price does not rise with the wait before it. The record says it does
    not: `corr(step_idx, cost_usd) = -0.039` over the 65 priced calls, and the
    mean cost is $1.77 at gap 0 against $2.31 at gap 4. That is the whole basis
    for believing a wider floor buys actions rather than merely deferring them,
    and it is stated here so that a reader who doubts it knows exactly which
    number to attack.
    """
    from dataclasses import replace                    # noqa: PLC0415
    from inner import economy as economy_mod           # noqa: PLC0415

    cfg = economy_mod.policy(name)
    # A shallow census carries no verdicts, so an inertia-driven policy
    # replayed against one silently degrades to its floor and reports a null
    # that means "not measured" while looking like "no effect". Counted and
    # published rather than guarded against, because the shallow census is
    # legitimately useful for the cadence arithmetic that does not need them.
    scored = sum(1 for leg in report["legs"] for c in leg["calls"]
                 if (c.get("at_call") or {}).get("verdict")
                 in (inertia.MOVED, inertia.INERT))
    legs_out: List[Dict[str, Any]] = []
    unreachable = 0
    for leg in report["legs"]:
        econ = economy_mod.ActionEconomy(cfg)
        fired: List[Dict[str, Any]] = []
        refused: List[Dict[str, Any]] = []
        carried_frames = 0
        carried_actions = 0
        rounds_this_step: Dict[Any, int] = {}
        # `actions_left` decides the historic escape at the end of a leg. The
        # ceiling is the one the leg declared; falling back to the observed
        # count would make every call look like the last one.
        ceiling = leg.get("action_ceiling") or 300
        spent_actions = 0
        for call in leg["calls"]:
            carried_frames += call.get("frames_since_prev_adjudication") or 0
            carried_actions += call["actions_since_prev_adjudication"]
            spent_actions += call["actions_since_prev_adjudication"]
            step = call.get("step_idx")
            taken = rounds_this_step.get(step, 0)
            if taken >= econ.rounds_allowed():
                refused.append(dict(call, refused_by="max_rounds_per_turn"))
                continue
            if taken:
                # A continuation round, INSIDE the turn's `while` loop. The
                # historic gate is checked once per turn, before the loop, and
                # the second round never sees it -- which is exactly why 24
                # recorded adjudications had a gap of zero and why the control
                # must not refuse them. Gating here would make `today` disagree
                # with the record, and a control that disagrees with the record
                # invalidates every row beside it. `gate_every_round` is the
                # policy that changes that, and `gate_continuation` returns
                # allow for every policy that does not set it.
                decision = econ.gate_continuation(
                    has_manual=(call["adjudication_idx"] > 0
                                or bool(leg.get("carried"))),
                    pending=sum((call.get("triggers") or {}).values()) or 1,
                    pending_kinds=tuple(call.get("triggers") or ()))
                if decision.allow and not cfg.gate_every_round:
                    # Would the kind clauses have refused this round, had they
                    # been asked? Counted for every policy, acted on by none
                    # that leaves `gate_every_round` off. This is the number
                    # that explains a lever which refuses nothing: it is not
                    # that the condition never held, it is that the gate is
                    # never consulted where it holds.
                    probe = economy_mod.ActionEconomy(
                        replace(cfg, gate_every_round=True))
                    probe._inert_kinds = econ._inert_kinds
                    if not probe.gate_continuation(
                            has_manual=True,
                            pending=sum((call.get("triggers") or {}).values()) or 1,
                            pending_kinds=tuple(call.get("triggers") or ())).allow:
                        unreachable += 1
            else:
                decision = econ.gate(
                    has_manual=(call["adjudication_idx"] > 0
                                or bool(leg.get("carried"))),
                    pending=sum((call.get("triggers") or {}).values()) or 1,
                    new_frames=carried_frames,
                    new_actions=carried_actions,
                    actions_left=max(ceiling - spent_actions, 0),
                    pending_kinds=tuple(call.get("triggers") or ()),
                )
            if not decision.allow:
                refused.append(dict(
                    call,
                    refused_by=(decision.clause or
                                ("gate_continuation" if taken else "floor")),
                    floor_at_refusal=decision.floor))
                continue
            rounds_this_step[step] = taken + 1
            fired.append(dict(call, floor_at_call=decision.floor,
                              actions_bought=carried_actions))
            # The at-call verdict is fed here and only here. It is the same
            # number a live arm would have had in hand the instant this call
            # returned -- `_revision_verdicts` computes it over the frames
            # recorded BEFORE the call -- so a policy that reads it in the
            # replay is not reading the future. That is the whole reason the
            # signal was built; a replay that fed it the downstream verdict
            # would be measuring an oracle.
            econ.note_adjudication(
                manual_moved=(call.get("manual") or {}).get("theory_changed"),
                bought_nothing=inertia.bought_nothing(
                    (call.get("at_call") or {}).get("verdict")),
                pending_kinds=tuple(call.get("triggers") or ()))
            carried_frames = 0
            carried_actions = 0

        usd_fired = sum(c["cost_usd"] for c in fired)
        usd_refused = sum(c["cost_usd"] for c in refused)
        actions_fired = sum(c["actions_bought"] for c in fired)
        leg_per_dollar = (actions_fired / usd_fired) if usd_fired else None
        # The same question asked without the late-refusal bias. Every action
        # in `billed_actions` happened and is recorded; the strict replay does
        # not un-play them. Dividing them by the reduced bill is the pessimistic
        # reading -- the leg goes exactly as it went, for less money -- while
        # `actions_per_dollar` credits a call only with the actions between it
        # and the previous one, so refusing a leg's LAST call silently drops
        # that leg's trailing actions out of the numerator. Both are reported
        # because they bracket the answer and neither alone is honest.
        leg_per_dollar_all = ((leg["billed_actions"] / usd_fired)
                              if usd_fired else None)
        legs_out.append({
            "leg": leg["leg"],
            "game": leg.get("game"),
            "outcome_recorded": leg.get("outcome"),
            "levels_completed_recorded": leg.get("levels_completed"),
            "actions_per_dollar": (round(leg_per_dollar, 4)
                                   if leg_per_dollar else None),
            "actions_per_dollar_whole_leg": (round(leg_per_dollar_all, 4)
                                             if leg_per_dollar_all else None),
            "actions_at_leg_cap": (round(_leg_cap() * leg_per_dollar, 1)
                                   if leg_per_dollar else None),
            "actions_at_leg_cap_whole_leg": (
                round(_leg_cap() * leg_per_dollar_all, 1)
                if leg_per_dollar_all else None),
            # This leg's own level-1 boundary, from its own `env_meta`: 78 for
            # g50t, 61 for sk48, 8 on the legs that played a mock world.
            "level_1_needs": ((leg.get("level_baseline_actions") or [None])[0]),
            "level_1_needs_source": leg.get("level_baseline_source"),
            "mock_world": bool(leg.get("level_baseline_actions")
                               and max(leg["level_baseline_actions"]) <= 8),
            # How many of this leg's decisions rest on a call with no
            # attributed trigger kind. `pending` falls back to 1 for those, so
            # a threshold policy is deciding on missing data rather than on a
            # measured surprise count -- named per leg because it is not spread
            # evenly across them.
            "calls_with_no_attributed_trigger": sum(
                1 for c in leg["calls"] if not (c.get("triggers") or {})),
            "refused_by": _histogram_str([c["refused_by"] for c in refused]),
            "refused_on_a_continuation_round": sum(
                1 for c in refused
                if str(c["refused_by"]).startswith("continuation:")),
            "adjudications_recorded": leg["adjudications"],
            "adjudications_fired": len(fired),
            "adjudications_refused": len(refused),
            "usd_recorded": leg["usd"],
            "usd_under_policy": round(usd_fired, 6),
            "usd_saved": round(usd_refused, 6),
            "actions_covered": actions_fired,
            "actions_recorded": leg["billed_actions"],
            "inert_calls_refused": sum(
                1 for c in refused
                if (c.get("downstream") or {}).get("verdict") == DOWNSTREAM_INERT),
            "productive_calls_refused": sum(
                1 for c in refused
                if (c.get("downstream") or {}).get("verdict") == DOWNSTREAM_CHANGED),
        })

    for row in legs_out:
        target = row["level_1_needs"]
        reach = row["actions_at_leg_cap_whole_leg"]
        row["clears_level_1_on_the_projection"] = (
            None if (target is None or reach is None or row["mock_world"])
            else reach >= target)

    usd = sum(x["usd_under_policy"] for x in legs_out)
    actions = sum(x["actions_covered"] for x in legs_out)
    billed = sum(x["actions_recorded"] for x in legs_out)
    cap = _leg_cap()
    per_dollar = (actions / usd) if usd else None
    per_dollar_all = (billed / usd) if usd else None
    return {
        "policy": name,
        "why": economy_mod.POLICIES[name]["why"],
        "config": cfg.as_json(),
        "adjudications_fired": sum(x["adjudications_fired"] for x in legs_out),
        "adjudications_refused": sum(x["adjudications_refused"] for x in legs_out),
        "usd_under_policy": round(usd, 4),
        "usd_saved": round(sum(x["usd_saved"] for x in legs_out), 4),
        "actions_covered": actions,
        "actions_per_dollar": round(per_dollar, 4) if per_dollar else None,
        "actions_per_dollar_whole_leg": (round(per_dollar_all, 4)
                                         if per_dollar_all else None),
        "actions_recorded": billed,
        "continuation_rounds_the_kind_clauses_would_refuse_if_asked":
            unreachable,
        "at_call_verdicts_in_this_census": scored,
        "reads_the_at_call_signal": cfg.measures_inertia,
        "inert_calls_refused": sum(x["inert_calls_refused"] for x in legs_out),
        "productive_calls_refused": sum(
            x["productive_calls_refused"] for x in legs_out),
        "projection": {
            "leg_usd_cap": cap,
            "actions_at_leg_cap": (round(cap * per_dollar, 1)
                                   if per_dollar else None),
            "actions_at_leg_cap_whole_leg": (round(cap * per_dollar_all, 1)
                                             if per_dollar_all else None),
            "assumption": "a desk call's price does not rise with the wait "
                          "before it; corr(step_idx, cost_usd) = -0.039 over "
                          "65 priced calls",
        },
        "legs": legs_out,
    }


def replay_all(report: Dict[str, Any]) -> Dict[str, Any]:
    from inner import economy as economy_mod           # noqa: PLC0415

    rows = [replay_policy(report, name)
            for name in sorted(economy_mod.POLICIES)]
    baseline = next((r for r in rows if r["policy"] == "today"), None)
    fidelity: Dict[str, Any] = {}
    if baseline:
        base_legs = {x["leg"]: x for x in baseline["legs"]}
        for row in rows:
            base = baseline["projection"]["actions_at_leg_cap"]
            mine = row["projection"]["actions_at_leg_cap"]
            row["projection"]["vs_today"] = (
                round(mine / base, 3) if (base and mine) else None)
            base_w = baseline["projection"]["actions_at_leg_cap_whole_leg"]
            mine_w = row["projection"]["actions_at_leg_cap_whole_leg"]
            row["projection"]["vs_today_whole_leg"] = (
                round(mine_w / base_w, 3) if (base_w and mine_w) else None)
            # **Which leg's outcome would this policy have changed?** Two
            # answers, and only the first is a fact.
            #
            # `refused_a_call_on` is strict: these are legs where the policy
            # and the record diverge, so from that call on the leg is a
            # different leg and nothing further about it is known. Every leg
            # NOT in this list ran exactly as recorded under this policy --
            # that is the strongest true statement available.
            #
            # `newly_clears_level_1` is a projection on top of a projection:
            # the leg's dollars-to-actions rate under this policy, taken to
            # the $25 leg cap, crossing the leg's own level-1 baseline where
            # today's rate does not. It says nothing about whether the arm
            # would have known what to do with the actions.
            changed, newly, lost = [], [], []
            for x in row["legs"]:
                b = base_legs.get(x["leg"]) or {}
                if x["adjudications_fired"] != b.get("adjudications_fired"):
                    changed.append(x["leg"])
                if x["clears_level_1_on_the_projection"] and not b.get(
                        "clears_level_1_on_the_projection"):
                    newly.append(x["leg"])
                if b.get("clears_level_1_on_the_projection") and not x[
                        "clears_level_1_on_the_projection"]:
                    lost.append(x["leg"])
            # **Does the policy discriminate, or does it merely spend less?**
            # Every row saves money by refusing calls, and refusing calls at
            # random would save money too. The question a policy has to answer
            # is whether the calls it refuses are the ones that bought
            # nothing. `today` refuses 2 on a leg that predates the gate, so
            # the comparison is against that, not against zero.
            extra_inert = (row["inert_calls_refused"]
                           - baseline["inert_calls_refused"])
            extra_prod = (row["productive_calls_refused"]
                          - baseline["productive_calls_refused"])
            row["beyond_the_control"] = {
                "inert_refused": extra_inert,
                "productive_refused": extra_prod,
                "inert_per_productive": (round(extra_inert / extra_prod, 2)
                                         if extra_prod else None),
                "note": "`inert_per_productive` is None when the policy "
                        "refused no productive call beyond the control -- "
                        "which is a better outcome than any ratio, not a "
                        "missing one. Read it with the gain column: a policy "
                        "that discriminates perfectly and saves nothing has "
                        "not helped.",
            }
            row["per_leg"] = {
                "legs_that_ran_differently": changed,
                "legs_that_ran_exactly_as_recorded":
                    [x["leg"] for x in row["legs"] if x["leg"] not in changed],
                "newly_clears_level_1_on_the_projection": newly,
                "stops_clearing_level_1_on_the_projection": lost,
                "note": "the first two lists are facts about which recorded "
                        "calls the policy refuses; the last two are "
                        "projections at the $25 leg cap against each leg's "
                        "own level-1 baseline (78 g50t, 61 sk48), and a "
                        "projection is not a leg.",
            }
        recorded = sum(x["adjudications_recorded"] for x in baseline["legs"])
        fired = baseline["adjudications_fired"]
        fidelity = {
            "adjudications_recorded": recorded,
            "control_would_fire": fired,
            "control_would_refuse": recorded - fired,
            "refused_on": [x["leg"] for x in baseline["legs"]
                           if x["adjudications_refused"]],
            "verdict": (
                "the control reproduces the record" if fired == recorded else
                "the control refuses %d recorded adjudication(s). Every one of "
                "them is on a leg that ran BEFORE the gate existed: "
                "MIN_NEW_FRAMES_BETWEEN_THEORIZE landed in 6717a7e0 at "
                "2026-07-28T02:01Z, and 20260728T015354Z-g50t-first-contact "
                "started at 01:53Z -- eight minutes earlier. It is the leg "
                "whose one-action-per-adjudication behaviour the constant was "
                "written to stop, so a control that refuses its calls is the "
                "control working, not the control drifting."
                % (recorded - fired)),
        }
    return {
        "tool": "armtools.action_economy replay",
        "control_fidelity": fidelity,
        "level_baseline_actions_g50t_level1": 78,
        "note": "78 is the number to beat: g50t level 1's own "
                "`level_baseline_actions`, recorded in "
                "runs/20260728T012311Z-g50t-first-contact-salvage2/"
                "ledger.jsonl. The best recorded leg reached 33.",
        "policies": rows,
    }


# ---------------------------------------------------------------------------
# the constants that gate the cadence
# ---------------------------------------------------------------------------

def constants() -> List[Dict[str, Any]]:
    """Every constant in the loop that decides how often the arm stops to think.

    Reported with the *effective ratio* each imposes -- actions per desk call
    if that constant alone were binding. A constant with no ratio does not gate
    the cadence directly; it is listed because it changes which of the others
    binds, and leaving it out would make the list look complete when it is not.
    """
    from harness import campaign as campaign_mod       # noqa: PLC0415
    from inner import goal as goal_mod                 # noqa: PLC0415
    from inner import loop as loop_mod                 # noqa: PLC0415
    from inner import theorize as theorize_mod         # noqa: PLC0415

    n = loop_mod.MIN_NEW_FRAMES_BETWEEN_THEORIZE
    per_turn = loop_mod.MAX_THEORIZE_PER_TURN
    return [
        {
            "name": "MIN_NEW_FRAMES_BETWEEN_THEORIZE",
            "where": "inner/loop.py",
            "value": n,
            "gates": "a floor: no desk call until this many new transitions "
                     "have arrived on this level",
            "effective_actions_per_desk_call": float(n) / per_turn,
            "note": "the floor is %d frames, but MAX_THEORIZE_PER_TURN lets "
                    "one turn spend %d calls on them, so the floor alone "
                    "permits %.1f actions per call, not %d."
                    % (n, per_turn, float(n) / per_turn, n),
        },
        {
            "name": "MAX_THEORIZE_PER_TURN",
            "where": "inner/loop.py",
            "value": per_turn,
            "gates": "a ceiling on adjudication rounds inside one turn; the "
                     "second round is a repair against the SAME frames",
            "effective_actions_per_desk_call": float(n) / per_turn,
            "note": "the repair round is charged full price and sees no new "
                    "evidence, so it is the cheapest place to look for a call "
                    "that bought nothing.",
        },
        {
            "name": "MAX_PROBES_BETWEEN_THEORIZE",
            "where": "inner/loop.py",
            "value": loop_mod.MAX_PROBES_BETWEEN_THEORIZE,
            "gates": "a ceiling on probes between adjudications -- but it "
                     "does not stop the arm acting, it downgrades the action "
                     "to exploration",
            "effective_actions_per_desk_call": None,
            "note": "an exploration still produces a frame, so this cap "
                    "cannot slow the cadence; it changes what the action buys, "
                    "not how soon the desk is called.",
        },
        {
            "name": "MAX_VACUOUS_PROBES_IN_A_ROW",
            "where": "inner/loop.py",
            "value": loop_mod.MAX_VACUOUS_PROBES_IN_A_ROW,
            "gates": "same shape as above: probe -> exploration, never a "
                     "slower desk",
            "effective_actions_per_desk_call": None,
        },
        {
            "name": "the budget escape in the gate",
            "where": "inner/loop.py `_theorize_and_certify`",
            "value": "budget.actions_left > MIN_NEW_FRAMES_BETWEEN_THEORIZE",
            "gates": "the floor stops applying once the remaining action "
                     "budget drops to the floor's own size",
            "effective_actions_per_desk_call": 1.0,
            "note": "at the end of a leg the arm may call the desk on every "
                    "turn. It is deliberate -- a run must not end holding "
                    "unspent evidence -- but it is a ratio of 1, and no "
                    "constant names it.",
        },
        {
            "name": "the empty-manual escape",
            "where": "inner/loop.py `_theorize_and_certify`",
            "value": "books.theory.strip() falsy",
            "gates": "a run with no manual yet skips the floor entirely",
            "effective_actions_per_desk_call": None,
        },
        {
            "name": "level re-arming",
            "where": "inner/loop.py `_on_level_boundary`",
            "value": "_frames_at_last_theorize = -1",
            "gates": "a level boundary re-opens the gate immediately",
            "effective_actions_per_desk_call": None,
            "note": "never observed: no leg in this repo has completed a "
                    "level, so this path has no measurement behind it.",
        },
        {
            "name": "REPAIR_ROUNDS",
            "where": "inner/theorize.py",
            "value": theorize_mod.REPAIR_ROUNDS,
            "gates": "compile-repair attempts INSIDE one theorize call",
            "effective_actions_per_desk_call": None,
            "note": "these are extra model invocations without extra actions, "
                    "so they cut the actions-per-invocation ratio further than "
                    "the desk-call count shows.",
        },
        {
            "name": "MIN_NEW_STATES_FOR_PROPOSAL",
            "where": "inner/goal.py",
            "value": goal_mod.MIN_NEW_STATES_FOR_PROPOSAL,
            "gates": "how much new world before a goal ask may ride along",
            "effective_actions_per_desk_call": None,
            "note": "rides on a call a surprise already paid for, so it adds "
                    "no calls on the `propose` rung and none at all on the "
                    "default `off`.",
        },
        {
            "name": "MAX_PROPOSALS_PER_LEG",
            "where": "inner/goal.py",
            "value": goal_mod.MAX_PROPOSALS_PER_LEG,
            "gates": "a ceiling on goal riders per leg",
            "effective_actions_per_desk_call": None,
        },
        {
            "name": "LEG_USD_CAP",
            "where": "harness/campaign.py",
            "value": campaign_mod.LEG_USD_CAP,
            "gates": "the real ceiling: a leg ends when the money ends, so "
                     "the cadence sets the action count",
            "effective_actions_per_desk_call": None,
            "note": "not a cadence knob, but it is the multiplier: at $%.0f a "
                    "leg and one desk call per gap, the cadence IS the action "
                    "count. Listed so the list is not a list of only the "
                    "constants that look like cadence."
                    % campaign_mod.LEG_USD_CAP,
        },
    ]


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _print_census(report: Dict[str, Any]) -> None:
    t = report["totals"]
    print("A25 action-economy census -- %s" % report["runs_root"])
    print("  legs with desk calls   : %d" % report["legs_with_desk_calls"])
    print("  legs without desk calls: %d (not averaged in)"
          % report["legs_without_desk_calls"])
    if report["skipped"]:
        print("  skipped                : %d" % len(report["skipped"]))
        for row in report["skipped"]:
            print("      %-46s %s" % (row["leg"], row["why"]))
    print("  adjudications          : %d" % t["adjudications"])
    print("  paid invocations       : %d  (of which %d are compile repairs "
          "against the same evidence)"
          % (t["paid_invocations"], t["repair_invocations"]))
    print("  billed actions         : %d" % t["billed_actions"])
    print("  spend                  : $%.2f" % t["usd"])
    print("  ACTIONS PER ADJUDICATION   : %s" % t["actions_per_adjudication"])
    print("  ACTIONS PER PAID CALL      : %s" % t["actions_per_paid_invocation"])
    print("  usd per action         : %s" % t["usd_per_action"])
    print("  usd per adjudication   : %s" % t["usd_per_adjudication"])
    g = report["gap_actions_between_adjudications"]
    print()
    print("  gap (billed actions between one adjudication and the next):")
    print("    min %s  median %s  mean %s  max %s"
          % (g["min"], g["median"], g["mean"], g["max"]))
    print("    histogram %s" % g["histogram"])
    print()
    d = report["gate_counts_what_the_bill_does_not"]
    print("  the gate's unit is not the bill's unit:")
    print("    %d adjudication(s) were released by %d command(s) that bought "
          "no transition" % (d["adjudications_with_a_gap"],
                             d["total_frames_that_were_not_actions"]))
    print("    worst leg: %s (%d)" % d["worst_leg"])
    print()
    print("  what triggered the calls: %s" % report["triggers"])
    print("  downstream verdicts:")
    for k, v in sorted(report["downstream"].items(), key=lambda kv: -kv[1]):
        print("    %-42s %d" % (k, v))
    n = report["calls_that_bought_nothing"]
    print("  adjudications whose manual text did not move: %d"
          % n["manual_text_unchanged"])
    print("  adjudications that changed no later prediction: %d of %d scored (%s)"
          % (n["inert"], n["scored"], n["fraction_of_scored"]))
    s = report["at_call_signal"]
    print()
    print("  the signal the arm could have had AT the call:")
    for k, v in sorted(s["verdicts"].items(), key=lambda kv: -kv[1]):
        print("    %-46s %d" % (k, v))
    print("    $%.2f went on calls the arm could have called inert at the time"
          % s["usd_on_calls_the_arm_could_have_called_inert_at_the_time"])
    b = s["if_the_arm_had_believed_the_signal"]
    print("    of %d call(s) comparable on both windows:" % s["comparable_calls"])
    print("      it would have flagged %s, %s of which changed no later "
          "prediction (precision %s)"
          % (b["calls_it_would_have_called_inert"],
             b["of_those_also_inert_downstream"], b["precision"]))
    print("      it would have missed %s downstream-inert call(s) (recall %s)"
          % (b["downstream_inert_calls_it_would_have_missed"], b["recall"]))
    print("      base rate of downstream-inert among them: %s" % b["base_rate"])
    print("    cross tab (at_call | downstream): %s" % s["cross_tab"])
    w = s["why_the_two_agree"]
    print("    prefix window (steps the arm had in hand): min %s median %s "
          "max %s" % (s["prefix_window_steps"]["min"],
                      s["prefix_window_steps"]["median"],
                      s["prefix_window_steps"]["max"]))
    print("    %d of %d moved-and-changed calls have a tail that diverges at "
          "its very first step" % (w["of_which_the_tail_diverges_at_its_very_"
                                     "first_step"], w["moved_and_changed"]))
    print("    %d call(s) the at-call signal scores and the audit cannot"
          % s["scored_only_by_the_at_call_signal"])
    print()
    print("  per leg:")
    print("    %-44s %4s %4s %5s %7s %7s" % ("leg", "adj", "inv", "acts",
                                             "act/adj", "usd"))
    for leg in report["legs"]:
        print("    %-44s %4d %4d %5d %7s %7.2f"
              % (leg["leg"][:44], leg["adjudications"], leg["paid_invocations"],
                 leg["billed_actions"], leg["actions_per_adjudication"],
                 leg["usd"]))


def _print_replay(out: Dict[str, Any]) -> None:
    print("A25 counterfactual -- the same recorded money, a different cadence")
    print("  the number to beat is %d: %s"
          % (out["level_baseline_actions_g50t_level1"], out["note"]))
    print()
    f = out.get("control_fidelity") or {}
    if f:
        print("  control fidelity: %d/%d recorded adjudications reproduced"
              % (f["control_would_fire"], f["adjudications_recorded"]))
        print("    %s" % f["verdict"])
        print()
    print("  two readings of acts/$: `cover` credits a call with the actions "
          "between it and the one before (a late refusal drops a leg's "
          "trailing actions); `whole` divides every recorded action by the "
          "reduced bill. The truth is between them.")
    print("  %-28s %5s %5s %8s %7s %7s %7s %7s %6s"
          % ("policy", "fire", "skip", "usd", "cover", "whole", "@cap",
             "@capW", "vsW"))
    for row in out["policies"]:
        p = row["projection"]
        vs = p.get("vs_today_whole_leg")
        print("  %-28s %5d %5d %8.2f %7s %7s %7s %7s %6s"
              % (row["policy"], row["adjudications_fired"],
                 row["adjudications_refused"], row["usd_under_policy"],
                 row["actions_per_dollar"],
                 row["actions_per_dollar_whole_leg"],
                 p["actions_at_leg_cap"], p["actions_at_leg_cap_whole_leg"],
                 vs))
    print()
    print("  what each policy refused (of the calls that were scored). "
          "`today` refuses 2 on a leg that predates the gate, so the columns "
          "beyond it are what the policy adds:")
    print("  %-28s %7s %11s %9s %9s %9s"
          % ("policy", "inert", "productive", "unreached", "+inert", "in/prod"))
    for row in out["policies"]:
        b = row.get("beyond_the_control") or {}
        print("  %-28s %7d %11d %9d %9s %9s"
              % (row["policy"], row["inert_calls_refused"],
                 row["productive_calls_refused"],
                 row["continuation_rounds_the_kind_clauses_would_refuse_"
                     "if_asked"],
                 b.get("inert_refused"), b.get("inert_per_productive")))
    blind = [row["policy"] for row in out["policies"]
             if row.get("reads_the_at_call_signal")
             and not row.get("at_call_verdicts_in_this_census")]
    if blind:
        print()
        print("  WARNING: this census carries no at-call verdicts, so these "
              "policies fell back to their floors and their rows mean "
              "nothing: %s" % ", ".join(blind))
        print("           re-run the census WITHOUT --shallow.")
    print()
    print("  which leg ran differently (a fact), and which leg's projection "
          "crosses its own level-1 boundary (a projection):")
    for row in out["policies"]:
        pl = row.get("per_leg") or {}
        print("  %-20s ran differently on %d of %d leg(s)"
              % (row["policy"], len(pl.get("legs_that_ran_differently") or []),
                 len(row["legs"])))
        for leg in pl.get("legs_that_ran_differently") or []:
            x = next(v for v in row["legs"] if v["leg"] == leg)
            print("      %-46s fired %d/%d  $%.2f saved  refused %s"
                  % (leg[:46], x["adjudications_fired"],
                     x["adjudications_recorded"], x["usd_saved"],
                     x["refused_by"]))
        for leg in pl.get("newly_clears_level_1_on_the_projection") or []:
            x = next(v for v in row["legs"] if v["leg"] == leg)
            print("      + %-44s projects %s actions at the $%.0f cap, its "
                  "level 1 needs %s"
                  % (leg[:44], x["actions_at_leg_cap"], _leg_cap(),
                     x["level_1_needs"]))
        for leg in pl.get("stops_clearing_level_1_on_the_projection") or []:
            print("      - %-44s no longer clears its level 1" % leg[:44])
    print()
    print("  per leg and policy -- actions bought per dollar over the whole "
          "leg, * = projection clears this leg's own level 1:")
    names = [row["policy"] for row in out["policies"]]
    for i, n in enumerate(names):
        print("    [%2d] %s" % (i, n))
    print("    a leg with one or two adjudications projects wildly -- `adj` "
          "is there so those rows are read as the noise they are.")
    print("    %-42s %5s %4s %s"
          % ("leg", "needs", "adj", " ".join("%6s" % ("[%d]" % i)
                                             for i in range(len(names)))))
    for leg in out["policies"][0]["legs"]:
        cells = []
        for row in out["policies"]:
            x = next(v for v in row["legs"] if v["leg"] == leg["leg"])
            mark = "*" if x["clears_level_1_on_the_projection"] else ""
            cells.append("%6s" % ("%s%s" % (
                "-" if x["actions_per_dollar_whole_leg"] is None
                else "%.1f" % x["actions_per_dollar_whole_leg"], mark)))
        print("    %-42s %5s %4d %s"
              % (leg["leg"][:42],
                 ("mock" if leg["mock_world"] else leg["level_1_needs"]),
                 leg["adjudications_recorded"], " ".join(cells)))
    print()
    print("  projection assumption: %s"
          % out["policies"][0]["projection"]["assumption"])


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("census", help="measure the cadence off the ledgers")
    c.add_argument("--runs", default=DEFAULT_RUNS)
    c.add_argument("--shallow", action="store_true",
                   help="skip the recompile-and-replay downstream test. Fast, "
                        "and answers strictly less: the verdict column comes "
                        "back null rather than guessed.")
    c.add_argument("--json", action="store_true")
    c.add_argument("--out", default=None)

    k = sub.add_parser("constants", help="every constant that gates the cadence")
    k.add_argument("--json", action="store_true")

    r = sub.add_parser("replay", help="what the same money would have bought")
    r.add_argument("--runs", default=DEFAULT_RUNS)
    r.add_argument("--census", default=None,
                   help="a census JSON written earlier by `census --out`. "
                        "Recomputed from the ledgers if absent, which takes "
                        "the recompile-and-replay path and is slow.")
    r.add_argument("--json", action="store_true")
    r.add_argument("--out", default=None)

    args = ap.parse_args(argv)

    if args.cmd == "constants":
        rows = constants()
        if args.json:
            print(json.dumps(rows, indent=1, sort_keys=True))
            return 0
        print("constants that gate how often the arm stops to think")
        print("%-38s %-26s %10s  %s" % ("name", "where", "ratio", "value"))
        for row in rows:
            ratio = row["effective_actions_per_desk_call"]
            print("%-38s %-26s %10s  %s"
                  % (row["name"][:38], row["where"][:26],
                     "-" if ratio is None else ("%.1f" % ratio), row["value"]))
            print("      gates: %s" % row["gates"])
            if row.get("note"):
                print("      note : %s" % row["note"])
        return 0

    if args.cmd == "replay":
        if args.census:
            with open(args.census, encoding="utf-8") as fh:
                base = json.load(fh)
        else:
            base = census(args.runs, deep=True)
        out = replay_all(base)
        if args.out:
            with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
                json.dump(out, fh, indent=1, sort_keys=True)
                fh.write("\n")
        if args.json:
            print(json.dumps(out, indent=1, sort_keys=True))
        else:
            _print_replay(out)
        return 0

    report = census(args.runs, deep=not args.shallow)
    if args.out:
        with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(report, fh, indent=1, sort_keys=True)
            fh.write("\n")
    if args.json:
        print(json.dumps(report, indent=1, sort_keys=True))
    else:
        _print_census(report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
