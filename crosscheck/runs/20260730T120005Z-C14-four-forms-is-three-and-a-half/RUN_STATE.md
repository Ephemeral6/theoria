# C14 — the fourth form, measured. Run narrative.

Worker W-1710, item `C14-four-forms-is-three-and-a-half`, territory `crosscheck`,
branch `agent/c14-four-forms-is-three-and-a-half`, base `cc7e414e`.
Zero API calls, zero sealed-pile contact, $0.00. `theory-compiler/` byte-untouched.

The machine record is `MANIFEST.json`; the numbers are `out/census.json`. This
file is the narrative, and it exists mainly to record two things a manifest cannot:
why the relayed work was trusted, and which of my own claims got broken.

## What was found on arrival

The worktree already contained an uncommitted `crosscheck/` from **W-1701** — a
census tool and a full run at base `1a86d67d`. The board warned this could be a
relay or could be rubbish, and said to justify trusting it before using it.

**It was kept, and here is the justification.** The tool was re-run unchanged on
`cc7e414e`, 56 commits later. It reproduced exactly: summary block identical field
for field, all 59 per-file records identical, and all 34 generated `*.domain.pddl`
byte-identical. The instrument is deterministic and the corpus had not moved under
it.

Reproduction alone is not enough — a tool can reproduce a wrong answer — so the
figure went through four independent checks before being published (below). W-1701's
run is committed alongside mine rather than deleted, because "the same tool gave
the same answer from two different base commits" is itself evidence.

## The number

**Of the 303 actions the DSL expresses, 0 compile — via
`theory_compiler.generators.gen_pddl` — to well-formed, semantically non-empty
PDDL.** Per-action list: `out/census.md` (303 rows, 0 GOOD, 18 REFUSED). That scope
qualifier was added late and is load-bearing; see "Things I got wrong".

## How it was attacked

Four parallel work packages, each with its own context, then a fifth adversarial
pass over my own conclusions document.

1. **Classifier attack** — try to make the instrument manufacture the zero. All six
   parsing routines were re-checked against an independent balanced-paren
   s-expression reader over all 34 domains (zero disagreements), mutation-tested
   with CRLF and re-indentation (zero verdict changes), and hand-compared on 10
   actions across 6 source DSLs (zero disagreements). Every defect family traces to
   a named line in `gen_pddl.py`. **Verdict: sound.**
2. **Denominator attack** — find the slicing that makes the generator look better.
   Thirteen slicings, including the flattering ones. **Good is 0 at every one; the
   maximum GOOD over any single file in the corpus is 0.** Found one real defect in
   the corpus definition, now fixed (below).
3. **Independent planner** — Fast Downward 24.06+'s translator, which has never
   heard of the generator. Accepted 7 of 34 domains, **and all 21 actions in those
   7 are doubly empty**. Acceptance is anti-correlated with meaning.
4. **Root cause** — read `gen_pddl.py` end to end against the other three
   backends. Backend gap, not a grammar limit, on every count except three declared
   refusals.
5. **Adversarial review of my own conclusions** before delivery.

## Things I got wrong, and fixed

**The headline was scoped wrong, and this is the one that mattered.** The delivered
document first said the four-forms claim was *false*, on the strength of 0 of 303.
The repository has a **second PDDL backend** — `cold-start-a0/compile/gen_pddl_a0.py`
— with 25 committed domains, 263 actions, **263 of them GOOD under this census's own
classifier**, accepted rc 0 by the same Fast Downward build, and it is the generator
behind every planning number in the paper. I verified all of that first-hand before
changing a word, because a reviewer's claim is not evidence either.

Had it shipped as written, an author would have retracted a claim that is defensible
for the arms the paper reports planning results on. The corrected finding is narrower
and still serious, and is in `FOUR_FORMS_TRUTH.md` §0 and `out/TWO_BACKENDS.md`.

**Why the measurement could not see it.** The census's population is *every `.dsl`,
as `gen_pddl`'s own front end sees it* — a corpus defined by **input** files. Backend
B leaves no trace there, because it is a different **output** path over the same
inputs. And the instrument had **no positive control**: it was never shown a
known-good domain and asked to score it GOOD. B is exactly that control, and it was
found by an adversarial review of the finished document, not by the measurement.
Both holes are now closed in the gate.

