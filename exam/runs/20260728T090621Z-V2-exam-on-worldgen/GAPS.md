# V2 · the three question types that did not ship, and what each is waiting on

The item asks for all four question types run over the factory's twenty worlds.
**One shipped. Three did not, and none of the three is a matter of effort inside
`exam/`.** Each is blocked on an artefact that does not exist anywhere in the
repository, and two of the three would have to be built in another track's
territory.

This file states each blocker precisely enough to be argued with, because the
alternative — shipping a paper that *looks* like the question type and quietly
answers a weaker question — is the failure `exam/` was built to catch. A
two-class verdict paper presented as a three-class one is exactly the shape of
"a framework that says unsolvable too readily", one level up.

---

## 1 · Rule-change adaptation — needs a rule-mutation layer in `worldgen/`

**The question type.** Change one rule; ask the examinee to detect it, describe
it, work out the collateral damage to claims that depended on it, and repair.
Collateral carries 41.7% of the marks because it is the part that matters.

**Why it cannot be built here.** The A0 paper enumerates its six variants over
`sokoban2.Rules` — a frozen dataclass with three fields, so a variant is
`dataclasses.replace(level, rules=...)` and the whole variant family is a small
product:

```python
_FIELDS = ("push_distance", "require_crossing_free", "walls_block_player")
_VARIANT_GRID = {"push_distance": (1, 3), "require_crossing_free": (False,),
                 "walls_block_player": (False,)}
```

`worldgen/` has **no analogue**. Its semantics live in mechanism classes'
`interact()` bodies; push distance is one cell because `mechanisms/push.py` says
so in code, not because a parameter says so. `spec.flags` exists but carries
world configuration (gravity on/off), not rule semantics.

Mutating a rule therefore means adding a **parameterisation layer to
`worldgen/mechanisms/`** — every mechanism gains a declared, enumerable set of
semantic knobs — plus the guarantee that a mutated world still passes `validate`
and the build gates. That is a `worldgen` change, and `worldgen/` is not this
item's territory.

**Three further things it needs, each independently missing:**

* **Dependency edges.** The paper's collateral family calls
  `adapt.dependent_theorems(dsl, rule)`, which reads `[depends: push2]`
  annotations in A0's manual. The factory's `ground_truth.json` has invariants
  with statements and a `rule_correspondence` block, but **no claim→rule
  dependency graph**. Without it there is no collateral to grade, which is 41.7%
  of the paper.
* **A miner that covers the mechanisms.** Repair cost is measured by
  `engine-rig`'s `stages.mine`/`predict` over a `Percept(player, box, walls, …)`
  — a two-object sokoban percept. Generated states carry arbitrary mechanism
  vars: portals, doors, tokens, colour-cycle phases, consumables. A repair score
  against a miner that cannot represent the state is not a measurement.
* **A build-time property that may not exist at all.** A0's `build()` refuses
  unless some variant is *undetectable on the base level* and some variant
  *flips a solvability verdict*. Both are facts about A0's particular geometry.
  Finding a (world, mutation) pair with either property in the generated
  catalogue is a **search**, and with 19 of 20 worlds solvable the
  verdict-flipping half is especially scarce.

**Honest estimate:** a `worldgen.mutate` module first, then the miner question
answered separately, then this paper. Weeks, and the first two are design work.

---

## 2 · Layered handover — needs a deliverable, which is a design question

**The question type.** Hand a fresh reader a self-contained bundle — the manual,
or the manual plus the playbook — and ask them to answer without the repository,
the history, or any earlier conversation. `reader_minus_author` is 新读者打平作者.

**The world side is easy and in places better than A0's.** `GridWorld.explain`
gives step semantics with the rule name; `explorer.shortest_paths` returns
distances directly, which is what the optimal-action family actually wants and
is cleaner than A0's `solve_bfs` wrapper.

**The blocker is that there is nothing to hand over.** The paper's author
baseline compiles the deliverable and runs it:

* `author_baseline()` needs an executable form exposing `RULES: [(name, fn)]`,
  `State`, `GRID_HEIGHT/WIDTH/WALLS`, `__source__`;
* `_observe()` **greps that source** for the push distance, the walk distance and
  the push guard;
* `_VOCABULARY` is twelve hand-authored names with per-name observables,
  class-balanced and length-matched, one of which exists only because A0's manual
  has a defect.

