# Line 2 — Planning: unsolvability certificates and admissible heuristics

规划领域的不可解证书与启发。Ammunition for `Theoria.md` §3.2 item 7 and for
`papers/phase1-workshop/sections/08_related.md` §8.2, first bullet.

## Why this line is in the argument

This line supplies the literature anchor for **证书与启发同源** — certificate and
heuristic are not two mechanisms but one object read at two amplitudes. An
admissible heuristic is a function *h* with *h(s) ≤ h\*(s)*: a **lower bound** on
the remaining cost, and therefore already a proof, discharged every time a node
is pruned, that no cheaper completion exists. Push that bound to its limit case
and the same object becomes an unsolvability certificate: *h(s₀)=∞* is the claim
that *no* completion exists at all. The planning literature arrives at this
identity from both ends. From the heuristic end, the LP-based family
(operator-counting, potential heuristics) writes admissibility as a set of
declarative linear constraints, so that *every feasible solution of the LP is an
admissible heuristic* — the heuristic is literally a dual solution, i.e. a
certificate. From the certificate end, the Basel proof-system line asks a planner
that answers "unsolvable" to hand over an independently checkable artefact,
because a plan can be validated and a claim of non-existence, until then, could
not.

`engine-rig/engines/lp_potential` is that identity implemented as one solver: a
single linear program over a state graph yields one integer weight vector, and
that same vector is read twice — once as an unsolvability certificate (weights
non-increasing along every legal move, yet strictly higher at the goal than at
the initial state) and once as an admissible heuristic
(`h(s) = min_g ⌈max(0, w(g) − w(s)) / M⌉`, `engine-rig/DECISIONS.md` D-008).

The name we put on that artefact — **pagoda** — is not ours and is not from
planning. It comes from the peg-solitaire literature, and §"Provenance of the
word *pagoda*" below records what could actually be established about it, since
we use the word in shipped artefacts (`engine-rig/interop/certificates/pagoda_*.json`,
schema `lp_potential/pagoda_certificate@1`).

**The delta, stated once for the whole line** (`Theoria.md` §3.2 item 7, verbatim):
*"他们证给定规则的游戏,我们证归纳出来的规则,且证书参与修复回路"* — every work
below certifies a task whose rules are **given** (a PDDL/SAS⁺ domain, a peg board,
a transition system handed to the solver). We certify rules that were **induced**
from a transition ledger, so a certificate that is valid can still be about the
wrong world; and the certificate therefore does not terminate the argument but
re-enters it as an obligation in a repair loop
(`cold-start-a2/artifacts/loop_ledger.json`). Per-entry deltas below say what
that means against that particular work.

---

## `hart1968formal` — Hart, Nilsson & Raphael, A\*

**What it did.** Gave a formal basis for heuristic search, proving that A\* is
guaranteed to find a minimum-cost path when its heuristic never overestimates the
remaining cost to a goal.

**Our delta.** This is the origin of the lower-bound reading of *h* that the whole
line rests on, and our LP emits exactly such a bound; what it does not consider is
where the cost structure came from — for us the transition model over which "the
remaining cost" is even defined is itself a mined hypothesis.

`verified:` (1) CrossRef API record for DOI `10.1109/TSSC.1968.300136`; (2) DBLP
record `journals/tssc/HartNR68`. Both give: *A Formal Basis for the Heuristic
Determination of Minimum Cost Paths*, IEEE Transactions on Systems Science and
Cybernetics 4(2):100–107, 1968.

## `culberson1998pattern` — Culberson & Schaeffer, pattern databases

**What it did.** Introduced pattern databases: admissible heuristics obtained by
solving a relaxed abstraction of the problem exhaustively and storing the exact
abstract distances in a lookup table.

**Our delta.** A pattern database is a certificate compiled ahead of time from a
given abstraction of given rules; our weight vector is solved on demand from rules
that were induced, and it is retained as a checkable object rather than a table.

`verified:` (1) CrossRef API record for DOI `10.1111/0824-7935.00065`; (2) DBLP
record `journals/ci/CulbersonS98`. Both give: *Pattern Databases*, Computational
Intelligence 14(3):318–334, 1998.

## `haslum2007domain` — Haslum, Botea, Helmert, Bonet & Koenig, PDBs for planning

**What it did.** Showed how to construct pattern-database heuristics for
cost-optimal domain-independent planning automatically, searching the space of
pattern collections rather than requiring hand-chosen patterns.

