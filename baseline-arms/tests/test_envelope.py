"""The envelope's arithmetic, checked against cases whose answers are known.

The report this produces is the input to a decision that is expensive to get
wrong -- Phase 4's per-cell repeat count `n`, which multiplies the cost of every
cell it is applied to. So the statistics get the same treatment as the transport
did: known inputs, hand-checkable outputs, and a negative control on each.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from harness import summarise_envelope as env  # noqa: E402


# -- the statistics ----------------------------------------------------------

def test_sample_sd_uses_n_minus_one():
    # [2, 4, 4, 4, 5, 5, 7, 9]: population sd 2, sample sd sqrt(32/7).
    xs = [2, 4, 4, 4, 5, 5, 7, 9]
    assert env.sample_sd(xs) == pytest.approx((32 / 7) ** 0.5)
    assert env.sample_sd([1.0]) is None, "one sample has no spread to report"


def test_cv_is_undefined_at_a_zero_mean_rather_than_infinite():
    """Not a formality: `levels_completed` was 0 in all twelve pilot cells, so
    the metric Phase 4 might most want is the one with no CV to give."""
    assert env.cv([0.0, 0.0, 0.0]) is None
    assert env.cv([2.0, 4.0]) == pytest.approx((2 ** 0.5) / 3)


def test_a_metric_with_no_spread_needs_no_repeats():
    assert env.cv([5.0, 5.0, 5.0]) == 0.0


# -- sizing ------------------------------------------------------------------

def test_n_for_precision_moves_the_right_way():
    """More noise or a tighter target both cost repeats; neither may reduce n."""
    loose = env.n_for_precision(0.20, 0.20)
    tight = env.n_for_precision(0.20, 0.10)
    noisier = env.n_for_precision(0.40, 0.20)
    assert tight > loose
    assert noisier > loose
    assert loose >= 2


def test_n_for_precision_reaches_the_fixed_point_it_claims():
    """The t multiplier depends on n, which is what is being solved for, so the
    answer must actually satisfy the inequality rather than merely stop."""
    for cv_value in (0.05, 0.15, 0.3, 0.6):
        for margin in (0.10, 0.20):
            n = env.n_for_precision(cv_value, margin)
            if n >= 60:
                continue
            half_width = env.t975(n - 1) * cv_value / (n ** 0.5)
            assert half_width <= margin + 1e-9, (cv_value, margin, n)


def test_the_two_sample_n_is_larger_than_the_precision_n():
    """Telling two arms apart is a harder question than quoting one arm's mean,
    and the report must not let the cheaper number stand in for the dearer one."""
    cv_value = 0.30
    assert env.n_for_two_sample(cv_value, 0.25) > env.n_for_precision(cv_value, 0.25)


def test_sizing_is_capped_rather_than_unbounded():
    """Past sixty the honest answer is not 'run more repeats'."""
    assert env.n_for_precision(5.0, 0.01) == 60
    assert env.n_for_two_sample(5.0, 0.01) == 60


# -- the report --------------------------------------------------------------

def _cell(game, rep, ok, failed, cost, http, wall, outcome="budget_exhausted"):
    return {"game_id": game, "repeat": rep, "run_id": "%s-%d" % (game, rep),
            "outcome": outcome, "actions_ok": ok, "actions_failed": failed,
            "cost_usd": cost, "http_calls_gameplay": http, "wall_seconds": wall,
            "levels_completed": 0, "model": "claude-haiku-4-5-20251001"}


def test_the_report_pools_cvs_and_not_raw_values():
    """Two games at different scales but identical repeatability must pool to
    that repeatability -- pooling raw numbers would measure the scale gap
    instead, which is a between-game difference and not the target."""
    cells = [_cell("g50t-5849a774", 1, 10, 2, 0.5, 70, 600),
             _cell("g50t-5849a774", 2, 12, 2, 0.6, 84, 700),
             _cell("sk48-d8078629", 1, 100, 2, 5.0, 700, 6000),
             _cell("sk48-d8078629", 2, 120, 2, 6.0, 840, 7000)]
    report = env.build(cells)
    per_game = [report["games"][g]["stats"]["actions_ok"]["cv"]
                for g in ("g50t-5849a774", "sk48-d8078629")]
    assert per_game[0] == pytest.approx(per_game[1])
    assert report["pooled_cv"]["actions_ok"] == pytest.approx(per_game[0])


def test_the_degraded_cells_are_excluded_by_name_and_the_reason_is_reported():
    """Excluded, not deleted, and never silently: a filter nobody can see is how
    a spread gets quietly made smaller."""
    cells = [_cell("ar25-0c556536", 1, 11, 10, 0.73, 128, 1059, "api_unusable"),
             _cell("g50t-5849a774", 1, 10, 2, 0.5, 70, 600),
             _cell("g50t-5849a774", 2, 12, 2, 0.6, 84, 700)]
    report = env.build(cells)
    assert "ar25-0c556536" not in report["games"]
    assert report["excluded"]["ar25-0c556536"]["cells"] == 1
    assert "INC-BA-003" in report["excluded"]["ar25-0c556536"]["reason"]


def test_an_all_zero_metric_reports_that_it_cannot_size_rather_than_a_number():
    cells = [_cell("g50t-5849a774", r, 10, 2, 0.5, 70, 600) for r in (1, 2, 3)]
    report = env.build(cells)
    assert report["sizing"]["levels_completed"].get("n_for_ci_10pct") is None
    assert "cannot be compared between arms" \
        in report["sizing"]["levels_completed"]["note"]


def test_degrees_of_freedom_are_reported_because_three_repeats_is_very_few():
    cells = [_cell("g50t-5849a774", r, 10 + r, 2, 0.5, 70, 600) for r in (1, 2, 3)]
    cells += [_cell("sk48-d8078629", r, 20 + r, 2, 1.0, 140, 900) for r in (1, 2, 3)]
    report = env.build(cells)
    assert report["degrees_of_freedom"] == 4          # (3-1) + (3-1)
