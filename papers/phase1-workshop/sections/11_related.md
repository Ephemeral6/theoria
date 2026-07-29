## 11 · Related work

Every citation in this section was cross-verified against two independent sources
before it was written, and a record that could not be confirmed twice was dropped
rather than hedged. The queries, the source URLs, and what each source confirmed
are in `papers/phase1-workshop/runs/20260728T102014Z-P7/search-traces/`, one file
per line below, together with an adversarial re-check over a sample of the set.
The bibliography is `papers/phase1-workshop/references.bib`. Where a work has no
citable venue — and several here do not — it is cited as what it is.

### 11.1 Three waves, and the thing they kept upgrading

`Theoria.md` §3.1 reads the world-model literature as three waves and argues that
what each wave actually upgraded was neither the architecture nor the score but the
**verification regime** — 检验制度, the rule by which a model is admitted as
correct.

The first wave put the model in weights. Ha and Schmidhuber brought "world model"
back onto the agenda by learning transitions in a latent space and training a
controller inside its own dream [`ha2018world`; the refereed companion, under a
different title, is `ha2018recurrent`]; PlaNet and the Dreamer line made planning
in imagination a mainstream method [`hafner2019planet`, `hafner2020dreamer`,
`hafner2021dreamerv2`, `hafner2025dreamerv3`]; MuZero was given no rules and
searched inside a self-learned implicit model, deliberately predicting only what
search needs rather than what the world is [`schrittwieser2020muzero`]; and the
recent generative branch — playable generated environments [`bruce2024genie`],
joint-embedding prediction [`assran2023ijepa`, `lecun2022path`], and the argument
that video generators are world simulators [`brooks2024sora`] — made frame-by-frame
prediction increasingly convincing. `Theoria.md` §3.1 grants the point in its
strongest form: "若预测本身就是理解,第一波已经赢了" (if prediction itself were
understanding, the first wave has already won). What these predictions never pass
through is a checkable concept; the model is weights, with nowhere inside it to
audit. Two of those citations carry a caveat that belongs in the sentence rather
than in a footnote: `lecun2022path` is an unrefereed position paper, and
`brooks2024sora` is a company technical report whose own scope statement excludes
implementation details, so its claims are cited as claims.

The second wave put the model in a program. WorldCoder has an agent learn an
environment model by writing Python and repairing it as it plays, requiring the
program to stay consistent with every interaction recorded so far
[`tang2024worldcoder`]; RAP uses the language model's own forward pass as the world
model for planning [`hao2023rap`]. Schema pushed the wave to its ceiling on
ARC-AGI-3: an editable, executable world model checked by replaying the entire
recorded history [`zeng2026schema`]. Three things about that citation are worth
stating plainly. It is a project page, not a paper — no venue, no arXiv id, no DOI,
and no released harness code, which is why no reproduction of it exists here or
anywhere (`baseline-arms/SCHEMA_LOCATE.md`). Its canonical signing is **Zeng et
al.**, not the "Feng et al." that `Theoria.md` and several of this project's work
orders use; Haiwen Feng is the last author. And the 98.98 % and +56pp figures that
`Theoria.md` §3.1 quotes are self-reported on the public set and are `Theoria.md`'s
summary of prior work, not a measurement of ours. **No arm of this paper was run
against WorldCoder, Schema, or any other system.** This paper reports no
comparison, and the three-arm comparison `Theoria.md` plans is Phase 3 work that
has not happened.

| wave | carrier | verification regime | claims it can carry | representatives |
|---|---|---|---|---|
| I | latent vectors | prediction error / return | no checkable proposition | Dreamer / MuZero / Genie |
| II | executable program | replay reconciliation | true of everything already experienced | WorldCoder / Schema |
| III | **formal theory** | replay + proof + active experiment | **true of everything (and refutable by reality)** | this line of work |

— reproduced from `Theoria.md` §3.1.

The regime decides what the model may carry. A model checkable only by prediction
error carries no proposition at all. A replayable model carries "true of everything
already experienced". "True of everything" — conservation laws, unsolvability — is
what neither carries, and §1.3 of `Theoria.md` gives the structural reason: replay
catches a rule written *wrong*, never a rule left *out*.

### 11.2 Where this sits, one neighbour at a time

**Certificates and admissible heuristics in planning.** This is the literature
anchor for 证书与启发同源 — certificate and heuristic are the same object. An
admissible *h(s)* is a lower bound, and an unsolvability certificate is its limit
case *h(s₀) = ∞*. The identity is not ours: potential heuristics are admissible
lower bounds obtained from a linear program [`pommerening2015general`,
`seipp2015potential`], the operator-counting framework recovers several heuristic
families as LPs over constraints every plan's operator counts must satisfy
[`pommerening2014lp`], and landmark, critical-path and abstraction heuristics are
all lower-bound constructions differing mainly in what they may see
[`helmert2009lmcut`, `culberson1998pdb`, `edelkamp2001pdb`].
`engine-rig/engines/lp_potential` is that identity realised as one solver, pushed
to the degenerate end of the bound — it asks only whether the LP admits a
potential separating the initial configuration from the goal. It is **sound but
incomplete**: it never certifies a solvable configuration, and some genuinely
unsolvable ones admit no *linear* certificate (`engine-rig/DECISIONS.md` D-014).

