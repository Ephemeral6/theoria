"""The A0 worlds this arm runs against — selected upstream, never reimplemented.

`plan_abl.run_plan` asks a world for four things: `initial()`, `step(state,
ACTION)`, `render(state)` and `is_win(state)`.  `cold_start_a0.world.a0_world.
A0World` already exposes exactly those four, so this module **selects** worlds
and does not wrap them.

That is a design constraint, not laziness.  The whole claim of this arm is that
the only difference between it and the full arm is the proof obligation
(`DESIGN.md` §5: 一字不改的部分, the other half of attribution).  Every line of
adapter code between the arm and the world is a place a second difference could
enter unnoticed — a subtly different `step`, a render that transposes, a goal
test that rounds.  If the two arms do not drive the *same object*, then P-1 and
P-2 stop being tests of the cut and become tests of this file.

So: no subclass, no wrapper, no copied constant.  The upstream module is
imported and its objects are handed straight through.

**Read-only.** `cold-start-a0/` belongs to another track and is imported here,
never written.  That is checked rather than promised — `pin.hash_tree` takes the
upstream trees' hashes around a full run and `tests/test_readonly.py` asserts
nothing moved.
"""

from __future__ import annotations

from typing import Callable, Dict, Tuple

import _bootstrap                                                  # noqa: F401

from world.a0_world import BASE, NO_BUTTON, A0World, WorldSpec     # noqa: E402

#: The two A0 instances the arm needs, and what each is for.
#:
#:   base       the solvable world. P-1/P-2 read replay and held-out accuracy
#:              off it, and P-5 reads the verdict.
#:   no_button  the Button is not there, so the Door can never open and the
#:              goal is unreachable. Constructively unsolvable, which is what
#:              makes it exhibit E1 — `DESIGN.md` §E1, a true impossibility of
#:              verdict class (i), where the full arm owes a certificate and
#:              this arm settles on bare search.
SPECS: Dict[str, WorldSpec] = {"base": BASE, "no_button": NO_BUTTON}


def world(name: str = "base") -> A0World:
    """The upstream world itself, for `run_plan(world=…)`."""
    if name not in SPECS:
        raise KeyError("no A0 world %r; this arm runs %s"
                       % (name, sorted(SPECS)))
    return A0World(SPECS[name])


def base() -> A0World:
    return world("base")


def no_button() -> A0World:
    return world("no_button")


#: Name -> factory, for a driver that iterates rather than hard-codes.
WORLDS: Dict[str, Callable[[], A0World]] = {"base": base, "no_button": no_button}


def provenance() -> Dict[str, object]:
    """What a ledger entry should say about which world it ran."""
    return {
        "family": "a0",
        "upstream_module": "cold-start-a0/world/a0_world.py",
        "adapter": "none -- the upstream object is passed through unwrapped",
        "worlds": {name: {"spec_name": spec.name,
                          "button_cell": spec.button_cell,
                          "goal_cell": spec.goal_cell}
                   for name, spec in sorted(SPECS.items())},
        "pile_contact": "none -- A0 is self-built and is in neither pile",
    }
