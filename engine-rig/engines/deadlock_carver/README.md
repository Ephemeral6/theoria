# deadlock_carver

Whole-level unsolvability is rare in the wild. Dead corners are not — and every
pruning region is a **conditional mini unsolvability theorem** (Theoria 1.9).
This engine carves them out of a grounded task, and the same theorem then goes
two places: into the candidate stream, where the LLM may adjudicate it into the
playbook as a `prune` clause, and into the planner, where it pays in nodes.

That double use is the claim being tested. "The theorem is true" and "the theorem
is worth having" are different statements, so this engine reports a node account
and not an adjective.

## The theorem

```
<pattern>  AND  not-goal   =>   dead
```

A pattern is a conjunction of ground atoms. It is **dead** when both hold:

1. **Closed.** Every ground action that would delete an atom of the pattern is
   impossible in any state containing it. So every successor of a state
   containing the pattern contains it too.
2. **Excludes the goal.** No state containing the pattern is a goal state.

Together: from a state containing the pattern you can only reach states
containing the pattern, and none of those wins. Note what the theorem does *not*
say — nothing about the level as a whole, only about the region the pattern cuts
out. That conditionality is the point.

## Mutexes, derived rather than declared

Both obligations need one fact the action set does not state outright: which
atoms can hold together. `mutex.py` computes it as the **h² reachability
fixpoint** (Haslum & Geffner), binary case — an over-approximation of the
reachable atom pairs, so the useful direction is negative: a pair the fixpoint
never produces genuinely never co-occurs.

On the sokoban fixture that recovers, from the action set alone:

* `at(b,c)` and `clear(c)` are mutex — a cell holds at most one thing;
* `at-player(c)` and `at(b,c)` are mutex;
* `at(b,c)` and `at(b,c')` are mutex for `c ≠ c'` — a box is in one place.

The engine is never shown the board. Negative preconditions are ignored rather
than approximated, which yields *fewer* mutexes and therefore fewer theorems —
the safe direction, since an unsound mutex would delete a real plan.

## The two proofs it actually produces

**Box in a dead corner** (`closure: no_deleting_action`) — Theoria 1.9's own
example, and the degenerate case: **no** ground action deletes the box's
position at all. Every push out of a corner needs a pusher cell that is a wall,
so `adj` is missing and grounding discarded those instances before the search
ever saw them (DECISIONS D-016). The certificate is an empty list.

**Two boxes side by side against a wall** (`closure: deleting_actions_blocked`) —
here pushes exist on paper. Pushing either box along the wall needs the cell the
*other* box occupies to be clear, or the player to stand where the other box is;
pushing away from the wall needs a pusher cell outside the board. Four deleting
actions, four mutex certificates. This one genuinely needs the h² facts.

Patterns are capped at two atoms — exactly the width h² can reason about, so a
wider pattern would be checked with evidence that cannot see it. Raising the cap
needs h^m, not a bigger loop. Pairs whose halves are already dead are dropped:
they say nothing new and would double-count in the node account.

## The node account

Measured on the sokoban fixture, `--deterministic`, both runs on the bundled BFS:

| Instance | Theorems | Expansions before | after | Plan length |
|---|---|---|---|---|
| `open4far` (solvable, 2 boxes) | 16 | 808 | **571** (−29.3%) | 11 either way |
| `ringstuck` (unsolvable) | 2 | 44 | **22** (−50.0%) | none either way |
| `open4` (solvable, shallow) | 16 | 47 | 47 (−0%) | 6 either way |

The third row is in the table on purpose. On `open4` the search finds its
6-action plan before wandering into a single dead region, so sixteen true
theorems buy nothing. Pruning pays where the search would otherwise go, and the
unsolvable instance is where it pays most — proving "no plan" means visiting
everything, unless half of everything is dead.

Plan length is unchanged in every row, which is the soundness check that matters
operationally: an unsound theorem shows up here as a *changed answer*, not as a
faster one.

## Soundness, checked by a different method

`tests/test_deadlock_carver.py` exhausts the reachable state space, computes by
backward closure which states can still reach a goal, and asserts that no state
matching any dead pattern is among them. The referee's *method* shares nothing
with the proof — forward BFS and backward closure, no mutexes, no blocked-action
argument — so a theorem that is wrong for the reason the proof is clever shows up
here as a live state it covers. That is the check worth having.

Its *grounding* is not independent. The referee is built from
`strip_static(domain, problem, ground_actions(domain, problem))` — the carver's
own reduction, the sharing `Task` discloses below. So a theorem that passes is
certified dead over the atoms the search actually holds, which is exactly the
claim the pruner needs, and not over the PDDL as written. A grounding that drops
an action makes that action absent for the referee too, and neither of them will
notice.

## Interface

