"""Fixture C - a 4-cell 1D peg solitaire, enumerated in full.

Four positions in a row.  A move takes a peg at i, jumps it over a peg at i+-1
into an empty hole at i+-2, and removes the jumped peg.  Every move removes
exactly one peg.

The state space is 2^4 = 16, so everything is enumerated rather than searched:
all states, all legal move instances (over the *whole* space, not just the
reachable part -- the LP certificate has to be closed under moves from any state
satisfying the invariant, not merely from the states this fixture happens to
visit), and BFS distances to the goal.

Goal: exactly one peg, at position 1 -- state 0100.

Hand-verified reachability (each 3-peg start, by exhaustive expansion):
    1110 -> 1001 (dead end)             UNSOLVABLE
    0111 -> 1001 (dead end)             UNSOLVABLE
    1011 -> 1100 -> 0010                UNSOLVABLE (ends on position 2)
    1101 -> 0011 -> 0100                SOLVABLE in 2 moves
The enumeration below re-derives this; the test cross-checks it against these
literals so a bug in the enumerator cannot silently redefine the ground truth.
"""

import os
from collections import deque
from typing import Dict, List, Optional, Tuple

from common.jsonio import write_json

N_POS = 4
GOAL = "0100"
INITIAL_CONFIGS = ("1110", "0111", "1011", "1101")

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
GRAPH_PATH = os.path.join(DATA_DIR, "peg4_graph.json")


def all_states() -> List[str]:
    return ["".join(bits) for bits in _bit_tuples(N_POS)]


def _bit_tuples(n: int) -> List[Tuple[str, ...]]:
    out: List[Tuple[str, ...]] = [()]
    for _ in range(n):
        out = [t + (b,) for t in out for b in ("0", "1")]
    return sorted(out)


def move_instances() -> List[Dict[str, int]]:
    """Every jump the geometry allows, as (src, over, dst) position triples."""
    out = []
    for i in range(N_POS):
        for step in (1, -1):
            over, dst = i + step, i + 2 * step
            if 0 <= dst < N_POS:
                out.append({"src": i, "over": over, "dst": dst})
    return sorted(out, key=lambda m: (m["src"], m["dst"]))


def legal(state: str, move: Dict[str, int]) -> bool:
    return (
        state[move["src"]] == "1"
        and state[move["over"]] == "1"
        and state[move["dst"]] == "0"
    )


def apply(state: str, move: Dict[str, int]) -> str:
    cells = list(state)
    cells[move["src"]] = "0"
    cells[move["over"]] = "0"
    cells[move["dst"]] = "1"
    return "".join(cells)


def edges() -> List[Dict[str, object]]:
    """All (state, move, successor) triples over the full state space."""
    out = []
    for state in all_states():
        for move in move_instances():
            if legal(state, move):
                out.append(
                    {
                        "src_state": state,
                        "move": "jump(%d,%d,%d)" % (move["src"], move["over"], move["dst"]),
                        "positions": [move["src"], move["over"], move["dst"]],
                        "dst_state": apply(state, move),
                    }
                )
    return out


def successors(state: str) -> List[str]:
    return [apply(state, m) for m in move_instances() if legal(state, m)]


def reachable_from(start: str) -> List[str]:
    seen = {start}
    queue = deque([start])
    while queue:
        state = queue.popleft()
        for nxt in successors(state):
            if nxt not in seen:
                seen.add(nxt)
                queue.append(nxt)
    return sorted(seen)


def distance_to_goal(start: str, goal: str = GOAL) -> Optional[int]:
    """BFS distance in moves, or None if the goal is unreachable."""
    if start == goal:
        return 0
    dist = {start: 0}
    queue = deque([start])
    while queue:
        state = queue.popleft()
        for nxt in successors(state):
            if nxt not in dist:
                dist[nxt] = dist[state] + 1
                if nxt == goal:
                    return dist[nxt]
                queue.append(nxt)
    return None


def generate() -> Dict[str, object]:
    states = all_states()
    graph = {
        "n_pos": N_POS,
        "goal": GOAL,
        "goal_states": [GOAL],
        "states": states,
        "move_instances": move_instances(),
        "edges": edges(),
        "initial_configs": list(INITIAL_CONFIGS),
        "reachable": {s: reachable_from(s) for s in INITIAL_CONFIGS},
        "distance_to_goal": {s: distance_to_goal(s) for s in states},
        "solvable": {s: distance_to_goal(s) is not None for s in INITIAL_CONFIGS},
    }
    return graph


def write(path: str = GRAPH_PATH) -> Dict[str, object]:
    graph = generate()
    write_json(path, graph)
    return graph


if __name__ == "__main__":  # pragma: no cover
    g = write()
    print("peg4: %d states, %d edges -> %s" % (len(g["states"]), len(g["edges"]), GRAPH_PATH))
    for cfg in INITIAL_CONFIGS:
        print("  %s solvable=%s reachable=%s" % (cfg, g["solvable"][cfg], g["reachable"][cfg]))
