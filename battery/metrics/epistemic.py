"""Epistemic — the quality of the books themselves, not the behaviour.

`Theoria.md`: *行为之外，两本书本身的质量*. This is the family only a
theory-bearing arm can answer, and on A0 it is the family with the most real
data behind it.

The pair to watch is **K1 against K2**. K1 is full-history replay accuracy —
the metric the field already optimises, and precisely the one that cannot see a
missing rule, because a rule you never had evidence for is a rule the history
never exercises. K2 is accuracy on the state-action pairs the trace never
covered. The gap between them is the DC22 shape: a manual that is 98.7%
right on everything it has seen and 0% right on everything it has not.

A0 shows that gap at its most extreme, and it is not an artefact of the
instrument — `cold-start-a0/THEORIZE_LOG.md` R-05 predicted the three failing
pairs, by name and for the right reason, before the score existed.
"""

from __future__ import annotations

from battery.metrics import metric, ok, thin
from battery.model import Run

THEOREM_KINDS = ("invariant", "theorem")


@metric("K1", "epistemic",
        "Full-history exact replay accuracy: the fraction of observed "
        "state-action pairs on which the manual agrees with the world.",
        needs=("theory",), direction="higher", unit="share")
def replay_accuracy(run: Run):
    pairs, agree = run.theory.replay_pairs, run.theory.replay_agree
    if not pairs:
        return thin("K1", "no replay score recorded for this run")
    return ok("K1", agree / pairs, agree=agree, pairs=pairs)


@metric("K2", "epistemic",
        "Accuracy on state-action pairs the trace never covered. The metric "
        "replay cannot see.",
        needs=("theory",), direction="higher", unit="share")
def held_out_accuracy(run: Run):
    """The metric replay cannot see — and the one that must say what it saw.

    **A held-out accuracy is meaningless without its sampling frame.** This
    battery holds two runs reporting a `K2`, and they do not mean the same
    thing: A0's denominator is the 3 state-action pairs its trace happened
    never to cover, a0-spike's is an exhaustive enumeration of all 39960
    well-formed pairs. `model.py` carries `held_out_frame` and says at length
    that it exists to stop those two being compared — and until v2.1 no metric
    read it, so a held-out set of **one** pair scored 1.000 and looked
    identical to the exhaustive one. `battery/audit/exploits/` demonstrates it.

    The guard is a *declared frame*, not a denominator floor. A floor is the
    obvious fix and it is the wrong one: any floor above 3 destroys A0's
    K2 = 0.000, which is the DC22 result — a manual replaying at 98.7% and
    scoring zero off-trace — and that is a real finding, not an artefact of a
    thin denominator.
    """
    pairs, agree = run.theory.held_out_pairs, run.theory.held_out_agree
    if not pairs:
        return thin("K2", "no held-out pairs; every reachable pair was covered")
    if not run.theory.held_out_frame:
        return thin("K2", "the held-out set declares no sampling frame, so "
                          "this ratio cannot be compared with any other K2 -- "
                          "a denominator of 3 adversarial gaps and one of "
                          "39960 exhaustive cases are different quantities "
                          "sharing a name")
    return ok("K2", agree / pairs, agree=agree, pairs=pairs,
              frame=run.theory.held_out_frame)


@metric("K3", "epistemic",
        "Invariants and theorems in the manual.",
        needs=("theory",), direction="higher", unit="count")
def theorem_count(run: Run):
    return ok("K3", sum(1 for c in run.theory.clauses
                        if c.kind in THEOREM_KINDS))


@metric("K4", "epistemic",
        "Mean coverage over clauses the manual annotates with one; the "
        "count of unannotated clauses is reported alongside, not folded in.",
        needs=("theory",), direction="higher", unit="share")
def evidence_coverage(run: Run):
    clauses = run.theory.clauses
    annotated = [c for c in clauses
                 if c.coverage_num is not None and c.coverage_den]
    if not annotated:
        return thin("K4", "no clause carries a coverage annotation")
    ratios = [c.coverage_num / c.coverage_den for c in annotated]
    return ok("K4", sum(ratios) / len(ratios), annotated=len(annotated),
              unannotated=len(clauses) - len(annotated),
              min_witnesses=min((c.evidence_transitions for c in clauses
                                 if c.evidence_transitions is not None),
                                default=None))


@metric("K5", "epistemic",
        "Concepts admitted to the manual's word table.",
        needs=("theory",), direction="higher", unit="count")
def vocabulary_size(run: Run):
    if not run.theory.concepts:
        return thin("K5", "the manual names no concepts")
    return ok("K5", len(run.theory.concepts))


