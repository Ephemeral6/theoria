# STATUS — theoria-arm

**Milestone: E3, the second online game.** Branch `agent/e3-engines-online`,
base commit `e182c95`. The previous milestone, P-8 (first online contact), is
recorded below and unchanged. This file is the state of the track; the reasons
live in `DECISIONS.md` and the per-run account in `runs/<slug>/MANIFEST.json`.

---

## E3 — carrying the books to sk48

P-8 proved the loop turns online. E3 asks two different questions, and neither
of them is about winning:

1. **does the engine supply chain hold up on a live game** — one row per
   dispatch per engine in `engines_online.jsonl`, with `delivered`, `error`,
   `skipped` and `n_refusals` as four separate columns, because a refusal is an
   engine working and an error is not;
2. **does a written theory transfer to a game it was not written for** — the
   g50t manual is carried into sk48 and certified *cold*, before the first
   model call, so the numbers belong to an unrepaired manual.

The game is **sk48-d8078629**, and tn36 was excluded for a mechanical reason
rather than a preference: `precheck.json` records its `available_actions` as
`[6]`, ACTION6 is the click family that `_legal_actions` filters out (D-P8-012),
and the arm would have found no legal action and stopped before its first turn.
sk48 offers `[1, 2, 3, 4, 6, 7]`. Pre-flight on it cost **0 billed actions**:
64×64, ten colours, eight levels, RESET in 5 attempts, and no `score` field —
the same Phase 1 obligation gap P-8 reported, unchanged.

### The pre-registered number

The carried manual does not only assert things about g50t. One theorem states a
*formula* — `unexplained(frame_0) = D0 - K` — and claims it is arithmetic that
can be run in advance. That claim is about this framework's renderer, not about
g50t, so a different game can genuinely test it. Evaluated on sk48's opening
frames and written to disk **before** certify ran:

| | |
|---|---|
| D0 (dynamic non-background cells at t0) | 73 |
| K (distinct declared colours present at t0) | 3 |
| **predicted unexplained cells** | **70** |

`transfer.json` carries a `prediction-only` revision with that number and no
certify result in it, then a `cold` revision with the verdict. The discipline is
`probe`'s: a prediction recorded after its result is not a prediction.

### Before the money

`armtools/spend_check.py` runs first and writes `BUDGET_PLAN.json`. Two things
come out of it.

**S3's shared spend gate has not landed.** `proxy/spend_gate.py` does not exist
on this commit and `agent/s3-spend-gate` carries nothing matching `*spend*`
under `proxy/`. The gate is looked for every time, used if present, and
recorded `absent` with no reservation held if not — never as a pass. A test
pins that.

**The action budget is not the binding constraint.** At P-8's measured $1.2635
per desk call, reaching 120 actions costs about **$35**; an $18 ceiling stops the
run at roughly **29–61 actions**. Saying so before the first action is what makes
the outturn a measurement of the bill's shape rather than a shortfall against
120.

```bash
cd theoria-arm && bash verify_e3.sh                 # 78 tests + a carried mock run
cd theoria-arm && bash verify_e3.sh <the live slug> # and the live artefacts
```

---

## P-8 — where the first online contact stands

The three arms of `Theoria.md`'s main table are: `bare_cc` (zero division of
labour, measured), the Schema reproduction (half), and this one (full). This is
the last of the three to go online, and it is the first time the inner loop —
proved four times offline in `a0-spike`, `cold-start-a0`, A1 and
`cold-start-a2` — has been connected to a real environment through the double
proxy.

The goal set for it was **not** to win. It was that the loop turns online and
that the books balance: the seven surprises counted for real, theorize rounds
counted for real, and a per-turn cost curve measured rather than predicted.

**Three live runs, two of them aborted on defects in this arm.** The honest
headline of the milestone: the inner loop had been proved four times offline
and still carried three defects that only a live 64×64 world surfaced. All
three are fixed, all three are recorded with the evidence that found them, and
the cost of finding them — 11 actions and $2.05 — is counted in this track's
totals rather than written off. `GAPS.md` is the contract read back line by
line, `INCIDENTS.md` INC-TA-004 is the account of the aborts, and the aborted
runs are archived intact rather than deleted.

## The suite

```bash
cd theoria-arm && python -m pytest          # 46 passed
```

No key, no network, no model call, no quota. Every property the live run
depends on is pinned before an action can be spent: the short-id refusal
(INC-005), which statuses are retryable and which are not, the action ceiling
and RESET's exemption from it, the arena crop's declared coverage, the law-cell
cap's declared narrowing, that certify turns a raising predictor into a finding
rather than a traceback, that a manual with no goal is not an unsolvability
claim, that a probe's prediction reaches disk before its result, that the
grammar card's worked example still compiles, and that the ledger the arm
writes satisfies `LEDGER_FORMAT.md` §1–§3.

