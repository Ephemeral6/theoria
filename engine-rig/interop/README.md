# interop — LP certificates for the theory-compiler track

The convergence interface the other track asked for in its M8 note:

> 后续汇合 sprint 需接入 engine-rig 的 LP 输出并重构 Lean 证明策略
> （权重为手算常量，非 LP 引擎求解；Lean 证明使用 BFS 枚举可达集，非 pagoda 代数证明）

This directory produces LP-solved pagoda weights as **self-contained, independently
checkable certificates**. It writes files here and reads their public fixtures; it
does not touch `/theory-compiler/`.

## The headline finding — read this before wiring the LP in

Their peg fixture is a 5-cell board, initial `[1,1,0,1,1]`, with

```
goal count(Peg, alive = true) = 1
invariant pagoda_weight ... [status: proven]
```

**The unsolvability claim is true** — enumeration confirms `11011` reaches only
`{00111, 11100, 01001, 10010}`, bottoming out at 2 pegs, never 1.

**But no linear pagoda proves that goal.** The LP is infeasible for
`count = 1`, robustly: infeasible at weight bounds 10, 100 and 10000, while
instances that do admit certificates still get them. It is a real answer, not a
solver limit.

Narrowing the goal to a *specific* target cell changes the picture:

| target cell | linear pagoda certificate |
|---|---|
| 0 | none |
| **1** | **found** — `w = [-1, 1, 0, 1, -1]` |
| 2 | none |
| **3** | **found** — `w = [-1, 1, 0, 1, -1]` |
| 4 | none |

So the disjunction "the last peg is *somewhere*" is not provable this way even
though two of its disjuncts are. The pagoda argument needs
`potential(g) > potential(s₀)` for **every** goal state at once, and cells 0, 2, 4
cannot satisfy that alongside the move constraints.

Three consequences for the convergence sprint:

1. `[status: proven]` on `invariant pagoda_weight` with goal `count = 1` is not
   discharged by a pagoda. The theorem is true; the stated justification is not
   available. Their Lean proof by BFS enumeration is what is actually carrying it.
2. To get an algebraic proof, either narrow the goal to a specific cell (the
   certificates here are ready) or extend the invariant language — which the
   frozen `dsl_grammar_v0.1.md` forbids doing silently: it goes in the
   expressiveness ledger (表达力台账).
3. This is the same incompleteness recorded in `../DECISIONS.md` D-014: linear
   pagodas are sound but not complete, and here that bites a real claim.

## Certificate format — `lp_potential/pagoda_certificate@1`

`certificates/pagoda_<n>_<initial>_to_<goals>.json`. Weights are exact integers
(rationals scaled by the LCM of denominators; the constraints are homogeneous so
this preserves validity, and the exact rationals are kept alongside).

Every obligation carries its own witnesses, so a checker never re-derives
anything — Lean only checks:

```json
{
  "schema": "lp_potential/pagoda_certificate@1",
  "initial_state": "11011",
  "goal_states": ["01000"],
  "weights_integer": [-1, 1, 0, 1, -1],
  "weights_rational": ["-1", "1", "0", "1", "-1"],
  "initial_potential": 0,
  "invariant": "I(s) := potential(s) <= 0, where potential(s) = sum of w[i] over occupied i",
  "obligations": {
    "inv_init":   {"statement": "...", "holds": true},
    "inv_closed": {"n_checked": 6,
                   "witnesses": [{"move": "jump(0,1,2)", "positions": [0,1,2],
                                  "w_dst": 0, "w_src": -1, "w_over": 1,
                                  "delta": 0, "holds": true}]},
    "goal_break": {"witnesses": [{"goal_state": "01000", "potential": 1,
                                  "exceeds_initial_by": 1, "holds": true}]}
  },
  "conclusion": "no goal state is reachable from 11011"
}
```

`inv_closed` is checked over **all move instances on the full state space**, not
just the reachable part, so the closure argument does not depend on knowing what
is reachable — which is the point of not enumerating.

## Importing

Do not trust the producer. `verify()` recomputes everything from the document's
own contents in integer arithmetic and ignores the `holds` flags:

```python
from interop import certificate_export as ce
errors = ce.verify(json.load(open("certificates/pagoda_5_11011_to_01000.json")))
assert errors == []
```

Tests cover tampering in both directions — perturbing a weight, and swapping in a
goal that no longer breaks the invariant.

## Modules

| File | Role |
|---|---|
| `peg1d.py` | 1D peg solitaire state graphs for any board size and goal. `fixtures/peg4.py` is frozen (M1 acceptance, byte-tested), so the parameter grows here; a test asserts the two agree on the 4-cell board. |
| `certificate_export.py` | `build` / `verify` / `write` for the certificate document |
