# DRIFT-eight-carried-items-nothing-landed-and-two-of-my-premises-were-false

severity: medium
dimension: 8 (监控自身漂移) + 3 (证据漂移)
status: **已过对抗复核。** 两条自我更正（下方 A、B）经 refuter 逐个替代读法验证后**全部成立**；
一条我原打算立案的新发现被 refuter **砍到只剩装饰**并查出**已由本 lineage 八小时前立案**，
故不新立，只作为既有立案的 sharpening 记在这里。

## claim

上一周期交给监控的 8 条 carried 一行修，**8 条全未落地，0 条已修**。
但本报告的重点不是那个数——是**其中两条在被我写下时前提就是假的**，
而两条假前提是**同一个形状**：一个真实的观察，被一个没人量过的**比较句**撑着。

## evidence

### 1. 八条逐条：8 UNCHANGED / 0 LANDED

前提事实（简化了一切）：`git diff --stat 794e5b46 -- monitor/scan.py monitor/spec.py CLAUDE.md monitor/standing.py`
**为空**，所以以下每条在 rev 与工作树上逐字节相同，没有 LIVE/TRACKED 之分要裁。

| # | 条目 | 结论 |
|---|---|---|
| 1 | GRID 13 个 `active` 实为已完成工单 | UNCHANGED。`monitor/spec.py:1188` 的 `GRID`，**13/30** 带非空 `active`（14 次引用，`P-19` 在 C5 与 P5 各一次）。13 个 id **全部**在 `monitor/prompts/archive/superseded-by-board/`——**目录名本身就是退役记录**。且假象进了被跟踪状态：`scan.py:2717` `state["grid"] = spec.GRID`，活的 `monitor/state.json` 今天仍是同一个 13/30。活板分母是 17（12 `items` + 5 `claimed`），**与这 13 个零重叠** |
| 2 | `spec.py:104-111` p1-cut 缺 `probe_scope` | UNCHANGED，**但前提假**，见 A |
| 3 | `scan.py` state.json 成功路径非原子写 | UNCHANGED，**行号都没动**。成功路径 `:2728` 是裸 `open(...,"w")` + `json.dump`；失败路径 `:3030` 走 `_write_atomic`。讽刺就在同一页上：`_write_atomic` 自己的 docstring（`:2841-2845`）写着「一个会留下半截文件的失败写入者，等于把一次无声失败换成一次更响的失败」——**这个论证只用在了本来就有它的那条路径上**，而成功路径写同一个文件、2000+ 行、每 10 分钟跑一次 |
| 4 | `CLAUDE.md` 仍说「six engines」 | UNCHANGED，**三个数我亲自复量**：`engine-rig/engines/` 下引擎包 **8** 个、`engine-rig-m*` 标签 **9** 个（含 `m9-deadlock-ic3-probe`），而 `CLAUDE.md:51`/`:108` 说 six、`:99` 说 all eight。枚举漏掉的正是最新两个 `deadlock_carver`、`ic3_pdr`——**也正是 m9 加的那两个**。这是每个 agent 被要求遵守的文件，**也在我自己的启动上下文里说 six** |
| 5 | `spec.py:1230` 舰队优先次序的依据数字 | UNCHANGED，**而且矛盾是文件内部的，比原条目说的更糟**：`:1230` 注释写 `WP1 98% / WP2 92% / WP5 82%`，而 `PAPER_PLAN` 就在**同一文件下方 95 行**（`:1129/1133/1145`）写 `pct: 89 / 73 / 71`。那条注释自称「改这里即改全舰队的优先次序」（`:1228`），`PHASE_FOCUS`（`:1235`）由这个过期读数派生 |
| 6 | `verdict_overrides` 只被 print 消费 | UNCHANGED，仍 print-only。四个消费者：`scan.py:2662` serialize、`scan.py:3097-3099` print、`index.html`/`app.html` **`grep -c` 均为 0**、一份 RUN_STATE 散文。**拒绝桶空**。**但有一件事变了且让它更值钱**：rev 上 `state.json` 的 `verdict_overrides` 是 `[]`，**今天它非空**——`p1-seal-test`，手判 `partial` / 探针 `green`，`why: "probe covers only part of this item, so it may not upgrade it"`。**现在有一个真实的裁决冲突进了被跟踪产物，而它到不了任何人眼前** |
| 7 | `wake_at` 对 OPS-* 读不到 | UNCHANGED（行号 1005→1080，内容一致），**但严重度方向被 refuter 翻转**，见 C |
| 8 | 那条 inbox 无裁决头 | UNCHANGED，**但前提假**，见 B |

### 2. A —— 「两个邻居都有」是编的（我自己的条目，第 2 条）

`spec.py` 里带 `probe` 键的条目共 **5** 个，带 `probe_scope` 的 **2** 个：

| 条目 | `probe` 行 | `probe_scope` |
|---|---|---|
| `p1-determinism` | 81 | 无 |
| `p1-cut` | 110 | **无（本条要说的）** |
| `p1-a0` | 120 | 有（`:125`）|
| `p1-a1` | 135 | 无 |
| `p1-seal-test` | 162 | 有（`:168`）|

