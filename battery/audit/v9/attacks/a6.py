"""v9 red-team attacks on K7, K8, K9, K10, K11, K12, K14.

Every builder is zero-argument, deterministic, lays out data only, and is
intended to pass battery/audit/v9/check.py.
"""
from battery.audit.v9.attack import Attack
from battery.model import Run, Step, Call, Concept, Clause, Theory, Beat, Repair, Truth


# ---------------------------------------------------------------- K7 (neutral)
# K7 = number of concepts whose compression_bits < 0, among concepts that carry
# a compression account at all. Two independent handles: the sign of a field,
# and whether the field is filled in at all.

def build_K7_sign_high():
    return Run(run_id="v9-K7-sign-high", arm="attacker", source="v9",
               theory=Theory(concepts=[Concept(name="c%d" % i, compression_bits=-1)
                                       for i in range(1000)]))


def build_K7_sign_low():
    return Run(run_id="v9-K7-sign-low", arm="attacker", source="v9",
               theory=Theory(concepts=[Concept(name="c%d" % i, compression_bits=1)
                                       for i in range(1000)]))


def attack_K7_sign():
    return Attack(
        metric_id="K7", name="sign",
        build=build_K7_sign_high, build_low=build_K7_sign_low,
        claim="K7 = 1000 vs 0 on two manuals with the identical 1000 concepts; only the sign of a declared integer differs",
        accidental=True,
        rationale="compression_bits is whatever the arm's own estimator wrote down; a sign convention "
                  "(cost-of-encoding vs. bits-saved) flipped once in that estimator moves every concept "
                  "across the boundary at the same time, which is exactly the 1000-vs-0 swing here.",
        benign_window="K7 is only a sanity check on K6 if the same estimator, with a fixed sign convention, "
                      "annotated every concept in the run; a K7 of 0 next to a K5 of 1000 should read as "
                      "'unaudited', not 'clean'.",
    )


def build_K7_silence_high():
    return Run(run_id="v9-K7-silence-high", arm="attacker", source="v9",
               theory=Theory(concepts=[Concept(name="c%d" % i, compression_bits=-3, load_bearing=True)
                                       for i in range(400)]))


def build_K7_silence_low():
    # The same 400 load-bearing concepts, but the compression account is simply
    # not filled in for 399 of them. K7's own filter drops them.
    return Run(run_id="v9-K7-silence-low", arm="attacker", source="v9",
               theory=Theory(concepts=[Concept(name="c0", compression_bits=7, load_bearing=True)]
                                      + [Concept(name="c%d" % i, load_bearing=True)
                                         for i in range(1, 400)]))


def attack_K7_silence():
    return Attack(
        metric_id="K7", name="silence",
        build=build_K7_silence_high, build_low=build_K7_silence_low,
        claim="K7 = 400 vs 0 on manuals of the same size; the low one simply declines to compute 399 of the 400 accounts",
        accidental=True,
        rationale="an estimator that raises or times out on hard concepts and leaves compression_bits=None "
                  "produces exactly the low run, so the arm with the *worst* compression tooling reports the "
                  "cleanest diagnostic; that is an ordinary failure mode of an optional annotation, not sabotage.",
        benign_window="K7 is harmless only when read together with its own support field of_concepts and with K5: "
                      "0 of 1 accounted concepts is not the same reading as 0 of 400.",
    )


# ----------------------------------------------------------------- K8 (higher)
# K8 = probes_executable / probes_designed. Both are free integers on Theory.

def build_K8_one_probe():
    return Run(run_id="v9-K8-one-probe", arm="attacker", source="v9",
               theory=Theory(probes_designed=1, probes_executable=1))


def attack_K8_one_probe():
    return Attack(
        metric_id="K8", name="one-probe",
        build=build_K8_one_probe,
        claim="K8 = 1.0 from a theory that designed exactly one probe and ran it",
        accidental=True,
        rationale="the denominator is proposals, so the cheapest way to a perfect ratio is to propose almost "
                  "nothing; any harness that only registers a probe design at the moment it dispatches it "
                  "records designed==executable by construction and can never score below 1.0.",
    )


