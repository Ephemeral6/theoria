# R2 — the frontier by generation, and what the measurement reclassified

Offline. No ARC action, no model call, no network, no spend. Development-pile
games only (`g50t-5849a774`, `sk48-d8078629`); nothing here touches the sealed
pile. R1 was live on `theoria-arm` while this was written and no `*R1*`
directory was read or written.

Reproduce, both from this directory:

```bash
python measure_frontier.py --legs-root ../          # MEASUREMENT.json
python replay_frontier.py  --legs-root ../ --with-cut-generators   # REPLAY.json
```

Both read `trace.jsonl`, which `theoria-arm/.gitignore` excludes. In a clone
without the traces they print a refusal per leg and measure nothing, rather
than reporting zero. `MEASUREMENT.json` and `REPLAY.json` are the durable
record; they carry counts and cell coordinates, never frames.

---

## 1. The measurement, and the reclassification it forces

Requirement: *for each of the four legs' recorded surprises, could ANY
generated frontier have contained the observed successor?* The honest answer
turned out to be **no for all 47**, and for two different reasons — neither of
which is probe design.

`20260801T0000Z-A-probe-economics` measured the same 52 completed probes from
`probes.jsonl` alone, i.e. from hashes. This pass reads the grids.

```
probes completed                                  52
frontier width, distinct predictions            2 on every one of the 52
off-frontier results                              47
  of which: designed from a state the world had already left    35
  of which: anchored, and missed by an unnameable cell          12
on-frontier results                                5
probes whose observed delta touches a cell that
  had never changed before in the run             23
```

**The frontier was not anchored to the world 35 times in 52.** Every hypothesis
`inner/probe.build_hypotheses` makes is a successor of the *manual's*
rolled-forward state, and `inert` — "nothing happens" — is that state rendered.
So `predictions["inert"]` **is** the frontier's anchor, and it can be compared
for free against `trace.before_hash`, the frame the world was actually showing.
They disagreed on 35 of the 52 probes, and **all 35 landed off the frontier**.
`inner/loop._roll_forward` replays the manual's `step` from `initial_state()`
over every recorded action, so a single mispredicted transition desynchronises
the manual's state permanently and every probe after it is an experiment about
a frame the world left behind. Nothing in the arm computed this number, and it
costs nothing to compute.

**The other 12 missed by one cell that no rule in this grammar can name.** Of
the 17 correctly anchored probes, 12 landed off-frontier, and every one of
those 12 has an observed delta containing **exactly one cell that had never
changed before in the run** — the counts are 49 cells with 1 virgin on r3's
ACTION2 probes, 13 with 1 virgin on `sk48-l1`, against 12 with 0 virgin on the
5 probes that landed *on* the frontier. The arm seats an object instance only
on a colour the board cannot explain; a cell that has never varied is board, so
it gets no instance, and `forall ?p in <Type>` has nothing to range over there.
r3's own manual says so, in
`i_cannot_manufacture_an_instance_on_a_cell_that_has_never_changed`, and posts
a one-pixel-per-second-command bill for it.

So the 47 decompose exactly: 35 state drift + 12 expressivity, 0 attributable
to choosing the wrong action. **That reclassification is the primary
deliverable.** A generated frontier of *rules* — near-miss variants out of the
DSL grammar, or a version space out of `cegis_miner` — would have contained
none of them, because a rule cannot be anchored to a state the arm is not in
and cannot name a cell it has no instance on.

### What `cegis_miner` was doing

It was not being discarded. `20260731T1430Z-...-r3`'s manual records its
verdict verbatim: *the world does not narrate as one mover* — the engine
**refused on every track**, because the mover here is a rigid 24-pixel ring
that `connected_components(4)` merges into the floor. The engine does return a
version-space frontier when it returns anything (`engines/cegis_miner/miner.py`
enumerates every minimal guard consistent with the ledger, `MAX_FRONTIER_SIZE
= 3`), so "the arm is throwing away a frontier the engine already computed" is
**not** what happened on these legs. Reported here rather than assumed, and
read-only: any ask about the segmenter's blindness to a ring-shaped mover
belongs in `monitor/inbox/`, not in a patch to `engine-rig`.

