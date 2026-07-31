"""World **S** behind the handoff: `a0-spike`'s world, sealed.

Imported read-only. The wrapper calls the world's public functions and hands
back pictures; it never re-exports the module, the rule table, the oracle, or
the level names. Level ids are deliberately neutral -- the originals are `match`
and `mismatch`, and telling a visitor which is which gives away the answer to
the only interesting question about them.
"""

import os
import sys
from typing import Any, Dict, List, Tuple

from a2_crosscheck.bridge import isolate
from a2_crosscheck.bridge.handoff import Frame, LevelInfo, SealedWorld

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_ROOTS = [os.path.join(HERE, "a0-spike"), os.path.join(HERE, "engine-rig")]

# Sealed: loaded under a private alias, never re-exported, never handed on.
_levels = isolate.load(_ROOTS, "world.levels", "_ccS.")
_sokoban2 = isolate.load(_ROOTS, "world.sokoban2", "_ccS.")


# neutral id -> the level object. The mapping is the seal.
_LEVELS: Dict[str, Any] = {
    "s-alpha": _levels.MATCH,
    "s-beta": _levels.MISMATCH,
}
for _i, _lvl in enumerate(_levels.CROSSING_LEVELS, start=1):
    _LEVELS["s-ev%d" % _i] = _lvl

_NOTES = {
    "s-alpha": "a task level",
    "s-beta": "a task level",
}


class WorldS(SealedWorld):
    world_id = "S"
    actions = ("UP", "DOWN", "LEFT", "RIGHT")
    background = 0
    rendering_note = (
        "Row-major grid of small non-negative integers. 0 is background. Every "
        "other value is a colour whose meaning is yours to infer; the palette is "
        "not part of the handoff. The goal cell is not drawn."
    )

    def levels(self) -> List[LevelInfo]:
        out = []
        for level_id in sorted(_LEVELS):
            lvl = _LEVELS[level_id]
            out.append(
                LevelInfo(
                    level_id=level_id,
                    height=lvl.height,
                    width=lvl.width,
                    goal_object_start=tuple(lvl.box),
                    goal_cell=tuple(lvl.target),
                    note=_NOTES.get(
                        level_id,
                        "an evidence level: its goal is already satisfied at t0, "
                        "so it is worth acting in but not worth planning for",
                    ),
                )
            )
        return out

    # ------------------------------------------------------------- internals

    def _reset(self, level_id: str) -> Any:
        return _sokoban2.initial_state(_LEVELS[level_id])

    def _advance(self, level_id: str, state: Any, action: str) -> Any:
        nxt, _event = _sokoban2.step(_LEVELS[level_id], state, action)
        return nxt                      # the event label stays behind the seal

    def _render(self, level_id: str, state: Any) -> Frame:
        return _sokoban2.render(_LEVELS[level_id], state)

    def _won(self, level_id: str, state: Any) -> bool:
        return tuple(state.box) == tuple(_LEVELS[level_id].target)


def open_world() -> WorldS:
    return WorldS()
