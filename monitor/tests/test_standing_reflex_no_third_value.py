"""S28 findings 6 and 10: the fleet loop and the reflex had no third value.

Both files answered "how much work is on the board?" and "did that child
succeed?" with a single healthy-looking literal whether or not they had managed
to find out. The two shapes:

* `except Exception: claimable = 0` -- a crashed board query renders as
  "no work to do", which is *quieter than an empty board*, because an empty
  board at least emits `SUPPLY-LOW:0`. And that alarm was itself wrapped in
  `except Exception: pass`.
* `merged = [l for l in r.stdout ...]` with the return code never read -- a
  crashed merger, a merger killed at the 3600s timeout, and a clean no-op are
  one observation: `quiet`.

Every test here comes in a pair. The positive one proves the failure is now
distinguishable; the **negative control** proves the healthy path stayed silent,
because a check that fires always is a check that says nothing. In particular
`test_a_genuinely_empty_board_still_reads_as_zero` is the one that matters most:
the point of the fix is a third value, not a louder second one.
"""

import os
import subprocess
import sys

import pytest

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import board as board_mod          # noqa: E402
import reflex                      # noqa: E402
import standing                    # noqa: E402


class _Boom(RuntimeError):
    """What a half-written item file or a locked directory looks like."""


@pytest.fixture
def crashing_board(monkeypatch):
    def boom(lane=None):
        raise _Boom("simulated board crash")
    monkeypatch.setattr(board_mod, "candidates", boom)
    monkeypatch.setattr(standing.board_mod, "candidates", boom)
    return boom


@pytest.fixture
def quiet_log(monkeypatch):
    """Capture standing.log lines instead of writing the live log file."""
    lines = []
    monkeypatch.setattr(standing, "log", lines.append)
    return lines


# --------------------------------------------------------------------------
# finding 6: standing.work_for
# --------------------------------------------------------------------------

def test_crashed_board_query_is_not_reported_as_an_empty_board(
        crashing_board, quiet_log, monkeypatch):
    monkeypatch.setattr(standing, "unread_count", lambda a: 0)
    monkeypatch.setattr(standing.os, "listdir", lambda p: [])

    w = standing.work_for("RES-9", "infra")

    assert w["claimable"] == standing.CLAIMABLE_UNKNOWN
    assert w["claimable"] != 0, "'could not measure' must not equal 'measured zero'"
    # and it must not masquerade as work either -- -1 is truthy in Python, which
    # is exactly the trap a naive sentinel falls into.
    assert w["any"] is False


def test_the_discarded_exception_is_now_on_the_record(
        crashing_board, quiet_log, monkeypatch):
    monkeypatch.setattr(standing, "unread_count", lambda a: 0)
    monkeypatch.setattr(standing.os, "listdir", lambda p: [])

    standing.work_for("RES-9", "infra")

    assert any("BOARD-QUERY-FAILED" in l for l in quiet_log)
    assert any("_Boom" in l for l in quiet_log), "the exception type must survive"


def test_a_genuinely_empty_board_still_reads_as_zero(quiet_log, monkeypatch):
    """NEGATIVE CONTROL. The fix adds a third value; it must not relabel the
    second one. An empty board is a measurement, and it must still be 0."""
    monkeypatch.setattr(standing, "unread_count", lambda a: 0)
    monkeypatch.setattr(standing.os, "listdir", lambda p: [])
    monkeypatch.setattr(standing.board_mod, "candidates", lambda lane=None: [])

    w = standing.work_for("RES-9", "infra")

    assert w["claimable"] == 0
    assert w["any"] is False
    assert quiet_log == [], "a healthy empty board must log nothing at all"


def test_a_board_with_work_still_reads_as_work(quiet_log, monkeypatch):
    """NEGATIVE CONTROL for the other direction."""
    monkeypatch.setattr(standing, "unread_count", lambda a: 0)
    monkeypatch.setattr(standing.os, "listdir", lambda p: [])
    monkeypatch.setattr(standing.board_mod, "candidates",
                        lambda lane=None: ["a", "b"])

    w = standing.work_for("RES-9", "infra")

    assert w["claimable"] == 2
    assert w["any"] is True
    assert quiet_log == []