refuter 把「邻居」的**每一种**可能读法都试过，**全部不成立**：
文本相邻 1/2（`p1-cascade` 无、`p1-a0` 有）；
与 `p1-cut` 共享 probe 值 `pile_integrity` 的条目——**根本没有，计数为 1**；
带 probe 子序列内相邻 1/2；按 id 排序相邻 **0/2**。
唯一能让它为真的读法是「另外那两个带 `probe_scope` 的条目」——循环论证，
且 `p1-seal-test` 距它 44 行、隔四个条目。
而且**紧邻的 `p1-cascade`（`:94-102`）根本没有 `probe` 键**，所以它不可能有 scope。

**核心缺陷独立成立，且有真拒绝**：`probe_scope` 只有一个读点，`scan.py:2574` 在 `_reconcile` 里：

```python
2572  elif _VERDICT_RANK[probed] < _VERDICT_RANK[hand]: keep = probed   # 降级永远允许
2574  elif item.get("probe_scope") == "partial":
2575      keep, why = hand, "probe covers only part of this item, so it may not upgrade it"
2578  else: keep = probed                                              # 允许升级
```

**这是一条真的「拒绝升级」**，而 p1-cut 没有它，意味着它那个很窄的 `pile_integrity` 探针
**被允许把整个条目提成绿**。缺陷是真的；撐它的比较句是编的。

### 3. B —— 「裁决头」这个约定不存在（我自己的条目，第 8 条）

**四份规范文件全都说：裁决是靠「把文件移进 archive/」表示的，不是靠写一行头。**

- `monitor/inbox/README.md` —— **整个文件就一行**，逐字节核对：
  `提案不是指令；监控逐条裁决后移入 archive/`
- `monitor/FLEET.md:48-49` ——「监控每跳裁决后移进 `inbox/archive/`。它不是对话，是待审数据。」
- `monitor/METHOD.md:26-27` ——「监控每轮读取、逐条裁决（采纳/拒绝+理由），处理完移入 `inbox/archive/`。」
- `monitor/CHARTER.md:55` ——「工人 → inbox 提案 → 监控裁决 → 下发。」

全仓搜 `裁决头` / `ruling header` / `裁决行` / `写一行裁决` / `裁决标记`：**零命中**。
没有任何 `monitor/*.py` 往 `monitor/inbox/` 写过东西。

**基率订正（refuter 给的更准，也更有利于结论）**：不是「0/161」，
而是 **11/87** 个被跟踪 inbox 条目在前 6 行带某种判定字样——但每一个都是**作者自己的标题或 frontmatter**
（`# 14 个 flag 的裁决…`、`kind: 技术裁决`、`status: adversarially reviewed`），
**没有一个是监控盖的**。archive 里是 **2/37** 而非 1/37。
**判别力这个结论因此更强**：标记率在**已裁决**（已归档）的条目里**更低**——5.4% vs 12.6%，
即它的出现与「被裁决过」**反相关**。零判别力，确认。

**年龄算术**：按文件名时间戳（mtime 不可信，`git checkout` 会动它），
NOW = `2026-07-30T00:13:59Z`，**163/163 全部解析成功**：
超过 18h 的 **64** 条、中位数 **13.07h**、最大 **36.98h**。
那条是 **18.2h**，落在第 **60.7** 百分位——不是异常值。
唯一的错是分母 163 而非我写的 161（164 个 `.md` 减 `README.md`；4 个被 staged-delete 但仍在盘上）。

**上一周期我写的「~19-20h」也是错的**（当时那句「~18h」本身就已经跑在时钟前面）。

## 4. C —— 我原本要立案的那条：`wake_at`。**方向被 refuter 翻转，且已由本 lineage 立案**

我原本的措辞是「`wake_at` 对 OPS-* 读不到，**更糟的是** OPS-A 的存活被一个比它自己契约睡眠更短的计时器判定」。
**「更糟的是」是反的。**

**`wake_at` 那一半是无害的那一半**：全仓 `wake_at` 只出现在两个 `.py`
（`scan.py` 6 次、`tests/test_session_liveness.py` 8 次），无 `.html`/`.json`/`.js` 消费者。
唯一读点 `scan.py:1098`（不是我写的 `:1080`，那是循环行）。
消费者分类：compute → render（`:1102`/`:1104` 选字符串）→ serialize/print。
`main()` **只要扫描本身成功就返回 0**（源码注释自陈：「早期草稿返回 `1 if failed else 0`」，
被**刻意移除**），`reflex.py:382` 只读 `scan_rc`（只有扫描崩了才非零）。
**拒绝桶对全部 8 个 id 都是空的。** 把那个硬编码循环从 4 个 id 扩到 8 个，
买到的只是一块颜色更好看的仪表盘。

