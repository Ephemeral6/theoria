## 1 · A perfect score and a broken theory

### 1.0 The setting, and two words that must not be confused

**ARC-AGI-3** is the benchmark this project is aimed at. An agent is dropped into
a small game it has never seen — a 64×64 grid, sixteen colours, deterministic
rules, the rules hidden — and can do exactly two things: act, and observe
(`Theoria.md` §1.0). Twenty-five games are public; each is a ladder of levels; the
agent's only verbs are `RESET` and up to six per-game actions, and a *scorecard*
opened against the API bills successful actions
(`arc-recon/README.md`). This project cut those 25 games into a
**development pile of four** and a **sealed pile of 21** before any play, and the
cut is binding (`arc-recon/data/piles.json`).

Because this paper reports both kinds of environment, it holds two words apart and
asks the reader to hold them apart too:

* a **game** is always an ARC-AGI-3 game — a real task on someone else's server,
  which costs money to play;
* a **world** is always one this project built for itself — small, deterministic,
  offline, with the ground truth in a file.

**Every pipeline result in this paper is on self-built worlds.** No ARC-AGI-3 game
was played for any of them. Games enter this paper in exactly two places: §7's
battery, which recomputes over development-pile trajectories that already existed,
and §9's two live runs against the API on one development-pile game.

### 1.1 Where the field's checking regime stops

The strongest reported result on ARC-AGI-3 belongs to the second wave of world
models, the one that writes the world down as a program: the model is an editable,
executable artefact, and it is verified by replaying the entire recorded history
against it. `Theoria.md` §3.1 reports that line reaching **98.98 %**. Two
qualifications travel with that figure and this paper carries both. It is a *game
score*, not a replay-fidelity figure — replay is the verification regime, not the
thing measured. And it is self-reported on a project page rather than in a paper,
against a public set whose composition our sources do not state, so §12.1 treats
it as prior work's own summary and not as a measurement of ours.

Read the three waves together and what each of them upgrades is the same thing:
not the model, the **checking regime** (`Theoria.md` §3.1). Weights admit only
prediction error. A program admits line-by-line reconciliation against what
happened. Neither admits *"true of everything"* — a conservation law, an
impossibility — and that is the ceiling. A world model can replay every frame of
its own history without a single error and still be bankrupt as an account of the
world. The claim is not new; it is the constructive gap `Theoria.md` §1.3 states.
What this paper adds is not the claim but instances of it, small enough to be
opened, measured and closed with every number attached to a file.

### 1.2 The instance that cost us most: our own metrics

Start where the evidence is strongest, which is not where the framework performs
well.

To score this work we wrote a battery of **38 metrics over five families** —
epistemic (14), economy (7), exploration (6), mechanism (6) and planning (5)
(`battery/artifacts/capability_spectrum.json`) — and beside it an **anti-gaming
register**: one entry per metric saying, in prose, how that metric could be
cheated, and two hand-set booleans — `accidental` and `defended` — that a
mechanical rule reads to decide whether the metric may enter the *main table*, the
subset trusted to rank arms (`battery/audit/gaming.py`). Through v1 the suite
checked only that an entry **existed**, never that it was **true**, so a wrong
`defended: True` kept a gameable metric in the main table and nothing noticed.

`battery/audit/exploits/` replaces the claim with a demonstration. For each metric
there is a zero-argument function that builds a fabricated run — a trajectory
possessing none of the capability the metric names — and the exploit's `succeeded`
field is recomputed from the battery's own scorer rather than asserted by its
author, so implementing a real defence flips the exploit to false by itself. The
result:

> **38 exploits exist, 34 still land, and 17 register entries were contradicted by
> their own demonstration** — fourteen of the seventeen contradicting a `defended`
> claim (`battery/artifacts/gaming_audit.json`: `n_demonstrated` 38,
> `n_disagreements` 17, `main` 9; the fourteen are the entries whose
> `fields_contradicted` includes `defended`).

The main table fell from 19 metrics to 6 on demonstration and returned to 9 after
four defences were implemented (§7.7; `battery/REPORT_V2.md`). Three of the four
contradicted defences are worth naming because each is a different way to be
wrong: `P4` was monotone in failure, so one action against a twelve-step plan
outscored any solved run; `K12` read six self-reported booleans out of a file its
own producer wrote and scored 1.000 for zero environment actions; and `E2`, a
`Theoria.md` Phase 4 primary endpoint, could be driven to 0.993 by dumping the
whole bill on turn one (`battery/REPORT_V2.md`, which names that figure in prose;
it is not in `battery/artifacts/`).

**Then we did it again, blind.** The first round's exploit writers could see the
register they were attacking (`battery/BLINDING.md`). A later round could not: six
mutually invisible attackers, working from a source tree stripped of the register,
the exploits and every report, against thresholds written down and committed
*before* any attack, with the ordering provable by `git merge-base --is-ancestor`
(`battery/PREREG_V9.md`). They wrote 105 attacks, of which 91 landed:

