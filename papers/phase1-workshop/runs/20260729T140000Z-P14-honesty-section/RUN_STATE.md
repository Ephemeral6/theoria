# P14-honesty-section — what was done, and the three things it refused to write

**Item:** `P14-honesty-section` · **Agent:** RES-2 · **Branch:**
`agent/p14-honesty-section-res2` · **Base:** `b05e1c9`, merged to `32f078c`
before writing · **Deliverable:** `papers/phase1-workshop/sections/10_adjudication.md`,
a new §10 of the workshop draft.

## The shape of the delivery

The item asked for a section reporting the read-only adjudication census as a
*finding* rather than an appendix: a named taxonomy with registered examples, an
immune control, the published numbers that rest on a re-derivation, the census's
own retraction, the positive `fd_adapter` result, the "computed but not gating"
duals, and the absence of held-out validation. All seven are in the section, in
that order, as §10.1–§10.7. The one part of the commission that is refused is the
**ratio** the item asked the immune control to carry: after the adversarial round
there is no defensible denominator, and §10.1 says why at length.

Placement was left to the writer. It is a standalone §10 in front of the
limitations rather than a subsection of them, on the item's own argument: the
census measures the mechanism §2.2 claims, so it is a result. The renumber that
follows is documented in `SECTION_RENUMBER.md` beside this file.

## Order of work

1. **Located the evidence.** The item cites
   `engine-rig/runs/20260729T000000Z-E11-engine-crosscheck-deep/SURVEY-*.md`.
   No such files exist in the repository. They were found as **untracked files
   in a sibling worktree on an unpushed branch** — on no ref, local or remote.
   Copied verbatim into `inputs-verbatim/` with sha256 in `MANIFEST.json`;
   re-compared against the originals at 14:45Z and still byte-identical, and the
   originals are still untracked. This is reported in the paper as §10.7, not
   buried here.
2. **Digested them against the tree** — `evidence-survey-located.md`, every claim
   carrying a path and a line, and eight places where the census reports are
   themselves wrong listed in an appendix.
3. **Re-verified at the writing commit.** The digest was made at `b05e1c9`;
   master moved. An independent pass re-read every load-bearing claim at
   `32f078c` — `reverification-at-32f078c.md`. Nothing was overturned. Two
   *non-changes* mattered enough to reach the text: `v19` is still unmerged, so
   `worldgen/core/truth.py:279` still defaults an uncheckable invariant to
   holding while the board records the fix as done; and `dividend.json` still
   carries the defective line's output.
4. **Wrote the section**, then renumbered §10 → §11 and §11 → §12 with the file
   renames the P6 precedent requires.
5. **Adversarial review** — two independent reviewers, one line-checking every
   number against the tree with instructions to refute, one reading for goal
   drift, overclaim and whether the section commits the error it describes.

## The adversarial round overturned the section's headline

Two independent reviewers — one refuting numbers against the tree, one reading
for drift and overclaim — converged on the same defect: the enumerated
**85 / 56** the draft published in place of the census's 340 / 48 **is the same
error one level down**. The 85 omits the largest pass's positives; the 56 is the
sum of the four summary lines the section had just impeached; and three sites
appear on *both* sides of the ledger because the passes disagree with each other
about them. Twenty findings in all, and the section was rebuilt around the
conclusion that **no aggregate is available at all**. Full record, with every
correction and its evidence: `ADVERSARIAL_ROUND.md` beside this file.

The three largest beyond the aggregate: the claim that the error always runs
toward good news is refuted by a 24-row group in the census's own largest pass
that runs the other way; the `a0-spike` crash repair does not reach the published
artefact, which this paper cites in §3.5, so the section now says which of those
numbers are unaffected and why; and the draft's independence claim for the census
was cut, because the surveying lane wrote most of the repairs it reports.

## Three things the item asked for that are not in the section

Each was checked before being refused, and the refusal is itself written into
the section rather than left as a silent omission.

1. **`340 points / 48 unsafe` is not published — and neither is any
   replacement.** The four passes used four different rulers; two of them state
   none at all, and 53 of the 56 unsafe judgements were made under a criterion
   that is unstated or different from the one they are quoted under. The passes'
   own arithmetic does not close: one states ~60 points and names over seventy,
   another states 37 unsafe and enumerates 40 rows. And the passes overlap and
   disagree — three sites are graded safe by one pass and unsafe by another. The
   section therefore publishes **per-pass figures and no aggregate**, labelled as
   each pass's own summary line. The draft's enumerated 85 / 56 was itself
   refused by the adversarial round, for the same reasons.
