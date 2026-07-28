"""Is the world winnable, and if not, what is the proof?

Solvable is easy: BFS from the initial state and keep the shortest action
sequence.  The interesting half is the other one.  `engine-rig`'s `lp_potential`
is sound but incomplete — it never certifies a *solvable* configuration and some
genuinely unsolvable ones admit no linear pagoda — so an unsolvable world in
this catalogue ships a certificate of a kind that is always available for a
finite state space, and two hints at the shape a real proof would take:

1. **the exhaustive one** — the reachable set is finite and fully enumerated, the
   goal is in none of it.  That is a proof, just an unenlightening one;
2. **the separating frontier** — the cells the agent can ever occupy, and the
   impassable cells that fence them off.  Those cells are the candidate cut, and
   they are what a hand proof or a pagoda function would have to talk about;
3. **the single-change flip** — for each entity in turn, the same question asked
   of the world with that entity deleted.  An entity whose removal makes the
   world solvable is *the* blocker, and naming it is what turns "no path exists"
   into "the Door never opens because nothing drives it".

(3) is a search over `len(entities)` worlds, so it is only run when asked; the
catalogue asks for it, because the resulting sentence is what an unsolvable
world is *for*.
"""

from collections import deque
from dataclasses import replace
from typing import Any, Dict, List, Optional, Tuple

from .spec import WorldSpec
from .types import ACTIONS, Cell, State
from .world import GridWorld


def solve(world: GridWorld) -> Optional[List[str]]:
    """A shortest winning action sequence, or None if there is none."""
    start = world.initial()
    if world.is_win(start):
        return []
    seen = {start.key()}
    queue = deque([(start, [])])
    while queue:
        state, path = queue.popleft()
        for action in ACTIONS:
            nxt = world.step(state, action)
            if nxt.key() in seen:
                continue
            seen.add(nxt.key())
            if world.is_win(nxt):
                return path + [action]
            queue.append((nxt, path + [action]))
    return None


def agent_cells(world: GridWorld) -> List[Cell]:
    return sorted({s.agent for s in world.reachable()})


def frontier(world: GridWorld) -> List[Dict[str, Any]]:
    """Cells adjacent to somewhere the agent can stand that it can never enter.

    Computed over the reachable set rather than over the initial frame, so a door
    that opens somewhere in the middle of the game is correctly *not* in the
    frontier.  What remains is the honest cut.
    """
    from .types import DELTA

    reachable = world.reachable()
    standable = {s.agent for s in reachable}
    ever_free = set()
    for state in reachable:
        occupied = world.occupied(state)
        for r in range(world.spec.height):
            for c in range(world.spec.width):
                if (r, c) not in occupied:
                    ever_free.add((r, c))

    kinds = {e.cell: e.kind for e in world.spec.entities}
    out: List[Dict[str, Any]] = []
    for cell in sorted(standable):
        for dr, dc in DELTA.values():
            neighbour = (cell[0] + dr, cell[1] + dc)
            if not world.in_bounds(neighbour) or neighbour in standable:
                continue
            if neighbour in world.walls:
                continue                      # walls are not news
            out.append({
                "cell": list(neighbour),
                "kind": kinds.get(neighbour, "floor"),
                "ever_passable": neighbour in ever_free,
            })
    seen = set()
    unique = []
    for row in out:
        key = tuple(row["cell"])
        if key not in seen:
            seen.add(key)
            unique.append(row)
    return unique


def _deletion_groups(spec: WorldSpec) -> List[Tuple[str, Tuple[int, ...]]]:
    """Index sets to try deleting: singletons, plus each portal pair as a unit.

    Deleting one mouth of a two-way portal leaves a spec `Portal._links` rejects,
    so a one-at-a-time sweep produced `invalid: portal pair 'p' has 1 mouth(s)`
    twice and named no blocker at all — the certificate's whole job, missing on
    exactly the worlds most likely to need it. A pair is one thing; it is deleted
    as one thing.
    """
    groups: List[Tuple[str, Tuple[int, ...]]] = []
    pairs: Dict[str, List[int]] = {}
    for i, entity in enumerate(spec.entities):
        label = entity.prop("pair")
        if entity.kind == "portal" and label is not None:
            pairs.setdefault(str(label), []).append(i)
        else:
            groups.append((entity.kind, (i,)))
    for label in sorted(pairs):
        groups.append(("portal pair %r" % label, tuple(pairs[label])))
    return groups


def blocking_entities(spec: WorldSpec) -> List[Dict[str, Any]]:
    """Which deletion would make an unsolvable world solvable?"""
    out: List[Dict[str, Any]] = []
    for label, indices in _deletion_groups(spec):
        trimmed = replace(spec, entities=tuple(
            e for j, e in enumerate(spec.entities) if j not in indices
        ))
        described = [spec.entities[j].as_json() for j in indices]
        try:
            plan = solve(GridWorld(trimmed))
        except Exception as exc:                  # a deletion can still break a spec
            out.append({"entity": described[0], "entities": described, "label": label,
                        "verdict": "invalid: %s" % exc})
            continue
        if plan is not None:
            out.append({"entity": described[0], "entities": described, "label": label,
                        "verdict": "removing it makes the world solvable in %d steps"
                                   % len(plan)})
    return out


def report(world: GridWorld, diagnose: bool = True) -> Dict[str, Any]:
    plan = solve(world)
    states = world.reachable()
    out: Dict[str, Any] = {
        "world_id": world.spec.world_id,
        "solvable": plan is not None,
        "reachable_states": len(states),
        "agent_cells": len(agent_cells(world)),
        "goal": list(world.spec.goal),
    }
    if plan is not None:
        out["optimal_plan"] = plan
        out["optimal_length"] = len(plan)
        return out

    out["certificate"] = {
        "kind": "exhaustive_reachability",
        "statement": "the reachable set has %d states and the agent occupies the "
                     "goal cell %r in none of them" % (len(states), tuple(world.spec.goal)),
        "separating_frontier": frontier(world),
    }
    if diagnose:
        out["certificate"]["blocking_entities"] = blocking_entities(world.spec)
    return out
