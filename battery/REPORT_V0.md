# Battery v0 — what the first full recompute found

Recomputed over every trajectory in the repository: 26 runs, 4 development-pile
games, 2 arms. Artefacts in [`artifacts/`](artifacts/), regenerable with
`python -m battery.run_battery` and byte-identical on a re-run.

Zero new game spend, zero model calls, zero network. That is the whole point of
a passive instrument.

---

## The headline: a metric can be perfect and still be measuring the wrong thing

A0's manual scores **K4 evidence coverage = 1.000** and **K2 held-out accuracy
= 0.000**, on the same manual, from the same recompute.

Those are not in tension by accident. The manual scores perfect evidence
coverage *because* it refused the one generalisation it lacked evidence for —
`cold-start-a0/THEORIZE_LOG.md` R-05 rejects "the Button is pressable from any
direction" on the grounds that the evidence for three of the four directions is
"not thin, zero". That refusal is what makes every clause fully supported. It
is also, exactly, why the three state-action pairs the trace never covered are
the three the manual gets wrong.

**Evidence coverage rewards precisely the caution that held-out accuracy
punishes.** A battery reporting K4 alone would show a flawless manual. The
gaming audit therefore demotes K4 to the reference tier with the instruction
that it is never to be reported without K2 beside it.

The same recompute puts numbers on the DC22 shape the design predicted: replay
accuracy 0.987 against held-out accuracy 0.000. Replay is the metric the field
already optimises, and on this manual it is 98.7% right while being 0% right
about everything it had not already seen.

## The pilot ledger cannot certify any metric, and says so

Every discriminative verdict came back `underpowered` or `no-data`. This is not
a soft finding — it is arithmetic:

> A two-sided sign test over 4 paired games has a smallest attainable p of
> **0.125**. No metric can reach p < 0.05 on this data however cleanly it
> separates. **Six** non-tied paired games are the minimum for the test to be
> able to clear the bar at all.

That number is now emitted in `discrimination.json` on every run, so nobody
reads a p of 0.125 as a near miss. It is also a concrete input to Phase 3
planning: the development pile has four games, so the confirmatory design needs
either repeats per game or a larger pile.

## Three metrics are measuring something other than what they claim

Found by running the instrument, not by inspecting it.

**P1 (actions per model call) is largely an API failure-rate readout.** It
separates the model ladder strongly — Cliff's δ = −1.000 — and *backwards*:
haiku gets 0.97 actions per call, opus 0.52. The explanation is in the
infrastructure, not the models. Between 27% and 45% of steps in the pilot
failed outright, on HTTP 500s and "game not found", and P1 divides *successful*
actions by *all* calls. A run whose infrastructure failed more looks like a run
that planned less. P1 correlates with the failure rate at **ρ = −0.83**.

Rather than leave that in prose, v0 adds **P5 `step_failure_rate`** as a
diagnostic metric so the confound appears in the spectrum and the correlation
matrix, where a reader will meet it before they meet P1.

**E5 (cost per action) is a price list.** δ = +1.000, also backwards: haiku
$0.031/action, sonnet $0.124, opus $0.279 — a 9× spread that tracks token
pricing and nothing else. Reference tier.

**A large effect in the wrong direction is now flagged separately** from the
power verdict, because burying "this metric is backwards" under "not enough
data" would waste the most informative thing the pass can find.

## The front-load index has a confound worth worrying about

E2 is one of Phase 4's three pre-registered primary endpoints, and it is the
signature of claim C2: understanding is bought early and spent late.

Within `bare_cc`, on this pilot, **the more capable model front-loads more** —
haiku 0.20, sonnet 0.25, opus 0.28, δ = +1.000 in the declared direction. No
arm here has a theory. If capability alone produces front-loading, then
front-loading is not specific to *having a theory*, and C2's evidence weakens
by however much of the effect capability explains.

Underpowered at n=4 and possibly an artefact. But it is a confound that the
ablation arm (Theoria − theorem obligations) is well placed to separate and that
should be checked before Phase 4 freezes, not after.

Two defences went into the code rather than the prose: E2 and E3 now refuse
runs shorter than eight turns, because a run that ends on turn four spent all
its money in its first quarter and looks maximally front-loaded while having
understood nothing.

## What de-redundancy found

Two clusters at |ρ| ≥ 0.9 out of 29 metrics:

* **X1 revisit rate ~ X4 no-progress streak**, ρ = +0.916, same family. Both
  count repetition; X1 represents.
* **P3 backtrack rate ~ X3 novelty front-load**, ρ = +0.909, across families.
  Plausible — an arm that stops finding new states also stops undoing — but at
  this sample size it should be treated as a hypothesis rather than a merge.

Twenty-seven clusters from twenty-nine metrics is *not* a reassuring result. It
mostly reflects thin data: most pairs of metrics share too few runs to
correlate at all, and `MIN_SHARED_RUNS = 4` correctly refuses to guess. The
de-redundancy pass will only do real work once there are runs enough for the
matrix to fill in.

## Coverage: what the battery still cannot see

| gap | why |
|---|---|
| **The whole economy family on Theoria** | A0 ran engines and hand adjudication with no LLM in the loop, so it has no model calls. Every economy metric is `not-applicable` on it |
| **Every epistemic metric on the controls** | `bare_cc` has no books. Structural, and predicted as such |
| **P4 solution redundancy — never computed once** | needs ground truth *and* a solve attempt. A0 has the truth but its trace is a coverage walk; the ledger runs are solve attempts with no truth. It is entirely notional in v0 |
| **M3 cross-level transfer (claim C3)** | no run reached a second level |
| **The specified discriminative gradient** | there is no Schema arm and may never be — `baseline-arms/SCHEMA_LOCATE.md`. v0 substitutes the model ladder; D-B-004 argues why that is weaker |

## Two smaller things worth recording

**An independent check that state identity is right.** X5 counts 59 distinct
states on the A0 base trace by digesting frames. `trace_summary.json` records
59 reachable states, computed by a different pipeline the battery never reads
for this purpose. The agreement is a real cross-check and is pinned by a test.

**`CLAUDE.md`'s pile hash reads as a file hash and is not one.** The published
digest `3feca53e…41bbc19a` is over the canonical JSON of `piles.json` minus its
own `sha256` field; the file itself hashes to `d3140eff…`. The cut is intact
and has never been modified since its first commit. Only the description
misleads. `arc-recon/` is shared ground so this track did not edit it —
D-B-011.

---

## What v1 needs, in order

1. **More paired games.** Six is the floor for the confirmatory test to be
   able to clear p < 0.05. Everything else is downstream of this.
2. **Separate the front-load confound.** Does capability alone front-load? The
   ablation arm can answer it and it bears directly on a primary endpoint.
3. **Fix K6.** The mean compression gain is carried entirely by one concept —
   A0's is +706 bits, from a Cart at +2125 while two of three concepts are
   negative. The minimum is the honest statistic.
4. **A defence for E4.** Context-growth curvature cannot currently tell a
   prompt-compaction policy from a theory that closed. Until it can, the metric
   that would catch Theoria failing to be what it claims is a reference item.
5. **A non-triviality filter for K3.** `0 = 0` is a theorem, and an LLM asked
   for theorems will supply them in quantity.
6. **A machine-readable manifest from the theory compiler.** `parse_dsl` is
   this track's weakest joint; it re-reads a grammar another track owns.
