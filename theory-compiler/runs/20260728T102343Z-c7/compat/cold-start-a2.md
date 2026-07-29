# Backward-compatibility measurement — the cold-start-a2 manual family vs. DSL v0.3

Claim under test: **"additions only"** — every manual the pre-change chain
compiled, the post-change chain compiles to the same world.

Worktree `.worktrees/c7-dsl-v03-mentions`. Nothing is committed on this branch,
so `HEAD` is the pre-change tree. Measured 2026-07-28.

## Method

1. `cd theory-compiler && python -m pytest -q` → **318 passed, 1 skipped** (24.2s).
2. Baseline extracted with
   `git archive HEAD theory-compiler/src | tar -x -C a2fam-baseline/`.
   The baseline `src/theory_compiler/` has no `writes.py`, confirming the
   pre-change tree.
3. Each side run in its own process by `a2fam-driver.py <src> <out>`, which
   puts `<src>` at `sys.path[0]` and **asserts** `theory_compiler.__file__`
   resolves under `<src>`. (`pyproject.toml` declares an editable install
   pointing at the MAIN checkout; without the assert both sides silently
   measure the same tree.) Both asserts passed and the resolved paths are
   printed in the run log.
4. Artifacts: `a2fam-out-baseline/`, `a2fam-out-current/`.

Manuals and their problem instances (the pairing used by
`theory-compiler/tests/test_conflict.py::_manuals`):

| label | manual | problem |
|---|---|---|
| `a2` | `cold-start-a2/theory/theory.dsl` | `cold-start-a2/theory/generated/problem.json` |
| `a2-holed` | `cold-start-a2/theory/theory_holed.dsl` | `cold-start-a2/theory/generated_holed/problem.json` |
| `a2-repaired` | `cold-start-a2/theory/theory_repaired.dsl` | `cold-start-a2/theory/generated_repaired/problem.json` |

Forms generated per manual, both sides:
`generate_python(ast, problem)`;
`generate_pddl(ast, problem_name=<label>, grid_width=9, grid_height=9)` → the
(domain, problem) tuple;
`generate_markdown(ast)` **and** `generate_markdown(ast, ir)`;
`generate_lean(ast, problem, proof="computational")` and `proof="algebraic"`;
plus `ir.warnings`, the `check_conflict` report, and the full transition dump.

Note: A2's own pipeline (`cold-start-a2/a2pipeline/compile_a2.py`) compiles
these manuals with **A0's** backends, not `theory_compiler`'s. This measurement
deliberately drives `theory_compiler`'s own four generators, since those are
what v0.3 changed.

## Per-manual, per-form result

| file | result |
|---|---|
| `a2.py.txt` | **DIFFERS** (three benign helpers, hunk below) |
| `a2.domain.pddl` | IDENTICAL |
| `a2.problem.pddl` | IDENTICAL |
| `a2.md` / `a2.ir.md` | IDENTICAL |
| `a2.computational.lean` / `a2.algebraic.lean` | IDENTICAL |
| `a2.trans.txt` | IDENTICAL |
| `a2.conflict.json` | IDENTICAL |
| `a2.warnings.txt` | **DIFFERS** (one added warning, expected) |
| `a2-holed.py.txt` | **DIFFERS** (same three helpers) |
| `a2-holed.domain.pddl` | IDENTICAL |
| `a2-holed.problem.pddl` | IDENTICAL |
| `a2-holed.md` / `a2-holed.ir.md` | IDENTICAL |
| `a2-holed.computational.lean` / `a2-holed.algebraic.lean` | IDENTICAL |
| `a2-holed.trans.txt` | IDENTICAL |
| `a2-holed.conflict.json` | IDENTICAL |
| `a2-holed.warnings.txt` | **DIFFERS** (one added warning, expected) |
| `a2-repaired.py.txt` | **DIFFERS** (same three helpers) |
| `a2-repaired.domain.pddl` | IDENTICAL |
| `a2-repaired.problem.pddl` | IDENTICAL |
| `a2-repaired.md` / `a2-repaired.ir.md` | IDENTICAL |
| `a2-repaired.computational.lean` / `a2-repaired.algebraic.lean` | IDENTICAL |
| `a2-repaired.trans.txt` | IDENTICAL |
| `a2-repaired.conflict.json` | IDENTICAL |
| `a2-repaired.warnings.txt` | **DIFFERS** (one added warning, expected) |

No ERROR on either side, for any manual, for any form.

## The gen_python hunk (identical for all three manuals)

```diff
-def render(state):
-    """The manual drawn back onto a frame."""
+def render(state, _exclude=()):
+    """The manual drawn back onto a frame.
+
+    `_exclude` leaves the named instances off the frame. ...
+    """
     grid = [list(row) for row in BOARD]
-    if True:
+    if 'Button' not in _exclude:
         r, c = state.Button_pos
         grid[r][c] = state.Button_color
-    if True:
+    if 'Cart' not in _exclude:
         r, c = state.Cart_pos
         grid[r][c] = state.Cart_color
-    if state.Door_present:
+    if 'Door' not in _exclude and state.Door_present:
         r, c = state.Door_pos
         grid[r][c] = state.Door_color
     return grid

-def _cell_colour(state, cell):
+def _cell_colour(state, cell, _exclude=()):
     if not _in_bounds(cell):
         return None
-    return render(state)[cell[0]][cell[1]]
+    return render(state, _exclude)[cell[0]][cell[1]]

 def _free(state, cell): ...

+def _free_except(state, cell, exclude):
+    """`free(<obj>.pos)` — is the asker's own cell a legal empty one? ..."""
+    return _cell_colour(state, cell, exclude) == BACKGROUND
```

