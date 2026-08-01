## 11 · Limitations and honesty clauses

`Theoria.md` §3.2 item 8 fixes, in advance, the list of things this project must
disclose. It is transcribed here clause by clause and answered for *this* paper,
followed by the limitations the individual acceptance reports raise on their own
account. Nothing in this section is a concession extracted by a reviewer; all of
it was written down by the runs themselves, and the paths are given so it can be
checked rather than believed.

### 11.1 The pre-declared clauses, answered

**(a) 便宜是预测 — "cheap" is a prediction, not a result.** `Theoria.md`'s cost
claim (C5, total spend 10⁸ → 10⁶) belongs to Phase 4 and is not evidenced here in
any form. This paper reports no cost comparison between arms. The battery's
economy family is `not-applicable` on the Theoria arm for a structural reason
given below.

**(b) 理解不消灭组合爆炸 — understanding does not abolish combinatorial
explosion.** PSPACE-hardness is untouched; the design's answer is engines and
caching, not a claim of tractability. Every world in this paper is tiny: 59
reachable states in A0 (`cold-start-a0/artifacts/score_vs_truth.json`), 57 in A0′
(`cold-start-a0/prime/artifacts/prime_report.json`), 55 in A2 with 148 in the
Lean enumeration (`cold-start-a2/A2_REPORT.md` §8), and a 5-hole board in A1
(`theory-compiler/STATUS.md`). Lean's `decide` is affordable at these sizes and
will not be at 10⁶; `theory-compiler/STATUS.md` records the sharper version — an
empty axiom list and a linearly-sized proof are **not simultaneously available**,
with the `computational` route empty-axiom at O(2ⁿ) (2³³ on the 33-hole English
board, not runnable) and the `algebraic` route linear but carrying `propext` and
`Quot.sound`. Both are honest; the trade-off is D-TC-008. **Scale is untested,
and no result here should be read as evidence about it.**

**(c) 仅确定性环境 — deterministic environments only.** Every world in this paper
is deterministic and self-built. `arc-recon/README.md` reports that the
cross-session determinism precheck now passes on all four development-pile games
(9/9, 3/3, 9/9, 9/9; `arc-recon/data/precheck.json`), so the target environment
appears to satisfy the assumption — but nothing here has been run under
stochasticity, and the framework as designed does not cover it.

**(d) 语法脚手架披露 — disclose the grammar scaffolding.** The DSL is ours, and it
did not stay fixed across the three acceptances. `dsl_grammar_v0.1` was frozen
before A0; A0's run produced an expressivity ledger of five gaps
(`cold-start-a0/THEORIZE_LOG.md` §E: E-01 guard negation, E-02 direction lifting,
E-03 the frame axiom, E-04 landmark declaration, E-05 weight vectors), and
`CONTRACTS/dsl_grammar_v0.2.md` was then authored to close them, with each
revision annotated with the ledger entry that forced it
(`theory-compiler/STATUS.md`). E-03 is the load-bearing disclosure: until v0.2,
the most important semantic fact about `step` — that an object no rule fires for
is unchanged — lived in a comment at the top of `theory.dsl` and was hard-coded
in all three backends. A manual whose default behaviour is a comment is not a
manual, and A0's results were produced under that condition. The ledger is
public, the grammar diff is public, and v0.1 was not edited.

**(e) 单一 benchmark 家族 — a single benchmark family.** This paper is weaker than
that clause anticipates: it reports **no benchmark result at all**. Every world
in §3–§5 was built by us; A1's is peg solitaire. The one thing recomputed over
ARC trajectories is the battery (§7), and those trajectories are a control-arm
pilot, not a Theoria result.

**(f) 封存堆污染分级与预训练先验 — sealed-pile contamination grading and the
pretraining-prior caveat.** Two entries, and both are worse than "clean":

* **INC-004.** A2 could not be the literal A2. The upstream game named in
  `Theoria.md`'s A2 item is in the sealed pile, and reading its released
  artifacts teaches its mechanics as effectively as playing it. The owner ruled
  option (b) — a self-built world isomorphic to the failure structure, with the
  isomorphism argument citing only the structural description already printed in
  `Theoria.md` §1.3 (`cold-start-a2/A2_REPORT.md` §1;
  `cold-start-a2/artifacts/loop_ledger.json` records the ruling as the run's
  authority). The same incident **downgrades that game's own seal**, from
  `never_audited` to `design_document_disclosed`, on the independent ground that
  `Theoria.md` discloses its mechanics in §1.3 and §3.2 — it was
  design-document-contaminated before the cut was ever made. **No claim about
  that game is made anywhere in this paper**, and any later claim must carry the
  caveat.
