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

## 3. What the repair exposed — E-09

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
*track's position*.

That was verified adversarially **before** anything was added to it
(`probes/09_adversarial_no_atom_separates.py`, written by a subagent told to
refute it). Against the 120-atom vocabulary as it stood at the base commit:

* **0** atoms are true on all 23 positives and false at t=31;
* only **19** hold on all the positives, and all 19 also hold at t=31;
* the conjunction of all 19 — the strongest guard the vocabulary can build for
  this rule — still admits t=31. A conjunction holds on all positives iff every
  conjunct does, so **no conjunction of any size** separates it. The failure is
  expressivity, not CEGIS search order.
* nearest misses, for the record: `!tcolor(RIGHT)==2` violates exactly one
  positive (t=71, where the agent eats a *different* token), `!at(1,2)` violates
  two (t=59, t=69, where the agent stands there again after obj1 is gone).

So one atom was added, and one only. `faces(T,D)` — *track T's anchor is where
the mover's anchor would be after one step in direction D* — with four limits,
each with its own test: one step (distance is not a parameter), mover-relative
(no relation between two non-mover tracks), anchors rather than body overlap
(that is the touching-objects gap, its own row), and only `(track, direction)`
pairs the trajectory exhibited.

It is priced at `2 * (_TRACK_BITS + _DIR_BITS)` = 8 bits of payload, the same as
`at(r,c)`, by the rule the module already published: an identity literal costs
twice a predicate. At the predicate price it would have been the cheapest atom in
the vocabulary while being the most instance-bound one. Ten kinds still fit in
four bits, so unlike E-08 no existing atom was re-priced.

Ledger entry: `cold-start-a0/THEORIZE_LOG.md` **E-09**, with the forcing world,
the transition, the four-atom table of what v1 could not say, and the price.

## 4. The acceptance line, met

`bash theory-compiler/runs/20260728T173400Z-C9-mover-identity/verify.sh` →
**VERIFY GREEN**. `python -m worldgen.qc.run_qc`, the layer that reported the
original failure:

| | before | after |
|---|---|---|
| L1 | `NoSeparatingGuard` at transition 1 | **true** |
| L2 | — | **true** |
| L3a (replay) | — | **true, 1.0** (110/110) |
| render self-check | — | **287/287** |
| rules mined | 0 | **36** |
| mover | `obj1`, a token | **`obj0`, the agent** |
| every track explained, exclusively | — | **5/5, 5/5** |

Exactly one mined guard uses the new atom, and it is the rule that forced it:

    obj1, RIGHT, nothing happens   <-   !faces(obj1,RIGHT) and act==RIGHT

Evidence is copied into `acceptance/` rather than left in `worldgen/out/`, which
was restored to its committed state after the run — `worldgen/` is not this
worker's territory and nothing there is modified by this branch.

**L3b is 0.497 and that is not met.** It is also not part of C9's line: the bar
is worldgen's own held-out generalisation gate, it fails on all three sampled
worlds including the two that already passed L1, and the family verdict was
already `pass: false` before this change for that reason. Why this world scores
where it does is visible in the rule the lock produces — the gate opens exactly
once, so CEGIS separates that single witness with the cheapest conjunction
available rather than with a count:

    obj4, RIGHT, vanish  <-  !clear(strip(RIGHT)) and !present(obj1)
                             and act==RIGHT and free(strip(LEFT))

