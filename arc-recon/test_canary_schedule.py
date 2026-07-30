"""Offline tests for the scheduled canary. No API, no network, no clock drift.

The instrument being tested is a *schedule*, so most of what can go wrong is
something not happening: a sweep that silently stops being due, a truncated plan
that reports INCOMPLETE forever, a run of outages that looks like a quiet log.
Each of those has a test here that asserts the red state, not just the green
one -- same rule as test_hygiene.py, and for the same reason (INC-003).

    cd arc-recon && python -m pytest test_canary_schedule.py
"""

import json
import time

import pytest

import canary
import canary_schedule as sched
from precheck import SealedGameError


# -- fixtures ---------------------------------------------------------------

def game(*hashes, reset="reset0"):
    """A canary spec game whose ACTION hashes are given, RESET fixed."""
    steps = [{"index": 0, "action": "RESET", "hash": reset, "n_frames": 1}]
    for i, h in enumerate(hashes, start=1):
        steps.append({"index": i, "action": "ACTION%d" % i, "hash": h,
                      "n_frames": 1})
    return {"sequence": list(range(1, len(hashes) + 1)),
            "expected": steps, "actions": len(hashes)}


SPEC = {
    "version": "test",
    "games": {
        # 3 discriminating steps in 3 actions
        "ar25-0c556536": game("h1", "h2", "h3"),
        # 1 discriminating step in 2 actions: step 1 repeats the RESET hash
        "g50t-5849a774": game("reset0", "h5", reset="reset0"),
        # 0 discriminating steps: every action is an accepted no-op (tn36's shape)
        "tn36-ef4dde99": game("reset1", "reset1", reset="reset1"),
    },
}


@pytest.fixture
def sandbox(tmp_path, monkeypatch):
    """Every writer points at a temp directory; nothing here touches data/."""
    monkeypatch.setattr(canary, "CANARY_PATH", str(tmp_path / "canary.json"))
    monkeypatch.setattr(canary, "RUNS_PATH", str(tmp_path / "runs.jsonl"))
    monkeypatch.setattr(canary, "FREEZE_PATH", str(tmp_path / "freeze.json"))
    monkeypatch.setattr(canary, "INCIDENTS_PATH",
                        str(tmp_path / "incidents.jsonl"))
    monkeypatch.setattr(sched, "CONFIG_PATH", str(tmp_path / "schedule.json"))
    monkeypatch.setattr(sched, "STATE_PATH", str(tmp_path / "state.json"))
    canary._write_json(str(tmp_path / "canary.json"), SPEC)
    return tmp_path


def fake_replay(verdicts, calls=None, http_calls=None, drop_actions=False):
    """A stand-in for canary.replay that records how it was called.

    `http_calls` defaults to actions + one per game, which is what the real
    sweep produces: RESET is a command rather than an action (ACCESS_CHECK.md
    6b) but it is still a request.  It used to be hardcoded to 0 here, and that
    is exactly why 42 green tests could not see the settlement bug S22 found on
    the live `full` sweep -- 0 is the single value at which charging http_calls
    and charging actions are indistinguishable.  A fixture that pins the one
    number under test to its harmless value tests the harness, not the code.

    `drop_actions` omits `actions_executed` entirely, for the case where the
    sweep reports no count at all.
    """
    def _replay(games=None, client=None, note="", plan=None, tags=None):
        if calls is not None:
            calls.append({"plan": plan, "note": note, "tags": tags})
        actions = sum((plan or {}).values())
        run = {"t": sched._now(), "verdicts": dict(verdicts),
               "actions_executed": actions,
               "http_calls": (actions + len(plan or {})
                              if http_calls is None else http_calls),
               "card_id": "card-test", "plan": plan or {}}
        if drop_actions:
            del run["actions_executed"]
        return run
    return _replay


