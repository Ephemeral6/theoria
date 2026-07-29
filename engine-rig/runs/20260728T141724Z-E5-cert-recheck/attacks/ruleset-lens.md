# Adversarial review — lens: the rule set as the trusted input (`recheck/ruleset.py`)

Reviewer: adversarial, ruleset lens. Goal: make `python -m recheck` print ACCEPT
(exit 0) for a certificate that is **not** a genuine invariant / dead region of
the transition system the rule set describes.

## Version under test

    branch        agent/e5-cert-recheck
    base commit   bd7e9e786129cb045d579f1df649fad6b4ec053d
    cwd           .worktrees/e5-cert-recheck/engine-rig

`recheck/` was being edited by another session *during* this review. All results
below were re-run and confirmed against these digests:

    5badf446f63ac9287bbc1638784362467f9e279b82c9fb81bf20e52412a9d450  ruleset.py
    dd676d912e86f4b9d166fa1741b2f868c02c07c6f1d93f3c9c8cfb60ab1f7f56  verify.py
    b3e80a405d4d7e3da5d162d1aed8008688ec1b812c6774206fd93db72d502953  certificate.py
    68640d2005ad4ebcfcbb4ef2e3eb27ce127b5dde7c8d6c7ad746b0eb28a6e164  expr.py

## Headline

**Two breaks.** Both produce ACCEPT / exit 0.

1. **R-01 (most serious).** A `dead_region` certificate is accepted whose region
   contains states that reach the goal — including states that *are* goal
   states. It works against the **shipped, unmodified**
   `recheck/cases/sokoban-open4far.rules.json`; nothing in the rule set is
   touched. `goal_break` prints `ok` over a region containing a win, and the
   second opinion prints "no goal state is reachable". This defeats the
   catalogued `region-over-the-goal` forgery.
2. **R-02.** Domain shrinking *does* pass `effects_in_domain` if the `nb` table
   is retargeted so the escaping rule's guard never fires. One table cell
   changed, all seven rules intact, no constraint declared. This falsifies the
   claim in `ruleset.py`'s own docstring that "shrinking the state space to hide
   an escaping transition fails here rather than passing quietly downstream",
   and the `forgeries.py` docstring's "All three are caught before any
   certificate is read".

Scoreboard: 21 hand-built attacks + 30 000 fuzzed pairs. 2 break classes
(4 accepted forgeries), 0 INCONSISTENT verdicts, 1 availability defect observed
live (§4). The `inductive_invariant` path plus a declared `constraint` held
under everything I threw at it, including 30 000 randomized pairs.

---

## 1. BREAK R-01 — the constraint carves the dead region's obligations, but not its claim

### The defect

`verify.py`:

```python
inside  = [ruleset.constraint(state) for state in states]
is_goal = [inside[i] and ruleset.goal(state) for i, state in enumerate(states)]
satisfies = [...]                       # the certificate predicate P
region  = [i for i in range(len(states)) if satisfies[i] and inside[i]]
...
for i in region:                        # region_closed
goal_bad = [... if is_goal[i] and satisfies[i]]   # goal_break
sources = list(region)                  # the second opinion
```

Every one of the three `dead_region` obligations — `region_nonempty`,
`region_closed`, `goal_break` — and the independent BFS are computed on
**P ∩ constraint**. The accepted claim, per `certificate.py`, is unqualified
over **P**:

> `dead_region` … P is a set of states closed under every action and disjoint
> from the goal.

So every state in **P \ constraint** is checked for nothing. It is not required
to be closed, and — because `is_goal` is `inside[i] and goal(state)` — it is not
even required to *not be a goal state*.

