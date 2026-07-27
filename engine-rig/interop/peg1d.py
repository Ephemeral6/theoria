"""Generic 1D peg solitaire state graphs, for any board size and goal.

`fixtures/peg4.py` is frozen: it is an M1 acceptance artifact and its bytes are
under test, so it is not the place to grow a parameter. This builder produces the
same shape of graph for an arbitrary board, which is what `lp_potential` needs in
order to answer questions posed by another track rather than only its own fixture.
"""

from collections import deque
from typing import Dict, List, Optional, Sequence

Move = Dict[str, int]


def all_states(n_pos: int) -> List[str]:
    return ["".join(bits) for bits in _bit_tuples(n_pos)]


def _bit_tuples(n: int):
    out = [()]
    for _ in range(n):
        out = [t + (b,) for t in out for b in ("0", "1")]
    return sorted(out)


def move_instances(n_pos: int) -> List[Move]:
    out = []
    for i in range(n_pos):
        for step in (1, -1):
            over, dst = i + step, i + 2 * step
            if 0 <= dst < n_pos:
                out.append({"src": i, "over": over, "dst": dst})
    return sorted(out, key=lambda m: (m["src"], m["dst"]))


def legal(state: str, move: Move) -> bool:
    return (
        state[move["src"]] == "1"
        and state[move["over"]] == "1"
        and state[move["dst"]] == "0"
    )


def apply(state: str, move: Move) -> str:
    cells = list(state)
    cells[move["src"]] = "0"
    cells[move["over"]] = "0"
    cells[move["dst"]] = "1"
    return "".join(cells)


def successors(state: str, n_pos: Optional[int] = None) -> List[str]:
    n_pos = n_pos or len(state)
    return [apply(state, m) for m in move_instances(n_pos) if legal(state, m)]


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


def distance_to(start: str, goals: Sequence[str]) -> Optional[int]:
    goal_set = set(goals)
    if start in goal_set:
        return 0
    dist = {start: 0}
    queue = deque([start])
    while queue:
        state = queue.popleft()
        for nxt in successors(state):
            if nxt not in dist:
                dist[nxt] = dist[state] + 1
                if nxt in goal_set:
                    return dist[nxt]
                queue.append(nxt)
    return None


def single_peg_states(n_pos: int) -> List[str]:
    return ["".join("1" if i == j else "0" for i in range(n_pos)) for j in range(n_pos)]


def build_graph(n_pos: int, initial: str,
                goal_states: Optional[Sequence[str]] = None) -> Dict[str, object]:
    """A graph in the shape `lp_potential` consumes (see fixtures/peg4.py)."""
    goals = list(goal_states or single_peg_states(n_pos))
    states = all_states(n_pos)
    edges = []
    for state in states:
        for move in move_instances(n_pos):
            if legal(state, move):
                edges.append(
                    {
                        "src_state": state,
                        "move": "jump(%d,%d,%d)" % (move["src"], move["over"], move["dst"]),
                        "positions": [move["src"], move["over"], move["dst"]],
                        "dst_state": apply(state, move),
                    }
                )
    return {
        "n_pos": n_pos,
        "goal": goals[0],
        "goal_states": goals,
        "states": states,
        "move_instances": move_instances(n_pos),
        "edges": edges,
        "initial_configs": [initial],
        "reachable": {initial: reachable_from(initial)},
        "distance_to_goal": {s: distance_to(s, goals) for s in states},
        "solvable": {initial: distance_to(initial, goals) is not None},
    }
