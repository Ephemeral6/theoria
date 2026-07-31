# `theoria-arm/` — the Theoria arm, online

The third of the three arms in `Theoria.md`'s main table, and the last one to
go online. `bare_cc` measured what zero division of labour costs; the Schema
reproduction measured half; this is full division of labour — engines do the
precise work, the LLM only adjudicates, and the world model is two written
books rather than weights or a session.

```
observe -> [ theorize -> certify -> probe -> plan -> commit ] -> record
```

The outer three beats are shared verbatim with the other arms (1.10(c)), so the
difference between arms is attributable. Everything in the brackets is what
this arm is.

## What is here

| Path | What it is |
|---|---|
| `harness/` | the shared shell: the keyless ARC client, the action budget, the model desk, the runner |
| `world/` | the frame store and the adapters that turn 64×64 ARC frames into each engine's input shape |
| `inner/` | the five beats, the two books, the seven surprises, and the grammar card the desk is held to |
| `armtools/` | `preflight` (prove the live chain for zero quota), `archive` (reconcile, audit, manifest) |
| `runs/` | one directory per run: ledger, trace, books and their snapshots, probes, surprises, desk transcripts, manifest |
| `tests/` | 44 offline tests. No key, no network, no model call, no quota. |

## Run it

Nothing here spends a dollar or opens a socket:

```bash
cd theoria-arm && python -m pytest
```

```bash
cd theoria-arm && python -m harness.run --mock --budget 8 --slug smoke
```

The whole inner loop, still offline, but with a real desk (this one does spend):

```bash
cd theoria-arm && python -m harness.run --mock --desk --model claude-haiku-4-5-20251001 --budget 10 --cost-ceiling 2 --slug dry
```

Live. `preflight` costs **zero** billed actions and proves the key, the guard,
the proxy and the retry envelope all work before anything is spent:

```bash
cd theoria-arm && python -m armtools.preflight --game g50t-5849a774
```

```bash
cd theoria-arm && python -m harness.run --game g50t-5849a774 --budget 120 --model claude-opus-5 --cost-ceiling 20 --slug "$(date -u +%Y%m%dT%H%M%SZ)-g50t-first-contact"
```

```bash
cd theoria-arm && python -m armtools.archive --slug <the slug>
```

## Carrying the books to a second game

The second online game (E3) starts from the first game's manual instead of from
nothing. Only the two hand-written books travel:

```bash
cd theoria-arm && python -m armtools.spend_check \
    --basis-run runs/<the first run> \
    --out runs/<this run>/BUDGET_PLAN.json \
    --game sk48-d8078629 --actions 120 --ceiling 18 --legal-actions 5
```

```bash
cd theoria-arm && python -m harness.run --game sk48-d8078629 --budget 120 \
    --cost-ceiling 18 --prompt-id E3-engines-online \
    --carry-books runs/<the first run>/books --carry-source-game g50t-5849a774 \
    --slug "$(date -u +%Y%m%dT%H%M%SZ)-sk48-carried"
```

```bash
cd theoria-arm && bash verify_e3.sh                 # offline, no quota
cd theoria-arm && bash verify_e3.sh <the live slug> # and the live artefacts
```

**`problem.json` never travels.** It is the level instance, computed from the
frames of the game being played, and carrying it would import the previous
game's board and make the transfer claim unfalsifiable. `transfer.json` names
the exclusion rather than leaving it as an absent line of code.

**The measurement happens before the first model call.** `_cold_transfer` runs
between the opening sweep and the main loop: it computes this level's problem
from the carried manual's own declarations, compiles, and certifies — so the
numbers belong to an *unrepaired* manual. Once the desk has been called, what
is being measured is a repaired manual, and the run can no longer tell the
difference.

**The carried manual predicts its own failure number, and that prediction is
scored.** `render_accounting_closed` states `unexplained(frame_0) = D0 - K` and
claims it is arithmetic runnable in advance. That claim is about this
framework's renderer, not about g50t, so a different game can genuinely test
it. The prediction is written to disk before certify runs, on the same
discipline `probe` follows.

