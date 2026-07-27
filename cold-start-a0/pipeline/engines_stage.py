"""M2: run the engines on the A0 trajectory and emit a real candidates.jsonl.

Order of work, and why:

  1. **board extraction** — what never varies sinks to the board (Theoria 1.8).
     Without this the walls are one giant connected component and the Door is
     glued to it.
  2. **mdl_segmenter** on the object layer — objects, tracks, event narration.
  3. **cegis (multi-track)** on the full frames — guards, and a frontier per rule.
  4. **zero_space** on the cart/latch occupancy — every GF(2) conservation law.
  5. **probe_frontier** on the rules whose evidence is thinnest — where to look
     next.

Every candidate goes through `common.candidates.make_candidate`, so
`CONTRACTS/candidates_schema.md` is enforced structurally rather than by
convention, and `status` is `"candidate"` by construction.

Nothing here adjudicates.  Adjudication is M3.
"""

import json
import os
import sys
from collections import Counter
from typing import Dict, List, Optional, Sequence

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import _bootstrap  # noqa: F401,E402

from common.candidates import emit, make_candidate  # noqa: E402
from engines import mdl_segmenter, probe_frontier as pf, zero_space  # noqa: E402

from pipeline import atoms_a0, multi_miner, segment_operators  # noqa: E402
from pipeline.board import Board, extract_board, object_layer  # noqa: E402
from world.ground_truth import read_trace  # noqa: E402

THIN_EVIDENCE = 3          # rules with at most this many witnesses get a probe


# ------------------------------------------------------------------ helpers

def background_color(board: Board, frames) -> int:
    """The colour a cell shows when nothing is on it.

    Taken over the *dynamic* cells only.  Counting over the whole frame gets it
    wrong on any world with a wall border -- there are more wall pixels than
    floor pixels here, and calling the walls "background" collapses the entire
    interior into one connected component.  The board cells are exactly the ones
    that carry no object, so the question is what the remaining cells look like
    most of the time.
    """
    dynamic = board.dynamic_cells
    counts = Counter(frame[r][c] for frame in frames for r, c in dynamic)
    return counts.most_common(1)[0][0]


def zero_space_cells(board: Board, background: int):
    """Floor plus everything the board fails to explain.

    The board's own map says which cells are plain floor; the dynamic cells are
    the ones it cannot account for.  Their union is the arena the objects live
    in, and it is the only honest domain for a law about where objects can be.
    """
    cells = [
        (r, c)
        for r in range(board.height)
        for c in range(board.width)
        if board.values[r][c] is None or board.values[r][c] == background
    ]
    return sorted(cells)


def zero_space_states(layer, cells, background: int):
    states = []
    for frame in layer:
        states.append([
            "." if frame[r][c] == background else str(frame[r][c])
            for r, c in cells
        ])
    return states


# --------------------------------------------------------------------- stage