def test_the_unknown_sentinel_has_its_own_skip_reason():
    """The sentinel is worthless if every consumer collapses it again. `sweep`
    is the only consumer, and it must not print a claim about the board it just
    failed to read."""
    src = open(os.path.join(HERE, "standing.py"), encoding="utf-8").read()
    i = src.index('why = "BOARD-QUERY-FAILED')
    j = src.index('why = "no work (unread=0 held=0 claimable=0)"')
    assert i < j, "the unknown branch must be tested before the 'no work' branch"


def test_the_skip_reason_survives_a_cp936_console():
    """This repo has crashed on UnicodeEncodeError mid-mutation twice."""
    src = open(os.path.join(HERE, "standing.py"), encoding="utf-8").read()
    line = [l for l in src.splitlines()
            if "claimable unknown, not claiming it is zero" in l][0]
    line.encode("cp936")            # must not raise


# --------------------------------------------------------------------------
# finding 10: reflex's children
# --------------------------------------------------------------------------

def _merge_events(returncode, stdout="", stderr=""):
    """Ask **reflex's own** ci_merge step what it reports for a child result.

    ADV-2/D12: this helper used to be a re-implementation of those eight lines,
    so the two tests below never called `reflex` at all and passed against the
    pre-fix `reflex.py` verbatim -- the fix's only real coverage was a source grep
    for the string `"merge:EXIT-"`. A test that owns a copy of the code under test
    cannot fail when that code changes. `reflex.merge_events` was extracted from
    the loop for exactly this reason; only the synthetic child result is built
    here now.
    """
    class R:
        pass
    r = R()
    r.returncode, r.stdout, r.stderr = returncode, stdout, stderr
    return reflex.merge_events(r)


def test_a_crashed_merger_no_longer_reads_as_a_clean_no_op():
    """Before the fix all three of these produced [] -> logged 'quiet'."""
    clean = _merge_events(0)
    crashed = _merge_events(1, stderr="Traceback (most recent call last):")
    killed = _merge_events(3)

    assert clean == [], "NEGATIVE CONTROL: a clean no-op must stay silent"
    assert crashed != clean
    assert killed != clean
    assert "merge:EXIT-1" in crashed[0]
    assert "merge:EXIT-3" in killed[0]
    assert "Traceback" in crashed[0], "the first stderr line is the diagnosis"


def test_a_successful_merge_is_unchanged():
    """NEGATIVE CONTROL: the happy path's events must be exactly as before."""
    assert _merge_events(0, stdout="MERGED agent/foo\nFLAG agent/bar\n") == [
        "MERGED agent/foo", "FLAG agent/bar"]


def test_the_ci_merge_step_is_not_reimplemented_anywhere(monkeypatch):
    """The guard that keeps ADV-2/D12 from coming back.

    The two tests above are honest about what they cover only as long as they
    call the shipped code. Their pre-fix red is an `AttributeError` -- the fix
    was an *extraction*, so there is no pre-fix symbol to behave differently, and
    this is deliberately **not** claimed as a behavioural negative control. What
    makes them meaningful is that the logic now exists in exactly one place; so
    that is what gets pinned here.

    Driving `reflex.main()` end to end would be the real behavioural test, and it
    is refused on purpose: that tick launches paid sessions.
    """
    # Assembled rather than written out: the first draft of this test put the
    # literal in its own assertion message, so the file matched itself and the
    # check went red on nothing. A source scan that trips over its own text is
    # the false-red twin of this item's disease -- worth one line to avoid.
    needle = 'startswith("' + 'MERGED")'

    src = open(os.path.join(HERE, "reflex.py"), encoding="utf-8").read()
    loop = src[src.index("def main("):]
    assert "merge_events(r)" in loop, (
        "the loop no longer calls merge_events -- the inline copy is back")
    assert needle not in loop, (
        "the ci_merge scrape was re-inlined into the loop; the function and the "
        "loop can now disagree, which is the shape D12 caught")
    assert src.count(needle) == 1, (
        "the scrape appears %d times in reflex.py; it must exist once, in "
        "merge_events" % src.count(needle))

    this_file = open(os.path.abspath(__file__), encoding="utf-8").read()
    assert needle not in this_file, (
        "the test file has its own copy of the code under test again")


