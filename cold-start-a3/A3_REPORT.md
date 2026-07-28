# A3_REPORT — C3 offline: what the domain carries, and what it does not

**Verdict: C3 holds on this world, in the strict sense Theoria §1.10a defines,
with four bounds stated in §6 and one of them serious.**

The two books written for level 1 were carried to level 2 unchanged.  Level 2
was rebuilt from **one frame**, planned, and won, with **no engine run, no
candidate read, no theorize round and no clause written**.  Both negative
controls — a carried domain against a world whose transition function was
edited — were caught, and neither claimed a win.

`python run_all.py` is green; `python -m pytest` is 33 passed.  Every number
below is generated into `artifacts/` by the run and is not typed into this
file.

---

## 1 · What was actually claimed, and what was actually built

C3 in Theoria's Phase 3 claim menu reads:

> C3 迁移：携两本书跨关，第二关边际成本 ⟨≪⟩（条件性，视关卡共享机制程度，Phase 1 核实）

Two things about that sentence set the experiment.  It is **conditional on how
much mechanism the levels share**, so the sharing has to be a controlled
variable rather than a hope; and §1.10a fixes what "carry" means:

> 说明书是 domain(跨关不变)，关卡布局是 problem(逐关实例) —— C3"迁移"的严格含义就是 domain 带得走。

So the unit under test is a **level**, not a game (D-A3-001), and the artefact
under test is a **file**.

The world is 9×9 with four mechanisms — push; a toggle Switch that drives a
Door in the same transition; a two-way portal pair; a goal cell — and two
layouts that **share no placed cell**: different walls, cart start, switch,
door, both portals, both exits, goal.  `tests/test_world.py` asserts the
disjointness field by field rather than leaving it to the drawing.

Two properties of the pair are load-bearing, and both are tests:

* **Level 2 wins through the portal leg level 1 never uses.**  Level 1's
  solution goes A → exit_a; level 2's goes B → exit_b.  A manual that had only
  recorded the leg its own level needed would fail on the other, so the carried
  domain's success is a claim about induction and not about repetition.
* **Every rule-generating guard context level 2 presents was witnessed in level
  1**, and level 1 witnessed three that level 2 does not need.  This is the
  "视关卡共享机制程度" condition, made into a checked containment instead of a
  qualitative judgement.

That containment is the honest statement of the condition under which the
result below holds, and §6 says what happens outside it.

---

## 2 · The bill

From `artifacts/bill_table.md`, generated from the meters.

| meter line | L1 cold start | **L2 with the books** |
|---|---|---|
| `world_frames` | 348 | **11** |
| `world_actions` | 347 | **10** |
| `engine_stages` | 1 | **0** |
| `candidates_adjudicated` | 41 | **0** |
| `theorize_rounds` | 1 | **0** |
| `dsl_clauses_written` | 23 | **0** |
| `compile_runs` | 1 | 1 |
| `certify_runs` | 3 | 3 |
| `plan_runs` | 1 | 1 |

**The bottom three lines are the honest part of this table.**  Compiling,
certifying and planning cost *exactly the same* on both arms, and they should:
carrying a domain does not make a level cheaper to compile or a plan cheaper to
check.  What collapses is everything upstream of the manual — the evidence, the
engines, the adjudication, the authoring.  A table that showed savings on all
nine lines would be measuring something other than transfer.

### Cost to first plan

The snapshot taken the instant a plan first existed — Theoria's C2 is about the
*shape* of a bill over time, and a total cannot show a shape.

| | L1 cold start | **L2 with the books** |
|---|---|---|
| frames | 333 | **1** |
| actions | **332** | **0** |

**The transfer arm reaches a plan having spent zero actions.**  On a live game
an action is quota, so this is the line that would appear on an invoice.  The
cold-start arm must spend its entire exploration budget *before* it can plan;
the carried arm plans first and spends 10 actions executing.  The 347 → 10
ratio is the headline, and the 332 → 0 is the one that matters.

---

## 3 · "The domain travels" as an artefact you can diff

The strongest available form of the claim is not a number.  Both levels'
`theory.py` is generated from the **same** `theory/domain.dsl`.  Diff them:

* `LANDMARKS` — the two portal exits
* `BOARD` — the walls
* `is_goal` — the bound goal cell
* `initial_state` — where the Cart, Switch and Door start

