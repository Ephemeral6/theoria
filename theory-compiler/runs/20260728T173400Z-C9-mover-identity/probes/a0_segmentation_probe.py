"""Read-only probe: did `identity_swap` change A0's own segmentation?

Runs exactly the segmentation half of `pipeline/engines_stage.run_stage` --
board extraction, background, object layer, `choose_operator` -- against A0's
base trace and, if present, the `_no_button` variant.  Prints the chosen
operator, track count, script bits, mover track, and the full `identity_repair`
report that `choose_operator` now returns as its third value.

Writes nothing.  Run from anywhere:

    python theory-compiler/runs/.../probes/a0_segmentation_probe.py
"""

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = HERE
for _ in range(6):
    REPO = os.path.dirname(REPO)
    if os.path.isdir(os.path.join(REPO, "cold-start-a0")):
        break
A0 = os.path.join(REPO, "cold-start-a0")
sys.path.insert(0, A0)

import _bootstrap  # noqa: F401,E402

from pipeline import multi_miner, segment_operators  # noqa: E402
from pipeline.board import extract_board, object_layer  # noqa: E402
from pipeline.engines_stage import background_color  # noqa: E402
from world.ground_truth import read_trace  # noqa: E402


def probe(label: str, trace_path: str) -> None:
    print("=" * 72)
    print("%s   %s" % (label, trace_path))
    print("=" * 72)
    if not os.path.exists(trace_path):
        print("  (trace absent)")
        return

    frames, actions, wins = read_trace(trace_path)
    board = extract_board(frames)
    background = background_color(board, frames)
    layer = object_layer(frames, board, background=background)

    operator, seg, report = segment_operators.choose_operator(
        layer, background=background
    )
    mover = multi_miner.mover_track(seg)
    chosen = next(o for o in report if o["chosen"])

    print("  frames             : %d" % len(frames))
    print("  chosen operator    : %s" % operator)
    print("  n tracks           : %d" % len(seg.tracks))
    print("  n events           : %d" % len(seg.events))
    print("  script_bits        : %s" % chosen["script_bits"])
    print("  baseline_bits      : %s" % chosen["baseline_bits"])
    print("  mover track        : %s" % mover)
    move_counts = {}
    for e in seg.events:
        if e.type == "move":
            move_counts[e.track] = move_counts.get(e.track, 0) + 1
    print("  move attribution   : %s" % json.dumps(move_counts, sort_keys=True))
    print("  tracks             : %s" % [t.track_id for t in seg.tracks])
    print()
    for entry in report:
        print("  -- operator %s (chosen=%s)" % (entry["operator"], entry["chosen"]))
        print("     script_bits=%s tracks=%s events=%s ratio=%s" % (
            entry["script_bits"], entry["tracks"], entry["events"], entry["ratio"]))
        print("     identity_repair:")
        for line in json.dumps(entry["identity_repair"], indent=2,
                               sort_keys=True).splitlines():
            print("       " + line)
    print()


def main() -> int:
    art = os.path.join(A0, "artifacts")
    probe("A0 BASE", os.path.join(art, "raw_trace.jsonl"))
    probe("A0 NO_BUTTON VARIANT", os.path.join(art, "raw_trace_no_button.jsonl"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
