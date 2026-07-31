# The live half — what was authorised, what was spent, what it bought

## Authorisation

The board re-issued A3 with an explicit monitor ruling attached, answering the
proposal in `monitor/inbox/20260729T002000Z-W-1640-a3-spend-proposal.md`:

> **监控事后授权（2026-07-29）**：这件是花真钱的战役，而它被一个通用工人领走，
> 是因为我解封赛道时顺手拆掉了那层**顺带**的保护（「只有 RES-1 能花 API 钱」
> 一直靠 campaign 赛道有主在执行）。缺口已堵：`spend: api` 的条目现在必须由
> 监控显式写 `generic_ok: yes` 才下放。**这一件我批准继续** […] 余额 $168，
> 而 WP3 是论文权重最大的缺口且已冻结八小时。

So the CHARTER blocker is resolved by the authority that owns it, with the item
now carrying `spend: api` and `generic_ok: yes`, and monitor reading the `spend`
probe every heartbeat. Recorded here rather than paraphrased, because the
Phase 1 gate at `Theoria.md:305` is still 9/16 and this is the exception that
lets a run past it.

Note the balance in the ruling is **$168**, while the gate's own arithmetic at
the time read $183.15 free. I sized to the smaller figure.

## Spend, in order, with what each bought

### 1. `--mock --desk`, haiku — $0.26 — the blocker-A proof

The cheapest possible check that a *completed* model call now survives the
ledger: a real desk against the mock world, so real model money but **zero ARC
quota**. This is step 1 of the runbook and it is not skippable — blocker A is
invisible until a model call completes, and no test in this repo had ever driven
one.

Two calls landed as canonical `model_call` records:

| call | step | beat | label | in/out tokens | cost |
|---|---|---|---|---|---|
| 0 | 6 | theorize | round1 | 9 / 16,925 | $0.1143 |
| 1 | 6 | theorize | round1 | 9 / 22,614 | $0.1463 |

with `beat`, `label`, `proxied` inside `request`, as D-A3-004 requires. **On the
code as inherited, both would have raised `NonCanonicalField` after the charge
settled**, and `inner/loop.py` would have filed each as an ordinary desk
failure. The fix is now proved against real money, not only against fixtures.

Incidental finding worth keeping: the first attempt at this used `--budget 4`
and never reached the desk at all — four actions went to the opening sweep, no
surprise fired, so no model call happened. That is constraint 8 behaving exactly
as specified (无意外则无模型调用), observed rather than asserted, and it cost
$0.00.

### 2. A killed run costs the ceiling — $4.00 — a lesson, not a purchase

I ran that proof under a foreground timeout. The harness tool caps at ten
minutes; the run was still working, and the process was killed mid-call.

`ModelDesk.call` charges an interrupted call at `MODEL_CALL_CEILING_USD` and
flags it unpriced, because *"the alternative is assuming it cost nothing, which
lets the provider decide whether it gets billed"*. So the third call — a haiku
call whose real cost would have been ≈$0.15 — was booked at **$4.00**.

That is the policy working, not a defect. But it means **killing a live run
mid-call costs roughly 25× what the call was worth**, and I am recording it as a
cost of my own process error rather than folding it into the campaign's
accounting. Total pool movement for the proof: $31.749 → $36.142, of which
$0.26 is measurement and **$4.13 is the interruption**.

The over-charge is reclaimable in principle via `SpendGate.price_unpriced()`,
and I am deliberately **not** reclaiming it: the killed CLI never reported a
price, so any number I supplied would be invented. An over-charge with evidence
beats an accurate-looking figure without any.

Second-order finding: SIGTERM skips `Run.__exit__`, so the reservation was
**leaked live** — $5.50 of shared headroom held with the process gone. It would
have self-expired at the 3600s TTL, but in a pool the whole fleet shares that is
not good enough. Released manually with the reason recorded
(`orphaned: run killed by an external timeout, __exit__ never ran`).
**Any long live run must be backgrounded, never foregrounded under a timeout.**

### 3. The live leg — g50t, opus

Launched in the background for exactly the reason above. Caps, all passed
explicitly rather than taken from the module defaults, because `CAMPAIGN_USD =
200` exceeds the pool's free headroom and nothing in the repo authorises the
constants:

    --campaign-usd 30  --game-usd 15  --actions-per-level 12
    --model claude-opus-5  --games g50t-5849a774  --max-legs 1

