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
    """Cost per billed model call, in call order. The money axis."""
    return [c.cost_usd or 0.0 for c in sorted(run.calls, key=lambda c: c.idx)]


def _turn_costs(run: Run) -> List[float]:
    """Cost per decision, in decision order. The *shape* axis.

    Not the same list as `_costs` whenever a decision was retried: three model
    attempts at one step are three billed calls but one turn. E1 wants the
    money and uses `_costs`; E2 and E3 describe how the bill is distributed
    over the run's decisions and must not count a retry as deliberation.
    """
    return run.turn_costs()


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
    costs = _turn_costs(run)
    total = sum(costs)
    if total <= 0:
        return thin("E2", "total cost is zero")
    if len(costs) < MIN_TURNS_FOR_SHAPE:
        return thin("E2", "fewer than %d turns; a short run is trivially "
                          "front-loaded" % MIN_TURNS_FOR_SHAPE)
    k = max(1, math.ceil(len(costs) * FRONTLOAD_K))
    return ok("E2", sum(costs[:k]) / total, turns=len(costs), head_turns=k,
              billed_calls=len(run.calls))


@metric("E3", "economy",
        "Fraction of the run's turns needed to reach 90% of its total cost. "
        "Low means the bill settled early.",
        needs=("model_calls", "cost"), direction="lower", unit="share")
def convergence_point(run: Run):
    costs = _turn_costs(run)
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


@metric("E6", "economy",
        "Mean HTTP attempts the harness burned per logged environment step. "
        "A diagnostic: it prices the infrastructure the other economy "
        "metrics charge silently to the arm.",
        needs=("steps", "http_tries"), direction="neutral", unit="tries/step")
def retry_amplification(run: Run):
    """The hidden denominator, surfaced rather than described.

    The harness retries a refused action up to eight times with backoff and
    then writes **one** ledger row. A step that cost eight round trips is
    therefore indistinguishable from one that cost a single round trip
    everywhere except in `http_tries`. On the envelope cells that is the
    difference between 44 successful actions and 425 HTTP calls.

    Registered `neutral` on purpose. This measures the API and the retry
    policy; ranking an arm on it would be ranking the weather. It is here so
    that it appears in the correlation matrix beside P5 and E1, where a reader
    meets it before concluding anything about cost.
    """
    tried = [s for s in run.steps if s.http_tries is not None]
    if not tried:
        return thin("E6", "no step records an HTTP attempt count")
    total = sum(s.http_tries or 0 for s in tried)
    failed = [s for s in tried if s.failed]
    return ok("E6", total / len(tried), steps=len(tried), http_calls=total,
              on_failed_steps=(sum(s.http_tries or 0 for s in failed)
                               / len(failed)) if failed else None)


@metric("E7", "economy",
        "R^2 of a quadratic fit to prompt size per turn minus R^2 of a linear "
        "fit. Positive means what the arm re-reads is accelerating.",
        needs=("model_calls", "prompt_chars"), direction="lower")
def prompt_growth_quadratic_gain(run: Run):
    """E4's question, asked of an axis that can answer it.

    E4 fits curvature to *context tokens* and finds nothing on `bare_cc` --
    and the reason is not that the arm's memory is flat. `bare_cc` invokes a
    fresh one-shot CLI per turn in a clean working directory, so
    `input_tokens` is a constant 10 and `cache_read_input_tokens` a constant
    24405 on every call in the envelope: those numbers describe the CLI's own
    fixed system prompt, not the arm. The history the arm re-reads is
    assembled into the prompt *body*, where the token fields cannot see it.

    `prompt_chars` is that body. It is a worse unit than tokens and a better
    axis than a constant, which is the whole argument for it.

    The confound is not cured, only moved: this counts what the harness chose
    to assemble, so a harness that truncates history on a schedule flattens
    the curve for reasons that have nothing to do with a theory closing.
    `PREDICTIONS.md` registers that, and the difference from E4 is that the
    confound now lives in a field a reader can go and check.
    """
    calls = sorted(run.calls, key=lambda c: c.idx)
    sizes = [(c.prompt_chars or 0) for c in calls]
    if len(calls) < 5:
        return thin("E7", "fewer than five turns; a quadratic needs room")
    if max(sizes) <= 0:
        return thin("E7", "no call records a prompt size")
    xs = [float(i) for i in range(len(sizes))]
    ys = [float(v) for v in sizes]
    linear = polyfit_r2(xs, ys, 1)
    quadratic = polyfit_r2(xs, ys, 2)
    return ok("E7", quadratic - linear, r2_linear=round(linear, 6),
              r2_quadratic=round(quadratic, 6), turns=len(calls),
              first_chars=sizes[0], last_chars=sizes[-1])