* **INC-BA-001.** The sealed pile is no longer 21 games at `never_audited`. While
  locating an upstream release, a search subagent read mechanics descriptions for
  **nine** sealed games before the page was judged unsafe, two of them
  materially (`baseline-arms/INCIDENTS.md`; `baseline-arms/TOUCHED_GAMES.md`).
  This was not an API call and no guard could have caught it; the institutional
  consequence recorded there is that the upstream artifact set is a
  read-it-and-you-contaminate-everything object whose only safe use is
  directory-name-exact selection of development-pile games. Phase 4's exam items
  must now avoid those nine.
* **Pretraining prior.** Public-game walkthroughs may already be in the
  pretraining corpus. The design's mitigation is that all three arms share a
  model so the *comparison* survives, plus the hard rule that game ids never
  enter model context. Any absolute phrasing of "induced from zero" is
  discounted accordingly. This paper makes no induction claim about any ARC game.

### 11.2 A correction to the repository's own summary

`CLAUDE.md` states that no game has been played and that all 25 are registered
`never_audited`. That was true when written and is **not true now**. The
baseline pilot played all four development-pile games — 12 cells (4 games × 3
models) plus 2 reruns, 109 successful actions, followed by a variance-envelope
campaign adding 44 more on one game — and all four are recorded at
`trajectories_reviewed`, because a model read the frames pixel-by-pixel and chose
actions from them (`baseline-arms/TOUCHED_GAMES.md`; `baseline-arms/ledger.jsonl`,
560 rows). No game was ever completed: `levels_completed` is 0 throughout, and
nothing reached level 2. This is the legitimate use of a development pile, and
recording it is the point of having one; it is corrected here because a paper
that repeated `CLAUDE.md`'s sentence would be repeating something false.

### 11.3 What the individual acceptances do not show

**The theorize step is not a measured LLM step.** This is the largest caveat in
the paper and it is stated first. `cold-start-a2/A2_REPORT.md` §8 puts it
plainly:

> Nothing about whether an LLM would have written these manuals. The theorize
> step is done by hand here, as in A0 — the DSL files are checked in as
> artefacts. A2 tests the instrument and the loop, not the theorizer.

The consequence is visible in the battery: `battery/REPORT_V0.md` records that
"A0 ran engines and hand adjudication with no LLM in the loop, so it has no model
calls", which is why **every economy metric is `not-applicable` on the Theoria
arm**. The adjudication records in `cold-start-a0/THEORIZE_LOG.md` and
`cold-start-a2/THEORIZE_LOG.md` are genuine and were written
before the scores existed, but nothing here measures a prompted theorize step
inside a harness, and no number in this paper should be read as one.

**The seal has one hole, in the same place twice.** In A0 and A0′ the same
instance built the world and adjudicated it (`cold-start-a0/A0_REPORT.md` §6.3;
`cold-start-a0/prime/A0P_REPORT.md` §5.5). No ground-truth file was opened before
M6 and every verdict is written to be re-derivable from the candidate stream
alone, but that is weaker than a genuine blind and the reports count it as a
threat to the result rather than a footnote. A2 mitigates differently rather than
better: it reuses an unmodified upstream compiler, hashes every imported file — 22 of them in
`cold-start-a2/artifacts/upstream_pin.json` — and verifies read-only-ness by
hashing 258 files before and after a full run (`cold-start-a2/A2_REPORT.md` §7,
which is where the 258 figure lives; the pin file does not carry it).

**No multi-round repair, anywhere.** Revision counts across the whole paper are
0 (A0), 0 (A0′ Run A) and 1 (A0′ Run B), each recorded as a `revisions` field in
`cold-start-a0/prime/artifacts/prime_report.json`. A2's loop ran its 修订 beat
once, but **no file in the tree states a revision count for A2** — the ledger's L4
beat records `re_derivable_from_grown_evidence: true` and no number — so "one
revision" for A2 is this paper's reading of the ledger, not a figure it can cite.
The failure class 修订抖动 is
unmeasured, and `cold-start-a0/prime/A0P_REPORT.md` §5.1 says so: nothing here
exercises a manual that must be revised, re-probed and revised again.

