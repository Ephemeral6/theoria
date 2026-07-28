# Certifying a world theory against something other than its own past

### Phase 1 of Theoria: three offline acceptances and a passive metrics battery

**⟨AUTHOR PLACEHOLDER⟩**
⟨AFFILIATION PLACEHOLDER⟩ · ⟨CONTACT PLACEHOLDER⟩

> **Draft status.** This is a working draft assembled from the acceptance
> reports already in the repository. Authorship, affiliation, venue and
> bibliography are unfilled placeholders. Every quantitative claim carries the
> repo-relative path of the artefact it came from; `PROVENANCE.md` is the index.

---

## Abstract

A world model that replays its own history perfectly can still be wrong about
the world, and the error is invisible to the check the field usually runs. We
report the closed-system phase of a framework in which the world model is an
explicit, hand-maintained theory — a manual saying what the world is and a
playbook saying how to win — compiled to four co-derived forms and certified in
two layers: full-history replay at the pixel, and declared laws discharged in
Lean with the axiom list inspected.

Phase 1 is offline: three acceptances on self-built deterministic worlds, plus a
metrics battery recomputed over trajectories that already existed. Four results.
**(1)** On a 9×9 self-built world, the induced manual replays 276/276 frames and
22 356/22 356 pixels with zero anomalies and is nonetheless wrong on 3 of 236
reachable (state, action) pairs — accuracy 0.000 on the three the trajectory
could never contain. The miss was named, with its three pairs, in the
adjudication log *before* the ground truth was opened. **(2)** A second world,
identical except that an irreversible latch becomes a reversible toggle and the
explorer is truncated to under half the state-action coverage, yields a manual
that is 228/228 correct. Reversibility of a mechanism mattered more than breadth
of trajectory; in the same world, a deliberately seeded replay-invisible clause
was caught independently by a coverage probe and by the Lean transcription, and
repaired in one revision. **(3)** A pagoda-style impossibility certificate
computed by a linear program in one track crosses a JSON data boundary into a
second, independently developed track, which re-verifies every obligation rather
than trusting the producer, and emits a Lean proof with an empty axiom list — a
check shown to be non-decorative by a negative control that makes it fail.
Where the invariant language cannot carry a conclusion, the compiler refuses to
generate rather than narrowing the theorem. **(4)** An exhibit: a manual with one
rule deleted passes replay at 100 %, its planner returns UNSAT, and Lean signs an
axiom-free impossibility theorem that an 18-action episode refutes. The
refutation loop then closes in six recorded beats. The headline artefact is a
*pair* of Lean files, identical in generator, tactic, dependency surface and
axiom list, differing only in a weight table — one true of its world, one not.
The instrument cannot tell them apart, and is not supposed to.

The battery, run over 26 existing trajectories at zero new spend, immediately
found three of its own metrics measuring something other than what they claim,
and reports that no metric on this pilot can reach significance — a two-sided
sign test over four paired games has a smallest attainable *p* of 0.125.

We claim none of the framework's comparative results. No arm was run against a
baseline; no benchmark game was played for any result here; the theorize step is
a checked-in artefact rather than a measured language-model step; every world is
small enough for `decide` to enumerate. What Phase 1 establishes is that the
instrument exists, that it produces the failure mode on demand, and that the loop
closes on it.

**Keywords** — world models · program synthesis · unsolvability certificates ·
interactive theorem proving · agent evaluation
