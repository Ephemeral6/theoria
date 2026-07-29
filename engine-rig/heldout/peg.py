"""Corpus L -- `pegN`, Fixture C generalised in the number of positions.

`fixtures/peg4.py` hard-codes `N_POS = 4` and `GOAL = "0100"` at module level, so
its functions cannot be re-parameterised without editing a committed fixture.
The geometry is ten lines, so it is restated here and then *checked against* the
fixture: `matches_fixture_peg4()` compares this generator's `n = 4, goal = 0100`
graph against `fixtures.peg4.generate()` field by field.  If that gate fails the
run is void -- see PREREGISTRATION.md section 1.
"""

from collections import deque
from typing import Dict, List, Optional, Tuple


def all_states(n: int) -> List[str]:
    return ["".join(bits) for bits in _bit_tuples(n)]


def _bit_tuples(n: int) -> List[Tuple[str, ...]]:
    out: List[Tuple[str, ...]] = [()]
    for _ in range(n):
        out = [t + (b,) for t in out for b in ("0", "1")]
    return sorted(out)


def move_instances(n: int) -> List[Dict[str, int]]:
    out = []
    for i in range(n):
        for step in (1, -1):
            over, dst = i + step, i + 2 * step
            if 0 <= dst < n:
                out.append({"src": i, "over": over, "dst": dst})
    return sorted(out, key=lambda m: (m["src"], m["dst"]))


def legal(state: str, move: Dict[str, int]) -> bool:
    return (state[move["src"]] == "1" and state[move["over"]] == "1"
            and state[move["dst"]] == "0")


def apply(state: str, move: Dict[str, int]) -> str:
    cells = list(state)
    cells[move["src"]] = "0"
    cells[move["over"]] = "0"
    cells[move["dst"]] = "1"
    return "".join(cells)


def edges(n: int) -> List[Dict[str, object]]:
    out = []
    for state in all_states(n):
        for move in move_instances(n):
            if legal(state, move):
                out.append({
                    "src_state": state,
                    "move": "jump(%d,%d,%d)" % (move["src"], move["over"], move["dst"]),
                    "positions": [move["src"], move["over"], move["dst"]],
                    "dst_state": apply(state, move),
                })
    return out


def successors(n: int, state: str) -> List[str]:
    return [apply(state, m) for m in move_instances(n) if legal(state, m)]


def distance_to_goal(n: int, start: str, goal: str) -> Optional[int]:
    if start == goal:
        return 0
    dist = {start: 0}
    queue = deque([start])
    while queue:
        state = queue.popleft()
        for nxt in successors(n, state):
            if nxt not in dist:
                dist[nxt] = dist[state] + 1
                if nxt == goal:
                    return dist[nxt]
                queue.append(nxt)
    return None


def graph(n: int, goal: str) -> Dict[str, object]:
    states = all_states(n)
    return {
        "n_pos": n,
        "goal": goal,
        "goal_states": [goal],
        "states": states,
        "move_instances": move_instances(n),
        "edges": edges(n),
        "distance_to_goal": {s: distance_to_goal(n, s, goal) for s in states},
    }


def graph_minus_geometry(g: Dict[str, object], positions: Tuple[int, int, int]
                         ) -> Dict[str, object]:
    """The same graph with every edge of one jump geometry deleted.

    `distance_to_goal` is deliberately **not** recomputed: it is the ground truth
    the held-out claim is scored against, and it must describe the real world,
    not the truncated evidence the LP was shown.
    """
    keep = [e for e in g["edges"] if tuple(e["positions"]) != tuple(positions)]  # type: ignore[index]
    out = dict(g)
    out["edges"] = keep
    return out


def geometries(g: Dict[str, object]) -> List[Tuple[int, int, int]]:
    seen: List[Tuple[int, int, int]] = []
    for e in g["edges"]:                                   # type: ignore[index]
        key = tuple(e["positions"])                        # type: ignore[index]
        if key not in seen:
            seen.append(key)
    return sorted(seen)


def matches_fixture_peg4() -> Tuple[bool, List[str]]:
    """Gate: this generator must reproduce the committed Fixture C exactly."""
    from fixtures import peg4

    reference = peg4.generate()
    mine = graph(4, peg4.GOAL)
    problems: List[str] = []
    for field in ("n_pos", "goal", "goal_states", "states", "move_instances",
                  "edges", "distance_to_goal"):
        if mine[field] != reference[field]:
            problems.append(field)
    solvable = {s: distance_to_goal(4, s, peg4.GOAL) is not None
                for s in peg4.INITIAL_CONFIGS}
    if solvable != reference["solvable"]:
        problems.append("solvable")
    return (not problems), problems
