"""The between-games reconciliation, checked against pools it built itself.

This audit is what decides whether the campaign advances, so its failure modes
matter more than its happy path. Every check below has a negative control: the
clean case AND the case it is supposed to catch.

The action identity is the sharp one. An episode makes `reset_attempts` RESET
requests, one scorecard open, its gameplay requests, and 1-8 close attempts, so

    close_tries = pool_actions - reset_attempts - 1 - gameplay

is determined by the other four terms and must land in [1, 8]. A miscount
anywhere pushes it out of range, which is why it is a real constraint and not a
restatement of the sum.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from harness import audit_pool, spend  # noqa: E402

CAMPAIGN = "phase3-variance-envelope"


def _spend_actions(gate, reservation, n):
    for _ in range(n):
        gate.record(reservation, usd=0.0, actions=1, detail={"path": "/api/cmd/X"})


def _cell(reservation_id, *, gameplay=50, resets=1, cost=0.5,
          outcome="budget_exhausted", repeat=1):
    return {"run_id": "r-%s" % repeat, "game_id": "g50t-5849a774",
            "repeat": repeat, "outcome": outcome,
            "http_calls_gameplay": gameplay, "reset_attempts": resets,
            "cost_usd": cost, "spend": {"reservation_id": reservation_id}}


def _live(gate, usd_cap=5.0, action_cap=400):
    return gate.reserve(CAMPAIGN, usd_cap, action_cap)


# -- the happy path ----------------------------------------------------------

def test_a_wellformed_cell_reconciles_clean(scratch_gate):
    res = _live(scratch_gate)
    _spend_actions(scratch_gate, res, 1 + 1 + 50 + 3)      # reset, open, play, close
    scratch_gate.record(res, usd=0.5, actions=0, detail={"model": "haiku"})
    scratch_gate.release(res)

    report = audit_pool.audit([_cell(res.reservation_id)], CAMPAIGN, scratch_gate)
    assert report["clean"], report["cells"][0]["problems"]
    assert report["cells"][0]["implied_close_tries"] == 3


# -- the action identity -----------------------------------------------------

def test_a_short_action_count_is_caught(scratch_gate):
    """The pool saw fewer requests than the cell says it made -- so either the
    gate was bypassed somewhere or the cell is overstating its work."""
    res = _live(scratch_gate)
    _spend_actions(scratch_gate, res, 1 + 1 + 40)          # 10 gameplay missing
    scratch_gate.record(res, usd=0.5, actions=0)
    scratch_gate.release(res)

    report = audit_pool.audit([_cell(res.reservation_id, gameplay=50)],
                              CAMPAIGN, scratch_gate)
    assert not report["clean"]
    assert any("action identity does not close" in p
               for p in report["cells"][0]["problems"])


def test_an_inflated_action_count_is_caught_too(scratch_gate):
    """Negative control in the other direction: more pool requests than the
    episode can account for is equally a discrepancy, not a rounding margin."""
    res = _live(scratch_gate)
    _spend_actions(scratch_gate, res, 1 + 1 + 50 + 40)     # 40 closes is absurd
    scratch_gate.record(res, usd=0.5, actions=0)
    scratch_gate.release(res)

    report = audit_pool.audit([_cell(res.reservation_id)], CAMPAIGN, scratch_gate)
    assert not report["clean"]
    assert report["cells"][0]["implied_close_tries"] == 40


def test_the_identity_is_not_checked_when_no_reset_window_was_ever_won(scratch_gate):
    res = _live(scratch_gate)
    _spend_actions(scratch_gate, res, 31)
    scratch_gate.release(res)
    report = audit_pool.audit(
        [_cell(res.reservation_id, gameplay=0, resets=30, cost=0.0,
               outcome="no_reset_window")], CAMPAIGN, scratch_gate)
    assert report["clean"], report["cells"][0]["problems"]


# -- the dollars -------------------------------------------------------------

def test_disagreeing_dollars_are_caught(scratch_gate):
    res = _live(scratch_gate)
    _spend_actions(scratch_gate, res, 1 + 1 + 50 + 2)
    scratch_gate.record(res, usd=0.90, actions=0)
    scratch_gate.release(res)
    report = audit_pool.audit([_cell(res.reservation_id, cost=0.50)],
                              CAMPAIGN, scratch_gate)
    assert any("dollars disagree" in p for p in report["cells"][0]["problems"])


def test_an_unpriced_call_is_reported_as_a_ceiling_not_a_mismatch(scratch_gate):
    """Two different statements. 'The sums differ' means someone counted wrong;
    'a call could not be priced' means the figure is a bound. Collapsing them
    would let a real mismatch hide behind a known blindness."""
    res = _live(scratch_gate)
    _spend_actions(scratch_gate, res, 1 + 1 + 50 + 2)
    scratch_gate.record(res, usd=spend.MODEL_CALL_CEILING_USD, actions=0,
                        unpriced=True)
    scratch_gate.release(res)
    report = audit_pool.audit([_cell(res.reservation_id, cost=0.50)],
                              CAMPAIGN, scratch_gate)
    problems = report["cells"][0]["problems"]
    assert any("could not be priced" in p for p in problems)
    assert not any("dollars disagree" in p for p in problems)


# -- the lease ---------------------------------------------------------------

def test_a_reservation_left_open_is_caught(scratch_gate):
    res = _live(scratch_gate)
    _spend_actions(scratch_gate, res, 1 + 1 + 50 + 2)
    scratch_gate.record(res, usd=0.5, actions=0)
    # deliberately not released
    report = audit_pool.audit([_cell(res.reservation_id)], CAMPAIGN, scratch_gate)
    assert any("never released" in p for p in report["cells"][0]["problems"])


# -- attribution -------------------------------------------------------------

def test_spend_in_this_campaign_claimed_by_no_cell_is_an_orphan(scratch_gate):
    kept = _live(scratch_gate)
    _spend_actions(scratch_gate, kept, 1 + 1 + 50 + 2)
    scratch_gate.record(kept, usd=0.5, actions=0)
    scratch_gate.release(kept)

    stray = _live(scratch_gate)
    _spend_actions(scratch_gate, stray, 7)
    scratch_gate.release(stray)

    report = audit_pool.audit([_cell(kept.reservation_id)], CAMPAIGN, scratch_gate)
    assert not report["clean"]
    assert [o["reservation_id"] for o in report["orphans"]] == [stray.reservation_id]
    assert any("Unattributable spend" in f for f in report["findings"])


def test_a_campaign_with_no_cells_is_attributed_not_orphaned(scratch_gate):
    """A smoke test or quota probe under its own campaign name is the correct
    shape, and must not be reported as the failure it is the fix for."""
    probe = scratch_gate.reserve("a-probe-campaign", 1.0, 10)
    _spend_actions(scratch_gate, probe, 3)
    scratch_gate.release(probe)
    report = audit_pool.audit([], "a-probe-campaign", scratch_gate)
    assert report["clean"]
    assert report["orphans"] == []
    assert len(report["unclaimed_informational"]) == 1
    assert any("not a discrepancy" in f for f in report["findings"])


def test_a_pre_gate_cell_is_unreconcilable_not_a_problem(scratch_gate):
    """An alarm nobody can ever clear is one people learn to ignore. The three
    ar25 cells have no pool line and never will."""
    cell = _cell(None)
    cell["spend"] = None
    report = audit_pool.audit([cell], CAMPAIGN, scratch_gate)
    assert report["clean"]
    assert report["unreconcilable_count"] == 1
    assert report["problem_count"] == 0


def test_a_cell_naming_a_reservation_the_pool_never_saw_is_a_problem(scratch_gate):
    """The opposite of an orphan, and worse: the cell claims a spend that is not
    in the one file other sessions read."""
    report = audit_pool.audit([_cell("res-neverexisted")], CAMPAIGN, scratch_gate)
    assert not report["clean"]
    assert any("absent from the pool" in p for p in report["cells"][0]["problems"])