class FakeGate:
    """A spend gate that records what it was asked to charge.

    `refuse_record` makes settlement raise the way the real gate does when a
    charge exceeds its reservation -- the name matters, because `main()`
    dispatches on `SpendGate*`.
    """

    def __init__(self, refuse_record=False):
        self.charges = []
        self.released = []
        self.refuse_record = refuse_record

    class Tripped(RuntimeError):
        pass

    Tripped.__name__ = "SpendGateTripped"

    def reserve(self, campaign, usd_cap=0.0, action_cap=0):
        self.reserved = {"campaign": campaign, "action_cap": action_cap}
        return type("Res", (), {"reservation_id": "res-test"})()

    def release(self, reservation, reason=""):
        self.released.append(reason)

    def record(self, reservation, usd=0.0, actions=0):
        self.charges.append(actions)
        if self.refuse_record:
            raise FakeGate.Tripped(
                "reservation res-test is over its action cap: %d > %d"
                % (actions, self.reserved["action_cap"]))


def with_gate(monkeypatch, gate):
    """Put `gate` on the spending path, keeping the real reservation size."""
    def _open(campaign, actions):
        res = gate.reserve(campaign, usd_cap=0.0, action_cap=int(actions))
        return gate, res, {"spend_gate": "reserved", "reservation": "res-test"}
    monkeypatch.setattr(sched, "open_spend_gate", _open)
    return gate


# -- which steps can actually catch a forgery -------------------------------

def test_a_step_repeating_its_own_reset_hash_discriminates_nothing():
    assert sched.discriminating(SPEC["games"]["g50t-5849a774"]) == [2]


def test_the_counterfeit_fingerprint_is_not_counted_as_discriminating():
    spoofed = game(sched.COUNTERFEIT_HASH, "h9")
    assert sched.discriminating(spoofed) == [2]


def test_a_game_of_pure_no_ops_discriminates_nothing():
    assert sched.discriminating(SPEC["games"]["tn36-ef4dde99"]) == []


# -- planning ---------------------------------------------------------------

def test_the_cheap_plan_still_buys_every_discriminating_step():
    plan = sched.plan_profile(SPEC, 5, "discriminating")
    assert plan["discriminating_bought"] == plan["discriminating_total"] == 4
    assert plan["actions"] == 5                  # 3 for ar25, 2 for g50t
    assert plan["plan"]["tn36-ef4dde99"] == 0    # no-ops are not bought


def test_an_unfunded_game_is_still_a_free_reset_check():
    plan = sched.plan_profile(SPEC, 5, "discriminating")
    assert set(plan["plan"]) == set(SPEC["games"])
    assert plan["reset_checks"] == 3


def test_a_budget_too_small_drops_the_worst_value_game_first():
    plan = sched.plan_profile(SPEC, 3, "discriminating")
    # ar25 yields 1.0 discriminating steps per action, g50t only 0.5.
    assert plan["plan"] == {"ar25-0c556536": 3, "g50t-5849a774": 0,
                            "tn36-ef4dde99": 0}
    assert plan["discriminating_bought"] == 3 < plan["discriminating_total"]


def test_planning_is_deterministic():
    assert (sched.plan_profile(SPEC, 5, "discriminating")
            == sched.plan_profile(SPEC, 5, "discriminating"))


def test_the_complete_sweep_buys_the_no_ops_the_cheap_one_skips():
    plan = sched.plan_profile(SPEC, 30, "complete")
    assert plan["plan"] == {"ar25-0c556536": 3, "g50t-5849a774": 2,
                            "tn36-ef4dde99": 2}
    assert plan["steps_bought"] == plan["steps_total"] == 7


def test_the_complete_sweep_refuses_rather_than_quietly_truncating():
    with pytest.raises(canary.BudgetExceeded):
        sched.plan_profile(SPEC, 3, "complete")


def test_an_unknown_mode_is_an_error_not_a_default():
    with pytest.raises(RuntimeError):
        sched.plan_profile(SPEC, 30, "whatever")


# -- apply_plan: the truncation that keeps a prefix a PASS -------------------

def test_a_planned_prefix_that_agrees_is_a_pass_not_incomplete():
    cut = canary.apply_plan(SPEC, {"ar25-0c556536": 1})
    observed = [{"index": 0, "action": "RESET", "hash": "reset0"},
                {"index": 1, "action": "ACTION1", "hash": "h1"}]
    assert canary.compare(cut["games"]["ar25-0c556536"]["expected"],
                          observed)["verdict"] == "PASS"


