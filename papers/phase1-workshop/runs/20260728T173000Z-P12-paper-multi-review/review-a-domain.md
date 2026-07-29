# Review (a) — the domain referee: novelty and fairness to prior work

**Paper:** `papers/phase1-workshop/PAPER.md` (v0.3, ~23 700 words)
**Bibliography:** `papers/phase1-workshop/references.bib` (70 records, 65 cited)
**Remit:** novelty; fairness of §11 to prior work; where a hostile expert says
"done"; whether §10.5 is overstated; whether the framing is honest about scale.
**Venue assumed:** a workshop on LLM agents / world models / neurosymbolic
reasoning.
**Recommendation:** major revision. The paper is unusually honest at the
sentence level and unusually careless at the *positioning* level. Its epistemic
hygiene is the best I have read in this area; its related-work section is
missing the four literatures that a domain expert will reach for first, and its
one-claim paragraph (§10.5) contradicts three of the paper's own hedges.

I have written this without consulting the other four reviewers and without
network access. Where I name a work as missing I have checked it appears nowhere
in `references.bib`, `PAPER.md`, `REVIEW.md`, `CITECHECK.md`, `OPEN_ITEMS.md` or
`REVIEW_TRIAGE.md`.

---

## 0 · Summary judgement

This paper's real contribution is **an instrument for making a specific failure
mode of induced world models reproducible, plus an unusually severe
self-audit of a measurement battery.** That is worth a workshop slot. But the
paper is currently positioned as a *wave* in the world-model literature (§11.1,
`PAPER.md:2388`), and on that framing it will be rejected, because the third
wave it claims already has occupants it does not cite.

The single most damaging fact about §11 is not an inaccuracy. It is an absence:
**there is no citation to Chollet, none to ARC-AGI in any form, none to
theory-based reinforcement learning, none to object-oriented / schema-network
world models, none to LLM agents with explicit skill libraries, and none to the
benchmark-contamination or construct-validity literatures.** Four of those are
load-bearing for four different sections. A referee who knows the area will
notice all four inside five minutes.

---

## 1 · What is actually new here

### 1.1 The contribution, in my words

Stripping the framework vocabulary, the paper does five things:

1. Builds a pipeline that induces a symbolic transition model from pixel traces
   of a small deterministic grid world, compiles it to four backends, and
   discharges declared invariants in Lean with `#print axioms` inspected.
2. Constructs — deliberately — a pair of Lean files with identical generator,
   tactic, dependency surface and empty axiom list, one of which states a
   theorem true of its world and one of which does not (§5.6,
   `PAPER.md`:§5.6 table). This is the "artefact" half.
3. Runs a mechanical repair loop that consumes the refutation and closes it in
   six recorded beats, each beat settled by a named file.
4. Transports an LP-derived pagoda certificate across a JSON boundary to a
   consumer that re-derives every obligation instead of trusting the
   `verified` flag, and makes the compiler *refuse to generate* when the
   invariant language cannot carry the conclusion (§4.4).
5. Recomputes a 38-metric battery over pre-existing trajectories and then
   attacks every metric with an executable exploit, finding 34/38 still land
   and 17 register entries contradicted by their own demonstration (§7.7).

### 1.2 Is "instrument-and-artefact" the right claim?

**Yes — and it is the best decision in the paper.** The abstract's closing
sentence ("The contribution is an instrument and a demonstration artefact …
not a result about world models", `sections/00_abstract.md:122–124`) is exactly
the right altitude for what §§3–9 contain. Item (2) above is a genuinely useful
teaching artefact: a *diffable* pair where the formal instrument returns `[]`
for a true and a false theorem is a better pedagogical object than another
prose warning about specification validity, and I would use it.

**But the paper does not hold that altitude.** Three places break it:

- §11.1's three-wave table (`PAPER.md:2388`) claims wave III for "this line of
  work" with the verification regime "replay + proof + active experiment" and
  the claim-carrying capacity "**true of everything (and refutable by
  reality)**". That is a result-about-world-models claim, in a related-work
  table, on n=1 self-built worlds. It also directly contradicts
  `PAPER.md:349` ("Neither layer certifies the manual against the world") and
  §5.6, whose whole point is that Lean guarantees *true relative to the
  manual*. You cannot claim a row that says "true of everything" and then
  spend §5 proving your instrument cannot deliver it.
- §10.5 (`PAPER.md:2308–2322`) lists two *substantive* findings —
  "reversibility of a mechanism mattered more than breadth of trajectory" and
  "two independently developed tracks" — which are not instrument claims, and
  which the body itself retracts (see §4 below).