and **nothing else**.  Every guard function and every effect function is
byte-identical, which `tests/test_transfer.py` checks line by line and again by
extracting the mechanism functions and comparing them directly.  A 35-line diff
between two working predictors, all of it level data.

Three things make that possible, and only one of them was designed in:

1. **`theory/domain.dsl` contains no coordinate.**  Not as a matter of style —
   the miner *offered* coordinates (`!at(3,1)`, `!at(5,1)`, in four proposals)
   and they were rejected on the record (THEORIZE_LOG R-08).  The
   domain/problem leak does not arrive as a section; it arrives as an atom
   inside a guard.
2. **The event language makes the level-specific reading unwritable.**  The
   miner proposed the eight teleports as ground displacements — four different
   vectors per portal, all landing on one cell.  `moved` carries exactly one
   cell and `jumped` carries a *landmark*, whose value the contract assigns to
   the problem instance; there is no form for "displace by (−1,+3)".  So the
   only expressible reading of a non-adjacent move is the portable one.  This
   was not anticipated and it is the most interesting thing A3 found about the
   framework: the domain/problem split is usually described as a discipline,
   and in the **effect** language it is an enforcement.  The **guard** language
   offers no such protection — see point 1.  The two halves are not equally
   safe.
3. **Level 1's evidence cannot distinguish the two readings at all.**  Same
   transitions, same predictions, zero residual, and `probe_frontier` cannot
   manufacture a separating experiment inside one level because separating them
   requires a portal somewhere else.  Level 2 is what decides it: the carried
   manual predicts cells it has never seen, and the replay agrees frame for
   frame.

### The carried manual is not merely consistent — it is correct

The transfer arm's replay is green over the 11 frames it executed.  That is the
right check to *run* in the field, and a weak measurement: 10 transitions could
be green by luck.  The referee can ask the stronger question, and
`a3world/score.py` does — for **every reachable (state, action) pair** of the
level, does the manual predict what the world does?

| manual | level | pairs | accuracy |
|---|---|---|---|
| `generated_l1` | level 1 — induced from it | 248/248 | **1.0000** |
| `generated_l2` | level 2 — **carried, never explored** | 252/252 | **1.0000** |

**252 of 252, on a level the manual never saw.**  A0 scored 233/236 this way
and found three errors that full-history replay could not see; the same
instrument on the carried manual finds none.  This is the claim at its
strongest: the domain that travelled is not approximately right on the new
level, it is exactly right on all of it.

The scorer lives in `a3world/` and not in `a3pipeline/`, because it needs the
transition function.  No arm imports it and no arm's result depends on it; it
runs after the arms are finished, which is what "truth is the referee's" means
operationally.

### The playbook travels too

C3 is stated over *two* books.  A manual that travels while the playbook must
be rewritten every level is a much weaker result than the claim, so
`theory/playbook.dsl` is held to the same standard and carried unchanged.  What
makes it portable is the same discipline that makes the manual portable: every
entry is written in the manual's vocabulary and cites the clause it depends on
— `press_before_door` names the Door and the Switch, which exist in both
levels, not `(6,7)` and `(3,1)`, which exist in one each.

One precision worth stating: the playbook entry travels, but **its proof
obligation is re-discharged per level**, because `decide` enumerates that
level's reachable states.  Re-checking is mechanical; re-deriving would need
evidence.  That is the honest shape of the claim and it is cheaper than
re-deriving by exactly the difference the table above measures.

---

## 4 · The control arm — the same level, done the hard way

There is one serious objection to everything above: **the person who carried
the books to level 2 is the person who wrote them for level 1, and they already
knew the answer.**  A2 faced the same objection about its repair and answered
it with three checks rather than with "trust us".  A3's answer is a control
arm, and the control arm's independence is structural rather than promised.