---

## 2. The change — `--frontier generated`, default off

`inner/probe.FrontierConfig`, threaded through `inner/loop.TheoriaArm` and
`harness/run.py --frontier {ablation,generated}`, on exactly the plumbing
`--goal-protocol` / `--probe-economy` / `--desk-diet` already use. Also
`THEORIA_FRONTIER=generated`, a positive whitelist: `1`, `true`, `banana`,
`GENERATED` and the empty string all leave it on `ablation`.

`ablation` is the default and is byte-identical: same hypotheses, same order,
same ids, and `design()`'s report grows no key. Two tests pin this, and one of
them passes the new `store=` argument *while* on the default, because the way
this breaks is that the evidence leaks into the old path and every leg that
left the switch off silently runs a different arm.

`generated` adds successor hypotheses that are not deletions of the manual:

| hypothesis | the mechanism the manual lacks |
|---|---|
| `world_inert` | nothing happens **to the world's frame** — not to the manual's stale state |
| `world_anchored_manual` | the manual's own rule effects transplanted onto the world's frame: the rules are right, the bookkeeping is stale |
| `world_inert_plus_edge[_k]` | nothing moves except one cell that has never changed — a board cell no rule can name |
| `edge_advance[_k]` | the manual's effects **plus** that cell: the leading edge advancing one step further along the line the previous first-ever changes travelled |

`next_unnameable_cells` returns up to four leading edges, not one: a chain per
colour, plus the colour-blind chain, because on `sk48-l1` the virgin cells
alternate colour and only the colour-blind reading sees the march, while on r3
only the per-colour chains do. Choosing between them cost 6 of the 47 on the
replay (38 → 32); returning both is the frontier discipline applied to the
frontier builder's own internals.

**A fifth generator was built, measured, and cut.** `action_replay` — "whatever
this action did last time, again, on the world's frame" — named the world's
answer **15 times of 52**, which sounds like a keeper. Its *marginal*
contribution is **0**: all 15 were answers `world_anchored_manual` already had,
and of the 9 the shipped set still misses it gets none. It widens the frontier
and lowers every action's split entropy for nothing.
`replay_frontier.py --with-cut-generators` re-measures both numbers so the
decision stays checkable.

---

## 3. The counterfactual (`REPLAY.json`)

Not a simulation. Every hypothesis is built by `inner/probe.build_hypotheses`
itself, against a manual **recompiled from the leg's own `books/snapshots/`**
and a `FrameStore` truncated to the moment before the action was sent.

**The reconstruction is checked before anything is scored.** For each probe the
replay walks every snapshot, compiles it, rolls the manual forward exactly as
`inner/loop._roll_forward` does, and accepts a snapshot only if the *ablation*
prediction dict it produces equals the dict `probes.jsonl` recorded — key for
key and hash for hash. A probe no snapshot reproduces is `unreconstructed` and
scored for nothing.

```
probes replayed                                   52
reconstructed exactly from the leg's snapshots    52     <-- 0 unreconstructed
unreconstructed                                    0

ablation frontier contains the world's answer      5 / 52
generated frontier contains the world's answer    43 / 52
  off-frontier answers recovered                  38 of 47
  still off-frontier after generation              9

frontier width (distinct predictions)   ablation  2, 2, 2 …  (one value, all 52)
                                        generated 5, 6, 8, 10

anchor drifted                                    35
anchor drifted AND off the ablation frontier      35 / 35
```

Which generated hypothesis was right, over the 38 recovered (they overlap):

```
world_anchored_manual   20      edge_advance_1        16
edge_advance_2          16      edge_advance          14
world_inert_plus_edge_1  5      world_inert            4
world_inert_plus_edge_2  4      world_inert_plus_edge  3
edge_advance_3           2
cut generator action_replay: 15 right, 0 of them marginal
```

