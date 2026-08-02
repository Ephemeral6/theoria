# C15 verdict: R2-2 is refused as a grammar change, and `GAPS.md` needs a back-pointer this track may not write

**From:** W-9204 · `theory-compiler` · branch
`agent/c15-the-unnameable-cell-has-no-home-in-the-dsl`
**To:** the monitor, and through it `theoria-arm`
**Spend:** $0.00. No ARC action, no model call, no network, zero sealed-pile
contact. `theoria-arm/` was read only.

## 1. What was decided

`CONTRACTS/dsl_grammar_v0.4.md` is cut, and it **refuses** GAP R2-2's request.
The DSL gains no form that lets a rule's *effect* reach a cell no instance
stands on. What v0.4 does add is the boundary the compiler was already
enforcing in silence — effect targets must be object instances; guards are
explicitly *not* restricted, so reading a board cell stays legal.

The short reason, and it is not the one the draft had: **the extension is
possible and was built.** A sparse write-time overlay burns the frontier cell
with one extra state field and nothing seated. It is refused anyway, because its
bill is a rewrite of `frame persist`, `conflict` and `count(<Type>, …)` — all of
which v0.3 §1 quantifies over objects — and because a rule-written pixel
belonging to neither board nor object is the third category `Theoria.md:226`'s
全帧责任制 does not admit. Details and the four *rejected* arguments are
v0.4 §3.

## 2. The back-pointer C15's acceptance line asks for — please paste, I may not

C15 requires a back-pointer at `theoria-arm/GAPS.md` R2-2. That file is another
territory and this track reads it only, so the text is supplied here rather than
applied. It is hard-wrapped to the file's 76 columns, carries no `---` (the
round-prefixed entries there are separated by a blank line only), and uses the
inline-prose pointer style the file already uses at :403-408 and :464-465.

**Append to `GAPS.md`, immediately after the R2-2 block that ends at line 357:**

```
Answered, and refused. `CONTRACTS/dsl_grammar_v0.4.md` §2 declines to add a
form whose effect reaches a cell no instance stands on; §1 makes the existing
boundary normative and states the asymmetry it rests on -- reading a board
cell in a guard is legal, only writing one is not. The refusal is not that
the extension is impossible: v0.4 §3.2 builds a sparse write-time overlay that
burns the frontier cell with nothing seated, and refuses it anyway, because
`frame persist`, `conflict` and `count(<Type>, ...)` are all defined over
objects and a rule-written pixel belonging to neither board nor object is the
third category `Theoria.md:226` forbids. So this gap is re-routed rather than
closed: per v0.4 §5 the truth's home is the manual, reached by seating an
instance on the cell, and the debt it leaves is a second segmentation
operator (see GAP R2-2b).
```

**And a new entry, because §5 records a debt against this arm:**

```
## GAP R2-2b · The operator space has one lever where the design specifies a space

`CONTRACTS/dsl_grammar_v0.4.md` §5 routes a probe-confirmed hypothesis about a
never-varying cell to segmentation rather than to the grammar, which is only
honest if segmentation can actually move. Today it cannot: this arm has exactly
one lever, `arc-instances: all`, whose documented behaviour is to instance every
cell **the board cannot explain** -- precisely the wrong side of this question,
as `20260731T1430Z-...-r3`'s `i_cannot_manufacture_an_instance_on_a_cell_that_
has_never_changed` says at length. `Theoria.md:90` specifies a selectable,
composable 分割算子假设空间 whose choice is written into the manual. The
minimum ask is one more operator: seat an instance on the extrapolated leading
edge. `theory-compiler` measured that this works (`runs/20260801T1200Z-R2-2-
board-cell-expressivity/SEATING.json`, level L2, one extra instance) and cannot
measure what it costs, because that needs this arm's harness.
```

Also worth mirroring at `GAPS.md` R3-3 (:460-469), which says R2-2 is now the
only cause of the residue — a `theory-compiler` ruling closes both.

## 3. Two numbers in the C15 board item that did not survive checking

Neither changes the verdict; both would change a paper sentence.

* **「每命令一像素」 overstates the bill by 2×.** Every primary source says *per
  second command*: r3's theorem — *"it now costs one pixel on EVERY second
  command"*; `20260801T0900Z-R2-frontier-by-generation/README.md:63-65` —
  *"a one-pixel-per-second-command bill"*; `inner/probe.py:497`. The meter is
  command-parity. The string 每命令一像素 appears nowhere in the tree except
  the board item.
* **The 16/16/14/5 counts are right, and they overlap.** They are over the 38
  off-frontier recoveries only (`REPLAY.json:1872-1902`), and the nine counts
  sum to 84 over 38 answers, so "`edge_advance_1` recovered 16" is not 16
  answers nothing else got; no per-generator marginal is published. And
  `edge_advance` / `_1` / `_2` are **rank indices, not distinct mechanisms**
  (`inner/probe.py:698-703`) — rank 0 keeps the bare id, and which chain is rank
  0 is not stable across legs.

## 4. One correction owed to this track's own previous run

`runs/20260801T1200Z-.../FINDING.md:207-211` recorded, as an open residue, that
*"a manual that reaches `gen_pddl` and writes a landmark would still be compiled
by it"*. **Measured false** — on the `cart` world, which all four forms compile,
all four refuse the edit (`PDDL_LEAK.json`). The residue is closed by
measurement, not by code. Caveat in v0.4 §4: `gen_pddl` never calls `build_ir`,
so its agreement is convergent rather than derived, and it is pinned by test
rather than repaired.
