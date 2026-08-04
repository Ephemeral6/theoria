"""A25b: the arm can tell, at the call, that it bought nothing -- and the
levers that act on that are off by default.

`test_action_economy.py` defends the claim that A25's knob changed no default.
This file defends three more.

**The signal is real.** `inner/inertia.py` recompiles the two book revisions an
adjudication was snapshotted between and replays both over the frames already
in hand. Two of this repo's own archived snapshot pairs are used as fixtures --
one where the new manual moved a prediction and one where it did not -- because
a detector tested only against DSL written for the test is a detector tested
against its author's imagination. Those two cases are exactly the ones the
census scores as `moved_a_prediction` and
`predicted_what_the_old_manual_predicted`, and if the machinery ever stops
agreeing with the census the test says so at the level of one call rather than
at the level of an aggregate.

**The signal decides nothing unless asked.** `inertia=off` is the default, the
module is not imported on that path, `gate_continuation` allows everything, and
a config that would act on a signal it does not compute raises rather than
silently doing nothing -- because a policy that silently does nothing looks,
in a round's results, exactly like an intervention that did not work.

**The measurement is separable from the intervention.** `measure-inertia`
computes the verdict and changes no decision, and the replay proves it: its
row must equal `today`'s to the dollar. That equality is the negative control
for every other row in the table -- if merely measuring moved the numbers, no
row below it would mean anything.

Offline: no key, no network, no model call, no spend.
"""

import json
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
ARM = os.path.dirname(HERE)
if ARM not in sys.path:
    sys.path.insert(0, ARM)

import _bootstrap                                     # noqa: E402,F401

from armtools import action_economy as census_mod     # noqa: E402
from inner import economy as economy_mod              # noqa: E402
from inner import inertia as inertia_mod              # noqa: E402

#: An archived adjudication whose new manual predicted something different, and
#: one whose new manual predicted exactly what the old one did. Both from
#: `20260728T015354Z-g50t-first-contact`, both tracked in git, both scored the
#: same way by the census.
_ARCHIVE = os.path.join(ARM, "runs", "20260728T015354Z-g50t-first-contact",
                        "books", "snapshots")
MOVED_PAIR = (os.path.join(_ARCHIVE, "rev03-before-theorize"),
              os.path.join(_ARCHIVE, "rev04-after-theorize"))
INERT_PAIR = (os.path.join(_ARCHIVE, "rev07-before-theorize"),
              os.path.join(_ARCHIVE, "rev08-after-theorize"))


def _ledger_store(run_dir):
    rows = census_mod.read_ledger(run_dir)
    grids, actions, _ = census_mod._observed_transitions(rows)
    return census_mod._LedgerStore(grids, actions)


def _archive_store():
    return _ledger_store(os.path.join(
        ARM, "runs", "20260728T015354Z-g50t-first-contact"))


# --------------------------------------------------- the signal is real
@pytest.mark.skipif(not os.path.isdir(_ARCHIVE),
                    reason="the archived leg is not in this checkout")
def test_an_archived_call_that_moved_a_prediction_is_seen_at_the_call():
    """The whole point: this is knowable when the call returns, not later.

    The window is the frames recorded BEFORE the call, so nothing in this
    verdict depends on the rest of the leg.
    """
    store = _archive_store()
    verdict = inertia_mod.compare_revisions(
        MOVED_PAIR[0], MOVED_PAIR[1], store.actions,
        {"prefix": (0, 5)}, 5)["prefix"]
    assert verdict["verdict"] == inertia_mod.MOVED
    assert verdict["divergent_steps"] > 0
    assert inertia_mod.bought_nothing(verdict["verdict"]) is False


@pytest.mark.skipif(not os.path.isdir(_ARCHIVE),
                    reason="the archived leg is not in this checkout")
def test_an_archived_call_that_bought_nothing_is_seen_at_the_call():
    store = _archive_store()
    verdict = inertia_mod.compare_revisions(
        INERT_PAIR[0], INERT_PAIR[1], store.actions,
        {"prefix": (0, 6)}, 6)["prefix"]
    assert verdict["verdict"] == inertia_mod.INERT
    assert verdict["divergent_steps"] == 0
    assert verdict["first_divergent_step"] is None
    assert inertia_mod.bought_nothing(verdict["verdict"]) is True


