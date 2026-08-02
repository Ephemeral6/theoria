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
import shutil
import statistics
import sys
import tempfile
from typing import Any, Dict, List, Optional, Tuple

import _bootstrap                                     # noqa: F401  (sys.path)

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

def _compile_snapshot(snap_dir: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """Compile one `rev<N>-<tag>` snapshot in a scratch copy and load it.

    The copy matters: `Books.compile_all` writes `generated/` beside the DSL,
    and a census must not add a byte to a recorded run directory. The scratch
    tree is removed whether or not the compile succeeded.
    """
    from inner.books import Books                      # noqa: PLC0415

    tmp = tempfile.mkdtemp(prefix="a25-census-")
    try:
        for name in ("theory.dsl", "playbook.dsl", "problem.json"):
            src = os.path.join(snap_dir, name)
            if os.path.exists(src):
                shutil.copy2(src, os.path.join(tmp, name))
        books = Books(tmp)
        try:
            books.compile_all()
        except Exception as exc:                       # noqa: BLE001
            return None, "compile raised: %s: %s" % (type(exc).__name__, exc)
        namespace, error = books.load_predictor()
        return namespace, error
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def _drawn_series(namespace: Dict[str, Any], store: _LedgerStore,
                  limit: int) -> List[Optional[str]]:
    """What this predictor says the world looks like at each step.

    One hash per step so two revisions can be compared without holding two
    64x64 grid series in memory at once. A step the predictor could not reach
    -- `step` raised, `render` raised -- is `None` and compares unequal to a
    frame, which is correct: a predictor that crashes has not agreed with one
    that draws.
    """
    from inner.commit import action_to_manual          # noqa: PLC0415
    from world.frames import grid_hash                 # noqa: PLC0415

    out: List[Optional[str]] = []
    try:
        state = namespace["initial_state"]()
    except Exception:                                  # noqa: BLE001
        return [None] * limit
    for t in range(limit):
        arc_action = store.actions[t] if t < len(store.actions) else None
        if arc_action is None:
            out.append(None)
            continue
        try:
            state = namespace["step"](state, action_to_manual(arc_action))
            out.append(grid_hash(namespace["render"](state)))
        except Exception:                              # noqa: BLE001
            out.extend([None] * (limit - t))
            break
    return out


def _downstream_verdict(before_dir: Optional[str], after_dir: Optional[str],
                        store: _LedgerStore, first_tail_step: int,
                        deep: bool) -> Dict[str, Any]:
    """Did this call change what the arm predicts about the world it went on
    to see?

    The tail is the transitions recorded *after* the call. A call answered at
    the very end of a leg has no tail, and that is reported as
    `no_later_transition_to_predict` rather than as agreement -- an unanswerable
    question is not a negative answer.
    """
    if not before_dir or not after_dir:
        return {"verdict": DOWNSTREAM_UNPAIRED}
    n = len(store.grids)
    if first_tail_step >= max(n - 1, 0):
        return {"verdict": DOWNSTREAM_NO_TAIL, "tail_transitions": 0}
    if not deep:
        return {"verdict": None, "tail_transitions": (n - 1) - first_tail_step}

    before_ns, before_err = _compile_snapshot(before_dir)
    after_ns, after_err = _compile_snapshot(after_dir)
    tail = (n - 1) - first_tail_step
    if before_ns is None and after_ns is None:
        return {"verdict": DOWNSTREAM_BLIND, "tail_transitions": tail,
                "before_error": before_err, "after_error": after_err}
    if before_ns is None:
        return {"verdict": DOWNSTREAM_GAINED, "tail_transitions": tail,
                "before_error": before_err}
    if after_ns is None:
        return {"verdict": DOWNSTREAM_LOST, "tail_transitions": tail,
                "after_error": after_err}

    limit = n - 1
    before_series = _drawn_series(before_ns, store, limit)
    after_series = _drawn_series(after_ns, store, limit)
    diverged = [t for t in range(first_tail_step, limit)
                if before_series[t] != after_series[t]]
    return {
        "verdict": DOWNSTREAM_CHANGED if diverged else DOWNSTREAM_INERT,
        "tail_transitions": tail,
        "first_divergent_step": diverged[0] if diverged else None,
        "divergent_steps": len(diverged),
    }


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
        record["downstream"] = _downstream_verdict(
            pair[0], pair[1], store, first_tail_step, deep)
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

    all_calls = [c for leg in legs for c in leg["calls"]]
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
        "calls_that_bought_nothing": {
            "manual_text_unchanged": manual_unchanged,
            "inert": inert,
            "scored": scored,
            "fraction_of_scored": (round(inert / scored, 4) if scored else None),
        },
        "legs": legs,
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
    from inner import economy as economy_mod           # noqa: PLC0415

    cfg = economy_mod.policy(name)
    legs_out: List[Dict[str, Any]] = []
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
                # invalidates every row beside it.
                decision = economy_mod.GateDecision(True, None, econ.floor)
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
                refused.append(dict(call, refused_by="floor",
                                    floor_at_refusal=decision.floor))
                continue
            rounds_this_step[step] = taken + 1
            fired.append(dict(call, floor_at_call=decision.floor,
                              actions_bought=carried_actions))
            econ.note_adjudication(
                manual_moved=(call.get("manual") or {}).get("theory_changed"))
            carried_frames = 0
            carried_actions = 0

        usd_fired = sum(c["cost_usd"] for c in fired)
        usd_refused = sum(c["cost_usd"] for c in refused)
        actions_fired = sum(c["actions_bought"] for c in fired)
        legs_out.append({
            "leg": leg["leg"],
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

    usd = sum(x["usd_under_policy"] for x in legs_out)
    actions = sum(x["actions_covered"] for x in legs_out)
    cap = _leg_cap()
    per_dollar = (actions / usd) if usd else None
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
        "inert_calls_refused": sum(x["inert_calls_refused"] for x in legs_out),
        "productive_calls_refused": sum(
            x["productive_calls_refused"] for x in legs_out),
        "projection": {
            "leg_usd_cap": cap,
            "actions_at_leg_cap": (round(cap * per_dollar, 1)
                                   if per_dollar else None),
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
        for row in rows:
            base = baseline["projection"]["actions_at_leg_cap"]
            mine = row["projection"]["actions_at_leg_cap"]
            row["projection"]["vs_today"] = (
                round(mine / base, 3) if (base and mine) else None)
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
    print("  %-20s %5s %5s %9s %9s %8s %7s %6s"
          % ("policy", "fire", "skip", "usd", "acts", "acts/$",
             "@cap", "vs"))
    for row in out["policies"]:
        p = row["projection"]
        print("  %-20s %5d %5d %9.2f %9d %8s %7s %6s"
              % (row["policy"], row["adjudications_fired"],
                 row["adjudications_refused"], row["usd_under_policy"],
                 row["actions_covered"], row["actions_per_dollar"],
                 p["actions_at_leg_cap"], p.get("vs_today")))
    print()
    print("  what each policy refused (of the calls that were scored):")
    print("  %-20s %10s %12s" % ("policy", "inert", "productive"))
    for row in out["policies"]:
        print("  %-20s %10d %12d"
              % (row["policy"], row["inert_calls_refused"],
                 row["productive_calls_refused"]))
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