That is the whole of it: `render(state, _exclude=())` with per-instance
`if 'X' not in _exclude` guards, `_cell_colour(state, cell, _exclude=())`, and a
new `_free_except`. Nothing outside these three helpers changed — no rule body,
no guard, no `step`, no `ACTIONS`, no `initial_state`.

`_free_except` is **emitted but never called** in all three a2 manuals. Every
`free(...)` clause in the a2 family names a *neighbour* cell —
`free(above(Cart))`, `free(below(Cart))`, `free(leftof(Cart))`,
`free(rightof(Cart))` — never `free(<obj>.pos)`. The changed compilation of
`free(<obj>.pos)` is therefore untriggered here, which is why every guard line
in the generated python still reads `_free(state, _neighbour(...))` unchanged
on both sides.

For the same reason the v0.3 additions to `gen_markdown.py` (a natural-language
rendering for `free(<obj>.pos)`) and to `gen_pddl.py` (an `UnsupportedClause`
refusal for `free(<obj>.pos)`, since a STRIPS `(free ?c)` cannot express "free
except for X") are inert on a2: no a2 clause reaches either branch. Hence
byte-identical PDDL and Markdown.

## Warnings

`ir.warnings`, baseline → current:

**a2** (1 → 2), added:
> theory.dsl declares no `writes { ... }` for jumped/2, moved/2, recolored/2,
> vanished/1, so their write sets come from v0.3's default table. The table is
> keyed by name and arity across all worlds; what a rule writes is a fact about
> this one. Declare them if the table is not what this manual means.

Retained unchanged: the E-04 `portal_exit` landmark warning.

**a2-holed** (0 → 1), added: the same warning, for `moved/2, recolored/2,
vanished/1` (no `jumped/2` — the holed manual has no teleport rule).

**a2-repaired** (1 → 2), added: the same warning, same event list as `a2`
(`jumped/2, moved/2, recolored/2, vanished/1`). Retained: the E-04
`portal_exit` warning.

No warning was **removed** or **reworded** on any manual. None of the three a2
manuals declares a `writes { ... }` clause, and every event they use is in the
published default table — so the fail-closed rule for unknown events is never
reached.

## Conflict report

`check_conflict` called the way `build_ir` calls it on each side: baseline
without `writes=` (the parameter does not exist there), current with
`writes=ir.writes`. Both with `strict=False`, `uniq=Uniqueness(ast, problem)`,
`background=problem.background`.

All three `*.conflict.json` are **byte-identical** between the sides.

| manual | policy | green | ground rules | overlapping | disjoint | ordered | undischarged | unclaimable |
|---|---|---|---|---|---|---|---|---|
| `a2` | exclusive | true | 7 | 10 | 10 | 0 | 0 | 0 |
| `a2-holed` | exclusive | true | 6 | 6 | 6 | 0 | 0 | 0 |
| `a2-repaired` | exclusive | true | 7 | 10 | 10 | 0 | 0 | 0 |

- **Discharged-before-and-not-now: none.** The serious failure mode did not occur.
- **Newly discharged: none.** Every pair discharged on the current side was
  already discharged on the baseline side, and by the *same reason text*.
  9 of the 10 a2 / a2-repaired pairs discharge on "their action arguments differ
  at position 1 … distinct names denote distinct things"; the tenth,
  `push_down | teleport_down`, on "the first requires
  `free(c:toward(n:Cart,n:down))` — i.e. colour 0 — and the second requires
  colour(s) [3] of the same cell". All 6 a2-holed pairs discharge on the
  argument-position rule.
- The new disjointness rule in `conflict.py` fires on no a2 pair; every pair was
  already discharged by an older rule, so there was nothing left for it to
  reach.

## Step equivalence

BFS from `initial_state()` over `ACTIONS` in declaration order, dedup by
dataclass `repr`, cap 5000 (never hit). Then `state | action -> successor`
emitted for **every** (reachable state, action) pair.

| manual | ACTIONS | reachable states | (state, action) pairs | raised | result |
|---|---|---|---|---|---|
| `a2` | 4 | 55 | 220 | 0 | IDENTICAL |
| `a2-holed` | 4 | 41 | 164 | 0 | IDENTICAL |
| `a2-repaired` | 4 | 55 | 220 | 0 | IDENTICAL |

`ACTIONS` on all three is
`[('push','Cart','up'), ('push','Cart','down'), ('push','Cart','left'),
('push','Cart','right')]` — identical both sides. (`teleport_down` is a ground
rule but not an action head, so it enters the conflict report and not the BFS;
that is a property of the manual and is the same on both sides.)
`a2` and `a2-repaired` produce a byte-identical transition dump, as expected —
the two manuals differ in their Lean invariant, not in their dynamics.

## Verdict

**"Additions only" holds for the cold-start-a2 family.** a2 matches the
cold-start-a0 pattern exactly: gen_python differs only in the three benign
helper changes (`render(state, _exclude=())` with per-instance guards,
`_cell_colour(state, cell, _exclude=())`, and the new `_free_except`); PDDL,
Lean (both proof modes) and Markdown (both routes) are byte-identical; the
conflict report is byte-identical with no pair losing a discharge; the full
transition table over the reachable set is byte-identical; and the only warning
change is the one expected new "v0.3's default table" warning per manual.

## Files

Namespaced under `theory-compiler/runs/20260728T102343Z-c7/compat/`:

- `a2fam-driver.py` — the harness
- `a2fam-baseline/theory-compiler/src/` — pre-change tree from `git archive HEAD`
- `a2fam-out-baseline/`, `a2fam-out-current/` — 30 measurement files each
