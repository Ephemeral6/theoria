# ic3_pdr

The fallback inductive-invariant engine of Theoria 1.10(b): *"the shapes LP and
the null space cannot reach."* `zero_space` finds linear conservation laws;
`lp_potential` finds invariants shaped like a potential function. IC3 is not
restricted to a shape at all — it searches for a CNF over-approximation of the
reachable states that excludes the goal, and it reports it as the three theorems
Lean wants.

## The case that needs it

Fixture C, configuration **0111**. It is unsolvable, and no linear pagoda proves
it — DECISIONS D-014 asserts exactly that, as a test, on the grounds that the
incompleteness of linear pagodas is a real property and not a bug to tune around.

IC3 proves it, and the invariant is not a weight function:

```
I(s) = (!pos1 | pos2) & (pos1 | !pos2)
```

In words: **positions 1 and 2 always hold the same thing.** True, non-obvious,
holds at `0111`, closed under every jump, and violated by the goal `0100` — where
position 1 holds a peg and position 2 does not. Eight of the sixteen states
satisfy it, which is a loose over-approximation of the two reachable ones, and
loose is fine: an invariant has to *contain* the reachable set, not equal it.

Across all four starting configurations, IC3 and the LP never disagree, and IC3
is strictly the wider net:

| Config | Solvable | LP certificate | IC3 |
|---|---|---|---|
| `1110` | no | yes | invariant |
| `0111` | no | **no** | **invariant** |
| `1011` | no | yes | invariant |
| `1101` | yes | no (correctly) | **counterexample**, 2 moves |

The last row matters as much as the second. A method that returned an invariant
for a solvable configuration would be worthless, so `1101` is tested for a
counterexample — `jump(0,1,2) jump(3,2,1)`, `1101 → 0011 → 0100` — and the
counterexample is replayed against the transition relation before it is emitted.

## The algorithm

Plain (non-delta) IC3/PDR. Frames `F[0] = Init, F[1], F[2], …`, where `F[i]`
over-approximates the states reachable in at most `i` steps; `F[i]` is a clause
set, more clauses meaning fewer states, and the frames stay nested.

* **block** — while some state of `F[k]` is bad, try to exclude it. Look for a
  predecessor in `F[k-1]`; if there is one it becomes an obligation one level
  down. Reaching an initial state means the property is genuinely false, and the
  obligation chain *is* the counterexample.
* **generalise** — a state with no predecessor in `F[k-1]` is excluded by the
  clause negating it; then literals are dropped one at a time for as long as the
  clause stays inductive **relative to** `F[k-1]`. A clause is a disjunction, so
  dropping a literal strengthens it: this is where the engine stops talking about
  one state and starts talking about a region.
* **propagate** — push clauses forward. When two adjacent frames describe the
  same states, that frame is inductive and it is the answer.

"Relative" is the subtle word, and Fixture C shows why it is not a technicality:
the first clause IC3 learns on `0111` is `(pos3)` — "position 3 always holds a
peg" — which is inductive relative to `F[0] = {0111}` and **not** globally
inductive (`0011 → 0100` breaks it). The propagation phase is what discovers
that and refines it.

## Two things done after convergence

**Minimisation.** The frame IC3 converges on is inductive but not minimal —
clauses learned early survive propagation after later ones subsume them. On
`0111` the converged frame is `(pos3) & (!pos1 | pos2) & (pos1 | !pos2)` and the
first clause is redundant. Since the invariant is an artefact a reader
adjudicates, the engine owes them the readable form rather than the search's
scratch paper; `clauses_dropped` records how much came off. A test asserts every
surviving clause is load-bearing.

**Independent re-checking.** `check.py` re-derives the three conditions from the
system and the clause set alone, by enumeration, and does not import `pdr`. Same
discipline as the plan validator (D-010), same reason: a search that grades its
own homework grades it generously. `run()` raises rather than emitting an
invariant the checker refuses.

The three conditions are the Lean skeleton of Theoria 1.10(a) verbatim —

