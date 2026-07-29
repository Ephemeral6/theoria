# DRIFT-app-and-res-claims-are-a-one-way-door

severity: medium
dimension: 单向门（第 7 维，监控 13:38Z 新增，本轮首次按它扫全仓）

evidence: 审计区间 `9e61399..a7afa60`（25 个提交、103 文件）。

**门在哪：`monitor/board.py` 的 `cmd_sweep` 自己把出口关上了一半。** docstring 逐字：

> 「一次性工人被额度或崩溃打断后，`claimed/` 里的认领永远挂着：板以为有人在做，领地被锁，新工人领不到活。判据保守——只清 `W-*` 前缀（一次性工人）且其计划任务已不在运行的；**App/常驻会话（`APP-*`/`RES-*`）一律不动，它们的存活从任务表看不出来。**」

于是 `APP-*` / `RES-*` 的认领只剩**一条**出口：当事会话自己调 `board.py done` 或 `release`。当事会话若已经结束、换了话题、或干脆没意识到自己还占着，**没有任何自动路径能把它收回来**。

**按新维度的两句判据逐条问：**

| 问 | 答 |
|---|---|
| 谁把这个状态退出来？ | 只有认领者本人（`cmd_done` / `cmd_release`，两者都先校验 `worker` 匹配，别人调用得到「not claimed by you」） |
| 那条路径今天真的被调用过吗？ | `W-*` 的：调用过，`board.log` 有 8 条 SWEEP（13:46:39Z 一次释放 5 件）。`APP-*`/`RES-*` 的自动路径：**从来没有，因为不存在** |

**它现在正卡着，不是假想：**
- `monitor/board/claimed/V3-battery-discrimination.APP-V3.md`，认领于 `2026-07-28 14:21:26 +0800`（06:21Z）。
- 而 `origin/agent/v3-battery-discrimination` **已于 `174c5a6`（15:55 +0800 ＝ 07:55Z）合并进 master**。
- 本轮基准时刻 13:56Z——**活干完并合并了约 6 小时，认领还挂着**，领地对其他人锁着。
- 上一轮 P9 撞的是同一扇门的另一次：`claimed/P7-paper-section7.APP-P7` 占着 `papers/`，P9 因此报了「`papers` 被两次认领」。那一件后来被人工清掉了——**人工，不是机制**。

**出口其实是有材料的，只是没接上：**
- `RES-*`：`monitor/ops-status/RES-1.json` / `RES-2.json` **在树上**，格式与运维心跳一致，而 `probe_ops_duty` 已经在按「陈旧多少分钟」判活。sweep 排除它们的理由（「存活从任务表看不出来」）对 schtasks 成立，**对心跳文件不成立**——判活所需的东西监控自己已经造好了。
- `APP-*`：`ops-status/` 下**只有** `OPS-A/B/M/R` 与 `RES-1/2` 六个，**没有任何 `APP-*.json`**。也就是说 APP 会话连一个可读的存活信号都没有，这一支是真正意义上的无法开启。

claim: `claimed/` 是一个只有当事人能开的门，而当事人可能已经不在了。`W-*` 那一半已经装了外部开关并且真的在用；`APP-*`/`RES-*` 那一半被显式排除，理由在写的时候成立、在心跳文件落地之后就不成立了。代价是领地被死锁——V3 这一件已经锁了六小时，而它的活早就在 master 上。

suggest:
1. **`RES-*` 立刻接心跳**：`cmd_sweep` 对 `RES-*` 改用 `monitor/ops-status/<ID>.json` 判活，超过该角色的 stale 阈值即释放（阈值 `OPS_DUTY` 里已有现成口径）。这一条不需要新基础设施，只是把两件已存在的东西连起来。
2. **`APP-*` 要么给心跳、要么别让它领**。App 会话若要领板上的活，就该和运维会话一样每周期写一行 `ops-status/APP-<id>.json`；做不到就限制 `APP-*` 只能领无领地锁的条目。现在这一支既能上锁又无法判活，是三种前缀里最危险的一种。
3. **补一个会红的负样本**（这正是新维度的第二句判据）：给 `cmd_sweep` 写一条测试——造一个心跳已陈旧的 `RES-*` 认领，断言 sweep 会释放它。没有这条测试，第 1 条改完之后仍然是一个「不可能变红的检查」。
4. 顺手把 `V3-battery-discrimination.APP-V3` 移进 `done/`（它的分支 `174c5a6` 已合并），并复核 `A4a-ablation-build.RES-1`、`P5-release.RES-2` 两件是否也已完成。

**本轮扫全仓的其余结果——两处我原以为是门、查完不是，一并记下，免得下一个转世重扫：**
- `proxy/spend_gate.py` 的 fail-closed 路径**有出口且是显式的**：未定价调用会 trip 闸门，但作者留了 `SpendGate.price_unpriced()` 作为「明确的、被记录的动作」而不是一个开关（`:855-880` 的注释把「一个能因为价目表少一行就砖掉整个项目的闸门不是 fail-closed，是穿着 fail-closed 外衣的单点故障」写得比我能写的清楚）。
- `proxy/runner.py:174-186` 的头寸释放用 `finally` 而非happy-path 释放，注释记着对抗测试数出「43 次崩溃的 run 把共享池占满整个 TTL」——**这正是一扇被发现并装上出口的门**，可以当作这一维的正面范例。
- 另一个正面范例在 `baseline-arms/tests/test_transport.py:272-280`：封存护栏的测试对两个封存 id 断言 `pytest.raises(SealedGameError)`，**并带一行开发堆的负控制**（`api.assert_playable("ar25-0c556536")`）。这就是第 7 维第二句判据要的形状——检查有一个会让它变红的负样本。
