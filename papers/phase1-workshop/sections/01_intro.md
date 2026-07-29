## 1 · A perfect score and a broken theory

A world model can replay every frame of its own history without a single error and
still be bankrupt as an account of the world. The claim is not new — it is the
constructive gap `Theoria.md` §1.3 states, and the reason that document gives for
why a score of 98.98 on replayed history (`Theoria.md` §3.1) stopped resolving
anything about understanding. What this paper adds is not the claim but an
instance of it: a small, offline, reproducible artefact in which the gap is
opened deliberately, measured, and then closed, with every number attached to a
file.

The instance is A0, a self-built 9×9 world with a cart, a button, a door and a
portal. Its induced manual passes full-history replay perfectly:
**276/276 frames, 22 356/22 356 pixels, 0 anomalies**
(`cold-start-a0/A0_REPORT.md` §2). Scored instead against the world's whole
transition function, it agrees on **233 of 236** reachable (state, action) pairs
— 98.73 %. The three it misses are exactly the three pairs the trajectory could
never have contained, and on those three its accuracy is **0.000**
(`cold-start-a0/artifacts/score_vs_truth.json`, field `held_out.accuracy`). The
metrics battery, recomputing over the same trajectory, reports the same manual at
**K4 evidence coverage = 1.000 and K2 held-out accuracy = 0.000** — K4 over 7
annotated clauses, K2 over 3 pairs with 0 agreements, unchanged from v0 to v2
(`battery/artifacts/capability_spectrum.json`, run `a0-base`) — and draws the
consequence for measurement rather than for A0:

> Evidence coverage rewards precisely the caution that held-out accuracy
> punishes. A battery reporting K4 alone would show a flawless manual.
> — `battery/REPORT_V0.md`

### 1.1 The miss was written down before it was measured

What makes this evidence rather than an anecdote is the order of events. During
adjudication, entry R-05 of `cold-start-a0/THEORIZE_LOG.md` rejected the
generalisation that the button is pressable from any direction, on the ground
that the evidence for the other three directions was "not thin, zero", and
recorded the consequence:

> the manual as written says that pushing up into the Button does nothing, and
> full-history replay will never catch that.
> — `cold-start-a0/THEORIZE_LOG.md` R-05

Be precise about what was named, because the precision is the whole argument.
R-05 names three **directions** — `press_up`, `press_down`, `press_right` — and
one concrete configuration, "drive the Cart to (2,2) and push DOWN into an
unpressed Button". It does not enumerate the coordinate pairs; the phrase "the
three pairs R-05 named" appears in `THEORIZE_LOG.md`'s seal section and
`A0_REPORT.md` §2, both written at M6 *after* the score existed, and this paper
does not inherit that gloss as if it were the pre-registration. The claim that
survives is still the one that matters: R-05 named the three directions,
predicted the manual would be wrong on them, and predicted that replay would not
notice. All three held.

The ground truth was first opened at M6, after M4 and M5 were green — M5 being
the unsolvable-variant milestone, not a planning stage — and only by the scoring
script; no clause was written or revised afterwards
(`cold-start-a0/THEORIZE_LOG.md`, "Ground-truth seal"; the same stamp is carried
in `cold-start-a0/artifacts/score_vs_truth.json` as `seal`). That stamp is a
declaration written by the authors' own script, not a control: the only thing
that could make it auditable is git history, which this paper does not appeal to.

The seal has a hole, and the log names it rather than hiding it: **the same
instance both built the A0 world at M1 and adjudicated it at M3**
(`cold-start-a0/THEORIZE_LOG.md`, preamble). No ground-truth file was read, and
every verdict is written to be re-derivable from the candidate stream alone, but
`cold-start-a0/A0_REPORT.md` §6.3 counts this as a threat to the result rather
than a footnote, and this paper carries it the same way.

### 1.2 The same failure as a file you can diff

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

This is the structural shape `Theoria.md` §1.3 describes under the name DC22, and
A2 reproduces that shape on a self-built world only: no upstream artefact of the
sealed game was read, per the incident record cited in
`cold-start-a2/A2_REPORT.md` §1 and `arc-recon/README.md`. Nothing in this paper
is a claim about that game.

### 1.3 What this paper contributes

Scoped to what was actually run:

1. **A cold-start pipeline run end to end on self-built worlds**, from pixels
   through engine proposals, adjudication, four co-derived forms, certification
   and planning — with a controlled A0/A0′ contrast in which the second world's
   manual reaches 228/228 = 100 % on 47 % of A0's state-action coverage
   (`cold-start-a0/A0_REPORT.md` §8).
2. **A machine-checked impossibility certificate whose weights cross a data
   boundary.** The pagoda weights are produced by an independent engine's LP and
   transported as a JSON certificate
   (`engine-rig/interop/certificates/pagoda_5_11011_to_00010.json`); the
   consuming track re-verifies every obligation rather than trusting the
   certificate's own `verified` flag (`theory-compiler/STATUS.md`).
3. **An exhibit of the replay-invisible failure mode together with the repair
   loop that closes it** — 打脸 (refute) → 定位 (locate) → 戳探 (probe) → 修订
   (revise) → 重证 (re-certify) → 解出 (solve), each beat settled by an artefact
   (`cold-start-a2/artifacts/loop_ledger.json`: 8 beats, 8 pass, 0 fail).
4. **A metrics battery recomputed over trajectories that already existed** — 95
   runs, 5 arms, 4 development-pile games, 38 metrics, at zero new game spend and
   zero model calls (`battery/artifacts/capability_spectrum.json`;
   `battery/REPORT_V2.md`) — with directional predictions pre-registered before
   each recompute, including a seal declaration marking which A0 predictions are
   post-dictions (`battery/PREDICTIONS.md`).

**Scope limit, stated here rather than deferred.** Every pipeline result in this
paper — A0, A0′, A1, A2 — was produced offline, on small deterministic worlds
this project built itself; no game was played for it and no network was touched
(`cold-start-a2/A2_REPORT.md` §7). The battery is passive: it recomputes over
trajectories that already existed and spends nothing new
(`battery/REPORT_V2.md`). No sealed-pile game was played or read for any result
here — though §10.1 records that the sealed pile is nonetheless no longer clean,
for reasons that have nothing to do with this paper's experiments. And the
theorize step is not a measured language-model step: the manuals are checked in
as artefacts, written by hand from engine output, so
`cold-start-a2/A2_REPORT.md` §8's sentence governs — "A2 tests the instrument and
the loop, not the theorizer." Section 7 collects the rest of the limitations;
none of them are discovered there for the first time, because each acceptance
report already states its own.
