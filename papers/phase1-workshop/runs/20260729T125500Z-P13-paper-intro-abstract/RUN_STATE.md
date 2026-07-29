# P13-paper-intro-abstract — run state

**Item:** `P13-paper-intro-abstract` · **Agent:** RES-2 · **Branch:**
`agent/p13-paper-intro-abstract` · **Base:** `a03fe99`

The brief written before this run is
`papers/phase1-workshop/runs/20260729T031000Z-P13-paper-intro-abstract/BRIEF.md`.
It set the acceptance test: a rewrite that does not fix the lay reviewer's
findings 1–4 has not done this item.

## What was rewritten

`sections/00_abstract.md` and `sections/01_intro.md`, entire. Three further
sections took a **class fix** rather than a local one, because the previous round
was criticised for applying a fix only where the reviewer pointed
(`runs/20260728T173000Z-P12-paper-multi-review/review-d-adversarial.md`: "The fix
was applied to the place the reviewer named and not to the class of error"):
`sections/03_a0.md` §3.3 heading, `sections/09_preflight.md` §9.4, and
`sections/10_limitations.md` §10.5.

`PAPER.md` regenerated with `assemble.py`; it is not hand-edited.

## Evidence gathered before writing

Four parallel evidence passes, all in this directory:

| file | what it settled |
|---|---|
| `evidence-arms-and-environment.md` | the five arms; ARC-AGI-3's definition; the game/world collision |
| `evidence-antigaming-register.md` | what the register is, its numbers, and that the paper's are stale |
| `evidence-metric-glossary.md` | which ids §1 uses undefined; the C3 count; the honest P3 sentence |
| `evidence-review-todo.md` | the 31-item to-do from the five P12 reviews, and the do-not-delete list |
| `evidence-six-specifics.md` | title, 98.98's denominator, §10.5, `trace_summary.json`, the live-run fusion, "controlled" |

## The acceptance test, item by item

1. **"The paper never says what benchmark it is about."** Fixed. §1.0 is a new
   subsection that defines ARC-AGI-3 (64×64, sixteen colours, hidden deterministic
   rules, act and observe), states the 25 public games, the level ladder, the
   scorecard, and the 4/21 pile cut, all with paths. The abstract opens on it.
2. **The word collision.** Fixed by declaring the convention in §1.0 —
   **game** = ARC-AGI-3 only, **world** = self-built — and by stating flatly that
   every pipeline result is on self-built worlds and that games enter the paper in
   exactly two places (§7's recompute, §9's two live runs). This is the paper's
   own dominant usage already (`sections/05_a2.md` contrasts "a sealed public
   *game*" with "a self-built 9×9 pushing *world*"), so it standardises rather
   than invents.
3. **"95 runs across 5 arms" — the arms are never enumerated.** Fixed in §1.5
   contribution 5, with each arm's id, one-clause description, control-or-framework
   status and run count, summing to 95. The same sentence discloses that the
   compound phrase "95 runs across 4 games" is false as a conjunction: 88 runs
   touch a development-pile game, 7 are synthetic.
4. **K2/K4 used in §1 six sections before they are defined.** Fixed: §1.3 now
   states the two quantities in words ("evidence coverage 1.000 and held-out
   accuracy 0.000") and glosses both ids inline from the metric cards, with the
   card's required companion figure (3 unannotated clauses) that the old §1 omitted.
5. **"Could not state the paper's claim."** §10.5 now opens with one sentence,
   and the abstract states the same sentence as its claim paragraph. The
   enumeration survives beneath it as an itemisation, not as the thesis.
6. **"The hook lands and then §1 dismantles it."** The disclosures are relocated,
   not deleted, into §1.6, after the contributions. Everything the P12 round marked
   do-not-delete is still in §1: the R-05 precision, the seal hole, the "not a
   minimal pair" correction, and the five scope disclosures.

## Changes of substance, not of arrangement

Everything below is a change to what the paper asserts, and each is a defect the
previous text had.

1. **Title.** "Certifying a world theory against something other than its own
   past" → "Neither layer certifies the manual against the world". §2.3 says in
   terms that neither certification layer certifies the manual against the world;
   the old title asserted what the paper's own framework section denies. The new
   title quotes §2.3.
2. **Subtitle.** No longer advertises "a transfer result" and "an examination
   instrument" — §10.5 disclaims both by name.
3. **"Eight results."** Removed. §11.3 says of the A2 exhibit that "it is not
   evidence about anything, and the abstract should not read as though it were";
   the abstract's numbered result list read as exactly that. The abstract is now
   claim-first.
4. **The lead contribution changed.** The anti-gaming register moves from item
   four of four to item one, and to the abstract's third paragraph. Two P12
   reviewers converged on this independently.
5. **The register result is one round out of date, and the paper now says both
   rounds.** §7.7 reports `battery/artifacts/gaming_audit.json` — 34 of 38
   exploits landing, main table 9. A blind pre-registered round is committed in
   the repository and is not in the paper at all:
   `battery/runs/20260729T021247Z-V9-battery-gaming-audit/v9_gaming_audit.json`
   has `verdict.gameable` 37, `verdict.b14_baseline_main` 9, `verdict.main` empty
   — 37 of 38 metrics driven to a pre-registered threshold and the main table
   reduced to zero, with 112 attacks written and 95 landing. `battery/METRICS.md`
   and `battery/STATUS.md` already carry the new number; the artefact §7 cites is
   frozen by `battery/PREREG_V9.md` §5 and does not regenerate. §1.2 and §10.5 now
   report both rounds and say which is which. **§7.7 itself still reports only the
   old round — a follow-up item is filed.**
6. **"98.98 on replayed history" was a misattribution.** `Theoria.md` §3.1 gives
   98.98 % as a *game score* on ARC-AGI-3 for a line of work whose *verification
   regime* is full-history replay. §1.1 now says which it is and states that the
   sources give no denominator, so none is asserted.
7. **"a controlled A0/A0′ contrast"** → "a paired A0/A0′ contrast, uncontrolled by
   construction", with the four confounded variables named. The abstract had been
   corrected on this in an earlier round and §1.3, §3.3's heading and §10.5 had
   not; all three now agree.
8. **"47 % of A0's state-action coverage" was arithmetically wrong.** 47 % is
   107/228 — A0′'s coverage of **A0′'s own** pairs (`sections/03_a0.md`). A0's own
   coverage is 99 %. Corrected.
9. **The live-run result fused two runs.** The preflight spent zero and has no
   byte-level sealing scan; the first-contact run carries the scan and spent 7
   actions and $6.32 in model calls. The abstract and §9.4 now keep them apart,
   and §9.4 additionally states that neither run byte-verifies the "injected in
   one place" claim.
10. **"No arm was run against a baseline" was false** — §6 runs three arms.
    Replaced with "no arm was run against another system's baseline … §6's three
    arms are all ours", plus the disclosure that there is **no language-model
    baseline anywhere in this paper**, which no previous draft stated.
11. **The intro's central claim now cites the decisive artefact.**
    `cold-start-a0/artifacts/trace_summary.json` is the only artefact that measures
    the trace's coverage and names the three uncovered pairs;
    `score_vs_truth.json` merely *labels* three pairs `held_out`. §1.3 cites both
    and states that they descend from one explorer, so the identity is auditable
    rather than independently confirmed.
12. **A0's seal and the battery's blind round are no longer presented as the same
    strength of evidence.** §1.3 says so explicitly: the blind round's ordering is
    checkable by a third party, A0's seal is a declaration by the authors' own
    script.
13. **The draft-status block** shrank from ~500 words to a binding-rule statement
    and pointers, and now names `verify_paper.py` as the executable half of the
    rule. The abstract's exemption from the path rule is restated, together with
    the condition under which it holds.

## Deliberately NOT done

* **No new literature citation.** Red line 6 forbids citing a record not
  cross-verified against two independent sources, and this session is offline. The
  domain referee's missing-citation findings remain open in `REVISION.md`.
* **`Theoria.md` §3.2's "19 perfect scores, only 14 actually reproduced the
  history"** is a strong hook and is *not* used: it is an upstream claim this
  paper cannot cross-verify offline. Filed as material for a browsing session.
* **§7.7 was not rewritten** to the blind round's numbers. That is a battery-section
  rewrite, not an intro rewrite, and it needs §7.8–§7.10 re-derived with it.
* **The workshop cut.** The draft is still ~26 700 words. §1 grew rather than
  shrank, because four of the acceptance-test items are things the old §1 failed to
  say at all.

## Gate

`python papers/phase1-workshop/verify_paper.py` — **FAIL (2/4), unchanged from
`master`**. A GENERATED passes; D NOSECRET passes. B PATHS fails on 3 broken and 2
elided path citations, all pre-existing on `master` (`out/dark/`,
`theory/theory.dsl`, `theory/generated_l2_scratch/`, two `.../MANIFEST.json`
ellipses). C FIGDATA fails on `fig1_concept_timeline.json`, also pre-existing.
**This run introduced no new failure and fixed none of the inherited ones** — both
belong to the figures item, not this one. Baseline captured by running the same
script on `master` before the rewrite.
