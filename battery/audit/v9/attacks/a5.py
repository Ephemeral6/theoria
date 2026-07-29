"""v9 red-team attacks against K1 K2 K3 K4 K5 K6 K13.

Every builder is a zero-argument function that only lays out data.
"""
from battery.audit.v9.attack import Attack
from battery.model import Run, Step, Call, Concept, Clause, Theory, Beat, Repair, Truth


# --------------------------------------------------------------------------
# K1 -- replay accuracy (higher, >= 0.95)
# --------------------------------------------------------------------------

def build_K1_hollow():
    """One self-declared pair, one self-declared agreement, no trace at all."""
    return Run(run_id="v9-K1-hollow", arm="attacker", source="v9",
               theory=Theory(replay_pairs=1, replay_agree=1))


def build_K1_bulk():
    """A big-sounding denominator, still with zero steps to have replayed."""
    return Run(run_id="v9-K1-bulk", arm="attacker", source="v9",
               theory=Theory(replay_pairs=39960, replay_agree=39960))


def build_K1_overrun():
    """agree > pairs: the metric never checks that the ratio is a share."""
    return Run(run_id="v9-K1-overrun", arm="attacker", source="v9",
               theory=Theory(replay_pairs=1, replay_agree=7))


def attack_K1_hollow():
    return Attack(
        metric_id="K1", name="hollow",
        build=build_K1_hollow,
        claim="K1 = 1.0 from a Theory carrying two integers and a run with no steps",
        accidental=True,
        rationale="A harness that writes replay_pairs/replay_agree from its own "
                  "self-check emits 1/1 whenever the manual has exactly one rule and "
                  "one transition to test it on; an arm that crashed after its first "
                  "transition lands here without trying.",
    )


def attack_K1_bulk():
    return Attack(
        metric_id="K1", name="bulk",
        build=build_K1_bulk,
        claim="K1 = 1.0 with a 39960-pair denominator that no step in the run supports",
        accidental=False,
        rationale="Nothing in the run cross-checks replay_pairs against len(steps), but "
                  "writing a five-digit denominator with an empty steps list is a "
                  "deliberate act, not a default a harness falls into.",
    )


def attack_K1_overrun():
    return Attack(
        metric_id="K1", name="overrun",
        build=build_K1_overrun,
        claim="K1 = 7.0 -- a 'share' above 1, status ok, no complaint",
        accidental=True,
        rationale="Double-counting is a classic off-by-one in a replay loop that "
                  "increments agree per matched field but pairs per transition, so a "
                  "real harness can emit agree > pairs by accident.",
    )


# --------------------------------------------------------------------------
# K2 -- held-out accuracy (higher, >= 0.95)
# --------------------------------------------------------------------------

def build_K2_frame_string():
    """The only guard is that held_out_frame is a non-empty string."""
    return Run(run_id="v9-K2-frame", arm="attacker", source="v9",
               theory=Theory(held_out_pairs=1, held_out_agree=1,
                             held_out_frame="exhaustive over all reachable pairs"))


def build_K2_adversarial_three():
    """The denominator the metric's own refusal text names as incomparable."""
    return Run(run_id="v9-K2-three", arm="attacker", source="v9",
               theory=Theory(held_out_pairs=3, held_out_agree=3,
                             held_out_frame="3 adversarial gaps"))


def build_K2_self_dealt():
    """Held-out set chosen after the fact: 200 pairs, all of them agreed."""
    return Run(run_id="v9-K2-self", arm="attacker", source="v9",
               theory=Theory(
                   held_out_pairs=200, held_out_agree=200,
                   held_out_frame="pairs withheld from the trace",
                   clauses=[Clause(name="c%d" % i, kind="rule") for i in range(5)]))


def attack_K2_frame_string():
    return Attack(
        metric_id="K2", name="frame-string",
        build=build_K2_frame_string,
        claim="K2 = 1.0 on 1 held-out pair; the sampling-frame guard is satisfied by any truthy string",
        accidental=True,
        rationale="held_out_frame is free text with no vocabulary and no comparison to "
                  "the run, so any harness that fills the field at all -- even with a "
                  "constant label -- clears the guard.",
    )


def attack_K2_adversarial_three():
    return Attack(
        metric_id="K2", name="adversarial-three",
        build=build_K2_adversarial_three,
        claim="K2 = 1.0 with frame literally set to '3 adversarial gaps' -- the case the code's own thin() text says is incomparable",
        accidental=False,
        rationale="The metric documents this exact failure in its refusal message and "
                  "then returns ok anyway; choosing a three-pair held-out set and "
                  "labelling it honestly is a choice an author makes, not a default.",
    )


