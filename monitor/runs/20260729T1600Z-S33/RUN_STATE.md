# S33 — master's own monitor gate was red, and the gate could not say why

RES-4, 2026-07-29, branch `agent/s33-monitor-gate-red`, base `bcfc1b93`.

## How it surfaced

I was rescuing three of my own flagged branches. Running the monitor gate on
`agent/s29-triage-the-five-red-gates` gave this:

```
== tests              FAILED(1)
Traceback (most recent call last):
  File "...\monitor\verify.py", line 187, in main
    print(stage["detail"].strip() or "(no output)")
UnicodeEncodeError: 'gbk' codec can't encode character '�' in position 420
```

Two separate defects in one line of output: the suite was red, *and* the gate
died while printing which test was red. The second one hid the first.

## Defect 1 — the pinned survey did not know `papers` gained a suite

Running pytest directly named it:

```
test_gates.py:129: AssertionError: ['papers', 'verify-lab']
assert {'papers', 'verify-lab'} <= {'fleetkit', 'verify-lab'}
```

`P16-uncited-number-gate` merged at 15:02:51Z with `gates: pytest:papers`. That
gave `papers/` a test suite, so `gates.survey()` moved it out of `ungated` and
into `tests_only` — and `test_this_repository_is_where_the_survey_says_it_is`
pins `tests_only` to a named set, deliberately, so that exactly this kind of
movement is noticed.

**It was not my branch. It was master.** Checked out `origin/master` clean in a
throwaway worktree and the same assertion fails there. So from 15:02Z the
monitor territory's merge gate was red for every branch that touched it,
regardless of what the branch did. The log shows the collateral:

```
15:05:53Z FLAG origin/agent/w1661-board-half-tracked: verify gate red in monitor (verify.sh)
15:07:43Z FLAG origin/agent/a3-campaign-devpile: verify gate red in monitor (verify.sh)  [NEEDS-HUMAN: 4 attempts since 04:14:01Z]
```

Neither branch caused it. `a3-campaign-devpile` was pushed to a
NEEDS-HUMAN escalation partly on someone else's defect.

This is the shape this lane exists to catch, with one twist: it did not fail
silently, it failed *loudly at the wrong address*. A gate that reports the
innocent branch is worse than one that says nothing, because the flag is
evidence and it now points somewhere false.

### The fix changed under me, and the second version is the one that matters

My first version was the two-line update the docstring prescribes: move
`papers` out of the `ungated` allowance and into `tests_only`, and drop
`fleetkit` from `tests_only` since S31 had gated it at 14:49:02Z.

Before I could deliver it, master went green on its own. At 15:55:51Z
`agent/s32-close-gate-gap` — another of my branches, waiting in the same queue —
gave `papers` a real `verify.py`, so `papers` skipped `tests_only` entirely and
landed in `gated`. `CONTRACTS` and `browser-ops` were gated in the same window.
The survey on master is now **24 gated, 1 tests-only, 0 ungated**, and
`test_gates.py` passes.

**It passes without having been touched.** The allowances still read
`ungated <= {CONTRACTS, browser-ops, papers}` and
`tests_only <= {verify-lab, fleetkit}` — four names that are all gated now. The
set was never updated; it merely stopped being triggered.

That is worse than the red, and it is the finding this item ends on. The
allowances use `<=`, which only catches a name *arriving*. It cannot catch a
name *coming back*: if someone deletes `papers/verify.py` tomorrow, `papers`
drops into `tests_only` or `ungated`, lands inside an allowance that still lists
it, and the pinned test stays green. Every one of those four territories had
just been given a gate, and the stale allowance was a standing exemption for
exactly the gate it had been given.

So S33 does not add a name. It closes both sets to the truth:

```python
assert set(survey["ungated"]) == set()
assert set(survey["tests_only"]) == {"verify-lab"}
```

Together those two say "every territory except `verify-lab` has a canonical
gate", which is what the docstring has claimed since S13 and what `<=` could
never enforce. A gate being deleted now fails. A new territory arriving without
one now fails. Both failures carry a message saying which territory and what to
do about it.

`S34-papers-owes-a-verify-gate`, which I filed while the first version was still
current, is **already closed by S32** — recorded here rather than quietly
dropped, because a board item that was obsolete when it was written is worth one
line of explanation.

## Defect 2 — the gate crashed while printing its own verdict

`monitor/verify.py` captured stage output with `errors="replace"`, so a child's
mis-decoded bytes arrived as `U+FFFD`. Printing that to a cp936 pipe — which is
what stdout is when `ci_merge` captures the gate — raised `UnicodeEncodeError`
inside the *reporting* loop.

The loop runs on green runs too. So any stage output containing a character the
console codepage cannot represent turns a passing gate into a traceback. Here it
merely destroyed the diagnosis; the general case is a spurious red.

Fixed by hardening the output side rather than the capture side:
`harden_stream()` reconfigures stdout/stderr to UTF-8 with `errors="replace"`
(guarded — not every stream supports `reconfigure`), and every print goes
through an `emit()` that falls back through the stream's own codec and then to
ASCII rather than raising. The exit-code contract is untouched: 0 green, 1 red,
and a crash can never stand in for a verdict.

`monitor/tests/test_verify_output_encoding.py` pins it with six tests driven
against a `TextIOWrapper` whose encoding is hard-coded to `gbk` with
`errors="strict"`, so the test means the same thing on a UTF-8 machine. One of
the six asserts the *fixture still reproduces the bug* against a raw `print`, so
the file cannot go quietly green by no longer triggering it. Verified against
`git show HEAD:monitor/verify.py`: 5 failed / 1 passed before, 6 passed after.

## Found and deliberately not fixed

**The `U+FFFD` is manufactured upstream, in `_tests()`.** It spawns pytest
without pinning the child's `PYTHONIOENCODING`, so on this box the child encodes
cp936 and the parent decodes UTF-8 with `errors="replace"` — every CJK character
in a failing test's source excerpt becomes `U+FFFD`. `ci_merge.py:97` already
pins `PYTHONIOENCODING=utf-8, PYTHONUTF8=1` on its children for exactly this.

I did not copy that here. `PYTHONUTF8=1` changes
`locale.getpreferredencoding(False)` in the child, which is precisely what
`childio._CONSOLE` is resolved from — and `dispatch.py`, `reflex.py`,
`accounts.py` and `standing.py` all decode their own children with it.
`scan.py:1516` carries a written record of this repo losing a day to that exact
interaction. Setting it inside the process that runs the whole monitor suite is
a change that deserves its own item and its own gate run, not a drive-by on a
branch whose job is to un-red master. The printing side is now robust whatever
it is handed, which is the property that actually matters here.

**`monitor/tests/test_verdict_reconcile.py:107` calls `scan.build()` with no
`out_dir`**, so running monitor's own suite rewrites the tracked
`monitor/index.html` and `monitor/state.json` — contradicting `verify.py`'s own
"the gate does not dirty the workspace" docstring. `ci_merge` already tolerates
this ("a gate dirtied the worktree"), which is how it stayed. Separate file,
separate defect, not this item's.

## Result

```
bash monitor/verify.sh   ->  GREEN, exit 0
python -m pytest monitor/tests  ->  197 passed, 2 xfailed
gates: 21 gated, 2 tests-only, 2 UNGATED (CONTRACTS, browser-ops)
```