@metric("K6", "epistemic",
        "Mean compression gain per admitted concept, in bits. Positive means "
        "the concept paid for itself.",
        needs=("theory",), direction="higher", unit="bits")
def mean_compression_gain(run: Run):
    gains = [c.compression_bits for c in run.theory.concepts
             if c.compression_bits is not None]
    if not gains:
        return thin("K6", "no concept carries a compression account")
    return ok("K6", sum(gains) / len(gains), concepts=len(gains),
              worst=min(gains), best=max(gains))


@metric("K7", "epistemic",
        "Concepts admitted despite a negative compression account. A "
        "diagnostic, not a score: it counts a live conflict between two of "
        "the framework's own admission criteria.",
        needs=("theory",), direction="neutral", unit="count")
def negative_gain_concepts(run: Run):
    """The O-04 finding, made countable.

    Theoria 1.8 admits a concept when it shortens the manual; constraint 2
    demands that every pixel be explained by *something*. On A0 those two
    rules disagreed about the Button and the Door, and the adjudication chose
    responsibility over compression. Counting the disagreements is how we find
    out whether that was an A0 accident or a structural hole — which is why
    this metric is neutral-direction. A high count is not a bad arm; it is a
    framework question that needs answering.
    """
    gains = [c.compression_bits for c in run.theory.concepts
             if c.compression_bits is not None]
    if not gains:
        return thin("K7", "no concept carries a compression account")
    negative = sum(1 for g in gains if g < 0)
    return ok("K7", negative, of_concepts=len(gains))


@metric("K8", "epistemic",
        "Executable probes as a fraction of probe designs. Low means the "
        "probe machinery proposed experiments it could not run.",
        needs=("theory",), direction="higher", unit="share")
def probe_executable_rate(run: Run):
    designed = run.theory.probes_designed
    if not designed:
        return thin("K8", "no probes were designed")
    return ok("K8", run.theory.probes_executable / designed,
              executable=run.theory.probes_executable, designed=designed)


@metric("K9", "epistemic",
        "Entries in the playbook — ordering, pruning, heuristics, "
        "preferences.",
        needs=("theory",), direction="higher", unit="count")
def playbook_entries(run: Run):
    if not run.theory.playbook_entries:
        return thin("K9", "the arm has no playbook")
    return ok("K9", run.theory.playbook_entries)


@metric("K10", "epistemic",
        "Deadlock theorems: machine-checked proofs that a region of the "
        "search space can never reach the goal.",
        needs=("theory",), direction="higher", unit="count")
def deadlock_theorems(run: Run):
    """The thing no baseline can produce.

    A bare agent that cannot win a level gives up; it cannot hand you a
    certificate that the level is unwinnable. `Theoria.md` Phase 4 calls this
    the cheapest possible witness that the machine did something people do not.
    """
    return ok("K10", run.theory.deadlock_theorems)


@metric("K11", "epistemic",
        "Manual revisions. The concept-birth timeline's coarse axis.",
        needs=("theory",), direction="neutral", unit="count")
def manual_revisions(run: Run):
    """Deliberately neutral-direction, and here mostly as a warning.

    On A0 the manual was revised zero times *by certify* — the cheap layer and
    the Lean layer both went green on their first run. `THEORIZE_LOG.md` is
    blunt that this is the loop not being exercised rather than the loop
    working, so a low count is ambiguous between "got it right first time" and
    "never got checked". Until the theorize->certify loop has produced a
    genuine revision, this number ranks nothing.
    """
    return ok("K11", run.theory.revisions)


@metric("K12", "epistemic",
        "Share of the six repair beats — 打脸→定位→戳探→修订→重证→解出 — "
        "that closed.",
        needs=("repairs",), direction="higher", unit="share")
