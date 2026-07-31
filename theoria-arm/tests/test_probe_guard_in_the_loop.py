"""The guards, driven through `TheoriaArm._probe_or_explore` itself.

`test_probe_economics.py` checks the measurements in isolation. This file checks
that the loop *acts* on them: a vacuous streak, a repeated experiment, and a run
of probes since the last adjudication each stop the arm from spending another
action on a question it has already asked or cannot answer, and each is recorded
as a finding rather than dropped.

The last section checks the same three still bite with `ProbeEconomy` switched
on -- the two halves of this loop's probe policy were written independently and
they meet here, so this is the only place their interaction is visible.
`test_probe_economy.py` checks the economy in isolation.

Offline: no key, no network, no model call. `_send` is replaced with a recorder,
because what is under test is which action the arm *chooses*, not what the world
says back.
"""

import json
import os
import sys
import types

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
ARM = os.path.dirname(HERE)
if ARM not in sys.path:
    sys.path.insert(0, ARM)

import _bootstrap                                     # noqa: E402,F401

from inner import probe as probe_beat                 # noqa: E402
from inner.loop import (MAX_PROBES_BETWEEN_THEORIZE,   # noqa: E402
                        MAX_VACUOUS_PROBES_IN_A_ROW, TheoriaArm)
from inner.probe import ProbeEconomyConfig            # noqa: E402

#: `_send` below always answers with this frame, so this is what the world
#: says back to every probe in this file.
OBSERVED = "fa99b1ac5b3d7708"


PREDICTIONS = {"manual": "aaaaaaaaaaaaaaaa", "inert": "bbbbbbbbbbbbbbbb"}
DESIGN = {"best": {"action": ["key", 5], "entropy_bits": 0.811,
                   "n_classes": 2},
          "n_hypotheses": 2,
          "verdict": "action ('key', 5) splits 2 hypotheses into 2 classes"}


def _arm(tmp_path, monkeypatch, predictions=None, design=None, economy=None):
    run_dir = str(tmp_path)
    os.makedirs(run_dir, exist_ok=True)
    run = types.SimpleNamespace(dir=run_dir, run=None, run_id="r-pytest")
    arm = TheoriaArm(env_base="http://127.0.0.1:1", run=run,
                     game_id="g50t-5849a774", offline=True,
                     probe_economy=economy)
    PREDICTIONS_ = PREDICTIONS if predictions is None else predictions
    DESIGN_ = DESIGN if design is None else design

    sent = []

    def _send(action_id, *, probe=False, note=""):
        sent.append({"action": action_id, "probe": probe, "note": note})
        return 200, {"state": "NOT_FINISHED"}, [[[0, 0], [0, 0]]]

    monkeypatch.setattr(arm, "_send", _send)
    monkeypatch.setattr(arm, "_legal_actions", lambda: [1, 2, 3, 4, 5])
    # A namespace of `None` means "no predictor", which is the one branch that
    # never designs a probe. These tests stub the design instead, so the guards
    # are reached with a real `chosen` and a real `predictions` dict.
    monkeypatch.setattr(probe_beat, "design", lambda *a, **k: DESIGN_)
    monkeypatch.setattr(
        probe_beat, "build_hypotheses",
        lambda ns: [types.SimpleNamespace(id=name, predict=lambda s, a, _v=value: _v)
                    for name, value in PREDICTIONS_.items()])
    return arm, sent


def _namespace():
    """Enough of a compiled manual for `_roll_forward` to return something."""
    return {"initial_state": lambda: {"t": 0},
            "step": lambda state, action: {"t": state["t"] + 1},
            "render": lambda state: [[0, 0], [0, 0]],
            "RULES": []}


def _probe_rows(arm):
    path = os.path.join(arm.dir, "probes.jsonl")
    if not os.path.exists(path):
        return []
    return [json.loads(line) for line in open(path, encoding="utf-8")]


# =========================================================================

def test_a_probe_is_spent_while_nothing_is_wrong(tmp_path, monkeypatch):
    arm, sent = _arm(tmp_path, monkeypatch)
    record = {}
    arm._probe_or_explore(_namespace(), record)

    assert record["probe"]["kind"] == "probe"
    assert sent[-1]["probe"] is True
    assert arm._probes_since_theorize == 1


