"""Economy — the shape of the bill.

`Theoria.md` calls this "无知的仪表", the instrument that reads ignorance: an
arm that never understands the world pays by the turn, forever, and an arm
that buys a theory pays up front and then coasts. Claim C2 is exactly this
shape, and the front-load index is one of Phase 4's three primary endpoints.

The turn axis is **the record's own `Call.turn`**, not step index and not call
order: a turn is a decision, and retries of one decision are summed into it.

That sentence used to end differently, and the change is the whole of S46.
Through v2 this module read *model-call order* as the axis, because
`INPUT_FORMAT.md` gap 5 records that the ledger carries no explicit turn index
and one-call-per-turn was offered as the substitute.  The substitute is
withdrawn.  `freeze/STATS_RULES.md` §3.0.2 step 4 and `freeze/RESIDUALS.json`
`E2-AXIS` establish why: the substitute was not applied *instead of* the labels
but *alongside* them, in one bucket dictionary, so a partly labelled record
summed a call's position into an unrelated call's turn; and on a wholly
unlabelled record it manufactured the very axis whose absence was the thing
worth reporting.  A substitute that cannot be told apart from the real axis in
the published number is not a substitute, it is a fabrication.

So there is no substitute now.  `Run.turn_axis()` says whether the axis exists
and E2/E3 decline when it does not.  The cost of that is real and is stated
here rather than hidden: a source that stops stamping turns loses its E2 and E3
readings entirely, where before it would have got a number.  Gap 5 is
consequently still open, and is now visible as an absence instead of being
papered over by one.

A caveat that belongs in the code and not only in a footnote: prompt caching
makes cost partly a function of how a harness batches its prompts. Comparing
arms on cost is only honest under the shared-shell discipline. E4 exists partly
to keep that visible — it reads the *token* series rather than the priced one.
"""

from __future__ import annotations

import math
from typing import List, Optional

from battery.metrics import Value, metric, ok, polyfit_r2, thin, unsound
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


def _cost_through(costs, mark: float) -> float:
    """Cumulative cost up to a fractional turn position.

    Whole turns up to `floor(mark)`, plus the matching fraction of the turn
    the mark lands inside. Treating a turn's cost as spread evenly across it is
    the only assumption available -- the ledger records a cost per decision,
    not a cost per instant -- and it is the assumption that makes a flat run
    score its share exactly, at every run length.
    """
    whole = int(mark)
    head = sum(costs[:whole])
    remainder = mark - whole
    if remainder > 0 and whole < len(costs):
        head += costs[whole] * remainder
    return head


def _unpriced(run: Run) -> int:
    """Model calls the source recorded without a price.

    V9-D3.  `_costs` reads `c.cost_usd or 0.0`, so a call with no price is a
    call that cost nothing, and the blind audit turned that one line into four
    attacks at once: 200 identically-sized calls with only the first priced
    scored E1 = 0.5 instead of 100.0, E2 = 1.0, E3 = 0.005, E5 = 2e-09.  None
    of them required an arm to do anything -- providers omit usage on cache
    hits, on streamed responses and on errors, so a partly-priced ledger is the
    ordinary case rather than the adversarial one.

    The capability gate does not help: it asks whether *any* call carries a
    price, which is a presence check.  This is the completeness check, and the
    economy family is the one family where the difference is the measurement.
    """
    return sum(1 for c in run.calls if c.cost_usd is None)


def _costs(run: Run) -> List[float]:
    """Cost per billed model call, in call order. The money axis."""
    return [c.cost_usd or 0.0 for c in sorted(run.calls, key=lambda c: c.idx)]


def _turn_costs(run: Run) -> List[float]:
    """Cost per decision, in decision order. The *shape* axis.

    Not the same list as `_costs` whenever a decision was retried: three model
    attempts at one step are three billed calls but one turn. E1 wants the
    money and uses `_costs`; E2 and E3 describe how the bill is distributed
    over the run's decisions and must not count a retry as deliberation.

    Empty whenever the axis cannot be rebuilt -- call `_axis_refusal` first.
    """
    return run.turn_costs()


