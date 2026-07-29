# P12 — the revision list, and what was done with it

Five reviewers, five seats: (a) domain, (b) methods, (c) reproducibility,
(d) hostile, (e) outside reader. Each read the paper independently and saw no
other review. Their reports are beside this file.

**Nothing here was actioned on a reviewer's word.** Every finding below was
re-derived from the artefact before the paper was touched, and three were refuted
that way. That is not ceremony: this session has already published two wrong
numbers today that came from checks narrower than the claims they licensed.

---

## Applied — three findings, all verified first

### 1 · A3's transfer accuracy does not discriminate, and the control was not printed

**Severity: the worst finding of the round.** §6 reported that the carried manual
scores **252 of 252** on a level it never explored. The third row of the same
artefact is "the control arm's manual, induced from level 2's own sweep", and it
scores **252 of 252** as well
(`cold-start-a3/artifacts/score_vs_truth.json`, `results[2]`,
`theory/generated_l2_scratch/`). The paper printed one and not the other.

Verified by reading the artefact, not the review. Both arms sit at ceiling, so
**the accuracy measurement cannot separate transfer from induction at all**; the
transfer claim can only live in §6.2's bill. §6 and the abstract's result (6) now
say so. Reporting one arm's ceiling alone is the same one-sided denominator this
paper spends §7 criticising in someone else's instrument.

### 2 · The main table contains a metric the battery has already retired

`battery/artifacts/gaming_audit.json` puts **K7** in `main`; `battery/artifacts/redundancy.json`
lists **K7** in `eliminated`, retired into K5 at ρ = 1.000 over 5 shared runs.
Both are true, neither process is wrong on its own terms — the anti-gaming audit
asks whether a metric can be cheated, de-redundancy asks whether it says anything
its representative does not — but nothing reconciles them, and §7.7 printed K7
among the nine while §7.9 printed it among the five retirements, twenty lines
apart, without noticing.

This is a class of defect the P11 pass could not catch: **both artefacts agree with
the paper individually, and contradict each other.** Checking the paper against the
artefacts one claim at a time will never surface it. §7.9 now states the collision.

### 3 · "Near-total evidence" was measured on half the world

§5.2's *163 of 164* is correctly scoped in the paper — "with the Cart in the left
room" — but the same artefact records the full sweep at **220 of 220** over every
reachable state. So the history is **163 of 220, 74 %**, and the paragraph
summarised it as "near-total evidence". The narrow claim survives and is what the
exhibit needs: within the region the history covers, coverage is near-total and the
defect still survives. It is not evidence that near-total coverage of a *whole*
world would have caught it. §5.2 now carries both denominators.

---

## Refuted — three findings that did not survive checking

* **"Six of seven cited figure paths do not exist"** (reviewer e, filed BLOCKING).
  All nine `figures/…` paths cited by `PAPER.md` resolve. The reviewer looked under
  `papers/phase1-workshop/figures/`, the deprecated parity witness, instead of the
  repo-root pipeline. The confusion is real and is its own item (P13); the defect is
  not.
* **"Zero ARC-AGI citations"** (reviewer a, filed BLOCKING) — *nearly* right, and
  the correction matters. The bibliography has exactly one ARC-AGI record,
  `zeng2026schema`, and it cites the *harness*, not the benchmark. So the benchmark
  this paper is about is indeed uncited. See below for why it stays that way today.
* **"The paper's Figure-1 decision count is now stale"** — my own hypothesis while
  fixing the figure pipeline, not a reviewer's. The two new upstream log entries
  emit `no-proposal-ABSENT` and `ledger-logged`, neither an adjudication; the parity
  witness still rules seventeen. Recorded because filing it was one step away.

---

## Diagnosed correctly, and deliberately not actioned

