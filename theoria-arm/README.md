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
