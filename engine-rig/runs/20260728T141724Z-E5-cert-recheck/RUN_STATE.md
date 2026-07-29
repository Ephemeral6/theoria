# E5-cert-recheck — an independent complaint department for the certificates

**Verdict: both acceptance lines pass, and the adversarial half found four real
defects, all fixed and all now standing tests.**

```bash
cd engine-rig
python -m recheck.verify_all --out runs/20260728T141724Z-E5-cert-recheck
python -m pytest                                # 315 passed, 9 skipped
```

`recheck_report.json` is this run's machine-readable output. `VERDICT GREEN`.

---

## 1 · What the item asked for, and what it got

> 造一个独立复核器：不看引擎实现、只拿证书与规则集，逐条验算三条件。

`recheck/` takes two files. A **rule set** declares finite variables with
explicit domains, an initial assignment, a goal predicate and a list of guarded
rules; a **certificate** carries a predicate and the claim it licenses. The
state space is the full Cartesian product of the declared domains and every edge
is computed here by grounding the rules. No edge list is ever read, no state
space ever comes from the certificate, and nothing in the package imports
`engines/` — enforced by `test_recheck_never_imports_the_engines`, not asserted.

That was the one design decision everything else follows from (D-028). The
failure it is against is not an engine that lies; it is an engine and its
checker being wrong together because they were built from one description.
`ic3_pdr`'s `check.py` genuinely does not import the search — and is handed the
`System` that `system.py::peg_system` built, from the graph the search read.

## 2 · The two acceptance runs

| rule set | certificate | verdict | |
|---|---|---|---|
| `peg4-0111` | `ic3_pdr`'s invariant, clause for clause | **ACCEPT** | 16 states, three conditions green |
| `a2-holed` | A2's `right_room_locked` | **ACCEPT** | 148 states — agreeing with Lean |
| `a2-world` | the same certificate | **REJECT** | `inv_closed` |

The A2 pair is the argument. One certificate — the 0/1 pagoda weight that
`cold-start-a2/theory/generated_holed/theory.lean` proves closed by `decide`,
with `#print axioms unsolvable` coming back `[]` — checked against two rule sets
that differ by exactly one rule.

Against `a2-holed` it verifies. **It has to**, and the row is not a formality:
if this rechecker rejected the invariant Lean accepted, the rejection in the
next row would say nothing about the world and everything about a bug here.

Against `a2-world` it fails `inv_closed`, with all four witnesses being the
teleport:

```
{button=7, cart=6,4, door=yes} -down-> {button=7, cart=7,6, door=yes} escapes
```

and the second opinion — a plain breadth-first search over the same derived
relation, sharing nothing with the three conditions — reaches the goal in **18
actions**, the same length as A2's own recorded refutation, by a different
route of the same length.

All **18** `deadlock_carver` theorems recheck green as `dead_region`
certificates: 16 on `open4far`, 2 on `ringstuck`. (`ringstuck` has four
geometric corners and the carver emits two; the other two are not h²-reachable
for a box in a one-wide corridor, so they are not candidates. That is the
carver's output transcribed, not a transcription loss — `deadlock_spotcheck.py`
re-ran it.)

## 3 · The state space had to be restricted, so the restriction is proved

The sokoban pair deadlocks are **false** over the raw product: a state with the
player standing on a box is in the product, and from it a "dead" box can be
pushed out of its corner. The carver is right; it reasons over h²-consistent
states. So a rule set may declare a constraint — and this rechecker refuses to
use one until it has shown it holds at every initial state, is closed under
every action, and (measured, by a breadth-first pass, not inferred) contains
everything reachable.

That is what makes the cheapest attack fail: add `constraint: cart != "6,4"` to
A2's world and the false theorem verifies, except `constraint_closed` does not.

## 4 · The rule sets are transcriptions, and that is the real risk

Nothing inside `recheck/` can tell you `a2-world.rules.json` is A2's world. So
the anchors are outside it, against artefacts written by other people for other
purposes:

| anchor | measured |
|---|---|
| A2's recorded 18-action refutation replayed through `a2-world`, compared on the rendered 9×9 | **19/19 frames**, 0 of 1539 pixels wrong |
| the derived step vs `cold-start-a2`'s compiled predictors, whole product, both worlds | **592/592**, and 0/592 differences in *which named rules fire* |
| Lean's explicit 592-row `step` table in `generated_holed/theory.lean` vs `a2-holed` | **592/592** |
| the certificate's pagoda table vs Lean's `def w` | **37/37** cells, exactly 21 zeros |
| the sokoban encoding vs the generated PDDL, independently parsed and grounded | **26 880/26 880** `open4far`, **1 056/1 056** `ringstuck` |
| optima the fixtures state by hand: ring 1, open4 6, ringstuck unsolvable, open4far 11 | 4/4 |
| peg reachability hand-verified in `peg4.py`'s docstring: 1110/0111/1011 unsolvable, 1101 in 2 | 4/4 |

