# v0.3 backward-compatibility check — the `peg` family

**Claim under test.** "Additions only": every manual the pre-change chain
compiled, the post-change chain compiles to the same thing.

**Verdict — HOLDS for the peg family.** All four forms are byte-identical for
both manuals. The only output differences are the two the brief names as
expected (`render(state, _exclude=())`, the `_free_except` helper) plus one
additive `build_ir` warning. Nothing in any rule guard, any effect body, the
`RULES` table, the PDDL, the Lean, or the Markdown changed. 83,072 exhaustive
`step` comparisons agree, including which of them raise.

## What was compared

| | |
|---|---|
| worktree | `C:\Users\user\Desktop\theoria\.worktrees\c7-dsl-v03-mentions` |
| baseline | `git archive HEAD theory-compiler/src` → `compat/baseline/`, HEAD = `f1346fb` (nothing committed on this branch) |
| current | the working tree: 8 modified files plus new `src/theory_compiler/writes.py` |
| suite before starting | `python -m pytest -q` → **288 passed, 1 skipped** |
| harness | `compat/gen_forms.py` (four forms, both trees), `compat/pp.py` (pretty-printer round trip), `compat/step_equiv.py` (successor equivalence) |
| outputs | `compat/out/base/*` vs `compat/out/cur/*`; raw hunks also in `compat/out/peg.hunks.md`, step log in `compat/out/step_equiv.txt` |

Manuals in scope:

* `tests/fixtures/peg_theory.dsl` + `peg5_problem.json` — label `peg5`
* `tests/fixtures/peg4_theory.dsl` + `peg4_problem.json` — label `peg4`
* `tests/fixtures/peg_playbook.dsl` — a playbook; it has no four-form route,
  only `parse_playbook`, so it was checked by parse + `print_playbook` round trip

Those are all three `peg*.dsl` fixtures in the tree.

Entry points, with the arguments the repository's own tests use
(`tests/test_e2e_rehearsal.py`, `tests/test_gen_lean.py`,
`tests/test_ic3_certificate.py`):

```
generate_python(ast, problem)
generate_pddl(ast, problem_name=<label>, grid_width=5|4, grid_height=1)
generate_markdown(ast)                and  generate_markdown(ast, build_ir(ast, problem))
generate_lean(ast, problem, cert, proof="computational" | "algebraic")
    peg5 cert = engine-rig/interop/certificates/pagoda_5_11011_to_00010.json  (load_certificate)
    peg4 cert = tests/fixtures/ic3_peg4_0111_to_0100.json                     (load_ic3_certificate)
```

Both Lean proof modes were generated because the algebraic development takes a
different route through the certificate and would hide a drift the
computational one shows, and vice versa.

## Result matrix

| form | peg5 | peg4 |
|---|---|---|
| `gen_python.generate_python` | **DIFFERS** (helpers only — hunks below) | **DIFFERS** (helpers only — hunks below) |
| `gen_pddl` domain | IDENTICAL | IDENTICAL |
| `gen_pddl` problem | IDENTICAL | IDENTICAL |
| `gen_markdown` (bare) | IDENTICAL | IDENTICAL |
| `gen_markdown` (with IR) | IDENTICAL | IDENTICAL |
| `gen_lean` computational | IDENTICAL | IDENTICAL |
| `gen_lean` algebraic | IDENTICAL | IDENTICAL |
| `pretty_printer.print_theory` | IDENTICAL | IDENTICAL |
| `build_ir(...).warnings` | **DIFFERS** (one added — hunk below) | **DIFFERS** (one added — hunk below) |

`print_playbook(parse_playbook(peg_playbook.dsl))` — IDENTICAL.

No ERROR and no traceback on either side, for any form, for either manual.

### sha256 (first 16 hex) of every artefact

