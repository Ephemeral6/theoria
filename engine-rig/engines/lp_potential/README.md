# lp_potential

One linear program, two products from the same weight vector: an unsolvability
**certificate** and an admissible **heuristic**. This is the minimal rehearsal of
the A1 pagoda argument, on a state graph built directly in Python — no DSL, no
theory-compiler dependency.

## The LP

Weights `w` over board positions; the potential of a state is the sum of `w` over
its occupied cells. Subject to:

| Constraint | Meaning |
|---|---|
| `w[dst] - w[src] - w[over] <= 0` for every jump geometry | no legal move raises the potential |
| `potential(s0) - potential(g) <= -margin` for every goal `g` | winning requires raising it |
| `-bound <= w_i <= bound`, minimise `sum |w_i|` | smallest weights that do the job |

The move constraints are collected over the **full** state space (all 16 states),
not just the reachable part, so the closure argument does not depend on knowing
what is reachable — which is the whole point of not enumerating.

Infeasible is a real answer, not a failure: if the goal *is* reachable, no such
weight function can exist. `solve_certificate` returns `None`.

## The certificate

Three conditions, mirroring the Lean skeleton of Theoria 1.10a, with
`I(s) := potential(s) <= potential(s0)`:

```
inv_init    I(s0)
inv_closed  every legal move keeps I         (dw <= 0 on every move instance)
goal_break  every goal state violates I      (potential(g) > potential(s0))
------------------------------------------------------------------------
            no goal state is reachable from s0
```

The LP runs in floating point; the result is snapped to rationals
(`Fraction.limit_denominator`) and all three conditions are re-checked in exact
arithmetic. The engine raises rather than emitting weights that only hold to
1e-9 — upstream hands the checker a certificate, the checker does not search.

## Result on Fixture C

```
initial 1110 (unsolvable)   w = (-1, 1, 0, 1)
                            potential(1110) = 0,  potential(goal 0100) = 1,  margin 1
                            inv_init / inv_closed / goal_break all hold exactly
initial 1011 (unsolvable)   certificate found
initial 1101 (solvable)     NO certificate -- the LP is infeasible, as it must be
initial 0111 (unsolvable)   NO certificate -- see "incompleteness" below
```

Cross-checked against the enumeration: from `1110` the only reachable states are
`{1110, 1001}`, and the goal `0100` is not among them.

**Sound but not complete.** `0111` is genuinely unsolvable and no *linear*
potential proves it. That limitation is asserted by a test rather than papered
over: the method may fail to prove a true statement, but it can never prove a
false one — no configuration ever gets a certificate unless the enumeration
agrees it is unsolvable.

## The heuristic

```
M    = max potential drop of any single legal move
h(s) = min over goals g of ceil((potential(s) - potential(g)) / M)
       infinite when potential(s) < potential(g)
```

Admissible by construction: the potential has to fall by `potential(s)-potential(g)`
and no move drops it by more than `M`. An infinite value is the certificate's
per-state form — a claim that this state cannot reach the goal at all — and every
such claim is checked against the enumeration.

On this fixture the bound is weak (0 or 1 against a true distance of 2): the LP
minimises the weights, so the potential is as flat as the constraints allow.
Admissibility is the requirement; sharpness is not, and erring flat is erring in
the safe direction (see DECISIONS.md D-008).

## Payload shapes (stable)

`kind: "invariant"` — the certificate:

```json
{
  "form": "potential_weights",
  "weights": ["-1", "1", "0", "1"],        // exact rationals, as strings
  "weights_float": [-1.0, 1.0, 0.0, 1.0],
  "initial": "1110",
  "initial_potential": "0",
  "goal_states": ["0100"],
  "goal_potentials": {"0100": "1"},
  "margin": "1",
  "max_decrease": "2",
  "conditions": {"inv_init": true, "inv_closed": true, "goal_break": true},
  "move_instances": ["jump(0,1,2)", "jump(1,2,3)", "jump(2,1,0)", "jump(3,2,1)"],
  "claim": "goal unreachable from 1110",
  "rendering": "potential(s) = sum of w over occupied cells; ..."
}
```

