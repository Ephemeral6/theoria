"""The three V9 defences, and the rule that the tests must not exhaust them.

`PREREG_V9.md` R2 requires a defence's attack surface to be **wider** than its
test surface, counted mechanically: `mutant_*` builders in
`battery/audit/v9/mutants.py` against pytest items named `test_D<n>_*` here.
`test_the_attack_surface_is_wider_than_the_test_surface` enforces it, so this
file cannot quietly grow until the two are equal — which is exactly what
happened to C11, where eighteen mutants met eighteen tests and the suite was
testing what it had already tested.

The mutant sweep as a whole is checked by **one** item, deliberately. If every
mutant had its own assertion the two counts would be equal by construction and
R2 would be theatre.
"""

from __future__ import annotations

import re

from battery.audit.v9 import mutants
from battery.metrics import evaluate
from battery.model import Beat, Call, Clause, Repair, Run, Step, Theory, Truth

THIS = __file__


def _test_counts_by_defence():
    """Collected item names in this file, bucketed by the defence they name."""
    with open(THIS, encoding="utf-8") as fh:
        names = re.findall(r"^def (test_\w+)", fh.read(), re.MULTILINE)
    out = {}
    for name in names:
        match = re.match(r"test_(D\d)_", name)
        if match:
            out[match.group(1)] = out.get(match.group(1), 0) + 1
    return out


# --- D1 -------------------------------------------------------------------

def test_D1_a_share_above_one_is_refused_not_reported():
    run = Run(run_id="t", arm="a", source="v9",
              theory=Theory(replay_pairs=1, replay_agree=7))
    value = evaluate(run)["K1"]
    assert value.status == "insufficient-data"
    assert value.reason.startswith("incoherent record:")


def test_D1_a_perfect_share_still_computes():
    run = Run(run_id="t", arm="a", source="v9",
              theory=Theory(replay_pairs=9, replay_agree=9))
    assert evaluate(run)["K1"].value == 1.0


def test_D1_k4_names_the_offending_clause():
    run = Run(run_id="t", arm="a", source="v9",
              theory=Theory(clauses=[Clause(name="loud", kind="rule",
                                            coverage_num=9, coverage_den=3)]))
    value = evaluate(run)["K4"]
    assert value.status == "insufficient-data"
    assert "loud" in value.reason


def test_D1_k12_cannot_shrink_its_own_denominator():
    run = Run(run_id="t", arm="a", source="v9",
              repairs=[Repair(episode_id="e", changed_clause="c",
                              beats_required=1,
                              beats=[Beat(tag="t%d" % i, name="b", closed=True)
                                     for i in range(6)])])
    assert evaluate(run)["K12"].status == "insufficient-data"


def test_D1_m6_refuses_more_collateral_than_theorems():
    run = Run(run_id="t", arm="a", source="v9",
              repairs=[Repair(episode_id="e", changed_clause="c",
                              invalidated_theorems=1000, theorems_before=1)])
    assert evaluate(run)["M6"].status == "insufficient-data"


# --- D2 -------------------------------------------------------------------

def test_D2_a_delay_may_not_run_backwards():
    run = Run(run_id="t", arm="a", source="v9",
              truth=Truth(mechanisms={"g": {"first_seen": 1000,
                                            "first_used": 0}}))
    value = evaluate(run)["M1"]
    assert value.status == "insufficient-data"
    assert value.reason.startswith("incoherent record:")


def test_D2_instant_uptake_is_not_incoherent():
    run = Run(run_id="t", arm="a", source="v9",
              truth=Truth(mechanisms={"g": {"first_seen": 4,
                                            "first_used": 4}}))
    assert evaluate(run)["M1"].value == 0.0


def test_D2_detection_before_injection_is_refused():
    run = Run(run_id="t", arm="a", source="v9",
              repairs=[Repair(episode_id="e", changed_clause="c",
                              detected=True, detection_actions=-500)])
    assert evaluate(run)["M4"].status == "insufficient-data"


# --- D3 -------------------------------------------------------------------

def test_D3_an_unpriced_call_is_not_a_free_one():
    run = Run(run_id="t", arm="a", source="v9",
              steps=[Step(idx=0, action="a", state_key="s")],
              calls=[Call(idx=0, cost_usd=1.0)]
                    + [Call(idx=i, cost_usd=None) for i in range(1, 40)])
    for metric_id in ("E1", "E2", "E3", "E5"):
        value = evaluate(run)[metric_id]
        assert value.status == "insufficient-data", metric_id
        assert value.reason.startswith("incoherent record:"), metric_id


def test_D3_a_genuinely_free_call_is_priced_at_zero_and_still_counts():
    run = Run(run_id="t", arm="a", source="v9",
              steps=[Step(idx=0, action="a", state_key="s")],
              calls=[Call(idx=i, cost_usd=(1.0 if i < 4 else 0.0))
                     for i in range(40)])
    assert evaluate(run)["E1"].value == 4.0
    assert evaluate(run)["E2"].ok


def test_D3_a_complete_flat_bill_still_scores_a_quarter():
    run = Run(run_id="t", arm="a", source="v9",
              steps=[Step(idx=0, action="a", state_key="s")],
              calls=[Call(idx=i, cost_usd=1.0) for i in range(40)])
    assert evaluate(run)["E2"].value == 0.25


def test_D3_leaves_the_token_axis_alone():
    """E4 and E7 read tokens, not money, and must be untouched by D3."""
    run = Run(run_id="t", arm="a", source="v9",
              calls=[Call(idx=i, input_tokens=100 * i, cost_usd=None,
                          prompt_chars=400 * i) for i in range(1, 20)])
    assert evaluate(run)["E4"].ok
    assert evaluate(run)["E7"].ok


# --- the discipline itself ------------------------------------------------

def test_the_mutant_sweep_agrees_with_its_own_expectations():
    """One item for the whole sweep, on purpose. See this module's docstring."""
    rows = mutants.sweep()
    disagreements = [r for r in rows if not r["agrees"]]
    assert not disagreements, disagreements


def test_the_mutant_suite_contains_records_the_defence_must_accept():
    """A defence that refuses everything is a metric switched off."""
    rows = mutants.sweep()
    accepted = [r for r in rows if not r["expected_refusal"]]
    assert len(accepted) >= len(rows) // 4
    assert all(r["status"] == "ok" for r in accepted)


def test_the_attack_surface_is_wider_than_the_test_surface():
    """PREREG_V9 R2, enforced rather than asserted in prose."""
    mutant_counts = mutants.counts()
    test_counts = _test_counts_by_defence()
    for defence, n_tests in sorted(test_counts.items()):
        assert mutant_counts.get(defence, 0) > n_tests, (
            "%s: %d mutants against %d tests -- the mutation suite has stopped "
            "reaching past what is already pinned"
            % (defence, mutant_counts.get(defence, 0), n_tests))