@pytest.mark.skipif(not os.path.isdir(_ARCHIVE),
                    reason="the archived leg is not in this checkout")
def test_a_revision_compared_against_itself_is_inert():
    """The negative control for the detector itself.

    A pair of identical directories MUST come back inert. If this ever fails,
    every `moved_a_prediction` in the census is suspect, because the comparison
    is finding differences that are not in the manuals.
    """
    store = _archive_store()
    verdict = inertia_mod.compare_revisions(
        MOVED_PAIR[1], MOVED_PAIR[1], store.actions,
        {"prefix": (0, 5)}, 5)["prefix"]
    assert verdict["verdict"] == inertia_mod.INERT


def test_a_missing_snapshot_is_an_unknown_and_never_an_inert_call(tmp_path):
    """`Books.snapshot` copies only files that exist, and git does not track an
    empty directory, so a cold start's first `before` is simply absent. Reading
    that as "the call bought nothing" would widen a floor on a missing file.
    """
    for pair in ((None, str(tmp_path)), (str(tmp_path), None), (None, None)):
        out = inertia_mod.compare_revisions(pair[0], pair[1], [], {"w": (0, 3)},
                                            3)["w"]
        assert out["verdict"] == inertia_mod.UNPAIRED
        assert inertia_mod.bought_nothing(out["verdict"]) is None


def test_an_empty_window_is_an_unknown_and_costs_no_compile(tmp_path, monkeypatch):
    """A call with no transition behind it cannot be judged, and must not be
    compiled to find that out.
    """
    monkeypatch.setattr(inertia_mod, "compile_snapshot",
                        lambda d: pytest.fail("compiled an empty window"))
    out = inertia_mod.compare_revisions(str(tmp_path), str(tmp_path), [],
                                        {"w": (0, 0)}, 0)["w"]
    assert out["verdict"] == inertia_mod.NO_EVIDENCE
    assert inertia_mod.bought_nothing(out["verdict"]) is None


@pytest.mark.parametrize("before,after,expected", [
    (None, {"initial_state": 1}, inertia_mod.GAINED),
    ({"initial_state": 1}, None, inertia_mod.LOST),
    (None, None, inertia_mod.BLIND),
])
def test_a_revision_that_does_not_compile_is_never_inert(
        tmp_path, monkeypatch, before, after, expected):
    """Gaining or losing a predictor is a change, whatever the frames say."""
    calls = iter([(before, "b"), (after, "a")])
    monkeypatch.setattr(inertia_mod, "compile_snapshot",
                        lambda d: next(calls))
    out = inertia_mod.compare_revisions(str(tmp_path), str(tmp_path),
                                        ["ACTION1", None], {"w": (0, 1)},
                                        1)["w"]
    assert out["verdict"] == expected
    assert inertia_mod.bought_nothing(out["verdict"]) is not True


def test_bought_nothing_is_three_valued():
    assert inertia_mod.bought_nothing(inertia_mod.INERT) is True
    assert inertia_mod.bought_nothing(inertia_mod.MOVED) is False
    for unknown in (None, inertia_mod.UNPAIRED, inertia_mod.BLIND,
                    inertia_mod.NO_EVIDENCE):
        assert inertia_mod.bought_nothing(unknown) is None
    assert set(inertia_mod.VERDICTS) >= {inertia_mod.MOVED, inertia_mod.INERT}


# ------------------------------------------- the default does not listen
def test_the_default_computes_nothing_and_gates_nothing():
    cfg = economy_mod.ActionEconomyConfig()
    assert cfg.inertia == economy_mod.INERTIA_OFF
    assert cfg.min_surprises == 1
    assert cfg.defer_after_inert is False
    assert cfg.gate_every_round is False
    assert cfg.measures_inertia is False
    econ = economy_mod.ActionEconomy(cfg)
    assert econ.gate_continuation(has_manual=True, pending=3,
                                  pending_kinds=("replay_mismatch",)).allow
    assert econ.inertia_log == []


