# `recheck` — an independent complaint department for engine certificates

M9's deadlock theorems and IC3 invariants pass in Lean with an empty axiom list.
That settles whether the *proof* is a proof. It does not settle whether the
**certificate** — the invariant, the pattern, the weight table — is the right
object at all, because until now every route to that question went through the
same construction the engine used. `ic3_pdr` ships `check.py`, which really does
re-derive the three conditions and really does not import the search; but it is
handed the engine's own `System`, built by the engine's own `peg_system()`. A
mistranscription there certifies itself.

So this package takes two files and nothing else:

```bash
cd engine-rig
python -m recheck recheck/cases/a2-holed.rules.json recheck/cases/a2-right-room-locked.cert.json
python -m recheck.verify_all --out runs/<id>          # the whole thing, with expectations
python -m recheck.build_cases --check                 # the cases have not been hand-edited
```

Exit codes: `0` ACCEPT, `1` REJECT, `3` INCONSISTENT, `2` the input would not
load, `4` the recheck itself failed. `4` exists because an uncaught exception
otherwise leaves Python's own status of 1, which is REJECT — a crash and a
refusal are not the same answer.

**Nothing in `recheck/` imports `engines/`.** A test enforces it
(`test_recheck_never_imports_the_engines`).

## What is checked

The three conditions, which are Theoria 1.10(a)'s Lean skeleton verbatim:

| | inductive invariant (`ic3_pdr`) | dead region (`deadlock_carver`) | pagoda (`lp_potential`) |
|---|---|---|---|
| holds at the start | `inv_init` | — replaced by `region_nonempty` | `potential_init` |
| survives every rule | `inv_closed` | `region_closed` | `potential_nonincreasing` |
| excludes the goal | `goal_break` | `goal_break` | `goal_break` |
| licenses | `unsolvable` | `conditional_unsolvability` | `unsolvable` |

A conditional theorem has no initial obligation — that is what *conditional*
means — so the first slot becomes non-vacuity instead. A pattern no state
satisfies is closed and goal-free for free, and a theorem about no state is
refused rather than filed as a pass.

Closure is checked from **every** state satisfying the predicate, reachable or
not. Restricting it to the reachable part would be circular: what is reachable
is exactly what the certificate is supposed to bound.

`goal_break` is checked over the whole product; closure is checked over the
subspace the rule set's constraint admits (see below), so the verdict reports
how many states the predicate covers that no obligation touched. For a genuine
`open4far` pair deadlock that is 2 of 16.

## The pagoda shape, and the two things it is careful about

A `potential_bound` certificate carries **no predicate**. It carries an integer
weight per state variable, the value that counts as occupied, and a bound; the
set of states is `potential(s) <= bound`, derived. The middle obligation is then
arithmetic rather than set-theoretic — *no legal move raises the potential* —
which is what `lp_potential` solves an LP for, and is strictly stronger than
closure.

```json
{ "kind": "potential_bound", "claim": "unsolvable",
  "occupied": 1, "bound": 0,
  "weights": {"pos0": -1, "pos1": 1, "pos2": 0, "pos3": 1} }
```

**The moves come from the rule set.** `lp_potential`'s exported document ships
an `obligations` block listing every move instance with its delta already
evaluated, and `interop/certificate_export.py::verify` iterates that list — so a
document that omits an inconvenient instance passes it, and one that lists a
move the geometry does not have is believed. Here the relation is grounded from
the declared rules over the product, exactly as for the other two kinds, and
`obligations` is on the certificate schema's refused-by-name list. It is read
exactly once, in `anchors.py`, as a differential: every listed move is replayed
through the derived relation and the two move sets are compared both ways, so a
discrepancy is a *finding* rather than a rejection or a silence.

**The obligation is checked from the region, not off the geometry.** "No legal
move raises the potential" quantifies over moves legal from a state the bound
admits. Checking every move instance regardless is a different, stronger claim,
and it **false-rejects** sound certificates. `keyed-gate` in `cases/` is the
exhibit: its only potential-raising move needs both keys, every state holding
both is already over the bound, and so the move can fire from nowhere the
invariant admits. `test_the_potential_obligation_is_quantified_over_moves_legal_from_the_region`
asserts both halves — that this rechecker accepts it, and that the stronger
check really would have rejected it.

Two smaller things follow the same principle. Weights must be **integers**:
the exporter scales the LP's exact rationals precisely so that `delta <= 0` is
decided exactly, and a float would put a rounding decision on that comparison.
And `occupied` must be a value the variable's declared domain actually holds —
a weight that can never be counted makes the potential constant, and a constant
potential is non-increasing under everything.

## Why the rule set is a *rule* set

The transition relation is never read. A rule set declares finite variables with
explicit domains; the state space is the **full Cartesian product** of those
domains, and every edge is computed here by grounding the rules. That is the one
design decision the rest follows from — a world description that shipped its own
edge list would let one program produce both the answer and the check on it.

