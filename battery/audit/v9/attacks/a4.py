"""Red-team attacks on the mechanism family (M1-M6).

Every builder is zero-argument, deterministic, lays out data only.
"""
from battery.audit.v9.attack import Attack
from battery.model import Run, Step, Call, Concept, Clause, Theory, Beat, Repair, Truth


# --------------------------------------------------------------------------
# M1 -- mean first-use delay, lower is better, target <= 0.001
# --------------------------------------------------------------------------

def build_M1_same_step():
    """One mechanism, annotated as used on the very step it became visible."""
    return Run(run_id="v9-M1-same-step", arm="attacker", source="v9",
               steps=[Step(idx=i, action="a%d" % i, state_key="s%d" % i)
                      for i in range(3)],
               truth=Truth(mechanisms={"gravity": {"first_seen": 7, "first_used": 7}}))


def attack_M1_same_step():
    return Attack(
        metric_id="M1", name="same-step",
        build=build_M1_same_step,
        claim="M1 = 0.0 from a single hand-written annotation; the run has 3 steps and no mechanism use in them",
        accidental=False,
        rationale=("The metric reads only run.truth.mechanisms and never cross-checks the "
                   "step list, so the number is a property of the annotation file, not the run. "
                   "An annotator who writes first_used=first_seen because that is the step "
                   "where they noticed the mechanism produces this by convention, not by luck."),
    )


def build_M1_saturate():
    """Sixty mechanisms, each annotated used-on-sight. Mean of sixty zeros."""
    return Run(run_id="v9-M1-saturate", arm="attacker", source="v9",
               steps=[Step(idx=i, action="a%d" % i, state_key="s%d" % i)
                      for i in range(5)],
               truth=Truth(mechanisms={"m%02d" % i: {"first_seen": i, "first_used": i}
                                       for i in range(60)}))


def attack_M1_saturate():
    return Attack(
        metric_id="M1", name="saturate",
        build=build_M1_saturate,
        claim="M1 = 0.0 with a large n (used=60) so the support looks well-evidenced",
        accidental=False,
        rationale=("Structurally different from same-step: it attacks the support field rather "
                   "than the value. A reader who sanity-checks 'is this mean built on enough "
                   "mechanisms?' sees used=60 and is reassured by fabricated breadth."),
    )


def build_M1_precognition():
    """first_used strictly before first_seen -- the mean goes negative."""
    return Run(run_id="v9-M1-precognition", arm="attacker", source="v9",
               steps=[Step(idx=i, action="a%d" % i, state_key="s%d" % i)
                      for i in range(5)],
               truth=Truth(mechanisms={"m%02d" % i: {"first_seen": 1000, "first_used": 0}
                                       for i in range(20)}))


def attack_M1_precognition():
    return Attack(
        metric_id="M1", name="precognition",
        build=build_M1_precognition,
        claim="M1 = -1000.0; the metric accepts a delay that is physically impossible and ranks it best",
        accidental=True,
        rationale=("No clamp at zero and no ordering assertion. Any pipeline that resolves "
                   "first_seen from a level-entry event and first_used from an action log with "
                   "different index origins (0-based vs 1-based, or per-level vs global) will "
                   "emit negative delays silently."),
    )


def build_M1_survivorship():
    """One mechanism used at delay 0; ninety-nine annotated but never used."""
    return Run(run_id="v9-M1-survivorship", arm="attacker", source="v9",
               steps=[Step(idx=i, action="a%d" % i, state_key="s%d" % i)
                      for i in range(5)],
               truth=Truth(mechanisms={"m%02d" % i: {"first_seen": i,
                                                     "first_used": i if i == 0 else None}
                                       for i in range(100)}))


def attack_M1_survivorship():
    return Attack(
        metric_id="M1", name="survivorship",
        build=build_M1_survivorship,
        claim="M1 = 0.0 (perfect) on a run that used 1 of 100 mechanisms; M2 = 0.01 on the same run",
        accidental=True,
        rationale=("_delays() `continue`s past every mechanism with first_used None, so the mean "
                   "is conditioned on success. An arm that learns one easy mechanism instantly and "
                   "never grasps the other ninety-nine scores a perfect M1 with no intent to cheat; "
                   "this is the normal shape of a weak run, not a contrived one."),
    )


# --------------------------------------------------------------------------
# M2 -- mechanism uptake, higher is better, target >= 0.95
# --------------------------------------------------------------------------

def build_M2_single():
    """Annotate exactly one mechanism and mark it used. 1/1 = 1.0."""
    return Run(run_id="v9-M2-single", arm="attacker", source="v9",
               truth=Truth(mechanisms={"gravity": {"first_seen": 0, "first_used": 0}}))


