"""The 2x2: anchor x frontier, over the 52 completed probes of 2026-07-31.

R2 measured one axis -- how the frontier is *built* -- and found that 35 of 52
probes were designed against a state the world had already left. This measures
the other: which frame the frontier is a successor *of*. The two are orthogonal
and the cells are not additive, so all four are run.

Built on `runs/20260801T0900Z-R2-frontier-by-generation/replay_frontier.py`,
which is the precedent this follows and the code this re-uses in spirit: every
hypothesis is built by `inner/probe.build_hypotheses` itself, against a manual
recompiled from the leg's own `books/snapshots/` and a `FrameStore` truncated
to the moment before the action was sent. Nothing is simulated.

**Two checks run before anything is scored.**

1. *Reconstruction*, R2's: a snapshot is accepted only if the ablation
   prediction dict it produces equals the dict `probes.jsonl` recorded, key for
   key and hash for hash. A probe no snapshot reproduces scores for nothing.

2. *Harness equivalence*, new here and not optional. R2's replay rolls the
   manual forward over `[s.action for s in prefix.steps]`, which begins with
   the leg's `RESET` and omits the trailing `None`; `inner/loop._roll_forward`
   rolls it over `store.actions`, which is that list shifted by one. Those are
   different action sequences, and if they produced different states then R2's
   headline 35 would be an artefact of its own harness rather than a fact about
   the arm. This recomputes both and reports whether they agree on every probe.
   A number that would have been wrong in the same direction as the conclusion
   has to be checked, not assumed.

The question this answers, precisely. "How many of the 35 would have been
designed from the right state" is **35, by construction**: under
`--anchor observed` the frontier's anchor *is* the world's last frame, so it
cannot have drifted. That is a definition, not a measurement, and it is not
reported as one. The measurement is the consequence: does the anchored frontier
then contain the answer the world actually gave?

Offline. Reads `probes.jsonl` (tracked) and `trace.jsonl` (gitignored). No
model call, no ARC action, no network. Development-pile games only.

    python replay_anchor.py [--legs-root <dir>] [--out ANCHOR_REPLAY.json]
"""

import argparse
import json
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ARM = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ARM)

import _bootstrap                                      # noqa: E402,F401

from inner import anchor as anchor_mod                 # noqa: E402
from inner import commit                               # noqa: E402
from inner import loop as loop_mod                     # noqa: E402
from inner import probe as probe_beat                  # noqa: E402
from inner.books import Books                          # noqa: E402
from world.frames import FrameStore, grid_hash, load_store   # noqa: E402

#: R2's four. The same set, so the numbers sit beside R2's without a caveat
#: about which probes each was taken over.
LEGS = [
    "20260731T1240Z-A3-level2-carried",
    "20260731T1310Z-A3-level2-carried-r2",
    "20260731T1430Z-A3-level2-carried-r3",
    "20260731T1500Z-A3-sk48-carried-l1",
]

ROLLED = anchor_mod.AnchorConfig(mode="rolled")
OBSERVED = anchor_mod.AnchorConfig(mode="observed")
ABLATION = probe_beat.FrontierConfig(mode="ablation")
GENERATED = probe_beat.FrontierConfig(mode="generated")

CELLS = [("rolled", "ablation", ROLLED, ABLATION),
         ("rolled", "generated", ROLLED, GENERATED),
         ("observed", "ablation", OBSERVED, ABLATION),
         ("observed", "generated", OBSERVED, GENERATED)]


