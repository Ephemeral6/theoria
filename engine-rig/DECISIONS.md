# engine-rig · DECISIONS

Design calls made without asking, per the ticket's standing instruction: pick the
most conservative option consistent with the frozen contract and the acceptance
criteria, record why, keep going.

---

## D-001 · Trajectory JSONL carries a final frame with `action: null`

**Context.** The ticket fixes Fixture A's line format as
`{"frame": <2D array>, "action": "<UP|DOWN|LEFT|RIGHT>"}`. A trajectory of N
frames has only N-1 actions, so the format is one field short of describing the
last frame.

**Decision.** Emit N lines. Line t holds frame_t and the action applied at t;
the last line holds frame_N-1 with `"action": null`.

**Why.** The alternative (emit N-1 lines and drop the final frame) discards a
real observation and would make the last transition unavailable to the miners.
Adding a null action loses nothing and keeps one line == one frame. Fixture B
follows the same convention.

---

## D-002 · The push guard is mined in its general form (`in-bounds AND empty`)

**Context.** Fixture A holds exactly one object, so on this board "the target
strip is inside the grid" already implies "the target strip is empty" — the two
predicates are extensionally equal over the observed transitions.

**Decision.** Ground truth and the mined guard both use `free(strip(D))` =
in-bounds AND all-background. `cegis_miner` treats `in_bounds` and `empty` as two
distinct atoms and reports both when they are indistinguishable, rather than
silently picking one.

**Why.** Picking one would be an unjustified commitment; the honest output on
indistinguishable atoms is the frontier containing both. This is exactly the
situation `probe_frontier` exists to resolve, and it keeps the two engines
consistent about what "not yet decided" means.

---

## D-003 · Fixture B scripts every adjacent pair before random actions

**Context.** The GF(2) null space recovered by `zero_space` depends on which
difference vectors were observed. If a pair never fires, the observed difference
space is smaller and the recovered invariant space is correspondingly larger
(still sound, but weaker than the ground truth `(#Red) mod 2`).

**Decision.** The first 7 actions walk through all 7 adjacent pairs once; the
remaining 33 are seeded-random.

**Why.** The acceptance criterion asks for equivalence to `(#Red) mod 2`, which
requires the observed differences to span the whole even-weight subspace. Making
that a property of the fixture rather than of a lucky seed is the conservative
choice. `zero_space` itself makes no assumption about which pairs appear.

---

## D-004 · `id` and `timestamp` are non-deterministic by default, pinnable by env

**Context.** The frozen contract mandates a uuid `id` and an ISO8601 `timestamp`
on every candidate. Both break byte-level reproducibility of `candidates.jsonl`.

**Decision.** Default behaviour is uuid4 + wall-clock UTC, exactly as the contract
reads. Setting `THEORIA_FIXED_TIME=<ISO8601>` and `THEORIA_DETERMINISTIC_IDS=1`
switches to a frozen timestamp and to uuid5 over the candidate's content hash.
Tests and `tools/run_all.py --deterministic` use the pinned mode.

**Why.** The contract is frozen and must be honoured literally in normal
operation; reproducibility is a test-harness need, so it lives behind an opt-in
switch rather than in the emitted format. M1's "same seed, same bytes" applies to
fixtures, which carry neither ids nor timestamps.

---

## D-005 · MDL cost model is an explicit bit-counting scheme, published in the README

**Context.** "Total edit-script length significantly shorter than a per-pixel
baseline" needs a code length both sides are measured in, or the comparison is
rigged by whoever picks the units.

**Decision.** One bit-counting scheme (`engines/mdl_segmenter/README.md`) prices
both the object/event script and the per-pixel baseline. Both pay the same
per-transition header and neither is charged for the initial frame; they differ
only in how each transition's content is encoded. The acceptance threshold is a
ratio (script <= 0.5 x baseline), not an absolute number. Measured on Fixture A:
826 vs 2888 bits, ratio 0.286.

**Why.** Sharing the header and skipping the initial frame on both sides removes
the easiest way to fake a win. Fields are fixed-width, and hand-auditable, with
one exception recorded as D-011.

---

## D-006 · Rules are mined per (action, effect) class, then lifted to one schema

**Context.** The acceptance criterion asks for *two* rule_hypothesis candidates
("push" with high coverage, "teleport" with 1/1), but the guard that separates
"moves up" from "does not move up" is direction-specific.

**Decision.** CEGIS mines one guard per (action, effect) class — four push rules,
four blocked rules, one teleport rule — and then lifts the four push rules to a
single parameterised `push` schema when they are alpha-equivalent under the
direction substitution. Coverage of the lifted rule is the sum over directions.
Both the per-direction rules and the lifted schema are emitted as candidates.

**Why.** Lifting is the compression step the framework asks for (a rule about
`dir`, not four rules about four constants), but throwing away the ground-level
rules would hide the evidence the lift rests on. Emitting both costs nothing —
adjudication is the LLM's job, not this sprint's.

---

## D-007 · The LP certificate is verified exactly over the rationals

**Context.** `scipy.linprog` returns floats. A certificate that only holds up to
1e-9 is not a certificate.

**Decision.** The LP result is snapped to rationals (`Fraction.limit_denominator`)
and every certificate condition is re-checked with exact arithmetic. Only the
exact rational weights are emitted as a candidate. If exact verification fails,
the engine raises rather than emitting an unverified weight vector.

**Why.** This is the rehearsal of "upstream engines hand Lean a certificate, Lean
only checks" — a float certificate would push the search back into the checker.

---

## D-008 · The potential-based heuristic uses the max single-step potential change

**Context.** The pagoda weight w proves unreachability; the acceptance criterion
additionally wants it as an admissible heuristic with a lower bound that never
exceeds the true shortest path.

**Decision.** `h(s) = min over goal states g of ceil(max(0, w(g) - w(s)) / M)`,
where `M = max |w(s') - w(s)|` over all legal move instances in the state graph.

**Why.** Each move changes the potential by at most M, so reaching g needs at
least `|w(g) - w(s)| / M` moves — admissible by construction, no tuning. It is
weak (M is a worst case), which is the right direction to err: admissibility is
the requirement, sharpness is not.

---

## D-009 · Fast Downward: two discovery attempts, then a BFS stub behind the same interface

**Context.** The ticket permits a stub after two reasonable attempts to install
or call Fast Downward.