For the `inductive_invariant` path this leak is plugged, because
`constraint_init` forces `init ⊆ C` and `constraint_closed` forces C inductive,
so `Reach(init) ⊆ C` and the unqualified claim ("the goal is unreachable from
init") is still true. **A `dead_region` certificate makes no reference to `init`
at all** — that is the whole point of the conditional theorem — so nothing ties
its region to the constraint. The obligation that rescues the invariant path
does not exist on the dead-region path.

### R-01a — an accepted dead region that contains a literal win

Rule set: `recheck/cases/sokoban-open4far.rules.json`, **unmodified**. Its
declared constraint is the ordinary sokoban well-formedness idiom
`player≠b1 ∧ player≠b2 ∧ b1≠b2`; its goal is `b1=4,2 ∧ b2=1,3`.

Certificate (`attacks/A1-dead-region-contains-a-win.cert.json`) — the shipped
corner-deadlock pattern with one disjunct bolted on:

```json
{
  "claim": "conditional_unsolvability",
  "kind": "dead_region",
  "name": "attack-A1-dead-region-contains-a-win",
  "predicate": ["or",
    ["=", ["var", "b1"], ["lit", "1,1"]],
    ["and", ["=", ["var", "player"], ["lit", "1,3"]],
            ["=", ["var", "b1"],     ["lit", "4,2"]],
            ["=", ["var", "b2"],     ["lit", "1,3"]]]],
  "produced_by": "engines/deadlock_carver (M9)",
  "ruleset": {"name": "sokoban-open4far",
              "sha256": "d010d2b77220aea6120dd0d883227477c5c3822b9f1bd1989869d46acafc5c31"},
  "schema": "engine-rig/recheck/certificate-v1"
}
```

Note the `ruleset` binding is the real one, name *and* sha256, and it verifies.

```
$ cd .worktrees/e5-cert-recheck/engine-rig
$ python -m recheck recheck/cases/sokoban-open4far.rules.json \
      runs/20260728T141724Z-E5-cert-recheck/attacks/A1-dead-region-contains-a-win.cert.json
ACCEPT       attack-A1-dead-region-contains-a-win
  rule set   sokoban-open4far (4096 states, 8 rules)
  claim      conditional_unsolvability
  predicate  ((b1 = '1,1') or ((player = '1,3') and (b1 = '4,2') and (b2 = '1,3')))
  rules  constraint_closed    ok
  rules  constraint_init      ok
  rules  effects_in_domain    ok
  rules  step_single_valued   ok
  cert   goal_break           ok
  cert   predicate_wellformed ok
  cert   region_closed        ok
  cert   region_nonempty      ok
  cert   ruleset_binding      ok
  second opinion: no goal state is reachable -- the claim is true of this rule set
  -> all three conditions hold over 4096 states, and an independent search agrees the goal is unreachable
EXIT=0
```

Falsification: `|P| = 257`, `|P ∩ constraint| = 210`; the checker looked at 210.
The state `{player=1,3, b1=4,2, b2=1,3}` is in the certified dead region and
satisfies the rule set's own `goal`. `goal_break` printed `ok` anyway, because
`is_goal` had already been masked to `False` for it by `inside`.

**BROKEN.**

### R-01b — the same, without the "but it is definitionally not a goal" defence

`attacks/A2-dead-region-two-moves-from-a-win.cert.json`, same shape, second
disjunct `player=3,2 ∧ b1=3,2 ∧ b2=1,3`:

```
ACCEPT       attack-A2-dead-region-two-moves-from-a-win
  ... all conditions ok ...
  second opinion: no goal state is reachable -- the claim is true of this rule set
EXIT=0
```

Falsification, computed over the checker's own derived relation:

```
{player=3,2, b1=3,2, b2=1,3}   is in the certified dead region
    in the constraint?  False
    is a goal?          False          <- not a goal, so no definitional escape
    reaches {player=3,2, b1=4,2, b2=1,3} in 2 actions:  move-up push-down
    that goal state is well-formed?  True   <- the win it reaches IS in the constraint
```

A two-action plan from a state the tool certified as dead, ending in a fully
well-formed winning position. This is the sharpest form of the break: the
certified-dead state reaches a win that the constraint itself admits.

**BROKEN.**

### R-01c — the realistic version (no hand-picked coordinates)

The two above look hand-tuned. This one is a pattern `deadlock_carver` could
plausibly emit — "b1 is cornered, or the player is standing on b1":

```json
"predicate": ["or", ["=", ["var", "b1"], ["lit", "1,1"]],
                    ["=", ["var", "player"], ["var", "b1"]]]
```

```
$ python -m recheck recheck/cases/sokoban-open4far.rules.json \
      runs/.../attacks/A3-player-on-box-is-dead.cert.json
ACCEPT       attack-A3-player-on-box-is-dead
EXIT=0
```

`|P| = 496`, `|P ∩ constraint| = 210`. **286 states are certified dead without a
single obligation being discharged on them**, and one of them,
`{player=4,2, b1=4,2, b2=1,3}`, is a goal state. A predicate that mentions no
literal cell at all silently doubles the certified region.

**BROKEN.**

### Why this matters beyond the letter

Every state in P \ C is unreachable from *this* rule set's `init` (C is proved
inductive, so `Reach(init) ⊆ C`). One could argue the theorem is therefore
harmless. That argument fails for `dead_region` specifically, because the
conditional theorem is the one artefact in this package that is **not** tied to
an initial state: `deadlock_carver` mines it to be applied to whatever state a
search is holding — another instance, another `init`, a replan, a position
recovered from a live episode. `certificate.py` says so itself: "There is no
initial obligation — the theorem is conditional". A pruning rule that fires on
`player = b1` and says "unsolvable" is wrong on 286 states of this very board.

