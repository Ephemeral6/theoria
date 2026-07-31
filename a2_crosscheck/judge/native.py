"""Each track's **own** manual, wearing the cross-check predictor interface.

These are the incumbents. A visiting pipeline's numbers on world C mean little
on their own; they mean something next to what `cold-start-a0`'s own manual
scores on the same sweep, because that manual was written by someone who could
see the world and was allowed to iterate.

Both natives are loaded from their compiled forms, never re-implemented here.
`a0-spike` compiles `theory/theory.dsl` per level through its own `gen_exec`;
`cold-start-a0` ships `theory/generated*/theory.py`. Wrapping is a matter of
reading a state out of a frame and writing one back, and in both cases the
palette needed to do that is referee knowledge -- which is why this file is on
the referee's side of the wall.
"""

import importlib.util
import os
from typing import Any, Dict, List, Tuple

from a2_crosscheck.bridge import isolate
from a2_crosscheck.judge import truth

Frame = List[List[int]]

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_SPIKE = os.path.join(HERE, "a0-spike")
_COLD = os.path.join(HERE, "cold-start-a0")

_S_ROOTS = [_SPIKE, os.path.join(HERE, "engine-rig")]
_gen_exec = isolate.load(_S_ROOTS, "pipeline.gen_exec", "_ccS.")

_C_ACTION = {"UP": ("push", "Cart", "up"), "DOWN": ("push", "Cart", "down"),
             "LEFT": ("push", "Cart", "left"), "RIGHT": ("push", "Cart", "right")}

_C_THEORY_DIR = {"c-alpha": "generated", "c-beta": "generated_no_button"}


class NativeRefused(RuntimeError):
    """The incumbent manual declined to predict. Recorded, never smoothed over."""


# --------------------------------------------------------------------- world S

_s_modules: Dict[str, Dict[str, Any]] = {}


def _s_module(level_id: str) -> Dict[str, Any]:
    if level_id not in _s_modules:
        level = truth.S_LEVELS[level_id]
        dsl = open(os.path.join(_SPIKE, "theory", "theory.dsl"),
                   encoding="utf-8").read()
        _s_modules[level_id] = _gen_exec.compile_module(
            dsl, level.height, level.width, level.walls)
    return _s_modules[level_id]


def _s_step_frame(level_id: str, frame: Frame, action: str) -> Frame:
    module = _s_module(level_id)
    player = box = None
    for r, row in enumerate(frame):
        for c, value in enumerate(row):
            if value == 2:
                player = (r, c)
            elif value == 4:
                box = (r, c)
    if player is None or box is None:
        raise NativeRefused("a0-spike manual cannot read this frame")
    try:
        nxt = module["step"](module["State"](player=player, box=box), action)
    except Exception as exc:
        raise NativeRefused(str(exc)[:200])
    return nxt.render()


# --------------------------------------------------------------------- world C

_c_modules: Dict[str, Any] = {}


def _c_module(level_id: str) -> Any:
    if level_id not in _c_modules:
        path = os.path.join(_COLD, "theory", _C_THEORY_DIR[level_id], "theory.py")
        spec = importlib.util.spec_from_file_location(
            "_ccC.native.%s" % level_id, path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        _c_modules[level_id] = module
    return _c_modules[level_id]


def _c_state_from_frame(module: Any, frame: Frame) -> Any:
    """Read the manual's own state out of a picture.

    Deliberately expressed in the manual's vocabulary rather than the world's:
    the cart is whatever carries the cart's declared colour, and the door is
    present iff its cell still carries the door's declared colour. A manual that
    does not declare a door -- as the no-button one does not, having sunk it into
    the board -- simply has no field to fill.
    """
    state = module.initial_state()
    cart_colour = getattr(state, "Cart_colour")
    found = [(r, c) for r, row in enumerate(frame)
             for c, value in enumerate(row) if value == cart_colour]
    if len(found) != 1:
        raise NativeRefused("cold-start-a0 manual sees %d carts" % len(found))
    state.Cart_pos = found[0]
    if hasattr(state, "Door_present"):
        door = state.Door_pos
        state.Door_present = frame[door[0]][door[1]] == state.Door_colour
    if hasattr(state, "Button_colour"):
        button = state.Button_pos
        seen = frame[button[0]][button[1]]
        if seen in (7, 8):
            state.Button_colour = seen
    return state


def _c_step_frame(level_id: str, frame: Frame, action: str) -> Frame:
    module = _c_module(level_id)
    state = _c_state_from_frame(module, frame)
    try:
        nxt = module.step(state, _C_ACTION[action])
    except Exception as exc:
        raise NativeRefused("%s: %s" % (type(exc).__name__, str(exc)[:200]))
    return module.render(nxt)


# ------------------------------------------------------------------ the facade

def _s_firing(level_id: str, frame: Frame, action: str) -> List[str]:
    module = _s_module(level_id)
    player = box = None
    for r, row in enumerate(frame):
        for c, value in enumerate(row):
            if value == 2:
                player = (r, c)
            elif value == 4:
                box = (r, c)
    if player is None or box is None:
        return []
    fired = []
    for name, rule in module["RULES"]:
        trial = module["State"](player=player, box=box)
        if rule(trial, action):
            fired.append(name)
    return fired


def _c_firing(level_id: str, frame: Frame, action: str) -> List[str]:
    module = _c_module(level_id)
    try:
        state = _c_state_from_frame(module, frame)
    except NativeRefused:
        return []
    return [name for name, guard, _effect, _obj in module.RULES
            if guard(state, _C_ACTION[action])]


# ------------------------------------------------------------------ the facade

_NATIVE = {"S": _s_step_frame, "C": _c_step_frame}
_FIRING = {"S": _s_firing, "C": _c_firing}


def native_rules(world_id: str, level_id: str) -> List[str]:
    """The incumbent manual's rule names, in file order."""
    if world_id == "S":
        return [name for name, _fn in _s_module(level_id)["RULES"]]
    return [name for name, _g, _e, _o in _c_module(level_id).RULES]


def native_firing(world_id: str, level_id: str, frame: Frame,
                  action: str) -> List[str]:
    """Which of the incumbent's rules claim this (state, action).

    Rule *recovery* is measured against these sets rather than against the text
    of the manual. Two manuals can name the same mechanism differently, split it
    across a different number of rules, or fold it into a guard, and a
    string-level comparison would score all three as failures. What a rule *is*,
    operationally, is the set of transitions it claims; a visitor has recovered
    it when it predicts every one of them correctly, whatever it called them.
    """
    return _FIRING[world_id](level_id, frame, action)


SOURCE = {
    "S": "a0-spike/theory/theory.dsl -> pipeline/gen_exec.py (per level)",
    "C": "cold-start-a0/theory/generated{,_no_button}/theory.py",
}


def native_step_frame(world_id: str, level_id: str, frame: Frame, action: str) -> Frame:
    return _NATIVE[world_id](level_id, frame, action)
