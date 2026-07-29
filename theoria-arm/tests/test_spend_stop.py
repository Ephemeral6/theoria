"""闸门红了立刻停 — a refused pool ends the leg, it does not get retried.

This file exists because of a measured failure rather than a hypothesis. On
2026-07-29 a live leg on `g50t` sent **780 commands for 9 successful actions**
(HTTP amplification 86.7 against the 1.75 its reservation was sized on) and
exhausted its 105-request action cap. Nothing was overspent -- the gate held --
but the arm spun against a closed gate until its wall clock ran out, and wrote
an 81 MB `candidates.jsonl` doing it.

The mechanism: a refusal raises inside the env proxy's request handler, so the
arm sees a *transport failure* rather than a status, and `_retryable(0)` is True
by design (a dropped socket usually is worth retrying). Every refused command
was therefore retried up to `ACTION_ATTEMPTS = 40` times.

The board item's red line -- "闸门红了立刻停" -- turned out to be implemented
nowhere. These tests are that red line.
"""

import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
ARM = os.path.dirname(HERE)
if ARM not in sys.path:
    sys.path.insert(0, ARM)

import _bootstrap                                      # noqa: E402,F401

from harness.arc import (ACTION_ATTEMPTS, ArcThroughProxy,  # noqa: E402
                         SpendGateStopped)
from harness.budget import Budget                      # noqa: E402

GAME = "g50t-5849a774"


class _Tripped:
    """A claim that refuses, the way `SpendBinding` does once it has latched."""

    def __init__(self, exc=None):
        self.asked = 0
        self.exc = exc or RuntimeError("POOL_ACTION_CEILING")

    def check_action(self, n=1):
        self.asked += 1
        raise self.exc


class _Open:
    def __init__(self):
        self.asked = 0

    def check_action(self, n=1):
        self.asked += 1


def _arc(binding, budget=None):
    arc = ArcThroughProxy("http://127.0.0.1:1", GAME,
                          budget or Budget(actions=40, commands=2000),
                          sleep=lambda _s: None, spend_binding=binding)
    # Any real socket would be a bug in these tests, not a slow test.
    arc._post = lambda path, body: pytest.fail(
        "a refused claim must not open a socket")
    return arc


def test_a_refused_claim_stops_before_the_first_socket():
    binding = _Tripped()
    arc = _arc(binding)
    with pytest.raises(SpendGateStopped) as caught:
        arc.act(1)
    assert "stops here rather than retrying" in str(caught.value)
    assert binding.asked == 1, (
        "asked once and stopped: the trip is latched, so asking again buys "
        "nothing")
    assert arc.budget.commands_sent == 0, (
        "no command may be counted against a claim that refused it")


def test_a_refusal_is_not_worth_forty_attempts():
    """The whole defect in one assertion. Before the fix a refusal reached
    `_post`, came back as a transport failure, and `_retryable(-1)` sent it
    round again -- forty times per command."""
    binding = _Tripped()
    arc = _arc(binding)
    with pytest.raises(SpendGateStopped):
        arc.act(1)
    assert binding.asked < ACTION_ATTEMPTS
    assert len(arc.attempt_log) == 0


def test_reset_stops_too():
    """RESET has its own forty-attempt envelope, and `_try_advance_level`
    sends one *after* a WIN -- exactly when a leg is likeliest to be near its
    ceiling."""
    binding = _Tripped()
    arc = _arc(binding)
    with pytest.raises(SpendGateStopped):
        arc.reset()
    assert arc.budget.commands_sent == 0


def test_an_unavailable_gate_is_terminal_too_not_just_a_tripped_one():
    """`SpendGateUnavailable` is not a budget problem -- it means the gate
    cannot do its job. `proxy/SPEND_GATE.md` is explicit that the rule is fail
    closed: never work around it, never spend uncounted."""
    class Unavailable(RuntimeError):
        pass

    arc = _arc(_Tripped(Unavailable("the pool lock could not be taken")))
    with pytest.raises(SpendGateStopped) as caught:
        arc.act(2)
    assert "Unavailable" in str(caught.value)


def test_an_open_claim_is_asked_before_every_attempt_and_costs_nothing():
    """The check has to be cheap enough to ask before each attempt, because
    the ceiling can be reached *during* a retry envelope -- which is precisely
    what happened on the leg that motivated this file."""
    binding = _Open()
    arc = ArcThroughProxy("http://127.0.0.1:1", GAME,
                          Budget(actions=40, commands=2000),
                          sleep=lambda _s: None, spend_binding=binding)
    calls = {"n": 0}

    def fake_post(path, body):
        calls["n"] += 1
        # Two transient 400 waves, then success: the envelope does its job.
        if calls["n"] < 3:
            return 400, {"message": "game %s not found" % GAME}
        return 200, {"frame": [[[0]]], "state": "NOT_FINISHED",
                     "available_actions": [1], "levels_completed": 0}

    arc._post = fake_post
    status, _ = arc.act(1)
    assert status == 200
    assert calls["n"] == 3
    assert binding.asked == 3, "asked before each attempt, not once per command"


def test_no_binding_means_no_gate_and_no_crash():
    """Offline runs and the whole existing test suite construct the client
    without a claim. That must stay legal."""
    arc = ArcThroughProxy("http://127.0.0.1:1", GAME,
                          Budget(actions=40, commands=2000),
                          sleep=lambda _s: None)
    assert arc.spend_binding is None
    arc._post = lambda path, body: (200, {"frame": [[[0]]],
                                          "state": "NOT_FINISHED",
                                          "available_actions": [1],
                                          "levels_completed": 0})
    status, _ = arc.act(1)
    assert status == 200
