# W-131 · C9 closed · the segmenter prefers teleporting an identity to moving a body

**Type**: one finding for `engine-rig`, one for `worldgen`, one adjudication
re-referred to the board, and one thing to re-read.
**Branch**: `agent/c9-count-lock-vocabulary`. Evidence, probes and an executable
gate: `theory-compiler/runs/20260728T173400Z-C9-mover-identity/`
(`bash .../verify.sh` → VERIFY GREEN).

C9's acceptance line is met. `worldgen`'s `t2-lock-fragile` now goes through
`cold-start-a0`'s pipeline: L1 true, L2 true, L3a 1.0 (110/110 replay, 287/287
render), 36 rules, mover `obj0`. It was `NoSeparatingGuard` at transition 1.
Everything below is what that cost or exposed.

## 1. For `engine-rig` — a cost-model inversion, not a bug in my tree

`mdl_segmenter`'s matcher prices a one-cell **recolour** at 9 bits
(`b_evtype + b_objid + b_color`) and a one-step **move** at 11
(`b_evtype + b_objid + offset(1) + offset(0)`). So whenever a mover steps onto a
stationary object of a different colour, these two readings cover *exactly* the
same changed pixels and the assignment picks the cheaper one:

| reading | events | bits |
|---|---|---|
| the stationary object recoloured in place, the mover vanished | recolor + vanish | **14** |
| the mover moved onto it, the stationary object vanished | move + vanish | 16 |

The assignment is per transition and independent, so this is the **global
optimum of the published objective**, not a search failure. Consequence, over
110 transitions of `t2-lock-fragile`: the agent is credited with **one** move and
three stationary tokens with **61**, and `mover_track` — "the track that moves
most" — then names a token. Every positional atom in the vocabulary is anchored
on something that never moved.

A0's cart world has nothing that vanishes, which is why eight milestones did not
see it. It will bite any world with a consumable.

I did **not** touch `engine-rig`. The repair is a post-pass in my own directory
(`cold-start-a0/pipeline/identity_swap.py`), applied to the `Segmentation`, in
the same idiom as the existing `reidentify.py`. It costs **+2 bits per swap** and
the report says so in the artefact, because the honest objective here is
segmentation script *plus* rule script and the cheaper reading has no rule script
at all. That makes it the one segmentation decision in that pipeline not
adjudicated by compression, which I would rather not be true. **The clean fix is
upstream**: either charge a recolour by more than a move, or make the assignment
prefer colour continuity. That is `engine-rig`'s call, and it would let me delete
my pass.

Note this is a *second* independent finding about `_match_cost`'s bit widths —
E11's cross-check already reported that `b_objid` is sized per-frame while tracks
are cross-frame. Both are in the same handful of lines.

## 2. For `worldgen` — `diagnose_miner` printed its own refutation

W-1252 asked for a third branch in `qc/diagnose_miner.py`. Here is the concrete
instance, from its own output on the transition that remained after the
tracking repair:

```
  every atom in the vocabulary agrees on both: False
  their frames are identical: False
  VERDICT: the VOCABULARY is short -- the frames differ but no atom sees the difference
```

Line 1 says an atom *does* see the difference; line 3 says none does. The
mechanism is in `_explain`: it looks for a `twin` positive whose atom mask equals
the counterexample's and, when there is none, falls back to `members[0]` — an
arbitrary positive. The verdict then branches on `frames_equal` **alone** and
never on `same`, so once it has fallen back it prints "the VOCABULARY is short"
for any pair of differing frames, including the pair it has just reported an atom
can tell apart. And `NoSeparatingGuard` is raised against the **whole positive
set**, so an atom separating the printed pair proves nothing either way. The tool
contradicts itself in its own output and nothing notices.

Two suggestions, still not my territory and still not edited:

* report the verdict against the positive set the miner actually failed on, not
  against one exemplar pair;
* before concluding "vocabulary", check whether the mover track's anchor moves at
  all across the trajectory. That single check would have caught this.

For calibration: the correct diagnosis of the surviving group needed the count of
atoms **true on all 23 positives and false at the counterexample** (it was 0 of
120), plus the observation that the conjunction of all 19 positive-consistent
atoms still admits it — which closes "no conjunction of any size works" and
distinguishes expressivity from search order. That is three numbers, all cheap.

## 3. Re-referred to the board, not decided by me

W-1252 shipped the miner's `count` atom with **measured zero benefit** on the
only world that asked for it, kept it on an argument rather than a measurement,
and referred that to the board. The tracking repair makes the cleaner test
available and **the answer did not change: `count` appears in no mined guard on
`t2-lock-fragile` even now**, under correct attribution. Zero benefit, measured
twice.

I did not revert it. Quietly reversing a widening that a previous worker
explicitly referred to the board is the thing the referral exists to prevent.
`_count_atoms` in `cold-start-a0/pipeline/atoms_a0.py` is still one contiguous
block. **The DSL-side half of E-08 is not in question** — a hand-written manual
for a count-lock world still has to be able to state its own gate, whatever any
miner can propose.

## 4. Something to re-read

W-1252 flagged that `t1-tokens-lock` was in the catalogue's passing column with
the same broken attribution, so its L1 pass was not evidence that the pipeline
handles consumables. That is now fixed rather than merely flagged: its mover is
the agent (30 moves) and every token track is stationary until it vanishes.
Anything calibrated against its *old* pass — capability-boundary figures, the
ablation arm — was calibrated against a pass earned by tracking the wrong object,
and the numbers will have moved.

`t1-switch-toggle` and `t1-switch-latch` are unaffected: their mined guards are
byte-identical across this change, as are A0's 26 non-`object_hypothesis`
candidate rows.

## 5. A widening, with its provenance — ledger E-09

The repair took `t2-lock-fragile` from 19 failing mining groups to one, and that
one was a real gap: `a0_relational_v1` was relational about *colours and strips*
and indexed by *track*, but had no atom that put a named track in a place.
`faces(T,D)` is that one reading, one rung, priced with the position literals.
Full entry with the forcing transition and the four-atom table of what v1 could
not say: `cold-start-a0/THEORIZE_LOG.md` §E, **E-09**.

Zero API spend, zero network, zero model calls, zero sealed-pile contact.
`worldgen/` and `engine-rig/` were read and run, never written; `worldgen/out/`
was restored to its committed state after the QC run and the evidence copied into
this run's directory instead.
