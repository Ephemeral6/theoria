"""The systematic sweep — one policy, run identically on every level.

The bill A3 reports is only a comparison if both levels are explored by the
same rule, so the policy is defined once here and parameterised by nothing but
the level.  It is also the reason the sweep is written as an *edge cover*
rather than as an episode: an episode's length depends on where the goal
happens to be, and that would leak level geometry into the cost column.

**The policy.** Visit every reachable `(state, action)` pair exactly once, in a
single connected trajectory:

1. if the current state has an unexecuted action, take the smallest one
   (`ACTIONS` order);
2. otherwise walk the shortest path to the nearest state that still has one,
   recording every step of the walk — a navigation step is a real action and is
   charged as one;
3. stop when nothing is pending.

Determinism is by construction, not by luck: step 1 pops a list in a fixed
order, and step 2 breaks ties on `(path length, state key, first action)`.
`tests/test_world.py::test_sweep_is_byte_stable` runs it twice and compares
bytes.

**Reversibility is what makes this policy available at all** (F-12, from
`cold-start-a0/prime`).  In an irreversible world step 2 is not always possible
— a latch that has fired cannot be un-fired, so the states behind it are gone
and their pending actions can never be reached.  A3's world is undirected, so
the sweep terminates with genuinely zero pending pairs, and every rule the
manual later states has as many witnesses as its geometry admits.  A manual
mined from this trace has no thin-evidence clause anywhere in it, which is the
precondition for A3 testing *transfer* rather than testing whether level 1
happened to get lucky.

`coverage_report` is the honest accounting: pairs covered, pairs reachable, and
the census of guard contexts actually exercised, which is what
`tests/test_transfer.py` compares between levels.
"""

from collections import deque
from typing import Dict, List, Optional, Sequence, Tuple

from a3world.a3_world import ACTIONS, A3World, LevelSpec, State

Trajectory = Tuple[List[State], List[Optional[str]]]


def _outgoing(incoming: Sequence[Optional[str]]) -> List[Optional[str]]:
    """Re-key an action list from "what produced frame t" to "what is taken at
    frame t", which is the convention A0's trace format uses and A0's
    `multi_miner.build_transitions` depends on: it stops at the first `None`,
    so an incoming-keyed trace mines zero transitions and says nothing about
    why.  The last frame's action is `None` — there is no successor to name.
    """
    return list(incoming[1:]) + [None]


def _shortest_path(world: A3World, start: State,
                   wanted: Sequence[Tuple[int, int, int]]) -> List[str]:
    """Fewest actions from `start` to any state key in `wanted`.

    Ties break on `(depth, state key, action)`, which is total, so the walk is
    a function of the level alone.
    """
    target = set(wanted)
    if start.key() in target:
        return []
    seen = {start.key()}
    queue = deque([(start, [])])
    best: Optional[Tuple[int, Tuple[int, int, int], List[str]]] = None
    while queue:
        state, path = queue.popleft()
        if best is not None and len(path) >= best[0]:
            break
        for action in ACTIONS:
            nxt = world.step(state, action)
            if nxt.key() in seen:
                continue
            seen.add(nxt.key())
            candidate = path + [action]
            if nxt.key() in target:
                key = (len(candidate), nxt.key(), candidate)
                if best is None or key[:2] < best[:2]:
                    best = key
                continue
            queue.append((nxt, candidate))
    return best[2] if best else []


def sweep(world: A3World) -> Trajectory:
    """Every reachable (state, action) pair, once, as one connected trajectory."""
    pending: Dict[Tuple[int, int, int], List[str]] = {
        s.key(): list(ACTIONS) for s in world.reachable()
    }

    current = world.initial()
    states: List[State] = [current]
    actions: List[Optional[str]] = [None]

    def take(action: str) -> None:
        nonlocal current
        todo = pending.get(current.key())
        if todo is not None and action in todo:
            todo.remove(action)
        current = world.step(current, action)
        states.append(current)
        actions.append(action)

    while True:
        todo = pending.get(current.key()) or []
        if todo:
            take(todo[0])
            continue
        remaining = sorted(k for k, v in pending.items() if v)
        if not remaining:
            break
        path = _shortest_path(world, current, remaining)
        if not path:                       # unreachable pending work: impossible
            break                          # in a reversible world; guarded anyway
        for action in path:
            take(action)

    return states, _outgoing(actions)


def coverage_report(world: A3World, states: Sequence[State],
                    actions: Sequence[Optional[str]]) -> Dict[str, object]:
    """What the sweep actually established, in the units the manual is written in."""
    reachable = world.reachable()
    total_pairs = len(reachable) * len(ACTIONS)

    executed = set()
    for t in range(len(states) - 1):        # actions are outgoing-keyed
        executed.add((states[t].key(), actions[t]))

    census = world.guard_contexts()
    return {
        "level": world.spec.name,
        "frames": len(states),
        "transitions": len(states) - 1,
        "reachable_states": len(reachable),
        "pairs_reachable": total_pairs,
        "pairs_covered": len(executed),
        "coverage": round(len(executed) / total_pairs, 6) if total_pairs else 0.0,
        "guard_contexts": census,
        "rule_generating_contexts": sorted(
            k for k in census
            if k.split("_")[0] in ("push", "teleport", "switch")
        ),
    }


def solved_episode(world: A3World) -> Trajectory:
    """The referee's winning run, delivered to the pipeline only as frames."""
    plan = world.solve()
    if plan is None:
        return [world.initial()], [None]
    states = [world.initial()]
    actions: List[Optional[str]] = [None]
    for action in plan:
        states.append(world.step(states[-1], action))
        actions.append(action)
    return states, _outgoing(actions)


def first_frame(spec: LevelSpec) -> List[List[int]]:
    """The single frame the transfer arm is allowed to see (M-T1).

    A separate entry point, so "the transfer arm saw one frame" is a property of
    the call graph and not of a promise in a report.
    """
    world = A3World(spec)
    return world.render(world.initial())
