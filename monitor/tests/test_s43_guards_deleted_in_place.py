"""S43: the guards 873d62ee deleted, and the two fixes it made that nothing watched.

`1585dd04` installed **seven** silent-failure guards in `reflex.py` and landed
tests alongside them. `873d62ee`, eight hours later, rewrote the same file for an
unrelated and **genuine** bug (the top-up threshold was a total, the crash it was
picked after was a concurrency) and removed all seven on the way past. Seventy-two
commits then landed on top of the resulting red without anything saying a word.

Six of the seven were still missing when S43 opened. The seventh, `merge:EXIT-`,
is on master today **not** because 873d62ee spared it: it was deleted inline like
the rest, and merge commit `7c1dd89b` happened to resolve in favour of the other
parent's extracted `merge_events()` function. It survived by merge resolution,
not by intent -- worth knowing, because it means the count of guards a reader can
see is not the count that was attacked.

The asymmetry that matters is *which* of the seven went red:

* five were watched by `test_standing_reflex_no_third_value.py` -- they went red
  immediately and stayed red, visibly, for 72 commits;
* `BOARD-QUERY-FAILED` and the `scan.py` guard were watched by **nothing**, so
  their deletion produced no signal at all. The scan one then cost a measured
  131 minutes of dead heartbeat on 2026-07-30 (reflex.log silent from 08:32:21Z
  while merge.log kept ticking) -- the 600s timeout propagated out of `main()`,
  `finally` dropped the lock, and no `rlog` line was ever written.

So this file covers the two nobody was watching. It also covers the two fixes
`873d62ee` itself made, which had **zero** tests of their own -- the identical
exposure one round later, and the reason this item forbids reverting it.

One honest qualification, from the adversarial review of this item: of the seven,
only the git-query guard and the scan guard changed what the loop *does*. The
rest changed only what it *says*. That is not a reason to leave them out -- this
whole rig's failures are failures of saying -- but a reader should not come away
thinking six control-flow bugs were fixed here. Two were; five were restorations
of the record.
"""

import os
import subprocess
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import reflex                       # noqa: E402
import standing                     # noqa: E402


class _R:
    """A CompletedProcess stand-in: only `returncode` is read."""

    def __init__(self, returncode):
        self.returncode = returncode


# --------------------------------------------------------------------------
# the guard nobody was watching: scan.py
# --------------------------------------------------------------------------

def test_a_scan_timeout_is_an_event_and_not_a_dead_heartbeat():
    """The failure this file exists for, driven rather than grepped.

    With the catch deleted, `subprocess.TimeoutExpired` left `main()` entirely:
    no event, no `rlog`, no heartbeat -- the 131-minute silence. The point is
    not merely that something is logged; it is that the exception must not
    escape `scan_events` at all.
    """
    def hangs():
        raise subprocess.TimeoutExpired(cmd="scan.py", timeout=600)

    events = reflex.scan_events(hangs)

    assert events, "a hung scan produced no event -- this is the 131-minute bug"
    assert "SCAN FAILED" in events[0]
    assert "timeout" in events[0]


def test_a_crashed_scan_is_distinguishable_from_a_clean_one():
    crashed = reflex.scan_events(lambda: _R(1))
    clean = reflex.scan_events(lambda: _R(0))

    assert clean == [], "NEGATIVE CONTROL: a healthy scan must stay silent"
    assert crashed != clean
    assert "rc=1" in crashed[0]


def test_an_unexpected_exception_is_also_caught_and_named():
    """Not just TimeoutExpired. A scan that raises anything at all used to take
    the cycle down the same way, and the exception *type* is the diagnosis."""
    def boom():
        raise OSError("scan.py is gone")

    events = reflex.scan_events(boom)

    assert events and "OSError" in events[0]


def test_the_scan_step_is_not_reimplemented_in_the_loop():
    """The guard against the shape ADV-2/D12 caught, applied to this extraction.

    The tests above are honest only while the shipped loop calls the same code
    they call. Driving `reflex.main()` end to end would be the real behavioural
    test and is refused on purpose: that tick launches paid sessions.
    """
    src = open(os.path.join(HERE, "reflex.py"), encoding="utf-8").read()
    loop = src[src.index("def main("):]

    assert "scan_events(" in loop, "the loop no longer calls scan_events"
    assert "TimeoutExpired" not in loop, (
        "the scan guard was re-inlined into the loop; the function and the loop "
        "can now disagree, which is the shape D12 caught")
    assert src.count("SCAN FAILED") == 1, (
        "the failure string appears %d times; it must exist once, in "
        "scan_events" % src.count("SCAN FAILED"))


