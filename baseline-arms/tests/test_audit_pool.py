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


def test_focusing_on_one_game_does_not_orphan_the_others(scratch_gate):
    """The regression. `--game sk48` used to filter the cell list itself, so the
    next run reported g50t's three reservations as unattributable spend -- the
    most serious thing this tool can say -- because their cells had been
    filtered out of the comparison it was making."""
    first = _live(scratch_gate)
    _spend_actions(scratch_gate, first, 1 + 1 + 50 + 1)
    scratch_gate.record(first, usd=0.5, actions=0)
    scratch_gate.release(first)

    second = _live(scratch_gate)
    _spend_actions(scratch_gate, second, 1 + 1 + 40 + 1)
    scratch_gate.record(second, usd=0.7, actions=0)
    scratch_gate.release(second)

    cells = [_cell(first.reservation_id, repeat=1),
             dict(_cell(second.reservation_id, gameplay=40, cost=0.7, repeat=2),
                  game_id="sk48-d8078629")]

    report = audit_pool.audit(cells, CAMPAIGN, scratch_gate, focus="sk48-d8078629")
    assert report["orphans"] == [], "focusing invented an orphan"
    assert report["clean"]
    # The view narrowed; the record did not.
    assert len(report["cells"]) == 1
    assert report["all_cells"] == 2
    assert report["cells"][0]["game_id"] == "sk48-d8078629"


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


# -- the refused / stopped distinction (audit_cells) -------------------------

def test_a_give_up_step_is_not_counted_as_a_refused_action():
    """Two tn36 cells ended `gave_up`, and the audit reported 'summary 5,
    ledger 6' on both. The summary was right: a GIVE UP writes failed=True and
    a null frame because it produced no frame, but it never reached the server,
    so it is not something `actions_failed` counts and it says nothing about
    the API."""
    from harness import audit_cells

    refusal = {"failed": True, "http_status": 500, "action": {"id": 6}}
    giveup = {"failed": True, "action": "gave up", "reason": "gave up"}
    success = {"failed": False, "action": {"id": 1}}

    assert audit_cells.reached_api(refusal) is True
    assert audit_cells.reached_api(giveup) is False
    assert audit_cells.reached_api(success) is True
    # An explicit field wins over the inference, so newer writers can state it.
    assert audit_cells.reached_api(dict(giveup, reached_api=True)) is True
    assert audit_cells.reached_api(dict(refusal, reached_api=False)) is False


def test_the_real_tn36_cells_now_reconcile():
    """The regression, against the actual records rather than a fixture."""
    from harness import audit_cells, run_campaign

    cells = [c for c in run_campaign.load_cells()
             if (c.get("game_id") or "").startswith("tn36")]
    if not cells:
        import pytest
        pytest.skip("tn36 has not been run in this checkout")
    records = [r for r, _, _ in audit_cells.read_jsonl(audit_cells.ledger_paths())]
    probes = [r for r, _, _ in audit_cells.read_jsonl(audit_cells.probe_paths())]
    for cell in cells:
        report = audit_cells.audit_run(cell, records, probes)
        assert not report["findings"], (cell["run_id"], report["findings"])
