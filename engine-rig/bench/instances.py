"""The batch every rung is measured on.

Two families, chosen because they ask the ladder two different questions.

**gripper** -- a size ladder with no deadlocks in it at all.  Every state is
solvable, so nothing a pruner could prove is worth anything, and what the ladder
is being asked is the plain one: how far does the bundled BFS get before the real
planner is worth its startup cost?  The family already exists in
`engines/fd_adapter/fuzz.py` with a closed-form optimum, so every length in the
table has an oracle that shares no code with any planner.

**sokoban** -- the family the deadlock theorems live in.  `fixtures/sokoban.py`
already generates it, and its `open4far` level exists precisely because pruning
only pays where the blind search would otherwise wander.  This module extends
that one level into a size ladder by the same rule, so the dividend can be read
as a function of board size rather than as one number from one board.

Nothing here writes into `fixtures/data/`.  Those files are committed and
byte-stable, the repo's determinism requirement covers them, and a benchmark that
regenerates its own inputs into a tracked directory is one `git status` away from
being blamed for a fixture drift it did not cause.  Bench instances go into the
run directory, next to the numbers they produced.
"""

import os
from dataclasses import dataclass
from typing import List, Optional, Tuple

from engines import fd_adapter
from engines.fd_adapter import fuzz
from fixtures import sokoban

# The gripper ladder.  It stops at 8 movers because the *bundled* rung is the
# subject here and its state space is exponential in the ball count: the point of
# the table is to show where it stops being usable, which needs at least one row
# on each side of that line, not thirty rows past it.
GRIPPER_MOVERS = (1, 2, 3, 4, 5, 6, 7, 8, 9, 10)

# Interior side lengths for the generated sokoban ladder.  `open4far` is N=4 with
# two boxes; the rest is the same construction at other sizes.
#
# It starts at 4 and not at 3 for a reason worth writing down, because the
# smaller board looks like a free extra row: at N=3 the construction puts `b2` on
# (3,3), which on a 3x3 interior is a *corner*, and asks it to reach another
# corner.  The instance is then unsolvable at step zero -- the carver's own first
# theorem kills it -- and it would sit in the table as a deadlock-pruning triumph
# that measured nothing but a badly generated board.
SOKOBAN_SIDES = (4, 5, 6)


@dataclass(frozen=True)
class BenchInstance:
    """One PDDL instance, plus whatever is independently known about it.

    `optimum` is filled in only where an oracle exists that is not a planner --
    the gripper closed form, or a hand-derived length argued in a README.  It is
    None everywhere else on purpose: writing a planner's own answer into the
    column headed "the right answer" is how a benchmark stops being able to fail.
    """

    name: str
    family: str
    domain_path: str
    problem_path: str
    optimum: Optional[int] = None
    solvable: Optional[bool] = None       # None = not independently known
    note: str = ""

    def as_json(self):
        return {
            "name": self.name,
            "family": self.family,
            "optimum": self.optimum,
            "optimum_source": (
                None if self.optimum is None
                else ("closed form" if self.family == "gripper" else "hand-derived")
            ),
            "solvable": self.solvable,
            "note": self.note,
        }


def _write(path: str, text: str) -> None:
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def gripper_ladder(directory: str, movers: Tuple[int, ...] = GRIPPER_MOVERS
                   ) -> List[BenchInstance]:
    """Gripper instances of growing size, each with its arithmetic optimum."""
    os.makedirs(directory, exist_ok=True)
    out = []
    for count in movers:
        instance = fuzz.Instance(name="gripper-%02d" % count, movers=count, settled=0)
        problem_path = os.path.join(directory, "%s.pddl" % instance.name)
        _write(problem_path, instance.problem_text())
        out.append(
            BenchInstance(
                name=instance.name, family="gripper",
                domain_path=fd_adapter.DOMAIN_PATH, problem_path=problem_path,
                optimum=instance.optimum, solvable=True,
                note="%d ball(s) to ferry; optimum 2m+2*ceil(m/2)-1" % count,
            )
        )
    return out