**The seeded error was of a convenient kind.** A0′ Run B's clause escaped the
declared arena, which is what let the Lean form catch it for free. A wrong rule
that stays inside the arena would have had only the coverage probe, and only
because the clause was untested; a wrong-but-*tested* clause would fail replay.
A right-looking-but-wrong clause on a tested firing state is covered by neither
mechanism, and `A0P_REPORT.md` §5.2 calls that gap real.

**A1 proved less than the manual asserts, and refused to hide it.** The peg
manual's `goal count(Peg, alive) = 1` was not proved. Three of the five singleton
end states are pinned by `engine-rig`'s own tests as *not derivable* by the linear
pagoda method — not merely unexported — and the compiler responds with
`CertificateGapError`, naming the uncovered end states and declining to generate,
rather than silently narrowing the theorem into one that reads stronger
(`theory-compiler/STATUS.md`, ledger entry E-06; D-TC-010, since superseded by
D-TC-022). That refusal is now past tense — the compiler emits a hybrid
development for this manual and refuses only above its enumeration bound — and the
ledger entry is discharged, by exhaustion rather than by any extension of the
invariant language (`cold-start-a0/THEORIZE_LOG.md`, E-06, **discharged**; §4.4,
which also records that the per-goal attribution the discharge claims is a
generated comment rather than a checked property). The limitation below is
unaffected: the linear pagoda method still cannot reach those three end states. The whole A1 verification also
ran on exactly **one** 5-hole fixture; the pipeline's generality is not supported
by this evidence.

