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
    pairs, agree = run.theory.held_out_pairs, run.theory.held_out_agree
    if not pairs:
        return thin("K2", "no held-out pairs; every reachable pair was covered")
    return ok("K2", agree / pairs, agree=agree, pairs=pairs)


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
