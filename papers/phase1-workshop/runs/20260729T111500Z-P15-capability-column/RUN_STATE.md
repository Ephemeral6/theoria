# RUN_STATE — P15-capability-column-has-no-signal

**Branch** `agent/p15-capability-column`, worktree `.worktrees/p15-capability-column/`,
base `20733a4f` on `agent/p7-p14-battery-section-blind-round` (pushed, unmerged;
both regenerate `PAPER.md`, which two branches cannot both do).
**Territory:** `papers/`. **Passive:** zero API, zero model calls, zero network,
$0.00, sealed pile untouched. Nothing outside `papers/phase1-workshop/` written.

`FINDINGS.md` beside this file carries the evidence task by task.

## What the item asked, and what was true

Four tasks. **Two of the four rested on premises that had expired or were wrong**,
and saying so is most of the delivery.

1. **"Change the main table's capability column to what it truly is."** There is no
   capability column. No table in the paper has one; the design's main table is
   `Theoria.md` §1.12's bet table and this paper does not reproduce it. And the
   framing "this quantity has no signal" is not what the source says: the sentence
   in `BUDGET_REPORT.md` §12.2 carries the qualifier **在 30 动作预算下** — *under
   a 30-action budget* — and its next clause prescribes raising the budget. The
   honest statement is that the quantity **was never purchased**: the first level of
   `g50t` costs 78 successful actions against an authorised 40 per level. Delivered
   as new **§7.10a**, with `envelope.json`'s `pooled_cv.levels_completed: null` as
   the machine-readable witness, plus a gap row in §7.10.
2. **"Clear the stale wording in the abstract."** Stale against v0.3: the subtitle
   selling transfer and the exam, "Eight results.", and the merged live run were
   all fixed already. Three live defects remained and are fixed — an orphan `$5.80`
   that existed only in the abstract, "a theory carried unchanged" where only the
   *manual* was carried, and a blind-round sentence crediting a sighted review with
   both of the last two metrics when one was retiered rather than defeated.
3. **"Verify P14's ruling reached the eight sites."** It did not, and should not
   have. P14 declined the blanket sweep, checked the eight sites, and **published
   the refusal in §10.6** rather than filing it. E17 has since landed for two of
   eight engine rows, so the blanket form was obsolete on its own terms. A
   confirmation, not an edit.
4. **The adversarial pass.** Ran, and found more in my own new text than in the
   pre-existing paper. See below.

## The refusal that is the finding

The item asked me to contrast the empty capability column against the bill shape,
"which has signal". **It does not, and writing it would have traded one overclaim
for another.** Cross-arm, E2's verdict is `no-data` with *zero* pairs. Within one
arm it separates by model tier — a capability gradient, which is exactly the
confound §7.8 registers as the thing to break before Phase 4. E5 is disqualified
twice over. And the paper currently disclaims cross-arm cost, so the sentence would
have introduced a claim §11 says this paper does not make. §7.10a states the
refusal and its reasons.

## What the adversarial pass cost me, and why that is the point

Eight defects, **six of them in text written today**, and five of those six
overclaim in the *modest* direction — understating an explanation, calling a
significant departure a null, refusing a contrast more broadly than the evidence
required. Three sentences were deleted outright rather than hedged, per the item's
instruction. The worst was mine: the first paragraph of §7.10a carried **six
quantities and no artefact path**, in the paper whose binding rule is that a number
without a path does not go in, and two of the six did not reproduce. `verify_paper.py`
passes 4/4 throughout, because it checks that cited paths *resolve* and cannot see
a claim that cites nothing.

**A modest overclaim survives review, because caution reads as diligence.** That is
what a hostile pass on one's own fresh prose is for, and it is why this run's
findings file records the failures in more detail than the fixes.

## Verification

```
python papers/phase1-workshop/assemble.py      13 sections
python papers/phase1-workshop/verify_paper.py  PASS (4/4)
```

`PAPER.md` is generated and was rebuilt from `sections/`, never hand-edited.

## Reported, not acted on

* `sections/05_a2.md`'s "The isomorphism is machine-checked, clause by clause" is
  the strongest verb in the paper attached to a non-proof object — one row is a
  Lean proof, the others are artefact comparisons. Every row names its artefact so
  the sentence is true; a later pass should rule on it deliberately rather than
  inherit it.
* `verify_paper.py` cannot detect an uncited quantity, only a broken citation. The
  defect class that bit this run is invisible to the paper's own gate.
