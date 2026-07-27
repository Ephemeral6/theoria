# DECISIONS — cold-start-a2

Design calls and their reasons. One entry per call that could reasonably have
gone the other way.

---

## D-A2-001 · A2 is run on a self-built world, on INC-004's authority

**Call.** Do not port the upstream DC22 model. Build a world isomorphic to
DC22's *failure structure* and run A2 on that.

**Why.** Phase 1's A2 item says "把上游那个漏了传送规则的模型移植进 DSL".
DC22 is in the sealed pile, and reading its upstream artifacts is
exactly what the pile cut forbids — reading them teaches the mechanics as well
as playing does. INC-004 records the conflict and the owner's ruling of
2026-07-28, option (b): *"A2 is fulfilled by a self-built world isomorphic to
DC22's failure structure (a pushing world with a teleport rule; hole introduced
by deleting that rule from an otherwise-certified manual). The isomorphism
argument may cite only the structural description already printed in Theoria
§1.3 — no upstream DC22 artifact is ever read."*

**What was read, exactly.** Theoria §1.3, one paragraph: the model replays
175/175, is missing one teleport rule, a complete search over it proves a
humanly-solvable goal unreachable, and the missing rule never fired so it owes
no frame. Nothing else. The sealed game's id is not carried in this directory —
INC-004 records it, A2 does not need it, and
`tests/test_a2.py::test_no_dc22_artifact_is_present` keeps it out byte-wise.

**What the substitution costs.** Any claim about DC22 *itself* — its geometry,
its frames, how its search actually failed — is out of reach and is not made.
A2's claim is about the structure, and it is now backed by a run rather than by
a citation. See `A2_REPORT.md` §1 for the difference stated in full.

---

## D-A2-002 · The hole is the teleport, and the world is built so that deleting it is provable

**Call.** Column c5 is solid wall from r1 to r7. The right room, which holds the
goal, touches nothing. The Portal is the only rule that crosses.

**Why.** §1.3's construction needs three things to hold at once: the deletion
must be invisible to replay, the resulting model must *prove* the goal
unreachable, and the goal must in fact be reachable. The third is free (the
world has the rule). The second needs the unreachability to be certifiable by a
small invariant, not merely true — a 0/1 pagoda weight over a region separated
by a wall is the cleanest such thing, and it is inside
`dsl_grammar_v0.1`'s invariant language (finite weight functions). A world where
the two rooms were merely far apart would be unreachable-in-fact but would need
a connectivity predicate to certify, which the contract does not support.

**Rejected alternative.** Making the *Door* the hole. The Door is a latch, and a
latched model still reaches the goal by another route in most layouts; where it
does not, the missing rule is a recolour, not a teleport, and the isomorphism to
§1.3 weakens to "a missing rule" instead of "a missing teleport rule".

---

## D-A2-003 · The play record is a prefix of the sweep, and the cut is found geometrically

**Call.** `history_trace.jsonl = raw_trace.jsonl[0 .. portal_transition]`, where
`portal_transition` is the single transition in which the Cart moves more than
one cell — found by looking at the frames, not at a flag.

**Why.** The alternative is to generate the two traces separately, and then the
honest question "was the history curated to make the hole invisible?" has no
good answer. As a prefix it has one: the history is the sweep, stopped. The
explorer covers each stratum exhaustively before advancing, so the history is
*exhaustive over its own strata* — 163 of the 164 reachable (state, action)
pairs with the Cart in the left room, omitting exactly the pair that fires the
deleted rule (`artifacts/trace_summary.json`).

**Consequence, stated because it is stronger than §1.3's own case.** DC22's 175
frames were a play record of unknown coverage. A2's is near-total. The defect
survives anyway, which is the construction argument at its sharpest: this is not
a coverage failure, it is what past-facing checking cannot see.

---

## D-A2-004 · `cascade single_frame`, as in A0

**Call.** The Button press and the Door opening happen in one transition; every
guard reads the pre-state and all effects apply together. Declared in each
manual's `semantics:` section and enforced by the compile backend.

**Why.** Theoria §1.8 defers the cascade question to the trace, so it is a
per-world fact and the manual has to say it. A2 keeps A0's answer deliberately:
the point of A2 is the teleport, and varying a second semantic axis at the same
time would make any difference in outcome unattributable. A0's `dialect.py`
rejects a manual that does not declare it, rather than assuming a default.

---

## D-A2-005 · The repaired manual proves a *true* theorem of the same shape

**Call.** Add a sealed floor pocket at (7,1) — walled on all four sides, never
occupied with or without the teleport — and have the repaired manual prove
`unsolvable` about it, using the same generator, the same `decide`-only tactic
and the same empty axiom list as the exhibit.

**Why.** Without it, "重证" degenerates into "the false theorem is gone", and a
reader can only take on faith that the instrument is still capable of a true
unreachability claim. With it, the two Lean files differ in their weight table
and nothing else, and the difference in truth value is carried entirely by the
world. That is Theoria §1.10a's two-layer regime as an artefact rather than a
sentence, and it is the thing figure 5 of the paper would show.