The object it computes has a name and a provenance: a **pagoda function**, an
assignment of values to positions that cannot increase under any legal jump,
introduced to prove peg-solitaire configurations unreachable
[`berlekamp2004winningways`]. Formulating that argument as the linear relaxation
of an integer program is also prior work [`kiyomi2001pegsolitaire`], and it is the
closest published analogue of what this engine does. The discipline of shipping
the evidence rather than the verdict is prior work too: unsolvability claims used
to be taken on trust while plans were independently validated, which is the gap
certificate formats and then a proof system for unsolvable tasks were built to
close [`eriksson2017certificates`, `eriksson2018proofsystem`]; and collapsing a
heuristic to the two-valued reachable/unreachable question when unsolvability is
the goal is a known move [`hoffmann2014unsolvability`]. Fast Downward, which
`engine-rig/engines/fd_adapter` wraps behind a `solve(domain, problem)` interface,
is used rather than competed with [`helmert2006fastdownward`], so the search half
of the pipeline is a citation and not a contribution.

The delta is twofold and narrow. **That literature certifies tasks whose rules are
given; here the rules were *induced* from an observed transition ledger**, so the
LP's constraints are mined by `engine-rig/engines/zero_space` and
`engine-rig/engines/cegis_miner` rather than read off a domain description, and
the soundness argument transfers only as far as the mining does — a certificate is
a theorem about the induced rules and is only as good as they are. Second, **the
certificate participates in a repair loop rather than terminating the argument**:
where an infeasibility result closes an instance, a failed derivation here is a
signal that the induced rules are wrong, and that is what the loop consumes
(`cold-start-a2/artifacts/loop_ledger.json`). Two consequences follow that are
worth stating because they are costs rather than features. A repair to the manual
can invalidate a certificate that was correct with respect to the earlier rules.
And a method that answers only "unreachable or don't know" cannot be scored by how
close its estimates are, which is why §5 reports what it decided and what it left
open rather than an error measure.

**Program synthesis, version spaces, and ILP.** `engine-rig/engines/cegis_miner`
runs the counterexample-guided loop of sketching and syntax-guided synthesis
[`solarlezama2006sketching`, `solarlezama2008thesis`, `alur2013sygus`] with the
observed transition ledger standing in for the verifier, so a counterexample is a
recorded transition the candidate rule mispredicts rather than a solver's witness
against a formal specification. The return value is the frontier of *all*
hypotheses consistent with the ledger rather than one point guess, and the honest
name for that object is a **version space** [`mitchell1982generalization`,
`lau2003vsa`] — an ancestor, not a contrast. What is added is a use for the
frontier's width: it is handed to `engine-rig/engines/probe_frontier` to design an
experiment that splits it. Mined rules land in the manual's own DSL, which is the
ILP shape [`muggleton1991ilp`, `muggleton1994ilptheory`, `cropper2022ilp30`], and
by that survey's axes this work occupies an unremarkable corner — small hypothesis
language, exhaustive search, no recursion. The step that differs is downstream of
learning: a mined rule is an *obligation*, not a conclusion, and is re-discharged
as a machine-checked Lean proof before being admitted. It should also be said
plainly that mining transition rules from an observed ledger is the action-model
learning problem [`yang2007arms`], not a new one; what differs is returning the
whole consistent set rather than one maximally-weighted model, and compiling the
induced model to a PDDL domain *and* to Lean, so the learned preconditions are also
the object of a proof.

**Petri invariants and model checking / IC3.** The kinship is with place
invariants — linear quantities preserved by every transition, computed as the left
null space of a net's incidence matrix [`petri1962kommunikation`,
`murata1989petri`, `colom1991convex`] — but the mechanism here is not the Petri one
and should not be described as if it were. `engine-rig/engines/zero_space` encodes
each `(cell, colour)` as an indicator, differences consecutive observed states, and
takes the null space of the *difference* matrix. A P-invariant is derived
symbolically from the **rules**; `zero_space` reads **data**, so what it returns is
an empirical regularity over one trajectory, not a symbolically derived invariant.
`engine-rig/engines/ic3_pdr` supplies inductive invariants of shapes the LP cannot
reach, in the lineage of IC3 and property-directed reachability
[`bradley2011ic3`, `een2011pdr`]; `engine-rig/engines/deadlock_carver` supplies
conditional mini unsolvability theorems, in the lineage of siphon-based deadlock
prevention [`ezpeleta1995deadlock`]. **Neither of those two engines is exercised by
any result in this paper.** The older model-checking literature
[`clarke1981skeletons`, `queille1982cesar`, `mcmillan2003interpolation`] assumes
the model is given and asks whether a property holds; here neither is in hand at
the start, so checking is one stage of a pipeline whose earlier stages can also be
wrong. All of these outputs are consumed as *sources of theorem obligations* rather
than as verdicts — the obligation is re-discharged in Lean, which is where "holds
on the trajectory" is upgraded to "holds under the manual's own `step`".

