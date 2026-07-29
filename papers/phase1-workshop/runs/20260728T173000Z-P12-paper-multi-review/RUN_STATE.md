# RUN_STATE — P12-paper-multi-review

Written incrementally. The run directory keeps the name its **first** holder
gave it (`20260728T173000Z`); this file is the **third** holder's narrative.

| | |
|---|---|
| item | `P12-paper-multi-review` |
| worker | `W-1651` (third holder) |
| branch | `agent/p12-paper-multi-review` |
| base_commit | `31bea4664d75e8ec6b14e093e85633db7470aebf` |
| subject | `papers/phase1-workshop/PAPER.md`, v0.3, 2572 lines |
| subject sha256 | `500867cdb66e38a258da51acde9ad0709242d8bb68e841b6f3c9f6acff6a8cbc` |
| API cost | $0.00 — zero network calls, zero model calls against the game API |

---

## 1 · Inheritance — what I found, and why I did not restart

Two prior holders died mid-run. I checked before rebuilding, as the ticket
instructed.

| review | file | bytes | author | state on arrival |
|---|---|---|---|---|
| (a) domain | `review-a-domain.md` | 39 105 | RES-2 | **complete** |
| (b) method | `review-b-method.md` | — | W-1632 | **absent from disk** |
| (c) repro | `review-c-repro.md` | 488 | W-1632 | **stub**, "Status: IN PROGRESS" |
| (d) adversarial | `review-d-adversarial.md` | 40 622 | W-1632 | **complete** |
| (e) lay reader | `review-e-lay.md` | 35 864 | RES-2 | **complete** |

**The three complete reviews are reusable and I reused them.** All three were
written against `PAPER.md` at sha256 `500867cd…f6a8cbc`. I re-hashed the file at
my own `base_commit` and it is **byte-identical**; `git log 29f41ea..master --
papers/` is empty. Re-running them would have bought a second opinion on the
same text and nothing else.

**Reviews (b) and (c) I re-ran from zero.** Reviewer (c) was told explicitly to
overwrite the stub rather than treat it as findings to agree with — a
half-finished audit is a worse starting point than none, because it anchors.

### A discrepancy in the inherited record, left standing

The inherited `MANIFEST.json` lists `review-b-method.md` under
`reviews_run_by_this_holder`. **That file does not exist on disk.** The manifest
records an intention as an accomplishment. I have not edited it — it is prior
provenance and append-only discipline says supersede, not overwrite — but the
gap is recorded here and in §2, which I think explains it.

## 2 · The disk was full — and it is probably the real cause of death

Mid-run, an ordinary `sed` failed with `No space left on device`. `C:` had
**0 bytes free**. Not nearly full: zero.

The culprit was outside the repo:
`%LOCALAPPDATA%\Temp\DiagOutputDir\RdClientAutoTrace`, **8.99 GB across 1090
files**, Remote Desktop client rolling diagnostic traces, still being written
that morning. I deleted that one directory and nothing else — no worktree, no
`runs/`, no tracked file — which freed 9 GB.

Why this belongs in a paper-review run state: **all three interrupted artefacts
stop at the moment of a file write.** `review-b-method.md` is registered as
written and is not on disk; `review-c-repro.md` stops after its header;
`missing-reference-material.md` stops at "in progress". The recorded cause of
death for both holders is session-quota exhaustion. Quota death removes the file
*and* the registration together; it does not produce a manifest that claims a
file that was never written. I cannot prove disk exhaustion was the cause and I
am not asserting it. I am asserting that the recorded cause does not fit the
evidence, and that both deaths should be re-marked **contested**.

Filed to monitor as
`monitor/inbox/20260729T013737Z-W-1651-disk-hit-zero-free.md`, with three
recommendations that are not mine to execute: cap the trace directory, add a
free-space check to the worker start ritual, and get someone to clean up the
100+ accumulated worktrees.

## 3 · Method

Five independent single-perspective reviews. No reviewer was told what any other
found; each was given one remit and the project's red lines (sealed-pile zero
contact, zero API spend, no credential values in tracked files). Cross-tabulated
afterwards by me into one revision list. Where reviewers disagree, the ticket
requires the disagreement be **preserved and adjudicated in the open**, not
averaged away.

## 4 · Baseline gate before any edit

`papers/phase1-workshop/verify_paper.py` — inherited from W-1632, untracked on
arrival, and a genuinely good piece of work: it is the executable half of
`CITECHECK.md`, which is only a report and so cannot fail a build.

Baseline at `base_commit`, before I changed anything:

```
[PASS] A GENERATED  -- PAPER.md == assemble(sections/)
[FAIL] B PATHS      -- 162 citations: 149 ok, 9 ambiguous-but-ruled, 2 elided, 2 broken
[FAIL] C FIGDATA    -- fig1_concept_timeline.json changed on rerun
[PASS] D NOSECRET   -- no credential value in any published file
verify_paper: FAIL (2/4)
```

This baseline is recorded **before** the revision list exists, so that "the gate
passes" at the end cannot be confused with "the gate was always passing".

---

*(sections 5+ — cross-tabulation, revision list, and what was implemented —
appended as the run proceeds)*