def test_without_truncation_the_same_prefix_would_read_incomplete():
    # The negative control for the test above: this is the bug that would make
    # every scheduled sweep look like an outage.
    observed = [{"index": 0, "action": "RESET", "hash": "reset0"},
                {"index": 1, "action": "ACTION1", "hash": "h1"}]
    assert canary.compare(SPEC["games"]["ar25-0c556536"]["expected"],
                          observed)["verdict"] == "INCOMPLETE"


def test_a_reset_only_plan_costs_nothing_and_still_catches_drift():
    cut = canary.apply_plan(SPEC, {"tn36-ef4dde99": 0})
    assert cut["games"]["tn36-ef4dde99"]["sequence"] == []
    verdict = canary.compare(cut["games"]["tn36-ef4dde99"]["expected"],
                             [{"index": 0, "action": "RESET", "hash": "moved"}])
    assert verdict["verdict"] == "DRIFT"


def test_a_plan_longer_than_the_spec_is_refused():
    with pytest.raises(canary.BudgetExceeded):
        canary.apply_plan(SPEC, {"ar25-0c556536": 9})


def test_the_run_record_says_which_prefix_was_bought(sandbox, monkeypatch):
    calls = []
    monkeypatch.setattr(canary, "replay",
                        fake_replay({"ar25-0c556536": "PASS"}, calls))
    sched.run_scheduled("quick")
    assert calls[0]["plan"] == {"ar25-0c556536": 3, "g50t-5849a774": 2,
                               "tn36-ef4dde99": 0}
    assert calls[0]["tags"] == ["scheduled", "quick"]


# -- the schedule -----------------------------------------------------------

def test_a_canary_that_never_ran_is_due(sandbox):
    assert sched.due("quick")["due"] is True


def test_a_canary_that_just_ran_is_not_due(sandbox):
    state = {"profiles": {"quick": {"last_attempt": sched._now()}}}
    assert sched.due("quick", state=state)["due"] is False


def test_a_canary_that_ran_yesterday_is_due_again(sandbox):
    old = time.strftime("%Y-%m-%dT%H:%M:%SZ",
                        time.gmtime(time.time() - 25 * 3600))
    state = {"profiles": {"quick": {"last_attempt": old}}}
    assert sched.due("quick", state=state)["due"] is True


def test_disabling_the_schedule_blocks_rather_than_delays(sandbox):
    config = sched.load_config()
    config["enabled"] = False
    verdict = sched.due("quick", config=config)
    assert verdict["due"] is False and verdict["blocked"] is True


def test_an_unparseable_timestamp_does_not_silently_skip_a_sweep(sandbox):
    state = {"profiles": {"quick": {"last_attempt": "yesterday-ish"}}}
    assert sched.due("quick", state=state)["due"] is True


# -- gating -----------------------------------------------------------------

def test_a_not_due_run_spends_nothing(sandbox, monkeypatch):
    calls = []
    monkeypatch.setattr(canary, "replay",
                        fake_replay({"ar25-0c556536": "PASS"}, calls))
    sched.run_scheduled("quick")
    record = sched.run_scheduled("quick")
    assert record["outcome"] == "not-due"
    assert len(calls) == 1
    assert sched.OUTCOME_EXIT[record["outcome"]] == 3


def test_a_frozen_programme_does_not_buy_another_sweep(sandbox, monkeypatch):
    calls = []
    monkeypatch.setattr(canary, "replay",
                        fake_replay({"ar25-0c556536": "PASS"}, calls))
    canary.freeze_campaigns("INC-TEST", ["ar25-0c556536"], "test freeze", {})
    record = sched.run_scheduled("quick")
    assert record["outcome"] == "gated"
    assert calls == []
    assert sched.OUTCOME_EXIT[record["outcome"]] == 5


def test_force_overrides_the_freeze_deliberately(sandbox, monkeypatch):
    calls = []
    monkeypatch.setattr(canary, "replay",
                        fake_replay({"ar25-0c556536": "PASS"}, calls))
    canary.freeze_campaigns("INC-TEST", ["ar25-0c556536"], "test freeze", {})
    assert sched.run_scheduled("quick", force=True)["outcome"] == "pass"
    assert len(calls) == 1


