# C9, second pass — the acceptance line, and what was actually in the way

**Worker** W-131. **Branch** `agent/c9-count-lock-vocabulary`. **Base**
`86d79c6`. Predecessor run:
`theory-compiler/runs/20260728T142307Z-C9-count-lock-vocabulary` (W-1252).

## Where this item stood before I touched it

C9's first pass is **already on master**. The counting guard (`count(Type, pred)
>= k`) compiles, ledger entry **E-08** is filed with its provenance, the four
existing manuals were measured not to regress, and two defects that fell out of
the lifting were fixed. None of that is redone here.

What was left is one line, and W-1252 recorded it unmet rather than lowering it:

> worldgen 的 count-lock 世界跑通 cold-start-a0 流水线作为验收

W-1252 measured why the counting predicate could not reach it — a colour
cardinality atom is a function of the frame's colour histogram, and all 276
transition pairs the miner was stuck on have identical histograms — and named
the real cause: `multi_miner.mover_track` picks a *token* as the mover on any
world with a consumable, so every positional atom is anchored on something that
never moves. They handed it on rather than folding an unreviewed change into
C9. The board re-issued the item with the line intact; this run meets it.

## 1. The cause, priced

The mis-attribution is not a bug in `mover_track` and not a search failure. It
is the segmenter's published objective preferring the wrong reading.

At the transition where the agent steps onto a token, two explanations cover
**exactly the same changed pixels**, and `_match_cost` scores them:

| reading | events | bits |
|---|---|---|
| the token **recoloured in place** to the agent's colour, the agent **vanished** | recolor + vanish | 9 + 5 = **14** |
| the agent **moved** onto the token, the token **vanished** | move + vanish | 11 + 5 = **16** |

A one-cell recolour is `b_evtype + b_objid + b_color` = 9. A one-step move is
`b_evtype + b_objid + offset(1) + offset(0)` = 11. The bipartite assignment is
per transition and independent, so 14 < 16 is the global optimum of the
objective as published — the matcher is right by its own lights.

`probes/07_price_the_two_readings.py` is that table, computed rather than
asserted.

Consequence, measured over 110 transitions of `t2-lock-fragile`
(`probes/04_move_attribution.py`, W-1252's, re-run):

    move events per track: {'obj0': 1, 'obj1': 23, 'obj2': 21, 'obj3': 17}
    mover chosen: obj1  -- a token at (1,3)

The agent is credited with one move; three stationary tokens with 61.
`probes/05_track_anatomy.py` shows the mechanism directly: three `recolor`
events, at t=1, t=31 and t=71, each handing colour 6 to the next token the agent
eats. A0's cart world has nothing that vanishes, which is why eight milestones
did not see it.

## 2. The repair, and the one place it does not obey compression

`cold-start-a0/pipeline/identity_swap.py`, wired into
`segment_operators.choose_operator` before `reidentify` (a swap repair turns a
`recolor` into a `vanish`, which is what gives `reidentify` a disjoint lifetime
to work with).

It fires on one pattern and one only: track `a` vanishes at *t*, track `b`
recolours **all** of its cells to `a`'s colour at *t*, `a` and `b` have the same
shape, and their anchors are 4-adjacent. Then `a` moved onto `b` and `b` was
consumed. Non-adjacent swaps, partial recolours and shape changes are refused
and counted into the report as near misses, so the next rung will have a forcing
case rather than a guess.

**It costs 2 bits per swap and the report says so.** This is the only
segmentation decision in the pipeline not made by script length, because script
length is precisely what prefers the wrong answer here. The criterion actually
being applied is total description length — segmentation script *plus* rule
script — and the mis-anchored reading has no rule script at all: the miner
raises `NoSeparatingGuard` rather than paying more bits. Callers get the number
(`identity_repair.delta_bits`) so they can disagree.

After the repair (`probes/05_track_anatomy.py`, same script, same worlds):

| world | mover before | mover after | agent's moves after |
|---|---|---|---|
| `t2-lock-fragile` | `obj1` (token) | `obj0` (agent) | 65 |
| `t1-tokens-lock` | `obj1` (token) | `obj0` (agent) | 30 |
| `t1-walk-maze` | `obj0` (agent) | `obj0` (agent) | 22 — unchanged |

Every token track is now stationary for its whole life and then vanishes; no
track changes colour anywhere in either world.

## 3. What the repair exposed — status: in progress

With the agent correctly tracked, `t2-lock-fragile` goes from **19 failing
mining groups to one**:

    FAILS  track=obj1 action=RIGHT effect=('none',0,0,None)  (23 positives)
    NoSeparatingGuard: no literal separates transition 31 from the positives

This one is a real, correctly-attributed vocabulary gap, and it is *not* the one
E-08 was cut for. The rule is "the token does nothing under RIGHT", and the
transition it must exclude is the one where the agent, standing directly left of
that token, steps onto it. `a0_relational_v1` cannot say that:

* `tcolor(RIGHT)==2` says "the cell ahead is a token" — true also when the agent
  steps onto a *different* token, so it fails on a positive;
* `at(r,c)` reads the mover's anchor only, and the agent revisits that cell after
  the token is gone;
* `present(T)` and `color(T)` are track-indexed but position-blind;
* `count(k)>=t` reads the frame, not a relation.

The vocabulary is relational about *colours and strips* but never about a
*track's position*. Being verified adversarially before anything is added to it
(`probes/09_...`).

## Discipline

No network, no model calls, no API spend, no sealed-pile contact. Nothing
outside `theory-compiler/` and `cold-start-a0/` is edited; `worldgen/` and
`engine-rig/` are read and run, never written.