- §6 (A3) reports a bill table with a 0.029 action ratio, 252/252 against the
  referee, and a "second level of the same game". That is a transfer result
  presented as one, in a paper whose §10.5 says transfer "is unevidenced here
  and is not claimed" (`PAPER.md:2324–2325`).

So: right claim, imperfectly earned. The fix is cheap for two of the three
(delete the wave-III row; rewrite §10.5), and structural for the third (decide
whether §6 is a result or an appendix — see MAJOR-4).

### 1.3 What I would actually call novel

Ranked by how hard it would be for a competent group to reproduce the *idea*:

1. **The executable anti-gaming register (§7.7).** Not the battery — the
   *audit*. One runnable exploit per metric, `succeeded` read from `evaluate()`
   rather than asserted, 34/38 landing, and a main table that moved 19→6→9 on
   demonstration. I have not seen a metric suite audited this way, and the
   finding that "the battery's validated metrics and its main-table metrics are
   very nearly disjoint sets" (`PAPER.md`:§7.2) is a real, transferable
   methodological result. **The paper undersells this badly** — it is item 4 of
   4 in §1.3 and gets one clause in §10.5.
2. **`CertificateGapError` — refusing to generate rather than narrowing the
   theorem (§4.4).** Small, but it is the right engineering answer to a real
   failure mode and the paper is right to call it the section's headline.
3. **The diffable true/false Lean pair (§5.6).** Novel as an *artefact*, not as
   a claim.
4. Everything else is a competent re-instantiation of known machinery.

---

## 2 · Is §11 fair to prior work? Line by line