def test_the_real_ci_merge_has_no_deliberate_nonzero_exit():
    """The alarm above is only honest if non-zero means "the merger broke".

    ci_merge reports a conflict or a red gate as a FLAG file on stdout, not as
    an exit status. If someone later adds `sys.exit(2)` for "nothing to do",
    this test fails and the alarm must be narrowed instead of crying wolf.
    """
    src = open(os.path.join(HERE, "ci_merge.py"), encoding="utf-8").read()
    assert "sys.exit" not in src


def test_reflex_reads_the_return_code_of_every_child_it_scrapes():
    """The three siblings found alongside finding 10 -- board sweep, the reaper,
    and the git query -- had the identical blind spot: output scraped, status
    dropped. Guard against the pattern coming back by construction."""
    src = open(os.path.join(HERE, "reflex.py"), encoding="utf-8").read()
    for marker in ("sweep:EXIT-", "reap:EXIT-", "revive:GIT-EXIT-",
                   "merge:EXIT-"):
        assert marker in src, "%s guard is missing" % marker
    # `.stdout` taken directly off a run() call is the shape that makes the
    # status unrecoverable rather than merely ignored, so the two sites that
    # did that must no longer.
    assert '"--reap"]).stdout' not in src
    assert '"--format=%(refname:short)"]).stdout' not in src


def test_the_memory_read_is_exempt_and_this_is_why():
    """One `run(...).stdout` remains, and it is deliberately left alone.

    The Win32_OperatingSystem query still takes `.stdout` inline, but it is not
    an instance of this bug: `free_gb` is initialised to 0.0 (fail-closed, the
    direction that spawns *fewer* workers), and a failed powershell yields an
    empty string whose `int()` raises and emits `mem-unreadable`. So the
    failure already has its own third value. It was one of the four the survey
    fixed on the spot -- the old code defaulted to 99 GB and opened the gate.

    This test exists so the exemption is a recorded judgment rather than an
    oversight; if the 0.0 default or the mem-unreadable event ever goes away,
    it fails.
    """
    src = open(os.path.join(HERE, "reflex.py"), encoding="utf-8").read()
    assert "free_gb = 0.0" in src
    assert "mem-unreadable:%s" in src


def test_a_failed_git_query_skips_revival_instead_of_reviving_everyone():
    """The failure direction here spends money.

    An empty `remote` makes every dead session look undelivered, so the loop
    would relaunch sessions that had already finished. The fix must skip the
    loop, not merely log -- so the revive call has to sit under the else.
    """
    src = open(os.path.join(HERE, "reflex.py"), encoding="utf-8").read()
    guard = src.index('events.append("revive:GIT-EXIT-%d(loop-skipped)"')
    tail = src[guard:guard + 2000]
    assert "else:" in tail
    assert tail.index("else:") < tail.index('"--only", pid_str'), (
        "the revive loop must be inside the else branch of the git guard")


def test_supply_unknown_is_distinct_from_supply_low_zero():
    """A broken board used to be quieter than an empty one: SUPPLY-LOW:0 was
    emitted for the empty case and `except: pass` swallowed the broken one."""
    src = open(os.path.join(HERE, "reflex.py"), encoding="utf-8").read()
    assert "SUPPLY-UNKNOWN:" in src
    assert "SUPPLY-LOW:%d" in src, "NEGATIVE CONTROL: the empty case still reports"
    # the bare `except Exception: pass` around the alarm must be gone
    i = src.index("SUPPLY-LOW:%d")
    assert "pass" not in src[i:i + 400].split("except Exception")[-1][:80]


def test_reflex_and_standing_still_import_and_compile():
    """Cheapest possible guard against a patch that breaks the live fleet loop.

    reflex.py and standing.py are running on this machine right now, from the
    main checkout. A syntax error merged into them stops the whole fleet, and
    the fleet is what would have reported it.
    """
    for mod in ("reflex.py", "standing.py"):
        r = subprocess.run([sys.executable, "-m", "py_compile",
                            os.path.join(HERE, mod)],
                           capture_output=True, text=True,
                           encoding="utf-8", errors="replace")
        assert r.returncode == 0, r.stderr


