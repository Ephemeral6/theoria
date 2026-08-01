# R2-2 is not an expressivity gap. The grammar says it; the compiler lied about it.

**Cell:** R2-2 · **Territory:** `theory-compiler` · **Branch:** `z/r2-2-grammar`
**Spend:** $0.00. No ARC call, no desk call, no model call, no network. Sealed
pile: zero contact. `theoria-arm/` was read only.

---

## 0. The one-sentence answer

`theoria-arm/GAPS.md` R2-2 says the arm can predict the edge advance and cannot
write it down, and files it as a DSL expressivity hole for `theory-compiler`.
**It is not one.** The v0.3 grammar, unmodified, states the edge-advance law
correctly and predicts exactly the right cell — the same manual, byte for byte,
compiles to a predictor that is silent or correct depending only on **which
cells the level seats an instance on**. What made it look like a grammar hole
was a defect in this compiler, in the exact spelling anyone reaching for a board
cell writes first, and that defect is the deliverable.

Per the brief's instruction 4: the honest answer is that the grammar can say it,
so **no grammar extension was invented**, and `CONTRACTS/dsl_grammar_v0.3.md` is
unchanged.

---

## 1. What the claim was, and how it was checked

`theoria-arm/runs/20260801T0900Z-R2-frontier-by-generation/README.md` §1:

> 12 of the 47 off-frontier probes … every one of those 12 has an observed delta
> containing **exactly one cell that had never changed before in the run** … a
> cell that has never varied is board, so it gets no instance, and
> `forall ?p in <Type>` has nothing to range over there.

The arm's own manual
(`theoria-arm/runs/20260731T1430Z-A3-level2-carried-r3/books/theory.dsl`,
theorem `i_cannot_manufacture_an_instance_on_a_cell_that_has_never_changed`)
locates the cause in the **arm**, not the grammar:

> the arm offers exactly one lever, `arc-instances: all`, and its documented
> behaviour is to instance every cell OF THAT COLOUR THE BOARD CANNOT EXPLAIN …
> **So the hole is a property of the arm.**

That sentence is the one GAPS.md re-routed to `theory-compiler`. The re-routing
is what this run tested, and it does not hold up.

The arm compiles through this compiler — `theoria-arm/inner/books.py` imports
`theory_compiler.generators.gen_python.generate_python` — so whatever this
compiler refuses, the arm cannot write, and the question is answerable here
without touching the arm.

**The forcing world.** `theoria-arm`'s row-63 meter, shrunk to what it needs to
be: one row of eight cells, board-painted colour 9, the two rightmost already
burned to colour 1 (so: varied, instanced), cols 0–5 never varied (so: board, no
instance). The law is the arm's — one command and the cell left of the leftmost
burn burns. Its next victim, col 5, is a board cell.

---

## 2. The measurement — `SEATING.json`

One manual. Three levels. The manual is **identical across all three**; only the
level's `objects` list differs.

```
  rule edge_advance forall ?p in Bar
    when act=key(2) and colored(?p, 9) and colored(rightof(?p), 1) then recolored(?p, 1)
```

| level | instances seated on | fired | row before | row after | edge advanced |
|---|---|---|---|---|---|
| **L1** the arm's seating | cols 6,7 (the varied cells) | *nothing* | `9 9 9 9 9 9 1 1` | `9 9 9 9 9 9 1 1` | **no** |
| **L2** + one on the edge | cols 5,6,7 | `edge_advance__Bar_5` | `9 9 9 9 9 9 1 1` | `9 9 9 9 9 1 1 1` | **yes** |
| **L3** every cell | cols 0–7 | `edge_advance__Bar_5` | `9 9 9 9 9 9 1 1` | `9 9 9 9 9 1 1 1` | **yes** |

L2 and L3 agree exactly, and each changes exactly one cell — the right one.
L1 is the arm's situation and it is silent, which is the 12-of-47.

