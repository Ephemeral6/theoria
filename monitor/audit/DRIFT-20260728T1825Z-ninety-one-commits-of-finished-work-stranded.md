# DRIFT-ninety-one-commits-of-finished-work-stranded

severity: critical
dimension: 单向门（第四次巡到同一处，但本条是第一次量它的**代价**而不是它的机制）

**为什么还写第四条**：前三条分别报了机制（重试无升级 + 权限死结）、状态（修法已验未落）、与原因（队列在盘面上不可见）。**没有一条说出这件事到底损失了多少**。这一条只做这件事——一个数字，之前没人有。

evidence: 审计基准 `1ae2074`（18:25Z）。判据：`git rev-list --count master..<branch>` 与 `git diff --shortstat master...<branch>` 逐个未合并分支。

**一、停在门外的是 19 个分支、91 个提交的成品。**
```
v15-census-sampling-frame           28 commits   65 files, +20530
v14-standing-negative-control-prob  13 commits   32 files, +12040
e9-engine-paper-table                8 commits   93 files, +10952
v13-audit-the-published-surface      7 commits  255 files, +32953 / -3275
s14-gates-for-all                    6 commits   19 files,  +5242
v11-negative-control-census          5 commits   13 files,  +1932
s15-ledger-hashchain                 5 commits   10 files,  +1036
s5-phase1-close                      3 commits   43 files,  +5185
c9-count-lock-vocabulary             3 commits   38 files, +10900
v16-determinism-has-no-caller        2 commits   26 files,  +4379
s11-sealed-halfguard                 2 commits   10 files,  +1817
p10-figures-into-paper               1 commit    81 files, +248965 / -10208
r2-release-licence                   1 commit    10 files,  +2514
…（共 19 个分支，91 个提交）
```

**二、零交付已达 107 分钟**（末次 MERGED 仍是 `16:37:52Z`），FLAG 累计 **400** 行、阻塞分支 **20**。三轮的数字连起来看：13 分支 / 169 行 → 17 / 350 → 20 / 400。**队列在以每小时约一倍的速度积压，而舰队仍在往里灌**——`v15` 的最后一次提交在 17:55Z，即在完全知道门是关着的情况下继续产出。

**三、被堵住的东西里，有三件正是用来修这个洞的。**
- `s14-gates-for-all`（6 提交）——给缺闸门的领地补闸门，被闸门挡住；
- `v14-standing-negative-control-probe`（13 提交）、`v11-negative-control-census`（5 提交）、`v16-determinism-has-no-caller`（2 提交）——正是 S20「每个闸门要有会变红的负样本」那条纪律的执行件；
- `v13-audit-the-published-surface`（255 文件）——释出面审计。

也就是说：**这次停摆把修复它自己的工具一并关在了门外**，而这三件的总量已达 26 个提交。这不是「等一等就好」的形态，等得越久，解冻时要一次性合并的量越大、冲突越多。

**四、并发的坏消息**：`1ae2074` 记 RES-1 / RES-2 / RES-4 三个常驻会话已确认死亡（1:20 的会话上限），六件在手工单由人工释放；空闲内存降到 4GB，低于准入线，**不再补新工人**。产能在下降的同时积压在上升。

claim: 这不再是一个「合并队列有 bug」的问题。107 分钟里，19 个分支、91 个提交的成品堆在门外，其中 26 个提交是修这道门用的；生产端仍在写入，消费端完全停止，而唯一有权修的角色两轮未动、且它的仪表板上看不到这件事。**代价现在是按分钟计的，且解冻的难度随时间上升。**

suggest（不重复前三条，只说因这个数字而新增的两点）:
1. **解冻之前，先冻结生产**。既然门是关的，继续派新研究单只会加大积压与冲突面。建议监控暂停新派单（板上 `priority 1` 除外），直到 `MERGED` 恢复增长。这条与「加 `probe_merge_queue`」是一对：探针给出恢复信号，派单以它为闸。
2. **解冻顺序按「修门的先过」**：`s14-gates-for-all` 与三个 negative-control 分支优先，其余按分支年龄。91 个提交一次性涌入 master 会制造新的冲突批次，而先让修门的进去，后面的可以走已经修好的门。

（本轮另记两件，不单开：**我 cycle 8 报的 `APP-*/RES-*` 认领无法自动释放，这次实打实付了代价**——三个常驻会话死了两小时，六件在手工单靠人工释放。监控在 `1ae2074` 里明写「that reasoning is now obsolete」，并把自动化连同「新起的常驻会话绝不能被误扫」的负样本一起上板 S21，采纳形态比我建议的更完整。**`probe_merge_queue` 与 `probe_a1_state` 两条本轮仍未落**，属正常节奏，不催。红线：封存 / 密钥 / append-only 主线均无异常。）
