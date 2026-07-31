# OPS-M34 arm: the three `test_standing_reflex_no_third_value.py` failures on `origin/master` (8a5a83f9)

Investigated in a detached worktree at 8a5a83f9
(`.worktrees/opsm34-standing`, removed on completion). Main tree untouched.

## Verdict

The three failures do **not** share a cause. They split 2 / 1:

| test | verdict |
|---|---|
| `test_a_running_launch_is_both_counted_and_reported_started` | **C — environment-dependent** |
| `test_a_declined_launch_is_not_counted_and_not_staggered` | **C — environment-dependent** |
| `test_the_ci_merge_step_is_not_reimplemented_anywhere` | **A — the code is wrong** |

The named test (`...running_launch...`, `0 == 5`) is **C**. The hypothesis about
954eb44c's pause switch is confirmed, and the switch is a **tracked file**, so the
suite's result is a function of live fleet state that happens to be committed.

---

## C: the two sweep tests

### The external input

`monitor/FLEET_PAUSE` — **tracked**, present at `origin/master`
(blob `0359c15e`) and in the main working tree.

954eb44c ("fleet: a pause switch that everything can see…") added to
`monitor/standing.py`:

```python
PAUSE = os.path.join(HERE, "FLEET_PAUSE")

def paused():
    return os.path.exists(PAUSE)

def sweep(dry=False, only=None):
    if paused():
        log("PAUSED — monitor/FLEET_PAUSE 存在，本跳不起任何会话")
        return []
    state = load_state()
    ...
```

The guard is the **first statement of `sweep()`**, ahead of every gate
`_drive_sweep` stubs out. `_drive_sweep` monkeypatches `standing.log` to a no-op,
so the one line of evidence that would have explained the zero is swallowed, and
the helper returns `(0, 0)` unconditionally.

`standing.HERE = os.path.dirname(os.path.abspath(__file__))`, so the path read is
the **checkout's own** `monitor/FLEET_PAUSE`, not a machine-global one — the
failure therefore reproduces from the commit alone, in any clone, on any machine.
That does not make it a code defect: it makes it a test whose result is pinned to
an operational switch that someone will delete the moment the merge queue is
cleared, at which point the same two tests silently go green with no code change.

### The flip, demonstrated

Same commit, same code, same test file; only the external input changed.

```
# worktree at 8a5a83f9, FLEET_PAUSE present (as committed)
$ python -m pytest tests/test_standing_reflex_no_third_value.py -q
FAILED ...::test_the_ci_merge_step_is_not_reimplemented_anywhere
FAILED ...::test_a_declined_launch_is_not_counted_and_not_staggered
   AssertionError: a declined launch must not consume the cap: 0 attempts for 6 agents
   assert 0 == 6
FAILED ...::test_a_running_launch_is_both_counted_and_reported_started
   AssertionError: the cap must still bind on healthy launches: 0
   assert 0 == 5

$ rm monitor/FLEET_PAUSE          # worktree only
$ python -m pytest tests/test_standing_reflex_no_third_value.py -q
FAILED ...::test_the_ci_merge_step_is_not_reimplemented_anywhere   # <- only this one left
```

Both sweep tests go green. Nothing in `standing.py`, `reflex.py` or the test file
was edited.

### Why the third sweep test does *not* fail — the corroborating detail

`test_a_launch_the_scheduler_accepted_is_counted_even_if_its_health_is_unknown`
also drives `_drive_sweep`, and it passes under the pause. Its assertions are
`launches <= MAX_STANDING` and `staggers == launches`, both of which `(0, 0)`
satisfies **vacuously**. That is the signature of C rather than A: a real
regression in the launch bookkeeping would move all three tests; a global
short-circuit to zero only trips the two that assert an exact positive count.
The positive-control test is the one that has been rendered meaningless without
going red, which is precisely the disease this whole file was written to catch.

### Ruling out A and B for these two

* Not **A**: with the file removed, the shipped `standing.py` at 8a5a83f9 produces
  exactly the counts the tests demand (5 launches / 5 staggers for `running`,
  6 attempts / 0 staggers for `declined`). The launch bookkeeping under test is
  intact.
* Not **B**: the tests target `standing.sweep`, `MAX_STANDING`, `STANDING_ORDER`
  and `dispatch.via_task` — all still present with the same meanings. The test
  file has not been touched since 5c872888, which predates 954eb44c, but nothing
  in its interface was superseded; it was never given a chance to run, so there is
  nothing stale to update.

