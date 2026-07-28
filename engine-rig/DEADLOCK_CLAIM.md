# What a proved deadlock is worth to a planner

**The claim under test**, Theoria.md §1.9:

> 每证一个死锁，规划器同时提速

*Every deadlock proved, the planner speeds up at the same time.*

E2 measured it with a real Fast Downward and reported the speed-up half does not
hold. E7 audits that report: replicates it, tries to overturn it, and asks the
question its shape left open — **why** zero. This file is the evidence, the
boundary, and a suggested wording. It does not change Theoria.md; that is the
monitor's hand.

Everything here is from `runs/20260728T150713Z-E7-deadlock-claim-audit/`
(`claim_audit.json`, raw FD logs in `logs/`). Reproduce with:

```bash
cd engine-rig
export FAST_DOWNWARD=".../.toolchain/downward/fast-downward.py"
python -m audit --out runs/<id>
```

---

## Verdict

**The speed-up half of §1.9 does not hold on this rig, and E2 was right about
that.** The audit replicates its numbers to the expansion.

**But "a proved deadlock is a substitute for a heuristic, not an addition to
one" — E2's explanation — is not what the measurements say, and the real reason
is sharper and more useful.** On this instance family, every deadlock the carver
proves is *already implied by the delete relaxation Fast Downward computes
before search begins*. The theorems are not competing with the heuristic. They
are a strict subset of information the planner already had for free.

That relocates the claim's boundary from "which search you use" to **"whether
the planner's own relaxation is complete for deadness on this domain"** — a
property of the domain, checkable in advance, and the thing a future claim
should be conditioned on.

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

**The ladder, extended.** "The instances are too small" is the first objection,
so `far8`, where a blind search expands five figures:

| `far8` | before | after | dividend | absolute |
|---|---|---|---|---|
| `astar(blind())` | 12078 | 10799 | −10.6% | **−1279 nodes** |
| `astar(lmcut())` | 84 | 83 | −1.2% | −1 node |
| `astar(ipdb())` | 27 | 24 | −11.1% | **−3 nodes** |

`ipdb` at `far8` is the one row in this whole audit where an admissible
heuristic shows a double-digit percentage, and it is **three nodes**. Reporting
it as −11% next to blind's −10.6% would be arithmetic in the service of a
conclusion: the percentages are equal and the savings differ by a factor of 426.
The honest column is the absolute one. Across the ladder the admissible rungs
save between 0 and 3 expansions and blind saves between 227 and 1279.

## 2 · The pruner is connected, and the prize is large

The second objection to any "no speed-up" result is that nothing was pruned.
Measured on the bundled rung, where the pruner is a Python callable that can be
counted, plus an independent breadth-first walk written in `audit/claim.py` that
never consults the pruner and asks the theorems about each state afterwards:

| instance | blind exp | pruned exp | pruner fired | states cut | reachable | dead | dead fraction | plan |
|---|---|---|---|---|---|---|---|---|
| `far4` | 808 | 571 | 69 | 237 | 3342 | 1624 | **48.6%** | unchanged |
| `far6` | 3152 | 2788 | 78 | 364 | 42803 | 9928 | 23.2% | unchanged |
| `far7` | 8003 | 7041 | 100 | 962 | 110494 | 18988 | 17.2% | unchanged |

The hook fires, cuts states, and the plan is unchanged every time. **Between a
sixth and a half of the reachable space is dead by the theorems' own reckoning**,
so the prize is not small and the zero is not "there was nothing to win".

## 3 · Why the dividend is zero — the mechanism, measured

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

Two facts, and the second is the finding:

1. **On this family the delete relaxation is exactly the true dead set.** Not a
   subset — equal, at all three sizes. Fast Downward gets a complete deadness
   test for free, before the search starts, on every instance.
2. **The theorems are a strict subset of it, and the gap widens with size** —
   56%, 42%, 33% of the relaxation's coverage. There is not one state, at any
   size, that a theorem detects and the relaxation misses.

So a guard compiled from the theorems removes states A\* was already refusing to
expand, because an admissible heuristic returns infinity on them and A\* prunes
an infinite-h node without being told anything. **The dividend is zero because
the information is redundant, not because it is unused.**

The Python relaxation is checked against Fast Downward's own verdict on 16
rebuilt one-state problems: **16/16 agree**. An independent reimplementation
nobody compared to the original is a second guess, not a second opinion.

### The confirmation, from instances E2's batch could not contain

Every unsolvable instance in E2's batch was settled by FD's translator before
search, so the batch never asked a planner what it thought of a dead region.
`audit/deadstart.py` builds instances whose **initial state is already dead**,
one per theorem kind, with a live control:

| instance | the theorem's closure | unguarded `astar(lmcut())` |
|---|---|---|
| `deadstart-corner{4,5,6}` | `no_deleting_action` | 0 expansions, `h=infinity`, proved unsolvable |
| `deadstart-pair{4,5,6}` | `deleting_actions_blocked` | 0 expansions, `h=infinity`, proved unsolvable |
| `alive-pair{4,5,6}` | — (nothing dead) | 21 / 41 / 88 expansions, `h=9/13/17`, solved |

