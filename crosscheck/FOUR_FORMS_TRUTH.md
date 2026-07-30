# The current truth value of the "four co-derived forms" claim

**Status: FALSE as written, today, in the abstract and in contribution 1.**
Owner of this finding: `crosscheck` (W-1710, item C14). For RES-2.
Evidence: `crosscheck/runs/20260730T120005Z-C14-four-forms-is-three-and-a-half/`.
Re-derive with `bash crosscheck/verify.sh`.

`theory-compiler/` is the other track's and was not modified. This document
registers a gap; it does not repair one.

---

## 1. The number

Of the **303 actions** the DSL expresses across the repository's 59 `.dsl` files,
**0** compile to PDDL that is both well-formed and non-empty.

| | |
|---|---|
| actions owed a PDDL form | **303** |
| semantically non-empty **and** well-formed | **0** |
| fraction good | **0.0 %** |

An action counts as good only if its `:precondition` has at least one literal, its
`:effect` has at least one literal, every `?var` it uses is in its `:parameters`,
and every predicate it uses is declared. Each criterion is a validity or
non-vacuity requirement, not a style preference.

**The zero is not an artefact of the denominator.** It holds under all thirteen
slicings tried, including every one chosen to flatter the generator:

| slicing | actions | good |
|---|---|---|
| all `.dsl` in repo (headline) | 303 | **0** |
| refusals folded out (the flattering slice) | 285 | **0** |
| deduplicated by DSL source bytes | 242 | **0** |
| deduplicated by generated-domain bytes | 202 | **0** |
| canonical hand-authored theories only | 165 | **0** |
| narrowest defensible (one latest file per world) | 115 | **0** |
| domains an independent planner accepted | 21 | **0** |
| **best single file in the corpus** | — | **0** |

**The zero is not an artefact of the bar either.** Dropping the one contested
criterion — "an empty precondition is a defect", when an always-applicable action
is legal PDDL — moves the headline from 0 to **0**: not one action in the corpus
has an empty precondition as its *only* defect. Of the sixteen possible
relaxations of the four criteria, the count stays 0 under the two that are
arguable, and only rises when you stop requiring an effect at all.

## 2. An independent planner agrees, and the way it agrees is the finding

Fast Downward 24.06+'s translator — which has never heard of `gen_pddl` — accepted
**7 of the 34** generated domains. That number must never be reported as partial
success. **All 21 actions inside those 7 accepted domains are simultaneously
empty-precondition and empty-effect.** FD accepts them precisely because they
assert nothing; every domain that tries to say something is rejected.

| FD verdict | domains | actions | of which good |
|---|---|---|---|
| accepted (rc 0) | 7 | 21 | **0** — all 21 doubly empty |
| rejected (rc 31) / crashed (rc 1) | 27 | 264 | **0** |

FD's acceptance is anti-correlated with meaning. It sorts the generator's output
into *malformed* and *vacuous*, and there is no third bin.

Four problems do not merely fail — they **crash** FD's translator with
`TypeError: unhashable type: 'list'`, on a generated goal of `(= (and) 1)`: the
generator emitted an equality between the logical connective `and` and the integer
1. Separately, **21 of the 34** generated problems carry a placeholder `(and)`
goal, so on the problem side too, most of the planning tasks have nothing to plan
toward.

Full logs and FD's verbatim words: `runs/…/out/INDEPENDENT_PLANNER.md`.

## 3. How deep the gap is — state this too, or you overstate it

"0 of 303" alone reads as *"the PDDL backend is an unimplemented stub"*, and that
is not what the corpus shows. Bucketed by repair distance (285 compiled actions):

| bucket | actions | depth |
|---|---|---|
| **naming-only** — precondition and effect both non-empty, fails on an undeclared name | **94** | shallow: **8 identifiers** |
| no effect — `:effect (and (and))` placeholder | 152 | deep: no event model |
| vacuous — both empty | 38 | deep |
| no precondition only | 1 | shallow |

The eight identifiers are three predicates the generator *emits* but never
*declares* — `adjacent-above`/`adjacent-below`/`boundary-above`, against a
hard-coded declaration block that says `adjacent-up`/`adjacent-down`/`boundary-up`
— and five variables used in a body but absent from `:parameters` (`?dest` in 50
actions, `?block-pos`, `?block`, `?spent`, `?spent-pos`).

A third of the corpus therefore compiles to *structurally correct* PDDL that is
then invalidated by a vocabulary mismatch inside one generator. Example, verbatim:
`push-up` in `ablation-arm/theory/a0_base.dsl` has three precondition literals and
four effect literals with correct add/delete structure — a real push action — and
is invalid solely because the domain declares `adjacent-up` and the action says
`adjacent-above`.

**This is not progress and must not be reported as any.** Nearly-valid PDDL is
invalid PDDL; the planner rejects the file. The count today is 0. But a reader
told only "0 of 303" will conclude something false about *why*, and the fix
estimate that follows from it will be wrong by an order of magnitude.