```python
from engines import deadlock_carver as dc

task     = dc.Task.build(domain, problem)     # grounds, strips statics, derives mutexes
theorems = dc.carve(task)                     # minimal dead patterns, deterministic order
report   = dc.pruning_report(domain, problem, theorems)
prune    = dc.pruner(theorems)                # -> fd_adapter.search(..., prune=prune)

task, theorems, report = dc.run(domain, problem, out_path="candidates.jsonl")
```

`Task.build` reduces the task with the planner's own `strip_static`, so the atoms
a theorem talks about are exactly the atoms the search's states contain.

## Payload shape — `kind: "invariant"` (stable)

```json
{
  "form": "conditional_unsolvability",
  "producer": "deadlock_carver",
  "domain": "sokoban",
  "problem": "sokoban-open4far",
  "pattern": [["at", "b1", "c11"]],
  "pattern_text": "at(b1,c11)",
  "size": 1,
  "closure": "no_deleting_action",
  "n_deleting_actions": 0,
  "blocked_actions": [],
  "goal_conflict": {"pattern_atom": "at(b1,c11)", "goal_atom": "at(b1,c42)",
                    "why": "mutex: the two can never hold in the same reachable state"},
  "mutexes": {"atoms": 64, "reachable_pairs": 1560},
  "claim": "every reachable state containing at(b1,c11) is dead",
  "rendering": "at(b1,c11) AND not-goal => dead"
}
```

`evidence.transitions` indexes the ground actions that delete a pattern atom —
the ones the proof had to discharge, empty for a corner. `evidence.coverage` is
`<ground actions>/<ground actions>`: every one was examined and none escapes.

## Payload shape — `kind: "plan"`, the node account (stable)

```json
{
  "form": "pruning_account",
  "producer": "deadlock_carver",
  "problem": "sokoban-open4far",
  "n_theorems": 16,
  "expansions_before": 808,
  "expansions_after": 571,
  "expansions_saved": 237,
  "expansions_ratio": 0.706683,
  "states_pruned": 69,
  "plan_length": 11,
  "plan_length_unchanged": true,
  "baseline": {"solved": true, "length": 11, "expansions": 808, "...": "..."},
  "pruned":   {"solved": true, "length": 11, "expansions": 571, "...": "..."}
}
```

`evidence.coverage` is `<expansions the pruned search still needed>/<nodes the
blind search generated>` — the account in the contract's own field, not only in
the payload.

## The account gates the theorems (D-034)

`plan_length_unchanged` is a **verdict on the theorems**, not a statistic beside
them: `false` means pruning changed the instance's answer, so at least one
theorem excluded a state the goal was reachable from. Until E16 the emitter ran
`carve -> pruning_report -> emit` with no branch in the middle, and published the
refuted theorems next to the report refuting them.

`candidates(..., on_refutation=...)` now decides:

| | `invariant` rows | `plan` row |
|---|---|---|
| no report | emitted | absent |
| verdict passed | emitted | no `refuted` key |
| refuted, `"withhold"` (default) | **none emitted** | `refuted: true`, `invariants_withheld: <n>`, `on_refutation` |
| refuted, `"mark"` | emitted, each with `refuted: true` + `refutation` | same, `invariants_withheld: 0` |

The `refutation` object is machine-readable on purpose — `bench/dividend.py`
reads fields, and a warning inside a `rendering` string is not a gate. The
withheld **count** is published for the same reason: a refuted run that simply
emitted nothing would be indistinguishable from a run that carved no theorems,
and "nothing to report" is the wrong reading of a suppression.

`refuted` is **absent**, never `false`, when no verdict was taken — "nobody
asked" and "asked and passed" are different states, and both differ from "asked
and failed". An unfinished comparison raises `UnfinishedComparison` out of
`candidates()` rather than resolving either way.

**The gate is one-directional, and the field name says so.** `false` proves
unsoundness: the answer moved, so some theorem excluded a state the goal was
reachable from. `true` proves nothing of the kind. An unsound theorem that
happens to cut only states lying on *other* optimal plans of the same length
leaves `solved` and `length` both untouched and passes. So a theorem that
survives this gate is a theorem *not caught by this instance*, which is why the
soundness evidence that matters is still the exhaustive referee above — and why
`with_report=False` is not a bypass to be closed but an honest absence of
verdict, recorded as `refuted` absent rather than as a pass.

## Provenance

The frozen contract's `engine` enum has six values and predates this engine, so
proposals go out as `fd_adapter` — the enum member whose work they are part of —
and identify themselves in `payload.producer`. The contract file is untouched and
so is its validator. See `../../DECISIONS.md` D-018.

## Modules

| File | Role |
|---|---|
| `mutex.py` | the h² reachable-pair fixpoint |
| `carve.py` | pattern enumeration, the two proof obligations, the pruner |
| `__init__.py` | node account, payloads, candidate emission |
