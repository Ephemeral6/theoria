"""One theory-free examinee, every world, scored through the real marker.

Five of the twenty per-world examiners independently wrote a variant of the same
strategy and reported that it ties the oracle. This script is the catalogue-level
form of that claim, written once by the synthesist rather than assembled from
twenty separate numbers -- if the finding is real it must survive being stated as
one function applied to all twenty worlds without a single per-world constant.

THE STRATEGY, IN FULL

Read the agent's cell from `legend["agent"]`. Step one cell in the action's
direction. If the target is off the grid or holds `legend["wall"]`, answer with
the input frame unchanged; otherwise move the agent there and repaint the cell it
left with `legend["floor"]`.

That is the entire world model, and it was not learned from anything -- it is the
prior any reader brings to a grid before being shown one. It reads only the sheet
side (`frame_before`, `action`, `legend`), never `Item.truth`, never
`ground_truth.json`, never the trace. It contains no world id, no rule name and no
tuned constant, so it cannot have been fitted to any particular world.

WHAT A HIGH SCORE HERE MEANS, AND WHAT IT DOES NOT

It does not mean the exam is worthless. It means the exam's *items* are, on these
worlds, mostly answerable without the thing the exam exists to measure -- and
that the score a real examinee earns is therefore not evidence that it holds a
world theory. The honest reading of a 1.000 is the one the per-world reports
give: the strategy did not learn a rule, it brought one.
"""

from __future__ import annotations

import json
import os
import sys

from exam.grading.mark import mark
from exam.grading.registry import digest
from exam.guard import no_network
from exam.model import Submission
from exam.papers import heldout_worldgen as hw
from exam.papers import worldgen_port as port

DELTA = {"UP": (-1, 0), "DOWN": (1, 0), "LEFT": (0, -1), "RIGHT": (0, 1)}


def answer(paper_side):
    """The prior. Sheet fields only."""
    frame = [list(row) for row in paper_side["frame_before"]]
    legend = paper_side.get("legend") or {}
    agent, wall, floor = legend.get("agent"), legend.get("wall"), legend.get("floor", 0)
    step = DELTA.get(str(paper_side.get("action")).upper())
    if agent is None or step is None:
        return frame
    here = next(((r, c) for r, row in enumerate(frame)
                 for c, v in enumerate(row) if v == agent), None)
    if here is None:
        return frame
    r, c = here[0] + step[0], here[1] + step[1]
    if not (0 <= r < len(frame) and 0 <= c < len(frame[0])):
        return frame
    if frame[r][c] == wall:
        return frame
    frame[here[0]][here[1]] = floor
    frame[r][c] = agent
    return frame


def main() -> int:
    rows = []
    with no_network():
        d = digest()
        for world_id in port.world_ids():
            paper = hw.build_for(world_id, 2)
            key_doc = paper.key(d)
            answers = {item.item_id: answer(item.paper) for item in paper.items}
            report = mark(key_doc, Submission(
                examinee_id="fake-prior", paper_id=paper.paper_id,
                answers=answers, capabilities=("answers",)), axes_fn=hw.axes)
            got = {s.item_id: s.verdict == "correct" for s in report.scores}

            # How much of the residue the profiler calls informative does a prior
            # with no evidence take? That is the number this run exists for.
            bluff = {item.item_id:
                     item.truth["frame_after"] == item.paper["frame_before"]
                     for item in paper.items}
            theory_ids = [i for i in got if not bluff[i]]
            rows.append({
                "world_id": world_id,
                "tier": paper.world.get("tier"),
                "items": len(paper.items),
                "bluffer_floor": round(sum(bluff.values()) / len(bluff), 6),
                "prior": round(report.fraction, 6),
                "changed_items": len(theory_ids),
                "changed_taken": sum(1 for i in theory_ids if got[i]),
                "gap": report.axes.get("gap_replay_minus_heldout"),
            })

    perfect = [r["world_id"] for r in rows if r["prior"] == 1.0]
    beats = [r for r in rows if r["prior"] > r["bluffer_floor"] + 1e-9]
    changed = sum(r["changed_items"] for r in rows)
    taken = sum(r["changed_taken"] for r in rows)
    out = {
        "strategy": "walk-or-wall; sheet fields only; no per-world constant",
        "worlds": rows,
        "totals": {
            "worlds": len(rows),
            "worlds_scoring_1.000": len(perfect),
            "perfect_worlds": perfect,
            "worlds_beating_their_bluffer_floor": len(beats),
            "items_total": sum(r["items"] for r in rows),
            "frame_changing_items": changed,
            "frame_changing_items_taken_by_the_prior": taken,
            "share_of_frame_changing_items_taken": round(taken / changed, 6),
        },
    }
    print(json.dumps(out, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.path.insert(0, os.getcwd())
    raise SystemExit(main())
