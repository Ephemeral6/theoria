"""The sealed-world registry.

    from a2_crosscheck.bridge import open_world
    world = open_world("C")          # the other track's world, frames only

`open_world` is the *only* import a visiting pipeline is permitted. Reaching
past it -- importing `world.a0_world`, reading `cold-start-a0/theory/`, or
opening either A0 README -- voids the run, because every one of those states the
mechanics in prose and the experiment is about arriving cold.
"""

from typing import TYPE_CHECKING

from a2_crosscheck.bridge.handoff import (          # noqa: F401
    Episode,
    Frame,
    LevelInfo,
    Ledger,
    SealedWorld,
    describe_frame,
    frame_key,
    frames_equal,
    parse_frame,
)

WORLDS = ("S", "C")


def open_world(world_id: str) -> "SealedWorld":
    """`"S"` is a0-spike's world, `"C"` is cold-start-a0's. Nothing else."""
    key = world_id.strip().upper()
    if key == "S":
        from a2_crosscheck.bridge.world_s import open_world as _open
        return _open()
    if key == "C":
        from a2_crosscheck.bridge.world_c import open_world as _open
        return _open()
    raise KeyError("no sealed world %r; have %s" % (world_id, list(WORLDS)))
