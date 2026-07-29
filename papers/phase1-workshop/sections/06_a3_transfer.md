## 6 · A3 — the second level costs one frame, and the free check is blind

A0 and A2 both induce a theory and then grade it on the world it came from. The
question this section reports is the next one: **does a theory carried to a
world it has never seen still work, and what does the second world cost?** In
the claim menu of `Theoria.md` §3.2 this is C3 — *携两本书跨关，第二关边际成本
⟨≪⟩* — and it is listed there as conditional, because whether it holds depends
on how much mechanism the two levels share.

A3 answers it for two levels of one game, which is the weakest interesting
reading of C3 and the one the framework's own wording licenses. Anything
stronger needs a different experiment, and `cold-start-a3/A3_REPORT.md` §6 says
so before we do.

### 6.1 The setup

Two 9×9 levels of the same four mechanisms — push, a toggle Switch that drives a
Door in the same transition, a two-way portal pair, and a goal cell
(`cold-start-a3/a3world/a3_world.py`). The layouts share no level constant:
every one of the eight placed cells moves between L1 and L2
(`cold-start-a3/artifacts/ground_truth.json`). L1 has 62 reachable states, L2 has
63.

Three arms were run against L2, which is what makes the comparison a measurement
rather than an anecdote:

| arm | what it was given | artefact |
|---|---|---|
| **cold start** | nothing; induce L1 from scratch | `cold-start-a3/artifacts/arm_l1_cold_start.json` |
| **transfer** | L1's two books, unchanged | `cold-start-a3/artifacts/arm_l2_transfer.json` |
| **blind control** | nothing; induce L2 from its own sweep, by an author held blind to L1 | `cold-start-a3/artifacts/domain_agreement.json` |

The transfer arm carried `cold-start-a3/theory/domain.dsl` and `cold-start-a3/theory/playbook.dsl` unchanged
and re-derived exactly one thing: the problem instance. Both levels' executable
theories are generated from the *same* domain source, and the diff between them
is 35 lines confined to `LANDMARKS`, `BOARD`, `is_goal` and `initial_state` — the
guard and effect functions are byte-identical, which
`cold-start-a3/tests/test_transfer.py` asserts rather than eyeballs.

### 6.2 The bill

The number C3 is about is the **like-for-like** one: the same level, with books
against without (`cold-start-a3/artifacts/bill_table.md`).

| line | L2 from scratch | L2 with books | ratio |
|---|---|---|---|
| world frames | 347 | **11** | 0.032 |
| world actions | 346 | **10** | **0.029** |
| engine stages | 1 | **0** | 0 |
| candidates adjudicated | 35 | **0** | 0 |
| theorize rounds | 5 | **0** | 0 |
| DSL clauses written | 33 | **0** | 0 |
| compile / certify / plan runs | 1 / 3 / 1 | 1 / 3 / 1 | 1 |

The zeros are the interesting column, and the last row is why. Carrying the
books removed the *inductive* work entirely — no engine stage ran, no candidate
was adjudicated, no theorize round happened, no clause was written — while the
*verification* work was paid in full and at exactly the same rate. Nothing was
saved by trusting the carried theory.

Sharper still is the cost to the **first plan**. The transfer arm read one frame
(`cold-start-a3/artifacts/l2_frame0.json`) and took zero actions before it had a
plan; the cold start needed 333 frames and 332 actions to reach the same point
(`cold-start-a3/artifacts/bill_table.md`). Of the nine fields the problem instance needs, six were
derived from that single frame and three were supplied
(`cold-start-a3/artifacts/provenance_l2_transfer.json`) — see §6.5.

The plan was SAT at length 10, equal to the referee's shortest solution for L2,
and executing it won: `outcome: "win"`, `actions_spent: 10`
(`cold-start-a3/artifacts/arm_l2_transfer.json`). Replay certify is green over
11 frames and 891 pixels with zero anomalies, and Lean discharges `inv_all` with
an empty axiom list.

Scored against the referee's copy, the **carried** manual is right on 252 of 252
reachable (state, action) pairs of a level it never explored
(`cold-start-a3/artifacts/score_vs_truth.json`). This is every reachable pair,
not a held-out split — A3 has no held-out set.

**And the control scores the same.** The third row of that artefact is "the
control arm's manual, induced from level 2's own sweep", and it is also right on
**252 of 252** (`cold-start-a3/artifacts/score_vs_truth.json`, `results[2]`, `cold-start-a3/theory/generated_l2_scratch/`).
Earlier drafts of this section reported the carried manual's 252/252 and did not
print the control's, which made an undiscriminating number look like the result.
It is not: **on accuracy the two arms are tied at ceiling, and this measurement
cannot separate transfer from induction at all.** Both manuals are right about
level 2; what differs is what each cost to obtain, which is §6.2's bill and is the
only place the transfer claim can live. A ceiling that both arms reach is a
property of the level — 252 pairs of a small deterministic world — rather than
evidence about carrying books, and reporting one arm's ceiling alone was the kind
of one-sided denominator this paper spends §7 criticising in someone else's
instrument.

The file's own framing of what the score means is still the honest one:

> Replay against a trajectory answers "is the manual consistent with what I
> saw". This answers "is the manual right".

### 6.3 Two negative controls, and which layer caught them

A cheap plan is worthless if it is also cheap to be wrong. So two perturbed
levels were pushed through the **unmodified** transfer arm
(`cold-start-a3/a3pipeline/negctl.py`), each breaking the portal in a way the
carried domain does not know about:

* `a3-l2-oneway` — the portal's B→exit_b leg is deleted. The level becomes
  unsolvable; reachable states drop from 63 to 34.