**I over-claimed the repair distance.** I wrote that the 94 naming-only actions
"become candidates for GOOD in one change". False: `gen_pddl` also makes a
`:parameters` entry out of every direction constant, typed `object`, and no object
of that type is ever declared — so the parameter cannot bind and the action
vanishes at grounding. Measured with only the naming defect patched: **0 ground
actions with the direction parameter, 144 without**. Corrected in
`out/REPAIR_DISTANCE.md` under a `CORRECTION` heading rather than by rewriting the
original sentence.

The general lesson outlived the correction and is now the most important caveat in
the deliverable: **the census bar is too lenient, not too strict.** An action can
satisfy all four criteria and still ground to nothing, or carry an inverted
precondition (`GuardPredicate.negated` is never read by this backend while the
other three honour it), or let a teleport land anywhere. `0 of 303` is a **ceiling
on correctness, not a floor on brokenness**.

**Three more, all caught by the same adversarial pass, all verified before changing:**

* "94 naming-only actions, structurally correct" → **37 of 285 (13 %)**. The 57
  wrongly folded in carry an unbound `?dest`; declaring it yields a *valid* action
  that teleports the cart anywhere, and the `shove-*` siblings move the cart instead
  of the block. For those 57 the real defect is the missing event model.
* "across both live-arm domains: 11 actions" → **9** (3 + 6).
* "only rises when you stop requiring an effect" → **six** relaxations raise it
  without touching the effect criterion.
* `D-TC-031` misattributed: lines 575-578 sit inside **D-TC-030** (heading 555);
  D-TC-031 is at 597 and is the decision that books the `gen_pddl` shortfall.

**Both repair estimates erred in the same direction** — each made the generator look
closer to working than it is. That is not two slips; it is one biased method, taking
a defect *label* as a proxy for how broken an action is when the label only records
which validity rule was tripped. Recorded because errors that land consistently on
one side are a method problem, not luck.

**I nearly published a citation I had not checked properly.** A `sed` truncated at
400 characters made `PARTNER_SYNC.md:923` look like it did not contain the quote I
attributed to it. It does — at character offset 601 of a 1231-character line. The
citation now leads with the paragraph heading, because P-P22 already recorded that
line anchors into append-only logs rot at commit.

## Things fixed in this territory

**The corpus depended on which checkout you ran from.** `SKIP_DIRS` excluded
`.worktrees` but not the agent harness's `.claude/worktrees/`, so the census saw
59 DSL files from a worktree and **237** from the main checkout — four nested
checkouts each carrying a full copy. A population that changes with the caller's
cwd is not a measurement. Fixed; both roots now yield 59; `c14_verify.py` pins it
by recomputing the corpus against the main checkout and failing on any difference.
Headline numbers unchanged.

**LF pinned.** `core.autocrlf=true` here, and `verify.sh` sha256-compares committed
PDDL against a fresh re-run, so without `crosscheck/.gitattributes` the gate would
report all 34 domains changed on a clean clone while nothing was wrong.

## Gaps left open, honestly

* **One PDDL backend was measured, not "the PDDL form".** The other one works.
* **Only the PDDL form was measured.** Nothing here supports or refuses any claim
  about Lean, Python or Markdown. The deliverable explicitly forbids the natural
  repair "three of four forms are verified" for exactly this reason.
* **The two backends were never cross-checked against each other**, by this item or
  by anything else in the repository. They emit incompatible encodings of the same
  manual and no test compares them. Worth its own item; not attempted here.
* **The census under-counts slightly.** Two `exam/handover_bundles` manuals with 5
  real rules are rejected by `parse_theory` for a missing `semantics:` section, so
  a wider reading of "expressible" gives 313 rather than 303. Left at 303 because
  the documented population is what `gen_pddl`'s own front end sees — stated rather
  than silently taken. Numerator 0 either way.
* **303 is a duplicate-inflated ceiling**: 61 of 303 actions (20%) are
  byte-identical copies. Deduplicated figures (242 by source bytes, 202 by
  generated-domain bytes) are published alongside it.
* **No fix was attempted and none may be from here.** `ROOT_CAUSE.md`'s eight-item
  fix list is a registration for the owning track, not work in progress.

## Verify

```bash
bash crosscheck/verify.sh
```

Re-derives the census and diffs it against the committed record: headline numbers,
all 59 per-file records, all generated PDDL byte-for-byte, and corpus
cwd-independence. Reports `SKIP` — never `pass` — for the Fast Downward tier when
no local build exists, because "no planner ran" and "every domain was rejected"
render identically if you are careless.
