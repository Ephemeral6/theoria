"""A relational guard vocabulary for a multi-object world.

`engine-rig`'s `cegis_miner.atoms` is written for Fixture A: one object, and a
guard language that can only talk about that object's strip and anchor.  The A0
world has three objects and a law that relates two of them, so the vocabulary has
to be able to say "the cell the mover is pushing into is the Button" and "the
Door is gone".  That is a *vocabulary* extension, not a change to the synthesis
algorithm, so this module supplies atoms and leaves CEGIS alone: `multi_miner`
calls `cegis_miner.synthesize` and `cegis_miner.enumerate_frontier` directly on
the masks built here.

The atoms duck-type `cegis_miner.atoms.Atom` (`.name`, `.cost`, `.strength`,
`.negate()`, `.substitute_direction()`), which is all the upstream synthesis and
ordering functions ever touch.

Kinds
-----
| atom                | reads                                              | bits |
|---------------------|----------------------------------------------------|------|
| `act==D`            | the action taken                                   | 6    |
| `free(strip(D))`    | mover's target strip is in bounds and all floor    | 6    |
| `in_bounds(strip(D))` | mover's target strip is inside the grid          | 6    |
| `clear(strip(D))`   | in-bounds part of the strip is floor               | 6    |
| `tcolor(D)==k`      | mover's target strip is entirely colour k          | 10   |
| `at(r,c)`           | mover's anchor                                     | 12   |
| `color(T)==k`       | track T's uniform colour                           | 10   |
| `present(T)`        | track T exists in this frame                       | 6    |

`tcolor` is the generalisation that Fixture A did not need: `free` is exactly
`tcolor==background`, and the Button and the closed Door are only distinguishable
from a wall by their colour.  Position literals stay twice the price of
predicates, for the reason upstream gives -- otherwise `at(r,c)` wins every
synthesis that has a single witness.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple, Union

DIRECTIONS = ("UP", "DOWN", "LEFT", "RIGHT")
DELTA = {"UP": (-1, 0), "DOWN": (1, 0), "LEFT": (0, -1), "RIGHT": (0, 1)}

Cell = Tuple[int, int]

_RANK = {
    "free": 2, "in_bounds": 1, "clear": 1, "act": 1, "at": 1,
    "tcolor": 1, "color": 1, "present": 1,
}

_KIND_BITS = 3
_NEG_BITS = 1
_DIR_BITS = 2
_POS_BITS = 8
_COLOR_BITS = 4
_TRACK_BITS = 2


@dataclass
class Obs:
    """Everything an atom may look at, minus the action."""

    frame: Tuple[Tuple[int, ...], ...]
    mover_anchor: Optional[Cell]
    mover_shape: Cell
    anchors: Dict[str, Optional[Cell]]
    colors: Dict[str, Optional[int]]
    background: int = 0

    @property
    def height(self) -> int:
        return len(self.frame)

    @property
    def width(self) -> int:
        return len(self.frame[0])

    def in_bounds(self, cell: Cell) -> bool:
        return 0 <= cell[0] < self.height and 0 <= cell[1] < self.width


def strip_cells(anchor: Cell, direction: str, shape: Cell) -> List[Cell]:
    r, c = anchor
    h, w = shape
    if direction == "UP":
        return [(r - 1, c + dc) for dc in range(w)]
    if direction == "DOWN":
        return [(r + h, c + dc) for dc in range(w)]
    if direction == "LEFT":
        return [(r + dr, c - 1) for dr in range(h)]
    if direction == "RIGHT":
        return [(r + dr, c + w) for dr in range(h)]
    raise ValueError(direction)


@dataclass(frozen=True)
class Atom:
    kind: str
    arg: Union[str, int, Cell, Tuple[str, int]]
    negated: bool = False

    # ------------------------------------------------------------- identity

    @property
    def name(self) -> str:
        if self.kind == "act":
            body = "act==%s" % self.arg
        elif self.kind == "at":
            body = "at(%d,%d)" % (self.arg[0], self.arg[1])
        elif self.kind == "tcolor":
            body = "tcolor(%s)==%d" % (self.arg[0], self.arg[1])
        elif self.kind == "color":
            body = "color(%s)==%d" % (self.arg[0], self.arg[1])
        elif self.kind == "present":
            body = "present(%s)" % self.arg
        else:
            body = "%s(strip(%s))" % (self.kind, self.arg)
        return ("!" + body) if self.negated else body

    @property
    def cost(self) -> int:
        if self.kind == "at":
            payload = _POS_BITS
        elif self.kind == "tcolor":
            payload = _DIR_BITS + _COLOR_BITS
        elif self.kind == "color":
            payload = _TRACK_BITS + _COLOR_BITS
        elif self.kind == "present":
            payload = _TRACK_BITS
        else:
            payload = _DIR_BITS
        return _KIND_BITS + _NEG_BITS + payload

    @property
    def strength(self) -> int:
        rank = _RANK[self.kind]
        return -rank if self.negated else rank

    def negate(self) -> "Atom":
        return Atom(self.kind, self.arg, not self.negated)

    def substitute_direction(self, direction: str, variable: str = "?dir") -> "Atom":
        """Replace a concrete direction by a variable, for rule lifting."""
        if self.kind in ("act", "free", "in_bounds", "clear") and self.arg == direction:
            return Atom(self.kind, variable, self.negated)
        if self.kind == "tcolor" and self.arg[0] == direction:
            return Atom(self.kind, (variable, self.arg[1]), self.negated)
        return self


# ---------------------------------------------------------------- semantics

def evaluate(atom: Atom, obs: Obs, action: str) -> bool:
    value = _positive(atom.kind, atom.arg, obs, action)
    return (not value) if atom.negated else value


def _positive(kind: str, arg, obs: Obs, action: str) -> bool:
    if kind == "act":
        return action == arg
    if kind == "present":
        return obs.anchors.get(arg) is not None
    if kind == "color":
        track, want = arg
        return obs.colors.get(track) == want
    if kind == "at":
        return obs.mover_anchor is not None and tuple(obs.mover_anchor) == tuple(arg)

    if obs.mover_anchor is None:
        return False
    direction = arg[0] if kind == "tcolor" else arg
    cells = strip_cells(obs.mover_anchor, direction, obs.mover_shape)
    inside = [cell for cell in cells if obs.in_bounds(cell)]
    if kind == "in_bounds":
        return len(inside) == len(cells)
    if kind == "clear":
        return all(obs.frame[r][c] == obs.background for r, c in inside)
    if kind == "free":
        return len(inside) == len(cells) and all(
            obs.frame[r][c] == obs.background for r, c in inside
        )
    if kind == "tcolor":
        want = arg[1]
        return len(inside) == len(cells) and all(
            obs.frame[r][c] == want for r, c in inside
        )
    raise ValueError(kind)


# -------------------------------------------------------------- vocabulary

def build_vocabulary(observations: Sequence[Obs], tracks: Sequence[str]) -> List[Atom]:
    """Every atom the evidence could need, positive and negated.

    The set is a function of what the trajectory actually contains -- observed
    anchors, observed target colours, observed track colours -- so the
    vocabulary never mentions a colour or a cell the world never showed.
    """
    atoms: List[Atom] = []
    for direction in DIRECTIONS:
        atoms.append(Atom("act", direction))
        for kind in ("free", "in_bounds", "clear"):
            atoms.append(Atom(kind, direction))

    target_colors: Dict[str, set] = {d: set() for d in DIRECTIONS}
    anchors = set()
    track_colors: Dict[str, set] = {t: set() for t in tracks}
    for obs in observations:
        if obs.mover_anchor is not None:
            anchors.add(tuple(obs.mover_anchor))
            for direction in DIRECTIONS:
                cells = strip_cells(obs.mover_anchor, direction, obs.mover_shape)
                if all(obs.in_bounds(cell) for cell in cells):
                    values = {obs.frame[r][c] for r, c in cells}
                    if len(values) == 1:
                        target_colors[direction].add(values.pop())
        for track in tracks:
            color = obs.colors.get(track)
            if color is not None:
                track_colors[track].add(color)

    for direction in DIRECTIONS:
        for color in sorted(target_colors[direction]):
            atoms.append(Atom("tcolor", (direction, color)))
    for anchor in sorted(anchors):
        atoms.append(Atom("at", anchor))
    for track in tracks:
        atoms.append(Atom("present", track))
        for color in sorted(track_colors[track]):
            atoms.append(Atom("color", (track, color)))

    return atoms + [atom.negate() for atom in atoms]


def atom_masks(atoms: Sequence[Atom], observations: Sequence[Obs],
               actions: Sequence[str]) -> Dict[Atom, int]:
    masks: Dict[Atom, int] = {}
    for atom in atoms:
        mask = 0
        for i, (obs, action) in enumerate(zip(observations, actions)):
            if evaluate(atom, obs, action):
                mask |= 1 << i
        masks[atom] = mask
    return masks