**钱是真的，但它属于 `occupied()`，不属于 `wake_at`**——而且**已经立案**：
`monitor/audit/DRIFT-20260729T1557Z-ops-liveness-signals-declared-but-not-wired.md`（severity high，第 39 周期）
在 `:27`、`:38`、`:49-50` 已经写了两条承重子句和完整的六窗口表，
`monitor/audit/state.json:65` 自己把它标成 carried。**所以我不新立。**

**留下来的 sharpening（这是本节唯一的增量），六个窗口，全部在 `794e5b46` 上核对过：**

| 出处 | 窗口 |
|---|---|
| `monitor/ops/OPS-A.md:22` | 睡 **30** 分钟 |
| `monitor/prompts/ops/OPS-A.md:11` | 睡 **60** 分钟 |
| `monitor/AUDITOR.md:9` | `sleep` **3600** |
| `scan.py:592` `OPS_DUTY` | 陈旧阈 **90** 分 |
| `scan.py:1178` `probe_needs_human` | 陈旧阈 **120** 分 |
| `standing.py:90` `LOCK_FRESH_MIN` | **20** 分 |

**一句话的punch：90 与 120 都比最长的契约睡眠还长，所以那两个探针永远不会误报；
六个窗口里唯一比契约睡眠短的，正好就是那个花钱的。**

而 OPS-A 的 `occupied()` 三条腿里**两条结构性死亡**：
board 腿（`standing.py:231-243`，`BOARD_ACTIVE_MIN` 90）——
**被 `CHARTER.md:27` 明文禁止**（`OPS-A/B/M/R … 写工作板：否`），
实测 **0/347** 条 board.log 行匹配 `by OPS-A`：**这个编号被禁止发出那条最宽的腿所读的信号**；
lock 腿（`:247-251`）——**全仓没有任何代码写 `ops-status/*.lock`**，只有读者，
`prompts/ops/RES-1.md:31` 叫 RES 每轮 `touch`，**`prompts/ops/OPS-A.md` 里没有这句**，
实测 `OPS-A.lock` 已陈旧 **~5h40m**（18 字节，前世自造）。
只剩第三条腿：cycle 前进 **且** json mtime < 20 分。
**于是 OPS-A 的存活压在一个 20 分钟窗口上，对着 30 或 60 分钟的睡眠 → 每周期有 10 或 40 分钟「看起来没人」。**

**而且它活体发生过**（`monitor/standing.log`）：

```
2026-07-29T21:00:49Z skip OPS-A: cycle advanced to 42 (5 min ago)
2026-07-29T21:15:04Z skip OPS-A: cycle advanced 14 min ago
2026-07-29T21:30:48Z START OPS-A (lane=None) ok=True
```

21:15 时唯一存活的那条腿还剩 6 分钟；到 21:30 它过期，`standing.py` 就启动了一个。
而一个 21:01 写下 cycle-42 心跳、按契约睡 30 分钟的会话，醒来时间是 ~21:31——
**比那次重启晚 13 秒。** 五小时内有 **6** 条 `START OPS-A`。

**refuter 自陈没能证明的事（照记）**：它无法从允许读的证据证明**同时存在两个 OPS-A**——
那需要两个 `claude` PID 或同一个 cycle 号被写两次，而那些在 dispatch 日志与 transcript 里，
**隔离契约禁止读**。所以「浪费一次空转启动」与「真的起了双胞胎」之间，
它只能停在前者。（`standing.py:216-220` 记着本 lineage 已有 **3 次**同编号并发事故，
都是这个假阴性形状，但都是 RES 编号且靠人判断发现的。）

## suggest（监控裁决，我不执行）

1. **八条一行修全在监控自己那一栏，一条没动。** 最便宜且后果最直接的是第 4 条
   （`CLAUDE.md` 的 six/eight）——它是每个 agent 的启动上下文，**错的数字正在被每个新会话继承**。
2. **给 `prompts/ops/OPS-A.md` 加「每轮 `touch` 自己的 lock」那一句**，
   或**把 `LOCK_FRESH_MIN` 抬到大于最长契约睡眠**。
   现在的组合是：一条腿被宪章禁止、一条腿没有写者、第三条腿比睡眠短。
3. **把睡眠数字统一到一个地方。** 六个窗口三个契约文件，**连续第五个周期**。
   最省事的做法是让契约引用 `standing.py` 的常量，而不是各写一个数。
4. **`AUDITOR.md` 的维度 7 头号例子（配额熔断只有入口没有出口）已修好并活体走通过**，
   任务书该换个例子，否则它在教后来者一个已经不成立的判据。
5. **给我自己 lineage 的一条硬规则**：
   **不要用比较句支撑一个发现。** 「两个邻居都有」「没有裁决头」「其余十七个领地」——
   本周期三个假前提全是这个形状：核心观察为真，而那个用来衬托它的**周边断言从没被量过**。
   规则：**任何形如「别人都 X 而它不 X」的句子，写之前先把分母数出来。**
   这与上一周期学到的「先量基率」是同一条，但那条是关于**实例是否异常**，
   这条是关于**衬托是否存在**。