`theory/domain_l2_scratch.dsl` was written **blind**: from level 2's own
candidate stream, by a worker with no access to `theory/domain.dsl`, to
`THEORIZE_LOG.md`, to this report, to `a3world/`, or to the referee's copy.
The blind constraint was stated as absolute and its holder confirmed compliance
explicitly, disclosing the two files they read beyond the brief (both about the
backend's guard vocabulary, neither about this world).

**The blind was partially broken, by us, and it is recorded as an incident.**
In round 3, diagnosing a Lean failure, the control arm's holder read the
docstring of `a3pipeline/compile_a3.switch_latch_invariant` — a module the arm
was *required to call* — and that docstring names the blinded manual's objects
(`Switch`, `Door`) and its law.  The arm disclosed the read unprompted and
recommended the remedy itself.  `DECISIONS.md` **Incident A3-I1** has the full
account.  What it means for this section:

* **No agreement on names is claimed**, and none is used as evidence.
* Every verdict was fixed in **round 1**, two rounds before the read, and
  rounds 2–4 changed none.
* Everything quoted below is the **`as_written`** comparison — the manual as it
  stood *before* round 3, with `Agent`, `Gate`, `warp_a_exit`, `warp_b_exit`
  and seven lifted schemas.  It is preserved at
  `artifacts/finding_r09_blind/domain_l2_scratch_lifted.dsl`.

### The two manuals agree on the world and disagree about everything else

`artifacts/domain_agreement.json`, generated by `a3pipeline/agreement.py`,
which reports both states side by side.

| | |
|---|---|
| clauses written — level 1 / blind | 20 / 7 |
| **strict** agreement (rules as written) | **0 %** |
| **canonical** agreement (meaning) | **all 20 of level 1's clauses**, plus 8 the blind arm added |
| invariants, canonical | **identical**: `count(MOVER) = 1`, `count(BARRIER) + count(TOGGLE,8) = 1` |
| `semantics:` | identical on all three statements |
| goal section | neither has one |

**Zero percent, strictly.**  The blind author called the mover `Agent`, the
door `Gate`, the landmarks `warp_a_exit` / `warp_b_exit`, and wrote seven
`?dir`-lifted schemas where level 1 writes twenty ground clauses.  Not one rule
matched textually.  Once naming is quotiented by **role** (what a rule *does*
to an object), landmarks by the **guard colour** that reaches them, and lifted
rules are expanded into their ground instances, every one of level 1's twenty
clauses is present in the blind manual.

The gap between 0 % and full agreement is not noise — it is a measurement of
**how much of a manual is convention rather than content**, and it is most of
the surface.  Anyone planning to compare two induced manuals mechanically
should expect to build the quotient first.

The two arms also converged on three judgements nobody prompted:

* both **rejected every no-op rule** on `semantics: frame persist` — 12 of them
  on level 1, 15 on level 2;
* both **rejected every guard containing a literal cell** on the domain/problem
  split, before any evidential question.  The miner offered coordinates to both;
  neither took one;
* both read the non-adjacent moves as a **landmark**, not a displacement, and
  the blind arm rebuilt the transition table itself to check that six
  displacements produce exactly two destinations.

### Where they differ, and which one is wrong

The blind manual has **8 clauses level 1's does not**: the Switch toggle in the
`left` and `right` directions.  Neither level's geometry can witness those —
both switches sit in an alcove walled on the horizontal — and the blind author
flagged the lift as *"my most extrapolated clause"* in their own log before
anyone asked.

So the disagreement is entirely one-sided: **level 1's manual is the
conservative one, and the blind manual over-generalises in a direction no
evidence in either level reaches.**  Both are consistent with all the evidence
either arm holds.  This is R-05's situation again — two readings, no experiment
inside the available levels that separates them — and it is recorded rather
than resolved.

### The control arm's bill, and the extra round it paid

The blind manual's first version **did not compile**:

    compile.gen_python_a0.UnsupportedClause: moved(o, dir)

`gen_python_a0`'s guard and effect subset takes a literal direction, so the
lifted form compiles to nothing.  This is `THEORIZE_LOG.md` R-09 — level 1's
manual avoided it only because its author already knew the limitation and wrote
twenty ground clauses while recording that the miner's single lifted rule, at
225/225, was the better answer.

**Given the same evidence and no knowledge of the backend, an independent pass
reached for the lifted form too.**  That makes R-09 sharper than either pass
could alone: the rule the compiler cannot express is not a stylistic preference
that happens to collide with a backend limit, it is the reading description
length recommends and the miner itself proposes.  The failed manual is kept at
`artifacts/finding_r09_blind/` with the error and the pre-grounding comparison.

The control arm was then told the toolchain limitation — a fact about the tool,
which level 1's arm also had, and not a fact about the answer — and ground its
rules.  That transcription cost a **theorize round**, and the round is charged
to the control arm's bill rather than being quietly absorbed, because it is a
real cost of the framework's current expressiveness.

A second conformance round followed, for the object names (D-A3-008), and the
control arm's log records that **two of its five theorize rounds — 40 % of its
adjudication budget — went to toolchain conformance rather than to the world.**
That is a number worth having, and it belongs to the arm that had to author a
manual at all.

### The like-for-like table

Same level, same supplied constants, same certify, same planner.  Only the
books differ.  From `artifacts/bill_table.md`.

| meter line | L2 from scratch | **L2 with the books** | ratio | saved |
|---|---|---|---|---|
| `world_frames` | 347 | **11** | 0.032 | 336 |
| `world_actions` | 346 | **10** | 0.029 | 336 |
| `engine_stages` | 1 | **0** | 0 | 1 |
| `candidates_adjudicated` | 35 | **0** | 0 | 35 |
| `theorize_rounds` | 5 | **0** | 0 | 5 |
| `dsl_clauses_written` | 33 | **0** | 0 | 33 |
| `compile_runs` | 1 | 1 | 1 | 0 |
| `certify_runs` | 3 | 3 | 1 | 0 |
| `plan_runs` | 1 | 1 | 1 | 0 |

**This is the number C3 is about**, and it is stronger than the cross-level
comparison in §2 because it holds the level fixed: 97 % of the evidence, all of
the engine work, all of the adjudication and all of the authoring, removed by
carrying two files.  What is *not* removed is the mechanical tail — compiling,
certifying and planning cost exactly the same — and a table that showed savings
there would be measuring something other than transfer.

Both level-2 arms won, both certify green, and both planned in 10 — the
referee's shortest.  The control arm's manual also scores 252/252 against the
referee.  Two manuals, disjoint evidence, same level, both exactly right.

---

## 5 · The safety valve: would a wrong carried domain be caught?

A transfer result is worth nothing without this.  "The books worked" is only
informative if books that *should* fail do fail.

Both controls are level 2 with **one mechanism edited** and are constructed as
overrides of `L2`, so every level constant is inherited and the rendered first
frames are **byte-identical** to level 2's — a test asserts it.  The edit is in
the transition function.  And both were run through the **transfer arm
unmodified**: same domain file, same problem builder, same compile path, same
certify calls, same executor.  A negative control implemented by a separate
code path would be testing a separate code path.

| | `l2-oneway` — leg deleted | `l2-rewired` — leg lands elsewhere |
|---|---|---|
| the world | **unsolvable** | solvable in 15 |
| static certify (frame 0, free) | GREEN | GREEN |
| plan | SAT | SAT |
| execute | 10 actions | 10 actions |
| replay certify | **RED** | **RED** |
| theorize triggered | yes | yes |
| **claimed a win** | **no** | **no** |

**The free half of the valve is blind and the paid half catches both.**  The
static check — the cheap layer against a one-row trace built from frame 0 —
verifies render, responsibility and the goal predicate before a single action
is spent, and it is genuinely useful: a domain that does not fit the new level
at all is caught for nothing.  But it reads the *board*, and neither control
touches the board.  Only the replay, after acting, can see a transition
function that changed.

That boundary is the result, and it is not the flattering version.  Carrying a
domain to a new level buys a plan for zero actions and buys **no free
assurance that the plan is valid**; the assurance costs plan-length actions and
arrives only after the fact.  The two controls are also not the same test:
`l2-oneway` is the dangerous case, because the level is unsolvable and a
pipeline that failed to notice would have reported a **win that never
happened** — Theoria §1.3's failure, every gate green and the conclusion false.

What a caught control produces here is a **theorize trigger**, not a repair.
The arm stops with `theorize_triggered: true` and the mismatching frame on the
record.  Turning that into a corrected manual is the 定位 → 戳探 → 修订 loop,
and `cold-start-a2` ran it end to end on a different defect.  **A3 did not run
it**, and this report does not imply otherwise.

---

## 6 · What A3 does not show

**Levels, not games.**  The two levels share a mechanism set by construction.
A3 says nothing about carrying a domain between games with different mechanics,
and the containment check in §1 is the exact boundary: every rule-generating
guard context level 2 needs was witnessed in level 1.  Outside that containment
the carried domain is *missing a clause*, and the failure mode is the negative
controls', not a graceful degradation.  This is the weakest interesting reading
of C3 and it is the one Theoria's own wording licenses; anything stronger needs
a different experiment.

**Three level constants are supplied, not derived.**  The goal cell and the two
portal exits are handed to every arm — the cold start, the control and the
transfer arm alike, so the comparison isolates the rules.  They are supplied
because they are not in the pixels: the goal is not rendered (D-A3-002) and a
portal exit is plain floor (D-A3-003).  The contract already assigns landmark
coordinates and the goal to the problem instance, so this is conformant rather
than a concession invented here — but it *is* three fields the arm did not have
to work out, and `artifacts/provenance_l2_transfer.json` records the split
field by field: **6 derived from the frame, 3 supplied**.  A world whose goal
and exits were visible would move those three into the derived column; a live
game where they are not would charge for discovering them.

**100 % sweep coverage is not realistic.**  Level 1's explorer is an edge cover
and visits every reachable (state, action) pair.  No live game affords that.
The effect on the result is conservative rather than flattering — a cheaper
cold start would make the transfer ratio *larger*, not smaller — but the
absolute cold-start numbers are an upper bound on evidence, not a forecast.

**The bill is structural, not economic.**  Wall-clock and token counts are not
recorded, because neither is reproducible on this box and determinism is a
repository-wide requirement (D-A3-009).  A3 measures frames, actions, engine
stages, candidates, rounds and clauses.  It does **not** measure what the
theorize step cost in model calls, which is the single largest term in a real
C3 bill.  The zeros in the `theorize_rounds` and `dsl_clauses_written` columns
are real and they are the right shape, but converting them to dollars is not
something this experiment did.

**Scale.**  62 and 63 reachable states, `decide` over the whole space.  A world
needing a genuinely clever pagoda is what A1 is for.

**The theorize step is a person, here as in A0 and A2.**  A3 tests the
instrument, the split and the bill's shape — not whether an LLM would have
written these manuals.  The control arm mitigates the specific risk that *this*
person remembered level 1's answer (§4), but it does not turn the theorize step
into a measured component.

**`fd_adapter` is still the bundled BFS stub**, not Fast Downward.  Optimal for
unit costs, so `SAT`/`UNSAT` and plan length are sound here; the standing caveat
in `engine-rig/STATUS.md` is unchanged.

---

## 7 · Four defects found in the reused instrument

A3 writes no engine and no generator.  Running the borrowed instrument on a
world with **two portals, a toggle instead of a latch, and a domain with no
`goal:` section** found four things the two earlier spikes could not have seen.
All four are in `DECISIONS.md` and on `PARTNER_SYNC.md`; none was fixed in
place.

**D-A3-003 — `mdl_segmenter` loses the mover when it lands on a marked cell.**
The first version of this world made each portal's exit the other portal's
cell, so both landmarks could be read straight off frame 0.  The segmenter
matches frame *t* against *t+1* only, so the cheaper script is "the resident
recolours to 6" plus "the mover vanishes".  Measured: the mover's track absent
in **19 of 326 frames**, and appear/vanish rules proposed instead of a jump.
Run kept at `artifacts/finding_d_a3_003/`.  Third segmentation gap in this
family, after touching objects and A0′'s re-identification.

**D-A3-004 — three of the four co-derived forms do not honour the
domain/problem split.**  The contract's own expressivity boundary lists
`word_table` + `semantics` + `rules` + `laws` as the domain and puts layout,
initial state and landmark coordinates in the problem.  `goal` is in neither
list, and the backends disagree: PDDL falls back to `problem.goal_cell`
correctly, Python emits `is_goal: return False` **silently**, and Lean then
raises.  So a coordinate-free domain — the only kind that can travel — compiles
to a predictor that can never win, and the cheap layer reports it as
`goal_mismatch` anomalies, which reads like a wrong manual rather than a
missing binding.  A3 supplies a binder.  Confirmed by negative control, not
merely asserted: with the AST unbound, `generate_lean` raises `no arena cell
satisfies the manual's goal`.

**D-A3-005 — the PDDL backend cannot encode more than one portal.**
`_action_jump` emits a single global `(portal-exit ?dest)` shared by every jump
action, and the problem emits that fact **only for a landmark literally named
`portal_exit`**.  With `exit_a` and `exit_b` this is wrong twice: no fact is
emitted, so the planner returns a confident **UNSAT for a correct manual** with
no warning; and even with the fact present, both jump families would draw from
one destination set, so a plan could legally jump from portal A to `exit_b`.
That is unsound, not incomplete.  A2 found the neighbouring arena defect on a
world with one portal — one portal is exactly the case where this one is
invisible.  A3's patch also closes the **entry** side, which was beyond the
brief: one shared `markedcell` type lets `teleport-a-*` ground on portal B.

**D-A3-007 — the Lean invariant helper is keyed on the object's *name*.**
`door_latch_invariant` looks for an axis literally called `Button_colour`.  A3's
toggle is called `Switch`, so the helper returns `None` and `generate_lean`
falls back to `I := true` — a file whose `inv_init`, `inv_closed` and `inv_all`
all pass, whose `#print axioms` list is **empty**, and which proves nothing.
Every gate in the certify column green.  A3 passes an explicit builder and
**keeps the vacuous version** at `theory/generated_l1_vacuous/` so the pair can
be diffed.  A2 had to build a false-but-green certificate deliberately, out of
a holed manual; this one arrives from an object-naming convention, which is
worse.

---

## 8 · An unplanned result: reversibility flips the concept account

A0's finding O-04 is that constraint 5 (compression) and constraint 2
(responsibility-completeness) can point in opposite directions: A0's Button and
A2's Button and Door had to be admitted to the word table at a **negative**
compression account (−5 and −1 in A2) and justified on other grounds.

A3's three objects all pay for themselves — Cart **+2371**, Door **+8**, Switch
**+7** (`artifacts/concept_accounts.json`).  The cause is mechanical: a latch
fires once, so an object declared to explain one event costs more than it
saves, while A3's Switch is a **toggle** and recolours dozens of times.

Reversibility was adopted for an unrelated reason — monitor finding F-12, from
A0′: *reversibility beats coverage*, because an irreversible mechanism caps
what any amount of exploration can establish.  That it also flips the sign of
the concept account was not predicted.  The consequence is worth stating
plainly: **A0's O-04 conflict is contingent on irreversibility, not intrinsic
to the two criteria.**  A framework-level claim that quietly depends on a
world-design choice should not stay quiet.

The same F-12 decision is load-bearing twice more in this spike.  It is why
level 1's manual has both portal legs — the winning path uses only one, and the
sweep witnesses the other only because the world can be walked backwards — and
level 2 wins through the leg level 1 never needed.  Had the world been
irreversible, transfer would have failed, and the failure would have looked
like a fact about C3 rather than a fact about level 1's exploration.

---

## 9 · Red lines held

* **Zero API calls, zero network, zero contact with the sealed pile.**  The
  world is self-built.  `tests/test_sealing.py` scans every shipped file for
  network imports, for the credential name, and for every sealed game id in
  `arc-recon/data/piles.json` (full and short form).
* **Truth reaches the pipeline only as frames.**  No `a3pipeline` module
  imports a world module or names `A3World`; a test enforces it byte-wise.  The
  one bridge is `a3world/executor.py`, an environment proxy shaped like a game
  API: hand it a level name and actions, get frames back.
* **The transfer arm's claim is a property of its call graph.**  A claim about
  what an arm did *not* read cannot be evidenced by the arm's own report, so
  `test_the_transfer_arm_cannot_reach_a_level_2_trace` reads the source and
  fails if it so much as mentions a sweep file, a candidate stream, or the
  engine stage.
* **The other tracks are read-only.**  `python -m tools.verify_readonly` hashes
  every file under `cold-start-a0`, `engine-rig`, `theory-compiler` and
  `CONTRACTS`, runs the whole pipeline, and hashes again.
* **The frozen contract is untouched.**  Every candidate stream validates
  against `CONTRACTS/candidates_schema.md`, every row's `status` is
  `"candidate"`, and `git status CONTRACTS/` is clean — asserted by a test.
* **Generated forms are never hand-edited.**  `theory/generated*/` is compiler
  output; `theory/*.dsl` is the only thing written by hand.
