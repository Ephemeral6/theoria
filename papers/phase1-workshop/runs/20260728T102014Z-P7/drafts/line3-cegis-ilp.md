# Line 3 — CEGIS, version spaces, ILP, action-model learning

Eleven confirmed records for the "Program synthesis: CEGIS and ILP" anchor of
`papers/phase1-workshop/sections/11_related.md` §8.2. Verification trace, with
two independent sources per record and the exact URLs, is at
`papers/phase1-workshop/runs/20260728T102014Z-P7/search-traces/line3-cegis-ilp.md`.

Every "our delta" sentence below states a difference in construction, not a
measured advantage. **No arm of this paper was run against any of these
systems**, and none of them was reimplemented for comparison. The relevant
artefact throughout is `engine-rig/engines/cegis_miner`.

A minimal citation set for one paragraph is C1, C3, C4, C6 and C11; C2, C5, C7,
C8, C9 and C10 are available if the paragraph is allowed to run longer.

---

## C1 · `solarlezama2006sketching`

> Armando Solar-Lezama, Liviu Tancau, Rastislav Bodík, Sanjit A. Seshia and
> Vijay A. Saraswat. "Combinatorial Sketching for Finite Programs." In
> *Proceedings of the 12th International Conference on Architectural Support for
> Programming Languages and Operating Systems (ASPLOS XII)*, pages 404–415, ACM,
> 2006. DOI 10.1145/1168857.1168907.

**What it did.** Introduced sketching — the programmer writes a partial program
with holes and a separate specification, and a SAT-based synthesiser fills the
holes, alternating between a candidate solution and a counterexample that
refutes it.

**Our delta.** `cegis_miner` runs the same candidate–counterexample alternation,
but the verifier is the observed transition ledger rather than a solver checking
a candidate against a formal specification, so a counterexample is a recorded
transition the candidate rule mispredicts.

---

## C2 · `solarlezama2008thesis`

> Armando Solar-Lezama. *Program Synthesis by Sketching.* PhD thesis, University
> of California, Berkeley, 2008. Technical report UCB/EECS-2008-176.

**What it did.** Gave the full account of the sketching approach and named the
counterexample-guided inductive synthesis loop that the rest of the literature
now cites as CEGIS.

**Our delta.** We take the loop and leave the specification behind: there is no
reference implementation to check against, only a ledger of what was observed,
which is why the loop terminates on a set of survivors rather than on a proof of
equivalence.

---

## C3 · `alur2013sygus`

> Rajeev Alur, Rastislav Bodík, Garvit Juniwal, Milo M. K. Martin, Mukund
> Raghothaman, Sanjit A. Seshia, Rishabh Singh, Armando Solar-Lezama, Emina
> Torlak and Abhishek Udupa. "Syntax-Guided Synthesis." In *2013 Formal Methods
> in Computer-Aided Design (FMCAD)*, pages 1–8, IEEE, 2013.
> DOI 10.1109/FMCAD.2013.6679385.

**What it did.** Standardised the synthesis problem as a logical specification
plus a syntactic restriction on the candidate space, and set out the
counterexample-guided solver architecture that most SyGuS solvers share.

**Our delta.** Our candidate space is likewise syntactically restricted — it is
the manual's rule grammar rather than a user-supplied one — but the logical
specification half of the SyGuS pair is absent, and the ledger stands in for it.

---

## C4 · `mitchell1982generalization`

> Tom M. Mitchell. "Generalization as Search." *Artificial Intelligence*
> 18(2):203–226, 1982. DOI 10.1016/0004-3702(82)90040-6.

**What it did.** Framed concept learning as search through a hypothesis space
and introduced the version space — the set of *all* hypotheses consistent with
the examples seen so far, maintained rather than collapsed to a single guess.

**Our delta.** The frontier `cegis_miner` returns is a version space by another
name, and we cite this as its ancestor rather than as a contrast; what we add is
a use for the frontier's width, which is fed to `probe_frontier` to design an
experiment that splits it.

---

## C5 · `lau2003vsa`

> Tessa Lau, Steven A. Wolfman, Pedro Domingos and Daniel S. Weld. "Programming
> by Demonstration Using Version Space Algebra." *Machine Learning*
> 53(1–2):111–156, 2003. DOI 10.1023/A:1025671410623.

**What it did.** Built version spaces compositionally, so that the set of all
hypotheses consistent with a demonstration could be maintained efficiently for
realistic program spaces rather than for toy concept languages.

**Our delta.** We maintain a frontier over transition rules rather than over
user-demonstrated programs, and we do not have their composition algebra — the
frontier is enumerated within a small grammar, which is adequate at the scale
reported here and would not be at theirs.

---

## C6 · `muggleton1991ilp`

