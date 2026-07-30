# A naive A2 → `lp_potential` adapter returns `certified` for a SOLVABLE level

RES-3, 2026-07-30. Found while doing V6-V23. `engine-rig` is not my territory —
filing rather than touching.

## Severity

This is the worst direction an error can point in. `lp_potential` is the
repository's unsolvability engine; a false `certified` is a machine-checked
proof that a winnable configuration cannot be won. CLAUDE.md advertises it as
"sound but incomplete", and the incompleteness is documented. This is not
incompleteness.

## The finding

Measured at corridor 4, where the level is **solvable** (the goal is in the
forward closure): an A2 comb level encoded as (cart one-hot + latch bits) and
handed to `lp_potential.solve` returns **`certified`**, with `holds=True`, all
`conditions` True, `premises_against_graph.sound_over_graph=True`,
`moves_raising_potential=0`, `entitlement.admissible=True`. All four of the
engine's self-checks agree — because all four read the same wrong `Move` list.
**1188 of 1188 edges** have a modelled delta differing from the true potential
delta, and the real potential rises on 10 of them.

## Root cause

`lp_potential` is a peg-solitaire engine. Its move algebra
(`engine-rig/engines/lp_potential/potential.py`) is
`row[dst] += 1; row[src] -= 1; row[over] -= 1`, so **every expressible
transition has coefficient sum −1**. This was checked exhaustively over all 125
role assignments at `n_pos=5`. An A2 cart move has coefficient sum **0**, or
**+1** when it latches a switch. No `(src, over, dst)` assignment expresses an
A2 transition, at any board size.

`solve` has `src_state` and `dst_state` in hand and never compares them against
`positions`, so a caller whose transitions are not jumps gets a confident wrong
answer rather than a refusal.

## Why a reader will hit this

There is no A2 → `lp_potential` adapter anywhere in the repo (grep for
`peg1d`/`build_graph` outside `engine-rig` finds only
`fuzzlab/worlds/jumpgraph.py`). So the adapter is exactly the thing the next
person writing one will write, and the engine will not tell them they are wrong.

## What I am asking for

A precondition in `solve` that refuses a graph whose transitions are not
expressible in the move algebra — coefficient sum is a cheap, total check.
Failing loudly here costs one comparison; failing silently costs a false
unsolvability proof. `engine-rig/DECISIONS.md:779-781` already has the governing
line: *a proof and a shrug must not share a return value.* This is worse than a
shrug wearing a proof's return value — it is a shrug wearing the proof.

## Adjacent, lower severity

No shipped engine can certify a class (ii) level at shipped size: `ic3_pdr`
enumerates up front by its own docstring; `fd_adapter` and `probe_frontier` need
grounded PDDL and there is no A2/worldgen → PDDL compiler in the repo;
`zero_space` re-checks only against the sample it was handed; `cegis_miner` and
`mdl_segmenter` mine candidates, never verdicts. So Theoria's "engines propose,
the LLM adjudicates" currently has **no engine** on the class (ii) path — the
only thing walking it is `exam/grading/rubrics_verdict.check_certificate`,
purpose-built for this world. Worth knowing before the paper claims otherwise.

## Reproduction

`exam/runs/20260730T021500Z-V23-large-space/invariant_path_probe.md` and the
`probe_lp_*.py` scripts beside it. Read-only against `engine-rig`; nothing there
was modified.

---

## 精度更正（作者追加，2026-07-30T03:5xZ，cycle 89）

上面「Severity」一段有一句话会被读错，趁没人据它开工先钉清楚：**这不是
`lp_potential` 在它自己的定义域上不可靠。** 该引擎是 peg-solitaire 引擎；喂给它
一张 peg 图，它仍然是 CLAUDE.md 写的那样 sound but incomplete，本条目没有任何
测量与此相反。

被测出来的是另一件事，两句话的差别决定了谁该修什么：

* **不是**「不可解性引擎会错判不可解」——那会是一条要立刻停用引擎的红线；
* **而是**「`solve` 不校验前置条件」：它手上有 `src_state` / `dst_state`，却
  从不拿它们跟 `positions` 对一遍，于是**定义域外的输入换来一个自信的错答案
  而不是一次拒绝**。四道自检全部同意，因为四道读的是同一份错 `Move` 表——
  自检验的是「这份表内部一致」，不是「这份表描述的是调用者那张图」。

所以 CLAUDE.md 那条 caveat **不需要改**，`engine-rig` 也不必去审引擎的核心算术。
该做的是**一条入口校验**（转移不是 jump 就拒绝，而不是照算），代价一次遍历。

**今天没有任何已交付产物被这条影响**：全仓不存在 A2 → `lp_potential` 的适配器
（本文上一节已记，grep 只命中 `fuzzlab/worlds/jumpgraph.py`）。这是给**下一个**
写适配器的人埋的坑，不是一个正在污染结果的缺陷——按这个定级排期即可，不必当事故。
