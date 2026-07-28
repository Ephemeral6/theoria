"""Why does the A0 miner refuse a world?  Localise it to one pair of transitions.

`run_stage` raises `NoSeparatingGuard` as a single line with a transition index
and nothing else, which is enough to know the run failed and not enough to say
whether the *world* is broken or the *vocabulary* is.  Those are opposite
verdicts: the first is a defect in this library, the second is a finding about
`cold-start-a0`'s atom set that belongs upstream.

So this reproduces the mining group by group and, for the group that fails,
prints the two transitions the vocabulary cannot tell apart, with the frames and
the effects side by side. If their frames differ, the vocabulary is missing an
atom that can see the difference. If their frames are identical and the effects
are not, the world does not determine its own behaviour and the defect is here.

```bash
python -m worldgen.qc.diagnose_miner t2-lock-fragile
```
"""

import json
import sys
from typing import Dict, List, Optional, Sequence, Tuple

from .bridge import atoms_a0, engines_stage, extract_board, multi_miner, object_layer, segment_operators
from ..core.trace import read_trace
from ..core.world import GridWorld
from ..generate import BY_ID
from .run_qc import WORLDS_OUT

import os


def main(argv: Optional[Sequence[str]] = None) -> int:
    world_id = (argv or ["t2-lock-fragile"])[0]
    frames, actions, _wins = read_trace(
        os.path.join(WORLDS_OUT, world_id, "raw_trace.jsonl"))

    board = extract_board(frames)
    background = engines_stage.background_color(board, frames)
    layer = object_layer(frames, board, background=background)
    _op, seg, _cmp = segment_operators.choose_operator(layer, background=background)
    transitions = multi_miner.build_transitions(frames, layer, actions, seg,
                                                background=background)
    track_ids = [t.track_id for t in seg.tracks]
    observations = [t.obs for t in transitions]
    vocabulary = multi_miner.build_vocabulary(observations, list(track_ids))
    masks = multi_miner.atom_masks(vocabulary, observations,
                                   [t.action for t in transitions])
    universe = (1 << len(transitions)) - 1

    print("world %s: %d frames, %d transitions, %d tracks, %d atoms"
          % (world_id, len(frames), len(transitions), len(track_ids), len(vocabulary)))

    for track in track_ids:
        groups: Dict[Tuple, List] = {}
        for tr in transitions:
            groups.setdefault((tr.action, tr.effects[track].key()), []).append(tr)
        for key in sorted(groups, key=lambda k: (k[0], str(k[1]))):
            members = groups[key]
            positives = 0
            for tr in members:
                positives |= 1 << tr.index
            try:
                multi_miner.synthesize(positives, universe, masks)
            except Exception as exc:                              # noqa: BLE001
                print("\nFAILS  track=%s action=%s effect=%s  (%d positives)"
                      % (track, key[0], key[1], len(members)))
                print("  %s: %s" % (type(exc).__name__, exc))
                cex = int(str(exc).split("transition ")[1].split(" ")[0])
                _explain(transitions, members, cex, vocabulary, masks)
    return 0


def _explain(transitions, members, cex: int, vocabulary, masks) -> None:
    """The negative the guard cannot exclude, against a positive it must keep."""
    negative = next(t for t in transitions if t.index == cex)
    twin = next((t for t in members
                 if masks_equal(vocabulary, masks, t.index, cex)), members[0])
    print("  negative t=%d action=%s" % (negative.index, negative.action))
    print("  positive t=%d action=%s" % (twin.index, twin.action))
    same = masks_equal(vocabulary, masks, twin.index, cex)
    print("  every atom in the vocabulary agrees on both: %s" % same)
    frames_equal = negative.obs.frame == twin.obs.frame
    print("  their frames are identical: %s" % frames_equal)
    print("  VERDICT: %s" % (
        "the WORLD is broken — identical frames, different behaviour"
        if frames_equal else
        "the VOCABULARY is short — the frames differ but no atom sees the difference"))
    if not frames_equal:
        for r, (a, b) in enumerate(zip(negative.obs.frame, twin.obs.frame)):
            if a != b:
                print("    row %d  negative=%s" % (r, "".join(str(v) for v in a)))
                print("    row %d  positive=%s" % (r, "".join(str(v) for v in b)))


def masks_equal(vocabulary, masks, i: int, j: int) -> bool:
    return all(((masks[a] >> i) & 1) == ((masks[a] >> j) & 1) for a in vocabulary)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:] or None))
