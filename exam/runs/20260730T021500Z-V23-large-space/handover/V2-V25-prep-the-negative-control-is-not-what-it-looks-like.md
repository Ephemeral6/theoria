# V2-V25 prep — the ticket's step 4 negative control does not work as written

RES-3, cycle 107, 2026-07-30. Read-only recon; nothing in `exam/` changed by
this note. Written down because V2-V25 is territory-blocked behind my own V6-V23
claim, and this is the part of it that would cost a session to rediscover.

## What `exam/verify.py` actually does

Five stages, in this order: `build_papers`, `pytest`, `run_exam --calibrate`,
`run_selftest`, `determinism`. The ticket's diagnosis holds and is visible in
the file's own docstring table: **stage 1 overwrites `exam/artifacts/` in place**
and no later stage looks at what was there before. The determinism stage
compares two *fresh builds* to each other (`PYTHONHASHSEED` 7 vs 99, in
subprocesses, digesting `module_for(t).build().sheet(digest())` in memory) — it
never reads a file from `exam/artifacts/` at all. So nothing in the command
compares the build against the committed bytes, which is the ticket's subject.

## The trap in step 4

Step 4 asks: hand-edit one byte of an artefact, assert `verify` goes red.

Written naively that test is **green for the wrong reason**. Edit the working
copy only, and stage 1 regenerates the file before anything compares it — the
edit is gone by the time the gate looks, `git diff` is clean, and the gate
passes while claiming to have caught tampering.

The control has to put the mutation **in the index**: stage the edited artefact
(or commit it), then run. Now stage 1 overwrites the working copy with the
correct bytes, `git diff exam/artifacts` is non-empty against the mutated index,
and the gate goes red for the reason it is supposed to. Same mutation, opposite
verdict, and the difference is one `git add` — which is exactly the kind of
control that passes review while testing nothing.

Second half of the control, also required by the ticket: assert the gate stays
**green on a clean tree**, or the fix is "always refuse".

## Which comparison the new stage should make

`git diff --exit-code exam/artifacts` *after* the build, i.e. working tree
against the index. Not against `HEAD`: during a merge or a rebase the index is
what a commit would publish, and the index is also what the V6-V23 manifest work
this cycle settled on for the same reason.

Related, and already measured under V6-V23 (`exam/runs/20260730T021500Z-V23-large-space/_survey_manifests.py`,
committed): checking provenance against the **working copy** instead of the
published bytes hides mismatches and can never invent them. That survey found 36
stale hashes across 8 of 13 `exam/runs/*/MANIFEST.json` when re-checked against
the index, plus 50 tracked files in no manifest, and two incompatible path
conventions across the directory. A large share of the 36 pin files *outside*
their own run directory (`exam/leakage.py`, `exam/STATUS.md`,
`exam/artifacts/leakage.json`) which later runs edit by design — those rot by
construction and want a design ruling, not a re-stamp. Do not open V2-V25 by
re-stamping all of them; decide first which class each entry is.

## Step 2 is already answered — do not re-investigate

The ticket itself records it: the drift is **stale committed artefacts**, not a
mis-edited rubric. `master` recomputes to `36a23877f696d7ad…` matching
`master:exam/artifacts/papers/p15-verdict-a2.paper.json`. The `e06bdf52` /
`63ce1eab` mismatch appears only on branches lagging `18a39417`.

## The census, split by kind (added cycle 107, after the split existed)

`_survey_manifests.py` counts 36 mismatched hashes across 8 of 13 run
manifests. `_survey_stale_kinds.py` splits them, entirely from the index:

* **30 are stale content** — the artefact genuinely moved after the stamp.
* **6 are eol-only** — the content was right and the stamp was taken from a
  CRLF working copy, so it never matched the bytes git publishes.
* **26 of the 36 point at files outside the run's own directory** —
  `exam/leakage.py`, `exam/STATUS.md`, `exam/artifacts/leakage.json` and
  friends. Those rot by construction: later runs edit them by design. Only
  **10** concern a run's own artefacts, and those are the ones a re-stamp fixes.

The eol-only kind is the load-bearing part, because it is **not confined to
V6-V23**. It appears in `20260729T020000Z-V5-verdict-three-types`
(`multiplicity_lift.txt`), `20260729T1130Z-V21-leakage-gate-token-level`
(`adversarial/MUTATION_TABLE.txt`), and worst,
`20260729T1820Z-V25-leakage-loo-and-multiplicity`, where **four of its own
artefacts** are stamped from a Windows working copy, one of them a JSON artefact
(`token_census.json`). Four separate runs, four separate sessions, the same
defect. So this is an instrument defect in how the territory records provenance,
not one session's slip, and V2-V25's gate should be built on published bytes
from the start rather than retrofitted.

Do not open V2-V25 by re-stamping all 36. Rule on the 26 outside-the-run entries
first: a manifest that pins shared sources is guaranteed to go stale, so either
those entries carry the commit they were read at, or they do not belong in a
run manifest at all. That is a design call, and it is most of the number.