def _drive_sweep(monkeypatch, tmp_path, status):
    """Run `standing.sweep()` with everything but the launch bookkeeping stubbed.

    Returns `(launches, staggers)` -- how many times `via_task` was called, and
    how many 45s staggers were taken. Nothing real is launched and nothing
    sleeps: `via_task` and `time.sleep` are both replaced.
    """
    import dispatch

    launches, staggers = [], []
    monkeypatch.setattr(dispatch, "via_task",
                        lambda a, p: (launches.append(a), status)[1])
    monkeypatch.setattr(standing.time, "sleep", lambda s: staggers.append(s))
    # Every gate ahead of the launch says "go", so the only thing under test is
    # what happens *after* the scheduler has been handed the launch.
    monkeypatch.setattr(standing, "running_tasks", lambda: set())
    monkeypatch.setattr(standing, "quota_held", lambda: False)
    monkeypatch.setattr(standing, "free_gb", lambda: 999.0)
    monkeypatch.setattr(standing, "occupied", lambda a, s: None)
    monkeypatch.setattr(standing, "load_state", lambda: {})
    monkeypatch.setattr(standing, "save_state", lambda s: None)
    monkeypatch.setattr(standing, "log", lambda m: None)
    monkeypatch.setattr(standing, "work_for",
                        lambda a, l: {"unread": 1, "held": 0, "claimable": 1,
                                      "any": True})
    monkeypatch.setattr(standing, "ops_work_for",
                        lambda a: {"unread": 1, "held": 0, "claimable": 1,
                                   "any": True})
    monkeypatch.setattr(standing.board_mod, "heartbeat_age", lambda a: 999)

    standing.sweep()
    return len(launches), len(staggers)


def test_a_launch_the_scheduler_accepted_is_counted_even_if_its_health_is_unknown(
        monkeypatch, tmp_path):
    """ADV-2/D13, and the regression was introduced by this item's own first
    commit: `n_standing += 1` and the 45s stagger were moved inside
    `if ok == "running":` together with `started.append`.

    `schtasks /Run` has already spawned the session by the time the status is
    read, so a *status read* failure -- `state-unknown`, a `/Query` blip giving
    `died-on-arrival(gone)`, or a task that has not flipped to Running inside
    `LAUNCH_SETTLE_S` -- took the standing cap and the stagger off at once. The
    reason for removing the safeties was "I am not sure it is alive"; the effect
    was "launch one more".

    Six at once with no stagger is the configuration `standing.py` blames for the
    05:39 session limit, so this fails in the expensive direction.
    """
    n_agents = len(standing.STANDING_ORDER)
    assert standing.MAX_STANDING < n_agents, (
        "fixture assumes the roster can exceed the cap (%d agents, cap %d)"
        % (n_agents, standing.MAX_STANDING))

    for status in ("state-unknown", "died-on-arrival(Ready)",
                   "died-on-arrival(gone)"):
        launches, staggers = _drive_sweep(monkeypatch, tmp_path, status)

        assert launches <= standing.MAX_STANDING, (
            "status %r launched %d sessions past the cap of %d"
            % (status, launches, standing.MAX_STANDING))
        assert staggers == launches, (
            "status %r took %d staggers for %d launches -- every accepted "
            "launch must be spaced" % (status, staggers, launches))


def test_a_declined_launch_is_not_counted_and_not_staggered(monkeypatch, tmp_path):
    """NEGATIVE CONTROL for the test above, and the reason the predicate is
    `!= "declined"` rather than "always".

    `declined` is the one status that means the scheduler *refused* -- no session
    exists. Charging it against the cap would starve the roster on a broken
    scheduler, and sleeping 45s per refusal would stretch a no-op sweep to
    minutes. If this ever passes by counting declines, the fix has over-corrected
    into the opposite silent failure.
    """
    launches, staggers = _drive_sweep(monkeypatch, tmp_path, "declined")

    assert launches == len(standing.STANDING_ORDER), (
        "a declined launch must not consume the cap: %d attempts for %d agents"
        % (launches, len(standing.STANDING_ORDER)))
    assert staggers == 0, "a refused launch must not stagger (%d)" % staggers


def test_a_running_launch_is_both_counted_and_reported_started(monkeypatch,
                                                               tmp_path):
    """NEGATIVE CONTROL: the healthy path keeps both meanings. `running` must
    still be capped and staggered *and* still be the only status that counts as
    a successful start -- the distinction the first commit was right to draw.
    """
    launches, staggers = _drive_sweep(monkeypatch, tmp_path, "running")

    assert launches == standing.MAX_STANDING, (
        "the cap must still bind on healthy launches: %d" % launches)
    assert staggers == launches, "healthy launches must still stagger"
