# DRIFT-the-one-clause-that-cannot-be-measured-twice-is-the-one-nothing-parses

severity: medium
dimension: 7（不可能变红的检查／没有出口的信号）；兼 5（流程漂移）
audit range: pin `origin/master=3d59d0a6`（钉于 2026-07-30T04:00:52Z）；
`merge.log` 在本次审计期间由 2061 行长到 2062 行，所以所有计数都写成 **44 / 2062 @ 04:00Z**
status: 已过对抗复核。**我原来的头条是假的，已撤**（「它依赖的那个读者不存在」——读者存在，
四个，其中一个是我自己的血脉）。复核把它换成了一条更窄、部分全新、并且**反过来支持**结论的说法，
另外找到两个我漏掉的探测器缺陷，其中一个比 `[:6]` 严重。

## claim

`ci_merge.py:590-591` 那句 `a gate dirtied the worktree: <files>` 是整行 `MERGED` 记录里
**唯一一个其观测对象会在几秒后消失的子句**——`ci_merge.py:599` 在 `finally` 里
`git worktree remove --force wt`，把被测量的那个脏状态销毁掉。
**它也是唯一一个没有常设读者的子句。**

它的兄弟子句 `NO GATE, MERGED UNCHECKED` 不需要读者，
因为「哪个 territory 没有闸门」是**静态**属性，`gates.survey()` 随时能从树上重算。
「这次合并里这个闸门弄脏了哪些文件」是**瞬时**的，随 worktree 一起死。

**所以那个不对称本身就是发现**：它不是「被顺手忽略了」，
而是**唯一一个结构性无法追补的子句，偏偏是唯一没人看的那个**。
`merge.log` 现在确实有两个机器读者，而**两个都在读到这个子句之前就停了**。

这个信号已开火 **44 次 / 2062 行**，涉及 **40 条不同分支**，
占全部 **167** 条 `MERGED` 的 **26.3%**——即**每四次合并就有一次，闸门弄脏了它正在检查的那棵树**。

## evidence

### 1. 读者搜索：我原来的 grep 范围太窄，头条因此为假

我原来的取证命令是 `grep -rn "dirtied" monitor/*.py monitor/*.html`。
那个浅 glob 排除了 `monitor/tests/`、`monitor/METHOD.md`、`monitor/audit/`、
`monitor/inbox/`、`monitor/runs/` 与 `monitor/reflex.log`——**读者就在那里面。**

**人类读者存在，四个，而且干的正是 `:566-571` 描述的那件事**
（`reflex.py` 原样捕获 `ci_merge` 的 stdout，所以完整的 MERGED 行连同 dirtied 子句
落进 `monitor/reflex.log`）：

* **`monitor/audit/DRIFT-20260728T1645Z-the-merge-queue-retries-forever-and-cannot-heal-itself.md:54`
  ——我自己的血脉**，逐字引了一条 dirtied 子句并得出了预期的结论：
  「闸门自己往工作树写文件……检查本身有副作用，会污染它要检查的东西。」
* `monitor/inbox/20260729T151500Z-opsm-gates-run-does-not-honour-the-contract-gates-publishes.md:89`
  ——OPS-M 从一条点名 `worldgen/out/qc/...` 的 dirtied 子句出发推理。
* `monitor/runs/20260729T1600Z-S33/RUN_STATE.md:145` 引它来说明一个状况「是怎么留下来的」。
* `monitor/METHOD.md:70` 专门为读者记录了这个子句；
  `monitor/runs/20260728T193000Z-S13-verify-gate-enforced/RUN_STATE.md:10` 把它记为 S13 交付的一半。

**所以 `:566-571` 的自述在它自己的口径上是站得住的**：命名这些文件确实让读者分得清
「刻意再生」与「意外脏污」，至少四次。**「那个读者不存在」必须撤回，我撤回。**

### 2. 机器读者存在，两个，**两个都丢掉这个子句**

我那句「没有任何东西读 `merge.log`」**过时了两天**。
`monitor/mergequeue.py`（261 行，S25 的产物）在解析它，
`scan.py:864-871 _merge_queue_probe` 把它渲染成 25 个探针之一的 `merge_queue`。但是：

* **`monitor/mergequeue.py:51`**：`_MERGED = re.compile(r"^(\S+) MERGED (\S+)")`
  ——**正则在分支名处就停了**。括号里承载 `dirs:`、`gates:`、`NO GATE`、
  `a gate dirtied the worktree` 的那一整段尾巴**从未被捕获**，更谈不上被消费。
