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

6. **Re-verified the whole adversarial pass from a clean worktree before
   delivery.** V7 was RES-2's item; that session died and the monitor released it
   at `2026-07-28T18:08:25Z`. RES-3 re-claimed it at `2026-07-29T04:48:57Z`,
   finished the pass, and then ran every adversarial script again rather than
   quoting the first run — three subagents, no relaying. `ADVERSARIAL.md` beside
   this file is that record, claim by claim. It cost three corrections, all to
   the *attacking* scripts rather than to any published number: `c2_ablate.py`
   compares a rounded fraction against an unrounded floor and so reports
   `beats_floor: 19` where the published 18 is right; `legend["floor"]` turns out
   not to be load-bearing at all (removing it is bit-identical to baseline, so §2's
   "load-bearing half" is `agent` and `wall` only); and `flipcheck.py` does not
   demonstrate what its docstring claims — it prints nothing when run as a script,
   flips one of the two strict xfails rather than both, and had no recorded
   invocation recipe until `ADVERSARIAL.md` supplied one (with both transcripts
   now saved beside it).

7. **Sent `ADVERSARIAL.md` itself to an adversary before delivering it**, which
   returned twelve defects, one of them blocking: **`FINDINGS.md` §8 still called
   the leak fix "a one-line change"** — the exact claim §1 had retired four
   sections earlier. A document that corrects itself in one section and repeats
   the error in another is worse than one that never corrected it, because the
   correction is what a reader trusts. Fixed, along with a residue stated as
   "30 → 16" (the fall is 69 → 16; 30 is `139 − 109`, a different quantity, and
   restating it reinstated the very category error §3 had retired), a
   double-count named in §2 but not cross-referenced from §3, and a "survived"
   on claim 3 that was really "was not attacked": nothing in the run
   re-implements the `free`/`memorised`/`theory` partition, so the 41.1 %
   headline still rests on the single tool that reports it. That gap is now
   written down as the largest thing the item still owes.

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
* **A cheap grid prior scores 1.000 on twelve of the twenty worlds**, beats
  the bluffer floor on eighteen, and takes **109 of 139 frame-changing items
  (78.4 %)**. Eight lines, no per-world constant, sheet fields only. **It is not
  theory-free, and this run's headline called it that.** Every number above
  reproduces byte-identically and none of them moves; the adjective is what was
  wrong. The prior carries brought-in world knowledge in two places, both
  measured: the sheet's `legend` (strip `legend["agent"]` and it falls to 0.4110,
  the bluffer floor) and the row/column orientation convention baked into its
  `DELTA` table — **reverse `DELTA` and it scores 0.2034, transpose it and it
  scores 0.1017**, both far *below* the 0.411 floor. A genuinely theory-free
  prior could not be halved by relabelling which way is up. See `ADVERSARIAL.md`
  and FINDINGS §2.
* **The paper's zero-discrimination share is 41 %, and that is the optimistic
  figure.** Measured against the prior, the informative residue falls from 69
  items to **16**, and to **zero on fourteen worlds**. Nine examiners independently
  reported their world's honest effective size as 0.

## Verification

```
python -m pytest exam/tests -q          308 passed, 2 xfailed in 106.66s  (287 before, +21 new)
python -m exam.tools.discrimination                   20/20 worlds, 0 dead, 0 anomalies
PYTHONPATH=. python .../prior_sweep.py                12/20 worlds at 1.000
```

(This block said `304 passed (287 before, +17 new)` until the adversarial pass.
`MANIFEST.json` — which is the canonical record and was right — says `passed:
308, added_this_run: 21`, and a re-run confirms 308. A narrative that disagrees
with its own manifest is the narrative that is wrong.)

**A committed artefact is stale and no test guards it.**
`exam/artifacts/matrix/heldout_worldgen.json` carries `rubric_digest
4afe3d17…`; the live registry digest is `e06bdf52…`, which is what every other
tracked artefact under `exam/artifacts/matrix/` carries
(`discrimination_worldgen.json`, `verdict_confusion.json`). So running the
documented `python -m exam.tools.run_matrix` rewrites that line and leaves a
committed file dirty in a working tree that was clean. Recorded, not
regenerated: re-deriving it here would fold an artefact refresh into a
measurement run, which is the move `ec3ad44` already cost this repository once.
It needs its own item, with a test that fails when a tracked artefact's digest
falls behind the registry.

Determinism: `test_the_profile_is_deterministic` compares two profiles of the same
world; the profiler adds no clock and no RNG, inheriting `heldout_worldgen`'s
salted-hash ordering.

**The failing run is explained, and it is a real concurrency defect in
`exam/`.** On the first full-suite run after the adversarial corrections landed
the suite reported **11 failed, 297 passed**, the named failures being
`test_selftest.py::test_a_submission_of_nothing_scores_nothing_on_every_paper`
at parameters `[None]` and `[nothing2]` among others. It did not reproduce
serially — `test_selftest.py` alone → 34 passed, the full suite → 308 passed,
three times — and this run first wrote down "the cause is not established". It
is now established, and the earlier guess was wrong.