`kind: "heuristic"` — the same weights as a lower bound:

```json
{
  "form": "potential_lower_bound",
  "weights": ["-1", "1", "0", "1"],
  "max_decrease": "2",
  "goal_states": ["0100"],
  "formula": "h(s) = min_g ceil((potential(s) - potential(g)) / M), ...",
  "admissible": true,
  "admissible_basis": {
    "certificate_holds": true,
    "certificate_conditions": {"inv_init": true, "inv_closed": true, "goal_break": true},
    "empirical_check": "3 state(s), 0 counterexample(s)",
    "counterexamples": [],
    "admissible": true
  },
  "admissibility_check": [{"state":"1101","h":0.0,"true_distance":2,"admissible":true}]
}
```

`admissible` is **derived, not asserted** (D-034). It was a literal `true` until
E16, sitting beside an `admissibility_check` that nothing read. It is now
`certificate_holds AND no counterexample`, computed in `Heuristic.as_json` from
the check passed into it — one expression, so the headline and the evidence
cannot drift apart. `admissible_basis` shows the working: which half licenced the
verdict, and which rows refuted it.

The proof half is `certificate.holds`, the exact rational re-check. The empirical
half is a **sample** against known shortest paths, so it can only ever subtract:
rows that all say `admissible` do not prove admissibility, but one row that says
otherwise settles it. An `admissibility_check` omitted leaves
`empirical_check: "not run"`, and an *empty* one leaves `"vacuous"` — neither is
scored as a pass, because `not []` is True and "no state was examined" must not
read as "every state passed".

## Both rows are gated on the premises, not just the heuristic

`check_exactly` iterates `certificate.moves`, so a move geometry missing from
that list is unconstrained in the LP **and** unexamined in the re-check (D-035,
site 1). No amount of sampling fixes that reliably, so `candidates()` re-derives
the premises from the graph instead:

```json
"premise_check": {
  "move_list_complete": true, "missing_moves": [],
  "moves_raising_potential": [],
  "goal_states_match_graph": true,
  "certificate_goal_states": ["0100"], "graph_goal_states": ["0100"],
  "sound_over_graph": true
}
```

`moves_raising_potential` is `inv_closed` recomputed over **every** geometry the
graph has — the check the certificate's own inputs structurally cannot perform.
When `sound_over_graph` is false, `on_unsound="withhold"` (the default) emits
**neither row**; `"mark"` emits both carrying `unsound: true`.

Gating one row and not the other was the first cut of this fix, and it was the
same defect one row over: the invariant went out asserting `goal unreachable from
1110` with all three conditions `true`, beside a heuristic row whose
counterexamples were a proof that `inv_closed` is false over the real move set.
The invariant payload now also publishes `holds` outright, because `conditions`
alone does not say what it looks like it says — `all({}.values())` is `True`, so a
consumer re-deriving the verdict from an unchecked certificate reads "never
checked" as "passed".

`run(..., goal_states=[...])` is supported and unaffected: a certificate about
other goals proves what it says. What it does not license is scoring `h` against
`graph["distance_to_goal"]`, which measures the distance to a *different* set —
on a mismatch every row of the report is a fabricated counterexample, so the
empirical check is declined (`"not comparable"`) rather than run and mis-scored.

## API

```python
from engines import lp_potential
certificate, heuristic = lp_potential.run(graph, "1110", out_path="candidates.jsonl")
certificate.conditions            # {'inv_init': True, 'inv_closed': True, 'goal_break': True}
certificate.potential("1110")     # Fraction
heuristic.value("1101")           # float lower bound, inf when unreachable
lp_potential.admissibility_report(heuristic, graph)
```
