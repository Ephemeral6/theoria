"""Planning — is a decision buying more actions over time, and how many of
those actions were wasted?

`Theoria.md` names three: actions per model call (over time), backtrack rate
(returning to a state within two steps), and the solution redundancy ratio
(actual steps / shortest, which needs ground truth and is therefore capped to
the development pile and to self-built worlds).

P2 is the one to watch. P1 can be high because an arm is reckless — it acts a
lot between thoughts. P2 asks whether it is getting *better* at that as the
run goes on, which is the shape a closing theory should produce and reckless
batching should not.
"""

from __future__ import annotations

from battery.metrics import metric, ok, thin
from battery.model import Run


@metric("P1", "planning",
        "Successful environment actions per model call.",
        needs=("steps", "model_calls"), direction="higher",
        unit="actions/call")
def actions_per_model_call(run: Run):
    calls = len(run.calls)
    actions = len(run.ok_steps)
    if calls == 0:
        return thin("P1", "no model calls")
    return ok("P1", actions / calls, actions=actions, calls=calls)


@metric("P2", "planning",
        "Actions per model call in the run's second half minus the first "
        "half; is a decision buying more actions as the run goes on?",
        needs=("steps", "model_calls"), direction="higher",
        unit="actions/call")
def actions_per_call_trend(run: Run):
    calls = sorted(run.calls, key=lambda c: c.idx)
    if len(calls) < 4:
        return thin("P2", "fewer than four model calls; no trend to fit")
    ok_steps = run.ok_steps
    if not ok_steps:
        return thin("P2", "no successful actions")

    midpoint = len(calls) // 2
    # Split the actions by the call that decided them where the ledger says so,
    # and by proportion otherwise. The fallback is stated in the support field
    # so a reader can tell which of the two produced the number.
    tied = [c for c in calls if c.step_idx is not None]
    if len(tied) == len(calls):
        boundary = calls[midpoint].step_idx
        first = sum(1 for s in ok_steps if s.idx < boundary)
        second = len(ok_steps) - first
        basis = "step_idx"
    else:
        first = len(ok_steps) * midpoint // len(calls)
        second = len(ok_steps) - first
        basis = "proportional"

    first_rate = first / midpoint if midpoint else 0.0
    second_half_calls = len(calls) - midpoint
    second_rate = second / second_half_calls if second_half_calls else 0.0
    return ok("P2", second_rate - first_rate, first_rate=round(first_rate, 6),
              second_rate=round(second_rate, 6), basis=basis)


@metric("P3", "planning",
        "Fraction of steps that returned to the state two steps earlier — an "
        "undo.",
        needs=("steps", "observations"), direction="lower")
def backtrack_rate(run: Run):
    keys = [s.state_key for s in run.steps if not s.failed]
    if len(keys) < 3:
        return thin("P3", "fewer than three successful steps")
    windows = 0
    undos = 0
    for i in range(1, len(keys) - 1):
        if keys[i - 1] is None or keys[i + 1] is None:
            continue
        windows += 1
        if keys[i + 1] == keys[i - 1]:
            undos += 1
    if windows == 0:
        return thin("P3", "no two-step window carries both observations")
    return ok("P3", undos / windows, undos=undos, windows=windows)


@metric("P5", "planning",
        "Fraction of environment steps that failed outright. A diagnostic: "
        "it is the confound P1 and P2 are most exposed to.",
        needs=("steps",), direction="neutral", unit="share")
def step_failure_rate(run: Run):
    """Surfaced as a metric, not left in a footnote.

    On the pilot ledger 27-45% of steps failed -- HTTP 500s and "game not
    found", which are properties of the API and the harness and of nothing
    else. P1 divides successful actions by model calls, so a run whose
    infrastructure failed more looks like a run that planned less. The
    ordering P1 finds across the model ladder is fully accounted for by this
    number, which is why P1 sits in the reference tier and why this sits
    beside it in the correlation matrix, where anyone reading the spectrum
    will meet it.
    """
    if not run.steps:
        return thin("P5", "no steps")
    failed = sum(1 for s in run.steps if s.failed)
    return ok("P5", failed / len(run.steps), failed=failed,
              steps=len(run.steps))


@metric("P4", "planning",
        "Actual successful steps divided by the shortest known plan, over runs "
        "that reached the goal. 1.0 is optimal; needs ground truth, so "
        "development pile and A0 only.",
        needs=("steps", "truth", "optimal", "solve_attempt", "won"),
        direction="lower", unit="ratio")
def solution_redundancy(run: Run):
    """Path efficiency, and it may only be asked of a run that got there.

    **1.0 is not a floor**, which made this metric monotone in failure until
    v2.1: one action against a twelve-step plan scores 0.083, better than any
    solved run can score, and `intent="solve"` is set for every ledgered run
    whatever the outcome. `battery/audit/exploits/` demonstrates it. Five real
    runs in `baseline-arms/ledger.jsonl` stopped at exactly ten cumulative
    failures and would have topped this table given ground truth.

    The `won` guard is the defence `gaming.py` had claimed since v0 —
    "restricted to solve attempts with ground truth" — which turned out to
    restrict coverage walks and not failures. `Step.won` was populated by every
    adapter and read by nothing.

    The cost is real and was accepted in advance: P4 is now unscoreable on
    every losing run, which on current material makes it a one-value metric
    behind two guards. A metric that rewards giving up is worse.
    """
    optimal = run.truth.optimal_steps
    actions = len(run.ok_steps)
    if not optimal:
        return thin("P4", "no optimal plan length")
    return ok("P4", actions / optimal, actions=actions, optimal=optimal,
              won=True)
