# probe_frontier

Which action would tell us the most? Under determinism that is a computation,
not an estimate.

Each surviving hypothesis predicts exactly one observation for a candidate
action. The action partitions the frontier into classes that agree with each
other; the entropy of that partition is how many bits the observation buys.
Greedy argmax over candidate actions.

Nothing here is bandit-shaped — no noise to average out, no exploration bonus, no
regret. An action that halves the frontier removes exactly one bit; an action
every hypothesis agrees on removes none. That is also why the thing to probe is
the rule with a single witness, and why probing where the theory is confident is
worth nothing.

## The hand-made scenario

Two guard hypotheses no evidence so far can separate:

* `h_empty` — the cart moves iff the target cell is **empty**
* `h_nonlethal` — the cart moves iff the target cell is **not lethal**

Every transition seen had a target that was either empty (both predict a move) or
lethal (both predict none). They come apart only where a *benign non-empty*
colour is in the way — a configuration the trajectory never produced.

```
      col 0  1  2  3  4  5
  row 0    .  .  .  .  .  .
  row 1    .  .  3  .  .  .     benign green, above the cart
  row 2    .  5  6  .  .  .     lethal left, cart at (2,2)
  row 3    .  .  .  .  .  .
```

| action | target | h_empty | h_nonlethal | bits |
|---|---|---|---|---|
| **UP** | benign 3 | none | move | **1.000** |
| DOWN | empty | move | move | 0 |
| LEFT | lethal 5 | none | none | 0 |
| RIGHT | empty | move | move | 0 |

Engine output: `UP`, 1 bit. The scenario is well posed in both directions — both
frontier hypotheses really do explain all past evidence, and a third one
(`h_in_bounds`) really is refuted by it, so consistency is a filter and not a
rubber stamp.

With a third surviving hypothesis the split becomes 2-1 and the answer is
0.918 bits; after observing `move`, `h_empty` is dropped and the next probe (from
a state in row 0) separates the two survivors with another full bit.

## Path cost

Reaching a divergent state is itself a planning problem, so probes are ranked by
**bits per unit cost** with a caller-supplied cost map (default 1). Two equally
informative probes are separated by what it costs to get to them. Ordering is
total and deterministic: value, then entropy, then cost, then the action's name.

## Fed by the miner

`hypotheses_from_guards(frontier, evaluate)` turns a `cegis_miner` frontier
straight into probe hypotheses — one per surviving guard, predicting whether the
rule fires. The two engines share one data structure, as the framework requires.
The `free` / `in_bounds` ambiguity that `cegis_miner` refuses to guess at
(DECISIONS.md D-002) is resolved by a probe into a configuration where the strip
is on the board but occupied.

## Payload shape — `kind: "probe_design"` (stable)

```json
{
  "action": "UP",
  "entropy_bits": 1.0,
  "value_bits_per_cost": 1.0,
  "cost": 1.0,
  "n_hypotheses": 2,
  "hypotheses": [{"id":"h_empty","description":"moves iff the target cell is empty","weight":1.0}],
  "partition": {"move": ["h_nonlethal"], "none": ["h_empty"]},
  "ranking": [{"action":"UP","entropy_bits":1.0,"cost":1.0,
               "value_bits_per_cost":1.0,"n_classes":2,
               "partition":{"move":["h_nonlethal"],"none":["h_empty"]}}],
  "state": ["000000","003000","056000","000000","000000","000000"],
  "rendering": "probe UP: it splits 2 hypotheses into 2 outcome classes (1.000 bits)"
}
```

`evidence.transitions` are the transitions that left the frontier where it is
(the ones that failed to separate the hypotheses); `evidence.coverage` is
`<hypotheses consistent with that evidence>/<hypotheses in the frontier>`.

## API

```python
from engines import probe_frontier as pf
best, ranked = pf.run(hypotheses, state, actions, costs=None, out_path=...)
best.action, best.entropy, best.partition
pf.surviving(hypotheses, state, action, observation)   # after the probe returns
pf.hypotheses_from_guards(rule.frontier, evaluate)     # from cegis_miner
```

`best` is `None` when no action separates anything — a real answer meaning this
state cannot advance the frontier, not a failure.
