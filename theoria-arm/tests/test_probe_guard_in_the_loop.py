"""The three guards, driven through `TheoriaArm._probe_or_explore` itself.

`test_probe_economics.py` checks the measurements in isolation. This file checks
that the loop *acts* on them: a vacuous streak, a repeated experiment, and a run
of probes since the last adjudication each stop the arm from spending another
action on a question it has already asked or cannot answer, and each is recorded
as a finding rather than dropped.

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


PREDICTIONS = {"manual": "aaaaaaaaaaaaaaaa", "inert": "bbbbbbbbbbbbbbbb"}
DESIGN = {"best": {"action": ["key", 5], "entropy_bits": 0.811,
                   "n_classes": 2},
          "n_hypotheses": 2,
          "verdict": "action ('key', 5) splits 2 hypotheses into 2 classes"}


def _arm(tmp_path, monkeypatch):
    run_dir = str(tmp_path)
    os.makedirs(run_dir, exist_ok=True)
    run = types.SimpleNamespace(dir=run_dir, run=None, run_id="r-pytest")
    arm = TheoriaArm(env_base="http://127.0.0.1:1", run=run,
                     game_id="g50t-5849a774", offline=True)

    sent = []

    def _send(action_id, *, probe=False, note=""):
        sent.append({"action": action_id, "probe": probe, "note": note})
        return 200, {"state": "NOT_FINISHED"}, [[[0, 0], [0, 0]]]

    monkeypatch.setattr(arm, "_send", _send)
    monkeypatch.setattr(arm, "_legal_actions", lambda: [1, 2, 3, 4, 5])
    # A namespace of `None` means "no predictor", which is the one branch that
    # never designs a probe. These tests stub the design instead, so the guards
    # are reached with a real `chosen` and a real `predictions` dict.
    monkeypatch.setattr(probe_beat, "design", lambda *a, **k: DESIGN)
    monkeypatch.setattr(
        probe_beat, "build_hypotheses",
        lambda ns: [types.SimpleNamespace(id=name, predict=lambda s, a, _v=value: _v)
                    for name, value in PREDICTIONS.items()])
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
