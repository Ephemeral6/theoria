"""World **C** behind the handoff: `cold-start-a0`'s world, sealed.

`cold-start-a0/` belongs to the theory-compiler track. It is imported here and
never written to; the import is the whole of the contact.

As with World S the level ids are neutral. The originals are `a0-base` and
`a0-no-button`, and the second name states the finding.
"""

import os
import sys
from typing import Any, Dict, List

from crosscheck.bridge import isolate
from crosscheck.bridge.handoff import Frame, LevelInfo, SealedWorld

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_ROOTS = [os.path.join(HERE, "cold-start-a0"), os.path.join(HERE, "engine-rig")]

# Sealed: loaded under a private alias, never re-exported, never handed on.
_a0_world = isolate.load(_ROOTS, "world.a0_world", "_ccC.")


_SPECS: Dict[str, Any] = {
    "c-alpha": _a0_world.BASE,
    "c-beta": _a0_world.NO_BUTTON,
}


class WorldC(SealedWorld):
    world_id = "C"
    actions = ("UP", "DOWN", "LEFT", "RIGHT")
    background = 0
    rendering_note = (
        "Row-major grid of small non-negative integers. 0 is background. Every "
        "other value is a colour whose meaning is yours to infer; the palette is "
        "not part of the handoff. The goal cell is not drawn."
    )

    def __init__(self) -> None:
        super().__init__()
        self._worlds = {k: _a0_world.A0World(spec) for k, spec in _SPECS.items()}

    def levels(self) -> List[LevelInfo]:
        out = []
        for level_id in sorted(_SPECS):
            spec = _SPECS[level_id]
            out.append(
                LevelInfo(
                    level_id=level_id,
                    height=_a0_world.HEIGHT,
                    width=_a0_world.WIDTH,
                    goal_object_start=tuple(spec.cart_start),
                    goal_cell=tuple(spec.goal_cell),
                    note="a task level",
                )
            )
        return out

    # ------------------------------------------------------------- internals

    def _reset(self, level_id: str) -> Any:
        return self._worlds[level_id].initial()

    def _advance(self, level_id: str, state: Any, action: str) -> Any:
        return self._worlds[level_id].step(state, action)

    def _render(self, level_id: str, state: Any) -> Frame:
        return self._worlds[level_id].render(state)

    def _won(self, level_id: str, state: Any) -> bool:
        return self._worlds[level_id].is_win(state)


def open_world() -> WorldC:
    return WorldC()