def attack_K2_self_dealt():
    return Attack(
        metric_id="K2", name="self-dealt",
        build=build_K2_self_dealt,
        claim="K2 = 1.0 on 200 pairs the run itself both selected and graded",
        accidental=True,
        rationale="Held-out pairs and their grades come from the same writer as the "
                  "manual, so a harness that generates negatives from the manual's own "
                  "rules will agree with itself on every one of them.",
    )


# --------------------------------------------------------------------------
# K3 -- theorem count (higher, >= 100)
# --------------------------------------------------------------------------

def build_K3_hundred():
    """120 clauses tagged 'invariant'. proven is False on every one of them."""
    return Run(run_id="v9-K3-hundred", arm="attacker", source="v9",
               theory=Theory(clauses=[Clause(name="inv%d" % i, kind="invariant")
                                      for i in range(120)]))


def build_K3_duplicates():
    """250 clauses with the same name and the same content: no de-duplication."""
    return Run(run_id="v9-K3-dupes", arm="attacker", source="v9",
               theory=Theory(clauses=[Clause(name="the same one", kind="theorem")
                                      for i in range(250)]))


def build_K3_pending():
    """150 theorems that all declare themselves unproven and probe-pending."""
    return Run(run_id="v9-K3-pending", arm="attacker", source="v9",
               theory=Theory(clauses=[Clause(name="t%d" % i, kind="theorem",
                                             proven=False, probe_pending=True,
                                             evidence_transitions=0)
                                      for i in range(150)]))


def attack_K3_hundred():
    return Attack(
        metric_id="K3", name="hundred",
        build=build_K3_hundred,
        claim="K3 = 120 from 120 Clause records whose only content is kind='invariant'",
        accidental=True,
        rationale="The count keys off a string field with no proof, evidence or "
                  "uniqueness requirement, so any template that emits one clause per "
                  "observed object type inflates it linearly in world size.",
    )


def attack_K3_duplicates():
    return Attack(
        metric_id="K3", name="duplicates",
        build=build_K3_duplicates,
        claim="K3 = 250 from 250 byte-identical clauses (same name, same kind)",
        accidental=True,
        rationale="Append-only theory files plus a re-run loop duplicate clauses "
                  "routinely; nothing in theorem_count() collapses by name.",
    )


def attack_K3_pending():
    return Attack(
        metric_id="K3", name="pending",
        build=build_K3_pending,
        claim="K3 = 150 where every clause says proven=False, probe_pending=True, evidence_transitions=0",
        accidental=False,
        rationale="The clause fields that would contradict the claim are all present in "
                  "the model and all ignored by the metric; setting them to their most "
                  "damning values on purpose is an attack, not an accident.",
    )


# --------------------------------------------------------------------------
# K4 -- evidence coverage (higher, >= 0.95)
# --------------------------------------------------------------------------

def build_K4_single_annotated():
    """One clause annotated 1/1, 200 clauses annotated with nothing."""
    return Run(run_id="v9-K4-single", arm="attacker", source="v9",
               theory=Theory(clauses=[Clause(name="covered", kind="invariant",
                                             coverage_num=1, coverage_den=1)] +
                                     [Clause(name="quiet%d" % i, kind="rule")
                                      for i in range(200)]))


def build_K4_unit_fractions():
    """60 clauses, each 1/1. Denominator of one is a legal denominator."""
    return Run(run_id="v9-K4-unit", arm="attacker", source="v9",
               theory=Theory(clauses=[Clause(name="u%d" % i, kind="invariant",
                                             coverage_num=1, coverage_den=1)
                                      for i in range(60)]))


def build_K4_over_covered():
    """coverage_num > coverage_den: unclamped, so the mean can exceed 1."""
    return Run(run_id="v9-K4-over", arm="attacker", source="v9",
               theory=Theory(clauses=[Clause(name="o%d" % i, kind="invariant",
                                             coverage_num=9, coverage_den=3)
                                      for i in range(10)]))


def attack_K4_single_annotated():
    return Attack(
        metric_id="K4", name="single-annotated",
        build=build_K4_single_annotated,
        claim="K4 = 1.0 computed over 1 clause while 200 clauses carry no coverage at all",
        accidental=True,
        rationale="The unannotated count is reported in support but never folded into "
                  "the value, so any pipeline that annotates only the clauses it "
                  "measured -- the normal case -- reports the mean of its easiest few.",
    )


def attack_K4_unit_fractions():
    return Attack(
        metric_id="K4", name="unit-fractions",
        build=build_K4_unit_fractions,
        claim="K4 = 1.0 from 60 clauses each covered by exactly 1 of 1 transitions",
        accidental=True,
        rationale="A denominator floor is absent, and a clause mined from a single "
                  "witnessed transition naturally has coverage 1/1, so a miner run on a "
                  "short trace produces this shape by default.",
    )