**Our delta.** The abstraction is selected automatically but the domain it
abstracts is still supplied; our abstraction is selected over a domain that is
itself the current hypothesis, so a badly chosen pattern and a badly mined rule
are failures of the same kind and both must return to the repair loop.

`verified:` (1) DBLP record `conf/aaai/HaslumBHBK07` (AAAI 2007, pp. 1007–1012);
(2) AAAI digital library page `aaai.org/Library/AAAI/2007/aaai07-160.php`. Both
give title, all five authors, AAAI 2007.

## `helmert2009landmarks` — Helmert & Domshlak, LM-cut

**What it did.** Proved that admissible heuristics based on delete relaxations,
critical paths, abstractions and landmarks are closely related, and introduced
the landmark-cut heuristic on the strength of that unification.

**Our delta.** This is the strongest statement in the literature that the
admissible heuristics are one family under different presentations — the
same-object claim we extend from heuristics to certificates; the unification
there is proved over a fixed task description, whereas ours has to survive the
description changing under it.

`verified:` (1) DBLP search-API record for this title (venue ICAPS, year 2009);
(2) AAAI OJS proceedings page
`ojs.aaai.org/index.php/ICAPS/article/view/13370`, which gives ICAPS vol. 19(1),
pp. 162–169, DOI `10.1609/icaps.v19i1.13370`. Both agree on title, authors,
venue and year.

## `pommerening2014lp` — Pommerening, Röger, Helmert & Bonet, operator counting

**What it did.** Gave a common LP framework for cost-optimal planning heuristics
in which constraints from different sources are stated over **operator-counting
variables** and can be combined into a single heuristic that dominates the maximum
of its components.

**Our delta.** Same LP-as-heuristic move, and our certificate is the dual object
their framework makes available; the constraints there are read off a given
operator set, while ours are read off operators recovered from a transition
ledger — so an unsound constraint is a live possibility we must be able to
retract, not a modelling error ruled out by construction.

`verified:` (1) AAAI OJS proceedings page
`ojs.aaai.org/index.php/ICAPS/article/view/13621` (ICAPS vol. 24(1), pp. 226–234,
DOI `10.1609/icaps.v24i1.13621`); (2) DBLP record `conf/aips/PommereningRHB14`.
Both agree on title, all four authors, ICAPS, 2014. (DBLP records no DOI for this
entry; the page range comes from the AAAI OJS record.)

## `pommerening2015nonnegative` — Pommerening, Helmert, Röger & Seipp, potential heuristics

**What it did.** Showed that operator cost partitioning does not require
non-negative costs, related LP heuristics over operator-counting constraints to
cost-partitioned heuristics, and in doing so introduced **potential heuristics** —
a family of heuristics defined by declarative constraints whose every feasible
solution is admissible.

**Our delta.** This is the closest formal relative of `lp_potential`: a potential
function is a weight vector constrained so that admissibility holds by
construction, which is exactly our certificate condition; the difference is that
their constraint system is generated from a given SAS⁺ task, while ours is
generated from induced rules and its infeasibility is therefore evidence about
the *hypothesis*, not only about the *task*.

`verified:` (1) DBLP search-API record (AAAI 2015, pp. 3335–3341, DOI
`10.1609/AAAI.V29I1.9668`); (2) AAAI OJS proceedings page
`ojs.aaai.org/index.php/AAAI/article/view/9668`, whose abstract confirms the
introduction of "a new family of potential heuristics". Both agree on title, all
four authors, AAAI, 2015.

## `seipp2015new` — Seipp, Pommerening & Helmert, optimising potential heuristics

**What it did.** Introduced several new objective functions for selecting a
potential heuristic from the space of admissible ones — optimising for all states,
or for a sample of reachable states, rather than only for the initial state.

**Our delta.** They choose among admissible weight vectors to maximise search
utility; we choose among them to maximise *certificate margin*, because our
consumer is a proof obligation rather than a node expansion — and our objective
also has to keep the solution integral so the certificate re-checks exactly
(`engine-rig/DECISIONS.md`).

`verified:` (1) AAAI OJS proceedings page
`ojs.aaai.org/index.php/ICAPS/article/view/13714` (ICAPS vol. 25(1), pp. 193–201);
(2) CrossRef API record for DOI `10.1609/icaps.v25i1.13714`. Both give title,
three authors, ICAPS, 2015, pp. 193–201.