*The mechanism.* `exam/papers/verdict.py::_emit_spec` (lines 464-488) writes
each of the paper's **17 variant specs into `exam/artifacts/variant_specs/` —
a shared, tracked, non-temporary directory** — through `exam/model.py:73
write_json`, which opens the target with mode `"w"`. `open(path, "w")`
truncates on open, so between that call and the first byte of JSON the file on
disk is **zero bytes**. `_emit_spec` then reads the same path straight back with
`Variant.load(path)` at `verdict.py:479` to validate it. Two `verdict.build()`
calls in different processes share that directory, so one builder's read can
land inside another builder's truncation window and gets an empty file:
`json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)`, raised
at `verdict.py:479`. `build()` is called by every test that touches the verdict
paper and by three tests that loop over all four `BUILDERS`, which is why the
failure moves from test to test and never reproduces alone.

*The evidence, re-run here rather than taken from the adversarial report.*

```
6 concurrent workers x 12 verdict.build()   -> 2 JSONDecodeError, both at verdict.py:479
pytest exam/tests/test_selftest.py -q
  with 4 concurrent verdict.build() hammers -> 1 failed, 33 passed in 60.02s
```

The single failure under load was
`test_a_submission_of_nothing_scores_nothing_on_every_paper[None]` — the exact
test, at the exact parameter, this section originally recorded as unexplained.
The adversary's independent run of the same experiment failed at
`test_no_sheet_names_the_genre_of_the_world_it_asks_about` instead, which is the
point: the defect is not attached to any one test.

*The earlier hypothesis is refuted.* This section previously noted that the bad
run was issued immediately after `python -m exam.tools.discrimination` in write
mode, and floated that as a possible clobber. Nothing in `exam/` reads
`exam/artifacts/matrix/discrimination_worldgen.json` — it is a write-only
output — so that path cannot reach the self-test. The shared file that matters
is the variant spec, not the discrimination artefact.

*Severity.* The 17 spec files are **tracked**, so the truncation window is also a
window in which a committed artefact is momentarily zero bytes; a build killed
inside it leaves the repository dirty with an empty tracked JSON file. Every
number this run and V4 published stands — the defect makes builds crash, not
mismark — but the suite is not safe to run concurrently with anything that builds
the verdict paper.

*Left unfixed on purpose*, and pinned instead:
`exam/tests/test_verdict.py::test_a_concurrent_builder_cannot_hand_emit_spec_an_empty_spec`
is a deterministic negative control marked `xfail(strict=True)`. It reproduces
the interleaving without a race — it truncates the shared path at the moment
`Variant.load` opens it — and it will flip to a suite failure the day
`_emit_spec` stops depending on re-reading a path another builder can truncate.
The fix (a private temp path, or validating the spec text in memory) is small,
but it belongs in an item that can also decide whether `SPEC_DIR` should be
per-process at all.

## Caveats a reader should carry

* **The instrument is weaker than its name.** `class` is exactly a function of
  `(split, frame_changes)` — zero violations in 236 items — so it does not measure
  difficulty, and `theory` is an upper bound on the informative residue rather than
  its size. This is stated in the module docstring, not only here.
* **The prior is a baseline choice, not a fact, and not theory-free.** It is a
  world model, brought in rather than learned. That is the point — no instrument
  in the exam separates those two — but a reader who wants a different baseline
  will get a different residue, and the number moves with the choice. Two
  ablations put a number on how much world knowledge it carries: without
  `legend["agent"]` it scores **0.4110**, exactly the bluffer floor, and with its
  `DELTA` table reversed or transposed it scores **0.2034** and **0.1017** —
  *below* the floor. The row/column orientation convention is load-bearing. An
  eight-line function that a relabelling of the compass can cut in four is
  carrying a theory.
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
* **On the held-out rubric, marker misjudgements are all in the verdict label,
  never in the mark. That is the whole of what survives, and this run claimed it
  "everywhere".** Scoped and re-run here: **11 712 probes over all 236 worldgen
  items** through `exam/grading/rubrics_heldout.py` — ground truth in eight
  wrappers, 21 spellings of silence, and per-item mutations of the truth
  (one-cell, transposed, reversed, ragged) — give **0 cases where the marker paid
  for an answer it should not have, 0 where silence was paid, and 0 where ground
  truth was marked wrong**. That claim stands.

  **It does not generalise, and on the adaptation paper it is false.** Submitting
  the bare empty list `[]` as the answer to every item scores **6.500 of 144**.
  The cause is `exam/grading/rubrics_adaptation.py::_read_set`: when the answer
  is not a dict it uses the *whole answer* as the value for every set-valued key,
  so one `[]` asserts the empty set for `rules_falsified`, `claims_to_reexamine`
  **and** `claims_now_false` simultaneously and collects the weight of each
  wherever the truth happens to be empty. The module's own `_read_claim` calls
  `[]` illegible — `exam/tests/test_selftest.py:286` asserts exactly that — so
  the marker pays, on one rubric, for an answer it declares unreadable on
  another. Two smaller cases sit beside it: `"unsolvable"` everywhere scores
  **12.000 of 144** on adaptation (and **9.000 of 34** on the verdict paper), and
  the bare integer `0` scores **1.000 of 144**. Those two are legible answers
  that happen to be right somewhere, which is defensible; `[]` is not.

  Pinned, not fixed:
  `exam/tests/test_selftest.py::test_the_bare_empty_list_is_not_paid_on_the_adaptation_paper`
  is `xfail(strict=True)`. Fixing `_read_set` would move V4's already-published
  calibration numbers, so it belongs in an item that re-derives them.
