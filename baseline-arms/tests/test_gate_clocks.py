"""G6a/G6b/G6c: three clocks, three different things.

The case that motivated the sitting clock is `test_a_long_pause_between_games`:
BUDGET_REPORT.md 11.5 requires waiting for a concurrent campaign to drain before
re-running, and under the old first-cell-to-now definition that wait consumed
the same budget as running would have. Obeying 11.5 tripped the clause that 11.5
told you to obey it under.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from harness import run_campaign as rc                              # noqa: E402

H = 3600.0
BASE = 1_800_000_000.0           # fixed clock


def iso(epoch):
    import time
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(epoch))


def cell(start_h, dur_h=0.4, outcome="budget_exhausted", **over):
    c = {
        "run_id": "cell-%s" % start_h,
        "game_id": "g50t-5849a774",
        "model": "claude-haiku-4-5-20251001",
        "budget": 30,
        "outcome": outcome,
        "started": iso(BASE + start_h * H),
        "ended": iso(BASE + (start_h + dur_h) * H),
        "actions_ok": 20, "actions_failed": 5,
        "cost_usd": 0.6, "http_calls_gameplay": 150, "wall_seconds": dur_h * H,
    }
    c.update(over)
    return c


# ----------------------------------------------------------------- sittings
def test_one_burst_is_one_sitting():
    cells = [cell(0), cell(0), cell(0)]
    assert len(rc.sittings(cells)) == 1


def test_a_six_hour_pause_starts_a_new_sitting():
    cells = [cell(0), cell(6)]
    assert len(rc.sittings(cells)) == 2


def test_games_run_back_to_back_stay_in_one_sitting():
    """The loop is run-a-game, audit, gate, next game. The audit takes minutes,
    not hours, so three games in a row must not read as three sittings."""
    cells = [cell(0), cell(0.6), cell(1.2)]
    assert len(rc.sittings(cells)) == 1


def test_a_gap_exactly_at_the_boundary_stays_in_the_sitting():
    cells = [cell(0, dur_h=0.0), cell(rc.SESSION_GAP_SECONDS / H)]
    assert len(rc.sittings(cells)) == 1


def test_cells_with_no_timestamp_are_skipped_not_crashed():
    assert rc.sittings([{"run_id": "x"}, cell(0)]) == rc.sittings([cell(0)])


def test_a_cell_with_no_end_is_treated_as_instantaneous():
    cells = [dict(cell(0), ended=None)]
    start, end = rc.sittings(cells)[0]
    assert start == end


# ------------------------------------------------------------ G6a semantics
def test_elapsed_measures_the_current_sitting_while_it_runs():
    cells = [cell(0), cell(0.5)]
    now = BASE + 1.0 * H
    assert rc.elapsed_seconds(cells, now=now) == 1.0 * H


def test_elapsed_reports_a_closed_span_once_the_campaign_is_idle():
    cells = [cell(0, dur_h=0.4)]
    now = BASE + 20 * H
    assert rc.elapsed_seconds(cells, now=now) == 0.4 * H


def test_a_long_pause_between_games_does_not_burn_the_elapsed_budget():
    """The motivating case. One game ran, then the campaign waited out a
    concurrent campaign for nine hours, then the next game ran for two."""
    cells = [cell(0), cell(9), cell(10.5)]
    now = BASE + 11 * H
    elapsed = rc.elapsed_seconds(cells, now=now)
    assert elapsed == 2.0 * H
    assert elapsed <= rc.ELAPSED_SECONDS_CAP


def test_a_genuinely_long_sitting_still_trips_g6a():
    """The clause is not weakened for the thing it was written to catch."""
    cells = [cell(i) for i in range(10)]
    now = BASE + 9.5 * H
    gate = rc.evaluate_gate(cells)
    assert rc.elapsed_seconds(cells, now=now) > rc.ELAPSED_SECONDS_CAP
    del gate            # evaluate_gate uses the real clock; the assertion above
                        # is the one that matters, and it is deterministic.


def test_no_cells_means_no_elapsed():
    assert rc.elapsed_seconds([]) is None


# ------------------------------------------------------------ G6c semantics
def test_total_span_runs_from_the_first_cell_ever():
    cells = [cell(0), cell(50)]
    assert rc.total_span_seconds(cells, now=BASE + 60 * H) == 60 * H


def test_a_campaign_dragging_on_for_a_week_trips_g6c():
    """What calendar-elapsed legitimately caught, now caught by its own clause."""
    cells = [cell(0), cell(24), cell(48), cell(96)]
    assert rc.total_span_seconds(cells, now=BASE + 100 * H) > rc.TOTAL_SPAN_SECONDS_CAP


def test_g6c_is_slack_for_a_campaign_that_merely_waited_a_day():
    cells = [cell(0), cell(12)]
    assert rc.total_span_seconds(cells, now=BASE + 13 * H) < rc.TOTAL_SPAN_SECONDS_CAP


# -------------------------------------------------------- timestamp parsing
def test_epoch_is_utc_not_local():
    """calendar.timegm, not mktime: an epoch that shifts with the machine's zone
    would make every clock in the gate depend on where it ran."""
    assert rc._epoch("1970-01-01T00:00:00Z") == 0
    assert rc._epoch("1970-01-02T00:00:00Z") == 86400


def test_epoch_tolerates_junk():
    assert rc._epoch(None) is None
    assert rc._epoch("") is None
    assert rc._epoch("not a date") is None
    assert rc._epoch(17) is None