def build_K8_bulk():
    return Run(run_id="v9-K8-bulk", arm="attacker", source="v9",
               theory=Theory(probes_designed=1000000, probes_executable=1000000,
                             clauses=[Clause(name="q%d" % i, kind="probe", probe_pending=True)
                                      for i in range(50)]))


def attack_K8_bulk():
    return Attack(
        metric_id="K8", name="bulk",
        build=build_K8_bulk,
        claim="K8 = 1.0 at a million designed probes, with 50 clauses still flagged probe_pending and none proven",
        accidental=False,
        rationale="K8 never consults the clause table, so probe_pending clauses sitting unresolved next to a "
                  "perfect executable rate raise no objection; declaring the two counters equal at any scale "
                  "requires deliberately writing both, which is why this one is not accidental.",
    )


def build_K8_overflow():
    # Nothing in K8 requires executable <= designed.
    return Run(run_id="v9-K8-overflow", arm="attacker", source="v9",
               theory=Theory(probes_designed=1, probes_executable=1000))


def attack_K8_overflow():
    return Attack(
        metric_id="K8", name="overflow",
        build=build_K8_overflow,
        claim="K8 = 1000.0 -- a 'share' with no upper clamp; executable is allowed to exceed designed",
        accidental=True,
        rationale="a counter that increments once per probe *execution* while designs are counted per distinct "
                  "template (retries, re-runs across levels) exceeds 1.0 without anybody intending it, and the "
                  "metric prints the ratio anyway, so a share silently becomes an unbounded score.",
    )


# ----------------------------------------------------------------- K9 (higher)
# K9 = run.theory.playbook_entries, a bare integer.

def build_K9_counter():
    return Run(run_id="v9-K9-counter", arm="attacker", source="v9",
               theory=Theory(playbook_entries=100000))


def attack_K9_counter():
    return Attack(
        metric_id="K9", name="counter",
        build=build_K9_counter,
        claim="K9 = 100000 from a theory whose every other field is empty: no concepts, no clauses, no revisions",
        accidental=True,
        rationale="playbook_entries is a self-reported integer with no object behind it, so a template that "
                  "emits one 'prefer action a in state s' line per observed transition reaches six figures on a "
                  "single long trace while containing no ordering, pruning or heuristic knowledge at all.",
    )


def build_K9_transcription():
    # Structurally different: the entries are "backed" by an equally cheap
    # clause table, so the count survives a naive cross-check against K3.
    return Run(run_id="v9-K9-transcription", arm="attacker", source="v9",
               theory=Theory(playbook_entries=512,
                             clauses=[Clause(name="prefer-a%d-in-s%d" % (i, i), kind="preference",
                                             evidence_transitions=1, coverage_num=1, coverage_den=1)
                                      for i in range(512)],
                             revisions=1))


def attack_K9_transcription():
    return Attack(
        metric_id="K9", name="transcription",
        build=build_K9_transcription,
        claim="K9 = 512 with 512 matching one-transition 'preference' clauses, so the count survives a cross-check against the clause table",
        accidental=True,
        rationale="each clause is a single memorised transition with coverage 1/1, which is what a rule miner "
                  "emits when it fails to generalise; the playbook is then a transcript of the trace and K9 "
                  "measures trace length, not policy.",
    )


# ---------------------------------------------------------------- K10 (higher)
# K10 = run.theory.deadlock_theorems. No guard of any kind, not even a thin().

def build_K10_counter():
    return Run(run_id="v9-K10-counter", arm="attacker", source="v9",
               theory=Theory(deadlock_theorems=1000000))


