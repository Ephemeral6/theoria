# DECISIONS — cold-start-a0

Design calls and their reasons. Anything tagged **上游缺陷** records a defect in
`engine-rig` or `theory-compiler` that blocked integration, what was done about
it, and which tagged milestone it touches.

---

## D-A0-001 · The A0 world is a latch world, not a sokoban

**Call.** Cart / Button / Door / Portal on a 9×9 grid. The Cart is pushed in four
directions; the Button is an *obstacle you push against* rather than a plate you
stand on; pressing it opens the Door; the Portal is a one-way shortcut with two
witnesses in the whole trajectory.

**Why the Button is not a floor plate.** A plate means the Cart stands on the
Button and occludes it. Occlusion makes a pixel belong to two objects at once,
which breaks the full-frame responsibility check (constraint 2) before the
theory ever gets a chance to be wrong for an interesting reason. The core
property the ticket asks for — *a rule that can only be stated by referring to a
second object* — survives intact: the Door's behaviour is not a function of the
Cart's position alone.

**Consequence.** No pixel is ever contested. Every frame is exactly
board ⊎ Cart ⊎ Button ⊎ (Door, while it exists).

## D-A0-002 · The goal is given, not induced from pixels

The goal cell carries no marker. Rendering one would put the Cart on top of it in
the winning frame — occlusion again — and the win signal is available anyway:
`raw_trace.jsonl` carries a per-frame `win` flag, which is the A0 analogue of
ARC's score. The theorizer induces `goal` from the win flag, not from a colour.

## D-A0-003 · The explorer has oracle access; the pipeline does not

`world/explorer.py` walks the ground-truth state graph to guarantee coverage. It
is a data generator, not an agent — the ticket asks for "系统性探索器…不需要智能
策略". Everything downstream of `raw_trace.jsonl` sees frames, actions and the
win flag only.

**Known coverage hole, by construction:** 233/236 state-action pairs. The Button
latch is irreversible, so of the four cells adjacent to the Button only the one
that presses it first can ever be observed pressing it; the other three
(state, action) pairs are unreachable once the latch is set. Listed explicitly in
`artifacts/trace_summary.json` under `uncovered_pairs`.

## D-A0-004 · Cascade semantics: one action, one frame

Pressing the Button recolours it **and** vanishes the Door in the *same*
transition. Theoria 1.8 leaves cascade semantics open pending the API check;
A0 has to pick one to be a world at all, and "action → single frame" is the
conservative choice — it is the shape `theory.py`, `theory.pddl` and the Lean
`step` all already assume, and it keeps `step : S → A → S` total and single
valued (constraint 9). The consequence for discovery is recorded honestly: the
Button's recolour and the Door's vanish are two events at one transition index,
and nothing in the evidence forces them to be read as cause and effect rather
than as coincidence.

## D-A0-005 · Board extraction runs before segmentation

Cells that hold the same value in every frame are board (Theoria 1.8,
"从不变的沉淀为棋盘"). Two frame sequences come out of it and both are used:

* the **object layer** (board cells forced to background) feeds
  `mdl_segmenter`, which narrates *what happened*;
* the **full frames** feed the guard vocabulary, which needs the walls to
  evaluate `free(strip(D))` at all.

Without this step the walls are a single connected component and the Door — a
gap in a wall — is glued to it. The split is the miner's own stated contract:
"the miner never re-derives what happened from pixels; it reads pixels only to
evaluate guards."

## D-A0-006 · Background is the modal colour of the *dynamic* cells

First implementation took the modal colour of the whole board and got `1` (wall),
because a bordered 9×9 grid has more wall pixels than floor pixels. Calling the
walls background collapses the entire interior into one component. The background
is defined instead as the colour the cells the board *cannot* explain show most
of the time — i.e. what a cell looks like with nothing on it.

## D-A0-007 · A second segmentation operator, chosen by MDL

