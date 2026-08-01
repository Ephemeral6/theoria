# RUN_STATE — R2, the frontier by generation

**Cell:** R2 · **Territory:** `theoria-arm` · **Branch:** `r2/frontier-gen`
**Spend:** $0.00. No ARC action, no model call, no network. Sealed pile: zero
contact. R1 was live on this territory throughout; no `*R1*` run directory was
read or written.

## What was asked, and what the evidence said back

The brief said: build the frontier by generation rather than ablation, and
measure first — *if no generated frontier could have contained the observed
successors, the reclassification is the deliverable.*

The measurement came back "no, for all 47", and with a decomposition nobody had
computed:

* **35 of the 52 completed probes were designed against a state the world had
  already left.** `predictions["inert"]` is the frontier's anchor — the manual's
  rolled-forward render — and `trace.before_hash` is the frame the world was
  showing. They disagreed 35 times, and all 35 of those probes landed
  off-frontier. `inner/loop._roll_forward` replays `step` from
  `initial_state()` over every action, so one mispredicted transition
  desynchronises the state permanently.
* **12 of the remaining 17 missed by exactly one cell that had never changed
  before.** No object instance can be seated on a board cell, so no
  `forall ?p in <Type>` rule can name it, so no rule — generated or ablated —
  can predict it.
* **0 of the 47 are attributable to picking the wrong action.**

So a generated frontier *of rules* would have contained none of them. The
failure class is state drift plus expressivity, not probe design. That is the
first deliverable and it is written up in `README.md` §1.

## What was built anyway, and why it is not a contradiction

The reclassification names two causes; one of them is reachable without
touching the grammar. `--frontier generated` (default `ablation`, byte-identical)
adds successor hypotheses anchored on the **world's own last frame** rather than
on the manual's state, plus hypotheses that write one cell the grammar cannot
name. These are not rules and are not proposals for the manual — they are
predictions, which is all a frontier needs to be.

Replayed through the real builder against manuals recompiled from each leg's own
snapshots: **52 of 52 probes reconstructed exactly** (the ablation prediction
dict matches `probes.jsonl` key for key), ablation contains the truth 5 times,
generation contains it 43. 38 of the 47 off-frontier answers recovered; 9 not.

## Numbers, verbatim

```
                                 ablation (2026-07-31)   generated
frontier width, distinct preds   2 on 52 of 52           5 / 6 / 8 / 10
contains the world's answer      5 / 52                  43 / 52
off-frontier                     47                      9
anchor drifted                   35 (never computed)     35 (reported)
```

`action_replay`, a fifth generator, was built, measured at 15 hits of 52 and
**0 marginal**, and cut. `--with-cut-generators` re-measures it.

## Residual gaps, stated

1. The drift is **diagnosed, not repaired**. Re-seating the manual's state on
   the world's frame is the actual fix and would make certify's replay trivially
   green, destroying the only instrument that currently detects a wrong manual.
   Out of scope, named.
2. A leg on the default still cannot see its own drift, because byte-identity
   forbids writing the anchor block when the switch is off.
3. The 12 expressivity cases can now be *predicted* but still cannot be
   *written down* — a confirmed edge hypothesis has no home in the DSL. Grammar
   change, not a probe change; owned by `theory-compiler`.
4. No live evidence. The counterfactual is about containment on recorded
   states; a real leg diverges after the first probe whose answer differs.
5. `cegis_miner` was read and is **not** being discarded by the arm: on these
   legs it refused on every track (`the world does not narrate as one mover`),
   because the mover is a ring the segmenter merges into the floor. Any ask
   about that belongs in `monitor/inbox/`.

## Gates

`python -m pytest -q`, `python verify.py`, `python -m armtools.verify_provenance`
— outputs verbatim in `GATES.txt`.