A generated world ships no manual and no playbook, because **nobody has
theorised it yet** — the factory produces worlds, not theories about them.

`GROUND_TRUTH.md` is the tempting substitute and it is the wrong one, for three
independent reasons:

1. it is marked **"Do not open while theorizing. Scoring only."** Using it as the
   handed-over document inverts the read licence that keeps the catalogue from
   being a rigged evaluation;
2. it is *ground truth*, not a theory somebody authored, so "新读者打平作者" has
   no author to draw with;
3. there is no executable form, so the author baseline cannot be computed at
   all — and it is computed, never hardcoded, on purpose.

**What would unblock it:** an arm actually producing a manual for a generated
world — which is what `a0-spike` / `cold-start-a0` did for A0 and what
`Theoria.md`'s A-family cold starts are for. That is upstream of this item, not
inside it.

A smaller, real gap alongside: the paper wants three instances of one world with
the same rules and different geometry. The catalogue has four *variant pairs*,
and `t1-push-open ↔ t1-push-corridor` is exactly the right shape — but there are
two, not three.

---

## 3 · Three-class verdict — one class is arithmetically out of reach

**The question type.** Nine unsolvable and eight solvable items across three
classes: small-space unsolvable (where exhaustive search also works, so the
*reason* is scored separately), **large-space unsolvable**, and solvable-but-hard
as the false-positive trap.

**Better placed than it looks:** `verdict.py` does not import `cold-start-a2` at
all — its boards are ASCII literals and its semantics are its own. So porting is
swapping the world engine, not rewriting the paper. And the factory supplies two
of the three ingredients outright: an **exhaustive-reachability certificate** with
a separating frontier and blocking entities for unsolvable worlds, and a
replayable `optimal_plan` witness for solvable ones.

**Two blockers, one of them arithmetic:**

* **Class (ii) is impossible with this catalogue.** The threshold is
  `LARGE_SPACE_THRESHOLD = 10**12` configurations and `build()` raises below it.
  The largest reachable set the factory ships is **2,654 states**
  (`t3-full-house`). The gap is nine orders of magnitude. A2 reaches it with a
  2^m latch construction; `worldgen` has `count_lock` and `switch_door` but
  nothing built at that scale. Closing this means **generating new worlds**, in
  `worldgen/`.
* **Only one world is unsolvable** (`t2-unsolvable-nodoor`). The paper needs nine,
  and near-twin solvable/unsolvable pairs on the same board so that board
  identity carries no signal. A2 gets them from five wrapper operators
  (`forbid_action`, `remap_action`, `step_limit`, `observation_loss`,
  `win_tighten`); the factory has no wrapper layer, so they would have to be
  ported onto `GridWorld` or the unsolvable variants generated.

Also real, though tractable: the certificate grammar (`cart_row`, `cut_set`,
`counting`, …) is written against a two-field state `(cart, pressed)`. Generated
states are `(agent, vars)` with arbitrary mechanism vars, so the checker's
geometry helpers would need rewriting.

**What could ship, and why it did not.** Classes (i) and (iii) are buildable —
one unsolvable world with a machine-checked certificate, and nineteen solvable
ones with witness plans. That is a **two-class verdict paper**, and shipping it
under the name of a three-class question type is precisely the misreport this
question type exists to catch. If it is wanted as a two-class instrument it
should be named one, and that is a decision for whoever owns the protocol, not a
default an agent picks at the end of a ticket.

---

## What this means for the item

The item's acceptance line is not lowered here and is not met either. One of four
question types ships, fully: twenty worlds, a calibrated marker on every one, a
grading matrix and a difficulty distribution. The other three are blocked on:

| type | blocked on | whose territory |
|---|---|---|
| adaptation | a rule-mutation layer + claim-dependency edges + a mechanism-aware miner | `worldgen/`, `engine-rig/` |
| handover | a theory somebody authored for a generated world | upstream (a cold start) |
| verdict (ii) | worlds with ≥10^12 configurations, and unsolvable variants | `worldgen/` |

The smallest next step that unblocks the most is **`worldgen.mutate`**: a
declared, enumerable set of semantic knobs per mechanism. It is the whole of
adaptation's first blocker and most of verdict's second.
