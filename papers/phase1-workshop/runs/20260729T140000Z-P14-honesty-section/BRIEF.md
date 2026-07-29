# P14-honesty-section — the brief, written before the section

**Item:** `P14-honesty-section` · **Agent:** RES-2 · **Branch:**
`agent/p14-honesty-section-res2` (the unsuffixed name already existed on an
unrelated tip) · **Base:** `b05e1c9`

## What the item asks for

A section of the paper — placed in the discussion or in threats-to-validity, the
writer's call — that reports the read-only adjudication survey as a **finding**,
not as an appendix. The item's own framing is the argument: the framework claims
*engines propose, the LLM adjudicates*; the survey measured whether that
adjudication surface has been quietly erased in the implementation, by tools'
**failure states being read as properties of the world** — and it found that the
error almost always points toward good news.

Required content, from the item:

1. **A named taxonomy of the failure families** — exit code taken as proof;
   default value taken as truth; crash taken as discovery; hitting a cap taken as
   exhaustion. One real in-repo example each, drawn from already-fixed or
   already-registered instances rather than freshly dug ones.
2. **The immune control.** A survey that reports only positives leaves a reader
   unable to judge how strict the criterion was. The ~45 *legitimate* exit-code
   readings and the gold-standard exemplar (`bench/ladder.py`, which records the
   cap into the artefact on purpose) must appear alongside, with the ratio.
3. **Which published numbers rest on a re-derivation** — `lp_potential`'s 29.2 %
   (the reviewer had to fetch the HiGHS status themselves) and the three
   `fd_unsolvable: true` rows in `runs/p13-fd-real/dividend.json` (bare exit code
   12, but the BFS stub independently agrees, so the conclusion currently holds
   while the method is unsound). **Write it fairly**: separate "the conclusion is
   wrong" from "the conclusion should not have been reached that way". At present
   everything is the second kind.
4. **The retraction stays in.** The survey withdrew one of its own paraphrases
   (the claimed false-negative at `p13:419` does not hold). A survey that retracts
   is more credible than one that does not.

**Monitor's addendum (2026-07-29), which changes the skeleton:**

* **The positive result must be written.** "A solver returned a plan, therefore
  the instance is solvable" **does not happen in this repository** — `fd_adapter`
  calls `validate_plan()` unconditionally on all three rungs, and the validator
  deliberately does not import the searcher. That is a structural guarantee
  rather than a promise, and it is one of the few hard pieces of evidence for the
  *engines propose, the LLM adjudicates* claim. Do not write only the pathology.
* **The real shape of the dual case** is "computed correctly, published, and then
  not used as a gate": `"admissible": True` is a literal while the real check sits
  in a sibling field of the same payload; `deadlock_carver` publishes a theorem
  and a report falsifying it side by side, with neither overriding the other.
* **The heaviest finding:** `engine-rig` has **no held-out validation anywhere**;
  `zero_space.verify` re-checks on the same trajectory it was fitted to.
  Therefore every place in the paper's body that says "verified" must, until E17
  lands, read **"self-consistent on the observed evidence"** — that is not
  cautious wording, it is what those cells currently mean.
* The fourth survey pass adds ~97 more legitimate usages to the immune control.

Adversarial subagent to check every sentence: can each number be pointed back to
a file and a line? Anything that cannot is **deleted, not softened**. Serves WP9
(body) and WP4 (the methodological control-arm argument).

## Blocker found at the opening ritual: the cited path does not exist

The item cites
`engine-rig/runs/20260729T000000Z-E11-engine-crosscheck-deep/SURVEY-*.md`.
**There are no `SURVEY-*.md` files there, and none anywhere in the repository**
(`find . -name "SURVEY*"` returns nothing on `master` at `b05e1c9`). That run
directory holds a *different* study: `CROSSCHECK.md` — six engines re-deriving
each other's outputs by a different engine's method — plus
`ADVERSARIAL-cegis.md`, `ADVERSARIAL-zero_space.md` and six `partials/`.

So the ~340 adjudication points / 48 unsafe survey, and the fourth pass of ~105
points / 8 unsafe, are either (a) under a different name in a run directory the
item mis-cites, (b) on an unmerged branch, or (c) in a mailbox or inbox report
rather than a run. **Locating them is step one and must not be guessed at**: the
whole item is a report about evidence discipline, so writing it from a
reconstruction rather than from the survey itself would be the exact failure it
describes.

`E11-engine-crosscheck-deep` is not obviously the wrong material — it is a
cross-check study with an explicit independence discipline and at least one
retracted claim, which matches items 2 and 4 above. It may be that the survey is
a *later* study that cites E11, or that the item's author conflated two runs. Do
not resolve this by assuming.

## Order of work

1. **Locate the survey.** Search merged and unmerged branches, `monitor/inbox/`,
   `monitor/mailbox/`, and every `*/runs/` directory for the counts 340 / 48 /
   105 / 8 / 45 / 97, for `bench/ladder.py`, and for the `p13:419` retraction.
   If it is on an unmerged branch, say which, and read it there.
2. **Digest it** into: the four families with one registered example each; the
   immune-control counts and ratio; the two published numbers that rest on a
   re-derivation; the retraction; the positive `fd_adapter` result; the dual
   "computed but not gating" cases; the no-held-out-validation finding.
3. **Decide placement.** §10 (threats to validity) versus a new discussion
   section. The item leaves it to the writer. The case for §10 is that it is
   already the paper's honesty section and the material is threats-shaped; the
   case for a standalone section is the item's own point — that this is an
   argument, not an appendix, and burying it in §10 does exactly what the item
   forbids.
4. **Write it**, every number carrying its path, per the paper's binding rule.
5. **Adversarial pass**, then the sweep the addendum requires: every "verified"
   in the body becomes "self-consistent on the observed evidence" unless E17 has
   landed for that cell. **Check E17's status first** — `E17-held-out-validation`
   is registered done on the board, so some cells may now be genuinely held-out
   and the blanket rewrite would be wrong. That check is a prerequisite, not a
   detail.

## Prior art in the same directory, to read before writing

`papers/phase1-workshop/runs/20260729T125500Z-P13-paper-intro-abstract/ADVERSARIAL_ROUND.md`
— the immediately preceding item. Its lesson applies directly here: two
independent reviewers overturned a headline that had been assembled from a
correct-looking summary rather than from the artefact. The specific trap was
attributing a whole result to the blind half of a study when a sighted follow-up
had done part of it. This item is a report *about* that class of error, so it will
be read unkindly if it commits one.
