"""The hard gate on this track's spending path, and the two rules it changed.

Three things are under test, and each of them is a thing that already went
wrong once:

  * **A client with no claim on the shared pool cannot open a socket.** Before
    this, `baseline-arms` spent through neither of the proxy's egress paths, so
    the pool's own report showed `$0.0000` against every campaign this track had
    ever run. INC-BA-003 is what an uncounted campaign costs.
  * **The abort rules.** `actions_failed >= 10`, cumulative and absolute, killed
    three ar25 cells with exactly ten failures each and standard deviation zero
    (BUDGET_REPORT 11.2). The replacement has to be shown to catch the case the
    old rule *claimed* to catch, and to stop manufacturing the case it did not.
  * **The barrier.** It moves G4 and nothing else. A test that only checked "the
    gate goes green" would pass for the forbidden change too, so the load-bearing
    assertion here is the negative one: the dollars still count.

    cd baseline-arms && python -m pytest tests/ -q
"""

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from harness import arc_client, bare_cc, run_campaign, spend  # noqa: E402

from conftest import spend_policy  # noqa: E402


# -- the gate is on the path, not beside it ----------------------------------

def test_a_client_without_a_binding_cannot_open_a_socket():
    api = arc_client.ArcClient(api_key="x")
    with pytest.raises(spend.NoSpendBinding):
        api.request("POST", "/api/cmd/RESET", body={"game_id": "ar25-0c556536"})


def test_play_refuses_without_a_binding():
    with pytest.raises(spend.NoSpendBinding):
        bare_cc.play("ar25-0c556536", "claude-haiku-4-5-20251001", 1)


def test_every_request_is_charged_to_the_pool_including_the_failures(
        scratch_gate, monkeypatch):
    """A 400 crossed the wire. Charging only for successes is exactly the
    undercount D-005's 5-11x retry amplification would hide."""
    binding = spend.SpendBinding(scratch_gate,
                                 scratch_gate.reserve("c", 5.0, 50))
    api = arc_client.ArcClient(api_key="x", spend_binding=binding)
    monkeypatch.setattr(arc_client.ledger, "probe", lambda *a, **k: None)

    class Failing:
        def open(self, request, timeout=None):
            raise OSError("no route")

    api._opener = Failing()
    for _ in range(4):
        api.request("GET", "/api/games", raise_on_error=False)

    assert binding.actions_charged == 4
    assert scratch_gate.totals().actions == 4


def test_the_pool_refuses_when_the_reservation_is_exhausted(scratch_gate,
                                                            monkeypatch):
    binding = spend.SpendBinding(scratch_gate, scratch_gate.reserve("c", 5.0, 2))
    api = arc_client.ArcClient(api_key="x", spend_binding=binding)
    monkeypatch.setattr(arc_client.ledger, "probe", lambda *a, **k: None)

    class Failing:
        def open(self, request, timeout=None):
            raise OSError("no route")

    api._opener = Failing()
    api.request("GET", "/api/games", raise_on_error=False)
    api.request("GET", "/api/games", raise_on_error=False)
    with pytest.raises(spend.SpendGateTripped) as exc:
        api.request("GET", "/api/games", raise_on_error=False)
    assert exc.value.rule == "RESERVATION_ACTION_CAP"


def test_the_check_happens_before_the_socket_not_after(scratch_gate, monkeypatch):
    """Negative control on the ordering. A gate that charges after the fact is a
    receipt; the refusal has to land before anything is sent."""
    binding = spend.SpendBinding(scratch_gate, scratch_gate.reserve("c", 5.0, 0))
    api = arc_client.ArcClient(api_key="x", spend_binding=binding)
    monkeypatch.setattr(arc_client.ledger, "probe", lambda *a, **k: None)
    opened = []

    class Watching:
        def open(self, request, timeout=None):
            opened.append(1)
            raise OSError("should never be reached")

    api._opener = Watching()
    with pytest.raises(spend.SpendGateTripped):
        api.request("GET", "/api/games", raise_on_error=False)
    assert opened == [], "the socket was opened before the gate answered"


def test_an_unpriced_model_call_is_charged_the_ceiling_not_zero(scratch_gate):
    binding = spend.SpendBinding(scratch_gate, scratch_gate.reserve("c", 5.0, 10))
    binding.record_model_call(None)
    totals = scratch_gate.totals()
    assert totals.usd == pytest.approx(spend.MODEL_CALL_CEILING_USD)
    assert totals.unpriced_calls == 1
    assert binding.unpriced_calls == 1


