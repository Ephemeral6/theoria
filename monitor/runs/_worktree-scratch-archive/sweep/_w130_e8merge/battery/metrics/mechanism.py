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

from battery.metrics import metric, ok, thin, unsound
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
    # V9-D2. The blind audit printed M1 = -1000.0 from `first_used=0,
    # first_seen=1000` -- an arm that used a mechanism a thousand steps before
    # it existed, ranked as the most capable run in the battery. A negative
    # delay is not a fast arm, it is two counters with different origins.
    if min(delays) < 0:
        return unsound("M1", "mechanism(s) recorded as first used before "
                             "first seen (minimum delay %d)" % min(delays))
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


@metric("M4", "mechanism",
        "Mean environment actions until a changed rule first contradicts the "
        "manual, over changes the manual noticed at all.",
        needs=("repairs",), direction="lower", unit="actions")
def change_detection_delay(run: Run):
    """The other half of "seen it, then used it": *changed it, then noticed*.

    M1 measures how long an arm takes to exploit a mechanism it can see. This
    measures how long it takes to notice that a mechanism it thought it knew
    has moved. A manual is a standing prediction about every transition, so a
    changed rule contradicts it the first time it fires; an arm with no manual
    has nothing to contradict and can only find out by losing.

    Measured on `earliest` -- the first action on *any* evidence level that
    surprises the manual -- because a change is detected once, not once per
    level. The single-level figure is kept in the support field, and the two
    differ in the case that matters: a0-spike's `nocross` variant is never
    noticed on `match` at all and is noticed after 6 actions elsewhere.
    """
    delays = []
    per_episode = {}
    for repair in sorted(run.repairs, key=lambda r: r.episode_id):
        earliest = repair.notes.get("earliest_detection")
        if earliest is None and repair.detected:
            earliest = repair.detection_actions
        if earliest is None:
            continue
        delays.append(earliest)
        per_episode[repair.episode_id] = earliest
    if not delays:
        return thin("M4", "no repair episode records a detection point")
    if min(delays) < 0:
        return unsound("M4", "detection recorded before the change was "
                             "injected (minimum %d actions)" % min(delays))
    undetected = sum(1 for r in run.repairs if not r.detected)
    return ok("M4", sum(delays) / len(delays), episodes=len(delays),
              per_episode=per_episode,
              undetected_on_own_level=undetected)


@metric("M5", "mechanism",
        "Fraction of injected rule changes the manual notices on the evidence "
        "it already holds.",
        needs=("repairs",), direction="higher", unit="share")
def change_detection_rate(run: Run):
    """The ceiling is the interesting part, not the floor.

    A rule can change in a way that the evidence you happen to hold never
    exercises. The manual then keeps replaying its history perfectly while
    being wrong about the world -- the same shape as the K1/K2 gap, arrived at
    from the other direction. A rate below 1.0 is not a defective manual; it
    is evidence that detection is a property of the *evidence set*, and that a
    theory can be silently wrong without any of its own checks firing.
    """
    if not run.repairs:
        return thin("M5", "no repair episodes")
    detected = sum(1 for r in run.repairs if r.detected)
    blind = sorted(r.episode_id for r in run.repairs if not r.detected)
    return ok("M5", detected / len(run.repairs), detected=detected,
              episodes=len(run.repairs), undetected=blind)


@metric("M6", "mechanism",
        "Mean share of the manual's theorems invalidated by one repair. A "
        "diagnostic: a repair that invalidates nothing had nothing "
        "load-bearing downstream.",
        needs=("repairs",), direction="neutral", unit="share")
def repair_collateral_share(run: Run):
    """Counts what dependency tracking is *for*.

    The number in the headline is deliberately not a score. High collateral is
    a theory whose theorems rested on the rule that moved -- which is what a
    theory is supposed to look like. Low collateral can mean a clean modular
    manual or a manual whose theorems were decorative, and this metric cannot
    tell those apart, which is why its direction is `neutral`.

    The support field carries the number that is not ambiguous:
    `silently_wrong_without_tracking` counts repairs after which a theorem
    would still be standing, still compiling with an empty axiom set, and
    false of the world -- if nobody had tracked the dependency. On a0-spike
    that is 1 of 4. A framework that could not count it would ship it.
    """
    shares = []
    broken = []
    for repair in sorted(run.repairs, key=lambda r: r.episode_id):
        if not repair.theorems_before:
            continue
        # V9-D1. Declared `unit="share"`, and the blind audit printed 1000.0
        # from `invalidated=1000, before=1`. A consumer reading this as a
        # fraction is wrong by three orders of magnitude.
        if (repair.invalidated_theorems < 0
                or repair.invalidated_theorems > repair.theorems_before):
            broken.append(repair.episode_id)
            continue
        shares.append(repair.invalidated_theorems / repair.theorems_before)
    if broken:
        return unsound("M6", "episode(s) %s invalidate more theorems than the "
                             "manual held" % ", ".join(sorted(broken)))
    silent = sum(1 for r in run.repairs if r.silently_wrong_without_tracking)
    if not shares:
        return thin("M6", "no repair episode records how many theorems the "
                          "manual had before it")
    return ok("M6", sum(shares) / len(shares), episodes=len(shares),
              silently_wrong_without_tracking=silent,
              of_episodes=len(run.repairs))
