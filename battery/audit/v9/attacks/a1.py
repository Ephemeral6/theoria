"""v9 red-team attacks against the exploration family (X1..X6).

Every builder is a zero-argument function that only *lays out data*: list
comprehensions, %-formatting and the battery.model constructors. No search,
no computation, no external input.
"""

from battery.audit.v9.attack import Attack
from battery.model import Run, Step, Call, Concept, Clause, Theory, Beat, Repair, Truth


# ---------------------------------------------------------------- X1 -------
# X1 = 1 - distinct(state_key) / observed. direction lower, target <= 0.05.
# state_key is a *label the arm supplies*. Nothing cross-checks it.

def build_X1_fresh_labels():
    """Never revisit anything -- because every label is minted fresh."""
    return Run(run_id="v9-X1-fresh-labels", arm="attacker", source="v9",
               steps=[Step(idx=i, action="press", state_key="s%d" % i)
                      for i in range(300)])


def build_X1_counter_in_key():
    """The realistic version: one frozen board, but the key carries a tick."""
    return Run(run_id="v9-X1-counter-in-key", arm="attacker", source="v9",
               steps=[Step(idx=i, action="press",
                           state_key="board=deadbeef|tick=%d" % i)
                      for i in range(300)])


def build_X1_early_exit():
    """Two observed steps is enough to clear the 'fewer than two' guard."""
    return Run(run_id="v9-X1-early-exit", arm="attacker", source="v9",
               steps=[Step(idx=0, action="reset", state_key="a"),
                      Step(idx=1, action="reset", state_key="b")])


def attack_X1_fresh_labels():
    return Attack(
        metric_id="X1", name="fresh-labels",
        build=build_X1_fresh_labels,
        claim="X1 = 0.0 over 300 steps that press one button and relabel the screen each time",
        accidental=False,
        rationale=("Minting a brand-new label every step is a deliberate choice here, "
                   "but it costs nothing: the metric consumes the arm's own naming of "
                   "state and has no way to notice 300 identical presses."),
    )


def attack_X1_counter_in_key():
    return Attack(
        metric_id="X1", name="counter-in-key",
        build=build_X1_counter_in_key,
        claim="X1 = 0.0 while the board hash is literally constant across all 300 steps",
        accidental=True,
        rationale=("Harnesses routinely build a state key by serialising the whole "
                   "observation record, and observation records routinely carry a step "
                   "index, frame counter or timestamp. One such field makes every state "
                   "unique and drives X1 to 0 with no exploration whatsoever."),
    )


def attack_X1_early_exit():
    return Attack(
        metric_id="X1", name="early-exit",
        build=build_X1_early_exit,
        claim="X1 = 0.0 from a two-step run that crashed before doing anything",
        accidental=True,
        rationale=("A run that dies after two steps clears the len(seen) < 2 guard by "
                   "exactly one step and then scores perfectly; crash-early runs are the "
                   "most common junk record in any batch harness."),
    )


# ---------------------------------------------------------------- X2 -------
# X2 = novel / total over keys "prev_state|action". direction higher, >= 0.95.
# Both halves of the key are arm-supplied, so making them unique is free.

def build_X2_fresh_states():
    """One action forever; the state label alone keeps every transition 'new'."""
    return Run(run_id="v9-X2-fresh-states", arm="attacker", source="v9",
               steps=[Step(idx=i, action="press", state_key="s%d" % i)
                      for i in range(300)])


def build_X2_fresh_actions():
    """Mirror image: one frozen state, a fresh action name every step."""
    return Run(run_id="v9-X2-fresh-actions", arm="attacker", source="v9",
               steps=[Step(idx=i, action="ACTION%d" % i, state_key="hub")
                      for i in range(300)])


def build_X2_failed_curtain():
    """failed steps are skipped by _transition_keys but keep updating `previous`.

    Only three non-failed steps survive into the key list, so the denominator
    is 3 and every arm-chosen action is trivially first-seen.
    """
    return Run(run_id="v9-X2-failed-curtain", arm="attacker", source="v9",
               steps=[Step(idx=i, action="spam", state_key="hub", failed=True)
                      for i in range(297)]
                     + [Step(idx=297 + i, action="late%d" % i, state_key="z%d" % i)
                        for i in range(3)])


def attack_X2_fresh_states():
    return Attack(
        metric_id="X2", name="fresh-states",
        build=build_X2_fresh_states,
        claim="X2 = 1.0 on 300 repetitions of a single action",
        accidental=True,
        rationale=("The key is prev_state|action and only one of the two halves has to "
                   "vary. Any harness whose state key is even slightly noisy -- a frame "
                   "counter, an animation phase, an RNG seed echoed in the observation -- "
                   "gets X2 = 1.0 while pressing the same button forever."),
    )


def attack_X2_fresh_actions():
    return Attack(
        metric_id="X2", name="fresh-actions",
        build=build_X2_fresh_actions,
        claim="X2 = 1.0 from a single frozen state and 300 never-repeated action names",
        accidental=True,
        rationale=("Agents that emit parameterised actions (click at x,y; type <string>) "
                   "almost never repeat an action string verbatim, so the transition set "
                   "is novel by construction even when the world does not move."),
    )