## `eriksson2017unsolvability` — Eriksson, Röger & Helmert, unsolvability certificates

**What it did.** Observed that plans for solvable tasks are routinely
machine-validated while claims of unsolvability were not, and proposed a sound and
complete class of unsolvability certificates that an independent program can
verify efficiently.

**Our delta.** This is the paper our artefact format answers to — a certificate
that travels and is re-checked by a consumer that does not trust the producer;
what is new here is that the task the certificate is *about* was not given to us,
so re-checking it establishes internal validity only, and external validity stays
with the ledger.

`verified:` (1) AAAI paper page
`aaai.org/papers/00088-13818-unsolvability-certificates-for-classical-planning/`;
(2) CrossRef API record for DOI `10.1609/icaps.v27i1.13818`. Both give: ICAPS
vol. 27(1), pp. 88–97, 2017, three authors.

## `eriksson2018proof` — Eriksson, Röger & Helmert, a proof system

**What it did.** Replaced single-shot certificates with a rule-based proof system
for unsolvable planning tasks: a knowledge base of verifiable basic statements
plus derivation rules from which unsolvability is inferred, argued to be more
flexible than their earlier inductive certificates.

**Our delta.** The nearest thing in planning to what we want, and the honest
comparison point: their derivation rules are sound with respect to a task
definition that is stipulated, whereas our rules are premises under test, so our
"proof" is conditional on a hypothesis and its refutation is informative rather
than merely fatal — it names which mined rule to repair.

`verified:` (1) AAAI OJS proceedings page
`ojs.aaai.org/index.php/ICAPS/article/view/13899`; (2) CrossRef API record for
DOI `10.1609/icaps.v28i1.13899`. Both give: ICAPS vol. 28(1), pp. 65–73, 2018,
three authors.

## `roger2017towards` — Röger, certified unsolvability (programme statement)

**What it did.** An IJCAI early-career paper setting out the research programme:
solutions are easy to validate, non-existence of solutions is not, and
certificates should allow independent verification of the absence of a solution
across a range of planning approaches.

**Our delta.** Useful as the field's own framing of the gap; our position is that
the gap does not close by certifying harder, because in an induced setting a
verified certificate about the wrong transition system is exactly the failure mode
`Theoria.md` §1.3 describes and the reason the certificate must feed a loop.

`verified:` (1) IJCAI proceedings page `ijcai.org/proceedings/2017/738` (IJCAI
2017, pp. 5141–5145, DOI `10.24963/ijcai.2017/738`); (2) DBLP search record for
the same title. Both give single author Gabriele Röger, IJCAI, 2017, pp.
5141–5145.

---

## Provenance of the word *pagoda*

Our artefacts ship the word (`lp_potential/pagoda_certificate@1`), so it was
checked rather than assumed. What is established:

* The term belongs to **peg solitaire**, not to planning. `berlekamp1982winning`
  is where it is published: Berlekamp, Conway & Guy use the pagoda-function
  argument to show the infeasibility of the peg-solitaire problem "sending a
  scout 5 paces out into the desert".
* The attribution is confirmed by an independent third party rather than inferred:
  `kiyomi2001integer` states it twice in its own words — "In the well-known book
  *Winning ways for Mathematical Plays* [3], Berlekamp, Conway and Guy discussed
  variations of problems related to peg solitaire problems. They showed the
  infeasibility of the peg solitaire problem 'sending scout 5 paces out into
  desert' by using the pagoda function approach", and "In [3], Berlekamp, Conway
  and Guy proposed the pagoda function approach for showing the infeasibility of
  some peg solitaire problems". Its reference [3] is *Winning Ways for
  Mathematical Plays*, Academic Press, London, 1982.
* **Limit of the claim.** What is verified is that the pagoda-function *argument*
  is published in `berlekamp1982winning` and is attributed to those three authors
  by later peer-reviewed work. Two things are *not* verified here and are not
  claimed anywhere in our artefacts: (a) that the coinage is original to that book
  rather than to earlier unpublished work by Conway — secondary sources describe
  the underlying solitaire-cone work as going back to Boardman and Conway in the
  1960s, which we did not trace to a citable primary source; and (b) the
  frequently repeated explanation that Conway chose "pagoda" for the tiered shape
  of the weight bar-graph, which we could not source to anything citable. So we
  cite the book as the published locus of the technique, not as a claim of first
  coinage.
