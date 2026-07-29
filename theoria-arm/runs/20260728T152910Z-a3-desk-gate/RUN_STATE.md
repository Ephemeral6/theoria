# A3 — the desk's spend gate

`prompt_id` A3-campaign-devpile · branch `agent/a3-campaign-devpile` ·
base commit `dc9865a1b5edd432350d4a7bee4b218776e135d5` · 2026-07-28T15:29:10Z

Offline throughout. No network call, no API key, no `claude -p` subprocess,
$0.00 spent. Every gate record produced here landed in a scratch pool in a temp
directory, not in `proxy/var/spend_gate.jsonl`.

## What was wrong

The board item's red line is *"每局动作预算先算后花、必须经
proxy/spend_gate.py reserve()，闸门红了立刻停"*. Half of it held, and not the
expensive half.

* **ARC actions were gated, by accident of routing.** `harness/arc.py` posts to
  the environment proxy, and `proxy/env_proxy.py:308,344` mints a permit and
  records the attempts. Nothing in this arm asked for that. It is where the
  pool's `theoria:r-<runid>` rows at **$0.00** came from — an auto-derived name
  and a dollar column that was not zero but absent.
* **Desk dollars were not gated at all.** `harness/modelcall.py` shells out to
  `claude -p` (the model proxy strips `Authorization` and there is no
  `ANTHROPIC_API_KEY`; 65 `model_call` @401 in
  `evidence/model-proxy-401.jsonl`). The one live g50t run spent **$6.317658**
  against a `cost_ceiling_usd` float inside one process. `grep -rn spend_gate
  theoria-arm/**/*.py` returned one false positive.

INC-BA-003's verdict applies verbatim: *"事故不在任何一方跑错，而在于没有任何
一方的闸门看得见另一方的花费。"*

## What changed

| file | what |
|---|---|
| `harness/spend.py` | new. `plan_caps` / `open_binding` / `SpendBinding`, the one-true-pool assertion, the latch. |
| `harness/modelcall.py` | `ModelDesk` takes a binding; `check` before the subprocess, `record` after, always. |
| `harness/run.py` | `Run` opens **one** reservation, names the campaign, hands the same claim to the env proxy, releases in a `finally`. |
| `tests/test_desk_gate.py` | new, 30 tests, all against temp-dir pools. |

Two ceilings, both kept, deliberately independent: the arm-local
`cost_ceiling_usd` stops the run on its own account and fires first;
`usd_cap = cost_ceiling + one call's ceiling` means the pool's cap is not what
stops a well-behaved run, and is there for when the arm-local one is wrong,
absent, or not the only spender.

## The arithmetic

Unit: **one outbound ARC HTTP request**, which `spend_policy.json` says is *not*
the scorecard's successful-action count. Neither of this arm's two counters is
that unit, so both are converted:

    arm_attempts = 3 + ceil(actions x 1.75 x 1.5)     # 1.75 measured, 1.5 tail
    arm_attempts = min(arm_attempts, commands)        # Budget.commands stops first
    action_cap   = arm_attempts x env_max_attempts    # env proxy retries inside
    hard_bound   = commands x env_max_attempts        # the only true bound
    usd_cap      = cost_ceiling_usd + model_call_ceiling_usd

`--budget 12`: `3 + ceil(12x1.75x1.5) = 35`; `35x3 = 105` actions, `$24.00`.
`--budget 120` (P-8 live): `3 + 315 = 318`; `318x3 = 954` actions, `$24.00`.

`MODEL_CALL_CEILING_USD = 4.00` is ~2.7x the worst desk call ever observed here
($1.489011, `runs/20260728T015354Z-g50t-first-contact/desk_log.json`, 5 calls,
$6.317658 total).

## The proof

`scratch-pool.jsonl` — `python -m harness.run --mock --budget 6 --slug
a3-gate-mock --pool <temp>` followed by `prove_desk_offline.py`, phase A.
Eleven rows for the mock run: one `reserve` naming
`theoria-arm:A3-campaign-devpile:g50t-5849a774:a3-gate-mock`, nine action
`spend`s, one `release`. Then phase A's desk rows: `$1.489011` priced, `$4.00`
unpriced from a call that raised, and the third call **refused before it
started** with `UNPRICED_SPEND`.

`scratch-pool-b.jsonl` — phase B, on a fresh pool because phase A left the
first one blind on purpose: an envelope with no `total_cost_usd` settles at
`$4.00` with `unpriced: true`, never `$0.00`.

`proof-output.txt` is the transcript.

## Two things worth carrying forward

* **An unpriced call blinds the whole pool's dollar axis**, for every session,
  until a human runs `price_unpriced()`. That is `spend_gate.py`'s design and
  the price of charging a ceiling rather than a zero. Phase A demonstrates it
  rather than tuning it away. A priced envelope whose `usage` block is merely
  incomplete is deliberately **not** flagged — the price came from
  `total_cost_usd`, so the total is still exact, and flagging it would brick the
  shared pool on a missing token count.
* **`test_arm.py`'s two mock tests write into a stable, gitignored ledger path**
  (`runs/pytest-<tmp_path basename>/ledger.jsonl`) that pytest reuses across
  sessions. `Ledger._seq` is seeded per object from the file's max, so repeated
  or concurrent invocations break LEDGER_FORMAT.md invariant 2. Reproduced with
  `proxy.ledger.Ledger` alone, two processes, one file: seqs
  `[1,2,3,4,5,1,2,3,4,5]`. Not caused by this change; `rm -rf runs/pytest-*`
  clears it.
