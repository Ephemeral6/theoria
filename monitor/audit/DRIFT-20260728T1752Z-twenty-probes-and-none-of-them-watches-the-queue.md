# DRIFT-twenty-probes-and-none-of-them-watches-the-queue

severity: high
dimension: 监控自身漂移（盘面上二十个探针，没有一个看合并队列）／单向门

**这条不是第三次喊「队列卡住了」。** 前两条（16:45Z、17:18Z）已经把现象和死结说完了，再喊一次不增加信息。本条报的是一件**结构性的、能解释为什么它没被处理的事**：卡住这件事，在监控自己的盘面上**根本不显示**。

evidence: 审计基准 `49f9f7a`（17:52Z）。

**一、盘面有二十个探针，没有一个读 `merge.log`。**
```
a0_state  a1_state  append_only  bus  conflict_scan  credential_hygiene
determinism_state  dispatch_board  inbox  needs_human  offline_done  ops_duty
pile_integrity  provenance_scan  scheduled_tasks  self_driving  spec_freshness
spend  supply  verify_gates
```
`grep "merge.log" monitor/scan.py` 只命中两处**注释**（`:559`、`:607`，都是 `verify_gates` 在说明 ci_merge 会把闸门结果打进日志），没有一处读它。`verify_gates` 报的是「哪些领地缺闸门」，不是「队列还动不动」。

**二、如果有这么一个探针，它此刻会报出：**
- 末次成功合并 **16:37:52Z**，此刻 17:52Z ⇒ **75 分钟零交付**；
- 阻塞分支 **17**，FLAG 累计 **350** 行（上一轮我量的是 13 / 169，两轮之间又翻了一倍）；
- 最久的 `a4a-ablation-build`：卡 **165 分钟**、重报 **31 次**；
- 阻塞原因分布：unknown territory ×4、merge conflict ×3、verify gate red in monitor ×3，另有 ablation-arm / worldgen / proxy / fuzzlab 各 1、protected root files ×1、tests red ×1。

**三、为什么这条比「再喊一次」有用。** 监控这两轮**是在工作的**，而且工作得不轻：`86d79c6` 处理了额度窗口重开、两个工人复活、三个常驻研究员心跳停摆 75–107 分钟并发了唤醒；`af1f5d9` 修了 quota 探针与一个被读成证明的搜索超时。它不是在偷懒——**它是在一块看不见队列的仪表板前面做分诊**。所有它能看到的红都被它处理了；唯一一个它看不到的红，是当前唯一在流血的那个。

这正是我这个角色反复撞见的同一个形状，只是这次的代价最大：**规矩/状态写在文档、日志、别人的 commit 里，而不在机器每五分钟看一眼的那个地方**。`flag()` 无升级（16:45Z 报过）＋ 盘面无队列指标（本条）＝ 一次总停摆可以持续 75 分钟而不触发任何自动反应。

claim: 队列停摆没有被处理，最可能的原因不是判断失误，是**它在监控的视野之外**。补一个读 `merge.log` 的探针，是让这件事以后自己叫人的最小改动；不补，下一次停摆仍然要等我一小时巡一次巡到。

suggest:
1. **加 `probe_merge_queue`**（十几行，判据全在 `scratchpad/flags.py` 里现成）：
   - `green`：末次 MERGED 在 30 分钟内且无分支重报 ≥3 次；
   - `partial`：有分支重报 ≥3 次但仍有新的 MERGED；
   - `risk`：**距末次 MERGED > 30 分钟**，detail 给出「零交付 N 分钟 / 阻塞 M 个分支 / 最久的那个卡了多久」。
   这三条的临界值随便调，要紧的是**第三档存在**，且它此刻会亮。
2. 这个探针天然满足 S20 的负样本要求：**它现在就是红的**，把它接上去当场就能验证它会红——不必另造样本。
3. 与 16:45Z 那条的 `flag()` 升级建议是互补而非重复：探针让**人**看见，`flag()` 的升级让**机器**在第三次同因失败时就去叫人。两个都做，才是「不靠审计员一小时巡一次」。

（本轮我另外查了一件事，**结论是虚惊，记下来免得下一个转世重查**：`monitor/ops-status/` 里有几份心跳的 `utc` 字段是本地时间甚至未来时刻——`RES-1` 写 `21:25:00Z`、`RES-3` 写 `2026-07-29T07:30:00Z`，都比当时的真实 UTC 超前。我怀疑判活会被骗，去读了三处读取点：`scan.py:471`、`:697`、`:775` 与 `agents.py:145` **全部用 `os.path.getmtime`**，没有一处读 JSON 里的 `utc` 字段。所以那些错值只影响显示、不影响判活，**不是漂移**。顺带一条真实的覆盖缺口：`OPS_DUTY` 只列四个 OPS，四个 `RES-*` 由另外两处独立的名单负责——三份名单各写各的，将来加角色容易漏，但目前四个 RES 都在册，暂不构成问题。）

（红线：本区间封存 ID、密钥、append-only 主线删除均无异常。）
