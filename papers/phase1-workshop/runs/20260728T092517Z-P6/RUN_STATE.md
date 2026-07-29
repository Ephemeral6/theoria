# RUN_STATE — P6-paper-assembly

Worker `W-1610`, 2026-07-28. Branch `agent/p6-paper-assembly`, base commit
`7724f60`.

## What the item asked for, and what is here

| goal | state |
|---|---|
| A3's C3 transfer adjudication into the body | **done** — new §6, `sections/06_a3_transfer.md` |
| theoria-arm's preflight into the body | **done** — new §9, `sections/09_preflight.md` |
| the exam's four question types + leak protection | **done** — new §8, `sections/08_exam.md` |
| every number points at a file; nothing unrun is written as a result | **held** — `PROVENANCE.md` gains §6 and §9 tables; the three sections' claims were extracted from the tree by three independent read-only passes, and each one's "could not find" list was applied |
| run CITECHECK | **done, and it is the most important output of this run** — see below |
| REVIEW's open items as a checklist | **done** — `OPEN_ITEMS.md` |

## The finding: §7 is stale, and no amount of editing fixes it

CITECHECK is a hand-written audit, not a script, so the check was re-run
mechanically. Citations came back with **0 broken paths** — nothing cited is
missing from the tree except gitignored `.toolchain/` — but **22 distinct
citations still violate the paper's own repo-relative rule**, 9 of them ambiguous
across 6 to 24 real candidate files. Four of those were introduced by this run's
own §6 and were fixed here; the other 18 are logged in `OPEN_ITEMS.md` §B.

The numeric spot-check is where it hurts. **The battery was rebuilt from v0 to v2
six hours after the paper's last commit**, and §7 now disagrees with every
artefact it cites:

| §7 says | the artefact says |
|---|---|
| 26 runs, 2 arms | 95 runs, 5 arms |
| 29 metrics, 15 main / 14 reference | 38 metrics, 9 main / 29 reference |
| 24 of 29 non-discriminating | 31 of 38 |
| 27 redundancy clusters | 32 |
| "there is no Schema arm and there may never be" | a `schema_repro` arm exists |

Everything downstream — the effect sizes, actions-per-call, the correlation, P5,
E5 — was computed over the 26-run v0 spectrum and cannot be patched number by
number.

**What was done about it, and what was not.** §7 now carries a standing note
stating that it reports v0, listing each superseded number against its artefact,
and naming the two known-wrong citations inside it (the determinism claim cites
D-B-001, which is the pile guardrail; the X5 cross-check is called independent and
is not). The section is left standing rather than deleted, because the four Phase
2 processes and the finding that three metrics measured something other than what
they claimed are properties of the instrument rather than of the run.

**Re-deriving §7 against v2 was not attempted.** It is a re-run of the battery's
analysis, not a copy-edit, and doing it from a fact sheet rather than from the
artefacts is exactly how the numbers drifted in the first place. It is item A1 in
`OPEN_ITEMS.md`.

## What the three new sections do and do not claim

Each fact-gathering pass returned a "would not let this into the paper" list, and
those shaped the prose more than the results did:

* **§6 (A3).** Reports the like-for-like bill (346 → 10 actions, four zeros in the
  inductive columns, verification unchanged), 252/252 against the referee, and
  both negative controls caught. It does **not** call 252/252 held-out — A3 has no
  held-out set — does not quote a canonical agreement percentage, and reports the
  playbook's transfer as a **design claim rather than a measurement**, because no
  code path reads `cold-start-a3/theory/playbook.dsl` and the byte-identity test
  its docstring cites does not exist.
* **§9 (preflight).** Reports 0 billable actions, 0 recorded bypasses, and a
  sealed-pile check that scans the bytes. It does **not** say an executable check
  confirms the credential is absent from the live ledger (the arm's archiver
  advertises that check and accepts an unused parameter instead of implementing
  it), does not say the double proxy ran end to end (the model side carries
  `proxied: false` and is a declared gap), does not say the spend gate bounded the
  run (it postdates it by seven hours), and does not say an episode can be
  replayed (the evidence is the environment's determinism on one game).
* **§8 (exam).** Reports the four papers, the calibrated marker, and 1 790 probes
  with 0 hits — then reports that the checker missed two real leaks because the
  hook it needed was optional and no paper implemented it, and that the coverage
  hole is still open on two papers. Says plainly that **three of the four papers
  have never been sat**, that the one real result saturated at the ceiling and so
  measures nothing about the playbook, and that the cheater's numbers exist only
  as prose because the artefacts are gitignored.

## Corrections to the item's own framing, applied

* "三类判决题" is **one** question type carrying three item classes, not three
  types. The code freezes exactly four.
* `exam/guard.py` is a network tripwire and a pile guard. The answer-key leak
  protection is `exam/leakage.py`. Writing the first as the second would have been
  wrong.

## Gaps

1. **§7 needs re-deriving against battery v2** (A1). Blocking, and it also blocks
   A2, because the abstract's "no game was played *for* this paper" has to be
   re-checked against whatever §7 becomes.
2. **A third audit pass is owed.** REVIEW was written against a 75 885-byte
   `PAPER.md`, CITECHECK against 91 244, and this run added three sections on top
   of both. Neither has seen the current draft.
3. **Two of REVIEW's six blocking items remain open**, both in the abstract.
4. **18 repo-relative citation violations remain**, and 5 of REVIEW's related-work
   priors are still uncited — the largest reviewer-facing gap.
5. **Length is now ~19 500 words** against a ~4 000-word workshop budget. The cut
   is still a separate pass and this run made it larger, not smaller.
6. `CITECHECK.md` and `REVIEW.md` are **not edited** — OUTLINE red line 3 — so
   their own stale entries (CITECHECK's target hash, REVIEW's claim that CITECHECK
   does not exist) stand, and are listed as struck in `OPEN_ITEMS.md` §G.

## Reproduce

```bash
cd .worktrees/p6-paper-assembly
python papers/phase1-workshop/assemble.py     # sections/*.md -> PAPER.md, deterministic
```
