"""v9 red-team attacks on P1, P2, P3, P4, P5, E6.

Every builder is zero-argument, deterministic, and lays out data only.
"""
from battery.audit.v9.attack import Attack
from battery.model import Run, Step, Call, Concept, Clause, Theory, Beat, Repair, Truth


# --------------------------------------------------------------------------
# P1 -- actions per model call, direction higher, target >= 50
# --------------------------------------------------------------------------

def build_P1_one_call_batch():
    """One model call; the environment log claims 5000 successful actions."""
    return Run(run_id="v9-P1-one-call-batch", arm="attacker", source="v9",
               steps=[Step(idx=i, action="a%d" % i, state_key="s%d" % i)
                      for i in range(5000)],
               calls=[Call(idx=0, input_tokens=10, output_tokens=10)])


def attack_P1_one_call_batch():
    return Attack(
        metric_id="P1", name="one-call-batch",
        build=build_P1_one_call_batch,
        claim="P1 = 5000.0 from a single model call that emits one batched macro",
        accidental=True,
        rationale=("Any harness that lets the model emit a list of actions per turn, "
                   "or that replays a recorded macro after one prompt, produces exactly "
                   "this shape without anyone trying to game it."),
    )


def build_P1_noop_saturation():
    """Four calls, 400 no-op steps: same action, same state, never fails."""
    return Run(run_id="v9-P1-noop-saturation", arm="attacker", source="v9",
               steps=[Step(idx=i, action="wait", state_key="idle")
                      for i in range(400)],
               calls=[Call(idx=i, input_tokens=5, output_tokens=5) for i in range(4)])


def attack_P1_noop_saturation():
    return Attack(
        metric_id="P1", name="noop-saturation",
        build=build_P1_noop_saturation,
        claim="P1 = 100.0 while every action is the identical no-op leaving state unchanged",
        accidental=True,
        rationale=("A polling/keep-alive loop or a stuck controller that re-issues the same "
                   "action until a timeout logs hundreds of non-failing steps against a "
                   "handful of prompts; nothing in P1 asks whether the state moved."),
    )


def build_P1_failure_free_by_omission():
    """The steps that failed were never logged; only the survivors are."""
    return Run(run_id="v9-P1-failure-free-by-omission", arm="attacker", source="v9",
               steps=[Step(idx=i, action="move", state_key="s%d" % (i % 7), failed=False)
                      for i in range(300)],
               calls=[Call(idx=i, input_tokens=100, output_tokens=20, is_error=True)
                      for i in range(5)])


def attack_P1_failure_free_by_omission():
    return Attack(
        metric_id="P1", name="failure-free-by-omission",
        build=build_P1_failure_free_by_omission,
        claim="P1 = 60.0 even though every model call is marked is_error=True",
        accidental=True,
        rationale=("P1 counts len(run.calls), not successful calls, and counts steps the "
                   "logger chose to write; a harness that drops rejected actions before "
                   "logging turns a broken run into a high score by omission alone."),
    )


# --------------------------------------------------------------------------
# P2 -- actions/call second half minus first half, direction higher, target >= 10
# --------------------------------------------------------------------------

def build_P2_boundary_lie():
    """All calls carry step_idx, and the midpoint call claims step_idx=0."""
    return Run(run_id="v9-P2-boundary-lie", arm="attacker", source="v9",
               steps=[Step(idx=i, action="a%d" % i, state_key="s%d" % i)
                      for i in range(400)],
               calls=[Call(idx=0, step_idx=0), Call(idx=1, step_idx=0),
                      Call(idx=2, step_idx=0), Call(idx=3, step_idx=0)])


def attack_P2_boundary_lie():
    return Attack(
        metric_id="P2", name="boundary-lie",
        build=build_P2_boundary_lie,
        claim="P2 = 200.0 because the half-way boundary is read off a self-reported step_idx",
        accidental=True,
        rationale=("Harnesses commonly stamp step_idx as 'the step this call was made "
                   "before', so every planning call in a plan-then-execute agent legitimately "
                   "carries step_idx=0; that alone puts the whole run in the second half."),
    )


def build_P2_late_success():
    """Honest tie: four calls on steps 0..3, early steps fail, late steps succeed."""
    return Run(run_id="v9-P2-late-success", arm="attacker", source="v9",
               steps=[Step(idx=i, action="probe%d" % i, state_key="s%d" % i, failed=True)
                      for i in range(4)] +
                     [Step(idx=i, action="exec%d" % i, state_key="t%d" % i)
                      for i in range(4, 204)],
               calls=[Call(idx=i, step_idx=i) for i in range(4)])


def attack_P2_late_success():
    return Attack(
        metric_id="P2", name="late-success",
        build=build_P2_late_success,
        claim="P2 = 100.0 from four honestly-tied calls, all of them made in the first four steps",
        accidental=True,
        rationale=("If the model is only consulted while it is failing and the harness then "
                   "runs an unattended scripted tail, every successful step lands after the "
                   "boundary; no lie about step_idx is needed, only that calls stop early."),
    )


