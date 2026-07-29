"""The circuit breaker's exit, tested end to end without a human in it.

The hold was a one-way latch: `check` set `mode=hold` and nothing ever called
`resume`, so a session-limit at 09:35 kept six workers frozen past its own
20:20 reset until somebody noticed. The exits exist now. What did not exist is
a test that walks the whole chain, and a state machine whose exit is only ever
exercised by an outage is a state machine whose exit is untested.

So each test here is one transition, and the two that matter most assert
something *absent*: that no human step was required, and that the exit did not
spend more than it was allowed to. The second is not decoration -- the first
version of the auto-exit pinged on every five-minute tick, and a ping is a paid
call made during the outage it is waiting on.

Nothing here touches the network. `claude` is never on PATH in this suite: the
one function that would call it is stubbed, and a test that forgot to stub it
fails on `shutil.which` returning None rather than quietly spending money.
"""

import datetime
import importlib
import json
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

import quota                                                    # noqa: E402


@pytest.fixture
def q(tmp_path, monkeypatch):
    """`quota` with its state file redirected into a tmpdir."""
    monkeypatch.setattr(quota, "STATE", str(tmp_path / "quota_state.json"))
    return quota


def stub_ping(monkeypatch, answer):
    """Replace the paid call with a fixed answer, keeping the bookkeeping.

    Counts attempts, because "how many times did the exit ask" is the thing the
    throttle is about and the only way to see it is to count.
    """
    calls = []

    class Proc:
        returncode = 0 if answer == "OPEN" else 1
        stdout = "ok" if answer == "OPEN" else ""
        stderr = "" if answer == "OPEN" else "You've hit your session limit"

    def fake_run(args, **kwargs):
        calls.append(args)
        return Proc()

    import shutil
    monkeypatch.setattr(quota.subprocess, "run", fake_run)
    monkeypatch.setattr(shutil, "which", lambda name: "claude")
    return calls


def held(q, **extra):
    """A state file mid-hold, as `check` would have left it."""
    st = {"mode": "hold", "requeue": [], "history": [],
          "detected_at": "2026-07-28T09:35:00Z",
          "reset_hint": "You've hit your session limit · resets 8:20pm "
                        "(Asia/Shanghai)"}
    st.update(extra)
    quota.save_state(st)
    return st


# -- the full chain, which is the thing that was missing ---------------------

def test_hold_to_window_reopen_to_auto_exit_needs_no_human(q, monkeypatch):
    """The whole incident, in one test, run forwards.

    09:35 a session limit holds the fleet. The provider's own hint says the
    window reopens at 20:20. Nothing but `check` runs -- no operator, no
    `resume`, no ping. At 20:21 the hold must be over.
    """
    held(q)
    monkeypatch.setattr(quota, "load", _registry_empty(quota))

    # Before the deadline: still held, and `check` says so on every tick.
    _frozen_now(monkeypatch, "2026-07-28T12:00:00Z")
    assert quota.check() == 2
    assert json.load(open(quota.STATE, encoding="utf-8"))["mode"] == "hold"

    # After it: the latch opens by itself, and says which fact opened it.
    _frozen_now(monkeypatch, "2026-07-28T12:21:00Z")   # 20:21 Shanghai
    assert quota.check() == 0
    st = json.load(open(quota.STATE, encoding="utf-8"))
    assert st["mode"] == "normal"
    assert st["auto_released_at"]
    assert "reopened" in st["note"]


def test_the_deadline_exit_does_not_need_the_window_to_answer(q, monkeypatch):
    """The exit that cannot be blocked by the outage it is waiting on.

    `resume` asks the window a question, so the outage can hold that exit shut
    -- and so can something unrelated, since a ping needs the `claude` CLI on
    PATH. The deadline exit reads the provider's own stated reset time and
    needs nothing else, which is why it is the one that ends a normal hold.
    Here `subprocess.run` is not stubbed at all: any attempt to ping is a hard
    error, and the test passes only because nothing tries.
    """
    held(q)
    monkeypatch.setattr(quota, "load", _registry_empty(quota))
    _frozen_now(monkeypatch, "2026-07-28T12:21:00Z")

    def explode(*a, **k):
        raise AssertionError("the deadline exit must not spend a call")
    monkeypatch.setattr(quota.subprocess, "run", explode)

    assert quota.check() == 0
    assert json.load(open(quota.STATE, encoding="utf-8"))["mode"] == "normal"