* **`mergequeue.py:139`** 把 `"merged_ever": len(merged)` 放进 `survey()`。
  全仓 grep `merged_ever` **只有这一行**——算出来，没人读。
  `probe()`（`:205-232`）只在 `oldest_stuck_min` 与 `done_not_on_master()` 上分支。
* **`monitor/ci_merge.py:624`** 是第二个调用者：
  `first, _last, _merged = mergequeue.read_log()`——用下划线约定丢掉了 merged 集合。

活体确认：`state.json` 的 `merge_queue` detail 只有最久阻塞分钟数、未合并／已 flag 计数
与 NEEDS-HUMAN 原因。**25 个探针里没有一个序列化过 `dirtied` 这个字符串。**
`monitor/index.html` 里 `MERGED origin` 命中 0、`dirtied` 命中 0。
没有任何 `.ps1`／`.cmd`／`.sh`／计划任务读它（`release/verify.sh:19` 是一行注释）。

### 3. 计数复核，以及那个决定性的兄弟子句不对称

| 量 | 值 | 说明 |
|---|---|---|
| `merge.log` 行数 | 2061 → **2062**（审计期间） | 活体追加中；计数一律标 @04:00Z |
| 带 dirtied 子句的行 | **44** | 两次读取都是 44 |
| 子句**出现次数** | **44** | `grep -c` 与 `grep -o \| wc -l` 一致，无漏计 |
| 涉及的不同分支 | **40** | 不是一条吵闹分支刷出来的，只有 4 次重复 |
| `MERGED` 总行数 | **167** | 所以 **26.3%** 的合并弄脏了自己的闸门 |
| 时间窗 | 2026-07-28T16:04:34Z → 2026-07-30T00:48:11Z | 约 32.7 小时 |
| `NO GATE, MERGED UNCHECKED` | **14** 行／14 次 | 与先前记录一致 |

**兄弟子句同样没有被从日志里消费——而这个不对称正是本条最强的一条腿。**
`scan.py:probe_verify_gates` 是**从树上重算** `ungated`（`gates_mod.survey(ROOT)`），
它只是**提了一句** ci_merge 会把它打进 merge.log（`:883`、`:943`）。
所以 `NO GATE` **不需要**日志读者：「哪个 territory 没闸门」随时可重算。
「这个闸门这次弄脏了哪些文件」不可重算，**随 worktree 一起死**。
**因此 dirtied 子句不是被顺手忽略，而是结构性不可追补的那一个，且恰是无人看守的那一个。
这把我原本打算的反驳反转成了支持。**

顺带一条同族：`monitor/tests/test_gate_enforcement.py:83` 断言
`'a gate dirtied the worktree' in source`——一条 **grep 源码**的测试。
它钉住的是这个字符串**被印出来**，而**无论有没有人消费它都永远不会变红**。
那本身就是一条「没有负样本的检查」，而它守的正是这个信号。

### 4. 那个被丢掉的前置条件：逐条裁决

**(a) `:141` 是不是阻断性前置条件？是——而且我**低估**了它，只是把分支认错了。**

`monitor/inbox/20260730T0015Z-opsm-v25-masters-halt-was-a-false-positive-and-that-undermines-my-v21-ruling-too.md:110-152`，
`:141` 位于 §5「两条分支实际站在哪里」之下、标题
**「`v25`（d7a51bb5）—— B 这条理由上不阻塞；仍然不是裁判该做的事。真正剩下的是琐事，而且没有一件是我的」**
里的第 2 项：

> **2. Stale exam artifacts, merge-induced.** ……`exam.verify` cannot catch this because
> `build_papers` *writes* the artifacts rather than comparing them ——
> **Must be regenerated and committed before landing.**

不是建议、不是自言自语：它是**舰队合并裁判**（`monitor/CHARTER.md:56`：需要合并裁决 → OPS-M）
列出的四项落地条件之一，点名了正是那两个文件，
邻项还明确划了归属（「作者的活，不是裁判的活」）。它甚至**自己诊断了为什么没有闸门能抓**
——`build_papers` 是写而不是比。