* **Why it matters for `lp_potential` specifically.** `kiyomi2001integer` records
  that Kanno gave a linear-programming characterisation — a pagoda function
  proving infeasibility exists **iff** a certain LP has negative optimum — which is
  precisely the shape of our solver, and it states in the same passage that "the
  inverse implication does not hold; that is, there exists an infeasible peg
  solitaire problem instance such that the optimal value of the corresponding
  linear programming problem […] is equal to 0". That is our `DECISIONS.md` D-014
  (configuration `0111` is unsolvable and `solve_certificate` returns `None`)
  appearing in the peg-solitaire literature decades earlier: **the incompleteness
  of the linear pagoda method is a known property of the method, not a defect of
  our implementation.** This is the citation that lets us say so in print.
  (Kanno's own work is a 1997 University of Tokyo bachelor thesis, in Japanese,
  known to us only through this reference — see quarantine.)
* `beasley1985ins` is included as the standard monograph on the game, the
  reference work behind the peg-solitaire tradition we borrowed the name from.

## `berlekamp1982winning` — Berlekamp, Conway & Guy, *Winning Ways*

**What it did.** The compendium of combinatorial game theory whose peg-solitaire
material introduces the pagoda-function argument and uses it to prove specific
peg-solitaire targets unreachable.

**Our delta.** We take the name and the argument shape — a weight assignment
monotone under every legal move — and mechanise the search for the weights as an
LP over a transition relation that was mined rather than stated in a rulebook.

`verified:` (1) reference [3] of `kiyomi2001integer` (peer-reviewed, cites
*Winning Ways for Mathematical Plays*, Academic Press, London, 1982); (2) review
by A. K. Austin, The Mathematical Gazette 67(441):242–243, 1983, DOI
`10.2307/3617209`, whose printed title records "vols 1 and 2, by Elwyn R.
Berlekamp, John H. Conway and Richard K. Guy … 1982 … (Academic Press)". Both
agree on authors, publisher and year. *Note:* the 1982 Academic Press edition is
in two volumes; the later A K Peters edition splits the same material into four.
We cite the 1982 edition and give no volume or page number, because we verified
neither.

## `beasley1985ins` — Beasley, *The Ins and Outs of Peg Solitaire*

**What it did.** The standard monograph on peg solitaire: its history, how to play
it, the theory behind it, and a large problem collection.

**Our delta.** Context rather than method — it is the body of work in which the
weight-function style of infeasibility argument lives, and which we are drawing on
by naming our certificates *pagoda* at all.

`verified:` (1) Open Library record `OL3028295M`; (2) Internet Archive catalogue
record `insoutsofpegsoli0000beas`. Both give: John D. Beasley, *The Ins and Outs
of Peg Solitaire*, Oxford University Press, 1985. *ISBN deliberately omitted* —
retailer listings give `0198532032` but no catalogue record we opened confirmed
it, so it is not in the `.bib`.

## `kiyomi2001integer` — Kiyomi & Matsui, IP/LP algorithms for peg solitaire

**What it did.** Formulated the peg-solitaire problem as an integer program,
showed that the pagoda-function approach is equivalent to the LP relaxation of
that program, and used the relaxation to prove many peg-solitaire instances
infeasible.

**Our delta.** This is the closest published analogue of `lp_potential`'s method —
same LP, same dual reading, same known incompleteness — applied to one fixed
classical board whose move rule is given by the game; ours runs over a state graph
whose move rule is a mined hypothesis, and emits the weight vector as a portable
certificate for a downstream re-checker rather than as a pruning bound inside its
own backtrack search.

`verified:` (1) CrossRef API record for DOI `10.1007/3-540-45579-5_15` (title,
both authors, pp. 229–240, Springer, 2001); (2) DBLP search record, same title,
both authors, venue *Computers and Games*, pp. 229–240, same DOI. *Year-label
discrepancy, resolved not suppressed:* DBLP labels it **2000** (the conference,
CG 2000, Hamamatsu, 26–28 October 2000), CrossRef labels it **2001** (the Springer
revised-papers volume). CrossRef's record for the containing book DOI
`10.1007/3-540-45579-5` confirms the reconciliation: *Computers and Games: Second
International Conference, CG 2000 … Revised Papers*, Springer, 2001. We cite 2001
and write the conference year into the `booktitle`. The LNCS series **number** is
not in the `.bib`: secondary sources say volume 2063, no source we opened
confirmed it, so the entry carries the series name only. Full text of the RIMS
Kōkyūroku version (1185:100–108, 2001) was read directly for the pagoda passages
quoted above.