# -- the throttle: the exit costs money, and it costs it during an outage ----

def test_an_automatic_ping_is_capped_at_one_per_twenty_minutes(q, monkeypatch):
    """The reflex tick is five minutes. Unthrottled, a hold from 09:35 to
    12:45 buys ~37 haiku calls where the work order allowed 9 -- the breaker
    spending the very quota it is waiting to get back."""
    held(q)
    calls = stub_ping(monkeypatch, "CLOSED")

    _frozen_now(monkeypatch, "2026-07-28T10:00:00Z")
    assert quota.ping(if_due=True) == 2               # no record yet: allowed
    assert len(calls) == 1

    for minute in ("10:05", "10:10", "10:15", "10:19"):
        _frozen_now(monkeypatch, "2026-07-28T%s:00Z" % minute)
        assert quota.ping(if_due=True) == 3           # 3 = not due, nothing spent
    assert len(calls) == 1, "throttled pings must not reach the provider"

    _frozen_now(monkeypatch, "2026-07-28T10:20:00Z")
    assert quota.ping(if_due=True) == 2
    assert len(calls) == 2                            # exactly one per 20 min


def test_a_closed_window_still_records_the_attempt(q, monkeypatch):
    """Recording only successes would mean no throttle exactly while the
    window is shut, which is the only time the throttle matters."""
    held(q)
    stub_ping(monkeypatch, "CLOSED")
    _frozen_now(monkeypatch, "2026-07-28T10:00:00Z")
    quota.ping(if_due=True)
    st = json.load(open(quota.STATE, encoding="utf-8"))
    assert st["last_ping_at"] == "2026-07-28T10:00:00Z"
    assert st["last_ping_result"] == "CLOSED"


def test_a_person_who_types_ping_gets_an_answer(q, monkeypatch):
    """The throttle exists to stop an unattended five-minute loop, not to argue
    with whoever is standing there."""
    held(q, last_ping_at="2026-07-28T10:00:00Z", last_ping_result="CLOSED")
    calls = stub_ping(monkeypatch, "CLOSED")
    _frozen_now(monkeypatch, "2026-07-28T10:01:00Z")
    assert quota.ping() == 2                          # bare ping: not gated
    assert len(calls) == 1


def test_the_exit_does_not_buy_the_same_answer_twice(q, monkeypatch):
    """reflex pings, then calls `resume`, which used to ping again -- two paid
    calls seconds apart, during the outage the calls are waiting on."""
    held(q, last_ping_at="2026-07-28T10:00:00Z", last_ping_result="OPEN")
    calls = stub_ping(monkeypatch, "OPEN")
    _frozen_now(monkeypatch, "2026-07-28T10:00:30Z")

    assert quota.resume() == 0
    assert calls == [], "a fresh OPEN is evidence; re-buying it is not diligence"
    assert json.load(open(quota.STATE, encoding="utf-8"))["mode"] == "normal"


def test_a_stale_open_is_re_asked(q, monkeypatch):
    """"Fresh" has to mean something. Past the throttle window the answer is
    bought again, because an OPEN from an hour ago is not evidence about now."""
    held(q, last_ping_at="2026-07-28T09:00:00Z", last_ping_result="OPEN")
    calls = stub_ping(monkeypatch, "OPEN")
    _frozen_now(monkeypatch, "2026-07-28T10:00:00Z")
    assert quota.resume() == 0
    assert len(calls) == 1


