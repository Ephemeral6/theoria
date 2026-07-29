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
| `present(T)`        | track T exists in this frame                       | 7    |
| `count(k)>=t`       | how many cells of the whole frame show colour k    | 13   |
| `faces(T,D)`        | track T sits where the mover's anchor would land   | 13   |

`tcolor` is the generalisation that Fixture A did not need: `free` is exactly
`tcolor==background`, and the Button and the closed Door are only distinguishable
from a wall by their colour.  Position literals stay twice the price of
predicates, for the reason upstream gives -- otherwise `at(r,c)` wins every
synthesis that has a single witness.

`count` — the one atom that is not local, and why
-------------------------------------------------

Every other atom reads a cell, a strip, or one track.  `count(k)>=t` reads the
**whole frame** and asks how many of its cells show colour `k`.  It was forced by
a specific world and the entry is in the ledger (`cold-start-a0/THEORIZE_LOG.md`
§E, **E-08**): `worldgen`'s `t2-lock-fragile` has a gate that opens once three
tokens have been picked up, and picking a token up **only** makes it stop being
drawn.  There is no counter object, no colour change, nothing else in the frame
announces that the count reached `k` — so the collected count exists solely as a
cardinality over the frame, and no atom that reads one place can see it.  With 98
local atoms the miner refused the world (`NoSeparatingGuard`) while its frames
were provably distinct, 87 states to 87 frames.

Three deliberate limits, so that "add a counting predicate" does not quietly
become "add quantifiers":

* **One relation, `>=`.**  `<=` comes free by negation (`count(k) <= t-1` is
  `!count(k)>=t`), and `==` is the conjunction of two atoms CEGIS can already
  build.  A second relation would buy nothing and cost a vocabulary twice as big.
* **Colours whose cardinality actually moves.**  A colour whose count is the same
  in every observed frame can never separate two transitions, so enumerating it
  is pure cost — walls and floor would otherwise contribute hundreds of atoms
  each.  The thresholds enumerated for a colour are likewise only those strictly
  inside its observed range: a threshold every frame passes, or none does, is a
  constant.
* **The frame, not the objects.**  `count` counts *cells showing a colour*, which
  is what a frame can be asked.  Counting *objects* would need object identity
  across absence, which this vocabulary does not have and which is its own ledger
  row.  For a world whose tokens are one cell each the two coincide; for one whose
  tokens are not, they do not, and this atom is honest about which it computes.

It is also the most expensive atom in the vocabulary, on purpose and for the same
reason `at(r,c)` is expensive: a global cardinality will separate almost any two
transitions if it is allowed to be cheap, and a guard that reads the whole board
should have to earn its place against one that reads the cell in front.

`faces` — the vocabulary knew about tracks and about places, never both
--------------------------------------------------------------------

Ledger entry **E-09**, and the same world forced it: `worldgen`'s
`t2-lock-fragile`, transition 31, after the segmentation was repaired so that the
agent is actually the mover (`pipeline/identity_swap.py`).  The rule that will
not mine is "this token does nothing when the agent presses RIGHT", and the one
transition it has to exclude is the one where the agent, standing directly to its
left, steps onto it and eats it.  Nothing in `a0_relational_v1` could say that:

* `tcolor(RIGHT)==2` says *the cell ahead is a token* — true as well when the
  agent eats a **different** token, so it is false on no negative and fails on a
  positive;
* `at(r,c)` reads the mover's anchor and nothing else, and the agent stands on
  that cell again later, once the token is gone;
* `present(T)` and `color(T)` are indexed by track but blind to where it is;
* `count(k)>=t` reads the frame, not a relation between two objects.

The vocabulary was relational about *colours and strips*, and indexed by *track*,
but it had no atom that put a named track in a place.  `faces(T,D)` is exactly
that one reading and no more: **track T's anchor is where the mover's anchor
would be after one step in direction D.**  For a world of one-cell objects that
is "T is the cell in front of me"; for a larger mover it is "T is where my
top-left would land", which is what an anchor is, and the atom computes that
rather than something more accommodating.

Four deliberate limits, so that "add a relational atom" does not quietly become
"add a relation algebra":

* **One step.**  Distance is not a parameter.  Two cells away, or a knight's
  move, is a different atom and needs its own forcing world.
* **Mover-relative only.**  There is no `faces(T, U, D)` between two non-mover
  tracks.  Every other atom in this vocabulary is anchored on the mover and this
  one keeps that shape.
* **Anchors, not overlap.**  It compares two anchors.  It does not ask whether
  the mover's body would intersect T's body, which is the touching-objects gap
  and is its own ledger row.
* **Only pairs the trajectory actually exhibited.**  A `(track, direction)` that
  is never true is a constant, and constants are dropped for the same reason
  `count` drops a threshold outside a colour's observed range.

It is priced with the position literals, at `2 * (_TRACK_BITS + _DIR_BITS)` = 8
bits of payload — the same payload as `at(r,c)`, by the same published rule that
makes `at` expensive.  `faces` names a specific object *and* a specific place;
it is the most instance-bound atom in the vocabulary, so it must not also be the
cheapest.  At the predicate price (4 bits of payload) it would have been cheaper
than every other atom here and would have displaced `tcolor` in guards that had
no need of it.

