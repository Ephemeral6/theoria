# DECISIONS — cold-start-a3

Design calls, and the upstream gaps this spike ran into.  Every entry says what
was decided, why, and what it costs.  Findings about code belonging to another
track are recorded here and on `PARTNER_SYNC.md`; **none of them was fixed in
place**, because `cold-start-a0/` and `theory-compiler/` are the
theory-compiler track's territory (CLAUDE.md).

---

## D-A3-001 · Two levels of one world, not two worlds

C3 is "carry the two books to the next level", so the unit under test is a
*level*, not a game.  The two levels share `step()` and differ only in a
`LevelSpec`: walls, cart start, switch, door, both portals, both exits, goal.
No cell coordinate is shared between them.

**Why this is the right unit.** The alternative — two unrelated worlds — would
test something A3 does not claim (that a manual generalises across mechanics)
and would make a negative result uninterpretable.  Theoria §1.10a is explicit
that the transfer claim is about *domain* portability across *problems*, which
is exactly a level change.

**What it costs.** A3 says nothing about transfer between games with different
mechanics.  Levels of one game is the weakest interesting reading of C3 and it
is the one Theoria's own wording licenses; anything stronger needs a different
experiment.  `A3_REPORT.md` §6 states the bound.

---

## D-A3-002 · The goal cell is not rendered, and is supplied per level

The goal is not discoverable from pixels in this world, and A3 does not pretend
otherwise.  PDDL puts the goal in the problem file; so does A3.

**Why not render it.** A rendered goal marker is a coloured cell, so `free()`
is false there and no push rule would move the Cart onto it — the manual would
need four extra `enter_goal_<dir>` clauses, and the Cart standing on the marker
would reintroduce the occlusion of D-A3-003.  The mechanism set would have
grown to serve the instrument rather than the experiment.

**What it costs.** The transfer arm is *given* the goal cell.  That is a real
concession and it is metered, not asserted: `problem_frame.provenance` records
every Problem field as `derived_from_frame` or `supplied`, and the count goes
in the report's table.  What the arm is not given is any rule.

---

## D-A3-003 · The reused segmenter cannot see a mover landing on a marked cell

**A defect in `engine-rig`'s `mdl_segmenter`, surfaced by A3, worked around in
the world rather than in the engine.**

The first version of this world made each portal's exit the *other* portal's
cell, so that both landmarks could be read straight off frame 0.
`mdl_segmenter` matches frame *t* against *t+1* only, so when the mover lands
on a cell that already hosts a static track, the cheaper script is "the
resident recolours to 6" plus "the mover vanishes" — not "the mover jumped".

Measured, not predicted: the mover's track was absent in **19 of 326 frames**,
and the miner proposed `obj3_appear_<dir>` and `obj3_vanish_<dir>` rules
instead of any jump.  The run is preserved at `artifacts/finding_d_a3_003/`.

