# S31 — fourth pickup. Two of the four were already on master; the other two are new.

Worker `W-1800`, cleanup-campaign resumption batch. Branch `cleanup2/s31-a10`,
worktree `.worktrees/s31-a10/`, base `6fabcc7e`. Territory `proxy`.
**Zero API calls, $0.00, zero sealed-pile contact, no credential value read or
written.**

The relay on this item is now four deep — W-1691 (died mid-sentence), W-1702
(wrote the substance, never pushed), W-1710 (pushed it, verified it), W-1800
(this run). The item was returned untouched by the cleanup campaign at
2026-07-31T09:06Z and re-dispatched.

## The first thing was to check whether there was anything left to do

There was, but not what the ticket says. Requirements 1, 3 and 4 are **on
`master` today** and I re-verified each rather than inheriting it
(`evidence/branch_state.txt`, `evidence/audit_delivery.txt`,
`evidence/req4_amount_mismatch.txt`):

| ticket requirement | state | where |
|---|---|---|
| 1 — which of the three cases is A10 | already delivered | `proxy/DELIVERY_RULING.md`, executable as `tools/audit_delivery.py` (re-run, exit 0) |
| 2 — one minimal real-arm call | diagnostic half done offline; **live half prepared, not fired** | `LIVE_PROBE_PLAN.md` + `live_probe.py` in this directory |
| 3 — land the reconciliation ruling | already on master, in amended form | `RECONCILIATION_KEY`, commit `26b387e5` — **and now gated**, see below |
| 4 — negative sample, amount mismatch goes red | already on master | `tests/test_reconcile_amount.py`, 8 passed; demonstrated again in `evidence/amount_mismatch.txt` |

**And S31's own branch is stale, not unmerged.** `agent/s31-a10-said-done-prove-it`
has exactly one commit `master` does not contain, and it is a merge commit; the
two-dot diff over `proxy/` is 48 insertions against 1115 deletions, i.e. `master`
is *ahead*. Merging it would be a regression. The ruling is appended to
`DELIVERY_RULING.md` §7 so this is not asked a fifth time, together with the
reading rule that would have caught it: a non-empty `git log master..<branch>`
containing only merge commits is the signature of a branch that is *behind*, and
it looks identical to one that is ahead if you only count lines.

## What is actually new in this pass

### 1. The reconciliation ruling is now enforced, not restated

Requirement 3's premise is misattributed — the `(cost × actions × turns)` triple
is monitor finding F-19, not S29, and **F-19 withdrew the `turns` leg the same
day it published it** (`monitor/spec.py:653-654` asks for it, `:678-681` takes it
back). Three previous passes have each had to rediscover that, and each time the
only thing standing between the document and the mistake was somebody reading
carefully.

`proxy/tests/test_ledger_format_sync.py` (new, 7 tests) makes it a gate. It reads
the voting legs out of `LEDGER_FORMAT.md` §3's own table and the gap names out of
a real `reconcile_run` report, and goes red when the two disagree — in particular
when a quantity the reconciler reports as a **non-voting gap** is written up in
the canon as a **leg of the obligation**, which is exactly the shape of both
near-misses this section has had. Four negative controls, one per drift
direction, are parametrized in the same file; the parse and every red is archived
at `evidence/doc_code_sync.txt`:

```
legs declared in the table   ['actions', 'cost', 'score_per_run']
RECONCILIATION_KEY           ['actions', 'cost', 'score_per_run']
gaps in a real report        ['score_per_step', 'turns']
GREEN: no drift
```

It is deliberately **not a digest**. `LEDGER_FORMAT.md` is still being edited, and
a byte check would go red on somebody else's correct prose while staying green on
a leg quietly renamed inside the table.

Two additive edits to `LEDGER_FORMAT.md` §3 make the gate exact and say it is
there: the per-step-score bullet now names `gaps.score_per_step` and its
`NOT_CROSS_VERIFIABLE` verdict the way the turns bullet already named
`gaps.turns`, and a short paragraph records that the section is held in sync by a
test rather than by care. No field, no record shape and no `v` changes.

### 2. The live probe is one command, and the command is not fired

`live_probe.py` dry-runs by default: it computes every number the live run would
use from the same functions the gate uses, prints the exact reservation and the
record shape that would prove success, and opens no socket. `--go` fires it and
requires `--authorised-by`.

Two rungs, because the cheaper one is a complete witness:

