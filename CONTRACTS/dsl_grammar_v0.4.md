# dsl_grammar_v0.4.md

**Version:** 0.4 · **Status:** 定稿（`theory-compiler` 单方所有，不需要会签）·
**Effective:** 2026-08-02

**Owner:** the `theory-compiler` track. **Supersedes:** `dsl_grammar_v0.3.md`,
which stays frozen and unedited, as v0.2 and v0.1 did before it. **v0.2's
validator is kept and still runs**, and nothing in this revision changes a
production, so every manual that compiled under v0.3 compiles under v0.4.

**Freeze policy.** Unchanged from v0.2: a change needs a ledger entry or a
defect that forced it, named in the revision record. "It would read better" is
not a reason to touch a contract two tracks compile against.

This revision exists because the grammar was **silent about a boundary it was
already enforcing**, and because a request to move that boundary was refused
without the refusal being written down anywhere a reader of the contract would
find it. The forcing entries are `cold-start-a0/THEORIZE_LOG.md` **E-10** — the
ledger's first REFUSED row — and `theoria-arm/GAPS.md` **GAP R2-2**. The two
compiler defects that disguised the question are `theory-compiler/DECISIONS.md`
D-TC-033; the adjudication itself is D-TC-034.

C15's own words for why silence was not an option: *写下来的拒绝是一条契约，
沉默不是*.

Executable form: `theory-compiler/src/theory_compiler/ir.py`
(`_check_write_targets`), `.../writes.py` (`written_names`),
`.../generators/gen_markdown.py` (`_check_effects_are_writable`), and
`theory-compiler/tests/test_c15_unnameable_cell.py`. Where this document and
that code disagree, the code is the defect.

---

## 1. What a rule's effect may name

> **Effect targets.** For every rule `r`, every member of `writes(r)` (v0.3 §1)
> must be an **object instance**. It may be a bare instance name, or a variable
> bound by `forall ?v in <ObjectType>` and grounded to one. It may not be a
> declared `landmark`, and it may not be a **cell term** — `leftof(?p)`,
> `toward(x, ?d)`, `?p.pos`, `pos(v)`, or any other expression denoting a
> location.
>
> **Guards are not restricted by this clause.** A landmark or a cell term in a
> guard is legal and stays legal. The asymmetry is deliberate: the language may
> *read* any cell and may *write* only a thing.

Three tiers, and they are not one defect wearing three hats. This table is the
normative form of `_check_write_targets`:

| what the effect names | verdict | why it is that tier |
|---|---|---|
| a declared `landmark` | **error** | the manual has *declared* it to be a cell, so no level can make it right |
| a **cell term** | **error** | a location is not a thing the manual owns |
| an instance **this level does not seat** | **warning** | `theory.dsl` is the domain and travels between levels; the rule is legal and simply cannot fire here |

The third tier is a warning and not an error because conflating it with the
other two is the easy mistake and was made once: `a0-cart`'s `press_left` writes
`Button`, and its `no-button` level is entitled to have no button. Erroring
would delete a working level from a checked-in handover package.

Every refusal under this clause **must name the repair** — v0.3 §4's standing
rule. The repair is always the same sentence: *have the level seat an instance
on that cell, and write the rule over the instance.*

## 2. What this refuses, stated as a refusal

> **The board is not addressable by an effect, and v0.4 declines to make it so.**
> A rule may not be given a form whose effect reaches a cell that no instance
> stands on — including, specifically, a cell that has never varied and is
> therefore sedimented into `board` (`dsl_grammar_v0.1.md`: *从不共变者，沉淀为
> 棋盘*). A theory that predicts such a cell will change is making a claim about
> **which cells are objects**, and that claim is adjudicated where segmentation
> is adjudicated, not by adding a syntactic form here.

This is GAP R2-2's request, and it is refused. What follows is why, including
the part that argues against the refusal.

## 3. Why — and what does *not* justify it

The measurements are `theory-compiler/runs/20260801T1200Z-R2-2-board-cell-
expressivity/` (SEATING.json, PROBE.json) and
`runs/20260802T085557Z-C15-unnameable-cell-verdict/` (FOURTH_FORM.json,
PDDL_LEAK.json, COUNTERDESIGN.txt).

**3.1 The grammar already states the law; only the seating was missing.** One
manual, byte for byte, three levels differing only in which cells carry an
instance. With an instance on the leading-edge cell the v0.3 rule fires and
burns exactly that cell; with the arm's varied-cells-only seating the identical
bytes fire nothing. So R2-2 is not a sentence the language cannot form. It is a
sentence with nothing to range over.

**3.2 The extension is possible. It is refused anyway, and this is the honest
part.** An earlier draft of this clause argued that option (a) had an *empty*
design space — that any effectful form reaching a never-changed cell must
reduce to seating an instance. **That argument is false and was withdrawn.** A
sparse, write-time board overlay was built and run: one extra state field, not
one per cell, populated only where a rule actually writes. The frontier cell
burns with nothing seated on it, and the successor state's `key()` differs, so
the enumerative Lean route carries it unchanged. Nothing is pre-allocated for
the cells nobody writes, so the finiteness of the word table is untouched.