def test_a_vacuous_streak_at_the_cap_stops_the_next_probe(tmp_path, monkeypatch):
    """r3's shape: after three answers that matched no hypothesis, the fourth
    probe is refused and the action goes to exploration instead."""
    arm, sent = _arm(tmp_path, monkeypatch)
    arm.probes.vacuous_streak = MAX_VACUOUS_PROBES_IN_A_ROW

    record = {}
    arm._probe_or_explore(_namespace(), record)

    assert record["probe"]["kind"] == "exploration"
    assert "empty posterior" in record["probe"]["why"]
    assert "0.0 bits" in record["probe"]["why"]
    assert sent[-1]["probe"] is False
    assert arm._probes_since_theorize == 0, "a refused probe is not a probe"


def test_the_refusal_is_written_to_probes_jsonl_not_dropped(tmp_path,
                                                            monkeypatch):
    """cold-start-a2's P-3: a probe quietly dropped is a lie."""
    arm, _sent = _arm(tmp_path, monkeypatch)
    arm.probes.vacuous_streak = MAX_VACUOUS_PROBES_IN_A_ROW
    arm._probe_or_explore(_namespace(), {})

    rows = _probe_rows(arm)
    assert len(rows) == 1
    assert rows[0]["phase"] == "unrunnable"
    assert "empty posterior" in rows[0]["reason"]
    assert rows[0]["design"] == DESIGN, (
        "the design that was refused must travel with the refusal")


def test_below_the_cap_the_probe_still_runs(tmp_path, monkeypatch):
    arm, sent = _arm(tmp_path, monkeypatch)
    arm.probes.vacuous_streak = MAX_VACUOUS_PROBES_IN_A_ROW - 1
    record = {}
    arm._probe_or_explore(_namespace(), record)
    assert record["probe"]["kind"] == "probe"
    assert sent[-1]["probe"] is True


def test_the_same_experiment_is_not_bought_twice(tmp_path, monkeypatch):
    """r3 ran P-25 and P-27 as identical designs, and P-26 and P-28 likewise.

    With the design stubbed constant, the second call is exactly that repeat.
    """
    arm, sent = _arm(tmp_path, monkeypatch)

    first = {}
    arm._probe_or_explore(_namespace(), first)
    assert first["probe"]["kind"] == "probe"

    second = {}
    arm._probe_or_explore(_namespace(), second)
    assert second["probe"]["kind"] == "exploration"
    assert "same experiment as P-01" in second["probe"]["why"]
    assert sent[-1]["probe"] is False


def test_exploration_after_a_refusal_takes_the_least_tried_action(
        tmp_path, monkeypatch):
    """The guard's whole point.

    `20260731T1500Z-A3-sk48-carried-l1` spent its last fourteen actions
    alternating ACTION4/ACTION3 and kept landing back in states it had already
    visited, because the frontier nominated the same pair every time. Falling
    through to the least-tried legal action is what breaks that.
    """
    arm, sent = _arm(tmp_path, monkeypatch)
    arm.probes.vacuous_streak = MAX_VACUOUS_PROBES_IN_A_ROW
    arm.action_counts = {1: 7, 2: 7, 3: 7, 4: 7, 5: 0}

    record = {}
    arm._probe_or_explore(_namespace(), record)
    assert record["probe"]["action"] == 5
    assert sent[-1]["action"] == 5


def test_the_probe_run_between_two_adjudications_is_capped(tmp_path,
                                                            monkeypatch):
    arm, sent = _arm(tmp_path, monkeypatch)
    arm._probes_since_theorize = MAX_PROBES_BETWEEN_THEORIZE

    record = {}
    arm._probe_or_explore(_namespace(), record)
    assert record["probe"]["kind"] == "exploration"
    assert "since the last adjudication" in record["probe"]["why"]


def test_the_caps_are_the_documented_numbers():
    assert MAX_VACUOUS_PROBES_IN_A_ROW == 3
    assert MAX_PROBES_BETWEEN_THEORIZE == 4


