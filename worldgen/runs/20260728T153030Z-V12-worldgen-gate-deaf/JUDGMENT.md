# Step 1 — was `gating=False` deliberate?

**Yes, and the evidence is unambiguous.** What follows is the evidence, then the
part of the ticket's complaint that survives it.

## The evidence that it was deliberate

1. **`verify.py` says so, in its own module docstring** (lines 17–29 at base
   commit `77e9216`):

   > **Both QC stages are reported and neither gates**, and that is deliberate
   > rather than convenient.

   with the reason: `PREREGISTERED.md` fixed a held-out threshold of 0.90 before
   the harness ran, the family came in under it, and "the honest response to a
   missed pre-registered bar is to publish the miss, not to lower the bar and not
   to quietly turn the exit code green."

2. **It was there in the first commit, so it is not drift.**
   `git show 66493f6:worldgen/verify.py` already carries the same paragraph in
   the singular — "The QC stage is reported but does not gate, and that is
   deliberate rather than convenient" — with `gating=False` on the one QC stage
   that existed then. `9a37d8a` (C6) added the mutants stage and *deliberately
   rewrote the paragraph into the plural*. Two separate sessions made the same
   call on purpose.

3. **`PREREGISTERED.md` fixes the disposition of a miss in advance**: "if a world
   misses the bar it is recorded as a miss, not re-scored against a lower one."

4. **The red does not belong to `worldgen/`.** `RUN_STATE.md` §gaps item 2:
   `t2-lock-fragile` makes the upstream miner raise `NoSeparatingGuard`, and
   "the fix is an atom in `cold-start-a0/pipeline/atoms_a0.py`, another track's
   file. Filed." `qc/diagnose_miner.py` localised it: the frames differ and no
   atom in `a0_relational_v1` sees the difference. That is another track's
   vocabulary, and `worldgen/` is forbidden from touching it.

5. **The mutants bar declares itself defective in its own postscript.**
   `PREREGISTERED_MUTANTS.md` §Postscript: `v-efe43df1` fails rule 1, and so does
   **`t2-switch-push`, its base** — same `NoSeparatingGuard`, same vocabulary
   cause. The postscript concludes the run is "a **fail of this bar and not a
   defect in the mutation layer**" and that rule 1 should have been written as
   the base-comparison form. The bar was left as written, on purpose.

**Therefore: turning `gating=True` on `pass` would be wrong.** It would make the
world factory's one command permanently red for a defect in another track's
miner, which `worldgen/` may not fix. A permanently red gate is a gate everybody
learns to route around — which is the ticket's own pathology, one level up. It
would also promote a bar its own author documented as mis-specified into a hard
gate.

## What is nevertheless defective

The ticket's shape is real; it is just not located where the ticket guessed.
Three separate things:

**(a) The word `green`.** Baseline transcript (`verify_before.txt`): two
pre-registered bars missed, `pass: false` in both artifacts, and the last line of
output is the bare token `green`, exit `0`. The docstring's honesty never reaches
the surface a reader or a CI log sees. That is the deafness.

**(b) A crash and a measured miss are the same signal — this is a real defect.**
`verify.py` judges a QC stage solely by `proc.returncode == 0`. `run_qc` returns
`1` for "ran fine, missed the bar" (`run_qc.py:371`, `:435`) and Python returns
`1` for an uncaught `ImportError` too. So **the entire QC layer could stop
executing and `verify` would print `[miss]` and exit 0**, indistinguishable from
today's honest miss. The baseline transcript demonstrates the swallowing
directly: `run_qc` exited non-zero, `verify` printed `[miss]`, and the process
exited 0. Non-gating was a decision about a *measured verdict*; it was never a
decision to accept a stage that did not run.

**(c) Nothing pins the miss, so "non-gating" currently means "accept anything".**
If `t1-switch-toggle`'s replay accuracy slid from 1.000 to 0.4, or a third world
started raising, or a mutant that passes today began to fail, `verify` would
still print `green` and exit 0. The deliberate decision was "publish *this*
measured miss and do not move the bar" — it was not "any QC outcome whatsoever
is acceptable".

## Step 2, consequently

Not "gate on `pass`" (re-litigates a documented decision, goes permanently red
for another track) and not docs-only (leaves (b) and (c) unfixed). Instead:

**Pin the known miss in a hand-written file, and gate on any deviation from the
pin, in either direction, plus on any stage that fails to produce a verdict.**

This lowers nothing: `PREREGISTERED.md` and `PREREGISTERED_MUTANTS.md` are
untouched, `QC.json` still says `pass: false`, the 0.90 bar is still 0.90. It
*adds* a gate where none existed. Before: every QC outcome exits 0. After:
exactly one outcome exits 0, and it is the one already published.

## An unrelated finding, recorded not fixed

`python -m worldgen.verify` on a clean tree **dirties ten committed artifacts**
under `worldgen/out/qc/*/` (`candidates.jsonl`, `engines_report.json`;
`frontier_size` 32 → 57 and similar). `QC.json` / `QC_MUTANTS.json` themselves
are byte-stable. These are the *upstream* pipeline's per-world scratch outputs,
so the drift is between the `cold-start-a0` code state that produced the
committed copies and the one on disk now. Diff kept as
`out_dirtied_by_verify.diff`; tree restored with `git checkout`. Not mine to fix,
and it is why the negative control below must never invoke the real QC stages.

Also worth flagging upstream: `exam/verify.py:25` says it is "Same shape as
`worldgen/verify.py`, and for the same reason stated there" — so (a)/(b)/(c) very
likely replicate in `exam/`. Out of this ticket's boundary.