```
peg4.algebraic.lean        base=f9f3f5a55c85c7b0 cur=f9f3f5a55c85c7b0
peg4.computational.lean    base=759576749b5e2dde cur=759576749b5e2dde
peg4.domain.pddl           base=77f5c8ca06afb585 cur=77f5c8ca06afb585
peg4.ir.md                 base=f5b7e4cbefb2873e cur=f5b7e4cbefb2873e
peg4.md                    base=f5b7e4cbefb2873e cur=f5b7e4cbefb2873e
peg4.pp.dsl                base=c60b1cf9a88fcffa cur=c60b1cf9a88fcffa
peg4.problem.pddl          base=868fd140c5635aac cur=868fd140c5635aac
peg4.python.py             base=c3c9430e530f165e cur=dbfb5d47bb2e51a7   <-- differs
peg4.warnings.txt          base=37517e5f3dc66819 cur=a05dbf9ea64f167c   <-- differs
peg5.algebraic.lean        base=cc233463b37658cd cur=cc233463b37658cd
peg5.computational.lean    base=951981b68c6a0785 cur=951981b68c6a0785
peg5.domain.pddl           base=77f5c8ca06afb585 cur=77f5c8ca06afb585
peg5.ir.md                 base=2761cf36fe33f686 cur=2761cf36fe33f686
peg5.md                    base=2761cf36fe33f686 cur=2761cf36fe33f686
peg5.pp.dsl                base=425eea321d83421d cur=425eea321d83421d
peg5.problem.pddl          base=418f32c6d6993e16 cur=418f32c6d6993e16
peg5.python.py             base=f6372ec3d11280d9 cur=b78c852c43e63c01   <-- differs
peg5.warnings.txt          base=1b4a3ad9d48f93f8 cur=e446bf2f807d75d7   <-- differs
peg_playbook.pp.dsl        base=4b29963f68c8454f cur=4b29963f68c8454f
```

Side observation, not a finding of this change: `peg4.domain.pddl` and
`peg5.domain.pddl` hash the same (`77f5c8ca...`) on **both** sides. The two
manuals' `rules:` sections are textually identical and `_gen_domain` does not
vary with the board dimensions, so this is pre-existing and unchanged by v0.3.

## Scope of the python diff, stated precisely

The whole `gen_python` delta is two hunks in the helper block, lines ~52-90.
Everything from the first `def _guard_` to end of file is byte-identical.
Checked directly:

* `RULES` table (`sed -n '/^RULES = /,/^]/p'`) — **byte-equal** for both manuals.
* All 24 (peg5) / 12 (peg4) `_guard_*` and `_effect_*` bodies — inside the
  unchanged region of the unified diff, i.e. zero changed lines.
* `SEMANTICS`, `ACTIONS`, `State` field order, `initial_state`, `is_goal`,
  `occupancy`, `step` — unchanged; asserted programmatically in
  `step_equiv.py` before the sweep.

## Why the three semantic changes do not reach these manuals

* **`free(<obj>.pos)` self-exclusion (X-5).** Both peg manuals write
  `free(pos(?a.pos + 2))`. The argument is a `pos(...)` arithmetic cell — not a
  `NameRef` naming an instance and not a `FieldAccess` on `.pos` — so
  `gen_python._self_excluded` returns `[]`, `gen_pddl`'s new `UnsupportedClause`
  refusal does not trigger, `gen_markdown`'s new wording branch does not
  trigger, and `conflict._self_excluding` returns `False`, so `_free_terms`
  keeps the same key namespace and no disjointness verdict moves. Measured:
  **zero call sites** of `_free_except` in either generated module — the helper
  is emitted and never invoked.

  ```
  $ grep -n "_free_except" cur/peg5.python.py
  59:    for `_free_except` and ledger X-5: asking whether an object's
  86:def _free_except(state, cell, exclude):
  ```

  Line 59 is the `render` docstring, line 86 the definition. peg4 is the same
  at lines 57 and 82. So the X-5 behaviour change has no reach here at all;
  the peg python module gains dead code and nothing else.

* **`writes { ... }` clause and the fail-closed rule for unknown events.**
  Neither manual carries a `writes` clause, so both resolve through
  `DEFAULT_WRITE_SETS`. Their only event is `jumped/3`, which the published
  table maps to `(0, 1)` — the mover and the peg jumped over — matching the old
  `conflict.CLAIMED_ARGS` entry exactly. `gen_python`'s compiled effect assigns
  `{?a, ?b}`, so the new `check_backend_agreement` passes on all 24 / 12 ground
  rules and the fail-closed branch never fires. The entire cost to these
  manuals is the one added warning.

* **`conflict._occupancy_terms`, the new disjointness route.** It requires a
  type with no `alive`/`present` observation (`uniq.has_aliveness[t]` false).
  `Peg` declares `alive: Bool`, so every candidate clause is skipped and no
  conflict verdict changes. Confirmed by `ir.warnings` carrying no conflict
  text on either side.

