"""Mechanism — how long between seeing a rule and using it?

`Theoria.md` scopes this family to hand-annotated games and therefore to the
development pile. The annotation says, per mechanism, when it became visible
and when the arm first exploited it; the delay between the two is the most
direct behavioural reading of "understood it" that a ledger can give.

The annotation for A0 lives in `battery/adapters/a0.py`, next to the world it
describes. It carries one subtlety worth stating: a mechanism that another
mechanism unlocks is measured from the unlock, not from frame zero. The door
is not a passage until the button has opened it, and charging an arm for the
turns before the door existed would measure the world, not the arm.
"""

from __future__ import annotations

from typing import List

from battery.metrics import metric, ok, thin
from battery.model import Run


def _delays(run: Run) -> List[int]:
    out: List[int] = []
    for _, entry in sorted(run.truth.mechanisms.items()):
        seen, used = entry.get("first_seen"), entry.get("first_used")
        if seen is None or used is None:
            continue
        out.append(used - seen)
    return out


@metric("M1", "mechanism",
        "Mean steps between a mechanism becoming visible and the arm first "
        "using it, over annotated mechanisms it did use.",
        needs=("truth", "mechanisms"), direction="lower", unit="steps")
def mean_first_use_delay(run: Run):
    delays = _delays(run)
    if not delays:
        return thin("M1", "no annotated mechanism was both seen and used")
    return ok("M1", sum(delays) / len(delays), used=len(delays),
              annotated=len(run.truth.mechanisms),
              per_mechanism={name: (entry["first_used"] - entry["first_seen"])
                             for name, entry in sorted(
                                 run.truth.mechanisms.items())
                             if entry.get("first_seen") is not None
                             and entry.get("first_used") is not None})


@metric("M2", "mechanism",
        "Fraction of annotated mechanisms the arm ever used.",
        needs=("truth", "mechanisms"), direction="higher", unit="share")
def mechanism_uptake(run: Run):
    mechanisms = run.truth.mechanisms
    if not mechanisms:
        return thin("M2", "no mechanisms annotated")
    used = sum(1 for entry in mechanisms.values()
               if entry.get("first_used") is not None)
    return ok("M2", used / len(mechanisms), used=used,
              annotated=len(mechanisms))


@metric("M3", "mechanism",
        "Mean first-use delay for mechanisms met again on a later level — "
        "does understanding travel? (Claim C3.)",
        needs=("steps", "truth", "mechanisms"), direction="lower",
        unit="steps")
def cross_level_first_use_delay(run: Run):
    levels = {s.level for s in run.steps if s.level is not None}
    if len(levels) < 2:
        return thin("M3", "the run never reached a second level; transfer "
                          "cannot be measured within one level")
    # Deliberately unimplemented beyond the guard until a multi-level run
    # exists to write it against. Guessing at the shape of data nobody has
    # produced yet is how a metric ends up measuring its author's imagination.
    return thin("M3", "multi-level runs exist but the cross-level annotation "
                      "schema is not yet defined; see STATUS.md")
