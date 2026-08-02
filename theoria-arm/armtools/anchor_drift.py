"""The drift triple, computed offline for any archived leg, on any anchor.

`runs/20260801T0900Z-R2-frontier-by-generation/MEASUREMENT.json` reported that
35 of 52 probes across the four 2026-07-31 legs designed their frontier around a
frame the world had already left, and that **all 35 came back off-frontier**.
The number costs nothing to take -- two hashes, no action, no model call, no
network -- and nothing in the arm takes it, because keeping `--frontier
ablation` byte-identical means the anchor block is written only when a switch is
on. `GAPS.md` GAP R2-1 named that trade: *the leg most likely to be drifting is
the one that cannot report it.* R3 paid the other half forward (`anchor.jsonl`
is written by every leg from now on); this module pays it **backward**, over
legs that are already on disk and will never run again.

## The measurement

Every hypothesis `inner/probe.build_hypotheses` builds is a successor of the
*manual's* rolled-forward state, and `inert` -- "this action does nothing" -- is
that state rendered unchanged. So `predictions["inert"]` **is** the frontier's
anchor. The frame the world was actually showing when the probe was sent is the
`before_hash` of the trace step that carries the probe's id as its `note`. The
triple is:

    probes                    -- designs that got a result
    drifted                   -- of those, anchor != the world's frame
    drifted_and_off_frontier  -- of those, the world's answer was in no hypothesis

## Two paths to one number, and exactly how far apart they are

R2 read `before_hash` out of the trace row as recorded. This module does not:
it hands `trace.jsonl` to `world.frames.load_store`, which never reads that
field and **recomputes** the anchor from the frames themselves
(`FrameStore.add` assigns `before_hash = grid_hash(self.current)`
unconditionally). Where they could disagree this says so
(`recorded_vs_recomputed_disagreements`) instead of preferring one silently.

**The gap is narrower than "independent" would suggest, and the record should
say which gap it is.** The recompute is independent of *R2's reader* -- that one
shares no line of code with this -- but not of the *recorder*: it runs the very
`FrameStore.add`/`current` that assigned the field at run time, over the frames
in the same file. So agreement establishes that the trace is internally
consistent and that R2's join and arithmetic were right. It does **not**
establish that `current` -- "the last step whose cascade was non-empty" -- is
the right notion of "the frame the world was showing". If that reading is
wrong, both paths are wrong together and nothing here can see it.

## Absence is absence

`theoria-arm/.gitignore` excludes `runs/*/trace.jsonl`, so in any clone the
frames are simply not there. A leg without its trace is **refused by name** and
measured `null` -- never `0`. A check that has only ever been seen to say "no
drift" because it could not look is not a check. `measure_frontier.py` is the
same shape and this follows it.

Offline. Reads `probes.jsonl` (tracked) and `trace.jsonl` (gitignored). No
model call, no ARC action, no network. Development-pile games only, by name --
never by glob, because a live round may be writing into `runs/` alongside this.

    python -m armtools.anchor_drift [--legs L ...] [--legs-root DIR]
                                    [--out PATH] [--crosscheck MEASUREMENT.json]
"""

import argparse
import json
import os
import sys
from typing import Any, Dict, List, Optional, Sequence

import _bootstrap                                     # noqa: F401  (sys.path)

from world.frames import FrameStore, Step, grid_hash, load_store

HERE = os.path.dirname(os.path.abspath(__file__))
ARM = os.path.dirname(HERE)
RUNS = os.path.join(ARM, "runs")

#: The four legs R2 measured. Recomputing these is the only way to know this
#: module measures the same thing R2 did rather than something else that also
#: produces integers.
R2_LEGS = (
    "20260731T1240Z-A3-level2-carried",
    "20260731T1310Z-A3-level2-carried-r2",
    "20260731T1430Z-A3-level2-carried-r3",
    "20260731T1500Z-A3-sk48-carried-l1",
)

#: The four legs that have never had an anchor number taken at all.
R1_LEGS = (
    "20260731T231654Z-R1-g50t-a",
    "20260731T231654Z-R1-sk48-b",
    "20260801T001851Z-R1b-g50t-a",
    "20260801T001851Z-R1b-sk48-b",
)

DEFAULT_LEGS = R1_LEGS + R2_LEGS

