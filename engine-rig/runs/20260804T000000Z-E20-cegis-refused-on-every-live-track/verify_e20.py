"""E20 -- reproduce the recorded `cegis_miner` refusal offline and locate its cause.

Reads a *recorded* arm ledger (no API, no network, no model call) and replays the
engines over it exactly as the live leg did.  Emits aggregate numbers only:
track sizes, event counts, refusal strings, atom-mask statistics.  **No pixel
data leaves this script** -- engine-rig holds no game frames, and nothing here
writes any.

    python verify_e20.py <ledger.jsonl> [--out findings.json]

The ledger argument is a path the caller supplies; the default is the r3 leg the
board item names.  Only development-pile legs may be passed: the guard below
refuses any other game id, so a sealed game cannot be analysed by accident.
"""

import argparse
import collections
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ENGINE_RIG = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, ENGINE_RIG)

# The pile cut is binding here too. Positive whitelist, defaults to deny.
DEVELOPMENT_PILE = {"ar25-0c556536", "g50t-5849a774", "sk48-d8078629", "tn36-ef4dde99"}

DEFAULT_LEDGER = os.path.abspath(os.path.join(
    ENGINE_RIG, "..", "theoria-arm", "runs",
    "20260731T1430Z-A3-level2-carried-r3", "ledger.jsonl"))


def load(path):
    """Recorded frames and actions, plus the game id, from an arm ledger."""
    frames, actions, games = [], [], set()
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("event") != "env_step":
                continue
            if row.get("game_id"):
                games.add(row["game_id"])
            if not row.get("frames"):
                continue
            frames.append(row["frames"][-1])
            actions.append((row.get("action") or {}).get("name"))
    if not games <= DEVELOPMENT_PILE:
        raise SystemExit("REFUSED: ledger names %s, which is not development pile"
                         % sorted(games - DEVELOPMENT_PILE))
    return frames, actions, sorted(games)


def per_operator(frames, actions, split):
    from engines import cegis_miner
    from engines.mdl_segmenter import segment_trajectory

    seg = segment_trajectory(frames, background=0, split_by_color=split)
    out = {
        "operator": "connected_components(4)+uniform_color" if split
                    else "connected_components(4)",
        "split_by_color": split,
        "n_tracks": len(seg.tracks),
        "script_bits": seg.script_bits,
        "events": dict(collections.Counter(e.type for e in seg.events)),
        "largest_track_cells": max(len(t.masks[t.first_frame] or ())
                                   for t in seg.tracks),
        "tracks_born_after_frame_0": sum(1 for t in seg.tracks if t.first_frame > 0),
    }

    refusals, passed = [], []
    for track in seg.tracks:
        try:
            trs = cegis_miner.transitions_from_segmentation(
                frames, actions, seg, track, 0)
        except Exception as exc:                      # noqa: BLE001 -- reason is the finding
            refusals.append("%s: %s" % (type(exc).__name__, exc))
            continue
        entry = {"track": track.track_id,
                 "cells": len(track.masks[track.first_frame] or ()),
                 "transitions": len(trs)}
        # (a) the vocabulary as the live leg had it: the compass
        try:
            cegis_miner.mine(trs)
            entry["compass"] = "mined"
        except Exception as exc:                      # noqa: BLE001
            entry["compass"] = "%s: %s" % (type(exc).__name__, exc)
        # (b) the alphabet the evidence actually contains, gaps recorded
        try:
            res = cegis_miner.mine(trs, on_unseparable="record")
            entry["alphabet"] = {
                "rules": len(res.rules),
                "frontier_widths": sorted(len(r.frontier) for r in res.rules),
                "unseparable_classes": len(res.unseparable),
                "explains_every_transition": res.explains_every_transition(),
                "vocabulary": res.vocabulary,
            }
        except Exception as exc:                      # noqa: BLE001
            entry["alphabet"] = "%s: %s" % (type(exc).__name__, exc)
        passed.append(entry)

    out["n_refusals"] = len(refusals)
    out["refusal_kinds"] = dict(collections.Counter(
        r.split(";")[0] for r in refusals))
    out["passed_precondition"] = passed
    return out


def co_variation(frames):
    """The common-fate operator's verdict, measured rather than assumed."""
    height, width = len(frames[0]), len(frames[0][0])
    classes = collections.defaultdict(int)
    for r in range(height):
        for c in range(width):
            sig = tuple(frames[t][r][c] != frames[t + 1][r][c]
                        for t in range(len(frames) - 1))
            if any(sig):
                classes[sig] += 1
    sizes = sorted(classes.values(), reverse=True)
    return {"n_classes": len(classes), "class_sizes": sizes[:8],
            "largest_class_cells": sizes[0] if sizes else 0}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ledger", nargs="?", default=DEFAULT_LEDGER)
    ap.add_argument("--out", default=os.path.join(HERE, "findings.json"))
    args = ap.parse_args()

    frames, actions, games = load(args.ledger)
    findings = {
        "ledger": os.path.basename(os.path.dirname(args.ledger)),
        "games": games,
        "n_frames_with_pixels": len(frames),
        "action_alphabet": sorted({a for a in actions if a}),
        "co_variation": co_variation(frames),
        "operators": [per_operator(frames, actions, split) for split in (False, True)],
    }
    with open(args.out, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(findings, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(json.dumps(findings, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
