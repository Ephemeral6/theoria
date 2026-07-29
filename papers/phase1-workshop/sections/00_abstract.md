# Neither layer certifies the manual against the world

### Phase 1 of Theoria: an explicit, machine-checkable world theory run offline on
### worlds we built ourselves — and a metrics battery attacked by its own
### executable exploit register

**⟨AUTHOR PLACEHOLDER⟩**
⟨AFFILIATION PLACEHOLDER⟩ · ⟨CONTACT PLACEHOLDER⟩

> **Draft status — v0.4.** A working draft assembled from the acceptance reports
> already in the repository. Authorship, affiliation and venue are unfilled
> placeholders, and at roughly 23 700 words it is about five times a workshop
> budget; the cut is a separate pass and no material has been dropped to make it.
> v0.4 rewrote this abstract and §1 against five independent reviews
> (`papers/phase1-workshop/runs/20260728T173000Z-P12-paper-multi-review/`); the
> changes of substance, rather than of arrangement, are listed in
> `papers/phase1-workshop/runs/20260729T125500Z-P13-paper-intro-abstract/RUN_STATE.md`.
>
> **The binding rule.** Every quantitative claim in the body carries the
> repo-relative path of the artefact it came from;
> `papers/phase1-workshop/PROVENANCE.md` is the index. **The abstract is the one
> exemption, by convention** — and the exemption holds only because every figure
> below recurs, cited, in the body. The rule is tested mechanically rather than
> asserted: `papers/phase1-workshop/verify_paper.py` checks that `PAPER.md` is
> what `assemble.py` generates and that every path cited in the sections
> resolves; `papers/phase1-workshop/CITECHECK.md` is a path/number/quote audit and
> `papers/phase1-workshop/REVIEW.md` an adversarial referee pass. Both reports are
> kept unedited, including the unflattering parts, so a reader can see what the
> rule caught. `papers/phase1-workshop/OPEN_ITEMS.md` is the derived checklist of
> what the audits left open; `papers/phase1-workshop/REVIEW_TRIAGE.md` sorts the
> referee pass by what each fix costs.

---

## Abstract

**ARC-AGI-3 drops an agent into a small world it has never seen** — a 64×64 grid,
sixteen colours, deterministic rules, the rules hidden — and lets it do two
things: act, and look. The strongest published result on it makes the world model
an editable, executable program and verifies that program by replaying the entire
recorded history against it. But a model that replays its own history perfectly
can still be bankrupt as an account of the world, and the error is invisible to
precisely that check. Each wave of this lineage has upgraded the same thing — the
*checking regime* — and the regime has stopped at "true of what already happened".

We report the closed-system phase of Theoria, a framework in which the world model
is an explicit, hand-maintained theory: a **manual** saying what the world is and
a **playbook** saying how to win, compiled to four co-derived forms and certified
in two layers — full-history replay at the pixel, and declared laws discharged in
Lean with the axiom list inspected. Neither layer certifies the manual against the
world. This paper is mostly about what that costs, and the most damaging evidence
for it comes not from the framework's runs but from our own measuring instrument.

**The strongest result is a negative one about our own metrics.** We wrote a
38-metric battery to score this work, and a register saying, for each metric, how
it could be cheated and whether it had been defended. Rewriting that register from
prose into executable exploits — each one a fabricated trajectory that the
battery's own scorer grades, with success recomputed from the scorer rather than
asserted by the author — showed that **34 of the 38 metrics can be driven to a
good score by a run possessing none of the capability being measured**, and that
**17 of the register's own written entries were contradicted by their own
demonstration, 14 of them claims that a metric had been defended**. A later blind
round — six mutually invisible attackers working from a stripped source tree,
against success criteria committed before any attack — moves every one of those
numbers further in the same direction and takes the table of metrics considered
safe for ranking arms from nine to zero. A subsidiary finding is upstream of
cheating altogether: for any two manuals differing by one clause, the epistemic
family contains a metric preferring each, so it cannot rank them at all.

**The pipeline, offline.** Three acceptances on worlds we built ourselves, plus an
early read on a claim the mandate does not list as an acceptance. On a 9×9 world,
the induced manual replays 276/276 frames and 22 356/22 356 pixels with zero
anomalies and is nonetheless wrong on all three of the 236 reachable
(state, action) pairs the trajectory never covered — accuracy 0.000 over three
pairs (n = 3). The miss was written down in the adjudication log, by direction,
*before* the ground truth was opened. A second world, in which an irreversible
latch becomes a reversible toggle, yields a manual that is 228/228 correct while
covering only 47 % of its own state-action pairs; the two worlds differ in four
ways at once, so this is a design lesson demonstrated by construction rather than
a hypothesis tested. A pagoda-style impossibility certificate computed by a linear
program in one track crosses a JSON boundary into a second, which re-verifies
every obligation rather than trusting the producer and emits a Lean proof with an
empty axiom list — shown to be non-decorative by a negative control that makes it
fail. And an exhibit: a manual with one rule deleted passes replay at 100 %, its
planner returns UNSAT, and Lean signs an axiom-free impossibility theorem that an
18-action episode refutes; the repair loop then closes in six recorded beats. The
artefact is a *pair* of Lean files identical in generator, tactic, dependency
surface and axiom list — `#print axioms` returns `[]` for both — of which one is
true of its world and the other is not. The instrument cannot tell them apart and
is not supposed to. That is a demonstration of a failure mode, not evidence about
anything.

The remaining sections report, without claiming: a theory carried unchanged to a
second level of the same self-built world, which re-fits from one frame and wins
with zero engine stages and zero adjudicated candidates while paying verification
in full — both arms score 252/252 against the referee, so the saving is in what
each cost and not in what either got right; an examination instrument whose leak
checker reports 1 790 probes with no hits and which nonetheless missed two real
leaks an adversarial reader found, and three of whose four papers have never been
sat; and two live runs against the real API on one development-pile game — a
preflight that sent 18 commands for zero billable actions and zero dollars, and a
first-contact run that spent seven actions and $6.32 in model calls, whose
manifest carries the byte-level scan showing no sealed-pile game was touched.

**What we do not claim.** No arm was run against another system's baseline, there
is no language-model baseline anywhere in this paper, and the three arms of the
transfer section are all ours. No game was played *for* this paper: the battery
recomputes over trajectories that already existed, and the comparative effect
sizes it reports run between two *control* arms — bare Claude Code, and released
upstream Schema trajectories — and across a model ladder within one of them.
**None is across the framework's own arms**, and the Schema side is another team's
agent on another team's infrastructure, so every effect size there bundles
capability with plumbing. Those effect sizes are unpaired, and on the one metric
this paper bolds the paired test disagrees with them. The theorize step is a
checked-in artefact rather than a measured language-model step, and every world is
small enough for `decide` to enumerate. Transfer, the exam, the ordering claim and
the cost magnitude are reported here and claimed nowhere. **The contribution is an
instrument, a demonstration artefact, and a negative result about our own
measurements** — Phase 1 establishes that the instrument exists, that it produces
the failure mode on demand, and that the loop closes on it — not a result about
world models.

**Keywords** — world models · program synthesis · unsolvability certificates ·
interactive theorem proving · metric gaming
