# C15 — running notes

Written as the work happened. Conclusions live in `FINDING.md`; this is the log.

**Cell:** C15 · **Territory:** `theory-compiler` · **Branch:**
`agent/c15-the-unnameable-cell-has-no-home-in-the-dsl` · **Base:** `1e5b3f00`
**Spend:** $0.00 — no ARC action, no model call, no network, no sealed-pile
contact. `theoria-arm/` read only.

---

## 1. Baseline (2026-08-02T08:55Z)

`cd theory-compiler && python -m pytest -q` → **375 passed, 1 skipped in 36.26s**,
matching the figure recorded by the previous run
(`runs/20260801T1200Z-R2-2-board-cell-expressivity/GATES.txt:8`). Green before
anything was touched.

Worktree note: `git worktree add` was interrupted by a 2-minute tool timeout
partway through checking out 13,086 files and left an `index.lock` behind. No
git process was running, so the lock was stale; removed, `reset --hard HEAD`,
clean tree. Recorded because the interrupted state *looked* like 13,120 staged
deletions, which is alarming and is not what it was.

## 2. What was already settled, and what C15 actually inherits

`5ee845ee` (D-TC-033, ledger E-10, run `20260801T1200Z-...`) already answered the
**routing** question and answered it correctly: the v0.3 grammar states the
edge-advance law whenever the level seats an instance on the cell, so R2-2 is a
segmentation gap, not an expressivity gap. That run is not re-litigated here.

What it explicitly did **not** do, and what C15's acceptance line demands:

1. it left the refusal **uncontracted** — `CONTRACTS/dsl_grammar_v0.3.md`
   untouched, by design, because it had invented no extension. But C15's own
   words: *写下来的拒绝是一条契约，沉默不是*. A refusal enforced only by
   `ir.py` is not a contract;
2. no back-pointer at `theoria-arm/GAPS.md` R2-2 (correctly — that is another
   territory; see §6);
3. its residue list named a hole in the **fourth form** and did not measure it.

## 3. The fourth form — measured, and the 2026-08-01 prediction is wrong

`FINDING.md:207-211` of the previous run predicted:

> `gen_pddl` never sees either new check. It does not call `build_ir`. … a
> manual that reaches `gen_pddl` and writes a landmark would still be compiled
> by it. Named, not fixed.

**Measured false.** Two probes:

`probe_fourth_form.py` → `FOURTH_FORM.json`. On the 1×8 bar, `gen_pddl` refuses
all four cases *including the arm's working shape*, because `colored(<cell>, n)`
has no STRIPS image in this subset. A refusal that lands equally hard on the
good manual is not enforcement, so this world cannot answer the question — which
is what the previous run also said, and it is right.

`probe_pddl_leak.py` → `PDDL_LEAK.json`. So the question was put where it is
answerable: the checked-in `cart` world, which all four forms compile today
(BASE row: four `compiled`). Then one-line edits that write a cell:

| manual | gen_python | gen_lean | gen_markdown | gen_pddl |
|---|---|---|---|---|
| BASE, unedited | compiled | compiled | compiled | compiled |
| `then recolored(origin, 1)` — landmark | IRError | IRError | UnrenderableRule | **UnsupportedClause** |
| `then vanished(origin)` — landmark | IRError | IRError | UnrenderableRule | **UnsupportedClause** |
| `then recolored(toward(Cart, up), 1)` — cell term | IRError | IRError | UnrenderableRule | **UnsupportedClause** |

`gen_pddl`'s two reasons, verbatim, and both are *on point*:

* landmark: `'origin' is not a declared object type; this backend can only
  parameterise over the word table's objects`
* cell term: `an event's first argument must be an object`

**So all four co-derived forms refuse, and the fourth was never leaking.** One
false start on the way, recorded because it changes what the numbers mean: the
first draft wrote `painted(c) writes { c }`, and `gen_pddl` refused with *"no
STRIPS encoding for event painted/1"* — a true refusal of the wrong thing,
reaching the event-name check before the write-target one. Measuring the fourth
form requires an event the backend actually implements (`recolored/2`,
`vanished/1`), or the probe scores a refusal it did not earn.

**The caveat that goes in the contract.** `gen_pddl` arrives at the same verdict
by its *own* route — PDDL's typing discipline, not `_check_write_targets`, which
it never runs (it does not call `build_ir`). The agreement is convergent, not
derived, and nothing currently pins it: a `gen_pddl` that one day parameterises
over landmarks would lose the refusal silently. That is why C15's deliverable
here is a **test that pins it**, not a change to `gen_pddl` — the previous run
declined to touch that file to protect the 2026-07-31 repair, and that judgment
still holds.