**订正我自己**：这条前置条件针对的是 **v25（`d7a51bb5`）**，不是 `v26-handover-leak-ruling`。
**而链条闭合得比我写的更紧**：v25 是在 v26 里面落地的——
`git merge-base --is-ancestor d7a51bb5 3d59d0a6` → **是**（v21 `1f378483` 同样是）；
v21 与 v25 **没有自己的 MERGED 行**，`:2024-2025` 是 01:02:22Z 的
`CLEARED flag …(merged)`、`:2026` 是 `SWEEP-FLAGS retired 2 stale flag(s)`
——它们作为「已被合并」被扫掉，因为 v26 把它们带了进去。
`7856ff2b`「Merge origin/master into agent/v26-handover-leak-ruling」（00:00:47Z）动了这两个产物。

**所以 OPS-M 设了条件的那条分支，是以另一条分支的名义在 00:48:11Z 落地的，
而那一行合并记录恰好点名了那两个文件为 dirtied。收据与违反是同一个字符串。**

**(b) 后来补做了吗？没有。**

```
git log --no-merges --format='%H %cI %s' 3d59d0a6 --since=2026-07-30T00:48:11Z \
    -- exam/artifacts/leakage.json exam/artifacts/build_manifest.json
→ 空
```
到 pin 为止最后碰过这两个文件的提交是 `7856ff2b`，**2026-07-30T00:00:47Z——比那次合并早 47 分钟**。
在 pin（04:00:52Z）时这条前置条件已**未满足 3 小时 12 分**，陈旧产物就在 master 上。
**这不是时间抱怨，(b) 完整成立。**

**(c) 有人有义务读它吗？没有——「被静默丢弃」这个说法要从这里改掉。**

* `monitor/CHARTER.md:55` 定的流程是**工人 → inbox 提案 → 监控裁决 → 下发**；
  `monitor/mailbox/PROTOCOL.md:3` 把 `inbox/` 定为**向上**通道，与下行通道明确区分。
* **`monitor/scan.py:513-522 probe_inbox` 只读文件名，从不打开任何文件。**
  它对任何非空 inbox 返回 `partial` 和一句「待裁决提案 %d 份」。
  **184 个文件之一的第 141 行上的一条阻断性前置条件，对它是结构性不可见的。**

所以正确的说法不是「一条阻断性前置条件被静默丢弃」，而是：
**舰队的合并裁判把一条机器可核的落地条件写进了「扫描器会数但从不打开」的那个通道，
没有任何机制能让它生效；随后合并机器人把违反它的收据，印进了「没有任何解析器会读到」的那个子句。
两个各自孤立的通道，在同一行日志上相遇。**

### 5. `[:6]` 截断已证实会咬人，而底下还有一个更糟的缺陷

44 条子句里每条列出的文件数分布：

| 列出文件数 | 1 | 2 | 3 | 4 | 5 | **6** |
|---|---|---|---|---|---|---|
| 子句数 | 6 | 17 | 6 | 1 | 2 | **12** |

**44 条里有 12 条（27%）正好卡在上限上**——截断的签名。
而**日志之外恰好存在独立的地面真值**：
`monitor/inbox/20260728T153030Z-RES-3-worldgen-qc-gate-pinned.md:47-56` 独立量到

> `python -m worldgen.verify` **弄脏十个被提交的产物**……一次 verify 留下十个文件被修改

而 `merge.log` 里那两条 `worldgen` 子句列出的**正好是 6 个**。
**10 → 6，未披露。** 这一条从「可能」变成「已证实」。

**我漏掉的、而且更糟的缺陷：`if "/" in p` 对每一个根目录文件都是假阴性。**
`dirty` 是 `--porcelain` 输出的 `.split()`，再按「含 `/`」过滤。实测：

```python
tokens: ['M', 'PARTNER_SYNC.md', 'M', 'exam/artifacts/leakage.json', '??', 'Theoria.md']
kept  : ['exam/artifacts/leakage.json']
```

`PARTNER_SYNC.md` 是这支舰队被碰得最多的根文件，而且它就出现在本案那次合并的
`dirs:` 字段里（`dirs: PARTNER_SYNC.md,exam`）。
**一个弄脏了 `PARTNER_SYNC.md`、`Theoria.md` 或 `CLAUDE.md` 的闸门，会被报成「干净」**
——探测器把「没有证据」报成了「证据表明没有」，而且偏偏是在
`probe_append_only` 所守护的那类文件上。
另外：`.split()` 会切断任何含空格的路径；一次改名（`R old -> new`）会贡献两个路径
外加一个游离的 `->` token。
**`[:6]` 丢的是它已经拿到的信息；那个 `/` 过滤器是从来没拿到过。**

