"""What actually happened between two frames, read off the pixels.

This oracle exists for one invariant: `cegis_miner` publishes `effect.*` — the
part of a rule that says *what happens* — and until V-13 no property compared it
against anything. The four guard invariants all audit *when* a rule fires, so a
rule set with perfect guards and inverted effects passed the whole battery
clean and went into the manual as the world's causal law.

## Where the truth comes from, and where it must not come from

The house rule (`fuzzlab/README.md`) is that an oracle may not call the engine
it judges. For effects that rule bites harder than it looks, because the obvious
source of "what really happened at transition *i*" is
`engines.cegis_miner.transitions_from_segmentation(...)[i].effect` — which is
`cegis_miner` reading `mdl_segmenter`'s narration. Comparing a rule's effect
against that would establish that the miner agrees with the segmenter, which is
not the question, and it would be blind to exactly the failure mode that
matters: both of them wrong in the same direction.

So this module reads **`world.frames` only**, plus the world's own declaration
of what its mover *is* (`mover_shape`, `mover_color`, `background` out of
`spec_json()`). It imports nothing from `engines`, and the module has no
`fuzzlab.rig` bootstrap for that reason — an import of `engines.*` here would
fail rather than quietly work.

The spec fields are the world's *definition*, not a derived assertion about it:
`props/cegis_miner.py` already takes `background` from the same place, and
`gridworld.py`'s `Rules` docstring calls itself "the world's transition
function, standing alone from any engine". What this module deliberately does
**not** read is `world.anchors` or `world.events` — those are the generator's
record of what it meant to draw, and a renderer that disagreed with them would
be invisible. Everything below is recomputed from the rendered pixels, which is
the same evidence the segmenter and the miner were given.

## The method

`frame_a` and `frame_b` differ only where the mover moved: the generator's
obstacles are static and the background is constant. So

* `D` = the changed cells. Empty `D` means nothing moved: `Effect(none)`.
* `vacated` = changed cells that were mover-coloured and became background;
  `entered` = changed cells that were background and became mover-coloured.
  If `vacated | entered != D`, some cell changed in a way a rigid translation of
  a single mover cannot explain, and the reading is refused rather than guessed.
* The mover is a `h x w` rectangle, so its position in each frame is an anchor.
  Enumerate every anchor whose rectangle is entirely mover-coloured in that
  frame **and** covers the cells that frame's diff attributes to the mover; then
  keep the `(before, after)` pairs for which erasing the first rectangle to
  background and painting the second reproduces `frame_b` **exactly**.

That last replay is the whole safety argument. Candidate anchors are cheap to
over-generate — a same-coloured obstacle sitting next to the mover produces
spurious ones — and the replay is what discards them. If it leaves no candidate,
or more than one, the answer is `Unreadable` and the caller records a `skipped`
with the reason. This oracle never guesses: it either knows or says so.

## What it cannot see, stated so nobody assumes otherwise

* Worlds whose diff is not one rigid rectangle translation on a static
  background — a segmentation-level ambiguity, not a mining defect.
* Which *object* moved, when two objects of the mover's colour and shape are
  both consistent with the diff. Those are `Unreadable`, counted, and reported.
"""

from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

Cell = Tuple[int, int]
Frame = Sequence[Sequence[int]]

#: `effect.type` for a transition in which the mover did not move.
NONE = "none"
#: `effect.type` for a transition in which it did.
MOVE = "move"


class Unreadable(Exception):
    """The pixel diff does not determine a unique rigid motion of one mover.

    Not a defect in anything: it is this oracle declining to state a truth it
    cannot establish. Every caller turns it into a `skipped` with the reason
    attached, never into a violation.
    """


