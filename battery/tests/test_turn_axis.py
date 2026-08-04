"""S46 · the decision axis is reported, and never manufactured.

`Run.turn_costs()` used to fill a missing `Call.turn` in with the call's
position in the list, and put that position into the same bucket dictionary as
the real labels.  So a *partly* labelled record summed the unlabelled call at
position 7 into the bucket of the call genuinely labelled `turn=7`, two
quantities with nothing to do with each other; and a *wholly* unlabelled record
was renumbered `0..n-1` and scored as if the axis had been recorded.

`freeze/RESIDUALS.json` registers this as `E2-AXIS` and
`freeze/STATS_RULES.md` §3.0.2 step 4 is the ruling that named it.  The
discipline applied here is `PREREG_E2L.md` §2 G4's, quoted verbatim in that
file: **轴重建不了就是没有测量** -- an axis that cannot be rebuilt is a
measurement that was not taken, not a measurement whose value is doubtful.

The two negative controls are the point of this module as much as the positive
one.  A fix that refuses more than it should is not a fix: a fully labelled
record has to come out reading exactly what it read before, or this was a
silent redefinition of the endpoint rather than a repair of it.
"""

import pytest

from battery.adapters.ledger_jsonl import parse_rows
from battery.guard import load_piles
from battery.metrics import evaluate
from battery.metrics.economy import MIN_TURNS_FOR_SHAPE
from battery.model import Call, Run, Step
from battery.run_battery import collect_runs


@pytest.fixture(scope="module")
def piles():
    return load_piles()


def _env(game_id, run_id="r", **kw):
    row = {"run_id": run_id, "game_id": game_id, "arm": "bare_cc",
           "model": "m", "step_idx": 0, "action": "RESET",
           "frame": [[[1, 2], [3, 4]]]}
    row.update(kw)
    return row


def _run(calls, steps=6, **kw):
    return Run(run_id="t", arm="test", source="test", intent="solve",
               steps=[Step(idx=i, action="a", state_key="s%d" % i)
                      for i in range(steps)],
               calls=list(calls), **kw)


def _labelled(n, price=1.0):
    """The ordinary record: one call per decision, and it says so."""
    return [Call(idx=i, step_idx=i, cost_usd=price, turn=i) for i in range(n)]


# --------------------------------------------------------------------------
# The axis itself.
# --------------------------------------------------------------------------

def test_the_four_axis_cases_are_told_apart():
    assert _run([]).turn_axis().status == "no-calls"
    assert _run(_labelled(4)).turn_axis().status == "exact"
    assert _run([Call(idx=i, cost_usd=1.0) for i in range(4)]
                ).turn_axis().status == "absent"
    mixed = _labelled(3) + [Call(idx=3, cost_usd=1.0)]
    assert _run(mixed).turn_axis().status == "partial"


def test_the_axis_counts_every_call_not_only_the_priced_ones():
    """An unpriced call still occupied a key, and so still moved the axis."""
    calls = _labelled(3) + [Call(idx=3, cost_usd=None)]
    axis = _run(calls).turn_axis()
    assert axis.status == "partial"
    assert (axis.n_calls, axis.n_labelled) == (4, 3)


def test_retries_collapse_onto_their_decision_and_the_axis_stays_exact():
    """The property `turn` was introduced for, unchanged by S46."""
    calls = [Call(idx=0, cost_usd=1.0, turn=0),
             Call(idx=1, cost_usd=2.0, turn=0),
             Call(idx=2, cost_usd=4.0, turn=1)]
    run = _run(calls)
    assert run.turn_axis().status == "exact"
    assert run.turn_costs() == [3.0, 4.0]


# --------------------------------------------------------------------------
# The defect the ticket names.
# --------------------------------------------------------------------------

