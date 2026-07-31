"""The referee's copy: both worlds' ground truth, behind the predictor contract.

Nothing here may be imported by a cross-run. It exists so that every claim a
visitor makes can be checked against the world rather than against a story about
the world.

Two things are exported per world:

* `truth_step_frame(level_id, frame, action)` -- the world itself, wearing the
  same interface a visitor's manual has to wear. Comparison is then a `==`.
* `representable_frames(level_id)` -- every state the level can *represent*,
  rendered. Not the reachable ones. `CONTRACTS/dsl_grammar_v0.2.md` insists on
  that distinction and both A0 runs paid for it: a rule can be right as a
  problem solution and wrong as a domain, and only the full sweep can tell.

Reachability is reported alongside rather than instead, because "wrong only in
unreachable states" is a materially different finding from "wrong where the game
actually goes", and collapsing the two would hide which one happened.
"""

import os
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from a2_crosscheck.bridge import isolate

Cell = Tuple[int, int]
Frame = List[List[int]]

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_S_ROOTS = [os.path.join(HERE, "a0-spike"), os.path.join(HERE, "engine-rig")]
_C_ROOTS = [os.path.join(HERE, "cold-start-a0"), os.path.join(HERE, "engine-rig")]

_s_levels = isolate.load(_S_ROOTS, "world.levels", "_ccS.")
_s_world = isolate.load(_S_ROOTS, "world.sokoban2", "_ccS.")
_c_world = isolate.load(_C_ROOTS, "world.a0_world", "_ccC.")

# The bridge's neutral ids, mapped back to the real levels. Kept here rather
# than imported from the bridge so that the seal has exactly one keyholder.
S_LEVELS: Dict[str, Any] = {"s-alpha": _s_levels.MATCH, "s-beta": _s_levels.MISMATCH}
for _i, _lvl in enumerate(_s_levels.CROSSING_LEVELS, start=1):
    S_LEVELS["s-ev%d" % _i] = _lvl

C_SPECS: Dict[str, Any] = {"c-alpha": _c_world.BASE, "c-beta": _c_world.NO_BUTTON}
_C_WORLDS = {k: _c_world.A0World(v) for k, v in C_SPECS.items()}

LEVELS_OF = {"S": sorted(S_LEVELS), "C": sorted(C_SPECS)}
TASK_LEVELS_OF = {"S": ["s-alpha", "s-beta"], "C": ["c-alpha", "c-beta"]}


class IllFormedFrame(ValueError):
    """The referee could not read a state out of this picture."""


# --------------------------------------------------------------------- world S

def _s_state_from_frame(level, frame: Frame):
    player = box = None
    for r, row in enumerate(frame):
        for c, value in enumerate(row):
            if value == _s_world.PLAYER:
                player = (r, c)
            elif value == _s_world.BOX:
                box = (r, c)
    if player is None or box is None:
        raise IllFormedFrame("world S frame without a player (%r) or a box (%r)"
                             % (player, box))
    return _s_world.State(player=player, box=box)


def _s_step_frame(level_id: str, frame: Frame, action: str) -> Frame:
    level = S_LEVELS[level_id]
    nxt, _event = _s_world.step(level, _s_state_from_frame(level, frame), action)
    return _s_world.render(level, nxt)


def _s_states(level_id: str) -> List[Any]:
    level = S_LEVELS[level_id]
    walls = set(level.walls)
    cells = [(r, c) for r in range(level.height) for c in range(level.width)
             if (r, c) not in walls]
    return [_s_world.State(player=p, box=b)
            for p in cells for b in cells if p != b]


def _s_render(level_id: str, state: Any) -> Frame:
    return _s_world.render(S_LEVELS[level_id], state)


def _s_initial(level_id: str) -> Any:
    return _s_world.initial_state(S_LEVELS[level_id])


def _s_won(level_id: str, state: Any) -> bool:
    return tuple(state.box) == tuple(S_LEVELS[level_id].target)


# --------------------------------------------------------------------- world C

def _c_state_from_frame(level_id: str, frame: Frame):
    spec = C_SPECS[level_id]
    cart = None
    for r, row in enumerate(frame):
        for c, value in enumerate(row):
            if value == _c_world.CART:
                cart = (r, c)
    if cart is None:
        raise IllFormedFrame("world C frame without a cart")
    # `pressed` is visible twice in the base level (the button's colour and the
    # door's absence) and once in the variant (the door alone). Read the door,
    # which both levels draw, and cross-check the button when it is there.
    door = spec.door_cell
    pressed = True
    if door is not None and cart != tuple(door):
        pressed = frame[door[0]][door[1]] != _c_world.DOOR_CLOSED
    button = spec.button_cell
    if button is not None and cart != tuple(button):
        by_button = frame[button[0]][button[1]] == _c_world.BUTTON_DOWN
        if door is not None and cart != tuple(door) and by_button != pressed:
            raise IllFormedFrame(
                "world C frame disagrees with itself: button says pressed=%s, "
                "door says pressed=%s" % (by_button, pressed))
        pressed = by_button
    return _c_world.State(cart=cart, pressed=pressed)