def attack_K10_counter():
    return Attack(
        metric_id="K10", name="counter",
        build=build_K10_counter,
        claim="K10 = 1000000 'machine-checked proofs' declared by an integer, with proven=False everywhere (there are no clauses at all)",
        accidental=True,
        rationale="the word 'machine-checked' lives only in the docstring; a counter incremented once per "
                  "dead-end region enumerated by a reachability sweep -- not once per checked proof -- crosses "
                  "100 on any non-trivial grid, which is the ordinary way this field gets wired up.",
    )


def build_K10_dressed():
    # Same claim, but dressed with unproven clauses of the right kind so that a
    # reader cross-checking K3/K10 sees a plausible manual.
    return Run(run_id="v9-K10-dressed", arm="attacker", source="v9",
               theory=Theory(deadlock_theorems=4096,
                             clauses=[Clause(name="deadlock-%d" % i, kind="theorem", proven=False)
                                      for i in range(4096)],
                             revisions=2))


def attack_K10_dressed():
    return Attack(
        metric_id="K10", name="dressed",
        build=build_K10_dressed,
        claim="K10 = 4096 alongside 4096 clauses of kind 'theorem' every one of which has proven=False",
        accidental=False,
        rationale="K10 reads the integer and never looks at Clause.proven, which is the field that would encode "
                  "'machine-checked'; laying out 4096 unproven theorem clauses to match the counter is a "
                  "deliberate dressing step, so this variant is not something a rig does by accident.",
    )


# --------------------------------------------------------------- K11 (neutral)
# K11 = run.theory.revisions, a bare integer, unguarded.

def build_K11_chatty():
    return Run(run_id="v9-K11-chatty", arm="attacker", source="v9",
               theory=Theory(revisions=1000,
                             concepts=[Concept(name="c%d" % i, admitted_revision=i, compression_bits=1)
                                       for i in range(10)]))


def build_K11_quiet():
    # Identical manual content; only the bookkeeping granularity differs.
    return Run(run_id="v9-K11-quiet", arm="attacker", source="v9",
               theory=Theory(revisions=1,
                             concepts=[Concept(name="c%d" % i, admitted_revision=0, compression_bits=1)
                                       for i in range(10)]))


def attack_K11_bookkeeping():
    return Attack(
        metric_id="K11", name="bookkeeping",
        build=build_K11_chatty, build_low=build_K11_quiet,
        claim="K11 = 1000 vs 1 for the same ten concepts; only the write granularity of the manual differs",
        accidental=True,
        rationale="a harness that bumps the revision counter on every file write gets 1000, one that rewrites "
                  "the manual once per episode gets 1; nothing about the theory changed, so the 'coarse axis' "
                  "of the concept-birth timeline is a property of the writer, not of the learning.",
        benign_window="K11 is a safe axis for K5/K6 only if revisions are counted per adjudicated manual "
                      "change and every concept's admitted_revision indexes into that same sequence; used as "
                      "a raw count it is a commit-frequency measurement.",
    )


def build_K11_zero():
    # The floor: K11 answers 'ok' with 0 on a theory that has no content at all.
    return Run(run_id="v9-K11-zero", arm="attacker", source="v9", theory=Theory())


def build_K11_hundred():
    return Run(run_id="v9-K11-hundred", arm="attacker", source="v9", theory=Theory(revisions=100))


def attack_K11_empty():
    return Attack(
        metric_id="K11", name="empty",
        build=build_K11_hundred, build_low=build_K11_zero,
        claim="K11 = 100 vs 0 on two empty theories -- the metric never checks that anything was revised",
        accidental=True,
        rationale="K11 has no thin() branch, so an arm that keeps a Theory object but never populates it still "
                  "gets a numeric answer; a crashed or stubbed theory-writer therefore lands on the 0 end "
                  "without any signal that the number is vacuous.",
        benign_window="0 revisions on a non-empty concept list should read as a broken writer, not as a stable "
                      "manual; K11 cannot tell those apart.",
    )


# ---------------------------------------------------------------- K12 (higher)
# K12 = closed beats / required beats, over repair episodes.
# Guard: an episode with closed beats and no repair_actions, no beat env_actions
# and no changed_clause is 'a claim, not a repair' -> insufficient-data.