> Stephen Muggleton. "Inductive Logic Programming." *New Generation Computing*
> 8(4):295–318, 1991. DOI 10.1007/BF03037089.

**What it did.** Named and delimited inductive logic programming: inducing
logic-program hypotheses from examples and background knowledge, with the
hypothesis in the same declarative language as the knowledge it extends.

**Our delta.** Mined rules land in the manual's DSL, which is the same language
the rest of the theory is written in, so the ILP shape holds; what differs is
what happens next — the rule is an obligation, not a conclusion, and is
re-discharged as a machine-checked Lean proof before being admitted.

---

## C7 · `muggleton1994ilptheory`

> Stephen Muggleton and Luc De Raedt. "Inductive Logic Programming: Theory and
> Methods." *The Journal of Logic Programming* 19–20:629–679, 1994.
> DOI 10.1016/0743-1066(94)90035-3.

**What it did.** Set out the field's theory — the generality orders, the
inverse-resolution and refinement operators, and the distinction between
learning from entailment and from interpretations.

**Our delta.** Our search is far cruder than any operator in that survey; the
generality order we use is inherited from the grammar rather than derived, and
we cite this to place the mining step, not to claim a method.

---

## C8 · `cropper2022ilp30`

> Andrew Cropper and Sebastijan Dumančić. "Inductive Logic Programming At 30: A
> New Introduction." *Journal of Artificial Intelligence Research* 74:765–850,
> 2022. DOI 10.1613/jair.1.13507.

**What it did.** Surveyed the field three decades on, comparing modern systems
along learning setting, hypothesis language, search strategy and their handling
of noise and recursion.

**Our delta.** By that survey's axes we occupy an unremarkable corner — small
hypothesis language, exhaustive search, no recursion — and the difference is
downstream of learning rather than in it: the induced rules are checked by a
proof assistant and probed against the environment.

---

## C9 · `evans2018dilp`

> Richard Evans and Edward Grefenstette. "Learning Explanatory Rules from Noisy
> Data." *Journal of Artificial Intelligence Research* 61:1–64, 2018.
> DOI 10.1613/jair.5714.

**What it did.** Gave a differentiable relaxation of ILP that induces explicit
rules by gradient descent, so that rule learning tolerates noisy and ambiguous
inputs.

**Our delta.** We keep the discrete search and pay for it with brittleness under
noise; the ledger we mine from is a deterministic record of an environment we
observed, so noise tolerance was not a pressure on the design and remains
untested.

---

## C10 · `cropper2021popper`

> Andrew Cropper and Rolf Morel. "Learning Programs by Learning from Failures."
> *Machine Learning* 110(4):801–856, 2021. DOI 10.1007/s10994-020-05934-z.

**What it did.** Introduced Popper and the learning-from-failures loop:
generate a hypothesis, test it, and turn each failure into a constraint that
prunes the remaining hypothesis space.

**Our delta.** Failure plays the same pruning role for us, but our failures come
from the ledger and from Lean rather than from an example test alone, and we
keep every hypothesis that survives instead of continuing until one remains.

---

## C11 · `yang2007arms`

> Qiang Yang, Kangheng Wu and Yunfei Jiang. "Learning Action Models from Plan
> Examples Using Weighted MAX-SAT." *Artificial Intelligence* 171(2–3):107–143,
> 2007. DOI 10.1016/j.artint.2006.11.005.

**What it did.** ARMS learned STRIPS action models — preconditions and effects —
from observed plan traces by encoding the constraints those traces impose as a
weighted MAX-SAT problem.

**Our delta.** Mining transition rules from a ledger is the same problem, and we
name it as such rather than presenting it as new; the differences are that we
return the whole consistent set instead of one maximally-weighted model, and
that the model we induce is compiled to a PDDL domain *and* to Lean, so the
learned preconditions are also the object of a proof.

---

## Fit with the existing §8.2 paragraph

The placeholder reads:

> **Program synthesis: CEGIS and ILP** [bib: TODO]. `engine-rig/engines/cegis_miner`
> runs the counterexample-guided loop for rule mining with the transition ledger as
> verifier; what differs is the return value — the frontier of all consistent
> hypotheses, kept as probe material, rather than one point guess.

Three edits are suggested, none of which changes a claim:

1. Attach C1 and C3 (and optionally C2) to "the counterexample-guided loop";
   attach C6, C7 and C8 to "ILP".
2. Attach C4 to "the frontier of all consistent hypotheses" and say plainly
   that it is a version space, since the honest ancestor of the return value is
   Mitchell's and the paragraph currently presents the frontier as the novelty.
   C5 belongs there too if the sentence is allowed a second citation.
3. Add one sentence naming action-model learning, cited to C11: mining
   transition rules from an observed ledger is that problem, and the paragraph
   should say so before it says what differs.
