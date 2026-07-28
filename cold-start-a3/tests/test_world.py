"""The world, the sweep, and the two properties the whole experiment rests on.

Two of these are not ordinary unit tests.  `test_every_guard_context_level_2
_needs_was_witnessed_in_level_1` and `test_level_2_wins_through_the_portal_leg
_level_1_never_uses` are the *experimental design*, asserted rather than drawn:
if either fails, A3's result would be an artefact of level 1 having been lucky
or level 2 having been a re-run, and the report would be measuring nothing.
"""

import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)

import _bootstrap  # noqa: F401,E402

from a3world.a3_world import (  # noqa: E402
    ACTIONS, DELTA, L1, L2, L2_ONEWAY, L2_REWIRED, A3World,
)
from a3world.explorer import coverage_report, first_frame, sweep  # noqa: E402

ARTIFACTS = os.path.join(HERE, "artifacts")


def _rule_generating(census):
    return {k for k in census if k.split("_")[0] in ("push", "teleport", "switch")}


# ----------------------------------------------------- the experimental design

def test_every_guard_context_level_2_needs_was_witnessed_in_level_1():
    """The containment that makes zero-relearn a fair test rather than a gift.

    If level 2 presented a guard context level 1 never showed, the carried
    domain would be missing a clause and the transfer would fail for a reason
    that has nothing to do with C3.
    """
    l1 = _rule_generating(A3World(L1).guard_contexts())
    l2 = _rule_generating(A3World(L2).guard_contexts())
    assert l2 - l1 == set(), "level 2 needs guards level 1 never witnessed: %s" % (l2 - l1)
    assert l1 - l2, "level 1 must witness strictly more, or the levels are the same shape"


def test_level_2_wins_through_the_portal_leg_level_1_never_uses():
    """Transfer must be a claim about induction, not about repetition.

    Level 1 wins through A -> exit_a and never needs B -> exit_b.  Level 2 wins
    through B -> exit_b and never needs A -> exit_a.  A manual that had only
    recorded the leg its own level required would therefore fail on the other,
    which is what makes the carried domain's success informative.
    """
    def legs_used(spec):
        world = A3World(spec)
        state = world.initial()
        used = set()
        for action in world.solve():
            dr, dc = DELTA[action]
            target = (state.cart[0] + dr, state.cart[1] + dc)
            if target == spec.portal_a:
                used.add("a")
            if target == spec.portal_b:
                used.add("b")
            state = world.step(state, action)
        return used

    assert legs_used(L1) == {"a"}
    assert legs_used(L2) == {"b"}


def test_the_two_levels_share_no_placed_cell():
    """"Same mechanisms, different layout" — checked, not drawn."""
    fields = ("cart_start", "switch_cell", "door_cell",
              "portal_a", "portal_b", "exit_a", "exit_b", "goal_cell")
    for field in fields:
        assert getattr(L1, field) != getattr(L2, field), field
    assert L1.layout != L2.layout


# ------------------------------------------------------------------ the sweep

def test_the_sweep_covers_every_reachable_pair_on_both_levels():
    for spec in (L1, L2):
        world = A3World(spec)
        report = coverage_report(world, *sweep(world))
        assert report["coverage"] == 1.0, (spec.name, report["coverage"])
        assert report["pairs_covered"] == report["pairs_reachable"]


def test_the_sweep_is_deterministic():
    for spec in (L1, L2):
        world = A3World(spec)
        first = [(s.key(), a) for s, a in zip(*sweep(world))]
        second = [(s.key(), a) for s, a in zip(*sweep(world))]
        assert first == second


def test_the_shipped_traces_are_byte_stable():
    """Regenerating must reproduce the committed artefacts exactly."""
    from a3world import ground_truth

    before = {}
    for name in sorted(os.listdir(ARTIFACTS)):
        if name.endswith("_sweep.jsonl") or name.endswith("_solved.jsonl"):
            with open(os.path.join(ARTIFACTS, name), "rb") as handle:
                before[name] = hashlib.sha256(handle.read()).hexdigest()
    assert before, "no traces on disk to compare against"

    ground_truth.build()

    for name, digest in before.items():
        with open(os.path.join(ARTIFACTS, name), "rb") as handle:
            assert hashlib.sha256(handle.read()).hexdigest() == digest, name