def attack_M2_single():
    return Attack(
        metric_id="M2", name="single",
        build=build_M2_single,
        claim="M2 = 1.0 from a one-element denominator",
        accidental=True,
        rationale=("The denominator is len(mechanisms), which the run itself supplies. Any game "
                   "whose annotator only bothered to write down the one mechanism the arm "
                   "obviously used gets 1.0; sparse annotation and perfect uptake are the same "
                   "number here."),
    )


def build_M2_never_seen():
    """Two hundred mechanisms marked used, none of them ever marked seen."""
    return Run(run_id="v9-M2-never-seen", arm="attacker", source="v9",
               truth=Truth(mechanisms={"m%03d" % i: {"first_seen": None, "first_used": 0}
                                       for i in range(200)}))


def attack_M2_never_seen():
    return Attack(
        metric_id="M2", name="never-seen",
        build=build_M2_never_seen,
        claim="M2 = 1.0 over 200 mechanisms that the run never observed becoming visible",
        accidental=False,
        rationale=("M2 tests only `first_used is not None`; it does not require first_seen, does "
                   "not require the mechanism to appear in steps, and does not bound first_used "
                   "by the run length. Structurally different from `single`: it inflates the "
                   "numerator and denominator together rather than shrinking them."),
    )


def build_M2_zero_step_run():
    """A run with no steps and no calls at all still scores 1.0."""
    return Run(run_id="v9-M2-zero-step", arm="attacker", source="v9",
               intent="solve",
               truth=Truth(optimal_steps=None,
                           mechanisms={"m%02d" % i: {"first_seen": 0, "first_used": 0}
                                       for i in range(20)}))


def attack_M2_zero_step_run():
    return Attack(
        metric_id="M2", name="zero-step-run",
        build=build_M2_zero_step_run,
        claim="M2 = 1.0 on a run whose steps list is empty -- the arm never acted",
        accidental=True,
        rationale=("M2's `needs` are ('truth','mechanisms') only, so the metric never asks whether "
                   "the run has steps. A harness that crashes after writing its truth sidecar but "
                   "before flushing the trajectory produces exactly this record."),
    )


# --------------------------------------------------------------------------
# M3 -- cross-level first-use delay, lower is better, target <= 0.001
# (expected to be unattackable: the implementation is a stub)
# --------------------------------------------------------------------------

def build_M3_two_levels():
    """Steps spanning two levels plus fully annotated mechanisms."""
    return Run(run_id="v9-M3-two-levels", arm="attacker", source="v9",
               steps=[Step(idx=i, action="a%d" % i, state_key="s%d" % i,
                           level=0 if i < 10 else 1)
                      for i in range(20)],
               truth=Truth(levels=2,
                           mechanisms={"m%02d" % i: {"first_seen": i, "first_used": i,
                                                     "level": 0, "later_level": 1,
                                                     "cross_level_first_used": i}
                                       for i in range(12)}))


def attack_M3_two_levels():
    return Attack(
        metric_id="M3", name="two-levels",
        build=build_M3_two_levels,
        claim="M3 refuses: insufficient-data, value None, even with two levels and cross-level annotation",
        accidental=False,
        rationale=("Not an accident of my data -- the body has no ok() path at all. Reported as a "
                   "failed attack."),
    )


def build_M3_one_level():
    """The other branch: a single level."""
    return Run(run_id="v9-M3-one-level", arm="attacker", source="v9",
               steps=[Step(idx=i, action="a%d" % i, state_key="s%d" % i, level=0)
                      for i in range(20)],
               truth=Truth(levels=1,
                           mechanisms={"m00": {"first_seen": 0, "first_used": 0}}))


def attack_M3_one_level():
    return Attack(
        metric_id="M3", name="one-level",
        build=build_M3_one_level,
        claim="M3 refuses on the other branch too: insufficient-data, value None",
        accidental=False,
        rationale=("Both branches of the function terminate in thin(); confirms the stub rather "
                   "than a data problem on my side."),
    )


# --------------------------------------------------------------------------
# M4 -- change-detection delay, lower is better, target <= 0.001
# --------------------------------------------------------------------------

def build_M4_instant():
    """One repair episode that claims it noticed the change after zero actions."""
    return Run(run_id="v9-M4-instant", arm="attacker", source="v9",
               repairs=[Repair(episode_id="ep01", trigger="rule-change",
                               changed_clause="c1", detected=True,
                               detection_actions=0, theorems_before=4,
                               invalidated_theorems=1)])