def test_an_enabled_policy_still_does_not_measure_unless_it_asks():
    for name in ("one-round", "floor-8", "floor-12", "actions-unit",
                 "adaptive", "one-round-floor-8", "min-info-2"):
        assert economy_mod.policy(name).measures_inertia is False, name
    for name in ("measure-inertia", "inert-guard", "defer-explained",
                 "defer-explained-every-round", "inert-guard-one-round"):
        assert economy_mod.policy(name).measures_inertia is True, name


@pytest.mark.parametrize("kwargs", [
    {"adapt": economy_mod.ADAPT_BY_PREDICTION_DELTA},
    {"defer_after_inert": True},
])
def test_acting_on_a_signal_that_is_never_computed_raises(kwargs):
    """A policy that silently does nothing is worse than one that will not
    start: in a round's results the first is indistinguishable from an
    intervention that did not work.
    """
    with pytest.raises(ValueError):
        economy_mod.ActionEconomyConfig(enabled=True,
                                        inertia=economy_mod.INERTIA_OFF,
                                        **kwargs)


@pytest.mark.parametrize("kwargs", [{"inertia": "sometimes"},
                                    {"min_surprises": 0}])
def test_a_nonsense_setting_raises(kwargs):
    with pytest.raises(ValueError):
        economy_mod.ActionEconomyConfig(enabled=True, **kwargs)


def test_the_environment_reads_a_false_as_false():
    """`bool("false")` is True, and a switch that reads it that way turns
    itself on when a round tries to turn it off.
    """
    cfg = economy_mod.ActionEconomyConfig.from_env({
        "THEORIA_ACTION_ECONOMY": "1",
        "THEORIA_ECONOMY_INERTIA": "measure",
        "THEORIA_ECONOMY_DEFER_AFTER_INERT": "false"})
    assert cfg.enabled is True
    assert cfg.inertia == economy_mod.INERTIA_MEASURE
    assert cfg.defer_after_inert is False
    on = economy_mod.ActionEconomyConfig.from_env({
        "THEORIA_ACTION_ECONOMY": "1",
        "THEORIA_ECONOMY_INERTIA": "measure",
        "THEORIA_ECONOMY_DEFER_AFTER_INERT": "yes"})
    assert on.defer_after_inert is True
    # Rubbish is dropped, not coerced: the field keeps its default and the
    # config still constructs.
    junk = economy_mod.ActionEconomyConfig.from_env({
        "THEORIA_ACTION_ECONOMY": "1",
        "THEORIA_ECONOMY_DEFER_AFTER_INERT": "perhaps"})
    assert junk.defer_after_inert is False


# ------------------------------------------------------------- the levers
def test_the_prediction_floor_widens_on_inert_and_resets_on_moved():
    econ = economy_mod.ActionEconomy(economy_mod.policy("inert-guard"))
    assert econ.floor == 4
    econ.note_adjudication(manual_moved=True, bought_nothing=True)
    assert econ.floor == 8, "an inert call must widen the floor"
    econ.note_adjudication(manual_moved=True, bought_nothing=True)
    assert econ.floor == 16
    econ.note_adjudication(manual_moved=True, bought_nothing=True)
    assert econ.floor == 16, "adapt_max caps it"
    econ.note_adjudication(manual_moved=False, bought_nothing=False)
    assert econ.floor == 4, "a call that moved a prediction resets it"


def test_the_prediction_floor_ignores_the_text_signal_and_the_unknown():
    """The two are deliberately different signals. `by_prediction_delta` must
    not fall back to the text when the prediction verdict is unknown -- the
    text agreed with the prediction on only 10 of the 23 archived inert calls.
    """
    econ = economy_mod.ActionEconomy(economy_mod.policy("inert-guard"))
    econ.note_adjudication(manual_moved=False, bought_nothing=None)
    assert econ.floor == 4
    econ.note_adjudication(manual_moved=False)
    assert econ.floor == 4


