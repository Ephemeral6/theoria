"""Fixture A - the Cart world.

A 12x12 grid, background colour 0, one 2x3 connected block of colour 6 (the
"Cart").  The dynamics are:

  push      : on action D, if every cell of the strip adjacent to the Cart in
              direction D is inside the grid and empty, the Cart moves one cell
              in direction D.  Otherwise nothing happens.
  teleport  : if the Cart's anchor sits on PORTAL_A, the next frame has the Cart
              at PORTAL_B, whatever the action was.  This fires EXACTLY ONCE in
              the trajectory -- it is the deliberately thin-evidence rule that
              cegis_miner must report as coverage 1/1.

The teleport step is scripted so that the push guard is false there (the Cart is
at the top-left corner and the action is UP, blocked by the wall).  That keeps
the two rules' guards mutually exclusive, i.e. the "exactly one successor"
obligation holds on this fixture; without it, "push" and "teleport" would both
match one transition and rule mining would be ill-posed.

Serialisation: one JSON object per line, `{"frame": <12x12 array>, "action": D}`.
The last line carries the final frame with `"action": null` -- there are N frames
and N-1 actions, and dropping the final frame would lose an observation.
See DECISIONS.md D-001.
"""

import os
from typing import Dict, List, Optional, Tuple

from common.jsonio import write_json, write_jsonl
from common.rng import SplitMix64

GRID_H = 12
GRID_W = 12
BACKGROUND = 0
CART_COLOR = 6
CART_H = 2
CART_W = 3

DIRECTIONS = ("UP", "DOWN", "LEFT", "RIGHT")
DELTA: Dict[str, Tuple[int, int]] = {
    "UP": (-1, 0),
    "DOWN": (1, 0),
    "LEFT": (0, -1),
    "RIGHT": (0, 1),
}

PORTAL_A = (0, 0)   # anchor (top-left cell of the Cart)
PORTAL_B = (8, 8)

START_ANCHOR = (5, 5)
SEED = 0xC0FFEE
N_FRAMES = 50       # inside the requested 40-60 band

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
TRAJ_PATH = os.path.join(DATA_DIR, "cart_world.jsonl")
TRUTH_PATH = os.path.join(DATA_DIR, "cart_world_truth.json")


def cart_cells(anchor: Tuple[int, int]) -> List[Tuple[int, int]]:
    r, c = anchor
    return [(r + dr, c + dc) for dr in range(CART_H) for dc in range(CART_W)]


def render(anchor: Tuple[int, int]) -> List[List[int]]:
    grid = [[BACKGROUND] * GRID_W for _ in range(GRID_H)]
    for (r, c) in cart_cells(anchor):
        grid[r][c] = CART_COLOR
    return grid


def strip_cells(anchor: Tuple[int, int], direction: str) -> List[Tuple[int, int]]:
    """The cells the Cart would sweep into when moving one step in `direction`."""
    r, c = anchor
    if direction == "UP":
        return [(r - 1, c + dc) for dc in range(CART_W)]
    if direction == "DOWN":
        return [(r + CART_H, c + dc) for dc in range(CART_W)]
    if direction == "LEFT":
        return [(r + dr, c - 1) for dr in range(CART_H)]
    if direction == "RIGHT":
        return [(r + dr, c + CART_W) for dr in range(CART_H)]
    raise ValueError(direction)


def in_bounds(cell: Tuple[int, int]) -> bool:
    r, c = cell
    return 0 <= r < GRID_H and 0 <= c < GRID_W


def strip_free(anchor: Tuple[int, int], direction: str) -> bool:
    """Ground truth push guard: the whole target strip is in-bounds and empty.

    With a single object on the board "in-bounds" already implies "empty"; the
    guard is written in the general form because that is the rule of the world,
    not an artefact of this trajectory (see DECISIONS.md D-002).
    """
    cells = strip_cells(anchor, direction)
    if not all(in_bounds(cell) for cell in cells):
        return False
    occupied = set(cart_cells(anchor))
    return all(cell not in occupied for cell in cells)


def step(anchor: Tuple[int, int], action: str) -> Tuple[Tuple[int, int], str]:
    """Ground-truth transition. Returns (next anchor, event label)."""
    if anchor == PORTAL_A:
        return PORTAL_B, "teleport"
    if strip_free(anchor, action):
        dr, dc = DELTA[action]
        return (anchor[0] + dr, anchor[1] + dc), "move:" + action
    return anchor, "noop"


def _drive(anchor: Tuple[int, int], direction: str, times: int) -> List[str]:
    return [direction] * times