def test_the_refutation_payload_carries_shape_not_a_table_of_hashes(
        tmp_path, monkeypatch):
    """What the desk is sent about a refutation.

    The old payload embedded `predictions` in full -- up to 24 opaque 16-hex
    grid hashes -- into a prompt that already ran to 100k characters on r3,
    once per pending surprise. A hash cannot be read, compared or reasoned
    from; the counts and the bits can.
    """
    arm, _sent = _arm(tmp_path, monkeypatch)
    arm._probe_or_explore(_namespace(), {})

    fired = [s for s in arm.register.items if s.kind == "probe_refutation"]
    assert len(fired) == 1
    payload = fired[0].payload
    assert "predictions" not in payload, "the hash table must not be resent"
    for key in ("n_hypotheses", "n_survivors", "information_gain_bits",
                "expected_bits", "frontier_vacuous", "vacuous_streak"):
        assert key in payload, key
    assert payload["frontier_vacuous"] is True
    assert payload["information_gain_bits"] == 0.0
    assert payload["expected_bits"] == pytest.approx(0.811)


def test_a_theorize_round_rearms_both_probe_counters(tmp_path, monkeypatch):
    """The frontier is a function of the manual. Once the manual is
    adjudicated the hypothesis set is different, so the caps must start over --
    otherwise the guard would silently end probing for the rest of the run."""
    arm, _sent = _arm(tmp_path, monkeypatch)
    arm._probes_since_theorize = MAX_PROBES_BETWEEN_THEORIZE
    arm.probes.vacuous_streak = MAX_VACUOUS_PROBES_IN_A_ROW + 5

    # The two lines `_theorize_and_certify` runs after a successful round.
    arm._probes_since_theorize = 0
    arm.probes.vacuous_streak = 0

    record = {}
    arm._probe_or_explore(_namespace(), record)
    assert record["probe"]["kind"] == "probe"


# =========================================================================
# ... and the same three, with `ProbeEconomy` switched on
# =========================================================================
#
# The economy retires refuted hypotheses so the next design is over a smaller
# frontier. That is the half of the policy that changes what the arm reasons
# over -- and it is exactly the half that can quietly disable the other, since
# `fingerprint` names an experiment by hashing what every hypothesis predicted.
# Hash a shrinking frontier and the same experiment gets a new name each time
# the theory narrows.

#: manual and `without_x` predict one thing, `inert` predicts what the world
#: will actually say. So the first probe lands ON the frontier, `without_x` is
#: refuted and retired, and the second design sees a frontier of two.
SHRINKING = {"manual": "aaaaaaaaaaaaaaaa", "inert": OBSERVED,
             "without_x": "aaaaaaaaaaaaaaaa"}
SHRINKING_DESIGN = dict(DESIGN, n_hypotheses=3)


def _on(tmp_path, monkeypatch):
    return _arm(tmp_path, monkeypatch, predictions=SHRINKING,
                design=SHRINKING_DESIGN,
                economy=ProbeEconomyConfig(enabled=True))


def test_the_economy_actually_shrinks_the_frontier_in_the_loop(tmp_path,
                                                               monkeypatch):
    """The framework change, seen through the loop rather than in isolation."""
    arm, _sent = _on(tmp_path, monkeypatch)
    arm._probe_or_explore(_namespace(), {})

    assert arm.probe_economy.retired == {"without_x"}, arm.probe_economy.retired
    rows = _probe_rows(arm)
    assert rows[0]["predictions"] == SHRINKING, "the first probe saw all three"
    assert rows[-1]["survived"] == ["inert"]


def test_the_repeat_guard_still_bites_after_the_frontier_has_shrunk(
        tmp_path, monkeypatch):
    """The interaction that would have gone unnoticed.

    Second turn, same stubbed design and same stubbed state -- so it is the
    same experiment. But `without_x` has been retired, so the *scored* frontier
    is two hypotheses where the first probe had three. The refusal has to
    survive that, and it only does because the loop fingerprints the unfiltered
    prediction set. Replaying the four live legs both ways put a number on the
    alternative: 9 repeats caught instead of 15.
    """
    arm, sent = _on(tmp_path, monkeypatch)
    first = {}
    arm._probe_or_explore(_namespace(), first)
    assert first["probe"]["kind"] == "probe"

    second = {}
    arm._probe_or_explore(_namespace(), second)
    assert second["probe"]["kind"] == "exploration", second["probe"]
    assert "same experiment as P-01" in second["probe"]["why"]
    assert sent[-1]["probe"] is False


