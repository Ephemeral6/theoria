# The adversarial round on §10, and the finding that rebuilt it

Two reviewers were run against the first draft, independently and with different
instructions: one line-checking every number against the tree with a standing
order to **refute**, one reading for goal drift, overclaim, and whether a section
about intellectual honesty had become a credibility claim. They did not see each
other's work.

**They converged on the same structural defect, from opposite directions**, and
it was the sentence the draft was proudest of.

## The finding that rebuilt the section

The draft refused the census's headline (340 points, 48 unsafe) on the ground
that it summed four incommensurable rulers, and replaced it with an enumerated
**85 legitimate / 56 unsafe**, under the banner *what can be published is what
can be counted*.

Both reviewers found that the replacement is the same error:

* **85 omits the largest pass's positives entirely.** It is `64 + 15 + 6` over
  three passes; `SURVEY-environment-as-semantics.md:138-230` names 28 further
  exemplars and grades 20 more cap sites, and none of them is in the total.
* **56 is the sum of the four passes' own summary lines** — `3 + 8 + 37 + 8` —
  i.e. exactly the class of object the section had just impeached. It also does
  not survive counting: the environment pass states 37 and its three unsafe
  tables enumerate 40 rows.
* **The passes overlap, and where they overlap they disagree.**
  `lp_potential/potential.py:170-171` is graded 安全 at
  `SURVEY-solver-status.md:308` and unsafe at
  `SURVEY-environment-as-semantics.md:77`; `probe_frontier/reach.py:94-99` is
  safe at `:290` and unsafe at `:80`; `cegis_miner/miner.py:323` is safe at
  `:339` and mismeasured at `:131`. Any sum counts three sites on **both sides of
  the ledger**.
* The draft's "48 of the 56" was itself the discarded headline reused with the
  wrong membership: unstated-or-different criteria cover 37 + 8 + 8 = **53**.
* "the largest pass" named two different files four lines apart.

**The section now publishes no aggregate at all**, gives per-pass figures
labelled as each pass's own summary line, and states the four reasons no total is
available. That is a weaker claim than the draft made and a stronger section:
the census cannot say what fraction of this repository's adjudication points are
unsafe, and saying so is the finding.

## Everything else that was corrected

