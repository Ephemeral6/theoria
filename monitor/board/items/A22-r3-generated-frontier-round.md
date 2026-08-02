priority: 1
cell: A22
territory: theoria-arm
deps: A23-anchor-drift-on-the-default-leg
spend: none — the api half was delivered as R2/R2b, see the 2026-08-02 reconciliation at the foot

# A22-r3-generated-frontier-round · R3 是唯一还需要花钱的一件，它现在被支出天花板挡着

`--frontier generated` **已经建好、已经离线证明、默认关闭**
（`theoria-arm/runs/20260801T0900Z-R2-frontier-by-generation/`）。R2 的反事实
replay 不是模拟：每条假设都由 `inner/probe.build_hypotheses` 本人、在从该 leg
自己的 `books/snapshots/` 重编译的 manual 上重建，52 条探针**全部**逐键逐哈希
复现了 `probes.jsonl` 记的 ablation 预测（`unreconstructed: 0`）。结果：

```
ablation  前沿含世界答案     5 / 52
generated 前沿含世界答案    43 / 52     (追回 38，仍漏 9)
前沿宽度  ablation 2,2,2…（52 条全是这一个值）  generated 5,6,8,10
锚点漂移  35，且这 35 条 100% 落在 ablation 前沿之外
```

`REPLAY.json` 里还有一条被**建成、量过、砍掉**的生成器：`action_replay` 说中
15 次，边际贡献 **0**（15 条全是 `world_anchored_manual` 已有的答案，仍漏的 9
条一条不沾），所以它只是摊薄每个动作的分裂熵。这条判决用
`replay_frontier.py --with-cut-generators` 可以随时复算——砍掉的东西留着它的
可检查性，这是本件不必再议的部分。

**欠的是唯一一件 replay 无法交付的事：这些数在活局上是不是这样。**
预注册的四个量（R2 README §4，写在任何活腿之前）：

| 量 | 2026-07-31 (ablation) | `--frontier generated` 预测 |
|---|---|---|
| 前沿宽度 | 52/52 都是 2 | ≥3，占探针 ≥80% |
| 完成探针的脱靶率 | 47/52 = 90.4% | ≤40%（replay 说 17.3%，40% 是活腿首探后发散的余量） |
| `information_gain_bits` | 52 条全 0.000 | >0，占完成探针 ≥半数 |
| 锚点漂移 | 从未计算 | 每条探针都报，且在 manual 误判的腿上非零 |

## 花费与阻塞——本件现在不许执行

R1b 实测（`runs/_rounds/20260801T001851Z-R1b/round.json`）：两条腿 $17.749106
与 $17.390721，一轮合计 **$35.139827**，`ceiling_per_leg: 25`，两条腿都以
`spend_gate_tripped` 收场，`levels_completed: 0`。
`fleet-study/ITERATION_PROTOCOL.md` §2.10 给的四腿确证轮口径是 **$40–55**。

**程序当前超支：已花约 $285，天花板 $214.90，所有者尚未裁决。** 所以本件的
活局部分**不得开始**，任何认领本件的会话没有支出权。可做且必须先做完的是
A23（默认腿也能报锚点漂移）与本件的干跑：`--frontier generated` 走 mock 整轮、
`round.py --knob --frontier=generated` 产出一份 `round.json` 骨架、把上表四行
预测写进 `_rounds/<id>/round.json` 的 `prediction` 字段**在开跑之前**。

一句话给所有者：**$35（两腿，R1b 口径）或 $40–55（四腿，§2.10 口径）买的是
上表四行的真/假**，尤其是第二行——如果宽度上去了而 yield 仍≈0，
`ITERATION_PROTOCOL` §3.4 的重分类规则会把失败类从「戳探设计差」改判为
`Theoria.md:345` 表达力不够，下一个旋钮就换成 DSL 而不是探针。这是本轮唯一
买得到的东西，也是它值这个价的理由。

验收（离线半）：mock 轮跑通；`round.json` 带 `prediction` 四行且在腿之前写入；
`--frontier ablation` 仍字节相同（R2 的两条 pin 测试继续绿）。
负样本：把 `THEORIA_FRONTIER` 设成 `1`/`true`/`banana`/`GENERATED`/空串
必须**仍留在 ablation**（正向白名单，R2 已实现，本件不许放宽），并断言一条
默认腿的 `design()` 报告不长出任何新键——证据泄进旧路径正是这件事的坏法。

---

## 对账 2026-08-02（监控）· 活的一半已交付，验收的一半没有——本件不关

**活腿已经跑了，而且是在本件写着「不得开始」的情况下跑的。**
2026-08-01 所有者裁定（登记 #13「不管预算，全额推进」、#14「额度限制全部
放开」，`monitor/spec.py:521-525`）解除了本件的支出封锁；轮次以 **R2/R2b**
的名字发出，不叫 R3。裁决书在 `theoria-arm/runs/_rounds/R2b-VERDICT.md`：

| 预注册量 | 目标 | 实测 | 判 |
|---|---|---|---|
| 前沿宽度 | 2 → ≥3 | **6, 8, 9, 10** | 达成 |
| 脱靶率 | 90.4% → ≤40% | **22%**（27 中 6） | 达成 |
| 实现比特 > 0 | 56 中 0 → 至少半数 | **27 中 21（78%）** | 达成 |

含世界答案率 **9.6% → 78%**；反驳条件（宽度≥3 而脱靶仍 >70% 则回退）
**没有触发**。离线 replay 事前预测 43/52 ≈ 83%，活腿 g50t 实测 **83%**。
`--frontier generated` 留树。**本件问的问题得到了回答，答案是「值」。**

**但本件的验收没有被满足，而且缺的正是它最要紧的一条。**
逐字读两份轮记录：

```
_rounds/20260801T043743Z-R2/round.json    "prediction": null
_rounds/20260801T044640Z-R2b/round.json   "prediction": null
```

`round.json` 的 `prediction` 字段**两轮都是 null**。四行预测确实是事前写下的
（在 `runs/20260801T0900Z-R2-frontier-by-generation/` 的 README §4），
所以这不是一次事后编故事——**但轮记录本身不知道它们**，三个数字与它们的目标
是由人手工誊进 `R2b-VERDICT.md` 的。本件写下「在开跑之前写进 `round.json` 的
`prediction` 字段」，要的就是让机器持有那张事前的表；今天持有它的仍然是人。
下一轮如果没有人写裁决书，这一层保护就不存在。

**因此本件保持 open，范围收窄为一件事**：`round.py` 必须能在开跑前接收预测
并落进 `round.json.prediction`，且**回填 R2/R2b 两轮时必须拒绝**——事后补写
预测正是这个字段存在的理由的反面。原件的支出段落、R3 的命名、四行预测的
内容，全部由本节取代；`deps: A23` 已满足（A23 于 2026-08-02T12:07:20Z 交付）。

零花费。