def test_a_dry_run_plans_and_spends_nothing(sandbox, monkeypatch):
    calls = []
    monkeypatch.setattr(canary, "replay",
                        fake_replay({"ar25-0c556536": "PASS"}, calls))
    record = sched.run_scheduled("quick", dry_run=True)
    assert record["outcome"] == "dry-run" and calls == []
    assert record["plan"]["actions"] == 5


def test_a_sealed_target_is_refused_before_anything_is_planned(sandbox,
                                                              monkeypatch):
    spec = {"version": "test", "games": {"ls20-016295f7": game("h1")}}
    canary._write_json(canary.CANARY_PATH, spec)
    monkeypatch.setattr(canary, "replay", fake_replay({}))
    with pytest.raises(SealedGameError):
        sched.run_scheduled("quick")


def test_an_underfunded_profile_says_so_out_loud(sandbox, monkeypatch):
    config = sched.load_config()
    config["profiles"]["quick"]["action_budget"] = 3
    canary._write_json(sched.CONFIG_PATH, config)
    monkeypatch.setattr(canary, "replay",
                        fake_replay({"ar25-0c556536": "PASS"}))
    record = sched.run_scheduled("quick")
    assert "coverage_warning" in record


# -- blindness: the failure mode a scheduled canary adds --------------------

def test_three_outages_in_a_row_are_filed_as_an_incident(sandbox, monkeypatch):
    monkeypatch.setattr(canary, "replay",
                        fake_replay({"ar25-0c556536": "INCOMPLETE"}))
    for _ in range(3):
        record = sched.run_scheduled("quick", force=True)
    assert record["outcome"] == "incomplete"
    assert record.get("blind_incident")
    filed = [json.loads(l) for l in
             open(canary.INCIDENTS_PATH, encoding="utf-8") if l.strip()]
    assert filed[-1]["severity"] == "process"
    assert "blind" in filed[-1]["title"].lower()


def test_blindness_does_not_freeze_campaigns(sandbox, monkeypatch):
    monkeypatch.setattr(canary, "replay",
                        fake_replay({"ar25-0c556536": "INCOMPLETE"}))
    for _ in range(3):
        sched.run_scheduled("quick", force=True)
    assert canary.freeze_state().get("frozen") is not True


def test_two_outages_are_not_yet_an_incident(sandbox, monkeypatch):
    monkeypatch.setattr(canary, "replay",
                        fake_replay({"ar25-0c556536": "INCOMPLETE"}))
    for _ in range(2):
        record = sched.run_scheduled("quick", force=True)
    assert record.get("blind_incident") is None


def test_the_blind_incident_is_not_re_filed_at_the_same_streak(sandbox,
                                                              monkeypatch):
    monkeypatch.setattr(canary, "replay",
                        fake_replay({"ar25-0c556536": "INCOMPLETE"}))
    for _ in range(3):
        sched.run_scheduled("quick", force=True)
    before = len(open(canary.INCIDENTS_PATH, encoding="utf-8").readlines())
    sched.run_scheduled("quick", force=True)      # streak 4: a new streak value
    after = len(open(canary.INCIDENTS_PATH, encoding="utf-8").readlines())
    assert after == before + 1                    # once per new streak length
    monkeypatch.setattr(canary, "replay",
                        fake_replay({"ar25-0c556536": "PASS"}))
    sched.run_scheduled("quick", force=True)
    assert sched.load_state()["consecutive_incomplete"] == 0


def test_a_pass_clears_the_streak(sandbox, monkeypatch):
    monkeypatch.setattr(canary, "replay",
                        fake_replay({"ar25-0c556536": "INCOMPLETE"}))
    sched.run_scheduled("quick", force=True)
    monkeypatch.setattr(canary, "replay",
                        fake_replay({"ar25-0c556536": "PASS"}))
    sched.run_scheduled("quick", force=True)
    state = sched.load_state()
    assert state["consecutive_incomplete"] == 0
    assert state["profiles"]["quick"]["last_pass"]


