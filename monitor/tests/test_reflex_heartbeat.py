"""S44: nothing watched `reflex.log`, so a tick that died before `rlog` was invisible.

`probe_standing` has done exactly this for `standing.log` since S-early. Same
machine, same class of log, one watched and one not -- and the unwatched one is
the loop that reaps sessions, trips the quota breaker, sweeps orphaned claims,
merges delivered branches and redraws the page. On 2026-07-30 it went silent for
131 minutes and the only reason that number is not 72 hours is that a human
happened to be looking.

## The negative controls are the point of this file

A probe that shows a warning on a healthy machine gets switched off, and this
repository has switched probes off before. Two of them therefore matter more
than the positives:

* `test_a_quiet_healthy_machine_reads_green` -- the ordinary case;
* `test_a_busy_healthy_machine_reads_green` -- the case that kills the naive
  probe. Measured on this box, a reflex *cycle* takes ~50 minutes end to end
  (`23:22:27Z / 00:14:11Z / 01:04:34Z / 01:54:33Z` on 2026-07-30/31), because
  `ci_merge` runs a full gate for every flag in the queue and `IgnoreNew` means
  no new tick starts meanwhile. So "last line older than 20 minutes" is the
  *normal* reading of a perfectly healthy busy machine, and a probe keyed on
  that alone would be red most of the day.

And one control in the other direction: `test_the_probe_reads_content_not_mtime`
encodes OPS-M's own retraction
(`inbox/20260729T152000Z-opsm-retraction-reflex-log-mtime-is-not-a-liveness-signal.md`).
`reflex.log` is a **tracked** file; git restamps it on every checkout, merge or
`ff-only` pull, and `ci_merge.main()` ends with one. A probe keyed on mtime
reads "healthy" whenever git has recently walked past, which on this repo is
constantly.
"""

import os
import sys
import time

import pytest

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import scan                                                   # noqa: E402


def _log(tmp_path, age_s, name="reflex.log"):
    """A `reflex.log` whose last completed cycle is `age_s` seconds ago."""
    path = tmp_path / name
    stamp = time.strftime("%Y-%m-%dT%H:%M:%SZ",
                          time.gmtime(time.time() - age_s))
    path.write_text("2026-07-30T00:00:00Z quiet\n%s quiet\n" % stamp,
                    encoding="utf-8")
    return str(path)


def _lock(tmp_path, age_s, pid=4242):
    path = tmp_path / "reflex.lock"
    path.write_text(str(pid), encoding="utf-8")
    when = time.time() - age_s
    os.utime(path, (when, when))
    return str(path)


def _run(tmp_path, *, log_age, lock_age=None, pid=4242, alive=True):
    log = _log(tmp_path, log_age)
    lock = str(tmp_path / "reflex.lock")
    if lock_age is not None:
        lock = _lock(tmp_path, lock_age, pid)
    return scan.probe_reflex_heartbeat(log_path=log, lock_path=lock,
                                       alive=lambda p: alive)


# ------------------------------------------------------------ negative controls

def test_a_quiet_healthy_machine_reads_green(tmp_path):
    """Cycle finished four minutes ago, lock released, next tick not due."""
    r = _run(tmp_path, log_age=240)
    assert r["status"] == "green", r["detail"]


def test_a_busy_healthy_machine_reads_green(tmp_path):
    """The case that would sink a last-line-age-only probe.

    Forty minutes since the last *completed* cycle is normal here: the lock is
    held for the whole cycle and `IgnoreNew` stops any tick from starting while
    it is. The lock is what makes the silence explicable, so the lock is what
    the probe has to consult before it calls silence a fault.
    """
    r = _run(tmp_path, log_age=2400, lock_age=1200, alive=True)
    assert r["status"] == "green", r["detail"]
    assert "一轮正在跑" in r["detail"]


def test_the_boundary_is_not_crossed_one_second_early(tmp_path):
    """Green at exactly the threshold; a probe that fires at the boundary is a
    probe that fires four times an hour on a machine doing nothing wrong."""
    assert _run(tmp_path,
                log_age=scan.REFLEX_IDLE_MAX_S)["status"] == "green"
    assert _run(tmp_path, log_age=2400,
                lock_age=scan.REFLEX_LOCK_STALE_S - 1)["status"] == "green"


def test_green_on_the_live_repository_is_not_asserted_but_the_probe_runs():
    """The probe must not raise against the real tree, whatever it finds there.

    Deliberately not asserting green: at the time of writing `TheoriaReflex` is
    Disabled on this box and the honest reading *is* risk. A test that demanded
    green here would be a test that demands the machine lie.
    """
    r = scan.probe_reflex_heartbeat()
    assert r["status"] in {"green", "risk"}
    assert r["detail"]


# ------------------------------------------------------------ positives

def test_no_lock_and_a_stale_log_is_risk(tmp_path):
    """Nothing running and nothing finished -- the 2026-07-30 shape."""
    r = _run(tmp_path, log_age=45 * 60)
    assert r["status"] == "risk"
    assert "没有一轮在跑" in r["detail"]


