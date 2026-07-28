# REVIEW — adversarial pass over `papers/phase1-workshop/PAPER.md`

**Reviewed state.** `PAPER.md`, 75 885 bytes / 11 451 words, mtime 08:47, together with
`PROVENANCE.md` (08:45), `README.md` (08:42), `sections/*.md` and `figures/*.py`. The
draft was being edited during the first half of this pass; §2.2 and §5.4 improved under
me and those fixes are credited below. Everything else here was re-checked against the
08:47 text and is current as of writing.

**Method.** Every claim below was checked by opening the cited file. Where the paper
cites a JSON field, the field was read; where it cites a diff, the diff was run; where it
cites a count, the count was recomputed. Figure scripts were executed twice and compared
byte-for-byte. Test suites were collected and, where cheap, run.

---

## Verdict

The underlying work is real, unusually well documented, and more honest than most of what
a program committee sees — the limitations section is the best part of the paper and was
written by the runs themselves rather than extracted by a reviewer. But the paper is not
submittable, and the reason is not polish. Its single most-repeated sentence — that the
two headline Lean files "differ in their weight table and in nothing else", asserted in
the abstract, in §1.2, and in §5.6 — is false, contradicted by the paper's own table two
lines above it and falsifiable by a thirty-second `diff` that shows the two files also
differ in `def Goal` and in four entries of the `step` transition table. That is the
worst possible failure mode for a paper whose binding rule is "every number points at a
file": the invitation to check is the mechanism by which the reader discovers the claim is
wrong. Three further claims fail the same way — the abstract's "no benchmark game was
played for any result here" (§6.5–§6.6 report Cliff's δ and 4-of-4 win counts over four
played ARC games, and §7.2 says so), the anti-circularity guarantee "`locate.py` and
`probe.py` import no world module at all" (one grep: `probe.py:59`), and "the miss was
named, with its three pairs" (R-05 names three *directions* and one cell). Separately, the
scientific core is thinner than the framing: "prediction perfect, understanding broken" is
the design document's own premise restated on a world the authors built by deleting a rule
they chose, "reversibility beats coverage" is n=1 per arm on two worlds that differ in
more than the one advertised variable and whose outcome is entailed by the construction,
and the paper's central conceptual point — a proof is only as good as the specification —
is the oldest result in formal methods and is not cited to anyone. Add 11 300 words
against a workshop budget of roughly 4 000, 17 unfilled `[bib: TODO]` markers with no
bibliography, three figure scripts that no sentence in the paper references, and a
`CITECHECK.md` that the README and `PROVENANCE.md` both promise and that does not exist.

**Reject** — as submitted. This is a reject of the draft, not of the work. Delete the
three false claims, halve the length, fill the bibliography, and re-scope the contribution
to "a fully auditable instrument and a demonstration artefact" rather than "four results",
and I would argue for weak accept at a workshop that wants engineering-grade artefacts.
As it stands the paper would be embarrassed by any reviewer who runs the `diff` it invites.

---

## Major issues

### 1 · [BLOCKING] §5.6 / §1.2 / Abstract — the headline "pair" claim is false

The paper's most load-bearing sentence, in three places (abstract L50 "differing only in a
weight table"; §1.2 L129 "They differ in their weight table and in nothing else"; §5.6 L813,
identical):

```
$ diff cold-start-a2/theory/generated_holed/theory.lean \
       cold-start-a2/theory/generated_repaired/theory.lean
```
returns **52 changed lines across 7 hunks** (791 vs 789 lines). Only 14 of them are the
weight table. The others are:

* **`def Goal`** — `s.cart == Cell.c10` (the goal cell (2,7)) vs `s.cart == Cell.c34`
  (the sealed pocket (7,1)). *The two theorems are about different goals.*
* **four entries of the `step` transition table** (holed lines 243/391/539/687),
  `⟨Cell.c31, …⟩, .down => ⟨Cell.c31, …⟩` vs `=> ⟨Cell.c35, …⟩` — one per
  colour × door stratum. *This is the teleport rule itself. The two files encode
  different transition functions.*
* the header comment and a 7-for-5 comment swap above `def I`.

§5.6's own table, two lines above the sentence, **lists the goal difference as a row**
(`goal | the goal cell (2,7) | the sealed pocket (7,1)`) and the invariant difference
(`0 on 21 cells` vs `0 on 35 cells`). The subsection contradicts itself.