def attack_K4_over_covered():
    return Attack(
        metric_id="K4", name="over-covered",
        build=build_K4_over_covered,
        claim="K4 = 3.0 -- a 'share' of three, status ok",
        accidental=True,
        rationale="Counting matched transitions across repeated visits to the same "
                  "state while sizing the denominator by distinct states is an easy "
                  "bookkeeping slip that pushes num past den.",
    )


# --------------------------------------------------------------------------
# K5 -- vocabulary size (higher, >= 100)
# --------------------------------------------------------------------------

def build_K5_alphabet():
    """140 named concepts, none load-bearing, none with a compression account."""
    return Run(run_id="v9-K5-alphabet", arm="attacker", source="v9",
               theory=Theory(concepts=[Concept(name="w%d" % i) for i in range(140)]))


def build_K5_duplicates():
    """110 concepts that are all the same word."""
    return Run(run_id="v9-K5-dupes", arm="attacker", source="v9",
               theory=Theory(concepts=[Concept(name="thing") for i in range(110)]))


def attack_K5_alphabet():
    return Attack(
        metric_id="K5", name="alphabet",
        build=build_K5_alphabet,
        claim="K5 = 140 from 140 Concept records that carry a name and nothing else",
        accidental=True,
        rationale="len(concepts) has no admission test beyond existence, so a "
                  "segmenter that emits one concept per distinct sprite or colour "
                  "crosses 100 on a mid-size grid without any of them being used.",
    )


def attack_K5_duplicates():
    return Attack(
        metric_id="K5", name="duplicates",
        build=build_K5_duplicates,
        claim="K5 = 110 where all 110 concepts have the identical name 'thing'",
        accidental=True,
        rationale="The word table is a list, not a set; a revision loop that re-admits "
                  "the same concept each pass grows it monotonically.",
    )


# --------------------------------------------------------------------------
# K6 -- mean compression gain (higher, >= 1000 bits)
# --------------------------------------------------------------------------

def build_K6_inflated():
    """Three concepts, each self-reporting a million bits saved."""
    return Run(run_id="v9-K6-inflated", arm="attacker", source="v9",
               theory=Theory(concepts=[Concept(name="big%d" % i,
                                               compression_bits=1000000)
                                       for i in range(3)]))


def build_K6_mean_hides():
    """One enormous gain drags 24 negative concepts over the bar."""
    return Run(run_id="v9-K6-hides", arm="attacker", source="v9",
               theory=Theory(concepts=[Concept(name="whale", compression_bits=10000000)] +
                                      [Concept(name="junk%d" % i, compression_bits=-200)
                                       for i in range(24)]))


def build_K6_thin_denominator():
    """100 concepts in the table, exactly one of them accounted for."""
    return Run(run_id="v9-K6-thin", arm="attacker", source="v9",
               theory=Theory(concepts=[Concept(name="accounted", compression_bits=5000)] +
                                      [Concept(name="silent%d" % i) for i in range(99)]))


def attack_K6_inflated():
    return Attack(
        metric_id="K6", name="inflated",
        build=build_K6_inflated,
        claim="K6 = 1000000.0 bits/concept from three integers nobody recomputed",
        accidental=False,
        rationale="compression_bits is taken on trust with no upper bound tied to the "
                  "size of the trace it supposedly compresses, but writing 10^6 is a "
                  "declaration, not a rounding error.",
    )


def attack_K6_mean_hides():
    return Attack(
        metric_id="K6", name="mean-hides",
        build=build_K6_mean_hides,
        claim="K6 = 399808.0 bits/concept while 24 of the 25 concepts have negative gain",
        accidental=True,
        rationale="A mean over a heavy-tailed quantity is dominated by its largest "
                  "term; one genuinely good abstraction plus a long tail of failed ones "
                  "is the expected shape of real concept mining.",
    )


def attack_K6_thin_denominator():
    return Attack(
        metric_id="K6", name="thin-denominator",
        build=build_K6_thin_denominator,
        claim="K6 = 5000.0 'per admitted concept' over a denominator of 1 while K5 counts 100 admitted concepts",
        accidental=True,
        rationale="The gains list silently drops concepts with compression_bits=None, "
                  "so a pipeline that only bothers to cost the concepts it is proud of "
                  "gets a mean over its own shortlist while K5 counts the whole table.",
    )


# --------------------------------------------------------------------------
# K13 -- repair cost ratio (lower, <= 0.001)
# --------------------------------------------------------------------------

def build_K13_empty_repair():
    """A repair episode with no beats at all: env_actions sums to 0."""
    return Run(run_id="v9-K13-empty", arm="attacker", source="v9",
               repairs=[Repair(episode_id="e1", trigger="contradiction",
                               baseline_actions=1000000)])


def build_K13_zero_declared():
    """repair_actions declared as literally zero against a baseline of one."""
    return Run(run_id="v9-K13-zero", arm="attacker", source="v9",
               repairs=[Repair(episode_id="e1", strategy="local",
                               repair_actions=0, baseline_actions=1,
                               beats=[Beat(tag="b%d" % i, name="beat%d" % i,
                                           closed=True, env_actions=0)
                                      for i in range(6)])])


