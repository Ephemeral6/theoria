## 8 · Related work

### 8.1 Three waves, and the thing they kept upgrading

`Theoria.md` §3.1 reads the world-model literature as three waves and argues that
what each wave actually upgraded was neither the architecture nor the score but
the **verification regime** — 检验制度, the rule by which a model is admitted as
correct.

The first wave put the model in weights. Ha & Schmidhuber [bib: TODO] brought
"world model" back onto the agenda by learning transitions in a latent space and
training the agent inside its own dream; PlaNet/Dreamer [bib: TODO] made planning
in imagination a mainstream method; MuZero [bib: TODO] was given no rules and
searched inside a self-learned implicit model; the recent generative branch —
Genie [bib: TODO], the video-models-as-world-simulators argument, JEPA's
predictive route [bib: TODO] — made frame-by-frame prediction increasingly
convincing. `Theoria.md` §3.1 grants the point in its strongest form: "若预测本身
就是理解，第一波已经赢了" (if prediction itself were understanding, the first wave
has already won). What these predictions never pass through is a checkable
concept; the model is weights, with nowhere inside it to audit.

The second wave put the model in a program. WorldCoder [bib: TODO] has an agent
learn an environment model by writing Python and editing it as it plays; RAP
[bib: TODO] uses the LLM itself as the world model for planning. Schema
[bib: TODO] pushed this to its ceiling on ARC-AGI-3: an editable, executable
world model checked by replaying the entire recorded history. `Theoria.md` §3.1
summarises the reported result as 98.98% and +56pp attributable to process rather
than to weights [bib: TODO]. Those two numbers are `Theoria.md`'s own summary of
prior work, not a measurement of ours. **No arm of this paper was run against
WorldCoder, Schema, or any other system.** This paper reports no comparison, and
the three-arm comparison `Theoria.md` plans is Phase 3 work that has not happened.

| wave | carrier | verification regime | claims it can carry | representatives |
|---|---|---|---|---|
| I | latent vectors | prediction error / return | no checkable proposition | Dreamer / MuZero / Genie [bib: TODO] |
| II | executable program | replay reconciliation | true of everything already experienced | WorldCoder / Schema [bib: TODO] |
| III | **formal theory** | replay + proof + active experiment | **true of everything (and refutable by reality)** | this line of work |

— reproduced from `Theoria.md` §3.1.

The regime decides what the model may carry. A model checkable only by prediction
error carries no proposition at all. A replayable model carries "true of
everything already experienced". "True of everything" — conservation laws,
unsolvability — is what neither carries, and §1.3 of `Theoria.md` gives the
structural reason: replay catches a rule written *wrong*, never a rule left
*out*.

### 8.2 Where this sits, one neighbour at a time

**Unsolvability certificates and admissible heuristics in planning.** Potential
heuristics, operator-counting, LM-cut and pattern databases [bib: TODO] are the
literature anchor for 证书与启发同源 — certificate and heuristic are the same
object, an admissible *h(s)* being a lower bound and an unsolvability certificate
its limit case *h(s₀)=∞*. `engine-rig/engines/lp_potential` is that identity as
one solver. The delta is twofold: that literature certifies games whose rules are
given, where we certify rules that were *induced* from a transition ledger; and
the certificate participates in a repair loop rather than terminating the
argument (`cold-start-a2/artifacts/loop_ledger.json`).

**Program synthesis: CEGIS and ILP** [bib: TODO]. `engine-rig/engines/cegis_miner`
runs the counterexample-guided loop for rule mining with the transition ledger as
verifier; what differs is the return value — the frontier of all consistent
hypotheses, kept as probe material, rather than one point guess.

**Petri invariants and model checking / IC3** [bib: TODO]. Linear conservation laws
are computed symbolically from the rules as Petri invariants
(`engine-rig/engines/zero_space`), and `engine-rig/engines/ic3_pdr` supplies
inductive invariants of shapes the LP cannot reach. We consume these as *sources
of theorem obligations*, not as the final verdict: the proof obligation is
re-discharged in Lean.

**Proof-carrying code** [bib: TODO] is the ancestry of the name. An artefact
travels with the evidence for its own correctness, and the consumer re-checks
rather than trusts — which is exactly the boundary discipline of §4
(`engine-rig/interop/certificates/pagoda_5_11011_to_00010.json`).

**LLM + theorem proving** [bib: TODO] is the feasibility basis rather than a
comparison target: it is why an LLM proposing a formal statement that a machine
then checks is a buildable loop at all.

> **Draft note.** This repository contains no bibliography file, and none was
> built for this draft. Every `[bib: TODO]` above is an unfilled obligation: the
> systems are named exactly as `Theoria.md` names them, with no year, venue, or
> identifier invented here. Each marker must become a real citation before
> submission.
