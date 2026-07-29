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


# -- scoping -----------------------------------------------------------------

def test_another_tiers_cells_cannot_pool_into_an_envelope():
    """campaign_cells.jsonl holds more than one campaign now. The tiers differ
    by 3-4x in unit price, so a stray opus cell would turn 'within-cell spread'
    into a between-tier difference wearing its name."""
    cells = [_cell("g50t-5849a774", r, 30, 0, 1.1, 30, 900) for r in (1, 2, 3)]
    intruder = _cell("g50t-5849a774", 4, 30, 0, 4.4, 30, 900)
    intruder["model"] = "claude-opus-5"

    clean = env.build(cells, model="claude-haiku-4-5-20251001")
    polluted = env.build(cells + [intruder], model=None)
    scoped = env.build(cells + [intruder], model="claude-haiku-4-5-20251001")

    assert scoped["pooled_cv"]["cost_usd"] == clean["pooled_cv"]["cost_usd"]
    assert polluted["pooled_cv"]["cost_usd"] > clean["pooled_cv"]["cost_usd"], \
        "the negative control did not actually pollute anything"


def test_load_cells_separates_campaigns_and_defaults_the_field_honestly():
    from harness import run_campaign
    import json as _json

    rows = [{"run_id": "a", "campaign": "phase3-variance-envelope"},
            {"run_id": "b", "campaign": "phase3-unit-price-remeasure"},
            {"run_id": "c"}]                       # written before the field
    path = run_campaign.CELLS_PATH
    original = open(path, encoding="utf-8").read() if os.path.exists(path) else None
    try:
        with open(path, "w", encoding="utf-8", newline="") as fh:
            for row in rows:
                fh.write(_json.dumps(row) + "\n")
        assert len(run_campaign.load_cells()) == 3
        envelope = run_campaign.load_cells("phase3-variance-envelope")
        assert [c["run_id"] for c in envelope] == ["a", "c"], \
            "a cell written before the field belongs to the campaign it came from"
        assert [c["run_id"] for c in
                run_campaign.load_cells("phase3-unit-price-remeasure")] == ["b"]
    finally:
        if original is not None:
            with open(path, "w", encoding="utf-8", newline="") as fh:
                fh.write(original)


# -- unit prices -------------------------------------------------------------

def test_a_barren_cell_is_charged_to_the_unit_price_and_declared():
    """opus/tn36 spent $1.13 for zero successful actions. Ratio-of-sums charges
    that to the other cells' actions, which is right for extrapolating a run
    that will also have dead cells -- and is invisible unless it is said."""
    from harness import unit_prices

    working = {"outcome": "budget_exhausted", "game_id": "g", "model": "m",
               "actions_ok": 30, "actions_failed": 0, "model_calls": 30,
               "http_calls_gameplay": 30, "cost_usd": 3.0, "wall_seconds": 300}
    barren = {"outcome": "api_unusable", "game_id": "h", "model": "m",
              "actions_ok": 0, "actions_failed": 10, "model_calls": 10,
              "http_calls_gameplay": 80, "cost_usd": 1.2, "wall_seconds": 330}

    alone = unit_prices.aggregate([working])
    both = unit_prices.aggregate([working, barren])

    assert alone["usd_per_action"] == pytest.approx(0.10)
    assert both["usd_per_action"] == pytest.approx(4.2 / 30)
    assert both["usd_per_action_working_cells_only"] == pytest.approx(0.10)
    assert both["barren_cells"] == 1
    assert both["barren_cost_usd"] == pytest.approx(1.2)


def test_a_ratio_of_sums_is_not_a_mean_of_ratios():
    """Section 2.1 extrapolates a large run, so a cell that completed three
    actions must not weigh the same as one that completed thirty."""
    from harness import unit_prices

    heavy = {"outcome": "budget_exhausted", "game_id": "g", "model": "m",
             "actions_ok": 30, "actions_failed": 0, "model_calls": 30,
             "http_calls_gameplay": 30, "cost_usd": 3.0, "wall_seconds": 300}
    light = {"outcome": "budget_exhausted", "game_id": "h", "model": "m",
             "actions_ok": 1, "actions_failed": 0, "model_calls": 1,
             "http_calls_gameplay": 1, "cost_usd": 1.0, "wall_seconds": 60}
    row = unit_prices.aggregate([heavy, light])
    # abs=5e-5: the row is rounded to four places, so approx's 1e-6 relative
    # default compares the reported number against an unrounded one and fails
    # on the rounding itself.
    assert row["usd_per_action"] == pytest.approx(4.0 / 31, abs=5e-5)
    mean_of_ratios = (0.10 + 1.0) / 2
    assert row["usd_per_action"] < mean_of_ratios / 2
