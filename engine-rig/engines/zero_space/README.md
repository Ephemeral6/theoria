# zero_space

Every linear conservation law over GF(2), computed in one elimination. No
search, no tolerance, no statistics — the answer is exact or it is a bug.

## What it does

1. Encode the state as one indicator feature per `(cell, colour)` pair. The
   engine is **not** handed the notion "red count": Fixture B reaches it as 16
   anonymous bits.
2. Difference consecutive states: `d_t = x_t XOR x_{t+1}`.
3. Compute the null space of the difference matrix. Every `a` in it satisfies
   `a · x(t) = a · x(0)` for all t — one linear conservation law each.
4. Canonicalise the basis, because the basis that falls out of the elimination
   depends on which columns happen to be free and mixes two very different kinds
   of law together:
   * **cell-local** — support inside one cell's feature group, e.g. "cell 3 holds
     exactly one of {R, B}". These are laws about the *encoding*.
   * **global** — everything left after quotienting those out. This is the part
     that says something about the *world*.

## Result on Fixture B (41 states, 40 transitions)

```
difference rank 7      (the 7 adjacent pairs span the even-weight subspace)
null space dim  9      (16 - 7)
  8 x cell-local  "cell i: B+R mod 2 = 1"
  1 x global      "(#R) mod 2 = 0"
```

The global law is exactly the ground truth `(#Red) mod 2 = const`, recovered
without ever being told which bits mean red.

## Equivalence, not string matching

`(#Red) mod 2` and `(#Blue) mod 2` are different vectors and the same law: they
differ by the sum of the eight cell-local laws. So the acceptance check is a
subspace identity, not a comparison of renderings:

```python
equivalent_modulo_encoding(result, target)
  <=>  span(recovered) == span(cell-local laws + {target})
```

This says both things at once — the law is *in* the recovered space (nothing
missing) and the recovered space claims *nothing more* (nothing extra). Any
representative of the coset passes; an unrelated vector such as "cell 0 is red"
fails.

Soundness has an independent check on top: `verify()` re-evaluates every reported
law directly against the trajectory rather than trusting the elimination. And a
world that breaks the law (a single-cell flip) does not yield it — the engine can
say no.

## Payload shape — `kind: "invariant"` (stable)

```json
{
  "form": "gf2_linear",
  "modulus": 2,
  "features": [{"cell": 0, "color": "B"}, {"cell": 0, "color": "R"}, ...],
  "coefficients": [0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1],   // aligned with features
  "support": ["R@0","R@1","R@2","R@3","R@4","R@5","R@6","R@7"],
  "value": 0,                         // the conserved value, from the first state
  "scope": "global",                  // global | cell_local
  "rendering": "(#R) mod 2 = 0",
  "space_dimension": 9,
  "difference_rank": 7
}
```

One candidate per basis law. `evidence.transitions` is every transition (the law
is checked against all of them); `evidence.coverage` is `<n>/<n>`.

## API

```python
from engines import zero_space
result = zero_space.run(states, colors=["R","B"], out_path="candidates.jsonl")
result.global_laws()[0].rendering()          # "(#R) mod 2 = 0"
result.contains(vector)                      # is this vector one of the laws?
zero_space.equivalent_modulo_encoding(result, vector)
```

`run()` raises rather than emitting if any recovered law fails re-verification.