The rhetoric depends on the false version. "The instrument cannot tell them apart, and it
is not supposed to be able to" lands hard if the files are a minimal pair differing in a
single table. It lands much softer once the reader sees they are theorems about two
different goals over two different transition systems — of course a checker cannot rank
them; they are not answers to the same question. The repaired file does not prove the
world's real goal unreachable, because it isn't (§5.5's 解出 beat solves it in 18). It
proves a *separately chosen, genuinely unreachable* pocket unreachable. That is a
different and much weaker exhibit than the abstract advertises.

**Fix.** State what is true and still sufficient: *the two files are identical in
generator, tactic, dependency surface and axiom list, and the instrument returns `[]` for
both; one is true of its world and one is not.* Drop "and in nothing else" everywhere. If
a genuine minimal pair is wanted, generate the repaired invariant against the *same* goal
`c10` and show that it fails — which `generated_repaired_stale/` already nearly is.
Note the false sentence also lives in `cold-start-a2/A2_REPORT.md` §4 and
`cold-start-a2/DECISIONS.md` D-A2-005; under the paper's rule 3 the reports may not be
edited, so the paper must diverge from them and say why.

### 2 · [BLOCKING] Abstract — "no benchmark game was played for any result here" is false

Abstract L58–59. But §6.5 reports the model ladder separating at Cliff's δ = −1.000 with
haiku at 0.97 and opus at 0.52 actions per call; §6.5 reports E5 at δ = +1.000 with three
per-action prices; §6.6 reports E2 at δ = +1.000 with **4 wins of 4 paired games**. Those
are comparative results across arms, computed over 26 trajectories from four ARC
development-pile games that were played — 109 successful actions plus a 44-action variance
campaign, `baseline-arms/ledger.jsonl`, 560 rows — as §7.2 itself states in order to
correct `CLAUDE.md`. A paper cannot correct the repository for saying no game was played
and then say it in its own abstract.

The intended claim is defensible and is made correctly in §1.3's scope limit ("no game was
played *for it*") and in §6.1 ("passive… recomputes over trajectories that already
existed"). The abstract's absolute phrasing is not.

**Fix.** "No game was played *for* this paper; §6 recomputes over trajectories that already
existed, and the comparative deltas it reports are across a model ladder, not across the
framework's arms."

### 3 · [BLOCKING] §5.5 — the anti-circularity guarantee is falsified by one grep

L759–760: "`locate.py` and `probe.py` import no world module at all
(`cold-start-a2/DECISIONS.md` D-A2-010)."

`cold-start-a2/a2pipeline/probe.py:59` is `from a2world import a2_world`, used at
`probe.py:108–109` (`self._world = a2_world.A2World(spec)`). `locate.py:36` imports
`from a2world.ground_truth import read_trace`, and `a2world/ground_truth.py` imports
`a2world.a2_world` and `a2world.explorer` at module level, so `locate.py` pulls the world
transitively too. D-A2-010 contradicts itself one clause later, and the paper copies the
false half.

This is the claim that carries §5's answer to the obvious objection ("the repairer already
knows the answer"). The *real* discipline is defensible and stronger — `probe.py`'s
`Environment` is the only channel, actions in and frames out, and its docstring says so —
but the paper states the version that a reviewer falsifies in ten seconds.

**Fix.** "The world is reached only through `probe.py`'s `Environment`: actions in, frames
out. No theorizing step reads `ground_truth.json`, and nothing reads `env._state`."

### 4 · [BLOCKING] §1 / Abstract — "named, with its three pairs" overstates R-05

Abstract L32 ("The miss was named, with its three pairs, in the adjudication log *before*
the ground truth was opened") and §1.1 L110 ("The three pairs were named there, before any
score existed"). This is explicitly the sentence that the paper says converts anecdote into
evidence: "What makes this evidence rather than an anecdote is the order of events."

`cold-start-a0/THEORIZE_LOG.md` R-05 names three **directions** (`press_up`,
`press_down`, `press_right`) and exactly one coordinate ("drive the Cart to (2,2) and push
DOWN into an unpressed Button"). It does not enumerate `(3,1)/RIGHT` or `(4,2)/UP`. The
retroactive phrasing "the three pairs R-05 named" appears in `THEORIZE_LOG.md`'s seal
section and `A0_REPORT.md` §2 — both written at M6, *after* the score existed. The paper
inherits a post-hoc gloss and presents it as the pre-registration.

The weaker true claim is still good and should be used: R-05 named the three directions,
predicted the manual would be wrong on them, and predicted replay would not notice — and
all three held.

**Fix.** Replace "with its three pairs" with "naming the three directions" in both places.

### 5 · [BLOCKING] §3.4 — the seeded-error experiment cites the wrong field, and gets Run A's numbers

L426–429: "Full-history replay stayed **GREEN** — 111 frames, 8991 pixels, 0 anomalies
(`cold-start-a0/prime/artifacts/prime_report.json`, `run_b.certify_cheap`)."

`run_b.certify_cheap` is the scalar `true`. The frame and pixel counts are in
`run_a.certify_cheap` — i.e. the run on the *unseeded* manual. The paper's own
`PROVENANCE.md:48` gets this right ("`run_b` / `run_a.certify_cheap`"); the body lost the
second half. Since the whole point of §3.4 is that replay is green *on the seeded manual*,
citing the clean run's pixel counts for it is the one miscitation in the paper that a
hostile reader will read as a thumb on the scale.

**Fix.** Cite `prime/A0P_REPORT.md` §3 for the Run-B prose and `run_a.certify_cheap` for
the shape of the check, and say plainly which artefact carries which.

### 6 · [BLOCKING] §6.4 / §7.4 — "every discriminative verdict came back `underpowered` or `no-data`" is false

`battery/artifacts/discrimination.json` carries **three** verdict values over 29 metrics:
`underpowered` (11), `no-data` (13), and **`not-ranked` (5)** — E1, K7, K11, P5, X5, the
neutral-direction diagnostics. The paper inherits the error from `battery/REPORT_V0.md:36`,
but it is repeated twice (§6.4, §7.4) as the paper's own headline honesty number, and it is
exactly the kind of statement a reviewer spot-checks.

**Fix.** "Every *ranked* metric's verdict" or "24 of 29".

### 7 · [SHOULD FIX] §5.3 — "diff the files and the deletion is the whole diff" is false

`diff cold-start-a2/theory/theory.dsl cold-start-a2/theory/theory_holed.dsl` also shows:
the 13-line header replaced by a 45-line block; every coverage annotation rewritten
(`push_up 56/56 → 38/38`, `push_down 51/51 → 39/39`, `push_left 39/39 → 32/32`,
`push_right 43/43 → 35/35`, `Cart ev: t0-t247 → t0-t183`); `events:` losing `jumped`; and
`laws:` swapping `teleport_is_colour_triggered` for `right_room_locked`. The *substance*
holds — every extra change is annotation or a consequence of the deletion — but the paper
issues a literal, checkable instruction and the check fails.

Related and worth disclosing: `PROVENANCE.md:124` records that
`cold-start-a2/artifacts/refutation.json` names the theorem `right_room_locked` with
`lean_target: "unsolvable"`, while §1.2 asserts the two files have "the same theorem name
`unsolvable`". The provenance file knows about the discrepancy; the paper does not mention
it.

### 8 · [SHOULD FIX] §3.3 — the "controlled contrast" changes more than one variable, and the abstract says so while §3.3 denies it

Abstract L33–35: "identical except that an irreversible latch becomes a reversible toggle
**and the explorer is truncated**". §3.3 L369: "differing in one deliberate respect".
Two variables, stated as one.

It is worse than two. `cold-start-a0/theory/theory.dsl` has 3 objects and **7 rules**;
`cold-start-a0/prime/theory/theory_prime.dsl` has 3 objects and **21+ rules** (four
`switch_on_*`, four `switch_off_*`, four `door_opens_*`, four `door_shuts_*`). The worlds
have different state counts (59 vs 57), different pair counts (236 vs 228), and a different
mechanism object (Button vs Switch). "Identical except" is not a fair description of two
worlds whose manuals differ threefold in rule count.

And the outcome is entailed by the construction rather than discovered by it. A0′'s toggle
was *designed* so that "every direction-by-polarity combination has its own witness"
(`prime/THEORIZE_LOG.md` R-03: sixteen clauses, each coverage 1/1). The adjudication rule
(admit a generalisation iff every case is witnessed) then mechanically admits what it
mechanically rejected in A0. Nothing was learned that was not built in. The paper says
"n = 1 per arm, not a statistical result", which is the right disclaimer for sampling
error; it is not a disclaimer for *analytic entailment*, and that is the objection that
actually bites.

**Fix.** Say that A0′ was constructed so the generalisation would be admissible, and that
the contrast therefore demonstrates the mechanism rather than testing it. Drop "identical
except". Then the honest claim — an irreversible mechanism caps what exploration can
establish — survives as a design lesson, which is what `A0_REPORT.md` §8 actually offers it
as.

### 9 · [SHOULD FIX] §3.2 vs §8.2 — `zero_space` is described two incompatible ways

§3.2: "Handed 152 anonymous indicator bits… returned [the law] with **275 transitions of
support**" — a null space of the observed difference matrix, i.e. an empirical
generalisation over the trajectory. §8.2: "Linear conservation laws are computed
**symbolically from the rules** as Petri invariants (`engine-rig/engines/zero_space`)."

`engine-rig/engines/zero_space/README.md` is unambiguous: encode each `(cell, colour)` as
an indicator, difference consecutive states, compute the null space of the difference
matrix. It reads *data*, not rules. The §8.2 description upgrades a data-driven regularity
into a symbolically derived invariant, which is exactly the kind of upgrade this paper is
otherwise careful about.

It also undercuts §3.2's own gloss: "The rule says *when* it happens; the law says *that it
always holds*." Over 275 observed transitions, the law says it always held *on the
trajectory* — precisely the "true of everything already experienced" that §8.1's table
assigns to wave II. The claim "true of everything" is earned only by the Lean closure
proof, and that is true *relative to the manual*, which §2.3 correctly insists on.

### 10 · [SHOULD FIX] §4 — "independently developed track" and "independent adversarial review" are doing more work than the setup supports

The two tracks are two Claude Code sessions on one repository, run by one operator, sharing
`CLAUDE.md`, `Theoria.md`, `CONTRACTS/`, and mutually visible through git history and
`PARTNER_SYNC.md` (repo `CLAUDE.md`, "Two independent tracks"). Calling the JSON hand-off a
crossing into "a second, independently developed track" (abstract L41) invites a reader to
imagine two teams. The re-verification discipline is genuinely good engineering —
`certificate.py` never reads `verified` and re-derives the move geometry from `n_pos`, and
`gen_lean.py` raises if its predictor-derived move set disagrees — but that is a
*defence-in-depth* result, not an independent-replication result.

Likewise §4.3's "independent adversarial review — read-only, permitted to falsify but not
to confirm" is an adversarial read-only pass inside the same project. The negative control
it ran is real and checks out verbatim (`w .p1 := 7` → `decide proved … is false`, all four
theorems `[sorryAx]`, exit 1). Say that; do not let "independent" carry the connotation of
a third party. `certificate.py`'s own docstring notes the geometry was "confirmed against
the producer" — calibrated, not blind.

### 11 · [SHOULD FIX] §6.3 / §6.5 — two "findings" that are entailed by their definitions

§6.5 opens "Found by running the instrument, not by inspecting it." For **E5** that is not
credible: E5 is cost per action, the arms are three models at different token prices, and
"E5 is a price list" follows from the definition without any data. Reporting it as
something the pass discovered inflates the battery's yield from three findings to arguably
one and a half. (**P1** is a real finding — the ρ = −0.83 correlation with step-failure
rate is not deducible from the definition and reproduces exactly. **K4 vs K2** is a real
finding.)

§6.3's K4/K2 tension is also partly definitional: K4 = 1.000 because the manual annotated
only clauses it had evidence for, K2 = 0.000 over **three pairs**. The held-out set is not
a test set — `cold-start-a0/certify/score_vs_truth.py:91–137` defines it as the complement
of the authors' own explorer's coverage on the authors' own world, which in this world is
exactly the three pairs the manual is known to miss. "Held-out accuracy 0.000" reported to
three decimals over n = 3 reads like a measurement and is a restatement of the three known
errors. Say n = 3 in the abstract.

### 12 · [SHOULD FIX] §7.3 — the Fast Downward paragraph implies A0/A0′ results ran on FD; they did not

§7.3: "Fast Downward was built and wired into A0/A0′, agreeing with the bundled BFS stub on
all three instances." True — `fd_real.json` shows identical plans on all three. But
`cold-start-a0/BLOCKER_FAST_DOWNWARD.md` states that "the reproducible pipeline
(`run_all.py`, `prime.run_prime`) still calls `solve(..., prefer=\"stub\")` **on purpose**,
so its checked-in artefacts stay byte-identical whether or not a planner is installed." So
§3.1's "SAT plan of 12 steps" and every planning number in §3 came from the stub; FD is a
separate conformance artefact. The paper never says this, and a reader will conclude
otherwise.

Two further gaps: (a) `fd_real.json` records the FD path as
`C:/Users/user/Desktop/theoria/cold-start-a0/.toolchain/downward/fast-downward.py` — an
absolute path into a *different* directory from this worktree, and `.toolchain/` is not in
the tree, so nobody can rerun that artefact without building FD themselves; (b)
`PROVENANCE.md:122` lists the `A0_REPORT.md` §5/§6.5 disagreement but omits §8 item 4,
which also says FD "could not be built (three failed compiler attempts)". If the paper is
going to cite both sides, it should cite all three.

### 13 · [SHOULD FIX] Reproducibility — `CITECHECK.md` does not exist, and it is the paper's own compliance mechanism

`README.md` lists `CITECHECK.md` as "a mechanical path/number/quote audit of the draft" and
states under rule 1 that "`CITECHECK.md` is the mechanical test of that rule; its findings
are not hidden." `PROVENANCE.md:5` says the same. The file is absent. Its absence is not
cosmetic: this pass found eight miscitations and four false statements, which is roughly
what a mechanical path/field/quote checker exists to catch.

Related reproducibility gaps, none individually fatal but cumulative:

* **A Lean toolchain is required and the paper does not say so.** §4.2's "83/83 tests pass"
  becomes `75 passed, 8 skipped` without `lean` on PATH —
  `theory-compiler/tests/test_gen_lean.py:31–32` is
  `needs_lean = pytest.mark.skipif(shutil.which("lean") is None, ...)`, and
  `theory-compiler/STATUS.md:101` says exactly this. The whole empty-axiom-list claim
  evaporates into skips. (Lean 4.9.0 *is* installed here, so 83/83 reproduces for me.)
  Also, of the 8 lean-gated items only **7** invoke `lean` and **6** read a named theorem's
  `#print axioms`; §4.2 says "eight of which invoke `lean` … and read `#print axioms`".
* **The battery determinism claim is not tested on the published artefacts.**
  `battery/tests/test_determinism.py:42` runs `main(["--ledger", <synthetic fixture>,
  "--a0", "none", ...])`. Byte-identity of the committed `battery/artifacts/*.json` is
  asserted in prose only. Also, the decision cited for determinism is **D-B-008**, not
  D-B-001 (D-B-001 is about verifying the cut).
* **The pile hash reproduces only after LF normalisation.** §6.8's `d3140eff…` is the
  LF-normalised hash; a Windows checkout of `arc-recon/data/piles.json` hashes to
  `f2ef44d1…`. The `3feca53e…` canonical-payload digest reproduces exactly. Worth a
  footnote given the paper invites the check.
* **The seal is not auditable.** §1.1's ground-truth seal rests on the string
  `"ground truth first read at M6, after M4 and M5 were green"`, written into
  `score_vs_truth.json` by `score_vs_truth.py:145` — the authors' own script asserting the
  authors' own discipline. The same is true of `battery/PREDICTIONS.md`'s "append-only from
  the commit that introduced it" and "written before `run_battery.py` was executed". The
  only thing that could make either auditable is git history, and the paper never appeals to
  it. If commit hashes and dates exist, cite them; otherwise state that the seal is a
  declaration, not a control.
* **Figures.** The three extractors *are* byte-deterministic — I ran each twice and diffed
  `figures/data/*.json` and `figures/*.txt`: identical. But no sentence in the paper
  references any figure (grep for `Figure`/`Fig.` returns zero hits), so three deterministic
  extractors currently support nothing. And two payload fields are hard-coded rather than
  read, against their own docstrings: `fig1_concept_timeline.py:111`
  `"revisions_driven_by_certify": 0` (docstring: "the extractor reads it off the record
  rather than being told it") and `fig2_coverage_accuracy.py:56` `"executable_probes": 0`
  for A0 (docstring: "Nothing here is retyped from the prose reports").
* **Submission mechanics.** 11 451 words is 2.5–3× a typical workshop budget. 17
  `[bib: TODO]` markers and no bibliography file. Placeholder authorship. `runs/` contains
  one file. These are known and flagged in the draft note, but they mean the artefact
  cannot be assessed as a submission yet.

### 14 · [SHOULD FIX] Novelty — where the paper is re-illustrating, and where the related work is missing

The paper is honest that its central claim "is not new". It is less honest about *how* not
new, and §8 does not cite the literatures that already own its results.

* **"Prediction perfect, understanding broken" is the paper's own setup, not a finding.**
  It is `Theoria.md` §1.3's premise, and §1.3 is what A2 was built to reproduce. A2's
  procedure is: take a certified manual, delete a rule that never fires in the retained
  history, observe that replay over that history does not notice. The observation is
  analytically guaranteed by the construction. The exhibit has real value as a teaching
  object and as an instrument test; it is not evidence about anything.
* **"Reversibility beats coverage" is a rediscovery of the reset assumption in active
  automata learning.** Angluin's L\* and the whole membership/equivalence-query line assume
  the learner can *reset* to a known state, precisely because without it a transition cannot
  be re-witnessed. A0's irreversible latch removes the reset for the button mechanism; A0′'s
  toggle restores it. The paper's finding is the standard reason that assumption is made.
  Not cited. Similarly, "replay coverage does not certify the model" is the FSM
  conformance-testing problem (Chow's W-method, Vasilevskii) — not cited.
* **The CEGIS "frontier of all consistent hypotheses, kept as probe material" is a version
  space** (Mitchell). Not cited. "Which experiment splits a guard frontier, **priced in
  bits**" is information-gain-based optimal experiment design / active learning. Not cited.
* **§5.6's conceptual point — Lean certifies relative to the manual, not the world — is the
  specification-validity problem**, the oldest caveat in formal verification (validation vs
  verification; De Millo–Lipton–Perlis; every "who verifies the spec" discussion since).
  §8.2 cites proof-carrying code for the *transport* discipline but nothing at all for the
  point the paper's headline exhibit dramatises. A reviewer from formal methods will read
  §5.6 as an unusually elaborate restatement of something their field settled decades ago,
  and the paper gives them no signal that it knows this.
* **"This is engineering, not a result"** applies cleanly to: all of §4 — `Theoria.md`
  itself defines A1 as "判死赌的是管线接通，不是 LLM 灵感", a plumbing test, and the paper
  should not let §4 read as a headline; §5.8's two compiler defects (real, useful, not
  results about world models); §6.1's battery plumbing; and §3.1's "the whole run takes
  about six seconds".

What *is* genuinely contributed is listed under "What is genuinely strong" below, and it is
worth a workshop slot — but it is an instrument-and-artefact contribution, and the paper
should say so in the abstract instead of "Four results."

### 15 · [SHOULD FIX] §6.6 — a Phase 4 conclusion drawn in a Phase 1 paper

"If capability alone produces front-loading, front-loading is not specific to *having a
theory*, and **C2's evidence weakens by however much of the effect capability explains**."
That is a substantive update to a Phase 4 claim, computed from a four-game pilot the paper
elsewhere says can certify nothing. §6.4's "it is a Phase-3 planning input" is fine as a
forward pointer; §6.6's sentence is a conclusion. Given §7.5 promises "Everything else in
`Theoria.md` … is unevidenced here and is not claimed", either soften §6.6 to "a confound to
separate before Phase 4 freezes" (which the next paragraph already says well) or drop the
weakening clause.

---

## Numbers checked

| claim | paper says | file says | verdict |
|---|---|---|---|
| A0 replay | 276/276 frames, 22 356/22 356 px, 0 anomalies (`A0_REPORT.md` §2) | `A0_REPORT.md` §2 verbatim; `certify_cheap_raw_trace.json` `frames 276, pixels_checked 22356, pixels_unexplained 0` | **match** |
| A0 accuracy | 233/236 = 98.73 %; held-out 0.000 | `score_vs_truth.json` `accuracy 0.987288, agree 233, pairs 236`; `held_out.accuracy 0.0` over `held_out_pairs 3` | **match** (n = 3 undisclosed in abstract) |
| R-05 pre-registration | "named, **with its three pairs**" | R-05 names three *directions* + one cell `(2,2) DOWN`; the "three pairs" gloss is written at M6 | **mismatch — overstated** |
| A0/A0′ table | 233/236 = 99 % vs 107/228 = 47 %; 228/228 = 100 %; probes 0 vs 13 | `prime/A0P_REPORT.md` §1 verbatim, every cell | **match** (but "47 % of A0's coverage" is 47 % of A0′'s *own* 228 pairs) |
| A0′ Run B replay | 111 frames, 8991 px, 0 anomalies @ `run_b.certify_cheap` | `run_b.certify_cheap` is literally `true`; the numbers are `run_a.certify_cheap` | **mismatch — wrong field, wrong run** |
| A0′ Run B repair | 0.991228 → 1.0000, 1 revision | `run_b.score_vs_truth_before.accuracy 0.991228` / `_after 1.0` | **match** |
| `ArenaEscape` diagnostic | verbatim string | `run_b.certify_lean`, character-for-character | **match** |
| MDL segmentation | 6511 vs 4423 bits; 90 vs 3 tracks | `A0_REPORT.md` §3 / `THEORIZE_LOG.md` O-01 say 6511/90; live `artifacts/engines_report.json` now says **5704 / 6 tracks**, with 6511/90 demoted to `reidentification.*_before` | **stale — artefact has moved** |
| per-object accounts | Cart **+2967**, Button −17, Door −13 | prose matches; `artifacts/concept_accounts.json` gives Cart **2125**, Button −5, Door −1 on the revised baseline. Paper reports the Button/Door revision but not the Cart's | **partial — Cart figure stale**; `PROVENANCE.md:42` cites the JSON, which disagrees |
| A2 exhibit gates | 184 frames, 14 904 px, 0 anomalies; UNSAT; Lean green; `#print axioms` `[]` | `exhibit_report.json` + `generated_holed/theory.lean:791`; 0 imports, 0 `Mathlib`, 0 `native_decide`, 0 `sorry` | **match** |
| A2 Lean state count | 148 states | `theory.lean:3` "States: 148"; 37 cells × 2 × 2 | **match** |
| A2 refutation | 18 actions, win on frame 18 | `solved_episode.jsonl`: 18 non-null actions + terminal `win: true`; `refutation.json` `length 18` | **match** |
| A2 full sweep | 248 frames, 44 anomalies, first at t184 (6,4); 128 px of 20 088 | artefact carries frames/anomalies/first_anomaly only; 128/20 088 exist in `A2_REPORT.md` §2 prose. Recomputed independently: 248/20 088/128/44 all correct. §5.4 now sources this correctly | **match** (fixed mid-review) |
| A2 anomaly "cap" | "the cheap layer caps its anomaly list" (44) | cap constant is **40** (`replay.py:68,82`), binding only `render_mismatch`/`unowned_pixel`; 44 = 40 + 4 uncapped `goal_mismatch` | **match in substance, misleading as phrased** |
| A2 history coverage | 163 of 164, omitting `cart=(6,4) pressed=1 act=DOWN` | `trace_summary.json` `coverage "163/164"`, `uncovered_pairs` exactly that | **match** |
| loop ledger | 8 beats, 8 pass, 0 fail, 0 absent | `loop_ledger.json` `summary {absent 0, fail 0, pass 8, total 8}`; extra beats are M0, M5 | **match** (ledger's `authority` cites INC-004 only, not D-A2-001) |
| the two Lean files | "differ in their weight table and in nothing else" | 52 changed lines: 14 weight, **1 `def Goal` (c10→c34)**, **4 `step` entries (c31→c35)**, header, comments | **mismatch — false** |
| holed vs full DSL | "diff the files and the deletion is the whole diff" | also: header 13→45 lines, all coverage annotations rewritten, `events:` loses `jumped`, `laws:` swaps theorem | **mismatch — false** |
| `probe.py`/`locate.py` | "import no world module at all" | `probe.py:59` `from a2world import a2_world` | **mismatch — false** |
| A1 certificate | `[-1,1,0,1,-1]`; 6 witnesses, deltas `0,0,-2,-2,0,0`; `inv_init` 0; `goal_break` 1 | all present in `pagoda_5_11011_to_00010.json`; deltas recomputed independently from `w[dst]−w[src]−w[over]` | **match** |
| A1 tests | "83/83 tests pass, eight of which invoke `lean` and read `#print axioms`" | 83 collected, 83 pass **with Lean installed**; without it 75 pass / 8 skip. Of the 8, **7** invoke `lean`, **6** read a named theorem's axioms | **partial — inflated, and toolchain dependency undisclosed** |
| A1 negative control | `w .p1 := 7` → `decide proved … is false`, four theorems `[sorryAx]`, exit 1 | `theory-compiler/STATUS.md` §独立复核, verbatim | **match** |
| A1 E-06 | `assert unprovable == [0, 2, 4]` | `engine-rig/tests/test_interop.py:65`, verbatim; control at :68–71 | **match** (D-014 is about the 4-cell fixture; tighter cite is the test) |
| a0-spike T-9 | 341 transitions, 8 mismatches, 315 reachable exact, 39 960 states, 1 966 vs 341 actions | `a0-spike/THEORIZE_LOG.md` T-9, all six verbatim | **match** |
| a0-spike T-10 | ghost 6 actions; nocross never in 341, 6 elsewhere | T-10 table verbatim | **match** |
| battery scope | 26 runs, 4 games, 2 arms | `capability_spectrum.json` `n_runs 26, n_games 4, arms [bare_cc, theoria_a0]`; 26 keys counted | **match** |
| battery metrics | 29 metrics, 5 families, 15 main / 14 reference | `METRICS.md` counts 29 over 5; main 15, reference 14 (`gaming_audit.json` agrees). Note `METRICS.md:7` and `DECISIONS.md:122` both say "twenty-eight" — repo bug, paper is right | **match** |
| K4 / K2 on `a0-base` | 1.000 over 7 clauses; 0.000 over 3 pairs, 0 agreements | `capability_spectrum.json` `K4 value 1.0, annotated 7`; `K2 value 0.0, {agree 0, pairs 3}` | **match** |
| discriminative verdicts | "every verdict `underpowered` or `no-data`" | 11 `underpowered`, 13 `no-data`, **5 `not-ranked`** | **mismatch** |
| sign test floor | smallest attainable p = 0.125; floor is 6 games | `REPORT_V0.md:40–43` verbatim; `discrimination.json` top-level `power` string present | **match** (`min_attainable_p` is on 11 of 29 metrics, nested under `sign_test`, not "per metric") |
| P1 confound | δ = −1.000; haiku 0.97, opus 0.52; 27–45 % failures; ρ = −0.83 | δ −1.0 ✓; haiku mean **0.9606**, opus 0.5176 ✓; ρ recomputed **−0.831** ✓; failure rates recompute to **28.3 %**–45.1 %, the 27 % lower bound does not reproduce | **partial** |
| E5 price list | δ = +1.000; $0.031 / $0.124 / $0.279 — "a 9× spread" | means 0.031719 / 0.124046 / 0.279259; true ratio **8.80×**, and haiku rounds to $0.032 | **partial — 9× is a rounding artefact** |
| E2 front-load | haiku 0.20, sonnet 0.25, opus 0.28; δ = +1.000; 4 of 4 | per-game aggregation gives 0.1994 / 0.2521 / 0.2830; `sign_test {wins 4, losses 0, n 4, p 0.125}` | **match** (the "three pre-registered primary endpoints" phrasing is `REPORT_V0.md:76`, not `PREDICTIONS.md`) |
| de-redundancy | 2 strong pairs, ρ = +0.916 / +0.909; 27 clusters from 29 | `redundancy.json` `n_metrics 29, n_clusters 27, min_shared_runs 4`; both ρ exact | **match** |
| K6 | mean +706 bits, one at +2125, two of three negative | `K6 value 706.333`, `support {best 2125, worst −5, concepts 3}`; Button −5, Door −1 | **match** |
| X5 cross-check | "59 … an independent cross-check, pinned by a test" | both counts descend from `cold-start-a0/world/explorer.py`; the battery adapter *does* read `trace_summary.json` (`a0.py:240,323`); the trace is by design a coverage walk over the reachable set | **overstated — not independent** |
| pile digest | `3feca53e…` is not the file hash; file hashes to `d3140eff…` | `sha256(payload minus its own `sha256`) = 3feca53e…41bbc19a` ✓; `sha256(LF-normalised file) = d3140eff…` ✓; Windows checkout gives `f2ef44d1…` | **match** (LF caveat undisclosed) |
| baseline pilot | 12 cells + 2 reruns, 109 actions, +44 campaign, 560 ledger rows, `levels_completed` 0 | `TOUCHED_GAMES.md:52,71,99–103`; 560 non-blank lines counted; all 185 rows carrying the field are 0. Note the printed 12-row table sums to **107**, not 109 | **match** (109 not reconstructible from the printed rows) |
| INC-BA-001 | 9 sealed games read, 2 materially | `INCIDENTS.md:37–47`, nine rows; `ls20`, `ft09` graded 实质泄露 | **match** |
| determinism precheck | 9/9, 3/3, 9/9, 9/9, all PASS | `arc-recon/data/precheck.json`, exact, in that order | **match** |
| engine count | §2.2 "Six engines carried the acceptances reported here… two more added at M9" | `engine-rig/engines/` has 8; `STATUS.md` L20 "eight engines". §8.2 cites `ic3_pdr` | **match** (fixed mid-review; earlier text said "six engines ship", contradicting §8.2) |
| `lp_potential` incompleteness | "sound but incomplete (`engine-rig/STATUS.md`)" | that phrase is not in `STATUS.md`; it is in `DECISIONS.md` D-014, `interop/README.md`, `engines/lp_potential/README.md`, root `CLAUDE.md` | **fact right, citation wrong** |
| figure determinism | "byte-deterministic: running them twice produces identical output" | ran all three twice; `figures/data/*.json` and `figures/*.txt` byte-identical | **match** |

---

## Minor issues

* **`CITECHECK.md` is referenced twice (`README.md`, `PROVENANCE.md:5`) and does not exist.**
  So does `runs/`, which holds one file.
* **No figure is cited in the text.** Three deterministic extractors, zero references.
  `OUTLINE.md` promises three figures; the paper has none.
* **`PROVENANCE.md:60`** cites `theory-compiler/src/certificate.py`; the file is
  `theory-compiler/src/theory_compiler/certificate.py`.
* **`PROVENANCE.md:41`** cites the segmentation bits to `THEORIZE_LOG.md` **O-03**; they are
  in **O-01**.
* **§6.1 cites `D-B-001`** for determinism; determinism is **D-B-008**. D-B-001 is
  "the guardrail verifies the cut, not just the id".
* **§4.2 cites `(D4, theory-compiler/DECISIONS.md)`** for the vector `[1,2,3,2,1]`. D4
  supports "hand-computed literal constants" but never names the vector; it is at
  `theory-compiler/STATUS.md:30`.
* **§3.1's "about six seconds"** is cited to §1/§3 of `A0_REPORT.md`; it is in the preamble
  and §7.
* **§1.1's seal gloss** — "after both certify layers and the plan were green" — the file
  says "after **M4 and M5** were green", and M5 is the unsolvable-variant milestone, not a
  planning stage.
* **§3.3's table** labels A0's explorer "exhaustive" in one row and its state-action coverage
  "233/236 = 99 %" in the next. Pick one word.
* **§3.3 renders the same fraction two ways one line apart** — 233/236 as "99 %" (coverage)
  and "98.73 %" (accuracy). Inherited from `A0P_REPORT.md` §1, but confusing.
* **§3.5's "the other track"** has no antecedent: the paper never says which track owns
  `cold-start-a0` or `theory-compiler`. Name them.
* **`deadlock_carver`** is shipped, tested and tagged, and appears nowhere in the paper — fine,
  but §2.2 should say so alongside `ic3_pdr` rather than leaving it silent.
* **§3.5's a0-spike corroboration is about reachability, not reversibility.** T-9's finding
  is that defects can hide in unreachable states; §3's thesis is that irreversible mechanisms
  cap re-witnessing. Related, but "reaches the same conclusion by a different route" is too
  strong.
* **§7.1(c)** cites the ARC determinism precheck as evidence the target environment satisfies
  the determinism assumption. Nine steps on one game and three on another is thin support for
  a framework-level assumption; the paper's own hedge ("appears to satisfy") is right but the
  numbers should be in the sentence.
* **Abstract's "caught independently by a coverage probe and by the Lean transcription"**
  drops the qualification §3.4 and §7.3 both make — the seeded clause escaped the declared
  arena, which is *why* Lean caught it for free, and it was untested, which is *why* the probe
  caught it. Both mechanisms fired because of the experimenter's choice of error. `A0_REPORT.md`
  §8 calls the Lean catch "unplanned"; the abstract should carry that word or the caveat.
* **`arc-recon/README.md:185`** still says "`contamination_register` records all 25 games as
  `never_audited`" while :173–177 says the log supersedes it. §7.2 corrects `CLAUDE.md` but
  not this; if the paper is in the business of correcting stale repo summaries it should be
  consistent.
* **`METRICS.md:7` and `battery/DECISIONS.md:122` say "twenty-eight" metrics** against a
  29-entry registry (stale string at `battery/docs.py:35`). The paper is on the right side;
  worth telling the authors since `METRICS.md` advertises itself as generated and test-pinned.
* **Typography.** Mixed `·` and `—` section separators, Chinese terms glossed inconsistently
  (§5.5's table glosses 重证 as "re-proof", §1.3's list as "re-certify").

---

## What is genuinely strong

Kept short, and every item here survived checking.

1. **The provenance discipline is real and it mostly works.** Roughly forty numbers were
   checked against their cited files and the great majority matched exactly, several to six
   decimal places, including arithmetic I recomputed independently (the six pagoda deltas, the
   Spearman ρ = −0.831, the 27-cluster count, the 148-state derivation, the sha256 of the
   canonical pile payload). Very few papers survive this. The failures found here are
   concentrated in *prose framing*, not in the numbers.
2. **The negative control in §4.3 is the single best methodological move in the paper.** An
   empty axiom list is worthless unless someone has made it non-empty on purpose;
   `w .p1 := 7` → `decide proved … is false`, all four theorems `[sorryAx]`, exit 1, checks
   out verbatim. More papers should do this and almost none do.
3. **`CertificateGapError` — the compiler refusing to generate rather than narrowing the
   theorem — is the right behaviour and is correctly presented as a headline rather than a
   caveat.** The accompanying `assert unprovable == [0, 2, 4]`, which forces a future "fix" to
   argue for itself, is a genuinely good piece of engineering hygiene.
4. **§7 is better than the paper it is attached to.** Transcribing a pre-declared honesty
   list clause by clause, and correcting the repository's own `CLAUDE.md` in §7.2 rather than
   repeating a convenient falsehood, is exactly right. INC-BA-001 — self-reporting that a
   subagent contaminated nine sealed games — is disclosed at real cost to the project and with
   no upside.
5. **The battery reporting its own metrics as broken, in the same pass that introduced them,
   and demoting K4 to reference tier with "K4 must never be reported without K2 beside it"
   written into `gaming_audit.json` rather than into prose.** The P1 finding in particular
   (ρ = −0.83 against step-failure rate) is a real discovery and is acted on in code.
6. **The figure extractors are byte-deterministic, as claimed** — verified by running each
   twice. Two hard-coded fields aside, the principle ("a figure whose data cannot be
   regenerated byte-for-byte is a figure a reviewer cannot check") is correct and rare.