def test_a_position_and_a_label_no_longer_share_a_bucket():
    """The exact shape from the ask: call 0 unlabelled, call 7 labelled `0`.

    Under the old fallback both landed in `buckets[0]` and were summed, which
    is why the ticket calls the two sources semantically unrelated.  The record
    is now refused, so the sum is not reachable at all.
    """
    calls = ([Call(idx=0, cost_usd=1.0)]
             + [Call(idx=i, cost_usd=1.0, turn=i - 7) for i in range(7, 15)])
    run = _run(calls)
    assert run.turn_axis().status == "partial"
    assert run.turn_costs() == []
    for mid in ("E2", "E3"):
        value = evaluate(run)[mid]
        assert value.status == "insufficient-data"
        assert value.value is None
        assert "turn label" in value.reason
        # `unsound`'s grep handle: this is an incoherent record, not a thin one
        assert value.reason.startswith("incoherent record: ")


def test_a_partly_labelled_record_is_refused_however_long_it_is():
    """Length is not a cure: the axis gate is not the eight-turn floor."""
    calls = _labelled(40)[:39] + [Call(idx=39, cost_usd=1.0)]
    run = _run(calls)
    assert len(calls) > MIN_TURNS_FOR_SHAPE
    for mid in ("E2", "E3"):
        assert evaluate(run)[mid].status == "insufficient-data"
        assert "1 of 40" in evaluate(run)[mid].reason


# --------------------------------------------------------------------------
# Negative control 1 -- a fully labelled record must not move.
# --------------------------------------------------------------------------

def test_a_flat_fully_labelled_bill_still_scores_a_quarter():
    """The pre-S46 number, pinned. A flat run reads 0.250 at every length."""
    assert evaluate(_run(_labelled(40)))["E2"].value == pytest.approx(0.25)


def test_a_fully_labelled_record_reads_what_it_read_before():
    """Every economy reading on one hand-checkable record, at both statuses.

    Forty turns, the first ten billed at 10.0 and the rest at 1.0: total 130,
    head = the first ten turns = 100, so E2 = 100/130.  E3 crosses 90% of 130
    at turn 27, so 27/40.  These are the numbers the old code produced on the
    same record and they are what it must still produce.
    """
    calls = [Call(idx=i, step_idx=i, turn=i,
                  cost_usd=10.0 if i < 10 else 1.0) for i in range(40)]
    values = evaluate(_run(calls))
    assert values["E1"].value == pytest.approx(130.0)
    assert values["E2"].value == pytest.approx(100 / 130)
    assert values["E3"].value == pytest.approx(27 / 40)
    assert values["E2"].support["turns"] == 40


def test_short_and_free_records_are_still_refused_for_their_own_reasons():
    """The axis gate must not swallow the gates that were already there."""
    short = evaluate(_run(_labelled(4)))["E2"]
    assert "trivially front-loaded" in short.reason
    free = evaluate(_run(_labelled(40, price=0.0)))["E2"]
    assert free.reason == "total cost is zero"


def test_an_unpriced_bill_still_reads_as_an_unpriced_bill():
    """Gate order: a partly priced record is named by its price, not its axis.

    Both defects are present here. `unpriced` is the more basic one and is the
    reason a reader can act on, so it is checked first.
    """
    calls = [Call(idx=i, cost_usd=None if i else 1.0) for i in range(40)]
    reason = evaluate(_run(calls))["E2"].reason
    assert "carry no price" in reason


# --------------------------------------------------------------------------
# Negative control 2 -- an unlabelled record is refused, not renumbered.
# --------------------------------------------------------------------------

def test_a_wholly_unlabelled_record_is_refused_not_renumbered():
    calls = [Call(idx=i, cost_usd=1.0) for i in range(40)]
    run = _run(calls)
    assert run.turn_axis().status == "absent"
    # The renumbering itself, gone: not `[1.0] * 40`, and not a shorter list
    # that quietly dropped the money either.
    assert run.turn_costs() == []
    for mid in ("E2", "E3"):
        value = evaluate(run)[mid]
        assert value.status == "insufficient-data"
        assert value.value is None
        assert "0..n-1" in value.reason


