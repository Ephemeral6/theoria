"""Metric semantics, on runs small enough to check by hand."""

import pytest

from battery.audit.stats import cliffs_delta, sign_test, spearman
from battery.metrics import REGISTRY, evaluate, polyfit_r2
from battery.metrics.exploration import START
from battery.model import Call, Clause, Concept, Run, Step, Theory, Truth


def make_run(state_keys, actions=None, *, calls=(), intent="solve", **kw):
    actions = actions or ["A"] * len(state_keys)
    steps = [Step(idx=i, action=a, state_key=k, failed=k is None)
             for i, (k, a) in enumerate(zip(state_keys, actions))]
    return Run(run_id="t", arm="test", source="test", intent=intent,
               steps=steps, calls=list(calls), **kw)


# ---------------------------------------------------------------- exploration

def test_revisit_rate_counts_repeats_not_distinct_states():
    run = make_run(["a", "b", "a", "c", "a"])
    assert evaluate(run)["X1"].value == pytest.approx(1 - 3 / 5)


def test_a_run_that_never_repeats_scores_zero_revisits():
    assert evaluate(make_run(["a", "b", "c"]))["X1"].value == 0.0


def test_novelty_keys_on_state_and_action_together():
    """Same state, different action is a new transition; same pair is not."""
    run = make_run(["a", "b", "b"], ["L", "R", "R"])
    # transitions: (START,L) (a,R) (b,R) -- all three distinct
    assert evaluate(run)["X2"].value == 1.0
    repeat = make_run(["a", "a", "a"], ["L", "L", "L"])
    # (START,L) (a,L) (a,L) -- the third repeats the second
    assert evaluate(repeat)["X2"].value == pytest.approx(2 / 3)


def test_failed_steps_name_no_transition():
    run = make_run(["a", None, "b"], ["L", "M", "R"])
    assert evaluate(run)["X2"].support["transitions"] == 2


def test_frontload_is_positive_when_novelty_dies_off():
    front = make_run([str(i) for i in range(8)] + ["0"] * 8)
    back = make_run(["0"] * 8 + [str(i) for i in range(8)])
    assert evaluate(front)["X3"].value > 0
    assert evaluate(back)["X3"].value < 0


def test_no_progress_streak_is_the_longest_run_of_repeats():
    run = make_run(["a", "b", "b", "b", "c"])
    value = evaluate(run)["X4"]
    assert value.support["longest_streak"] == 2      # the 2nd and 3rd 'b'
    assert value.value == pytest.approx(2 / 5)


def test_start_marker_is_used_for_the_first_transition():
    assert START == "<start>"
    assert evaluate(make_run(["a", "b"]))["X2"].support["transitions"] == 2


# ------------------------------------------------------------------- planning

def test_actions_per_call_ignores_failed_steps_in_the_numerator():
    calls = [Call(idx=i) for i in range(2)]
    run = make_run(["a", None, "b", "c"], calls=calls)
    assert evaluate(run)["P1"].value == pytest.approx(3 / 2)


def test_backtrack_detects_a_two_step_undo():
    run = make_run(["a", "b", "a", "c", "d"])
    value = evaluate(run)["P3"]
    assert value.support["undos"] == 1
    assert value.support["windows"] == 3


def test_redundancy_refuses_a_coverage_walk():
    """The A0 bug this guard exists for: 275 steps against a 12-step plan."""
    walk = make_run(["a"] * 20, intent="explore",
                    truth=Truth(optimal_steps=4))
    assert evaluate(walk)["P4"].status == "not-applicable"
    solve = make_run(["a"] * 20, intent="solve", truth=Truth(optimal_steps=4))
    assert evaluate(solve)["P4"].value == pytest.approx(5.0)


# -------------------------------------------------------------------- economy

def _cost_calls(costs, context=None):
    return [Call(idx=i, cost_usd=c,
                 cache_read_tokens=(context[i] if context else 0))
            for i, c in enumerate(costs)]


def test_frontload_index_reads_the_head_of_the_bill():
    calls = _cost_calls([10.0] + [0.0] * 7)
    run = make_run(["a"] * 8, calls=calls)
    assert evaluate(run)["E2"].value == pytest.approx(1.0)
    flat = make_run(["a"] * 8, calls=_cost_calls([1.0] * 8))
    assert evaluate(flat)["E2"].value == pytest.approx(0.25)


def test_short_runs_are_refused_not_scored_as_perfectly_frontloaded():
    run = make_run(["a"] * 4, calls=_cost_calls([1.0, 0.0, 0.0, 0.0]))
    value = evaluate(run)["E2"]
    assert value.status == "insufficient-data"
    assert "trivially front-loaded" in value.reason