Semantics are the DSL contract's, unchanged: `frame persist` (a variable no
firing rule writes is unchanged, which makes `step` total), `conflict exclusive`
(two rules writing one variable on one action is an error, not a precedence
question), `cascade single_frame` (guards and effects read the pre-state).

These obligations are discharged on the rule set **before** any certificate is
looked at, so a broken world never gets reported as a broken certificate:

* `step_single_valued` — no `(state, action)` has two rules claiming a variable
* `effects_in_domain` — no rule *that fires* can drive a variable outside its
  declared domain
* `goal_satisfiable` — some state in the declared space satisfies the goal
* `constraint_init` / `constraint_closed` / `constraint_contains_reachable` — a
  rule set may declare a well-formedness constraint, and this rechecker **proves
  it inductive** instead of believing it, then measures that it really does
  contain everything reachable

The constraint obligations are load-bearing and also the sharpest knife in the
drawer. The sokoban deadlock theorems are false over the raw product — a state
with the player standing on a box is in the product and lets a "dead" box be
pushed out of its corner — and true over the states the grounded task can
represent. So the rule set declares "the player and the boxes are on distinct
cells", and the rechecker refuses to use it until it has shown the constraint
holds at the initial state and is closed under every action. Adding
`constraint: cart != "6,4"` to A2's world would otherwise verify the false
theorem; it fails `constraint_closed` instead (`constrained-witness`).

`goal_satisfiable` is there because of one specific attack, and the shape of it
is worth keeping in mind: `effects_in_domain` only ever evaluates an effect
whose guard fires, so shrinking `cart`'s domain to the left room **and**
retargeting one entry of the `nb` table stops `teleport_down` firing, and the
out-of-domain literal is never reached. What that pair of edits cannot hide is
that the goal cell went with the shrink — and `unsolvable` is free in a world
with no goal state (`shrunken-domain-and-patched-guard`).

## The second opinion, and its limit

After the three conditions, the tool runs a plain breadth-first search over the
same derived relation and asks whether a goal state is reachable at all. This is
**not** how certificates are meant to be checked — the entire point of a
certificate is that it is cheaper than the search, and at any real scale this
would be unavailable. Every world this package can hold is under 5 000 states,
so it is affordable here, and it catches the one thing the three conditions
cannot: a certificate that is impeccable about a rule set that is not the world.

If the conditions hold *and* the goal is reachable, the verdict is
`INCONSISTENT`, not `ACCEPT`. That combination is impossible if this code is
correct, so it is escalated as a defect in the checker rather than rounded down.

## The two runs this package exists for

```
peg4-0111   + peg4-0111-ic3          ACCEPT   16 states
a2-holed    + a2-right-room-locked   ACCEPT  148 states
a2-world    + a2-right-room-locked   REJECT  148 states, inv_closed
```

All three of `lp_potential`'s exported pagodas pass, each against the rule set
its claim names and each with the producer's document compared against the
transcription:

```
peg4-1110            + peg4-1110-pagoda             ACCEPT  16 states, 0 raising
peg5-11011-to-01000  + peg5-11011-to-01000-pagoda   ACCEPT  32 states, 0 raising
peg5-11011-to-00010  + peg5-11011-to-00010-pagoda   ACCEPT  32 states, 0 raising
```

The A2 pair is the whole argument. It is one certificate — the 0/1 pagoda weight
`cold-start-a2/theory/generated_holed/theory.lean` proves closed by `decide`,
with `#print axioms unsolvable` coming back `[]` — checked against two rule sets
that differ by exactly one rule. Against the manual it was written for it
verifies, and it should: Lean was not wrong. Against the world's own rules it
fails `inv_closed`, with the witness the teleport:

```
{button=7, cart=6,4, door=yes} -down-> {button=7, cart=7,6, door=yes} escapes
```

and the independent search finds the goal in 18 actions — the same length as
A2's own recorded refutation. **A rechecker that passed this would not be
lenient; it would be wrong.**

## The rule sets are transcriptions, and that is the real risk

Nothing inside this package can tell you that `a2-world.rules.json` describes
A2's world. So the checks are outside it, against artefacts written by other
people for other purposes (`anchors.py`, run by `verify_all`):

| anchor | result |
|---|---|
| A2's recorded 18-action refutation replayed through `a2-world`, compared frame by frame on the rendered 9×9 | 19/19 frames, world `win: true` |
| Lean's explicit 592-row `step` table in `generated_holed/theory.lean` vs the relation derived from `a2-holed.rules.json` | 592/592 rows |
| sokoban optima the fixture states by hand: `ring` 1, `open4` 6, `ringstuck` unsolvable, `open4far` 11 | 4/4 |
| peg reachability, hand-verified in `fixtures/peg4.py`'s docstring: 1110, 0111, 1011 unsolvable; 1101 in 2 | 4/4 |
| peg-5 reachability, enumerated in `interop/README.md`: `11011` reaches only `{00111, 11100, 01001, 10010}` | 5/5 states, both rule sets |
| `lp_potential`'s three exported documents vs the pagoda cases transcribed from them — weights, bound, start, goal states, and every listed move replayed through the derived relation | 3/3 agree |

