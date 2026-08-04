# cegis_miner

Counterexample-guided synthesis of rules (guard + effect) against an exact
ledger. Zero noise and a few dozen transitions, so the ledger *is* the verifier:
a rule is right exactly when it fires on every transition carrying its effect and
on no other.

## The loop

1. Group transitions by `(action, effect)`. Effects come from `mdl_segmenter`'s
   narration — the miner never re-derives *what happened* from pixels; it reads
   pixels only to evaluate guards.
2. Propose the most general guard (the empty conjunction, true everywhere).
3. Ask the ledger for a counterexample: a transition the guard admits but whose
   effect is different.
4. Strengthen with the cheapest literal that kills the counterexample while
   remaining true on every positive. Repeat. Terminates because each round
   strictly shrinks the admitted set.
5. Minimise (drop literals the rest already imply), then enumerate the
   **frontier**: every minimal-by-inclusion guard up to `frontier_max_size`
   literals, ordered by description length.

The output is a frontier, not a point guess — the framework's stated reason for
choosing CEGIS/version spaces over a statistical learner.

## Guard vocabulary

| Atom | Meaning | Cost |
|---|---|---|
| `act==A` | the action taken was A | 6 bits |
| `free(strip(D))` | target strip is in-bounds **and** all background | 6 bits |
| `in_bounds(strip(D))` | target strip is inside the grid | 6 bits |
| `clear(strip(D))` | the in-bounds part of the strip is background (vacuous off-board) | 6 bits |
| `at(r,c)` | the object's anchor is exactly (r,c) | 12 bits |

plus every negation. Position literals cost twice what predicates cost, on
purpose: minimising literal *count* alone would let `at(r,c)` — true of exactly
one transition — win every synthesis that has a single positive example.

Among guards of equal cost the **logically strongest** wins (`free ⇒ in_bounds`,
`act==A ⇒ !act==A'`): a stronger guard fires on fewer states, so it claims less.

`D` in the strip predicates is a *geometric* direction and is always one of
UP/DOWN/LEFT/RIGHT. `A` in `act==` is an **action**, and the actions come from
the evidence: `mine` reads the alphabet off the transitions it is given. They
were the same list until E20, which is why a world whose actions are
`ACTION1..ACTION5` produced a vocabulary in which every `act==` literal was
identically false — 36 atoms, 4 of them discriminating — and the miner reported,
correctly, that no literal separated two transitions differing only by action.
Pass `action_alphabet=` to override; `build_vocabulary(states)` with no actions
still assumes the compass. See DECISIONS.md D-E20-001.

## When a class has no guard

`mine` groups transitions by (action, effect) and synthesises per group. If no
literal in the vocabulary separates a group, `synthesize` raises
`NoSeparatingGuard` — a true report, and the default `on_unseparable="raise"`
lets it out, as it always has.

`on_unseparable="record"` keeps the frontier for every class that has one and
files the rest on `MiningResult.unseparable`:

```json
{"action": "ACTION2", "effect": {"type": "none"}, "support": [2],
 "reason": "no literal separates transition 2 from the positives"}
```

`explains_every_transition()` then returns **false**, because those transitions
are not covered and a gap must not read as coverage. `MiningResult.vocabulary`
carries the alphabet and the atom census (`n_discriminating_atoms`,
`act_atoms_are_all_constant`) so a blind vocabulary is visible in the output
rather than only in a failure. See DECISIONS.md D-E20-002.

## Result on Fixture A (49 transitions)

| rule | guard | effect | coverage |
|---|---|---|---|
| `push` (lifted) | `act==?dir ∧ free(strip(?dir))` | `move(?dir)` | **41/41** |
| `push_UP` | `act==UP ∧ free(strip(UP))` | `move(-1,0)` | 10/10 |
| `push_DOWN` | `act==DOWN ∧ free(strip(DOWN))` | `move(1,0)` | 6/6 |
| `push_LEFT` | `act==LEFT ∧ free(strip(LEFT))` | `move(0,-1)` | 19/19 |
| `push_RIGHT` | `act==RIGHT ∧ free(strip(RIGHT))` | `move(0,1)` | 6/6 |
| `teleport` | `at(0,0)` | `move to (8,8)` | **1/1** |
| `blocked_D` | `act==D ∧ !in_bounds(strip(D))` | `none` | 3/3, 2/2, 1/1, 1/1 |

The ground rules' guards are **mutually exclusive** and together admit all 49
transitions — the "exactly one successor" obligation (constraint 9) holds on this
fixture, and it holds because CEGIS was forced to add `!at(0,0)`-style literals
to keep the blocked rules off the teleport transition.

Two frontiers are worth reading:

* `push` — `free` and `in_bounds` are extensionally equal on a one-object board,
  so both survive. Neither is picked *over* the other on evidence; `free` is
  reported first only because it is the logically stronger of the two.
* `teleport` and `blocked_UP` — a single witness cannot pin a guard down, so the
  frontier holds 21 and 14 hypotheses respectively. Coverage `1/1` is the flag:
  thin evidence, probe first. This is the input `probe_frontier` consumes.

Naming (`push`, `teleport`, `blocked_D`) is a deterministic function of rule
*shape*, not of meaning — the engine only needs a stable handle. Naming a concept
is the adjudicating LLM's job and does not happen in this sprint.

## Payload shape — `kind: "rule_hypothesis"` (stable)

```json
{
  "name": "push",
  "action": "?dir",                  // a concrete direction, or "?dir" when lifted
  "guard": ["act==?dir", "free(strip(?dir))"],
  "guard_cost_bits": 12,
  "effect": {"type": "move", "direction": "?dir"},
                                     // ground rules: {"type":"move","dy":-1,"dx":0}
                                     // plus "to":[r,c] when every witness agrees
                                     // no-op rules: {"type":"none"}
  "frontier": [["act==?dir","free(strip(?dir))"], ["act==?dir","in_bounds(strip(?dir))"]],
  "frontier_size": 2,
  "frontier_max_size": 3,            // enumeration depth actually searched
  "frontier_truncated": false,       // true if the guard needed more literals than that
  "cegis_guard": ["act==?dir", "free(strip(?dir))"],
  "cegis_iterations": 4,
  "cegis_trace": [{"iteration":0,"counterexample":0,"added":"!act==LEFT","admitted_before":49}],
  "lifted_from": ["push_DOWN","push_LEFT","push_RIGHT","push_UP"]
}
```

`evidence.transitions` lists the supporting transition indices;
`evidence.coverage` is `<supporting>/<admitted by the guard>` — equal by
construction for a consistent rule, so the numerator is the evidence-strength
signal (41 vs 1).

## API

```python
from engines import cegis_miner, mdl_segmenter
seg = mdl_segmenter.segment_trajectory(frames)
transitions = cegis_miner.transitions_from_segmentation(frames, actions, seg)
result = cegis_miner.run(transitions, out_path="candidates.jsonl")
result.by_name("teleport").coverage        # "1/1"
result.guards_are_mutually_exclusive()     # True
result.explains_every_transition()         # True
```