**Proof-carrying code and certifying algorithms** [`necula1997pcc`,
`necula1996safekernel`, `appel2001fpcc`] are the ancestry of the name. An artefact
travels with the evidence for its own correctness and the consumer re-checks rather
than trusts, which is exactly the boundary discipline of §4
(`engine-rig/interop/certificates/pagoda_5_11011_to_00010.json`). The engines are
certifying in the sense of the survey literature [`mcconnell2011certifying`,
`blum1995checkers`], and the instance-level framing is adopted for the same reason
it was invented there: no claim is made to have verified any engine. What differs
is that proof-carrying code certifies a program against a policy a human wrote,
whereas the property certified here concerns a world model whose rules were
*induced*, so the certificate's own premises are fallible. Appel's accounting
question — a certificate is worth only what its axioms are worth — is the one §5.6
answers badly: shrinking the checker does not shrink the exposure, because the
exposure lives in the premises.

**Specification validity — the oldest caveat in the field, and the one §5.6
dramatises.** That a machine-checked proof is only as good as the specification it
is about is not news to formal methods. Dijkstra's own sentence is "Program testing
can be used to show the presence of bugs, but never to show their absence!"
[`dijkstra1970notes`] — which is why the manual is proved rather than merely
replayed; the symmetric half, that a proof shows the absence of bugs only
*relative to a specification*, is what §5.6 walks into. The
validation-versus-verification distinction and the arguments around it long predate
this work [`boehm1984vandv`, `demillo1979social`, `fetzer1988veryidea`], and §5.6
does not claim the point as novel. What the exhibit contributes is a concrete pair
of artefacts in which the specification was *induced from data* rather than written
by hand — the setting named by the specification-mining literature
[`ammons2002mining`], which said in 2002 that a mined specification is a hypothesis
and can be wrong. That is why §5.6's error is best called a **mining error** rather
than a proof error, and the one thing added is downstream: here a mined
specification is not a lint oracle but the premise set of a Lean theorem, so a bad
mine is laundered into a formally proved false statement, and the refutation feeds
a mechanical repair loop rather than a human rewrite
(`cold-start-a2/artifacts/loop_ledger.json`).

**LLM + theorem proving** [`polu2020generative`, `han2022pact`,
`lample2022hypertree`, `jiang2023draft`, `yang2023leandojo`] is the feasibility
basis rather than a comparison target: it is why an LLM proposing a formal
statement that a machine then checks is a buildable loop at all, and it supplies
the checker this work compiles into [`demoura2015lean`, `demoura2021lean4`]. One
difference governs the rest. That work proves theorems inside a *given* formal
library [`mathlib2020`] or a curated problem set, where the statement is supplied
and correct by construction and the difficulty is the proof. Here the LLM writes
the specification itself — the manual is a formal description of an unknown
interactive world, induced from a transition ledger — so a proof can succeed while
the theorem it establishes is false *of the world*, which is what §5.6 exhibits.
Autoformalisation [`wu2022autoformalization`] is the nearest neighbour, since it
also produces statements and not only proofs, but its statements translate a
natural-language original that already denotes something definite; the manual has
no original to be checked against, only the world. **This paper runs no LLM-based
prover.** Every Lean obligation reported here is discharged by ordinary Lean
checking, and no result depends on neural proof search.

### 11.3 What the neighbours own that this paper re-illustrates

An adversarial review of an earlier draft (`papers/phase1-workshop/REVIEW.md`,
issue 14) found that several of this paper's framings restate results the
literature already owns, and that the related-work section did not say so. Three of
those are answered above — the version space, the specification-validity problem,
and the mined-specification setting. Two are recorded here rather than argued away.

**"Reversibility beats coverage" is close to the reset assumption in active
automata learning.** L\* and the membership/equivalence-query line assume the
learner can reset to a known state, precisely because a transition that cannot be
re-witnessed cannot be pinned down [`angluin1987lstar`]; §3's irreversible latch
removes the reset for the button mechanism and A0′'s toggle restores it, so the
finding there is the standard reason that assumption is made, arrived at from the
other direction. The neighbouring claim — that replay coverage does not certify
the model — is the FSM conformance-testing problem, whose W-method
[`chow1978wmethod`] exists because covering every observed transition is not the
same as distinguishing every state. Vasilevskii's independent line on the same
problem is named in `papers/phase1-workshop/REVIEW.md` and is **not** cited here:
it was not verified to this section's standard, and attaching a plausible-looking
record to a source nobody in this pass read is the same failure as inventing one.

**"Prediction perfect, understanding broken" is this framework's own premise, not a
finding.** §5's procedure is to take a certified manual, delete a rule that never
fires in the retained history, and observe that replay over that history does not
notice — which is analytically guaranteed by the construction. The exhibit has
value as a teaching object and as a test of the instrument. It is not evidence
about anything, and the abstract should not read as though it were.
