"""Corpus Z -- `parityworld`, the family Fixture B is one member of.

`n` cells, each always holding exactly one of two colours.  An *operation* is a
contiguous window of `k` cell indices; applying it flips every cell in the
window.  `pair_flip` is `n = 8, k = 2` with the same window rule, so Fixture B is
inside this family rather than beside it.

Generated in memory.  Nothing under `fixtures/data/` is read or written -- the
committed fixtures are byte-pinned artifacts and this run does not touch them.
"""

from dataclasses import dataclass
from typing import List, Sequence, Tuple

from common.rng import SplitMix64

COLORS: Tuple[str, str] = ("B", "R")
N_CELLS = (6, 8, 10)
WIDTHS = (2, 3)
N_TRANSITIONS = 60
WORLDS_PER_SETTING = 20
SEED_BASE = 0xE17A0000


@dataclass
class ParityWorld:
    world_id: str
    n_cells: int
    width: int
    seed: int
    operations: List[Tuple[int, ...]]
    actions: List[int]                    # index into `operations`, one per transition
    states: List[Tuple[str, ...]]         # len(actions) + 1


def operations_for(n_cells: int, width: int) -> List[Tuple[int, ...]]:
    return [tuple(range(i, i + width)) for i in range(n_cells - width + 1)]


def apply(state: Sequence[str], cells: Sequence[int]) -> Tuple[str, ...]:
    out = list(state)
    for c in cells:
        out[c] = COLORS[0] if out[c] == COLORS[1] else COLORS[1]
    return tuple(out)


def build(n_cells: int, width: int, seed: int, n_transitions: int = N_TRANSITIONS
          ) -> ParityWorld:
    ops = operations_for(n_cells, width)
    rng = SplitMix64(seed)
    initial = tuple(COLORS[rng.below(2)] for _ in range(n_cells))

    # Every operation is witnessed once before the random tail.  This is D-003's
    # own fixture rule, kept deliberately: without it a *random* split would
    # sometimes be a *coverage* split by accident, and Z-S1 would be measuring
    # Z-S2's mechanism under another name.
    actions = list(range(len(ops)))
    while len(actions) < n_transitions:
        actions.append(rng.below(len(ops)))
    actions = actions[:n_transitions]
    if set(actions) != set(range(len(ops))):
        raise AssertionError("not every operation is witnessed in %s" % (seed,))

    state = initial
    states = [state]
    for a in actions:
        state = apply(state, ops[a])
        states.append(state)

    return ParityWorld(
        world_id="pw-n%d-k%d-s%08x" % (n_cells, width, seed),
        n_cells=n_cells,
        width=width,
        seed=seed,
        operations=ops,
        actions=actions,
        states=states,
    )


def corpus() -> List[ParityWorld]:
    out = []
    for n_cells in N_CELLS:
        for width in WIDTHS:
            for i in range(WORLDS_PER_SETTING):
                seed = SEED_BASE + 1000 * n_cells + 100 * width + i
                out.append(build(n_cells, width, seed))
    return out