def test_drift_is_reported_as_drift_and_not_as_an_outage(sandbox, monkeypatch):
    monkeypatch.setattr(canary, "replay",
                        fake_replay({"ar25-0c556536": "DRIFT", "g50t-5849a774": "PASS"}))
    record = sched.run_scheduled("quick", force=True)
    assert record["outcome"] == "drift"
    assert sched.OUTCOME_EXIT[record["outcome"]] == 1


# -- the spend gate ---------------------------------------------------------

def test_an_absent_spend_gate_is_recorded_not_assumed_away(sandbox, monkeypatch):
    monkeypatch.setattr(canary, "replay",
                        fake_replay({"ar25-0c556536": "PASS"}))
    record = sched.run_scheduled("quick", force=True)
    assert record["gate"]["spend_gate"] in ("absent", "reserved")


def test_a_gate_that_refuses_stops_the_sweep(sandbox, monkeypatch):
    calls = []

    class Refused(RuntimeError):
        pass
    Refused.__name__ = "SpendGateTripped"

    def refuse(campaign, actions):
        raise Refused("action ceiling reached")

    monkeypatch.setattr(sched, "open_spend_gate", refuse)
    monkeypatch.setattr(canary, "replay",
                        fake_replay({"ar25-0c556536": "PASS"}, calls))
    with pytest.raises(Refused):
        sched.run_scheduled("quick", force=True)
    assert calls == []


def test_the_cli_maps_a_gate_refusal_to_exit_5(sandbox, monkeypatch):
    class Refused(RuntimeError):
        pass
    Refused.__name__ = "SpendGateTripped"

    def refuse(campaign, actions):
        raise Refused("action ceiling reached")

    monkeypatch.setattr(sched, "open_spend_gate", refuse)
    monkeypatch.setattr(canary, "replay",
                        fake_replay({"ar25-0c556536": "PASS"}))
    assert sched.main(["run", "--profile", "quick", "--force"]) == 5


# -- the shipped configuration, not just the machinery ----------------------

def test_the_shipped_daily_sweep_fits_its_declared_budget():
    spec = canary._read_json(canary.CANARY_PATH)
    config = canary._read_json(sched.CONFIG_PATH)
    plan = sched.plan_profile(spec, config["profiles"]["quick"]["action_budget"],
                              config["profiles"]["quick"]["mode"])
    assert plan["actions"] <= 12
    assert plan["discriminating_bought"] == plan["discriminating_total"] == 11


def test_the_shipped_weekly_sweep_buys_every_stored_step():
    spec = canary._read_json(canary.CANARY_PATH)
    config = canary._read_json(sched.CONFIG_PATH)
    plan = sched.plan_profile(spec, config["profiles"]["full"]["action_budget"],
                              config["profiles"]["full"]["mode"])
    assert plan["steps_bought"] == plan["steps_total"] == 16


def test_every_outcome_run_scheduled_can_produce_has_an_exit_code():
    import re
    source = open(sched.__file__, encoding="utf-8").read()
    produced = set(re.findall(r'record\["outcome"\] = "([a-z-]+)"', source))
    assert produced and produced <= set(sched.OUTCOME_EXIT)


# -- running from a worktree ------------------------------------------------
# The working agreement puts every agent in .worktrees/<id>/, and `.env` is
# gitignored, so it exists only in the main checkout. Without the fallback below
# every network-facing tool in this directory is unusable from the one place
# agents are required to work.

def test_a_worktree_finds_the_main_checkouts_env(tmp_path):
    import client
    main = tmp_path / "repo"
    (main / ".git" / "worktrees" / "wt").mkdir(parents=True)
    (main / ".env").write_text("ARC_API_KEY=not-a-real-key\n", encoding="utf-8")
    tree = tmp_path / "repo" / ".worktrees" / "wt"
    tree.mkdir(parents=True)
    (tree / ".git").write_text(
        "gitdir: %s\n" % (main / ".git" / "worktrees" / "wt"), encoding="utf-8")
    assert client.main_checkout(str(tree)) == str(main)


def test_a_normal_checkout_has_no_fallback_to_follow(tmp_path):
    import client
    (tmp_path / ".git").mkdir()
    assert client.main_checkout(str(tmp_path)) is None


