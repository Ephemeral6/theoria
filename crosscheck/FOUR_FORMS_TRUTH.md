# The current truth value of the "four co-derived forms" claim

**Status: OVERSTATED as written in the abstract and in contribution 1 — but the
correction is narrower than "the fourth form does not exist", and the difference
matters. Read §0 before quoting any number in this document.**

Owner of this finding: `crosscheck` (W-1710, item C14). For RES-2.
Evidence: `crosscheck/runs/20260730T120005Z-C14-four-forms-is-three-and-a-half/`.
Re-derive with `bash crosscheck/verify.sh`.

`theory-compiler/` is the other track's and was not modified. This document
registers a gap; it does not repair one.

---

## 0. Scope — there are two PDDL backends, and this measured one of them

**This is the most important sentence in the document, and an earlier revision
did not contain it.** The census measures
`theory_compiler.generators.gen_pddl` — the theory-compiler track's backend, the
one behind the shipped handover packages and the `theoria-arm` live handbook. It
is 0 for 303.

The repository contains a **second PDDL backend**,
`cold-start-a0/compile/gen_pddl_a0.py`, and it works. Verified first-hand:

| | |
|---|---|
| committed domains headed `; Auto-generated from theory.dsl by compile/gen_pddl_a0.py` | **25** |
| actions in them | **263** |
| scoring GOOD under *this census's own* `classify()` | **263 (100 %)** |
| fed to the same Fast Downward build the census used | **accepted, rc 0** |

Its `push-up`, from `cold-start-a0/theory/generated/domain.pddl` — generated from
`cold-start-a0/theory/theory.dsl`, a file backend A scores **0 of 7**:

```pddl
  (:action push-up
    :parameters (?from - cell ?to - cell)
    :precondition (and (at ?from) (adj-up ?from ?to) (passable ?to))
    :effect (and (not (at ?from)) (at ?to)))
```

**But B is not a general PDDL backend that happens to live elsewhere.** Its entire
state space is one cell plus one boolean (`(at ?c)`, `(switched)`); it requires an
object literally named `Cart`, a `Door`, a `Button`/`Switch` and a landmark
`portal_exit`; it accepts exactly five event kinds; and it needs a **played trace**,
not the manual alone. It cannot represent a second moving object — the repository
already records the consequence, D-A6-001: *"the planner returns UNSAT for a manual
that is correct, silently and with confidence."* Every world after A0 needed a local
patch to use it, the last of which is whole-domain text surgery.