def test_defer_after_inert_refuses_the_same_question_and_nothing_else():
    econ = economy_mod.ActionEconomy(economy_mod.policy("defer-explained"))
    kinds = ("probe_refutation", "replay_mismatch")
    common = dict(has_manual=True, pending=2, new_frames=8, new_actions=8,
                  actions_left=200)
    assert econ.gate(pending_kinds=kinds, **common).allow, "nothing learnt yet"

    econ.note_adjudication(manual_moved=False, bought_nothing=True,
                           pending_kinds=kinds)
    assert not econ.gate(pending_kinds=("replay_mismatch",), **common).allow
    assert not econ.gate(pending_kinds=kinds, **common).allow
    assert econ.gate(pending_kinds=("heuristic_miss",), **common).allow, (
        "a kind the inert call never saw is new information")
    assert econ.gate(pending_kinds=(), **common).allow, (
        "no attributed kind is not the same as a kind already explained")

    econ.note_adjudication(manual_moved=False, bought_nothing=False,
                           pending_kinds=kinds)
    assert econ.gate(pending_kinds=("replay_mismatch",), **common).allow, (
        "a call that moved a prediction clears the guard")


def test_the_guard_lapses_once_enough_new_evidence_has_arrived():
    """Without this bound the guard is a trap, and the archive shows the trap
    springing: nothing clears `_inert_kinds` except a call that fires, so a
    guard that refuses every call is never cleared. On
    `20260728T083400Z-E3-sk48-carried-v2` the unbounded version parks the desk
    for ten consecutive adjudications and the leg stops theorising for good.
    """
    econ = economy_mod.ActionEconomy(economy_mod.policy("defer-explained"))
    econ.note_adjudication(manual_moved=False, bought_nothing=True,
                           pending_kinds=("replay_mismatch",))
    common = dict(has_manual=True, pending=1, actions_left=200,
                  pending_kinds=("replay_mismatch",))
    assert not econ.gate(new_frames=8, new_actions=8, **common).allow
    assert econ.gate(new_frames=16, new_actions=16, **common).allow, (
        "at adapt_max the question is no longer the same question")


def test_defer_after_inert_yields_to_the_end_of_leg_escape():
    """The unnamed historic clause: near the end of a leg the gate stops
    applying, so the arm does not finish holding evidence it never adjudicated.
    Every new clause is subject to it, or a policy could park the desk for the
    last actions of every leg.
    """
    econ = economy_mod.ActionEconomy(economy_mod.policy("defer-explained"))
    econ.note_adjudication(manual_moved=False, bought_nothing=True,
                           pending_kinds=("replay_mismatch",))
    assert econ.gate(has_manual=True, pending=1, new_frames=8, new_actions=8,
                     actions_left=2,
                     pending_kinds=("replay_mismatch",)).allow


def test_the_threshold_is_inert_at_its_historic_value():
    """The negative control for `min_surprises`: at 1 the clause must never
    fire, whatever else is switched on. A knob that changes behaviour at its
    historic setting is not a knob, it is a rewrite.
    """
    econ = economy_mod.ActionEconomy(
        economy_mod.ActionEconomyConfig(enabled=True, min_surprises=1))
    for pending in (0, 1, 5):
        assert econ.gate(has_manual=True, pending=pending, new_frames=99,
                         new_actions=99, actions_left=200).allow


def test_the_threshold_refuses_a_single_surprise_when_asked():
    econ = economy_mod.ActionEconomy(economy_mod.policy("min-info-2"))
    refused = econ.gate(has_manual=True, pending=1, new_frames=99,
                        new_actions=99, actions_left=200)
    assert not refused.allow
    assert "threshold of 2" in refused.reason
    assert econ.gate(has_manual=True, pending=2, new_frames=99,
                     new_actions=99, actions_left=200).allow
    assert econ.gate(has_manual=False, pending=1, new_frames=99,
                     new_actions=99, actions_left=200).allow


def test_the_continuation_round_is_gated_only_when_a_policy_asks():
    """The second adjudication of a turn has never met a gate. That is why 24
    recorded calls had a gap of zero, and it is why the control reproduces the
    record; only `gate_every_round` changes it.
    """
    for name in ("today", "defer-explained", "inert-guard", "floor-12"):
        econ = economy_mod.ActionEconomy(economy_mod.policy(name))
        econ.note_adjudication(manual_moved=False, bought_nothing=True,
                               pending_kinds=("replay_mismatch",))
        assert econ.gate_continuation(
            has_manual=True, pending=1,
            pending_kinds=("replay_mismatch",)).allow, name

    econ = economy_mod.ActionEconomy(
        economy_mod.policy("defer-explained-every-round"))
    econ.note_adjudication(manual_moved=False, bought_nothing=True,
                           pending_kinds=("replay_mismatch",))
    out = econ.gate_continuation(has_manual=True, pending=1,
                                 pending_kinds=("replay_mismatch",))
    assert not out.allow
    assert "stopped repairing" in out.reason
    assert econ.gate_continuation(has_manual=True, pending=1,
                                  pending_kinds=("render_mismatch",)).allow