The differential was checked for its ability to fail before its silence was
believed: pointed at the *holed* predictor, `a2-world`'s rules disagree in
exactly 4 places, all `cart=(6,4)` on `down`. The teleport, and nothing else.

Two anchors need `cold-start-a2/` on the machine. This package reads it and
writes nothing to it; when it is absent they report **unavailable**, never as
passes (D-030).

## 5 · The adversarial half — four real defects

The item asked for a subagent tasked with forging a certificate that fools the
rechecker. Three were run, on three lenses. **They found four wrong ACCEPTs and
a class of crashes.** Reports and every input are under `attacks/`.

| finding | severity | fix |
|---|---|---|
| a `def` compiled for guards keeps `["act"]`; a rule set's **goal** could read the action label through it, evaluate to `None`, and become unsatisfiable — a genuine ACCEPT on the solvable `peg4-1101`, with the second opinion agreeing because it read the same poisoned goal | wrong ACCEPT | defs compiled twice, once per scope (D-031) |
| a domain shrink **plus** one retargeted `nb` entry passes `effects_in_domain`, because the escaping effect's guard no longer fires | wrong ACCEPT | `goal_satisfiable`: the same shrink drops the goal cell, and `unsolvable` is free in a world with no goal state |
| `goal_break` was evaluated on the constrained subspace, so a dead region could contain an outright winning state parked outside it | wrong ACCEPT | `goal_break` over the whole product; costs nothing, all 18 carver theorems still pass |
| a dead region's states outside the constraint carry no obligation, and nothing said so — 286 of 496 in the reviewer's example | silent gap | counted and named in every verdict; the genuine pair deadlocks lean on it by 2 states each |
| deep nesting, `["lit"]` with no argument, and a deep `json.loads` escaped as tracebacks, exiting 1 — which this tool defines as REJECT | crash read as verdict | depth cap by an iterative walk, total `render`/`names_used`, exit code 4 |
| the certificate→rule set binding was by name only | weak | every generated certificate carries the rule set file's sha256 |

Every one is now an entry in `forgeries.py` with the condition that must fail
named in advance, so none can come back quietly. The catalogue is **31
forgeries, 31 behaving as declared**.

The third reviewer, on transcription, found **nothing** — and is the one whose
silence is worth something, because it ran the differentials rather than reading
the code, and checked its instrument could fail first.

## 6 · Two forgeries end in ACCEPT, and both are on the record

**`delete-the-rule`.** Hand the rechecker a rule set with a rule missing and a
certificate true of it, and it accepts — correctly. That rule set is well
formed, its step is single-valued, its constraint is inductive, and the
certificate really is an invariant of it. This is not a hole; it is Theoria §1.3
entire, and the instrument for it is the refutation loop, not any checker. It is
carried as `expect: NOT-CAUGHT`, and the suite fails if it ever starts being
caught — that would mean this code had grown an opinion about worlds it cannot
see.

**`region-reaching-outside-the-constraint`.** Accepted because it is true of
every reachable state, which is the qualifier `deadlock_carver`'s theorem
already carries. Rejecting it would reject every genuine pair deadlock. What was
wrong was silence; the entry now fails unless the verdict reports, with a count,
how much of the region rested on the qualifier rather than on a check.

## 7 · Gaps, stated

* **It enumerates.** The product is capped at 10^6 states and refused above
  that rather than sampled. Same substitution `fd_adapter` and `ic3_pdr` make,
  same reason, same consequence (D-009): correctness unaffected, reach is.
* **It does not parse PDDL, Lean or the DSL.** The rule sets are transcriptions
  into one small language, which is why §4 exists. A parser per source language
  would trade a transcription risk for a parser-bug risk in three languages, and
  that parser would be this package's own code — the dependency the exercise is
  avoiding. Recorded, not resolved (D-030).
* **`lp_potential`'s pagoda certificates are not covered.** The two engines the
  item named are. A numeric pagoda needs a fourth condition shape (the potential
  never rises), which this language can express but no case here exercises.
* **Nothing here says a rule set is the world.** See §6.