**Nor is "shallow" the same as "cheap".** Reconciling the eight identifiers is
*not* sufficient to make those 94 work. A fifth defect, invisible to all four of
the census's criteria, kills them anyway: `gen_pddl` makes a `:parameters` entry
out of every direction constant, typed `object`, and no object of that type is
ever declared — so the parameter cannot bind. Measured with only the naming defect
patched, against the track's own grounder: **0 ground actions with the direction
parameter, 144 without it.** The naming fix alone buys a domain that parses and
grounds to nothing.

### The bar is too lenient, not too strict

This is the single most important methodological caveat in this document. The four
criteria test well-formedness and non-vacuity. An action can satisfy all four and
still be dead or wrong: it can ground to zero actions (above); it can carry an
**inverted** precondition, because `GuardPredicate.negated` is never read by this
backend while the other three honour it; and a declared landmark becomes a free
cell parameter, so a teleport may land anywhere.

So **`0 of 303` is a ceiling on correctness, not a floor on brokenness.** A future
census that fixes the four classes and reports a positive number has not thereby
shown the form works. Full diagnosis: `runs/…/out/ROOT_CAUSE.md`.

## 4. The handover packages ship no planning form at all

Both published packages, extension by extension:

| pack | .dsl | .json | .lean | .md | .py | **.pddl** |
|---|---|---|---|---|---|---|
| `theory-compiler/handover_packages/a0-cart` | 2 | 3 | 2 | 8 | 2 | **0** |
| `theory-compiler/handover_packages/a0-sokoban2` | 1 | 3 | 2 | 7 | 2 | **0** |
| **combined** | **3** | **6** | **4** | **15** | **4** | **0** |

Across every `handover_packages/`, `handover_bundles/` and `packs/` path in the
repo: 10 dsl, 10 json, 4 lean, 20 md, 4 py, **0 pddl**. (The A6 *run* directory
does contain 14 tracked `.pddl` files, but under `generated/`, not under `packs/`
— do not let that be used to rebut the claim.)

## 5. The one live handbook

`theoria-arm/runs/20260728T015354Z-g50t-first-contact/books/generated/domain.pddl`
— the only on-line manual — has **3 actions, 3 of them `:parameters ()`,
`:precondition (and )`, `:effect (and (and))`**. 100 % empty. It declares 10
predicates and 4 types that no action reads or writes; that header machinery is
what makes the file look like a planning form on casual inspection.

Its aborted sibling (`…20260728T012311Z-…-aborted`) has 6 actions: five empty and
one, `budget-advances`, malformed — it references `?spent`, `?spent-pos` and
`?dest` while declaring `:parameters ()`. **Across both live-arm domains: 11
actions, 0 with a well-formed non-empty effect, and the single non-empty effect in
the pair is unparseable.**

---

## 6. What the paper should say

The claim appears unqualified in the abstract, in numbered contribution 1, in
§2.1, in §3, and as a rendered label in Figure 1. Replace it with a sentence of
this shape — every clause below is backed by an artefact in §1–§5:

> The manual compiles to four forms, of which **the fourth is emitted but not
> valid**. Of the 303 actions the DSL expresses, **0** compile to PDDL that is
> both well-formed and semantically non-empty: `gen_pddl` implements only the
> `moved` and `teleported` events and emits the placeholder `(and)` for every
> other, and it emits three predicate names and five variables it never declares.
> An independent planner (Fast Downward 24.06+) accepts 7 of 34 generated
> domains, and every action in those 7 is simultaneously empty-precondition and
> empty-effect — acceptance tracks vacuity, not correctness. Both published
> handover packages therefore ship no planning form at all (3 dsl / 6 json /
> 4 lean / 15 md / 4 py, zero pddl), which the packages' own cover pages disclose.

**§2.1 needs a stronger repair than a count.**
(`papers/phase1-workshop/sections/02_framework.md:20-23`; the sentence wraps, so
grep it as two fragments.) It currently claims co-derivation
makes disagreement *visible*: *"a disagreement between forms is a bug that can be
seen rather than a drift that cannot."* An empty form cannot disagree with
anything. The visibility mechanism the paper claims is not degraded on the fourth
form — it is **inoperative**, and this is the exact failure mode that sentence
promises is impossible. That is a claim about the design, not about a backend, and
it cannot be fixed by adding a caveat elsewhere.

**Figure 1 carries the claim as pixels.** `figures/fig06_concept_timeline.py:166`
renders the literal label `"four forms"`, present as visible text in both
`figures/paper/light/figure1_concept_timeline.svg` and the dark variant. No prose
edit reaches it; the generator must change and the SVGs be regenerated.

### Every site that asserts the claim unqualified

`PAPER.md` is assembled from `sections/*.md` — **edit the section file; `PAPER.md`
is generated.** Both are listed because both are tracked and both must end up
consistent. Line numbers as of `cc7e414e`.