## Pre-flight, live, zero quota

`python -m armtools.preflight --game g50t-5849a774` opens a scorecard, sends one
RESET and closes. RESET is not billed, so this exercises the entire live chain
for nothing:

| what | result |
|---|---|
| key injected inside the proxy, arm keyless | yes (`key_injected: true`) |
| guard fingerprint | `3feca53e…41bbc19a`, cut `v1`, 4 dev / 21 sealed |
| RESET | 200 — **after 18 attempts** |
| frame | one 64×64 grid, colours `{0, 1, 5, 8, 9}` |
| `available_actions` | `[1, 2, 3, 4, 5]` |
| `win_levels` | 7 |
| `score` field in the response | **absent** |
| billed actions | 0 (`scorecard.total_actions: 0`) |

Two of those lines are load-bearing findings rather than green ticks:

**18 attempts for one RESET.** `arc-recon`'s wave-outlasting envelope is not a
historical artefact — the wave was active at launch. `proxy/forward.py`'s
5-attempt envelope, which does not retry 400 at all, would have failed here.
See `DECISIONS.md` D-P8-003.

**No `score` field.** `LEDGER_FORMAT.md` §3 makes the ledger-derived score
equalling the scorecard's a *hard obligation*, and it is not dischargeable
against this API: the response key set is `action_input, available_actions,
frame, full_reset, game_id, guid, levels_completed, state, win_levels`.
`armtools/archive.py` reports it as `unavailable` with that reason and reconciles
`levels_completed` and the action count instead. Reported, not waived.

## The declared gap: the model side is not proxied

`proxy/model_proxy.py` cannot record this arm's model calls. Tried live before
the arm was written: the Claude Code CLI authenticates with an OAuth bearer,
the proxy strips `Authorization` by design and injects an `ANTHROPIC_API_KEY`
that does not exist in this repo's `.env`, and upstream answers `401 x-api-key
header is required` to every request. 65 such `model_call` records and 66
`bypass_attempt` incidents are archived at `evidence/model-proxy-401.jsonl`.

The stripping is the sealing property, not a defect, and fixing it means
editing another track's directory or acquiring a key this repo does not have.
So the calls go through `claude -p` — the transport `bare_cc` is already
measured on — and are written to the same ledger by the same frozen writer,
carrying `proxied: false`. **What is lost:** `request` is the prompt this arm
sent the CLI, not the `/v1/messages` body the CLI sent onward, so input-token
composition may not be read off this ledger. Output usage and cost are
unaffected. Full account: `DECISIONS.md` D-P8-002.

## Standing limits, stated up front

* **The proof layer is usually unavailable on a real level.** Lean's
  enumerative development decides every state in the kernel; a 64×64 grid world
  has far too many, and the pagoda development needs a LINE world plus an
  `lp_potential` certificate. `certify.expensive` reports `available: false`
  with the state estimate that caused it and the run's `green` flag stays
  false. An unavailable proof layer is never a passed one.
* **`gen_pddl` is the weakest of the four generators** — it ignores the level
  instance, hardcodes objects to cell (0,0) and does not expand `forall` — so
  the designed PDDL→Fast-Downward planning route is expected to refuse on a
  real manual. It is tried anyway and its refusal is recorded as evidence about
  the generator. The ladder's first rung (object-state BFS over the manual's
  own predictor) is what actually plans.
* **`cegis_miner` may refuse outright.** Its precondition — exactly one `move`
  event per transition — is a real claim about a world, and a real game need
  not satisfy it. The refusal is recorded per track, never worked around.
* **Constraint 9 is checked, but sampled.** Ambiguity is tested by driving the
  states the run actually visited through every declared action. That is not a
  proof over all states and the report says `scope: sampled`.
* **Determinism holds for everything except the desk's text.** Engine dispatch,
  the four generators and the planner are deterministic; `claude -p` exposes no
  sampling seed. The manifest records `seed: null` with that reason, and every
  desk prompt and reply is archived verbatim as the substitute.

## Territory

Written: `theoria-arm/` only. Imported and never modified: `proxy/`,
`engine-rig/`, `theory-compiler/`, `arc-recon/` — their sha256s go into every
run manifest, because two other sessions have work in flight in this repo.
`PARTNER_SYNC.md` is append-only. `master` is untouched; this work is on
`agent/p8-theoria-arm` in its own worktree.

`baseline-arms/schema_traces/` covers `g50t` and is on the development pile, so
reading it would be legal. This arm does not, because feeding another arm's
trajectory to this one would give Theoria evidence bare-CC never had and the
three arms are supposed to differ only in the inner loop.