The first two need `cold-start-a2/` to be on the machine. It is another track's
directory: this package reads it and never writes to it, and if it is absent the
anchors are reported as **unavailable**, never as passes.

## The forgeries

`forgeries.py` is a catalogue of ways to lie to this rechecker, each with the
rejection it must draw and the condition that must be the one to fail.
42 entries in four families — lying in the certificate, lying in the rule set,
lying in a pagoda, and the two that end in ACCEPT.

The eleven pagoda entries are the same shapes as the others wherever the shape
exists — claim nothing (every weight zero), claim everything (a bound raised
past the goal), bring your own goal, offer a real certificate for the wrong
instance — plus four that only integers make possible: a weight the world can
never count, a weight that is not an integer, a bound chosen after seeing the
goal, and a document that ships its own obligations.

```bash
python -c "from recheck import forgeries; print(forgeries.summary(forgeries.run_all())['n_as_declared'])"
```

**Six of them were found by adversarial review, and four of those worked.**
Three reviewers were run against this package with no brief except to break it —
one on the expression language, one on the rule set's obligations, one on
whether the rule sets are the worlds they name. Reports and every input are in
`runs/20260728T141724Z-E5-cert-recheck/attacks/`. What they found:

| finding | was | now |
|---|---|---|
| a `def` compiled for guards keeps `["act"]`, so a rule set's **goal** could read the action label, evaluate to `None`, and become unsatisfiable — a real ACCEPT on the solvable `peg4-1101` | wrong ACCEPT | defs are compiled twice, once per scope; `act-through-a-def` |
| a domain shrink plus one retargeted `nb` entry passes `effects_in_domain`, because the effect's guard no longer fires | wrong ACCEPT | `goal_satisfiable`; `shrunken-domain-and-patched-guard` |
| `goal_break` was evaluated on the constrained subspace, so a dead region could contain a winning state parked outside it | wrong ACCEPT | `goal_break` over the whole product; `region-hiding-a-win` |
| a dead region's states outside the constraint carry no obligation, and nothing said so — 286 of 496 in the reviewer's example | silent | counted and stated in every verdict; `region-reaching-outside-the-constraint` |
| deep nesting, `["lit"]` with no argument, and a deep `json.loads` all escaped as tracebacks, exiting 1 — indistinguishable from REJECT | crash read as REJECT | depth cap, total `render`/`names_used`, exit code 4 |
| the certificate→rule set binding was by name only | weak | every generated certificate carries the rule set file's sha256; `tampered-under-the-same-name` |

The transcription audit found **no** discrepancy, having run the differentials
rather than reading the code — and checked its own differential could fail by
pointing it at the wrong predictor, where it reported exactly the 4 teleport
states.

**The one that works is `delete-the-rule`.** Hand the rechecker a rule set with
a rule missing and a certificate true of it, and it accepts — correctly. That
rule set is well formed, its step is single-valued, its constraint is inductive,
and the certificate really is an invariant of it. This is not a hole in the
rechecker; it is Theoria §1.3 entire, and the instrument for it is the
refutation loop, not any checker. It is carried in the catalogue as
`expect: NOT-CAUGHT` with the reason attached, and the suite fails if it ever
starts being caught — that would mean this code had grown an opinion about
worlds it cannot see.

## Adding a case

Rule sets and certificates under `cases/` are **generated** by
`build_cases.py` and never hand-edited; `--check` compares the committed bytes
against what the generator makes. Add the world to `build_cases.py`, add its
expected verdict to `MATRIX` in `verify_all.py`, and add an anchor — a number
somebody else published about that world — to `SOKOBAN_OPTIMA`,
`PEG_REACHABILITY`, `PEG5_REACHABLE` or `anchors.py`. A case with no anchor is a
case that can only tell you this package is self-consistent.

The generator is **hermetic**: it reads no file, so `all_cases()` is the same
dictionary on any machine and a case cannot drift because something outside the
package moved. A pagoda's weights and bound are therefore transcribed into
`PAGODA_CLAIMS` as literals, and the comparison against the document they came
from lives in `anchors.py`, where it belongs and where a disagreement is
reported rather than silently absorbed.

## What this does not do

* **It enumerates.** The state space is the product of the declared domains,
  capped at 10^6, and refused above that rather than sampled. A world needing a
  solver behind `states_where` needs one here too; nothing above the enumeration
  would change, which is the same substitution `fd_adapter` and `ic3_pdr` make
  and record (D-009).
* **It does not read PDDL, Lean or the DSL.** The rule sets are transcriptions
  into one small language, which is why the anchors above exist. A parser per
  source language would remove the transcription risk and add a parser bug risk;
  the trade is recorded, not resolved.
* **It says nothing about whether a rule set is the world.** See
  `delete-the-rule`.
