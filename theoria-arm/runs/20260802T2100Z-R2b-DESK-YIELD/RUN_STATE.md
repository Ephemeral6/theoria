# R2b — the sk48 leg was not thinking harder, it was paying for replies the arm threw away

Offline forensics over the two archived R2b legs of 2026-08-01. No model call,
no API call, no spend. Everything below is read off `desk/*.md`,
`desk_log.json`, `ledger.jsonl` and `books/snapshots/`.

## The question

g50t fired 24 probes and advanced 29 actions at $2.08 per desk call; sk48 fired
3 probes and advanced 9 at $3.38, and one of its calls ran over 22 minutes. The
brief's hypothesis was that sk48's manual is large and desk cost is
proportional to manual size.

## The obvious hypothesis is refuted by the record

It is refuted in both directions at once. **sk48 sent the desk the smaller
prompt and paid more.**

| | g50t-a | sk48-b |
|---|---|---|
| largest prompt sent | 128,759 chars | 85,904 chars |
| manual at the last write | 72,299 chars | 32,522 chars |
| desk spend | $18.74 / 9 calls | $20.30 / 6 calls |
| billed actions | 29 | 9 |
| **$ per billed action** | **0.646** | **2.256** |

Within sk48, prompt length explains none of the bill:
`prompt_census.fit_tokens` returns r² = 7.6e-6 over its six calls. The manual
that was supposed to be the cost driver *shrank* — 48,472 chars carried,
27,479 after the first write, then frozen at 32,522.

## Where the money is: the output side

`desk_yield.price_fit` recovers the per-million rates by least squares from
each leg's own bills and reproduces every one of them to within 0.4% of the
mean bill:

    g50t: cache_write $10.65/Mtok, output $25.07/Mtok — worst residual $0.0045
    sk48: cache_write $11.11/Mtok, output $24.59/Mtok — worst residual $0.0124

Output tokens carry **69% of the bill on both legs**. Elapsed time is a linear
function of output tokens (corr 0.996 across all 15 calls, median 86 tok/s):
the 22-minute call is not a hang and not a network stall, it is 109,763 output
tokens generated at the model's own rate. The two 25-minute calls are 132,309
and 131,033 — each above the CLI's reported 64,000 `maxOutputTokens`, on a
single reported turn.

## What those output tokens bought: nothing

`inner.theorize.OUTPUT_CONTRACT` demands three blocks and the arm rejects a
reply without `=== THEORY ===` ("the reply carried no === THEORY === block").
The replies are not truncated — every one ends with a complete, well-formed
`=== LOG ===`. The desk simply stopped emitting the manual.

    sk48  call 3  $2.79  13.7 min   69,743 out   LOG+PLAYBOOK   VOID
    sk48  call 4  $2.83  14.2 min   71,146 out   LOG+PLAYBOOK   VOID
    sk48  call 5  $4.68  25.3 min  132,309 out   LOG            VOID  (prompt byte-identical to call 4)
    sk48  call 6  $4.63  25.3 min  131,033 out   LOG            VOID

Four consecutive void calls, all at `step_idx` 10, all at 9 actions:
**$14.93 = 74% of the leg's spend bought no change to the books and no action
in the world.** Call 5 was sent a prompt byte-identical to call 4's — same
manual, same evidence, same 422-character compiler complaint — and produced
less than the call before it. The books confirm it: 32,522 chars after
theorize, twice, unchanged.

g50t has the identical failure mode, twice (calls 5 and 9, $6.05 = 32% of its
spend), and recovered each time. It is the same defect at a different rate, not
a different defect.

**Corrected per-action reading.** sk48's $2.256/action is not the price of
theorising about sk48; it is $5.38 of theory plus $14.93 of nothing, divided by
9 actions. Split the two questions apart:

| | g50t-a | sk48-b | ratio |
|---|---|---|---|
| whole spend ÷ billed actions | $0.646 | $2.256 | 3.49x |
| whole spend ÷ calls that moved the books | $2.68 | $10.15 | 3.79x |
| mean bill of a call that *worked* | $1.81 | $2.69 | **1.49x** |

sk48 is about half again dearer to theorise about when the theorising lands.
Everything past that 1.5x — the other 2.3x — is spend that bought nothing, and
the actions it therefore never bought.

## Two framework findings, not sk48 findings

1. **The output contract mandates the expensive thing.** "the whole of
   theory.dsl, not a diff" makes the manual an *output* cost on every call, and
   output is 69% of the bill. `inner/deskdiet.py`'s `theory_patch` knob is the
   fix already written; both R2b legs ran with it off (no `patch_contract`
   section appears in any of the 15 prompts).