**Every planning number in the paper is B's**, not A's — A0's 12-step SAT plan and
Button-less UNSAT (`cold-start-a0/artifacts/fd_real.json`, whose `c5-1` cell naming
and three-parameter `press-left` are uniquely B's), A2's results, A3/A6's transfer
plans. So **no empirical planning claim in the paper is falsified by A being
broken.** What A being broken falsifies is the *framework* claim about the fourth
form. Keep those two apart.

A bare headline of "the four-forms claim is false" would therefore be **wrong**, and
would have an author retract a claim that is defensible for the arms the paper
reports planning results on. The defensible finding is narrower and still serious:

> The framework's **general** PDDL backend produces nothing usable — 0 of 303
> actions well-formed and non-empty — and it is the backend on **both documented
> compile paths from the two books**, so the live arm's handbook and both handover
> packages carry no working planning form. A second, **hand-fitted** backend
> produces everything the paper reports, but its state is one cell and one boolean,
> it hard-codes the object names, it needs a played trace rather than the manual
> alone, and it returns a confident UNSAT for a correct manual containing a second
> moving object. **Neither is "the manual compiles to PDDL" in general form**, and
> no document in either track records that these are two different programs.

**The sharpest single fact.**
`theory-compiler/handover_packages/a0-cart/manual/MANUAL.dsl` is **byte-identical**
to `cold-start-a0/theory/theory.dsl` (verified: one sha256 across both). The
repository simultaneously ships that manual with a working, real-Fast-Downward-solved
PDDL form under `cold-start-a0/theory/generated/domain.pddl`, **and** publishes on
that package's own front page that its planning form could not be generated
(`handover_packages/a0-cart/README.md:33-34`). Both statements are true; they are
about different programs; nothing in the package says so.

Everything in §1–§5 below is scoped to backend A unless it says otherwise.
Mapping of which artefacts and which paper claims depend on which backend:
`runs/…/out/TWO_BACKENDS.md`.

**How this was nearly published wrong.** The census's population is "every `.dsl`
in the repo, as `gen_pddl`'s own front end sees it" — a corpus defined by *input*
files. Backend B leaves no trace in that corpus, because it is a different
*output* path over the same inputs. The instrument had no positive control: it was
never shown a known-good domain and asked to score it GOOD. Backend B is exactly
that control, and it was found by an adversarial pass, not by the measurement.

---

## 1. The number (backend A only)

Of the **303 actions** the DSL expresses across the repository's 59 `.dsl` files,
**0** compile — *via `theory_compiler.generators.gen_pddl`* — to PDDL that is both
well-formed and non-empty.

| | |
|---|---|
| actions owed a PDDL form | **303** |
| semantically non-empty **and** well-formed | **0** |
| fraction good | **0.0 %** |

An action counts as good only if its `:precondition` has at least one literal, its
`:effect` has at least one literal, every `?var` it uses is in its `:parameters`,
and every predicate it uses is declared. Each criterion is a validity or
non-vacuity requirement, not a style preference.

**The zero is not an artefact of the denominator.** Every slicing below is
generated by `python -m crosscheck.tools.c14_slicings`, each from a named rule in
that file, and `crosscheck/verify.sh` re-checks them. Table emitted verbatim:

| slicing | files | actions | good |
|---|---|---|---|
| all `.dsl` in repo (headline) | 37 | 303 | **0** |
| compiled only, refusals folded out (the flattering slice) | 34 | 285 | **0** |
| deduplicated by DSL source bytes | 28 | 242 | **0** |
| deduplicated by generated-domain bytes | 20 | 202 | **0** |
| excluding theory-compiler test fixtures | 31 | 280 | **0** |
| canonical hand-authored theories only | 15 | 165 | **0** |
| narrowest defensible: canonical, deduped by generated-domain bytes | 10 | 133 | **0** |
| domains an independent planner accepted | 7 | 21 | **0** |
| theory-compiler/ contribution alone | 8 | 36 | **0** |

**Max good over every slicing: 0. Max good over any single file in the corpus: 0.**
`runs/…/out/DENOMINATOR.md` records further hand-checked variants, all also 0.

*(An earlier revision of this table carried a "narrowest defensible" row of 115.
That figure came from a hand slicing nobody had written a rule for and could not
be re-derived; the reproducible form of the same idea is 133. The row is corrected
and every row is now machine-generated, which is why the tool exists.)*

**The zero is not an artefact of the bar either.** Dropping the one contested
criterion — "an empty precondition is a defect", when an always-applicable action
is legal PDDL — moves the headline from 0 to **0**: not one action in the corpus
has an empty precondition as its *only* defect. Of the sixteen possible
relaxations of the four criteria, the count stays 0 under exactly the two that are
arguable (relax nothing; relax empty-precondition). The other fourteen do raise it
— dropping `undeclared-variable` gives 49, dropping `undeclared-predicate` gives
37, dropping both gives 94, dropping `empty-effect` gives 152 — but every one of
those waives a **validity** requirement, an undeclared name or a missing effect,
not a matter of taste. A domain with an undeclared predicate is not weak PDDL; a
parser rejects the file, as Fast Downward does below.

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

**Those 7 are 7 byte-identical copies of a single domain** (one sha256; the
`theoria-arm` `rev04`–`rev09` + `books/theory.dsl` snapshot lineage that
`DENOMINATOR.md` calls "one book counted nine times"). So the honest form is
**1 distinct domain of the 18 distinct domains in the corpus** — a document that
spends a section on duplicate-inflated denominators must not present a
duplicate-inflated numerator two sections later. The second blind reader, the
`pddl` 0.4.8 PDDL-3.1 parser, accepted **0 of 34**.

Within backend A, FD's acceptance is anti-correlated with meaning: it sorts this
generator's output into *malformed* and *vacuous*, and there is no third bin.
(Repository-wide there **is** a third bin — see §0.)

Four problems do not merely fail — they **crash** FD's translator with
`TypeError: unhashable type: 'list'`, on a generated goal of the form `(= (and) X)`:
`(= (and) 1)` twice and `(= (and) exit_cell)` twice — the generator emitted an
equality between the logical connective `and` and a term. **Seven** problems carry
such a goal; only four crash, because the other three fail domain parsing first, so
the crash count understates the defect. Separately, **21 of the 34** generated
problems carry a placeholder `(and)` goal, so on the problem side too, most of the
planning tasks have nothing to plan toward.

Full logs and FD's verbatim words: `runs/…/out/INDEPENDENT_PLANNER.md`.

## 3. How deep the gap is — state this too, or you overstate it

"0 of 303" alone reads as *"the PDDL backend is an unimplemented stub"*, and that
is not what the corpus shows. Bucketed by repair distance (285 compiled actions):

| bucket | actions | depth |
|---|---|---|
| **vocabulary-only** — both bodies non-empty, sole defect is `undeclared-predicate` | **37** | shallow: 3 names |
| both bodies non-empty but an **undeclared variable** — the effect moves an object to an unbound `?dest` | 57 | **deep, mislabelled** — see below |
| no effect — `:effect (and (and))` placeholder | 152 | deep: no event model |
| vacuous — both empty | 38 | deep |
| empty precondition **and** undeclared variables (`budget-advances`) | 1 | deep |

(37 + 57 + 152 + 38 + 1 = 285.)

**An earlier revision of this table said "94 naming-only" and called them
structurally correct. That was wrong and is the biggest single error the
adversarial pass caught.** Of those 94, only **37** have the vocabulary mismatch as
their sole defect. The other 57 carry an undeclared variable, and reading the raw
PDDL shows they are not near-correct at all — e.g. `step-left` in
`cold-start-a3/theory/push/domain.dsl`:

```pddl
  (:action step-left
    :parameters (?cart - cart ?left - object ?cart-pos - cell)
    :precondition (and (at ?cart ?cart-pos))
    :effect (and (not (at ?cart ?cart-pos)) (at ?cart ?dest)
                 (not (free ?dest)) (free ?cart-pos)))
```

Adding `?dest` to `:parameters` — the "one-line repair" — produces a *valid* action
that teleports the cart to **any cell in the arena, unconditionally**, and it would
pass this census's GOOD bar. Sibling actions are worse: `shove-up/down/left/right`
(8 actions) move the cart rather than the block, the effect copy-pasted from
`step-*`; `block-left`/`block-right` move `?block` from `?block-pos` to `?dest`
with all three unbound and no precondition mentioning the block. **For those 57 the
real failure is the same missing event model as the 152, wearing a different defect
label.**

The eight identifiers are three predicates the generator *emits* but never
*declares* — `adjacent-above`/`adjacent-below`/`boundary-above`, against a
hard-coded declaration block that says `adjacent-up`/`adjacent-down`/`boundary-up`
— and five variables used in a body but absent from `:parameters` (`?dest` in 50
actions, `?block-pos`, `?block`, `?spent`, `?spent-pos`).

So **13 % of the corpus (37 of 285), not a third**, compiles to PDDL whose sole
defect is the vocabulary mismatch. The best case, verbatim — `push-up` from
`ablation-arm/theory/a0_base.dsl` — has three precondition literals and four effect
literals with correct add/delete structure, a real push action, invalid solely
because the domain declares `adjacent-up` and the action says `adjacent-above`.
**That is the best case, not the representative one.**

**This is not progress and must not be reported as any.** Nearly-valid PDDL is
invalid PDDL; the planner rejects the file. The count today is 0. But a reader
told only "0 of 303" will conclude something false about *why*, and the fix
estimate that follows from it will be wrong.

**Nor is "shallow" the same as "cheap".** Reconciling the identifiers is *not*
sufficient even for the 37. A fifth defect, invisible to all four of the census's
criteria, kills them anyway: `gen_pddl` makes a `:parameters` entry out of every
direction constant, typed `object`, and no object of that type is ever declared —
so the parameter cannot bind. Measured with only the naming defect patched, against
the track's own grounder: **0 ground actions with the direction parameter, 144
without it.** The naming fix alone buys a domain that parses and grounds to nothing.

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
`?dest` while declaring `:parameters ()`. **Across both live-arm domains: 9
actions (3 + 6), 0 with a well-formed non-empty effect, and the single non-empty
effect in the pair is unparseable.**

---

## 6. What the paper should say

The claim appears **unqualified** in the abstract, in numbered contribution 1, in
§2.1 and in §3, and as a rendered label in Figure 1. It is *partially* qualified in
§11.3 (`sections/11_limitations.md:210-211`: *"The four-co-derived-forms design is
meant to make that drift visible; here it took a human reading the plan output"*) —
a concession, not a repair, and it does not say the form is empty.

Replace it with a sentence of this shape — every clause is backed by an artefact in
§0–§5:

> The manual compiles to four forms. Of these, **one — PDDL — was measured here,
> and the theory-compiler track's backend does not produce a usable instance of
> it**: of the 303 actions that backend is asked to compile, **0** yield PDDL that
> is both well-formed and semantically non-empty. `gen_pddl` implements only the
> `moved` and `teleported` events and emits the placeholder `(and)` for every
> other; it emits three predicate names and five variables it never declares. The
> A-arm planning results in §3 do not run through that backend — they use a
> separate generator (`cold-start-a0/compile/gen_pddl_a0.py`) whose committed
> domains are non-empty and are accepted by Fast Downward. Both published handover
> packages nevertheless ship no planning form at all (3 dsl / 6 json / 4 lean /
> 15 md / 4 py, zero pddl), which the packages' own cover pages disclose. **The
> other three forms were not measured by this work.**

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
renders the literal label `"four forms"`. Note how it appears in the output:
`figures/theme.py:307` sets `"svg.fonttype": "path"`, so the label is emitted as
**glyph outlines, not text** — the string occurs in both
`figures/paper/{light,dark}/figure1_concept_timeline.svg` exactly once, at line
1142, and only inside an XML comment (`<!-- four forms -->`). Do not grep the SVG
and conclude the label is a stale comment: it is the rendered label, and no prose
edit reaches it. The generator must change and the SVGs be regenerated.

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
* `theory-compiler/DECISIONS.md:578` — inside **D-TC-030** (heading at line 555;
  D-TC-031 begins at 597): *"四形态之一允许是散文，不允许是错的"* ("one of the four
  forms may be prose; it may not be wrong"). **D-TC-031** (`:597`) is the decision
  that records the `gen_pddl` backend shortfall itself: *"`gen_pddl` 达不到 v0.3 的
  后端义务——记账并钉住，不在本轮修"* ("`gen_pddl` does not meet the v0.3 backend
  obligation — booked and pinned, not fixed this round").
* `theory-compiler/tests/test_writes.py:376-397` — `TestBackendObligationShortfall`
  pins the shortfall by name: `EMPTY_EFFECT = {teleport-down, press-left,
  door-opens-left}`, `UNDECLARED_DEST = {push-left, push-right}`.
* `theory-compiler/README.md:32-37` already states the four and then discloses the
  PDDL gap in the next breath. **That is the model wording.**

The correction is therefore cheap and uncontested: the owning track has been
saying this for two days. What C14 adds is the *magnitude* — 0 of 303, confirmed
by a planner that never heard of the generator — and the repair distance.

## 8. Scope and limits of this finding

* **Measures one PDDL backend** (`theory_compiler.generators.gen_pddl`), not "the
  PDDL form". See §0: a second backend exists and works. An earlier revision of
  this document stated the headline at repository scope, which was wrong; it was
  caught by an adversarial pass, not by the measurement.
* **The instrument had no positive control.** It was never shown scoring a
  known-good domain as GOOD before being trusted on a corpus where everything
  scored bad. Backend B now serves as one (263/263 GOOD), retroactively. A known
  false negative also exists: `PREDICATES_RE` requires the `(:predicates …)` block
  to close on its own line, so a domain closing it inline yields an empty
  declared-set and every action is reported `undeclared-predicate` — demonstrated
  on `engine-rig/engines/fd_adapter/domain.pddl`, a gripper domain FD solves. It
  does not bite on `gen_pddl` output, which always formats `\n  )`, so the 303
  stand; but this instrument is not safe to point at arbitrary PDDL unfixed.
* Measures the **PDDL form only**. Says nothing about Lean, Python or Markdown.
* `theory-compiler/` was imported read-only and is byte-untouched; no fix was
  attempted from here and none may be.
* The denominator is disclosed as an inflated ceiling: 303 counts 61 byte-identical
  duplicate actions (20 %), and the census slightly *under*-counts elsewhere — two
  `exam/handover_bundles` manuals with 5 real rules are rejected by `parse_theory`
  for a missing `semantics:` section, so a wider reading of "expressible" gives
  313. Numerator 0 either way.
* Zero API calls. Zero sealed-pile contact. $0.00.
