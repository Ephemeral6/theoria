"""Exploration — is the arm covering the world, or circling in it?

`Theoria.md` names three: state revisit rate, the novel-transition fraction
curve, and the longest no-progress streak.

One deviation from the text, recorded rather than hidden: the streak is
reported as a **fraction of the run**, not a raw count. The runs in hand
differ in length by a factor of twenty, and a raw streak would rank a long run
above a short one for no reason but its length. `DECISIONS.md` D-B-002.
"""

from __future__ import annotations

from typing import List, Optional

from battery.metrics import metric, ok, thin
from battery.model import Run, Step

START = "<start>"


def _observed(run: Run) -> List[Step]:
    return [s for s in run.steps if s.state_key]


def _transition_keys(run: Run) -> List[str]:
    """(state before, action) for each step whose predecessor is known."""
    keys: List[str] = []
    previous: Optional[str] = START
    for step in run.steps:
        if step.failed:
            # A failed step never reached the environment, so it names no
            # transition; the state it would have left from is still current.
            continue
        if previous is not None:
            keys.append("%s|%s" % (previous, step.action))
        previous = step.state_key
    return keys


@metric("X1", "exploration",
        "Fraction of observed states that had been visited before.",
        needs=("steps", "observations"), direction="lower")
def state_revisit_rate(run: Run):
    seen = [s.state_key for s in _observed(run)]
    if len(seen) < 2:
        return thin("X1", "fewer than two observed states")
    return ok("X1", 1.0 - len(set(seen)) / len(seen),
              observed=len(seen), distinct=len(set(seen)))


@metric("X2", "exploration",
        "Fraction of (state, action) transitions taken for the first time.",
        needs=("steps", "observations"), direction="higher")
def novel_transition_rate(run: Run):
    keys = _transition_keys(run)
    if len(keys) < 2:
        return thin("X2", "fewer than two transitions")
    seen = set()
    novel = 0
    for key in keys:
        if key not in seen:
            novel += 1
            seen.add(key)
    return ok("X2", novel / len(keys), transitions=len(keys), novel=novel)


@metric("X3", "exploration",
        "Novelty in the first quarter of a run minus novelty in the last "
        "quarter; the curve's shape as one number.",
        needs=("steps", "observations"), direction="higher")
def novelty_frontload(run: Run):
    """The signature of a theory that closes.

    An arm that builds a model should be surprised early and unsurprised late.
    A flat novelty curve is an arm that is still discovering the world on its
    last turn — which is what "the theory never closed" looks like from
    outside.
    """
    keys = _transition_keys(run)
    if len(keys) < 8:
        return thin("X3", "fewer than eight transitions; quartiles meaningless")
    quarter = len(keys) // 4
    seen = set()
    flags: List[int] = []
    for key in keys:
        flags.append(0 if key in seen else 1)
        seen.add(key)
    first = sum(flags[:quarter]) / quarter
    last = sum(flags[-quarter:]) / quarter
    return ok("X3", first - last, first_quarter=round(first, 6),
              last_quarter=round(last, 6), transitions=len(keys))


@metric("X4", "exploration",
        "Longest run of consecutive steps discovering no new state, as a "
        "fraction of the run's length.",
        needs=("steps", "observations"), direction="lower")
def max_no_progress_streak(run: Run):
    steps = _observed(run)
    if len(steps) < 2:
        return thin("X4", "fewer than two observed states")
    seen = set()
    longest = 0
    current = 0
    for step in steps:
        if step.state_key in seen:
            current += 1
            longest = max(longest, current)
        else:
            seen.add(step.state_key)
            current = 0
    return ok("X4", longest / len(steps), longest_streak=longest,
              observed=len(steps))


@metric("X5", "exploration",
        "Distinct states observed. Support for X1/X4, not a ranking.",
        needs=("steps", "observations"), direction="neutral")
def distinct_states(run: Run):
    seen = {s.state_key for s in _observed(run)}
    if not seen:
        return thin("X5", "no observed states")
    return ok("X5", len(seen))


@metric("X6", "exploration",
        "Fraction of failed steps after which the arm chose a different "
        "action. Does the arm read its own refusals?",
        needs=("steps", "failed_steps"), direction="higher", unit="share")
def post_failure_action_change(run: Run):
    """What the degraded envelope run made measurable.

    Between a fifth and a half of the pilot's environment steps are refused
    outright -- HTTP 400 "game not found" and 500s -- and until now the battery
    treated that purely as a confound to be divided out (P5). It is also a
    *stimulus*: the environment just told the arm that this action, right now,
    does not work. An arm carrying any model of the interaction should try
    something else; an arm that re-decides from a fresh prompt every turn has
    no memory of the refusal and should repeat itself at roughly chance.

    Deliberately measured across the failure boundary only, and only where the
    next step exists. A run whose last step failed contributes no window,
    because "what did it do next" has no answer.

    The reading is not clean and the register says so: a harness that varies
    its action on retry would score 1.0 for reasons that have nothing to do
    with the arm. That is why this sits in the reference tier.
    """
    changed = 0
    windows = 0
    for i, step in enumerate(run.steps[:-1]):
        if not step.failed:
            continue
        windows += 1
        if run.steps[i + 1].action != step.action:
            changed += 1
    if windows == 0:
        return thin("X6", "no failed step is followed by another step")
    return ok("X6", changed / windows, changed=changed, windows=windows)