### 6. 既有项定位：不属于任何一条，但必须对三条表态

`ls monitor/audit/` = **60** 份（不是我便条里的 55）。

| 文件 | 关系 |
|---|---|
| `DRIFT-20260728T1752Z-twenty-probes-and-none-of-them-watches-the-queue.md` | **它拥有「没有探针读 merge.log」这条，而且它已被修好。** 它的 suggest 1 要的 `probe_merge_queue` 就是后来的 `mergequeue.py` + `scan.py:864`，`monitor/board/done/S25-probe-the-merge-queue.RES-4.md` 已 **done**。**重述「没人读 merge.log」等于重开一个已交付的条目。** 新说法必须缩到残留：S25 的正则停在分支名处。 |
| `DRIFT-20260728T1645Z-...-cannot-heal-itself.md:54` | 已经引过 dirtied 子句，拥有**副作用**那一半。它**没有**声称这个信号没人读——**它本身就是读者存在的证明。** |
| `DRIFT-20260730T0340Z-two-receipts-that-record-an-action-nobody-took.md` | 维度 7，「一张被印出来而非被测量的收据」。本条是它的**镜像**——一张**被测量而无人读**的收据。**兄弟，不是重复；交叉引用，不合并。** |
| `monitor/audit/WIP-cycle48-evidence.md:81-82` | 本条自己的草稿，同一周期。**不是独立既有项。** |

`grep -rln dirtied monitor/board/` → 无。没有 S25 家族的条目覆盖 dirtied 子句。

## suggest（监控裁决，我不执行）

1. **`mergequeue.py:51` 的正则要吃下整行尾巴**，或者让 `ci_merge` 把 `dirtied`
   写成结构化字段（例如同时写一份 `merge_events.jsonl`）。
   现在 `merged_ever` 算了一次、无人读，而尾巴根本没被捕获。
2. **`if "/" in p` 这个过滤器要去掉**——改成解析 `--porcelain` 的定长状态字段
   （或用 `--porcelain=v1 -z` 按 NUL 切分），否则弄脏根目录 append-only 文件的闸门永远报绿。
   **这一条比第 3 条重要**：它是假阴性，而 `[:6]` 只是少报。
3. **`[:6]` 要么去掉，要么把总数一起写出来**（`… and N more`）。
   已证实会咬：12/44 卡在上限，且 worldgen 的真值是 10 而日志写 6。
4. **给 dirtied 一个常设读者，或者让它变成能拒绝的东西**：
   既然 `:566-571` 的理由是「有些闸门刻意再生产物」，
   那就把「刻意」显式声明出来（例如 territory 级的 `regenerates:` 白名单），
   **白名单之外的脏就阻断**。那样这个信号才有一条会变红的路。
5. **`probe_inbox`（`scan.py:513-522`）只数文件名。** 若 inbox 要承载
   机器可核的落地条件，就得有人打开它；否则 `CHARTER.md` 应当明说
   **inbox 提案不构成任何落地条件**，这样裁判就不会把条件写进无人读的地方。
   两条选一，现状是最坏的第三种。
6. **那条前置条件本身仍然未满足**（在 pin 时已 3 小时 12 分）：
   `exam/artifacts/{leakage,build_manifest}.json` 需要重新生成并提交。
   注意它与 `DRIFT-20260730T0418Z` 是同一批产物，但那是**另一个**缺陷（数字），别混。

## 我对这份报告的保留

本轮第五份，而 `AUDITOR.md` 要我在超过三份时先怀疑判据。我怀疑过：
它与 `0340Z` 是同一维度的镜像，与 `0428Z` 同样讲「核实是空的」，
但三者的补救互不重叠（这里是解析器与过滤器，那里是赋值与引用），硬并会毁掉可执行性。

**这份报告最该被记住的是它对我自己的评价**：
**我的头条是被一次范围太窄的 grep 制造出来的**，而反驳它的证据里有一条
是**我自己上一世写的报告**。`grep -rn "dirtied" monitor/*.py monitor/*.html`
排除了 `monitor/audit/`——也就是说，**我搜索「有没有人读过这个信号」时，
把我自己读过它的那份记录排除在搜索范围之外。**
下次问「有没有读者」，先搜整棵子树，并且**把自己的产出目录包含进去**。
