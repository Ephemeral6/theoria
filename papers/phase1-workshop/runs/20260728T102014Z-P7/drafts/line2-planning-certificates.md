# Line 2 — certificates and admissible heuristics in classical planning

Thirteen confirmed records for the "Unsolvability certificates and admissible
heuristics in planning" anchor of
`papers/phase1-workshop/sections/11_related.md` §8.2. Verification trace, with
two independent sources per record and the exact URLs, is at
`papers/phase1-workshop/runs/20260728T102014Z-P7/search-traces/line2-planning-certificates.md`.
One candidate was dropped (the 2016 Unsolvability IPC, D1 in the trace): it has
no bibliographic record that could be cross-verified in two indexes.

Every "our delta" sentence below states a difference in construction, not a
measured advantage. **No arm of this paper was run against any of these
systems**, none of them was reimplemented, and no heuristic below was compared
against ours on any benchmark. The relevant artefact throughout is
`engine-rig/engines/lp_potential`, whose standing caveat applies to every claim
made for it here: it is sound but incomplete — it never certifies a solvable
configuration, and some genuinely unsolvable ones admit no *linear* pagoda.

Two facts about our setting recur in the deltas and are stated once here rather
than repeated in full each time. First, everything cited below certifies or
bounds a planning task whose **rules are given**; ours were **induced** from an
observed transition ledger, so a certificate we produce is a theorem about the
induced rules and is only as good as they are. Second, in that literature a
certificate ends the argument about an instance; here it is an input to a
mechanical repair loop (`cold-start-a2/artifacts/loop_ledger.json`).

A minimal citation set for one paragraph is C3, C4, C7 and C11; C1, C2, C5, C6,
C8, C9, C10, C12 and C13 are available if the paragraph is allowed to run
longer. C11 is the one the §4 boundary discipline needs, since the exported
artefact `engine-rig/interop/certificates/pagoda_5_11011_to_00010.json` uses the
term.

---

## C1 · `pommerening2015general`

> Florian Pommerening, Malte Helmert, Gabriele Röger and Jendrik Seipp. "From
> Non-Negative to General Operator Cost Partitioning." In *Proceedings of the
> Twenty-Ninth AAAI Conference on Artificial Intelligence (AAAI 2015)*,
> volume 29, AAAI Press, 2015. DOI 10.1609/aaai.v29i1.9668.

**What it did.** Showed that operator cost partitioning need not restrict itself
to non-negative distributed costs, that LP heuristics over operator-counting
constraints are cost-partitioned heuristics, and that a family of potential
heuristics falls out of general cost partitioning.

**Our delta.** This is where the paper's identity claim comes from — a potential
function is an admissible lower bound obtained from a linear program — and our
only structural difference is the direction we push it: we care about the
degenerate end of the bound, where the LP witnesses that no plan exists at all,
rather than about additivity among several heuristics.

---

## C2 · `seipp2015potential`

> Jendrik Seipp, Florian Pommerening and Malte Helmert. "New Optimization
> Functions for Potential Heuristics." In *Proceedings of the Twenty-Fifth
> International Conference on Automated Planning and Scheduling (ICAPS 2015)*,
> volume 25, pages 193–201, AAAI Press, 2015. DOI 10.1609/icaps.v25i1.13714.

**What it did.** Studied what a potential heuristic should be optimised for,
comparing objective functions that maximise the estimate at the initial state
against ones that maximise average estimates over sampled or all syntactic
states.

**Our delta.** Our objective is fixed rather than chosen: `lp_potential` asks
only whether the linear program admits a potential separating the initial from
the goal configuration, so the question "which objective gives the better
heuristic" does not arise, and the price of that simplification is the
incompleteness noted above.

---

## C3 · `pommerening2014lp`

> Florian Pommerening, Gabriele Röger, Malte Helmert and Blai Bonet. "LP-Based
> Heuristics for Cost-Optimal Planning." In *Proceedings of the Twenty-Fourth
> International Conference on Automated Planning and Scheduling (ICAPS 2014)*,
> volume 24, pages 226–234, AAAI Press, 2014. DOI 10.1609/icaps.v24i1.13621.

**What it did.** Introduced the operator-counting framework, in which several
families of admissible heuristics are recovered as linear programs over
constraints that every plan's operator counts must satisfy, and showed that such
constraints can be combined.

