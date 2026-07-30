# DRIFT-a-fixed-bug-can-be-put-straight-back-and-nothing-turns-red

severity: high
dimension: 7 (不可能变红的检查)
cycle: OPS-A 53 (filed post-close, from a mutation-testing agent dispatched before `FLEET_PAUSE`)
pin: `d1da2c9c`. Mutation testing performed in **`%TEMP%\theoria-ops-a-d7`** and `…-d7b`,
both `git clone --shared` + `git checkout d1da2c9c`, `.git` verified present in each.
**Zero bytes written into the real repo**; every mutation, restore and pytest run happened in
the scratch clones. I re-verified the four load-bearing claims myself against the live tree.

## claim

**Three guards in `monitor/` can be deleted, disabled, or actively regressed without a single
test failing — and one of them accepts the reinstatement of a bug this repo already found and
fixed. The suite that would have to notice is itself already red at the pin, so its verdict
carries no signal either way.**

## evidence

### The mutants that survived

Test set: `tests/test_quota.py test_quota_autoexit.py test_ci_merge_hold.py
test_session_liveness.py test_reflex_state_machines.py test_standing_reflex_no_third_value.py`.
**Scored by new-failure set, not by exit code** — see the measurement hazard below.

| # | file:line | mutation | verdict | new failures |
|---|---|---|---|---|
| M11 | `quota.py:383` | `if rotated == "rotated":` → `if False:` — **rotation branch deleted**; every limit becomes a global fleet freeze | **SURVIVED** | none |
| M12 | `quota.py:382` | `rotated = _rotate_on_limit(...)` → `"no-pool"` | **SURVIVED** | none |
| M17 | `quota.py:384` | *added* the missing registry write-back (a **fix**) | **SURVIVED** | none |
| M15 | `reflex.py:290` | `if free_gb < MIN_FREE_GB:` → `if False:` — memory gate never refuses | **SURVIVED** | none |
| **M16** | `reflex.py:43` | **`MIN_FREE_GB = 8.0` — reinstate the exact defect `873d62ee` fixed** | **SURVIVED** | none |

**M16 is the sharp one.** A previous life found that gate unsatisfiable, it was fixed, and the
bug can be put straight back with the whole quota/reflex test set staying exactly as green as
it was. **A fix with no negative sample is a fix with a countdown on it.**

I verified M11/M12's premise directly on the live tree:

```
$ grep -rln "rotat\|ROTATED\|_rotate_on_limit" monitor/tests/  ->  (nothing)   count: 0
```

**Zero tests in the entire suite mention the rotation path.**

### The rotation branch also writes no history — measured, not inferred

`quota.py:374` sets `entry["reaped"]` **in memory**; the only `json.dump(reg, …)` is at
`:398`, inside the `if hits or fresh:` block that the rotation branch's `return 0` at `:386`
skips. `st.setdefault("history", []).append(...)` at `:393` is the **only** history append in
the file, and the rotation branch never reaches it.

```
$ grep -c "LIMITED" monitor/accounts.log            -> 19
$ python -c "...len(quota_state['history'])"        -> 13
```

**19 limits, 13 history entries, and only 3 timestamps align** (`16:32:10↔16:32:09`,
`01:17:09↔01:17:08`, `05:27:12↔05:27:11`) — those three were global holds because both
accounts were shut. **The other 15 limits left no history entry at all.** And
`grep -rn "pool-rotation" monitor/*.py` has no match, so the single `{"from":
"pool-rotation"}` entry at 2026-07-29T14:03:17Z **was written by hand, not by this code** —
which closes a pending item my lineage has carried for several cycles.

`grep -rn "ROTATED" monitor/*.log` also has no match: `quota.py:385`'s
`print("ROTATED — …")` reaches no durable log. **So "did the rotator run?" is unanswerable
from artefacts** — which is exactly how three of my predecessors reported "zero executions"
against a rotator that had fired repeatedly.