Whether the price is enough was measured, not argued.  Across this widening and
the identity repair together, **every mined guard in the tree is unchanged**:
all 26 non-`object_hypothesis` rows of A0's `artifacts/candidates.jsonl` are
byte-identical, as are all 31 and 27 `rule_hypothesis` rows of `worldgen`'s
`t1-switch-toggle` and `t1-switch-latch`.  The three `object_hypothesis` rows do
move, because they carry the segmentation report and it now has an
`identity_repair` section in it; their content-derived ids move with it.  That
is the whole diff, and it is in this commit.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple, Union

DIRECTIONS = ("UP", "DOWN", "LEFT", "RIGHT")
DELTA = {"UP": (-1, 0), "DOWN": (1, 0), "LEFT": (0, -1), "RIGHT": (0, 1)}

Cell = Tuple[int, int]

_RANK = {
    "free": 2, "in_bounds": 1, "clear": 1, "act": 1, "at": 1,
    "tcolor": 1, "color": 1, "present": 1, "count": 1, "faces": 1,
}

#: Ten kinds still need four bits, so E-09 widened the vocabulary without
#: touching the cost of a single existing atom -- unlike E-08 below, which cost
#: every atom one bit and had to measure what that moved.
#:
#: Nine kinds need four bits.  The widening adds one bit to *every* atom, which
#: is uniform and therefore leaves the ordering between equal-length guards
#: alone, but does tilt the choice between a short guard and a long one very
#: slightly further toward the short one — so whether it moved anything was
#: measured rather than argued.  Re-running `cold-start-a0/run_all.py` changes
#: `artifacts/candidates.jsonl` in exactly one field: `guard_cost_bits`, 16 → 18
#: on the 23 `rule_hypothesis` rows (two atoms per guard, one bit each).  Zero
#: guards differ, no row is added or dropped, and `candidates_no_button.jsonl`
#: moves the same way.  The diff is in this commit and is the evidence.
_KIND_BITS = 4
_NEG_BITS = 1
_DIR_BITS = 2
_POS_BITS = 8
_COLOR_BITS = 4
_TRACK_BITS = 2
#: A threshold, in the same width as a colour.  Payload for `count` is therefore
#: `_COLOR_BITS + _COUNT_BITS` = 8, the same as a position literal: both are
#: literals about the board rather than predicates about the mover.
_COUNT_BITS = 4


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
        elif self.kind == "count":
            body = "count(%d)>=%d" % (self.arg[0], self.arg[1])
        elif self.kind == "faces":
            body = "faces(%s,%s)" % (self.arg[0], self.arg[1])
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
        elif self.kind == "count":
            payload = _COLOR_BITS + _COUNT_BITS
        elif self.kind == "faces":
            # A named object in a named place: an identity literal, priced with
            # the position literals at twice its predicate payload.
            payload = 2 * (_TRACK_BITS + _DIR_BITS)
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
        if self.kind == "faces" and self.arg[1] == direction:
            return Atom(self.kind, (self.arg[0], variable), self.negated)
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
    if kind == "count":
        colour, threshold = arg
        return frame_count(obs.frame, colour) >= threshold
    if kind == "faces":
        track, direction = arg
        there = obs.anchors.get(track)
        if obs.mover_anchor is None or there is None:
            return False
        dr, dc = DELTA[direction]
        return (tuple(there)
                == (obs.mover_anchor[0] + dr, obs.mover_anchor[1] + dc))

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

def frame_count(frame, colour: int) -> int:
    """How many cells of the whole frame show `colour`.

    The single global reading in the vocabulary, and the only place a count is
    computed, so that the atom, its mask and any explanation of it can never
    drift apart.
    """
    return sum(row.count(colour) for row in frame)


def _count_atoms(observations: Sequence[Obs]) -> List[Atom]:
    """`count(k)>=t` for every colour whose cardinality is not a constant.

    A colour showing the same number of cells in every observed frame separates
    nothing, and a threshold outside a colour's observed range is true of every
    frame or of none.  Both are dropped, which is what keeps a global atom family
    from swamping a vocabulary of local ones: on `t2-lock-fragile` this yields
    three atoms, not several hundred.
    """
    counts: Dict[int, set] = {}
    for obs in observations:
        seen = set()
        for row in obs.frame:
            seen.update(row)
        for colour in seen:
            counts.setdefault(colour, set()).add(frame_count(obs.frame, colour))
        # A colour absent from this frame has count 0 here, and that zero is
        # exactly the observation that makes a consumable's cardinality vary.
        for colour in list(counts):
            if colour not in seen:
                counts[colour].add(0)

    atoms: List[Atom] = []
    for colour in sorted(counts):
        observed = counts[colour]
        low, high = min(observed), max(observed)
        for threshold in range(low + 1, high + 1):
            atoms.append(Atom("count", (colour, threshold)))
    return atoms


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
    #: `(track, direction)` pairs the trajectory ever actually exhibited.  One
    #: that is never true is a constant and separates nothing -- the same filter
    #: `_count_atoms` applies to thresholds.
    faced: set = set()
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
                for direction in DIRECTIONS:
                    if _positive("faces", (track, direction), obs, ""):
                        faced.add((track, direction))
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
    for track, direction in sorted(faced):
        atoms.append(Atom("faces", (track, direction)))
    atoms.extend(_count_atoms(observations))

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