§11 is the most carefully *sourced* related-work section I have reviewed — the
two-independent-sources rule, the "cited as what it is" discipline for
venue-less work, the refusal to cite Vasilevskii because nobody in the pass read
it (`PAPER.md`:§11.3), and §11.3 itself ("what the neighbours own that this
paper re-illustrates") are all genuinely creditable and rare. My complaints are
about *coverage*, not integrity.

### 2.1 Wave I — world models in weights

**Characterisation:** accurate. Ha & Schmidhuber split into two records with the
title trap documented, Dreamer lineage complete through DreamerV3, MuZero's
"predicts only what search needs" is a fair one-line summary, and the caveats on
`lecun2022path` (unrefereed) and `brooks2024sora` (company report, scope
statement excludes implementation) are exactly right.

**Comparison drawn:** *not* the honest one. The paragraph's move is: wave I puts
the model in weights, "with nowhere inside it to audit". True of Dreamer, MuZero
and Sora. **But the taxonomy silently deletes the structured/symbolic
world-model line**, which is neither latent vectors nor an executable program
checked by replay, and which is where this paper actually lives.

**Missing, and each is a direct hit:**

- **Tsividis, Pouncy, Xu, Tenenbaum, Gershman et al., "Human-level
  reinforcement learning through theory-based modeling, exploration, and
  planning" (2021)** — the EMPA line. This system builds an *explicit symbolic
  theory* of an Atari-like game in a program DSL, induces it from few
  observations, drives exploration by theory uncertainty, and plans with it.
  The word "theory" is in the title. **This is the single closest prior work to
  the entire Theoria framework and it is cited nowhere.** A referee will read
  the absence as either ignorance or avoidance, and neither is survivable.
  (See also Tsividis et al. 2017, "Human learning in Atari".)
- **Kansky et al., "Schema Networks: Zero-shot Transfer with a Generative
  Causal Model of Intuitive Physics" (ICML 2017).** Learns an object-level
  causal transition model and transfers it zero-shot to *perturbed variants of
  the same game*, evaluated by breaking a mechanism the model does not know
  about. That is §6.3's negative-control design, published in 2017.
- **Diuk, Cohen & Littman, "An object-oriented representation for efficient
  reinforcement learning" (ICML 2008)** — OO-MDPs. The manual's "vocabulary of
  objects and properties, rules that fire events" is an OO-MDP with a proof
  obligation bolted on.
- **Ellis et al., "DreamCoder" (PLDI 2021)** and behind it **Lake,
  Salakhutdinov & Tenenbaum (Science 2015)**. This is not optional: §2.1's
  constraint that "a concept's ticket of admission is that it shortens the
  manual" and §3.6's per-object compression accounting are *library learning by
  description length*. The paper uses the idea without citing anyone for it.
  That is worse than an uncited neighbour — it is an uncited borrowing.

**Wave III is empty because its occupants were excluded from the survey.** Fix
the survey and the table stops being defensible in its current form.

### 2.2 Wave II — the model in a program

**Characterisation:** accurate and admirably scrupulous about `zeng2026schema`
(project page, no venue, no harness, correct signing as Zeng et al., figures
flagged as self-reported and as `Theoria.md`'s summary rather than a
measurement). The bold "**No arm of this paper was run against WorldCoder,
Schema, or any other system**" is the right sentence and it is in the right
place.

**Missing — and this is where the paper's claimed differentiator gets
contested:**

- **Guan, Valmeekam, Sreedharan & Kambhampati, "Leveraging pre-trained large
  language models to construct and utilize world models for model-based task
  planning" (NeurIPS 2023).** An LLM writes a *PDDL domain model*; an external
  validator and a human-in-the-loop correct it; the corrected model is used for
  planning. §11.2's claimed delta over the LLM-theorem-proving literature is
  "*Here the LLM writes the specification itself*" (`PAPER.md`:§11.2). Guan et
  al. is precisely that, two years earlier, without the Lean layer.
- **Oswald et al., "Large language models as planning domain generators"
  (ICAPS 2024)**; **Silver et al., "Generalized planning in PDDL domains with
  pretrained LLMs" (AAAI 2024)**; **Liu et al., "LLM+P" (2023)**. Same family.
- **Wong, Grand, Lew, Tenenbaum, Andreas et al., "From word models to world
  models" (2023)** — LLM-to-probabilistic-program translation as world model.

Add these and the honest delta shrinks to: *the induced domain is additionally
compiled to Lean and its declared laws are discharged there.* That is still a
delta. It is a much smaller one than §11.2 currently implies, and the paper is
better off stating the smaller one itself.

### 2.3 Certificates and admissible heuristics in planning

**The strongest paragraph in §11, and I have almost no complaint.** Potential
heuristics via LP (`pommerening2015general`, `seipp2015potential`),
operator-counting (`pommerening2014lp`), lm-cut and PDBs, Eriksson's
unsolvability certificates and proof system, Hoffmann's merge-and-shrink for
unsolvability, Fast Downward "used rather than competed with", the pagoda
function traced to Berlekamp–Conway–Guy with the edition trap documented, and
Kiyomi & Matsui named as "the closest published analogue". The stated delta —
rules *induced* rather than given, and the certificate feeding a repair loop
rather than terminating an argument — is correct and correctly narrow, and the
two costs it then volunteers (a repair can invalidate an earlier-correct
certificate; a reachable/don't-know method admits no error measure) are the
right ones.

**One gap, and it is material because it sits on the paper's headline.**

- **Formally verified certificate checkers.** Eriksson & Helmert's later work
  on *verified* unsolvability certificate checking (Isabelle/HOL), and on the
  SAT side the DRAT/LRAT line with `cake_lpr` — machine-checkable unsolvability
  evidence validated by a formally verified checker — is the closest prior art
  to "an impossibility claim shipped with machine-checked evidence and an
  inspected axiom list". Also **Abdulaziz & Lammich's verified plan validator**.
  Without these, §4's empty-axiom-list result reads more novel than it is; with
  them, the honest delta is again "the domain was induced, not given". State it.

### 2.4 Program synthesis, version spaces, and ILP

**Characterisation:** accurate, and §11.2's self-demotion ("by that survey's
axes this work occupies an unremarkable corner — small hypothesis language,
exhaustive search, no recursion", `PAPER.md:2460`) is exactly the kind of
sentence that buys a referee's trust. Naming the object a *version space* and
calling Mitchell "an ancestor, not a contrast" is right. Conceding that
transition-rule mining from a ledger *is* action-model learning
(`yang2007arms`) is right.

**Problems:**

- **`cropper2021popper` (Popper, "Learning Programs by Learning from Failures")
  and `evans2018dilp` (∂ILP) are in `references.bib` and deliberately
  uncited** (`references.bib:44–48` names them among the five kept-but-uncited
  records). Popper is not an optional extra here. Learning-from-failures —
  hypothesise, test, derive a constraint from the failure, restrict the
  hypothesis space, repeat — is structurally the paper's own repair loop
  (refute → locate → probe → revise). Contribution 3 has a named modern
  ancestor sitting in the paper's own bibliography, unmentioned. This is the
  cheapest possible fix and the most embarrassing omission if left.
- **Action-model learning is under-cited at one record.** `yang2007arms` alone
  is thin. **LOCM (Cresswell, McCluskey & West)** learns domain models from
  plan traces *without* being given predicates — closer to this pipeline than
  ARMS is. Also **FAMA (Aineto, Jiménez, Onaindia)** and the **Arora et al.
  (2018) review of learning planning action models**.
- **Daikon (Ernst et al., "The Daikon system for dynamic detection of likely
  invariants", SCP 2007) is absent, and its absence is conspicuous.**
  `zero_space` differences consecutive observed states and takes a null space:
  it is a dynamic invariant detector. §11.2's own caveat — "what it returns is
  an empirical regularity over one trajectory, not a symbolically derived
  invariant" — is Daikon's *likely invariant* caveat, stated in 2001. The
  paragraph cites `ammons2002mining` for specification mining but not the
  canonical system for exactly this operation.
- **Houdini (Flanagan & Leino, FME 2001)** — generate candidate annotations,
  discard the ones the checker cannot prove. That is "engines propose, the
  checker adjudicates" for invariants, twenty-five years ago.

### 2.5 Petri invariants, model checking, IC3

**Characterisation:** careful and honest, including the explicit refusal to
describe `zero_space` as computing a P-invariant. The disclaimer "**Neither of
those two engines is exercised by any result in this paper**" for `ic3_pdr` and
`deadlock_carver` is correct practice. No complaint on accuracy.

**Missing:** **vacuity detection / sanity checking in formal verification**
(Beatty & Bryant 1994; Kupferman & Vardi, "Vacuity detection in temporal model
checking", 2003). §5's exhibit — the checker says GREEN and the property is
vacuous or false of the artefact it was supposed to be about — is the problem
that literature exists to name. Not citing it lets §5.6 read as a novel
observation when it is a re-instantiation. (§11.3 concedes the *general* point
under specification validity; the specific, closer literature is still absent.)

### 2.6 Proof-carrying code and certifying algorithms

Accurate; the delta (PCC certifies against a human-written policy, here the
premises are induced and fallible) is correct; Appel's accounting question is
turned on the paper's own §5.6, which is good practice. **Minor addition:**
translation validation (Pnueli et al. 1998) and CompCert (Leroy 2009) are the
natural modern anchors for "the artefact travels with its evidence".

### 2.7 Specification validity

Accurate. Dijkstra quoted with the correct EWD249 wording and the trap
documented; DeMillo/Fetzer/Boehm placed correctly; `ammons2002mining` is the
right anchor for "a mined specification is a hypothesis". The framing "§5.6's
error is best called a **mining error** rather than a proof error" is precise
and I endorse it. No complaint.

### 2.8 LLM + theorem proving

**Characterisation:** accurate, and the framing "feasibility basis rather than a
comparison target" is honest. The bold "**This paper runs no LLM-based
prover**" is the right disclosure.

**Problems:**

- The claimed differentiator — that prior work proves theorems *inside a given
  library* whereas here the LLM writes the specification — is contested by the
  LLM→PDDL literature of §2.2 above, which the paragraph does not know about.
- Autoformalisation is addressed well (`wu2022autoformalization`, with the
  correct distinction that its statements have an original to be checked
  against). Good.
- `hubert2026alphaproof` and `trinh2024alphageometry` are in the bib and
  uncited. Less serious than Popper — they are genuinely peripheral — but if
  space is found, AlphaProof is the natural one-clause citation for "an LLM
  proposing a formal statement a machine then checks is a buildable loop".

### 2.9 The literature that has no paragraph at all

Three whole areas are missing rather than mischaracterised. Two of them are
areas the paper *works in*.

**(A) ARC-AGI. Zero citations. This is the one that gets the paper desk-flagged.**
The pile cut, the development/sealed split, the 25 public games, the battery's
four development-pile games, the Schema comparison, INC-BA-001, the preflight,
the exam's pile guard — all of it is ARC-AGI-3. **Chollet, "On the Measure of
Intelligence" (arXiv:1911.01547, 2019)** does not appear in
`references.bib`, and neither does any ARC-AGI-2/3 technical report or any
ARC-AGI method paper. A workshop reader will ask, reasonably, "what benchmark is
this and who defined it?" and the bibliography has no answer. Also absent:
the LLM-on-ARC program-synthesis line (Greenblatt-style program sampling;
Wang et al. hypothesis search; Xu et al. on LLMs and ARC), which is the closest
existing family to "induce a program that explains the observations".

**(B) LLM agents with explicit memory or symbolic scaffolds. Zero citations.**
For a workshop on *LLM agents* this is disqualifying on its own. The playbook —
"entries at theorem level and at experience level", carried unchanged to a new
level (§6.1) — is a skill library. **Voyager (Wang et al. 2023)** grows an
explicit, reusable, code-valued skill library in Minecraft and transfers it;
**Reflexion**, **ReAct**, **Generative Agents (Park et al. 2023)**, **CLIN**,
and **ExpeL** are the surrounding family. The paper's §6 transfer claim needs to
say what it does that a skill library does not, and right now it cannot,
because it has not named one.

**(C) Benchmark contamination and evaluation integrity. Zero citations.**
The paper spends §7 (38 metrics, exploits, pre-registration seals), §8 (leakage
probes, calibrated marker, adversarial cheater), §10.1(f) (two contamination
incidents) and the whole pile-cut apparatus on evaluation integrity, and cites
nothing. Missing, all directly on point:
- **Construct validity / measurement:** Jacobs & Wallach, "Measurement and
  fairness" (FAccT 2021); Raji et al., "AI and the everything in the whole wide
  world benchmark" (2021); Blodgett et al. on benchmark construct validity.
  §7.7's finding that 34/38 metrics score at their best while possessing none of
  the capability they claim to measure **is a construct-validity result** and
  should be stated in that vocabulary.
- **Goodharting / specification gaming:** Manheim & Garrabrant, "Categorizing
  variants of Goodhart's law" (2018); Amodei et al., "Concrete problems in AI
  safety" (2016); Krakovna et al.'s specification-gaming catalogue.
- **Contamination:** Sainz et al. (2023); Golchin & Surdeanu, "Time travel in
  LLMs" (2023); Oren et al., "Proving test set contamination" (2023); Zhou et
  al., "Don't make your LLM an evaluation benchmark cheater" (2023). §10.1(f)'s
  INC-BA-001 (nine sealed games read by a search subagent) is a textbook
  instance and deserves to be placed in that literature rather than treated as
  a local incident.
- **Statistical power:** **Card et al., "With little power comes great
  responsibility" (EMNLP 2020)** is exactly §7.5's argument, published; also
  Bouthillier et al., "Accounting for variance in machine learning benchmarks"
  (MLSys 2021). §7.5's minimum-attainable-*p* = 0.125 argument is correct and
  well made, and citing Card et al. costs one line and makes it a contribution
  to an existing conversation instead of a local observation.
- **Pre-registration in ML:** Forde & Paganini (2019); Bell & Kampman (2021);
  Pineau et al., "Improving reproducibility in machine learning research"
  (JMLR 2021).

---

## 3 · Where a hostile domain expert says "this has been done"

Taking §1.3's four contributions (`PAPER.md:229–249`) in order, closest prior
work and the daylight remaining:

| # | contribution | closest prior work | daylight |
|---|---|---|---|
| 1 | cold-start pipeline, pixels → symbolic model → four forms → certify → plan; A0/A0′ contrast | **Tsividis et al. 2021 (EMPA)** for the whole shape; **Kansky et al. 2017** for object-level induced transition models; **LOCM / ARMS** for the mining; **Angluin 1987** for the A0′ finding | **Thin on the pipeline.** EMPA induces symbolic theories from pixels, explores by uncertainty, and plans. The daylight is the Lean layer and the four co-derived forms. The A0/A0′ finding has *no* daylight — §11.3 already concedes it is the reset assumption (`PAPER.md:2553`), and §3.3 concedes it is analytically entailed (`PAPER.md:541`) |
| 2 | machine-checked impossibility certificate crossing a data boundary | **Eriksson et al. 2017/2018** + **verified checkers (Isabelle; DRAT/cake_lpr)**; **Kiyomi & Matsui 2001** for the pagoda LP itself | **Narrow but real.** Induced-vs-given rules is a genuine difference and §11.2 states it. But the "data boundary" half is not a contribution at all — §4.2 concedes the two tracks are two agent sessions under one operator sharing `CLAUDE.md` (`PAPER.md:721`). Certifying-algorithms/PCC already owns "consumer re-checks rather than trusts" |
| 3 | exhibit of the replay-invisible failure mode + repair loop | **Popper (Cropper & Morel 2021)** for learning-from-failures; **Kupferman & Vardi 2003** for vacuity/sanity checking; **Chow 1978** for coverage ≠ conformance; **Ammons et al. 2002** for mined-spec-as-hypothesis | **Almost none on the claim; real on the artefact.** §11.3 already says the exhibit is "analytically guaranteed by the construction" and "not evidence about anything". The diffable Lean pair is the only novel object here, and it should be sold as an object |
| 4 | passive metrics battery + executable anti-gaming register | **Jacobs & Wallach 2021**, **Raji et al. 2021**, **Manheim & Garrabrant 2018** for the framing; **Card et al. 2020** for the power argument | **The widest daylight in the paper.** I know of no metric suite that ships a runnable exploit per metric and reports how many still land. This should be contribution 1, not 4 |

Two additional "done that" hits that do not map to a numbered contribution:

- **§6 (A3 transfer)** — carrying a learned symbolic model to perturbed
  variants of the same environment and observing that it silently fails on the
  perturbed mechanics is **Schema Networks (2017)**, evaluated the same way. The
  paper's genuinely new observation is the *layer* result — the free static
  layer passes and only replay, after acting, catches it. That is a good
  finding and it is buried under a bill table.
- **§2.1's compression criterion** — DreamCoder / MDL library learning.

---

## 4 · Is the central claim overstated?

§10.5, quoted in full (`PAPER.md:2310–2322`):

> That the pipeline runs end to end on self-built deterministic worlds; that on
> those worlds a manual can be perfect on replay and wrong about the world in a
> way that was predicted in advance and later measured; that reversibility of a
> mechanism mattered more than breadth of trajectory in the one controlled
> comparison run; that a machine-checked impossibility can be produced whose
> weights crossed a data boundary between two independently developed tracks and
> whose empty axiom list is a check that has been made to fail on purpose; that
> the refutation loop closed on a false theorem in six recorded beats; and that a
> passive metrics battery over existing trajectories, once its anti-gaming
> register was made executable rather than written, contradicted 17 of its own
> register entries by demonstration — 14 of them defence claims … — and found
> the exploration family's declared signature separating the specified gradient
> backwards.

Clause by clause against §§3–9:

1. **"pipeline runs end to end on self-built deterministic worlds"** — **Earned.**
   §3.1, §5.3, §6.2.
2. **"perfect on replay and wrong about the world in a way that was predicted in
   advance and later measured"** — **Earned, with a caveat the clause hides.**
   §1.1 itself corrects the record: R-05 named three *directions*, not three
   coordinate pairs, and the "three pairs R-05 named" gloss was written at M6
   after the score existed (`PAPER.md`:§1.1). The clause should say "predicted
   by direction". Also *n* = 3, which §7.4 says the abstract should carry.
3. **"reversibility … mattered more than breadth of trajectory in the one
   controlled comparison run"** — **Not earned. This clause contradicts §3.3
   twice.** §3.3 says "'Identical except' would be a false description and is
   not used here" (`PAPER.md:494`) — so calling it "the one controlled
   comparison" is precisely the description §3.3 refused. And §3.3 says the
   result is **analytically entailed**: "The outcome follows from the
   construction; nothing was learned that was not built in"
   (`PAPER.md:541–547`), concluding that the contrast "**demonstrates the
   mechanism rather than tests it**" (`PAPER.md:548`). A thing that demonstrates
   rather than tests does not belong in a paragraph titled "The one thing this
   paper claims". **BLOCKING.**
4. **"weights crossed a data boundary between two independently developed
   tracks"** — **Not earned as phrased.** §4.2: "A reader should not picture two
   teams. What crosses the boundary is therefore a *defence-in-depth* result,
   not an independent replication" (`PAPER.md:721`). "Two independently
   developed tracks" is the reading §4.2 exists to forbid. **BLOCKING.**
5. **"empty axiom list is a check that has been made to fail on purpose"** —
   **Earned.** §4.3's negative control is real and I credit it.
6. **"refutation loop closed on a false theorem in six recorded beats"** —
   **Earned as a process claim.** Note §10.3 concedes "one revision" for A2 is
   the paper's reading of the ledger, not a citable figure.
7. **Battery clause** — **Earned**, and it is the strongest clause in the
   paragraph.

**Overall verdict on §10.5:** two of seven clauses are retracted elsewhere in
the same paper. That is not an overstatement of the *field*-level kind — this
paper does not claim to have solved world modelling — but it is a
self-inconsistency, and self-inconsistency is fatal in a paper whose entire
rhetorical strategy is "check anything I say". A referee who verifies one claim
and finds it contradicted three sections earlier will stop verifying and start
discounting.

Additionally, §10.5's closing sentence — "**transfer** … is unevidenced here and
is not claimed" (`PAPER.md:2324–2325`) — is contradicted by §6, which is nine
pages of transfer results including a bill table (the "bill shape", also
disclaimed in the same sentence) and 252/252 against a referee. Either §6 is not
a result, in which case say so in §6, or §10.5's disclaimer is false.

---

## 5 · Is the framing honest about scale?

**Mostly yes, and conspicuously so.** §10.1(b) enumerates every world's
reachable-state count and says "**Scale is untested, and no result here should
be read as evidence about it**"; §3.7, §6.5(5), §8.4 and §9.3 each carry their
own scale limits; §10.1(e) volunteers that the paper "reports **no benchmark
result at all**". §7.5's power floor is stated three times. This is better than
the field norm by a wide margin, and I want to say so before listing the
sentences that leak.

**The sentences that let a reader believe more:**

1. **The title** (`PAPER.md:3`): "Certifying a world theory against something
   other than its own past". §2.3 says "**Neither layer certifies the manual
   against the world**" (`PAPER.md:349`). The title asserts the thing §2.3
   denies. The honest title is about *making the gap visible*, not about
   certifying across it.
2. **Abstract (6)** (`PAPER.md:100`): "A theory carried unchanged to a **second
   level of the same game** … wins … at **252/252 against the referee**." In an
   abstract that elsewhere discusses ARC development-pile games, upstream Schema
   trajectories and a live API run, "the same game" will be read as an ARC game.
   It is a self-built 9×9 world (`cold-start-a3/a3world/a3_world.py`). The words
   "game", "level" and "referee" all import benchmark connotations the object
   does not have. §6 is scrupulous; the abstract is not.
3. **Abstract (3)** (`PAPER.md:77`): "crosses a JSON data boundary into a
   **second track developed alongside it**". Same problem as §10.5 clause 4;
   §4.2's correction never reaches the abstract.
4. **§11.1 wave-III row** (`PAPER.md:2388`): "**true of everything (and
   refutable by reality)** … this line of work". On four self-built worlds of
   55–63 reachable states, with `decide` enumerating the whole space. This is
   the single most overreaching sentence in the paper and it is in the
   related-work section, which is where a referee looks for calibration.
5. **Keywords** (`PAPER.md:128`): "world models · **program synthesis** ·
   unsolvability certificates · interactive theorem proving · **agent
   evaluation**". The paper runs no LLM agent (§10.3: the theorize step is done
   by hand) and measures no synthesis step. Two of five keywords advertise
   capabilities the paper explicitly disclaims.
6. **"three offline acceptances"** (title block, §2.5). "Acceptance" reads as
   external acceptance testing. These are the project's own internal
   milestones, self-defined and self-graded. Minor, but it compounds.
7. **Abstract "Eight results"** (`sections/00_abstract.md:61`). Counting the
   preflight (which spent nothing and establishes a property of the apparatus,
   §9.4's own words) and the exam (three of four papers never sat, §8.2) as
   "results" inflates the count. §10.5 claims six things; the abstract advertises
   eight.

To be explicit about what is *not* a problem: I looked for, and did not find,
any sentence claiming an ARC result, any comparison against Schema or
WorldCoder presented as a measurement, any suppression of the *n* = 3 held-out
denominator, or any laundering of the hand-written theorize step. The abstract's
penultimate paragraph ("We claim none of the framework's comparative results …
**None is across the framework's own arms**") is exemplary and should be kept
verbatim.

---

## 6 · Findings, graded

### BLOCKING

- **B1. No ARC-AGI citation anywhere.** `references.bib` contains no Chollet
  2019, no ARC-AGI-2/3 report, and no ARC method paper, yet §7, §8, §9, §10.1(f)
  and the entire pile-cut apparatus are about ARC-AGI-3.
  (`references.bib`, whole file; `PAPER.md:1286` ff., `PAPER.md:1897` ff.)
- **B2. Theory-based RL and symbolic/object-centric world models are absent,
  and their absence is what makes §11.1's wave-III row possible.** Add
  Tsividis et al. 2021 (EMPA), Kansky et al. 2017 (Schema Networks),
  Diuk et al. 2008 (OO-MDP), Ellis et al. 2021 (DreamCoder), Lake et al. 2015.
  Then either delete the wave-III row or rewrite the table so it does not claim
  an unoccupied category. (`PAPER.md:2341–2388`)
- **B3. §11.1's wave-III row contradicts §2.3 and §5.6.** "True of everything"
  vs "Neither layer certifies the manual against the world"
  (`PAPER.md:2388` vs `PAPER.md:349`).
- **B4. §10.5 clause 3 contradicts §3.3.** "the one controlled comparison run"
  vs "'Identical except' would be a false description" and "demonstrates the
  mechanism rather than tests it" (`PAPER.md:2313–2314` vs
  `PAPER.md:494`, `541–548`). Delete the clause or restate it as a design
  lesson.
- **B5. §10.5 clause 4 contradicts §4.2.** "two independently developed tracks"
  vs "A reader should not picture two teams … not an independent replication"
  (`PAPER.md:2315` vs `PAPER.md:721`). Same wording leaks into the abstract
  (`PAPER.md:77`) and §1.3 item 2 (`PAPER.md:234–240`).
- **B6. No LLM-agent literature at all**, at a workshop on LLM agents. Voyager,
  Reflexion, ReAct, Generative Agents at minimum; the playbook needs to be
  positioned against skill libraries. (`PAPER.md:2329` ff.)

### MAJOR

- **M1. Popper and ∂ILP sit in the paper's own bibliography, uncited by
  policy** (`references.bib:44–48`). Popper's learning-from-failures is the
  named modern ancestor of contribution 3's repair loop. Cite it, and say what
  the Lean re-discharge adds. Zero research cost.
- **M2. The LLM→PDDL literature is missing and it contests §11.2's stated
  delta.** Guan et al. 2023, Oswald et al. 2024, Silver et al. 2024,
  Liu et al. 2023. The claim "*Here the LLM writes the specification itself*"
  (`PAPER.md`:§11.2, LLM+theorem-proving paragraph) needs to be narrowed to
  "…and the specification is discharged in an ITP, not validated by VAL".
- **M3. Daikon and Houdini are missing from the invariant paragraph.**
  `zero_space` is a dynamic likely-invariant detector; Daikon named the caveat
  §11.2 restates. Houdini is "propose candidates, keep what the checker proves".
  (`PAPER.md`:§11.2, Petri paragraph)
- **M4. §6 is a transfer result that §10.5 says is not claimed.** Resolve.
  Either promote A3 to a contribution with the Schema-Networks comparison made
  explicitly, or demote §6 to an appendix with a one-line pointer.
  (`PAPER.md:1086` ff. vs `PAPER.md:2324`)
- **M5. The benchmark-contamination and construct-validity literatures are
  absent**, and §7.7's headline finding is a construct-validity result stated
  without the vocabulary. Jacobs & Wallach 2021; Raji et al. 2021; Manheim &
  Garrabrant 2018; Sainz et al. 2023; Card et al. 2020 for §7.5's power
  argument. (`PAPER.md:1286` ff.)
- **M6. Verified certificate checkers are missing from §11.2's certificates
  paragraph** (Eriksson & Helmert's Isabelle work; DRAT/LRAT + cake_lpr;
  Abdulaziz & Lammich). Without them §4 reads more novel than it is.
- **M7. Vacuity/sanity-checking literature missing from §5.6's neighbourhood**
  (Kupferman & Vardi 2003; Beatty & Bryant 1994).
- **M8. The paper's best contribution is buried.** The executable anti-gaming
  register (§7.7) is item 4 of 4 in §1.3 and one clause in §10.5. For a workshop
  audience it is the most transferable thing here. Promote it.
- **M9. The compression concept-admission criterion (§2.1, §3.6) is used
  without attribution.** MDL library learning has owners. (`PAPER.md:268` ff.,
  §3.6)

### MINOR

- **m1. Title overclaims relative to §2.3** (`PAPER.md:3` vs `349`).
- **m2. Abstract (6)'s "second level of the same game" reads as an ARC game**
  (`PAPER.md:100`). Say "self-built world" in the abstract as §6 does.
- **m3. Two of five keywords advertise disclaimed capabilities**
  (`PAPER.md:128`): "program synthesis" and "agent evaluation" against §10.3's
  "the theorize step is not a measured LLM step".
- **m4. "Eight results" (abstract) vs six claims (§10.5).** Reconcile the
  counts; the preflight and the exam are apparatus, not results, by the paper's
  own §9.4 and §8.4.
- **m5. Action-model learning is a one-citation paragraph.** Add LOCM, FAMA,
  and the Arora et al. survey (`PAPER.md`:§11.2).
- **m6. §11.3 concedes only the two cheapest borrowings** (version space,
  specification validity). After the additions above it will need at least two
  more rows — Popper for the repair loop, Schema Networks for §6.
- **m7. "three offline acceptances"** is internal milestone vocabulary that
  reads as external validation. Consider "three offline milestones".
- **m8. AlphaProof / AlphaGeometry are in the bib and uncited**; one clause in
  the LLM+ITP paragraph would use them.
- **m9. Length.** At ~23 700 words this is ~5× a workshop budget, as the draft
  status note concedes. My cut, offered because a referee should say where:
  §7 and §8 are the sections that will not survive the cut intact, and §7.7 is
  the part of §7 that must.

---

## 7 · What I would tell the authors in one paragraph

The instrument-and-artefact framing is right and you should defend it harder
than you currently do — by deleting the two clauses in §10.5 that your own body
retracts, by deleting the wave-III row that your own §2.3 contradicts, and by
promoting the executable anti-gaming register from fourth contribution to first.
Then spend a day on the bibliography. Four literatures that a domain referee
reaches for immediately — ARC-AGI, theory-based/object-centric world models,
LLM agents with skill libraries, and evaluation integrity — are absent entirely,
and one work that is arguably your nearest neighbour in the whole field
(Tsividis et al. 2021) is uncited. Your related-work section currently
demonstrates that you verified every citation you made; it does not yet
demonstrate that you know which citations you owe. Fix the second and this is a
good workshop paper, because the underlying discipline — every number carrying
its artefact path, source reports kept unedited including where they are wrong,
guards tested by being made to fire — is genuinely better than the norm and
deserves to be seen.
