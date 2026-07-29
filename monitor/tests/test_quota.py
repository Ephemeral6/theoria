"""Every transition of the quota breaker, and every way it must refuse to move.

The breaker froze the fleet for most of a day (OPS-M cycle 5). A session-limit
at 09:35 set `mode=hold`; the limit's own text said the window reopened at
20:20; the fleet was still held long after. Two holes in one state machine:
nothing ever called `resume`, and `resume` returned early on an empty queue
**without clearing the mode**. Neither hole is exotic. Both are the same shape:
a state with an entry and no exit.

So each transition below is tested twice -- once that it happens, and once that
it does *not* happen when its precondition is absent. A test that only checks
the happy direction cannot tell a working exit from one that fires
unconditionally, and an exit that fires unconditionally is how a breaker stops
being a breaker.

    cd monitor && python -m pytest tests
"""

import ast
import datetime
import os

import pytest

import quota


def ago(hours):
    return (datetime.datetime.now(datetime.timezone.utc)
            - datetime.timedelta(hours=hours)).strftime("%Y-%m-%dT%H:%M:%SZ")


LIMIT_LINE = "You've hit your session limit · resets 8:20pm"


# ------------------------------------------------------------ normal -> hold
def test_a_limit_signature_flips_normal_to_hold(rig):
    rig.write_state()
    rig.dead_session("P-8", "working...\n%s\n" % LIMIT_LINE)

    assert quota.check() == 2

    st = rig.read_state()
    assert st["mode"] == "hold"
    assert st["requeue"] == ["P-8"]
    assert "session limit" in st["reset_hint"]
    assert st["history"][-1]["killed"] == ["P-8"]


def test_a_dead_session_without_a_limit_signature_does_not_hold(rig):
    """The negative sample. A session dies for a hundred reasons and only one
    of them is the quota; holding on any death would freeze the fleet whenever
    a single run crashed."""
    rig.write_state()
    rig.dead_session("P-8", "Traceback (most recent call last)\nKeyError: 3\n")

    assert quota.check() == 0
    assert rig.read_state()["mode"] == "normal"
    assert rig.read_state()["requeue"] == []


def test_a_session_that_pushed_its_branch_is_not_a_quota_kill(rig):
    """It finished. A limit line in the log of a session whose work landed is
    history, not a live outage."""
    rig.write_state()
    rig.dead_session("P-8", LIMIT_LINE, pushed=True)

    assert quota.check() == 0
    assert rig.read_state()["mode"] == "normal"


def test_a_session_already_requeued_is_not_counted_twice(rig):
    rig.write_state(mode="hold", requeue=["P-8"])
    rig.registry({"P-8": {"pid": 1, "log": "P-8.log",
                          "reaped": "quota-requeued"}})
    rig.log("P-8.log", LIMIT_LINE)
    rig.write_state(mode="hold", requeue=["P-8"], detected_at=ago(1),
                    reset_hint=LIMIT_LINE)

    quota.check()
    assert rig.read_state()["requeue"] == ["P-8"]


# ------------------------------------- hold -> normal, on the deadline alone
def test_the_hold_expires_when_the_window_it_named_has_reopened(rig):
    """The exit that the outage itself cannot hold shut.

    `resume`'s exit asks the window a question, so an outage -- or merely a
    missing `claude` binary -- can keep it closed. The provider's own reset
    time does not depend on anything working.
    """
    rig.write_state(mode="hold", requeue=[], detected_at=ago(24),
                    reset_hint=LIMIT_LINE)
    rig.registry({})

    assert quota.check() == 0

    st = rig.read_state()
    assert st["mode"] == "normal"
    assert st["auto_released_at"]
    assert "reopened" in st["note"]


def test_the_hold_does_not_expire_before_its_deadline(rig):
    """The negative sample. A deadline that fires early is not a deadline; it
    would lift the hold straight back into the outage that caused it."""
    rig.write_state(mode="hold", requeue=[], detected_at=quota.now_utc(),
                    reset_hint="resets in a while")
    rig.registry({})

    assert quota.check() == 2

    st = rig.read_state()
    assert st["mode"] == "hold"
    assert "auto_released_at" not in st
    assert st["reopen_at"], "a hold must always publish when it expects to end"