**上游限制 (not a defect).** `mdl_segmenter`'s component proposal is 4-connected
and colour-agnostic, deliberately so (colour-splitting shatters multi-coloured
objects). In A0 the Cart is constantly adjacent to the Button, so the two merge
and the tracker fragments: **90 tracks, 88 vanishes, 87 appears** for a world
with three objects.

**Call.** Add the operator the world needs — 4-connected blobs of *uniform
colour* — to the operator space, and let the engine's own objective choose
between operators by total script bits. Theoria 1.8 specifies a *segmentation
operator hypothesis space* chosen per world, not a fixed operator, so this is
using the design rather than escaping it; and the choice is made by compression,
which is the criterion the framework already commits to.

**Mechanics.** `pipeline/segment_operators.py` rebinds
`mdl_segmenter.segmenter.connected_components` for the duration of one call and
restores it. The cost model, the bipartite matcher and the narration stay
upstream and unmodified. **No file in `engine-rig` is touched**, so no tag is
affected. The comparison table is carried in every `object_hypothesis` payload
under `operator_comparison`, so the choice is auditable from the candidate stream
alone.

## D-A0-008 · A relational guard vocabulary, with CEGIS left alone

`cegis_miner.atoms` can only talk about one object's strip and anchor — enough
for Fixture A, not enough to say "the cell the Cart is pushing into is the
Button". `pipeline/atoms_a0.py` supplies a vocabulary that adds

| atom | says |
|---|---|
| `tcolor(D)==k` | the mover's target strip is entirely colour `k` |
| `color(T)==k` | track `T` currently shows colour `k` |
| `present(T)` | track `T` exists in this frame |

`tcolor` is the generalisation Fixture A did not need: `free` is exactly
`tcolor==background`, and a Button is distinguishable from a wall only by colour.

**The synthesis itself is not reimplemented.** `cegis_miner.synthesize` and
`cegis_miner.enumerate_frontier` are called verbatim on masks over the new
vocabulary; both are generic over the atom type (they touch only the mask table
and `atom_order_key`), so the extended atoms duck-type the upstream `Atom` and
the CEGIS loop, the minimisation and the frontier enumeration all stay upstream.
Every emitted `rule_hypothesis` payload carries `"vocabulary":
"a0_relational_v1"` and `"driver": ".../multi_miner"` so the provenance is in the
stream, not only in this file.

`multi_miner` additionally lifts `none` rules (upstream lifts `move` rules only).

## D-A0-009 · The consumer-side frontier convention

The ticket's open question: does `candidates_schema.md` support hanging several
hypotheses off one event slot? **It does, and no extension was needed.** Two
mechanisms carry the frontier and both are already inside the frozen contract:

1. `payload.frontier` — a list of guards, which is the engine's own stable
   payload shape (`cegis_miner/README.md`). One candidate row, many hypotheses.
2. Several rows with the same `payload.name` and different payloads. `status` is
   `"candidate"` on all of them and the file is append-only, so nothing in the
   contract is strained.

**Consumer-side convention adopted here** (binding on this directory only, since
`/CONTRACTS/` is frozen):

* the theorize step evaluates **each guard in `payload.frontier` separately**,
  and `THEORIZE_LOG.md` records a verdict per guard, not per candidate row;
* a rule is written into `theory.dsl` only when exactly one frontier member
  survives adjudication. If several survive and a probe can separate them, the
  rule is logged `probe-pending`. If several survive and **no** experiment in
  this world can separate them, they are extensionally identical here, and the
  tie is broken by description length with the reason recorded — that is a
  decision the evidence genuinely cannot make, and pretending otherwise would be
  the dishonest move;
* `probe_frontier` output is split into two tiers, **executable** (a state the
  trajectory actually visited, reachable by prefix replay) and **hypothetical**
  (a one-edit variation on such a state). Only the executable tier is emitted as
  a `probe_design` candidate. A frontier with no split in either tier is reported
  as such.

## D-A0-010 · `zero_space` is asked about the arena, not the pixels