class Motion:
    """What happened between two frames, as the oracle can establish it."""

    __slots__ = ("type", "dy", "dx", "to", "frm")

    def __init__(self, type: str, dy: int = 0, dx: int = 0,
                 to: Optional[Cell] = None, frm: Optional[Cell] = None) -> None:
        self.type = type
        self.dy = dy
        self.dx = dx
        self.to = to                 # anchor after, when the mover moved
        self.frm = frm               # anchor before, when it could be located

    @property
    def delta(self) -> Cell:
        return (self.dy, self.dx)

    def __repr__(self) -> str:                                # pragma: no cover
        if self.type == NONE:
            return "Motion(none)"
        return "Motion(move, d=(%d,%d), to=%s)" % (self.dy, self.dx, self.to)

    def __eq__(self, other: Any) -> bool:
        return (isinstance(other, Motion) and other.type == self.type
                and other.delta == self.delta and other.to == self.to)

    def __hash__(self) -> int:
        return hash((self.type, self.dy, self.dx, self.to))


def mover_spec(world: Any) -> Tuple[Tuple[int, int], int, int]:
    """`((h, w), colour, background)` — the world's declaration of its mover."""
    spec = world.spec_json()
    shape = tuple(spec["mover_shape"])
    return (int(shape[0]), int(shape[1])), int(spec["mover_color"]), \
        int(spec.get("background", 0))


def _changed(a: Frame, b: Frame) -> List[Cell]:
    return [(r, c) for r in range(len(a)) for c in range(len(a[r]))
            if a[r][c] != b[r][c]]


def _rect(anchor: Cell, height: int, width: int) -> List[Cell]:
    return [(anchor[0] + dr, anchor[1] + dc)
            for dr in range(height) for dc in range(width)]


def _anchors_covering(frame: Frame, shape: Tuple[int, int], colour: int,
                      must_cover: Set[Cell]) -> List[Cell]:
    """Anchors of a fully `colour` rectangle containing every cell of `must_cover`.

    Over-generates on purpose: a same-coloured obstacle adjacent to the mover can
    put a second anchor in this list, and `read_motion`'s replay is what removes
    it. Filtering here on anything cleverer would be a second segmentation, and
    a second segmentation is the thing this oracle exists to avoid.
    """
    height, width = shape
    rows, cols = len(frame), len(frame[0])
    out: List[Cell] = []
    for r in range(rows - height + 1):
        for c in range(cols - width + 1):
            cells = _rect((r, c), height, width)
            if not must_cover.issubset(cells):
                continue
            if all(frame[y][x] == colour for (y, x) in cells):
                out.append((r, c))
    return out


def _replay(a: Frame, before: Sequence[Cell], after: Sequence[Cell],
            colour: int, background: int) -> List[List[int]]:
    grid = [list(row) for row in a]
    for (r, c) in before:
        grid[r][c] = background
    for (r, c) in after:
        grid[r][c] = colour
    return grid


def read_motion(a: Frame, b: Frame, shape: Tuple[int, int], colour: int,
                background: int) -> Motion:
    """The unique rigid translation of the mover taking `a` to `b`.

    Raises `Unreadable` when the pixels do not determine one.
    """
    diff = _changed(a, b)
    if not diff:
        return Motion(NONE)

    vacated = {cell for cell in diff
               if a[cell[0]][cell[1]] == colour and b[cell[0]][cell[1]] == background}
    entered = {cell for cell in diff
               if a[cell[0]][cell[1]] == background and b[cell[0]][cell[1]] == colour}
    unexplained = set(diff) - vacated - entered
    if unexplained:
        raise Unreadable(
            "%d changed cell(s) are neither mover->background nor "
            "background->mover, e.g. %s: this frame pair is not one rigid "
            "translation of a single mover on a static background"
            % (len(unexplained), sorted(unexplained)[:4]))
    if not vacated or not entered:
        raise Unreadable(
            "the diff is one-sided (%d vacated, %d entered), so no rigid "
            "translation of a fixed-size mover produces it"
            % (len(vacated), len(entered)))

    height, width = shape
    befores = _anchors_covering(a, shape, colour, vacated)
    afters = _anchors_covering(b, shape, colour, entered)
    if not befores or not afters:
        raise Unreadable(
            "no %dx%d block of colour %d covers the %s cells (before: %d "
            "candidates, after: %d)"
            % (height, width, colour,
               "vacated" if not befores else "entered", len(befores), len(afters)))

    target = [list(row) for row in b]
    solutions: List[Tuple[Cell, Cell]] = []
    for start in befores:
        cells_before = _rect(start, height, width)
        for end in afters:
            if end == start:
                continue                # a no-op cannot explain a non-empty diff
            if _replay(a, cells_before, _rect(end, height, width),
                       colour, background) == target:
                solutions.append((start, end))
    if len(solutions) != 1:
        raise Unreadable(
            "%d rigid translations of a %dx%d colour-%d block reproduce the "
            "next frame; the motion is not determined by the pixels%s"
            % (len(solutions), height, width, colour,
               "" if not solutions else " (%s)" % (sorted(solutions)[:3],)))
    start, end = solutions[0]
    return Motion(MOVE, dy=end[0] - start[0], dx=end[1] - start[1],
                  to=end, frm=start)