A refusal that misdescribes what it refuses is worth nothing, so: **the thing
being refused is available, and cheap in the generators.** The bill is
elsewhere, and §3.3 is it.

**3.3 The bill is a semantics rewrite, not a backend patch.** v0.3 §1 defines
`frame persist`, `frame reset` and `conflict` **over object instances**:

> **`frame persist`** — for every object `o` outside `⋃ writes(r)` … `s'(o) = s(o)`.
> **`conflict`** ranges over pairs of rules whose `writes` sets intersect.

An overlay cell is outside that quantifier in all three. `count(<Type>, …)` — the
goal language — also cannot see it. So a cell-writing form does not cost six
lines of `gen_python`; it costs a new clause in the frame axiom, a cell-level
intersection rule for `conflict`, and a decision about whether the goal language
can count cells. Those are the three definitions v0.3 exists to have pinned
down. Reopening them to buy a form that seating already buys is the trade this
revision declines.

**3.4 全帧责任制 forbids the overlay's ontology, and that constraint is
immovable.** `Theoria.md:226` requires that **every pixel belong either to the
board or to some object**, with unexplained pixels counted as surprises; it is
part of 内环十条约束, which `Theoria.md:355` lists as 不动. An overlay pixel is
written by a rule and belongs to neither — a third category the disjunction does
not admit. Calling it "board that changed" empties `board` of its meaning
(*从不共变者*) and makes the whole-frame audit vacuous, since any unexplained
pixel could be charged to a mutable board.

**3.5 The right reading of a confirmed edge hypothesis is 看错了棋盘.**
`Theoria.md:90` states the segmentation principle and, in the same breath,
refuses to freeze it: 落地是一个**分割算子假设空间**…模型按局选择、可组合；
**选择本身写进说明书**…也不写死单一先验. So 从不变的沉淀为棋盘 is a defeasible
default over the history observed *so far*, not an axiom. `Theoria.md:43`
pre-registers **一开始就看错了棋盘** as one of exactly three canonical diagnoses
when a prediction fails. A cell the theory predicts will change was, if the
prediction holds, never board. The repair is to re-seat it — which needs no new
syntax, and which §3.1 measured working.

**3.6 What does NOT justify this refusal.** Recorded so that a later reader does
not rebuild the verdict on the parts that failed:

* **not** "the write-extent of a compiled theory is its instance set". False for
  the PDDL form: `gen_pddl` declares the colour fluent over `?c - cell`
  (`gen_pddl.py:260`) and emits colour facts read straight off `problem.board`
  (`:440-443`), which is by definition the never-varying layer.
* **not** "all four forms independently refuse". They all refuse (§4), but
  `gen_lean` obtains its transition relation by executing `gen_python`'s output,
  so it is a dependent rather than a second opinion, and `gen_markdown`'s
  refusal is an AST check added in 2026-08-01, not a structural consequence.
* **not** "seating every cell costs 4096 instances". True of the naive seating
  and irrelevant: the competitor is one instance on the leading edge, and its
  cost has never been measured on the arm's harness.
* **not** "the segmentation operator holds the evidence". It does not — the cell
  has never varied, so there is no frame evidence about it, and the operator's
  own principle says *not* to seat. The artefact that knows the cell is about to
  change is the manual's law. §5 is written the way it is because of this.

## 4. The obligation on the four forms

> A refusal under §1 must hold in **every** co-derived form. A manual that one
> form refuses and another renders as meaning something is the defect class that
> produced GAP R2-2 in the first place.

Measured on a world all four forms otherwise compile: `gen_python` and
`gen_lean` raise `IRError`, `gen_markdown` raises `UnrenderableRule`, and
`gen_pddl` raises `UnsupportedClause`. This **corrects** the residue
`runs/20260801T1200Z-.../FINDING.md:207-211` recorded, which predicted that a
manual writing a landmark *"would still be compiled by"* `gen_pddl`; it is not.

The correction carries a caveat that is part of the clause. `gen_pddl` does not
call `build_ir` and so never runs `_check_write_targets`; it arrives at the same
verdict through PDDL's own typing discipline — *"'origin' is not a declared
object type"*, *"an event's first argument must be an object"*. The agreement is
**convergent, not derived**, and a `gen_pddl` that one day parameterised over
landmarks would lose it silently. `gen_pddl` is deliberately not modified — the
2026-07-31 repair is not worth risking for a check that already passes — so the
two reasons are pinned by test instead.

## 5. Where a confirmed board-cell hypothesis goes

The refusal owes an answer to *"then where does this truth live"*, or it merely
relocates the silence.

