# a0-spike — the A0 cold start

Theoria.md Phase 1 calls A0 第一优先: a self-built world with fully known ground
truth, zero API, zero contamination, run cold through the whole loop —
**perceive → mine → adjudicate → certify → plan → win, plus one conservation
theorem**. The bet of the whole framework rests on `theorize`, and A0 is where it
gets tested cheaply enough to fail cheaply.

> This directory is deliberately separate from `cold-start-a0/`, which the other
> track is working in. Nothing here touches it.

```bash
cd a0-spike && python -m pipeline.run_a0     # the whole loop
cd a0-spike && python -m pytest              # 18 acceptance tests
```

## The world

A sokoban variant in which **a push slides the box two cells**, not one. That is
the design choice that makes the last deliverable real: in ordinary sokoban the
box changes checkerboard colour on every push and nothing is conserved. Sliding
two cells keeps it on its own colour forever, giving a law that is true,
provable, inside the frozen invariant language (mod-2 parity), and *useful*.

Two levels, differing **only** in the target square:

| level | box | target | parity | truth |
|---|---|---|---|---|
| `match` | (3,3) | (3,1) | equal | solvable in 2 |
| `mismatch` | (3,3) | (3,2) | opposite | unsolvable |

The pair is the experiment. A framework that can only search cannot tell them
apart from the inside — it reports "no plan found" and cannot say why. A
framework with the law answers the second in one arithmetic step, and says why.

## What the run does

```
explore   60 episodes, 341 actions, 341 transitions
perceive  5 objects (2 move, 3 settle into the board); 373 vs 412 bits
mine      17 rules
certify   341 transitions replayed; exactly-one-successor=True, exact=True
prove     (box.row + box.col) mod 2 = 0   (conserved)
match     solved in 2 actions -> box on target: True
mismatch  unsolvable: box parity 0, target parity 1 -- the box never leaves its colour
```

Both verdicts agree with ground truth; the plan is optimal. On `mismatch` **the
planner is never consulted** — the theorem answers first.

## The three findings worth reading

**1. The under-guarded push rule — DC22 in miniature.** The first pass, on a
casual 28-step walk, mined `act==D and ahead_is_box(D) → box slides two`, with one
witness per direction, and **replay was exact**. The rule is still wrong: it
predicts a push when the box has nowhere to go. Accepting it because replay
passed is precisely the failure the framework exists to catch. The fix was to
plan exploration around *situations* rather than *outcomes* — "box ahead but its
path obstructed" is a distinct situation even though it looks like every other
"nothing happened" — and re-mine. The guard gained `box_beyond_free(D)` and the
witness count went from 1 to 12–19 per direction. Cost: 341 actions.

**2. The guard language bites, and the contract holds.** With enough evidence the
`blocked` class is genuinely disjunctive — a wall ahead, *or* a box that cannot
slide — and no single conjunction covers it. `cegis_miner.synthesize` raised
`NoSeparatingGuard`, correctly. Rather than add disjunction to the guard language
(a contract change), the class is learned as *several* rules whose guards are each
conjunctions. Every rule stays inside the frozen grammar.

**3. The engine corrected the adjudicator.** I proposed `(row+col) mod 2` as the
law. `zero_space` returned a null space of dimension **2** — `row mod 2` and
`col mod 2` are each conserved separately, which is strictly stronger and equally
true. The stronger pair went into the manual. This is the division of labour
working in the direction it was designed to: the engine computes, the LLM
decides, and the LLM was wrong.

Full reasoning, decision by decision: [THEORIZE_LOG.md](THEORIZE_LOG.md).

## Known warts

* `blocked_DOWN_1` carries literals about LEFT and RIGHT that are accidental —
  greedy sequential covering found a local optimum. It is sound on all 341
  transitions (replay exact, one successor everywhere) but it is not the rule a
  person would write. Left as mined rather than hand-edited: the manual should
  say what the evidence forced.
* The compression win is modest (373 vs 412 bits). This world's typical
  transition moves one cell, so a pixel dump is only two edits. The Cart
  fixture's 0.29 ratio is not the number to expect here.

## Layout

| Path | Contents |
|---|---|
| `world/sokoban2.py` | the world and its ground truth — imported only to generate frames and to grade |
| `world/levels.py` | the two levels, and the BFS oracle |
| `pipeline/explore.py` | prefix-replay episodes targeting discriminating situations |
| `pipeline/stages.py` | perceive / mine / certify / prove, over engine-rig |
| `pipeline/dnf.py` | sequential covering for disjunctive effect classes |
| `pipeline/pddl_gen.py` | the planning form of the same rules |
| `pipeline/run_a0.py` | the loop |
| `theory/theory.dsl` | what was adjudicated — parses against the frozen grammar |
| `THEORIZE_LOG.md` | why each thing was adjudicated |
