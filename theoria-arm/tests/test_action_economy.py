"""A25: the action economy is switchable, and its default is today.

The claim this file has to defend is narrow and total: **with no configuration,
the arm decides exactly what it decided before `inner/economy.py` existed, and
writes exactly the same words into `turns.json` when it decides to wait.** A
cadence change that leaks into a default leg does not merely alter behaviour --
it retro-actively invalidates every leg the A/B is measured against, and it does
so silently, because a leg that theorises slightly less often still looks like a
leg.

So the default is pinned three ways:

* the refusal STRING, character for character, against the literal that was in
  `inner/loop.py` before this ticket (`HISTORIC_SKIP`);
* the DECISION, exhaustively, over the whole grid of inputs the gate can see,
  against a re-implementation of the historic predicate written from the old
  source rather than from the new code;
* the ROUND CAP, against `MAX_THEORIZE_PER_TURN`, which is still the constant
  the rest of the arm imports.

The measurement half is tested separately and for a different reason: the census
in `armtools/action_economy.py` reads ledgers whose shape is fixed history, so
its parsing is testable against synthetic ledgers of exactly that shape. The
three parsers that carry the argument -- invocation grouping, transition
alignment, snapshot pairing -- each have a case here for the irregular input
that actually appears in this repo's archive, because each of those irregular
cases was found by the census disagreeing with the record rather than by
inspection.

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
from inner.loop import (MAX_THEORIZE_PER_TURN,        # noqa: E402
                        MIN_NEW_FRAMES_BETWEEN_THEORIZE)

#: The literal that was in `inner/loop._theorize_and_certify` before A25, with
#: its `%` arguments in their original order. Copied here rather than imported
#: so that this test fails if the string is edited -- importing the new one
#: would only prove the new code agrees with itself.
HISTORIC_SKIP = ("skipped: %d surprise(s) pending but only %d new "
                 "transition(s) since the last call (want %d). Going to "
                 "get more.")


def _historic_gate(has_manual, new_frames, actions_left):
    """The old predicate, transcribed from the pre-A25 source.

    Written out rather than called so that the comparison below is between two
    independent statements of the rule. A helper that both sides call would
    make the test tautological.
    """
    n = MIN_NEW_FRAMES_BETWEEN_THEORIZE
    if has_manual and new_frames < n and actions_left > n:
        return False
    return True


# ------------------------------------------------------- the default is today
def test_the_default_refusal_is_the_historic_string_byte_for_byte():
    econ = economy_mod.ActionEconomy()
    decision = econ.gate(has_manual=True, pending=3, new_frames=2,
                         new_actions=2, actions_left=100)
    assert decision.allow is False
    assert decision.reason == HISTORIC_SKIP % (3, 2,
                                               MIN_NEW_FRAMES_BETWEEN_THEORIZE)


def test_the_default_allows_without_a_reason():
    econ = economy_mod.ActionEconomy()
    decision = econ.gate(has_manual=True, pending=1, new_frames=9,
                         new_actions=9, actions_left=100)
    assert decision.allow is True
    assert decision.reason is None


def test_the_default_decision_matches_the_historic_predicate_everywhere():
    """Every input the gate can see, against the old rule.

    The three clauses interact -- the budget escape switches the floor off
    entirely near the end of a leg -- and an off-by-one in any of them would
    show up on only a handful of the 264 combinations below. Exhaustion is
    cheaper than choosing which handful to guess at.
    """
    econ = economy_mod.ActionEconomy()
    checked = 0
    for has_manual in (True, False):
        for new_frames in range(-1, 11):
            for actions_left in range(0, 11):
                got = econ.gate(has_manual=has_manual, pending=1,
                                new_frames=new_frames,
                                new_actions=new_frames,
                                actions_left=actions_left).allow
                want = _historic_gate(has_manual, new_frames, actions_left)
                assert got is want, (has_manual, new_frames, actions_left)
                checked += 1
    assert checked == 2 * 12 * 11


def test_the_default_round_cap_is_the_historic_constant():
    assert economy_mod.ActionEconomy().rounds_allowed() == MAX_THEORIZE_PER_TURN


def test_the_default_ignores_defer_kinds_and_the_adaptive_floor():
    """Off means off, not "off unless something else is set".

    A config that is disabled but carries knobs is the failure mode this test
    exists for: `enabled=False` must short-circuit before any of them is read,
    or a half-configured environment silently changes a control leg.
    """
    cfg = economy_mod.ActionEconomyConfig(
        enabled=False, min_new=99, unit=economy_mod.UNIT_ACTIONS,
        adapt=economy_mod.ADAPT_BY_MANUAL_DELTA, max_rounds_per_turn=1,
        defer_kinds=("replay_mismatch",))
    econ = economy_mod.ActionEconomy(cfg)
    econ.note_adjudication(manual_moved=False)
    econ.note_adjudication(manual_moved=False)
    assert econ.rounds_allowed() == MAX_THEORIZE_PER_TURN
    decision = econ.gate(has_manual=True, pending=1, new_frames=5,
                         new_actions=0, actions_left=100,
                         pending_kinds=("replay_mismatch",))
    assert decision.allow is True
    assert decision.floor == MIN_NEW_FRAMES_BETWEEN_THEORIZE


def test_the_policy_named_today_is_the_default_config():
    assert economy_mod.policy("today") == economy_mod.ActionEconomyConfig()


# ------------------------------------------------------------- the levers work
def test_one_round_forbids_the_second_adjudication_in_a_turn():
    econ = economy_mod.ActionEconomy(economy_mod.policy("one-round"))
    assert econ.rounds_allowed() == 1


def test_a_wider_floor_refuses_what_the_narrow_one_allowed():
    econ = economy_mod.ActionEconomy(economy_mod.policy("floor-8"))
    assert econ.gate(has_manual=True, pending=1, new_frames=5,
                     new_actions=5, actions_left=100).allow is False
    assert econ.gate(has_manual=True, pending=1, new_frames=8,
                     new_actions=8, actions_left=100).allow is True


def test_the_actions_unit_counts_actions_not_frames():
    """The two units differ exactly where the record says they differ.

    On the two sk48 legs the arm's frame counter advanced on commands that
    returned 400 and moved nothing, so the floor was met by four failures. This
    is that case: four frames, zero actions.
    """
    econ = economy_mod.ActionEconomy(economy_mod.policy("actions-unit"))
    decision = econ.gate(has_manual=True, pending=1, new_frames=4,
                         new_actions=0, actions_left=100)
    assert decision.allow is False
    assert "new actions" in decision.reason
    assert econ.gate(has_manual=True, pending=1, new_frames=0,
                     new_actions=4, actions_left=100).allow is True


def test_the_adaptive_floor_widens_resets_and_is_capped():
    cfg = economy_mod.ActionEconomyConfig(
        enabled=True, adapt=economy_mod.ADAPT_BY_MANUAL_DELTA,
        min_new=4, adapt_factor=2, adapt_max=16)
    econ = economy_mod.ActionEconomy(cfg)
    assert econ.floor == 4
    econ.note_adjudication(manual_moved=False)
    assert econ.floor == 8
    econ.note_adjudication(manual_moved=False)
    assert econ.floor == 16
    econ.note_adjudication(manual_moved=False)
    assert econ.floor == 16                            # capped, not 32
    econ.note_adjudication(manual_moved=True)
    assert econ.floor == 4                             # reset by a real edit


def test_an_unknown_manual_delta_does_not_widen_the_floor():
    """A desk failure is not evidence that the desk had nothing to say."""
    cfg = economy_mod.ActionEconomyConfig(
        enabled=True, adapt=economy_mod.ADAPT_BY_MANUAL_DELTA)
    econ = economy_mod.ActionEconomy(cfg)
    econ.note_adjudication(manual_moved=None)
    econ.note_adjudication(manual_moved=None)
    assert econ.floor == cfg.min_new


def test_defer_kinds_refuses_only_when_every_pending_kind_is_deferrable():
    cfg = economy_mod.ActionEconomyConfig(
        enabled=True, min_new=0, defer_kinds=("probe_refutation",))
    econ = economy_mod.ActionEconomy(cfg)
    assert econ.gate(has_manual=True, pending=2, new_frames=9, new_actions=9,
                     actions_left=100,
                     pending_kinds=("probe_refutation",)).allow is False
    # One non-deferrable kind in the set is enough to open the gate. A
    # `replay_mismatch` is certify saying the manual contradicts the recorded
    # world, and no policy in this module is allowed to sit on one.
    assert econ.gate(has_manual=True, pending=2, new_frames=9, new_actions=9,
                     actions_left=100,
                     pending_kinds=("probe_refutation",
                                    "replay_mismatch")).allow is True


def test_the_shipped_defer_kinds_are_empty():
    """The measurement did not support deferring anything, so nothing is.

    Six of the eight adjudications triggered by `probe_refutation` alone
    changed a later prediction. The knob exists; the list is empty; this test
    is what makes the emptiness deliberate rather than forgotten.
    """
    for name in economy_mod.POLICIES:
        assert economy_mod.policy(name).defer_kinds == ()


# ------------------------------------------------------------------- the switch
def test_from_env_is_a_positive_whitelist():
    assert economy_mod.ActionEconomyConfig.from_env({}).enabled is False
    assert economy_mod.ActionEconomyConfig.from_env(
        {"THEORIA_ACTION_ECONOMY": "0"}).enabled is False
    assert economy_mod.ActionEconomyConfig.from_env(
        {"THEORIA_ACTION_ECONOMY": "yes please"}).enabled is False
    assert economy_mod.ActionEconomyConfig.from_env(
        {"THEORIA_ACTION_ECONOMY": "1"}).enabled is True


def test_from_env_reads_the_knobs_and_ignores_rubbish():
    cfg = economy_mod.ActionEconomyConfig.from_env({
        "THEORIA_ACTION_ECONOMY": "on",
        "THEORIA_ECONOMY_MIN_NEW": "12",
        "THEORIA_ECONOMY_ROUNDS_PER_TURN": "1",
        "THEORIA_ECONOMY_ADAPT_FACTOR": "not-a-number",
    })
    assert (cfg.enabled, cfg.min_new, cfg.max_rounds_per_turn) == (True, 12, 1)
    assert cfg.adapt_factor == economy_mod.ActionEconomyConfig().adapt_factor


def test_an_out_of_range_environment_falls_all_the_way_back():
    """Half a policy is not a policy."""
    cfg = economy_mod.ActionEconomyConfig.from_env({
        "THEORIA_ACTION_ECONOMY": "1",
        "THEORIA_ECONOMY_ROUNDS_PER_TURN": "0",
    })
    assert cfg == economy_mod.ActionEconomyConfig()
    assert cfg.enabled is False


@pytest.mark.parametrize("kwargs", [
    {"unit": "hours"},
    {"adapt": "vibes"},
    {"min_new": -1},
    {"max_rounds_per_turn": 0},
])
def test_a_nonsense_config_raises_rather_than_defaults(kwargs):
    with pytest.raises(ValueError):
        economy_mod.ActionEconomyConfig(**kwargs)


def test_an_unknown_policy_name_raises():
    with pytest.raises(KeyError):
        economy_mod.policy("floor-9000")


# ------------------------------------------------- the census reads the record
def _call(seq, step_idx, label, usd=1.0):
    return {"event": "model_call", "seq": seq, "step_idx": step_idx,
            "ts": "2026-08-01T00:00:%02dZ" % (seq % 60),
            "request": {"beat": "theorize", "label": label},
            "response": {"total_cost_usd": usd}}


def test_repair_rounds_are_grouped_into_the_adjudication_that_spent_them():
    """104 paid calls were 73 adjudications. The difference is this function."""
    groups = census_mod._group_adjudications([
        _call(1, 6, "round1"), _call(2, 6, "round2"), _call(3, 6, "round3"),
        _call(4, 10, "round1"),
        _call(5, 14, "round1"), _call(6, 14, "round2"),
    ])
    assert [len(g) for g in groups] == [3, 1, 2]


def test_two_round_ones_at_the_same_step_are_two_adjudications():
    """`MAX_THEORIZE_PER_TURN = 2` puts two `round1`s at one `step_idx`.

    Recorded on 20260801T001851Z-R1b-sk48-b, ledger seqs 95 and 96. Collapsing
    them would hide the zero-gap call, which is the finding.
    """
    groups = census_mod._group_adjudications([
        _call(95, 6, "round1"), _call(96, 6, "round1"),
        _call(97, 6, "round2"), _call(98, 6, "round3"),
    ])
    assert [len(g) for g in groups] == [1, 3]


def test_an_unlabelled_first_call_still_opens_an_adjudication():
    """The two aborted first-contact legs predate the `round1` label."""
    groups = census_mod._group_adjudications([_call(1, 0, None)])
    assert [len(g) for g in groups] == [1]


def test_transitions_align_the_way_the_replay_reads_them():
    """`actions[t]` is the action taken AT `grids[t]`, and the last is None.

    Getting this backwards shifts every replay by one step and turns an
    agreeing predictor into a diverging one -- which would have inflated the
    "changed a later prediction" count rather than deflating it, so it would
    have looked like good news.
    """
    rows = [
        {"event": "env_step", "seq": 1, "http": {"status": 200},
         "action": {"name": "RESET"}, "frames": [[[0]]]},
        {"event": "env_step", "seq": 2, "http": {"status": 400},
         "action": {"name": "ACTION2"}, "frames": None},
        {"event": "env_step", "seq": 3, "http": {"status": 200},
         "action": {"name": "ACTION2"}, "frames": [[[1]]]},
        {"event": "env_step", "seq": 4, "http": {"status": 200},
         "action": {"name": "ACTION5"}, "frames": [[[2]]]},
    ]
    grids, actions, seqs = census_mod._observed_transitions(rows)
    assert grids == [[[0]], [[1]], [[2]]]
    assert actions == ["ACTION2", "ACTION5", None]
    assert seqs == [1, 3, 4]


def test_a_failed_command_is_not_a_billed_action_and_nor_is_reset():
    ok = {"event": "env_step", "http": {"status": 200},
          "action": {"name": "ACTION2"}}
    reset = {"event": "env_step", "http": {"status": 200},
             "action": {"name": "RESET"}}
    bad = {"event": "env_step", "http": {"status": 400},
           "action": {"name": "ACTION2"}}
    assert census_mod._is_billed_action(ok) is True
    assert census_mod._is_billed_action(reset) is False
    assert census_mod._is_billed_action(bad) is False


def _snapdir(root, name, theory="rule x\n"):
    d = os.path.join(root, name)
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "theory.dsl"), "w", encoding="utf-8",
              newline="\n") as fh:
        fh.write(theory)
    return d


def test_snapshot_records_keep_position_when_a_before_is_missing(tmp_path):
    """An orphan `after` is a record, not a thing to drop.

    `Books.snapshot` copies only files that exist, so a cold start's first
    `before` is an empty directory and git does not track it. Dropping the
    record would shift every later adjudication by one and put each downstream
    verdict against the wrong call.
    """
    snaps = tmp_path / "books" / "snapshots"
    os.makedirs(snaps)
    _snapdir(str(snaps), "rev02-after-theorize")
    _snapdir(str(snaps), "rev03-before-theorize")
    _snapdir(str(snaps), "rev04-after-theorize")
    _snapdir(str(snaps), "rev05-before-theorize")
    records = census_mod._snapshot_adjudications(str(tmp_path))
    assert len(records) == 3
    assert records[0][0] is None                       # the orphan `after`
    assert records[0][1].endswith("rev02-after-theorize")
    assert records[1][0].endswith("rev03-before-theorize")
    assert records[2][1] is None                       # never returned


def test_an_unmoved_manual_is_reported_as_unmoved(tmp_path):
    snaps = tmp_path / "books" / "snapshots"
    os.makedirs(snaps)
    before = _snapdir(str(snaps), "rev01-before-theorize", "same\n")
    after = _snapdir(str(snaps), "rev02-after-theorize", "same\n")
    assert census_mod._dsl_delta(before, after)["theory_changed"] is False
    moved = _snapdir(str(snaps), "rev04-after-theorize", "different\n")
    assert census_mod._dsl_delta(before, moved)["theory_changed"] is True


def test_a_live_round_in_flight_is_skipped_and_named(tmp_path):
    """Absence recorded as absence.

    A round writing into `runs/` while the census reads it would be measured
    half-written. Skipping is right; skipping silently is not -- a reader must
    be able to tell "no such legs existed" from "such legs existed and were not
    read".
    """
    runs = tmp_path / "runs"
    os.makedirs(runs / "20260802T0000Z-A26-long-leg")
    with open(runs / "20260802T0000Z-A26-long-leg" / "ledger.jsonl", "w",
              encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(_call(1, 0, "round1")) + "\n")
    report = census_mod.census(str(runs), deep=False)
    assert report["legs_with_desk_calls"] == 0
    assert [row["leg"] for row in report["skipped"]] == [
        "20260802T0000Z-A26-long-leg"]
    assert "A26" in report["skipped"][0]["why"]


# ------------------------------------------------------- the loop is unchanged
def _offline_arm(tmp_path, **kwargs):
    import types                                       # noqa: PLC0415

    from inner.loop import TheoriaArm                  # noqa: PLC0415
    run = types.SimpleNamespace(dir=str(tmp_path), run=None, run_id="r-pytest")
    return TheoriaArm(env_base="http://127.0.0.1:1", run=run,
                      game_id="g50t-5849a774", offline=True, **kwargs)


def test_an_arm_built_with_no_economy_keyword_has_it_off(tmp_path, monkeypatch):
    """Constructed exactly as `harness/run.py` constructed it before A25.

    No keyword at all, because the defect this guards against is a default that
    moved, and a test that passes the default in explicitly cannot see that.
    """
    monkeypatch.delenv("THEORIA_ACTION_ECONOMY", raising=False)
    arm = _offline_arm(tmp_path)
    assert arm.economy.config.enabled is False
    assert arm.economy.config.min_new == MIN_NEW_FRAMES_BETWEEN_THEORIZE
    assert arm.economy.config.unit == economy_mod.UNIT_FRAMES
    assert arm.economy.rounds_allowed() == MAX_THEORIZE_PER_TURN
    # The other four knobs are still where `test_three_knobs_default_off.py`
    # left them. A fifth knob that switched one of them on while every
    # single-knob test stayed green is exactly the failure that file exists for.
    assert arm.probe_economy.enabled is False
    assert arm.frontier.mode == "ablation"
    assert arm.goal.enabled is False
    assert arm.desk_diet.name == "full"


def test_the_economy_knob_is_independent_of_the_other_four(tmp_path,
                                                           monkeypatch):
    monkeypatch.delenv("THEORIA_ACTION_ECONOMY", raising=False)
    arm = _offline_arm(tmp_path,
                       action_economy=economy_mod.policy("one-round-floor-8"))
    assert arm.economy.config.enabled is True
    assert arm.economy.rounds_allowed() == 1
    assert arm.economy.floor == 8
    assert arm.probe_economy.enabled is False
    assert arm.frontier.mode == "ablation"
    assert arm.goal.enabled is False
    assert arm.desk_diet.name == "full"


def test_the_arm_writes_its_gate_decisions_even_when_the_economy_is_off(
        tmp_path, monkeypatch):
    """A default leg is the thing a switched-on leg is compared against.

    `action_economy.json` is a new file, so writing it unconditionally costs no
    existing artefact a byte -- and a comparison with only one side measured is
    not a comparison.
    """
    monkeypatch.delenv("THEORIA_ACTION_ECONOMY", raising=False)
    arm = _offline_arm(tmp_path)
    decision = arm.economy.gate(has_manual=True, pending=1, new_frames=1,
                                new_actions=1, actions_left=100)
    arm.economy.note_decision(decision, step_idx=3, new_frames=1,
                              new_actions=1, pending=1)
    doc = arm.economy.as_json()
    assert doc["config"]["enabled"] is False
    assert doc["decisions"][0]["allowed"] is False
    assert doc["decisions"][0]["floor"] == MIN_NEW_FRAMES_BETWEEN_THEORIZE
    assert doc["decisions"][0]["unit"] == economy_mod.UNIT_FRAMES
    assert json.dumps(doc, sort_keys=True)             # serialisable as written


def test_the_run_flag_offers_exactly_the_named_policies():
    """`harness/run.py` and `inner/economy.py` cannot drift apart.

    The flag's `choices` is built from `POLICIES` rather than hand-listed, so
    this asserts the two agree. A hand-written list would rot the first time a
    policy is added, and the failure mode is a round unable to select the
    policy it was dispatched to measure -- which looks like a null result.
    """
    from harness import run as run_mod                 # noqa: PLC0415

    with open(run_mod.__file__, encoding="utf-8") as fh:
        text = fh.read()
    assert 'ap.add_argument("--action-economy"' in text
    assert "choices=tuple(sorted(economy_mod.POLICIES))" in text
    assert "economy_mod.policy(args.action_economy)" in text
    # And the policy names are argparse-legal: one with a space in it would be
    # parsed as two arguments and the flag would be unusable.
    for name in economy_mod.POLICIES:
        assert " " not in name and not name.startswith("-")