def test_an_unreadable_reset_hint_still_bounds_the_hold(rig):
    """No parsable time is not a licence to hold forever -- `MAX_HOLD_HOURS`
    is the backstop, and it has to be reachable."""
    rig.write_state(mode="hold", requeue=[],
                    detected_at=ago(quota.MAX_HOLD_HOURS + 1),
                    reset_hint="something went wrong")
    rig.registry({})

    assert quota.check() == 0
    assert rig.read_state()["mode"] == "normal"


def test_a_hold_that_expired_but_still_has_a_queue_says_so(rig):
    """`check` may lift the mode; it may never spawn a session. The queue has
    to survive the lift, or the sessions the outage killed are simply lost."""
    rig.write_state(mode="hold", requeue=["P-8", "M-0"], detected_at=ago(24),
                    reset_hint=LIMIT_LINE)
    rig.registry({})

    assert quota.check() == 0

    st = rig.read_state()
    assert st["mode"] == "normal"
    assert st["requeue"] == ["P-8", "M-0"], "the requeue must not be dropped"


def test_reopen_at_never_runs_past_the_cap(rig):
    """A hint reading further out than the cap has more likely been misread
    than not: the window this breaker exists for is five hours."""
    st = {"detected_at": ago(0), "reset_hint": "resets 11pm (Pacific/Kiritimati)"}
    due = quota.reopen_at(st)
    detected = quota.parse_stamp(st["detected_at"])
    assert due <= detected + datetime.timedelta(hours=quota.MAX_HOLD_HOURS)


def test_a_hold_with_no_detected_at_is_not_left_unbounded(rig):
    """`reopen_at` returns None when it cannot date the hold, and `check` then
    has no deadline to fire. That is a real gap and it is pinned here so it
    cannot be widened silently: the hold survives, and `resume` is its only
    exit. Recorded in the run's RUN_STATE as the one hold shape that still
    depends on `ping`.
    """
    rig.write_state(mode="hold", requeue=[], reset_hint=LIMIT_LINE)
    rig.registry({})

    assert quota.check() == 2
    st = rig.read_state()
    assert st["mode"] == "hold"
    assert st["reopen_at"] is None


# ---------------------------------- hold -> normal, on an empty queue + ping
def test_an_empty_queue_with_an_open_window_clears_the_hold(rig):
    """The OPS-M cycle 5 bug, pinned.

    This branch used to `print("nothing to resume."); return 0` and leave
    `mode=hold` untouched. Every tick called it, every tick it did nothing, and
    the fleet stayed frozen with an empty queue and an open window.
    """
    rig.write_state(mode="hold", requeue=[])
    rig.window(True)

    assert quota.resume() == 0

    st = rig.read_state()
    assert st["mode"] == "normal"
    assert st["resumed_at"]


def test_an_empty_queue_with_a_closed_window_stays_held(rig):
    """The negative sample. If this passed too, the exit would be
    unconditional and the breaker would lift itself mid-outage."""
    rig.write_state(mode="hold", requeue=[])
    rig.window(False)

    assert quota.resume() == 0
    assert rig.read_state()["mode"] == "hold"


def test_resume_does_not_ping_when_there_is_nothing_to_do(rig):
    """A breaker already in `normal` with an empty queue must not spend a call
    to discover it has nothing to do -- every tick would buy one."""
    rig.write_state(mode="normal", requeue=[])
    calls = rig.window(True)

    assert quota.resume() == 0
    assert calls == [], "resume pinged with nothing to resume"


# ------------------------------- hold -> recovering -> normal, with a queue
def test_a_queue_relaunches_in_priority_order_and_lands_in_recovering(rig):
    rig.write_state(mode="hold", requeue=["B-1", "P-8", "M-0", "P-20"])
    rig.window(True)
    spawned = rig.no_dispatch()

    assert quota.resume(stagger=0) == 0

    st = rig.read_state()
    assert st["mode"] == "recovering", "a partial relaunch is not a full one"
    assert st["requeue"] == ["B-1"], "the tail must stay queued"

    launched = [c[-1] for c in spawned]
    assert launched == ["M-0", "P-8", "P-20"]
    assert launched == sorted(launched, key=quota.PRIORITY.index)