**`lp_potential` is sound but incomplete.** It never certifies a solvable
configuration, but some genuinely unsolvable ones admit no linear pagoda
(`engine-rig/DECISIONS.md` D-014, `engine-rig/interop/README.md`; the phrasing is
`CLAUDE.md`'s). E-06 is that caveat arriving in practice. §10.2 and §10.5 report
a second, separate defect in the same engine — until recently it could not tell
an iteration cap from infeasibility — and the incompleteness rate it publishes
rests on a reviewer's re-derivation.

**Every planning number in this paper came from the bundled BFS stub, not from
Fast Downward.** Fast Downward *was* built and wired into A0/A0′ and agrees with
the stub on all three instances including the UNSAT variant, with no caller code
changed (`cold-start-a0/BLOCKER_FAST_DOWNWARD.md`,
`cold-start-a0/artifacts/fd_real.json`, `cold-start-a0/STATUS.md`) — but that is
a separate conformance artefact. The reproducible pipeline (`cold-start-a0/run_all.py`,
`prime.run_prime`) plans through `cold-start-a0/pipeline/plan_stage.py:59`,
which calls `solve(..., prefer="stub")` **on purpose**, so its
checked-in artefacts stay byte-identical whether or not a planner is installed.
§3.1's 12-step plan and every other planning figure in §3 are the stub's. The
stub is length-optimal for unit costs, so SAT/UNSAT verdicts and plan lengths are
sound at these sizes; nothing about search at scale is evidenced. A2 likewise ran
on the stub (`cold-start-a2/A2_REPORT.md` §8), and `engine-rig`'s shipped default
is still the stub.

Reproducing `fd_real.json` needs Fast Downward built locally: the artefact records
an absolute path into a `.toolchain/` directory that is gitignored and not in the
tree. Three of the repository's own statements about this disagree —
`cold-start-a0/A0_REPORT.md` §5 and §6.5 say "still not connected", its §8 item 4
says FD "could not be built (three failed compiler attempts)", and
`BLOCKER_FAST_DOWNWARD.md` and `cold-start-a0/STATUS.md` record the successful install dated
2026-07-28. The install is the latest. None of the three was edited, as no report
in this repository is; where they disagree the paper cites all of them and says
which is later.

**A2's goal was supplied, not induced,** as was A0′'s: the truncated trace never
wins, and the goal is confirmed empirically afterwards rather than derived
(`cold-start-a0/prime/A0P_REPORT.md` §5.3).

**Two of A0's three real defects were in the compiler, not the theory**
(`cold-start-a0/A0_REPORT.md` §6.4). A wrong backend is indistinguishable, from
inside the loop, from a wrong manual — and one of those bugs manufactured a
*false* UNSAT, which under constraint 6 would have triggered a certificate
obligation for a theorem that is false. §10 is the systematic form of that
observation: a census of every place a tool's failure state is read as a fact
about the world. The four-co-derived-forms design is meant to make that drift
visible; here it took a human reading the plan output — and on the fourth form
the mechanism was, for most of this project's life, not weak but inoperative.
The next paragraph is the census that established that, and the repair it
forced.

**The general PDDL backend produced nothing usable until 2026-07-31.** A
crosscheck census dated 2026-07-30 measured
`theory_compiler.generators.gen_pddl` — the backend on both documented compile
paths from the two books, behind the live arm's handbook and both handover
packages — at **0 of 303** actions compiling to PDDL that is both well-formed
and semantically non-empty, a zero that survives every slicing of the
denominator and is confirmed by an independent planner: Fast Downward's
translator accepted only domains whose actions assert nothing
(`crosscheck/FOUR_FORMS_TRUTH.md`; the frozen record is
`crosscheck/runs/20260730T120005Z-C14-four-forms-is-three-and-a-half/`). An
empty form cannot disagree with anything, so on that form the visibility this
design promises did not exist. Three scope clauses keep the finding its right
size. First, **no planning number in this paper ran through that backend**:
every plan here was produced over PDDL from the world-specific generator
`cold-start-a0/compile/gen_pddl_a0.py` and its per-world drivers — hand-fitted
to this family of worlds, and carrying its own recorded defects (§5.8, §6.6) —
and
`crosscheck/runs/20260730T120005Z-C14-four-forms-is-three-and-a-half/out/TWO_BACKENDS.md`
maps each planning artefact to its generator, so the empirical planning claims
above stand or fall with backend defects recorded in their own sections, not
with this zero. That provenance statement is about how the data was made, and
the later repair does not change it. Second, the census measured **the PDDL
form only**: nothing in it verifies the Lean, Python or Markdown forms, and
"three of four forms verified" is a sentence this work has not earned — the
lesson of the zero is that *emitted* is not *valid*, and asserting the other
three unmeasured forms would repeat the error being corrected. Third, the
repair landed and was measured with the same instrument: `gen_pddl` was
repaired on 2026-07-31, and the re-run census counts **196 of 299** actions
semantically non-empty, with the other **103 as declared refusals** — 34
theories whose guards use geometry or arithmetic the grammar cannot yet
express, refused with a written reason rather than emitted empty under a green
light (`crosscheck/runs/20260731T061500Z-C14-after-the-repair/out/census.md`).
The census's own methodological caveat carries over to the 196: its bar is a
ceiling on correctness, not a floor on brokenness — an action can be non-empty
and well-formed and still ground to nothing or invert a guard — so that count
is of forms passing the bar, not of forms verified correct
(`crosscheck/FOUR_FORMS_TRUTH.md` §3).
The A0 manual's generated planning form now grounds every schema and solves
its level in the 12 steps the world is known to need, pinned as a test
(`theory-compiler/tests/test_e2e_rehearsal.py`); the handover packages were
rebuilt the same day, `a0-cart` with all five files of its four forms
generated and `a0-sokoban2` with its planning form a declared refusal whose
reason is printed on the package's own cover
(`theory-compiler/handover_packages/a0-cart/README.md`,
`theory-compiler/handover_packages/a0-sokoban2/README.md`); and the failure
shape the census caught is guarded in code — the generator parses its own
output before shipping, and the live arm's `theoria-arm/inner/books.py` keys
its green on the planning and prose forms too, turning red on an undeclared
PDDL failure. The pre-repair record stays frozen, because the zero is what
forced the repair.

### 11.3a The probe beat, measured against live play, contradicts its own design

§2.3 offers `probe` as the answer to this paper's title: neither certification
layer checks the manual against the world, and the probe beat is what does. That
sentence has now been measured on live ARC play, on 2026-08-01, and **it is
false as written**. It is stated here with the measurement and the date, the way
§11.3's four-forms correction was stated on 2026-07-31, because a claim that a
mechanism works as designed is exactly the kind this paper keeps finding it has
to withdraw.

**The frontier could not have contained the answer.** The live arm builds its
hypothesis frontier by ablation in `theoria-arm/inner/probe.py`: the manual as
written, an inert reading, and one without-rule-N variant per schema. That family
is closed downward under clause deletion, so no member of it states a mechanism
the manual does not already state. Over the four live legs of 2026-07-31 the
measured consequence is unambiguous — 56 probes designed, 52 completed, frontier
width **two distinct predictions on every one of the 52**, **47 of the 52
observations matching no hypothesis at all**, realised information gain **0.000
bits on all 56** against a design-time price of 0.5436–1.0000 bits, and **zero
monotone frontier shrinks** in any leg
(`theoria-arm/runs/20260801T0000Z-A-probe-economics/README.md` §1;
`theoria-arm/runs/20260801T0900Z-R2-frontier-by-generation/MANIFEST.json`).
Every number in that list was recounted for this paper from tracked files alone,
because the arm's own measurement reads a per-leg frame trace that is gitignored,
so a reader of this repository could not re-run it; all six recomputed quantities
agree
(`papers/phase1-workshop/runs/20260801T1200Z-P23-probe-frontier-contradicts-the-design/census.py`,
`--check`).

**And it is the design document the measurement contradicts, not only the
implementation.** `Theoria.md`'s engine table assigns the rule miner the job of
returning 全体一致假设的前沿, the frontier of all consistent hypotheses rather
than a point guess, and names that frontier 戳探的原料. Across the eight live
legs that carry an engine record, `cegis_miner` was dispatched **48** times and
returned a refusal with a written reason **48** times, with zero errors — so the
mined frontier the design is built on has never once reached a live probe
(`papers/phase1-workshop/runs/20260801T1200Z-P23-probe-frontier-contradicts-the-design/census.json`,
key `cegis_miner`). The arm was not discarding a frontier the engine had
computed; the engine declined, on every dispatch, for a reason it wrote down
(`theoria-arm/runs/20260801T0900Z-R2-frontier-by-generation/README.md` §1).

**What the 47 misses actually were, which is not what the failure taxonomy would
have guessed.** Reading the grids rather than their hashes decomposes them
exactly: **35** of the 47 were designed from a state the world had already
left — the manual's rolled-forward state, which is the anchor every hypothesis is
a successor of, did not equal the frame the world was showing, and all 35 of
those landed off-frontier; **12** were correctly anchored and missed by a delta
containing exactly one cell that had never changed before in the run, a board
cell on which the arm seats no object instance and which no rule in this grammar
can name; and **0** are attributable to choosing the wrong action
(`theoria-arm/runs/20260801T0900Z-R2-frontier-by-generation/MANIFEST.json`, the
`measurement` block). So 戳探设计差 — the failure class §2.4 pre-declares for bad
probe design — is the wrong diagnosis for all 47. The classes actually hit are
state drift and 表达力不够, and the second of them is a grammar limit rather than
a probe limit: a confirmed edge hypothesis about a board cell is a fact the arm
can hold and cannot write down.

**The repair has offline evidence only, and saying more would be the error this
section exists to record.** A generated frontier — successor hypotheses anchored
on the world's own last observed frame rather than on the manual's state — is
implemented and **default off**, with the ablation path byte-identical; replayed
through the real builder against manuals recompiled from each leg's own
snapshots, with all 52 probes reconstructed exactly before anything was scored,
it contains the world's answer **43 of 52** where ablation contains it 5
(`theoria-arm/runs/20260801T0900Z-R2-frontier-by-generation/MANIFEST.json`, the
`replay` block). That is a counterfactual about containment on recorded states,
not a forecast for a leg: a real leg diverges after the first probe whose answer
differs, **no live leg has ever run with the switch on**, and 9 of the 47 are
missed even on the replay — six opening probes with too little history for an
edge chain, and three correctly-anchored mid-leg probes where the extrapolated
edge lands on a different board cell than the world burned. The drift is
diagnosed and *not* repaired; re-seating the manual's state on the world's frame
would make the replay layer trivially green and destroy the only instrument that
currently detects a wrong manual.

**Underneath all of it: no level has been completed.** Every live leg of the
Theoria arm carries a tracked level record, and across all ten of them — the six
the battery reads and the four added by the two rounds since — the total number
of level-completion rows is **zero**, and the two rounds that publish the figure
directly report `levels_completed: 0` on every leg, each stopped by the spend
gate rather than by understanding
(`papers/phase1-workshop/runs/20260801T1200Z-P23-probe-frontier-contradicts-the-design/census.json`,
keys `levels` and `rounds`; `battery/STATUS.md` §B18 for the six-leg reading).
No claim in this paper rests on a completed level, and none should be read as
implying one.

### 11.4a Three defects found in the instruments that read the live legs

None of these is a result about world models; all three are results about
measurement, which is the register §1.2 says this paper is strongest in, and each
was found by an instrument other than the one it indicts.

**A cost curve that lost its most expensive call.** The arm builds a turn record
at the top of the loop and appends it at the bottom, and the desk call spends in
the middle — so when the spend gate stopped a leg the exception unwound past the
append and the turn in flight was never written. Every gate-tripped leg
understated its own bill: r2 by $1.63 of $9.56 and r3 by $1.68 of $13.44, which
is **12–17 %** of the money, and the arm's own self-check could not see it
because the vanished turn had issued no ARC command, so the command counts
balanced exactly (`theoria-arm/DECISIONS.md`, the entry for the in-flight turn;
the cross-territory report that caught it is
`monitor/inbox/20260731T1731Z-battery-to-theoria-arm-curves-shortfall.md`). It
was found by a three-way reconciliation from another territory, not by the arm.
Repaired at three levels — the loop parks the in-flight turn, the archiver
reconstructs leftover invocations as rows that own no command and say why, and
`theoria-arm/armtools/curves.py` now checks three equalities instead of one — and
the join confidence stays `degraded`, because money adding up must not launder a
claim about the join. Any cost figure in this paper drawn from a gate-tripped
live leg predates that repair unless it says otherwise.

**An endpoint check that was reading names instead of statements.** The first of
the three frozen primary endpoints decided its criterion with a prefix matcher
over theorem *names*, which makes it a naming-convention detector: a name is a
label the arm picks freely. The development the endpoint's own rule text names as
the paradigm of what it means — a deadlock theorem over 28 672 states, with an
empty axiom set (`freeze/STATS_RULES.md`, the G1 argument) — was being labelled
vacuous by it, and the same illness was found a second time in *definition*
names, where a hard-coded lookup missed an invariant that was called something
else. The repair reads what a theorem proves off its statement; the census over
the 24 Lean books on disk moves `discharged` from **14 to 17** and `vacuous` from
**9 to 2**, with **4** newly `unclassified` and the one `failing_obligation`
unchanged, and every one of the seven moves is an accusation being withdrawn
rather than a pass being granted
(`freeze/runs/20260801T0700Z-E1-kind-census/COMPARISON.md`;
`freeze/runs/20260801T0700Z-E1-kind-census/CENSUS.md`; `freeze/theorem_shape.py`).
`vacuous` and
`unclassified` are now different words because they are different acts — one is
an accusation, the other a confession that the check does not know this kind of
assertion — and both still count as not attained.

**The battery's headline anti-gaming number is one finding stated many times
over.** §7 and §1.2 report that 37 of 38 metrics were driven to their
pre-registered thresholds by blind attackers, and §11.5 carries it as a
contribution. A follow-up ruling on 2026-08-01 demotes what that number means
without changing the number: the attackers wrote zero-argument constructors
returning the run record itself, so every metric being a total function of that
record reduces "can this metric be pushed over its threshold" to "is this
threshold reachable by any record at all" — a property of the threshold, not of
the metric. The attack techniques really are mechanically heterogeneous, and they
share one threat model, and under it a universal demotion is what a tautology
looks like from outside (`battery/STATUS.md`, the V-E2L note;
`battery/runs/20260801T0300Z-E2L-frontload-step-axis/RUN_STATE.md` §1). Narrowing
the threat model does not rescue it: the narrowed filter cleared four economy
families, that clearance was then defeated by attaching forty step records — pure
layout, which the poverty certificate explicitly permits — and the defeat is
pinned as an assertion so that a green there reads as somebody loosening the
audit. The blocker underneath is not metric quality at all: the endpoint is a
paired difference and there are zero pairs, so no amount of replication on this
one arm buys one.

### 11.4 What the battery cannot yet certify

Restated from §7 so that the limitations section is complete on its own. Every
ranked metric's verdict is `underpowered` or `no-data` — **31 of 38** on the model
ladder and **31 of 38** on the specified gradient, the other 7 in each case being
direction-less diagnostics returned as `not-ranked`
(`battery/artifacts/discrimination.json`,
`battery/artifacts/discrimination_arms.json`) — and that is arithmetic rather than
softness: a two-sided sign test over four paired games has a smallest attainable p
of **0.125**, so no metric can clear p < 0.05 on this data however cleanly it
separates, and six non-tied paired games is the floor for the test to be able to
clear the bar at all.

Two statements this section used to make have been overtaken and are corrected
rather than left standing. There **is** a Schema arm — 8 runs of released upstream
trajectories, which is what let process 1 run on the gradient `Theoria.md`
specifies; what does not exist, and may never, is a *reproduction*, because the
harness was never published (`baseline-arms/SCHEMA_LOCATE.md`;
`battery/DECISIONS.md` D-B-019). And the model ladder is no longer the substitute
for that gradient but a second, differently-confounded pass beside it, which is
why §7.6 reports P1 separating the two in opposite directions.

What does not change is the part that matters here: the battery's author also
wrote the metric definitions, which is structurally impossible to blind; five
metrics on A0 are marked `[seen]` post-dictions in `battery/PREDICTIONS.md` — K1,
K2, K7 and K8 in the v0 seal, K14 added in the v1 table — rather
than being passed off as predictions; and **21 of 38 metrics have never been
checked against any known gradient at all** — the entire epistemic family, the
entire mechanism family, and P4 — a count that adding a whole second control arm
moved by zero (`battery/artifacts/validation_material.json`).

One further data-integrity note belongs here rather than in §7: the ledger the
battery reads was produced in part by two concurrent sessions on the same track
sharing one budget and one API quota without knowing about each other
(`baseline-arms/INCIDENTS.md` INC-BA-003). The runs are individually accounted,
but any aggregate read off that ledger inherits the incident.

### 11.5 The one thing this paper claims

**We built an instrument for holding a world model as an explicit,
machine-checkable theory, ran it end to end on small deterministic worlds we
constructed ourselves, and then applied the same adversarial standard to our own
measurements, where it did the most damage.** That is a claim about an artefact
and a negative result about a measuring instrument. It is not a claim about world
models.

Itemised, and in the order a reader can check them:

That the pipeline runs end to end on self-built deterministic worlds; that on
those worlds a manual can be perfect on replay and wrong about the world in a way
that was predicted in advance and later measured; that reversibility of a
mechanism mattered more than breadth of trajectory in an A0/A0′ contrast which is
**not** controlled — the two worlds differ in mechanism, rule count, state count
and explorer budget at once, so the outcome is entailed by the construction (§3.3)
— ; that a machine-checked impossibility can be produced whose weights crossed a
data boundary between two sessions that do not import each other's code and whose
empty axiom list is a check that has been made to fail on purpose; that the
refutation loop closed on a false theorem in six recorded beats; and that a
passive metrics battery over existing trajectories, once its anti-gaming register
was made executable rather than written, contradicted 17 of its own register
entries by demonstration — 14 of them defence claims
(`battery/artifacts/gaming_audit.json`) — found the exploration family's declared
signature separating the specified gradient backwards, and, when re-attacked blind
against thresholds committed in advance, had 37 of its 38 metrics driven to those
thresholds and its main table cut from nine to two — and to zero by a sighted
follow-up review
(`battery/runs/20260729T021247Z-V9-battery-gaming-audit/v9_gaming_audit.json`;
§7.7 reports the earlier round, whose artefacts were frozen before this one, and
§1.2 states the five limits that qualify all of it — including that the
adjudication rule was amended after the results were seen).

Two of the clauses in that itemisation are weaker than they read, and §11.3a and
§11.4a say how. The blind round's headline is retained as a number and demoted as
an interpretation: a universal demotion obtained by an attacker who is also the
record's author measures the reachability of thresholds, not the resistance of
metrics (`battery/runs/20260801T0300Z-E2L-frontload-step-axis/RUN_STATE.md` §1).
And nothing in the itemisation is a claim about the probe beat working on a live
game; the frontier it split there was closed downward under clause deletion and
contained the world's answer 5 times in 52
(`theoria-arm/runs/20260801T0900Z-R2-frontier-by-generation/MANIFEST.json`).

Everything else in `Theoria.md` — the ordering claim, the bill shape, transfer,
the exam, the cost magnitude — is unevidenced here and is not claimed.