def attack_X2_failed_curtain():
    return Attack(
        metric_id="X2", name="failed-curtain",
        build=build_X2_failed_curtain,
        claim="X2 = 1.0 on a 300-step run of which 297 steps were rejected spam",
        accidental=True,
        rationale=("_transition_keys drops failed steps entirely, so a run that spent 99% "
                   "of its budget being refused is scored only on the three steps that "
                   "landed -- an arm that mostly fails looks maximally exploratory."),
    )


# ---------------------------------------------------------------- X3 -------
# X3 = novelty(first quarter) - novelty(last quarter). higher, >= 0.9.
# Maximised by exploring first and then jamming -- the shape it should punish.

def build_X3_explore_then_jam():
    """Fresh labels for 20 steps, then 20 steps of one action on one state."""
    return Run(run_id="v9-X3-explore-then-jam", arm="attacker", source="v9",
               steps=[Step(idx=i, action="a%d" % i, state_key="s%d" % i)
                      for i in range(20)]
                     + [Step(idx=20 + i, action="loop", state_key="hub")
                        for i in range(20)])


def build_X3_minimum_length():
    """Eight transitions -- exactly the guard -- still yields 1.0."""
    return Run(run_id="v9-X3-minimum-length", arm="attacker", source="v9",
               steps=[Step(idx=i, action="a%d" % i, state_key="s%d" % i)
                      for i in range(4)]
                     + [Step(idx=4 + i, action="loop", state_key="hub")
                        for i in range(4)])


def attack_X3_explore_then_jam():
    return Attack(
        metric_id="X3", name="explore-then-jam",
        build=build_X3_explore_then_jam,
        claim="X3 = 1.0 for a run that dies in an infinite loop over its whole second half",
        accidental=True,
        rationale=("Explore-then-get-stuck is the single most common real trajectory "
                   "shape, and X3 pays it the maximum score: the metric rewards the last "
                   "quarter being *empty* of novelty, which is exactly what being stuck "
                   "looks like. This is an inversion, not just a fill."),
    )


def attack_X3_minimum_length():
    return Attack(
        metric_id="X3", name="minimum-length",
        build=build_X3_minimum_length,
        claim="X3 = 1.0 from eight steps, the smallest run the guard admits",
        accidental=True,
        rationale=("quarter = len(keys)//4 = 2 here, so the whole statistic rests on four "
                   "transitions; short truncated runs land on the extreme values of X3 "
                   "constantly and there is no sample-size floor beyond eight."),
    )


# ---------------------------------------------------------------- X4 -------
# X4 = longest consecutive-repeat streak / observed. lower, <= 0.05.
# The denominator is the arm's own step count, so the stall can be diluted.

def build_X4_no_streak():
    """Distinct labels everywhere: the streak counter never leaves zero."""
    return Run(run_id="v9-X4-no-streak", arm="attacker", source="v9",
               steps=[Step(idx=i, action="press", state_key="s%d" % i)
                      for i in range(300)])


def build_X4_dilute_the_stall():
    """A genuine 50-step stall, hidden under 1200 cheap unique steps."""
    return Run(run_id="v9-X4-dilute-the-stall", arm="attacker", source="v9",
               steps=[Step(idx=i, action="scan", state_key="s%d" % i)
                      for i in range(1200)]
                     + [Step(idx=1200 + i, action="stuck", state_key="s0")
                        for i in range(50)])


def build_X4_sawtooth():
    """Alternate a new label with an old one: every streak is length 1."""
    return Run(run_id="v9-X4-sawtooth", arm="attacker", source="v9",
               steps=[Step(idx=2 * i + j, action="probe",
                           state_key=["new%d" % i, "home"][j])
                      for i in range(150) for j in range(2)])


def attack_X4_no_streak():
    return Attack(
        metric_id="X4", name="no-streak",
        build=build_X4_no_streak,
        claim="X4 = 0.0 on 300 identical presses relabelled as 300 states",
        accidental=True,
        rationale=("Same mechanism as X1: X4 reads the arm's own state labels, so any "
                   "monotone field in the observation record (tick, frame, score, elapsed "
                   "ms) makes the no-progress streak structurally unreachable."),
    )


def attack_X4_dilute_the_stall():
    return Attack(
        metric_id="X4", name="dilute-the-stall",
        build=build_X4_dilute_the_stall,
        claim="X4 = 0.04 for a run that ends in a real 50-step dead stall",
        accidental=True,
        rationale=("The streak is normalised by run length, so cheap high-volume stepping "
                   "buys immunity: a harness that batches many micro-actions per decision "
                   "inflates the denominator without inflating the stall."),
    )


def attack_X4_sawtooth():
    return Attack(
        metric_id="X4", name="sawtooth",
        build=build_X4_sawtooth,
        claim="X4 = 0.003... while the arm bounces between one hub and one-shot side states",
        accidental=True,
        rationale=("`current = 0` resets on *any* new label, so a single novel state "
                   "between repeats truncates the streak. Agents that return to a menu or "
                   "home screen between probes produce exactly this sawtooth."),
    )