def attack_M4_instant():
    return Attack(
        metric_id="M4", name="instant",
        build=build_M4_instant,
        claim="M4 = 0.0 from one self-reported detection_actions=0",
        accidental=True,
        rationale=("detection_actions is a self-report by the arm being scored, and 0 is the "
                   "natural value when a harness initialises the counter and the detection is "
                   "recognised on the same tick it is logged, i.e. an off-by-one in the "
                   "instrumentation, not a lie."),
    )


def build_M4_blind_but_instant():
    """Forty episodes, every one undetected, every one carrying earliest_detection=0."""
    return Run(run_id="v9-M4-blind-but-instant", arm="attacker", source="v9",
               repairs=[Repair(episode_id="ep%02d" % i, trigger="rule-change",
                               detected=False, detection_actions=None,
                               theorems_before=3, invalidated_theorems=0,
                               notes={"earliest_detection": 0})
                        for i in range(40)])


def attack_M4_blind_but_instant():
    return Attack(
        metric_id="M4", name="blind-but-instant",
        build=build_M4_blind_but_instant,
        claim="M4 = 0.0 while support says undetected_on_own_level=40 -- the manual noticed nothing, instantly",
        accidental=False,
        rationale=("notes['earliest_detection'] outranks the detected flag (it is read first and "
                   "detected is only a fallback), so a post-hoc 'when could it in principle have "
                   "known?' annotation overwrites the actual detection record. The contradiction "
                   "survives into the support dict, which is the tell."),
    )


def build_M4_negative():
    """Detection reported at a negative action count."""
    return Run(run_id="v9-M4-negative", arm="attacker", source="v9",
               repairs=[Repair(episode_id="ep%02d" % i, trigger="rule-change",
                               detected=True, detection_actions=-500,
                               theorems_before=2, invalidated_theorems=1)
                        for i in range(6)])


def attack_M4_negative():
    return Attack(
        metric_id="M4", name="negative",
        build=build_M4_negative,
        claim="M4 = -500.0; no lower bound, so 'better than instantaneous' is expressible",
        accidental=True,
        rationale=("The delay is a difference of two action indices somewhere upstream; if the "
                   "change-injection index and the detection index come from different counters "
                   "(pre-injection baseline vs post-injection episode), the subtraction goes "
                   "negative on its own."),
    )


# --------------------------------------------------------------------------
# M5 -- change-detection rate, higher is better, target >= 0.95
# --------------------------------------------------------------------------

def build_M5_one_detected():
    """A single repair episode with detected=True."""
    return Run(run_id="v9-M5-one", arm="attacker", source="v9",
               repairs=[Repair(episode_id="ep01", trigger="rule-change",
                               detected=True, detection_actions=3)])


def attack_M5_one_detected():
    return Attack(
        metric_id="M5", name="one-detected",
        build=build_M5_one_detected,
        claim="M5 = 1.0 from a single boolean the scored arm sets itself",
        accidental=True,
        rationale=("detected is an unverified flag; nothing in the metric compares it against "
                   "beats, clauses or steps. A harness whose default for `detected` is True "
                   "(or which sets it when it writes the episode at all) yields 1.0 for every arm."),
    )


def build_M5_bulk():
    """Five hundred episodes, all detected, none carrying any evidence."""
    return Run(run_id="v9-M5-bulk", arm="attacker", source="v9",
               repairs=[Repair(episode_id="ep%03d" % i, trigger="rule-change",
                               strategy="unknown", detected=True,
                               detection_actions=None, beats=[], beats_required=6,
                               theorems_before=0, invalidated_theorems=0)
                        for i in range(500)])


def attack_M5_bulk():
    return Attack(
        metric_id="M5", name="bulk",
        build=build_M5_bulk,
        claim="M5 = 1.0 over 500 episodes with zero beats, zero detection_actions and zero theorems",
        accidental=False,
        rationale=("Structurally different from one-detected: it defeats the obvious patch "
                   "'require a decent sample size'. Every other field on the Repair record is "
                   "empty and the metric still returns a perfect score with episodes=500."),
    )


# --------------------------------------------------------------------------
# M6 -- repair collateral share, NEUTRAL, controllability
# --------------------------------------------------------------------------

def build_M6_high():
    """Every theorem invalidated by every repair: share 1.0."""
    return Run(run_id="v9-M6-high", arm="attacker", source="v9",
               repairs=[Repair(episode_id="ep%02d" % i, trigger="rule-change",
                               detected=True, detection_actions=1,
                               theorems_before=8, invalidated_theorems=8,
                               silently_wrong_without_tracking=False)
                        for i in range(12)])


