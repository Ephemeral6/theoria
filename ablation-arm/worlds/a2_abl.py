"""The A2 world, and — kept carefully apart from it — the holed manual's world.

`a0_abl.py` selects and hands upstream objects straight through, for the reason
stated there.  This module does the same for the real world, and then adds
**one** wrapper, because the A2 exhibit needs two transition functions that
disagree and upstream deliberately does not present the second one as a world.

`A2World.step_holed` is documented upstream, in its own words, as *"not a
variant of the world and never used to generate a trace: it is the referee's
copy of what the holed manual claims"*.  That sentence is load bearing here.
`DESIGN.md` §E2 is the exhibit the whole A4 ticket is about:

* the **world** has the teleport rule, so the goal is reachable and the level is
  **solvable**;
* the **holed manual** is missing that rule, and under it the goal is
  unreachable, so the manual derives **unsolvable** — a theorem that is true of
  the manual and false of the world;
* the full arm owes a certificate for that verdict and probes the clauses the
  theorem depends on, which is where the missing rule surfaces. This arm owes
  nothing, so `plan_abl` settles UNSAT on bare search and the loop never turns.
  P-6 predicts nobody finds it.

So the two must be nameable separately and must never be confused, because
confusing them is the exact failure the exhibit exists to display — and an
exhibit that displays its own bug instead of the arm's proves nothing.  Hence:

    world()          the world. Unwrapped upstream object, as in `a0_abl`.
    manual_world()   `HoledManualWorld`, whose `step` is `step_holed`.
                     **Not a world.** It is what the holed manual claims the
                     world is, given a world-shaped interface so that the two
                     can be run against each other as transition functions
                     rather than compared as two prose paragraphs.

**Read-only.** `cold-start-a2/` belongs to another track; it is imported and
never written, checked by `pin.hash_tree` in `tests/test_readonly.py`.
"""

from __future__ import annotations

from typing import Any, Dict, List

import _bootstrap                                                  # noqa: F401

from a2world.a2_world import BASE, A2World, State, WorldSpec       # noqa: E402


class HoledManualWorld:
    """What the holed manual claims, wearing the world's interface.

    Everything is delegated to the real world except `step`, which is the real
    world's `step_holed`.  Delegation rather than reimplementation, for the same
    attribution reason as `a0_abl`: if this object differed from the world in
    any way other than the deleted teleport rule, the exhibit would be measuring
    this file.

    It carries `is_a_world = False` and refuses to be pickled into a ledger as a
    world, because the one thing that must never happen is a run that believes
    this was the world it was standing in.
    """

    is_a_world = False
    deleted_rule = "teleport: the Portal moves the Cart to the Portal's dest"

    def __init__(self, spec: WorldSpec = BASE):
        self._world = A2World(spec)
        self.spec = spec

    def initial(self) -> State:
        return self._world.initial()

    def is_win(self, state: State) -> bool:
        return self._world.is_win(state)

    def render(self, state: State) -> List[List[int]]:
        return self._world.render(state)

    def step(self, state: State, action: str) -> State:
        """The holed transition: the deleted rule, and nothing else changed."""
        return self._world.step_holed(state, action)

    def __repr__(self) -> str:
        return ("<HoledManualWorld %s -- what the manual claims, missing %r; "
                "NOT the world>" % (self.spec.name, self.deleted_rule))


def world(spec: WorldSpec = BASE) -> A2World:
    """The world. Unwrapped upstream object."""
    return A2World(spec)


def manual_world(spec: WorldSpec = BASE) -> HoledManualWorld:
    """What the holed manual claims. **Not the world.**"""
    return HoledManualWorld(spec)


def disagreement(spec: WorldSpec = BASE) -> Dict[str, Any]:
    """Every state and action on which the two transition functions differ.

    Computed rather than asserted: the exhibit's whole point is that the
    disagreement is real, small, and invisible to an arm that owes no
    certificate. A count of zero here would mean the exhibit is not exhibiting
    anything and should fail loudly rather than pass quietly.
    """
    from a2world.a2_world import ACTIONS

    real, holed = A2World(spec), HoledManualWorld(spec)
    seen, frontier, differ = set(), [real.initial()], []
    while frontier:
        state = frontier.pop()
        if state.key() in seen:
            continue
        seen.add(state.key())
        for action in ACTIONS:
            after_real = real.step(state, action)
            after_holed = holed.step(state, action)
            if after_real != after_holed:
                differ.append({"state": state.key(), "action": action,
                               "world_goes_to": after_real.key(),
                               "manual_says": after_holed.key()})
            frontier.append(after_real)
    return {"n_states_explored": len(seen), "n_disagreements": len(differ),
            "disagreements": differ,
            "deleted_rule": HoledManualWorld.deleted_rule}


def provenance() -> Dict[str, object]:
    return {
        "family": "a2",
        "upstream_module": "cold-start-a2/a2world/a2_world.py",
        "adapter": ("none for the world; HoledManualWorld delegates every "
                    "method except `step`, which is upstream's `step_holed`"),
        "pile_contact": "none -- A2 is self-built and is in neither pile",
    }
