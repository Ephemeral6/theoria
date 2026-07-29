# Pre-registered: the mutants' factory inspection

Written before `python -m worldgen.qc.run_qc --mutants` was run for the first
time, for the same reason `PREREGISTERED.md` was: a bar chosen after the numbers
are in is not a bar.

**What backs that claim, and what does not.** The body below and the postscript
after the rule were written at different times and the postscript says so; but
this file was untracked when both were written, so there is no commit ordering
to appeal to and the only evidence for "before" is this sentence. A reviewer
should read it as an assertion, not a proof.

## The sample — fixed here, not a tunable

One mutant per edit family, chosen for diagnosability rather than for
difficulty:

| variant | family | base | why this one |
|---|---|---|---|
| `v-ce732813` | `forbid_action` | `t1-walk-maze` | the only edit that touches a **new** engine knob, on the world with no mechanisms at all, so anything that breaks localises to the knob and not to a family |
| `v-707a64ad` | `change_guard` | `t1-switch-toggle` | its base is already in `PREREGISTERED.md`'s sample and measured 1.000 replay / 0.773 held-out, so the comparison is direct rather than inferred |
| `v-efe43df1` | `reversible_to_irreversible` | `t2-switch-push` | the A0/A0′ contrast, in a world with two families interacting |
| `v-a3446614` | `move_portal_exit` | `t1-portal-oneway` | the invisible edit: no frame anywhere differs until the mouth is entered, and its base is one of the four worlds `RUN_STATE.md §gaps` flags as having a thin trace, so a bad number here has a known alternative explanation |

## The question, which is not `PREREGISTERED.md`'s question

`PREREGISTERED.md` asks whether the mined manual clears a held-out threshold of
0.90. The family **missed** it and the miss is published; re-imposing that
threshold here would measure the same miner again and report nothing about
mutation.

The question a mutant's inspection has to answer is different: **does a mutated
world behave, under the upstream pipeline, like the world it was mutated from?**
A mutant that crashes a pipeline its base survives is a defect in this layer. A
mutant whose held-out accuracy differs from its base's is a *finding* about what
the edit did to learnability, which is the thing the corpus exists to supply.

So, fixed in advance:

1. **L1 liveness and L2 structure must pass** on every sampled mutant. No
   threshold, no tolerance: the pipeline runs or the mutant is not shippable.
2. **L3a replay must be 1.000**, matching what every non-raising world in
   `PREREGISTERED.md`'s sample achieved. A mined rule set that cannot reproduce
   the trace it was mined from is a defect regardless of the edit.
3. **L3b held-out is recorded and compared to the base, with no threshold.**
   Any threshold here would be a claim about `a0_relational_v1`'s expressiveness,
   which `QC_REPORT.md` already measured and found wanting. What is reported is
   the pair (base, mutant) and the difference.
4. **Failing 1 or 2 fails the inspection.** 3 cannot fail; it can only be
   surprising, and a surprise is the result.

`v-707a64ad`'s base raises nothing; `t2-lock-fragile` — the world that makes the
miner raise `NoSeparatingGuard` — is deliberately **not** a base in this sample,
because a mutant of it would inherit a known upstream expressiveness failure and
measure nothing about mutation.

---

## Postscript, 2026-07-28, after the first run — the bar above is defective

Appended, not edited. The text above is what was fixed in advance and it stands
as written; this records what running it showed about it.

`v-efe43df1` failed rule 1: the pipeline raises `NoSeparatingGuard` on it. It
also raises on **`t2-switch-push`, its base** — see `out/qc/QC_MUTANTS.json`,
which runs the base through the same harness in the same process, and
`runs/…-C6-worldgen-mutate/diagnose_t2-switch-push.txt`, which localises it to
the same cause as `t2-lock-fragile`'s: *"the VOCABULARY is short — the frames
differ but no atom sees the difference"*. That is `a0_relational_v1`'s
expressiveness, in another track, and it was not previously known to affect this
world; `PREREGISTERED.md`'s sample never included it.

So the run is a **fail of this bar and not a defect in the mutation layer**, and
the two sentences at the top of §the question that are supposed to distinguish
those cases contradict each other:

* rule 1 is absolute — "the pipeline runs or the mutant is not shippable";
* the paragraph above it says the defect is "a mutant that crashes a pipeline
  **its base survives**".

The second is the one that means anything, and rule 1 should have been written
as it. Enforcing the absolute form would mean refusing to ship a mutant of a
world the catalogue already ships, which is not a statement about the mutant.

**What was not done about it.** The bar was not rewritten, the sample was not
swapped for one that passes, and `pass` stays `false` in the report. What is
recorded alongside it is `base_runs_the_pipeline`, measured rather than argued,
so a reader can see which of the two cases this is without taking anyone's word.
The consequence is a real gap and it is in `RUN_STATE.md §gaps`: the
`reversible_to_irreversible` family has **no** end-to-end pipeline measurement,
because the base drawn for it does not run.