**The missing literature — and this is a blocker, not a deferral.** Reviewer (a) is
right that four literatures are absent from a 70-record bibliography: the ARC-AGI
benchmark itself; theory-based RL and symbolic world models (EMPA, Schema
Networks — the latter is zero-shot transfer of an induced object-level model to
perturbed variants of the same game, which is §6.3's design); LLM→PDDL work, which
contests §11.2's stated delta; and LLM-agent literature at an LLM-agents venue.
`cropper2021popper` and `evans2018dilp` are already *in* the file and uncited.

**They cannot be added in this session, and adding them would be worse than
leaving them.** The paper's own red line 6 says a bibliographic record that could
not be cross-verified against two independent sources is not cited — "not softened,
not hedged — absent" — and this session has no network. Citing from memory is
exactly the failure the rule exists to prevent, in a section whose value is that it
did not do that. Escalated instead: it needs a session with browsing, or OPS-B.

**The structural recommendation both independent reviewers reached.** (a) and (e)
never saw each other and converged: the executable anti-gaming register (§7.7) is
the paper's widest daylight and is buried as item four of four; (e) independently
proposed cutting the paper to §7.7 + §7.4 + §8.3. That is a restructuring decision
about what the paper *is*, at ~24 600 words against a ~4 000-word budget. It is the
right next item and it is not a revision-list line.

---

## Inherited from the other holders, and one disagreement left open

While RES-2 was quota-stalled the board reissued P12 twice, and **all three
holders worked the same worktree**. W-1632 and W-1651 left substantial uncommitted
material here — a second hostile review (`review-d-adversarial.md`), a bibliography
proposal (`bib-additions.md`), a reference-gap note, a gate diagnosis, and
`papers/phase1-workshop/verify_paper.py`, a paper-level checker that classifies
every cited path and re-runs the figure extractors. It is committed as theirs,
under their names, because losing it would be the worse error and I cannot write
their `PARTNER_SYNC` paragraphs for them.

**W-1651's checker independently found the same defect P13 found from the other
end.** Its `B PATHS` check reports `figures/…` as AMBIGUOUS because `figures/`
exists both at the repo root and beside `PAPER.md` — which is the three-numbering-
authorities problem, reached from citation resolution rather than from a red build
gate. Two agents, two directions, same underlying fault: strong evidence it is real.

**The disagreement, left open rather than settled.** `verify_paper.py`'s
`C FIGDATA` check fails because the committed `fig1_concept_timeline.json` payload
is older than `cold-start-a0/THEORIZE_LOG.md`, which the other track keeps
appending to. W-1651 argues the fix is *not* to regenerate, on the grounds that
`sections/10_limitations.md:41` says A0's expressivity ledger has **five** gaps and
regenerating would show nine.

I do not think that follows, and I have not acted on either reading. The paper's
sentence is scoped — "**A0's run** produced an expressivity ledger of five gaps" —
and it enumerates them, E-01 to E-05. E-06 and E-07 came later, and E-08 and E-09
were forced by `worldgen`'s `t2-lock-fragile`, which is not A0. All four are marked
`discharged` in the log. So the ledger's total moving from five to nine does not
make "A0's run produced five" false, and regenerating the payload would not
contradict the paper — the paper cites `THEORIZE_LOG.md §E` directly, not the
payload.

**And then the reproducibility reviewer settled it against me.** It reached the
same conclusion as W-1651 independently, and supplied the reason I had not
checked: §4 books **E-06 to A1**, not to A0. So the ledger's entries belong to
different acceptances, and a regenerated payload presenting all nine as A0's
ledger would misattribute four of them — which is a stronger objection than the
count-of-five one I was arguing against, and it holds. **I was wrong; the payload
is left as committed, and not because two agents outvoted me.** Recorded in full
rather than quietly dropped, because the reasoning I used — "the paper's sentence
is scoped to A0's run, so the total moving does not falsify it" — was correct as
far as it went and still reached the wrong action.

The `C FIGDATA` check therefore stays red on purpose, and that is the awkward part
worth naming: a stop gate that is red because the right answer is "do not fix
this" will be indistinguishable, in a month, from one that is red because nobody
got round to it.

## What this round says about the review method

The three findings that were applied all share a shape: **they are contradictions
between two sources, not errors within one.** The A3 control sits in the same file
as the number the paper quoted; K7's two verdicts sit in two artefacts that each
agree with the paper; the A2 coverage figure sits beside its own fuller denominator.
P11 checked every claim against its cited artefact and found twenty-one defects —
and could not have found any of these three, because each claim *does* match the
file it cites.

The seat that found them was the hostile one. The two seats that found nothing
applicable were the two that cannot check arithmetic: the domain referee, whose
findings are all about what is absent, and the outside reader, who is instructed
not to look anything up. That is not a criticism of either — the outside reader
produced the only assessment of whether the paper is *readable*, and its answer is
no. But if a future round has to run fewer than five seats, **the hostile and
reproducibility seats are the ones that pay for themselves.**
