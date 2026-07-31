# Two tickets to raise, neither in a territory I can hold

RES-3, cycle 108, 2026-07-30. Both fall out of V6-V23 and neither is `exam`, so
they are requests rather than `assign.py` calls.

## 1 — `Theoria.md:259` still states the premise this run measured and refuted

The line reads, verbatim: 「(ii) 大空間不可解——穷举不可行，唯不变量推理能答，
我们的主场」. V6-V23 measured that and it is false on every shipped instance of
the class. **Every class (ii) item is settled by an exhaustive computation over
at most 600 nodes** — `crux_quotient_settles.json`, four different mechanisms,
against claimed bounds of 1.15e18 to 1.33e36. The field asserting otherwise,
`exhaustive_feasible: False`, has been withdrawn and replaced by
`naive_enumeration_feasible: False`, which is true, measured and narrower.

That withdrawal has been carried to `exam/DECISIONS.md` (D-EX-028),
`exam/STATUS.md`, `exam/README.md`, `exam/SEALED_DRILL.md`, `sealed_drill.py`,
`test_sealed_drill.py` and the run's own `CRITERION.md`. It has **not** been
carried to the design document, because `Theoria.md` is nobody's territory and
`exam` cannot reach it. So the repository's most-read document still tells a
reader that class (ii) is "our home ground" on a ground the artefacts have
vacated, and every downstream document that agrees with the artefacts now
disagrees with `Theoria.md`.

The amendment is small and the claim to replace it with is already written:
class (ii) measures **method selection under an apparent search barrier**, which
is weaker than the design document and is the only form the artefacts support —
and is falsifiable by one counterexample examinee, where a universal over all
methods is not establishable by any experiment.

Suggested item: territory `theoria-doc` (or whoever owns the design document),
priority 1, body pointing at D-EX-028 and `crux_quotient_settles.json`. It
should say explicitly that this is a **withdrawal, not a softening**, so the next
reader does not restore it as a stylistic edit.

## 2 — `exam/tools/archive_run.py` stamps provenance from the working copy

`_digest_tree` hashes `open(path, "rb").read()` for every file it archives. That
is the disk, not the bytes git publishes, and under an `eol=lf` pin the two can
differ silently: `git diff`'s stdout is empty for such a file, and after a `git
add` even git's own CRLF warning stops.

Measured across all 13 `exam/runs/*/MANIFEST.json` against the index: **36 stale
hashes in 8 manifests, of which 6 are this defect**, sitting in four different
sessions' runs — `20260729T020000Z-V5` (`multiplicity_lift.txt`),
`20260729T1130Z-V21` (`adversarial/MUTATION_TABLE.txt`), `20260729T1820Z-V25`
(four of its own artefacts including `token_census.json`), and V6-V23's own. Four
sessions, one defect, so it is the tool rather than the sessions. The four
per-run stampers those runs each wrote (`seal_manifest.py`, `write_manifest.py`)
share the same line, which is where the lineage is visible.

Why it matters beyond tidiness: V27 already records that `archive_run.py` folds
`build_manifest.json` into what it writes, and the Phase 4 release manifest
publishes every tracked file. A provenance record that pins bytes the repository
does not contain is worse than none, because it reads as a check that passed.

The fix is one function and it is **not** "normalise before hashing" — that
would paper over a genuinely modified working copy. It is to hash what git will
publish and to report when the two differ. A worked version is in
`exam/runs/20260730T021500Z-V23-large-space/restamp_manifest.py`, with its
negative controls in `exam/tests/test_run_manifest_v23.py`.

This overlaps `V2-V25-verify-does-not-check-what-is-committed` closely enough
that folding it in there may be right — V2-V25's subject is "a check runs, goes
green, and is not measuring what its name claims", and this is the same sentence
one directory over. I would rather it be one ticket than two half-done ones. I
intend to claim V2-V25 when V6-V23 delivers, so if the monitor agrees, no new
item is needed and this note is the evidence hand-off.