| file | line | why it overstates |
|---|---|---|
| `papers/phase1-workshop/sections/00_abstract.md` | 47–51 | **the worst site.** Abstract, unqualified, names PDDL as a delivered co-derived form |
| `papers/phase1-workshop/PAPER.md` | 49–53 | same sentence, assembled |
| `papers/phase1-workshop/sections/01_intro.md` | 269–273 | numbered **contribution 1** enumerates PDDL with no caveat |
| `papers/phase1-workshop/PAPER.md` | 421–425 | same, assembled |
| `papers/phase1-workshop/sections/02_framework.md` | 20–23 | **the load-bearing one** — claims co-derivation makes disagreement visible (see above) |
| `papers/phase1-workshop/PAPER.md` | 511–513 | same, assembled |
| `papers/phase1-workshop/sections/03_a0.md` | 20–22 | places "four co-derived forms" inside a list of *verified* results (pixels, axiom list, SAT plan), lending the PDDL form credibility it lacks |
| `papers/phase1-workshop/PAPER.md` | 647–649 | same, assembled |
| `papers/phase1-workshop/sections/11_limitations.md` | 210–211 | design statement in *Limitations* that does not note the fourth form is empty — **the best place to insert the correction** |
| `figures/fig06_concept_timeline.py` | 166 | renders the literal label into Figure 1 (see below) |

Already appropriately hedged, and worth citing *in* the correction rather than
changing: `sections/05_a2.md:325-333` (D-A2-006, the PDDL backend cannot ground a
teleport), `sections/06_a3_transfer.md:206-208` (the backend returns a confident
UNSAT for a correct manual — unsoundness, not incompleteness), and
`sections/10_adjudication.md:238-244` (a validated plan is legal under the shared
grounding, not under the PDDL as written).

Outside the paper, the same unqualified claim sits in `CLAUDE.md:4-6` — the first
paragraph every agent reads — and in `Theoria.md:139` and `Theoria.md:239`, where
mandatory constraint 1 justifies itself with *"证明者、执行器、规划器、人，读的是同一本书"*
("prover, executor, planner and human read the same book"). That justification is
precisely what fails: the planner reads an empty book.

### Do not write "three of four forms are verified"

That is the natural repair and it is **not supported by this work**. This item
measured one form and found it empty. It did not measure Lean, Python or Markdown.
The whole lesson here is that *emitted* ≠ *valid* — the PDDL form was counted as
delivered for months on the strength of a file existing — so asserting the other
three are verified would repeat, in the same sentence, the error being corrected.
Say what was measured. If "three are verified" is wanted, it needs its own census.

Note also that **byte-identical regeneration is not evidence of content**: an
empty PDDL form regenerates deterministically too. Several run records lean on
this and should not be read as support.

## 7. The tree already knew — the paper is behind its own records

This is not a discovery the theory-compiler track hid. It disclosed the gap and
the paper did not follow:

* `PARTNER_SYNC.md`, paragraph **`## [theory-compiler] 2026-07-28T15:10:00Z C8-handover-package`**
  (line 923 as of `cc7e414e`, at character offset ~601 of that 1231-character
  line) — *"于是两个包都没有规划形态，四形态实际是四缺一，这写在每个包的封面上"*
  ("so neither package has a planning form; four forms is really four-minus-one,
  and it is written on each package's cover page").
  Cited by heading first, then line: `PARTNER_SYNC.md` is append-only, and
  P-P22 recorded that a line anchor into a growing log is a moving target —
  correct in the author's tree, out of range in the commit that carries the
  claim. Appending (which this item also does) does not shift earlier lines, so
  923 is stable here; the heading is given anyway because it survives edits that
  a number does not.
* `theory-compiler/DECISIONS.md:615` — **D-TC-032**: *"移交包——「四形态」是承诺，不是清单；生成不等于校验"*
  ("four forms is a promise, not an inventory; generating is not validating").
* `theory-compiler/DECISIONS.md:575-578` — **D-TC-031**: *"四形态之一允许是散文，不允许是错的"*
  ("one of the four forms may be prose; it may not be wrong").
* `theory-compiler/tests/test_writes.py:376-397` — `TestBackendObligationShortfall`
  pins the shortfall by name: `EMPTY_EFFECT = {teleport-down, press-left,
  door-opens-left}`, `UNDECLARED_DEST = {push-left, push-right}`.
* `theory-compiler/README.md:32-37` already states the four and then discloses the
  PDDL gap in the next breath. **That is the model wording.**

The correction is therefore cheap and uncontested: the owning track has been
saying this for two days. What C14 adds is the *magnitude* — 0 of 303, confirmed
by a planner that never heard of the generator — and the repair distance.

## 8. Scope and limits of this finding

* Measures the **PDDL form only**. Says nothing about Lean, Python or Markdown.
* `theory-compiler/` was imported read-only and is byte-untouched; no fix was
  attempted from here and none may be.
* The denominator is disclosed as an inflated ceiling: 303 counts 61 byte-identical
  duplicate actions (20 %), and the census slightly *under*-counts elsewhere — two
  `exam/handover_bundles` manuals with 5 real rules are rejected by `parse_theory`
  for a missing `semantics:` section, so a wider reading of "expressible" gives
  313. Numerator 0 either way.
* Zero API calls. Zero sealed-pile contact. $0.00.