def test_a_priced_model_call_is_charged_what_it_cost(scratch_gate):
    binding = spend.SpendBinding(scratch_gate, scratch_gate.reserve("c", 5.0, 10))
    binding.record_model_call(0.0217)
    assert scratch_gate.totals().usd == pytest.approx(0.0217)
    assert scratch_gate.totals().unpriced_calls == 0


def test_the_pool_is_global_not_per_reservation(tmp_path):
    """The property the whole module exists for: a second claim sees the first
    one's spend, and its own headroom is what is left."""
    gate = spend.SpendGate(policy=spend_policy(tmp_path, usd_ceiling=1.0))
    first = spend.SpendBinding(gate, gate.reserve("a", 0.5, 10))
    first.record_model_call(0.4)
    first.release()
    second = spend.SpendBinding(gate, gate.reserve("b", 0.5, 10))
    assert gate.totals().usd == pytest.approx(0.4)
    with pytest.raises(spend.SpendGateTripped) as exc:
        gate.check(second.reservation, usd=0.7, actions=0)
    assert exc.value.rule == "POOL_USD_CEILING"


# -- the abort rules ---------------------------------------------------------

def test_the_cumulative_cap_scales_with_the_budget():
    """The defect BUDGET_REPORT 11.2 diagnosed: an absolute ten, judging an
    episode whose expected failure count grows with its action budget."""
    assert bare_cc.cumulative_failure_cap(20) == 20
    assert bare_cc.cumulative_failure_cap(30) == 30
    assert bare_cc.cumulative_failure_cap(120) == 120
    # Never stricter than the constant it replaces.
    assert bare_cc.cumulative_failure_cap(1) == 10
    assert bare_cc.cumulative_failure_cap(5) == 10


def test_consecutive_and_cumulative_are_different_verdicts():
    """The rule `api_unusable` was always described as (section 7) and never
    was (section 11.2): failures back to back, not scattered."""
    assert bare_cc.CONSECUTIVE_FAILURE_ABORT == 10
    # And the outcome names must not be collapsed: one is a claim about the
    # API, the other a result about the arm.
    assert "api_unusable" in run_campaign.DEAD_OUTCOMES
    assert "failure_grind" not in run_campaign.DEAD_OUTCOMES
    assert "failure_grind" in run_campaign.LIVE_OUTCOMES
    assert "spend_gate_tripped" not in run_campaign.DEAD_OUTCOMES


def test_the_old_ar25_shape_no_longer_reads_as_api_unusable():
    """The regression this whole change is for.

    Ten scattered failures at a 30-action budget -- the exact shape of all three
    ar25 cells -- must no longer be reported as the API being unusable, because
    at a ~0.6 action success rate that shape was guaranteed by construction.
    """
    scattered, longest = 10, 3
    assert scattered < bare_cc.cumulative_failure_cap(30)
    assert longest < bare_cc.CONSECUTIVE_FAILURE_ABORT
    # ...while a genuine run of refusals still is.
    assert 10 >= bare_cc.CONSECUTIVE_FAILURE_ABORT


# -- the barrier -------------------------------------------------------------

def _cell(run_id, outcome, cost=1.0):
    return {"run_id": run_id, "game_id": "ar25-0c556536", "model":
            "claude-haiku-4-5-20251001", "outcome": outcome, "cost_usd": cost,
            "actions_ok": 5, "actions_failed": 10, "http_calls_gameplay": 50,
            "wall_seconds": 100, "budget": 30,
            "started": "2026-07-27T18:21:28Z"}


def test_a_barrier_moves_g4_and_nothing_else(monkeypatch, tmp_path):
    cells = [_cell("dead-1", "api_unusable"), _cell("dead-2", "api_unusable"),
             _cell("live-1", "budget_exhausted")]

    monkeypatch.setattr(run_campaign, "barriers", lambda: [])
    before = run_campaign.evaluate_gate(cells)
    assert before["state"] == "red"
    assert any(t.startswith("G4") for t in before["tripped"])

    monkeypatch.setattr(run_campaign, "barriers", lambda: [
        {"barrier_id": "B-1", "adjudicated_through_run_id": "dead-2",
         "remediations": ["something real"]}])
    after = run_campaign.evaluate_gate(cells)
    assert not any(t.startswith("G4") for t in after["tripped"])

    # The load-bearing negative: the adjudicated cells' money is still counted.
    # A barrier that reset the dollar total would be the move BUDGET_REPORT
    # section 11.3 rules out, and this assertion is what tells the two apart.
    assert after["totals"]["cost_usd"] == before["totals"]["cost_usd"] == 3.0
    assert after["totals"]["cells"] == 3
    assert after["g4_judges_cells"] == 1
    # G6b, the work-done clock, still sums the adjudicated cells too.
    assert after["totals"]["compute_seconds"] == before["totals"]["compute_seconds"]