* **rung 1 (default)** — ARC upstream live, model upstream on the loopback mock.
  **$0.000000 of model spend**, 4 ARC requests. Produces
  `run_start.env_upstream = https://three.arcprize.org`, which is axis 2, which
  is the only proposition the offline probe left open.
* **rung 2** — both live. Adds one `/v1/messages` call at a ceiling of
  **$0.009688** (`claude-haiku-4-5`, `max_tokens=256`, 4204 input tokens
  estimated at a pessimistic 3.0 chars/token, 1h-cache multiplier 2.0 — computed
  by `PriceTable.ceiling_for`, the same function `model_proxy.py:218` uses to
  decide whether to open the socket).

The reservation is **declared**: `reserve("s31-live-arm-probe", 0.05, 10,
holder={..., "undeclared": False})`. This is why it is a script and not
`python -m proxy.runner --game … --arm bare_cc`: that CLI has no `--usd-cap`, so
it falls through to `default_run_caps` — $5.00 and 600 actions, stamped
`undeclared: True`, 500× the ceiling this probe can reach. `spend_policy.json`'s
own provenance note says the defaults exist to make *not* declaring inconvenient.

Three refusals, all exercised and archived in `refusals.txt`:

```
REFUSED: the id given is not in the development pile.   (whitelist is positive;
         the sealed list is never loaded, and the refused id is NOT echoed —
         a refusal that repeats what it refused would write a sealed id into
         whatever captured the output)
REFUSED: --go needs --authorised-by. A live call carries a name.
REFUSED: rung 2 needs ANTHROPIC_API_KEY and it is not set.   (checked BEFORE the
         reservation, so a run that cannot pay does not first take the pool's
         headroom and then fail)
```

The shared pool is unchanged across this pass — `$36.1423 / $214.90 spent, 0
held, 0 live reservations` (`evidence/pool.txt`, taken after the refusals were
exercised).

## Two things found while doing it

* **`ANTHROPIC_API_KEY` is not in `.env.example`.** Only `ARC_API_KEY` is. Rung 2
  cannot run without it and nothing documents the variable name. `.env.example`
  is repo-root shared ground, so this went to `monitor/inbox/` as a request
  rather than being edited here.
* **A worktree splits the money from the evidence.** `proxy/paths.py` resolves
  `LEDGER_PATH` and `.env` from `__file__`, so both are worktree-local — but
  `SpendGate` walks to the main checkout on purpose, so the *pool* is genuinely
  shared. Firing the live rung from a worktree would charge the shared pool and
  write the evidence into a gitignored file nobody audits. It would in fact
  refuse first, on the absent key, but that ordering is luck rather than design,
  so `live_probe.py` prints a banner when it detects a worktree and
  `LIVE_PROBE_PLAN.md` §5 states it as precondition 1.

## Gates

```
cd proxy && python -m pytest              ->  421 passed in 66.77s
                                              (414 baseline + 7 new)
cd proxy && python verify.py              ->  proxy: green -- 5/5 stages
```

`verify.py` stage by stage: suite 421 passed; spend gate has no off switch and no
stray egress; one game through both proxies offline; 61 records, seq dense 1..61,
one run_id, all 6 envelope fields, LEDGER_FORMAT v1.0 clean; win_tighten
degeneracy guard refused the marked stream (exit 2) and passed it unmarked.
Full output in `evidence/verify.txt`.

## Gaps left open

* **The zero-real-arm state is unchanged and still real**, and it still belongs to
  the three arm territories rather than to `proxy`. `theoria-arm` needs
  configuration only (`harness/run.py` takes `ledger_path` and `main()` never
  forwards it); `baseline-arms` and `ablation-arm` need source changes, and
  `ablation-arm` has D-AB-004 pointing the other way. Requested as three items in
  the inbox note; not done here, and not doable here.
* **Axis 2 has still never been witnessed.** That is the whole point of the
  prepared probe, and a green rung 1 would witness only that — it would not close
  the gap above. One probe record would make the ledger's histogram read `1` and
  still not mean the arms are running.
* **Cost reconciliation cannot witness an amount on `/v1/messages`**, which
  returns no per-model breakdown. `amount_not_witnessed` reports it and the leg's
  note says so; on that transport a uniformly inflated usage block still
  reconciles. Unchanged from the previous pass, restated because it is the one
  limit of requirement 4's answer.
* The sync gate covers the reconciliation section of `LEDGER_FORMAT.md` and
  nothing else. The rest of the canon is still held together by reading.