def repair_loop_closure(run: Run):
    """U4's yes-or-no half: 被打脸后修得好吗.

    `Theoria.md` 1.11 makes U4 one of four **ordering** questions (排座次) and
    says in the same breath that they are 不当证据 — not evidence. So this is
    reported and never cited: no number computed here may support claim C1.

    The six beats are an order, not a set. A loop that revises the manual but
    never re-proves it has produced an unverified edit; a loop that re-proves
    but never solves has not shown the repair was worth anything. Reporting the
    fraction rather than a boolean is what makes a *partial* loop visible —
    a0-spike detects a broken rule and re-mines the world, which is real work
    and closes none of the six beats, and a boolean would score that identically
    to having done nothing.
    """
    if not run.repairs:
        return thin("K12", "no repair episodes")

    # A closed beat has to be a beat that happened.  Until v2.1 this read six
    # self-reported booleans out of a file the producer wrote, so an episode
    # declaring all six closed while spending nothing and changing nothing
    # scored 1.000 -- identical to A2, which spent 48 environment actions and
    # rewrote `teleport_down`.  `battery/audit/exploits/` demonstrates it.
    #
    # The requirement is deliberately at the *episode* level and not per beat.
    # `model.py` is explicit that localisation and re-proof are offline work
    # and honestly cost zero environment actions, so demanding a cost per beat
    # would refuse the real loops along with the invented one.  What an episode
    # may not do is claim closed beats while showing neither a cost nor an edit.
    unevidenced = [r.episode_id for r in sorted(run.repairs,
                                                key=lambda r: r.episode_id)
                   if r.beats_closed
                   and not (r.repair_actions or r.env_actions
                            or r.changed_clause)]
    if unevidenced:
        return thin("K12", "episode(s) %s report closed beats while showing "
                           "neither environment cost nor a changed clause; a "
                           "loop that left no trace of having run is a claim, "
                           "not a repair" % ", ".join(unevidenced))

    closed = sum(r.beats_closed for r in run.repairs)
    required = sum(r.beats_required for r in run.repairs)
    if not required:
        return thin("K12", "no repair episode declares a beat requirement")
    return ok("K12", closed / required, closed=closed, required=required,
              episodes=len(run.repairs),
              per_episode={r.episode_id: "%d/%d" % (r.beats_closed,
                                                    r.beats_required)
                           for r in sorted(run.repairs,
                                           key=lambda r: r.episode_id)})


@metric("K13", "epistemic",
        "Environment actions spent repairing, over the actions the original "
        "theory cost. Low means the repair was localised.",
        needs=("repairs",), direction="lower", unit="ratio")
def repair_cost_ratio(run: Run):
    """What repairing actually costs, in the only currency anyone recorded.

    **This is a measurement of repair *strategy* at least as much as of the
    arm, and the two cannot be separated on the material in hand.** A2 locates
    the culprit clause, probes it and patches it. a0-spike re-mines the entire
    world from fresh evidence. A patch coming in at a fraction of a rebuild is
    not a discovery about which arm is better; it is arithmetic about patching.
    `PREDICTIONS.md` registers the confound rather than letting the ratio be
    read as a ranking, and the audit puts this in the reference tier for it.

    The currency is environment actions because it is the only cost any
    producer wrote down: neither A2 nor a0-spike records tokens, wall time, or
    model calls for a repair. That is itself a finding — U4's measurement unit
    is undefined in `Theoria.md`, and the battery has picked the one the
    artefacts can support, not the one that would be most informative.
    """
    ratios = {}
    for repair in sorted(run.repairs, key=lambda r: r.episode_id):
        spent = (repair.repair_actions if repair.repair_actions is not None
                 else repair.env_actions)
        base = repair.baseline_actions
        if not base or spent is None:
            continue
        ratios[repair.episode_id] = spent / base
    if not ratios:
        return thin("K13", "no repair episode records both its own cost and "
                           "the cost of the theory it repaired")
    values = [ratios[k] for k in sorted(ratios)]
    strategies = sorted({r.strategy for r in run.repairs})
    return ok("K13", sum(values) / len(values), episodes=len(values),
              per_episode={k: round(v, 6) for k, v in sorted(ratios.items())},
              strategy=strategies[0] if len(strategies) == 1 else strategies)


@metric("K14", "epistemic",
        "Minimum per-concept compression gain in bits. The statistic K6's "
        "mean hides.",
        needs=("theory",), direction="higher", unit="bits")
def min_compression_gain(run: Run):
    """The honest version of K6, and the fix REPORT_V0 asked for.

    K6 reports A0's mean at +706 bits. That mean is carried entirely by one
    concept at +2125 while two of the three are negative — so the headline
    says the vocabulary paid for itself and the distribution says two thirds of
    it did not. The minimum cannot be rescued by one large concept, which is
    exactly the property wanted here.

    K7 counts how many concepts were admitted against their compression
    account; this prices the worst of them. Reading them together is the
    intended use, and a negative minimum on every theory-bearing arm is the
    prediction that the O-04 conflict is structural rather than an accident of
    A0.
    """
    gains = [c.compression_bits for c in run.theory.concepts
             if c.compression_bits is not None]
    if not gains:
        return thin("K14", "no concept carries a compression account")
    worst = min(gains)
    return ok("K14", worst, concepts=len(gains), best=max(gains),
              mean=round(sum(gains) / len(gains), 6),
              worst_concept=sorted(
                  c.name for c in run.theory.concepts
                  if c.compression_bits == worst)[0])
