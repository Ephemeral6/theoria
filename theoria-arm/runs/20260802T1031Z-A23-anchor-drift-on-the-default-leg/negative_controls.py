"""Two legs whose drift is known before it is measured, and the check must say both.

A drift detector that has only ever been watched saying *"drifted"* has not been
shown to be a detector -- it has been shown to be a function that returns a
positive number. So this builds legs where the answer is fixed by construction
and asks the same `armtools.anchor_drift.measure_leg` that read the archive:

1. **the self-consistent leg** -- the world *is* the manual, and the arm's
   manual is that same object. `inner/loop._roll_forward` cannot be wrong, so
   the anchor is the world's frame at every probe. Required: **drift 0, and
   every probe anchored** -- `drifted == 0` alone is not enough, because
   `drifted` counts only `True` and folds the *unknown* anchor into the same
   zero. Rename the trace's notes so the join misses, or strip `inert` from
   every design, and a leg that measured nothing at all would pass a bare
   `drifted == 0`. So this asserts `anchor_unknown == 0` and
   `anchored_to_world == len(actions)` as well.
2. **the mispredicting leg** -- the same manual, wrapped so the one transition
   out of world-frame `MISPREDICT_AT` is a no-op while the world takes it.
   Required: **the exact set of drifted probes**, not `drift > 0`. A roll for
   probe *t* consumes actions 1..*t*-1, so freezing frame *k* breaks probes
   *t* >= *k*+2 and no others; a `> 0` predicate would accept the check firing
   in the wrong place, and did -- the comment below used to predict `P-03`
   onward while the file's own output said `P-04`, `P-05`.
3. **the cascade leg** -- the self-consistent leg with each command answering in
   several frames instead of one, which is what a real ARC command does (26 of
   the 34 steps on `…-r3` are multi-frame). Required: **the triple does not
   move.** On a one-grid world every candidate reading of "the frame the world
   was showing" coincides, so without this the whole measurement rests on an
   untested modelling choice.

Both are run on **two** manuals from two different development-pile games, so a
result cannot be an accident of one compiled theory.

Nothing here is a simulation of the arm: the trace is written by
`world.frames.FrameStore`, the frontier by `inner.probe.build_hypotheses`, the
rolled state by `inner.loop._roll_forward` itself, and the verdict by the same
`measure_leg` that produced `ANCHOR_DRIFT.json`.

The synthetic legs are built under a temporary directory and deleted. They are
derived artefacts -- re-derivable from this file in seconds -- and a leg
directory under `runs/` without a `MANIFEST.json` is a provenance finding
(`armtools.verify_provenance` check 2), so they do not go there.

Reads `books/snapshots/` (tracked), so it runs in a clone with no traces. No
model call, no ARC action, no network.

    python negative_controls.py [--legs-root DIR] [--out NEGATIVE_CONTROLS.json]
"""

import argparse
import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ARM = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ARM)

import _bootstrap                                       # noqa: E402,F401

from armtools import anchor_drift                       # noqa: E402

#: One manual per development-pile game, and an action list that actually moves
#: it. `[4, 3, ...]` leaves g50t's world untouched and `[2, 5, ...]` leaves
#: sk48's untouched -- on a frozen world every hypothesis agrees and the
#: mispredicting control could not fail, so the pairing is load-bearing.
MANUALS = (
    {"leg": "20260731T1310Z-A3-level2-carried-r2",
     "game": "g50t-5849a774", "actions": [2, 5, 2, 5, 2]},
    {"leg": "20260731T1500Z-A3-sk48-carried-l1",
     "game": "sk48-d8078629", "actions": [4, 3, 4, 3, 4]},
)

#: The transition the mispredicting manual gets wrong: the one out of
#: world-frame 2. The roll before probe *t* consumes actions 1..*t*-1, so it
#: only meets that transition from *t* = 4 on: `P-01`..`P-03` stay anchored and
#: `P-04`, `P-05` drift. A control that broke frame 0 would drift everywhere and
#: could not show that the check is reading the anchor rather than the leg.
#:
#: It must satisfy `MISPREDICT_AT <= len(actions) - 2` or the break falls off
#: the end of the roll and the control silently measures nothing; `_expected`
#: derives the answer from the arithmetic rather than restating it, so a bad
#: constant fails loudly instead of passing vacuously.
MISPREDICT_AT = 2


def _expected_drifted(actions, mispredict_at):
    """Which probes must drift, derived rather than remembered."""
    if mispredict_at is None:
        return []
    return ["P-%02d" % t for t in range(1, len(actions) + 1)
            if t >= mispredict_at + 2]