Per leg: r2 5 of 8, r3 25 of 28, `sk48-l1` 13 of 16, and the one probe of
`20260731T1240Z` never resolved so it scores nothing anywhere.

**The 9 it still misses split two ways, and neither is a rounding error.**

* `r2 P-01/P-02/P-04` and `r3 P-01/P-02/P-04` — six opening probes at steps
  6–9. Three of them have a 71-cell delta and **zero** virgin cells: a
  panel-wide cascade the transplanted manual delta does not reproduce, on a
  drifted anchor, with too little history behind it for an edge chain to mean
  anything. Generation needs evidence and on turn one there is none.
* `sk48-l1 P-03/P-06/P-09` — mid-leg, **correctly anchored**, 13-cell delta
  with exactly 1 virgin cell each. These are the expressivity cases in their
  purest form: the manual is right about 12 cells, the 13th is a board cell,
  and the leading edge this arm extrapolates lands on a *different* board cell
  than the world burned. Widening the chain cap catches more of them and each
  one caught costs every other action some entropy; four edges is where the
  replay stops paying for itself. The residue is real and is not closed here.

---

## 4. The falsifiable prediction, and what would refute it

Written before any live leg runs it.

| quantity | 2026-07-31 (ablation) | predicted with `--frontier generated` |
|---|---|---|
| frontier width, distinct predictions | 2 on 52 of 52 | **≥ 3 on at least 80% of probes** |
| off-frontier rate of completed probes | 47/52 = 90.4% | **≤ 40%** (the replay says 9/52 = 17.3%; 40% is the allowance for a live leg diverging after the first probe) |
| `information_gain_bits` realised | 0.000 on all 52 | **> 0 on at least half the completed probes** |
| anchor drift reported | never computed | **reported on every probe**, and non-zero on a leg whose manual mispredicts |

**What refutes the change** — as opposed to merely disappointing:

1. **Off-frontier rate stays above 70% with width ≥ 3.** That would say the
   world's answers are outside the *generated* class too, and the failure is
   expressivity end to end rather than anchoring. The change would then be
   noise and should be reverted, not tuned.
2. **`world_anchored_manual` is right and `manual` is wrong on fewer than 20%
   of probes.** The replay's 20-of-38 rests on anchor drift being the dominant
   cause; if a live leg drifts and the transplanted delta still misses, the
   drift diagnosis was wrong.
3. **Width rises but realised bits stay at 0.** A wider frontier that still
   never contains the truth is strictly worse than a narrow one: it prices
   every action higher for the same nothing.

Explicitly **not** a prediction: that this completes a level. Nothing here was
run against ARC.

---

## 5. What this does not do

* **No live evidence.** Same caveat `20260801T0000Z-A-probe-economics` §4
  carries, and for the same reason.
* **The replay is a counterfactual for the frontier, not for the leg.** A real
  leg diverges after the first probe whose answer differs; `(5, 43)` of 52 is a
  statement about containment on the recorded states, not a forecast.
* **The drift is diagnosed, not fixed.** `generated` adds a hypothesis that
  *survives* drift (`world_anchored_manual`) and a diagnostic that *reports* it
  (`anchor_drift`). It does not re-seat the manual's state on the world's
  frame, which is the actual repair and is a change to `_roll_forward` — a
  different blast radius, and it belongs to whoever owns certify's replay
  contract, since re-seating would make replay trivially green and destroy the
  only instrument that currently detects a wrong manual.
* **The default leg still cannot see its own drift.** Keeping `ablation`
  byte-identical means no anchor block is written when the switch is off. A
  leg that wants the number must turn the switch on, which is the price of the
  byte-identity guarantee and is stated rather than quietly resolved.
* **12 of the 47 remain out of reach of any rule the DSL can write.** The
  `*_plus_edge` hypotheses can *predict* those cells; the manual still cannot
  *state* them, so a confirmed edge hypothesis has nowhere to be written down.
  That is the expressivity gap, and it is a grammar change, not a probe change.