2. **`Theoria.md` 1.8's compression rule is not enforced anywhere.** Rule 3 of
   the preamble states it ("a concept earns its place by making the manual
   shorter"), nothing checks it, and neither leg obeys it. g50t's manual grew
   monotonically 38,044 → 72,299 (+90% from its own first write, +49% over the
   carried seed). sk48's stopped changing size at all. Growth is not read as a
   surprise, is not certified against, and costs money on every subsequent
   call — a growth loop with no brake.

3. **No ceiling bounds a call in flight, and the arm's own guard is already
   red about it.** There are two ceilings and neither is a cap. The flat
   `harness.spend.MODEL_CALL_CEILING_USD` is $4.00 and is what this leg's
   `plan_caps` arithmetic sized with; the per-model
   `MODEL_CALL_CEILINGS_USD["claude-opus-5"]` is $15.00. Both are *pre-flight
   headroom checks against the pool*, consumed before the subprocess starts —
   sk48 calls 5 and 6 then billed $4.68 and $4.63 apiece, and nothing could
   have stopped them.

   The consequence is a **standing red on master**, not something this run
   introduced:

       tests/test_desk_gate.py::test_the_ceiling_table_still_covers_the_archive
       AssertionError: claude-opus-5: ceiling $15.00 is below $18.7391, which is
       what this table's own stated rule -- max(timeout x rate, 4x worst call) --
       produces from the archive.

   Verified pre-existing: the test fails identically with this run directory
   moved out of the tree. The table's ladder is 6.00 → 7.00 → 12.00 → 15.00,
   "each step forced by a measurement, never by a guess" — and R2b's
   $4.684776 worst call makes 4x = $18.74, which $15.00 no longer covers. The
   table has been telling this story since 2026-08-01 and nobody read it.

   **Not fixed here, deliberately.** `harness/spend.py` is on the path of the
   A26 round that is live right now; raising the ladder (and rescaling the four
   derived rows the table's own arithmetic ties to the opus anchor) is a
   separate ticket and not one to land under a running leg.

## Harder game, or worse-served? Neither, as posed

The brief says "same tree, same books". The books are byte-identical
(`theory.dsl` sha256 `231ae4d7…`, 48,472 bytes, both legs) — and they were
written **for g50t**, seeded from `runs/20260731T1430Z-A3-level2-carried-r3`,
`game_id g50t-5849a774`. So g50t-a is a *continuation* of its own theory and
sk48-b is a *cross-game transplant*. That is not a controlled comparison of two
games; it is one leg refining a fitted manual and another demolishing a wrong
one, and the demolition shows: sk48 cut the manual 43% on its first write and
logged 4 `replay_mismatch` surprises against g50t's 1.

So the honest answer is: sk48 is **worse-served**, and the record cannot say
whether it is also harder, because no leg has ever theorised sk48 from a seed
that was about sk48.

## What neither leg could do, and it is not about cost

`plan.json` on **both** legs is `no_goal_declared` on every single planning
beat — 25 of 25 on g50t, 5 of 5 on sk48. Neither manual declares a winning
condition, so `is_goal` is False everywhere and no search can succeed. Against
`level_baseline_actions = 78` for g50t level 1, a leg that spends $18-20 to buy
9-29 actions *and cannot plan at all* is not one fix away from a level. Fixing
the void calls buys roughly 3x the actions per dollar; it does not buy a goal.

## Absence recorded as absence

* No leg on sk48 has ever started from an sk48 manual. Not measured, not zero.
* The 3-term price fit's `cache_read` coefficient comes out negative on both
  legs — only 2 and 5 of the calls read any cache, so that term is not
  identified. Reported as unidentified, not rounded to zero. The two terms that
  carry the finding are unaffected.
* `CHARS_PER_OUTPUT_TOKEN_EST = 3.7` is a stated constant, not a measurement;
  every field derived from it is named `_est`. The thinking-vs-text split is
  therefore approximate. The gap it describes (sk48 call 6: ~7 kB of reply
  against 131,033 output tokens) survives any constant in 3.0–4.5.
* `num_turns` is 1 on all 15 calls while two of them billed above
  `maxOutputTokens`. The arm's records cannot say what happened inside the CLI
  subprocess. Recorded, not explained.

## Gate

`cd theoria-arm && python -m pytest -q`. `tests/test_desk_yield.py` is 15
passed. One pre-existing failure stands —
`test_desk_gate.py::test_the_ceiling_table_still_covers_the_archive`, quoted in
full above, red on master before this branch and confirmed red with this run
directory removed from the tree. It is this run's finding restated by the
arm's own guard, and it is left red rather than patched under a live round.