The engine's cell set is *floor plus every cell the board cannot explain*. Using
only the dynamic cells would make the unsolvability law inexpressible — in the
no-Button variant the entire right room is static, hence board, and a law saying
"the Cart never enters the right room" would have no cells to be about. Only the
`global` laws are emitted as candidates; `cell_local` laws are laws about the
encoding by the engine's own README, and are counted in the report instead.

## D-A0-011 · Lean generation is A0's own, not `theory-compiler`'s

**上游限制 (not a defect).** `theory_compiler.generators.gen_lean.generate_lean`
ignores its `TheoryAST` argument entirely: it BFS-es 1D peg solitaire and emits a
`PegState` structure. It is a correct generator for A1's rehearsal and structurally
inapplicable to any other world. `gen_python` is nearly as specialised — it
hard-codes the `moved` and `teleported` events and assumes one instance per object
type.

**Call.** Reuse `theory_compiler.parser` — which *is* generic, and which is the
executable form of the frozen `dsl_grammar_v0.1` contract — and write A0's own
backends in `cold-start-a0/compile/`. Nothing upstream is modified; no tag is
affected. This is recorded as a **gap in the compiler track's coverage**, not as
a defect: the generators were built and tagged against a hand-written peg DSL and
were never claimed to be world-general.

## D-A0-012 · Lean toolchain fetched locally, not committed

`lake`, `lean` and `elan` were all absent from PATH at the start of this sprint.
Rather than downgrade the expensive certify layer, the toolchain pinned by
`theory-compiler/lean/lean-toolchain` (`leanprover/lean4:v4.9.0`) was fetched
into `cold-start-a0/.toolchain/` and gitignored — 278 MB of binaries do not
belong in the repository, and Phase 4's release manifest publishes every tracked
file. `certify/lean_check.py` looks for `lean` in this order: `$LEAN` →
`.toolchain/lean-4.9.0-windows/bin/lean` → `PATH`. If none is found it says so
and returns `unavailable`; it never silently downgrades a proof to a claim.

Reproduction, for anyone re-running this:

```bash
curl -sSL -o lean.zip \
  https://github.com/leanprover/lean4/releases/download/v4.9.0/lean-4.9.0-windows.zip
unzip -q lean.zip -d cold-start-a0/.toolchain/
```

The generated `theory.lean` deliberately uses **no Mathlib**, so `lean` alone is
enough and `lake` is never invoked.

## D-A0-013 · Nested parentheses in an event argument, worked around

**上游缺陷 (theory-compiler, minor).**
`theory_compiler.parser.theory_parser.TheoryParser._parse_func_call` matches the
argument list with `r'(\w+)\(([^)]*)\)'`, which stops at the first `)`. The `then`
clause of a rule goes through that function, so an event with a nested call or a
tuple argument — `then jumped(Cart, (1, 1))` — silently parses its second
argument as the malformed name `(1, 1`. No exception is raised; the AST is just
wrong. (`_parse_expr`, used for guards, uses a greedy pattern and is unaffected,
which is why `colored(leftof(Cart), 7)` parses correctly.)

**Not fixed upstream, and no tag is affected.** The workaround is a better design
anyway: the Portal's exit cell is *problem* data, not *domain* data, so the rule
says `then jumped(Cart, portal_exit)` and the landmark's coordinates live in the
problem instance. Logged here so the compiler track can see it; the defect is
real and will bite any DSL that needs a tuple in an event.

---

# Follow-ups (A0_REPORT §7, items 1–4)

## D-A0-014 · `semantics:` is a local dialect, not a contract edit

`CONTRACTS/dsl_grammar_v0.1.md` is frozen and owned by the compiler track, so the
frame axiom could not be added there. It is implemented in
`compile/dialect.py`, used by all four backends, and written up as a formal
extension request in `proposals/dsl_grammar_v0.2_semantics.md`.

Three statements over closed value sets — `frame`, `conflict`, `cascade` — each
closing a hole the A0 sprint fell into: the frame axiom (E-03), constraint 9's
two discharge routes, and Theoria 1.8's deferred cascade question.

