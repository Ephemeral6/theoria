# S12 · every transition of the quota breaker, and every mutant that proves it

**Worker** W-1412 · **branch** `agent/s12-quota-hold-tests` · **base** `d751ccd`
· **utc** 2026-07-28T14:54:19Z · zero tokens, zero network, zero quota.

## What was asked

The quota breaker froze the fleet: a session-limit at 09:35 set `mode=hold`,
the limit's own text said the window reopened at 20:20, and the fleet was still
held long after. Two holes, one shape — a state with an entry and no exit.
Nothing called `resume`; and `resume`, on an empty queue, returned **without
clearing the mode**. Monitor fixed both on the spot. This item is the tests, so
the next one is caught by a suite rather than by a person.

## What is here

`monitor/tests/` — 22 passing, 2 `xfail(strict=True)`:

| transition | test | negative sample |
|---|---|---|
| normal → hold | a limit signature holds and requeues | a death with **no** signature must not hold; a session that **pushed** is not a quota kill |
| hold → normal (deadline) | the hold expires when the window it named reopened | it must **not** expire before its deadline; an unreadable hint still hits `MAX_HOLD_HOURS` |
| hold → normal (empty queue + ping) | queue empty and window open clears the mode | a **closed** window must stay held; `normal` + empty queue must not spend a ping |
| hold → recovering → normal | priority order, half the batch, tail stays queued | a closed window relaunches **nothing** |
| ci_merge under hold | structurally not inside any branch testing `hold` | and dispatch **is** still behind the gate — otherwise the breaker holds nothing |

## The part that matters more than the count

A green suite proves the code passes the suite. It does not prove the suite
would have caught the bug — and for a state machine that froze the fleet for
most of a day that is the only question worth asking. `tests/mutants.py` puts
each defect **back** into a throwaway copy of `monitor/` and checks a test goes
red. Both real OPS-M cycle 5 defects are in the table:

```
resume-empty-queue-never-clears-the-mode             RED   test_an_empty_queue_with_an_open_window_clears_the_hold; ...[ping]
check-never-lifts-the-hold-on-its-deadline           RED   test_the_hold_expires_when_the_window_it_named_has_reopened; ...
ci-merge-blocked-by-the-quota-hold                   RED   test_ci_merge_is_not_gated_on_the_quota_hold
resume-relaunches-into-a-closed-window               RED   test_a_closed_window_relaunches_nothing_and_holds
hold-fires-on-any-dead-session-not-just-a-quota-one  RED   test_a_dead_session_without_a_limit_signature_does_not_hold

all 5 mutants caught
```

Nothing writes to the live `quota_state.json` or `dispatch-logs/`. The fleet is
running while these tests run; a test that wrote the real state file could hold
the whole fleet, which is the failure being prevented.

## The audit: what else has an entry and no exit

Asked for by the item, not fixed here (it says to list them, and `monitor/` is
live). Both defects are recorded as `xfail(strict=True)` rather than as prose,
so they stay quiet today and go **loud** the moment someone fixes the
underlying thing and leaves the marker behind.

**1. `death_counts` — the three-strikes rule. Entry, no exit.** `MAX_DEATHS`
is 3, `deaths[pid_str]` only ever increments, and nothing in `reflex.py` lowers
it: no decay, no reset on a successful run, no un-bench. A session benched by
three *transient* deaths never comes back without someone hand-editing
`loop_state.json`. The sharp edge: **a quota outage produces exactly those
deaths**, so the outage this breaker exists for can permanently bench the
sessions it kills. Same shape as the bug that opened this item.

**2. `reflex.lock` — the window is shorter than the work it guards.** The lock
is the one clean case in the loop: two independent exits, `finally:
os.remove(LOCK)` and a staleness override, and the second does not depend on a
clean shutdown. But it goes stale after **1500 s** while a single tick can
legitimately run far longer — `ci_merge` alone is invoked with `timeout=3600`,
`resume` with `timeout=1800`. A slow tick outlives its own lock and a second
reflex starts beside it. Not "no exit"; the mirror image — **the exit fires
while the door is still in use.** Fix is a raised window or a lock refreshed as
the tick proceeds.

**3. Board claims — swept, but not for every worker.** `board.py sweep` runs
every tick and is not behind the hold gate (checked by a test: an outage must
not be able to stop its own victims' claims being freed). It frees only `W-*`
claims, and deliberately — `APP-*`/`RES-*` liveness is not visible in the task
table. It is still a door only its own claimant can open, and it has already
cost one incident. Listed, not fixed: any sweep of those needs a liveness
signal that does not exist yet.

## One note on scope

The item header says `territory: proxy`. There is no quota code under `proxy/`,
and the item body names `monitor/quota.py` four times. Read as a slip in the
header rather than a genuine relocation: the work is in `monitor/`, and nothing
under `proxy/` was touched.

## Verify

```bash
cd monitor && python -m pytest tests    # 22 passed, 2 xfailed
cd monitor && python tests/mutants.py   # all 5 mutants caught
```