def build_M6_low():
    """Same shape, one theorem in twenty: share 0.05. Factor of 20 apart."""
    return Run(run_id="v9-M6-low", arm="attacker", source="v9",
               repairs=[Repair(episode_id="ep%02d" % i, trigger="rule-change",
                               detected=True, detection_actions=1,
                               theorems_before=20, invalidated_theorems=1,
                               silently_wrong_without_tracking=False)
                        for i in range(12)])


def attack_M6_dial():
    return Attack(
        metric_id="M6", name="dial",
        build=build_M6_high,
        build_low=build_M6_low,
        claim="M6 = 1.0 vs 0.05 -- a factor of 20 -- from two runs identical except for two integers",
        accidental=True,
        rationale=("Both numerator and denominator are declared by the arm and are never "
                   "reconciled with theory.clauses or theory.deadlock_theorems. How many "
                   "theorems a manual 'had before' depends entirely on whether the "
                   "implementation counts clauses, proven clauses, or derived corollaries -- a "
                   "naming choice moves this diagnostic by an order of magnitude."),
        benign_window=("Harmless only as a strict-zero check: M6 == 0.0 across episodes tells you "
                       "no repair touched anything downstream. Any non-zero magnitude is "
                       "uninterpretable without knowing what the reporter counted as a theorem."),
    )


def build_M6_unbounded():
    """Nothing clamps the share to [0,1]: 1000 invalidated out of 1."""
    return Run(run_id="v9-M6-unbounded", arm="attacker", source="v9",
               repairs=[Repair(episode_id="ep01", trigger="rule-change",
                               detected=True, detection_actions=1,
                               theorems_before=1, invalidated_theorems=1000)])


def build_M6_zero():
    """Zero collateral, with a real denominator."""
    return Run(run_id="v9-M6-zero", arm="attacker", source="v9",
               repairs=[Repair(episode_id="ep01", trigger="rule-change",
                               detected=True, detection_actions=1,
                               theorems_before=1, invalidated_theorems=0)])


def attack_M6_unbounded():
    return Attack(
        metric_id="M6", name="unbounded",
        build=build_M6_unbounded,
        build_low=build_M6_zero,
        claim="M6 = 1000.0 vs 0.0 -- a 'share' with unit `share` that exceeds 1 by three orders of magnitude",
        accidental=False,
        rationale=("Structurally different from `dial`: it breaks the unit rather than the "
                   "magnitude. There is no min(1.0, ...) and no assertion that "
                   "invalidated_theorems <= theorems_before, so the declared unit `share` is "
                   "not enforced anywhere."),
        benign_window=("A reader using M6 to sanity-check another metric should first assert "
                       "0 <= value <= 1; the code never does."),
    )


# --------------------------------------------------------------------------
# One run that sweeps the whole family at once (M1,M2,M4,M5 all at target).
# Registered under M2 for the table; the cross-metric print is the point.
# --------------------------------------------------------------------------

def build_MALL_sweep():
    return Run(run_id="v9-MALL-sweep", arm="attacker", source="v9", intent="solve",
               steps=[Step(idx=i, action="a%d" % i, state_key="s%d" % i,
                           level=0 if i < 6 else 1)
                      for i in range(12)],
               truth=Truth(levels=2,
                           mechanisms={"m%02d" % i: {"first_seen": i, "first_used": i}
                                       for i in range(30)}),
               repairs=[Repair(episode_id="ep%02d" % i, trigger="rule-change",
                               detected=True, detection_actions=0,
                               theorems_before=8, invalidated_theorems=8)
                        for i in range(20)])


def attack_M2_all_family_sweep():
    return Attack(
        metric_id="M2", name="all-family-sweep",
        build=build_MALL_sweep,
        claim="one 12-step run hits M1=0.0, M2=1.0, M4=0.0, M5=1.0, M6=1.0 simultaneously",
        accidental=False,
        rationale=("The whole mechanism family is a function of two sidecar structures (Truth and "
                   "the Repair list) that the arm supplies about itself; the 12 steps are decoration. "
                   "There is no consistency check between the family's five live metrics, so one "
                   "record satisfies all of them at once."),
    )


ATTACKS = [
    attack_M1_same_step, attack_M1_saturate, attack_M1_precognition, attack_M1_survivorship,
    attack_M2_single, attack_M2_never_seen, attack_M2_zero_step_run,
    attack_M2_all_family_sweep,
    attack_M3_two_levels, attack_M3_one_level,
    attack_M4_instant, attack_M4_blind_but_instant, attack_M4_negative,
    attack_M5_one_detected, attack_M5_bulk,
    attack_M6_dial, attack_M6_unbounded,
]