# ------------------------------------------------------------- the transition

def test_the_transition_function_is_total_and_deterministic():
    for spec in (L1, L2, L2_ONEWAY, L2_REWIRED):
        world = A3World(spec)
        for state in world.reachable():
            for action in ACTIONS:
                once = world.step(state, action)
                assert once == world.step(state, action)


def test_the_world_is_reversible():
    """F-12's premise, as a property of the state graph rather than a claim.

    The property is **strong connectivity**, not edge-wise invertibility, and
    the difference is not pedantry: a portal is reversible as a *mechanism* —
    you can always get back — but not as an *edge*.  Pushing into portal A from
    (1,2) lands the Cart on `exit_a`, and the return trip goes through portal B
    to `exit_b`, which is a different cell.  The first version of this test
    asserted a one-action inverse and failed on exactly that transition.

    Strong connectivity is what F-12 actually needs (any configuration can be
    revisited, so any rule can be re-witnessed) and what the edge-cover sweep
    needs (D-A3-008: the walk-back step must always be possible).
    """
    from collections import deque

    for spec in (L1, L2):
        world = A3World(spec)
        reachable = {s.key(): s for s in world.reachable()}
        start = world.initial()

        for state in reachable.values():
            seen = {state.key()}
            queue = deque([state])
            while queue and start.key() not in seen:
                current = queue.popleft()
                for action in ACTIONS:
                    nxt = world.step(current, action)
                    if nxt.key() not in seen:
                        seen.add(nxt.key())
                        queue.append(nxt)
            assert start.key() in seen, (spec.name, state.key())


def test_the_cart_never_stands_on_a_portal_cell():
    """D-A3-003's repair, enforced.  If this fails the segmenter breaks."""
    for spec in (L1, L2, L2_ONEWAY, L2_REWIRED):
        world = A3World(spec)
        for state in world.reachable():
            assert state.cart != spec.portal_a
            assert state.cart != spec.portal_b
            assert state.cart != spec.switch_cell


def test_the_portal_cells_are_constant_across_the_sweep():
    """The consequence of the above, at the pixel level: portals are terrain."""
    for spec, name in ((L1, "l1"), (L2, "l2")):
        path = os.path.join(ARTIFACTS, "%s_sweep.jsonl" % name)
        values = {spec.portal_a: set(), spec.portal_b: set()}
        with open(path, encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                frame = json.loads(line)["frame"]
                for cell in values:
                    values[cell].add(frame[cell[0]][cell[1]])
        assert values[spec.portal_a] == {3}, values[spec.portal_a]
        assert values[spec.portal_b] == {4}, values[spec.portal_b]


# -------------------------------------------------------- the negative controls

def test_the_negative_controls_are_pixel_identical_to_level_2():
    """The edit is in the transition function, not in the board.

    A negative control whose first frame differed would be a different level,
    and catching it would say nothing about carrying a domain.
    """
    base = first_frame(L2)
    assert first_frame(L2_ONEWAY) == base
    assert first_frame(L2_REWIRED) == base


def test_the_negative_controls_really_differ_in_behaviour():
    assert A3World(L2).solve() is not None
    assert A3World(L2_ONEWAY).solve() is None, "control 1 must be unsolvable"
    rewired = A3World(L2_REWIRED).solve()
    assert rewired is not None, "control 2 must stay solvable"
    assert len(rewired) != len(A3World(L2).solve())


def test_the_solutions_are_the_lengths_the_report_quotes():
    assert len(A3World(L1).solve()) == 15
    assert len(A3World(L2).solve()) == 10
    assert len(A3World(L2_REWIRED).solve()) == 15