**So the sentence a reader can check is:** *the v0.3 grammar can state the
edge-advance law; what it cannot do is state it about a cell the level seats
nothing on, and which cells get seated is decided by the segmentation operator,
not by the grammar.* Theoria.md line 90's `从不变的沉淀为棋盘` is the
segmentation principle that produces L1, and Theoria.md's 可动/不可动 line lists
**分割算子空间** among the movable parts, next to `DSL 表达力`. R2-2 is a live
gap in a movable part. It is the other movable part.

---

## 3. What made it look like a grammar hole — the defect, `LANDMARK_EFFECT.txt`

Nine spellings of the law went through the parser and all four forms
(`PROBE.json`). One of them is the trap.

```
  landmark edge  # arc-cell: (0, 5)

  rule edge_burns
    when act=key(2) and colored(edge, 9) then recolored(edge, 1)
```

A landmark is a cell the level locates; naming one is the obvious way to talk
about a cell with no instance on it, and it is what a desk tries first. Before
this run it **compiled**, in three of the four forms, and:

* `writes(edge_burns)` resolved to `{edge}` — `edge` is a `NameRef`, and
  `WriteSets.of_rule` never asked whether a written name is an object;
* `gen_python`'s compiled effect was `state.edge_color = 1`, and
  `check_backend_agreement` passed, because both sides said `{edge}`;
* `State` has **no `edge_color` field**. It is a plain dataclass, so the
  assignment *succeeds*, creating an attribute nothing reads;
* `State.key()` omits it, so `s0.key() == s1.key()` — the two states are equal;
* `render` rebuilds the frame with `grid = [list(row) for row in BOARD]`, and
  `BOARD` is a compile-time constant, so the cell can never move.

Measured, verbatim, with the new check disabled so the defect still reproduces:

```
run it:
   rules fired   ['edge_burns']
   row before    [9, 9, 9, 9, 9, 9, 1, 1]
   row after     [9, 9, 9, 9, 9, 9, 1, 1]
   states equal  True
   the leaked attribute: state.edge_color = 1
```

**A rule that fires and means nothing, reading exactly like a rule that works.**
That is strictly worse than a refusal: a refusal names the repair, and this sent
the reader away believing the language could not say it — which is how R2-2 came
to be filed against `theory-compiler` at all. It is E-03's failure class
(a silent default) and X-1's (a backend that quietly overrides the manual) one
level further down, in the code X-1 installed to prevent exactly this.

**And a second one.** `gen_markdown` — the form a human reads, and the only one
producible with no level — renders `recolored(leftof(?s), 1)` as

> then leftof(?s)'s colour becomes 1.

while `gen_python` and `gen_lean` both refuse the same manual outright. Nothing
on the Markdown path ever asked what a rule writes. Four co-derived forms, and
the prose one was the only one saying the manual meant something.

### The other seven spellings, for the record

| spelling | verdict |
|---|---|
| S1 `recolored(?p, 1)`, bound object | the arm's own shape; correct, and can only ever name a varied cell |
| S2 `recolored(leftof(?p), 1)`, cell term | refused by `gen_python`/`gen_lean`; **rendered as prose by `gen_markdown`** |
| S3 `recolored(edge, 1)`, landmark | **the trap above** |
| S4 landmark in the guard, object in the effect | fine — this is what r3's thirteen panel rules do with `spawn_probe` |
| S5 `appeared(leftof(?p))` | same refusal as S2; not specific to `recolored` |
| S6 `moved(?p, left)` onto the virgin cell | compiles and **burns col 5** — but by *un*-burning col 6: `9 9 9 9 9 1 9 1`. It slides a mark, it does not advance an edge. The closest workaround, and it says a different law |
| S7 `forall ?d in dir` over a value domain | grounds four copies that all write `edge`; `AmbiguousTransition` at runtime |
| S8 `recolored(?p.pos, 1)` | cell term the long way; same refusal as S2 |
| S9 a second type on colour 9, level seats none | grounds to **zero** rules and fires nothing — r3 rejected this workaround in prose, and it is vacuous in fact |

`gen_pddl` refuses all nine, for a reason that has nothing to do with R2-2:
`act=key(2)` carries a numeric argument this STRIPS subset has no ground action
for. That refusal lands on S1 — the arm's *working* shape — exactly as hard as
on the others, so it is not evidence about anything here. It is the pre-existing
declared refusal `dsl_grammar_v0.3.md` §5 describes for a whole world class, and
this run does not touch `gen_pddl`, which was repaired on 2026-07-31.

