"""Random colour-flip worlds -- the fuzz generalisation of Fixture B (Pair-Flip).

`n` cells, each holding one colour from a `k`-symbol palette.  An *operation* is
a subset `S` of cells plus a shift `d`: every cell in `S` advances `d` places
around the palette.  Fixture B is the special case `k=2`, `|S|=2`, `d=1`.

Two flavours, and the distinction is the point:

* **`planted`** -- `k=2` and every operation has even support, so `(#colour) mod 2`
  is genuinely conserved for both colours.  The generator hands that vector over
  as ground truth and the recovery property demands the engine find it.

* **`free`** -- arbitrary `k`, arbitrary supports, arbitrary shifts.  There is no
  planted law; some worlds conserve a great deal and some conserve only the
  encoding's own "each cell holds exactly one colour".  These worlds are checked
  against an *independently computed* null space rather than against a planted
  answer, which is the only honest way to test completeness on a world whose
  answer nobody knows in advance.

A `free` world with `k=2` and at least one odd-support operation that actually
fires carries `breaks_parity`, and then colour parity must **not** be reported --
the negative control that keeps "recovers the law" from being satisfied by an
engine that reports every vector it can think of.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence, Tuple

from fuzzlab.prng import Rng
from fuzzlab.worlds.common import World

PALETTE_SYMBOLS = "ABCDEFGH"


@dataclass(frozen=True)
class Operation:
    cells: Tuple[int, ...]
    shift: int

    def json(self) -> Dict[str, Any]:
        return {"cells": list(self.cells), "shift": self.shift}


@dataclass(frozen=True)
class ParitySpec:
    seed: int
    n_cells: int
    colors: Tuple[str, ...]
    operations: Tuple[Operation, ...]
    initial: Tuple[str, ...]
    script: Tuple[int, ...]                # indices into `operations`
    flavour: str                           # planted | free
    breaks_parity: bool

    def json(self) -> Dict[str, Any]:
        return {
            "seed": self.seed,
            "n_cells": self.n_cells,
            "colors": list(self.colors),
            "operations": [o.json() for o in self.operations],
            "initial": list(self.initial),
            "script": list(self.script),
            "flavour": self.flavour,
            "breaks_parity": self.breaks_parity,
        }


@dataclass
class ParityWorld(World):
    spec: ParitySpec
    states: List[List[str]]

    family = "parityworld"

    @property
    def seed(self) -> int:
        return self.spec.seed

    def spec_json(self) -> Dict[str, Any]:
        return self.spec.json()

    @property
    def colors(self) -> List[str]:
        return list(self.spec.colors)

    def planted_color(self) -> Optional[str]:
        """The colour whose count-parity is conserved by construction, or None."""
        if self.spec.flavour != "planted":
            return None
        return self.spec.colors[0]

    def color_counts(self, color: str) -> List[int]:
        return [sum(1 for c in state if c == color) for state in self.states]


def apply_operation(state: Sequence[str], operation: Operation,
                    colors: Sequence[str]) -> List[str]:
    out = list(state)
    k = len(colors)
    index = {c: i for i, c in enumerate(colors)}
    for cell in operation.cells:
        out[cell] = colors[(index[out[cell]] + operation.shift) % k]
    return out


def generate(seed: int) -> ParityWorld:
    """A colour-flip world, a pure function of `seed`."""
    rng = Rng(seed)

    planted = rng.chance(1, 2)
    n_cells = rng.between(3, 8)
    n_colors = 2 if planted else rng.between(2, 4)
    colors = tuple(PALETTE_SYMBOLS[:n_colors])

    n_ops = rng.between(2, min(6, max(2, n_cells)))
    operations: List[Operation] = []
    for _ in range(n_ops):
        if planted:
            size = 2 * rng.between(1, max(1, n_cells // 2))
            size = min(size, n_cells - (n_cells % 2))
            size = max(2, size)
            shift = 1
        else:
            size = rng.between(1, n_cells)
            shift = rng.between(1, n_colors - 1)
        cells = tuple(sorted(rng.sample(list(range(n_cells)), size)))
        operations.append(Operation(cells=cells, shift=shift))

    initial = tuple(rng.choice(colors) for _ in range(n_cells))

    # Every operation is witnessed once before the random tail, so the observed
    # difference matrix spans what the world can actually do rather than what a
    # short random draw happened to sample.
    n_steps = rng.between(n_ops, 40)
    script = list(range(n_ops))
    while len(script) < n_steps:
        script.append(rng.below(n_ops))

    states = [list(initial)]
    state = list(initial)
    for index in script:
        state = apply_operation(state, operations[index], colors)
        states.append(state)

    used_odd = any(
        len(operations[i].cells) % 2 == 1 for i in set(script)
    )
    breaks_parity = (n_colors == 2) and used_odd

    spec = ParitySpec(
        seed=seed, n_cells=n_cells, colors=colors,
        operations=tuple(operations), initial=initial, script=tuple(script),
        flavour="planted" if planted else "free",
        breaks_parity=breaks_parity,
    )
    return ParityWorld(spec=spec, states=states)
