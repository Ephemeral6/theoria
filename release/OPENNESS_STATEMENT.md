# Openness statement — draft for the paper

`R2-release-licence`, deliverable 3. **A draft for the paper to adopt, not a
paper section.** It lives in `release/` because that is this item's territory
and because the numbers in it are produced by `release/bundle.py`; whoever owns
`papers/` should lift the prose, re-derive the counts at submission time, and
delete this note.

Authority for every licence claim: `browser-ops/TERMS.md` §2, whose per-page
provenance is in `browser-ops/runs/2026-07-28-visits.md`. The classification is
`release/LICENCE_POSTURE.md`; the file-by-file verdicts are
`release/MANIFEST.jsonl`; what actually ships is `release/BUNDLE.jsonl`; what
does not, with hashes, is `release/FRAME_HASHES.jsonl`.

---

## Draft (≈ 250 words, for a Data & Code Availability section)

> **Data and code availability.** All code, all design documents, all engine
> fixtures, and all derived statistics are released: 1,930 of the 1,950 tracked
> files in the repository, including every generator needed to rebuild the
> offline artefacts byte for byte.
>
> **Twenty files are withheld, and they are the ARC interaction records.** The
> ARC Prize terms of service permit local caching but require *"express prior
> written permission"* before content retrieved from the Services is
> republished, and the default is refusal. Our per-command ledgers pair ARC game
> identifiers with environment payload — frames, actions, responses — and are
> therefore compilations of retrieved content rather than our own observations
> about it. We have not sought that permission, so we do not publish them.
>
> **What we publish instead is a sha256 of each withheld file and the command
> that regenerates it.** A reader with their own ARC API key can reproduce the
> interaction records and verify them against our hashes; a reader without one
> can still confirm that the artefacts we describe are the artefacts we held.
> The withheld set is enumerated in full — path, hash, size, reason, recipe — so
> the gap is nameable rather than merely absent.
>
> **This is a real limitation and we state it as one.** Our stated target was
> openness matching prior work that released full public-set artefacts. On
> frame-level data that target is not met, and it cannot be met by us
> unilaterally: it requires a permission we have not requested. Every *claim* in
> this paper is checkable from what we do release; every *byte* of ARC
> interaction is not.

---

## Notes for whoever adopts this

**Re-derive the two counts before submission.** `python release/bundle.py`
prints them and rewrites both files; `--check` fails if they have drifted. They
were 1,930 / 20 when this draft was written, and the repository is still
growing.

**Do not soften the last paragraph.** The temptation is to write "for licensing
reasons, raw frames are available on request", which reads as though the
constraint were procedural and ours to waive. It is neither: the permission is
the rights-holder's to grant, and we have deliberately not applied for it
(`LICENCE_POSTURE.md`, `needs_human`). Saying so plainly is also the more useful
disclosure — a reader who wants the frames needs to know whom to ask, not to
email us.

**The 146 flagged files ship.** They are class C, derived statistics that
mention ARC identifiers without carrying environment payload; the flag is an
instruction to read them once before shipping, not a licence reservation. If a
reviewer asks why `CLAUDE.md` is flagged, that is the answer.

**One withheld file is probably misclassified in our favour of caution.**
`battery/tests/fixtures/ledger_fixture.jsonl` is written by a tracked generator
and contains nothing retrieved, but the file alone cannot prove it, so it is
held at class B. If it is reclassified before submission the count becomes
1,931 / 19. It would be wrong to quietly reclassify it to make the number
rounder.