> A probe-confirmed hypothesis about a cell that has never varied is **not** a
> manual clause awaiting a grammar, and **not** a permanent ledger resident. It
> is evidence that the level's board/object cut should be revised, and its home
> is the manual, reached by seating an instance on that cell. Two things are
> owed in the meantime, and neither is optional:
>
> 1. **The expressivity ledger takes a REFUSED row** naming the legs and probes
>    that forced it (`Theoria.md:100` — 语法说不出的东西全部进表达力台账). E-10
>    is that row. `dsl_grammar_v0.1.md:30` is the standing precedent for a
>    refusal recorded rather than an extension taken.
> 2. **The segmentation operator owes a second lever.** `Theoria.md:90`
>    specifies a *selectable, composable* operator space whose choice is written
>    into the manual. `theoria-arm` has exactly one lever, `arc-instances: all`,
>    whose documented behaviour is to instance every cell *the board cannot
>    explain* — which is precisely the wrong side of this question. Routing R2-2
>    to a movable part that cannot in practice move would make the manual
>    hostage to a heuristic, and that is the one objection to this verdict that
>    the design document actually supports.

Parking the fact in a ledger and stopping would leave `Theoria.md:18`'s
**预测无侧门** violated: the arm would keep holding a prediction the only
prediction machine cannot make. So (2) is a debt this contract records against
`theoria-arm`, not a suggestion.

## 6. Open, and named

1. **R2-2 is re-addressed, not closed.** The repair is a seating operator in
   `theoria-arm`. Neither its cost nor its effect is measured: whether a seated
   edge instance converts the recovered predictions into confirmed rules needs a
   live leg, and the targeted-seating cost needs the arm's own harness.
2. **`gen_pddl`'s agreement is convergent (§4).** Pinned by test, not by
   structure.
3. **The check is name-based.** `_check_write_targets` inspects names, and a
   rule whose write set does not resolve — an event in neither the manual's
   `writes { … }` nor v0.3 §3's table — is skipped by it entirely, staying a
   warning here and a refusal at the point of use (v0.3 §7). Widening that would
   trade a good diagnostic for a worse one.
4. **The guard side is legal in three forms, not four.** `gen_pddl`'s STRIPS
   subset has no image for `colored(<cell>, n)` or `free(<landmark>)` and
   refuses those worlds wholesale, including manuals that are correct. That is
   v0.3 §5's declared pre-existing shortfall for a world class, not a fact about
   this clause, and it is not repaired here.
5. **`freeze/build_manifest.py` hard-codes the grammar file list.** This file
   will be silently unhashed in the release manifest until that list gains it.
   `freeze/` is another territory; the ask is in `monitor/inbox/`.

## The one hazard, stated plainly (as v0.2 and v0.3 did)

This revision refuses an extension, and a refusal is easier to over-read than a
production. It refuses **one** thing: a cell as the target of a rule's effect.
It does not refuse reading board cells, it does not refuse landmarks, and it is
not a general finding that the DSL is finished. The adjacent holes are real and
are somebody's work: `theoria-arm`'s own manual records that the language has no
way to say *unobserved, the manual declines to predict* and no state counter
with which to state a parity law — and that second one is a rule that cannot be
written here at any length. Neither is settled by this file, and quoting §2 at
them would be a misuse of it.

## Revision record — which entry forced which change

| # | change | forced by | what it cost to not have |
|---|---|---|---|
| 1 | §1 effect targets must be object instances; the three tiers made normative | the two 2026-08-01 defects, D-TC-033 | `recolored(<landmark>, 1)` compiled in three forms, fired, and changed nothing — a rule that reads exactly like one that works |
| 2 | §1 guards explicitly excluded from the restriction | this revision | without it §2 reads as a ban on naming board cells at all, which no code enforces and no evidence supports |
| 3 | §2 the refusal itself, written down | **E-10**, GAP R2-2 | the refusal existed only as an `IRError`, so the desk met it as a compiler failure rather than as a decision — which is how R2-2 came to be filed against this track |
| 4 | §3.2/§3.6 the counter-design named and priced; four failed arguments recorded | an adversarial review of this file's own draft | the draft claimed an empty design space, which is false; publishing it would have frozen a refusal whose stated reason a reader could disprove in an afternoon |
| 5 | §4 the four-form obligation, and `gen_pddl` measured | `FINDING.md:207-211`'s open residue | the residue predicted a leak in the fourth form; nobody had looked |
| 6 | §5 where the truth goes, including the debt owed by the operator space | `Theoria.md:18` 预测无侧门, `:90`, `:100` | a refusal that names no home is the silence it replaced |

## Deliberately not changed

* `dsl_grammar_v0.1.md`, `v0.2.md`, `v0.3.md` — frozen. v0.4 is a new file, and
  v0.2's validator is kept and still runs. **No production is added, removed or
  altered by this revision**; it makes an enforced boundary normative and
  records a refusal.
* `gen_pddl` — see §4. Not touched, pinned by test.
* `candidates_schema.md` — frozen, and not this track's.
* `playbook.dsl` — unchanged, including the hard anti-cheat rule.
* `theoria-arm/` — read only throughout. §5's debt is recorded here and asked in
  `monitor/inbox/`; no file under that territory was edited.
