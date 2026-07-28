# What a proved deadlock is worth to a planner

**The claim under test**, Theoria.md §1.9:

> 每证一个死锁，规划器同时提速

*Every deadlock proved, the planner speeds up at the same time.*

E2 measured it with a real Fast Downward and reported the speed-up half does not
hold. E7 audits that report: replicates it, tries to overturn it, and asks the
question its shape left open — **why** so little. This file is the evidence, the
boundary, and a suggested wording. It does not change Theoria.md; that is the
monitor's hand.

Measurements are from `runs/20260728T150713Z-E7-deadlock-claim-audit/`
(`claim_audit.json`, adversarial artefacts under `attacks/`, raw FD logs in
`logs/` and `attacks/logs/`). Where a figure comes from E2's run instead, it says
so. Reproduce with:

```bash
cd engine-rig
export FAST_DOWNWARD=".../.toolchain/downward/fast-downward.py"
python -m audit --out runs/<id>
python -m audit.verify runs/20260728T150713Z-E7-deadlock-claim-audit
```

**Three drafts of this document were wrong before this one.** §7 records what the
adversarial reviewers broke, including five numbers earlier drafts published.
Where a claim was narrowed, the narrowing is in the section that made it, not
only in §7.

---

## Verdict

**The speed-up half of §1.9 does not hold as a general promise, and E2 was right
about that.** The audit replicates its numbers to the expansion.

**E2's explanation — "a proved deadlock is a substitute for a heuristic, not an
addition to one" — is not what the measurements say.** On the `far{N}` family
every deadlock the carver proves is already implied by the delete relaxation
Fast Downward computes before search begins. The theorems are not competing with
the heuristic; they are a subset of information the planner already had for free.

**But the containment is not universal, and the dividend on an admissible
heuristic is not always zero.** An adversarial hunt found both boundaries:

* a theorem *can* detect a dead state the relaxation misses — one instance in
  267, and there is a **structural reason** it cannot happen in the `far{N}`
  family *for the singleton theorems the guard carries* (§3a). The boundary is
  **h² versus h¹**: the carver's mutexes are h², Fast Downward's pre-search
  deadness test is h¹.
* `astar(lmcut())` *does* save expansions on instances where containment holds,
  and **not by pruning** — every state the guard removes was already an lmcut
  dead end (§3c). Where containment *fails*, on `rnd0021`, lmcut goes 33 → 0 and
  the saving is entirely pruning.

The claim's boundary is therefore not "which search you use" and not merely
"whether the relaxation covers the region", but **whether the theorems' proof
system is stronger than the planner's own pre-search relaxation** — a property of
the domain encoding, checkable in advance.

---

## 1 · Replication

E2 §3b, re-measured from a fresh process, singleton guard held fixed on both
sides so only the configuration changes:

| instance | configuration | before | after | dividend | E2 |
|---|---|---|---|---|---|
| `far4` | `astar(blind())` | 837 | 610 | −27.1% | 837 → 610 ✔ |
| `far4` | `astar(lmcut())` | 23 | 22 | −4.3% | 23 → 22 ✔ |
| `far4` | `astar(ipdb())` | 12 | 12 | 0 | 12 → 12 ✔ |
| `far6` | `astar(blind())` | 3070 | 2762 | −10.0% | 3070 → 2762 ✔ |
| `far6` | `astar(lmcut())` | 47 | 47 | 0 | 47 → 47 ✔ |
| `far6` | `astar(ipdb())` | 18 | 18 | 0 | 18 → 18 ✔ |
| `far7` | `astar(blind())` | 7196 | 6365 | −11.6% | 7196 → 6365 ✔ |
| `far7` | `astar(lmcut())` | 69 | 68 | −1.4% | 69 → 68 ✔ |
| `far7` | `astar(ipdb())` | 21 | 21 | 0 | 21 → 21 ✔ |

**Every row reproduces exactly.** This is replication, not independence — it
re-runs `bench/`'s compiler and `bench/`'s FD driver, and is reported as such.
§2 and §3 are the parts that do not share code with what they check.

**The ladder, extended past where E2 stopped.** "The instances are too small" is
the first objection:

| instance | `astar(blind())` | `astar(lmcut())` | `astar(ipdb())` |
|---|---|---|---|
| `far8` | 12078 → 10799 (−1279, −10.6%) | 84 → 83 | 27 → 24 † |
| `far9` | 19272 → 17354 (−1918, −10.0%) | 102 → 101 | 78 → 30 † |
| `far10` | 27630 → 25215 (−2415, −8.7%) | 122 → 121 | 93 → 93 |

† **Both `ipdb` rows are withdrawn as evidence — see §7b.** They are artefacts of
iPDB's pattern generation, not deadlock dividends: `far9`'s 78 → 30 disappears
under two of nine random seeds and under a larger PDB budget. Quoting them as an
admissible-heuristic dividend would have been wrong, and an earlier draft of this
file did quote `far8`'s 27 → 24.

On Fast Downward's blind control the `far{N}` ladder runs **−8.7% to −27.1%**,
so `far9` and `far10` fall below the "10–27%" band E2 and this document's first
draft published. Off the `far{N}` ladder the spread is far wider still (§3c).

## 2 · The pruner is connected, and the prize is large

The second objection to any "no speed-up" result is that nothing was pruned.
Three independent checks:

**The guard reaches the search.** On `far6`, the rig's own grounder takes the
plain domain from 312 ground actions to 296 under the singleton guard — 16
removed, 0 added, all of them pushes into the four corners. Fast Downward's own
translator, asked the same question, reports 312 → 296 with a byte-identical set
of removed operator names (verifiable from `attacks/work/a1/sas-plain/output.sas`
against `sas-singleton/output.sas`; `a1_connected.py` printed its results and
wrote no JSON, so the rig-grounder half of this sentence has no artefact).

**The hook fires.** Measured on the bundled rung, where the pruner is a Python
callable that can be counted, plus an independent breadth-first walk in
`audit/claim.py` that never consults the pruner and asks the theorems about each
state afterwards:

| instance | blind exp | pruned exp | pruner fired | states cut | reachable | theorem dead | plan |
|---|---|---|---|---|---|---|---|
| `far4` | 808 | 571 | 69 | 237 | 3342 | 1624 (48.6%) | unchanged |
| `far6` | 3152 | 2788 | 78 | 364 | 42803 | 9928 (23.2%) | unchanged |
| `far7` | 8003 | 7041 | 100 | 962 | 110494 | 18988 (17.2%) | unchanged |

**Between a sixth and a half of the reachable space is dead by the theorems' own
reckoning**, so the prize is not small and the zero is not "there was nothing to
win".

*One caveat on that column.* `coverage()` counts **every** theorem, but the guard
whose dividend §1 reports carries only the 8 singleton ones. The two numbers are
not the same and this run never computed the second for the `clear` encoding, so
"theorem dead" here is an upper bound on what the guard removes. The direction is
safe — the overcount inflates the theorems and so cannot manufacture the
redundancy finding — but it is an upper bound and an earlier draft printed a
"guard-carried" column whose `far6` figure existed in no artefact at all.

## 3 · Why the dividend is small — the mechanism, measured

Three sets over one instance's whole reachable space:

* **`truly dead`** — no goal reachable, by backward search over the real
  transition relation;
* **`relaxation dead`** — the delete relaxation cannot reach the goal. This is
  what Fast Downward's translator computes before search, and what makes it
  print `No relaxed solution! Generating unsolvable task...`;
* **`theorem dead`** — covered by a `deadlock_carver` theorem.

| instance | reachable | truly dead | relaxation dead | theorem dead | theorem-dead the relaxation misses |
|---|---|---|---|---|---|
| `far4` | 3342 | 2904 | **2904** | 1624 | **0** |
| `far5` | 13774 | 10687 | **10687** | 4508 | **0** |
| `far6` | 42803 | 29776 | **29776** | 9928 | **0** |

