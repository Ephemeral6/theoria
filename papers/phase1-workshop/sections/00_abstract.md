# Certifying a world theory against something other than its own past

### Phase 1 of Theoria: four offline acceptances, a passive metrics battery,
### an examination instrument, and a live run that spent nothing

**⟨AUTHOR PLACEHOLDER⟩**
⟨AFFILIATION PLACEHOLDER⟩ · ⟨CONTACT PLACEHOLDER⟩

> **Draft status — v0.3.** This is a working draft assembled from the acceptance
> reports already in the repository. Authorship, affiliation and venue are
> unfilled placeholders, and at ~23 000 words it is roughly five times a workshop
> budget — the cut is a separate pass, and no material has been dropped yet in
> order to make it.
>
> v0.2 added three sections — §6 (A3, transfer), §8 (the exam) and §9 (the
> preflight) — and renumbered the two that follow them; the map from v0.1 is
> `papers/phase1-workshop/runs/20260728T092517Z-P6/SECTION_RENUMBER.md`. v0.3
> closes the two gaps that renumbering left. **§7 has been re-derived against
> battery v2** — it reported v0 behind a standing note admitting the battery had
> moved, and every figure in it is now read from `battery/artifacts/*.json`
> rather than from a report's prose. **§11 has a bibliography**:
> `papers/phase1-workshop/references.bib`, 70 records each cross-verified against
> two independent sources, with the traces in
> `papers/phase1-workshop/runs/20260728T102014Z-P7/search-traces/`; no
> `[bib: TODO]` marker survives anywhere in the draft, and the records that could
> not be confirmed twice are named as uncited rather than hedged.
>
> `papers/phase1-workshop/OPEN_ITEMS.md` is the derived checklist of everything
> the two audits left open. `papers/phase1-workshop/REVIEW_TRIAGE.md` sorts the
> referee pass by what each fix costs — writing, re-derivation, or an experiment
> that has not been run.
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

Phase 1 is offline: four acceptances on self-built deterministic worlds, a
metrics battery recomputed over trajectories that already existed, an examination
instrument, and one live run that spent nothing. Eight results.
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

**(5)** A metrics battery recomputed over 95 runs across five arms at zero new
spend, whose harshest reader is its own audit: 34 of 38 executable exploits still
score a metric at or near its best value while possessing none of the capability
it claims to measure, 17 of its written defence claims were contradicted by their
own demonstration, and the exploration family's declared signature separates the
one gradient the design specifies *backwards*. No metric on this pilot can reach
significance in any case — a two-sided sign test over four paired games has a
smallest attainable *p* of 0.125.

**(6)** A theory carried unchanged to a second level of the same game re-fits from a single
frame and wins with zero engine stages, zero adjudicated candidates and zero
theorize rounds, at 252/252 against the referee — while the verification work is
paid in full and at the same rate. Two perturbed levels, each breaking a
mechanism the carried theory does not know about, were both caught, and both were
caught only *after* acting: the free static layer passed them and returned the
same plan. **(7)** An examination instrument with four question types, a marker
calibrated on four synthetic subjects with pre-registered bands, and a leak
checker that reports 1 790 probes with no hits — and which nonetheless missed two
real leaks that an adversarial reader found, because the hook the checker needed
was optional and no paper implemented it. Three of its four papers have never
been sat. **(8)** A live run against the real API that exercised the whole
credential path — key injected in one place, sealed pile untouched by a check on
the bytes — for zero billable actions.

We claim none of the framework's comparative results. No arm was run against a
baseline. No game was played *for* this paper: the battery recomputes over
trajectories that already existed, and the comparative effect sizes it reports
run between two *control* arms — bare Claude Code, and released upstream Schema
trajectories — and across a model ladder within one of them. **None is across the
framework's own arms**, and the Schema side is another team's agent on another
team's infrastructure, so every effect size there bundles capability with
plumbing. The theorize step is a checked-in artefact rather than a measured
language-model step, and every world is small enough for `decide` to enumerate.
The contribution is an instrument and a demonstration artefact — Phase 1
establishes that the instrument exists, that it produces the failure mode on
demand, and that the loop closes on it — not a result about world models.

**Keywords** — world models · program synthesis · unsolvability certificates ·
interactive theorem proving · agent evaluation