**Decision.** Both attempts failed (full log in `STATUS.md`: FD is not on PATH,
not in any of the usual locations, and not on PyPI in any form). The stub is in
use. The adapter exposes one function, `solve(domain, problem)`, and picks a
backend at call time;
the stub is a grounded-STRIPS breadth-first search, which is optimal for unit
costs, so the acceptance criterion ("plan length equals the hand-verified
optimum") means the same thing under either backend.

**Why.** Keeping one interface means the FD path can be switched on later without
touching callers or tests.

---

## D-010 · Plan validation is independent of the search that produced the plan

**Context.** Asserting "BFS returns length 5" against a BFS implementation is
close to circular.

**Decision.** The fd_adapter tests assert (a) the plan length equals a literal
hand-derived optimum documented in the engine README, and (b) the plan is valid
under a separate executor that applies each action to the state and checks the
goal — code that shares nothing with the search.

**Why.** A search bug that returns a too-short plan is caught by the validator; a
search bug that returns a too-long plan is caught by the literal.

---

## D-011 · Move displacement is Elias-gamma coded, not fixed-width

**Context.** The first cut of the cost model charged a fixed-width field per
displacement component. That makes every move cost the same number of bits.

**Decision.** A displacement component costs `1 + gamma(|d|)` bits (sign plus
Elias-gamma magnitude): 4 bits for a unit step, 8 for a jump of 8.

**Why.** Not a refinement for its own sake — with a fixed-width offset the
matcher is *indifferent* between "each block moved one cell" and "the two blocks
swapped identities", both being two move events of equal cost, so tracking is
ill-posed as soon as two look-alike objects share a board. Charging by magnitude
also prices the teleport honestly: 19 bits against a unit move's 9, i.e. the
rare long jump is the expensive thing to describe, which is exactly why it is
the informative one. Caught by the two-identical-blocks test, not by the Cart
fixture, which has only one object.

---

## D-012 · zero_space encodes (cell, colour) indicators, and canonicalises the basis

**Context.** The engine could be handed a "red count" feature directly, which
would make recovering `(#Red) mod 2` nearly vacuous.

**Decision.** The state is encoded as one indicator per (cell, colour) pair — 16
anonymous bits for Fixture B — and the recovered null space is then split into
*cell-local* laws (support inside one cell's feature group: "this cell holds
exactly one colour", i.e. facts about the encoding) and *global* laws (what is
left after quotienting those out).

**Why.** Feeding the engine the abstraction it is supposed to discover would be
testing nothing. The split is needed because the null space basis that falls out
of the elimination depends on which columns happen to be free, and left alone it
reports laws like `B@0+...+R@7` that are correct but unreadable. After
canonicalisation the world-level content of the space is a single law, and the
acceptance criterion becomes a subspace identity: `span(recovered) ==
span(cell-local laws + {target})` — satisfied by any equivalent linear
expression, including `(#Blue) mod 2`, and refused for an unrelated vector.

---

## D-013 · The LP minimises weight magnitude; the margin-maximising variant is rejected

**Context.** The certificate LP has many feasible vertices, and which one is
returned changes how sharp the derived heuristic is. An obvious alternative is
to normalise the largest single-move drop to 1 and maximise the certificate
margin.

**Decision.** Keep feasibility with a fixed margin >= 1 and an L1 objective on
the weights.

**Why.** The margin-maximising variant is feasible with the all-zero weight
vector at margin zero, so it returns a "certificate" for solvable configurations
too — it destroys the property that infeasibility means "no such proof exists".
Soundness is worth more than sharpness here: with the chosen formulation, the
only configurations that receive a certificate are the ones the enumeration
independently confirms are unsolvable, and 1101 (solvable) correctly gets none.
Tried empirically on Fixture C: the margin-maximising LP returns w = 0 for both
1101 and 0111.

---

## D-014 · Pagoda incompleteness is asserted by a test, not hidden

**Context.** Fixture C's configuration 0111 is unsolvable, and no linear
potential function proves it.

**Decision.** A test asserts exactly that: `0111` is unsolvable *and*
`solve_certificate` returns None for it.

**Why.** The method is sound but incomplete, and the incompleteness is a real
property of linear pagodas, not a bug to be quietly tuned around. Writing it as
a test means a future change that appears to "fix" it is forced to explain
itself.

---

## D-015 · The committed candidates.jsonl is the deterministic-mode run

**Context.** M8's candidate stream is checked into the repository at
`engine-rig/artifacts/candidates.jsonl`. The contract mandates a uuid `id` and a
wall-clock ISO8601 `timestamp` per candidate, both of which change on every run.

**Decision.** The committed copy is generated with `--deterministic` (frozen
timestamp, uuid5 over each candidate's content hash, per D-004). Ordinary runs
still default to real uuids and wall-clock time and write to untracked `out/`.
A test asserts the committed file is byte-identical to a fresh deterministic run.

**Why.** A committed artefact regenerated with wall-clock timestamps produces a
24-line diff every time anyone runs the engines, which makes it useless as a
reference: nobody could tell an incidental re-run from a real change in engine
output. Freezing the two non-substantive fields makes the file diff only when the
engines actually propose something different, and the byte-equality test stops it
going stale. The default emission path is untouched, so the contract is still
honoured literally in normal operation.

---

## D-016 · fd_adapter grounds by join, not by cross product

**Context.** The A0 sokoban domain's `push2` action mentions four cells. Grounding
it as a full cross product is |cells|^4 -- 5.7M combinations on a 7x7 board, and
23M with the direction parameter -- essentially all naming cells that are not
collinear. Grounding took 16 s and the whole solve 49 s.

**Decision.** Predicates that no action adds or deletes are *static*; their truth
is fixed by the initial state. Grounding now (a) discards any instance whose
static preconditions are false, (b) checks each static precondition the moment
its variables are bound, and (c) binds parameters in an order taken from the
static atoms themselves, so the check can fire early. Static atoms are also
stripped from the search state.

**Why.** Correct by construction -- a static atom false initially is false
forever, so no reachable plan is lost -- and the effect is not marginal:
grounding 16.4 s -> 0.03 s, solve 49 s -> 0.05 s, with identical output (254
ground actions, the same 2-action plan, the same "no plan" on the unsolvable
level). Ordering matters as much as the pruning: with the direction parameter
bound last, `adj ?p ?b ?d` cannot be checked until 49^4 partial bindings exist.

---

## D-017 · A second segmentation operator, chosen per world

**Context.** `mdl_segmenter`'s colour-agnostic connectivity fuses a player
standing against a wall, or beside the box it is about to push, into one blob.
The A0 trajectory is unreadable under it.

**Decision.** `connected_components(..., split_by_color=True)` refuses to cross a
colour change. Both operators stay; which one a world needs is recorded in that
world's manual.

**Why.** Neither is right everywhere -- colour-splitting shatters multi-coloured
objects, colour-agnostic fuses touching ones. This is the "segmentation operator
hypothesis space" of Theoria 1.8, and the honest form is a choice the manual
records rather than a default hidden in the engine.

---

## D-018 · Two new engines emit under the frozen enum, and name themselves in the payload

**Context.** `deadlock_carver` and `ic3_pdr` are rows seven and eight of Theoria
1.10(b)'s engine table. `CONTRACTS/candidates_schema.md` is frozen at v0.1, its
`engine` field is an enum of the six engines that existed when it was written,
and the contract says outright that neither track may modify the file.

**Decision.** The contract is not touched, and neither is
`tools/validate_candidates.py`, which is its executable form. Each new engine
emits under the enum member whose work it extends — `deadlock_carver` as
`fd_adapter`, `ic3_pdr` as `lp_potential` — and records its real identity in
`payload.producer`, a field the contract explicitly leaves to each engine's
README.

**Why.** Three options were on the table and two of them are worse. Adding enum
members unilaterally edits a file both tracks are forbidden to edit. Holding the
engines back until a v0.2 is negotiated blocks work on a coordination round-trip
that this repo deliberately does not have — the two tracks do not communicate.
What is left is to emit inside the contract as written, which costs one field of
indirection and no honesty: every line still validates, `payload.producer` is
never absent, and `run_all`'s `by_engine` histogram still shows exactly the six
frozen names, so nothing downstream is surprised.

The pairing is not arbitrary in either case. A deadlock theorem is a planner
artefact: it is carved out of a grounded PDDL task, it is expressed in the
search's own reduced atoms, and its second consumer is `fd_adapter.search`
itself. An IC3 invariant is precisely `lp_potential`'s unfinished business — it
answers the same question, reports the same three conditions
(`inv_init`/`inv_closed`/`goal_break`), and exists because the LP is infeasible
on `0111` (D-014).

This is flagged in `PARTNER_SYNC.md` rather than solved there. If the enum ever
opens, the change is one line per engine and the payload field can stay.

---

## D-019 · Deadlock patterns are capped at two atoms, matching the mutex width

**Context.** A dead pattern could in principle be any conjunction of ground
atoms, and wider patterns catch more deadlocks (the classic sokoban 2x2 block
needs four).

**Decision.** `MAX_PATTERN = 2`. The pattern enumeration stops at pairs.

**Why.** The proofs rest on h² mutexes, which are facts about *pairs* of atoms.
A three-atom pattern would be checked against evidence that cannot see it: h²
can tell you that atoms a and b never co-occur, but not that {a,b,c} is jointly
impossible while each pair is fine. The cap is therefore not a performance
budget that could be raised by waiting longer — it is the width of the evidence,
and widening it means implementing h^m, which is a different engine. Recording
it as a constant with that reason attached beats discovering later that
three-atom patterns were quietly being proved on two-atom grounds.

---

## D-020 · The pruning claim is reported as a node account, including where it is zero

**Context.** "Every deadlock proved speeds the planner up" (Theoria 1.9) is an
empirical claim, and the tempting way to support it is to pick the instance where
it looks best.

**Decision.** `pruning_report` solves the same instance twice, blind and pruned,
and reports both expansion counts plus whether the answer changed. Three
instances are measured and all three are in the engine README, including
`open4`, where sixteen true theorems save **zero** expansions.

**Why.** The zero row is the informative one: on `open4` the search finds its
6-action plan before wandering into a single dead region, which says something
true about when pruning pays — it pays where the search would otherwise go, and
most where the search must exhaust (the unsolvable instance, 44 → 22). Reporting
only `open4far`'s 808 → 571 would have made a conditional result look
unconditional.

The same mechanism doubles as the soundness alarm. An unsound theorem does not
show up as a suspiciously large speed-up; it shows up as a *changed answer*, so
`same_answer` is checked on every report and asserted in `run_all`.

---

## D-021 · IC3's converged frame is minimised before it is emitted, by a second implementation

**Context.** IC3 terminates when two adjacent frames describe the same states.
That frame is inductive but not minimal: clauses learned early survive
propagation even after later ones subsume them. On Fixture C's `0111` it comes
out as `(pos3) & (!pos1 | pos2) & (pos1 | !pos2)`, whose first clause is
redundant.

**Decision.** After convergence, drop clauses greedily while the set stays
inductive, and record `clauses_dropped`. The inductiveness test used for this
lives in `pdr.py` as its own function, deliberately duplicating what
`check.py::verify` does.

**Why.** The invariant is an artefact a human or an LLM adjudicates into a book,
not an intermediate value — `(!pos1 | pos2) & (pos1 | !pos2)` reads as
"positions 1 and 2 always hold the same thing", and the unminimised form does
not read as anything. The duplication is the price of D-010's discipline: if the
search called the checker, the checker would no longer be independent of the
search, and its verdict on the final answer would be worth less than the
duplication costs. A test asserts every surviving clause is load-bearing, so the
minimisation cannot silently stop working.

---

## D-022 · An unreachable probe configuration is emitted, not dropped

**Context.** Once probe configurations are handed to the planner, some come back
UNSAT. The obvious behaviour is to filter them out and rank what is left.

**Decision.** Unreachable configurations are emitted as `probe_design`
candidates with `tier: "hypothetical"`, `verdict: "unreachable"` and a null
cost, and they keep their entropy — `p_side` is a full bit that cannot be
bought.

**Why.** This is R-05's finding, reproduced by machinery instead of noticed by a
human afterwards: *the experiment that would settle this manual cannot be
performed on this instance.* Dropping it makes "no experiment settles this here"
indistinguishable from "nothing to propose", which is the difference between a
finding and a silence. It also keeps the engine from proposing impossible
experiments forever, since the verdict is the thing that stops the loop.

---

## D-023 · The planner is a three-rung ladder, and the Plan names its rung

**Context.** Theoria 1.10b asks for a ladder — exact object-state search, then
A* with an admissible heuristic, then landmark-based satisficing — not a switch
between "the stub" and "FD". With Fast Downward actually installed there are now
three real options, and callers must not have to know which one answered.

**Decision.** `stub-bfs` / `fd-optimal` / `fd-satisficing`, picked by
`backends.choose_tier` under a four-clause rule written in its docstring and
tested clause by clause with an injected discovery function. `solve(domain,
problem)` is unchanged. `Plan.backend` is the tier id and `Plan.search` carries
the configuration verbatim, both built by the same function that builds the
command line. Naming a rung that is unreachable raises `FastDownwardMissing`
rather than dropping to another one. A bare `downward` binary, which has no
driver and so no `--alias`, gets an explicit greedy-FF configuration and the
payload says so instead of claiming LAMA.

**Why.** A benchmark that quietly answers on a different engine than the one it
was asked for is a benchmark that lies. Every acceptance criterion in this rig
is a plan *length*, and a length only means the same thing on every machine if
the artifact records which rung produced it and whether that rung was optimal.
The satisficing rung reports `optimal: false` for exactly this reason: its
length is an upper bound and must never be read as an optimum.

---

## D-024 · A proof of unsolvability is decided on what the planner said, not on how it exited

**Context.** The cold-start-a0 track reported a real defect: on the FD path this
adapter could not tell "the planner proved there is no plan" — which starts the
certificate obligation and the whole unsolvability track — from "the planner
fell over", which is an incident. Both arrived as the same `RuntimeError`. The
obvious fix is to read the exit code, and both tracks assumed that would work.

**Decision.** It does not, and the rule is now `backends.proves_unsolvable`,
which reads FD's log as well as its exit code. Exit 10 (`TRANSLATE_UNSOLVABLE`)
and 11 (`SEARCH_UNSOLVABLE`) are proofs. Exit 12 is a proof **only** on the
optimal rung and **only** when FD reports `Completely explored state space`.
Everything else raises. On success the adapter returns the plan; on a proof it
returns `None`, exactly as the bundled search does, and `solve()` raises
`NoPlanExists(RuntimeError)` — a subclass, so callers written against the old
behaviour keep working.

**Why, and what the measurement showed.** Fast Downward's own
`driver/returncodes.py` reads `TRANSLATE_UNSOLVABLE = 10`, `SEARCH_UNSOLVABLE =
11`, `SEARCH_UNSOLVED_INCOMPLETE = 12`. But `SEARCH_UNSOLVABLE` is emitted only
by algorithms that detect unsolvability structurally (EHC, the PDB CEGAR loop).
A complete `astar(blind())` that exhausts the reachable state space of
`sokoban_ringstuck` — an instance `deadlock_carver` independently proves
unsolvable — exits **12**, printing `Completely explored state space -- no
solution!`. `--alias lama-first` exits 12 on the same instance. So the one code
covers both "I explored everything and there is nothing" and "I gave up", and no
reading of the exit code alone can separate them.

The refusal on the satisficing rung is deliberate and costs us something: LAMA is
a portfolio whose later iterations search under a cost bound, and "exhausted
under a bound" proves only that no cheaper plan exists. Telling those apart would
mean reasoning about which iteration wrote that line. Refusing costs a caller one
re-ask on the optimal rung; getting it wrong would mean this rig publishing an
unsolvability claim no planner actually made — the bare-UNSAT failure the
Theoria constraint exists to prevent.

---

## D-025 · The artifact path stays on the bundled rung

**Context.** `solve()` now climbs to Fast Downward whenever one is reachable.
`run()` is the path that writes `artifacts/candidates.jsonl`, which is committed
and must be byte-reproducible.

**Decision.** `run()` resolves an unspecified backend to `ARTIFACT_TIER =
"stub-bfs"`. Fast Downward on the artifact path is opt-in via
`prefer="fd-optimal"`. Verified: `tools/run_all --force` reproduces the committed
stream byte for byte both with `FAST_DOWNWARD` set and unset.

**Why.** Determinism here is a requirement, not a nicety. If `run()` discovered
the planner, the committed candidate stream would depend on whether the machine
that produced it happened to have one installed, and a diff would silently mean
"different laptop" instead of "different answer". The same discipline the
cold-start-a0 track adopted as D-A0-021, for the same reason. FD's independent
answers are recorded, but in their own artifact under `runs/`, where they cannot
contaminate the committed stream.

---

## D-026 · The bench never divides a STRIPS node count by a SAS+ one

**Context.** E2 asks for a nodes / wall-clock / optimality table across the three
rungs. The obvious table has a "nodes expanded" column per rung and a speed-up
ratio beside it.

**Decision.** `bench/` reports node counts per rung and **no cross-rung ratio**.
Cross-rung comparison is restricted to plan length and wall clock. The
prohibition is written into the artifacts themselves, as a field in `ladder.json`
and a line above the table in `LADDER.md`.

**Why.** `stub-bfs` expands grounded STRIPS states — frozensets of atoms, one
node per distinct set. Fast Downward expands SAS+ states, assignments to the
finite-domain variables its translator invents after merging mutually exclusive
atoms and discarding unreachable ones. On this rig's own gripper fixture that is
14 STRIPS facts against 5 SAS+ variables. "Fast Downward expanded 8 where the
stub expanded 18" therefore compares two different objects, and the ratio is
the single most quotable number the run could produce. Plan length survives the
translation (both rungs are length-optimal for unit costs) and a second is a
second on every rung, so those two are compared and the node counts are not.

---

## D-027 · Deadlock theorems reach Fast Downward as a task edit, not as a pruner

**Context.** Theoria 1.9 promises that every proved deadlock speeds up *the
planner*. `fd_adapter.search` takes a `prune` callable; Fast Downward does not,
and `choose_tier` clause 3 records that as a fact about the backend. So the
promise could not be tested on the rungs that actually plan.

**Decision.** `bench/compile_theorems.py` compiles the theorems into the PDDL
instead: an action is forbidden when its effect would produce a state containing
a proved-dead pattern. Two guards are emitted — `singleton` (corner deadlocks, a
negative precondition, still STRIPS) and `full` (adds pair deadlocks, needs a
universally quantified negated conjunction, hence `:adl`).

The compilation is **not** trusted. Every plan it produces is replayed against
the *original* domain by the rig's own validator, and on the optimal rungs any
change in plan length is reported as a soundness failure of the run.

**Why this preserves the answer.** A theorem says its pattern is closed and
excludes the goal, so every state containing it is dead. Forbidding the
transitions that enter the pattern removes only states from which no goal is
reachable: every original plan survives, and every plan of the compiled task is a
plan of the original. Plan existence and optimal length are therefore unchanged —
the same guarantee the pruner gives, obtained by editing the task instead of the
search.

**What it cost, and the limit found.** FD's translator compiles the `full`
guard's universal precondition into an **axiom**, and `astar(lmcut())` and
`astar(ipdb())` both refuse a task with axioms (driver exit 34, `This
configuration does not support axioms!`).

This decision first concluded from that that the optimal rungs simply cannot be
given the pair deadlocks. An adversarial review refuted it by writing the
encoding that can: nothing about a pair deadlock needs quantification, only the
schema's ignorance of how many dead partners a position has, so numbering them
through static selectors (`indexed`) removes the `forall` and stays in STRIPS.
The optimal rungs accept it.

The measurement that replaced the claim is worth more than the claim was:
`lmcut` expands **more** with the pair theorems than without (`far4` 23 -> 34,
`far6` 47 -> 66), because FD compiles a negative precondition on a fluent into
one operator copy per other value of that variable and the task grows about an
order of magnitude. Optimal length is unchanged throughout. Both the axiom
refusal and the indexed encoding's acceptance are pinned by tests, so a later FD
build that changes either fails the suite instead of going unnoticed.

**A third clause `guardable()` needed.** The pair guard is evaluated against the
pre-state, in which the pushed box still holds its old position. A pattern naming
one box twice therefore blocks the transitions that *leave* it -- stronger than
the theorem, and stronger is the unsound direction (measured: `far4`'s optimal
length 11 -> 25). `carve()` cannot emit one, but that is another module's
property and this one is supposed to check rather than assume.
`tools/p13_fd_dividend.py` had the check and documented it; `bench/` had dropped
it and has it back.

---

## D-028 · The rechecker derives the transition relation; nothing may hand it one

**Context.** M9's certificates already have a checker each -- `ic3_pdr`'s
`check.py` re-derives the three conditions and pointedly does not import `pdr`,
and the deadlock carver's referee exhausts the state space sharing nothing with
the proof. Both are handed the *engine's* object: `check.py` verifies against
the `System` that `system.py::peg_system` built, from the same graph the search
read. A transcription error there is invisible to both, and Lean cannot see it
either -- Lean checks the manual, and the manual is what is in question.

**Decision.** `recheck/` takes a rule set and a certificate as two files and
derives everything else. The rule set declares finite variables with explicit
domains; **the state space is the full Cartesian product of those domains**, and
every edge is computed by grounding the rules over it. A rule set carrying
`transitions`, `edges` or `states` is refused as a malformed input, and so is a
certificate carrying `goal`, `init`, `constraint`, `states`, `transitions` or
`rules` -- each by name, with the reason, rather than as a generic unknown key.
Nothing in the package imports `engines/`, and a test enforces that.

**Why.** The failure this is against is not an engine that lies; it is an engine
and its checker being wrong together because they were built from one
description. The only structural fix is to make the description an input that
neither of them produced. Refusing the forbidden keys by name matters for the
same reason: `goal` is a perfectly reasonable-looking thing for a certificate to
carry, and a certificate that picks its own goal proves a different theorem than
the one it claims.

**What it cost.** A small expression language, because "the rules" has to be
sayable in something. Roughly 300 lines, total and pure by construction: no
`eval`, no recursion (a `def` may only call one declared before it, so recursion
fails to resolve rather than being caught by a depth counter), and every world in
the rig fits under a 10^6-state enumeration cap. It also means the rule sets
under `cases/` are **transcriptions**, which is a real risk and is answered by
anchors rather than by assertion -- see D-030.

---

## D-029 · A declared restriction of the state space is proved inductive, never believed

**Context.** The sokoban deadlock theorems are false over the raw product of the
declared domains and true over the states the grounded task can represent. A
state with the player standing on a box is in the product, and from it a "dead"
box in a corner can be pushed out: `at(b1,c12) AND at(b2,c13)` leaks if the
player may occupy `c13`. The carver is right; it reasons over h^2-consistent
states. So the rechecker needs the same restriction, and a rule set has to be
able to say it.

**Decision.** A rule set may declare a `constraint`, and the rechecker refuses to
use it until it has shown, over the whole product, that it holds at every
initial state and is closed under every action. Only then are the certificate's
three conditions evaluated on the constrained subspace. `constraint_init` and
`constraint_closed` are reported alongside the certificate's own conditions.

**Why.** A declared restriction is exactly as dangerous as it sounds: it is the
cheapest possible attack on this rechecker. Take A2's world rules, leave every
rule intact, and add `constraint: cart != "6,4"` -- the escaping teleport now
starts from a state that has been declared ill-formed, and the false theorem
verifies. Proving the constraint inductive kills that attack at the root, because
a constraint that excludes a state the rules can enter is not closed. The forgery
is in the catalogue as `constrained-witness`, and it fails on
`constraint_closed`. The soundness argument is the ordinary one: an inductive
constraint holding at init contains every reachable state, so restricting a
reachability claim to it changes nothing.

**What an adversarial review corrected, and it is the interesting half.**
"Restricting a reachability claim to it changes nothing" is true of the
*reachability* claim and was quietly assumed to be true of the check. It is not.
Both conditions of a dead region were being evaluated on `P and constraint`
while the accepted claim was stated over `P`, so a reviewer built a region
containing an outright winning state -- parked at a player/box collision the
constraint excludes -- and it passed `goal_break`; and another where 286 of 496
covered states carried no obligation at all, with nothing in the output saying
so. Three changes:

* **`goal_break` moved to the whole product.** It costs nothing there -- a
  pattern that contradicts the goal contradicts it everywhere, and all 18 carver
  theorems still pass -- and it kills the hidden-win region outright.
* **Closure stays on the subspace**, because the sokoban pair deadlocks are
  genuinely false over the raw product and moving it would reject them. What
  changed is that the verdict now *counts* the states the predicate covers
  outside the constraint and names the qualifier carrying them, in every report.
  The genuine `open4far` pair theorems lean on it by 2 states each; saying so is
  the difference between a qualified result and a silent one.
* **The qualifier's premise is measured, not inferred.** `constraint_contains_reachable`
  runs a breadth-first pass and checks that no reachable state lies outside the
  constraint. It follows from the other two conditions; running it anyway costs
  one pass and means a bug in the closure loop cannot quietly widen what
  "well-formed" is allowed to hide.

The claim a `dead_region` licenses is now written the way `deadlock_carver`
writes it, qualifier included: *every reachable state* containing the pattern is
dead.

---

## D-030 · The rule sets are transcriptions, and the anchors are outside the package

**Context.** Nothing inside `recheck/` can tell you that `a2-world.rules.json`
describes A2's world. If it does not, every verdict about it is about a world
nobody has -- and the verdicts would look exactly as convincing.

**Decision.** Every case carries an anchor: a number or an artefact published by
someone else, for another purpose, before this package existed. A2's own
recorded 18-action refutation is replayed through the generated rules and
compared frame by frame on the rendered 9x9 (19/19). Lean's explicit 592-row
`step` table inside `generated_holed/theory.lean` -- the file Lean compiled
axiom-free -- is compared edge by edge against the relation derived here
(592/592). The sokoban optima the fixture states by hand come back out of the
derived relation (ring 1, open4 6, ringstuck unsolvable, open4far 11). So do the
four peg configurations `fixtures/peg4.py` hand-verifies. A case with no anchor
is refused at review, not at runtime.

**Why.** The alternative -- parsing PDDL, Lean and the DSL directly -- trades a
transcription risk for a parser-bug risk in three languages, and the parser would
be this package's own code, which is the dependency the whole exercise is
avoiding. Anchoring instead means the risk is bounded by artefacts that were
already going to be there, and it is bounded *by measurement*: 592 edges and 19
frames is not an argument, it is a count.

**The limit, stated.** Two anchors need `cold-start-a2/` on the machine. That is
the theory-compiler track's directory: this package reads it, writes nothing to
it, and reports the anchors as **unavailable** rather than as passes when it is
absent. A missing cross-check is a missing check.

---

## D-031 · A scope flag is not a check until the thing it guards is recompiled

**Context.** `recheck`'s expression language says `["act"]` -- the action label --
is legal only inside a rule guard. A certificate, a goal or a constraint denotes
a *set of states*; one that reads the action is describing the rules. The rule
was enforced by a `allow_action` flag on the compiling scope.

**The defect an adversarial review found.** Compilation turns an expression into
a closure, and `defs` were compiled once, with `allow_action=True`, for the
guards. The state-reading scope was then built by reusing those *already
compiled* closures and setting the flag to `False`. A closure does not
re-consult the flag. So a rule set could write

```json
"defs":  [{"name": "peek", "params": [], "body": ["=", ["act"], ["lit", "jump(0,1,2)"]]}],
"goal":  ["call", "peek"]
```

and the goal would read the action. At evaluation the state scope passes
`action=None`, so the comparison is a constant `False`, the goal becomes
unsatisfiable, and the world is trivially "unsolvable". Measured on `peg4-1101`,
which is solvable in two moves: with the honest goal the catalogue's
`claims-everything` certificate is REJECTed and the second opinion prints the
two-action win; with the goal restated as `["call","peek"]` the same certificate
is **ACCEPTed**, and the second opinion agrees, because it reads the same
poisoned goal. Nothing on stdout hinted at it -- `render` printed the goal as
`peek()`, and the report did not print the goal at all.

**Decision.** Compile the defs **twice**, once per scope. The second compilation
raises on any def that mentions the action, which is what the flag was always
supposed to mean. Three smaller changes travel with it:

* `compile_macros` extends the enclosing scope's macros instead of replacing
  them, so a certificate can call the rule set's `free` -- which the docstring
  had claimed all along and which had silently not been true. That is fixed
  *after* the leak, deliberately: fixing it first would have made the leak
  reachable from certificates too.
* the verdict now prints the goal and the coverage counts, so a poisoned goal
  has somewhere to be visible.
* expression depth is capped at 64 by an iterative walk, and `render` and
  `names_used` are total. They run on input that has not been compiled -- a
  verdict summarises the certificate it is rejecting -- so `["lit"]` with no
  argument used to raise `IndexError` from inside the rejection, and 900 nested
  `and`s used to raise `RecursionError`, which is not a `ValueError` and escaped
  every `except` around a load.

**Why it matters more than the bug.** All of those crashes exited with Python's
own status of 1, which this tool defines as REJECT. A caller reading the exit
code could not tell a refused certificate from a checker that fell over. There
is now an exit code 4 for "the recheck itself failed", and it is the same
distinction D-024 had to make for Fast Downward: a proof and a shrug must not
share a return value.

**The general lesson, since this is the second time.** The reviewer also caught
this package mid-edit, in a state where `obligations()` raised `NameError` on
every input -- and reported, correctly, that it exited 1 and looked like a
rejection. A guarantee enforced at construction time has to be re-established
every time the constructed thing is reused, and a checker's failure mode has to
be distinguishable from its verdict. Neither is a fact about expressions.

---

## D-032 · The deadlock claim is conditioned on the proof system, not on the search

*(Numbered 032, not 028: the `agent/e5-cert-recheck` branch takes D-028 through
D-031 and was pushed first. Two branches numbering into the same file is a
collision waiting to happen, and leaving a gap is cheaper than renumbering a
cross-reference later.)*

**Context.** E2 measured Theoria 1.9's promise that every proved deadlock speeds
the planner up, found the speed-up half false against a real Fast Downward, and
explained it: *a proved deadlock is a substitute for a heuristic, not an addition
to one.* E7's brief was to check that finding before it hardened into a clause in
the design document.

**What the audit found, and what the attack on it then found.** The numbers
replicate exactly -- all nine rows, to the expansion. E2's explanation does not
survive: over the whole reachable space of the `far{N}` family the delete
relaxation Fast Downward computes before search is *equal* to the true dead set
(2904/2904 at far4, 10687/10687 at far5, 29776/29776 at far6), and the carver's
theorems are a strict subset of it. The theorems are not competing with the
heuristic; they are information the planner already had for free.

E7's own first draft then claimed two things the adversarial pass broke, and the
breakages are the reason this decision reads as it does:

* **"Not one state, at any size, that a theorem detects and the relaxation
  misses"** is false. `rnd0021` has eleven, verified against real Fast Downward,
  and there the pruning dividend is total (`astar(lmcut())` 33 -> 0). More useful
  than the counterexample is the structural argument it forced: a width-1 theorem
  can escape the relaxation only if its pattern atom *is* a goal atom, which
  requires h^2 to have proved the goal conjunction inconsistent, which means the
  instance is unsolvable. `far{N}` is solvable, so for the 8 **singleton**
  theorems the guard carries the zero was a **theorem about that family rather
  than a measurement**. The argument does not reach the width-2 majority, which
  stays a measurement at far4/5/6. The boundary is **h^2 versus h^1** -- the
  carver proves with h^2 mutexes, FD's pre-search deadness test is h^1.
* **"The dividend is zero because the information is redundant, not because it is
  unused"** is a false exclusive and is withdrawn. A compiled guard is a domain
  transformation, not a per-state filter, so containment does not entail a zero
  dividend -- and it does not deliver one: `astar(lmcut())` saves up to 153
  expansions, tie-break-invariantly. It saves them by a third mechanism neither
  word names. Every state the guard removes was already an lmcut dead end,
  evaluated and never expanded; what deleting the dead push operators does is
  make the delete relaxation *harder*, raising h on **live** states. That last
  step is isolated on exactly one instance (`hunt0021` h(init) 15 -> 18); on the
  other three that save expansions, h(init) does not move, so the mechanism is
  exhibited once rather than established four times.

**Decision.** The claim in `DEADLOCK_CLAIM.md` is conditioned on **whether the
theorems' proof system is stronger than the planner's own pre-search
relaxation**, not on which search is running and not merely on whether the
relaxation covers the region. Suggested wording is offered there; Theoria.md is
not edited, which is the monitor's call and was the ticket's instruction.

**Why that conditioning rather than the flat negative.** "Deadlock theorems do
not speed planners up" is wrong twice: it forbids the `rnd0021` case where a
theorem beats the relaxation, and it hides the small real lmcut effect.
Conditioning says what was measured, says what would have to hold for the promise
to be true, and hands the next person a test instead of a verdict. The test is
cheap and runs before the planner does: compute both sets and compare, which is
`audit.claim.coverage`.

**A prediction this decision cost, and the explanation that also failed.**
`audit/deadstart.py` was built expecting the two theorem kinds to split -- corner
deadlocks fall out of grounding and should survive a relaxation, pair deadlocks
need h^2 mutexes and should not. They do not split. The first draft explained that
by `clear` being false on a box's cell and never coming back; a reviewer
re-encoded sokoban with `occupied` instead and the relaxation still found all
2904 dead states on far4 with occupancy information removed. What is load-bearing
is **static push geometry**, not the `clear` fluent. Both the prediction and the
wrong explanation are kept beside their refutations, because a prediction deleted
after it fails is a prediction nobody made.

**One instrument ruled inadmissible.** `astar(ipdb())` expansion counts are not
usable evidence at this effect size. `far9`'s 78 -> 30 vanishes under two of
eight random seeds and under a larger PDB budget; `swap-passage`'s 454 -> 0 is a
`pdb_max_size` effect -- iPDB's winning projection returns h = infinity on the
*unguarded* task too, and the guard's whole contribution is shrinking that PDB
from 2,725,888 entries to 1,103,872, under the 2,000,000 default cap. An earlier
draft quoted far8's `ipdb` 27 -> 24 as a dividend; it is one of these. The ipdb
column is measured and reported, and is evidence for nothing.

---

## D-033 · The summary table reads verdicts; it does not re-derive them

*(Numbered 033 after D-032, which `agent/e7-deadlock-claim-audit` takes.)*

**Context.** E6 assembles one table -- *what is an engine worth?* -- out of three
runs that measured three different things. `tools/engine_dividend_table.py` is
that assembler and `ENGINE_DIVIDEND.md` is its output.

**Decision.** The assembler reads measurements and, where an artefact carries a
**verdict**, reads that verdict rather than recomputing an equivalent one. Its
arithmetic is confined to percentages and totals over fields it read.

**Why, concretely.** An earlier draft recomputed section C's optimality
agreement. Four sokoban instances have no *known* optimum; the recomputation
scored "no ground truth" as "disagreement", rendered **no** against `lmcut`,
`ipdb` and the bundled BFS, and printed the sentence *"Every optimal rung agrees
... (4 disagreements)"*. E2's `ladder.json` carries `agreement_ok: true` on all
four and its own `LADDER.md` renders them `yes`. A false accusation that three
admissible planners returned non-optimal plans, in the file whose whole purpose
is to be quoted in a paper. Reading `verdicts.agreement_ok` gives 0.

**The generalisation, which is the part worth keeping.** Three further defects in
the same draft had one shape: a column reading a key that does not exist,
rendering as a valid table full of `--`.

| column | read | actual field |
|---|---|---|
| FD blind | `config` | `rung` |
| plan | `plan_unchanged` | `plan_length_unchanged` |
| pagoda region | `n_region` | `n_satisfying` |
| tie-break dividend | `dividend_min` | `guards.<guard>.dividend_min_pct` |

**A `--check` that re-renders and diffs cannot catch any of them.** It proves the
file matches its renderer, never that the renderer reads the right field; a
wrong-key column is perfectly stable and perfectly wrong. The plan column was the
worst of the four, because `stub.get("plan_unchanged", True)` would have printed
`unchanged` for a guard that changed the plan -- a soundness claim defaulting to
true. So: **every summary column is pinned by a test that asserts a real measured
number, plus a perturbation test that moves one field in a temp copy and requires
exactly the matching cell to move.** Two fields that agree on today's data are
indistinguishable to a transcription test; only perturbation separates them.

**A related call: what the theorem count beside a planner row means.** It is the
number proved, which is not the number that reached the planner -- the
`singleton` guard expresses size-1 theorems only, 8 of 40 on `far7`. The table
carries both, because a dividend attributed to 40 theorems that eight bought is
the same class of error as the columns above, one layer up.

---

## D-034 · A verdict that is computed is a verdict that gates

*(Numbered 034 after D-033. E16, `agent/e16-verdict-must-gate`.)*

**Context.** RES-3's dual census walked ~105 judgement points and called 8
unsafe. The shape it found is not the one the phrase "unverified claim" leads you
to expect. In every one of the 8, **the check had been written, and it ran, and
it was right.** What was missing was the `if`. The verdict landed in a sibling
field of the artefact and the headline field did not read it.

Two instances, both fixed here.

**`lp_potential`'s heuristic payload.** `"admissible": True` was a literal in the
dict. The genuine check — h against the true shortest path on every state with a
finite one — was computed by `admissibility_report` and attached *afterwards*, by
the caller, under `admissibility_check`. So the two could not agree or disagree;
one was a constant. A `Heuristic` built on a certificate that fails its own exact
rational re-check published itself as admissible, and so did one whose
`conditions` were empty because nobody had checked it at all.

**Decision.** `Heuristic.as_json(admissibility_check=None)` takes the check as an
argument and derives both `admissible` and `admissible_basis` from it; the caller
no longer bolts the check on afterwards. The licence is `certificate.holds` — the
exact re-check of `inv_closed` is *literally* the premise the bound
`h = min_g ceil((pot(s) - pot(g)) / M)` rests on — conjoined with the empirical
rows, which can only ever subtract, since a sample refutes but does not prove.

**`deadlock_carver`'s emitter.** `carve() -> pruning_report() -> emit()` ran with
no branch between the second and the third. `PruningReport.same_answer` asks a
question that can falsify a theorem operationally — *did pruning change the
instance's answer?* — and its value was serialised as `plan_length_unchanged` and
published **beside the theorems it had just falsified.** A reader received a
theorem and a report saying that theorem is unsound, side by side, with nothing
in the stream saying which one wins.

The gate this installs is **one-directional, and deliberately not more.**
`same_answer == False` proves unsoundness. `True` proves nothing: an unsound
theorem cutting only states that lie on other optimal plans of the same length
moves neither `solved` nor `length`. So this gate withholds what it catches and
makes no claim about what it passes — the soundness evidence remains the
exhaustive referee in `tests/`, with the grounding caveat D-035 records against
it. Writing the gate as though passing it were a clearance would have reproduced
the defect being fixed, one level up.

**Decision.** `candidates()` reads the verdict before it builds rows. Refuted
theorems are **withheld** by default; `on_refutation="mark"` emits them carrying
a machine-readable `refuted: true` and a `refutation` object instead. Either way
the `plan` account carries `refuted`, `invariants_withheld` and `on_refutation`,
so a suppressed run is distinguishable from a run that carved nothing — silent
truncation would read as "all clear", which is the same defect one layer up.

**Why the marker is a field and not a sentence.** The consumer that has to honour
this is `bench/dividend.py:868`, and it reads fields. A `rendering` string saying
"but this theorem was refuted" is not a gate; it is a hope about who is reading.

**What is deliberately *not* collapsed.** `same_answer` raises
`UnfinishedComparison` when either search stopped, and `candidates()` does not
catch it. Withholding on an unfinished search would file a soundness violation
against a theorem on the strength of a search that answered nothing; publishing
would clear it on the same nothing. Three states, three behaviours: no report at
all leaves `refuted` **absent**, a passed verdict also leaves it absent, and only
a real refutation writes it. "Nobody asked" and "asked and passed" are both
distinct from "asked and failed".

**What an adversarial review of this decision then found, in the fix itself.**
The first cut gated the heuristic row and left the invariant row beside it
ungated — **the same defect one row over.** Both rows come from one weight
vector; the invariant went out asserting `goal unreachable from 1110` with all
three conditions `true`, next to a heuristic row whose counterexamples were a
proof that `inv_closed` is false over the real move set. Two rows from one call,
contradicting each other, nothing saying which wins.

The repair is not another sibling check. `candidates()` re-derives the premises
**from the graph** (`premises_against_graph`) and withholds both rows when they
fail — `moves_raising_potential` recomputes `inv_closed` over every geometry the
graph has, which is the one check the certificate's own inputs cannot perform.
The invariant payload also publishes `holds` outright, because `conditions`
alone does not say what it appears to: `all({}.values())` is `True`, so a
consumer re-deriving the verdict from a never-checked certificate reads it as a
pass. Four more instances of the shape came out of the same review and are fixed
here: `interop/certificate_export.build` wrote `conclusion` as a literal *above*
the line computing `verified`; its `checked_over` asserted "all move instances on
the full state space" regardless of how many were listed; `tools/run_all.py`
handed the RING deadlock theorems to the probe planner — whose reachability
verdicts are published — with no verdict taken on that instance at all; and
`tools/p13_fd_dividend.py` had no prose branch for `same_answer is False`, so a
refuted row fell through to "the plan is N steps either way", which is the one
thing it was not.

That is the argument for the review, and it belongs in the decision: **a fix for
"the verdict is not read" is exactly the kind of change that leaves a sibling
unread.** Five of the six sites above are in files this work item had already
opened.

**The generalisation.** A computed verdict sitting next to the thing it judges,
with no branch between them, is *indistinguishable from an uncomputed one* to
every consumer. The work of checking is wasted precisely when it is most needed.
So: **the site that publishes a claim is the site that must read its verdict** —
not a caller upstream, not a reviewer downstream. `tools/run_all.py:152` did
check `report.same_answer` and raise — but it checked *after* `dc.run(...)` had
already written the refuted theorems to disk. A gate behind the write is not a
gate.

---

## D-035 · "Verified" and "verified by something independent" are two claims

*(E16 item 3. The wording task RES-3 filed separately, because this cell is the
one most easily read as safe.)*

**Context.** RES-3's §4 promised six places that are "verified but not
independently" and named three; the remaining three were found by walking the
same question through the other engines. All six are listed below. **None of them
is a missing check.** Every one has a checker that runs, and most were
deliberately built not to import the producer — which is real work and really
does buy something. What none of them buys is what the surrounding prose claimed.

**The distinction.** A checker that re-derives a conclusion from the **same
premise** the producer used is evidence about the producer's *arithmetic*. It is
not evidence about the *world*. Independence has to be traced to the premises,
not to the import graph — two oracles that agree are one piece of evidence when
they share a premise, and `CROSSCHECK.md:31` had written that sentence down
before this decision existed.

**The six, with the shared premise named.**

| site | verifier does not import | but shares |
|---|---|---|
| `lp_potential` `check_exactly` | the LP | `Certificate.moves`, from `moves_from_graph(graph)` |
| `ic3_pdr` `check.py` | `pdr` | `System.transitions` |
| `interop/certificate_export.verify` | — | the producer's own witness list |
| `zero_space` `verify()` | — (it sits in the module it checks) | the trajectory the laws were fitted to |
| `deadlock_carver` referee + `same_answer` | the carver's proof | `ground_actions` / `strip_static` |
| `fd_adapter` `validate_plan` | `search` | `ground_actions` |

**What follows, concretely.** `check_exactly` iterating `certificate.moves` means
a move geometry missing from that list is *unconstrained in the LP and unexamined
in the re-check at once*. This is not hypothetical:
`tests/test_lp_potential.py` now carries a certificate over three of peg4's four
moves that passes all three conditions exactly and yields `h = inf` — a per-state
unsolvability claim — for two states that are one and two moves from the goal.
Exhaustive search over integer weights in [-4,4] finds **no such vector against
the complete move list**, which is the cleanest available statement of where the
soundness actually lives: in the completeness of the enumeration, not in the
arithmetic.

`zero_space`'s gap is sharp in a different way: a vector in the null space of the
observed differences is constant on the observed trajectory *by construction*, so
`verify()` is close to a tautology and its `AssertionError` close to unreachable.

`interop/certificate_export.verify` is the only one exploitable by omission
rather than by error — it iterates the witnesses the producer chose to list, so a
document that leaves out an inconvenient move instance passes with an empty
finding list.

**Decision.** The wording is separated everywhere it appears, and the docstrings
that claimed more than they had are corrected in this commit rather than
annotated. Specifically: `validate.py`'s "the only code shared with the planner
is the parser" was false (`ground_actions` is shared and is not the parser);
`interop/README.md`'s "recomputes everything from the document's own contents"
names the defect as though it were the remedy; `zero_space/README.md`'s
"independent check" is independent of the elimination, not of the evidence; and
`deadlock_carver/README.md`'s "that referee shares nothing with the proof or with
the planner" is contradicted by the referee's own construction — while
`carve.py:139-143` had disclosed the sharing honestly all along, which is why the
README is the layer that was fixed.

**A correction this forces on E16's own premise.** The work item opens with good
news: `fd_adapter/__init__.py:140` calls `validate_plan()` unconditionally and
`validate.py` pointedly does not import `search`, so "the solver returned a plan,
therefore it is solvable" does not happen here. **The unconditional call is
true and verified.** The *structural* half is one function weaker than
advertised: validator and searcher share `ground_actions`, so a wrong add/delete
effect or a wrongly-admitted instance in the grounder corrupts both identically.
The claim survives against search bugs, which is what it was aimed at, and does
not survive against grounder bugs, which it was written as though it covered.

**What is *not* being claimed.** These six are not defects to be repaired by
making every checker independent; for most of them that is the same work as
writing the engine twice. `recheck/` is the one place in the rig that pays that
price in full — it grounds moves from the rule set, refuses a certificate
carrying its own `transitions`, imports no `engines/`, and adds a second opinion
(a plain reachability BFS) sharing nothing with the three conditions. The
decision here is that **everywhere else says what it is**, so `recheck/`'s
guarantee stays legible as the stronger thing it is.

**A contrast worth keeping.** `cegis_miner` states outright, in both `miner.py:3`
and its README, that "the ledger *is* the verifier". Its self-checks are circular
and it says so. That is not a defect — it is the correct behaviour, and what
separates it from the four sites corrected above is one sentence of prose.

**Two earlier decisions are superseded on exactly one clause each.** This file is
append-only, so they are corrected here rather than edited in place, and both are
corrected only on the independence claim — everything else in them stands.

* **D-010** reads "a separate executor … *code that shares nothing with the
  search*". Read as **shares no search code**, it is true and remains the reason
  the validator is worth having. Read as **shares nothing**, it is false:
  `validate.py` and `search.py` both import `pddl.ground_actions`. The guarantee
  is against frontier, ordering and duplicate-detection bugs; it is not against
  grounder bugs.
* **D-028** reads the deadlock carver's referee "exhausts the state space
  *sharing nothing with the proof*". Its **method** shares nothing — forward BFS
  and backward closure, no mutexes, no blocked-action argument. Its **grounding**
  is the carver's own: `tests/test_deadlock_carver.py:127` builds it from
  `strip_static(domain, problem, ground_actions(domain, problem))`. So a passing
  theorem is certified dead over the atoms the search holds, which is the claim
  the pruner needs, and not over the PDDL as written.

Both were found by an adversarial review of *this* decision, which is the
argument for running one: D-035 corrected six docstrings and left two decision
entries asserting the sentences it had just falsified. A boundary written in one
file and contradicted in another is not a boundary.

---

## D-036 · The checker for an exchange format cannot sit on the producer's side of the exchange

*(Numbered 036 after D-035. C13, `agent/c13-certificate-bridge-two-halves`.)*

**Context.** D-035 listed six checkers that do not import their producer and
named the one that is "exploitable by omission rather than by error":
`interop/certificate_export.verify` iterates the witness list the certificate
itself supplies, so a document that leaves out an inconvenient move instance
passes with an empty finding list. That entry recorded the gap and corrected the
prose around it. It did not close it, and `interop/certificates/*.json` is the
one artefact class in this rig that leaves the track — the theory-compiler
reader has been consuming it since `f58959e7`.

**The decision.** The rig ships a reference reader for its own exchange format,
`interop/pagoda_reader.py`, and the format is pinned in
`CONTRACTS/pagoda_certificate_v0.1.md`. The reader pays independence in three
currencies, each checked rather than asserted:

* **It imports nothing from here.** `json`, `fractions`, `os`, `sys`, and that
  is the whole list — no `engines`, no `interop`, no `recheck`, not even numpy.
  `tests/test_pagoda_reader.py` scans the import lines.
* **It runs alone.** Copied into an empty directory and executed with `python
  -I`, it still adjudicates. A promise about the import graph that no process
  ever tests is a promise about a comment.
* **It grounds the move relation instead of reading it.** This is the one that
  matters; the other two are hygiene.

**Why the geometry is duplicated on purpose.** `pagoda_reader.jump_moves` is a
second implementation of `peg1d.move_instances`, six lines re-written rather than
imported. Importing them would make the reader re-check the producer's premise
against itself, which is exactly the shape D-035 was about. The duplication is
the guarantee, and the contract is the single text both copies are written from.
The cost is real and named: two implementations can drift. What catches drift is
that both are exercised against the same three committed documents, and that the
reader carries an exhaustive second opinion on boards small enough to settle.

**The non-vacuity, because a checker that has never said no is not a checker.**
A forged certificate: `weights_integer[2]` moved from `0` to `-1`, which makes
`jump(1,2,3)` and `jump(3,2,1)` raise the potential, with those two witnesses
deleted and every remaining field — deltas, `holds`, `n_checked`, `checked_over`,
`weights_rational` — recomputed to agree. The bound and the goal are untouched
because neither depends on cell 2, so `inv_init` and `goal_break` still hold.

```
certificate_export.verify(forged)                  -> []          # accepted
pagoda_reader.check(forged, geometry=<the document's own list>) -> []          # accepted
pagoda_reader.check(forged)                        -> two rejections
```

The middle line is the point. Same reader, same document; only the source of the
move relation changes, and the verdict flips. So what the decision fixes is not
"check `inv_closed`" — `verify()` already did — but **where the transition
relation is allowed to come from**.

**A second consequence, smaller but load-bearing.** `initial_potential` is read
as a *declared* bound and `potential(initial) <= bound` is checked against it,
rather than recomputed from `initial_state`. `certificate_export.build` writes
the bound *as* `potential(initial)`, so recomputing turns `inv_init` into
`x <= x` — a certificate with a tampered-down bound would then be caught by no
obligation at all. Its own docstring already admitted the field "is here for the
Lean skeleton's third slot"; reading it as a declaration is what makes it
evidence.

**What this does not buy.** That peg1d is the right rule set for anybody's world.
Three obligations discharged entitle a reader to "no goal state is reachable
under the 1-D peg jump relation on `n_pos` cells", and the reader declares that
assumption in `GEOMETRY` rather than pretending the document settled it. A
different rule family needs a different schema id, not an extra field — an extra
field would put the relation back inside the document.

**Two things repaired in passing.** `interop/certificates/*.json` had no
producer: no script in the tree rebuilt them, and the only record of a
regeneration was a prose line in another run's `MANIFEST.json`.
`interop/export_certificates.py --check` rebuilds all three byte-for-byte and is
in the suite. And the item that commissioned this work asserted that
`monitor/scan.py`'s `probe_a1_state` reports the bridge unconsumed; it reports
`green`, and has been able to since `f58959e7` landed the consumer two days
earlier. Nothing here was changed to make that so — the probe is untouched and
this branch changes zero bytes under `theory-compiler/`. The correction is filed
on the board and in `monitor/inbox/`, because a work item whose premise has
expired is worth more as a correction than as a completed ticket.