def test_the_scan_failure_string_survives_a_cp936_console():
    """This repo has crashed on UnicodeEncodeError mid-mutation twice, and the
    pre-deletion version of this very string carried a U+2014 em dash."""
    src = open(os.path.join(HERE, "reflex.py"), encoding="utf-8").read()
    i = src.index("SCAN FAILED")
    src[i:i + 300].encode("cp936")          # must not raise


# --------------------------------------------------------------------------
# the other guard nobody was watching: the board query behind the refill gate
# --------------------------------------------------------------------------

def test_a_crashed_board_query_does_not_look_like_an_empty_board_to_refill():
    """`avail` gates the whole worker-refill loop via `if not hold and avail:`.
    Collapsing a crash to 0 skips refill in total silence -- the fleet simply
    stops hiring and nothing anywhere says why."""
    src = open(os.path.join(HERE, "reflex.py"), encoding="utf-8").read()

    assert "BOARD-QUERY-FAILED:%s(refill-skipped)" in src, (
        "the refill board-query guard is missing")
    # the bare `except Exception:` that replaced it must not be back
    i = src.index("claimed = len(board_mod.claimed_map())")
    tail = src[i:i + 300]
    assert "except Exception as exc" in tail, (
        "the exception is being discarded again rather than reported")


# --------------------------------------------------------------------------
# what 873d62ee itself fixed -- untested until now, which is the same exposure
# --------------------------------------------------------------------------

def test_the_two_refill_gates_agree_on_the_same_number():
    """`standing.py` and `reflex.py` both answer "does one more session fit?".

    The night they disagreed, reflex's gate never opened once: reflex.log is a
    run of `worker-hold:low-memory(7.5GB)`, `(7.3GB)`, `(6.7GB)` against a total
    threshold of 8, and the fleet's headcount had to be added by hand. That is
    the bug 873d62ee fixed, and this item forbids reverting it -- so it needs a
    test of its own, or the next in-place rewrite erases it exactly as silently.
    """
    assert reflex.HEADROOM_GB == standing.HEADROOM_GB
    assert reflex.PER_SESSION_GB == standing.PER_SESSION_GB
    assert reflex.MIN_FREE_GB == standing.HEADROOM_GB + standing.PER_SESSION_GB


def test_the_refill_gate_is_reachable_on_a_real_machine():
    """NEGATIVE CONTROL for the pairing above: two files can agree on a number
    that is wrong for both. 8 was a *total*-memory figure picked after a crash
    whose real cause was concurrency, and no spawn ever cleared it."""
    assert reflex.MIN_FREE_GB < 8, (
        "the threshold is back at the total-memory number that never once let a "
        "spawn through")


def test_a_failed_dashboard_restart_does_not_report_success():
    """873d62ee's second undocumented fix, also untested until now.

    The old code appended `serve:restarted` whether or not the port came up, so
    an automatic mechanism that exists solely because "the page dies and nobody
    notices" failed in precisely that way itself.
    """
    src = open(os.path.join(HERE, "reflex.py"), encoding="utf-8").read()

    assert "serve:restart-FAILED" in src, (
        "the failed-restart branch is gone; success and failure write the same "
        "line again")
    assert "serve:spawn-FAILED:%s" in src, (
        "a Popen that raises is unreported again")
    # the probe is what makes the distinction real rather than nominal
    i = src.index("serve:restart-FAILED")
    assert "connect_ex" in src[i - 600:i], (
        "the restart is reported without probing the port, so the two branches "
        "are decided by something other than whether the page is up")


def test_reflex_still_compiles_after_all_of_this():
    """reflex.py is running on this machine right now, from the main checkout."""
    r = subprocess.run([sys.executable, "-m", "py_compile",
                        os.path.join(HERE, "reflex.py")],
                       capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    assert r.returncode == 0, r.stderr