def motions(world: Any) -> Dict[int, Motion]:
    """`{transition index: Motion}` for every frame pair the world has an action for.

    Indices match `cegis_miner.transitions_from_segmentation`'s, which numbers a
    transition by the index of the frame it starts from — the only thing taken
    from the engine here is that convention, and it is checked rather than
    assumed by the caller (`props/cegis_miner.py` compares the index sets).

    A pair the oracle cannot read is **absent from the mapping** rather than
    present with a guessed value, so a caller that forgets to handle the gap gets
    a `KeyError` instead of a silent pass.
    """
    shape, colour, background = mover_spec(world)
    frames = world.frames
    n_actions = len(world.action_list)
    out: Dict[int, Motion] = {}
    for index in range(min(n_actions, len(frames) - 1)):
        try:
            out[index] = read_motion(frames[index], frames[index + 1],
                                     shape, colour, background)
        except Unreadable:
            continue
    return out


def mover_anchors(world: Any) -> Optional[List[Cell]]:
    """The mover's anchor in each frame, chained from the pixel diffs.

    `None` when the pixels do not fix it: either some frame pair is `Unreadable`,
    or the mover never moves in the whole trajectory and its position is
    therefore not recoverable from motion alone. Both cases are the caller's to
    handle, and neither is a defect in anything.

    This exists so a property can answer *which object* a rule was mined from
    without asking the segmenter where its tracks are. The answer is then a
    comparison between two independently derived trajectories rather than a
    reading of one.
    """
    shape, colour, background = mover_spec(world)
    frames = world.frames
    span = min(len(world.action_list), len(frames) - 1)
    read: List[Motion] = []
    for index in range(span):
        try:
            read.append(read_motion(frames[index], frames[index + 1],
                                    shape, colour, background))
        except Unreadable:
            return None

    first = next((i for i, m in enumerate(read) if m.type == MOVE), None)
    if first is None:
        return None                     # never moves; no pixel fixes its anchor

    anchors: List[Optional[Cell]] = [None] * (span + 1)
    anchors[first] = read[first].frm
    anchors[first + 1] = read[first].to
    for index in range(first + 1, span):
        here = read[index]
        if here.type == NONE:
            anchors[index + 1] = anchors[index]
            continue
        if here.frm != anchors[index]:
            return None                 # the chain does not close; refuse
        anchors[index + 1] = here.to
    for index in range(first - 1, -1, -1):
        anchors[index] = anchors[index + 1]      # every earlier motion is NONE
    if any(a is None for a in anchors):          # cannot happen; refuse anyway
        return None
    return [a for a in anchors if a is not None]


def unreadable_reasons(world: Any) -> Dict[int, str]:
    """The reason each unreadable transition was refused; for `skipped` details."""
    shape, colour, background = mover_spec(world)
    frames = world.frames
    n_actions = len(world.action_list)
    out: Dict[int, str] = {}
    for index in range(min(n_actions, len(frames) - 1)):
        try:
            read_motion(frames[index], frames[index + 1], shape, colour, background)
        except Unreadable as why:
            out[index] = str(why)
    return out