def test_refusing_the_shape_does_not_hide_the_money():
    """The failure mode the ticket is really about: 看不出钱少了一截.

    E2 and E3 decline, and E1 keeps saying exactly how much was spent. An
    absent shape must not become an absent bill -- that would replace one
    silent misreading with a quieter one.
    """
    run = _run([Call(idx=i, cost_usd=0.25) for i in range(40)])
    values = evaluate(run)
    assert values["E1"].value == pytest.approx(10.0)
    assert values["E2"].status == "insufficient-data"
    assert values["E3"].status == "insufficient-data"


# --------------------------------------------------------------------------
# One layer down: the adapter that could build the collision unobserved.
# --------------------------------------------------------------------------

def _call_row(run_id="a", **kw):
    row = {"run_id": run_id, "model": "m", "provider": "p",
           "total_cost_usd": 1.0, "usage": {"input_tokens": 10}}
    row.update(kw)
    return row


def test_the_ledger_adapter_does_not_invent_a_turn_from_row_order(piles):
    """`ledger_jsonl.py` used to hand an unstamped row its own position.

    Worth stating precisely, because the precise version is weaker than the
    ticket's: this adapter sorts unstamped rows *last* (`ledger_jsonl.py:193`),
    so their positions start at or above the number of distinct stamped steps
    and can never land on a real `turn_of` value.  The ledger adapter could
    therefore fabricate a label but not collide one.  It is still a fabricated
    label -- an unrecorded decision ordinal presented as a recorded one -- and
    the mixed record it produces is what reaches `turn_costs`, where the two
    sources did share a key space.
    """
    rows = [_env("ar25-0c556536", run_id="a"),
            _call_row(step_idx=4),
            _call_row(),                       # no step_idx
            _call_row(step_idx=9)]
    run = parse_rows(rows, source="t", piles=piles)[0]
    assert [c.turn for c in run.calls] == [0, 1, None]
    assert run.turn_axis().status == "partial"
    assert run.notes["turns"] == 2


def test_a_ledger_that_stamps_nothing_yields_no_axis_at_all(piles):
    rows = [_env("ar25-0c556536", run_id="a"), _call_row(), _call_row()]
    run = parse_rows(rows, source="t", piles=piles)[0]
    assert [c.turn for c in run.calls] == [None, None]
    assert run.turn_axis().status == "absent"
    # Not the call count standing in for a decision count.
    assert run.notes["turns"] is None


def test_a_fully_stamped_ledger_is_unchanged(piles):
    rows = [_env("ar25-0c556536", run_id="a"),
            _call_row(step_idx=4), _call_row(step_idx=4),
            _call_row(step_idx=9)]
    run = parse_rows(rows, source="t", piles=piles)[0]
    assert [c.turn for c in run.calls] == [0, 0, 1]
    assert run.turn_axis().status == "exact"
    assert run.turn_costs() == [2.0, 1.0]
    assert run.notes["turns"] == 2


# --------------------------------------------------------------------------
# The corpus, which is what makes negative control 1 an empirical claim.
# --------------------------------------------------------------------------

def test_no_real_run_loses_a_reading_to_the_new_gate(piles):
    """Measured 2026-08-02: every loadable run is `exact` or has no calls.

    This is the whole warrant for the change being a repair rather than a
    redefinition -- the fallback was reachable but never actually load-bearing
    on the offline corpus, so no confirmatory number moves.  If a future
    source starts emitting partly stamped ledgers this test is where it
    surfaces, and the right answer then is to fix the source, not the gate.
    """
    runs = collect_runs(piles)
    assert len(runs) >= 100
    by_status = {}
    for run in runs:
        status = run.turn_axis().status
        by_status.setdefault(status, []).append(run.run_id)
    assert set(by_status) <= {"exact", "no-calls"}, {
        k: v[:3] for k, v in by_status.items()
        if k not in ("exact", "no-calls")}
