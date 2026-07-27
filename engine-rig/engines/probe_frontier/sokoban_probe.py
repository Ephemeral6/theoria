"""The hand-made frontier for the ring level, and its hand-computed answers.

Two guard hypotheses about pushing that the ring's own history cannot separate:

    h_free_push        a box moves whenever the cell beyond it is clear floor
    h_no_corner_entry  ... and the cell beyond it is not a corner

Nothing in the ring's history pushes a box into a corner, so both explain
everything seen.  They come apart only where a push *would* land a box in one --
and whether the agent can get to such a place is a planning question, which is
the point of this scenario.

Two configurations, both worth exactly one bit, separated only by what they cost:

    p_row1   player at c13, box at c12; push LEFT lands the box in corner c11.
             Reachable.  The player starts at c11 with the box to its right, so
             it cannot simply walk past -- the box is in the way and walking into
             it is a push.  It has to go the long way round the ring: 10 moves.
             Hand-computed cost 1 + 10 = 11, value 1/11 bits per unit cost.

    p_side   player at c21, box at c31; push DOWN lands the box in corner c41.
             **Unreachable.**  A box in a 1-wide corridor can be pushed along it
             but never turned out of it: turning needs the player standing beside
             the box, and a 1-wide corridor has no beside.  The box starts in row
             1 and can never leave it, so no plan puts it at c31.

`p_side` is the deliverable, not the consolation prize.  It is R-05's shape --
an experiment that would settle a question and cannot be performed on this
instance -- reported as a verdict by the machinery instead of noticed by a human
reading the log afterwards.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence, Tuple

from engines.fd_adapter.pddl import Atom
from engines.probe_frontier.frontier import Hypothesis
from engines.probe_frontier.reach import Configuration
from fixtures import sokoban

PUSH = "push"
WALK = "walk"
BLOCKED = "blocked"

DIRECTIONS = sokoban.DIRECTIONS
LEVEL = sokoban.RING


@dataclass(frozen=True)
class BoardState:
    """Where everything stands on a sokoban board."""

    level: Any
    player: Tuple[int, int]
    boxes: Tuple[Tuple[str, Tuple[int, int]], ...]

    def box_at(self, cell: Tuple[int, int]) -> Optional[str]:
        for name, position in self.boxes:
            if position == cell:
                return name
        return None

    def clear(self, cell: Optional[Tuple[int, int]]) -> bool:
        return (
            cell is not None
            and self.level.is_floor(cell)
            and cell != self.player
            and self.box_at(cell) is None
        )

    def goal_atoms(self) -> Tuple[Atom, ...]:
        """This configuration as PDDL atoms -- what the planner is asked for."""
        atoms = [("at-player", self.level.cell_name(self.player))]
        atoms += [
            ("at", name, self.level.cell_name(cell))
            for name, cell in sorted(self.boxes)
        ]
        return tuple(atoms)

    def render(self) -> List[str]:
        rows = [list(row) for row in self.level.grid]
        for _, (r, c) in self.boxes:
            rows[r][c] = "$"
        rows[self.player[0]][self.player[1]] = "@"
        return ["".join(row) for row in rows]


# --------------------------------------------------------------- hypotheses

def _outcome(state: BoardState, action: str, refuse_corners: bool) -> str:
    ahead = state.level.neighbour(state.player, action)
    if ahead is None:
        return BLOCKED
    if state.box_at(ahead) is None:
        return WALK if state.clear(ahead) else BLOCKED
    beyond = state.level.neighbour(ahead, action)
    if not state.clear(beyond):
        return BLOCKED
    if refuse_corners and beyond in set(state.level.corners()):
        return BLOCKED
    return PUSH


def _free_push(state: BoardState, action: str) -> str:
    return _outcome(state, action, refuse_corners=False)


def _no_corner_entry(state: BoardState, action: str) -> str:
    return _outcome(state, action, refuse_corners=True)


def _boxes_never_move(state: BoardState, action: str) -> str:
    outcome = _outcome(state, action, refuse_corners=False)
    return BLOCKED if outcome == PUSH else outcome


H_FREE_PUSH = Hypothesis(
    id="h_free_push",
    predict=_free_push,
    description="a box moves whenever the cell beyond it is clear floor",
)
H_NO_CORNER_ENTRY = Hypothesis(
    id="h_no_corner_entry",
    predict=_no_corner_entry,
    description="a box moves onto clear floor, but never into a corner",
)
H_BOXES_NEVER_MOVE = Hypothesis(
    id="h_boxes_never_move",
    predict=_boxes_never_move,
    description="boxes never move at all",
)

FRONTIER = [H_FREE_PUSH, H_NO_CORNER_ENTRY]


# ------------------------------------------------------------------- states

def state(player: Tuple[int, int], boxes: Sequence[Tuple[str, Tuple[int, int]]]
          ) -> BoardState:
    return BoardState(level=LEVEL, player=player, boxes=tuple(sorted(boxes)))


START = state(LEVEL.player, LEVEL.boxes)
ROW1 = state((1, 3), (("b1", (1, 2)),))          # push LEFT -> corner c11
SIDE = state((2, 1), (("b1", (3, 1)),))          # push DOWN -> corner c41

# Evidence the ring really produced: a push along row 1 (no corner involved) and
# a walk into the side corridor. Both survivors agree on both; h_boxes_never_move
# does not, so consistency is a filter here and not a rubber stamp.
PAST_EVIDENCE: List[Tuple[BoardState, str, str]] = [
    (START, "right", PUSH),
    (START, "down", WALK),
    (START, "left", BLOCKED),
    (START, "up", BLOCKED),
]


def consistent(hypothesis: Hypothesis,
               evidence: Sequence[Tuple[BoardState, str, str]] = None) -> bool:
    for board, action, observed in (evidence or PAST_EVIDENCE):
        if hypothesis.predict(board, action) != observed:
            return False
    return True


def configurations() -> List[Configuration]:
    return [
        Configuration(
            name="p_row1", state=ROW1, actions=DIRECTIONS,
            goal_atoms=ROW1.goal_atoms(),
        ),
        Configuration(
            name="p_side", state=SIDE, actions=DIRECTIONS,
            goal_atoms=SIDE.goal_atoms(),
        ),
    ]


def build() -> Dict[str, Any]:
    """The scenario as one bundle, for the engine and the tests to share."""
    return {
        "level": LEVEL,
        "hypotheses": list(FRONTIER),
        "configurations": configurations(),
        "evidence": list(PAST_EVIDENCE),
        "hand_computed": {
            "p_row1": {"action": "left", "bits": 1.0, "reach_length": 10, "cost": 11.0},
            "p_side": {"action": "down", "bits": 1.0, "reach": "unreachable"},
        },
    }