def _axis_refusal(run: Run, metric_id: str) -> Optional[Value]:
    """The turn axis has to exist before a shape can be read off it.

    E2 and E3 are the only metrics defined *over* `Call.turn`, and until S46
    they were the only ones that could not tell a recorded axis from a
    manufactured one: `Run.turn_costs()` filled a missing label in with the
    call's position in the list.  `freeze/STATS_RULES.md` §3.0.2 step 4 and
    `freeze/RESIDUALS.json` `E2-AXIS` are the ruling; `PREREG_E2L.md` §2 G4 is
    the discipline being applied -- **an axis that cannot be rebuilt is a
    measurement that was not taken**, so this returns rather than degrades.

    Gate order, both halves of which were argued rather than assumed:

    * **After** the price completeness check.  A record can fail both, and an
      unpriced bill is the more basic defect and the more actionable reason.
    * **Before** `total <= 0` and before `MIN_TURNS_FOR_SHAPE`.  Both of those
      are computed *from* `_turn_costs`, which is empty here, so on an
      unrebuildable axis they would report "total cost is zero" and "fewer
      than 8 turns" about a record that may have spent thousands of dollars
      over hundreds of decisions.  Live leg `20260731T231654Z-R1-sk48-b` is
      that record: 3 billed calls, $7.6085275, no turn label on any of them,
      and E1 says so in the same artefact where E2 would have said zero.
      A false reason is worse than a refusal, because it reads as a finding.
    """
    axis = run.turn_axis()
    if axis.status == "partial":
        return unsound(metric_id,
                       "%d of %d model calls carry no turn label; the "
                       "decision axis cannot be rebuilt, and the fallback "
                       "that would rebuild it puts a call's position and "
                       "another call's turn label in one bucket"
                       % (axis.n_calls - axis.n_labelled, axis.n_calls))
    if axis.status == "absent":
        return thin(metric_id,
                    "no model call carries a turn label; %d call(s) of "
                    "unknown decision order is not a bill shape, and "
                    "numbering them 0..n-1 would answer a question this "
                    "record cannot answer" % axis.n_calls)
    return None


@metric("E1", "economy",
        "Total model cost. Support for the shape metrics, not a ranking.",
        needs=("model_calls", "cost"), direction="neutral", unit="usd")
def total_cost(run: Run):
    missing = _unpriced(run)
    if missing:
        return unsound("E1", "%d of %d model calls carry no price, and an "
                             "unpriced call is not a free one"
                             % (missing, len(run.calls)))
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

    **The head is interpolated, not rounded** (v2.1). Through v2 this took
    `ceil(n × 0.25)` whole turns, so the head was 3/9 = 33% of a nine-turn run
    and 3/12 = 25% of a twelve-turn one, and a *perfectly flat* run scored
    0.333 or 0.250 depending only on where it stopped. Run length here is set
    by the crash, not by the arm: `bare_cc.py` has four separate early breaks
    and the API refused a large share of actions. The artefact was the size of
    the whole finding — E2's observed range across every real run was
    0.162–0.321, and `ceil` alone manufactures a swing of that magnitude.

    Interpolating the cumulative cost at exactly 25% of the turn axis makes a
    flat run score 0.250 at every length, which is the property the definition
    is supposed to have.

    Still deliberately *not* normalised away from concentration: an arm that
    genuinely pays early should score high, and that is the measurement. Note
    what this does **not** fix — a run that dumps its entire bill on turn one
    still scores near 1.0 over any number of turns, so the anti-gaming audit
    keeps E2 in the reference tier on the concentration attack alone.
    """
    missing = _unpriced(run)
    if missing:
        return unsound("E2", "%d of %d model calls carry no price; the "
                             "shape of a bill cannot be read from a "
                             "partial bill" % (missing, len(run.calls)))
    refusal = _axis_refusal(run, "E2")
    if refusal is not None:
        return refusal
    costs = _turn_costs(run)
    total = sum(costs)
    if total <= 0:
        return thin("E2", "total cost is zero")
    if len(costs) < MIN_TURNS_FOR_SHAPE:
        return thin("E2", "fewer than %d turns; a short run is trivially "
                          "front-loaded" % MIN_TURNS_FOR_SHAPE)
    head = _cost_through(costs, len(costs) * FRONTLOAD_K)
    return ok("E2", head / total, turns=len(costs),
              head_turns=round(len(costs) * FRONTLOAD_K, 9),
              billed_calls=len(run.calls))


@metric("E3", "economy",
        "Fraction of the run's turns needed to reach 90% of its total cost. "
        "Low means the bill settled early.",
        needs=("model_calls", "cost"), direction="lower", unit="share")
def convergence_point(run: Run):
    missing = _unpriced(run)
    if missing:
        return unsound("E3", "%d of %d model calls carry no price; the "
                             "shape of a bill cannot be read from a "
                             "partial bill" % (missing, len(run.calls)))
    refusal = _axis_refusal(run, "E3")
    if refusal is not None:
        return refusal
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
    missing = _unpriced(run)
    if missing:
        return unsound("E5", "%d of %d model calls carry no price, and an "
                             "unpriced call is not a free one"
                             % (missing, len(run.calls)))
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
