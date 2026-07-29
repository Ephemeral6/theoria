# RUN_STATE — P11-battery-section-refresh

`MANIFEST.json` beside this file is canonical; this is the narrative.
`FINDINGS.md` carries the defect table with severities.

**Branch** `agent/p11-battery-section-refresh`, worktree
`.worktrees/p11-battery-section-refresh/`, base `8d42373` (master).
**Territory:** `papers/` only, plus one appended paragraph in `PARTNER_SYNC.md`.
Nothing outside `papers/phase1-workshop/` was written.

**Passive throughout:** zero API calls, zero model calls on any generation path,
zero network, zero game spend, zero sealed-pile contact. No artefact in `battery/`
was regenerated — every check reads the bytes as committed.

## What happened, in order

1. **Read the ground first, and found the work order standing on it had
   expired.** P11 asks for §7 to be rewritten because it is "marked stale". It is
   not: `OPEN_ITEMS.md:25` carries that item struck through and closed at P7, and
   `REVIEW_TRIAGE.md:133` records the exact moment the note stopped being true.
   The two rounds the order names — 区分力首跑 and 去冗余首跑 — are battery **v1**;
   the section already reports **v2**, which re-ran both on better material.

2. **Executed the clause that had not expired.** The order's second half — check
   whether the paper's *other* battery citations went stale — was live, and turned
   out to be the whole job. Three verifiers ran in parallel over disjoint slices
   with one instruction: check the paper against `battery/artifacts/*.json`, not
   against `battery/REPORT_V*.md`. A fourth built an independent fact sheet of the
   battery arm so that a shared misreading would have somewhere to show up.

3. **Twenty-one defects, thirteen inside §7.** Full table with severities in
   `FINDINGS.md`. All twenty-one fixed.

4. **Rebuilt and adversarially re-checked.** `python papers/phase1-workshop/assemble.py`
   → 12 sections. A fifth agent was then pointed at the diff with instructions to
   refute, not confirm, each corrected number from the artefact.

## The result in one line

**Six of the twenty-one defects are places where the paper faithfully reproduced a
sentence from `battery/REPORT_V*.md` that the battery's own artefacts contradict.**
§7.3 states the precedence rule — artefacts over reports — and the neighbouring
subsections did not apply it to the report's summary sentences. A rule stated in
one place and disregarded next door is worth less than no rule, because it invites
trust in the parts nobody checked.

Two of those six are the report being stale about the **code** rather than the
data: `REPORT_V2.md` still lists `Step.won`, `held_out_frame` and
`Beat.env_actions` as fields no metric reads, when its own v2.1 defences went on to
read all three; and it quotes a main-table low of 6 that rests on a demotion count
from before its own last round. The report is left unedited by policy — right for
a record, and exactly why a reader who takes its recommendations as current is one
round behind.

## The three worst, by consequence

* **`PROVENANCE.md:196` said "Six of seven economy metrics resolved to `no-data`".**
  Four did. The row exists to record that the paper *follows the artefacts over the
  report* on this very question, and it misreported the artefact while saying so.
* **"Nineteen of twenty **epistemic** metrics"** (§7.7) is arithmetically
  impossible — the epistemic family has fourteen members. The audit's scope is
  M1–M6 plus K1–K14, and the twentieth metric, the one an empty manual cannot
  reach, is M3. `REPORT_V2.md` says "nineteen of twenty metrics"; the paper added
  the word that broke it.
* **The pile-digest paragraph invented a third hash.** `arc-recon/data/piles.json`
  carries no CRLF, so its LF-normalised sha256 *is* its raw sha256 and there is no
  Windows-checkout value. Both real digests reproduce exactly. The paragraph exists
  to make a misleading description visible, and had a misleading description of its
  own in it.

## Verification

```
python papers/phase1-workshop/assemble.py        12 sections, ~23 968 words
```

`PAPER.md` is generated and was rebuilt from `sections/`; it was not hand-edited.
Determinism confirmed before the edits (a bare re-run left the tree clean).

Every corrected number was read from a named artefact and key, and every one was
put to an adversarial agent afterwards with instructions to break it.

## Caveats a reader should carry

* **This pass checked the paper against the artefacts, not the artefacts against
  reality.** Where an artefact is itself wrong, this pass agrees with it.
* **`battery/` has its own stale strings that are not this paper's to fix** and
  were reported upstream rather than edited: `METRICS.md` still titles itself
  "battery v1" and its K10 entry says the metric "stays in the main table" while
  the same file's tier column reads `reference`; `DECISIONS.md` has no entry for
  the four v2.1 defences although they moved a published value; and the round's
  test count is recorded three different ways (210 / 213 / 214).
* **One fix is outside the battery brief and is declared rather than folded in.**
  `sections/02_framework.md` said "the three acceptances" against the abstract's
  "four offline acceptances" — a contradiction that appeared when §6 (A3) landed.
  One word, inside this territory, corrected here.
* **The premise-expiry pattern is now three for three** in this territory
  (P9, and this item twice over). The board is slower than `OPEN_ITEMS.md`, and
  `OPEN_ITEMS.md` is slower than the artefacts. A work order that restates a
  finding rather than pointing at the file holding it will keep arriving stale.
