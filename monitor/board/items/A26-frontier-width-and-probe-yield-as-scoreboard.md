priority: 2
cell: A26
territory: theoria-arm
deps: A24
spend: none

# A26-frontier-width-and-probe-yield-as-scoreboard · 记分板分不出「有信息的反驳」和「没信息的反驳」

`fleet-study/ITERATION_PROTOCOL.md` §2.4 的结论，来自四条真腿：现行记分板
（`Theoria.md:351`：电池 v0 + 七个意外计数 + 证明义务通过率 + theorize 轮数）
**无法区分一次窄化前沿的反驳和一次把整个假设集一次性清空的反驳**。R1b 的
`probe_refutation` 是 15（R1 是 5）——这个数在涨，而记分板说不出涨的是哪一种。

两个补丁，两者都由现成文件算出，零 API、零新 beat：

* **`frontier_width`**——探针对所选动作，假设集预测出的**互异**结果数。
  它是 `Theoria.md:208` 定义探针价值的那个分裂熵的上界。宽度 1 什么也不买，
  宽度 2 最多买一比特。今天实测：`ablation` 在 52 条探针上**全是 2**
  （`runs/20260801T0900Z-R2-frontier-by-generation/MEASUREMENT.json`）。
* **`probe_yield`**——观测结果落在候选预测集内的比例。真值在假设集**里面**的
  反驳是窄化，是环在工作；真值在**外面**的反驳一次淘汰全部候选、什么也没选中。
  今天实测：ablation 5/52 在里面，47 在外面。

两者今天都存在，但都在别人的 run 目录里：宽度在 R2 的
`MEASUREMENT.json`，yield 由 `fleet-study/runs/20260731T1723Z-ITERATION-PRACTICE/
probe_yield.py` 只读地算。**臂自己每条腿不产出这两个数**，所以下一轮读记分板
的人仍旧读不到它们。本件是把它们提成臂的每腿输出，接进 `round.json` 的
`legs[*]`——和 A24 那两列同一处落地，所以挂 A24 的依赖。

外部锚：OPINE-World 的记分板是本体错误频率**加解释范围**
（「说明先前异常观测的能力」，[2607.01531](https://arxiv.org/pdf/2607.01531)）。
`probe_yield` 就是在探针处测的解释范围。

验收：R1/R1b 四条腿离线补算出两个数，且宽度对 2026-07-31 那四条腿复算时必须
等于 R2 的「52 条全 2」；`round.json` 的 legs 带上这两列。

负样本，两条：一条**每条探针的真值都在假设集外**的 mock 腿必须读出
`probe_yield = 0`，而**不是**读成「没有探针」——0 和缺席在这个指标上是两句话；
一条只有一个假设的 mock 腿必须读出宽度 1 并被标成「这次探针什么也没买」，
而不是静默通过。