def build_K12_clause_tag():
    # Evade the trace guard with a single string in changed_clause.
    return Run(run_id="v9-K12-clause-tag", arm="attacker", source="v9",
               repairs=[Repair(episode_id="e0", changed_clause="c0", beats_required=6,
                               beats=[Beat(tag="t%d" % i, name="b%d" % i, closed=True)
                                      for i in range(6)])])


def attack_K12_clause_tag():
    return Attack(
        metric_id="K12", name="clause-tag",
        build=build_K12_clause_tag,
        claim="K12 = 1.0 (6/6 beats closed) on a repair episode that spent zero environment actions; the evidence guard is satisfied by the string 'c0'",
        accidental=True,
        rationale="the guard asks for repair_actions OR env_actions OR changed_clause, and changed_clause is a "
                  "free-text field a summariser fills in from the clause it *intended* to touch; any pipeline "
                  "that records the target clause before doing the work passes the guard for free.",
    )


def build_K12_one_env_action():
    # Structurally different evasion: no changed_clause at all, one beat
    # declares a single environment action, which is enough for the guard.
    return Run(run_id="v9-K12-one-env-action", arm="attacker", source="v9",
               repairs=[Repair(episode_id="e%d" % e, beats_required=6,
                               beats=[Beat(tag="t%d" % i, name="b%d" % i, closed=True,
                                           env_actions=1 if i == 0 else 0)
                                      for i in range(6)])
                        for e in range(40)])


def attack_K12_one_env_action():
    return Attack(
        metric_id="K12", name="one-env-action",
        build=build_K12_one_env_action,
        claim="K12 = 1.0 across 40 episodes, 240/240 beats, on a total budget of 40 environment actions (one per episode)",
        accidental=True,
        rationale="Repair.env_actions is a sum over beats, so a single action anywhere in the episode unlocks "
                  "the whole six-beat claim; a harness that always takes one confirmatory step after editing "
                  "the theory clears the guard on every episode without the beats meaning anything.",
    )


def build_K12_short_requirement():
    # Nothing clamps the ratio: declare a requirement of 1 and close 6.
    return Run(run_id="v9-K12-short-requirement", arm="attacker", source="v9",
               repairs=[Repair(episode_id="e0", changed_clause="c0", beats_required=1,
                               beats=[Beat(tag="t%d" % i, name="b%d" % i, closed=True)
                                      for i in range(6)])])


def attack_K12_short_requirement():
    return Attack(
        metric_id="K12", name="short-requirement",
        build=build_K12_short_requirement,
        claim="K12 = 6.0 -- the episode declares its own denominator, so a 'share' exceeds 1",
        accidental=False,
        rationale="beats_required is per-episode and self-declared, and the metric divides by the sum of it "
                  "without checking it against the six named beats; setting it to 1 is a deliberate act, so "
                  "this is not an accident, but it shows K12's denominator is under the measured party's control.",
    )


def build_K12_whitespace():
    # The minimal form of the same evasion: the guard is a truthiness test on a
    # string, so a single space is "a changed clause".
    return Run(run_id="v9-K12-whitespace", arm="attacker", source="v9",
               repairs=[Repair(episode_id="e0", changed_clause=" ", beats_required=6,
                               beats=[Beat(tag="t%d" % i, name="b%d" % i, closed=True)
                                      for i in range(6)])])


def attack_K12_whitespace():
    return Attack(
        metric_id="K12", name="whitespace",
        build=build_K12_whitespace,
        claim="K12 = 1.0 where the entire evidence that a repair happened is the string ' '",
        accidental=False,
        rationale="the guard is `not (r.repair_actions or r.env_actions or r.changed_clause)`, a truthiness "
                  "test, so it separates 'unset' from 'set to anything at all' rather than 'no work' from "
                  "'work'; a space is not something a rig writes by accident, but it bounds how much the guard "
                  "can possibly be asking for.",
    )


