# C15 — the unnameable cell has no home in the DSL

**Cell:** C15 · **Territory:** `theory-compiler` · **Prompt id:**
`C15-the-unnameable-cell-has-no-home-in-the-dsl` · **Worker:** W-9204
**Branch:** `agent/c15-the-unnameable-cell-has-no-home-in-the-dsl` ·
**Base:** `1e5b3f00` · **UTC:** 2026-08-02T08:55:57Z
**Spend:** $0.00 — no ARC action, no desk call, no model call, no network, zero
sealed-pile contact. `theoria-arm/` and `freeze/` read only.

The narrative of how the work went is `NOTES.md`. This is what it produced and
what it did not.

---

## The verdict

**(b) — the extension is refused**, and the refusal is now a contract:
`CONTRACTS/dsl_grammar_v0.4.md`. No production is added, removed or altered, so
every manual that compiled under v0.3 compiles under v0.4.

Three things go into it:

1. **§1** makes normative the boundary the compiler was already enforcing in
   silence — a rule's effect may name only an object instance; the three tiers
   (landmark = error, cell term = error, unseated instance = warning) become
   contract text instead of living only in `ir.py`. It also states the
   asymmetry the whole thing rests on: **reading a board cell in a guard is
   legal and stays legal; only writing one is refused.**
2. **§2** is the refusal of GAP R2-2's request itself, and **§3** is why.
3. **§5** is where a probe-confirmed board-cell hypothesis goes instead —
   its home is the manual, reached by re-seating, and the debt that leaves is a
   second segmentation operator, recorded against `theoria-arm`.

## What changed the verdict's reasoning, and why that is the main result

The draft argument was wrong and an adversarial review broke it. All three of
its counter-claims were re-run first-hand (`probe_counterdesign.py`,
`COUNTERDESIGN.txt`) rather than taken on report:

| draft claim | status |
|---|---|
| the write-extent of a compiled theory is exactly its instance set, in all four forms | **false** — `gen_pddl` declares the colour fluent over `?c - cell` (`gen_pddl.py:260`) and emits colour facts straight off `problem.board` (`:440-443`) |
| option (a)'s design space is empty; any such form reduces to seating | **false** — a sparse write-time overlay burns the frontier cell with **one** extra state field and nothing seated; `key()` differs, so the enumerative Lean route carries it unchanged |
| all four forms independently refuse | **overstated** — `gen_lean` execs `gen_python`'s output (`gen_lean.py:101`), so it is a dependent, not a second opinion |
| seating costs 4096 instances | **straw man** — the competitor is L2, one instance on the leading edge, whose cost nobody has measured |
| the segmentation operator holds the evidence | **backwards** — the cell has never varied, so there is *no* frame evidence about it; the manual's law is the only artefact that knows |

So the refusal was rebuilt on what survives: the overlay's real bill is a
rewrite of `frame persist`, `conflict` and `count(<Type>, …)`, all of which v0.3
§1 quantifies over objects; 全帧责任制 (`Theoria.md:226`, an immovable
constraint per `:355`) does not admit a rule-written pixel belonging to neither
board nor object; and a confirmed edge hypothesis is best read as
`Theoria.md:43`'s **一开始就看错了棋盘**, whose repair is re-seating and needs no
new syntax. v0.4 §3.6 records the four failed arguments by name so the verdict
cannot be rebuilt on them.

## The negative sample C15 demanded

`theory-compiler/tests/test_c15_unnameable_cell.py` — **30 tests, all passing.**
Under verdict (b) it is permanent: it never turns green by being fixed, only red
by the refusal being lost. It holds five things, of which the middle three are
what the contract needed and nobody had measured:

* §1 the `edge_advance` law aimed at the frontier cell, refused **with its
  reason**, in every form that can see it — the demonstration C15 asked for;
* §2 all four co-derived forms refuse, on a world all four otherwise compile;
* §3 `gen_pddl`'s two exact reasons pinned, because its agreement is convergent
  rather than derived;
* §4 the read/write asymmetry, so the refusal cannot be read as broader than it is;
* §5 no event allocates — `appeared(<landmark>)` is refused too;
* §6 the positive control: the same bytes, seated, burn exactly the right cell.

## A correction to this track's own previous run

`runs/20260801T1200Z-.../FINDING.md:207-211` left open that *"a manual that
reaches `gen_pddl` and writes a landmark would still be compiled by it."*
**Measured false** (`PDDL_LEAK.json`): on the `cart` world all four forms refuse.
Closed by measurement, not by code — `gen_pddl` is deliberately untouched.

One false start is recorded because it changes what a number means: the first
version of that probe used `painted(c) writes { c }` and drew *"no STRIPS
encoding for event painted/1"* — a true refusal of the wrong thing. Measuring
the fourth form needs an event the backend implements.

## Gaps — what this run did not do

1. **R2-2 is re-addressed, not closed.** The repair is in `theoria-arm`, and
   whether a seated edge instance converts the recovered predictions into
   confirmed rules needs a live leg this run did not spend.
2. **The `GAPS.md` back-pointer is not applied.** C15's acceptance asks for it
   at `theoria-arm/GAPS.md` R2-2; that is another territory and this track reads
   it only. The exact text, hard-wrapped to the file's 76 columns and in its own
   pointer style, plus a proposed `GAP R2-2b` for the operator-lever debt, is in
   `monitor/inbox/20260802T085557Z-W-9204-c15-verdict-and-the-gaps-backpointer-
   theoria-arm-must-paste.md`. **This is the one acceptance item that needs
   another territory's hand, and it is not lowered — it is handed over whole.**
3. **`freeze/build_manifest.py` will not hash v0.4.** Its grammar path list is
   hard-coded; `freeze/` is another territory. Ask in `monitor/inbox/`. Same for
   `CLAUDE.md`'s contract table, a root shared surface.
4. **`gen_pddl` is unmodified.** Its agreement is pinned by test, not by
   structure.
5. **The guard side is legal in three forms, not four.** `gen_pddl` refuses
   `colored(<cell>, n)` and `free(<landmark>)` for a whole world class — v0.3
   §5's declared pre-existing shortfall, not this clause's business.
6. **The overlay was measured, not costed.** It is enough to show the design
   space is non-empty. Nobody has priced the semantics rewrite §3.3 names.

## Reproduce

```bash
cd theory-compiler && python -m pytest -q tests/test_c15_unnameable_cell.py
cd theory-compiler/runs/20260802T085557Z-C15-unnameable-cell-verdict
python probe_fourth_form.py     # all four forms, the 1x8 bar
python probe_pddl_leak.py       # the fourth form, on a world PDDL compiles
python probe_counterdesign.py   # the three claims that broke the draft
python probe_scratch.py         # allocation, and the guard side
```