def run(legs_root):
    controls = []
    for spec in MANUALS:
        leg_dir = os.path.join(legs_root, spec["leg"])
        with tempfile.TemporaryDirectory() as work:
            name, namespace = anchor_drift.newest_compiling_snapshot(
                leg_dir, os.path.join(work, "compile"))
            if namespace is None:
                controls.append({"manual": spec["leg"],
                                 "status": "no snapshot of this leg compiles; "
                                           "nothing controlled"})
                continue
            n = len(spec["actions"])
            baseline = None
            for label, mispredict, cascade in (
                    ("self_consistent", None, 1),
                    ("mispredicting", MISPREDICT_AT, 1),
                    ("cascade", None, 4)):
                out_dir = os.path.join(work, label)
                built = anchor_drift.synthesise_leg(
                    out_dir, namespace, spec["actions"],
                    mispredict_at=mispredict, cascade=cascade)
                measured = anchor_drift.measure_leg(out_dir)
                triple = measured["triple"]
                drifted = [r["probe_id"] for r in measured["probes"]
                           if r["drifted"]]
                want = _expected_drifted(spec["actions"], mispredict)

                # Common to every control: the world has to move, or a frozen
                # world would make "no drift" true of any anchor whatsoever,
                # and every anchor has to be known, or an unmeasured leg would
                # pass as a clean one.
                sane = (built["world_frames_distinct"] == n + 1
                        and measured["status"] == anchor_drift.MEASURED
                        and measured["anchor_unknown"] == 0
                        and triple["probes"] == n)
                if label == "cascade":
                    required = ("the triple is what the same leg measured with "
                                "one frame per step")
                    held = bool(sane and baseline is not None
                                and triple == baseline)
                else:
                    required = ("exactly these probes drift: %s"
                                % (want or "none"))
                    held = bool(sane and drifted == want
                                and measured["anchored_to_world"]
                                == n - len(want))
                if label == "self_consistent":
                    baseline = dict(triple)

                controls.append({
                    "control": label,
                    "manual": spec["leg"],
                    "snapshot": name,
                    "game": spec["game"],
                    "actions": spec["actions"],
                    "mispredict_at": mispredict,
                    "cascade": cascade,
                    "world_frames_distinct": built["world_frames_distinct"],
                    "frontier_widths": built["frontier_widths"],
                    "status": measured["status"],
                    "triple": triple,
                    "anchored_to_world": measured["anchored_to_world"],
                    "anchor_unknown": measured["anchor_unknown"],
                    "drifted_probes": drifted,
                    "drifted_probes_required": want,
                    "required": required,
                    "held": held,
                })

    # The third control is not synthetic: hand `measure_leg` a directory whose
    # trace is missing exactly as a clone's is, and it must refuse by name.
    with tempfile.TemporaryDirectory() as work:
        bare = os.path.join(work, "leg-without-its-trace")
        os.makedirs(bare)
        with open(os.path.join(bare, "probes.jsonl"), "w",
                  encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps({"probe_id": "P-01", "phase": "design",
                                 "step_idx": 1, "action": 2,
                                 "predictions": {"inert": "a" * 16,
                                                 "manual": "b" * 16}},
                                sort_keys=True) + "\n")
            fh.write(json.dumps({"probe_id": "P-01", "phase": "result",
                                 "observed": "b" * 16}, sort_keys=True) + "\n")
        measured = anchor_drift.measure_leg(bare)
        # The refusal has to name the right reason, not merely have the right
        # shape. An empty directory and an unparseable probes.jsonl also come
        # back all-null, so a predicate that only checked the nulls would pass
        # on inputs this control is not about.
        controls.append({
            "control": "trace_absent_as_in_a_clone",
            "manual": None,
            "status": measured["status"],
            "triple": measured["triple"],
            "required": "the triple is all null, none of it is 0, and the "
                        "status names the missing trace specifically",
            "held": (all(measured["triple"][k] is None
                         for k in anchor_drift.TRIPLE_KEYS)
                     and measured["status"] == anchor_drift.NO_TRACE),
        })

        # …and the neighbouring refusals, so "all null" is never mistaken for
        # "the trace was missing".
        for label, path, want in (
                ("probes_absent", os.path.join(work, "empty-leg"),
                 anchor_drift.NO_PROBES),
                ("leg_absent", os.path.join(work, "never-existed"),
                 anchor_drift.NO_LEG)):
            if want is anchor_drift.NO_PROBES:
                os.makedirs(path, exist_ok=True)
            measured = anchor_drift.measure_leg(path)
            controls.append({
                "control": label, "manual": None,
                "status": measured["status"],
                "triple": measured["triple"],
                "required": "all null, and a status distinct from the missing "
                            "trace's",
                "held": (all(measured["triple"][k] is None
                             for k in anchor_drift.TRIPLE_KEYS)
                         and measured["status"] == want
                         and want != anchor_drift.NO_TRACE),
            })

    return {"controls": controls,
            "all_held": all(c.get("held") for c in controls),
            "mispredict_at": MISPREDICT_AT}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--legs-root", default=os.path.dirname(HERE))
    ap.add_argument("--out", default=os.path.join(HERE,
                                                  "NEGATIVE_CONTROLS.json"))
    args = ap.parse_args(argv)

    report = run(args.legs_root)
    with open(args.out, "wb") as fh:
        fh.write((json.dumps(report, indent=1, sort_keys=True, default=str)
                  + "\n").encode("utf-8"))

    for control in report["controls"]:
        print("%-28s %-40s required %-12s -> %s  %s" % (
            control.get("control"), control.get("manual") or "-",
            control["required"], "HELD" if control["held"] else "BROKE",
            json.dumps(control["triple"], sort_keys=True)))
    print("all_held:", report["all_held"])
    return 0 if report["all_held"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
