"""Instances that start inside a deadlock, which E2's batch did not contain.

E2 measured what the theorems are worth to a planner **solving** an instance,
and found the dividend goes to zero the moment an admissible heuristic is on.
That is the right measurement for the claim as Theoria 1.9 states it, and the
audit reproduces it.  It also leaves the sharper question unasked: *why* zero.

Two candidate explanations predict different things, and the difference is
testable:

  (A) **Fast Downward already knows.**  The dead region is unreachable in the
      delete relaxation too, so every heuristic built on that relaxation returns
      infinity there and the theorem restates something the planner had.  The
      dividend is zero because the information is redundant.

  (B) **Fast Downward never goes there.**  The heuristic guides the search
      around the dead region without ever proving anything about it.  The
      dividend is zero because the information is unused, not because it is
      already held -- and it would pay on any instance the search cannot avoid.

They come apart on an instance whose **initial state is already dead**.  A
planner that holds explanation (A) settles it without searching; one that holds
(B) has to exhaust the space.

The two theorem kinds the carver emits then split cleanly, and that is the point
of this module:

  `deadstart-corner`  one box in an interior corner.  The carver calls this
                      `no_deleting_action`: grounding discarded every push that
                      would move it, because each needs a pusher cell that is a
                      wall.  Deleting effects are irrelevant to that argument, so
                      the delete relaxation makes it too.

  `deadstart-pair`    two boxes side by side against a wall.  The carver calls
                      this `deleting_actions_blocked`: the pushes exist, and are
                      impossible only because each needs the cell the other box
                      occupies to be clear.  `clear` is *deleted* by a push, so
                      the delete relaxation keeps it and the argument evaporates.

If the split is real, the honest claim is not "deadlock theorems do not speed
planners up" but something narrower and more useful: **a deadlock theorem is
worth what it adds to the planner's own relaxation, and the two kinds this rig
proves sit on opposite sides of that line.**

--------------------------------------------------------------------------
WHAT HAPPENED.  The prediction above is wrong, and is kept because a prediction
deleted after it fails is a prediction nobody made.

**The two kinds do not split.**  `deadstart-corner{4,5,6}` and
`deadstart-pair{4,5,6}` are both settled *unguarded* at 0 expansions with
h = infinity; the live control searches normally (21/41/88).  The conclusion the
split was meant to license is reached anyway, by the coverage measurement in
`claim.py` instead of by this contrast.

**The explanation first given for that is also wrong.**  It was: dropping
deletes cannot manufacture atoms, `clear` is false on a box's cell at the start
and never comes back without a real push, so the player still cannot get between
two adjacent boxes.  An adversarial reviewer re-encoded sokoban with `occupied`
in place of `clear` and the relaxation still found all 2904 dead states on
`far4` with occupancy information removed entirely.  What is load-bearing is
**static push geometry**: a box against a wall has no pusher cell outside the
wall, so it is confined to one row or column whatever the relaxation does with
`clear`.

**And (A)/(B) is a false dichotomy.**  Both hold, on different rows.  (A) is
right about containment -- no theorem-dead state on this family is outside the
relaxation.  But (B) is literally true on some searches: `astar(ipdb())` on far6
reports `Dead ends: 0`, having never generated a dead state at all.  Neither
covers the effect that does exist, which is that deleting the dead push
operators makes the relaxation harder and raises h on *live* states.

See `DEADLOCK_CLAIM.md` §3c, §3d and §7.
"""

from typing import List, Tuple

from fixtures import sokoban

Cell = Tuple[int, int]


def _open_grid(side: int) -> Tuple[str, ...]:
    return tuple(
        ["#" * (side + 2)]
        + ["#" + "." * side + "#" for _ in range(side)]
        + ["#" * (side + 2)]
    )


def corner_level(side: int) -> sokoban.Level:
    """`far{side}`'s board, with b1 already in the top-left interior corner.

    Unsolvable, and unsolvable for the reason the carver's first theorem gives:
    (1,1) has a wall above and a wall to the left, so no `push` instance that
    moves b1 was ever grounded.  b1's goal is `(side,2)`, so the pattern really
    does exclude the goal rather than sitting on it.
    """
    if side < 4:
        raise ValueError("side must be at least 4")
    return sokoban.Level(
        name="deadstart-corner%d" % side,
        grid=_open_grid(side),
        player=(side, side),
        boxes=(("b1", (1, 1)), ("b2", (3, 3))),
        goals=(("b1", (side, 2)), ("b2", (1, 3))),
        optimum=None,
        path="",
    )


def pair_level(side: int) -> sokoban.Level:
    """The same board, with b1 and b2 side by side against the top wall.

    Unsolvable, and *not* for a reason grounding supplies.  Every push that
    would separate them exists as a ground action; each is impossible only
    because it needs the cell the other box is on to be clear, or the player to
    stand there.  Both boxes' goals are elsewhere, so neither is parked on its
    target.

    `b2`'s goal is moved off `(1,3)` deliberately: `far{side}` puts it there,
    and a pattern whose second atom sits on the goal would make the instance
    solvable-looking for the wrong reason.
    """
    if side < 4:
        raise ValueError("side must be at least 4")
    return sokoban.Level(
        name="deadstart-pair%d" % side,
        grid=_open_grid(side),
        player=(side, side),
        boxes=(("b1", (1, 2)), ("b2", (1, 3))),
        goals=(("b1", (side, 2)), ("b2", (side, 3))),
        optimum=None,
        path="",
    )


def alive_level(side: int) -> sokoban.Level:
    """A control: the same two boxes, one row down, where nothing is dead.

    Without it, "the planner searched hard on `deadstart-pair`" says nothing --
    it could be the board size.  This instance is the pair instance with both
    boxes moved off the wall, so it is solvable and the search cost on it is the
    baseline the dead one is read against.
    """
    if side < 4:
        raise ValueError("side must be at least 4")
    return sokoban.Level(
        name="alive-pair%d" % side,
        grid=_open_grid(side),
        player=(side, side),
        boxes=(("b1", (2, 2)), ("b2", (2, 3))),
        goals=(("b1", (side, 2)), ("b2", (side, 3))),
        optimum=None,
        path="",
    )


def levels(sides: Tuple[int, ...] = (4, 5, 6)) -> List[sokoban.Level]:
    out: List[sokoban.Level] = []
    for side in sides:
        out.append(corner_level(side))
        out.append(pair_level(side))
        out.append(alive_level(side))
    return out
