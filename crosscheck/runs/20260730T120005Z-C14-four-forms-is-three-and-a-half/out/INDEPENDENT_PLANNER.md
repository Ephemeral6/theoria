# C14 deliverable (2) — what a planner that never heard of `gen_pddl` says

The producer saying its output is fine does not count. Every domain the generator
produced was fed to **Fast Downward 24.06+'s own translator** (`python -m translate`,
build at `cold-start-a0/.toolchain/downward/builds/release/bin`, machine-local and
gitignored) and, separately, to the `pddl` 0.4.8 PDDL-3.1 parser. Neither has ever
heard of `gen_pddl`. Raw logs: `fd_translate/*.fast-downward-translate.log`,
one per domain, returncode on line 1.

## Headline

| | |
|---|---|
| DSL theories with at least one rule | 37 |
| of those, the generator produced a domain for | 34 |
| of those, **Fast Downward's translator accepted** | **7** |
| theories the generator refused outright | 3 (18 rules) |

## The finding that matters: FD accepts only the empty ones

Cross-tabulating FD's verdict against the census's per-action verdict:

| FD verdict on the domain | actions in those domains | their defect profile |
|---|---|---|
| **accepted** (rc 0), 7 domains | 21 | **21/21 are `empty-precondition` + `empty-effect`** — every single one |
| rejected (rc 31 / crash), 27 domains | 264 | 152 `empty-effect`; 49 `undeclared-variable`; 37 `undeclared-predicate`; 17 both-empty; 8 var+pred; 1 mixed |

Fast Downward's acceptance is **anti-correlated with meaning**. The seven accepted
domains are the `theoria-arm` live-handbook snapshots, and they parse cleanly for
exactly one reason: they assert nothing. Domain `047-theory` in full — three actions,
each of them vacuous:

```pddl
  (:action key5-advances-marker
    :parameters ()
    :precondition (and
    )
    :effect (and
      (and)
    )
  )
```

An action with no precondition and no effect is always applicable and changes
nothing. A planner will parse it, then correctly ignore it. **"7 of 34 domains pass
a real planner" must never be reported as a partial success**: zero of the 21 actions
inside those 7 domains has any content. The correct reading is that the generator
produces either malformed PDDL or vacuous PDDL, and FD sorts it into exactly those
two bins.

## What FD actually said, grouped by distinct verdict

| rc | FD's message | domains |
|---|---|---|
| 31 | `Expected logical operator or predicate name` / `Got: adjacent-above` | 18 |
| 31 | `Undefined variable` / `Got: ?dest` | 4 |
| 1 | `TypeError: unhashable type: 'list'` — **translator crash** | 4 |
| 0 | `Done!` (accepted — and vacuous, see above) | 7 |

Verbatim, `001-a0_base` (undeclared predicate — the generator emitted `adjacent-above`
in a precondition while declaring `adjacent-up` in `(:predicates ...)`):

```
Parsing domain
	->Parsing axiom/action entry #1
	->Parsing action #1
	->Parsing action 'push-up'
	->Parsing precondition
	->Parsing condition
Expected logical operator or predicate name
Got: adjacent-above
```

`000-theory` (undeclared variable — `?dest` used in an effect, absent from
`:parameters`):

```
	->Parsing action 'walk'
	->Parsing effect
	->Parsing literal
Undefined variable
Got: ?dest
```

## The crash — a defect the action census could not see

Four problems do not merely get rejected, they **crash FD's translator** with an
unhandled `TypeError: unhashable type: 'list'` in
`translate/pddl_parser/parsing_functions.py:843`. The input that causes it is the
generated goal:

```pddl
  (:goal
    (= (and) 1)
  )
```

The generator emitted an equality between the logical connective `and` and the
integer `1`. FD's `check_predicate_and_terms_existence` then tries to hash the
parsed list `(and)` as a term name and dies.

This is why the census measures the **problem half** separately: a domain can be
flawless and still ship a problem with no goal, and a planning form whose goal is
nonsense is not a planning form. Of the 34 generated problems:

| goal verdict | problems |
|---|---|
| `placeholder` (contains the bare `(and)`) | 21 |
| `stated` (names a real predicate) | 13 |

So on the problem side too, **21 of 34 planning tasks have no goal to plan toward.**

## Second reader

The `pddl` 0.4.8 PDDL-3.1 parser was run over the same 34 pairs as a second blind
reader (`fd_translate/*.pddl-3.1-parser.log`). It is recorded for completeness; the
Fast Downward result above is the one the finding rests on, because FD is the
planner the engine rig actually uses (`engine-rig/fd_adapter`).

## Reproduce

```bash
python -m crosscheck.tools.c14_pddl_census --out <dir>
```

Requires a local FD build; `.toolchain/` is gitignored by design, so on a machine
without one the FD column reports `SKIPPED`, not `0 accepted`. The distinction is
load-bearing — "no planner ran" and "every domain rejected" render identically if
you are careless, and the script refuses to conflate them.