def test_the_continuation_gate_never_asks_the_floor():
    """A continuation round has no new evidence by construction. Applying the
    floor to it would be `max_rounds_per_turn=1` under a second name, and two
    levers that are secretly one cannot be told apart in a replay.
    """
    econ = economy_mod.ActionEconomy(economy_mod.ActionEconomyConfig(
        enabled=True, min_new=99, gate_every_round=True))
    assert econ.gate_continuation(has_manual=True, pending=1,
                                  pending_kinds=("replay_mismatch",)).allow


# ------------------------------------------------------------- the loop
def _offline_arm(tmp_path, **kwargs):
    import types                                       # noqa: PLC0415

    from inner.loop import TheoriaArm                  # noqa: PLC0415
    run = types.SimpleNamespace(dir=str(tmp_path), run=None, run_id="r-pytest")
    return TheoriaArm(env_base="http://127.0.0.1:1", run=run,
                      game_id="g50t-5849a774", offline=True, **kwargs)


def test_a_default_arm_never_computes_the_signal(tmp_path, monkeypatch):
    monkeypatch.delenv("THEORIA_ACTION_ECONOMY", raising=False)
    arm = _offline_arm(tmp_path)
    monkeypatch.setattr(inertia_mod, "verdict_at_call",
                        lambda *a, **k: pytest.fail("measured by default"))
    assert arm._inertia_at_call({"snapshot_before": {"dir": "x"},
                                 "snapshot_after": {"dir": "y"}}, ()) is None
    assert arm.economy.inertia_log == []
    assert arm.economy.as_json()["inertia"] == []


@pytest.mark.skipif(not os.path.isdir(_ARCHIVE),
                    reason="the archived leg is not in this checkout")
def test_a_measuring_arm_records_the_verdict_and_can_be_read_back(
        tmp_path, monkeypatch):
    """End to end through the loop's own helper, on a real snapshot pair."""
    monkeypatch.delenv("THEORIA_ACTION_ECONOMY", raising=False)
    arm = _offline_arm(tmp_path,
                       action_economy=economy_mod.policy("measure-inertia"))
    store = _archive_store()
    monkeypatch.setattr(arm, "_level_store", lambda: store)
    out = arm._inertia_at_call(
        {"snapshot_before": {"dir": INERT_PAIR[0]},
         "snapshot_after": {"dir": INERT_PAIR[1]}},
        ("replay_mismatch",))
    assert out is True
    row = arm.economy.inertia_log[-1]
    assert row["verdict"] == inertia_mod.INERT
    assert row["pending_kinds"] == ["replay_mismatch"]
    assert json.dumps(arm.economy.as_json())        # serialisable as written


def test_a_measurement_that_raises_is_an_unknown_not_an_inert_call(
        tmp_path, monkeypatch):
    """An instrument failure must not end a leg the desk has been paid for,
    and must not be read as evidence that the call bought nothing.
    """
    monkeypatch.delenv("THEORIA_ACTION_ECONOMY", raising=False)
    arm = _offline_arm(tmp_path,
                       action_economy=economy_mod.policy("inert-guard"))

    def _boom(*a, **k):
        raise RuntimeError("the compiler fell over")

    monkeypatch.setattr(inertia_mod, "verdict_at_call", _boom)
    assert arm._inertia_at_call({"snapshot_before": {"dir": "a"},
                                 "snapshot_after": {"dir": "b"}}, ()) is None
    assert "the compiler fell over" in arm.economy.inertia_log[-1]["error"]
    assert arm.economy.floor == 4, "an unknown must not widen the floor"


