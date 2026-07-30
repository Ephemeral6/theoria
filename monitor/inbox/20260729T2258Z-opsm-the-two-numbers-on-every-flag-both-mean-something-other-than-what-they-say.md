# OPS-M · The two numbers on every flag both mean something other than what they say

utc: 2026-07-29T22:58:00Z
from: OPS-M (merge referee), cycle 21
master at time of measurement: c54954d6
territory: `monitor/` — **I do not change it (CHARTER). This is a report, not a patch.**

## Summary

`monitor/ci/` currently holds 8 flags. The two numbers a reader uses to
prioritise them — `attempts` and `first_seen`, which `ci_merge` promotes into
the log as `[NEEDS-HUMAN: N attempts since T]` — are **both** measuring
something other than what they are read as. Neither is a lie anyone told; both
are artefacts of `flag()` keying its memo on the branch and nothing else.

There is a third number that is not recorded anywhere and is the one that
actually separates "stuck" from "abandoned": **the age of the branch tip.**

## Finding 1 — `attempts` and `first_seen` survive a change of failure

`flag()` (`ci_merge.py:340`) reads `prev = last_attempt(branch)` (`:355`), keyed
on the branch alone. `first_seen` is carried forward (`:357`) and `attempts` is
incremented (`:359`) **without ever comparing `reason` to the previous one.**
So when a branch stops failing one way and starts failing another, the counter
and the clock march straight through the discontinuity.

This is not hypothetical. `a3-campaign-devpile`, from `merge.log`:

```
01:55Z–02:19Z   tests red in theoria-arm
02:32Z–04:14Z   verify gate red in monitor (verify.sh)
05:25Z onward   verify gate red in theoria-arm (verify.py)   <- current
15:07Z          one relapse to verify gate red in monitor (verify.sh)
17:21Z onward   back to verify gate red in theoria-arm (verify.py)
```

Its flag today reads `attempts: 13`, `first_seen: 2026-07-29T04:14:01Z`. That
04:14Z timestamp belongs to the **monitor-gate** failure — a different defect,
in a different territory, now gone. The failure the flag actually describes has
been continuous only since 17:21Z. `v5-battery-freeze` has the same shape with
two reasons (`merge conflict` and `verify gate red in battery (verify.py)`).

The comment authorising the escalation says:

```python
if attempts >= 3:
    # Three distinct tips have failed the same way.
    # Retrying is no longer the useful act; naming it for a human is.
```
(`ci_merge.py:370-373`)

**Both halves of that sentence are false as written.**

* *"the same way"* — refuted by a3 above.
* *"three distinct tips"* — `should_hold` (`:222-223`) returns False whenever
  `base` moves, i.e. whenever master moves, **irrespective of the tip**. Each
  such retry calls `flag()` and increments `attempts`. Empirically: a3's tip
  `41ad497c` was pushed 2026-07-29T20:58:15Z, and it has been re-flagged at
  21:03, 21:27, 21:49, 22:21 and 22:41Z — **five attempts, one tip.**

I want to be precise about the blast radius: the retry behaviour itself is
*correct*, and the base check is well argued in its own docstring (`:190-204`,
the p13 case). Nothing merges wrongly because of this. **The cost is entirely
in prioritisation** — `attempts` reads as evidence of effort and `first_seen`
as evidence of age, and a human triaging eight flags spends their attention
accordingly. I did exactly that at the top of this cycle.

This is the same family the file already worries about at `:206-210` — "S21
shipped with a docstring, a commit message and a reflex comment all describing
a third condition its code never had". Here the drift is between the comment at
`:371` and the code three lines above it.

Cheapest honest fix, if you want one: when `reason` differs from `prev`,
restart `first_seen` and `attempts` (and perhaps keep a `previously:` line so
the history is not lost). That makes both numbers mean what they are read as.

## Finding 2 — tip age is the missing column, and it inverts the triage

Flag age says nothing about whether anyone is still working on a branch. Tip
age does, and it is not displayed anywhere. Measured this cycle:

| branch | attempts | flag since | **tip age** | reading |
|---|---|---|---|---|
| `v25-leakage-loo-and-multiplicity` | 2 | 22:15Z | **0h** | active |
| `a3-campaign-devpile` | 13 | 04:14Z | **1h** | **active** — author pushed 1h ago |
| `r4-ruling-path` | 6 | 19:02Z | 3h | active |
| `r3-release-classifier-defaults` | 7 | 18:32Z | 4h | active |
| `v21-leakage-gate-token-level` | 7 | 18:32Z | 4h | active |
| `e8-ic3-scale` | 11 | 04:15Z | 10h | slowing |
| `v5-battery-freeze` | 10 | 04:33Z | **27h** | **abandoned** |
| `s11-sealed-halfguard` | 10 | 04:19Z | **32h** | **abandoned** |

Sorting by `attempts`/`first_seen` puts a3 (13, 18h) at the top of the worry
list. Sorting by tip age puts it sixth — its author is *at the keyboard right
now*. The two branches that genuinely need intervention, `v5` and `s11`, are
the ones whose **tips predate their own flags**: nobody has touched either
since before it was first flagged.

### The part that needs a decision from you

Both of those two are currently parked with the disposition *"waiting on the
branch author"* (v5: needs V5 to register `BATTERY_V2` in `freeze.FREEZE`;
s11: my DO-NOT-MERGE-AS-IS, plus your outstanding call on it touching
`CLAUDE.md`). That disposition has now been in force for over a day **while the
author has been absent for the whole of it.**

Waiting on someone who has not appeared in 27–32 hours is not a plan, and the
queue will retry these two forever without ever changing anything. They need
reassignment to a live worker or closure — either is fine, but the current
state is a deadlock that cannot resolve itself. **This is the one item in this
note that will not fix itself if ignored.**

## What I am not claiming

* I have not shown any branch merged that should not have, or failed to merge
  that should have, because of Finding 1. I looked; I did not find one.
* I have not audited whether `attempts` resets anywhere else in the file.
* Tip age is a proxy for author attention, not a measurement of it. A 27-hour
  tip is consistent with an author who is deliberately blocked and waiting on
  a ruling — which is, in fact, exactly s11's situation, and is *why* it needs
  your decision rather than more patience.
