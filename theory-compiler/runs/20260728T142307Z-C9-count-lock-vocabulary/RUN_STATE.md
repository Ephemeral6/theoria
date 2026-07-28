# C9 · a counting guard, and the premise it did not fix

`prompt_id: C9-count-lock-vocabulary` · worker `W-1252` · branch
`agent/c9-count-lock-vocabulary` · cell C1 · territory `theory-compiler`

**Read `FINDING_premise.md` first.** It is the measurement that changed what this
run could deliver, and it was written and committed before anything was built on
the work order's premise.

## The work order, and where it holds

> 做：给守卫语言加计数谓词（`count(Type, pred) >= k` 一档，不要一步跨到全称量词），
> 过表达力台账登记；四份既有 DSL 不回归；worldgen 的 count-lock 世界跑通
> cold-start-a0 流水线作为验收。

| clause | state |
|---|---|
| counting predicate in the guard language, one rung | **done** |
| registered in the expressivity ledger with provenance | **done** — `cold-start-a0/THEORIZE_LOG.md` **E-08** |
| four existing DSLs do not regress | **done, measured** |
| the count-lock world runs through the `cold-start-a0` pipeline | **not met.** Unreachable by a counting predicate — proved, not conceded |

## What was built

`count(<Type>)` and `count(<Type>, <field> = <value>)` now compile inside a
**guard**, compared against an integer with any of `= != < <= > >=`.

Most of it was a lifting, not an extension. `>=` was already legal in a guard
(`_find_comparison_op` accepts it, the contract's guard language already says
"integer arithmetic"), and the call shape already parsed. `count` was implemented
**once, inline in the goal compiler, reachable only under `=`**; a guard that
mentioned it reached `unknown predicate 'count'` and refused. There is now a
single `_count_expr` and the goal and the guard share it — two implementations of
a counting rule is how a manual comes to mean one thing when it predicts and
another when it decides it has won.

**One rung, and each rung below it refuses with its own message and its own
test**: a second condition, a condition that is not an equality, counting a type
the level supplies no instance of, and a bare `count(...)` used as a truth value.
A quantifier is the next rung and needs its own forcing world.

Fixture: `theory-compiler/tests/fixtures/countlock_theory.dsl` — the smallest
world that needs the clause and nothing else. Deliberately *not* a model of
`t2-lock-fragile`: that world's collect rule moves the agent and consumes a token
in one transition, a two-object write and a separate question. Taking a token is
its own action here, so the fixture tests the counting predicate and not the
event vocabulary. Verified at the boundary — gate holds at 0, 1 and 2 tokens
collected, opens at 3, and in any collection order.

## A live defect the lifting exposed

`count(<Type>)` with no condition compiled to a literal `1` per declared
instance — **a constant**. So `count(Door)` stayed 1 after the Door vanished.
The A0 manual's own conservation law

```
invariant door_latch count(Button, 8) + count(Door) = 1 [status: proven]
```

is therefore false as written on any state where the Door is gone, and it is
tagged `proven`. Nothing caught it because invariants are never compiled and no
shipped **goal** exercised a vanish; a guard does, immediately. `count` now
counts present instances. The invariant itself is *not* edited — it is the
deliverable, and a run that quietly repaired a shipped manual would be reporting
on a document nobody wrote. It is recorded here and in E-08.

## `gen_pddl` was dropping the clause, silently

A manual with a counting guard compiled to a PDDL domain and reported success —
with the count condition simply absent, i.e. a gate that opens unconditionally.
`_extract_pred_pddl` has no else-branch, so anything it does not recognise falls
out of the precondition without a word (D-TC-031 records two further instances of
the same shape). `:strips :typing` has no numeric fluent, so the honest options
are a chain of threshold predicates or a refusal. It refuses.

`gen_lean` is unaffected: the enumerative development reads the compiled
predictor's transition table and inherits the semantics.

## No regression, measured rather than asserted