def _c_step_frame(level_id: str, frame: Frame, action: str) -> Frame:
    world = _C_WORLDS[level_id]
    return world.render(world.step(_c_state_from_frame(level_id, frame), action))


def _c_states(level_id: str) -> List[Any]:
    world = _C_WORLDS[level_id]
    spec = C_SPECS[level_id]
    out = []
    for cell in world.passable_cells():
        for pressed in (False, True):
            if spec.door_cell is not None and cell == tuple(spec.door_cell) \
                    and not pressed:
                continue                  # the closed door is standing there
            out.append(_c_world.State(cart=cell, pressed=pressed))
    return out


def _c_render(level_id: str, state: Any) -> Frame:
    return _C_WORLDS[level_id].render(state)


def _c_initial(level_id: str) -> Any:
    return _C_WORLDS[level_id].initial()


def _c_won(level_id: str, state: Any) -> bool:
    return _C_WORLDS[level_id].is_win(state)


# ------------------------------------------------------------------ the facade

_IMPL = {
    "S": {"step": _s_step_frame, "states": _s_states, "render": _s_render,
          "initial": _s_initial, "won": _s_won, "actions": _s_world.DIRECTIONS},
    "C": {"step": _c_step_frame, "states": _c_states, "render": _c_render,
          "initial": _c_initial, "won": _c_won, "actions": _c_world.ACTIONS},
}


def actions_of(world_id: str) -> Tuple[str, ...]:
    return tuple(_IMPL[world_id]["actions"])


def truth_step_frame(world_id: str, level_id: str, frame: Frame, action: str) -> Frame:
    return _IMPL[world_id]["step"](level_id, frame, action)


def representable_frames(world_id: str, level_id: str) -> List[Frame]:
    impl = _IMPL[world_id]
    return [impl["render"](level_id, s) for s in impl["states"](level_id)]


def reachable_frames(world_id: str, level_id: str) -> List[Frame]:
    """Frames the level actually reaches from its own initial state."""
    impl = _IMPL[world_id]
    start = impl["render"](level_id, impl["initial"](level_id))
    seen = {_key(start): start}
    frontier = [start]
    while frontier:
        frame = frontier.pop()
        for action in actions_of(world_id):
            nxt = impl["step"](level_id, frame, action)
            if _key(nxt) not in seen:
                seen[_key(nxt)] = nxt
                frontier.append(nxt)
    return [seen[k] for k in sorted(seen)]


def _key(frame: Frame) -> Tuple[Tuple[int, ...], ...]:
    return tuple(tuple(int(v) for v in row) for row in frame)


def execute(world_id: str, level_id: str, actions: Sequence[str]) -> Dict[str, Any]:
    """Run a plan in the true world and say whether it won."""
    impl = _IMPL[world_id]
    state_frame = impl["render"](level_id, impl["initial"](level_id))
    won_at: Optional[int] = None
    for t, action in enumerate(actions):
        state_frame = impl["step"](level_id, state_frame, action)
        if _frame_wins(world_id, level_id, state_frame) and won_at is None:
            won_at = t + 1
    return {"length": len(actions), "won": won_at is not None, "won_at": won_at,
            "final_frame": state_frame}


def _frame_wins(world_id: str, level_id: str, frame: Frame) -> bool:
    if world_id == "S":
        return _s_won(level_id, _s_state_from_frame(S_LEVELS[level_id], frame))
    return _c_won(level_id, _c_state_from_frame(level_id, frame))


def solvable(world_id: str, level_id: str) -> Dict[str, Any]:
    """Ground truth for the plan question: shortest winning action sequence."""
    from collections import deque

    impl = _IMPL[world_id]
    start = impl["render"](level_id, impl["initial"](level_id))
    if _frame_wins(world_id, level_id, start):
        return {"solvable": True, "optimal_length": 0, "optimal_plan": []}
    seen = {_key(start)}
    queue = deque([(start, [])])
    while queue:
        frame, plan = queue.popleft()
        for action in actions_of(world_id):
            nxt = impl["step"](level_id, frame, action)
            if _key(nxt) in seen:
                continue
            if _frame_wins(world_id, level_id, nxt):
                return {"solvable": True, "optimal_length": len(plan) + 1,
                        "optimal_plan": plan + [action]}
            seen.add(_key(nxt))
            queue.append((nxt, plan + [action]))
    return {"solvable": False, "optimal_length": None, "optimal_plan": None}
