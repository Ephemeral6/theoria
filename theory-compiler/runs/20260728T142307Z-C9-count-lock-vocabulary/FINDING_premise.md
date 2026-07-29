# C9 · the count is not what the miner cannot see

**Status: measured, reproducible, and it changes the work order's premise.**
Written before any of C9's own deliverable, because the four probes in `probes/`
are the finding and everything else follows from them.

## What the work order and the upstream report say

W-1610's report
(`monitor/inbox/archive/20260728T093000Z-W-1610-…`) and the C9 board item both
conclude: `a0_relational_v1` cannot express *"collect k tokens and the lock
opens"*, so add a counting predicate. `worldgen/qc/diagnose_miner.py` supports
this by printing, for each failing group,

> VERDICT: the VOCABULARY is short — the frames differ but no atom sees the difference

on all 19 failing groups of `t2-lock-fragile`.

## What is actually true

A counting predicate cannot separate a single one of the transitions the miner
is stuck on. Not "does not help much" — **zero**.

`probes/01_can_a_count_separate.py`, run against
`worldgen/out/worlds/t2-lock-fragile/raw_trace.jsonl`:

```
atoms=114  of which count=16
count atoms: count(0)>=19 … count(0)>=22, count(2)>=1..3, count(3)>=1

inseparable (pos,neg) pairs the whole vocabulary agrees on: 276
of those, pairs whose colour histograms DIFFER: 0
  -> a colour-cardinality atom can separate at most those 0.
```

The argument is closed rather than statistical: a colour-cardinality atom is a
function of the frame's colour histogram, so if two frames have **identical
histograms** then every such atom agrees on them, whatever colour and whatever
threshold. All 276 stuck pairs have identical histograms. Adding the count atom
family leaves the failure list byte-identical — 19 failing groups before, the
same 19 after, same tracks, same actions, same counts.

## What the stuck pairs actually differ in

Every one of them differs only in **where the agent is**:

```
example: ('obj0','DOWN','identical histogram', [(1,1,6,0), (2,1,0,6)])
example: ('obj2','DOWN','identical histogram', [(1,5,6,0), (5,5,0,6)])
```

Colour 6 is the agent. One cell loses it, another gains it. Nothing else on the
board moves.

So the vocabulary *does* contain a reading that separates these — `at(r,c)` reads
the mover's anchor. `probes/02_which_reading_separates.py` measures three
candidate readings against all 276 pairs:

| reading | separates |
|---|---|
| the absolute anchor of **each track** | **276 / 276** |
| each track's anchor **relative to the mover** | 76 / 276 |
| "track T is one step from the mover in direction D" | 0 / 276 |

The absolute anchor of each track separates everything. Which raises the real
question: `at(r,c)` already reads an anchor, so why does it agree on both?

## The root cause: the vocabulary is aimed at the wrong object

`probes/03_what_is_the_mover.py`:

```
== t2-lock-fragile: 5 tracks ['obj0'…'obj4']
   mover_anchor over first 5 transitions: [(1,3), (1,3), (1,3), (1,3), (1,3)]
   anchors dict (t0): {'obj0': (1,1), 'obj1': (1,3), 'obj2': (1,5),
                       'obj3': (3,1), 'obj4': (5,6)}
```

`obj0` at (1,1) is the agent — the catalogue's `agent_start`. `obj1` at (1,3) is
a **token**, and it is what `multi_miner.mover_track` selected as the mover.
Every positional and strip atom in the vocabulary — `at`, `free(strip(D))`,
`in_bounds`, `clear`, `tcolor` — is therefore anchored on a token that never
moves, in a world where the only thing that moves is the agent.

`mover_track` picks "the track that moves most"
(`cold-start-a0/pipeline/multi_miner.py:156`). `probes/04_move_attribution.py`
shows what it is given:

| world | move events per track | mover chosen |
|---|---|---|
| `t1-walk-maze` (no consumables) | `obj0: 22` | `obj0` — the agent, correct |
| `t1-tokens-lock` | `obj0: 1`, `obj1: 16`, `obj2: 11` | `obj1` — a token |
| `t2-lock-fragile` | `obj0: 1`, `obj1: 23`, `obj2: 21`, `obj3: 17` | `obj1` — a token |

The agent is credited with **one** move in 110 transitions. Three stationary
tokens are credited with 61 between them. The segmenter is handing the agent's
identity to whichever token is nearest whenever an object disappears — this is
the **object-identity-across-absence** gap, which W-1610's own report lists as a
*previously* recorded gap, and it is upstream of everything else here.

On a world with no consumables (`t1-walk-maze`) the attribution is clean, which
is why nobody hit this before: A0's cart world has nothing that vanishes.

## Three consequences worth acting on

1. **`diagnose_miner`'s verdict is a false attribution, and it cannot know.** Its
   test is binary: frames identical ⇒ the world is broken, frames differ ⇒ the
   vocabulary is short. There is a third case, and it is the one that occurred —
   *the vocabulary is fine and is pointed at the wrong object*. The tool is not
   wrong to have been built; it is wrong to be read as ruling that third case
   out. Reported to worldgen rather than edited (not my territory).
2. **`t1-tokens-lock` passes L1 with the same broken attribution.** It is in the
   catalogue's passing column. Whatever it mined, it did not mine by tracking the
   agent, so its pass should not be read as evidence the pipeline handles
   consumables.
3. **The C9 acceptance line — "the count-lock world runs through the
   cold-start-a0 pipeline" — cannot be reached by a counting predicate.** It is
   reachable by fixing mover selection or object identity across absence, which
   is a different piece of work in a different module. The line is not lowered
   here; it is recorded as unmet with the reason measured.

## What C9 still delivers, and on what provenance

The DSL-side widening stands on its own and is **not** retracted by any of the
above. A hand-written `theory.dsl` for a count-lock world has to be able to say
*"passable once k tokens are collected"*, and the v0.3 guard language cannot say
it — that is a fact about the grammar, independent of what any miner can
propose. That is the provenance the ledger entry cites, and it is checked by a
fixture manual that compiles and predicts rather than by the miner.

The **miner atom** is a separate question and is answered separately in
`RUN_STATE.md`: on the only world that forced it, it is measured to buy nothing.

## Reproduce

```bash
cd <repo root>
python -m worldgen.qc.diagnose_miner t2-lock-fragile          # 19 failing groups
python theory-compiler/runs/20260728T142307Z-C9-count-lock-vocabulary/probes/01_can_a_count_separate.py
python theory-compiler/runs/.../probes/02_which_reading_separates.py
python theory-compiler/runs/.../probes/03_what_is_the_mover.py
python theory-compiler/runs/.../probes/04_move_attribution.py
```

No network, no model calls, no API spend, no sealed-pile contact.