def test_a_fresh_closed_never_short_circuits_the_exit_open(q, monkeypatch):
    """The direction that must not be symmetric. Reusing a recent CLOSED to
    skip the ping would be fine for cost and wrong for correctness: it would
    keep the fleet held on stale evidence, which is the original bug."""
    held(q, requeue=["P-8"],
         last_ping_at="2026-07-28T10:00:00Z", last_ping_result="CLOSED")
    calls = stub_ping(monkeypatch, "OPEN")            # the window reopened since
    _frozen_now(monkeypatch, "2026-07-28T10:01:00Z")

    launched = []
    real_run = quota.subprocess.run                    # the OPEN stub

    def spy(args, **kwargs):
        if any("dispatch.py" in str(a) for a in args):
            launched.append(args)

            class Ok:
                returncode = 0
                stdout = stderr = ""
            return Ok()
        return real_run(args, **kwargs)
    monkeypatch.setattr(quota.subprocess, "run", spy)
    monkeypatch.setattr(quota.time, "sleep", lambda s: None)

    assert quota.resume(stagger=0) == 0
    assert len(calls) == 1, "a stale CLOSED must be re-asked, not believed"
    assert launched, "the requeued worker must actually be relaunched"


# -- transitions with a queue ----------------------------------------------

def test_resume_relaunches_in_priority_order_and_half_the_pool(q, monkeypatch):
    """(2) of the work order. The order is not cosmetic: the integration gate
    goes first because everything else merges through it."""
    held(q, requeue=["B-1", "P-8", "M-0", "P-20", "R-1", "A-1"],
         last_ping_at="2026-07-28T10:00:00Z", last_ping_result="OPEN")
    stub_ping(monkeypatch, "OPEN")
    _frozen_now(monkeypatch, "2026-07-28T10:00:30Z")

    launched = []

    def spy(args, **kwargs):
        if any("dispatch.py" in str(a) for a in args):
            launched.append(args[args.index("--only") + 1])

        class Ok:
            returncode = 0
            stdout = stderr = ""
        return Ok()
    monkeypatch.setattr(quota.subprocess, "run", spy)
    monkeypatch.setattr(quota.time, "sleep", lambda s: None)

    assert quota.resume(stagger=0) == 0
    assert launched == ["M-0", "P-8", "P-20"]          # priority order, half pool
    st = json.load(open(quota.STATE, encoding="utf-8"))
    assert st["mode"] == "recovering"
    assert st["requeue"] == ["R-1", "A-1", "B-1"]      # the rest, still ordered


def test_an_empty_queue_is_not_a_reason_to_stay_held(q, monkeypatch):
    """The second half of the original latch: `resume` returned early on an
    empty queue and never touched `mode`, so even a hand-run resume left the
    fleet frozen."""
    held(q, requeue=[], last_ping_at="2026-07-28T10:00:00Z",
         last_ping_result="OPEN")
    stub_ping(monkeypatch, "OPEN")
    _frozen_now(monkeypatch, "2026-07-28T10:00:30Z")
    assert quota.resume() == 0
    assert json.load(open(quota.STATE, encoding="utf-8"))["mode"] == "normal"


# -- helpers ----------------------------------------------------------------

def _frozen_now(monkeypatch, stamp):
    """Pin both clocks `quota` reads. They have to agree, or a test can pass
    against a state the code can never be in."""
    when = datetime.datetime.strptime(stamp, "%Y-%m-%dT%H:%M:%SZ").replace(
        tzinfo=datetime.timezone.utc)

    class FrozenDatetime(datetime.datetime):
        @classmethod
        def now(cls, tz=None):
            return when if tz else when.replace(tzinfo=None)

    monkeypatch.setattr(quota.datetime, "datetime", FrozenDatetime)
    monkeypatch.setattr(quota, "now_utc", lambda: stamp)
    return lambda _: None


def _registry_empty(mod):
    """`check` reads the dispatch registry and then the state file. Only the
    registry needs faking; the state file is already redirected."""
    real = mod.load

    def load(path, default):
        if path.endswith("registry.json"):
            return {}
        return real(path, default)
    return load
