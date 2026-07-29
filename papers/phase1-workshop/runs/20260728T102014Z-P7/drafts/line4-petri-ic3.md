# Line 4 — Petri-net invariants, model checking, IC3/PDR

Nine confirmed records for the "Petri invariants and model checking / IC3"
anchor of `papers/phase1-workshop/sections/11_related.md` §8.2. The verification
trace, with two independent sources per record and the exact URLs, is at
`papers/phase1-workshop/runs/20260728T102014Z-P7/search-traces/line4-petri-ic3.md`.

Every "our delta" sentence below states a difference in construction, not a
measured advantage. **No arm of this paper was run against any of these systems**,
and none of them was reimplemented for comparison.

Three honesty constraints govern this whole section and are repeated in the
delta sentences rather than assumed:

1. **`engine-rig/engines/zero_space` is not a Petri-net tool and must not be
   described as one.** It encodes each `(cell, colour)` pair as an indicator
   variable, differences consecutive *observed* states, and takes the null space
   of the resulting difference matrix. The kinship with place invariants is real
   but is a structural analogy: a P-invariant is derived symbolically from the
   net's incidence matrix — that is, from the **rules** — whereas `zero_space`
   reads **data**. What it returns is an empirical regularity over one
   trajectory, not a symbolically derived invariant.
2. **`engine-rig/engines/ic3_pdr` and `engine-rig/engines/deadlock_carver` are
   not exercised by any result in this paper.** They are cited here as the
   lineage of two engines that exist in the rig; the paper reports no run of
   either.
3. **All engine output is consumed as a source of theorem obligations, never as
   a verdict.** The obligation is re-discharged in Lean, which is where "holds
   on this trajectory" is upgraded to "holds under the manual's own `step`".

A minimal citation set for one paragraph is C1, C2, C5 and C6; C3, C4, C7, C8
and C9 are available if the paragraph is allowed to run longer. If the paragraph
must be a single sentence, C2 and C5 carry it.

---

## C1 · `petri1962kommunikation`

> Carl Adam Petri. *Kommunikation mit Automaten.* Dissertation, Technische
> Hochschule Darmstadt, Fakultät für Mathematik und Physik, 1962 (defended
> 20 June 1962). Published as *Schriften des Rheinisch-Westfälischen Instituts
> für Instrumentelle Mathematik an der Universität Bonn*, Nr. 2, Bonn, 1962.
> English translation: *Communication with Automata*, Griffiss Air Force Base,
> New York, Technical Report RADC-TR-65-377, Vol. 1, 1966.

**What it did.** Introduced the net formalism that became known as Petri nets,
giving concurrent systems a graphical and algebraic representation in which
places hold tokens and transitions move them.

**Our delta.** We inherit only the idea that a system's structure can carry
quantities that no step disturbs; our carrier is not a net but an induced world
manual, and the artefact `zero_space` produces is read off recorded states
rather than off a net's structure.

**Citation hygiene.** A widespread secondary error gives this as a thesis of the
University of Bonn. Bonn is where the work was *published*, in the IIM series;
the doctorate was awarded by TH Darmstadt. See the trace, C1, for the catalogue
records that separate the two.

---

## C2 · `murata1989petri`

> Tadao Murata. "Petri Nets: Properties, Analysis and Applications."
> *Proceedings of the IEEE*, 77(4):541–580, 1989. DOI 10.1109/5.24143.

**What it did.** The canonical survey of Petri-net theory, including the
matrix-algebraic treatment in which a place invariant is a vector in the left
null space of the incidence matrix — a linear quantity that every transition
preserves.

**Our delta.** `zero_space` computes a null space too, but of a *difference
matrix built from observed consecutive states*, not of an incidence matrix
derived from rules; the object it returns is therefore an empirical regularity
over one trajectory, and it becomes a claim about the world only after the same
statement is re-proved in Lean against the manual's own `step` function.

---

## C3 · `colom1991convex`

> José Manuel Colom and Manuel Silva Suárez. "Convex Geometry and Semiflows in
> P/T Nets: A Comparative Study of Algorithms for Computation of Minimal
> P-Semiflows." In *Advances in Petri Nets 1990*, ed. Grzegorz Rozenberg,
> Lecture Notes in Computer Science 483, pages 79–112, Springer, 1991.
> DOI 10.1007/3-540-53863-1_22. (10th International Conference on Applications
> and Theory of Petri Nets, Bonn, June 1989.)

**What it did.** Compared algorithms for computing the minimal P-semiflows of a
place/transition net, treating invariant extraction as a convex-geometry problem
over the incidence matrix rather than as an ad-hoc search.

**Our delta.** The same question — which non-negative linear combinations are
conserved — is asked of a matrix we assembled from observations, so minimality
of the returned basis buys us a compact set of *candidate* obligations rather
than a complete structural characterisation of a known net.

---

## C4 · `ezpeleta1995deadlock`

> Joaquín Ezpeleta, José Manuel Colom and Javier Martínez. "A Petri Net Based
> Deadlock Prevention Policy for Flexible Manufacturing Systems." *IEEE
> Transactions on Robotics and Automation*, 11(2):173–184, 1995.
> DOI 10.1109/70.370500.

**What it did.** Used siphons — structural subsets of places that once emptied
can never refill — to derive a control policy guaranteeing that a class of
resource-allocation nets cannot deadlock.