def build_K12_no_trace():
    # NOT an attack: the control that shows what the guard rejects.
    return Run(run_id="v9-K12-no-trace", arm="attacker", source="v9",
               repairs=[Repair(episode_id="e0", beats_required=6,
                               beats=[Beat(tag="t%d" % i, name="b%d" % i, closed=True)
                                      for i in range(6)])])


# ---------------------------------------------------------------- K14 (higher)
# K14 = min over concepts of compression_bits, restricted to concepts that
# carry the annotation at all.

def build_K14_single():
    return Run(run_id="v9-K14-single", arm="attacker", source="v9",
               theory=Theory(concepts=[Concept(name="c0", compression_bits=1000000)]))


def attack_K14_single():
    return Attack(
        metric_id="K14", name="single",
        build=build_K14_single,
        claim="K14 = 1000000 bits from a manual containing exactly one concept",
        accidental=True,
        rationale="a minimum over one element is that element, and the natural unit bug -- reporting the total "
                  "encoded size of the corpus rather than the delta the concept bought -- is off by orders of "
                  "magnitude in the favourable direction, so the 1000-bit threshold is cleared by a rounding "
                  "convention rather than by compression.",
    )


def build_K14_censor():
    # The interesting one: 512 concepts, of which 511 are genuinely terrible
    # (large negative accounts) -- but their accounts are simply not recorded,
    # so K14's own filter removes them and the minimum is taken over the one
    # concept that looks good. This is the statistic that is supposed to be
    # the thing "K6's mean hides".
    return Run(run_id="v9-K14-censor", arm="attacker", source="v9",
               theory=Theory(concepts=[Concept(name="good", compression_bits=4096, load_bearing=True)]
                                      + [Concept(name="bad%03d" % i, load_bearing=True)
                                         for i in range(511)],
                             playbook_entries=511, revisions=3))


def attack_K14_censor():
    return Attack(
        metric_id="K14", name="censor",
        build=build_K14_censor,
        claim="K14 = 4096 bits over a manual of 512 concepts, 511 of which carry no compression account at all (support reports concepts=1)",
        accidental=True,
        rationale="K14 filters to concepts whose compression_bits is not None, so the worst-case statistic is "
                  "taken over the self-selected subset the estimator succeeded on; an estimator that gives up "
                  "on exactly the concepts that compress badly produces this shape as its normal output.",
    )


def build_K14_floor():
    # Structurally different again: many concepts, all annotated, none None --
    # a flat floor. Nothing in K14 compares bits to any independent quantity.
    return Run(run_id="v9-K14-floor", arm="attacker", source="v9",
               theory=Theory(concepts=[Concept(name="c%03d" % i, compression_bits=1024,
                                               first_seen_step=i, admitted_revision=0)
                                       for i in range(256)],
                             revisions=1, probes_designed=0))


def attack_K14_floor():
    return Attack(
        metric_id="K14", name="floor",
        build=build_K14_floor,
        claim="K14 = 1024 bits with all 256 concepts annotated -- a constant written into every concept passes the worst-case test",
        accidental=False,
        rationale="a constant per-concept credit is what a stubbed or table-driven estimator emits, but writing "
                  "1024 into 256 records is a choice; it matters because K14 is a min and a min over a constant "
                  "is maximally robust to the very outlier-hunting the metric exists for.",
    )


ATTACKS = [
    attack_K7_sign, attack_K7_silence,
    attack_K8_one_probe, attack_K8_bulk, attack_K8_overflow,
    attack_K9_counter, attack_K9_transcription,
    attack_K10_counter, attack_K10_dressed,
    attack_K11_bookkeeping, attack_K11_empty,
    attack_K12_clause_tag, attack_K12_one_env_action, attack_K12_short_requirement,
    attack_K12_whitespace,
    attack_K14_single, attack_K14_censor, attack_K14_floor,
]