## 4. Two numbers in the board item that do not survive checking

Recorded because C15's own acceptance line says a claim must be demonstrated
rather than asserted, and that cuts both ways.

* **「每命令一像素」** overstates the bill by 2×. Every primary source says *per
  second command*: r3's own theorem — *"it now costs one pixel on EVERY second
  command rather than only on key 2 and key 4"*; `README.md:63-65` of the R2 run
  — *"posts a one-pixel-per-second-command bill for it"*; `inner/probe.py:497` —
  *"pays one pixel for it on every second command"*. The meter is command-parity.
  The string 每命令一像素 appears nowhere in the tree except the board item.
* **The 16/16/14/5 counts are right but overlap.** They are over the 38
  off-frontier recoveries only (`REPLAY.json:1872-1902`), and the nine
  hypothesis counts sum to 84 over 38 answers, so "`edge_advance_1` recovered
  16" is not 16 answers nothing else got. No per-generator marginal is published.
  Also `edge_advance` vs `_1` vs `_2` are **rank indices**, not distinct
  mechanisms (`inner/probe.py:698-703`): rank 0 keeps the bare id, and which
  chain is rank 0 is not stable across legs.

Neither changes the verdict. Both would change a paper sentence.

## 5. The draft argument was wrong, and this is where it broke

§1–§4 above were written before the verdict's *reasoning* had been attacked. It
was, and it did not survive. Recorded here in the order it happened, because the
sequence is the point: the conclusion (b) stood, and every load-bearing premise
under it had to be replaced.

The draft's argument was: *the write-extent of a compiled theory is exactly its
instance set, so any form that lets an effect reach a never-changed cell must
either fail in all four forms or amount to the compiler seating an instance —
and compiler-side seating is strictly worse, because the segmenter has the frame
evidence.* Three of those clauses are false. All three were re-run first-hand
(`probe_counterdesign.py`, `COUNTERDESIGN.txt`) rather than taken on the
reviewer's word:

* **A.** `gen_pddl` declares the colour fluent over `?c - cell`
  (`gen_pddl.py:260`, printed by the probe) and emits colour facts read straight
  off `problem.board` (`:440-443`) — the never-varying layer by definition. So
  the write-extent is *not* the instance set in the PDDL form. One honest
  qualification: the probe measured the declaration; the fact emission is read
  from the source, because the world with a painted board is the 1×8 bar and
  `gen_pddl` refuses that world for the unrelated `colored(<cell>, n)` reason. A
  first pass saw `colour facts in :init : 0` on the cart world and nearly read it
  as a refutation — it is not, the cart board is all background.
* **B.** `gen_lean` obtains its transition relation by exec'ing `gen_python`'s
  output (`gen_lean.py:101`). "All four forms refuse" is true as an observation
  and overstated as four independent witnesses.
* **C.** The decisive one. A sparse write-time overlay — **one** extra state
  field, not one per cell, filled only where a rule writes — burns the frontier
  cell with nothing seated, and `key()` changes, so the enumerative Lean route
  carries it unchanged. **Option (a)'s design space is not empty.** It is also
  not "seating by another name": no entry in `problem.instances`, no rule
  multiplication in `ground_over_instances`, nothing for `count` or `free` to
  see.

And the routing claim was backwards. The segmentation operator does *not* hold
the relevant evidence — the cell has never varied, so there is none, and the
operator's own principle says not to seat. The artefact that knows the cell is
about to change is the manual's law.

So the refusal was rebuilt on what survives, all of it checkable: the overlay's
bill is a rewrite of `frame persist`, `conflict` and `count(<Type>, …)`, which
v0.3 §1 quantifies over objects; `Theoria.md:226`'s 全帧责任制 is an immovable
constraint that admits no rule-written pixel belonging to neither board nor
object; and `Theoria.md:90` makes 从不变的沉淀为棋盘 a defeasible default over
history-so-far, with `:43` pre-registering 一开始就看错了棋盘 as a canonical
diagnosis. `dsl_grammar_v0.4.md` §3.6 lists the four dead arguments by name so
nobody rebuilds the verdict on them.

A note for whoever reads this next: the value of the adversarial pass was not
that it changed the answer. It did not. It was that the published reason would
otherwise have been one a careful reader could disprove in an afternoon, on a
file marked 定稿.
