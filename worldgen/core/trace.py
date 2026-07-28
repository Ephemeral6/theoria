"""`raw_trace.jsonl` — byte-identical in shape to cold-start-a0's.

One JSON object per line, keys sorted, compact separators, LF endings:

```json
{"action":"DOWN","frame":[[1,1,...],...],"t":0,"win":false}
```

The format is copied rather than improved on purpose.  `cold-start-a0` and its
`prime` spike both read exactly this, and the point of this library is that
their pipelines can consume a worldgen world with **no downstream change at
all** — so the last row carries `"action": null`, the goal cell is not rendered,
and the win signal rides in the row rather than in the grid, all as they do.

`append_probe` exists for the same reason: A0′ appends probe frames to the same
append-only file so that a revised manual's replay covers the probe as well.
"""

import json
import os
from typing import Any, Dict, List, Optional, Sequence, Tuple

from .types import State
from .world import GridWorld


def rows(world: GridWorld, states: Sequence[State],
         actions: Sequence[Optional[str]]) -> List[Dict[str, Any]]:
    return [
        {"t": t, "frame": world.render(state), "action": actions[t],
         "win": world.is_win(state)}
        for t, state in enumerate(states)
    ]


def write_trace(path: str, world: GridWorld, states: Sequence[State],
                actions: Sequence[Optional[str]]) -> int:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        for row in rows(world, states, actions):
            handle.write(json.dumps(row, sort_keys=True,
                                    separators=(",", ":")) + "\n")
    return len(states)


def append_probe(path: str, world: GridWorld, states: Sequence[State],
                 actions: Sequence[Optional[str]], tag: str) -> None:
    start = sum(1 for _ in open(path, encoding="utf-8"))
    with open(path, "a", encoding="utf-8", newline="\n") as handle:
        for i, state in enumerate(states):
            row = {"t": start + i, "frame": world.render(state),
                   "action": actions[i], "win": world.is_win(state),
                   "probe": tag}
            handle.write(json.dumps(row, sort_keys=True,
                                    separators=(",", ":")) + "\n")


def read_trace(path: str) -> Tuple[List[List[List[int]]], List[Optional[str]], List[bool]]:
    """The reader `cold-start-a0/world/ground_truth.py` exposes, repeated here so
    that worldgen's own tests do not have to import the other track's package."""
    frames: List[List[List[int]]] = []
    actions: List[Optional[str]] = []
    wins: List[bool] = []
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            frames.append(row["frame"])
            actions.append(row["action"])
            wins.append(bool(row["win"]))
    return frames, actions, wins