> **37 of the 38 metrics were driven to their pre-registered threshold, and the
> main table fell from nine metrics to two.**
> — `battery/runs/20260729T021247Z-V9-battery-gaming-audit/v9_gaming_audit.json`
> (`verdict.gameable` 37, `verdict.b14_baseline_main` 9); summarised at
> `battery/STATUS.md` and carried into `battery/METRICS.md`

The last two went afterwards, and **not blind**: a sighted adversarial review,
whose author had read everything, wrote seven more attacks of which four landed,
knocking out `E1`; and `M3` was re-recorded from `main` to `undetermined`
(`battery/audit/v9/REPORT.md` §9). `M3` is not a survivor of the blind round
either — it was re-recorded because no path through it calls its own success
predicate, so it returns the same thing for a genuinely capable arm as for an
attacker. With the main table empty, the front-load index `E2`, one of
`Theoria.md` Phase 4's three primary endpoints, has no metric underneath it that
cleared the audit (`battery/STATUS.md`).

**Five limits, and none of them is small.** Eleven of the 38 first-round exploits
hard-code their own success rather than reading it back from the scorer, so for
those eleven "the exploit landed" means only that the metric returned a value
(`battery/audit/exploits/exploration_planning.py`). The register was written by
the same author as the metrics, which makes the first round a self-check. The
blind round's own pre-registration was breached: the adjudication implementation
was **not** in the pre-registered commit, and its `NOT defended` clause was
collapsed after the results were seen, in the direction that emptied the table
(`battery/PREREG_V9.md`, revision 1, which calls this the round's worst lapse).
The poverty certificate that was to establish that an attack had done no real work
**passed all 105 attacks and rejected none**, so on this data set it has no
demonstrated selectivity and what carried the claim was attacker discipline, not
the checker (`battery/audit/v9/REPORT.md` §7). And of the nine demotions the round
produced, its own report grades three *weak*, because for count-shaped diagnostics
the threshold is close to unavoidable — "driven to threshold" is not everywhere a
defeat.

What survives all five is narrower than the headline and still worth having: a
register whose entries are executable, and whose `succeeded` is read back from the
scorer instead of asserted, falsified 17 of its own author's written claims, and a
second round run against criteria fixed in advance overturned the first round's
survivors. The result is existential — *these* attacks landed on *these* metrics —
so it is not weakened by the battery's tiny sample, and equally it licenses nothing
about metrics we did not write.

One further finding is upstream of cheating altogether. **The epistemic family
cannot rank two manuals at all**: for any pair differing by one concept or one
clause, at least one `higher`-direction metric prefers each, and a single manual
that describes nothing holds eighteen of the twenty metrics in that audit's scope
at their best reading simultaneously (`battery/audit/exploits/mechanism_epistemic.py`,
`omnibus_manual`; §7.7 says nineteen, from before `K12`'s defence landed). That
lands on the two families which are also entirely unvalidated.

One bookkeeping fact belongs here rather than in a footnote, because this paper's
binding rule is provenance. The first round's numbers above are read from
`battery/artifacts/gaming_audit.json`, which `battery/PREREG_V9.md` froze so that
the blind round could be judged against a fixed baseline. Re-running the same code
against the tree as it now stands gives 33 exploits landing and 19 contradicted
entries rather than 34 and 17
(`battery/runs/20260729T025515Z-V18-battery-prereg-check/recompute/gaming_audit.json`).
The frozen file is the right one to cite for a baseline; §7.1's claim that the
battery's artefacts regenerate on demand is not true of this one.

### 1.3 The same failure inside the pipeline

A0 is a self-built 9×9 world with a cart, a button, a door and a portal. Its
induced manual passes full-history replay perfectly: **276/276 frames,
22 356/22 356 pixels, 0 anomalies** (`cold-start-a0/A0_REPORT.md` §2). Scored
instead against the world's whole transition function, it agrees on **233 of 236**
reachable (state, action) pairs — 98.73 %. The three it misses are exactly the
three pairs the trajectory never covered, and on those three its accuracy is
**0.000** (`cold-start-a0/artifacts/score_vs_truth.json`, field
`held_out.accuracy`).

That the missed pairs are the uncovered pairs is the whole point, and it is
measurable rather than merely labelled: `cold-start-a0/artifacts/trace_summary.json`
records the trace's own coverage as 233 of 236 and names its three
`uncovered_pairs` item for item as the three the scorer marks `held_out`. Both
counts descend from the same explorer, so this makes the identity auditable rather
than independently confirmed (`papers/phase1-workshop/REVIEW.md`).

The battery, recomputing over the same trajectory, reports the same manual at
**evidence coverage 1.000 and held-out accuracy 0.000** — the first over 7
annotated clauses, with 3 more unannotated and reported alongside; the second over
3 pairs with 0 agreements (`battery/artifacts/capability_spectrum.json`, run
`a0-base`, metrics `K4` and `K2`; the metric cards define `K4` as the share of the
manual's own evidence-annotated clauses that a witness actually backs, and `K2` as
accuracy on state-action pairs the trace never covered — "the metric replay cannot
see"). The battery drew the consequence for measurement rather than for A0:

> Evidence coverage rewards precisely the caution that held-out accuracy
> punishes. A battery reporting K4 alone would show a flawless manual.
> — `battery/REPORT_V0.md`

**The miss was written down before it was measured.** During adjudication, entry
R-05 of `cold-start-a0/THEORIZE_LOG.md` rejected the generalisation that the
button is pressable from any direction, on the ground that the evidence for the
other three directions was "not thin, zero", and recorded the consequence:

> the manual as written says that pushing up into the Button does nothing, and
> full-history replay will never catch that.
> — `cold-start-a0/THEORIZE_LOG.md` R-05

Be precise about what was named, because the precision is the whole argument. R-05
names three **directions** — `press_up`, `press_down`, `press_right` — and one
concrete configuration, "drive the Cart to (2,2) and push DOWN into an unpressed
Button". It does not enumerate the coordinate pairs; the phrase "the three pairs
R-05 named" appears in `cold-start-a0/THEORIZE_LOG.md`'s seal section, and `A0_REPORT.md` §2
makes the same gloss in different words — both written at M6 *after* the score
existed, and this paper does not inherit either as if it were the
pre-registration. The claim that survives is still the one
that matters: R-05 named the three directions, predicted the manual would be wrong
on them, and predicted that replay would not notice. All three held.

The ground truth was first opened at M6, after M4 and M5 were green — M5 being the
unsolvable-variant milestone, not a planning stage — and only by the scoring
script; no clause was written or revised afterwards
(`cold-start-a0/THEORIZE_LOG.md`, "Ground-truth seal"; the same stamp is carried in
`cold-start-a0/artifacts/score_vs_truth.json` as `seal`). That stamp is a
declaration written by the authors' own script, not a control.

The seal has a hole, and the log names it rather than hiding it: **the same
instance both built the A0 world at M1 and adjudicated it at M3**
(`cold-start-a0/THEORIZE_LOG.md`, preamble). No ground-truth file was read, and
every verdict is written to be re-derivable from the candidate stream alone, but
`cold-start-a0/A0_REPORT.md` §6.3 counts this as a threat to the result rather
than a footnote, and this paper carries it the same way. Neither A0's seal nor the
battery's blind round (§1.2) is a clean pre-registration: A0's is a self-declaration
a third party cannot audit, and the blind round's adjudication rule was amended
after the results were seen. They fail differently, and neither is offered as the
standard the other should have met.

### 1.4 The same failure as a file you can diff

The second exhibit makes the failure mode inspectable. A2 built a manual with one
rule deleted — a teleport — and ran the ordinary machinery on it. The result is a
pair of Lean files carrying the same theorem name `unsolvable`, produced by the
same generator, closed by the same tactic (`decide`), with no Mathlib in either,
the same dependency surface, and `#print axioms` returning `[]` for both. One is
true of its world; the other is false of its world, refuted by an 18-action
episode that ends in a win (`cold-start-a2/A2_REPORT.md` §4, §2). The instrument
returns the same verdict either way.

The two files are *not* a minimal pair — §5.6 corrects the source report on that
point and says what the correction costs — but they do not need to be. Identical
provenance and an identical empty axiom list, on one theorem that holds of the
world and one that does not, is the whole demonstration.

> The instrument cannot tell them apart, and it is not supposed to be able to.
> — `cold-start-a2/A2_REPORT.md` §4

This is the structural shape `Theoria.md` §1.3 describes under the name DC22. It
is an exhibit built to order, not a finding: A2 reproduces the shape on a
self-built world only, no upstream artefact of any sealed game was read
(`cold-start-a2/A2_REPORT.md` §1; `arc-recon/README.md`), and nothing in this
paper is a claim about a sealed game.

### 1.5 What this paper contributes

Scoped to what was actually run:

1. **A negative result about measurement, obtained by attacking our own
   instrument.** An anti-gaming register rewritten from prose into executable
   exploits, then re-attacked blind against pre-registered thresholds: 34 of 38
   metrics gamed in the first round and 37 of 38 in the blind one, 17 written
   register entries contradicted by their own demonstration, and the table of
   metrics trusted to rank arms cut from nine to two blind and to zero by a
   sighted follow-up (`battery/artifacts/gaming_audit.json`;
   `battery/runs/20260729T021247Z-V9-battery-gaming-audit/v9_gaming_audit.json`;
   the five limits on all of it are in §1.2 and are not small). This is the one
   contribution here that does not require believing the framework, and the one
   that is not guaranteed by its own construction.
2. **An artefact that produces the replay-invisible failure on demand, together
   with the repair loop that closes it** — 打脸 (refute) → 定位 (locate) → 戳探
   (probe) → 修订 (revise) → 重证 (re-certify) → 解出 (solve), each beat settled by
   an artefact — these six are `L1`–`L6` of
   `cold-start-a2/artifacts/loop_ledger.json`, whose other two beats build the
   exhibit rather than repair it; all 8 pass, 0 fail.
3. **A cold-start pipeline run end to end on self-built worlds**, from pixels
   through engine proposals — six offline solvers that mine candidate rules and
   certificates but never adjudicate them — through adjudication, the four
   co-derived forms (Lean, Python, PDDL, Markdown), certification and
   planning — with a paired A0/A0′ contrast, **uncontrolled by construction**,
   in which the second world's manual reaches 228/228 = 100 % while covering only
   107/228 = 47 % of its own state-action pairs. The two worlds differ in
   mechanism, rule count, state count and explorer budget at once, and §3.3 shows
   the outcome is entailed by the construction rather than discovered by it
   (`cold-start-a0/A0_REPORT.md` §8).
4. **A machine-checked impossibility whose invariant weights crossed a data
   boundary.** The impossibility is the machine-checked object — a Lean theorem
   with an empty axiom list (§4.2) — and the certificate is what crossed. The
   distinction is worth the extra clause: the certificate is a JSON document, and
   what re-checks it is Python, not a kernel. The pagoda weights are produced by
   an independent engine's linear program and transported as that certificate
   (`engine-rig/interop/certificates/pagoda_5_11011_to_00010.json`); the consuming
   side re-verifies every obligation rather than trusting the certificate's own
   `verified` flag (`theory-compiler/STATUS.md`). The two sides are sessions that
   do not import each other's code (§4.2), which is weaker than independent
   implementation and is not claimed as more.
5. **A passive metrics battery** recomputed over trajectories that already
   existed — 95 runs across 5 arms, at zero new game spend and zero model calls
   (`battery/artifacts/capability_spectrum.json`; `battery/REPORT_V2.md`) — with
   directional predictions pre-registered before each recompute, including a seal
   declaration marking which A0 predictions are post-dictions
   (`battery/PREDICTIONS.md`). The five arms, never previously enumerated in this
   paper, are `bare_cc` (plain Claude Code on development-pile games, no theory
   layer — 80 runs), `schema_repro` (another team's released Schema trajectories on
   the same games, ingested rather than re-run — 8), `theoria_a0` (2),
   `theoria_a0_spike` (1) and `theoria_a2` (4); the first two are controls and the
   last three are the framework's, and they sum to 95
   (`battery/artifacts/capability_spectrum.json`, `provenance.arms` and
   `runs[*].arm`). **88 of the 95 runs touch a development-pile game and the other
   7 are synthetic**, so the compound phrase "95 runs across 4 games" used
   elsewhere in this draft is true of neither number by itself.

Sections 6, 8 and 9 report a transfer result, an examination instrument and two
live API runs. They are reported and not claimed; §11.5 says why.

### 1.6 What this paper does not claim

Stated here rather than deferred, because §1.5's list is the part a reader is
entitled to hold us to.

Every pipeline result — A0, A0′, A1, A2, A3 — was produced offline, on small
deterministic worlds this project built itself; no game was played for any of them
and no network was touched (`cold-start-a2/A2_REPORT.md` §7 for A2;
`cold-start-a3/A3_REPORT.md` for A3, whose unit under test is a *level* of a
self-built world and not a game). The battery is passive: it
recomputes over trajectories that already existed and spends nothing new
(`battery/REPORT_V2.md`). No sealed-pile game was played or read for any result
here — though §11.1 records that the sealed pile is nonetheless no longer clean,
for reasons unconnected to this paper's experiments.

The theorize step is not a measured language-model step: the manuals are checked in
as artefacts, written by hand from engine output, so `cold-start-a2/A2_REPORT.md`
§8's sentence governs — "A2 tests the instrument and the loop, not the theorizer."
There is no language-model baseline anywhere in this paper, and no arm was run
against another system's baseline; §6's three arms are all ours. Every world here
is small enough for `decide` to enumerate, so the certification layer has not been
tested at a scale where enumeration fails.

Section 10 reports one measurement that is neither a contribution above nor a
limitation below: a census of whether the engines-propose/LLM-adjudicates
division of §2.2 is enforced in the implementation, in both directions.
Section 11 collects the rest of the limitations; none of them is discovered there
for the first time, because each acceptance report already states its own.