2. **"~45 legitimate exit-code readings" and "~97 more" are not published.** 45
   appears in no survey; the solver-status pass enumerates 51 table rows plus 11
   backticked paths, and the two accountings do not reconcile, so no total is
   given for it either. 97 is `105 − 8`, arithmetic residue; that pass names 15
   sites, 7 of which it files under a heading warning they are the category most
   easily misread as safe.
3. **The blanket `verified` → `self-consistent on the observed evidence` sweep
   was not run.** The addendum asks for it across the body, conditioned on
   held-out validation not having landed; it has landed, for two of eight rows.
   `PAPER.md` carries **eight** occurrences of the word outside this section —
   one about a third party's model, three naming a certificate field on lines
   whose point is that the field is *not* trusted, one about the pile digest, and
   three in the related-work section, one of which is the sentence *"no claim is
   made to have verified any engine"*. 已验证 occurs exactly once in the paper:
   in the sentence of §10.6 that says it occurs nowhere else. A find-and-replace
   would have corrupted correct sentences and changed nothing that needed
   changing. Both counts are re-checked against the assembled `PAPER.md` and are
   the checkable kind: `ADVERSARIAL_ROUND.md` records that the draft got them
   wrong (seven and two) by inheriting a dropped occurrence from an earlier
   audit.

## What is still open, and not mine to close

* **The census reports are on no git ref.** They back six work items and this
  section. RES-2 does not write outside `papers/`, so the fix — `git add` and
  push the originals in `engine-rig/runs/20260729T000000Z-E11-engine-crosscheck-deep/`
  — needs someone holding that territory. Requested on the bus at 13:55Z and
  again at 15:20Z. Until then `inputs-verbatim/` is the only copy in version
  control, and it is explicitly **not** canonical (`inputs-verbatim/PROVENANCE.md`).
* **`worldgen/core/truth.py:279`** is unrepaired on the mainline while the board
  records `V19` as done. Reported in §10.2; the repair is engine/worldgen
  territory.
* **`zero_space`'s `scope_exhaustive` bit is still absent from the published
  candidate stream**, blocked by the release manifest's sha256 pin rather than
  by disagreement. Reported in §10.4 as such.

## Gate

`python papers/phase1-workshop/verify_paper.py` → **PASS (4/4)**.

It was **not** passing on the incoming tree. B PATHS and C FIGDATA were both
red before this branch touched anything — measured by removing the new section
and re-running, which reproduced the failures with 176 path citations instead of
197. The new section itself added 21 path citations and zero broken ones. The
pre-existing failures were then repaired rather than reported around, in a
separate commit (`9bc2775`):

* **B, three broken citations.** All three referents exist and all three were
  missing an arm prefix the paper writes correctly everywhere else:
  `theory/theory.dsl` → `cold-start-a0/theory/theory.dsl`;
  `theory/generated_l2_scratch/` → `cold-start-a3/theory/generated_l2_scratch/`
  (copied verbatim out of `score_vs_truth.json`'s own arm-relative field);
  and `(and out/dark/)` → the dark plate's full path.
* **B, two elided citations.** `09_preflight.md` cited `.../MANIFEST.json` and
  `.../run.json`; both live in `theoria-arm/runs/preflight-20260728T012057Z/`
  and are now written out.
* **One gate edit, disclosed.** Naming the dark plate in full turns `BROKEN`
  into `AMBIGUOUS`, because `figures/` exists both at the repository root and
  beside `PAPER.md`. `figures/out/dark/fig06_concept_timeline.svg` was added to
  `verify_paper.py`'s `ADJUDICATED_AMBIGUITY`. That applies the existing
  `figures/PARITY.md` ruling to a file the list omitted — its own light twin is
  one line above it — rather than creating a new exemption. The alternative was
  to unbacktick the token and cite nothing, which is worse for a reader. It is
  called out here and in the commit message because editing a gate to make it
  pass is the exact move this paper's §10 is about, and it should be checkable
  rather than quiet.
* **C was staleness, not nondeterminism.** Two regenerations agree
  byte-for-byte; the committed `fig1_concept_timeline.json` differed from both
  by a pure append of `E-06`…`E-09` to `expressivity_ledger`, rows added to
  `cold-start-a0/THEORIZE_LOG.md` after the payload was last written.
  Regenerated. **No number in `PAPER.md` moves**: no section cites this figure
  (it is the parity witness), `figures/check_figure_parity.py` reads three keys
  and none of them changed, and the two prose mentions of "five gaps" are
  time-scoped to A0's run and remain true.

One finding from that diagnosis is out of this item's scope and is filed rather
than fixed: `sections/04_a1.md` heads a subsection "What A1 did not settle:
E-06, an open problem", while `cold-start-a0/THEORIZE_LOG.md` now marks E-06
discharged and `theory-compiler/STATUS.md` books it both ways on two different
lines. That is a live contradiction between the paper and the ledger it cites.
