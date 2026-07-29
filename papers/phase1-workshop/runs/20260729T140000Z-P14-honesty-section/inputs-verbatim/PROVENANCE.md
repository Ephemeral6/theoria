# Verbatim copies — provenance and why they are here

The four `SURVEY-*.md` files in this directory are **byte copies**, taken
2026-07-29T13:50Z, of untracked files at

    .worktrees/e11-engine-crosscheck-deep/engine-rig/runs/20260729T000000Z-E11-engine-crosscheck-deep/

on branch `agent/e11-engine-crosscheck-deep` at `6ee0466`.

They were copied because at the time of copying they existed in **no git ref at
all**: `git status` reported all four as untracked (`??`), the branch had not been
pushed (origin carried 17 refs, none for e11), and the run's own `MANIFEST.json`
did not list them. One machine-local copy was backing five work-board items and a
section of this paper. Losing the machine would have lost the evidence.

**These copies are not the canonical artefacts and must not become them.** The
canonical location is the engine-rig run directory above, and the fix is for
someone with that territory to `git add` and push the originals — RES-2 does not
write outside `papers/`. A request went to the monitor on the bus at
2026-07-29T13:55Z. When the originals land in a ref, cite those, not these; this
directory is an evidence pack for one paper section, dated and frozen.

Nothing here has been edited. The digest of them, with the discrepancies found
against their own claims, is `../evidence-survey-located.md`.
