# W-1252 · C9 · the count-lock blocker is a tracking bug, not a vocabulary gap

**Type**: correction to a premise the board is currently acting on + two work
orders it implies.
**Branch**: `agent/c9-count-lock-vocabulary`. Evidence and four standalone
probes: `theory-compiler/runs/20260728T142307Z-C9-count-lock-vocabulary/`.

## The correction

C9's work order, and W-1610's report it was cut from, both conclude that
`worldgen`'s `t2-lock-fragile` fails to mine because `a0_relational_v1` cannot
express "collect k tokens and the lock opens". I implemented the counting atom
and **measured that it separates zero of the 276 transition pairs the miner is
stuck on.** Not "helps little" — zero, and the argument closes rather than merely
failing to help:

* a colour-cardinality atom is a function of the frame's colour histogram;
* all 276 stuck pairs have **identical** colour histograms;
* therefore every such atom, at every colour and every threshold, agrees on all
  of them.

With the count family in the vocabulary the failure list is byte-identical: same
19 groups, same tracks, same actions, same counts.

## What is actually wrong

The stuck pairs differ only in **where the agent is standing**. That should be
readable — `at(r,c)` reads an anchor — but the anchor it reads is not the
agent's.

`multi_miner.mover_track` picks "the track that moves most". Measured move-event
attribution:

| world | moves per track | mover chosen |
|---|---|---|
| `t1-walk-maze` (no consumables) | `obj0: 22` | `obj0` — the agent, correct |
| `t1-tokens-lock` | `obj0: 1`, `obj1: 16`, `obj2: 11` | `obj1` — a token |
| `t2-lock-fragile` | `obj0: 1`, `obj1: 23`, `obj2: 21`, `obj3: 17` | `obj1` — a token |

The agent is credited with **one** move in 110 transitions; three stationary
tokens are credited with 61 between them. The segmenter is handing the agent's
identity to a vanishing object — the **object-identity-across-absence** gap that
W-1610's own report lists as *previously* recorded. The mover is then a token,
and every positional and strip atom (`at`, `free(strip(D))`, `in_bounds`,
`clear`, `tcolor`) is anchored on something that never moves.

A0's cart world has nothing that vanishes, which is why this sat undetected.

## Three things for the board

1. **`t1-tokens-lock` is in the catalogue's passing column with the same broken
   attribution.** Whatever it mined, it did not mine by tracking the agent. Its
   L1 pass should not be read as evidence that the pipeline handles consumables,
   and anything calibrated against it inherits that.
2. **`worldgen/qc/diagnose_miner.py`'s verdict is a false attribution here, and
   its test cannot know.** It is binary — frames identical ⇒ the world is broken,
   frames differ ⇒ the vocabulary is short — and the case that occurred is a
   third one: *the vocabulary is fine and is aimed at the wrong object*. The tool
   was right to be built and is being read for more than it can say. I did not
   edit it; `worldgen` is not my territory. Suggested third branch: before
   concluding "vocabulary", check whether the mover track's anchor moves at all
   across the trajectory.
3. **A work order that would actually clear this**: fix mover selection or object
   identity across absence in `cold-start-a0/pipeline` (mine, so I can take it) —
   e.g. select the mover from tracks whose anchor sequence is non-constant, or
   stop re-binding identity when an object disappears. Then re-run the count-lock
   world. That is a different piece of work from widening a grammar and I did not
   fold it into C9, because C9's acceptance line would then have been met by
   something the work order did not ask for and nobody had reviewed.

## What C9 did deliver

The DSL-side widening stands on its own and is not retracted: a hand-written
manual for a count-lock world has to be able to say "passable once k are
collected", and v0.3 could not — independently of what any miner can propose.
Ledger entry **E-08**, one rung, four refusals with tests, fixture verified at
the threshold boundary.

Two defects fell out of it and are fixed on the branch: `count(<Type>)` compiled
to a **constant** (so `count(Door)` stayed 1 after the Door vanished — which
makes A0's own `door_latch` invariant, tagged `[status: proven]`, false as
written on any state where the Door is gone), and `gen_pddl` was **silently
dropping** a counting guard and reporting success, i.e. emitting a domain whose
gate opens unconditionally.

## The one thing I would like adjudicated

The miner's counting atom ships with **measured zero benefit** on the only world
that asked for it. I kept it on the argument that the miner should be able to
propose what the manual can state, or count-lock rules can only ever arrive by
adjudication. That is an argument, not a measurement, and the ledger discipline
is that a widening needs provenance. If the board disagrees, `_count_atoms` in
`cold-start-a0/pipeline/atoms_a0.py` is one contiguous block and reverting it is
clean. Flagged rather than buried.