def build_actions() -> List[str]:
    """Deterministic action script; exactly N_FRAMES-1 actions.

    Phase 1  random walk (never landing on PORTAL_A)
    Phase 2  drive to the top wall, bump UP once (blocked), drive left to
             PORTAL_A, then act UP -> the single teleport
    Phase 3  wall tour from PORTAL_B (one blocked DOWN, RIGHT and LEFT each) so
             that every direction has both a moving and a blocked witness, then
             random walk padding to length
    """
    rng = SplitMix64(SEED)
    actions: List[str] = []
    anchor = START_ANCHOR

    def push(action: str) -> None:
        nonlocal anchor
        actions.append(action)
        anchor = step(anchor, action)[0]

    def random_walk(n: int) -> None:
        for _ in range(n):
            # Reject any action that would land the Cart on PORTAL_A: the
            # teleport must be witnessed exactly once, at the scripted step.
            offset = rng.below(4)
            for k in range(4):
                cand = DIRECTIONS[(offset + k) % 4]
                if step(anchor, cand)[0] != PORTAL_A:
                    push(cand)
                    break
            else:  # pragma: no cover - unreachable on a 12x12 board
                raise AssertionError("no safe action available")

    random_walk(12)

    # Phase 2: up to the top wall, one blocked UP, then left into PORTAL_A.
    for _ in _drive(anchor, "UP", anchor[0]):
        push("UP")
    assert anchor[0] == 0, anchor
    push("UP")                      # blocked by the wall -> noop witness for UP
    for _ in range(anchor[1]):
        push("LEFT")
    assert anchor == PORTAL_A, anchor
    push("UP")                      # the teleport (push guard is false here)
    assert anchor == PORTAL_B, anchor

    # Phase 3: wall tour.
    while anchor[0] < GRID_H - CART_H:
        push("DOWN")
    push("DOWN")                    # blocked
    while anchor[1] < GRID_W - CART_W:
        push("RIGHT")
    push("RIGHT")                   # blocked
    while anchor[1] > 0:
        push("LEFT")
    push("LEFT")                    # blocked
    random_walk(max(0, (N_FRAMES - 1) - len(actions)))

    if len(actions) != N_FRAMES - 1:
        raise AssertionError(
            "script produced %d actions, need %d" % (len(actions), N_FRAMES - 1)
        )
    return actions


def simulate(actions: List[str]) -> Dict[str, object]:
    anchor = START_ANCHOR
    anchors = [anchor]
    events = []
    for action in actions:
        anchor, event = step(anchor, action)
        anchors.append(anchor)
        events.append(event)
    return {"anchors": anchors, "events": events}


def generate() -> Dict[str, object]:
    """Build the trajectory in memory. Pure function of the module constants."""
    actions = build_actions()
    sim = simulate(actions)
    anchors: List[Tuple[int, int]] = sim["anchors"]      # type: ignore[assignment]
    events: List[str] = sim["events"]                    # type: ignore[assignment]

    teleports = [i for i, e in enumerate(events) if e == "teleport"]
    if len(teleports) != 1:
        raise AssertionError("expected exactly one teleport, got %r" % (teleports,))
    for direction in DIRECTIONS:
        moved = any(e == "move:" + direction for e in events)
        blocked = any(
            events[i] == "noop" and actions[i] == direction for i in range(len(actions))
        )
        if not (moved and blocked):
            raise AssertionError(
                "direction %s lacks a moving (%s) or blocked (%s) witness"
                % (direction, moved, blocked)
            )

    rows = []
    for t, anchor in enumerate(anchors):
        action: Optional[str] = actions[t] if t < len(actions) else None
        rows.append({"frame": render(anchor), "action": action})

    truth = {
        "grid": [GRID_H, GRID_W],
        "background": BACKGROUND,
        "cart": {"color": CART_COLOR, "height": CART_H, "width": CART_W},
        "portal_a": list(PORTAL_A),
        "portal_b": list(PORTAL_B),
        "seed": SEED,
        "n_frames": len(anchors),
        "anchors": [list(a) for a in anchors],
        "masks": [sorted([list(c) for c in cart_cells(a)]) for a in anchors],
        "actions": actions,
        "events": events,
        "teleport_transition": teleports[0],
    }
    return {"rows": rows, "truth": truth}


def write(traj_path: str = TRAJ_PATH, truth_path: str = TRUTH_PATH) -> Dict[str, object]:
    out = generate()
    write_jsonl(traj_path, out["rows"])          # type: ignore[arg-type]
    write_json(truth_path, out["truth"])
    return out


if __name__ == "__main__":  # pragma: no cover
    result = write()
    print("cart_world: %d frames -> %s" % (len(result["rows"]), TRAJ_PATH))