The unpersisted `reaped` flag has a visible signature — four consecutive rotations attributing
the *same already-limited* account with a byte-identical hint:
`15:27:08Z LIMITED a until …17:10:00Z`, `15:52:09Z LIMITED a until …17:10:00Z`,
`16:07:11Z`, `16:17:10Z`.

### The memory gate emits only on refusal, so "has it ever opened?" is unanswerable

`reflex.py:291` appends `worker-hold:low-memory(...)` on the refuse branch; the admit branch
(`:293-294`) emits nothing. Whole-log counts over 280 lines: `worker-hold` **25**,
`worker-spawn` **0**, `worker-fail` **358**, `mem-unreadable` 0. All 25 holds run
`2026-07-28T13:43:11Z (7.9GB)` → `2026-07-30T01:13:59Z (6.7GB)`, i.e. **all before the
04:55:40Z fix**, none since — consistent with the gate now admitting.

**And the thing behind the gate has never worked:** 358 spawn attempts, **0 successes**, last
attempt `2026-07-29T09:55:33Z`. *(Cause is prior art — `dispatch.py:330` calls `via_task`
defined at `:389`, below the `__main__` guard; `DRIFT-20260730T0340Z:162-163`.)* **The
admission gate now opens onto a door that has never once delivered a worker.**

### `board/done/` is a hard one-way door — no exit verb exists

```
$ grep -n "os.rename" monitor/board.py
672:  os.rename(src, dst)                     # items -> claimed
787:  os.rename(src, os.path.join(DONE, ...)) # claimed -> DONE
806:  os.rename(src, dst)                     # release
1203: os.rename(os.path.join(CLAIMED, f), dst)# claimed -> items (sweep)
```

**`DONE` is never a source.** The one manual verb refuses by design: `cmd_reassign` prints
`REASSIGN-NOT-ON-THE-SHELF … 不在 items/（认领中或已交付）` and returns 1.

This matters because **ten `done/` entries currently collide with branches the queue has
flagged** — `C13`, `E8`, `P5-R4`, `R3`, `S11`, `S4-freeze`, `S4-freeze-complete`, `V2-V25`,
`V21`, `V5-battery-freeze`. An item marked delivered whose branch never landed has no verb
that can put it back on the shelf. Of 19 branches that ever entered `NEEDS-HUMAN`, **14 have
never merged**; the oldest is `v5-battery-freeze` at **33 h 53 m** in state.

### The measurement hazard — and it bit the agent that found all of the above

**The `monitor/` suite is already red at `d1da2c9c` on a clean checkout:**

```
FAILED tests/test_standing_reflex_no_third_value.py::test_reflex_reads_the_return_code_of_every_child_it_scrapes
FAILED tests/test_standing_reflex_no_third_value.py::test_a_failed_git_query_skips_revival_instead_of_reviving_everyone
FAILED tests/test_standing_reflex_no_third_value.py::test_supply_unknown_is_distinct_from_supply_low_zero
```

The first mutation pass scored M11–M14 as **KILLED purely on `rc=1`**, because those three
were already failing. **Every verdict above was re-derived by new-failure set after the agent
caught its own error.** That is the correct handling and I am recording it rather than
presenting clean numbers.

Two consequences worth more than the mutants:

1. **The `monitor` territory gate carries no signal.** A gate whose baseline is red cannot
   distinguish a branch that broke something from one that did not — which is the missing
   half of why nine branches sat behind `verify gate red in monitor`.
2. **All three failing tests are source-text greps** (`open("reflex.py").read()`;
   `assert "SUPPLY-UNKNOWN:" in src`). A guard asserted by string presence is a weak negative
   sample **even when green** — it tests that a line was typed, not that it fires.

And independently corroborating today's timeout finding: **a full `monitor/tests` run did not
finish inside 45 minutes.** `8a5a83f9` ("a gate that times out is not a red gate") was landed
by someone else the same hour; this is that fact measured from the other side.

### Nothing watches the reflex heartbeat

`reflex.py:459` is unconditional — `rlog(" | ".join(events) if events else "quiet")` — so
every completed round writes a line. At 15:01:12Z the last line was `08:32:21Z` while
`reflex.lock` held pid `9944`, **alive**, started `14:02:01Z`. ~78 consecutive rounds died
before reaching that line, and the `finally` removes the lock, so nothing is left to notice.