**The section is mandatory here.** The v0.1 parser skips lines it does not
recognise, so a manual carrying it still parses upstream — silently, and to a
different world. That is the hazard the section exists to close, not graceful
degradation, so `compile_a0.py` raises `SemanticsError` on a manual that does not
declare its semantics rather than assuming a default. The proposal asks for the
same rule in v0.2.

## D-A0-015 · The concept account prices a responsibility-complete alternative

A0's accounting compared "the object" against "its pixel edits", charged the
object 21 bits of declaration and the alternative none. `pipeline/concept_account.py`
replaces it with a three-term verdict:

* **script** — the object's declaration plus its events, against a
  responsibility-complete raw encoding of the same pixels *including their
  frame-0 declaration*;
* **expressibility** — is any law or rule *effect* stated over the object? The
  invariant language is counts, parity and finite weights over objects, so there
  is no pixel-level paraphrase of `count(Button, 8) + count(Door) = 1`;
* **verdict** — `mandatory` (dropping it breaks responsibility or costs a law the
  DSL cannot restate) · `pays` · `rejected`.

Effect on A0: Button −17 → **−5**, Door −13 → **−1**. Both still fail to pay for
themselves on the trace, and both are `mandatory`. The conflict reported in
`A0_REPORT.md` §4 is therefore **narrowed but not dissolved**, which is the
honest outcome: for an object with one event in 275 transitions the object
framing is not a compression win on the *trace*, it is a win on the *manual* —
which is what Theoria 1.8 actually says ("它让**说明书**变短").

## D-A0-016 · A0′ changes three things and nothing else

`prime/` — the second self-built world, built against A0's own post-mortem:
toggle instead of latch, a Crate that is an obstacle but not a wall, and an
explorer truncated at **40 % of the exhaustive walk, a fraction fixed once before
looking at the gaps it produced**. Everything else is A0's geometry, so the
comparison is clean. Result and diagnosis: `prime/A0P_REPORT.md`.

## D-A0-017 · Track re-identification, priced

**上游限制 (not a defect).** `mdl_segmenter` matches frame *t* against *t+1*, so
an object that vanishes and returns is a fresh track every time. A0 never saw it
— its Door opened once. A0′'s toggle produced **five Doors**.

`pipeline/reidentify.py` merges same-template, disjoint-lifetime tracks and is
applied only when the script gets shorter (7 → 3, 48 bits on A0′; 68 → 6 on the
colour-agnostic operator). This is Theoria 1.8's template-matching operator, and
it is the second capability gap the A0 family has found in the segmenter. Upstream
is untouched; the pass consumes a `Segmentation` and returns a new one.

Consequence worth noting: the pass also repairs part of the colour-agnostic
operator's fragmentation (90 → 6 on A0), which is why
`test_uniform_colour_operator_wins_on_script_bits` now asserts fragmentation on
the pre-merge count.

## D-A0-018 · ~~BLOCKER~~ **RESOLVED** — Fast Downward is connected

**Resolved on 2026-07-28**, after the user authorised installing it. Route:
winlibs mingw-w64 gcc 16.1.0 (no installer, unpacked into the gitignored
`.toolchain/`), then CMake + Ninja directly — **not** `build.py`, which
hard-codes `NMake Makefiles` on Windows and therefore needs MSVC. 235/235
targets, ~90 s, no patches. Full recipe and results:
`BLOCKER_FAST_DOWNWARD.md`.

Result: FD agrees with the bundled BFS on all three compiled instances —
`a0-base` SAT/12, `a0p-base` SAT/10, and `a0-no-button` **proved UNSAT**, which
is the row that matters because it puts the planner and M5's impossibility
theorem in agreement instead of taking one on trust. Setting `FAST_DOWNWARD` was
the entire integration; **no caller code changed.**

The three attempts that had failed before, kept for the record:

