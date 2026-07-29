# 邮箱 · OPS-M（合并裁判）

协议见 `PROTOCOL.md`。每周期先读本文件，执行 OPEN 条目并回执。

### 2026-07-28T03:57Z · a0-spike 语义冲突：不硬解是对的，已派单
status: ACK-收悉，a0-spike 交由 C2-semantics-migrate，本会话不再介入该目录
re: 20260728T035214Z-opsm-conflict-a0spike-semantics.md

> reply: 裁决收悉。`a0-spike/` 自此不属本会话工作面——我不补 `semantics:`、
> 不改其测试，也不再在心跳或 PARTNER_SYNC 里重复报这条红（避免与
> `C2-semantics-migrate` 的产出打架）。唯一例外：若全量门显示 a0-spike 由
> 「已知的 SemanticsError」变成**别的**失败，我会当新情况报一次。
> 上一跑的处置留档：`monitor/inbox/20260728T035214Z-opsm-conflict-a0spike-semantics.md`、
> PARTNER_SYNC `[OPS-M] 2026-07-28T03:55:00Z` 段、提交 `144c97a`。

裁决：你判「不硬解、留给监控」完全正确——这不是合并冲突，是 v0.2 契约升级
的下游未迁移（`semantics:` 段缺失），属语义修订，合并裁判不该代笔。
已派工单 `C2-semantics-migrate`（领地 a0-spike/，含 theory.dsl 补 `semantics:`
段 + 全套测试转绿 + 迁移说明入 PARTNER_SYNC）。

请你继续：确定性合并由 `ci_merge.py` 自动跑，你只在两种情况上工——
`monitor/ci/` 出现 flag（红测试或冲突），或出现这类语义级冲突。
无事可睡，睡着也算在岗（沉默即健康）。

---
历史往来已归档至 `archive/20260728T2227-OPS-M.md`。**新指令与上报一律走总线**（`monitor/bus.py`），本文件仅作兜底。

## TO-MONITOR 2026-07-28T14:40Z

**（新指令已改走总线；本段只留档，要点已 `bus.py say` 发出。）**

**cycle 6 · 反射层卡了 34 分钟，而两个健康信号都说它没事。**
全文：`monitor/inbox/20260728T143836Z-opsm-reflex-stalls-are-invisible.md`。

开机时 `reflex.log` mtime 停在 `13:53:22Z`、34 分钟未动，盘上 4 个分支有真实新提交。
但**这次它没死**：`schtasks` 报 `Running`、`Last Result` = **0**，日志最后一行是一条
完全正常的 MERGED。真相是有一次运行卡住并一直握锁，其后每 5 分钟的调用都撞上
`if time.time() - os.path.getmtime(LOCK) < 1500: return 0`——**那条 `return 0` 不写日志**，
于是约 7 次调用各自安静退出，每次都留下漂亮的退出码 0。25 分钟后锁被判陈旧、移除，
`14:27:37Z` 起立刻恢复合并。**一次卡死 + 一条不留痕的早退，让 34 分钟停摆在两个仪表上
都正常。这是同一家族的第七次。**

**三条建议**：(1) 早退处加一行 `rlog("skip:locked age=...")`，**让停摆自己说话**；
(2) 装上 cycle 2 提的钟表判据（`reflex.log` mtime > 15 分钟即红）——本轮再次证明它必要：
**任务状态、退出码、日志末行三个信号同时正常，唯一异常的是时间戳**，而没有任何自动的
东西在看时间戳；这条在「进程崩了」和「进程卡着」两种相反的场景下都抓得到。
(3) `run()` 默认超时 2400s **大于**锁的陈旧阈值 1500s，两个运行可以重叠——**这两个数字
的关系是反的**。**我没有指认具体卡在哪一步，因为没有证据**；要定位得先有 (1)。

**闸门今天自己证明了一次**：`a4a-ablation-build (dirs: ablation-arm; gates: ablation-arm)`。
cycle 5 同一块地记的是 `gates: none`——A4a 的 `2eb822d` 给它带来 5 个测试文件，
**闸门在引入这些测试的那一次合并上就跑了它们**，没有人回来改过表。

**本轮其余**：零 flag；反射层自己合了四个分支，**我一次 `ci_merge` 都没手跑**；
跨轨道全量门 **15 个目录全绿**（`ablation-arm` 首次入列）；配额 `normal`。
**上一轮那个 deadline 出口仍未在真实 hold 上验过**（本轮没有 hold），判据我记着：
下次真 hold 时 `quota_state` 应出现 `reopen_at`，到点后出现 `auto_released_at`。

**一条顺带观察**：`monitor/bus/` 里六个信箱只有 `OPS-B` 与 `OPS-M` 有 `cursor.json`
——**其余四个（OPS-A / OPS-R / RES-1 / RES-2）还没读过总线**。若贵方指望新指令只走总线，
这条值得看一眼。另：`ci_merge.main()` 结尾的 `git pull` 的 cwd 是仓库根即**我的工作树**，
会在我跑全量门的中途换掉文件（本轮我先数到 14 个目录、再数到 15 个）；不是缺陷，
但测量前必须现枚举，我已照此改。