* **`stayed/1` narrowed from `(0,)` to `()`, and the `ahead` / `beyond` cell
  functions.** Neither manual mentions `stayed`, `ahead`, or `beyond`.

## Step equivalence

Not a sample — **exhaustive over the representable state space**, which for
these worlds is small enough to enumerate outright. A state is `(pos, alive)`
per instance, so the space is `(N_POS * 2) ** n_instances`. Every representable
state was crossed with every action in `ACTIONS`, and the two modules' results
compared, treating a raised exception as a result (exception type plus message)
rather than skipping it.

Representable rather than reachable on purpose: the reachable set is 5 states
for peg5 and 2 for peg4 and would never enter the guard branches this change
touches. The illegal-looking states — two live pegs on one cell — are where a
drift would show, and are also where `conflict exclusive` raises.

```
peg5: fields=['Peg_0_pos','Peg_0_alive','Peg_1_pos','Peg_1_alive',
              'Peg_3_pos','Peg_3_alive','Peg_4_pos','Peg_4_alive']
      actions=8  representable_states=10000  pairs=80000
      successors_equal=80000  mismatches=0   (returned a state 79400, raised 600)
      is_goal disagreements=0   occupancy disagreements=0
      BFS-reachable from initial_state: base=5 cur=5 identical=True

peg4: fields=['Peg_1_pos','Peg_1_alive','Peg_2_pos','Peg_2_alive',
              'Peg_3_pos','Peg_3_alive']
      actions=6  representable_states=512  pairs=3072
      successors_equal=3072  mismatches=0   (returned a state 3060, raised 12)
      is_goal disagreements=0   occupancy disagreements=0
      BFS-reachable from initial_state: base=2 cur=2 identical=True
```

83,072 (state, action) pairs, zero disagreements.

The 600 peg5 raises are `AmbiguousTransition` and match, count for count, the
600 collisions `peg_theory.dsl`'s own E-07 comment reports across "the 80,000
representable states". They raise identically on both sides, so the
`unique` / `conflict exclusive` path is untouched by the `CLAIMED_ARGS` →
`writes.DEFAULT_WRITE_SETS` move.

`render`, `occupancy` and `is_goal` were compared over the same exhaustive
space as well: `_exclude` defaults to `()` and every existing call site omits
it, so `render` returns the same frame on every representable state.

## The diffs, in full

### peg5.python.py

```diff
--- base/peg5.python.py
+++ cur/peg5.python.py
@@ -52,30 +52,47 @@
     return abs(a - b) == 1
 
 
-def render(state):
-    """The manual drawn back onto a frame."""
+def render(state, _exclude=()):
+    """The manual drawn back onto a frame.
+
+    `_exclude` leaves the named instances off the frame. It exists
+    for `_free_except` and ledger X-5: asking whether an object's
+    own cell is free is a question about the board and the *other*
+    objects, and painting the asker onto the frame first makes the
+    answer unconditionally False.
+    """
     grid = [BACKGROUND] * N_POS
-    if state.Peg_0_alive:
+    if 'Peg_0' not in _exclude and state.Peg_0_alive:
         grid[state.Peg_0_pos] = 1
-    if state.Peg_1_alive:
+    if 'Peg_1' not in _exclude and state.Peg_1_alive:
         grid[state.Peg_1_pos] = 1
-    if state.Peg_3_alive:
+    if 'Peg_3' not in _exclude and state.Peg_3_alive:
         grid[state.Peg_3_pos] = 1
-    if state.Peg_4_alive:
+    if 'Peg_4' not in _exclude and state.Peg_4_alive:
         grid[state.Peg_4_pos] = 1
     return grid
 
 
-def _cell_colour(state, cell):
+def _cell_colour(state, cell, _exclude=()):
     if not _in_bounds(cell):
         return None
-    return render(state)[cell]
+    return render(state, _exclude)[cell]
 
 
 def _free(state, cell):
     return _cell_colour(state, cell) == BACKGROUND
 
 
+def _free_except(state, cell, exclude):
+    """`free(<obj>.pos)` — is the asker's own cell a legal empty one?
+
+    Ledger X-5. On the board, not a wall, and nobody *else* on it.
+    False exactly when the object stands off the board, on a wall,
+    or on top of another object.
+    """
+    return _cell_colour(state, cell, exclude) == BACKGROUND
+
+
 def occupancy(state):
     """The frame as a bitstring — the view a pagoda weight sees."""
     cells = render(state)
```

