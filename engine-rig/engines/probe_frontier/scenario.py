"""The hand-made frontier scenario, and its hand-computed answer.

Two guard hypotheses that no evidence so far can separate:

    h_empty      the cart moves iff the target cell is EMPTY
    h_nonlethal  the cart moves iff the target cell is not LETHAL

Every transition seen so far had a target cell that was either empty (both
predict a move) or lethal (both predict none), so both survive.  They disagree
only where a *benign non-empty* colour sits in the way -- a configuration the
trajectory never produced.

The probe state puts exactly one such cell on the board:

        col   0  1  2  3  4  5
    row 0     .  .  .  .  .  .
    row 1     .  .  3  .  .  .     <- benign green, above the cart
    row 2     .  5  6  .  .  .     <- lethal left, cart at (2,2)
    row 3     .  .  .  .  .  .
    row 4     .  .  .  .  .  .
    row 5     .  .  .  .  .  .

By hand: UP is the only discriminating action (h_empty says none, h_nonlethal
says move -- a 1-bit split); DOWN and RIGHT are empty (both say move, 0 bits);
LEFT is lethal (both say none, 0 bits).  Answer: **UP, 1 bit**.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence, Tuple

from engines.probe_frontier.frontier import Hypothesis

EMPTY = 0
BENIGN = 3
LETHAL = 5
CART = 6

DIRECTIONS = ("DOWN", "LEFT", "RIGHT", "UP")
DELTA = {"UP": (-1, 0), "DOWN": (1, 0), "LEFT": (0, -1), "RIGHT": (0, 1)}

MOVE = "move"
NONE = "none"


@dataclass(frozen=True)
class GridState:
    """A 1x1 cart on a small board -- the smallest thing that shows the split."""

    frame: Tuple[Tuple[int, ...], ...]
    anchor: Tuple[int, int]

    def target(self, action: str) -> Optional[int]:
        """Colour of the cell the cart would move into, or None if off-board."""
        dr, dc = DELTA[action]
        r, c = self.anchor[0] + dr, self.anchor[1] + dc
        if not (0 <= r < len(self.frame) and 0 <= c < len(self.frame[0])):
            return None
        return self.frame[r][c]

    def render(self) -> List[str]:
        return ["".join(str(cell) for cell in row) for row in self.frame]


def _board(cells: Dict[Tuple[int, int], int], size: int = 6) -> Tuple[Tuple[int, ...], ...]:
    grid = [[EMPTY] * size for _ in range(size)]
    for (r, c), color in cells.items():
        grid[r][c] = color
    return tuple(tuple(row) for row in grid)


def make_state(cells: Dict[Tuple[int, int], int], anchor: Tuple[int, int],
               size: int = 6) -> GridState:
    """Build a board for a variant scenario; `cells` maps (row, col) to colour."""
    occupied = dict(cells)
    occupied[anchor] = CART
    return GridState(frame=_board(occupied, size=size), anchor=anchor)


PROBE_STATE = GridState(
    frame=_board({(1, 2): BENIGN, (2, 1): LETHAL, (2, 2): CART}),
    anchor=(2, 2),
)

TOP_ROW_STATE = GridState(
    frame=_board({(0, 2): CART, (0, 3): BENIGN}),
    anchor=(0, 2),
)


# --------------------------------------------------------------- hypotheses

def _predict_empty(state: GridState, action: str) -> str:
    return MOVE if state.target(action) == EMPTY else NONE


def _predict_nonlethal(state: GridState, action: str) -> str:
    target = state.target(action)
    return MOVE if target is not None and target != LETHAL else NONE


def _predict_in_bounds(state: GridState, action: str) -> str:
    return MOVE if state.target(action) is not None else NONE


def _predict_nonlethal_below_top(state: GridState, action: str) -> str:
    target = state.target(action)
    if target is None or target == LETHAL or state.anchor[0] == 0:
        return NONE
    return MOVE


H_EMPTY = Hypothesis(
    id="h_empty",
    predict=_predict_empty,
    description="moves iff the target cell is empty",
)
H_NONLETHAL = Hypothesis(
    id="h_nonlethal",
    predict=_predict_nonlethal,
    description="moves iff the target cell is not lethal",
)
H_IN_BOUNDS = Hypothesis(
    id="h_in_bounds",
    predict=_predict_in_bounds,
    description="moves iff the target cell is on the board",
)
H_NONLETHAL_BELOW_TOP = Hypothesis(
    id="h_nonlethal_below_top",
    predict=_predict_nonlethal_below_top,
    description="moves iff the target cell is not lethal and the cart is not in row 0",
)

FRONTIER = [H_EMPTY, H_NONLETHAL]
EXTENDED_FRONTIER = [H_EMPTY, H_NONLETHAL, H_NONLETHAL_BELOW_TOP]


# ------------------------------------------------------------------ evidence

EDGE_STATE = GridState(frame=_board({(2, 5): CART}), anchor=(2, 5))

PAST_EVIDENCE: List[Tuple[GridState, str, str]] = [
    (PROBE_STATE, "DOWN", MOVE),      # empty below
    (PROBE_STATE, "LEFT", NONE),      # lethal to the left
    (PROBE_STATE, "RIGHT", MOVE),     # empty to the right
    (EDGE_STATE, "RIGHT", NONE),      # wall
]


def consistent(hypothesis: Hypothesis,
               evidence: Sequence[Tuple[GridState, str, str]] = PAST_EVIDENCE) -> bool:
    """Does this hypothesis explain every transition seen so far?"""
    return all(
        hypothesis.predict(state, action) == observed
        for state, action, observed in evidence
    )


def build() -> Dict[str, Any]:
    """The scenario as one bundle, for the engine and the tests to share."""
    return {
        "state": PROBE_STATE,
        "actions": list(DIRECTIONS),
        "hypotheses": list(FRONTIER),
        "evidence": list(PAST_EVIDENCE),
        "hand_computed_answer": "UP",
        "hand_computed_entropy": 1.0,
    }