def test_recovering_becomes_normal_once_the_queue_drains(rig):
    rig.write_state(mode="recovering", requeue=["B-1"])
    rig.window(True)
    rig.no_dispatch()

    assert quota.resume(stagger=0) == 0

    st = rig.read_state()
    assert st["mode"] == "normal"
    assert st["requeue"] == []


def test_a_closed_window_relaunches_nothing_and_holds(rig):
    """The negative sample for the whole relaunch path: no session may be
    spawned into an outage."""
    rig.write_state(mode="hold", requeue=["P-8", "M-0"])
    rig.window(False)
    spawned = rig.no_dispatch()

    assert quota.resume(stagger=0) == 2

    st = rig.read_state()
    assert st["mode"] == "hold"
    assert st["requeue"] == ["P-8", "M-0"]
    assert spawned == [], "a session was launched while the window was closed"


# --------------------------------------------------- zero-token work is exempt
def _reflex_source():
    path = os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), "reflex.py")
    return path, ast.parse(open(path, encoding="utf-8").read())


def test_ci_merge_is_not_gated_on_the_quota_hold():
    """A merge spends zero tokens, so a token budget must not be able to stop it.

    Checked structurally rather than by running the reflex loop: the question
    is whether the call sits inside a branch that depends on `hold`, and that
    is a fact about the tree. A worker's proposal caught this being blocked by
    a budget it cannot possibly consume.
    """
    path, tree = _reflex_source()

    def mentions_hold(node):
        return any(isinstance(n, ast.Name) and n.id == "hold"
                   for n in ast.walk(node))

    def calls_ci_merge(node):
        return any(isinstance(n, ast.Constant) and isinstance(n.value, str)
                   and "ci_merge.py" in n.value for n in ast.walk(node))

    assert calls_ci_merge(tree), "no ci_merge.py call in %s at all" % path

    for node in ast.walk(tree):
        if isinstance(node, ast.If) and mentions_hold(node.test):
            assert not calls_ci_merge(node), (
                "ci_merge is inside a branch that tests `hold` (line %d): a "
                "zero-token step must not be stoppable by a token budget"
                % node.lineno)


def test_the_hold_gate_still_guards_the_things_that_do_spend(reflex_dispatch=None):
    """The other half: exempting the merge must not have exempted dispatch.

    If nothing is left under the hold gate, the breaker holds nothing.
    """
    path, tree = _reflex_source()
    guarded = []
    for node in ast.walk(tree):
        if not (isinstance(node, ast.If)
                and any(isinstance(n, ast.Name) and n.id == "hold"
                        for n in ast.walk(node.test))):
            continue
        for inner in ast.walk(node):
            if isinstance(inner, ast.Constant) and isinstance(inner.value, str):
                if "dispatch.py" in inner.value or "worker" in inner.value.lower():
                    guarded.append(node.lineno)
    assert guarded, (
        "nothing that spends tokens is under the hold gate in %s -- the "
        "breaker would hold nothing" % path)


# ------------------------------------------------------------- the exits exist
@pytest.mark.parametrize("scenario", ["deadline", "ping"])
def test_a_hold_has_at_least_two_independent_exits(rig, scenario):
    """The property the outage violated, stated directly.

    One exit is not enough when that exit can be held shut by the thing it is
    waiting on. These two share no dependency: the deadline needs only a clock,
    the ping needs only the API.
    """
    if scenario == "deadline":
        rig.write_state(mode="hold", requeue=[], detected_at=ago(24),
                        reset_hint=LIMIT_LINE)
        rig.registry({})
        quota.check()
    else:
        rig.write_state(mode="hold", requeue=[])
        rig.window(True)
        quota.resume()
    assert rig.read_state()["mode"] == "normal"
