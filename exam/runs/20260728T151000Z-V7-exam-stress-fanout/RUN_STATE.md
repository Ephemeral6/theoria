# RUN_STATE — V7-exam-stress-fanout

`MANIFEST.json` beside this file is canonical; this is the narrative.
`FINDINGS.md` carries the results. `worlds/<id>.json` is each world's item
profile; `worlds/<id>.report.md` is that world's independent examiner's report.

**Branch** `agent/v7-exam-stress-fanout`, worktree
`.worktrees/v7-exam-stress-fanout/`, base `8d42373` (master).
**Territory:** `exam/` only, plus one appended paragraph in `PARTNER_SYNC.md`.
Nothing outside `exam/` was written.

**Passive throughout:** zero API calls, zero model calls on any generation or
grading path, zero network (every driver runs inside `exam.guard.no_network`),
zero game spend, zero sealed-pile contact. The twenty worlds are synthetic;
`exam/guard.py:103` refuses any id that is not in `worldgen/out/worlds/INDEX.json`.

## What happened, in order

1. **Established the matrix, and found the work order's arithmetic did not hold.**
   V7 asks for four question types over twenty worlds, 80+ combinations. Three of
   the four builders take no world argument — they are hard-wired to hand-built A0
   and A2 — and their blockers were already written down, blocker by blocker, in
   V2's `GAPS.md`. The honest full matrix is 20 papers × 1 type = **236 items**,
   and V2 had already run it. Reported rather than re-run.

2. **Built the instrument the work order actually needs.** `run_matrix` reports
   what each fake *scored*; a fraction is an average and hides the question a
   question-setter most needs answered — which items separate anybody.
   `exam/tools/discrimination.py` classifies every item by which of oracle /
   memoriser / bluffer answer it. First run: **97 of 236 items free (41.1 %), 69
   theory, 70 memorised, 0 dead, 0 anomalies.**

3. **Sent twenty examiners, one per world.** Not to re-run a 1.7-second command —
   that would have been fan-out for its own sake. Each was asked to re-derive its
   world's items by hand from `spec.json`, stress the marker with near-miss
   answers, and **try to build a cheap examinee that beats the paper without a
   world model**. Twenty independent attempts at the same attack is the only way to
   learn whether one success was a quirk.

4. **Checked their two biggest claims myself rather than relaying them.** Both
   headline results in `FINDINGS.md` were re-derived by the synthesist: the
   leakage gate was re-run over all twenty papers, and the cheap prior was
   rewritten once as a single function with no per-world constant
   (`prior_sweep.py`) and scored through the real marker.

5. **Wrote the instrument's own limit into the instrument**, and pinned it with a
   test built to fail when the limit is lifted.

## The three results

* **The exam's own leak checker refuses all twenty generated papers, and nothing
  ever pointed it at them.** Every item's sheet carries
  `tags: [split, "rule:<name>"]` — the name of the rule that answers it.
  `leakage.check_paper` raises on 20 of 20 worlds, **236 of 236 items** hit by
  their own declared probe. It was never caught because its only non-test caller
  iterates `BUILDERS`, and `heldout_worldgen` is not in it; no test anywhere runs
  the gate against a worldgen paper. Affects no number published so far — the
  synthetic examinees answer from `Paper.items` and never read a sheet — and
  affects every real examinee handed one.
* **A theory-free grid prior scores 1.000 on twelve of the twenty worlds**, beats
  the bluffer floor on eighteen, and takes **109 of 139 frame-changing items
  (78.4 %)**. Eight lines, no per-world constant, sheet fields only.
* **The paper's zero-discrimination share is 41 %, and that is the optimistic
  figure.** Measured against the prior, the informative residue falls from 69
  items to **16**, and to **zero on fourteen worlds**. Nine examiners independently
  reported their world's honest effective size as 0.

## Verification

```
python -m pytest exam/tests -q                        304 passed  (287 before, +17 new)
python -m exam.tools.discrimination                   20/20 worlds, 0 dead, 0 anomalies
PYTHONPATH=. python .../prior_sweep.py                12/20 worlds at 1.000
```

Determinism: `test_the_profile_is_deterministic` compares two profiles of the same
world; the profiler adds no clock and no RNG, inheriting `heldout_worldgen`'s
salted-hash ordering.

**One unexplained failing run, recorded because burying it would be the worse
choice.** On the first full-suite run after the adversarial corrections landed, the
suite reported **11 failed, 297 passed**, the named failures being
`test_selftest.py::test_a_submission_of_nothing_scores_nothing_on_every_paper`
at parameters `[None]` and `[nothing2]` among others. It has not reproduced:
`test_selftest.py` alone → 34 passed; `test_discrimination.py` +
`test_selftest.py` → 55 passed; the full suite → **308 passed**, three times.
Ordering is not the explanation — there is no `conftest.py` and no random-order
plugin, so collection order is fixed. The failing run was issued in the same shell
line immediately after `python -m exam.tools.discrimination` in write mode, and
three other agents were being terminated by a quota limit at that moment; neither
is a mechanism I can demonstrate. **The cause is not established.** The tests
concerned belong to the marker's self-test and are untouched by this run's changes,
which is a reason to look again rather than a reason to relax: an assertion failure
that appears once and cannot be reproduced is exactly the shape of a real
concurrency defect, and this repository has already been bitten once by a test that
passed while silently overwriting a committed artefact (`ec3ad44`).

## Caveats a reader should carry

* **The instrument is weaker than its name.** `class` is exactly a function of
  `(split, frame_changes)` — zero violations in 236 items — so it does not measure
  difficulty, and `theory` is an upper bound on the informative residue rather than
  its size. This is stated in the module docstring, not only here.
* **The prior is a baseline choice, not a fact.** It is a world model, brought in
  rather than learned. That is the point — no instrument in the exam separates
  those two — but a reader who wants a different baseline will get a different
  residue, and the number moves with the choice.
* **Twenty synthetic worlds and one marker.** Nothing here is a claim about ARC,
  about a real examinee, or about the framework's own arms.
* **The leak is reported, not fixed — and it is not the one-line change this run
  first called it.** Setting `tags=(split,)` still leaves **16 items across 4
  worlds** refused by the gate, because the sheet also publishes `Paper.world`:
  `world_id` (the string `t1-walk-maze` contains `walk`) and `families`
  (`['push']`). A real fix touches at least three places and must decide what to do
  about `world_id`, which cannot be dropped without breaking provenance. Left for
  its own item because a defect present in every published number since V2 deserves
  the V2 artefacts re-derived behind it, not a quiet edit inside a measurement run.
* **Marker misjudgements are all in the verdict label, never in the mark.** No
  examiner, across twenty worlds and several hundred crafted answers, found a case
  where the marker paid for an answer it should not have, and both structural
  invariants — silence is never paid, ground truth is never marked wrong — hold
  everywhere.
