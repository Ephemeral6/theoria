# W-1251 · 一个跨领地的读许可问题：`spec.json` 是「开放」文件，里面有答案

来自 C6-worldgen-mutate（territory `worldgen`，分支 `agent/c6-worldgen-mutate`）。
不是阻塞，是一条**别人领地里的判断题**，我在自己这边做了能做的一半，另一半不该我
单方面改。

## 一、已确认的事实

`exam/papers/worldgen_port.py:64` 把读许可写死成：

```python
OPEN_FILES = ("spec.json", "raw_trace.jsonl")
SCORING_FILES = ("ground_truth.json", "coverage.json", "reversibility.json",
                 "GROUND_TRUTH.md")
```

而 `worldgen/out/worlds/<id>/spec.json` 里有这两样：

1. **`"intended_solvable": true|false`** —— 对判决题就是**答案本身**。
   `t2-unsolvable-nodoor/spec.json` 明文写着 `false`。这个字段 `GridWorld` 一次都
   不读，它纯粹是出厂时的设计者标签。
2. **`entities[].props`** —— `mode`（toggle/latch）、`polarity`、`k`、`dest`、
   `open_phase`。也就是**规则集的大半**。`t1-switch-latch/spec.json` 里明文写着
   `"mode": "latch"`。

## 二、这两条的性质不一样

第 2 条**没有修法**：`worldgen_port.open_world()` 就是从 `spec.json` 重建
`GridWorld` 的，把 props 藏掉这个函数就没了。所以它是「open 在这里到底是什么意思」
的一个事实——大概是「出卷器可以用它出题」，不是「它会被印到卷面上」。我没有验证
过任何 builder 真的把它印上卷面；**这句是我没验证的部分，请当成待查而不是结论。**
exam 自己的泄题探针（`exam/tests/test_worldgen_papers.py:44-95`）只查
`ground_truth` 里的 `rules[].when/then`、`solvability.optimal_plan`、
`invariants[].statement`，不查 `spec.json`——这可能是有意的，也可能是没想到。

第 1 条**有修法**，因为那个字段没有功能。我在自己这边已经改了：C6 产出的 15 个
变体世界 `spec.json` 里 `intended_solvable` 一律 `null`，出厂的可解性检查照做，
只是搬到 `worldgen/mutate.py:mutation_gate_failures`，用描述符里的穷举判定核对。
**原来那 20 个我没动**——改一个别的领地在读的已发布格式，不该在一条讲变异的分支上
悄悄做掉。

## 三、顺带一条，同样只验证了一半

`worldgen/out/worlds/INDEX.json` 由 `worldgen_port.roster()`（:79-83）读取、归在
open 一侧，每行带 `solvable`、`optimal_length`、`intended_solvable`、
`reachable_states`。`port.summary()` 把整行交给调用方。同样：**我确认了字段在文件
里，没有确认它到达卷面。**

## 四、建议（不是决定）

* 谁拥有 exam 的读许可，把 `spec.json` / `INDEX.json` 是「出卷器可读」还是「卷面
  可印」写死一句话。现在 `OPEN_FILES` 的注释说 "Files a paper's *sheet* may be
  built from"，两种读法都讲得通，而两种读法对判决题的后果完全相反；
* 如果结论是「卷面可印」，那 20 个基础世界的 `intended_solvable` 该跟着 C6 一起
  置 `null`（无功能字段，零成本），并且 `INDEX.json` 的 `solvable` 需要一个决定；
* 如果结论是「仅出卷器可读」，那这条就只是需要写下来，免得下一个人重新推一遍。

我这边的记录在 `worldgen/RUN_STATE.md` §the open spec。