---

## Quarantined

Not in `02_planning_certificates.bib`. Per red line 1, these are recorded with
what specifically could not be confirmed.

### `edelkamp2001planning` — Edelkamp, "Planning with Pattern Databases", ECP-01

Wanted for the line (it is the standard planning-PDB citation), **withheld on a
page-range conflict and a missing second source.**

* Web search asserted "Proceedings of the 6th European Conference on Planning
  (ECP'01), pages 13–24".
* The AAAI-hosted scan of the paper (`cdn.aaai.org/ocs/7280/7280-37829-1-PB.pdf`)
  was read directly: its running header is "Proceedings of the Sixth European
  Conference on Planning" and its **first page is numbered 84**, which is
  irreconcilable with a 13–24 range.
* DBLP does not appear to index ECP 2001: four separate queries
  (`Edelkamp Planning with Pattern Databases`, `Planning with Pattern Databases`,
  `pattern databases planning Edelkamp`, and the guessed key
  `conf/ecp/Edelkamp01`, which 404s) returned no 2001 ECP entry. So the only
  record obtained is AAAI's, and the AAAI OCS landing page and the AAAI PDF are
  the same publisher, not two independent sources.
* Title, sole author, venue and year (2001) are consistent everywhere and are
  probably fine; the *page range* is not, and no independent second record was
  obtained. Coverage of planning pattern databases is carried instead by
  `culberson1998pattern` (the origin) and `haslum2007domain` (the planning
  construction), both of which verified cleanly.

### Unsolvability IPC 2016 — no citable write-up located

The brief asked for the unsolvability IPC track "if it has a citable write-up".
Searching found the competition itself (organised by Christian Muise and Nir
Lipovetzky, run ahead of ICAPS 2016), a call-for-domains mailing-list post, a
planner-abstracts booklet hosted at `unsolve-ipc.eng.unimelb.edu.au`, and a
GitHub instance repository — but **no peer-reviewed competition report** that
could be cross-verified against two independent bibliographic records. Later
papers cite it as "(Muise and Lipovetzky, 2016)" pointing at the competition
website. A `@misc` entry citing the website would be admissible under red line 4
if the paper needs it, but it was not manufactured here without a second source
for the record; the certificate literature is anchored instead by
`eriksson2017unsolvability` and `eriksson2018proof`, which are the technical
content the IPC track was organised around.

### Kanno (1997), LP algorithm for peg solitaire — untraceable primary source

Cited by `kiyomi2001integer` as "Kanno, E.: Linear Programming Algorithm for Peg
Solitaire Problems, Bachelor thesis, Department of Mathematical Engineering,
Faculty of Engineering, University of Tokyo, 1997 (in Japanese)". This is the
source of the *iff* characterisation and of the incompleteness counterexample
that mirror our D-014, so it matters; but it is an unpublished undergraduate
thesis in Japanese and no independent catalogue record was found. **Cite the
result through `kiyomi2001integer`, never directly.**

### Not attempted: origin of the coinage "pagoda"

See "Provenance of the word *pagoda*" above. The claims that the term originates
with Conway personally (rather than with the 1982 book) and that it refers to the
tiered shape of the weight bar-graph are widely repeated but were not traced to a
citable source, so neither claim appears in the `.bib`, the line file's assertions,
or any repository artefact.

---

## Red line 3 — sealed pile

No back-off was needed. Every query on this line was academic-bibliographic
(arXiv/DBLP/CrossRef/Semantic Scholar/AAAI-OJS/IJCAI/Springer/Cambridge Core/
library catalogues). No ARC-AGI-3 page, game page, walkthrough, leaderboard,
`schema-harness.github.io` or trajectory dataset was opened or returned, and no
result began describing the mechanics of any sealed game. The only *game*
mechanics encountered are those of peg solitaire — a classical puzzle in the
mathematical literature, unrelated to the pile — and they are the subject matter
of `berlekamp1982winning`, `beasley1985ins` and `kiyomi2001integer` by design.
