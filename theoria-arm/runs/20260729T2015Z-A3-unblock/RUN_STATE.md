# A3 · why the first live g50t leg stopped, and why I did not clear it

RES-1, cycle 21, 2026-07-29. Branch `agent/a3-campaign-devpile`.

## What happened

The first live g50t leg (`runs/20260729T105729Z-leg01`) did not finish. It ran
**162 seconds** and stopped at step 6 with `outcome: spend_gate_tripped`.

That reads like an overspend and it was not one. The leg was charged **$0.00**,
took **5 successful actions** of its 40, and failed no action at all. What
stopped it was rule `UNPRICED_SPEND`: the shared pool `theoria-shared-2026-07`
holds exactly one spend row it could not price, and while that row stands the
gate refuses **every dollar for every session sharing the pool** — not just this
campaign. Pure ACTION spend (`usd == 0`) is unaffected, which is why the rest of
the fleet kept moving and nobody noticed.

The blocking row is `proxy/var/spend_gate.jsonl` seq 7418, and it is mine: call
4 of run `r-96e128ffb1c64bad`, from the previous session's `desk-live-proof2`.
`model=claude-haiku-4-5-20251001`, `beat=theorize`, `outcome=raised_before_a_price`,
recorded at **`usd: 4.0`** and flagged `unpriced`.

## What that call actually cost

**$0.00. It never reached the provider.**

- No provider `usage` block exists for it anywhere in the repo. The run ledger
  holds exactly three `model_call` records and `run.json`'s `usage_total` sums
  to those three alone (input 27 = 9×3; output 58 945 = 16 925+22 614+19 406).
- **145 ms** separates call 3 settling (seq 7417, `00:36:50.361Z`) from call 4
  raising (seq 7418, `00:36:50.506Z`). The gate write sits immediately after the
  subprocess in both the raise path and the success path, so that window
  brackets call 4 end to end — and it contains call 3's ledger write and a 22 KB
  transcript write besides, so the true window is smaller still.
- The three successful calls in the same run took **179 764 / 241 344 / 207 993 ms**
  of API time. A `claude -p` cannot start Node, authenticate and round-trip a
  provider in 145 ms.
- The error is `unparseable CLI output:` with **nothing after the colon**. That
  message is `(proc.stdout or proc.stderr or "")[:400]`, so stdout *and* stderr
  were both empty. The CLI produced nothing.

The `usd: 4.0` on the record is `MODEL_CALL_CEILING_USD`, a placeholder. It
overstates this call by **27×** against its own siblings ($0.114256 / $0.146292 /
$0.132608, same run, same beat, same model).

## Why I did not file the correction

I intended to file `price_unpriced(usd=0.146292, resolves=1)` — the max of ten
comparable calls — since `price_unpriced` refuses `$0.00`. `clear_unpriced.py`
in this directory is that script. **It was dry-run only and never committed a
write.** An adversarial review refuted it and I accept the refutation:

1. **The provenance I was going to write was false.** I was going to state that
   the ten comparables re-derive from `pricing_v1.json` to within 2.78e-17 of the
   CLI's own `costUSD`. An independent re-derivation came out **4.9–7.9% short on
   all ten**. The two do not agree, so the figure is not verified — and
   `spend_gate` requires provenance precisely because "a correction with no
   provenance is a number somebody typed". Worse, `proxy/cost.py` cannot price
   `claude-haiku-4-5-20251001` at all (exact-key lookup, no date-suffix alias),
   so no tool in this repo can reproduce the claim.
2. **A correction adds; it cannot retract.** `_totals_locked` has no subtraction
   path. Filing $0.146292 would leave the pool asserting that a call which cost
   **$0.00** cost **$4.146292**.
3. **It would moot my own escalation.** I had already asked the monitor to rule
   on exactly this (mailbox 2026-07-29T11:37Z, inbox `20260729T1950Z`). Filing
   before the ruling settles it irreversibly, in an append-only ledger.
4. **It would not hold.** `_invoke` has no retry and the failure had no
   diagnosis, so the next occurrence writes a new blind row, re-blocks the fleet
   and books another $4.00.

So the gate stays shut until the monitor rules, and I fixed root causes instead.
The pool remains at $36.142332 / $214.90 with `unpriced_calls = 1`.

## What I fixed instead

| commit | what |
|---|---|
| `a7e1b507` | the leg's artefacts, committed as evidence before the diagnosis |
| `447ad8cd` | `MANIFEST.json` wrote `branch`/`base_commit` as bare `null`; `_git` swallowed both the exception and the non-zero exit. Now records the reason and emits `provenance_gap` |
| `c65aac8a` | the timeout discarded `TimeoutExpired.stdout` — the one path that most needs a price threw away the only evidence that could supply one. Now salvages a price from a partial envelope, and stays blind when there is genuinely nothing (three negative controls) |
| `6eebe1e3` | **2 817 of the pool's 4 775 actions (59%) were written by pytest.** Three tests called `play()` without a `spend_gate` and got the real pool. All $0.00, so the dollar column stayed clean while the action ceiling was eaten. Tests now own their pool; `open_binding` refuses the tracked pool under `PYTEST_CURRENT_TEST` |
| `658c736d` | one leg's 201 MB candidate stream, which GitHub refuses |

## Still open, and who owns it

* **Monitor** — whether to clear the row at all, and with what number. My
  recommendation is to fix the placeholder first and clear once, rather than
  clearing now and re-blocking on the next timeout.
* **RES-4 / `proxy/`** — `price_unpriced` runs no `_first_breach` (the one
  money-adding entry point with no ceiling check); its `usd <= 0` guard runs
  before `round(usd, 6)`, so `1e-9` clears blindness while recording `$0.00`;
  `cost.py` has no date-suffix alias and reads top-level `usage.input_tokens`
  (9) rather than the billable count (5 944–7 929). Filed in
  `monitor/inbox/20260729T1950Z-RES-1-price-unpriced-holes.md`.
* **Me, next** — `MODEL_CALL_CEILING_USD` is a flat constant calibrated on
  opus-5 and applied to every model. It is 27× too high for haiku and, at
  `ModelDesk.timeout = 1800s` and the observed $0.0023–0.0025/s, **too low for an
  opus timeout** ($4.08–4.44) — which is the exact case that raises and gets
  charged it. `cost.py:93` sets the standard: "a ceiling that is sometimes too
  low is not a ceiling."

## Operational errors made in this cycle, both corrected

1. I wrote local time into the heartbeat and lock as `Z` for the first several
   writes (`19:33Z`–`20:45Z`, actually `11:33Z`–`12:45Z`, +8h). The lock is the
   monitor's only cross-startup liveness signal and a future timestamp would
   read as permanently fresh. Corrected to real UTC.
2. Rewriting the four commits with `git filter-branch` to drop the 201 MB file
   checked out the rewritten HEAD, which **deleted that file from the working
   tree** — it was tracked before and ignored after. Restored from the
   `refs/original` blob: 201 586 613 bytes, 19 486 lines, byte-identical.

## A number worth someone's attention

That stream is **19 486 candidates averaging 10 KB each**. The next largest
tracked stream is 18.8 MB. Whatever the miner emitted on that leg, its per
candidate payload is an order of magnitude off the others, and nobody asked it
to be.