The leg's own ceiling is then `min(LEG_COST_CEILING_USD, headroom - 1) = $14`,
and `plan_caps` reserves `$14 + $4 = $18` against the pool with an action cap in
the pool's unit (outbound HTTP requests), refusing up front if global free
headroom cannot cover it. 先算后花, at the entry point.

Expectations written before the result, so they can be wrong in public:

* **No level will be completed.** g50t level 1's own baseline is 78 successful
  actions; this leg has 12.
* Therefore **no level boundary, and no C3 transfer observation.**
* What it should buy is a real per-turn series — theorize rounds, the seven
  surprise counters, and the cost curve — on the `campaign_turn` axis.
* At the measured 394 s/action this is a ~1–2 hour leg, and **wall clock, not
  money, is what will end it.**

Result appended below when it lands.

## Two findings from the live leg, before it even reached a model call

### The credential alarm fires on every single request

The leg's ledger carries one `incident` per `env_step`, all of kind
`credential_in_body` — *"a key-shaped string appeared in a request body"* —
across all five command paths (`RESET`, `ACTION1`–`ACTION4`).

They are false positives, and provably so: this arm holds no credential at all.
`harness/arc.py` is checked by a test that greps it for `os.environ`,
`read_secret`, `getenv`, `X-API-Key` and `Authorization` and requires all of
them absent; the key is injected only inside `proxy/env_proxy.py`. What the
detector is matching is the **`guid`** every request body carries, which is a
UUID, and `redact.py`'s `_KEYISH` includes a UUID-shaped alternative. The
comment beside that pattern already anticipates it —
*"`card_id` and `guid` are also UUIDs, so matching here raises an incident and
never rewrites the ledger"* — so the ledger is not corrupted and this is a
detector limitation working as documented.

**But the consequence is not benign.** The signal fires on 100% of requests, so
a genuine credential leak would arrive as one more line in a stream that is
already all alarm. An alarm with a 100% false-positive rate is not a
conservative alarm; it is an alarm nobody can read, and it is exactly the shape
of thing that gets filtered out of a dashboard and then misses the one that
mattered. Worth a cheap fix in `proxy/` — exclude the known UUID-valued fields
(`guid`, `card_id`) before matching, so the detector's remaining hits mean
something.

### CORRECTED — HTTP amplification is 17.0x, and the cookie-jar blocker is real

**I got this wrong first and am correcting it rather than quietly editing it,
because the wrong version was committed.**

What I first reported: "amplification exactly 1.0, every request succeeding
first try", read as a refutation of the pre-spend audit's "no cookie jar, so
5-17x" blocker.

What I measured to get that: `http.attempts` per `env_step`, summed and divided
by the number of steps. That is *retries within one request*, and it is 1.0
because the arm's retry envelope is not being exercised — each request is
answered on its first attempt.

Why it is the wrong quantity: **a failed request is logged as its own
`env_step`.** The metric that matters, and the one the P-8 figures use, is
outbound requests per *successful* action. Recomputed on the same leg:

| quantity | value |
|---|---|
| `env_step` records | 51 |
| HTTP 400 | **47** |
| HTTP 200 | 4 |
| outbound attempts | 51 |
| **HTTP per successful action** | **17.0x** |

So the blocker is **confirmed, not refuted** — and at the worst of the three
P-8 values, not the best. The 400 wave is exactly what the cookie jar fixes
(`arc-recon` INC-007/007a: cookie arm 20/20 first-attempt RESETs, cookie-less
arm 0/20; paired canary 11.88 -> 1.25 HTTP/action, and for g50t specifically
41 -> 3). `baseline-arms/harness/arc_client.py` has the fix;
`theoria-arm/harness/arc.py` still does not. My earlier sentence "the porting
job is, on this evidence, not needed" is withdrawn: it is needed, and this leg
is the evidence.

**The consequence is worse than slow, and it is a budgeting defect.**
`harness/spend.py` reserves against `HTTP_PER_COMMAND = 1.75`. The measured
figure for this arm on live g50t is 17.0 — about **ten times** the constant the
reservation is computed from. So every `plan_caps` call for this arm undersizes
its action reservation by an order of magnitude, and a leg sized to 12 actions
reserves ~34 requests while actually needing ~204. The gate will trip mid-leg,
correctly, on a claim that was wrong when it was made. That is fail-safe, but
"先算后花" only works if the arithmetic uses a number from this arm's own
transport rather than one measured on another arm's.

The general lesson, and it is the third time in this run: **a number that looks
good is the moment to check what it is a number of.** 1.0 was a real
measurement of the wrong quantity, and it happened to say exactly what would
have been convenient.