```lean
theorem inv_init   : I s₀
theorem inv_closed : ∀ s a, I s → I (step s a)
theorem goal_break : ∀ s, Goal s → ¬ I s
```

— and they are the same three keys `lp_potential` reports for its pagoda
certificate. Two engines, two invariant shapes, one proof obligation, so the
adjudicating reader compares like with like.

## The SAT oracle is enumeration

Every query IC3 would normally put to a SAT solver is answered here by walking
the state space (`System.states_where`). That is exact, and it is the same
substitution `fd_adapter` makes for Fast Downward (D-009) with the same
consequence: correctness is unaffected, reach is. A system with more than a few
dozen variables wants a real solver behind that one function, and nothing above
it would change.

## Interface

```python
from engines import ic3_pdr

system = ic3_pdr.peg_system(graph, "0111")        # Fixture C as a transition system
verdict, checked = ic3_pdr.run(system, out_path="candidates.jsonl")

isinstance(verdict, ic3_pdr.Invariant)            # proved unreachable
verdict.clauses                                   # CNF, minimal
system.render_cnf(verdict.clauses)                # '(!pos1 | pos2) & (pos1 | !pos2)'

isinstance(verdict, ic3_pdr.Counterexample)       # or: the goal IS reachable
verdict.moves                                     # ('jump(0,1,2)', 'jump(3,2,1)')
```

The transition relation is taken over the **whole** state space, not the part
reachable from the start — the same call `lp_potential` makes, for the same
reason: an inductive invariant must be closed under moves from every state
satisfying it, and restricting the relation to the reachable part would make the
closure check quietly circular.

## Payload shape — `kind: "invariant"` (stable)

```json
{
  "form": "inductive_invariant",
  "producer": "ic3_pdr",
  "system": "peg4",
  "variables": ["pos0", "pos1", "pos2", "pos3"],
  "initial": "0111",
  "goal_states": ["0100"],
  "cnf": [[["pos1", false], ["pos2", true]], [["pos1", true], ["pos2", false]]],
  "cnf_text": "(!pos1 | pos2) & (pos1 | !pos2)",
  "n_clauses": 2,
  "converged_at_frame": 2,
  "frame_sizes": [0, 3, 3, 1, 0],
  "states_blocked": 6,
  "literals_dropped": 15,
  "clauses_dropped": 1,
  "conditions": {"inv_init": true, "inv_closed": true, "goal_break": true},
  "check": {"conditions": {"...": true}, "counterexamples": {},
            "n_states": 16, "n_satisfying": 8,
            "method": "exhaustive enumeration over the state space"},
  "checked_by": "engines.ic3_pdr.check.verify -- shares no code with the search",
  "claim": "goal unreachable from 0111",
  "rendering": "I(s) = ...; it holds at 0111, no move leaves it, and every goal state breaks it, ..."
}
```

`evidence.coverage` is `<states satisfying the invariant>/<states in the space>`.

## Payload shape — `kind: "plan"`, a counterexample (stable)

```json
{
  "form": "counterexample_path",
  "producer": "ic3_pdr",
  "system": "peg4",
  "initial": "1101",
  "goal_state": "0100",
  "length": 2,
  "actions": ["jump(0,1,2)", "jump(3,2,1)"],
  "trace": ["1101", "0011", "0100"],
  "replayed": true,
  "claim": "the goal IS reachable -- no invariant separates it from the start"
}
```

## Provenance

The frozen contract's `engine` enum has six values and predates this engine, so
proposals go out as `lp_potential` — the enum member whose unfinished business
they are — and identify themselves in `payload.producer`. See `../../DECISIONS.md`
D-018.

## Modules

| File | Role |
|---|---|
| `system.py` | the enumerated transition system; literals, clauses, cubes; the peg builder |
| `pdr.py` | frames, blocking, inductive generalisation, propagation, minimisation |
| `check.py` | the independent checker — imports `system`, **not** `pdr` |
| `__init__.py` | payloads and candidate emission |