def run_stage(trace_path: str, out_path: str, report_path: str,
              timestamp: Optional[str] = None) -> Dict[str, object]:
    frames, actions, wins = read_trace(trace_path)

    board = extract_board(frames)
    background = background_color(board, frames)
    layer = object_layer(frames, board, background=background)

    # --- 1. segmentation -------------------------------------------------
    operator, seg, operator_report = segment_operators.choose_operator(
        layer, background=background
    )
    emit(out_path, [
        make_candidate(
            engine="mdl_segmenter",
            kind="object_hypothesis",
            payload=dict(
                mdl_segmenter.to_payload(seg, track),
                segment_operator=operator + "+bipartite_common_fate",
                operator_comparison=operator_report,
            ),
            transitions=sorted({e.t for e in seg.events if e.track == track.track_id}),
            coverage="%d/%d" % (
                sum(1 for m in track.masks if m is not None), seg.n_frames
            ),
            timestamp=timestamp,
        )
        for track in seg.tracks
    ])
    track_ids = [t.track_id for t in seg.tracks]
    mover = multi_miner.mover_track(seg)

    # --- 2. rule mining --------------------------------------------------
    transitions = multi_miner.build_transitions(
        frames, layer, actions, seg, background=background
    )
    result = multi_miner.mine(transitions, track_ids, mover=mover)
    emit(out_path, [
        make_candidate(
            engine="cegis_miner",
            kind="rule_hypothesis",
            payload=rule.as_json(),
            transitions=rule.support,
            coverage=rule.coverage,
            timestamp=timestamp,
        )
        for rule in result.all_rules
    ])

    # --- 3. conservation laws -------------------------------------------
    cells = zero_space_cells(board, background)
    states = zero_space_states(layer, cells, background)
    colors = sorted({v for s in states for v in s if v != "."})
    zs = zero_space.analyse(states, colors)
    if not zero_space.verify(zs, states):
        raise AssertionError("a recovered law does not hold on the trajectory")
    globals_ = zs.global_laws()
    emit(out_path, [
        make_candidate(
            engine="zero_space",
            kind="invariant",
            payload=dict(
                zero_space.to_payload(law, zs),
                cells=[list(c) for c in cells],
                note="cell set = floor plus every cell the board cannot explain",
            ),
            transitions=list(range(zs.n_transitions)),
            coverage="%d/%d" % (zs.n_transitions, zs.n_transitions),
            timestamp=timestamp,
        )
        for law in globals_
    ])

    # --- 4. probes wherever the frontier is still split -------------------
    probes = []
    for rule in result.rules:            # ground rules only: `?dir` is not a probe
        if len(rule.frontier) < 2:
            continue
        probes.append(design_probe(rule, transitions, board, out_path, timestamp))

    report = {
        "trace": os.path.basename(trace_path),
        "frames": len(frames),
        "transitions": len(transitions),
        "board": {
            "static_cells": len(board.static_cells),
            "dynamic_cells": len(board.dynamic_cells),
            "background": background,
            "map": board.render(background),
        },
        "segmentation": {
            "operator": operator,
            "operator_comparison": operator_report,
            "tracks": [
                {
                    "id": t.track_id,
                    "first_frame": t.first_frame,
                    "color": t.color,
                    "shape": list(t.shape),
                    "frames_present": sum(1 for m in t.masks if m is not None),
                }
                for t in seg.tracks
            ],
            "mover": mover,
            "script_bits": seg.script_bits,
            "baseline_bits": seg.baseline_bits,
            "ratio": round(seg.compression_ratio, 4),
            "event_types": dict(Counter(e.type for e in seg.events)),
        },
        "mining": {
            "vocabulary_size": len(result.vocabulary),
            "rules": [
                {
                    "name": r.name,
                    "track": r.track,
                    "action": r.action,
                    "guard": sorted(a.name for a in r.guard),
                    "effect": r.effect.as_json(),
                    "coverage": r.coverage,
                    "frontier_size": len(r.frontier),
                }
                for r in result.all_rules
            ],
            "mutually_exclusive": {
                tid: result.guards_are_mutually_exclusive(tid) for tid in track_ids
            },
            "explains_every_transition": {
                tid: result.explains_every_transition(tid) for tid in track_ids
            },
        },
        "zero_space": {
            "cells": len(cells),
            "colors": colors,
            "features": zs.n_features,
            "difference_rank": zs.difference_rank,
            "space_dimension": zs.dimension,
            "cell_local_laws": len(zs.cell_local_laws()),
            "global_laws": [
                {
                    "rendering": law.rendering(),
                    "value": law.value,
                    "support": ["%s@(%d,%d)" % (f.color, cells[f.cell][0], cells[f.cell][1])
                                for f in law.support()],
                }
                for law in globals_
            ],
        },
        "probes": probes,
    }
    with open(report_path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return report


def _hypothetical_states(transitions, board: Board):
    """Configurations the trajectory never produced, one edit deep.

    `probe_frontier`'s own worked example is exactly this: a benign non-empty
    colour in the way, which the trajectory never showed.  Each candidate is a
    visited frame with the mover moved to some visited anchor and one neighbour
    cell repainted with a colour seen somewhere on the board.  These are
    *hypothetical*: nothing here promises the world can be driven into them, so
    they are reported separately from the executable tier.
    """
    base = transitions[0].obs
    anchors = sorted({t.obs.mover_anchor for t in transitions
                      if t.obs.mover_anchor is not None})
    palette = sorted({v for t in transitions for row in t.obs.frame for v in row})
    out = []
    for anchor in anchors:
        for direction in atoms_a0.DIRECTIONS:
            cells = atoms_a0.strip_cells(anchor, direction, base.mover_shape)
            if not all(base.in_bounds(c) for c in cells):
                continue
            for color in palette:
                frame = [list(row) for row in base.frame]
                for r, c in cells:
                    frame[r][c] = color
                out.append((anchor, direction, color, atoms_a0.Obs(
                    frame=tuple(tuple(row) for row in frame),
                    mover_anchor=anchor,
                    mover_shape=base.mover_shape,
                    anchors=dict(base.anchors, **{}),
                    colors=dict(base.colors),
                    background=base.background,
                )))
    return out


def _best_split(hypotheses, states):
    """(state, ranked) maximising the frontier-splitting entropy, or None."""
    best = None
    for tag, obs in states:
        ranked = pf.rank_probes(hypotheses, obs, list(atoms_a0.DIRECTIONS))
        if not ranked or not ranked[0].splits:
            continue
        if best is None or ranked[0].entropy > best[1][0].entropy:
            best = (tag, ranked, obs)
    return best


def design_probe(rule, transitions, board: Board, out_path, timestamp):
    """Where would an experiment split this rule's surviving hypotheses?

    Two tiers, kept apart on purpose:

      * **executable** — a state the trajectory already visited, so the world can
        be driven back there by replaying a prefix and the probe can actually be
        run.  Only this tier is emitted as a `probe_design` candidate.
      * **hypothetical** — a one-edit variation on a visited state.  A split here
        says the ambiguity is *in principle* decidable by experiment; no split
        anywhere says the surviving guards are extensionally identical in this
        world and no experiment can ever choose between them.  That is a real
        answer, and it hands the decision back to description length.
    """
    hypotheses = pf.hypotheses_from_guards(
        rule.frontier, atoms_a0.evaluate, label=rule.name
    )
    visited = [(("visited", t.index), t.obs) for t in transitions]
    found = _best_split(hypotheses, visited)
    row = {
        "rule": rule.name,
        "coverage": rule.coverage,
        "n_hypotheses": len(hypotheses),
        "frontier": [sorted(a.name for a in g) for g in rule.frontier],
    }
    if found is not None:
        tag, ranked, obs = found
        best, _ = pf.run(
            hypotheses, obs, list(atoms_a0.DIRECTIONS),
            transitions=rule.support,
            coverage="%d/%d" % (len(rule.frontier), len(rule.frontier)),
            state_rendering=["".join(str(v) for v in r) for r in obs.frame],
            out_path=out_path,
            timestamp=timestamp,
        )
        row.update({
            "tier": "executable",
            "at_transition": tag[1],
            "mover_anchor": list(obs.mover_anchor),
            "action": best.action,
            "entropy_bits": round(best.entropy, 6),
            "partition": best.as_json()["partition"],
        })
        return row

    hypothetical = [
        (("hypothetical", list(anchor), direction, color), obs)
        for anchor, direction, color, obs in _hypothetical_states(transitions, board)
    ]
    found = _best_split(hypotheses, hypothetical)
    if found is None:
        row.update({
            "tier": None,
            "verdict": "no experiment separates these guards in this world "
                       "— they are extensionally identical here; decide on "
                       "description length",
        })
        return row
    tag, ranked, obs = found
    row.update({
        "tier": "hypothetical",
        "construction": {"mover_anchor": tag[1], "direction": tag[2],
                         "painted_color": tag[3]},
        "action": ranked[0].action,
        "entropy_bits": round(ranked[0].entropy, 6),
        "partition": ranked[0].as_json()["partition"],
        "verdict": "separable in principle, but the world was never observed in "
                   "this configuration — not emitted as an executable probe",
    })
    return row


def main() -> int:
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    artifacts = os.path.join(here, "artifacts")
    os.environ.setdefault("THEORIA_DETERMINISTIC_IDS", "1")
    os.environ.setdefault("THEORIA_FIXED_TIME", "2026-07-28T00:00:00Z")

    suffix = sys.argv[1] if len(sys.argv) > 1 else ""
    trace = "raw_trace%s.jsonl" % suffix
    out = os.path.join(artifacts, "candidates%s.jsonl" % suffix)
    if os.path.exists(out):
        os.remove(out)                       # append-only within a run, not across
    report = run_stage(
        os.path.join(artifacts, trace),
        out,
        os.path.join(artifacts, "engines_report%s.json" % suffix),
    )
    print(json.dumps({k: report[k] for k in ("frames", "transitions")}, sort_keys=True))
    print("tracks:", [t["id"] + "/" + str(t["color"]) for t in report["segmentation"]["tracks"]])
    print("mover:", report["segmentation"]["mover"])
    print("events:", report["segmentation"]["event_types"])
    for rule in report["mining"]["rules"]:
        print("  %-22s %-6s %-28s %-8s frontier=%d  %s" % (
            rule["name"], rule["action"], json.dumps(rule["effect"]),
            rule["coverage"], rule["frontier_size"], " AND ".join(rule["guard"])))
    print("exclusive:", report["mining"]["mutually_exclusive"])
    print("total:", report["mining"]["explains_every_transition"])
    for law in report["zero_space"]["global_laws"]:
        print("law: %s = %d   support=%s" % (law["rendering"], law["value"],
                                             ",".join(law["support"])))
    for probe in report["probes"]:
        print("probe:", json.dumps(probe, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