def test_the_loop_asks_the_continuation_gate_and_only_when_told_to():
    """A source assertion, in the shape `test_the_run_flag_offers_exactly_the
    _named_policies` already uses in this territory.

    The continuation gate cannot be reached offline -- `rounds` only advances
    after a desk call returns, and the offline loop breaks before that -- so
    the alternative to reading the source is a live call, and this ticket
    spends nothing. What is checked is exactly what a reader would check: the
    call exists, it is guarded on the config, and the verdict feeds
    `note_adjudication` rather than being computed and dropped.
    """
    from inner import loop as loop_mod                 # noqa: PLC0415

    with open(loop_mod.__file__, encoding="utf-8") as fh:
        text = fh.read()
    assert "if rounds and self.economy.config.gate_every_round:" in text
    assert "cont = self.economy.gate_continuation(" in text
    assert "bought_nothing=self._inertia_at_call(report, kinds)" in text
    assert "if not self.economy.config.measures_inertia:" in text
    # And the import is local to the helper, so a default leg never loads it.
    assert "from . import inertia as inertia_mod" in text
    assert "\nfrom .inertia" not in text and "\nimport inertia" not in text


# ------------------------------------------------- the replay, and its control
@pytest.fixture(scope="module")
def shallow_report():
    """A census over the archive without the recompile-and-replay pass.

    Deep enough for the replay's cadence arithmetic, which reads gaps and
    triggers rather than verdicts, and fast enough to sit in a suite.
    """
    return census_mod.census(census_mod.DEFAULT_RUNS, deep=False)


def test_measuring_changes_no_decision(shallow_report):
    """**The negative control for the whole table.** `measure-inertia` computes
    the verdict after every call and acts on none of it, so its replay row must
    equal the control's in every field that describes behaviour. If merely
    measuring moved the numbers, no row below it would mean anything.
    """
    today = census_mod.replay_policy(shallow_report, "today")
    measured = census_mod.replay_policy(shallow_report, "measure-inertia")
    for key in ("adjudications_fired", "adjudications_refused",
                "usd_under_policy", "usd_saved", "actions_covered",
                "actions_per_dollar", "actions_per_dollar_whole_leg"):
        assert measured[key] == today[key], key
    assert ([leg["adjudications_fired"] for leg in measured["legs"]]
            == [leg["adjudications_fired"] for leg in today["legs"]])


def test_the_control_still_reproduces_the_record(shallow_report):
    """Unchanged from A25 and re-asserted here: every policy row is read
    relative to this one, so a control that drifted would move every number in
    the table without moving a single fact.
    """
    today = census_mod.replay_policy(shallow_report, "today")
    recorded = sum(leg["adjudications_recorded"] for leg in today["legs"])
    assert today["adjudications_fired"] == recorded - 2
    assert [leg["leg"] for leg in today["legs"]
            if leg["adjudications_refused"]] == [
        "20260728T015354Z-g50t-first-contact"]


def test_every_policy_replays_and_none_invents_money(shallow_report):
    """No policy may spend a dollar the ledger does not record, and no policy
    may cover an action the leg did not take.
    """
    for name in sorted(economy_mod.POLICIES):
        row = census_mod.replay_policy(shallow_report, name)
        assert row["usd_under_policy"] <= shallow_report["totals"]["usd"] + 1e-6
        assert row["actions_covered"] <= shallow_report["totals"][
            "billed_actions"]
        for leg in row["legs"]:
            assert leg["adjudications_fired"] + leg["adjudications_refused"] \
                == leg["adjudications_recorded"], (name, leg["leg"])


def test_a_leg_is_judged_against_its_own_level_boundary(shallow_report):
    """A25's replay quoted 78 -- g50t level 1 -- for every leg, and a third of
    the archive is sk48, whose level 1 baseline is 61. Each leg's own number is
    in its own ledger.
    """
    by_leg = {leg["leg"]: leg for leg in shallow_report["legs"]}
    g50t = by_leg["20260731T231654Z-R1-g50t-a"]["level_baseline_actions"]
    sk48 = by_leg["20260731T231654Z-R1-sk48-b"]["level_baseline_actions"]
    assert g50t[0] == 78
    assert sk48[0] == 61
    row = census_mod.replay_policy(shallow_report, "today")
    targets = {leg["leg"]: leg["level_1_needs"] for leg in row["legs"]}
    assert targets["20260731T231654Z-R1-sk48-b"] == 61
    assert targets["20260731T231654Z-R1-g50t-a"] == 78


