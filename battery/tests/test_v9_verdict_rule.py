"""The tier rule, as a rule — including the branch that never fired.

`PREREG_V9.md` R1 refuses to promote a metric because nobody thought of an
attack.  In the first cut it was an inline expression inside `adjudicate()`,
every input derived from the live tree, and it evaluated `False` for all 38
metrics — so "is R1 alive?" was not a question the suite could ask, and it
turned out the answer was no: a V9 defence closed E1's B14 exploit, which
flipped E1's *baseline* to `main`, which meant the promotion guard was never
reached by the one metric it existed for.

The fix is not a better assertion, it is a smaller function.  `decide_tier` is
pure, so every combination can be enumerated here rather than hoped about.
"""

from __future__ import annotations

import itertools

import pytest

from battery.audit.v9.verdict import (B14_BASELINE_MAIN, DEFENCE_OF,
                                      decide_tier, r2_counts)


def test_an_accidental_landed_attack_always_demotes():
    for prior, r2 in itertools.product(("main", "reference"), (True, False)):
        out = decide_tier(prior, gameable=True, accidental=True,
                          answered=True, attacked=True, r2_satisfied=r2)
        assert out["tier"] == "reference", (prior, r2)


def test_a_deliberate_only_attack_does_not_demote_a_main_metric():
    out = decide_tier("main", gameable=True, accidental=False, answered=True,
                      attacked=True, r2_satisfied=False)
    assert out["tier"] == "main"


def test_r1_refuses_to_promote_on_silence():
    """The branch that was dead. Unbroken *and* undefended is not evidence."""
    out = decide_tier("reference", gameable=False, accidental=False,
                      answered=True, attacked=True, r2_satisfied=False)
    assert out["tier"] == "reference"
    assert out["R1_promotion_refused"] is True


def test_r1_allows_a_promotion_that_a_defence_paid_for():
    out = decide_tier("reference", gameable=False, accidental=False,
                      answered=True, attacked=True, r2_satisfied=True)
    assert out["tier"] == "main"
    assert out["R1_promotion_refused"] is False


def test_a_metric_that_never_answered_is_undetermined_not_main():
    """R4, executable. Unimplemented must not read as survived."""
    out = decide_tier("main", gameable=False, accidental=False,
                      answered=False, attacked=True, r2_satisfied=False)
    assert out["tier"] == "undetermined"


def test_an_unattacked_metric_is_not_called_undetermined():
    out = decide_tier("main", gameable=False, accidental=False,
                      answered=False, attacked=False, r2_satisfied=False)
    assert out["tier"] == "main"


@pytest.mark.parametrize(
    "prior,gameable,accidental,answered,attacked,r2",
    list(itertools.product(("main", "reference"), (True, False), (True, False),
                           (True, False), (True, False), (True, False))))
def test_the_rule_is_total_and_never_promotes_a_broken_metric(
        prior, gameable, accidental, answered, attacked, r2):
    out = decide_tier(prior, gameable, accidental, answered, attacked, r2)
    assert out["tier"] in ("main", "reference", "undetermined")
    if gameable and accidental:
        assert out["tier"] != "main"


def test_the_b14_baseline_is_pinned_not_recomputed():
    """It has to be a record: recomputing it let a V9 defence rewrite it."""
    assert B14_BASELINE_MAIN == ("E2", "E3", "K7", "K11", "K12", "M3", "M6",
                                 "P3", "P4")


def test_r2_counts_only_the_mutants_that_must_be_refused():
    """Accept-cases guard against overreach; they are not attack surface."""
    counts = r2_counts()
    for defence_id, row in sorted(counts.items()):
        assert row["mutants"] > row["tests"], (defence_id, row)


def test_r2_test_attribution_does_not_depend_on_test_names():
    """The first version counted `^def test_D\\d_`, gameable by rename."""
    counts = r2_counts()
    assert set(counts) == set(DEFENCE_OF.values())
    assert all(row["tests"] > 0 for row in counts.values())
