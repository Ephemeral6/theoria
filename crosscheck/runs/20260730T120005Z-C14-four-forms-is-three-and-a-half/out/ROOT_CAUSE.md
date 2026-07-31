# Why the fourth form is empty — root cause, and what a fix would cost

Diagnostic read of `theory-compiler/src/theory_compiler/generators/gen_pddl.py`.
**Read-only. `theory-compiler/` is the other track's and is byte-untouched.** This
is a cross-track registration, not a repair. Line numbers are as of `cc7e414e`.

## Verdict: backend gap, not a grammar limit

For every defect class except three declared refusals, the information is present
in the AST and **three of the four backends consume it**. `gen_pddl` alone drops it.

| defect class | actions | gap | evidence |
|---|---|---|---|
| empty `:effect` | 190 | **backend** | `_event_to_pddl` dispatches on **name only, with two entries** (`moved`, `teleported`). `gen_python._effect` dispatches the same AST node on **(name, arity) across 9 events**; `gen_markdown` has a 10-entry table. |
| empty `:precondition` | 39 | **backend** | `_extract_pred_pddl` is a chain of `if`s **with no `else` at any level** — it knows three clause shapes and silently drops everything else. `gen_python` compiles `colored`, `adjacent`, field comparisons and arithmetic. |
| undeclared predicate | 45 | **backend — a two-word bug** | `gen_pddl.py:360`/`:368` interpolate the *DSL* spelling into the *PDDL* name (`adjacent-{above}`) while the hard-coded `(:predicates …)` block at `:99-106` declares `adjacent-up`/`adjacent-down`. `gen_python.py:50` holds the translation table gen_pddl lacks: `SPATIAL = {"above":"up","below":"down","leftof":"left","rightof":"right"}`. |
| undeclared variable | 58 | **backend — the same two words** | The recogniser at `:351` tests `inner.name in ("above","below","left","right")`, but the manuals write `leftof`/`rightof`. Those clauses drop, so `params["dest"]` is never created — while `_event_to_pddl` unconditionally writes `?dest` into the effect. |
| whole-file refusal | 3 files / 18 rules | **genuine design limit, declared** | see below |

The two placeholder emitters, verbatim:

```python
412	    if not effects:
413	        effects.append("(and)")  # empty effect placeholder
```

and the generator's own docstring at `:265-267` already confesses the other one:

> `_extract_pred_pddl` has no else-branch, so anything it does not recognise falls
> out of the precondition without a word.

## The decisive cross-backend evidence

Same file, same AST, run live — `cold-start-a0/theory/theory.dsl`:

| rule | `gen_pddl` | `gen_python` |
|---|---|---|
| `press-left` precondition | `(at ?cart ?cart-pos)` — `colored(leftof(Cart), 7)` **gone** | `if not (_cell_colour(state, _neighbour(state.Cart_pos,'left')) == 7): return False` |
| `press-left` effect | `(and (and))` | `state.Button_color = 8` |
| `door-opens-left` effect | `(and (and))` | `state.Door_present = False` |
| `teleport-down` effect | `(and (and))` | `state.Cart_pos = LANDMARKS['portal_exit']` |

`gen_lean` inherits all of it by construction — `gen_lean.py:98-102` `exec`s the
generated Python and reads the predictor out of it. `gen_markdown` has an
independent reader and renders all seven a0 rules in full, negation included.

## Three defects the census's four criteria cannot see

The census measures well-formedness and non-vacuity. That bar turns out to be
**too lenient**, not too strict: an action can satisfy all four criteria and still
be dead or wrong.

**1. The spurious direction parameter — fatal, and invisible to every criterion.**
`gen_pddl.py:300-307` makes a parameter out of *every* `NameRef` argument of
`act=…`, including the direction constants `up`/`down`/`left`/`right`, typed
`"object"` because they are not declared object types. No object of type `object`
is ever declared in `_gen_problem`, so **the parameter cannot bind and the action
vanishes at grounding.** Measured directly — take the a0 domain, patch *only* the
predicate-name defect, and ground with the track's own `strips.ground`:

```
with the ?up / ?down parameter:      0 ground actions
without it:                        144 ground actions
```

**Fixing the eight identifiers alone therefore buys nothing**: the domain becomes
parseable and still grounds to zero actions. See the correction in
`REPAIR_DISTANCE.md`.

**2. `GuardPredicate.negated` is never read.** `grep -n negated gen_pddl.py` →
no hits. `gen_python.py:293` and `gen_markdown.py:285-287` honour it. Today this is
masked, because the negated clauses in this corpus use spellings gen_pddl already
fails to recognise — **so fixing the spelling bug unmasks it, and a dropped
negation becomes an inverted one.** Any repair must do both or neither.

**3. Landmarks become free parameters.** `_event_to_pddl:402-407` turns
`teleported(Cart, origin)` into `?origin - cell`, existentially quantified — the
teleport may land anywhere. Invisible to all four criteria *and* to `strips.ground`.

Also: `generate_pddl` never calls `expand_theory`, so a `forall ?d in dir` schema
reaches the generator carrying `VarRef` nodes no branch matches, and the direction
disappears entirely — `tests/fixtures/cart_theory.dsl` compiles to **one** action
`push` with no direction at all.

## The test that pins the bug, and what a fix breaks

`theory-compiler/tests/test_writes.py:377-439`, `TestBackendObligationShortfall`.
Both assertions are **exact set equalities**, so a fix makes them fail — by design:

```python
394	    # Measured on `cold-start-a0/theory/theory.dsl`, 2026-07-28.
395	    EMPTY_EFFECT = {"teleport-down", "press-left", "door-opens-left"}
396	    UNDECLARED_DEST = {"push-left", "push-right"}
```
```python
410	        assert empty == self.EMPTY_EFFECT, (
411	            "the set of actions gen_pddl compiles to an empty effect has "
412	            "changed: %r. If it shrank, delete this pin and celebrate. …"
```

The class docstring says outright: *"the day `gen_pddl` grows the events, this test
goes red and gets deleted."* **This is a pin, not a spec — the honest kind.** It
records a known shortfall by name so it cannot drift silently. C14's finding is not
that this test exists; it is that the *paper* never inherited what the test knows.

Blast radius of a real fix, concretely:

1. `tests/test_e2e_rehearsal.py:71` — `test_peg_still_produces_all_four_forms`
   asserts `":action" in domain` for a **line world**; a fix that refuses
   unencodable guards makes it raise. The one currently-green test outside
   `test_writes.py` that a correct fix breaks.
2. Both `handover_packages/*/MANIFEST.json` pin `"planning_domain": {"status":
   "refused", "why": "StripsError: action 'push-up' mentions undeclared predicate
   'adjacent-above'"}`. A fix flips these to `generated`, adds new files and
   sha256s, and breaks `tools/verify_c8.py` checks 2–3 and
   `tests/test_handover.py:165` until the packages are rebuilt and re-sealed.
   **This is the "changes the fourth form of four manuals" cost, concretely.**
3. `CONTRACTS/dsl_grammar_v0.3.md` §5 states the shortfall as normative contract
   text and becomes false.
4. **`tests/test_gen_pddl.py`'s six cart tests all survive a fix — because they
   cannot see any of the defects.** They assert balanced parens, `":action" in
   domain`, `":predicates" in domain`, and the absence of `(at \d+ \d+)`. They pass
   today on a domain with one direction-less action whose effect references an
   undeclared `?dest`. The PDDL generator's own test file is blind to all six
   defect classes.

## The three refusals are the good part

`UnsupportedClause`, raised deliberately with a written rationale — not crashes:

* `gen_pddl.py:344-350` (X-5, `free(<obj>.pos)`) — *"…has no way to say `free
  except for %s`. Refusing rather than dropping the precondition."* Hits
  `tests/fixtures/sokoban2_theory.dsl` and `handover_packages/a0-sokoban2/manual/MANUAL.dsl`, 6 rules each.
* `_refuse_count`, `:272-280` (E-08, counting guards) — *"Refusing rather than
  dropping the precondition — a dropped one yields a domain whose gate opens
  unconditionally."* Hits `tests/fixtures/countlock_theory.dsl`, 6 rules.

6+6+6 = **18 rules, matching the census exactly.** These are the only two places
this generator declines to approximate, and the only two classes that are genuine
design limits. Everything else is a silent drop with the same consequence and none
of the honesty.

## Suggested fix, ordered by leverage — for the theory-compiler track

Registered as a proposal. This territory attempted none of it and may not.

1. **Stop parameterising direction constants** (`:300-307`). Enables everything
   else; without it every action grounds to zero regardless of what is fixed.
2. **Add the spatial translation table** — reuse `gen_python.py:50`'s `SPATIAL`,
   recognise the DSL spelling and emit the PDDL one. Clears the undeclared-predicate
   (45) and undeclared-variable (58) classes; same root cause.
3. **Dispatch events on (name, arity)** from the table `gen_python` and
   `gen_markdown` already carry. Needs a colour proposition and `(present ?o)` in
   the predicates block. Clears ≈150 of the 190 empty effects.
4. **Delete the `(and)` placeholder at `:412-413` and raise instead** — what
   `gen_python.py:379-382` already does. Turns the residual ≈40 into declared
   refusals.
5. **Give `_extract_pred_pddl` an `else` that raises**, and encode `colored`,
   `<inst>.pos` and `adjacent`. Clears the 39, and — more important — the larger
   set of actions that are not empty but *silently weakened*.
6. **Call `expand_theory(ast)`** at the top of `generate_pddl`, as every other
   backend gets via `build_ir`.
7. **(mandatory companion) Honour `negated`** — or item 2 turns ~30 dropped
   negations into inverted ones.
8. **(companion) Resolve landmarks to constants**, not free cell parameters.

### What needs a grammar or contract change, not a backend change

| limit | the change to name |
|---|---|
| counting guards (E-08), 6 rules | lift `(:requirements)` off pure STRIPS, **or** add a bounded-counter declaration to `word_table:` so the compiler can emit a finite threshold chain instead of inventing the bound |
| `free(<obj>.pos)` self-exclusion (X-5), 12 rules | **split `free` in the grammar** into `on_board(c)` and `unoccupied(c)`; `free(Box.pos)` then becomes exactly encodable. A `CONTRACTS/dsl_grammar` change. |
| line geometry (peg) | not a grammar change — gen_pddl already knows how to refuse it (`:64-68`), it just never does on the domain path because the refusal is conditional on a `ProblemSpec` the domain path never passes |
| negative preconditions | a `:requirements` change, plus the matching change to `strips.py:316` |

### The highest-value structural change

`theory_compiler/strips.py` is this track's own STRIPS front end and it **already
refuses every one of the four classes** — undeclared predicate (`:324`), unbound
variable (`:333`), empty effect (`:340`), wrong arity (`:326`). `handover.check_pddl`
runs it, which is exactly why both shipped packages honestly report
`planning_domain: refused` today.

**Move that check inside `generate_pddl` itself**, so the generator cannot return a
domain its own reader refuses. That converts every defect class here from a silent
unsoundness into a refusal at the moment of generation, independent of whether
items 2–6 ever land. `handover.py:1223-1225` already states the principle:

> A form generated is not a form checked. A backend that cannot yet emit a sound
> encoding is a declared gap; one that emits an unsound encoding under a green
> status is a trap.

Caveat: `strips.ground` would **not** catch the spurious-direction-parameter defect
as an error — it grounds to zero actions, and only `check_pddl`'s second assertion
(`if not task.actions`) catches that. It would not catch the landmark defect at all.
