# Certifying a world theory against something other than its own past

### Phase 1 of Theoria: three offline acceptances and a passive metrics battery

**⟨AUTHOR PLACEHOLDER⟩**
⟨AFFILIATION PLACEHOLDER⟩ · ⟨CONTACT PLACEHOLDER⟩

> **Draft status.** This is a working draft assembled from the acceptance
> reports already in the repository. Authorship, affiliation, venue and
> bibliography are unfilled placeholders, and at ~11 500 words it is roughly
> three times a workshop budget — the cut is a separate pass, and no material has
> been dropped yet in order to make it.
>
> **The binding rule.** Every quantitative claim in the body carries the
> repo-relative path of the artefact it came from;
> `papers/phase1-workshop/PROVENANCE.md` is the index. The abstract is the one
> exemption, by convention — each figure in it is cited where it recurs in the
> body. The rule is tested mechanically rather than asserted:
> `papers/phase1-workshop/CITECHECK.md` is a path/number/quote audit of this
> draft and `papers/phase1-workshop/REVIEW.md` an adversarial referee pass, both
> run against the first assembled version. Their findings were applied, and both
> files are kept unedited — including the parts that are unflattering — so a
> reader can see what the rule caught.

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
reachable (state, action) pairs — accuracy 0.000, over the three pairs (n = 3)
the trajectory could never contain. The miss was named in the adjudication log,
by direction, *before* the ground truth was opened. **(2)** A second world, in
which an irreversible latch is replaced by a reversible toggle and the explorer
is truncated to under half the state-action coverage, yields a manual that is
228/228 correct. Reversibility of a mechanism mattered more than breadth of
trajectory — a design lesson demonstrated by construction rather than a
hypothesis tested. In the same world, a deliberately seeded replay-invisible
clause was caught by a coverage probe and, unplanned, by the Lean transcription,
and repaired in one revision. **(3)** A pagoda-style impossibility certificate
computed by a linear program in one track crosses a JSON data boundary into a
second track developed alongside it, which re-verifies every obligation rather
than trusting the producer, and emits a Lean proof with an empty axiom list — a
check shown to be non-decorative by a negative control that makes it fail. Where
the invariant language cannot carry a conclusion, the compiler refuses to
generate rather than narrowing the theorem. **(4)** An exhibit: a manual with one
rule deleted passes replay at 100 %, its planner returns UNSAT, and Lean signs an
axiom-free impossibility theorem that an 18-action episode refutes. The
refutation loop then closes in six recorded beats. The headline artefact is a
*pair* of Lean files, identical in generator, tactic, dependency surface and
axiom list — the instrument returns `[]` for both — where one is true of its
world and the other is not. The instrument cannot tell them apart, and is not
supposed to.

The battery, run over 26 existing trajectories at zero new spend, immediately
found three of its own metrics measuring something other than what they claim,
and reports that no metric on this pilot can reach significance — a two-sided
sign test over four paired games has a smallest attainable *p* of 0.125.

We claim none of the framework's comparative results. No arm was run against a
baseline. No game was played *for* this paper: the battery recomputes over
trajectories that already existed, and the comparative effect sizes it reports
are across a model ladder within one control arm, not across the framework's
arms. The theorize step is a checked-in artefact rather than a measured
language-model step, and every world is small enough for `decide` to enumerate.
The contribution is an instrument and a demonstration artefact — Phase 1
establishes that the instrument exists, that it produces the failure mode on
demand, and that the loop closes on it — not a result about world models.

**Keywords** — world models · program synthesis · unsolvability certificates ·
interactive theorem proving · agent evaluation