---

## 4. What was changed

No grammar. No contract. Two refusals and their tests.

| where | change |
|---|---|
| `writes.py` | `written_names(rule, writes)` — the names a rule's event writes, or `None` when the event has no resolvable write set. Splits "unknown event" (someone else's error, better message elsewhere, v0.3 §7) from "resolved, and pointing at a non-object". Returns `?a` for a rule variable, which is legitimate on an ungrounded rule |
| `ir.py` | `_check_write_targets` — writing a declared **landmark** is an `IRError` naming the repair; writing a **cell term** is an `IRError`; writing an instance **this level does not seat** is a *warning* |
| `gen_markdown.py` | `_check_effects_are_writable` — the same two errors, from the AST alone, so the bare `generate_markdown(ast)` path is under the same rule as the other three forms |
| `tests/test_write_targets.py` | 12 tests: 3 positive controls, 7 negative controls, 2 pinning the warning |

**Why the third row is a warning and not an error.** It is a different situation
wearing the same symptom, and conflating them was the easy mistake — the first
draft of this check did, and it deleted a working level from a checked-in
handover package. `theory.dsl` is the **domain** and travels between levels;
`a0-cart`'s `press_left` writes `Button`, and its `no-button` level is entitled
to have no button, so the rule simply cannot fire there. A landmark is different
in kind: the manual has *declared* it to be a cell, so no level can make it
right, which is what makes it an error. The unseated-instance case still
compiles to the same do-nothing assignment, so it is reported and the count is
pinned in the tests — v0.3 §5's own precedent, that a shortfall is carried as a
measured number rather than as a memory.

**The negative controls were seen to say no.** With both checks removed, 9 of the
12 tests go red and the 3 survivors are exactly the positive controls, which must
pass either way.

---

## 5. Residual gaps, stated

1. **R2-2 is not closed — it is re-addressed.** The repair is in
   `theoria-arm`'s segmentation operator: seat an instance on the leading-edge
   cell. This run shows that would work (L2) and does not do it, because that
   is another territory. The ask is in `monitor/inbox/`.
2. **The seating has a price nobody has measured.** L3 seats 8 instances in an
   8-cell world. `theoria-arm`'s board is 64×64 = 4096 cells against 87 that
   have ever varied, and `ground_over_instances` grounds one rule per instance
   per binding. Seating every cell would ground r3's 22 rules over 4096
   instances instead of 51. **L2's targeted seating — the leading edge only —
   is the cheap version and is the one the ask asks for.** Neither cost is
   measured here; that measurement needs the arm's own harness.
3. **`gen_pddl` never sees either new check.** It does not call `build_ir`.
   It refuses this world class for its own reason, so nothing is currently
   hidden, but a manual that reaches `gen_pddl` and writes a landmark would
   still be compiled by it. Named, not fixed — touching `gen_pddl` risks the
   2026-07-31 repair, and the brief says not to regress it.
4. **The unseated-instance case is still compiled, not refused.** A warning is
   read only if someone reads it. `a0-cart`'s two rules are unreachable in that
   level so nothing is presently wrong; a level where the guard *could* hold
   would fire a rule that does nothing, warned about and not stopped.
5. **No live evidence, and none was needed.** Everything here is offline
   against a synthetic 1×8 world plus the arm's checked-in artefacts. A live
   leg would settle a different question — whether a seated edge instance
   actually converts the 12 recovered predictions into confirmed rules — and
   would cost one `theoria-arm` leg. It is not needed to settle R2-2's routing,
   which is what this run was for.

---

## 6. Reproduce

```bash
cd theory-compiler/runs/20260801T1200Z-R2-2-board-cell-expressivity
python probe_seating.py          # the finding: same manual, three levels
python probe_grammar.py          # nine spellings, four forms
python probe_landmark_effect.py  # the defect, before and after the check
cd ../.. && python -m pytest -q tests/test_write_targets.py
```
