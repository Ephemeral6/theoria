"""ring_world -- the world class that defeated `cegis_miner` on every live track.

Built from the shape of the recorded `g50t-5849a774` r3 leg
(`theoria-arm/runs/20260731T1430Z-A3-level2-carried-r3/ledger.jsonl`, 34 frames
with pixels), reduced to the smallest grid that keeps every property that
mattered.  Nothing here is copied from the game: this is a synthetic world with
the same *class* of structure, which is what engine-rig is allowed to hold and
what a regression test needs.

Four properties are reproduced, and each one broke something:

1. **The mover is an annulus that sits on the floor.**  A 5x5 block of `INK`
   with its centre left as floor is 24 cells, and it is 4-adjacent to the floor
   on every side.  `connected_components(4)` with `split_by_color=False`
   therefore merges mover and floor into one blob, and the mover's motion is
   narrated as a `recolor` of that blob -- which violates `cegis_miner`'s
   one-move precondition, so the track is refused.
2. **The colour-splitting operator separates it, and MDL does not choose that
   operator.**  With `split_by_color=True` the ring is its own track and its
   motion is a clean `move`; but the floor now changes shape every time the ring
   crosses it (the hole moves), so the floor is re-declared each transition and
   the total script is far longer.  The MDL objective prefers the merge.
3. **The action alphabet is not the compass.**  Actions are `ACTION1..ACTION4`,
   so every `act==UP` literal in the default guard vocabulary is identically
   false and the miner cannot see which action was taken.
4. **(optional) There is hidden state.**  With `hidden_state=True` one action
   from one anchor produces two different effects, because a counter cell the
   guard vocabulary has no atom for decides between them.  On r3 this was real:
   `ACTION2` from anchor (14,14) was `none` once and `move(-6,0)` twelve times.

The trajectory is deterministic and depends on nothing but its arguments.
"""

from typing import Dict, List, Optional, Sequence, Tuple

BACKGROUND = 0
FLOOR = 5
INK = 9
COUNTER = 1

H = W = 16
FLOOR_BOX = (2, 2, 13, 13)          # r0, c0, r1, c1 inclusive
RING_SIZE = 5
TOP = (3, 5)                        # anchor of the ring, upper berth
BOTTOM = (8, 5)                     # anchor of the ring, lower berth

Frame = List[List[int]]


def ring_cells(anchor: Tuple[int, int]) -> List[Tuple[int, int]]:
    """The 24 cells of the annulus: a 5x5 block minus its centre."""
    r0, c0 = anchor
    mid = RING_SIZE // 2
    return [(r0 + dr, c0 + dc)
            for dr in range(RING_SIZE) for dc in range(RING_SIZE)
            if not (dr == mid and dc == mid)]


def _blank() -> Frame:
    grid = [[BACKGROUND] * W for _ in range(H)]
    r0, c0, r1, c1 = FLOOR_BOX
    for r in range(r0, r1 + 1):
        for c in range(c0, c1 + 1):
            grid[r][c] = FLOOR
    return grid


def frame_at(anchor: Tuple[int, int], counter: int = 0) -> Frame:
    """The world with the ring at `anchor` and `counter` tally marks lit."""
    grid = _blank()
    for r, c in ring_cells(anchor):
        grid[r][c] = INK
    for i in range(counter):
        grid[0][i] = COUNTER            # a tally the guard vocabulary cannot name
    return grid


#: what each action does to the ring, as (from_anchor -> to_anchor).
#: ACTION1 drives it down, ACTION2 drives it up, ACTION3 and ACTION4 are inert.
SCRIPT: Dict[str, Dict[Tuple[int, int], Tuple[int, int]]] = {
    "ACTION1": {TOP: BOTTOM, BOTTOM: BOTTOM},
    "ACTION2": {TOP: TOP, BOTTOM: TOP},
    "ACTION3": {TOP: TOP, BOTTOM: BOTTOM},
    "ACTION4": {TOP: TOP, BOTTOM: BOTTOM},
}

DEFAULT_ACTIONS: Tuple[str, ...] = (
    "ACTION1", "ACTION2", "ACTION3", "ACTION1", "ACTION2",
    "ACTION4", "ACTION1", "ACTION3", "ACTION2", "ACTION1",
    "ACTION2", "ACTION4",
)


def trajectory(actions: Optional[Sequence[str]] = None,
               hidden_state: bool = False,
               ) -> Tuple[List[Frame], List[str]]:
    """`(frames, actions)`, with `len(frames) == len(actions) + 1`.

    With `hidden_state=True` the ring refuses to move on the *first* `ACTION1`
    it sees from `TOP` and obeys every later one.  The deciding state is the
    tally in row 0, which is in the frame and so is visible to the miner's
    `State` -- but there is no atom that reads it, which is exactly the
    condition under which a frontier engine must say "this class has no guard in
    this vocabulary" instead of throwing away the whole track.
    """
    acts = list(DEFAULT_ACTIONS if actions is None else actions)
    anchor = TOP
    counter = 0
    frames = [frame_at(anchor, counter)]
    seen_action1 = False
    for action in acts:
        nxt = SCRIPT[action][anchor]
        if hidden_state and action == "ACTION1" and anchor == TOP and not seen_action1:
            nxt = anchor                       # the one disobedient transition
        if action == "ACTION1":
            seen_action1 = True
        if action in ("ACTION1", "ACTION2"):
            counter = min(counter + 1, W - 1)  # the tally advances, unreadably
        anchor = nxt
        frames.append(frame_at(anchor, counter))
    return frames, acts