### Smallest fix that would close it

Either check the region's obligations over all of P (drop `inside[i]` from
`region`, keep it only in `is_goal`'s *negation*, i.e. use the unmasked goal),
or make `dead_region` refuse a certificate for which
`any(satisfies[i] and not inside[i])` — the region must lie inside the
well-formed subspace it was proved in. The second is the smaller change and
keeps the sokoban theorems working. The `n_satisfying` stat should also report
`|P|`, not `|P ∩ C|`; right now the report gives the reader no signal at all
that 286 states were skipped.

---

## 2. BREAK R-02 — domain shrinking passes `effects_in_domain` once the guard is retargeted

`ruleset.py`'s docstring:

> A constraint that is not inductive is refused, so shrinking the state space to
> hide an escaping transition fails here rather than passing quietly downstream.

`forgeries.py`'s catalogue entry `shrunken-domain` expects REJECT via
`effects_in_domain`, and it does get one — but only because that forgery leaves
the escaping rule's *guard* able to fire. `effects_in_domain` evaluates an
effect **only when its guard fires**, so shrinking plus one guard-side edit is
not caught.

A2's only escape from the left room is `teleport_down`:
guard `rendered(nb[cart,down]) = 3`, effect `cart := "7,6"`. It fires exactly at
`cart = 6,4`, because `nb[6,4,down] = 7,4` and `board[7,4] = 3`.

`attacks/B2-a2-shrunken-domain-patched-nb.rules.json` = `a2-world.rules.json`
with two edits, both inside the trusted rule set:

* `cart`'s domain cut from 37 cells to the 21 left-room cells (the same cut the
  catalogued forgery makes);
* one `nb` entry retargeted: `["6,4", "down", "7,4"]` → `["6,4", "down", "6,4"]`.

`rendered("6,4")` is 5 (door up) or 6 (the cart itself), never 3, so
`teleport_down` never fires anywhere in the shrunken product and its
out-of-domain literal `"7,6"` is never evaluated. `push_down` does not fire
either (`free("6,4")` is false), so `frame persist` holds the cart still and
there is no `conflict exclusive` violation. **All seven rules are present and
unmodified.**

```
$ python -m recheck runs/.../attacks/B2-a2-shrunken-domain-patched-nb.rules.json \
      recheck/cases/a2-right-room-locked.cert.json
ACCEPT       a2-right-room-locked
  rule set   forged-a2-shrunken-domain-with-patched-nb (84 states, 7 rules)
  claim      unsolvable
  predicate  (w[cart] = 0)
  rules  effects_in_domain    ok
  rules  step_single_valued   ok
  cert   goal_break           ok
  cert   inv_closed           ok
  cert   inv_init             ok
  cert   predicate_wellformed ok
  second opinion: no goal state is reachable -- the claim is true of this rule set
  -> all three conditions hold over 84 states, and an independent search agrees the goal is unreachable
EXIT=0
```

Baseline for contrast — the same certificate against the true world:

```
$ python -m recheck recheck/cases/a2-world.rules.json recheck/cases/a2-right-room-locked.cert.json
REJECT ... inv_closed FAILED
    inv_closed: {button=7, cart=6,4, door=no} -down-> {button=7, cart=7,6, door=no} escapes
  second opinion: a goal state IS reachable ... plan (18 actions)
EXIT=1
```

**BROKEN** — as a falsification of the documented defence. Honest caveat: this
is a *lie in the rule set*, and the rule set is the declared trust boundary, so
the severity is that of `delete-the-rule` (catalogued `NOT-CAUGHT`), not of
R-01. The finding is that the catalogue and the module docstring both assert
this particular lie *is* caught, and it is not. The catalogue should either move
`shrunken-domain` to the `NOT-CAUGHT` family with this witness attached, or the
docstring should stop claiming domain shrinking is defended. Note the one real
signal is in the report already: `148 states` became `84 states`, and the
certificate carried no `ruleset` binding to pin the file.

---

## 3. Attacks that HELD

Run with the `ruleset` binding stripped where a mutation would otherwise
short-circuit on `ruleset_binding`.