1. the Lean toolchain's bundled `clang` 15 — no C++ standard library headers
   (`fatal error: 'vector' file not found`);
2. `conda install -c conda-forge m2w64-toolchain` — `RemoveError: 'setuptools'
   is a dependency of conda and cannot be removed from conda's operating
   environment`;
3. direct winlibs / mingw-builds release URLs — 404. **This third record was
   my error, and it is corrected here rather than left standing:** the URLs are
   fine, I guessed release tags instead of looking them up, and the GitHub API
   was rate-limited so I could not enumerate the real ones. The correct winlibs
   URL is in `BLOCKER_FAST_DOWNWARD.md` and answers `HTTP 206`. Attempts 1 and 2
   stand as recorded.

`cmake` 4.4.0 and `ninja` 1.13.0 are installed and `aibasel/downward` is cloned
to `.toolchain/downward` (commit `7120aa0`); **only the compiler is missing.**
Per the ticket's stopping rule this is recorded and left for human intervention.
Three routes, verification command, and expected results:
**`BLOCKER_FAST_DOWNWARD.md`**.

When a real Fast Downward becomes reachable, `certify/fd_conformance.py`
switches out of stand-in mode on its own and re-runs M4 through it on all three
compiled instances (`a0-base` SAT/12, `a0-no-button` UNSAT, `a0p-base` SAT/10),
writing `artifacts/fd_real.json`. No caller changes — which is the claim under
test.

`certify/fd_conformance.py` now has two modes and picks between them itself:
real Fast Downward when one is reachable, and the protocol stand-in otherwise, so
the suite still runs on a machine without a planner.

## D-A0-019 · Our PDDL was not standard-conformant; the stub was masking it

**Found within minutes of connecting the real planner.** The generated domain
declared `(:types buttoncell doorcell markedcell - cell)` and never introduced
`cell` itself. `fd_adapter`'s parser is lenient and accepted it all sprint; Fast
Downward's translator dies with `KeyError: 'cell'`.

Fixed in `compile/gen_pddl_a0.py` — the domain now emits `cell - object` on its
own line before the subtypes. Every PDDL this generator produced before today
would have been rejected by any standards-conformant planner, and nothing in the
pipeline could have told us. `test_generated_pddl_declares_every_type_it_uses`
keeps it fixed by parsing the `(:types …)` block and checking that every
supertype used is also declared.

## D-A0-020 · **上游缺陷** — `fd_adapter` cannot express "proved unsolvable" on the FD path

The bundled BFS reports unsolvability as
`RuntimeError("no plan exists for <problem>")`. Fast Downward reports it by
exiting **12** with no plan file, which `backends.run_fast_downward` turns into
`RuntimeError("Fast Downward produced no plan file (exit 12): …")` — the *same*
exception type it raises when FD genuinely crashes.

So on the FD path a caller cannot tell *the planner proved there is no plan* —
the branch that under constraint 6 triggers the certificate obligation and all of
M5 — from *the planner fell over*, which is an incident. That is the single
distinction the unsolvability work exists to make.

Handled here, not upstream: `certify/fd_unsat.py` owns the predicate and both
`plan_stage` and `fd_conformance` use it. Exit **13**
(`SEARCH_UNSOLVED_INCOMPLETE`) is deliberately not treated as UNSAT — an
incomplete search finding nothing is not a proof, and laundering it into one
would be exactly the "裸 UNSAT" constraint 6 forbids.

**Suggested upstream fix**, for `engine-rig` to take or leave: `solve()` returns
`None`, or raises a distinguishable `NoPlanExists`, on exit 12 — matching what
the stub already means.

## D-A0-021 · The reproducible pipeline still prefers the stub

`run_all.py` and `prime.run_prime` call `solve(..., prefer="stub")` even when a
planner is installed, so their checked-in artefacts stay byte-identical on a
machine with or without Fast Downward. The FD comparison is its own artefact,
`artifacts/fd_real.json`. Determinism of the committed stream is worth more here
than routing the default path through whichever planner happens to be present.