TRIPLE_KEYS = ("probes", "drifted", "drifted_and_off_frontier")

MEASURED = "measured"
NO_PROBES = "no probes.jsonl here; nothing measured"
NO_TRACE = ("trace.jsonl is gitignored and absent here; nothing measured "
            "(this is the normal case in a clone -- it is an absence, not a "
            "drift of zero)")
NO_LEG = "no such directory; nothing measured"


def _absent_triple() -> Dict[str, Optional[int]]:
    return {key: None for key in TRIPLE_KEYS}


def _read_jsonl(path: str) -> List[Dict[str, Any]]:
    with open(path, encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


# --------------------------------------------------------------------------
# the measurement
# --------------------------------------------------------------------------

def measure_leg(leg_dir: str) -> Dict[str, Any]:
    """One archived leg's drift triple, or a stated refusal.

    Never returns a zero it did not measure: every early return carries a
    `status` naming what was missing and a triple of `None`.
    """
    leg = os.path.basename(os.path.normpath(leg_dir))
    probes_path = os.path.join(leg_dir, "probes.jsonl")
    trace_path = os.path.join(leg_dir, "trace.jsonl")

    if not os.path.isdir(leg_dir):
        return {"leg": leg, "status": NO_LEG, "trace_available": False,
                "triple": _absent_triple(), "probes": []}
    if not os.path.exists(probes_path):
        return {"leg": leg, "status": NO_PROBES, "trace_available": False,
                "triple": _absent_triple(), "probes": []}
    if not os.path.exists(trace_path):
        return {"leg": leg, "status": NO_TRACE, "trace_available": False,
                "triple": _absent_triple(), "probes": []}

    probes = _read_jsonl(probes_path)
    designs = {r["probe_id"]: r for r in probes if r.get("phase") == "design"}
    results = {r["probe_id"]: r for r in probes if r.get("phase") == "result"}

    # The recorded field, kept only to be disagreed with. `load_store` drops it
    # and rebuilds the anchor from the frames; this is the other path.
    recorded = {r["step_idx"]: r.get("before_hash") for r in
                _read_jsonl(trace_path)}
    store = load_store(trace_path)

    by_note: Dict[str, Any] = {}
    duplicates: List[str] = []
    for step in store.steps:
        if not step.note:
            continue
        if step.note in by_note and step.note in designs:
            duplicates.append(step.note)
        by_note[step.note] = step

    rows: List[Dict[str, Any]] = []
    disagreements: List[Dict[str, Any]] = []
    for probe_id, design in sorted(designs.items()):
        if results.get(probe_id) is None:
            continue                              # designed, never resolved
        result = results[probe_id]
        predictions = design.get("predictions") or {}
        observed = result.get("observed")
        anchor_hash = predictions.get("inert")
        step = by_note.get(probe_id)

        world_hash = step.before_hash if step is not None else None
        if step is not None:
            was_recorded = recorded.get(step.step_idx)
            if was_recorded != world_hash:
                disagreements.append({"probe_id": probe_id,
                                      "step_idx": step.step_idx,
                                      "recorded": was_recorded,
                                      "recomputed": world_hash})

        # `None` is not `False`. A probe whose step the trace does not carry,
        # or whose frontier has no `inert`, has an *unknown* anchor, and an
        # unknown anchor is not a drift. A probe whose id two trace steps both
        # claim is the same case: `by_note` keeps the last of them, and which
        # of the two the arm meant is not something this can know.
        if step is None or anchor_hash is None or probe_id in duplicates:
            drifted: Optional[bool] = None
        else:
            drifted = (anchor_hash != world_hash)

        off_frontier = observed not in set(predictions.values())
        rows.append({
            "probe_id": probe_id,
            "step_idx": design.get("step_idx"),
            "trace_step_idx": step.step_idx if step is not None else None,
            "action": design.get("action"),
            "anchor_hash": anchor_hash,
            "world_before_hash": world_hash,
            "drifted": drifted,
            "observed": observed,
            "off_frontier": off_frontier,
            "n_hypotheses": len(predictions),
            "frontier_width_distinct": len(set(predictions.values())),
        })

    drifted_rows = [r for r in rows if r["drifted"] is True]
    unanswered = [r for r in rows if r["observed"] == "none"]

    # 0/0/0 reads exactly like "measured, and clean", and so does 1/0/0 when
    # that one probe's action was refused and returned no frame at all. Neither
    # is a bill of health, and the triple alone cannot say so.
    if not rows:
        note = ("no probe was designed and resolved on this leg, so the "
                "triple is empty rather than clean")
    elif len(unanswered) == len(rows):
        note = ("every resolved probe here came back with no frame "
                "(`observed: \"none\"`), so the triple counts experiments the "
                "world never answered -- it is empty rather than clean")
    elif unanswered:
        note = ("%d of %d resolved probes came back with no frame "
                "(`observed: \"none\"`); those cannot be off-frontier in any "
                "sense that means anything" % (len(unanswered), len(rows)))
    else:
        note = None

    return {
        "leg": leg,
        "status": MEASURED,
        "note": note,
        "probes_without_an_answer": len(unanswered),
        "trace_available": True,
        "triple": {
            "probes": len(rows),
            "drifted": len(drifted_rows),
            "drifted_and_off_frontier": sum(
                1 for r in drifted_rows if r["off_frontier"]),
        },
        "probes_designed": len(designs),
        "anchored_to_world": sum(1 for r in rows if r["drifted"] is False),
        "anchor_unknown": sum(1 for r in rows if r["drifted"] is None),
        "off_frontier": sum(1 for r in rows if r["off_frontier"]),
        "recorded_vs_recomputed_disagreements": disagreements,
        "duplicate_probe_notes": sorted(set(duplicates)),
        "probes": rows,
    }


def measure(legs: Sequence[str] = DEFAULT_LEGS,
            runs_root: str = RUNS) -> Dict[str, Any]:
    """The triple for each named leg, plus totals over the ones that measured.

    Totals sum the measured legs only. A refused leg contributes nothing --
    not a zero -- and is named in `refused` so the total can never be read as
    covering it.
    """
    per_leg = [measure_leg(os.path.join(runs_root, leg)) for leg in legs]
    done = [row for row in per_leg if row["status"] == MEASURED]
    refused = [{"leg": row["leg"], "status": row["status"]}
               for row in per_leg if row["status"] != MEASURED]
    totals = {key: sum(row["triple"][key] for row in done)
              for key in TRIPLE_KEYS} if done else _absent_triple()
    return {
        "legs": per_leg,
        "totals": {
            "legs_named": len(legs),
            "legs_measured": len(done),
            "legs_refused": len(refused),
            "triple": totals,
            "recorded_vs_recomputed_disagreements": sum(
                len(row["recorded_vs_recomputed_disagreements"])
                for row in done),
        },
        "refused": refused,
    }


# --------------------------------------------------------------------------
# the crosscheck against R2
# --------------------------------------------------------------------------

def crosscheck(report: Dict[str, Any], measurement_path: str) -> Dict[str, Any]:
    """Does this module reproduce `MEASUREMENT.json`, probe for probe?

    Two independently written readers of the same two files must agree on every
    row, not merely on the total -- a total can match by two errors cancelling.

    **Agreement on the intersection is not agreement**, and an earlier draft of
    this only had that. It skipped a probe the other side did not carry and
    skipped a leg this side could not measure, so `equal: true` was reachable
    while the two readers disagreed about which probes exist -- and, worse,
    while a leg named in `legs_compared` had never been opened at all (withhold
    one `trace.jsonl` and the four-leg crosscheck still said EQUAL over 52
    probes). So the row sets are compared as sets, and a leg the report refused
    is a failure of the crosscheck rather than a zero inside it.
    """
    with open(measurement_path, encoding="utf-8") as fh:
        theirs = json.load(fh)

    mine_by_leg = {row["leg"]: row for row in report["legs"]}
    their_probes = {(r["leg"], r["probe_id"]): r for r in theirs["probes"]}

    # Every leg the other side measured, this side must have measured too.
    # Otherwise the comparison is over fewer legs than it names.
    named = [row["leg"] for row in theirs["legs"]]
    not_measured = [leg for leg in named
                    if mine_by_leg.get(leg, {}).get("status") != MEASURED]

    mine_ids = {(leg, r["probe_id"]) for leg in named
                if mine_by_leg.get(leg, {}).get("status") == MEASURED
                for r in mine_by_leg[leg]["probes"]}
    their_ids = {key for key in their_probes if key[0] in set(named)}

    per_probe_diff: List[Dict[str, Any]] = []
    compared = 0
    for leg_name, leg in mine_by_leg.items():
        if leg["status"] != MEASURED:
            continue
        for row in leg["probes"]:
            other = their_probes.get((leg_name, row["probe_id"]))
            if other is None:
                continue
            compared += 1
            # R2 wrote `anchored`; the negation is this module's `drifted`.
            theirs_drifted = (None if "anchored" not in other
                              else not other["anchored"])
            if (theirs_drifted != row["drifted"]
                    or other["off_frontier"] != row["off_frontier"]
                    or other["observed"] != row["observed"]):
                per_probe_diff.append({
                    "leg": leg_name, "probe_id": row["probe_id"],
                    "mine": {"drifted": row["drifted"],
                             "off_frontier": row["off_frontier"],
                             "observed": row["observed"]},
                    "theirs": {"drifted": theirs_drifted,
                               "off_frontier": other["off_frontier"],
                               "observed": other["observed"]}})

    per_leg_diff: List[Dict[str, Any]] = []
    for other in theirs["legs"]:
        mine = mine_by_leg.get(other["leg"])
        if mine is None or mine["status"] != MEASURED:
            continue
        want = {"probes": other["probes_completed"],
                "drifted": other["anchor_drifted"]}
        got = {"probes": mine["triple"]["probes"],
               "drifted": mine["triple"]["drifted"]}
        if want != got:
            per_leg_diff.append({"leg": other["leg"],
                                 "mine": got, "theirs": want})

    mine_totals = {key: sum(mine_by_leg[leg]["triple"][key] for leg in named
                            if mine_by_leg.get(leg, {}).get("status")
                            == MEASURED)
                   for key in TRIPLE_KEYS}
    their_totals = {"probes": theirs["totals"]["probes_completed"],
                    "drifted": theirs["totals"]["anchor_drifted"],
                    "drifted_and_off_frontier":
                        theirs["totals"]["off_frontier_while_drifted"]}
    only_mine = sorted(mine_ids - their_ids)
    only_theirs = sorted(their_ids - mine_ids)
    return {
        "source": os.path.basename(measurement_path),
        "legs_named_by_the_other_reader": named,
        "legs_this_reader_could_not_measure": not_measured,
        "totals_mine": mine_totals,
        "totals_theirs": their_totals,
        "totals_equal": mine_totals == their_totals,
        "per_leg_disagreements": per_leg_diff,
        "probes_compared": compared,
        "probes_only_this_reader_has": only_mine,
        "probes_only_the_other_reader_has": only_theirs,
        "per_probe_disagreements": per_probe_diff,
        "equal": (mine_totals == their_totals and not per_leg_diff
                  and not per_probe_diff and not not_measured
                  and not only_mine and not only_theirs and compared > 0),
    }


# --------------------------------------------------------------------------
# the negative controls: legs whose drift is known before it is measured
# --------------------------------------------------------------------------

def _prefix_store(store: FrameStore, upto: int) -> FrameStore:
    """A store holding every step strictly before `upto`."""
    view = FrameStore()
    for step in store.steps:
        if step.step_idx < upto:
            view.add(step)
    return view


def _predict(hypotheses, state, action) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for hypothesis in hypotheses:
        try:
            out[hypothesis.id] = hypothesis.predict(state, action)
        except Exception:                              # noqa: BLE001
            out[hypothesis.id] = "error"
    return out


def _mispredicting_step(true_step, render, frozen_hash):
    """The manual, wrong about the one transition out of `frozen_hash`.

    Keyed on the *frame* rather than on a call counter, so it is wrong at the
    same place however many times it is called and in whatever order -- a
    counter would make the control depend on how many times `build_hypotheses`
    happened to consult the manual.

    **It is one wrong transition, not one wrong call, and the difference shows.**
    The no-op returns the frozen state, so that state is absorbing: once a roll
    reaches it, every later action is wrong too. Instrumented on the g50t manual
    at `mispredict_at=2`, the wrapper fires 3 times inside the roll-forwards and
    63 times counting the hypotheses' own `predict` calls. That is the mechanism
    under study rather than a flaw -- `inner/loop._roll_forward` is open-loop, so
    one mispredicted transition is *supposed* to carry forward -- but "wrong
    once" would be the wrong sentence and an earlier draft of this docstring
    used it.

    **What it therefore cannot be used to test.** At the frozen state every
    hypothesis that consults `step` returns the frozen frame, so the frontier
    collapses from 2 distinct predictions to 1. The drifted probes on this leg
    are off-frontier because their frontier is a point, not because their anchor
    moved. The archive's `drifted => off_frontier` implication cannot be
    confirmed here; see `GAPS.md` GAP A23-3.
    """
    def step(state, action):
        try:
            if grid_hash(render(state)) == frozen_hash:
                return state              # "this action does nothing" -- wrongly
        except Exception:                              # noqa: BLE001
            pass
        return true_step(state, action)
    return step


def synthesise_leg(out_dir: str, namespace: Dict[str, Any],
                   arc_actions: Sequence[int], *,
                   mispredict_at: Optional[int] = None,
                   cascade: int = 1) -> Dict[str, Any]:
    """Write a leg whose drift is known by construction, then let it be measured.

    The world here **is** a compiled manual: frame *t* is that manual's own
    state after the first *t* actions, rendered. The arm's manual is the same
    object, so with `mispredict_at=None` the roll-forward cannot be wrong and
    the anchor is the world's frame at every probe -- **drift 0**.

    With `mispredict_at=k` the arm's copy is wrapped so that the one transition
    out of world-frame *k* is a no-op while the world takes it. From then on
    `inner/loop._roll_forward` is replaying a state the world has left --
    **drift > 0** -- which is the failure this whole module exists to find.

    Nothing is simulated: the trace is written by `world.frames.FrameStore`,
    the frontier by `inner.probe.build_hypotheses`, and the rolled state by
    `inner.loop._roll_forward` itself.

    `cascade` pads each step with that many grids instead of one. It matters
    because a real ARC command returns 1--113 frames -- 26 of the 34 steps on
    `…-r3` are multi-frame -- and on a one-grid world every candidate reading of
    "the frame the world was showing" coincides. With `cascade > 1` the earlier
    grids of the cascade are frames the world passed *through*, and the anchor
    must still be the frame it settled on. The triple must not move; that is
    what `test_the_measurement_does_not_move_when_the_world_answers_in_a_cascade`
    asks.
    """
    from inner import loop as loop_mod                 # noqa: PLC0415
    from inner import probe as probe_beat              # noqa: PLC0415

    render = namespace["render"]
    true_step = namespace["step"]

    world = [namespace["initial_state"]()]
    for action in arc_actions:
        world.append(true_step(world[-1], ("key", int(action))))
    frames = [render(state) for state in world]

    arm_ns = dict(namespace)
    if mispredict_at is not None:
        arm_ns["step"] = _mispredicting_step(
            true_step, render, grid_hash(frames[mispredict_at]))

    def _cascade(idx):
        """The grids one command returned, settling on `frames[idx]`.

        The world passes through the frames it has already shown before landing
        on the new one, which is the shape a real cascade has: the last grid is
        the state, the earlier ones are the way there.
        """
        if cascade <= 1:
            return [frames[idx]]
        earlier = [frames[max(0, idx - n)] for n in range(cascade - 1, 0, -1)]
        return earlier + [frames[idx]]

    legal = sorted({int(a) for a in arc_actions})
    store = FrameStore()
    store.add(Step(0, "RESET", _cascade(0), status=200, state="NOT_FINISHED",
                   levels_completed=0, available_actions=legal, note=""))
    for idx, action in enumerate(arc_actions, start=1):
        store.add(Step(idx, "ACTION%d" % int(action), _cascade(idx), status=200,
                       state="NOT_FINISHED", levels_completed=0,
                       available_actions=legal, probe=True,
                       note="P-%02d" % idx))

    os.makedirs(out_dir, exist_ok=True)
    store.to_jsonl(os.path.join(out_dir, "trace.jsonl"))

    probes_path = os.path.join(out_dir, "probes.jsonl")
    written = []
    predicted = []
    with open(probes_path, "w", encoding="utf-8", newline="\n") as fh:
        for idx, action in enumerate(arc_actions, start=1):
            manual_action = ("key", int(action))
            state = loop_mod._roll_forward(                # noqa: SLF001
                arm_ns, _prefix_store(store, idx))
            predictions = _predict(probe_beat.build_hypotheses(arm_ns),
                                   state, manual_action)
            observed = grid_hash(frames[idx])
            design = {"probe_id": "P-%02d" % idx, "phase": "design",
                      "step_idx": idx, "action": int(action),
                      "rationale": "synthetic negative control",
                      "predictions": predictions,
                      "design": {"n_hypotheses": len(predictions)}}
            result = {"probe_id": "P-%02d" % idx, "phase": "result",
                      "status": 200, "observed": observed, "n_frames": 1,
                      "survived": sorted(k for k, v in predictions.items()
                                         if v == observed),
                      "refuted": sorted(k for k, v in predictions.items()
                                        if v != observed),
                      "manual_survived":
                          predictions.get("manual") == observed,
                      "verdict": "synthetic negative control"}
            for row in (design, result):
                fh.write(json.dumps(row, sort_keys=True, default=str) + "\n")
            written.append(design["probe_id"])
            predicted.append(predictions)

    return {"dir": out_dir, "probes": written,
            "mispredict_at": mispredict_at,
            "cascade": cascade,
            "world_frames_distinct": len({grid_hash(f) for f in frames}),
            "frontier_widths": sorted({len(set(p.values()))
                                       for p in predicted}),
            "n_frames": len(frames)}


def compile_manual(snapshot_dir: str, workdir: str):
    """Compile one `books/snapshots/<rev>` into a live predictor namespace."""
    import shutil                                      # noqa: PLC0415

    from inner.books import Books                      # noqa: PLC0415

    dst = os.path.join(workdir, "books")
    os.makedirs(dst, exist_ok=True)
    for fname in ("theory.dsl", "playbook.dsl", "problem.json"):
        src = os.path.join(snapshot_dir, fname)
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(dst, fname))
    books = Books(dst)
    books.compile_all()
    namespace, _err = books.load_predictor()
    return namespace


