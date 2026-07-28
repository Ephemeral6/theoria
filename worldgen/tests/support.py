"""Shared helpers for the test suite.  Not a test module.

`GridWorld.reachable()` is cheap per call but the suite asks for it from a dozen
angles, and the biggest world in the catalogue (`t3-full-house`, 2654 states) is
walked by almost every structural test.  Caching the built world and its
reachable set here keeps the whole catalogue sweep under a second, which is what
lets those tests be property-style over all twenty worlds instead of a sample.

Nothing here mutates a world, so sharing one instance between tests is safe:
`GridWorld` holds only the spec and the bound mechanisms, and every mechanism in
`worldgen/mechanisms/` re-reads its parameters from the spec on each call rather
than caching them (see `Portal._links`, `ColorCycle._params`) precisely because a
single registry instance is shared across worlds.
"""

import functools
import os
from typing import List, Tuple

from worldgen.core.types import State
from worldgen.core.world import GridWorld
from worldgen.generate import BY_ID, CATALOGUE

WORLD_IDS: Tuple[str, ...] = tuple(spec.world_id for spec in CATALOGUE)

# Where `python -m worldgen.build` puts the shipped artefacts.
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "out", "worlds")


@functools.lru_cache(maxsize=None)
def world(world_id: str) -> GridWorld:
    return GridWorld(BY_ID[world_id])


@functools.lru_cache(maxsize=None)
def reachable(world_id: str) -> Tuple[State, ...]:
    return tuple(world(world_id).reachable())


def trace_path(world_id: str) -> str:
    return os.path.join(OUT, world_id, "raw_trace.jsonl")


def drive(grid: GridWorld, actions: List[str]) -> Tuple[State, List[str]]:
    """Apply `actions` from the initial state; return the final state and the
    rule tag each step fired.  Used by the regression tests, which state a defect
    as a scripted trajectory rather than as a search over the reachable graph."""
    state = grid.initial()
    rules: List[str] = []
    for action in actions:
        state, rule = grid.explain(state, action)
        rules.append(rule)
    return state, rules