334 tests pass in `theory-compiler` (319 before, 15 new). `cold-start-a0`'s own
suite passes and `run_all.py` is green end to end.

The miner-side atom bumps `_KIND_BITS` from 3 to 4 (nine kinds need four bits),
which adds one bit to **every** atom. Uniform, so it cannot reorder equal-length
guards, but it does tilt short-versus-long very slightly. Re-running
`cold-start-a0/run_all.py` moves `artifacts/candidates.jsonl` in exactly one
field:

```
rows: 29 -> 29
top-level fields that differ: {'id': 23, 'payload': 23}
payload keys that differ:    {'guard_cost_bits': 23}
  guard_cost_bits  kind=rule_hypothesis  old=16  new=18
rows whose GUARD differs: 0
```

Zero guards changed; `id` moves because it is a hash of the payload.
`candidates_no_button.jsonl` moves the same way. The regenerated artefacts are in
this commit, so the delta is inspectable rather than described.

## The acceptance line: not met, not lowered

The count-lock world still does not run through the pipeline, and a counting
predicate cannot make it. `FINDING_premise.md` has the argument; the short form:

* a colour-cardinality atom is a function of the frame's colour histogram;
* all **276** transition pairs the miner is stuck on have **identical**
  histograms;
* so no such atom separates any of them — and the failure list is byte-identical
  with the count atom family present, same 19 groups.

The stuck pairs differ only in where the agent is standing. That is readable —
`at(r,c)` reads an anchor — but the anchor it reads is not the agent's:
`multi_miner.mover_track` picks "the track that moves most", and on this world the
agent is credited with **1** move in 110 transitions while three stationary
tokens are credited with 61 between them. The segmenter hands the agent's
identity to a vanishing object, so the mover is a token and every positional and
strip atom is anchored on something that never moves. On a world with no
consumables (`t1-walk-maze`) the attribution is clean, which is why A0's cart
world never hit it.

The fix is in mover selection or in object identity across absence — a different
module, upstream of the vocabulary, and not something to reach by widening a
grammar. Handed on rather than half-done:
`monitor/inbox/20260728T151500Z-W-1252-count-lock-is-a-tracking-bug-not-a-vocabulary-gap.md`.

## Gaps

1. **The acceptance line is unmet**, above. The bar is not lowered and no partial
   credit is claimed.
2. **The miner's counting atom buys nothing on the world that asked for it** —
   measured zero. It ships anyway, on a different justification, and the
   justification is stated rather than implied: the miner should be able to
   *propose* what the manual can *state*, or count-lock rules can only ever
   arrive by adjudication. If a later pass decides that principle does not carry
   its 16 atoms, the atom family is one contiguous block (`_count_atoms`) and
   removing it is a clean revert. It is the one thing in this run whose provenance
   is an argument rather than a measurement, and it is flagged here for that
   reason.
3. **`diagnose_miner`'s verdict is a false attribution** on this world and its
   test cannot detect the case that occurred. Reported to `worldgen`, not edited —
   not my territory.
4. **`t1-tokens-lock` passes L1 with the same broken attribution**, so its pass
   is not evidence that the pipeline handles consumables. Also in the note.
5. **The contract is not revised.** `count` in a guard is inside
   `dsl_grammar_v0.2` §"Guard language: spatial predicates, object comparisons,
   integer arithmetic, and negation" as written, so no revision item is owed for
   the clause itself; what changed is that the compiler now implements what the
   contract already said. If a later reading disagrees, E-08 is the entry a
   revision item would cite.

## Reproduce

```bash
cd theory-compiler && python -m pytest -q          # 334 passed, 1 skipped
cd cold-start-a0   && python -m pytest -q && python run_all.py
python -m worldgen.qc.diagnose_miner t2-lock-fragile     # still 19 groups
python theory-compiler/runs/20260728T142307Z-C9-count-lock-vocabulary/probes/01_can_a_count_separate.py
```

Zero network, zero model calls, zero API spend, zero sealed-pile contact.