---

## A: `test_the_ci_merge_step_is_not_reimplemented_anywhere`

Unrelated to the pause. This is ADV-2/D12 coming back, exactly as the guard
predicted, in two steps.

### The regression

1. **c8061d7b** extracted the ci_merge scrape out of `main()` into
   `reflex.merge_events(r)`, so the two behavioural tests above it call shipped
   code instead of a copy. After it: `startswith("MERGED")` appears **once** in
   `reflex.py`, and `main()` contains `events += merge_events(r)`.

2. **954eb44c** (the same pause-switch commit) **deleted `def merge_events`** and
   re-inlined the eight lines back into `main()`:

   ```diff
   -            events += merge_events(r)
   +            merged = [l for l in r.stdout.splitlines() if l.startswith("MERGED")]
   ```

   That commit rewrote 215 lines of `reflex.py`; the revert of the D12 fix rode
   in as collateral, unmentioned in the message.

3. **6b953a60** `Merge remote-tracking branch 'origin/agent/s43-three-guards-reverted'`
   — recorded conflict in `monitor/reflex.py`. The resolution restored
   `def merge_events` (and `scan_events`) from the incoming side but **kept
   954eb44c's inline copy in `main()`**. Net result at 8a5a83f9:

   * `def merge_events` exists at reflex.py:84 — dead code, no caller;
   * `main()` at reflex.py:412 has its own copy;
   * `src.count('startswith("MERGED")') == 2`.

   The function and the loop can now disagree, and the two behavioural tests
   (`test_a_crashed_merger_no_longer_reads_as_a_clean_no_op`,
   `test_a_successful_merge_is_unchanged`) are green while testing a function the
   fleet loop never calls. That is the precise failure mode D12 named.

Observed failure is the first of the three assertions:

```
assert "merge_events(r)" in loop
E   AssertionError: the loop no longer calls merge_events -- the inline copy is back
```

The other two (`needle not in loop`, `count == 1`) would fail as well.

### Why not B or C

Not C: no external input involved; it is a source scan of `reflex.py` and
reproduces identically with `FLEET_PAUSE` removed. Not B: nothing was
"legitimately changed" — the inline copy is byte-equivalent logic to the
function, so this is a duplicate, not an interface migration, and the commit that
caused it does not mention `reflex`'s merge step at all.

---

## The fix

### For C (2 tests) — the instrument, OPS-M / monitor territory

The bug is in `_drive_sweep`, not in `standing.py`. It stubs every gate ahead of
the launch **except the one that was added after it was written**. One line:

```python
    monkeypatch.setattr(standing, "paused", lambda: False)
```

added alongside the other `monkeypatch.setattr(standing, ...)` calls in
`_drive_sweep` (`monitor/tests/test_standing_reflex_no_third_value.py:336-349`).
That restores the helper's stated contract — "every gate ahead of the launch says
go" — and makes the result independent of whether the fleet is paused.

Do **not** fix it by deleting `monitor/FLEET_PAUSE`: the pause is a live
operational instruction from the user and deleting it resumes fleet dispatch.

Worth pairing with a `paused()` test of its own (currently the pause switch has
no coverage at all — it can be deleted from `sweep()` without any test going
red), and worth a sweep for other tests that call `standing.sweep()` or
`reflex.main()` and are silently no-op'd by the same guard.

### For A (1 test) — `monitor/reflex.py`, the fleet-loop owner

Delete the inline copy at `reflex.py:405-425` in `main()` and restore
`events += merge_events(r)`, keeping the surviving `merge_events` at line 84 as
the single definition. Then `startswith("MERGED")` is back to one occurrence and
all three assertions pass. This is a genuine merge-resolution defect from
6b953a60 and should be recorded as such — the conflict resolution silently
reverted a fix that had a dedicated guard, and the guard did its job.

---

## Provenance

* base commit: 8a5a83f9 (`origin/master`)
* worktree: `.worktrees/opsm34-standing` (detached, removed after the run)
* commits implicated: 954eb44c (pause switch + reflex re-inline), 6b953a60
  (merge that half-restored), c8061d7b (the original D12 extraction)
* nothing committed, pushed, or changed outside the worktree
