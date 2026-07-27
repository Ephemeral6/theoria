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