def test_a_live_holder_past_the_stale_threshold_is_risk_and_says_why(tmp_path):
    """Scenario A: the takeover that `IgnoreNew` forbids.

    `reflex.py:150-153` frees a lock older than 1500s -- but only a *second*
    reflex process ever executes that branch, and `MultipleInstances: IgnoreNew`
    is precisely what stops a second process from starting. `ExecutionTimeLimit`
    is PT72H, so Windows will not kill the stuck one either. The self-heal
    cannot fire, which is why a probe has to shout instead.
    """
    r = _run(tmp_path, log_age=3000, lock_age=scan.REFLEX_LOCK_STALE_S + 1,
             pid=4242, alive=True)
    assert r["status"] == "risk"
    assert "IgnoreNew" in r["detail"]
    assert "4242" in r["detail"], "the operator needs the pid, not just a colour"


def test_a_dead_holder_is_risk(tmp_path):
    """Crashed before `finally` -- the lock outlives the process."""
    r = _run(tmp_path, log_age=600, lock_age=300, pid=4242, alive=False)
    assert r["status"] == "risk"
    assert "已经死了" in r["detail"]


def test_an_unanswerable_tasklist_is_risk_not_green(tmp_path):
    """`None` from the liveness call means *unknown*, and unknown is not green.

    S28's family: forcing UTF-8 on `tasklist` made a live process read as gone.
    The direction of the mistake was the reassuring one, so "cannot tell" gets
    its own verdict rather than defaulting into either colour.
    """
    log = _log(tmp_path, 600)
    lock = _lock(tmp_path, 300)
    r = scan.probe_reflex_heartbeat(log_path=log, lock_path=lock,
                                    alive=lambda p: None)
    assert r["status"] == "risk"
    assert "问不出" in r["detail"]


def test_a_missing_log_is_risk_not_silence(tmp_path):
    r = scan.probe_reflex_heartbeat(log_path=str(tmp_path / "nope.log"),
                                    lock_path=str(tmp_path / "nolock"))
    assert r["status"] == "risk"


def test_a_log_with_no_parseable_stamp_is_risk(tmp_path):
    path = tmp_path / "reflex.log"
    path.write_text("garbage without a timestamp\n", encoding="utf-8")
    r = scan.probe_reflex_heartbeat(log_path=str(path),
                                    lock_path=str(tmp_path / "nolock"))
    assert r["status"] == "risk"


# ------------------------------------------------------------ the retraction

def test_the_probe_reads_content_not_mtime(tmp_path):
    """A git checkout restamps `reflex.log`; it must not restamp the verdict.

    This is OPS-M's cycle-16 retraction made executable: he recommended an
    mtime clock twice and then measured a 3h18m gap between the file's mtime
    and its last content line, because `ci_merge.main()` ends with a
    `git pull --ff-only` in a live working tree.
    """
    log = _log(tmp_path, 45 * 60)
    os.utime(log, None)                      # git just walked past
    r = scan.probe_reflex_heartbeat(log_path=log,
                                    lock_path=str(tmp_path / "nolock"))
    assert r["status"] == "risk", "mtime was fresh; the last cycle was not"


def test_the_source_never_calls_getmtime_on_the_log():
    """Belt to the previous test's braces: the file itself must not regrow the
    habit. `_reflex_last_tick` is allowed to touch the *lock*'s mtime -- that
    file is untracked and its mtime is its whole meaning -- but never the log's.
    """
    src = open(os.path.join(HERE, "scan.py"), encoding="utf-8").read()
    i = src.index("def _reflex_last_tick(")
    j = src.index("def _accounts_rows()", i)
    body = src[i:j]
    assert "getmtime(log_path)" not in body
    assert body.count("getmtime") == 1, \
        "only the lock's mtime may be read; the log's is git's, not reflex's"


# ------------------------------------------------------------ wiring

def test_the_probe_is_registered():
    """An unregistered probe is a probe that does not run."""
    assert scan.PROBES["reflex_heartbeat"] is scan.probe_reflex_heartbeat


def test_the_thresholds_agree_with_reflex_itself():
    """`REFLEX_LOCK_STALE_S` is copied from `reflex.py`, not chosen again.

    Two numbers for the same fact drift, and the drift shows up as a probe that
    is red inside the window reflex considers healthy -- or, worse, green
    outside it.
    """
    src = open(os.path.join(HERE, "reflex.py"), encoding="utf-8").read()
    assert "< %d:" % scan.REFLEX_LOCK_STALE_S in src or \
           "getmtime(LOCK) < %d" % scan.REFLEX_LOCK_STALE_S in src, \
        "reflex.py's stale-lock threshold moved and scan.py did not follow"


@pytest.mark.parametrize("age", [0, 60, 1200])
def test_the_detail_always_names_a_time(tmp_path, age):
    """Whatever the colour, the line has to say *when* -- a colour with no
    timestamp cannot be acted on, and this probe exists to be acted on."""
    r = _run(tmp_path, log_age=age)
    assert "Z（" in r["detail"]