This is the **third** segmentation gap the A0 family has found in that engine,
after touching objects (A0) and re-identification across a vanish/return
(A0′ — whose `pipeline/reidentify.py` repairs the *static* object's identity but
not the mover's absorption).  It is reported upstream as a capability the
engine needs, not as a bug to be patched from here.

**The workaround and its price.** Portal exits are ordinary floor cells, which
matches A2's proven shape.  The price is that an exit is invisible in every
frame, so it joins the goal cell as supplied level data (D-A3-002).

---

## D-A3-004 · Three of the four co-derived forms do not honour the domain/problem split

`CONTRACTS/dsl_grammar_v0.2.md` says, in the expressivity boundary:

> **domain/problem split:** `word_table` + `semantics` + `rules` + `laws` are
> the domain and travel across levels.  Grid layout, initial state, landmark
> coordinates and weight vectors are the problem, and are supplied per level.

`goal` is conspicuously not in that list, and the backends disagree about what
that means:

| form | behaviour when `ast.goal is None` |
|---|---|
| PDDL | falls back to `problem.goal_cell` — **correct** |
| Python | emits `return False` — a theory that can never win, **silently** |
| Lean | scans the Python module for a goal cell and raises |
| Markdown | omits the section |

So a coordinate-free domain — the only kind that can travel — compiles to a
Python predictor whose `is_goal` is constantly false.  The cheap layer then
reports `goal_mismatch` anomalies, which reads like a wrong manual rather than
like a missing binding.

**Decision.** A3 supplies a **binder** in its own tree
(`a3pipeline/compile_a3.py`): a pure function that takes the domain AST and the
Problem and returns an AST with a `goal:` section synthesized from
`problem.goal_cell`, built from the parser's own AST node classes.  No string
surgery on the `.dsl`, and `theory/domain.dsl` on disk stays coordinate-free.

**Why a binder is the right shape and not just a patch.** domain + problem →
bound instance → four forms is what the split *means* operationally.  The
backends have half of it already (they bind `landmarks` from the Problem at
generation time); the goal is the one field where the binding step was missing.

**What it costs.** A3 is doing work the compiler should do, in a tree the
compiler's owner does not read.  Reported on `PARTNER_SYNC.md` to
theory-compiler.

---

## D-A3-005 · The PDDL backend cannot encode more than one portal

`gen_pddl_a0._action_jump` emits

```
:precondition (and (at ?from) (adj-<dir> ?from ?p) (portal-exit ?dest))
```

— a single global `(portal-exit ?c)` predicate shared by every jump action —
and `_problem` emits that fact **only for a landmark literally named
`portal_exit`**.  A3 has `exit_a` and `exit_b`, so the encoding is wrong twice:

1. **no fact is emitted at all**, the `jump` actions' preconditions are
   unsatisfiable, and the planner returns a confident **UNSAT for a correct
   manual** — with no warning anywhere;
2. even with the fact present, both jump families would draw from one
   destination set, so a plan could legally jump from portal A to `exit_b`.
   That is unsound, not merely incomplete.

A2 found the neighbouring defect (D-A2-006, the arena) on a world with one
portal; one portal is exactly the case where this second defect is invisible.

**Decision.** A PDDL-only rewrite in A3's tree: each jump action's
`(portal-exit ?dest)` becomes `(exit-<landmark> ?dest)`, the predicates are
declared, and the matching init facts are emitted.  The rule → landmark map is
read off the **AST** (each rule's `jumped(Cart, <name>)` effect), never guessed
from names, and the rewrite raises if an expected substring is not found
exactly once per jump action — a silent no-op there would produce a wrong plan
rather than a failure.

---

## D-A3-006 · Marked cells are addressable but not occupiable (A2's D-A2-006, re-derived)

`problem.arena` is floor plus dynamic cells, so a *static coloured* cell — a
portal entry — is in neither, its `cell` object and adjacency facts are never
emitted, and the jump actions cannot ground.  A2 diagnosed this and patched it
with `pddl_addressable`.

A3 re-derives the patch rather than importing A2's, for the reason set out in
`_bootstrap.py`: A2 is a sibling experiment, not a library, and importing it
would put a third module named `_bootstrap` on the path and couple A3's results
to another run's `artifacts/`.  Credit is in the docstring.  The Python and
Lean forms keep the unaugmented arena, because their arena means "states the
Cart can be in" and the Cart is never on a portal.

---

## D-A3-007 · The Lean invariant helper is keyed on the object's *name*

`gen_lean_a0.door_latch_invariant` looks for an axis literally named
`Button_colour`.  A3's toggle is called `Switch`, so the helper returns `None`,
and `generate_lean` falls back to

```python
built = ("true", "this instance has no latch; the invariant is vacuous")
```

— a Lean file whose `I` is `true`, whose `inv_init` / `inv_closed` / `inv_all`
all pass, whose `#print axioms` list is empty, and which **proves nothing**.
Every gate in the certify column is green.

**Decision.** A3 passes an explicit `switch_latch_invariant` builder, and
**keeps the vacuous version as an artefact** (`theory/generated_l1_vacuous/`)
so the report can put a green-but-empty certificate beside a green-and-real
one.  A2 built the same kind of pair deliberately, out of a holed manual; this
one arrives for free, from an object-naming convention, which makes it worse.

**Why not just name the object `Button`.** Because it is a toggle, and because
renaming to satisfy a helper would hide the defect rather than record it.

---

## D-A3-008 · The sweep covers every reachable (state, action) pair, in one trajectory

The explorer is an **edge cover**, not an episode: it takes an unexecuted
action if one is available at the current state and otherwise walks the
shortest path to the nearest state that has one.  333 frames for level 1, 339
for level 2, 100 % of reachable pairs in both.

**Why not an episode.** An episode's length depends on where the goal happens
to be, which would leak level geometry into the cost column and make the
two-arm comparison meaningless.  One policy, parameterised by nothing but the
level.

**Why this policy is even available.** Reversibility (F-12).  In an
irreversible world the "walk back to pending work" step is not always possible,
so an edge cover cannot be completed and coverage is capped by the order the
explorer happened to choose.

**What it costs.** 100 % coverage is not realistic for a live game, so A3's
cold-start bill is an *upper* bound on evidence and therefore a *conservative*
denominator for the transfer ratio: a cheaper level-1 arm would make the
transfer look better, not worse.  Stated in `A3_REPORT.md` §6.

---

## D-A3-009 · The meter counts structure, not time or tokens

Wall-clock and token counts are not recorded.  Neither is reproducible on this
box, and determinism is a requirement across this repo, not a nicety.  A3
therefore measures the *shape* of the bill — evidence consumed, engine stages,
candidates adjudicated, theorize rounds, clauses authored — and not its dollar
value.  `A3_REPORT.md` §6 says so where a reader would otherwise assume
otherwise.

---

## D-A3-010 · Two negative controls, not one

The prompt asked for one (a one-way portal).  A3 runs two, because one cannot
separate two different failures:

* **L2_ONEWAY** deletes the B → A leg.  Level 2 becomes **unsolvable**, so a
  manual that fails to notice does not merely mis-predict a step — it certifies
  a win that never happened.
* **L2_REWIRED** keeps the leg but lands the Cart elsewhere.  Level 2 stays
  **solvable in 14**, so the valve is tested against a *wrong prediction* rather
  than against unsolvability.

Both render **byte-identical first frames** to L2 — the edit is in the
transition function, not in the pixels — which is the point: no amount of
looking at the board reveals either one.  `_variant_of_l2` enforces the
identity by construction rather than by care.

---

## D-A3-008 · The toolchain hard-codes object *names*, in four places

The control arm named its mover `Agent` and its barrier `Gate` — reasonable
names for a world it had only seen through frames.  Four components assume
otherwise, and the manual was **correct and uncertifiable**:

| component | assumption | symptom |
|---|---|---|
| `certify.replay.ACTION_NAMES` | emits `("push", "Cart", <dir>)` | the manual's guards never fire |
| `gen_python_a0.generate_python` | `mover="Cart"` default the driver never overrides | the generated `ACTIONS` constant contradicts the manual |
| `gen_lean_a0.door_latch_invariant` and A3's own `switch_latch_invariant` | an axis named `Door_present` | returns `None`, no `theory.lean` is written |
| **A3's own `bind_goal`** (D-A3-004's fix) | emits `state.Cart_pos` | `AttributeError` at replay |

The evidence is at `artifacts/finding_d_a3_008/`: the `Agent`/`Gate` manual, its
generated `theory.py`, and the recorded failure.

**The fourth row is ours.**  A3 wrote the goal binder specifically to repair a
name-independence defect and reproduced the same hard-coding while doing it.
That is worth recording against ourselves rather than filing three upstream
findings and one silence: the assumption is pervasive enough that someone
actively fixing a neighbouring instance of it still made it.

**Decision.** The control arm was told the naming requirement — a property of
the tool, in the same category as the `?dir` grounding, and not a fact about
the other manual — and renamed.  The pre-rename manual is kept.  The cost is
charged to the control arm's bill as a theorize round.

---

## Incident A3-I1 · The control arm's blind was partially broken, by us, in round 3

**What happened.** The from-scratch control arm was run blind: no access to
`theory/domain.dsl`, `THEORIZE_LOG.md`, `A3_REPORT.md`, `a3world/` or the
referee's copy.  In round 3, diagnosing why no `theory.lean` was produced, its
holder read the docstring of `a3pipeline/compile_a3.switch_latch_invariant` —
which names the blinded manual's objects (`Switch`, `Door`), its law
`switch_door_latch`, and its ledger entry L-02.

**Who caused it.** Us.  The blind list named files, and that docstring is in a
module the arm was required to call.  The arm disclosed the read unprompted and
recommended the correct remedy itself.

**What it contaminates, exactly.**

* **Object names and the law's name: contaminated.**  No cross-arm agreement on
  naming may be claimed, and none is.  The rename in D-A3-008 makes the point
  moot anyway — we forced the names to match.
* **Every verdict: not contaminated.**  All of them were fixed in round 1, two
  rounds before the read.  Rounds 2–4 changed none, which the arm's log states
  round by round.
* **The convergence result: not contaminated**, because the report cites the
  **`as_written`** comparison — the manual as it stood *before* round 3, with
  `Agent`, `Gate`, `warp_a_exit`, `warp_b_exit` and seven lifted schemas.  That
  snapshot is preserved at
  `artifacts/finding_r09_blind/domain_l2_scratch_lifted.dsl` and is the only
  state `A3_REPORT.md` §4 quotes for agreement.
  `a3pipeline/agreement.py` reports both states side by side and a test fails
  if the pair ever collapses to one.

**What would have prevented it.** A blind list that named *modules the arm must
call* as well as files it must not open, or docstrings in shared modules
written so they do not restate the content of a blinded file.  The second is
cheap and is the better fix; it is not applied retroactively here because
editing `compile_a3.py` now would not un-read it.
