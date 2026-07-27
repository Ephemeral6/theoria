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
cd engine-rig && python -m tools.run_all
```

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

## Contract compliance

* `common/candidates.py` is the only writer; it opens candidate files in append
  mode and hardcodes `status: "candidate"`.
* `tools/validate_candidates.py` checks every emitted line against the frozen
  schema; M8 requires the full stream to pass.
* Each engine's `README.md` fixes its payload shape.