**A refusal is a delivery.** `engines_online.jsonl` gets a row per dispatch per
engine, with `delivered`, `error`, `skipped` and `n_refusals` as separate
columns. `cegis_miner` refusing because a world does not narrate as one mover
is the engine working; an engine that raises or comes back empty without saying
why is not.

**The action budget is not the binding constraint.** At the first run's
measured $1.26 per desk call, a 120-action run costs about $35. `BUDGET_PLAN.json`
computes that from the prior run's cost curve and states which constraint binds
*before* the first action is spent.

## The four things to know before building on this

**The model side is recorded but not proxied.** `proxy/model_proxy.py` strips
`Authorization` by design and injects an `ANTHROPIC_API_KEY` this repo does not
have; pointing the Claude Code CLI at it returns 401 on every request. The
model calls therefore go through `claude -p` — the same transport `bare_cc` is
measured on — and are written into the same ledger by the same frozen writer,
with `proxied: false` on every record. The one thing this loses is that
`request` is the prompt this arm sent to the CLI, not the `/v1/messages` body
the CLI sent onward, so **input-token composition may not be read off this
ledger**. Full reasoning and the archived 401 evidence: `DECISIONS.md` D-P8-002.

**The score obligation cannot be discharged against this API.**
`LEDGER_FORMAT.md` §3 requires the ledger-derived score to equal the
scorecard's. Live ARC command responses contain no `score` field at all — the
key set is `action_input, available_actions, frame, full_reset, game_id, guid,
levels_completed, state, win_levels`. `armtools/archive.py` reports the score
reconciliation as `unavailable` with that reason, and reconciles
`levels_completed` and the action count instead, both of which the API does
return. This is a finding about a Phase 1 obligation, not a passed check.

**The ledger has more steps than the scorecard has actions, on purpose.** ARC's
transient `400 game not found` waves need a 40-attempt envelope;
`proxy/forward.py` does not retry 400, so the arm does, and each retry is its
own request and its own `env_step`. The pre-flight for the first live run
needed 18 attempts for a single RESET. `MANIFEST.json` carries both counts and
the amplification.

**`candidates.jsonl` grows by a full engine sweep per theorize round, and that
is not duplication.** The engines are re-dispatched on the whole history every
time the desk is called, so a run with eight rounds has eight `zero_space`
sweeps in the box — roughly 360 invariant rows each. They are not copies: each
sweep sees more transitions than the last, so the laws it proposes and the
`evidence.transitions` it cites differ. The frozen candidate schema has no
round field (`CONTRACTS/candidates_schema.md`, seven keys, not ours to change),
so `timestamp` and `evidence` are what separate one sweep from another. Expect
a few thousand rows and a few megabytes on a full run; git packs it down by
roughly ten to one.

**The proof layer is usually unavailable on a real level, and says so.** Lean's
enumerative development decides every state in the kernel; a 64×64 grid world
has far too many. The pagoda development needs a LINE world and an
`lp_potential` certificate. `certify.expensive` reports `available: false` with
the state estimate that caused it, and the run's `green` flag stays false. An
unavailable proof layer is never a passed one.

## Territory

This directory is the only thing here that is written. `proxy/`, `engine-rig/`,
`theory-compiler/` and `arc-recon/` are imported and never modified; their
hashes go into every run manifest, because two other sessions have work in
flight in this repo and a silent change upstream would otherwise silently
change these results. `PARTNER_SYNC.md` is append-only.

`baseline-arms/schema_traces/` covers `g50t` and would be legal to read — it is
on the development pile. This arm does not read it. Feeding another arm's
trajectory to this one would give Theoria evidence bare-CC never had, and the
three arms are supposed to differ only in the inner loop. Every frame this arm
reasons over, it paid for.