def build_P2_proportional_floor():
    """The other branch: no call carries step_idx, so the split is proportional."""
    return Run(run_id="v9-P2-proportional-floor", arm="attacker", source="v9",
               steps=[Step(idx=i, action="a%d" % i, state_key="s%d" % i)
                      for i in range(999)],
               calls=[Call(idx=i) for i in range(5)])


def attack_P2_proportional_floor():
    return Attack(
        metric_id="P2", name="proportional-floor",
        build=build_P2_proportional_floor,
        claim="P2 stays near zero on the proportional branch no matter how many steps are laid out",
        accidental=False,
        rationale=("This is a deliberate probe of the fallback branch rather than a score "
                   "attack; the proportional split defines first/second from the same "
                   "constant rate, so only integer-floor slack (bounded well under 1) leaks."),
    )


# --------------------------------------------------------------------------
# P3 -- backtrack rate, direction lower, target <= 0.05
# --------------------------------------------------------------------------

def build_P3_counter_keys():
    """Same action forever; the state key carries a counter, so no key repeats."""
    return Run(run_id="v9-P3-counter-keys", arm="attacker", source="v9",
               steps=[Step(idx=i, action="wait", state_key="tick-%d" % i)
                      for i in range(500)])


def attack_P3_counter_keys():
    return Attack(
        metric_id="P3", name="counter-keys",
        build=build_P3_counter_keys,
        claim="P3 = 0.0 while the agent repeats one no-op action 500 times",
        accidental=True,
        rationale=("State keys are routinely hashed from a frame that embeds a step counter, "
                   "score, or timestamp; any such key makes every state unique and P3 "
                   "identically zero for free."),
    )


def build_P3_three_cycle():
    """A pure loop -- but of period three, which the two-step window cannot see."""
    return Run(run_id="v9-P3-three-cycle", arm="attacker", source="v9",
               steps=[Step(idx=i, action=["left", "right", "up"][i % 3],
                           state_key=["A", "B", "C"][i % 3])
                      for i in range(300)])


def attack_P3_three_cycle():
    return Attack(
        metric_id="P3", name="three-cycle",
        build=build_P3_three_cycle,
        claim="P3 = 0.0 on a run that cycles A->B->C->A forever and makes no progress",
        accidental=True,
        rationale=("The window compares keys[i+1] with keys[i-1], so it only detects "
                   "period-2 oscillation; a stuck agent whose loop has any other period "
                   "scores a perfect zero, and three-move loops are common in grid worlds."),
    )


def build_P3_sparse_observations():
    """Only three successful steps survive; two of them carry distinct keys."""
    return Run(run_id="v9-P3-sparse-observations", arm="attacker", source="v9",
               steps=[Step(idx=0, action="start", state_key="s0"),
                      Step(idx=1, action="go", state_key=None),
                      Step(idx=2, action="stop", state_key="s2"),
                      Step(idx=3, action="crash", state_key="s3", failed=True)])


def attack_P3_sparse_observations():
    return Attack(
        metric_id="P3", name="sparse-observations",
        build=build_P3_sparse_observations,
        claim="P3 = 0.0 from a four-step run that dies immediately, on a single window",
        accidental=True,
        rationale=("A run that crashes after three steps clears the len(keys) >= 3 gate with "
                   "exactly one window and reports the best possible backtrack rate; early "
                   "termination is the single most common way real runs end."),
    )


# --------------------------------------------------------------------------
# P4 -- actual steps / optimal plan, direction lower, target <= 1
# --------------------------------------------------------------------------

def build_P4_inflated_optimal():
    """The run supplies its own ground truth: a 1000-step 'shortest known plan'."""
    return Run(run_id="v9-P4-inflated-optimal", arm="attacker", source="v9",
               intent="solve",
               truth=Truth(optimal_steps=1000, levels=1),
               steps=[Step(idx=0, action="win", state_key="goal", won=True)])


def attack_P4_inflated_optimal():
    return Attack(
        metric_id="P4", name="inflated-optimal",
        build=build_P4_inflated_optimal,
        claim="P4 = 0.001 because the denominator is read from the run's own Truth record",
        accidental=False,
        rationale=("No harness accidentally writes optimal_steps=1000 for a one-step win; "
                   "this is a pure trust attack showing P4's 'ground truth' is run-supplied "
                   "and unverified by the metric."),
    )


def build_P4_failed_steps_are_free():
    """Ten thousand failed attempts and one win: only the win is divided."""
    return Run(run_id="v9-P4-failed-steps-are-free", arm="attacker", source="v9",
               intent="solve",
               truth=Truth(optimal_steps=20),
               steps=[Step(idx=i, action="try%d" % i, state_key="s%d" % i, failed=True)
                      for i in range(10000)] +
                     [Step(idx=10000, action="win", state_key="goal", won=True)])


def attack_P4_failed_steps_are_free():
    return Attack(
        metric_id="P4", name="failed-steps-are-free",
        build=build_P4_failed_steps_are_free,
        claim="P4 = 0.05 after 10000 failed actions, against an honest optimal of 20",
        accidental=True,
        rationale=("P4 divides len(run.ok_steps) by optimal, so any action the environment "
                   "rejects is free; a brute-force agent whose illegal moves bounce off the "
                   "rules looks more efficient than optimal without deceiving anyone."),
    )


