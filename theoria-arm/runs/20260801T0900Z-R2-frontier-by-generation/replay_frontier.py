"""Replay the four legs' recorded probes through the new frontier builder.

The counterfactual requirement 4 asks for, and the reason it is not a
simulation: every hypothesis here is built by `inner/probe.build_hypotheses`
itself, against a manual recompiled from the leg's own snapshot and a
`world.frames.FrameStore` truncated to the moment before the action was sent.
Nothing is re-implemented and nothing is scored against a model of the arm.

**The reconstruction check comes first, and it can fail.** For each recorded
probe this walks the leg's `books/snapshots/`, compiles each one, rolls the
manual forward over the trace's actions exactly as `inner/loop._roll_forward`
does, and computes the *ablation* frontier. A snapshot is accepted only if the
prediction dict it produces equals the dict `probes.jsonl` recorded, key for
key and hash for hash. A probe no snapshot reproduces is reported as
`unreconstructed` and scored for nothing -- because a counterfactual over a
state we cannot show is the state the arm was in is a story, not a measurement.

Then, on exactly that verified state and store, the `generated` frontier is
built and asked one question: does it contain the hash the world actually
returned?

Offline. Reads `probes.jsonl` (tracked) and `trace.jsonl` (gitignored). No
model call, no ARC action, no network. Development-pile games only.

    python replay_frontier.py [--legs-root <dir>] [--with-cut-generators]
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

from inner import commit                               # noqa: E402
from inner import probe as probe_beat                  # noqa: E402
from inner.books import Books                          # noqa: E402
from world.frames import FrameStore, grid_hash, load_store   # noqa: E402

LEGS = [
    "20260731T1240Z-A3-level2-carried",
    "20260731T1310Z-A3-level2-carried-r2",
    "20260731T1430Z-A3-level2-carried-r3",
    "20260731T1500Z-A3-sk48-carried-l1",
]


def _read_jsonl(path):
    with open(path, encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def _namespaces(leg_dir, workdir):
    """Every snapshot of this leg's manual, compiled, newest first."""
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


def _roll_forward(namespace, actions):
    """`inner/loop._roll_forward`, verbatim in behaviour."""
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
    """A store holding every step strictly before `upto`."""
    view = FrameStore()
    for step in store.steps:
        if step.step_idx < upto:
            view.add(step)
    return view


def _predict(hypotheses, state, action):
    out = {}
    for hypothesis in hypotheses:
        try:
            out[hypothesis.id] = hypothesis.predict(state, action)
        except Exception:                              # noqa: BLE001
            out[hypothesis.id] = "error"
    return out


def _cut_generator_action_replay(prefix, action):
    """The generator that was built, measured at zero, and left out.

    Kept here and nowhere else: `--with-cut-generators` re-measures it so the
    claim "it was right zero times" stays checkable instead of being a sentence
    in a docstring.
    """
    steps = list(prefix.steps)
    world = prefix.current
    if world is None:
        return None
    want = action[1] if isinstance(action, (tuple, list)) else action
    for idx in range(len(steps) - 1, 0, -1):
        label = steps[idx].action
        if not (isinstance(label, str) and label.upper().startswith("ACTION")):
            continue
        try:
            number = int(label[6:])
        except ValueError:
            continue
        if number != want:
            continue
        before, after = steps[idx - 1].grid, steps[idx].grid
        if before is None or after is None:
            return None
        delta = probe_beat._delta(before, after)       # noqa: SLF001
        return grid_hash(probe_beat._applied(world, delta))   # noqa: SLF001
    return None