def _read_jsonl(path):
    with open(path, encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def _namespaces(leg_dir, workdir):
    snaps = os.path.join(leg_dir, "books", "snapshots")
    out = []
    if not os.path.isdir(snaps):
        return out
    for name in sorted(os.listdir(snaps), reverse=True):
        src = os.path.join(snaps, name)
        dst = os.path.join(workdir, name, "books")
        os.makedirs(dst, exist_ok=True)
        for fname in ("theory.dsl", "playbook.dsl", "problem.json"):
            path = os.path.join(src, fname)
            if os.path.exists(path):
                shutil.copy2(path, os.path.join(dst, fname))
        books = Books(dst)
        try:
            books.compile_all()
            namespace, _err = books.load_predictor()
        except Exception:                              # noqa: BLE001
            namespace = None
        if namespace is not None:
            out.append((name, namespace))
    return out


def _roll_forward_r2(namespace, actions):
    """R2's `replay_frontier._roll_forward`, verbatim in behaviour."""
    state = namespace["initial_state"]()
    step = namespace["step"]
    for arc_action in actions:
        if arc_action is None:
            break
        try:
            state = step(state, commit.action_to_manual(arc_action))
        except Exception:                              # noqa: BLE001
            break
    return state


def _prefix_store(store, upto):
    view = FrameStore()
    for step in store.steps:
        if step.step_idx < upto:
            view.steps.append(step)
    return view


def _predict(hypotheses, state, action):
    out = {}
    for hypothesis in hypotheses:
        try:
            out[hypothesis.id] = hypothesis.predict(state, action)
        except Exception:                              # noqa: BLE001
            out[hypothesis.id] = "error"
    return out


def replay_leg(leg_dir, workdir):
    leg = os.path.basename(leg_dir)
    probes_path = os.path.join(leg_dir, "probes.jsonl")
    trace_path = os.path.join(leg_dir, "trace.jsonl")
    if not (os.path.exists(probes_path) and os.path.exists(trace_path)):
        return {"leg": leg,
                "status": "trace.jsonl is gitignored and absent here; "
                          "nothing replayed"}, []

    probes = _read_jsonl(probes_path)
    designs = {r["probe_id"]: r for r in probes if r.get("phase") == "design"}
    results = {r["probe_id"]: r for r in probes if r.get("phase") == "result"}
    store = load_store(trace_path)
    by_note = {s.note: s for s in store.steps if s.note}
    namespaces = _namespaces(leg_dir, os.path.join(workdir, leg))

    rows = []
    for probe_id, design in sorted(designs.items()):
        result = results.get(probe_id)
        step = by_note.get(probe_id)
        if result is None or step is None:
            continue
        recorded = design.get("predictions") or {}
        observed = result.get("observed")
        action = ("key", design["action"])
        prefix = _prefix_store(store, step.step_idx)

        row = {"leg": leg, "probe_id": probe_id, "action": design["action"],
               "step_idx": step.step_idx, "observed": observed,
               "reconstructed": False}

        for name, namespace in namespaces:
            state = loop_mod._roll_forward(namespace, prefix)   # noqa: SLF001
            got = _predict(probe_beat.build_hypotheses(namespace), state,
                           action)
            if got != recorded:
                continue

            row["reconstructed"] = True
            row["snapshot"] = name

            # -- check 2: is R2's roll the arm's roll? ---------------------
            r2_state = _roll_forward_r2(
                namespace, [s.action for s in prefix.steps])
            render = namespace["render"]
            try:
                row["harness_equivalent"] = (
                    grid_hash(render(state)) == grid_hash(render(r2_state)))
            except Exception:                          # noqa: BLE001
                row["harness_equivalent"] = None

            row["anchor"] = anchor_mod.divergence(namespace, state, prefix)
            row["anchor"].pop("first_cells", None)

            for anchor_name, frontier_name, anchor_cfg, frontier_cfg in CELLS:
                hypotheses = probe_beat.build_hypotheses(
                    namespace, frontier=frontier_cfg, store=prefix,
                    anchor=anchor_cfg)
                predictions = _predict(hypotheses, state, action)
                key = "%s__%s" % (anchor_name, frontier_name)
                row[key] = {
                    "width": len(set(predictions.values())),
                    "n_hypotheses": len(hypotheses),
                    "contains_truth": observed in set(predictions.values()),
                    "right": sorted(hid for hid, value
                                    in predictions.items()
                                    if value == observed),
                }
            break
        rows.append(row)

    done = [r for r in rows if r["reconstructed"]]
    summary = {
        "leg": leg,
        "status": "measured",
        "probes_completed": len(rows),
        "reconstructed": len(done),
        "unreconstructed": len(rows) - len(done),
        "harness_equivalent_on": sum(1 for r in done
                                     if r.get("harness_equivalent")),
        "harness_disagreed_on": sum(1 for r in done
                                    if r.get("harness_equivalent") is False),
        "anchor_drifted": sum(1 for r in done if r["anchor"].get("drifted")),
        "drift_cells_max": max([r["anchor"].get("cells_wrong") or 0
                                for r in done] or [None]) if done else None,
    }
    for _a, _f, _ac, _fc in CELLS:
        key = "%s__%s" % (_a, _f)
        summary[key] = {
            "contains_truth": sum(1 for r in done if r[key]["contains_truth"]),
            "widths": sorted({r[key]["width"] for r in done}),
        }
    return summary, rows


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--legs-root", default=os.path.dirname(HERE))
    ap.add_argument("--out", default=os.path.join(HERE, "ANCHOR_REPLAY.json"))
    args = ap.parse_args(argv)

    per_leg, all_rows = [], []
    workdir = tempfile.mkdtemp(prefix="r3-anchor-replay-")
    try:
        for leg in LEGS:
            summary, rows = replay_leg(os.path.join(args.legs_root, leg),
                                       workdir)
            per_leg.append(summary)
            all_rows.extend(rows)
    finally:
        shutil.rmtree(workdir, ignore_errors=True)

    done = [r for r in all_rows if r["reconstructed"]]
    drifted = [r for r in done if r["anchor"].get("drifted")]
    totals = {
        "probes_completed": len(all_rows),
        "reconstructed": len(done),
        "unreconstructed": len(all_rows) - len(done),
        "anchor_drifted": len(drifted),
        "harness_equivalent_on": sum(1 for r in done
                                     if r.get("harness_equivalent")),
        "harness_disagreed_on": sum(1 for r in done
                                    if r.get("harness_equivalent") is False),
        "harness_equivalence_means": (
            "R2's replay rolls the manual over [s.action for s in "
            "prefix.steps]; inner/loop._roll_forward rolls it over "
            "store.actions, which is that list shifted by one. These are "
            "different action sequences. Equal on every probe means R2's "
            "measured 35 is a fact about the arm and not an artefact of its "
            "own harness."),
        "how_many_of_the_drifted_would_be_seated_correctly": {
            "count": len(drifted),
            "why": "all of them, by construction and not by measurement: "
                   "under --anchor observed the frontier's anchor IS the "
                   "world's last observed frame, so it cannot have drifted "
                   "from it. The measurement worth reporting is the "
                   "consequence, which is the containment row below.",
        },
    }
    for _a, _f, _ac, _fc in CELLS:
        key = "%s__%s" % (_a, _f)
        cell = [r for r in done]
        totals[key] = {
            "contains_truth": sum(1 for r in cell if r[key]["contains_truth"]),
            "of": len(cell),
            "widths": sorted({r[key]["width"] for r in cell}),
            "on_the_drifted_subset": {
                "contains_truth": sum(1 for r in drifted
                                      if r[key]["contains_truth"]),
                "of": len(drifted),
            },
        }
    payload = {"legs": per_leg, "totals": totals, "probes": all_rows}
    with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(payload, fh, indent=1, sort_keys=True)
        fh.write("\n")
    print(json.dumps(totals, indent=1, sort_keys=True))
    for leg in per_leg:
        print(json.dumps(leg, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
