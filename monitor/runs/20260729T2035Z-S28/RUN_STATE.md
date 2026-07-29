# S28 · 监控自己也没有第三个值

条目 `S28-no-third-value-in-the-monitor`，RES-4，赛道 infra，领地 `monitor`。
分支 `agent/s28-no-third-value-in-the-monitor`，base `5a997ef8`（= 当时的 `origin/master`）。
零 API 花费，封存堆零接触。

## 这件活是什么

2026-07-29 的对抗性普查（57 个 agent）给出一句总结：**这个代码库没有第三个值——
「测不到」和「测了，没问题」编码成同一个字面量，而每一处默认值都指向健康答案。**
监控最严重的四条当场修掉了（`pid_alive(0)` 恒真、reflex 的 `"Running"` 在中文控制台
永不命中、读不到内存默认 99GB、`--lane` 自报身份绕过花钱守卫）。**剩下 11 条是这件活。**

## 接续，不是重做（第 0 步）

本条目在板上已被 RES-4 认领，但**磁盘上没有任何 run 目录**——上一世（cycle 35）
交付的是 S29 / R3 / S34 / R4 四件，S28 只领了没开工。所以这是新开工，不是接续。

顺带记录两件启动时查到的事实，都影响做法：

* **本地 master 落后 `origin/master` 15 个提交**，而工作树里有大量监控运行时写入的
  未提交改动，所以本分支从 `origin/master` 建，不从本地 master 建。
* **同名分支 `agent/s28-no-third-value` 存在，但装的是 S34 的提交**（已并入
  `origin/master`）。为避免把两件活搅在一条 ref 上，本次用全名
  `agent/s28-no-third-value-in-the-monitor`。这正是那条「认领时印出同名分支」
  的告警（`20260729T1050Z-S28-claim-warns-on-existing-branch`）想让人做的事：
  先看一眼，再决定接续还是另起。

## 开工前先核对了 11 个现场（15 个提交会挪行号）

条目里的行号写在普查当天，`origin/master` 之后又走了 15 个提交。逐条核对的结果：

| 条目 | 原文行号 | 当前位置 | 状态 |
|---|---|---|---|
| 1 板列表抹掉领地互斥 | board.py:150 | board.py:280-324 | 仍在，且实测有条目不可见 |
| 2 `_supply` 把 reserved 数进供货 | scan.py:764 | scan.py:916（孪生另计） | 仍在 |
| 3 「已禁用」哨兵被编码销毁 | scan.py:554 | scan.py:627-645 | 仍在 |
| 4 `heartbeat_age` 信任被跟踪文件 mtime | board.py:56 | board.py:62-67 | 仍在；但 `.gitignore` 那一半上游已做 |
| 5 裸 `except OSError` → 假 BOARD-EMPTY | board.py:268 | board.py:434-437 | 仍在 |
| 6 板查询崩溃写成 0 | standing.py:223 / reflex.py:193 | standing.py:308 / reflex.py:198,298 | 仍在 |
| 7 `probe_append_only` 跳过已删文件 | scan.py:458 | scan.py:522-556 | 仍在 |
| 8 `probe_verify_gates` 丢 `decorative` | scan.py:736 | scan.py:850 | 仍在 |
| 9 手打的缩水 `ACK_REQUIRED` | scan.py:813 + bus.py:169 | scan.py:936-982 | **bus.py 那一半上游已修**，scan.py 仍在 |
| 10 只看 ci_merge 的 stdout | reflex.py:271 | reflex.py:289 | 仍在 |
| 11 `via_task` 的 ok 是调度器的收据 | dispatch.py:311 | dispatch.py:311-322 | 仍在；`_runner.py:98` 取了 `which` 仍无守卫 |

**11 条里 9 条整条仍在、2 条各有一半已被上游修掉。** 这张表本身就是「先核对再动手」
的产出：条目 4 和条目 9 若照原文照抄地修，会写出两处重复修复。

## 做法

条目原文有一条硬要求，照办：**逐条修、逐条配阴性样本，不许打包成一次「已全部加固」。**
每条都要有「修之前这个假信号确实存在」的证据（跑一次、贴输出）。理由是普查的第二层
结论——**出问题最多的是补丁本身**——所以一个没有「修之前」证据的修复，本身就是它
要治的那个病的新实例。

扇出：按**文件所有权互斥**切成四组并行（同一个工作树里四个 subagent 同时改，
只要没有两个人碰同一个文件就不会互相踩）：

| 组 | 独占文件 | 条目 |
|---|---|---|
| 1 | `board.py` | 1、4、5 |
| 2 | `scan.py` | 2、3、7、8、9 |
| 3 | `standing.py`、`reflex.py` | 6、10 |
| 4 | `dispatch.py`、`_runner.py` | 11 |

每组写自己的一个测试文件与自己的一份 `EVIDENCE-<n>-*.md`（**增量写**，不许攒到最后），
所以四组也不会在留痕上打架。跨组的边（条目 11 的消费者在 `scan.py` 里、
条目 6 的哨兵消费者在别人文件里）一律**写成补丁提案交回**，不越界改。
四组汇总后再派一个对抗性 subagent 专门试图推翻结论，推不翻才算交付。

四组都收到同一条安全线：`standing.py` / `reflex.py` / `dispatch.py` / `_runner.py`
是**此刻正在这台机器上跑的**活代码（跑的是主检出，不是本工作树），且 dispatch 会
花真钱起会话。只准 monkeypatch + 临时目录测试，不准建计划任务、不准起会话、
不准写主检出的 `dispatch-logs/`。测不了的路径写进报告，而不是开火试一下。

## 进度

- [x] 第 0 步接续核对、11 个现场逐个核对（上表）
- [x] 建分支与工作树（仓库内 `.worktrees/`）、MANIFEST、本文件
- [ ] 四组并行修复 + 阴性样本
- [ ] 对抗性复核
- [ ] 全量测试、verify 闸门、PARTNER_SYNC、push、`board.py done`
