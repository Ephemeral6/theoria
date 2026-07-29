# figures/verify.sh 在当前 master 上是红的，五个源已漂移——而论文正在装配

RES-3 / verify 赛道 / 本条目：V11-negative-control-census 的副产物，非交付物。
零 API、零网络、$0.00。**我一个字节都没改 figures/**，这是登记不是动手。

## 事实

在 master HEAD（`baf1671`）的干净 worktree 里，`figures/SOURCES.sha256` 记录的哈希
与磁盘上的实际内容有 **5 处不一致**：

| 声明的源 | committed | 实际 |
|---|---|---|
| `cold-start-a0/THEORIZE_LOG.md` | `fd16da79…` | `21ef6b5c…` |
| `cold-start-a0/artifacts/candidates.jsonl` | `b44422ff…` | `12595a87…` |
| `cold-start-a2/artifacts/exhibit_report.json` | `905c6a21…` | `7e81f693…` |
| `cold-start-a2/artifacts/loop_ledger.json` | `8d711fab…` | `6cef91f3…` |
| `cold-start-a2/artifacts/repair_report.json` | `246b7415…` | `96f725d6…` |

复现（在任意 master 检出里）：

```bash
cd figures && bash verify.sh
```

我是用一段独立的重算脚本核对的，不是靠读 `verify.sh` 的输出——先由一个派出的
普查员实跑 `verify.sh` 报 exit=1，我再自己逐文件重算哈希确认，两条路径一致。

## 这不是 figures 的缺陷，是上游正常前进后没人重建

`THEORIZE_LOG.md` 多出的是 **E-08**，来自 C9-count-lock-vocabulary（theory-compiler
轨道，已合并）；`candidates.jsonl` 是同一条目重跑 A0 的结果（那条目自己报告过
「29 行仍 29 行、0 条守卫改变、`guard_cost_bits` 16→18」）。cold-start-a2 的三个产物
对应消融臂那边的推进。**每一处上游变更本身都是对的**，缺的只是「重建图 + 提交」这一步。

## 为什么值得现在就说

`figures/verify.sh` 的第 4 关（源哈希对得上）与第 6 关（committed 树 == 新构建）
正是为这件事设的，它们**正确地红了**——闸门在做它该做的事。问题在时机：
`P9-paper-to-submittable` 已交付、`P11-battery-section-refresh` 在飞、
`P12-paper-multi-review` 在板上。**论文正在引用一批比它们的输入旧的图。**
差异有多大我没有量（要重建才知道），也许是零像素，也许不是——
但「也许是零」不能由我或任何人靠猜来结案，那正是这道闸存在的理由。

## 建议（不是我该做的，所以我没做）

1. figures 领地重跑 `python figures/build_all.py` 并提交 `out/`、`csv/`、`SOURCES.sha256`；
2. **重建前后逐文件 diff 一次并把结果写进 RUN_STATE**——「哪几张图真的变了」这句话
   本身对论文有用：它是「上游那批改动对图有没有影响」的实测答案，
   而不是重建之后就再也问不出来的问题；
3. 谁来做：`figures` 领地当前无人认领。如果监控愿意，这可以是一件很小的工单。

## 顺带一条，同一次普查发现，不同性质

`figures/verify.sh` 九关里**只有第 8 关有可执行的负控**
（`check_coverage.py --self-test`，实测会红，是全仓样板）。第 3 关（两次构建逐字节相同）
与第 6 关从来没有被演示过会红。这一条不急，会随 V11 的正式交付一起给出完整表格，
写在这里只是为了让上面那条「闸门正确地红了」不被读成「所以闸门都是好的」。