| # | Draft said | Correction |
|---|---|---|
| 1 | "in all four families the defaulting runs one way… almost always toward good news" | **Refuted by the largest survey it cites.** `SURVEY-environment-as-semantics.md:37-64` is a 24-row group for the *opposite* direction, and `:92-107` marks a fourth group conservative. Narrowed to the four exhibited families, with the counter-group reported. |
| 2 | the `a0-spike` crash repair, stated as complete | **`a0-spike/artifacts/a0_report.json` predates the fix**, carries twelve `blocked_*_{1,2,3}` rules — the fallback path's output — and no `reason` field. Whether that disjunction is a verdict about the world or an unrecorded crash cannot be told from the artefact. §3.5 of this paper cites that arm, so the section now says which of its numbers are unaffected (all of the quoted ones: they measure the adjudicated theory, not the miner) and which claim is not (the provenance of the guard shape). |
| 3 | "the repository calls Fast Downward only under `astar(blind())`" | A per-tool fact generalised to the repository. `bench/ladder.py` runs `lmcut`, `ipdb` and a satisficing alias; the adapter's default heuristic is `lmcut`. Scoped to the calling tool. |
| 4 | "all 1408 certificates are emitted… into the shared candidate stream" | A **counterfactual** the held-out harness measured, not an emission. No such row is in `candidates.jsonl`. Changed to "would be emitted", with the distinction stated. |
| 5 | 13.1 % held-out hit rate, unqualified | The table calls it a dial: 35.3 % under a one-fifth split, 2.0 % leaving two operations out, and 66.7 % / 100.0 % on a cyclic rebuild — the magnitude is a fact about the corpus. Added as a fifth qualification. |
| 6 | "seven occurrences of *verified*", "twice in §12" | **Eight** and **three**. The earlier audit counted 8; the re-verification dropped one ("cross-verified") without saying so and the draft inherited the drop. All eight are now enumerated. |
| 7 | "已验证 does not occur at all" | It occurs once — in that sentence. Rewritten to "nowhere in the body outside this paragraph", which is checkable and true. |
| 8 | "the eight places the census reports are themselves wrong" | Of the eight appendix rows, two are census errors; four are errors of the *work item* that commissioned this section; two are downstream. Decomposed. |
| 9 | "a search of every local and remote head returns nothing" | Self-contradicting two paragraphs later, since this branch commits the copies. Narrowed to "the originals are on no ref". |
| 10 | "13 of 35 built worlds" attributed to the census | The census states 13 and **no denominator**. The 35 is re-derived here from `worldgen/out/worlds/`, and the section now says so. |
| 11 | "64 in the solver-status pass (51 rows plus 13 CI paths)" | Two of the 13 are identifiers, not paths. 51 rows plus **11** paths over 10 files, and the two accountings do not reconcile to 64, so the total is dropped. |
| 12 | "76 named sites against a stated surface of 60" | Not reproducible under either counting rule (74 or 77). Replaced with the claim that *is* checkable: the legitimate list alone is of the same order as the whole stated surface. |
| 13 | the 7 verified-but-not-independent sites counted as immune controls | The census heads that category *the one most easily misread as safe*, and two of the seven are defects this section reports elsewhere. Excluded, and the reason stated. |
| 14 | "85 named sites read a failure signal correctly" | Two of the four passes grade *success* signals and empty results, not failure signals. Gloss dropped. |
| 15 | "close to impossible to trigger" | The source is harder: `ENGINE_TABLE.md` says the check **cannot fail by construction**. The draft had softened a proof into an estimate. |
| 16 | "corrupting several sentences" | "Several" in the one place the section holds the exact number. Rewritten. |
| 17 | "the cleanest instance in the repository" | A superlative over a population nobody enumerated. Narrowed to "the clearest case the census found". |
| 18 | "Two instances, both now closed, one still open" over three bullets | Miscount, in a section about counting. Fixed. |
| 19 | "run by a reviewer inside the repository, not by the authors of the code" | **Unsupportable from the tree and cut against by the board**: the surveying lane wrote most of the repairs it reports and filed the work items. Replaced with the deflated form the paper uses elsewhere, and promoted into §10.7 as a limit. |
| 20 | "Two of the four passes found the division structurally enforced" | Which two is never said, and only one structural positive is exhibited. Replaced with the concrete claim. |

## Tone and framing corrections

The second reviewer's central charge was that a section about honesty can become
a credibility claim, and named six instances. Cut or deflated: "not by the
authors of the code it examined" (now a stated limit, not a credential); "None
was dug up for the occasion"; "against its own interest"; "each signed by a
different party"; "because its most useful findings are not concessions"; "The
finding belongs in a section, which is where it is"; and the near-miss framing of
`git clean`. What remains states the facts and lets them stand.

## Two structural gaps, both closed

The section was an orphan: §1.5's contribution list did not mention it and §11
never referred to it, while §11.3 discussed `lp_potential`'s incompleteness, the
BFS-stub provenance and a compiler-manufactured false UNSAT — the section's own
subject matter — with no link in either direction. Added: one paragraph in §1.6
announcing §10 as neither a contribution nor a limitation, and two
cross-references from §11.3.

## Three questions a hostile reviewer would ask, now answered in §10.7

1. *What would have falsified §2.2, and what is the base rate?* Nothing was
   declared in advance, and there is no base rate. Stated as a bound.
2. *Who ran this?* Another working session of the same model, in the same
   repository, which also wrote the repairs. Stated as a bound.
3. *Which numbers in the paper are affected?* §3.5's `a0-spike` figures are the
   only paper numbers downstream of a surveyed defect; the section now says
   exactly which of them are unaffected and why, and which claim is not.

## Gate

`python papers/phase1-workshop/verify_paper.py` → **PASS (4/4)** after the
rewrite. Two of the section's self-referential claims are machine-checkable and
were re-checked against the assembled `PAPER.md`: "verified" occurs 8 times
outside §10, and 已验证 occurs exactly once in the whole paper, in the sentence
that says so.