**Discipline.** The pocket claim is probed (P-02.1–3, the wall ring, executed)
*before* it is proved, not after.

---

## D-A2-006 · The PDDL backend cannot ground a teleport; worked around, not fixed

**Finding.** `cold-start-a0/compile/gen_pddl_a0.py::_problem` emits a cell object
and its adjacency facts only for cells in `problem.arena`, and
`compile/problem.py::derive` builds the arena from floor and dynamic cells. A
static coloured cell — a Portal entry — is in neither. The `teleport-down`
action's precondition is `(adj-down ?from ?p)` with `?p - markedcell`, so with no
`c7-4` object the action never grounds and the planner reports **UNSAT on a
manual that contains the teleport rule**.

**Why A0 could not see it.** A0's goal was reachable through the Door, so no A0
plan ever needed the jump action to ground. The bug was latent and produced a
correct answer by luck. A2's goal is reachable only through the teleport, so it
produces a wrong answer immediately — the control manual came back UNSAT on the
first attempt.

**Call.** Fix it in A2, PDDL-only, in `a2pipeline/compile_a2.py::pddl_addressable`:
the PDDL cell universe is the arena plus every cell some guard names by colour.
`_problem` already withholds `(passable ...)` from markedcells, so move actions
still cannot step onto one — these cells are addressable, not occupiable. The
Lean and Python forms keep the unaugmented arena, because their arena means
"states the Cart can be in" and the Cart is never on the Portal.

**Why not fixed upstream.** `cold-start-a0/` is the theory-compiler track's
directory and this track does not edit it (CLAUDE.md). Reported on
`PARTNER_SYNC.md`.

---

## D-A2-007 · Lean's output is decoded as UTF-8 by A2, not by the process locale

**Finding.** `certify/lean_check.py` runs Lean with `subprocess.run(text=True)`,
which decodes with the locale encoding — GBK here. Lean's *error* messages
contain U+2019 and ⟨⟩, so the reader thread raises `UnicodeDecodeError` and the
diagnostic is destroyed precisely when there is a diagnostic.

**Why A0 could not see it.** A0 never had a red Lean file. A2 has one on
purpose: `generated_repaired_stale/` exists to hold the refuted certificate,
and its error message is evidence.

**Call.** `a2pipeline/certify_a2.py::lean` runs the binary in bytes mode and
decodes UTF-8 with `errors="replace"`. The *parsing* rules — the two axiom
regexes and the green criteria — are imported from A0 rather than restated, so
the two cannot drift on what counts as green.

---

## D-A2-008 · `$LEAN` is pinned to elan's toolchain, not to A0's `.toolchain/`

**Call.** `ensure_lean()` looks at `$LEAN`, then `~/.elan/toolchains/*/bin/lean`,
and only then falls through to A0's discovery order.

**Why.** A0's `find_lean` falls back to `cold-start-a0/.toolchain/`, which would
make A2's headline result depend on a directory belonging to another track and
on whatever that track does to it. The binary actually used is recorded in every
Lean report (`certify_lean.lean`). Lean 4.9.0, no Mathlib, `decide` only,
`#print axioms` empty — A0's three commitments, unchanged.

---

## D-A2-009 · The certificate's region is derived twice, differently, and the difference is a result

**Call.** For the *exhibit*, adopt `zero_space`'s occupancy law as the pagoda's
zero set. For the *repaired* manual, widen it to the manual's own reachability
closure and remove the pocket.

**Why.** The engine proposes the cells the Cart was *observed* on. For the holed
manual that set is already closed under the manual's `step` and it is used as
is. For the repaired manual it is not — the probe only ever put the Cart on
(7,6), so the engine's law would fail `inv_closed` one move into the right room.
Closing it under `theory.py` is reading the manual, not the world: the manual is
a program, and asking a program where it says the Cart can go uses no oracle.
The numbers are in `artifacts/repair_report.json` — 22 cells proposed, 35 in the
closure, 35 adopted.

**Why this is worth writing down.** It is a concrete case of the division of
labour: the engine hands back a whole space of laws, and picking a
representative that is both *readable* and *closed* is the semantic act. The
engine cannot know that the evidence under-determines the region, because the
evidence is all it has.

---

## D-A2-010 · Scoring against the referee's copy happens inside the run

**Call.** Unlike A0, which held `score_vs_truth` back as a separate command, A2
compares manual against world inside `run_all.py`.

**Why.** A2's entire subject *is* that comparison — a report that only said "the
theorem type-checks" would be reporting half the finding. The discipline that
replaces A0's is stricter in the place that matters: **no theorizing step ever
reads `ground_truth.json`**, and the loop's own evidence reaches the manual only
as frames. `refute.py` writes the world's solved episode out as
`solved_episode.jsonl` — the same four fields as every other trace — and
`locate.py` and `probe.py` import no world module at all. `probe.py`'s
`Environment` is the single channel: actions in, frames out.
