"""The other state machines in the loop, audited for the same defect shape.

S12 asked, after the quota breaker was fixed: what else has an entry and no
exit? Three answers, and only one of them is clean.

* **`reflex.lock`** has two exits -- `finally: os.remove` and a staleness
  window -- and they are independent, which is the property the quota hold
  lacked. But the window is shorter than the work it guards; see below.
* **`death_counts`** (the three-strikes rule) has an entry and no exit at all.
* **Board claims** are swept every tick, but only for `W-*` workers. For
  `APP-*` and `RES-*` there is no sweep, deliberately -- their liveness is not
  visible in the task table. It is still a door only its own claimant can open,
  and that has already cost one incident.

The two defects are recorded as `xfail(strict=True)` rather than as prose: they
are true statements about the code that currently fail, so they stay quiet
today and go loud the moment somebody fixes the underlying thing and forgets to
delete the marker. Neither is fixed here -- S12 says to list them, and the
`monitor/` loop is live.
"""

import ast
import os

import pytest

MONITOR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REFLEX = os.path.join(MONITOR, "reflex.py")


def _tree():
    return ast.parse(open(REFLEX, encoding="utf-8").read())


def _assigned_number(name):
    for node in ast.walk(_tree()):
        if (isinstance(node, ast.Assign)
                and any(isinstance(t, ast.Name) and t.id == name
                        for t in node.targets)
                and isinstance(node.value, ast.Constant)):
            return node.value.value
    return None


def _timeouts():
    """Every `timeout=` the reflex loop passes, keyed by what it is calling."""
    found = {}
    for node in ast.walk(_tree()):
        if not isinstance(node, ast.Call):
            continue
        seconds = next((kw.value.value for kw in node.keywords
                        if kw.arg == "timeout"
                        and isinstance(kw.value, ast.Constant)), None)
        if seconds is None:
            continue
        names = [n.value for n in ast.walk(node)
                 if isinstance(n, ast.Constant) and isinstance(n.value, str)
                 and n.value.endswith(".py")]
        found[names[0] if names else "line %d" % node.lineno] = seconds
    return found


def test_the_lock_has_an_exit_that_does_not_depend_on_a_clean_shutdown():
    """The good case, pinned so it stays good.

    A lock removed only in `finally` is lost forever if the process is killed
    outright -- which is exactly how the sessions in this fleet die. The
    staleness window is the second, independent exit.
    """
    source = open(REFLEX, encoding="utf-8").read()
    assert "finally:" in source and "os.remove(LOCK)" in source
    assert "getmtime(LOCK)" in source, "no staleness exit on the reflex lock"


@pytest.mark.xfail(strict=True, reason=(
    "KNOWN DEFECT (S12 audit): the lock's staleness window is shorter than the "
    "work it guards, so a slow tick outlives its own lock and a second reflex "
    "starts beside it. Delete this marker when the window is raised above the "
    "loop's own timeouts, or the lock is refreshed as the tick proceeds."))
def test_the_lock_window_outlasts_the_longest_thing_the_loop_does():
    window = 1500
    source = open(REFLEX, encoding="utf-8").read()
    assert "< %d" % window in source, "the staleness window moved; re-read this"
    longest = max(_timeouts().values())
    assert window > longest, (
        "reflex.lock goes stale after %ds but the loop can legitimately run "
        "for %ds (%s). A tick that takes longer than its own lock is a tick "
        "with no lock." % (window, longest, _timeouts()))


@pytest.mark.xfail(strict=True, reason=(
    "KNOWN DEFECT (S12 audit): `death_counts` only ever increments. A session "
    "benched by three transient deaths -- a quota outage counts -- never comes "
    "back without someone hand-editing loop_state.json. Delete this marker "
    "when a decay, a reset on success, or an explicit un-bench exists."))
def test_the_three_strikes_counter_can_come_back_down():
    source = open(REFLEX, encoding="utf-8").read()
    assert _assigned_number("MAX_DEATHS"), "MAX_DEATHS moved; re-read this"
    lowered = any(marker in source for marker in (
        "deaths.pop(", "death_counts.pop(", "deaths[pid_str] = 0",
        "death_counts\"] = {}", "deaths.clear()"))
    assert lowered, (
        "nothing in reflex.py ever lowers a death count: the three-strikes "
        "rule is an entry with no exit, the same shape as the quota hold that "
        "froze the fleet")


def test_board_claims_are_swept_every_tick():
    """The claim sweep exists and runs unconditionally -- not behind the hold.

    A worker killed by the quota leaves its claim hanging, so the very outage
    that needs the board freed is the one that would stop it being freed.
    """
    tree = _tree()
    sweeps = [node for node in ast.walk(tree)
              if isinstance(node, ast.Call)
              and any(isinstance(n, ast.Constant) and n.value == "sweep"
                      for n in ast.walk(node))]
    assert sweeps, "reflex never sweeps orphaned board claims"

    for node in ast.walk(tree):
        if isinstance(node, ast.If) and any(
                isinstance(n, ast.Name) and n.id == "hold"
                for n in ast.walk(node.test)):
            assert not any(s in ast.walk(node) for s in sweeps), (
                "the claim sweep is behind the quota hold: an outage would "
                "leave its own victims' claims locked")