**Our delta.** `engine-rig/engines/deadlock_carver` aims at the same shape of
statement, a structural reason why a region of the state space cannot be left,
but emits it as a *conditional mini unsolvability theorem* to be discharged in
Lean rather than as a controller; **it is not exercised by any result in this
paper**, and is named here only to locate the engine's ancestry.

---

## C5 · `bradley2011ic3`

> Aaron R. Bradley. "SAT-Based Model Checking without Unrolling." In
> *Verification, Model Checking, and Abstract Interpretation (VMCAI 2011)*,
> ed. Ranjit Jhala and David A. Schmidt, Lecture Notes in Computer Science 6538,
> pages 70–87, Springer, 2011. DOI 10.1007/978-3-642-18275-4_7.

**What it did.** Introduced IC3: instead of unrolling the transition relation,
it incrementally strengthens a sequence of over-approximate frames with
relatively inductive clauses until an inductive invariant separating the initial
states from the bad states is found.

**Our delta.** `engine-rig/engines/ic3_pdr` supplies inductive invariants of
shapes the LP-based potential-function engine cannot express, and it does so
over a transition relation that was *induced from a ledger* rather than given;
**it is not exercised by any result in this paper**, and whatever it produces is
an obligation for Lean, not a verdict.

---

## C6 · `een2011pdr`

> Niklas Eén, Alan Mishchenko and Robert K. Brayton. "Efficient Implementation
> of Property Directed Reachability." In *Proceedings of the International
> Conference on Formal Methods in Computer-Aided Design (FMCAD 2011)*, pages
> 125–134, FMCAD Inc. / IEEE, Austin, TX, 2011.

**What it did.** Reformulated and re-engineered Bradley's algorithm as property
directed reachability, and gave the implementation — proof-obligation queues,
ternary simulation, incremental SAT — that made the method fast enough to be
adopted as a default hardware model-checking engine.

**Our delta.** We take the algorithm as a component and not as the verifier of
record: its inductive invariant is an obligation re-discharged in Lean against
the manual's own `step`, because a proof about an induced transition relation is
only a proof about the world once the relation itself has been written down as
the theory under test.

---

## C7 · `clarke1981skeletons`

> Edmund M. Clarke and E. Allen Emerson. "Design and Synthesis of
> Synchronization Skeletons Using Branching-Time Temporal Logic." In *Logics of
> Programs, Workshop, Yorktown Heights, New York, USA, May 1981*, ed. Dexter
> Kozen, Lecture Notes in Computer Science 131, pages 52–71, Springer, 1981
> (volume published 1982). DOI 10.1007/BFb0025774.

**What it did.** One of the two independent origins of model checking: gave an
algorithm deciding whether a finite-state concurrent program satisfies a
branching-time temporal-logic specification, and used it to synthesise
synchronisation skeletons.

**Our delta.** Model checking assumes the model is given and asks whether the
property holds; our loop has neither in hand at the start — the model is mined
from a transition ledger and the properties are proposed by engines — so
checking is one stage of a pipeline whose earlier stages can also be wrong.

---

## C8 · `queille1982cesar`

> Jean-Pierre Queille and J. Sifakis. "Specification and Verification of
> Concurrent Systems in CESAR." In *International Symposium on Programming, 5th
> Colloquium, Torino, Italy, April 6–8, 1982, Proceedings*, ed. Mariangiola
> Dezani-Ciancaglini and Ugo Montanari, Lecture Notes in Computer Science 137,
> pages 337–351, Springer, 1982. DOI 10.1007/3-540-11494-7_22.

**What it did.** The other independent origin of model checking: the CESAR
system, which verified branching-time temporal properties of concurrent programs
against a finite-state model derived from the program text.

**Our delta.** CESAR derived its model from a program a human had written; we
derive ours from behaviour a human never wrote down, which is what makes
specification error a *mining* error in our setting rather than a transcription
error, and what makes the refutation loop of §5.6 necessary rather than
optional.

---

## C9 · `mcmillan2003interpolation`

> Kenneth L. McMillan. "Interpolation and SAT-Based Model Checking." In
> *Computer Aided Verification, 15th International Conference, CAV 2003,
> Boulder, CO, USA, July 8–12, 2003, Proceedings*, ed. Warren A. Hunt Jr. and
> Fabio Somenzi, Lecture Notes in Computer Science 2725, pages 1–13, Springer,
> 2003. DOI 10.1007/978-3-540-45069-6_1.

**What it did.** Showed that Craig interpolants extracted from the refutation
proof of a bounded-model-checking instance yield over-approximations of
reachable states, turning a bounded method into a complete one without
computing exact image sets.

**Our delta.** The lesson we take is the one about provenance rather than the
technique: an artefact extracted from a proof carries its own justification and
can be re-checked downstream, which is the same discipline our engines are held
to when their output crosses into Lean.

---

## Not offered

**Lautenbach on linear-algebraic deadlock/trap calculation.** Considered and
**dropped** — a single lookup for it failed and no second source was obtained,
so no record for it is written here. See the trace, "Dropped".

**Somenzi & Bradley, "IC3: Where Monolithic and Incremental Meet" (FMCAD
2011).** Real, and adjacent, but not verified against two sources because C5 and
C6 already cover the IC3/PDR anchor. Not cited.