def test_a_shallow_census_cannot_measure_an_inertia_policy_and_says_so(
        shallow_report):
    """The trap this guards: `--shallow` skips the recompile, so every at-call
    verdict is absent, and a policy that reads the signal quietly degrades to
    its floor. Its row then looks like a measured null instead of an
    unmeasured one. The replay publishes the count so the difference is
    visible in the artefact rather than only in the operator's memory.
    """
    row = census_mod.replay_policy(shallow_report, "inert-guard")
    assert row["reads_the_at_call_signal"] is True
    assert row["at_call_verdicts_in_this_census"] == 0
    assert census_mod.replay_policy(
        shallow_report, "today")["reads_the_at_call_signal"] is False


def _synthetic_report(verdicts, steps, kinds):
    """A census-shaped report with the at-call verdicts written by hand.

    Small on purpose. The archive-wide numbers belong in the run's artefacts,
    where they can be regenerated; what a test can pin is the mechanism.
    """
    calls = []
    for i, (verdict, step, kind) in enumerate(zip(verdicts, steps, kinds)):
        calls.append({
            "adjudication_idx": i, "step_idx": step, "cost_usd": 1.0,
            "actions_since_prev_adjudication": 0 if i and step == steps[i - 1]
                                               else 4,
            "frames_since_prev_adjudication": 0 if i and step == steps[i - 1]
                                              else 4,
            "triggers": {k: 1 for k in kind},
            "manual": {"theory_changed": True},
            "downstream": {"verdict": census_mod.DOWNSTREAM_INERT},
            "at_call": {"verdict": verdict},
        })
    return {"legs": [{
        "leg": "synthetic", "game": "g50t-5849a774", "outcome": "budget",
        "levels_completed": 0, "level_baseline_actions": [78],
        "action_ceiling": 300, "carried": True, "adjudications": len(calls),
        "billed_actions": 4 * len(calls), "usd": float(len(calls)),
        "calls": calls}]}


def test_the_lever_that_refuses_nothing_says_where_the_calls_it_wants_are():
    """`defer-explained` refuses nothing on the archive, and that is a fact
    about where the gate is asked rather than about the lever: every call it
    would refuse is a second round of a turn, which the historic gate never
    sees. `gate_every_round` is the version that can reach them, and the
    unreached count is what makes the null readable instead of silent.
    """
    report = _synthetic_report(
        verdicts=[inertia_mod.INERT, inertia_mod.INERT],
        steps=[6, 6],                                  # one turn, two rounds
        kinds=[("replay_mismatch", "probe_refutation"), ("replay_mismatch",)])
    quiet = census_mod.replay_policy(report, "defer-explained")
    loud = census_mod.replay_policy(report, "defer-explained-every-round")
    assert quiet["adjudications_fired"] == 2
    assert quiet["continuation_rounds_the_kind_clauses_would_refuse_if_asked"] \
        == 1
    assert loud["adjudications_fired"] == 1
    assert loud["legs"][0]["refused_on_a_continuation_round"] == 1


def test_a_second_turn_with_a_new_kind_is_not_deferred():
    """The negative control for the guard: it must refuse a repeat of the same
    question, not the next question.
    """
    report = _synthetic_report(
        verdicts=[inertia_mod.INERT, inertia_mod.INERT],
        steps=[6, 6],
        kinds=[("replay_mismatch",), ("render_mismatch",)])
    loud = census_mod.replay_policy(report, "defer-explained-every-round")
    assert loud["adjudications_fired"] == 2


def test_a_productive_call_clears_the_guard_in_the_replay():
    report = _synthetic_report(
        verdicts=[inertia_mod.MOVED, inertia_mod.INERT],
        steps=[6, 6],
        kinds=[("replay_mismatch",), ("replay_mismatch",)])
    loud = census_mod.replay_policy(report, "defer-explained-every-round")
    assert loud["adjudications_fired"] == 2