def replay_leg(leg_dir, workdir, with_cut=False):
    probes_path = os.path.join(leg_dir, "probes.jsonl")
    trace_path = os.path.join(leg_dir, "trace.jsonl")
    leg = os.path.basename(leg_dir)
    if not (os.path.exists(probes_path) and os.path.exists(trace_path)):
        return {"leg": leg, "status": "trace.jsonl is gitignored and absent "
                                      "here; nothing replayed"}, []
    probes = _read_jsonl(probes_path)
    designs = {r["probe_id"]: r for r in probes if r.get("phase") == "design"}
    results = {r["probe_id"]: r for r in probes if r.get("phase") == "result"}
    store = load_store(trace_path)
    by_note = {s.note: s for s in store.steps if s.note}
    namespaces = _namespaces(leg_dir, os.path.join(workdir, leg))

    generated_cfg = probe_beat.FrontierConfig(mode="generated")
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
        actions = [s.action for s in prefix.steps]

        row = {"leg": leg, "probe_id": probe_id, "action": design["action"],
               "step_idx": step.step_idx, "observed": observed,
               "reconstructed": False}

        for name, namespace in namespaces:
            state = _roll_forward(namespace, actions)
            ablation = probe_beat.build_hypotheses(namespace)
            got = _predict(ablation, state, action)
            if got != recorded:
                continue
            row["reconstructed"] = True
            row["snapshot"] = name
            row["ablation_width"] = len(set(got.values()))
            row["ablation_contains_truth"] = observed in set(got.values())

            full = probe_beat.build_hypotheses(
                namespace, frontier=generated_cfg, store=prefix)
            new = _predict(full, state, action)
            generated_ids = [h.id for h in full if h.id not in got]
            row["generated_ids"] = sorted(generated_ids)
            row["generated_width"] = len(set(new.values()))
            row["generated_contains_truth"] = observed in set(new.values())
            row["which_generated_hypotheses_were_right"] = sorted(
                hid for hid in generated_ids if new.get(hid) == observed)
            row["anchor"] = probe_beat.anchor_drift(namespace, state, prefix)
            if with_cut:
                row["cut_action_replay_right"] = (
                    _cut_generator_action_replay(prefix, action) == observed)
            break
        rows.append(row)

    done = [r for r in rows if r["reconstructed"]]
    summary = {
        "leg": leg,
        "probes_completed": len(rows),
        "reconstructed": len(done),
        "unreconstructed": len(rows) - len(done),
        "ablation_contains_truth": sum(
            1 for r in done if r["ablation_contains_truth"]),
        "generated_contains_truth": sum(
            1 for r in done if r["generated_contains_truth"]),
        "ablation_widths": sorted({r["ablation_width"] for r in done}),
        "generated_widths": sorted({r["generated_width"] for r in done}),
        "anchor_drifted": sum(1 for r in done if r["anchor"]["drifted"]),
    }
    if with_cut:
        summary["cut_action_replay_right"] = sum(
            1 for r in done if r.get("cut_action_replay_right"))
    return summary, rows


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--legs-root", default=os.path.dirname(HERE))
    ap.add_argument("--out", default=os.path.join(HERE, "REPLAY.json"))
    ap.add_argument("--with-cut-generators", action="store_true")
    args = ap.parse_args(argv)

    per_leg, all_rows = [], []
    workdir = tempfile.mkdtemp(prefix="r2-frontier-replay-")
    try:
        for leg in LEGS:
            summary, rows = replay_leg(os.path.join(args.legs_root, leg),
                                       workdir, args.with_cut_generators)
            per_leg.append(summary)
            all_rows.extend(rows)
    finally:
        shutil.rmtree(workdir, ignore_errors=True)

    done = [r for r in all_rows if r["reconstructed"]]
    off_ablation = [r for r in done if not r["ablation_contains_truth"]]
    won = [r for r in off_ablation if r["generated_contains_truth"]]
    by_hypothesis = {}
    for row in won:
        for hid in row["which_generated_hypotheses_were_right"]:
            by_hypothesis[hid] = by_hypothesis.get(hid, 0) + 1
    totals = {
        "probes_completed": len(all_rows),
        "reconstructed": len(done),
        "unreconstructed": len(all_rows) - len(done),
        "ablation_off_frontier": len(off_ablation),
        "generated_recovers_off_frontier": len(won),
        "generated_still_off_frontier": len(off_ablation) - len(won),
        "which_generated_hypothesis_was_right": dict(sorted(
            by_hypothesis.items())),
        "ablation_width_values": sorted({r["ablation_width"] for r in done}),
        "generated_width_values": sorted({r["generated_width"] for r in done}),
        "anchor_drifted": sum(1 for r in done if r["anchor"]["drifted"]),
        "anchor_drifted_and_off_ablation_frontier": sum(
            1 for r in off_ablation if r["anchor"]["drifted"]),
    }
    if args.with_cut_generators:
        totals["cut_generator_action_replay_right"] = sum(
            1 for r in done if r.get("cut_action_replay_right"))
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