def test_a_git_file_that_is_not_a_worktree_marker_is_ignored(tmp_path):
    import client
    (tmp_path / ".git").write_text("something else entirely\n", encoding="utf-8")
    assert client.main_checkout(str(tmp_path)) is None


def test_an_explicit_env_path_is_never_second_guessed(tmp_path):
    import client
    missing = tmp_path / "nowhere.env"
    with pytest.raises(RuntimeError):
        client.load_api_key(str(missing))


# -- settlement: the unit charged, and what survives a refusal --------------
#
# All four came out of S22 item (1), the first ever run of the `full` profile
# (2026-07-30).  It had been configured, scheduled and documented as a standing
# instrument without once executing, and it tripped its own reservation on the
# first try.

def test_the_pool_is_charged_actions_not_http_calls(sandbox, monkeypatch):
    """RESET is a request but not a billable action, so the two differ.

    `README.md` item 6: ARC's `total_actions` counts successful actions only --
    failed 400s and retry amplification do not bill.  Charging http_calls both
    over-charges the shared pool and exceeds a reservation that was made in
    actions, which is what tripped the live sweep.
    """
    gate = with_gate(monkeypatch, FakeGate())
    monkeypatch.setattr(canary, "replay",
                        fake_replay({"ar25-0c556536": "PASS"}))
    record = sched.run_scheduled("quick", force=True)
    planned = record["plan"]["actions"]
    assert gate.charges == [planned], (
        "settled %r against a reservation of %d actions" % (gate.charges, planned))
    assert gate.charges[0] < record["run"]["http_calls"], (
        "the fixture must make the two units differ, or this test cannot fail")
    assert record["gate"]["settlement"] == "recorded"
    assert record["gate"]["charged_actions"] == planned


def test_a_settlement_refusal_does_not_erase_the_sweep_from_the_schedule(
        sandbox, monkeypatch):
    """The actions are already spent; losing the record makes the next run respend.

    This is the failure the live `full` sweep actually produced: 16 actions
    gone, all four games PASS, and `due` still answering "never run".  A
    scheduled task in that state re-spends on every wake-up forever.
    """
    gate = with_gate(monkeypatch, FakeGate(refuse_record=True))
    monkeypatch.setattr(canary, "replay",
                        fake_replay({"ar25-0c556536": "PASS"}))

    with pytest.raises(FakeGate.Tripped):
        sched.run_scheduled("quick", force=True)

    # The refusal must still surface -- but only AFTER the state is on disk.
    state = sched.load_state()
    entry = state.get("profiles", {}).get("quick", {})
    assert entry.get("last_attempt"), (
        "the sweep spent actions and left no trace in the schedule state, so "
        "`due` will call it 'never run' and it will be spent again")
    assert entry.get("last_outcome") == "pass"
    assert sched.due("quick")["due"] is False, (
        "a sweep that just ran is still reported as due")


def test_a_sweep_reporting_no_action_count_is_not_settled_at_zero(
        sandbox, monkeypatch):
    """A missing measurement must not be priced as a free sweep.

    The old code read `run.get("http_calls", 0)`, so an absent count charged
    nothing.  `spend_gate.jsonl` seq 12487 is a canary settlement of
    `actions: 0`; its cause is not established, but a default that prices a
    missing number at zero is not worth keeping while wondering.
    """
    gate = with_gate(monkeypatch, FakeGate())
    monkeypatch.setattr(canary, "replay",
                        fake_replay({"ar25-0c556536": "PASS"}, drop_actions=True))
    with pytest.raises(RuntimeError, match="nothing honest to charge"):
        sched.run_scheduled("quick", force=True)
    assert gate.charges == [], "charged the pool despite having no count"


def test_the_cli_still_reports_a_settlement_refusal_as_exit_5(sandbox, monkeypatch):
    """Recording the sweep must not make the refusal quiet."""
    with_gate(monkeypatch, FakeGate(refuse_record=True))
    monkeypatch.setattr(canary, "replay",
                        fake_replay({"ar25-0c556536": "PASS"}))
    assert sched.main(["run", "--profile", "quick", "--force"]) == 5