def build_P4_won_but_failed():
    """The winning step is itself marked failed, so the numerator is zero."""
    return Run(run_id="v9-P4-won-but-failed", arm="attacker", source="v9",
               intent="solve",
               truth=Truth(optimal_steps=12),
               steps=[Step(idx=0, action="terminal", state_key="goal",
                           failed=True, won=True)])


def attack_P4_won_but_failed():
    return Attack(
        metric_id="P4", name="won-but-failed",
        build=build_P4_won_but_failed,
        claim="P4 = 0.0 -- a perfect-and-then-some score from zero successful actions",
        accidental=True,
        rationale=("won and failed are independent flags on Step, and a terminal transition "
                   "that both wins and errors (win detected on a call the harness marks "
                   "failed, e.g. a timeout on the final ACK) empties ok_steps entirely."),
    )


# --------------------------------------------------------------------------
# P5 -- step failure rate, neutral, controllability
# --------------------------------------------------------------------------

def build_P5_all_failed():
    return Run(run_id="v9-P5-all-failed", arm="attacker", source="v9",
               steps=[Step(idx=i, action="a%d" % i, state_key="s%d" % i, failed=True)
                      for i in range(200)])


def build_P5_none_failed():
    return Run(run_id="v9-P5-none-failed", arm="attacker", source="v9",
               steps=[Step(idx=i, action="a%d" % i, state_key="s%d" % i,
                           failed=(i == 0))
                      for i in range(200)])


def attack_P5_flag_only():
    return Attack(
        metric_id="P5", name="flag-only",
        build=build_P5_all_failed,
        build_low=build_P5_none_failed,
        claim="P5 = 1.0 vs 0.005 on runs with identical actions and identical state keys",
        accidental=True,
        rationale=("The two runs differ only in a boolean the logger sets; harnesses disagree "
                   "on whether a rejected action is a failed step or simply not a step, so "
                   "the same behaviour lands anywhere on this axis depending on the adapter."),
        benign_window=("Harmless only if P5 is read alongside a fixed, documented definition "
                       "of 'failed' from the same adapter; across adapters it ranks nothing."),
    )


# --------------------------------------------------------------------------
# E6 -- HTTP tries per step, neutral, controllability
# --------------------------------------------------------------------------

def build_E6_high_retry():
    return Run(run_id="v9-E6-high-retry", arm="attacker", source="v9",
               steps=[Step(idx=i, action="a%d" % i, state_key="s%d" % i, http_tries=500)
                      for i in range(100)])


def build_E6_low_retry():
    return Run(run_id="v9-E6-low-retry", arm="attacker", source="v9",
               steps=[Step(idx=i, action="a%d" % i, state_key="s%d" % i, http_tries=1)
                      for i in range(100)])


def attack_E6_retry_dial():
    return Attack(
        metric_id="E6", name="retry-dial",
        build=build_E6_high_retry,
        build_low=build_E6_low_retry,
        claim="E6 = 500.0 vs 1.0 on runs whose agent behaviour is byte-identical",
        accidental=True,
        rationale=("http_tries is a property of the transport layer -- retry policy, backoff "
                   "config, a flaky proxy -- not of the agent; changing one client constant "
                   "moves E6 by orders of magnitude with no change in play."),
        benign_window=("Harmless only as a same-session infrastructure check: E6 near 1.0 "
                       "means the step log and the HTTP log agree; any other reading is "
                       "about the network, not the arm."),
    )


def build_E6_unlogged_majority():
    """Only one step of a thousand carries an http_tries count."""
    return Run(run_id="v9-E6-unlogged-majority", arm="attacker", source="v9",
               steps=[Step(idx=i, action="a%d" % i, state_key="s%d" % i)
                      for i in range(999)] +
                     [Step(idx=999, action="a999", state_key="s999", http_tries=3000)])


def build_E6_unlogged_majority_low():
    return Run(run_id="v9-E6-unlogged-majority-low", arm="attacker", source="v9",
               steps=[Step(idx=i, action="a%d" % i, state_key="s%d" % i)
                      for i in range(999)] +
                     [Step(idx=999, action="a999", state_key="s999", http_tries=2)])


def attack_E6_partial_logging():
    return Attack(
        metric_id="E6", name="partial-logging",
        build=build_E6_unlogged_majority,
        build_low=build_E6_unlogged_majority_low,
        claim="E6 = 3000.0 vs 2.0 from a single annotated step out of a thousand",
        accidental=True,
        rationale=("The mean is taken over steps that carry the field, not over all steps, so "
                   "a partially-instrumented adapter reports the retry behaviour of whichever "
                   "steps happened to be instrumented and calls it the run's mean."),
        benign_window=("Only trustworthy when support['steps'] equals the run's total step "
                       "count; otherwise it is a sample of unknown provenance."),
    )
