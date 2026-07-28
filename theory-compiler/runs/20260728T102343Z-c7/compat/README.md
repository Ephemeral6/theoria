# Four-manual compatibility evidence

Four independent checks of one claim: **every manual the v0.2 chain compiled,
the v0.3 chain compiles, to the same world.** Each was run by a separate agent
against a baseline extracted with `git archive HEAD theory-compiler/src` (HEAD =
`f1346fb`, the base commit — nothing was committed on this branch at the time).

| report | manuals | verdict |
|---|---|---|
| [peg.md](peg.md) | `peg_theory`, `peg4_theory`, `peg_playbook` | additions only |
| [cold-start-a0.md](cold-start-a0.md) | `theory`, `theory_no_button`, `theory_prime`, `theory_prime_seeded` | additions only |
| [cold-start-a2.md](cold-start-a2.md) | `theory`, `theory_holed`, `theory_repaired` | additions only |
| [a0-spike.md](a0-spike.md) | `a0-spike/theory/theory.dsl` + the migrated fixture | outcome bit-for-bit unchanged |

**The measured shape, identical across all three compiling families.** PDDL,
Lean and Markdown byte-identical. `gen_python` differs in exactly three helper
hunks — `render(state, _exclude=())` with a per-instance `'X' not in _exclude`
conjunct, `_cell_colour`'s extra parameter, and the new `_free_except` — with
everything from the first `def _guard_` to EOF byte-identical. One added
warning per manual, naming the events whose write sets came from the default
table. Transition relations identical: 83,072 pairs for peg (representable, not
reachable), 792 for the a0 family, 604 for a2.

`_free_except` is emitted and **never called** in any of the three families:
peg writes `free(pos(?a.pos + 2))`, a0 and a2 write `free(above|below|leftof|rightof(Cart))`.
Not one existing manual names a cell through an object, which is why X-5 stayed
open long enough to cost 52 states in the one manual that needed to.

## The baseline trees and generated dumps are not kept

They are `git archive HEAD` plus the output of running two generators, both
reproducible in a minute from the harnesses beside this file. What is kept is
the four reports, which carry the diffs, the hashes and the counts.

## Two defects found in passing, neither caused by this change

Both pre-existing, both byte-identical across the change — evidence, not
regressions. Recorded in `CONTRACTS/dsl_grammar_v0.3.md` §5 and pinned by name
in `theory-compiler/tests/test_writes.py`:

* `gen_pddl` compiles every event outside `moved`/`teleported` to `:effect (and
  (and))`. Affected: `teleport-down`, `press-left`, `door-opens-left` in
  `cold-start-a0`; `teleport-down` in `theory_no_button`; sixteen
  `switch-*`/`door-*` actions across the two `prime` manuals.
* `push-left` and `push-right` emit `?dest` in their effect and never declare it
  as a parameter — the manuals write `free(leftof(Cart))` and
  `_extract_pred_pddl` matches only `above|below|left|right`. Those actions are
  malformed, and this one *over*-approximates applicability: the cart may push
  left through a wall.

A third, narrower one, from the a0-spike report: the **unrepaired** A0 manual
still gets silent invalid PDDL out of that backend while the **repaired** one is
refused, because the unrepaired guards are dropped before reaching v0.3's new
check. The refusal is right; what it exposes is how much `gen_pddl` was already
dropping.