* `a3-l2-rewired` — the B leg still fires but lands the Cart on a different
  cell. The level stays solvable, in 15 steps.

Both were caught, and neither claimed a win
(`cold-start-a3/artifacts/negative_controls.json`: `all_caught: true`,
`none_claimed_a_win: true`). **Which layer caught them is the result.**

| layer | `a3-l2-oneway` | `a3-l2-rewired` |
|---|---|---|
| first frame vs honest L2 | byte-identical | byte-identical |
| static certify (frame 0, 0 actions) | **green**, 0 anomalies | **green**, 0 anomalies |
| plan | SAT, length 10 — the same plan | SAT, length 10 — the same plan |
| execute | 10 actions, no win | 10 actions, no win |
| replay certify | **red**: 13 anomalies, 8 of 891 pixels unexplained | **red**: same figures |
| Lean | green | green |

The free half of the valve saw nothing. The static check reads the board, and
neither control touches the board; Lean re-proved a domain that was still
internally consistent. Only replay — which costs plan-length actions and arrives
only *after* acting — could see that the transition function had changed. The
report states the consequence plainly (`cold-start-a3/A3_REPORT.md` §5):

> Carrying a domain to a new level buys a plan for zero actions and buys **no
> free assurance that the plan is valid**; the assurance costs plan-length
> actions and arrives only after the fact.

That is the honest shape of the C3 saving. The induction is free; the
verification is not, and it cannot be moved earlier.

What a caught control produced here is a theorize *trigger*, not a repair.
`cold-start-a3/artifacts/negative_controls.json` records `theorize_triggered: true` for both, and A3 did
not run the resulting round — the report is explicit that it does not imply
otherwise.

### 6.4 What the blind control measured instead

The blind arm's manual and L1's agree on **0 %** of clauses as written, and on
all 20 of L1's clauses once canonicalised — plus 8 the blind arm added, which
neither level's geometry can witness and which its author flagged as his most
extrapolated clause before being asked
(`cold-start-a3/artifacts/domain_agreement.json`; `cold-start-a3/A3_REPORT.md` §4). The gap is
not noise:

> The gap between 0 % and full agreement is not noise — it is a measurement of
> **how much of a manual is convention rather than content**, and it is most of
> the surface.

The blind arm also spent 5 theorize rounds to the cold start's 1
(`cold-start-a3/artifacts/bill_table.md`), and the report records that two of
those five — 40 % of its adjudication budget — went to toolchain conformance
rather than to the world (`cold-start-a3/A3_REPORT.md` §4).

### 6.5 What A3 does not show

Six items, from `cold-start-a3/A3_REPORT.md` §6, and they bound the claim
tightly:

1. **Levels, not games.** A3 says nothing about carrying a domain between games
   with different mechanics. Outside the containment condition — every guard
   context L2 needs was witnessed in L1 — the carried domain is *missing a
   clause*, and the failure mode is the negative controls', not graceful
   degradation.
2. **Three level constants were supplied, not derived** — the goal cell and the
   two portal exits, handed to all three arms alike. Six of nine fields came from
   the frame; three did not.
3. **100 % sweep coverage is not realistic**, so the cold-start column is an
   upper bound on evidence rather than a forecast. A cheaper cold start would
   make the transfer ratio larger, not smaller.
4. **The bill is structural, not economic.** It counts frames, actions, engine
   stages, candidates, rounds and clauses. It does not count wall-clock or
   tokens, and the model calls behind the theorize step are the single largest
   term in a real C3 bill. The zeros are real and the right shape; converting
   them to money is not something this experiment did.
5. **Scale** — 62 and 63 reachable states, with `decide` enumerating the whole
   space.
6. **The theorize step is a person**, here as in A0 and A2. The blind control
   addresses the specific risk that the same person remembered L1's answer; it
   does not turn theorize into a measured component.

Two further caveats belong beside the numbers. The planner was the bundled BFS
stub rather than Fast Downward (`plan.backend: "stub-bfs"` in every artefact),
which is optimal for unit costs and so leaves `SAT`/`UNSAT` and plan length
sound. And **the playbook's transfer is a design claim, not a measurement**: the
manual's carry is mechanised and asserted by tests, but no code path in A3 reads
or compiles `cold-start-a3/theory/playbook.dsl`, and the byte-identity test its docstring cites
does not exist in the tree. We report the manual as carried and the playbook as
declared.

### 6.6 An incident, and four defects the run found in its own instrument

The blind was **partially broken, by us**, and is recorded as an incident
(A3-I1, `cold-start-a3/DECISIONS.md`). In round 3, while diagnosing a Lean
failure, the blind arm's holder read the docstring of a module the arm was
required to call, and that docstring names the Switch, the Door and the latch
law. The arm disclosed it unprompted and proposed the remedy. The recorded scope:
object and law *names* are contaminated, so no naming agreement is claimed; every
verdict was fixed in round 1, two rounds earlier, and rounds 2–4 changed none;
and the convergence result quotes only the preserved `as_written` snapshot.

The run also found four defects in the toolchain it was using, of which two are
worth the reader's attention because they are unsoundness rather than
incompleteness: the PDDL backend cannot encode more than one portal and returns
a confident **UNSAT for a correct manual**; and a Lean invariant helper keyed on
object *name* silently degrades to `I := true`, at which point every theorem
passes with an empty axiom list and the artefact proves nothing. The vacuous
Lean output is kept in the tree, at `cold-start-a3/theory/generated_l1_vacuous/`,
precisely so that an empty axiom list is not read as a guarantee on its own.
