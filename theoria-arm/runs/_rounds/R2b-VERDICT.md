# R2b verdict — the generated frontier is kept

**Change (one):** `--frontier=generated`. Build the probe frontier from
generated successor hypotheses anchored on the world's own last frame,
instead of from ablations of the current manual.

**Baseline:** the 52 probes recorded across the four 2026-07-31 legs,
plus R1b which changed nothing that touches probing.

## The three pre-registered predictions, and what happened

| prediction | target | measured | verdict |
|---|---|---|---|
| frontier width | 2 → ≥3 | **6, 8, 9, 10** | met |
| off-frontier rate | 90.4% → ≤40% | **22%** (6 of 27) | met |
| realised bits > 0 | 0 of 56 → at least half | **21 of 27 (78%)** | met |

Containment **9.6% → 78%**. Every probe that landed on the frontier
realised positive information; the two numbers are equal at 21 because a
contained answer is exactly what buys bits here.

**The refutation condition did not fire.** It was: off-frontier stays
above 70% *with* width ≥3, meaning the world is outside the generated
class too and the change reverts. Width rose and off-frontier fell
together, which is the outcome the condition was written to distinguish
from a lucky width increase.

## Per leg

| leg | actions | desk | usd | surprises | probes | contained |
|---|---:|---:|---:|---:|---:|---:|
| R2b-g50t-a | 29 | 9 | 18.74 | 31 | 24 | **20 (83%)** |
| R2b-sk48-b | 9 | 6 | 20.30 | 7 | 3 | 1 (33%) |

The legs disagree and the disagreement is not noise: sk48 fired three
probes to g50t's twenty-four, at $3.38 per desk call against $2.08, and
advanced nine actions against twenty-nine. Whatever sk48's manual is
doing, it is doing it in the desk rather than in the world. n=3 on that
leg is too thin to read as a containment rate and is reported as a count.

## The methodological result, which outlasts the number

The offline replay predicted **43 of 52 contained ≈ 83%** before the
round fired. The live g50t leg measured **83%**. The counterfactual
harness that produced that prediction — reconstructing each recorded
probe's frontier and checking it against the observed successor — is
therefore an instrument that can be trusted to size a change before it is
paid for. That is worth more than this one result: it means the next
candidate can be ranked offline.

## What did not move

**Zero levels completed.** Eight live legs, ten with these two, and no
level has ever been finished. A better frontier buys better probes, and
better probes are not a plan. The goal protocol (R1b) established why:
the desk refuses to write a goal it has not seen a win for, in writing,
on principle — and its argument stands unrefuted.

## Cost

$39.04 for the round. R2's aborted attempt cost $0.00 (upstream refused
RESET 40 times; measured refusal rate 83%, unrelated to any change here).

## Disposition

**Kept.** `--frontier=generated` should become the default once one more
round confirms it on a second game with more than three probes; until
then it stays a flag and the default stays byte-identical, per the
plumbing precedent this arm now has for five knobs.