**Our delta.** The transition-invariant constraints our LP is built from play
the same role as operator-counting constraints — each is a linear inequality
every legal move must respect — but they are mined from the ledger by
`zero_space` and `cegis_miner` rather than derived from a domain description, so
the framework's soundness argument transfers only as far as the mining does.

---

## C4 · `helmert2009lmcut`

> Malte Helmert and Carmel Domshlak. "Landmarks, Critical Paths and
> Abstractions: What's the Difference Anyway?" In *Proceedings of the Nineteenth
> International Conference on Automated Planning and Scheduling (ICAPS 2009)*,
> volume 19, pages 162–169, AAAI Press, 2009. DOI 10.1609/icaps.v19i1.13370.

**What it did.** Showed that landmark, critical-path and abstraction heuristics
are closely related as ways of extracting an admissible lower bound, and
introduced the landmark cut heuristic.

**Our delta.** We rely on the same reading — that these are all lower-bound
constructions and differ mainly in what they are allowed to see — and add only
that the lower bound remains meaningful when it becomes infinite, which is the
case our engine is built for and which a heuristic used to guide search normally
treats as a boundary condition rather than as the point.

---

## C5 · `culberson1998pdb`

> Joseph C. Culberson and Jonathan Schaeffer. "Pattern Databases."
> *Computational Intelligence*, 14:318–334, 1998. DOI 10.1111/0824-7935.00065.

**What it did.** Introduced pattern databases: an admissible heuristic obtained
by solving an abstraction of the problem exhaustively and storing the exact
abstract distances in a lookup table.

**Our delta.** Our abstraction is not chosen by a human designer over known state
variables but is whatever the induced rules happen to expose, and it is stored as
a linear function rather than as an enumerated table, which is what makes the
certificate small enough to export and re-check at the boundary.

---

## C6 · `edelkamp2001pdb`

> Stefan Edelkamp. "Planning with Pattern Databases." In *Proceedings of the
> Sixth European Conference on Planning (ECP 2001)*, Toledo, Spain, 2001.

**What it did.** Brought pattern databases into domain-independent planning by
constructing abstractions automatically from a planning task's own variable
structure rather than by hand.

**Our delta.** Automatic construction from the task's structure is exactly what
we also need, with the difference that the structure is itself a hypothesis: the
abstraction is built over variables that `mdl_segmenter` proposed and that the
manual may later revise, so a repair to the manual can invalidate a certificate
that was correct with respect to the earlier rules.

---

## C7 · `eriksson2017certificates`

> Salomé Eriksson, Gabriele Röger and Malte Helmert. "Unsolvability Certificates
> for Classical Planning." In *Proceedings of the Twenty-Seventh International
> Conference on Automated Planning and Scheduling (ICAPS 2017)*, volume 27,
> pages 88–97, AAAI Press, 2017. DOI 10.1609/icaps.v27i1.13818.

**What it did.** Observed that plans for solvable tasks are routinely checked by
an independent validator while claims of unsolvability are taken on trust, and
defined certificate formats that let a planner's unsolvability verdict be
verified by a separate tool.

**Our delta.** We adopt the same discipline of shipping the evidence rather than
the verdict, and differ in what the verifier is being asked to trust: their
certificate is checked against a task the verifier already has, whereas ours must
travel with the induced rules it is a theorem about, which is why the obligation
is re-discharged in Lean rather than by a standalone checker.

---

## C8 · `eriksson2018proofsystem`

> Salomé Eriksson, Gabriele Röger and Malte Helmert. "A Proof System for
> Unsolvable Planning Tasks." In *Proceedings of the Twenty-Eighth International
> Conference on Automated Planning and Scheduling (ICAPS 2018)*, volume 28,
> pages 65–73, AAAI Press, 2018. DOI 10.1609/icaps.v28i1.13899.

**What it did.** Replaced the fixed certificate formats of the previous year with
a proof system whose rules compose set-based reasoning steps, so that a planner
can emit a derivation rather than a single monolithic witness.

**Our delta.** Ours is the degenerate case of that idea — one derivation step,
the linear pagoda — and the interesting difference is downstream: a failed
derivation here is not a negative result about the instance but a signal that the
induced rules are wrong, which is what the repair loop consumes.