### peg5.warnings.txt

```diff
--- base/peg5.warnings.txt
+++ cur/peg5.warnings.txt
@@ -1,3 +1,4 @@
 [
-  "theory.dsl declares `weights w over Peg.pos` and problem 'peg5-11011' supplies no vector; a certificate will have to."
+  "theory.dsl declares `weights w over Peg.pos` and problem 'peg5-11011' supplies no vector; a certificate will have to.",
+  "theory.dsl declares no `writes { ... }` for jumped/3, so their write sets come from v0.3's default table. The table is keyed by name and arity across all worlds; what a rule writes is a fact about this one. Declare them if the table is not what this manual means."
 ]
```

### peg4.python.py

```diff
--- base/peg4.python.py
+++ cur/peg4.python.py
@@ -50,28 +50,45 @@
     return abs(a - b) == 1
 
 
-def render(state):
-    """The manual drawn back onto a frame."""
+def render(state, _exclude=()):
+    """The manual drawn back onto a frame.
+
+    `_exclude` leaves the named instances off the frame. It exists
+    for `_free_except` and ledger X-5: asking whether an object's
+    own cell is free is a question about the board and the *other*
+    objects, and painting the asker onto the frame first makes the
+    answer unconditionally False.
+    """
     grid = [BACKGROUND] * N_POS
-    if state.Peg_1_alive:
+    if 'Peg_1' not in _exclude and state.Peg_1_alive:
         grid[state.Peg_1_pos] = 1
-    if state.Peg_2_alive:
+    if 'Peg_2' not in _exclude and state.Peg_2_alive:
         grid[state.Peg_2_pos] = 1
-    if state.Peg_3_alive:
+    if 'Peg_3' not in _exclude and state.Peg_3_alive:
         grid[state.Peg_3_pos] = 1
     return grid
 
 
-def _cell_colour(state, cell):
+def _cell_colour(state, cell, _exclude=()):
     if not _in_bounds(cell):
         return None
-    return render(state)[cell]
+    return render(state, _exclude)[cell]
 
 
 def _free(state, cell):
     return _cell_colour(state, cell) == BACKGROUND
 
 
+def _free_except(state, cell, exclude):
+    """`free(<obj>.pos)` — is the asker's own cell a legal empty one?
+
+    Ledger X-5. On the board, not a wall, and nobody *else* on it.
+    False exactly when the object stands off the board, on a wall,
+    or on top of another object.
+    """
+    return _cell_colour(state, cell, exclude) == BACKGROUND
+
+
 def occupancy(state):
     """The frame as a bitstring — the view a pagoda weight sees."""
     cells = render(state)
```

### peg4.warnings.txt

```diff
--- base/peg4.warnings.txt
+++ cur/peg4.warnings.txt
@@ -1 +1,3 @@
-[]
+[
+  "theory.dsl declares no `writes { ... }` for jumped/3, so their write sets come from v0.3's default table. The table is keyed by name and arity across all worlds; what a rule writes is a fact about this one. Declare them if the table is not what this manual means."
+]
```

## Assessment of each difference

| difference | finding? | why |
|---|---|---|
| `render(state, _exclude=())` signature + `'X' not in _exclude` guard | no — expected, brief names it | default `()`; every call site in the generated module omits the argument; exhaustively verified to return the same frame on all 10,000 / 512 representable states |
| `_cell_colour(state, cell, _exclude=())` threading | no | same reason; `_free` still calls it with two arguments |
| `_free_except` helper added | no — expected | defined, never called in either peg module |
| one added `build_ir` warning about `jumped/3` | no — intentional and additive; step 5's answer | `warnings` are legibility complaints, not errors, and the change is by design not-silent (E-03). It does say the peg manuals now compile with a warning they did not have before, which a caller asserting `ir.warnings == []` would notice — `peg4` went from `[]` to one entry |
| rule guards, effects, `RULES`, PDDL, Lean, Markdown | **none — all byte-identical** | |

## Verdict

**"Additions only" holds for the peg family**: all four co-derived forms are
byte-identical across the change for `peg_theory.dsl`/`peg5_problem.json` and
`peg4_theory.dsl`/`peg4_problem.json`, the generated predictors agree on all
83,072 exhaustive (state, action) pairs including all 612 raises, and the only
deltas are the expected `render`/`_free_except` plumbing plus one intentional
additive warning.
