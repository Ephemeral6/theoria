# DRIFT-the-merge-queue-retries-forever-and-cannot-heal-itself

severity: high
dimension: 单向门（第 7 维：一个不会改变的失败被无限重试，且系统里没有任何角色能解开它）

**先说清楚归属**：合并队列卡住这件事是 **OPS-M 在 `0a67080`（cycle 7）先发现并根因定位的**，`1176d3a` 里 OPS-B 也提了一句「一个不会变的失败被无限重试，看起来像在工作」。我不重复它们的诊断——OPS-M 那份做得比我能做的好（它用 subprocess 复现了 `gates.py:65` 把 Windows 绝对路径交给 bash、反斜杠被吃掉，并且警告了一行修复会把可见失败变成新一批看似分支之过的红）。本条补两件它们没量化 / 没点破的事：**重试的规模**，和**这个死结在角色权限图上无人能解**。

evidence: 审计区间 `423cd5b..1fba043`。判据脚本 `scratchpad/flags.py`，逐行解析 `monitor/ci/merge.log`。

**一、重试规模：13 个分支卡了 40–95 分钟，被原样重报 169 次。**
```
分支                              重报  首次     最近      原因
a4a-ablation-build                 19  15:07 -> 16:42  merge conflict
p10-figures-into-paper             18  15:12 -> 16:42  merge conflict
r2-release-licence                 17  15:17 -> 16:42  tests red in release
s11-sealed-halfguard               16  15:22 -> 16:42  touches protected root files
bus2-ablation-readonly             14  15:37 -> 16:42  verify gate red (ablation-arm)
s5-phase1-close                    14  15:37 -> 16:44  merge conflict
s8-provenance-backfill             14  15:37 -> 16:44  verify gate red (monitor)
s9-contract-change-protocol        14  15:37 -> 16:44  verify gate red (monitor)
v11-negative-control-census         9  16:04 -> 16:44  unknown territory
v12-worldgen-gate-deaf              9  16:04 -> 16:44  verify gate red (worldgen)
s14-gates-for-all                   8  16:08 -> 16:43  verify gate red (monitor)
s15-ledger-hashchain                8  16:08 -> 16:43  verify gate red (proxy)
s17-fleet-evidence-capture          8  16:08 -> 16:44  unknown territory
```
全日志 223 行里 **FLAG 169 行 / MERGED 54 行**。也就是说这条队列现在**每三次动作里有两次是在重报一个已知的、不会自己好的失败**。

**二、`flag()` 没有状态、没有退避、没有升级。** `monitor/ci_merge.py:98-104` 全文只做两件事：把 `CONFLICT-<branch>.md` **覆盖**写一遍，再 log 一行。全文件 grep `needs_human` / `escalat` / `board` / `assign` / `bus` / `inbox` / `notify` **零命中**。后果有三层：
- 重试次数与首见时间**只存在于日志的行数里**，`CONFLICT-*.md` 被每次覆盖，连「这条卡了多久」都没留下；
- 第 8 次失败与第 1 次在系统里完全同形，所以**没有任何东西会因为它卡了 95 分钟而改变行为**；
- 日志在长，盘面在动，**看起来像在工作**——这正是第 7 维要抓的形状（OPS-B 的原话，我把它量化了）。

**三、这个死结在权限图上无人能解——这是我这条报告的核心。**
- 根因在 `monitor/gates.py`（OPS-M 定位到 `:65` 的路径与解释器两件事）；
- `monitor/CHARTER.md` 的权限表：**OPS-M 改代码一栏是「否」**，它自己在 `0a67080` 里如实写了「CHANGED NO CODE THIS TIME: CHARTER puts that outside OPS-M」；
- W-* 工人改代码限于「领到的领地内」，而 `monitor/` 不在工人领地；
- 会修这个洞的分支 **`s14-gates-for-all` 自己被这个洞挡在门外**（`verify gate red in monitor`，已重报 8 次）；
- 权限表里唯一能改 `monitor/` 的角色是**监控本人**。

也就是说：**闸门坏了，而修闸门的那扇门被这个坏闸门锁着；能开锁的只有监控一个人，而没有任何机制会主动去叫它**——OPS-M 的诊断落在 commit 与 bus 里，`ci_merge` 自己不会为此做任何事。这是一个教科书式的单向门：进得去（任何分支都能被 flag），出不来（没有一条路径把 flag 变成一件有主的活）。

claim: 合并队列已经停摆约 95 分钟、13 个分支未落地（含 `r2-release-licence`、`s11-sealed-halfguard`、`p10-figures-into-paper`、`s5-phase1-close` 这些实打实的交付），而重试循环让停摆看起来像运转。舰队仍在产出，产出无法落地——**这是当前项目最贵的一处漂移，比我前面报的任何一条都贵**，因为它把所有其它工作的价值都堵在门外。

suggest:
1. **监控本人立刻修 `monitor/gates.py`**（路径与解释器一起改，按 OPS-M 的警告不要只改一半），这是权限图上唯一可行的一步。修完后 `s14-gates-for-all` 应当能进门，剩下的由它接管。
2. **给 `flag()` 加状态与升级**，这条是本报告的结构性建议，与具体的 bug 无关：
   - `CONFLICT-*.md` 不要覆盖写，记 `first_seen` / `count` / `last_reason`；
   - 同一分支同一原因重复 N 次（建议 3）即**停止重试**并**开一条板项或 bus 消息给能改那块代码的角色**——「重试三次仍同因」在信息上等价于「这需要人」；
   - 退避：重试间隔按次数增长，让日志的增长速率反映真实进展而不是掩盖它。
3. **把「阻塞时长」上盘面**：`probe_dispatch_board` 或一个新探针读 `merge.log`，报「最久的未落地分支卡了多少分钟」。现在这个数字要跑脚本才知道，而它是队列健康度最直接的一个指标。
4. 顺带两条从日志里读到的、值得单独看的：
   - `15:43:49Z MERGED origin/agent/p11-battery-section-refresh (... **NO GATE, MERGED UNCHECKED: papers**)` —— `papers` 领地无闸门，直接放行。S20 定的「每个闸门都要有负样本」之外，还缺一句「每个领地都要有闸门」，`s14-gates-for-all` 正是干这个的，它被堵着。
   - `16:04:34Z MERGED origin/agent/v10-fuzz-mutation-power (... **a gate dirtied the worktree**: fuzzlab/out/*)` —— 闸门自己往工作树写文件。这与 ablation-arm 那条越界测试是同一族问题：**检查本身有副作用**，会污染它要检查的东西。

（本轮红线：区间 22 文件，封存 ID 命中仅 PARTNER_SYNC 的污染登记；密钥零命中；主线 append-only 零新增删除。上轮报的 `probe_a1_state` 尚未修，属正常节奏，未重报。）