---

## C9 · `hoffmann2014unsolvability`

> Jörg Hoffmann, Peter Kissmann and Álvaro Torralba. "'Distance'? Who Cares?
> Tailoring Merge-and-Shrink Heuristics to Detect Unsolvability." In *ECAI 2014*,
> Frontiers in Artificial Intelligence and Applications, volume 263, pages
> 441–446, IOS Press, 2014. DOI 10.3233/978-1-61499-419-0-441.

**What it did.** Argued that when the goal is to detect unsolvability the
numerical distance a heuristic estimates is beside the point, and re-tuned
merge-and-shrink so that it preserves only the distinction between reachable and
unreachable.

**Our delta.** We take the same collapse of the heuristic to a two-valued
question, and the consequence for us is not efficiency but honesty about
coverage: a method that only answers "unreachable or don't know" cannot be
scored by how close its estimates are, so §5 reports what it decided and what it
left open rather than an error measure.

---

## C10 · `helmert2006fastdownward`

> Malte Helmert. "The Fast Downward Planning System." *Journal of Artificial
> Intelligence Research*, 26:191–246, 2006. DOI 10.1613/jair.1705.

**What it did.** Described the Fast Downward planner, including the translation
of propositional planning tasks into multi-valued planning tasks and the
causal-graph heuristic built on that representation.

**Our delta.** We use it rather than compete with it:
`engine-rig/engines/fd_adapter` wraps a real Fast Downward build behind a
`solve(domain, problem)` interface, so the search half of the pipeline is a
citation rather than a contribution, and the PDDL our manual compiles to is
written to be consumed by it.

---

## C11 · `berlekamp2004winningways`

> Elwyn R. Berlekamp, John H. Conway and Richard K. Guy. "Purging Pegs Properly."
> Chapter 23 of *Winning Ways for Your Mathematical Plays*, 2nd edition, volume
> 4, pages 803–841, A K Peters, 2004. First edition: Academic Press, London,
> 1982, volume 2 (*Games in Particular*), where the pagoda-function material is
> at pages 729–730.

**What it did.** Introduced the pagoda function — an assignment of real values to
board positions that cannot increase under any legal jump — and used it to prove
particular peg-solitaire configurations unreachable, most famously the scout who
cannot be sent five paces into the desert.

**Our delta.** `lp_potential` computes exactly this object by linear programming
over a board whose jump relation was inferred from a transition ledger rather
than given by the rules of solitaire, so the certificate it emits is a pagoda for
the world as our manual currently describes it, and it is that qualification, not
the mathematics, that is ours.

---

## C12 · `beasley1992pegsolitaire`

> John D. Beasley. *The Ins and Outs of Peg Solitaire.* Oxford University Press,
> Oxford, 1992.

**What it did.** Gave the standard book-length treatment of peg solitaire,
collecting the feasibility arguments — resource counts, parity and position
classes among them — that decide which configurations can be reached from which.

**Our delta.** Nothing in our engine is new mathematics against this book; what
we add is that the invariants it presents as facts about a known game are, in our
setting, conjectures about an unknown one, which is why they are emitted as
theorem obligations rather than applied directly.

> Bibliographic caveat, carried over from the trace: both scholarly bibliographies
> that could be read directly give the year as 1992, and a 1985 Oxford first
> edition in the *Recreations in Mathematics* series is plausible but was not
> confirmable — no library catalogue was reachable. Re-check before submission.

---

## C13 · `kiyomi2001pegsolitaire`

> Masashi Kiyomi and Tomomi Matsui. "Integer Programming Based Algorithms for Peg
> Solitaire Problems." In *Computers and Games*, Lecture Notes in Computer
> Science, pages 229–240, Springer, 2001. DOI 10.1007/3-540-45579-5_15.
> Presented at CG 2000.

**What it did.** Formulated peg solitaire as an integer program, showed that the
pagoda-function argument is equivalent to the linear relaxation of that program,
and used the relaxation to prove many instances infeasible before search.

**Our delta.** This is the closest published analogue of what our engine does, and
the two differences are the ones this whole line turns on: their constraint matrix
is read off the board's known jump geometry where ours is assembled from mined
transitions, and their infeasibility result closes the instance where ours opens
a repair.