Both theorem kinds, unguarded, at zero cost. The control searches normally, so
the instrument can tell the two apart.

**This refuted the hypothesis the module was built to test.** The prediction was
that the two kinds would come apart — corner deadlocks fall out of grounding and
survive the delete relaxation, while pair deadlocks need mutexes and should not.
They do not come apart. The relaxation catches the pair case too, because
`clear` is *false* on a box's cell in the initial state and the relaxation never
adds it back without an actual push: dropping deletes does not manufacture the
space the player would need to get between two boxes. The prediction was wrong
and the reason it was wrong is the more interesting half.

## 4 · Where the claim does hold

* **On a search with no relaxation of its own.** The bundled BFS has none, and
  the theorems buy it 10–27% consistently, at every size, with the plan
  unchanged. `astar(blind())` — a control, never a selectable rung — replicates
  that on Fast Downward. §1.9's promise is true of a blind search and this rig
  can now say by how much.
* **As proof obligations, not as speed.** A deadlock theorem is a candidate the
  LLM adjudicates into the playbook as a `prune` clause, and an unsolvability
  certificate Lean can check without searching. §1.9's frequency argument — that
  deadlocks are the everyday form of unsolvability, where whole-level
  unsolvability is rare — is untouched by any of this. What is refuted is the
  speed clause, and only where a planner with its own relaxation is reachable.
* **The condition to state it under.** A proved deadlock is worth expansions to
  a planner exactly to the extent that it detects deadness the planner's own
  relaxation does not. That is a property of the **domain encoding**, testable
  in advance and cheaply: compute both sets and compare. On this sokoban
  encoding the answer is "none", at every size measured.

## 5 · Suggested wording

For §1.9, replacing the speed clause. Offered as a draft, not applied:

> 死锁定理的价值在于**可证的剪枝判据与不可解证书**，而不在于必然提速。它是候选
> 条款与 Lean 可查的证明义务，其数量优势（死锁是不可解的日常形态）不受影响。
>
> **提速须以实测为准，且取决于规划器自身的松弛是否已经覆盖该死区。** 在本仓库的
> sokoban 编码上实测：删除松弛（Fast Downward 在搜索开始前免费计算的那个）**恰好
> 等于**真实死区，而 carver 证出的定理是它的真子集——因此对可采纳启发式的节点收益
> 在 0 至 3 个扩展之间；对没有自带松弛的盲搜索则稳定为 10%–27%。判据：只有当定理
> 能判定规划器松弛判不出的死区时，提速才可期待。

In English, for the same paragraph:

> A proved deadlock is worth a **checkable pruning criterion and an
> unsolvability certificate**; it is not a promise of speed. Whether it speeds a
> planner up depends on whether that planner's own relaxation already covers the
> region, which is a property of the domain encoding and is cheap to test. On
> this repository's sokoban encoding the delete relaxation is *exactly* the true
> dead set and the proved theorems are a strict subset of it, so the saving on
> an admissible heuristic is 0–3 expansions; on a search with no relaxation of
> its own it is a steady 10–27%.

**Why this wording rather than "the speed-up does not happen".** The flat
negative is true of this rig and would be wrong as a general statement — it
would forbid the case where a theorem does beat the relaxation, which nothing
here rules out. Conditioning on the relaxation says what was measured, says what
would have to be true for the promise to hold, and hands the next person a test
instead of a verdict.

## 6 · What this does not show

* **One domain, one encoding.** Every number is sokoban as
  `fixtures/sokoban.py` encodes it, with a `clear` fluent that covers the player
  as well as the boxes. That encoding may be why the relaxation is complete for
  deadness; a formulation using negative preconditions instead might not be.
  Nothing here is a claim about planning in general.
* **One planner.** Fast Downward 24.06+, `astar(blind/lmcut/ipdb)`. The
  satisficing rung is not in this comparison because it is not
  length-optimal and the before/after plans would not be comparable.
* **Wall clock is worse than expansions, and E2 already said so.** Carving
  `far7`'s theorems takes 1.44 s and saves 0.08 s of blind search. The
  expansion dividend on the blind rung is real; the wall-clock dividend, with
  carving on the invoice, is negative everywhere in this batch.
* **`n_theorem_dead_outside_relaxation = 0` is a measurement, not a theorem.**
  It holds on every instance measured. A geometry where a carver theorem beats
  the relaxation would not contradict anything above — it would be the boundary
  case §4 says to look for, and it is what an adversarial reviewer was set to
  hunt (§7).

## 7 · Adversarial review

Two reviewers were run against the conclusions above with no brief except to
break them. Findings and every script are under
`runs/20260728T150713Z-E7-deadlock-claim-audit/attacks/`.

*(Filled in when they report; see that directory.)*
