"""M6 — 打脸.  Someone solved it, and the frames say so.

Theoria §1.4: an "impossible" assertion becomes informative the moment reality
contradicts it, and what contradicts it is a **solved episode**.  This module
produces one, and it is careful about the channel it comes through.

*The world hands back frames, not reasons.*  `A2World.solve()` is the
environment's own search — the stand-in for "有人解出来了" — but what it returns
here is written out as `artifacts/solved_episode.jsonl`, the same four-field
rows as every other trace: `t`, `frame`, `action`, `win`.  Everything downstream
(M7 locate, M8 probe) reads that file.  Nothing downstream imports `a2world`,
reads `ground_truth.json`, or otherwise looks at the world's source.  The
refutation is evidence, and evidence in this project means pixels.

What the refutation establishes, and what it does not:

* **establishes** — `unsolvable`, the theorem `theory/generated_holed/theory.lean`
  proves with an empty axiom list, is false of the world.  A 18-action episode
  ends on the goal cell with `win: true`.
* **does not establish** — where the manual is wrong.  §1.4 gives the search
  space (the error is necessarily on this path, in one of three places) but not
  the answer.  That is M7.
"""

import json
import os
import sys
from typing import Dict, List

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import _bootstrap  # noqa: F401,E402

from a2world import a2_world  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARTIFACTS = os.path.join(ROOT, "artifacts")
EPISODE = os.path.join(ARTIFACTS, "solved_episode.jsonl")


def solved_episode(spec=a2_world.BASE) -> Dict[str, object]:
    """Play a winning episode in the world and write it out as frames."""
    world = a2_world.A2World(spec)
    actions = world.solve()
    if actions is None:
        raise AssertionError(
            "the world does not solve its own goal — then there is no exhibit, "
            "because the holed manual's theorem would be true")

    state = world.initial()
    states = [state]
    for action in actions:
        state = world.step(state, action)
        states.append(state)

    rows: List[Dict[str, object]] = []
    for t, s in enumerate(states):
        rows.append({
            "t": t,
            "frame": world.render(s),
            "action": actions[t] if t < len(actions) else None,
            "win": world.is_win(s),
        })
    with open(EPISODE, "w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True,
                                    separators=(",", ":")) + "\n")
    return {
        "path": os.path.relpath(EPISODE, ROOT),
        "actions": list(actions),
        "length": len(actions),
        "frames": len(rows),
        "final_win": rows[-1]["win"],
        "win_frames": [r["t"] for r in rows if r["win"]],
    }


def main() -> int:
    exhibit_path = os.path.join(ARTIFACTS, "exhibit_report.json")
    exhibit = json.load(open(exhibit_path, encoding="utf-8"))

    episode = solved_episode()
    claim = {
        "theorem": exhibit["theorem"]["name"],
        "lean_target": exhibit["theorem"]["lean_target"],
        "lean_green": exhibit["certify_lean"]["green"],
        "lean_axioms": exhibit["theorem"]["axioms"],
        "says": "no reachable state satisfies Goal, i.e. the Cart can never "
                "occupy the goal cell (2,7)",
    }
    report = {
        "claim": claim,
        "episode": episode,
        "refuted": bool(episode["final_win"]),
        "verdict": (
            "REFUTED — the episode ends on the goal cell with win=true, so the "
            "machine-checked, axiom-free theorem `unsolvable` is false of the "
            "world.  Nothing in the proof is broken: it is true relative to the "
            "manual, and the manual is missing a rule.  Theoria §1.4 now bounds "
            "the search: the error is necessarily on this path — a mispredicted "
            "step, a wrong goal test, or a misread board.  Three places, and M7 "
            "checks all three."
        ),
        "search_space_per_1_4": [
            "some transition on this path is mispredicted by the manual",
            "the manual's goal test disagrees with the episode's win flag",
            "the manual misread the board at frame 0",
        ],
    }
    with open(os.path.join(ARTIFACTS, "refutation.json"), "w",
              encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(report, indent=2, sort_keys=True) + "\n")

    print("claim :", claim["says"])
    print("        lean green=%s axioms=%s"
          % (claim["lean_green"], json.dumps(claim["lean_axioms"])))
    print("world :", "%d actions, win on frame %s"
          % (episode["length"], episode["win_frames"]))
    print("verdict: REFUTED" if report["refuted"] else "verdict: NOT refuted")
    return 0 if report["refuted"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