def build_K13_inflated_baseline():
    """One real action of repair against a self-declared 10^6-action baseline."""
    return Run(run_id="v9-K13-inflated", arm="attacker", source="v9",
               repairs=[Repair(episode_id="e1", strategy="local",
                               repair_actions=1, baseline_actions=1000000)])


def build_K13_selective_annotation():
    """The cheap episode is annotated; the 500000-action one omits its baseline
    and is dropped by the `if not base ... continue` line."""
    return Run(run_id="v9-K13-selective", arm="attacker", source="v9",
               repairs=[Repair(episode_id="a-cheap", strategy="local",
                               repair_actions=0, baseline_actions=1000),
                        Repair(episode_id="b-ruinous", strategy="local",
                               repair_actions=500000, baseline_actions=None)])


def attack_K13_empty_repair():
    return Attack(
        metric_id="K13", name="empty-repair",
        build=build_K13_empty_repair,
        claim="K13 = 0.0 from a Repair with no beats, no detection, no changed clause",
        accidental=True,
        rationale="repair_actions defaults to None, which falls through to env_actions, "
                  "which sums an empty beat list to 0; any episode logged before its "
                  "beats are written scores a perfect zero.",
    )


def attack_K13_zero_declared():
    return Attack(
        metric_id="K13", name="zero-declared",
        build=build_K13_zero_declared,
        claim="K13 = 0.0 with all six beats closed and every one of them costing 0 environment actions",
        accidental=True,
        rationale="A repair carried out purely by editing the manual -- no re-probing "
                  "of the world -- genuinely costs zero environment actions, which is "
                  "exactly the unverified repair the ratio should have penalised.",
    )


def attack_K13_inflated_baseline():
    return Attack(
        metric_id="K13", name="inflated-baseline",
        build=build_K13_inflated_baseline,
        claim="K13 = 1e-06 by writing a large baseline_actions rather than a small repair",
        accidental=False,
        rationale="baseline_actions is a free integer never reconciled against "
                  "len(run.steps); making the denominator large is the cheapest lever "
                  "but it takes a deliberate choice of number.",
    )


def attack_K13_selective_annotation():
    return Attack(
        metric_id="K13", name="selective-annotation",
        build=build_K13_selective_annotation,
        claim="K13 = 0.0 averaged over one episode while a 500000-action repair sits in run.repairs, silently skipped",
        accidental=True,
        rationale="`if not base or spent is None: continue` drops any episode missing a "
                  "baseline, and the hardest repairs are exactly the ones whose "
                  "pre-repair cost nobody managed to reconstruct.",
    )


# --------------------------------------------------------------------------
# One Run that clears all seven thresholds at once.
# --------------------------------------------------------------------------

def build_ALL_sweep():
    return Run(
        run_id="v9-sweep", arm="attacker", source="v9", intent="solve",
        theory=Theory(
            replay_pairs=1200, replay_agree=1200,
            held_out_pairs=300, held_out_agree=300,
            held_out_frame="held-out transitions sampled from the sealed pile",
            concepts=[Concept(name="k%d" % i, compression_bits=200000)
                      for i in range(140)],
            clauses=[Clause(name="inv%d" % i, kind="invariant",
                            coverage_num=1, coverage_den=1)
                     for i in range(120)],
            playbook_entries=140, deadlock_theorems=140, revisions=12,
            probes_designed=50, probes_executable=50),
        repairs=[Repair(episode_id="e1", strategy="local",
                        repair_actions=0, baseline_actions=4000)])


def attack_ALL_sweep():
    return Attack(
        metric_id="K1", name="sweep-all-seven",
        build=build_ALL_sweep,
        claim="one 20-line Run clears K1 K2 K3 K4 K5 K6 K13 simultaneously",
        accidental=False,
        rationale="No metric in this family cross-checks any other, and none of them "
                  "reads run.steps or run.calls, so the seven scores are seven "
                  "independent fields of a single self-report.",
    )


ATTACKS = [
    attack_ALL_sweep,
    attack_K1_hollow, attack_K1_bulk, attack_K1_overrun,
    attack_K2_frame_string, attack_K2_adversarial_three, attack_K2_self_dealt,
    attack_K3_hundred, attack_K3_duplicates, attack_K3_pending,
    attack_K4_single_annotated, attack_K4_unit_fractions, attack_K4_over_covered,
    attack_K5_alphabet, attack_K5_duplicates,
    attack_K6_inflated, attack_K6_mean_hides, attack_K6_thin_denominator,
    attack_K13_empty_repair, attack_K13_zero_declared,
    attack_K13_inflated_baseline, attack_K13_selective_annotation,
]
