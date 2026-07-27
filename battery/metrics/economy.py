"""Economy — the shape of the bill.

`Theoria.md` calls this "无知的仪表", the instrument that reads ignorance: an
arm that never understands the world pays by the turn, forever, and an arm
that buys a theory pays up front and then coasts. Claim C2 is exactly this
shape, and the front-load index is one of Phase 4's three primary endpoints.

The turn axis is **model-call order**, not step index: a turn is a decision.
`INPUT_FORMAT.md` gap 5 records that the ledger has no explicit turn index and
that this is the substitute.

A caveat that belongs in the code and not only in a footnote: prompt caching
makes cost partly a function of how a harness batches its prompts. Comparing
arms on cost is only honest under the shared-shell discipline. E4 exists partly
to keep that visible — it reads the *token* series rather than the priced one.
"""

from __future__ import annotations

import math
from typing import List

from battery.metrics import metric, ok, polyfit_r2, thin
from battery.model import Run

FRONTLOAD_K = 0.25      # "the first k% of turns"
CONVERGENCE_SHARE = 0.9  # "the turn by which the bill is essentially settled"

# The anti-gaming floor for the two shape metrics. A run that ends on turn
# four spent 100% of its cost in its first quarter and looks maximally
# front-loaded while having understood nothing -- which matters more here than
# elsewhere, because the front-load index is one of Phase 4's three primary
# endpoints. `audit/gaming.py` records this floor as E2's and E3's defence, so
# it has to be in the code and not only in the prose.
MIN_TURNS_FOR_SHAPE = 8


def _costs(run: Run) -> List[float]:
    return [c.cost_usd or 0.0 for c in sorted(run.calls, key=lambda c: c.idx)]


@metric("E1", "economy",
        "Total model cost. Support for the shape metrics, not a ranking.",
        needs=("model_calls", "cost"), direction="neutral", unit="usd")
def total_cost(run: Run):
    total = sum(_costs(run))
    if total <= 0:
        return thin("E1", "total cost is zero")
    return ok("E1", total, calls=len(run.calls))


@metric("E2", "economy",
        "Share of total cost spent in the first 25% of turns. High means "
        "front-loaded: the arm paid to understand, then coasted.",
        needs=("model_calls", "cost"), direction="higher", unit="share")
def frontload_index(run: Run):
    """Claim C2's signature, and a Phase 4 primary endpoint.

    Deliberately *not* normalised for run length. A short run is trivially
    front-loaded, which is a real confound; the discrimination pass pairs by
    game to control for it, and `METRICS.md` records it as this metric's main
    way of being gamed.
    """
    costs = _costs(run)
    total = sum(costs)
    if total <= 0:
        return thin("E2", "total cost is zero")
    if len(costs) < MIN_TURNS_FOR_SHAPE:
        return thin("E2", "fewer than %d turns; a short run is trivially "
                          "front-loaded" % MIN_TURNS_FOR_SHAPE)
    k = max(1, math.ceil(len(costs) * FRONTLOAD_K))
    return ok("E2", sum(costs[:k]) / total, turns=len(costs), head_turns=k)


@metric("E3", "economy",
        "Fraction of the run's turns needed to reach 90% of its total cost. "
        "Low means the bill settled early.",
        needs=("model_calls", "cost"), direction="lower", unit="share")
def convergence_point(run: Run):
    costs = _costs(run)
    total = sum(costs)
    if total <= 0:
        return thin("E3", "total cost is zero")
    if len(costs) < MIN_TURNS_FOR_SHAPE:
        return thin("E3", "fewer than %d turns; the same early-exit confound "
                          "as E2" % MIN_TURNS_FOR_SHAPE)
    running = 0.0
    for i, cost in enumerate(costs, start=1):
        running += cost
        if running >= CONVERGENCE_SHARE * total:
            return ok("E3", i / len(costs), turn=i, turns=len(costs))
    return ok("E3", 1.0, turn=len(costs), turns=len(costs))


@metric("E4", "economy",
        "R^2 of a quadratic fit to context tokens per turn minus R^2 of a "
        "linear fit. Positive means context is accelerating.",
        needs=("model_calls",), direction="lower")
def context_growth_quadratic_gain(run: Run):
    """Does the arm's memory grow like a transcript or like a manual?

    An arm whose memory is the conversation re-reads a growing transcript every
    turn, so its context cost is quadratic in turns. An arm whose memory is a
    manual re-reads a manual of roughly fixed size. This reads the token
    series rather than the priced one, so it survives a change in the price
    list — and it is the metric that would catch Theoria failing to be what it
    claims.
    """
    calls = sorted(run.calls, key=lambda c: c.idx)
    if len(calls) < 5:
        return thin("E4", "fewer than five turns; a quadratic needs room")
    xs = [float(i) for i in range(len(calls))]
    ys = [float(c.context_tokens) for c in calls]
    if max(ys) <= 0:
        return thin("E4", "no context tokens recorded")
    linear = polyfit_r2(xs, ys, 1)
    quadratic = polyfit_r2(xs, ys, 2)
    return ok("E4", quadratic - linear, r2_linear=round(linear, 6),
              r2_quadratic=round(quadratic, 6), turns=len(calls))


@metric("E5", "economy",
        "Total cost divided by successful environment actions.",
        needs=("steps", "model_calls", "cost"), direction="lower",
        unit="usd/action")
def cost_per_action(run: Run):
    total = sum(_costs(run))
    actions = len(run.ok_steps)
    if total <= 0:
        return thin("E5", "total cost is zero")
    if actions == 0:
        return thin("E5", "no successful actions to divide by")
    return ok("E5", total / actions, total_usd=round(total, 6),
              actions=actions)