def test_convergence_point_finds_the_turn_the_bill_settles():
    calls = _cost_calls([9.0] + [0.125] * 8)
    run = make_run(["a"] * 9, calls=calls)
    assert evaluate(run)["E3"].support["turn"] == 1


def test_quadratic_gain_is_positive_for_accelerating_context():
    quad = make_run(["a"] * 10,
                    calls=_cost_calls([1.0] * 10, [i * i * 100 for i in range(10)]))
    lin = make_run(["a"] * 10,
                   calls=_cost_calls([1.0] * 10, [i * 100 for i in range(10)]))
    assert evaluate(quad)["E4"].value > 0.01
    assert evaluate(lin)["E4"].value == pytest.approx(0.0, abs=1e-6)


# ------------------------------------------------------------------ mechanism

def test_first_use_delay_averages_over_used_mechanisms_only():
    truth = Truth(mechanisms={
        "portal": {"first_seen": 0, "first_used": 10},
        "door": {"first_seen": 5, "first_used": 25},
        "never": {"first_seen": 0, "first_used": None},
    })
    run = make_run(["a", "b"], truth=truth)
    assert evaluate(run)["M1"].value == pytest.approx((10 + 20) / 2)
    assert evaluate(run)["M2"].value == pytest.approx(2 / 3)


# ------------------------------------------------------------------ epistemic

def _theory(**kw):
    base = dict(concepts=[], clauses=[], playbook_entries=0,
                deadlock_theorems=0, revisions=1, probes_designed=0,
                probes_executable=0)
    base.update(kw)
    return Theory(**base)


def test_epistemic_metrics_are_not_applicable_without_books():
    run = make_run(["a", "b"])
    for mid in ("K1", "K2", "K3", "K4"):
        assert evaluate(run)[mid].status == "not-applicable"
        assert "no explicit theory" in evaluate(run)[mid].reason


def test_replay_and_held_out_are_separate_questions():
    theory = _theory(replay_pairs=236, replay_agree=233,
                     held_out_pairs=3, held_out_agree=0)
    values = evaluate(make_run(["a"], theory=theory))
    assert values["K1"].value == pytest.approx(233 / 236)
    assert values["K2"].value == 0.0


def test_evidence_coverage_reports_unannotated_clauses_separately():
    theory = _theory(clauses=[
        Clause("r1", "rule", coverage_num=5, coverage_den=5,
               evidence_transitions=3),
        Clause("i1", "invariant", proven=True),      # no coverage annotation
    ])
    value = evaluate(make_run(["a"], theory=theory))["K4"]
    assert value.value == pytest.approx(1.0)
    assert value.support["annotated"] == 1
    assert value.support["unannotated"] == 1


def test_negative_compression_concepts_are_counted_not_hidden():
    theory = _theory(concepts=[
        Concept("Cart", compression_bits=2125),
        Concept("Button", compression_bits=-5),
        Concept("Door", compression_bits=-1),
    ])
    values = evaluate(make_run(["a"], theory=theory))
    assert values["K7"].value == 2
    assert values["K6"].support["worst"] == -5


# ----------------------------------------------------------------- statistics

def test_cliffs_delta_is_one_when_groups_do_not_overlap():
    assert cliffs_delta([5, 6, 7], [1, 2, 3]) == 1.0
    assert cliffs_delta([1, 2, 3], [5, 6, 7]) == -1.0
    assert cliffs_delta([1, 2, 3], [1, 2, 3]) == 0.0


def test_sign_test_reports_the_floor_on_attainable_p():
    result = sign_test([(2, 1)] * 4)
    assert result["wins"] == 4 and result["losses"] == 0
    assert result["min_attainable_p"] == pytest.approx(0.125)
    assert result["p_value"] >= 0.05      # four pairs can never clear the bar


def test_six_pairs_can_finally_clear_the_bar():
    result = sign_test([(2, 1)] * 6)
    assert result["min_attainable_p"] < 0.05
    assert result["p_value"] < 0.05


def test_spearman_is_rank_based_not_value_based():
    assert spearman([1, 2, 3, 4], [10, 200, 3000, 40000]) == pytest.approx(1.0)
    assert spearman([1, 2, 3, 4], [4, 3, 2, 1]) == pytest.approx(-1.0)


def test_constant_series_correlate_with_nothing():
    assert spearman([1, 1, 1, 1], [1, 2, 3, 4]) is None
    assert polyfit_r2([0, 1, 2, 3, 4, 5], [7, 7, 7, 7, 7, 7], 1) == 0.0


def test_every_registered_metric_has_a_gaming_entry():
    """Process 4 is not optional: an unaudited metric cannot reach the main
    table, and this test makes forgetting one a failure rather than a demotion."""
    from battery.audit.gaming import GAMING_REGISTER
    assert set(REGISTRY) == set(GAMING_REGISTER)
