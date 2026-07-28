# cegis_miner, cross-checked by brute-force enumeration

**Work order** E11-engine-crosscheck-deep (RES-3, verify lane) · **2026-07-29**
**Tree** `.worktrees/e11-engine-crosscheck-deep` @ `ed592a6`
**Discipline** read-only against `engine-rig/` and `fuzzlab/`. No file under either was
modified. No network, no `.env`, no sealed-pile contact. Harness lives in the session
scratchpad, not in the repo.

Headline: **two of the engine's published rule kinds are factually false on evidence the
engine itself accepted, and the entire four-invariant battery is green on every world
where that happens (162/193).** Both are invisible to `cegis_miner`'s own tests because
Fixture A is a one-object world with a load-bearing `free` conjunct — the exact
configuration in which both defects cancel.

---

## 1. Chain, and who wrote each link

| Step | Code used | Author |
|---|---|---|
| World generation | `fuzzlab/worlds/gridworld.py::generate(seed)` | **shared** (engine-rig track) |
| Fixture A trajectory | `engine-rig/fixtures/data/cart_world.jsonl` + `_truth.json` | **shared** (data) |
| Segmentation | `engines.mdl_segmenter.segment_trajectory` | **shared** (subject-adjacent) |
| Evidence rows (frame, anchor, shape, action) | `cegis_miner.transitions_from_segmentation` | **shared** (subject) |
| Rule mining | `cegis_miner.mine`, `Rule.as_json()` | **subject under test** |
| Guard-literal parsing (name string → my tuple) | `to_my_lit` | **mine** |
| Strip geometry, `in_bounds`/`clear`/`free`/`at`/`act` evaluation | `my_strip`, `my_eval` | **mine** |
| Vocabulary construction | `my_vocabulary` | **mine** |
| Firing set of a guard | `my_fires` | **mine** |
| Minimal-guard enumeration (all `C(V,k)`, k ≤ 3) | inline in `audit_world` | **mine** |
| "What actually changed" oracle, from pixels only | `my_effect` | **mine** |
| Second effect oracle | `GridWorld.events` (generator's own labels) | **shared** (independent of every engine) |
| Battery green/red demonstration | `fuzzlab.props.cegis_miner.check` | **shared**, used *only* to show the battery's verdict — never to form one of mine |

Nothing in the judgment path calls `atoms.evaluate`, `atom_masks`, `_mask_of`,
`synthesize`, `enumerate_frontier`, `guards_are_mutually_exclusive`,
`explains_every_transition`, or any bitmask. `atoms.py` was **read** for the predicate
definitions and `Atom.name`'s format; the evaluator is rewritten here from those
definitions. The engine is consulted only through the published payload
(`Rule.as_json()` / `to_payload`) plus `rule.applicable`.

### 1.1 Shared dependencies — the full list, nothing omitted

1. **`fuzzlab/worlds/gridworld.py`** — supplies worlds *and* serves as my second effect
   oracle via `world.events`. It is the engine-rig track's own code. Mitigation: my
   pixel oracle (`my_effect`) is fully independent of it, and **every falsification
   below is reported only when both oracles agree**. `eff_wrong_both = 0` disagreements
   between the two.
2. **`engines.mdl_segmenter` + `cegis_miner.transitions_from_segmentation`** — build the
   evidence rows. Unavoidable: a guard must be checked against the same
   `(frame, anchor, shape, action)` the engine saw, or I am auditing a different object.
   This shared link is *itself* where finding **F-1** lives, so it is not a blind spot
   here — it is the finding.
3. **`engines.cegis_miner`** — the subject. `mine()` and the payload only.
4. **`engines/cegis_miner/atoms.py`** — definitions read, code never executed.
5. **`fuzzlab/props/cegis_miner.py`** — executed once per affected world purely to record
   what the existing battery says. Its verdict never feeds mine.
6. **Fixture A truth file** (`cart_world_truth.json`) — `anchors` used to confirm the
   segmenter picked the right object; not used to judge guards.

---

## 2. What the engine actually promises (with sources)

| # | Promise | Source |
|---|---|---|
| P1 | "a rule is right exactly when it fires on every transition carrying its effect and on no other" | `engines/cegis_miner/README.md:5-6`; `miner.py:3-5` |
| P2 | the output is "**every** minimal guard consistent with the evidence, ordered by description length" | `miner.py:10-11` |
| P3 | "every minimal-by-inclusion guard up to `frontier_max_size` literals" | `README.md:19-21`; `enumerate_frontier` docstring `miner.py:182` |
| P4 | "Frontier enumeration is exhaustive up to this many literals **[3]**; anything deeper is reported as truncated rather than silently dropped." | `miner.py:39-41` |
| P5 | "The **ground** rules' guards are mutually exclusive and together admit all 49 transitions" | `README.md:55-56` — scoped to ground rules, explicitly |
| P6 | "Effects come from `mdl_segmenter`'s narration — the miner never re-derives *what happened* from pixels" | `README.md:10-12`; `__init__.py:31-35` |
| P7 | `frontier_max_size` is "enumeration depth actually searched" | `README.md:86` |
| P8 | naming is "a deterministic function of rule *shape*" and only "a stable structural handle so that proposals can be referred to" | `README.md:69-71`; `miner.py:201-206` |

P1 is the load-bearing one and it is stated of *rules*, not of ground rules. P5 is the
only place the README narrows a claim to ground rules — which makes the absence of any
such narrowing on P1 meaningful.

**Deliberately not asserted.** CEGIS uniqueness and global minimality are nowhere
promised, so "my enumeration picked a different guard" is never reported below as a
defect. Every finding is a falsification of P1–P4 or P7 as written.

---

## 3. Method and scale

* Guard check: for each published guard (and each frontier entry), compute its firing set
  by direct evaluation over every evidence row and compare to `support` / `applicable`.
  Lifted guards are evaluated with `?dir` **bound to that row's action** — the only
  reading under which `act==?dir` is not meaningless.
* Frontier completeness: enumerate all `C(|V|, k)` literal subsets, drop strict supersets
  of an already-found minimal guard, keep those firing exactly on `support`, diff against
  the published frontier. Depth 3 on Fixture A and on 25 worlds; depth 2 on 60 worlds.
  `|V|` = 24 + 2·(distinct anchors), 40–70 in practice.
* Effect check: `my_effect(f_t, f_{t+1})` reconstructs `f_{t+1}` from `f_t` by translating
  one cell set, and returns **every** delta that works. A published effect is called false
  only when it is in **no** explanation **and** the generator's label disagrees.

| Corpus | Worlds | Transitions | Ground rules | Lifted rules |
|---|---|---|---|---|
| Fixture A (cart world) | 1 | 49 | 9 | 1 |
| `gridworld` seeds 1–200 | 193 judged, 7 unminable | 4 277 | 932 | 149 |

Both segmentation operators are tried in the same order `fuzzlab/props/cegis_miner.py::_mine`
uses (`split_by_color=False`, then `True` on `ValueError`); `True` was reached in 62 worlds.

---

## 4. Results

| Check | Fixture A | gridworld 1–200 | Verdict |
|---|---|---|---|
| Ground guard fires exactly on support | 9/9 ok | 932/932 ok | **clean** |
| Every ground frontier entry fires exactly on support | 24 entries ok | 0 bad | **clean** |
| `applicable == support` (ground) | ok | ok | **clean** |
| Ground rules partition the evidence | 49/49, no overlap | no overlap | **clean** |
| Minimal guards missing **within** the rule's own `frontier_max_size` | 0 | 0 (depth 3, 25 worlds; depth 2, 60 worlds) | **clean — P3 holds** |
| Minimal guards missing **beyond** `frontier_max_size` but ≤ 3, with `frontier_truncated=false` | **2** | **125** (25 worlds, depth 3) | **F-3, P4 false** |
| **Published effect false on both oracles** | 0 | **1 209 rows / 72 worlds** | **F-1** |
| **Lifted guard fires where its promised effect is false** | 0 | **91 of 149 lifted rules (61 %), 342 rows, 90 worlds** | **F-2** |
| Battery (`props/cegis_miner.check`) green on an affected world | — | **162 / 162** | **the gap** |

### F-1 — every rule in 72 of 193 worlds describes the wrong object, effects included

`transitions_from_segmentation` defaults to `track = seg.tracks[0]`
(`engines/cegis_miner/__init__.py:36`). `mdl_segmenter` orders tracks by first
appearance, and components within a frame by raster order of their cells
(`segmenter.py:156`, `:224-242`). So `tracks[0]` is **whichever object sorts first in
frame 0** — routinely a static obstacle.

Seed 2, an 11×7 board, 1×1 mover at `(4,0)`, one obstacle at `(1,1)`:

```
mined track          obj0, anchors [(1,1), (1,1), (1,1), (1,1), (1,1), …]   # the obstacle
true mover anchors        [(4,0), (4,1), (5,1), (5,0), (4,0), …]
t=1  action DOWN   generator event "move:DOWN"   my pixel oracle ["move", [[1,0]]]
                   segmenter narrated  ('obj1','move',{'dy':1,'dx':0})      # correct!
                   published effect    {"type": "none"}
```

The segmenter got it right. The miner then mined the object that never moves, so every
transition falls into an all-`none` effect class and the published rules are
`blocked_UP/DOWN/LEFT/RIGHT` with effect `{"type":"none"}` — asserted over 1 595
transitions in which the real mover moved. **1 209 of those rows are outright false on
both oracles.** Affected rule names: `blocked_UP`, `blocked_DOWN`, `blocked_LEFT`,
`blocked_RIGHT`.

The guards are impeccable: `applicable == support`, mutually exclusive, complete. The
rule set is *internally* perfect and *externally* about the wrong object. That is P1
falsified — the rules fire on transitions that do not carry their effect.

Scope note, stated plainly: `track=` is an optional parameter, so a caller *can* pass the
mover. But the README's API example passes none (`README.md:104-111`), the docstring says
only "the segmenter's object trajectory", nothing anywhere says `tracks[0]` is the mover,
and `fuzzlab/props/cegis_miner.py::_mine` — the code that certifies this engine — passes
none either. The unsafe default is undocumented and is what the certification actually
exercises. 72/115 obstacle-bearing worlds hit it; 0 obstacle-free worlds do, which is why
Fixture A (one object) never has.

### F-2 — 61 % of lifted rules promise an effect that does not happen

`lift` (`miner.py:227-264`) takes `members[0]` as template, substitutes the concrete
direction for `?dir` in its guard and frontier, and unions the supports. **It never
re-checks the substituted guard against the union.** Substitution can only weaken it:
`act==DOWN` fires on 1/4 of the evidence, `act==?dir` fires on all of it.

Seed 6, published verbatim (two rules, both named `push`):

```json
{"name":"push","action":"?dir","guard":["act==?dir"],"guard_cost_bits":6,
 "effect":{"type":"move","direction":"?dir"},"frontier":[["act==?dir"]],
 "frontier_size":1,"frontier_max_size":1,"frontier_truncated":false,
 "cegis_guard":[],"cegis_iterations":0,"cegis_trace":[],
 "lifted_from":["push_DOWN","push_RIGHT"]}
```

`act==?dir` is a tautology once `?dir` binds to the action. The rule therefore asserts
*"every action moves the object one cell in that direction"* — false on transitions
3, 5, 6, 7, 9 of that trajectory, all of which the generator labels `noop` and my pixel
oracle sees as no change. It was lifted from two per-direction rules that were each sound
(`push_DOWN: act==DOWN`, `push_RIGHT: act==RIGHT`) precisely because in that world no
DOWN or RIGHT action was ever blocked.

**104 of 149 lifted rules carry the tautological guard `["act==?dir"]`.** 91 of 149 fire
on at least one transition where the promised move does not occur — 342 such rows across
90 worlds. Fixture A escapes only because there the `free(strip(?dir))` conjunct was
load-bearing in all four directions, so the substituted guard stayed sound by luck of the
evidence, not by construction.

The same defect hits lifted **frontiers**, more coarsely: the template's frontier is
instantiated for directions it was never enumerated against. Seed 6's second `push`
publishes `["!in_bounds(strip(UP))","act==?dir"]` and `["act==?dir","at(0,1)"]` — literals
that came out of the `push_LEFT` enumeration and are now offered as hypotheses for UP,
DOWN and RIGHT. 76 such frontier entries in the 60-world sample.

Also visible in the block above: `cegis_guard: []`, `cegis_iterations: 0`,
`cegis_trace: []`. A consumer reading the frozen payload sees "the empty guard sufficed,
zero refinement needed". Nothing refined this rule at all — the fields are structurally
absent, published as if they were measured. And **27 of 131 worlds emit two distinct
rules under the same name `push`**, so `result.by_name("push")` silently returns one of
them and the candidate stream carries a name collision.

### F-3 — P4 is false as written; the payload's own field is the honest one

`MAX_FRONTIER_SIZE`'s comment promises exhaustiveness to 3 literals with anything deeper
flagged truncated. `mine` sets `size = min(max(len(cegis_guard), 1), max_frontier_size)`
(`miner.py:321`) and `truncated = len(guard) > max_frontier_size` (`:323`), so a rule
whose CEGIS guard came out at 1 literal enumerates its frontier at depth 1 — and reports
`frontier_truncated: false`.

Fixture A, `push_LEFT`, `frontier_max_size: 2`, `frontier_truncated: false`: the
3-literal guard `!at(10,0) ∧ !at(9,0) ∧ act==LEFT` is minimal-by-inclusion, consistent,
and absent. Same for `push_UP` with `!at(0,0) ∧ !at(0,7) ∧ act==UP`. 125 such omissions
across 25 gridworlds at depth 3.

This is the one finding I want to *under*-state. **P3 holds exactly** — I found zero
minimal guards missing within any rule's own declared bound, over every world I searched.
`frontier_max_size` is published in the payload and is accurate, so a consumer who reads
the field is not misled. What is wrong is the module constant's comment and the README's
example payload, which shows `"frontier_max_size": 3` for a two-literal `push` guard
(`README.md:86`) where the real value is 2. Documentation defect, not a mining defect.

### The gap that lets F-1 and F-2 through

All four invariants in `fuzzlab/props/cegis_miner.py` iterate `result.rules`
(lines 128, 161, 209, 236). `candidates()` publishes `result.all_rules`
(`__init__.py:86`). **Lifted rules are emitted and never audited.** And no invariant of
any engine compares a rule's `effect` against anything — all four ask only when a guard
fires. `guards_are_mutually_exclusive` / `explains_every_transition` are ground-only by
their own docstrings, and `props` deliberately re-derives them rather than calling them,
so neither closes the hole.

Consequence, measured: on all **162** worlds carrying a falsified published rule,
`fuzzlab.props.cegis_miner.check(world)` returns an empty finding list — no violation,
no skip. Verified directly on seeds 2, 5, 6.

---

## 5. What only the cross-check could expose

1. **F-1.** Every single-engine test of `cegis_miner` is internally consistent with the
   wrong object, because consistency is a property of guards against a *given* evidence
   set and the evidence set is what is wrong. It surfaces only when a source of truth
   outside the segmenter/miner pair says what moved — my pixel oracle and the generator's
   labels. `mdl_segmenter` is also blameless in isolation: it narrated the move correctly.
   The defect exists strictly at the seam.
2. **F-2.** Requires evaluating a lifted guard under the `?dir` binding, which no engine
   code and no invariant ever does. Ground rules and lifted rules are individually
   plausible; only checking the lifted one against the ground evidence it generalises
   over shows the substitution lost the separating power.
3. **The effect blind spot itself.** "Guards all correct, effects all wrong, battery
   green" was a hypothesis in the work order. It is now measured: 1 209 false effect
   assertions, 0 red lights.
4. **F-3** and the duplicate-`push` name collision need an enumerator and a second reader
   of the payload respectively — neither is reachable from inside the engine's own frame.

## 6. Where I could not reach a conclusion

* **Depth.** Frontier brute force stopped at 3 literals (Fixture A, 25 worlds) and 2
  literals (60 worlds). Minimal guards of 4+ literals are unexamined. `C(|V|,4)` with
  `|V| ≈ 64` is ~635 k subsets per rule; I chose not to sample, because a partial sweep
  reported as a pass claims coverage it does not have.
* **My pixel oracle is genuinely ambiguous.** Translating a sub-slab of a solid rectangle
  reproduces the same frame, so 41 of Fixture A's 49 transitions admit more than one
  delta. I never use it to say the engine chose the wrong delta — only that the published
  delta is in *no* explanation. Where it was unambiguous, the published delta was the
  minimum-|δ| explanation in 679/679 cases.
* **Whether F-1 is filed against `cegis_miner` or its callers.** I have established the
  default is unsafe, undocumented, and is the one the certification path uses. Who owns
  the fix — a `track=` argument at every call site, a "must move" check inside
  `transitions_from_segmentation`, or a documented contract on `tracks[0]` — is a design
  call, not mine to make. Work order says report, not repair.
* **Family coverage.** `gridworld` + Fixture A only. `hypset`, `jumpgraph`, `parityworld`,
  `blockworld` do not feed `cegis_miner`. Nothing here generalises past the grid family.
* **`teleport` naming.** `structural_name` calls any multi-cell move with a positive `at`
  literal a teleport (`miner.py:212-213`). I did not test whether that misfires, because
  P8 declares naming to be shape-derived and meaningless — there is no promise to falsify.

## 7. Reproduction

Harness (scratchpad, not committed):
`bruteforce_cegis.py` (independent evaluator + oracles), `run_fixtureA.py`,
`run_batch.py <n> <start> <depth>`, `run_strict.py <n>`, `run_final.py <n>`.
Deterministic: `gridworld.generate(seed)` is a pure function of the seed, and every
number above is keyed to seeds 1–200.