def test_a_barrier_restarts_the_elapsed_clock_but_not_the_compute_clock(monkeypatch):
    """G6a is a condition clock ("this has been running all day") and G6b is a
    work clock ("this did far more work than planned"). Only the first can be
    restarted by an adjudication, because only the first counts a stop."""
    old = dict(_cell("old-1", "budget_exhausted"), started="2020-01-01T00:00:00Z")
    new = dict(_cell("new-1", "budget_exhausted"),
               started=run_campaign.ledger.utcnow())

    monkeypatch.setattr(run_campaign, "barriers", lambda: [])
    without = run_campaign.evaluate_gate([old, new])
    assert any(t.startswith("G6a") for t in without["tripped"])

    monkeypatch.setattr(run_campaign, "barriers", lambda: [
        {"barrier_id": "B-1", "adjudicated_through_run_id": "old-1",
         "remediations": ["x"]}])
    with_barrier = run_campaign.evaluate_gate([old, new])
    assert not any(t.startswith("G6a") for t in with_barrier["tripped"])
    assert with_barrier["totals"]["compute_seconds"] \
        == without["totals"]["compute_seconds"] == 200
    # The full-history figure is still reported, just not used as a threshold.
    assert with_barrier["totals"]["elapsed_seconds_all_cells"] \
        > with_barrier["totals"]["elapsed_seconds"]


def test_a_barrier_does_not_stop_g4_firing_again_afterwards(monkeypatch):
    cells = [_cell("dead-1", "api_unusable"), _cell("dead-2", "api_unusable"),
             _cell("dead-3", "api_unusable"), _cell("dead-4", "model_error")]
    monkeypatch.setattr(run_campaign, "barriers", lambda: [
        {"barrier_id": "B-1", "adjudicated_through_run_id": "dead-2",
         "remediations": ["x"]}])
    gate = run_campaign.evaluate_gate(cells)
    assert any(t.startswith("G4") for t in gate["tripped"]), \
        "a barrier must adjudicate the past, not disarm the future"


def test_a_barrier_naming_an_unknown_cell_judges_everything(monkeypatch):
    """Fail closed. An unpositionable barrier can only stop the campaign."""
    cells = [_cell("dead-1", "api_unusable"), _cell("dead-2", "api_unusable")]
    monkeypatch.setattr(run_campaign, "barriers", lambda: [
        {"barrier_id": "B-1", "adjudicated_through_run_id": "not-a-cell",
         "remediations": ["x"]}])
    assert run_campaign.evaluate_gate(cells)["state"] == "red"


def test_a_barrier_with_no_remediation_is_refused(monkeypatch, tmp_path):
    path = tmp_path / "campaign_barriers.jsonl"
    path.write_text(json.dumps({"barrier_id": "B-0", "remediations": []}) + "\n",
                    encoding="utf-8")
    monkeypatch.setattr(run_campaign, "BARRIERS_PATH", str(path))
    with pytest.raises(ValueError, match="remediations"):
        run_campaign.barriers()


def test_the_real_barrier_file_is_wellformed_if_it_exists():
    """Whatever this repository actually ships must load and must say what was
    fixed -- the file is the audit trail, not a scratch pad."""
    for bar in run_campaign.barriers():
        assert bar["barrier_id"]
        assert bar["adjudicated_through_run_id"]
        assert bar["remediations"]
        assert bar["utc"]


def test_cell_caps_are_the_campaign_gates_restated_not_new_numbers():
    caps = run_campaign.cell_caps("claude-haiku-4-5-20251001", 30)
    unit = run_campaign.PILOT_UNIT["claude-haiku-4-5-20251001"]["usd_per_action"]
    assert caps["usd"] == pytest.approx(run_campaign.CELL_COST_MULTIPLE * unit * 30)
    assert caps["actions"] > run_campaign.HTTP_PER_ACTION_CAP * 30
