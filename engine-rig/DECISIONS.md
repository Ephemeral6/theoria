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
per-transition header and the same cost for the initial frame; they differ only
in how each transition's content is encoded. The acceptance threshold is a ratio
(script <= 0.5 x baseline), not an absolute number.

**Why.** Sharing the header and the initial frame between the two models removes
the easiest way to fake a win. Fixed-width fields (rather than an entropy coder)
keep the count auditable by hand.

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

**Decision.** See `STATUS.md` for the attempt log and the outcome. The adapter
exposes one function, `solve(domain, problem)`, and picks a backend at call time;
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
