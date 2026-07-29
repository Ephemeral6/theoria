"""Replay A2's recorded 18-action winning episode (the WORLD's own frames)
through the a2-world rule set, frame by frame, pixel by pixel."""

import sys
sys.dont_write_bytecode = True

import json
import os

RIG = r"C:\Users\user\Desktop\theoria\.worktrees\e5-cert-recheck\engine-rig"
A2 = r"C:\Users\user\Desktop\theoria\cold-start-a2"
sys.path.insert(0, RIG)
from recheck.ruleset import load_ruleset  # noqa: E402

rows = [json.loads(l) for l in open(os.path.join(A2, "artifacts", "solved_episode.jsonl"),
                                    encoding="utf-8")]
print("episode frames:", len(rows), "actions:", [r["action"] for r in rows if r["action"]])

for case in ("a2-world.rules.json", "a2-holed.rules.json"):
    rs = load_ruleset(os.path.join(RIG, "recheck", "cases", case))
    rendered = rs.scope.macros["rendered"]
    s = rs.init[0]
    bad_pixels = 0
    first_bad = None
    for i, row in enumerate(rows):
        frame = row["frame"]
        for r in range(9):
            for c in range(9):
                got = rendered(s, None, ("%d,%d" % (r, c),))
                if got != frame[r][c]:
                    bad_pixels += 1
                    if first_bad is None:
                        first_bad = (i, (r, c), got, frame[r][c])
        win = rs.goal(s)
        if win != bool(row["win"]):
            print("   %s: win flag disagrees at t=%d (rules=%s episode=%s)"
                  % (case, i, win, row["win"]))
        act = row["action"]
        if act:
            s = rs.step(s, act.lower())
    print("%-22s replayed %d frames, %d mispredicted pixels; first=%s"
          % (case, len(rows), bad_pixels, first_bad))