def newest_compiling_snapshot(leg_dir: str, workdir: str):
    """The newest snapshot of this leg's manual that compiles, and its name."""
    snaps = os.path.join(leg_dir, "books", "snapshots")
    if not os.path.isdir(snaps):
        return None, None
    for name in sorted(os.listdir(snaps), reverse=True):
        try:
            namespace = compile_manual(os.path.join(snaps, name),
                                       os.path.join(workdir, name))
        except Exception:                              # noqa: BLE001
            continue
        if namespace and namespace.get("render") and namespace.get("step"):
            return name, namespace
    return None, None


# --------------------------------------------------------------------------

def _render_report(payload: Dict[str, Any]) -> bytes:
    return (json.dumps(payload, indent=1, sort_keys=True, default=str)
            + "\n").encode("utf-8")


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--legs", nargs="+", default=list(DEFAULT_LEGS),
                    help="leg directory names, by name -- never a glob")
    ap.add_argument("--legs-root", default=RUNS)
    ap.add_argument("--out", default=None)
    ap.add_argument("--crosscheck", default=None,
                    help="path to R2's MEASUREMENT.json")
    args = ap.parse_args(argv)

    report = measure(args.legs, args.legs_root)
    if args.crosscheck:
        report["crosscheck"] = crosscheck(report, args.crosscheck)

    if args.out:
        with open(args.out, "wb") as fh:
            fh.write(_render_report(report))

    for row in report["legs"]:
        triple = row["triple"]
        print("%-42s probes=%-5s drifted=%-5s drifted_and_off=%-5s  %s" % (
            row["leg"], triple["probes"], triple["drifted"],
            triple["drifted_and_off_frontier"],
            "" if row["status"] == MEASURED else row["status"]))
    print(json.dumps(report["totals"], sort_keys=True))

    for row in report["refused"]:
        print("REFUSED %s -- %s" % (row["leg"], row["status"]), file=sys.stderr)

    if "crosscheck" in report:
        check = report["crosscheck"]
        print("crosscheck vs %s: %s (%d probes compared)" % (
            check["source"], "EQUAL" if check["equal"] else "DISAGREES",
            check["probes_compared"]))
        if not check["equal"]:
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