def far_level(side: int) -> sokoban.Level:
    """`open4far`, generalised to an N x N interior.

    The construction is `open4far`'s, verbatim: two boxes near the middle of the
    board, each one's goal on the far side of the other's, and the player in a
    corner.  At `side=4` it *is* `open4far` -- checked by
    `tests/test_bench_instances.py`, so this ladder cannot quietly diverge from
    the fixture whose optimum the deadlock carver's README argues.

    Every interior corner is a dead cell for both boxes and none of them is a
    goal, so the theorems the carver proves are the same shape at every size --
    which is the point of varying only the size.
    """
    if side < 4:
        raise ValueError(
            "side %d puts b2 on a corner at (3,3) and the instance is dead on "
            "arrival; see SOKOBAN_SIDES" % side
        )
    grid = tuple(
        ["#" * (side + 2)]
        + ["#" + "." * side + "#" for _ in range(side)]
        + ["#" * (side + 2)]
    )
    return sokoban.Level(
        name="far%d" % side,
        grid=grid,
        player=(side, side),
        boxes=(("b1", (2, 2)), ("b2", (3, 3))),
        goals=(("b1", (side, 2)), ("b2", (1, 3))),
        optimum=None,
        path="",
    )


def sokoban_ladder(directory: str, sides: Tuple[int, ...] = SOKOBAN_SIDES
                   ) -> List[BenchInstance]:
    """The committed sokoban fixtures, then the same construction at other sizes.

    The fixtures come first and are used from `fixtures/data/` unchanged -- their
    lengths are already argued elsewhere in this rig, so they are the rows of the
    table that can be checked against something other than this run.
    """
    os.makedirs(directory, exist_ok=True)
    domain_path = sokoban.DOMAIN_PATH
    out = [
        BenchInstance(
            name="sokoban-open4", family="sokoban",
            domain_path=domain_path, problem_path=sokoban.OPEN4_PATH,
            optimum=sokoban.OPEN4.optimum, solvable=True,
            note="committed fixture; optimum 6 argued in deadlock_carver/README.md",
        ),
        BenchInstance(
            name="sokoban-open4far", family="sokoban",
            domain_path=domain_path, problem_path=sokoban.OPEN4FAR_PATH,
            solvable=True,
            note="committed fixture; the deep one -- boxes cross the board",
        ),
        BenchInstance(
            name="sokoban-ring", family="sokoban",
            domain_path=domain_path, problem_path=sokoban.RING_PATH,
            optimum=sokoban.RING.optimum, solvable=True,
            note="committed fixture; 1-wide corridor loop",
        ),
        BenchInstance(
            name="sokoban-ringstuck", family="sokoban",
            domain_path=domain_path, problem_path=sokoban.RINGSTUCK_PATH,
            solvable=False,
            note="committed fixture; unsolvable -- a box cannot turn a corner",
        ),
    ]
    for side in sides:
        level = far_level(side)
        problem_path = os.path.join(directory, "sokoban-%s.pddl" % level.name)
        _write(problem_path, level.problem_text())
        out.append(
            BenchInstance(
                name="sokoban-%s" % level.name, family="sokoban",
                domain_path=domain_path, problem_path=problem_path,
                # Deliberately not asserted.  The construction is `open4far`'s and
                # `open4far` is solvable, but "the same construction one size up"
                # is an argument about geometry I have not made, and a column that
                # says True because the author expected True cannot disagree with
                # the run.  The optimal rung's verdict goes in the results, as
                # evidence; this field stays empty.
                solvable=None,
                note="generated: %dx%d interior, open4far's construction" % (side, side),
            )
        )
    return out


def all_instances(directory: str) -> List[BenchInstance]:
    return gripper_ladder(directory) + sokoban_ladder(directory)