# ---------------------------------------------------------------- X5 -------
# X5 = |distinct state_key|. neutral -> success is controllability.

def build_X5_high():
    return Run(run_id="v9-X5-high", arm="attacker", source="v9",
               steps=[Step(idx=i, action="press", state_key="s%d" % i)
                      for i in range(500)])


def build_X5_low():
    return Run(run_id="v9-X5-low", arm="attacker", source="v9",
               steps=[Step(idx=i, action="press", state_key="hub")
                      for i in range(500)])


def attack_X5_label_dial():
    return Attack(
        metric_id="X5", name="label-dial",
        build=build_X5_high,
        build_low=build_X5_low,
        claim="X5 = 500 vs 1 from two runs that take the identical 500 actions",
        accidental=True,
        rationale=("The two runs differ only in the naming convention of state_key, not in "
                   "behaviour; whether a harness hashes the raw frame or a canonicalised "
                   "one swings this diagnostic by 500x with no change to the agent."),
        benign_window=("X5 is harmless only as a floor check -- 'this run saw more than a "
                       "handful of distinct states' -- and only when state_key is a hash of "
                       "a canonicalised environment frame produced by the harness, never by "
                       "the arm."),
    )


# ---------------------------------------------------------------- X6 -------
# X6 = (failed steps whose successor action differs) / (failed steps with a
# successor). higher, >= 0.95. Nothing checks the *new* action is informed.

def build_X6_round_robin():
    """Every step fails; the arm cycles action names blind and scores 1.0."""
    return Run(run_id="v9-X6-round-robin", arm="attacker", source="v9",
               steps=[Step(idx=i, action="a%d" % i, state_key=None, failed=True)
                      for i in range(200)])


def build_X6_two_stroke():
    """A hard-coded ABABAB oscillation: no reading, still a perfect score."""
    return Run(run_id="v9-X6-two-stroke", arm="attacker", source="v9",
               steps=[Step(idx=2 * i + j, action=["A", "B"][j],
                           state_key=None, failed=True)
                      for i in range(100) for j in range(2)])


def build_X6_single_window():
    """One failure in 400 steps -> the denominator is 1."""
    return Run(run_id="v9-X6-single-window", arm="attacker", source="v9",
               steps=[Step(idx=0, action="probe", state_key="s0", failed=True),
                      Step(idx=1, action="other", state_key="s1")]
                     + [Step(idx=2 + i, action="grind", state_key="hub")
                        for i in range(398)])


def build_X6_family_sweep():
    """One run that clears X1, X2, X4, X5 and X6 at once.

    Distinct labels everywhere (X1/X4/X5), one action name per step so every
    transition key is new (X2), and every tenth step flagged failed with a
    different successor action (X6).
    """
    return Run(run_id="v9-X6-family-sweep", arm="attacker", source="v9",
               steps=[Step(idx=i, action="a%d" % i, state_key="s%d" % i,
                           failed=[False, True][[0, 1][i % 10 == 0]])
                      for i in range(300)])


def attack_X6_family_sweep():
    return Attack(
        metric_id="X6", name="family-sweep",
        build=build_X6_family_sweep,
        claim="one poverty-certified run clears the X1/X2/X4/X6 thresholds simultaneously",
        accidental=False,
        rationale=("Deliberately constructed, but it shows the family shares a single point "
                   "of failure rather than four: all of X1, X2, X4 and X6 read only "
                   "arm-supplied strings, so one relabelling convention satisfies all of "
                   "them at once and the four metrics are not independent evidence."),
    )


def attack_X6_round_robin():
    return Attack(
        metric_id="X6", name="round-robin",
        build=build_X6_round_robin,
        claim="X6 = 1.0 on 200 consecutive failures with a fresh action name each time",
        accidental=True,
        rationale=("A scripted sweep over an action list -- the standard fallback when an "
                   "agent has no idea what to do -- changes action after every refusal by "
                   "construction, so the least adaptive possible policy maxes the metric."),
    )


def attack_X6_two_stroke():
    return Attack(
        metric_id="X6", name="two-stroke",
        build=build_X6_two_stroke,
        claim="X6 = 1.0 from a two-symbol ABAB oscillation that ignores every refusal",
        accidental=True,
        rationale=("X6 only compares consecutive action strings for inequality; a period-2 "
                   "loop satisfies that on every window while demonstrably learning "
                   "nothing, since it re-issues the refused action two steps later."),
    )


def attack_X6_single_window():
    return Attack(
        metric_id="X6", name="single-window",
        build=build_X6_single_window,
        claim="X6 = 1.0 decided by exactly one of 400 steps",
        accidental=True,
        rationale=("The `windows == 0` guard is the only sample floor, so one lucky failure "
                   "early in a long run fixes the metric at 1.0; near-flawless runs with a "
                   "single stumble are common and will be scored on that stumble alone."),
    )
