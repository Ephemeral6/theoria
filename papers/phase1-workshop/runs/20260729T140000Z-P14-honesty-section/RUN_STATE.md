# P14-honesty-section — what was done, and the three things it refused to write

**Item:** `P14-honesty-section` · **Agent:** RES-2 · **Branch:**
`agent/p14-honesty-section-res2` · **Base:** `b05e1c9`, merged to `32f078c`
before writing · **Deliverable:** `papers/phase1-workshop/sections/10_adjudication.md`,
a new §10 of the workshop draft.

## The shape of the delivery

The item asked for a section reporting the read-only adjudication census as a
*finding* rather than an appendix: a named taxonomy with registered examples, an
immune control with its ratio, the published numbers that rest on a
re-derivation, the census's own retraction, the positive `fd_adapter` result,
the "computed but not gating" duals, and the absence of held-out validation.
All seven are in the section, in that order, as §10.1–§10.7.

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

## Three things the item asked for that are not in the section

Each was checked before being refused, and the refusal is itself written into
the section rather than left as a silent omission.

1. **`340 points / 48 unsafe` is not published.** The four passes used four
   different rulers — two write a criterion down and the two differ, two state
   none — so the sum is across incommensurable scales, and 48 of the 56 unsafe
   judgements were made under an unstated or different criterion. Separately the
   largest pass names 76 sites against a stated scan surface of 60. The section
   publishes **85 legitimate / 56 unsafe**, which is what enumerates, and reports
   the discrepancy as a finding — the census fails the very rule
   `SURVEY-empty-as-negative.md:87-92` proposes for everyone else.
2. **"~45 legitimate exit-code readings" and "~97 more" are not published.** 45
   appears in no survey; the enumerable figure is 64. 97 is `105 − 8`, arithmetic
   residue; that pass names 15 sites.
3. **The blanket `verified` → `self-consistent on the observed evidence` sweep
   was not run.** The addendum asks for it across the body. `PAPER.md` contains
   **seven** occurrences of the word — one about a third party's model, three
   naming a certificate field on lines whose point is that the field is not
   trusted, one about the pile digest, and two in the related-work section, one
   of which is the sentence *"no claim is made to have verified any engine"*.
   已验证 occurs zero times. A find-and-replace would have corrupted correct
   sentences and changed nothing that needed changing. The finding is reported in
   §10.6 instead, together with what E17 did and did not change.

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

`python papers/phase1-workshop/verify_paper.py`

* **A GENERATED — pass.** `PAPER.md` is `assemble.py`'s output from the renamed
  `sections/`.
* **D NOSECRET — pass.**
* **B PATHS — fail, pre-existing.** Three broken citations (`out/dark/` and
  `theory/theory.dsl` in `03_a0.md`, `theory/generated_l2_scratch/` in
  `06_a3_transfer.md`) and two elided ones in `09_preflight.md`. Measured with
  the new section temporarily removed: identical output, 176 citations instead of
  197. **The new section adds 21 path citations and zero broken ones.**
* **C FIGDATA — fail, pre-existing.** `fig1_concept_timeline.json` differs on
  rerun. Not touched by this item.

B and C are being diagnosed separately; they are reported here rather than
described as green, because a section about reading failure states honestly
cannot ship under a summary that rounds two failures away.
