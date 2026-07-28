"""Regression: the witness count is graded, and the graded branch was dead code.

`reversibility.analyse` decides "unbounded" by asking whether a rule's firing
transition can get back to the state it fired from.  The version that shipped
asked a cross-product instead —

    any(can_reach(t, s) for t in targets for s in sources)

— which is a different question: firing transition A and then reaching *B's*
source is a second witness of the rule, not a repeat of the first.  With more
than one firing transition in a mutually reachable region that test is satisfied
almost always, so every finite-but-repeatable rule in the catalogue collapsed
onto the `UNBOUNDED` sentinel and the longest-chain branch below it never ran.
`max_witnesses` is the number A0′'s criterion is stated in — `1` is the A0
failure mode — so a stamp that reads `-1` everywhere is the measurement quietly
switched off.

Three catalogue worlds pin the three cases, one per reversibility class:

* `collect_token` in `t1-tokens-lock` — three tokens, three witnesses, and the
  count is *the number of tokens*, which is what makes the graded branch worth
  having: the effect is one-way and the rule is still re-witnessable;
* `cross_fragile` in `t1-fragile-bridge` — two tiles, two witnesses;
* `toggle_switch` in `t1-switch-toggle` — genuinely unbounded, so the sentinel
  is right there and the test would not catch a stamp stuck on `-1` alone.

The catalogue is used here rather than an inline world on purpose: the numbers
are properties of published artefacts, and a reader comparing this file against
`reversibility.json` should be reading the same three numbers.
"""

import pytest

from worldgen.core import reversibility as rev
from worldgen.tests import support

# (world, rule, expected max_witnesses)
CASES = (
    ("t1-tokens-lock", "collect_token", 3),
    ("t1-fragile-bridge", "cross_fragile", 2),
    ("t1-switch-toggle", "toggle_switch", rev.UNBOUNDED),
)


@pytest.mark.parametrize("world_id,rule,expected", CASES)
def test_max_witnesses_is_measured_not_flattened(world_id, rule, expected):
    measured = rev.analyse(support.world(world_id))["rules"]
    assert rule in measured, "%s never fires %s" % (world_id, rule)
    assert measured[rule]["max_witnesses"] == expected, (
        "%s/%s: max_witnesses is %r, expected %r"
        % (world_id, rule, measured[rule]["max_witnesses"], expected))


def test_the_catalogue_still_contains_a_bounded_grade():
    """A guard against the defect returning in a subtler form: if every rule in
    every world reads `-1`, the grading is off again whatever the three cases
    above happen to say."""
    grades = set()
    for world_id in support.WORLD_IDS:
        for stats in rev.analyse(support.world(world_id))["rules"].values():
            grades.add(stats["max_witnesses"])
    assert grades - {rev.UNBOUNDED}, "every rule in the catalogue measures unbounded"
    assert rev.UNBOUNDED in grades, "no rule in the catalogue measures unbounded"


def test_single_witness_rules_are_reported_as_such():
    """`max_witnesses == 1` is the A0 failure mode and has to be nameable; the
    latch in `t1-switch-latch` is the catalogue's control condition for it."""
    stats = rev.analyse(support.world("t1-switch-latch"))["rules"]["press_latch"]
    assert stats["max_witnesses"] == 1
    assert stats["single_witness"] is True
    assert stats["re_witnessable"] is False