A single-witness rule is what `t2-lock-fragile` was *built* to be
(`worldgen/generate.py`: "nearly every rule here has a single witness, which
makes it the worst case for a pipeline that leans on repetition"). Getting the
count law out of one witness is a different problem from being able to state it,
and it is not claimed here.

## 5. The thing W-1252 flagged for adjudication, now measurable

W-1252 shipped the miner's `count` atom with measured zero benefit on the only
world that asked for it, kept on the argument that "the miner should be able to
propose what the manual can state", and flagged that as an argument rather than a
measurement for the board to rule on.

The tracking repair makes the cleaner test available, and the answer did not
change: **`count` appears in no mined guard on `t2-lock-fragile` even now.** Its
benefit is measured at zero a second time, under correct attribution.

I did not act on it. Reverting a merged widening that the previous worker
explicitly referred to the board is exactly the decision the referral was meant
to prevent a single worker from making quietly. It is re-reported instead, with
the stronger measurement, in `cold-start-a0/THEORIZE_LOG.md` E-09 and in
`monitor/inbox/`. `_count_atoms` in `pipeline/atoms_a0.py` is still one
contiguous block if the board rules against it.

Note that the DSL-side half of E-08 is untouched by any of this: a hand-written
manual for a count-lock world still has to be able to state its own gate, which
is a fact about the grammar and not about any miner.

## 6. Regression, measured

| surface | result |
|---|---|
| `cold-start-a0` suite | **82 passed** (26 new) |
| `theory-compiler` suite | **363 passed, 1 skipped**; **364 passed** under `THEORIA_REQUIRE_LEAN=1` |
| `engine-rig` suite | **315 passed, 9 skipped** — untouched, no file in it modified |
| `cold-start-a0/run_all.py` | nine steps green, schema validation OK |
| A0's mined guards | **byte-identical** — all 26 non-`object_hypothesis` rows of `candidates.jsonl` and all 12 of `candidates_no_button.jsonl` |
| `worldgen` `t1-switch-toggle` | 31 `rule_hypothesis` rows, guards **byte-identical** |
| `worldgen` `t1-switch-latch` | 27 `rule_hypothesis` rows, guards **byte-identical** |
| A0's own identity repair | **0 swaps**, one refusal at t=99 (the Button press — the Switch recolours while the Door vanishes, and the recolour is not into the vanishing track's colour). Pinned by a test. |

**The work order's "四份既有 DSL 不回归" clause, checked against the base commit
rather than against itself.** A subagent ran the four cross-track manuals through
all four forms in *this* tree and in a throwaway worktree at `86d79c6`, and
sha256'd every generated form:

| manual | Lean | Python | PDDL | Markdown | vs `86d79c6` |
|---|---|---|---|---|---|
| `theory-compiler/tests/fixtures/peg_theory.dsl` | refused¹ | ok | refused² | ok | **byte-identical** |
| `cold-start-a0/theory/theory.dsl` | ok | ok | ok | ok | **byte-identical** |
| `a0-spike/theory/theory.dsl` | refused³ | refused³ | ok | ok | **byte-identical** |
| `cold-start-a2/theory/theory.dsl` | ok | ok | ok | ok | **byte-identical** |

¹ no certificate supplied for the pagoda potential; ² the peg problem is a line
world, not a grid; ³ E-02's free name `dir`. Every refusal is pre-existing and
its message is byte-identical too. `theory-compiler/runs/20260728T102343Z-c7/verify.sh`
is green (all eleven manuals in the tree, the two ledger numbers), and
`tests/test_count_guard.py` is 15 passed — the in-suite four still compile.

Worth correcting for anyone reading the older survey: `a0-spike`'s manual *does*
have a `semantics:` section, and its refusal is form-specific — it parses, builds
IR, and still generates PDDL and Markdown.

**Determinism.** Three consecutive runs of the acceptance produce a
byte-identical `engines_report.json`, and a byte-identical `candidates.jsonl`
under the documented switch (`THEORIA_DETERMINISTIC_IDS=1`,
`THEORIA_FIXED_TIME`). Without it the `id` field is `uuid4` by design and every
row differs — that is `engine-rig/common/candidates.py`'s stated contract
(D-004), not drift, and it is why `run_all.py` sets it.

What *does* move, and why: the three `object_hypothesis` rows carry the
segmentation report, which now has an `identity_repair` section, so those rows
and their content-derived ids change; `vocabulary_size` moves 162 → 172 for the
new atom.

`theory/generated/theory.md` and `theory/generated_no_button/theory.md` also
move, and that one is **not** this change. `compile_a0.py` reads the
hand-written `theory.dsl` and never touches `candidates.jsonl`, so it cannot see
any of this. Those files were last regenerated at commit `eaa0075` (08:57) and
`gen_markdown.py` moved at `aeee50e` (22:22) with C8 — they have been stale on
master for thirteen hours and re-running the chain surfaced it. Confirmed rather
than argued: regenerating that file **in a clean worktree at `86d79c6`, with the
baseline chain**, produces `22ac738f…` — which is exactly what this branch
commits, while `86d79c6` had `5b100206…` checked in. Committed regenerated,
since a generated file that does not match its generator is worse than the diff.

## Discipline

No network, no model calls, no API spend, no sealed-pile contact. Nothing
outside `theory-compiler/` and `cold-start-a0/` is edited; `worldgen/` and
`engine-rig/` are read and run, never written.
