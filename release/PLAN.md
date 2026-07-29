# release/PLAN.md — the release kit, planned before it is built

`P5-release`, RES-2, branch `agent/p5-release`, base `398144e`. Written before
any manifest code, per this repository's own rule that a plan precedes the
artefact it describes. Nothing under `release/` existed before this file.

## What the item asks for

`monitor/board/items/P5-release.md`: an enumerator that lists everything that
should be released (ledgers, the two books in four forms, the Lean proofs, the
candidate box, probe logs, battery code and results, the incident ledger, the
`runs/` archive), sha256 per file into `release/MANIFEST.jsonl`, ticked or marked
absent against `Theoria.md`'s release list; a `release/reproduce.py` that re-runs
the deterministic artefacts per territory and compares hashes into
`REPRODUCTION_REPORT.md`, grading honestly what cannot be re-run; a
`REPRODUCING.md`; and then **a fresh subagent as the stranger**, following the
document, with the document fixed rather than the stranger. Red lines: no `.env`
value and no sealed-pile frame data anywhere in the release set.

> **Corrected at step 1.** The section below frames the constraint as being about
> **frame data**. That is too narrow, and too narrow in the dangerous direction —
> it came from reading `R2`'s summary rather than `browser-ops/TERMS.md` itself.
> ToS §4's first prohibited activity names *"a collection, compilation, database"*,
> and a ledger of API interactions is literally that. The constrained class is
> everything systematically retrieved and compiled — frames, actions, scores,
> scorecards and the ledgers holding them. `release/LICENCE_POSTURE.md` carries
> the corrected classification; this section is left as written, because a plan
> whose wrong turns are quietly deleted teaches nobody.

## The constraint the item does not mention, and it changes the shape

**`R2-release-licence` is not an optional follow-up; it is a precondition on the
manifest.** OPS-B established from the benchmark's own terms
(`browser-ops/TERMS.md` §2, per-page provenance in
`browser-ops/runs/2026-07-28-visits.md`) that locally cached **frame data needs
no extra licence to hold, but re-releasing it requires written permission and is
forbidden by default** — the ToS wording is "without our express prior written
permission".

This bites directly on `Theoria.md:379`, which sets the release's ambition as
*"scale and openness reaching Schema's floor (the full public set + artifacts)"*.
On frame data that target **cannot be met**, and the release kit must not be
built as though it could. Concretely, the enumerator needs a **licence filter as
a first-class stage, not a later patch**:

* raw frames (`env_step`'s `frame` field, and any frame dump) are **excluded by
  default**;
* what ships instead is a **frame hash plus a reproduction script**, so anyone
  with their own key can regenerate them;
* `release/LICENCE_POSTURE.md` classifies every artefact class as
  releasable / needs-permission / not-releasable, citing `TERMS.md` line numbers;
* **nobody applies for permission** — that is a human decision and goes in
  `needs_human`.

Building the manifest first and filtering afterwards would mean computing, and
probably committing, a manifest that lists frames as releasable. **The filter
goes in before the first manifest is generated.**

## Order of work

1. `release/LICENCE_POSTURE.md` — the classification, from `TERMS.md`, first.
2. The enumerator, with the licence filter as a stage of it. `MANIFEST.jsonl` is
   append-only and one JSON object per file: path, sha256, size, class,
   licence verdict, and the checklist item it satisfies.
3. The checklist cross-walk against `Theoria.md:379`'s list — ticked or **marked
   absent with a reason**. An item silently missing from a release manifest is
   the same failure this repository has now hit twice in figures.
4. `reproduce.py` — re-run per territory, compare to the manifest hashes, grade:
   `reproduced` / `needs-API` / `needs-ground-truth` / `not-reproducible`. The
   grading is the honest part; a report that only lists successes is a report
   that measures nothing.
5. `REPRODUCING.md`, then the stranger subagent. **Fix the document, never the
   stranger** — the whole value is that the stranger has no context, and coaching
   them destroys the instrument.
6. Red-line self-audit, and it must be **executable**, not a paragraph:
   * no `.env` value anywhere in the release set. Note the shape of this check:
     it must not itself write the key anywhere. `arc-recon/client.py` already
     redacts, and `load_api_key()` + a constant-time compare against file
     contents is the way, never printing the value.
   * no sealed-pile frame data. The sealed pile is the 21 games in
     `arc-recon/data/piles.json` (sha256 `3feca53e…41bbc19a`); the check reads
     the cut from that file rather than from a copied list.

## Two hazards worth naming before starting

**A release manifest publishes every tracked file.** `CLAUDE.md` says this
plainly: a key committed here is a key published later, and git history makes it
effectively irreversible. So the red-line audit is not a final step to run once
the kit is finished — it is the thing that decides whether the kit may be
generated at all, and it should run *first* and on every regeneration.

**The `runs/` archive is large and full of other tracks' work.** Enumerating it
is in scope; deciding what another track may publish is not. Where the licence
or pile status of an artefact is unclear, the manifest records
`verdict: needs_human` rather than guessing in either direction. A release kit
that quietly excluded something is as wrong as one that quietly included it, and
only one of those two is recoverable.

## Status

**All six steps done.** `LICENCE_POSTURE.md` and `check_redlines.py` (both red lines
measured clear); `enumerate.py` and `MANIFEST.jsonl` (1,940 rows, byte-identical
across two runs, red lines gating generation); `checklist.py` and `CHECKLIST.md`
(6 present, 3 withheld, 1 absent, plus two items that matched and still were not
what the list asks for). `reproduce.py` and `REPRODUCTION_REPORT.md`
(3 of 9 declared targets reproduced; the rest graded, not hidden). `REPRODUCING.md` (the checklist's
last ABSENT item now closes: 7 present, 3 withheld, 0 absent). and the stranger subagent ran against a clean
clone with no `.env`. It got stuck on the document's **second command** and
found seven defects; all are fixed and recorded in `RUN_STATE`-equivalent form
in the commit history. Two upstream findings it surfaced -- the battery drifting
and an exam artefact embedding absolute maintainer paths -- are reported to the
monitor and are not this territory's to fix.

**Order matters and is enforced:** `enumerate.py` -> `checklist.py` ->
`reproduce.py`. Running reproduce against a manifest written before the tree
moved grades every target `manifest-stale`, which is the script refusing to
measure the baseline instead of the build.

Previously: **plan only.** No enumerator, no manifest, no reproduce script yet. The next
session starts at step 1 — and should read `browser-ops/TERMS.md` §2 and
`browser-ops/runs/2026-07-28-visits.md` before writing a line of it, because
that is where the licence verdict actually comes from.
