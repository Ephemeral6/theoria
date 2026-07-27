# engine-rig

Six engines from Theoria's workshop (§1.10b), built and proved correct against
synthetic data only. No LLM calls, no game API, no network — this whole
directory runs offline against fixtures it generates itself.

The engines propose; nothing here adjudicates. Every proposal is one appended
line in a `candidates.jsonl` shaped by the frozen contract at
`/CONTRACTS/candidates_schema.md`.

## Layout

```
engine-rig/
  common/          canonical JSON, deterministic PRNG, candidate writer
  fixtures/        the three synthetic worlds + their ground truth
    data/          generated artefacts (checked in; regenerable byte-for-byte)
  engines/
    mdl_segmenter/   diff -> objects and events, by minimum description length
    cegis_miner/     counterexample-guided rule synthesis (guard + effect)
    zero_space/      GF(2) null space -> linear conservation laws
    lp_potential/    pagoda weights: unsolvability certificate + admissible heuristic
    fd_adapter/      PDDL -> planner -> plan
    probe_frontier/  which action splits the hypothesis frontier hardest
  tools/           schema validator, integration runner
  tests/           acceptance tests, one module per engine
  DECISIONS.md     design calls and their reasons
  STATUS.md        milestone state, blockers
```

## Running

Regenerate the fixtures (same seed, same bytes):

```bash
cd engine-rig && python -m fixtures.generate_all
```

Run the acceptance suite:

```bash
cd engine-rig && python -m pytest
```

Run every engine end to end and validate the candidate stream:

```bash
cd engine-rig && python -m tools.run_all --force
```

which prints:

```
engine-rig integration run
------------------------------------------------------------------------
  mdl_segmenter   1 object(s), 42 events, 826 vs 2888 bits (ratio 0.286)
  cegis_miner     10 rules; push cov 41/41, teleport cov 1/1; guards exclusive=True, total=True
  zero_space      null space dim 9; global law: (#R) mod 2 = 0
  lp_potential    w=['-1', '1', '0', '1'] certifies 1110 unsolvable; conditions all true
  fd_adapter      stub-bfs plan of length 5
  probe_frontier  probe UP worth 1.000 bits
------------------------------------------------------------------------
  candidates: 24
  SCHEMA    : OK -- every line satisfies CONTRACTS/candidates_schema.md
```

Validate any candidate stream on its own:

```bash
cd engine-rig && python -m tools.validate_candidates artifacts/candidates.jsonl
```

## The checked-in candidate stream

[`artifacts/candidates.jsonl`](artifacts/candidates.jsonl) is the M8 output,
committed: 24 proposals, all six engines, all six candidate kinds. It is produced
in deterministic mode (frozen timestamps, uuid5 over each candidate's content) so
that it is byte-stable and regenerating it produces no diff:

```bash
cd engine-rig && python -m tools.run_all --out artifacts/candidates.jsonl --deterministic --force
```

A test asserts the committed file equals a fresh run byte-for-byte, so it cannot
go stale silently. `out/` stays untracked scratch for ordinary runs, which use
real uuids and wall-clock timestamps exactly as the contract reads.

## The three synthetic worlds

**A · Cart world** (`fixtures/cart_world.py`) — 12x12 grid, one 2x3 colour-6
block, push dynamics, plus exactly one teleport event. Feeds `mdl_segmenter` and
`cegis_miner`. The teleport is the deliberately thin evidence: one transition,
coverage 1/1, the thing a miner must flag rather than generalise from.

**B · Pair-Flip world** (`fixtures/pair_flip.py`) — 8 cells, each red or blue,
`flip_pair(i,j)` inverts both. `(#Red) mod 2` is invariant. Feeds `zero_space`.

**C · 4-cell peg solitaire** (`fixtures/peg4.py`) — fully enumerated state graph.
`1101` reaches the goal `0100` in 2 moves; `1110` provably cannot. Feeds
`lp_potential`. This is the minimal rehearsal of the A1 pagoda argument, with no
DSL involved.

## What each engine was held to

| Engine | Acceptance result |
|---|---|
| `mdl_segmenter` | masks identical to ground truth on all 50 frames; script 826 bits vs 2888-bit pixel baseline |
| `cegis_miner` | `push` at coverage 41/41, `teleport` at 1/1; guards mutually exclusive and total |
| `zero_space` | recovered space == `(#Red) mod 2` plus the encoding's own laws, as a subspace identity |
| `lp_potential` | all three certificate conditions exact over ℚ; no certificate for the solvable config; heuristic admissible everywhere |
| `fd_adapter` | 5-action plan = hand-verified optimum, cross-checked by an independent validator and by exhaustive enumeration |
| `probe_frontier` | picks `UP` at exactly 1 bit, matching the hand computation; 0 bits for every other action |

Two results are worth reading as findings rather than checkmarks: `cegis_miner`
returns a *frontier* where the evidence cannot separate guards (rather than
guessing), and `lp_potential` is sound but incomplete — configuration `0111` is
unsolvable and no linear pagoda proves it, which is asserted by a test.

## Contract compliance

* `common/candidates.py` is the only writer; it opens candidate files in append
  mode and hardcodes `status: "candidate"`.
* `tools/validate_candidates.py` checks every emitted line against the frozen
  schema; M8 requires the full stream to pass.
* Each engine's `README.md` fixes its payload shape.
