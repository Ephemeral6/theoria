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
configuration does not support axioms!`). So the optimal rungs can be given the
corner deadlocks and cannot be given the pair deadlocks. That limit is measured
rather than asserted, and pinned by a test, so a later FD build that lifts it
fails the suite instead of going unnoticed.