On this family the delete relaxation is exactly the true dead set — equal, not a
subset — and the theorems are a strict subset of it, the gap widening with size
(56%, 42%, 33% of the relaxation's coverage).

**`far4` is verified exhaustively against real Fast Downward, not sampled.** Each
of the 3342 states was injected into the translated SAS task and only the search
component run, so FD answers about the real task: `astar(hmax())` returns
infinity on exactly the same 2904 states — **0 disagreements in 3342**. The same
sweep re-derived *truly dead* with `astar(blind())` run to exhaustion from every
state, an oracle sharing no code with the audit, and got the same 2904. The
state-by-state crosscheck of the Python relaxation against FD's translator now
stands at **116/116** across five geometries and two encodings, not the 16/16 an
earlier draft claimed.

So a guard compiled from the theorems removes states A\* was already refusing to
expand. This is confirmed with the translator bypassed, which matters because
FD's translator replaces the whole task when it settles an instance and would
otherwise confound the measurement: on 6 theorem-dead, 6 relaxation-dead-only and
6 live `far4` states, `lmcut` and `ipdb` both return **infinity on 12/12 dead**
states and finite values on every live one.

### 3a · The containment is not universal, and the exception has a structure

`n_theorem_dead_outside_relaxation = 0` survives 225 swept instances and 42 more
from a hand-and-random family — and **fails on exactly one**, `rnd0021`, which an
adversarial reviewer found and which was then verified against real Fast Downward:

```
######
#...##      player c34;  boxes b1@c42, b2@c12
#..#.#      goals  b1@c41, b2@c11
#....#
#....#      92 reachable, 0 goal states, 92 truly dead
######      relaxation dead 59 · theorem dead 70 · outside the relaxation 11
```

The 11 witnesses are `b1` on `c41`, `b2` on `c12`, the player anywhere it can
stand. FD's translator does **not** settle them (0 of 11 print `No relaxed
solution!`), `hmax` and `lmcut` return finite values 3–9, and `astar(blind())`
run to exhaustion proves each one unsolvable in 23 expansions. The theorem is
right and the relaxation is wrong. It is also the one instance in this audit
where a proved deadlock buys an admissible heuristic a large saving:
`astar(lmcut())` goes **33 → 0**.

**Why, and why `far{N}` could never have shown it.** A width-1
`no_deleting_action` theorem says grounding left no push out of that cell, so in
the relaxation no other position of that box can ever be added — hence if the
goal wants the box *somewhere else*, the relaxation is dead too. **A theorem of
this kind can escape the relaxation only if its pattern atom is itself a goal
atom** — a box frozen on its own goal. But then `excludes_goal` had to find a
mutex with a *different* goal atom, which means h² has proved the goal
conjunction inconsistent and the whole instance is unsolvable. `far{N}` is
solvable, so no `far{N}` singleton theorem can have a goal atom as its pattern,
so every one of them is inside the relaxation. Confirmed on `rnd0021`: the
escaping theorem's pattern atom is exactly `b1`'s goal atom, and
`goal_pair_h2_copossible` is false.

**So for the 8 singleton theorems the guard carries,
`n_theorem_dead_outside_relaxation = 0` on `far{N}` is a theorem about the
family, not a measurement.** That is a real narrowing of the argument's reach:
`far{N}` is *majority* width-2 (`far4` is 8 singleton + 8 pair, `far10` is
8 + 56), and a width-2 `deleting_actions_blocked` escape is neither exhibited
nor excluded. For the width-2 majority the zero remains a measurement at
far4/5/6 and an extrapolation above.

The real boundary is **h² versus h¹**: the carver's mutexes are h², Fast
Downward's pre-search deadness test is h¹, and `rnd0021` is a state the gap
between them contains. One more honest limit: `rnd0021` is unsolvable from its
initial state, so its theorem is a whole-instance unsolvability certificate
wearing a deadlock's clothes, not the interaction deadlock inside a solvable
instance that §4 asks for.

### 3b · "Exactly the true dead set" is a property of `far{N}`, not of the encoding

The equality in the table above does **not** generalise, and an earlier draft's
suggested wording promoted it to "this repository's sokoban encoding". Swept over
228 generated instances (225 analysed, 3 over the state cap) plus 42 from the
hand-and-random family:

| | instances | `relaxation dead == truly dead` | theorem-dead outside the relaxation |
|---|---|---|---|
| named + fuzz sweep | 225 | 202 | 0 |
| — of those, solvable | 28 | **15** | 0 |
| — of those, dead from the start | 197 | 187 | 0 |
| hand + random family | 42 | 40 | **1** (`rnd0021`) |

**On genuinely solvable instances the delete relaxation is not the true dead set
about half the time** — 13 of the 28 solvable sweep instances fail it. Two of the
failures are hand-built named geometries, `three-a` (208 states short) and
`goal-in-corner` (26); the other eleven are fuzz instances. Five further named
geometries fail it too — `ell` (45), `rect3x5`/`rect5x3` (39), `plus`, `plus2` —
as does `swap-passage` (7974 truly dead, 7344 relaxation dead), but those have no
reachable goal state at all and so say less.

Every failure is in the same direction: the relaxation is **incomplete, never
unsound**. The containment chain `theorem_dead ⊆ relaxation_dead ⊆ truly_dead`
holds everywhere except the single `rnd0021` exception to its left-hand link.

The carver is sound on all 267 instances checked: not one theorem-dead state is
alive. That test is vacuous on the unsolvable majority, though — only 3 of the 42
hand-and-random instances are solvable, so the non-vacuous soundness evidence is
those 3 plus far4/5/6.

### 3c · The lmcut dividend is real, and where containment holds it is not pruning

An adversarial hunt over random geometries — 71 instances screened for an lmcut
baseline above 40 expansions, 3 kept — found `astar(lmcut())` savings on all
three survivors, and a hand-built family found three more, of which the largest
is shown:

| instance | `astar(lmcut())` | saved | `astar(blind())` |
|---|---|---|---|
| `three-far8` | 9175 → 9048 / 9022 ‡ | −127 / −153 (−1.4% / −1.7%) | — |
| `hunt0021` | 701 → 690 | −11 (−1.6%) | 6654 → 3316 (−50.2%) |
| `hunt0037` | 193 → 178 | −15 (−7.8%) | 5724 → 4556 (−20.4%) |
| `hunt0070` | 122 → 117 | −5 (−4.1%) | 9588 → 7223 (−24.7%) |
| `swap-passage` | 630 → 630 | 0 | 7974 → 3110 (−61.0%) |

‡ **`three-far8`'s guarded compile is not byte-reproducible.** The guarded task on
disk and a clean rebuild from the same source hash differently
(`attacks/verify/admissible/three-far8_provenance.json`: `guard_matches_disk:
false`; the *base* task does match). The on-disk task gives −127 and the rebuild
gives −153. Both are reported because neither can be preferred on the evidence,
and the non-determinism is itself a defect against this repo's byte-stability
convention — it is not tracked down here.

Plan lengths are unchanged and every guarded plan was replayed against the
original domain. **This is not tie-breaking noise**, which was the obvious
objection and was tested: swapping A\*'s secondary key moves `hunt0070`'s
baseline from 122 to 178, but the tie-break-invariant quantity — the count of
distinct states with *f* < C\*, which A\* must expand under any tie-breaking —
falls every time and is identical across the tie-break rules tried (four rules
for the three hunt instances, three for `three-far8`): 695 → 683, 162 → 154,
113 → 108, and 8428 → 8321 / 8298 for `three-far8`'s two task versions.

**Where containment holds, the cause is not the one §1.9 promises.**
`n_theorem_dead_outside_relaxation = 0` on the three hunt instances and on
`swap-passage`, so lmcut already returned infinity on every state the guard
removes: those states were *evaluated as dead ends and never expanded* — FD's
`Dead ends:` counter falls 59 → 28, 15 → 4, 13 → 11. A\* was not expanding them,
so removing them cannot be the saving. (`three-far8` is over the analyser's
400 000-state cap, so its containment is **unmeasured**; the no-pruning inference
is verified on the three small rows and assumed on the large one.)

What is left is that deleting the dead push operators makes the delete relaxation
harder to solve, so lmcut's estimate can rise on *live* states. **That mechanism
is exhibited on one instance, not four**: `hunt0021`'s live initial state has
h = 15 unguarded and h = 18 guarded, while `hunt0037`, `hunt0070` and
`three-far8` save expansions with h(init) **unchanged** (18/18, 14/14, 27/27).
So the mechanism is demonstrated once and is consistent with, but not
established by, the other three — where a competing explanation (fewer dead
successors, hence fewer reopenings and evaluations; `three-far8` reopened
124 → 107) is not excluded.

This is why the containment result does **not** license the sentence an earlier
draft closed this section with. A compiled guard is a *domain transformation*,
not a per-state filter; `theorem_dead ⊆ relaxation_dead` says the guard adds no
new dead states, and says nothing about what removing 10–24 operators does to the
heuristic computed on the transformed task.

### 3d · The confirmation, from instances E2's batch could not contain

Every unsolvable instance in E2's batch was settled by FD's translator before
search, so the batch never asked a planner what it thought of a dead region.
`audit/deadstart.py` builds instances whose **initial state is already dead**,
one per theorem kind, with a live control:

| instance | the theorem's closure | unguarded `astar(lmcut())` |
|---|---|---|
| `deadstart-corner{4,5,6}` | `no_deleting_action` | 0 expansions, `h=infinity`, proved unsolvable |
| `deadstart-pair{4,5,6}` | `deleting_actions_blocked` | 0 expansions, `h=infinity`, proved unsolvable |
| `alive-pair{4,5,6}` | no theorem covers the initial state | 21 / 41 / 88 expansions, `h=9/13/17`, solved |

Both theorem kinds, unguarded, at zero cost. The control searches normally, so
the instrument can tell the two apart.

**One instrument failure in this table.** On all three `alive-pair` instances the
**`full` guard** runs of `lmcut` and `ipdb` failed outright — exit 34, *"This
configuration does not support axioms!"* — because the compiled full guard emits
a `forall` that FD's normaliser turns into an axiom the optimal configurations
reject. That is a standing limit on what a compiled guard can be handed to an
admissible search, inherited from E2 §3c, and the rows above are the singleton
guard's.

**This refuted the hypothesis the module was built to test.** The prediction was
that the two kinds would come apart — corner deadlocks fall out of grounding and
survive the delete relaxation, while pair deadlocks need mutexes and should not.
They do not come apart.

The *reason* given for that in an earlier draft was also wrong, and a reviewer
who re-encoded sokoban with `occupied` instead of `clear` showed it: the
relaxation still finds all 2904 dead states on `far4` with occupancy information
removed entirely. What is load-bearing is **static push geometry** — a box
against a wall has no pusher cell outside the wall, so it is confined to one row
or column no matter what the relaxation does with `clear`. The relaxation's
verdict changed on only 1 of 8 re-encoded levels. (What *does* change is the
carver: theorem counts move on 6 of the 8 levels and pair theorems vanish
entirely, 16 → 8 on `far4`, because it cannot reason about negative
preconditions.)

## 4 · Where the claim does hold

* **On a search with no relaxation of its own.** The bundled BFS has none, and
  the theorems buy it **11.5%–29.3%** at the three sizes measured (§2), plan
  unchanged. `astar(blind())` — a control, never a selectable rung — gives
  **8.7%–27.1%** across `far4`…`far10`. §1.9's promise is true of a blind search
  on this family and this rig can say by how much.
* **But not on every instance, even for a blind search.** Off the `far{N}`
  ladder the blind dividend runs from **0%** (`stub-wall` 33 → 33 and `rnd0013`
  12 → 12, both solvable, both with theorems proved and operators removed)
  through 62.3% (`door-swap` 1230 → 464) to 100% (`rnd0021` 92 → 0, where the
  guard settles the instance outright). There is no stable band; there is a
  family on which it is stable.
* **On an admissible heuristic, a few percent where containment holds, and by a
  different mechanism.** 0 to −153 expansions, 0% to −7.8%, via a relaxation that
  is harder to solve on the transformed task rather than pruning of dead states
  (§3c). Where containment *fails*, the saving is pruning and can be total:
  `rnd0021` lmcut 33 → 0.
* **As proof obligations, not as speed.** A deadlock theorem is a candidate the
  LLM adjudicates into the playbook as a `prune` clause, and an unsolvability
  certificate Lean can check without searching. §1.9's frequency argument — that
  deadlocks are the everyday form of unsolvability, where whole-level
  unsolvability is rare — is untouched by any of this. What is refuted is the
  unconditional speed clause.
* **The condition to state it under.** A proved deadlock is worth expansions to a
  planner to the extent its **proof system is stronger than that planner's own
  pre-search relaxation**. The carver proves with h² mutexes; Fast Downward's
  pre-search deadness test is h¹. Where the two coincide — which on this sokoban
  encoding is every solvable instance measured — the pruning dividend is nil.
  Where they do not, as in `rnd0021`, a theorem detects deadness the planner
  misses and the dividend is large. That is a property of the domain encoding,
  testable in advance and cheaply: compute both sets and compare
  (`audit.claim.coverage`).

## 5 · Suggested wording

For §1.9, replacing the speed clause. Offered as a draft, not applied:

> 死锁定理的价值在于**可证的剪枝判据与不可解证书**，而不在于必然提速。它是候选
> 条款与 Lean 可查的证明义务，其数量优势（死锁是不可解的日常形态）不受影响。
>
> **提速须以实测为准，且取决于定理的证明系统是否强于规划器自身的前置松弛。**
> carver 用 h² 互斥证明；Fast Downward 搜索前的死端判定是 h¹。本仓库 sokoban 编码
> 上实测：在测到的**可解**实例中两者重合，定理判出的死状态无一在松弛之外，因而
> 对可采纳启发式几乎没有剪枝红利——lmcut 仍会省下至多 153 个扩展（≤7.8%），但在
> 实测的一例上那来自删去死推动作后松弛变紧、活状态上的 h 抬高，而非剪掉死状态。
> 一旦定理落在松弛之外（`rnd0021`），红利就是剪枝，且可以是全部（lmcut 33→0）。
> 盲搜索在 `far{N}` 族上稳定得到 9%–27%，但跨实例可以是 0% 到 100%。判据：只有当
> 定理判定的死区落在规划器自身松弛之外时，剪枝提速才可期待；这一条件可在跑规划器
> 之前算出来。

In English, for the same paragraph:

> A proved deadlock is worth a **checkable pruning criterion and an
> unsolvability certificate**; it is not a promise of speed. Whether it speeds a
> planner up depends on whether the theorems' proof system is stronger than that
> planner's own pre-search relaxation — the carver proves with h² mutexes, Fast
> Downward's pre-search deadness test is h¹. On this repository's sokoban
> encoding the two coincide on every **solvable** instance measured, so there is
> almost no pruning dividend for an admissible heuristic; lmcut still saves up to
> 153 expansions (≤7.8%), and on the one instance where the mechanism was
> isolated it saves them by tightening the relaxation and raising h on *live*
> states rather than by pruning. Where a theorem does fall outside the relaxation
> (`rnd0021`) the dividend is pruning and can be total — lmcut 33 → 0. A blind
> search gains a steady 9%–27% on the `far{N}` family, but 0%–100% across
> instances generally. The criterion: expect a pruning speed-up only where the
> theorems decide deadness the planner's own relaxation cannot, and that is
> computable before the planner is run.

**Why this wording rather than "the speed-up does not happen".** The flat
negative is wrong twice over: it forbids the `rnd0021` case where a theorem does
beat the relaxation, and it hides the small-but-real lmcut effect. Conditioning
on the proof system says what was measured, says what would have to be true for
the promise to hold, and hands the next person a test instead of a verdict.

## 6 · What this does not show

* **One domain, one encoding.** Every number is sokoban as `fixtures/sokoban.py`
  encodes it. Nothing here is a claim about planning in general.
* **One planner, and one of its heuristics is not a usable instrument.** Fast
  Downward 24.06+, `astar(blind/lmcut/ipdb)`. §7b shows `ipdb` expansion counts
  move with its pattern-generation lottery by far more than the effect under
  study, so no `ipdb` row in this audit is evidence either way.
* **`far7` and `far8` have no *relaxation-dead* measurement.** §2's wiring table
  covers `far7`, but §3's three-set table stops at `far6`; containment at larger
  sizes rests on §3a's structural argument, which covers only the singleton
  theorems.
* **Only `far4` is verified exhaustively against Fast Downward.** `far5` and
  `far6` rest on the audit's own Python relaxation — now validated exactly at
  `far4` and on 116 one-state problems, which is strong but is not proof.
* **`three-far8`'s guarded compile is not byte-reproducible** (§3c ‡), and the
  cause was not found.
* **Wall clock is worse than expansions.** The figures for this are E2's, not
  this run's: carving `far7`'s theorems takes 1.44 s against 0.08 s of blind
  search saved (`runs/20260728T072633Z-E2-fd-ladder-bench/RUN_STATE.md`). This
  run's `far7` blind search times are 0.0125 s → 0.0102 s, against the same
  carve. Either way the wall-clock dividend, with carving on the invoice, is
  negative everywhere in both batches.
* **The textbook four-box deadlock was never measured** (§7d).

## 7 · Adversarial review

Six reviewers were run against the conclusions above with no brief except to
break them, and they broke five published numbers. Scripts and artefacts are
under `runs/20260728T150713Z-E7-deadlock-claim-audit/attacks/` — with two
exceptions noted in §7a, where the script printed to stdout and stored nothing.

### 7a · What survived

* **The guard is connected.** 312 → 296 ground actions on `far6`, 16 removed and
  0 added, at FD's own translator (`attacks/work/a1/`); a decisive-transition
  probe finds a 1-step plan on the plain domain and none on the guarded one.
  `a1_connected.py` wrote no JSON, so its rig-grounder half and its probe's exit
  code survive only as the absence of a plan file.
* **The instrument is sound.** 104 of E2's committed FD logs scanned, 0
  structural problems, 0 of 36 instance/rung pairs given different `--search`
  arguments, and the parser demonstrated reading `Expanded N state(s).` rather
  than `Expanded until last jump:` on the one log where they differ.
  `a4_instrument.py` also stored nothing, so these three numbers are not
  independently checkable from this run.
* **The relaxation really is FD's.** The exhaustive `far4` sweep (0/3342
  disagreements) and the 116/116 one-state crosscheck, including 48 problems in a
  negative-precondition re-encoding built specifically to break the Python
  fixpoint (`fd_crosscheck.py`, `attacks/independent/`).
* **The carver is sound** on all 267 instances checked, though the test is
  non-vacuous on only a handful (§3b).
* **The goal-state cut does not bias the sets.** Enumerating past goal states
  changes only the live count (`far4` 3342 → 3352); all three dead sets are
  byte-identical (`goalcut.json`).

### 7b · The two `ipdb` rows, withdrawn

`far9` 78 → 30 and `swap-passage` 454 → 0 looked like large admissible-heuristic
dividends. Both are artefacts of iPDB's pattern generation, established by
pinning the generator:

| `far9` | base | guarded |
|---|---|---|
| `cpdbs(systematic(2))` | 180 | 180 |
| `cpdbs(systematic(3))` | 76 | 75 |
| `ipdb()` default | 78 | **30** |
| `ipdb(random_seed=0)` / `(random_seed=11)` | 76 | **76** |
| `ipdb(pdb_max_size=8e6)`, seeds 0/1/42 | 76 / 27 / 30 | 76 / 27 / 30 |

Two of the nine seeds tried give no dividend at all, and with a larger PDB budget
the *unguarded* run reaches the guarded run's number on its own.

`swap-passage` is sharper and its disposal is more interesting. The 454 → 0
collapse is stable across all nine seeds, so "hill climbing got lucky" does not
explain it. The reviewer instead exhibited the pattern: iPDB's winning projection
on the guarded task — `{b1, b2, player}` plus eight `clear` variables — gives
h = ∞ and 0 expansions **on the unguarded task too**. The base PDB for it is
2,725,888 entries; the guarded one is 1,103,872, because the translator drops the
eight proved-dead cells from each box variable's domain. **iPDB's default
`pdb_max_size` is 2,000,000.** The guard's entire contribution is making the
abstraction cheap enough to fit under the cap — confirmed by raising the budget,
after which the unguarded run also reports 0 expansions. Thirty-six random
patterns of comparable shape (9 variables, ~0.5–0.7M entries) gave identical
values on both tasks, 0 of 36 infinite.

**Consequence:** an earlier draft's "0–3 expansions" was falsified, and its
`far8` `ipdb` 27 → 24 was one of these artefacts. `ipdb` expansion counts are not
a usable instrument for an effect this size, and the whole ipdb column has been
demoted to "measured, not evidence".

### 7c · The conclusions that broke

* **`n_theorem_dead_outside_relaxation = 0` is falsified** by `rnd0021`, 11
  states, verified against real Fast Downward. §3a carries it, with the
  structural argument for why `far{N}` cannot exhibit one — which turns the
  audit's headline number into a theorem about the family *for the singleton
  theorems* and relocates the boundary to h² versus h¹. Better than what it
  replaces, and it exists only because the number was attacked.
* **"The dividend is zero because the information is redundant, not because it
  is unused" is withdrawn.** A false exclusive on three counts. Containment does
  not entail a zero dividend, because a compiled guard is a domain transformation
  and not a per-state filter — the `lmcut` rows of §3c are the counterexample.
  "Unused" is literally true on some rows: `logs/R-far6-ipdb-before.log` reports
  `Dead ends: 0`, so that search never generated a dead state at all. And the
  effect that does exist is a third thing neither word names.
* **Two published ranges were wrong.** "The saving on an admissible heuristic is
  0–3 expansions" (§7b), and "a steady 10–27%" for blind search — contradicted at
  both ends by `far10` (−8.7%) and by `stub-wall`/`rnd0013` (0%),
  `door-swap` (62.3%) and `rnd0021` (100%). §4 now states the `far{N}` band and
  the cross-instance spread separately.

### 7d · What the attacks did not settle, and should not be read as settled

* **`a6_subsets.py` produced nothing.** It is the one instrument that would
  decide monotonically whether an admissible dividend is information or
  perturbation, by carrying *k* of 8 theorems for *k* = 0…8. The session was
  killed with roughly 9 of 72 configurations run and it wrote no output. The
  `ipdb` disposal in §7b was reached another way; the monotonicity test remains
  undone.
* **`wider.py`'s zero is vacuous.** It asks whether width-3 theorems catch states
  the relaxation misses, but evaluates that question only on states the wide
  theorems cover and the narrow ones do not — and that set is **empty** on both
  instances it ran. Zero states were tested. Width 4 never ran anywhere (both
  instances have 3 boxes), and `four-block` — the board built so the textbook
  2×2 four-box deadlock is one push from the start, the module's entire
  motivation — is **absent from the output**. The real finding buried there is
  that width-3 packed patterns add exactly zero coverage over width-2, on
  instances where 12 092 truly-dead states (`three-c`; 70 on `three-b`) are
  detected by no theorem at all.
* **`a2b_ipdb_repeat.py` tested the wrong thing.** It checks whether FD's `ipdb`
  is repeatable on a *fixed* input, which cannot discriminate the hypothesis it
  names — the two numbers come from two different tasks. It also wrote no output.
* **`a7_hunt.py` was killed mid-run**, at 71 of a default 400 instances. Its 3
  hits are real; its yield statistics are a partial run's and are quoted as such.
* **The `occupied` re-encoding is not a faithful delete relaxation.**
  `relaxed_reachable_goal` ignores `pre_negative`, so the occupied column is
  strictly weaker than a real one. The direction is conservative — a faithful
  relaxation could only find *more* dead states, which strengthens §3d's
  conclusion — but those numbers must not be published as that encoding's
  relaxation.
* **Two sweep instances are duplicates** (`far4` ≡ `open4far`, `open4` ≡
  `goal-against-wall`) and three fuzz instances have no theorems at all, so the
  honest denominator for the subset claim is 220, not 225.
* **`three-far8`'s containment is unmeasured** — over the analyser's state cap —
  so §3c's no-pruning inference is verified on three instances and assumed on the
  one carrying the largest saving.