def test_the_scored_frontier_is_the_live_one_not_the_fingerprinted_one(
        tmp_path, monkeypatch):
    """The other side of the same coin: identity is the full set, but what
    `survived` is measured over is the frontier still standing."""
    arm, _sent = _on(tmp_path, monkeypatch)
    arm._probe_or_explore(_namespace(), {})
    arm.probe_economy.retired = {"without_x"}
    arm.probes.asked.clear()               # let a second probe through

    arm._probe_or_explore(_namespace(), {})
    designs = [r for r in _probe_rows(arm) if r["phase"] == "design"]
    assert set(designs[-1]["predictions"]) == {"manual", "inert"}
    assert designs[-1]["fingerprint"] == designs[0]["fingerprint"], (
        "the same experiment keeps its name across a frontier change")


def test_a_vacuous_streak_still_stops_the_probe_with_the_economy_on(
        tmp_path, monkeypatch):
    arm, sent = _on(tmp_path, monkeypatch)
    arm.probes.vacuous_streak = MAX_VACUOUS_PROBES_IN_A_ROW
    record = {}
    arm._probe_or_explore(_namespace(), record)
    assert record["probe"]["kind"] == "exploration"
    assert "empty posterior" in record["probe"]["why"]
    assert sent[-1]["probe"] is False


def test_the_cap_still_stops_the_probe_with_the_economy_on(tmp_path,
                                                           monkeypatch):
    arm, _sent = _on(tmp_path, monkeypatch)
    arm._probes_since_theorize = MAX_PROBES_BETWEEN_THEORIZE
    record = {}
    arm._probe_or_explore(_namespace(), record)
    assert record["probe"]["kind"] == "exploration"
    assert "since the last adjudication" in record["probe"]["why"]


def test_the_audit_trail_records_every_refusal_whichever_half_made_it(
        tmp_path, monkeypatch):
    """`probe_economy.json` is the run's account of its own probe policy, so a
    refusal the loop made must appear there beside one the economy made -- one
    row per designed probe, and never "allowed" about an action never sent."""
    arm, _sent = _on(tmp_path, monkeypatch)
    arm._probe_or_explore(_namespace(), {})            # allowed
    arm._probe_or_explore(_namespace(), {})            # refused: repeat

    decisions = arm.probe_economy.decisions
    assert len(decisions) == 2, decisions
    assert decisions[0]["allowed"] is True and decisions[0]["reason"] == ""
    assert decisions[1]["allowed"] is False
    assert "same experiment as P-01" in decisions[1]["reason"]
    blob = arm.probe_economy.as_json()
    assert (blob["probes_allowed"], blob["probes_refused"]) == (1, 1)


def test_the_economys_own_refusal_is_written_as_a_finding_too(tmp_path,
                                                              monkeypatch):
    """A collapsed frontier is the economy's refusal, not the loop's, and it
    has to reach `probes.jsonl` by the same road."""
    collapsed = dict(DESIGN, n_hypotheses=1)
    arm, sent = _arm(tmp_path, monkeypatch, design=collapsed,
                     economy=ProbeEconomyConfig(enabled=True))
    record = {}
    arm._probe_or_explore(_namespace(), record)

    assert record["probe"]["kind"] == "exploration"
    assert "collapsed" in record["probe"]["why"]
    assert sent[-1]["probe"] is False
    rows = _probe_rows(arm)
    assert rows[0]["phase"] == "unrunnable" and "collapsed" in rows[0]["reason"]
    assert arm.probe_economy.decisions[0]["allowed"] is False


def test_with_the_economy_off_the_frontier_never_moves(tmp_path, monkeypatch):
    """The default leg. Same stubs, switch off.

    The retirement is still *recorded* -- that is the counterfactual the A/B
    round reads out of `probe_economy.json` -- but nothing is filtered, so the
    second design sees all three hypotheses, and the repeat guard catches it on
    exactly the same evidence it would have with the change on.
    """
    arm, _sent = _arm(tmp_path, monkeypatch, predictions=SHRINKING,
                      design=SHRINKING_DESIGN)
    assert arm.probe_economy.enabled is False
    arm._probe_or_explore(_namespace(), {})
    assert arm.probe_economy.retired == {"without_x"}, "noted, not applied"
    assert [h.id for h in arm.probe_economy.filter_hypotheses(
        probe_beat.build_hypotheses(None))] == list(SHRINKING)

    second = {}
    arm._probe_or_explore(_namespace(), second)
    assert second["probe"]["kind"] == "exploration"
    assert "same experiment as P-01" in second["probe"]["why"]