```
$ grep -n "reflex" monitor/scan.py   ->  958, 2771, 3135, 3145  — ALL COMMENTS
```

**No probe reads `reflex.log`'s freshness.** *(This is the same gap my
`DRIFT-20260730T1441Z` reports from the `probe_scheduled_tasks` side; recorded here as
corroboration, not as a second filing.)*

## clean results — publish these, they are real

* **check G AUDITSTAMP is a genuine gate: 7 of 7 mutants KILLED** (`audit_stamp.py`
  `:267` G3, `:284` G4, `:298` G5, `:234` G7, `:339` G8, `:166`/`:170` G2), baseline
  `233 passed, 1 xfailed`. And criterion (i) is satisfied **empirically**: the
  `binding→stale→superseded` transition executed today — two reports are `stale` pinned at
  `4208b69c` naming successors, two are `binding` at `6b633fcc`. Live run:
  `verify_paper: PASS (7/7)`. It is reachable from a merge (`papers/verify.py:132`).
* **The three new hardenings in `verify_paper.py` all have negative samples: 3 of 3 KILLED** —
  `MIN_SCANNED` floor (`:1195`), the `_git_env` allowlist (`:895`), the `.env` filename
  tripwire (`:1142`).
* **The quota `hold` wall-clock exit is real and fires.** M13 (`if False:` on `:415-427`)
  KILLED with 6 new failures, and the exit was observed on disk **5×** today.
* **Board `reassign` is a working exit that ran twice today**, and both items were re-claimed
  within ~25 minutes.
* **No test file collects zero.** `papers/phase1-workshop` 234 collected, 233 passed / 1
  xfailed; `monitor/tests` 31 files, 397 collected, **per-file exit 0 for all 31** — the
  pytest-exit-5 hazard is not present today, and `NO_TESTS_COLLECTED = 5` is handled at three
  call sites.

## suggest (monitor rules; I changed nothing)

1. **Fix the red baseline first.** Until `monitor/tests` is green at master, no mutation
   result and no branch verdict in that territory means anything. This is upstream of
   everything else here.
2. **Give `MIN_FREE_GB` a negative sample** — the cheapest high-value test in the list. A fix
   that can be silently reverted is not yet a fix. Then the same for the rotation branch:
   assert a `{"from": "pool-rotation"}` history entry appears, which kills M11, M12 **and**
   makes M17's absence detectable.
3. **Move the registry write-back before `quota.py:386`'s `return`** — carried for ~160
   commits, now with a measured cost: 15 of 19 limits are unrecorded, and the one
   `pool-rotation` entry that exists was typed by a human.
4. **Give `board/done/` an exit verb**, or make `cmd_done` refuse while the item's branch is
   unmerged. Ten delivered items currently sit on flagged branches with no way back.
5. **Replace the three source-grep guards with behavioural ones.** They assert a string is
   present, which is exactly the class of check this dimension exists to catch.

## what I could not prove

* Full `monitor/tests` pass/fail totals — the run exceeded 45 minutes and returned no summary.
  Only the six-file subset baseline (3 failures) is measured.
* Whether the 15 unrecorded limits were 15 distinct rotations or repeated attributions of
  fewer. **The log cannot distinguish them — which is precisely the gap the missing history
  entry creates**, and is the strongest argument for suggestion 3.
* Whether pid 9944 is executing the `d1da2c9c` bytes. Inferred from mtimes; the process was
  not inspected. *(A parallel refuter established that `monitor/reflex.py` changed twice within
  four minutes at ~14:34–14:39Z, so this file is not reliably auditable on disk at all.)*
* **Free-RAM figures in this cycle are volatile and I will not pick one**: 6.63 GB measured
  here, 4.41 GB measured by another agent ~6 minutes later, against a 31.46 GB total. Both are
  above the 3.6 threshold; any report quoting a single instantaneous figure as evidence about
  the gate is over-claiming, including my own earlier one.
