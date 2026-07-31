# V2/V25 — verify went green for weeks without ever comparing a build to what is committed

Cleanup campaign 2026-07-31. Branch `cleanup2/v2exam`, base `6fabcc7e`.
Territory `exam`. Zero API calls, zero network, zero sealed-pile contact, no
credential value anywhere.

The ruling is `exam/DECISIONS.md` D-EX-032. This file is what was done, in what
order, and the two things the work found that the ticket did not predict.

## The defect, in one sentence

`build_papers` overwrites `exam/artifacts/` in place and runs as verify's first
stage, so by the time any stage could have asked "is what is committed what this
code produces?", the committed bytes were gone from the working tree — and no
stage asked. The determinism stage compares two *fresh* builds to each other in
memory (`PYTHONHASHSEED` 7 vs 99) and opens no committed file at all.

## The four things the ticket asked for

1. **`artifacts_match_committed`, and the restructure that makes it possible.**
   `exam.model.ARTIFACTS` now honours `EXAM_ARTIFACTS_DIR`. `exam/verify.py`
   seeds a temporary copy of `exam/artifacts`, runs `build_papers`,
   `run_exam --calibrate` and `run_selftest` against it, and never writes into
   the tracked tree at any point in the run. The new stage
   (`exam/tools/check_artifacts_match.py`) then asks two questions, both of which
   must hold: `git diff HEAD -- exam/artifacts` is empty, and every tracked
   artefact reproduces byte for byte in the shadow tree.

   Per the S23 precedent, **comparison, never silent adoption**: the gate prints
   the two dispositions (stale artefacts → rebuild and commit; mistaken
   generator → revert the generator), says that deciding between them is a
   judgement, and exits 1. Adoption is running `build_papers` on purpose.

2. **Regeneration, per RES-3's ruling — and there was nothing to regenerate.**
   RES-3 (V25 cycle 72) had already settled step 2: the drift was stale committed
   artefacts, not an edited rubric, so the disposition is rebuild-and-commit. I
   did not re-derive that. What the new gate measures on today's master is that
   **all 41 tracked artefacts already reproduce**, `rubric_digest`
   `f01dbeb2b6c6`, with the producers rewriting 32 of them and 0 differing. The
   `e06bdf52` / `63ce1eab` mismatch was a property of the branches lagging
   `18a39417`; merging them regenerated the artefacts before this ticket ran.
   RES-3 said as much about master ("master 上没有漂移") and the measurement now
   agrees. So there is no artefact commit in this delivery, and that absence is
   itself a gate output rather than an omission.

3. **`build_manifest.json` repo-relative.** Already true on master (V27), and
   `exam/tools/check_artefact_locations.py` already enforces it — extended, not
   duplicated. What changed is where the rule lives: see below.

4. **Negative sample.** Recorded in `NEGATIVE-SAMPLE.md` in this directory: one
   flipped byte in one artefact, verify red; clean tree, verify green. Both
   directions, because a gate that always says "drift" is as green in a
   one-sided test as one that always says "match".

## The two things the work found that the ticket did not

**The redirect had to be earned: two artefacts recorded where they were built.**
The first shadow build reported drift in `build_manifest.json` and
`truth/p15-verdict-a2.truth.json` — not real drift, but
`os.path.relpath(path, REPO)` resolving to
`../../AppData/Local/Temp/exam-shadow-…/variant_specs/…` under the redirect. A
gate whose own mechanism produces the finding can never be green, so `_repo_rel`
moved out of `exam/tools/build_papers.py` into `exam.model.artifact_rel`, became
relative to the **artefact root** rather than the repo root, relabels to
`exam/artifacts/…`, and raises on a path outside the tree. `exam/papers/verdict.py`
(`spec_file`, 17 values in the verdict key) and `exam/tools/run_exam.py`
(`report_path`, which lands in the tracked `exam_summary.json`) now use it too.
D-EX-031's rule is unchanged; it now has one implementation instead of three.
The `report_path` case had never shipped an absolute path only because every
committed summary has `marked: []` — one marked submission was all it needed.

**"0 rebuilt" was an honest-looking lie.** The first version of the coverage line
counted files whose contents differed from the seed, which on a green run reads
`0 of 41` — indistinguishable from a gate that compared nothing. It now counts
files a producer *wrote* (by mtime) and files that *differ* separately:
`producers rewrote 32 of 41 tracked artefacts; 0 of those differ from the seed`.
A gate has to state its own coverage, or its green is unreadable.

## Gate outputs

Recorded verbatim in `GATE-OUTPUT.md` and `NEGATIVE-SAMPLE.md` in this directory.
