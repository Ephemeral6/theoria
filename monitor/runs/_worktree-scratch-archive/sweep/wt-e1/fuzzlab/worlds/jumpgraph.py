"""Random peg-jump graphs -- the fuzz generalisation of Fixture C (peg4).

`lp_potential` models exactly one kind of world, and hard-codes its semantics in
`Move.delta`: a jump `(src, over, dst)` needs pegs at `src` and `over` and a hole
at `dst`, and leaves holes at `src` and `over` and a peg at `dst`.  So the free
parameter is the *geometry* -- which triples exist -- not the rule.  A generated
world here is `n` positions plus an arbitrary set of jump triples, which covers
1-D peg solitaire, the English board, and a great many boards nobody has built.

The whole `2^n` state space is enumerated (`n <= 9`, so at most 512 states), which
is what makes the oracles exact: "the certificate is sound" is checked by BFS
over the real reachable set, not by re-running the LP.  That enumeration is the
reason `n` is capped rather than the engine being slow.

The emitted dict is the same shape `fixtures/peg4.py` writes, because that shape
is what `solve_certificate` and `admissibility_report` read:
`n_pos`, `goal_states`, `states`, `move_instances`, `edges`, `distance_to_goal`.
"""

from collections import deque
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence, Tuple

from fuzzlab.prng import Rng
from fuzzlab.worlds.common import World

MAX_POSITIONS = 9


@dataclass(frozen=True)
class JumpSpec:
    seed: int
    n_pos: int
    triples: Tuple[Tuple[int, int, int], ...]     # (src, over, dst)
    goal_states: Tuple[str, ...]
    initial: str
    solvable: bool
    n_reachable: int

    def json(self) -> Dict[str, Any]:
        return {
            "seed": self.seed,
            "n_pos": self.n_pos,
            "triples": [list(t) for t in self.triples],
            "goal_states": list(self.goal_states),
            "initial": self.initial,
            "solvable": self.solvable,
            "n_reachable": self.n_reachable,
        }


@dataclass
class JumpWorld(World):
    spec: JumpSpec
    graph: Dict[str, Any]

    family = "jumpgraph"

    @property
    def seed(self) -> int:
        return self.spec.seed

    def spec_json(self) -> Dict[str, Any]:
        return self.spec.json()

    @property
    def initial(self) -> str:
        return self.spec.initial

    @property
    def goal_states(self) -> List[str]:
        return list(self.spec.goal_states)


# ------------------------------------------------------------------ semantics

def all_states(n: int) -> List[str]:
    return [format(i, "0%db" % n) for i in range(1 << n)]


def legal(state: str, triple: Tuple[int, int, int]) -> bool:
    src, over, dst = triple
    return state[src] == "1" and state[over] == "1" and state[dst] == "0"


def apply(state: str, triple: Tuple[int, int, int]) -> str:
    src, over, dst = triple
    cells = list(state)
    cells[src] = "0"
    cells[over] = "0"
    cells[dst] = "1"
    return "".join(cells)


def successors(state: str, triples: Sequence[Tuple[int, int, int]]) -> List[str]:
    return [apply(state, t) for t in triples if legal(state, t)]


def distances_to_goals(triples: Sequence[Tuple[int, int, int]], n: int,
                       goals: Sequence[str]) -> Dict[str, Optional[int]]:
    """Backward BFS from the goal set over the reversed move relation.

    Reversed rather than one forward BFS per state: `2^n` forward searches would
    dominate the campaign's runtime, and the answer is the same number.
    """
    predecessors: Dict[str, List[str]] = {}
    for state in all_states(n):
        for triple in triples:
            if legal(state, triple):
                predecessors.setdefault(apply(state, triple), []).append(state)

    dist: Dict[str, Optional[int]] = {g: 0 for g in goals}
    queue = deque(goals)
    while queue:
        state = queue.popleft()
        for prev in predecessors.get(state, ()):
            if prev not in dist:
                dist[prev] = dist[state] + 1
                queue.append(prev)
    return {state: dist.get(state) for state in all_states(n)}


def reachable_from(start: str, triples: Sequence[Tuple[int, int, int]]) -> List[str]:
    seen = {start}
    queue = deque([start])
    while queue:
        state = queue.popleft()
        for nxt in successors(state, triples):
            if nxt not in seen:
                seen.add(nxt)
                queue.append(nxt)
    return sorted(seen)


def build_graph(n: int, triples: Sequence[Tuple[int, int, int]],
                goals: Sequence[str], initial: str) -> Dict[str, Any]:
    states = all_states(n)
    edges = []
    for state in states:
        for triple in triples:
            if legal(state, triple):
                edges.append(
                    {
                        "src_state": state,
                        "move": "jump(%d,%d,%d)" % triple,
                        "positions": list(triple),
                        "dst_state": apply(state, triple),
                    }
                )
    return {
        "n_pos": n,
        "goal": goals[0],
        "goal_states": list(goals),
        "states": states,
        "move_instances": [
            {"src": s, "over": o, "dst": d} for (s, o, d) in triples
        ],
        "edges": edges,
        "initial_configs": [initial],
        "reachable": {initial: reachable_from(initial, triples)},
        "distance_to_goal": distances_to_goals(triples, n, goals),
    }


# ------------------------------------------------------------------ generator

def generate(seed: int) -> JumpWorld:
    """A peg-jump world, a pure function of `seed`."""
    rng = Rng(seed)

    n = rng.between(4, MAX_POSITIONS)

    # Candidate geometries: any ordered triple of distinct positions.  A "linear"
    # draw keeps the classic collinear jumps (over is between src and dst), a
    # "wild" draw allows any triple -- the engine's algebra never assumed
    # collinearity and should not start now.
    linear = rng.chance(1, 2)
    candidates: List[Tuple[int, int, int]] = []
    for src in range(n):
        for over in range(n):
            for dst in range(n):
                if len({src, over, dst}) != 3:
                    continue
                if linear and not (over - src == dst - over):
                    continue
                candidates.append((src, over, dst))
    if not candidates:                                    # pragma: no cover
        candidates = [(0, 1, 2)]

    n_triples = rng.between(1, min(len(candidates), 2 * n))
    triples = tuple(sorted(rng.sample(candidates, n_triples)))

    states = all_states(n)
    n_goals = rng.between(1, 2)
    goals = tuple(sorted(rng.sample(states, n_goals)))

    initial = rng.choice(states)

    graph = build_graph(n, triples, goals, initial)
    reach = graph["reachable"][initial]
    solvable = any(g in reach for g in goals)

    spec = JumpSpec(
        seed=seed, n_pos=n, triples=triples, goal_states=goals,
        initial=initial, solvable=solvable, n_reachable=len(reach),
    )
    return JumpWorld(spec=spec, graph=graph)
