"""Two red lines, enforced rather than promised.

**Zero API, zero network.**  The exam is the *active* instrument -- it sets
questions and needs a new run -- which is exactly why it is the instrument most
likely to reach for the live game.  The whole dress rehearsal happens in
self-built worlds, so nothing here should ever open a socket.  `no_network()` is
a context manager that makes `socket.socket` raise; the test suite runs the
paper builders inside it, so "zero API" is a property the suite would fail to
report rather than a sentence in a README.

**The sealed pile is untouchable.**  Reused wholesale from `battery.guard` --
same cut, same digest check, same refusal of unknown ids.  Importing it rather
than reimplementing is deliberate: two copies of a guardrail drift, and the copy
that drifts is the one that lets something through.  We add one thing on top:
`assert_synthetic_world`, because at this phase an exam question has no business
naming *any* live game, dev pile included.  Phase 4 lifts that to the dev pile
by passing `allow_dev=True`; the sealed pile is never lifted.
"""

from __future__ import annotations

import os
import socket
import sys
from contextlib import contextmanager
from typing import Any, Dict, Iterator, Optional

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
if REPO not in sys.path:
    sys.path.insert(0, REPO)

from battery.guard import (  # noqa: E402
    CutIntegrityError, Piles, SealedPileError, UnknownGameError, load_piles,
)

__all__ = ["CutIntegrityError", "Piles", "SealedPileError", "UnknownGameError",
           "load_piles", "NetworkForbidden", "no_network",
           "assert_synthetic_world", "provenance"]

#: Worlds an exam may be set in at this phase.  All self-built, all with fully
#: known ground truth, none in either pile.
SYNTHETIC_WORLDS = ("a0", "a0-prime", "a2")


class NetworkForbidden(RuntimeError):
    """Something in the exam tried to open a socket."""


@contextmanager
def no_network() -> Iterator[None]:
    """Make socket creation raise for the duration.

    Not a sandbox -- a process determined to get out can get out.  It is a
    tripwire for the accident that actually happens: a helper three imports
    down that quietly fetches something.
    """
    real_socket = socket.socket
    real_create = socket.create_connection

    def _refuse(*args: Any, **kwargs: Any) -> Any:
        raise NetworkForbidden(
            "the exam does not open sockets. Every question is set in a "
            "self-built world; a socket here means something reached for the "
            "live game or the network by accident.")

    socket.socket = _refuse          # type: ignore[assignment]
    socket.create_connection = _refuse   # type: ignore[assignment]
    try:
        yield
    finally:
        socket.socket = real_socket        # type: ignore[assignment]
        socket.create_connection = real_create   # type: ignore[assignment]


def assert_synthetic_world(world_id: Optional[str], *,
                           allow_dev: bool = False,
                           piles: Optional[Piles] = None) -> str:
    """Refuse any world that is not one of ours.

    A `None` world_id is refused too.  Unlike the battery -- which meets
    genuinely synthetic runs carrying no id -- an exam item always knows which
    world it was set in, so a missing id is a bug, not a synthetic run.
    """
    if world_id is None:
        raise UnknownGameError(
            "an exam item must name the world it was set in; None is not a "
            "synthetic world, it is a missing field.")
    key = world_id.strip().lower()
    if key in SYNTHETIC_WORLDS:
        return "synthetic"
    piles = piles or load_piles()
    verdict = piles.classify(world_id)
    if verdict == "sealed":
        raise SealedPileError(
            "%r is in the sealed pile. Constructing an exam question about a "
            "sealed game requires understanding its mechanics, and that is the "
            "contamination the cut exists to prevent. Theoria.md Phase 4 orders "
            "this the other way round: the main table runs first, and only then "
            "are the exam-subset games studied." % world_id)
    if verdict == "dev" and allow_dev:
        return "dev"
    if verdict == "dev":
        raise UnknownGameError(
            "%r is a dev-pile game. The rehearsal is set in self-built worlds "
            "only (%s); pass allow_dev=True once there is a reason to spend a "
            "dev game on a question." % (world_id, list(SYNTHETIC_WORLDS)))
    raise UnknownGameError(
        "%r is neither a self-built world nor a registered game. An unknown id "
        "is not a safe id, it is an unaudited one." % world_id)


def provenance(piles: Optional[Piles] = None) -> Dict[str, Any]:
    """What every exam artefact records about the cut it was built under."""
    piles = piles or load_piles()
    return {"synthetic_worlds": list(SYNTHETIC_WORLDS), **piles.provenance()}
