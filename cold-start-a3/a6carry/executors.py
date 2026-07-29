"""Two `Executor` adapters: A3's world, and a `worldgen` world.

They exist to show the interface is an interface.  A3's negative controls and a
world from another track's factory go through **the same** `protocol.carry`, with
nothing swapped but this object — a protocol that only ever ran against the world
it was written for would be a driver, not a protocol.

**Read-only, both of them.**  `WorldgenExecutor` imports `worldgen.core` and reads
`worldgen/out/worlds/<id>/spec.json`; it writes nothing there, and
`tools/verify_readonly.py` hashes that tree before and after a full run.  Reading
a spec is the *environment's* business, not the arm's: the arm receives frames
and never sees this object's constructor arguments.

The level constants an arm is handed — the goal cell, and any landmark — come out
of the same spec here, and that is the concession A3 recorded and this does not
reduce: `A3_REPORT` §6, "three level constants are supplied, not derived".  On
these two `worldgen` worlds it is one constant, the goal, because a `worldgen`
goal cell is not rendered either.  `constants()` returns it labelled, so it lands
in the provenance as supplied rather than blending into the derived column.
"""

import json
import os
import sys
from typing import Dict, List, Optional, Sequence, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import _bootstrap  # noqa: F401,E402

from a6carry.executor_api import Executor  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(ROOT)
WORLDGEN_OUT = os.path.join(REPO, "worldgen", "out", "worlds")

# `_bootstrap` puts `engine-rig`, `theory-compiler/src`, `cold-start-a0` and this
# directory on the path; the repository root is not among them, so `worldgen` is
# importable only when the process happens to have been started there.  That is
# the whole difference between "this executor works" and `ModuleNotFoundError`,
# and it belongs here rather than in `_bootstrap`: *this* module is the one that
# reaches out of the track, and putting the line anywhere higher would put a
# world on the path of the modules that must not have one.
if REPO not in sys.path:
    sys.path.insert(0, REPO)


# ------------------------------------------------------------------- worldgen

class WorldgenExecutor(Executor):
    """A world from `worldgen/out/worlds/<id>/`, driven through its own library.

    `worldgen` belongs to another track.  What is imported is its `core` package
    — `WorldSpec`, `GridWorld` — and what is read is the world's `spec.json`,
    which `worldgen/README.md` lists as readable by anyone ("the picture and the
    legend, already parsed").  `ground_truth.json`, `coverage.json` and
    `reversibility.json` are marked *scoring only* there and this module does not
    open them; the source is the evidence for that and a test asserts it.
    """

    def __init__(self, world_id: str, out_root: str = WORLDGEN_OUT):
        self.name = world_id
        self.world_id = world_id
        self.dir = os.path.join(out_root, world_id)
        if not os.path.isdir(self.dir):
            raise KeyError("no such worldgen world: %r" % world_id)
        with open(os.path.join(self.dir, "spec.json"), encoding="utf-8") as handle:
            self._spec_json = json.load(handle)
        from worldgen.core.spec import WorldSpec        # noqa: E402  (read-only)
        from worldgen.core.world import GridWorld       # noqa: E402
        self._spec = WorldSpec.from_json(self._spec_json)
        self._world = GridWorld(self._spec)

    # -- the level constants, labelled as supplied -------------------------
    def constants(self) -> Dict[str, Tuple[int, int]]:
        """`goal_cell`, and nothing else these two worlds need.

        A `worldgen` goal is a cell in `spec.goal` and is not drawn on any frame
        — the same situation A3 recorded as D-A3-002.  No amount of looking
        recovers it, so it is supplied, and the provenance says so.
        """
        return {"goal_cell": tuple(int(v) for v in self._spec_json["goal"])}

    def palette(self) -> Dict[str, int]:
        """The world's per-kind colour assignment, from the legend.

        `worldgen/core/types.py` assigns colours **per world** out of a pool, in
        the order kinds first appear, precisely so that a downstream reader
        cannot memorise them across worlds.  A pack that carries a colour literal
        in a guard is therefore carrying an assumption, and `protocol.carry`
        checks it against the frame rather than hoping.  This accessor exists so
        a *test* can assert the two worlds agree; the arm never calls it.
        """
        return dict(self._spec_json.get("colors") or {})

    # -- the interface ------------------------------------------------------
    def first_frame(self) -> List[List[int]]:
        return [list(row) for row in self._world.render(self._world.initial())]

    def execute(self, actions: Sequence[str]) -> Dict[str, object]:
        state = self._world.initial()
        frames = [self._world.render(state)]
        wins = [bool(self._world.is_win(state))]
        taken: List[str] = []
        for action in actions:
            if wins[-1]:
                break
            state = self._world.step(state, action)
            frames.append(self._world.render(state))
            wins.append(bool(self._world.is_win(state)))
            taken.append(action)
        return {"level": self.name, "frames": frames, "wins": wins,
                "actions": taken, "actions_spent": len(taken),
                "win": wins[-1], "plan_length": len(actions)}


# --------------------------------------------------------------------- a3world

class A3Executor(Executor):
    """A3's levels and its two negative controls, through A3's own proxy.

    Delegates to `a3world.executor.execute`, which is already the only way an A3
    arm may act.  Wrapping rather than reimplementing matters for the negative
    controls: `negctl` is only evidence if the control runs the *same* execution
    path as the real arm, and a second implementation here would quietly make it
    a different test.
    """

    #: The three level constants A3's frames cannot show — the goal cell and the
    #: two portal exits.  `A3_REPORT` §6 and `a3pipeline/transfer.py` record why
    #: these three and no others; the values are level 2's, shared by both
    #: negative controls because both render byte-identical first frames to it.
    L2_CONSTANTS: Dict[str, Tuple[int, int]] = {
        "goal_cell": (1, 1), "exit_a": (1, 5), "exit_b": (4, 1),
    }

    def __init__(self, level: str,
                 constants: Optional[Dict[str, Tuple[int, int]]] = None):
        self.name = level
        self.level = level
        self._constants = dict(constants or self.L2_CONSTANTS)

    def constants(self) -> Dict[str, Tuple[int, int]]:
        return dict(self._constants)

    def first_frame(self) -> List[List[int]]:
        from a3world.executor import execute      # noqa: E402  (act only)
        return execute(self.level, [])["frames"][0]

    def execute(self, actions: Sequence[str]) -> Dict[str, object]:
        from a3world.executor import execute      # noqa: E402
        return execute(self.level, list(actions))