| # | Attack | Result | Verdict |
|---|---|---|---|
| C1 | constraint `cart != "7,6"` — exclude the teleport target (the catalogued forgery) | REJECT `constraint_closed` | held |
| C2 | constraint `cart in {the 21 zero-weight cells}` — exclude the whole right room | REJECT `constraint_closed` | held |
| C3 | constraint `door = "yes"` — a plausible-looking restriction | REJECT `constraint_closed` | held |
| C4 | constraint `cart != "2,7"` — hide the goal cell itself | REJECT `constraint_closed` | held |
| H1 | two `init` states, the second outside the constraint | REJECT `constraint_init` | held — `constraint_init` iterates all of `self.init` |
| H2 | two `init` states, both well-formed | ACCEPT (legitimately; region still dead) | held |
| I1 | `dead_region` whose region lies wholly outside the constraint | REJECT `region_nonempty` | held |
| F1 | declared constraint **and** two rules writing one variable | REJECT `step_single_valued` | held (see §4) |
| F2 | no constraint, two rules writing one variable | REJECT `step_single_valued` | held |
| D1 | effect returns a Python `bool` into an int domain `{0,1}` | ACCEPT, 0 off-domain edges | held — `True == 1` and `hash(True) == hash(1)`, so `frozenset` membership, `index_of` tuple lookup and predicate evaluation all agree; no divergence |
| E1 | duplicate `"pos0"` key inside one rule's `effects` | ACCEPT | held — `json.load` keeps the last, `owns` is compared post-parse, so the result is a well-formed different world, not a conflict-exclusive bypass |
| G1/G2 | certificate `def` calling the rule set's `clear` | REJECT `predicate_wellformed` | held (over-strict; also logged by the expr lens as A08 — `compile_macros` returns a scope carrying only the newly compiled macros, dropping the base scope's, so a certificate can never call a rule-set `def`) |

**`transitions()` returning `-1` is not reachable when `effects_in_domain`
passes.** `expr.py` admits only `str | int | bool` values; if every effect value
is in its variable's `frozenset` domain then the successor tuple compares and
hashes equal to a product member, so `index_of.get` finds it. `-1` is treated as
an escape (REJECT) in both `region_closed` and `constraint_closed`; the only
place it is silently skipped is `_bfs`, and that path is unreachable for the
same reason. Held.

### Differential fuzz — the `inductive_invariant` + `constraint` path

`attacks/fuzz_ruleset.py` re-implements the DSL semantics (`frame persist`,
`conflict exclusive`, `cascade single_frame`) independently, over the full
product, ignoring the constraint entirely, and flags any ACCEPT where the ground
truth says a goal is reachable from the certificate's own sources.

    $ python runs/20260728T141724Z-E5-cert-recheck/attacks/fuzz_ruleset.py 4000
    30 000 random (rule set, certificate) pairs, seed 20260728

    inductive_invariant breaks .......... 0
    dead_region breaks (all with a constraint) ... 65
    INCONSISTENT verdicts ............... 0
    crashes ............................. 0

Every single break the fuzzer found is R-01. That is the evidence that the
invariant path's `constraint_init` + `constraint_closed` really are sufficient,
and that the dead-region path is the one missing an obligation.

---

## 4. Availability defect observed live (not a break, but worth recording)

At 22:42 local, mid-review, `recheck/ruleset.py` was saved in a state where
`obligations()` referenced a deleted local:

```
  File ".../recheck/ruleset.py", line 427, in obligations
    assignment[index] = value
NameError: name 'assignment' is not defined
```

Every invocation of `python -m recheck` failed this way for ~70 seconds — the
line executes whenever any rule fires anywhere in the product, i.e. always.
`__main__.main()` wraps only *loading* in its `try`; `recheck()` is outside it,
so an exception escapes as an uncaught traceback and Python exits **1**, which
`__main__`'s own docstring defines as REJECT. A caller reading only the exit
status cannot distinguish "the certificate was refused" from "the tool is
broken". A bare `except Exception` around `recheck()` returning a distinct
non-verdict code (or reusing 2) would make that failure legible. The NameError
itself was fixed by the owning session; the exit-code aliasing was not.

Separately, and to that session's credit, the same edit added `and not single`
to the `constraint_closed` guard in `obligations()` — before it, a rule set with
both a declared constraint and a `conflict exclusive` violation would call
`transitions()`, `step()` would raise `RuleSetError`, and the same
traceback-as-exit-1 path would fire instead of the intended REJECT. Attack F1
confirms that is now closed.

---

## Artefacts

All under `runs/20260728T141724Z-E5-cert-recheck/attacks/`. Nothing under
`recheck/` was modified.

    A1-dead-region-contains-a-win.cert.json         R-01a  ACCEPT / exit 0
    A2-dead-region-two-moves-from-a-win.cert.json   R-01b  ACCEPT / exit 0
    A3-player-on-box-is-dead.cert.json              R-01c  ACCEPT / exit 0
    B2-a2-shrunken-domain-patched-nb.rules.json     R-02   ACCEPT / exit 0
    fuzz_ruleset.py                                 differential fuzzer

A1–A3 run against the shipped `recheck/cases/sokoban-open4far.rules.json`; B2 is
a rule set and runs against the shipped
`recheck/cases/a2-right-room-locked.cert.json`.
