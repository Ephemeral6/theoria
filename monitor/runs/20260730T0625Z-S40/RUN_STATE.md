# S40 · fleetkit 是 board.py 的抽取分叉（RES-4，infra）

**进行中。** 本文件边跑边写——只存在于上下文里的信息视同不存在。

## 状态

- 分支 `agent/s40-fleetkit-fork-has-drifted`，worktree `.worktrees/s40-fleetkit`，
  基线 `origin/master` = 60def5cb。
- 要求 1（逐函数行为比对）已派 subagent 测量，未回。
- 要求 2 的判断（跟着走 vs 故意简化）**尚未做**——它依赖要求 1 的数字。

## 下一世从这里接

若本文件没有「验收」一节，说明这件活没做完，板上的认领仍然是我的。

## 先记一条结构性发现（06:35Z，测量还没回来，但这条不依赖它）

fleetkit **已经有一套「说出自己没做什么」的纪律**，而且理由写得很好：
`fleetkit/verify.py:213` 的 `unported_note()` 每一轮都打印

> `note  NOT ported, ~1400 lines: dispatch, reflex, quota, assign, ci_merge.`
> `Printed every run because a gap named once in a README is invisible in a week.`

模块 docstring（`verify.py:25-33`）把理由写死了：「一个没人被提醒的未移植的一半，
过一阵读起来就是一个完成了的工具包」。

**但这套机制的粒度是「模块」，判据是 `os.path.exists(fleetkit/<name>.py)`**
（`verify.py:214`）。于是：

* `board.py` **存在**，所以它算「已移植」；
* 而 S40 说的那三处（`released_by` 概念、S35 的三处修复、死的 `LANE_OWNER`）
  是**同一个模块内部的判据缺失**——现有机制看不见这一档。

**一个部分移植的模块，在这套机制里读起来和一个完整移植的模块一模一样。**
这正是本条目「看起来一样、实际不一样、没人说过它该是哪种」的第三种状态的
机制层面成因，而且它把答案也指出来了：fleetkit 的设计本来就是**故意的简化**
（「The kit coordinates; it does not yet launch or merge」），所以要求 2 的
两条路里该走「故意分叉 + 写明」——但**写明的地方不该只是 README**，
按 fleetkit 自己的理由，该进那个每轮都打印的机制，并且粒度要从模块降到判据。

要求 4 的阴性对照因此也有了形状：让 `monitor/board.py` 的某条判据变了而
fleetkit 没跟，检查必须红。

---

## 要求 2 的判断（做完了）：**跟着走**，理由是测量把另一条路排除了

条目给了两条合法路：跟着 monitor 走，或者故意的简化分叉并写明。
**「故意的简化」这条路在证据面前不成立**，三个理由：

1. **没有任何东西是被有意去掉的。** 分叉基线有 18 个顶层函数，fleetkit
   恰好有这 18 个、一个不多不少。monitor 那 18 个独有函数**全部**是分叉之后
   才落上去的（S21/S27/S28/S29/S34/S35/S35a，7 个提交；fleetkit 一辈子 1 个提交）。
   这不是简化，是**过期快照**。
2. **它的后果里有真缺陷，写进文档就是把 bug 写成 feature。** 最响的一条：
   `_PREFIX = ""` 从未被赋值，于是 `cmd_sweep` 判定每个工人都死了、
   **把还在跑的工人的活抢走**——这是 `fleetkit/KNOWN_TRAPS.md` 第 1 条一字不差，
   潜伏在那个 ship 出这份警告的工具包自己身上。
3. **两份文档里没有 track/sync/drift/fork/snapshot/upstream 任何一个词**，
   而 README 给 `board.py` 的状态是 `ported: ... lanes, sweep`——
   **`lanes` 与 `sweep` 两项实测都不工作**。

所以：**跟着走**。机制是 `monitor/tests/test_fleetkit_drift.py`。

### 机制的形状（为什么不是「两个文件必须相同」）

判据是 **「分叉必须被声明，否则红」**，不是「必须一致」。后者会永远红，
而永远红等于没有闸——S39 刚把这条教训写下来。于是：

* 今天的 10 处分叉全部进 `DECLARED` 表，每条带 **verdict**（`extraction` /
  `stale` / `defect`）与一段**实测出来的**理由；
* monitor 以后改了某条判据而 fleetkit 没跟 → **下一轮就红**；
* 有意为之的分叉 → 一行加一个理由；
* 反向也管：某条被真的移植了、表项没删 → **另一个测试红**（陈旧的声明本身是谎）。

**这就是把「第三种状态」逼成两种合法状态之一的装置。**

### 要求 4 的阴性对照（5 条，都跑过）

新分叉未声明 → 红；同一处声明了 → 绿；两边完全相同 → 绿；
只有一边有的函数 → 不算分叉（那是 README 已经回答过的模块级问题）；
**只有行尾不同 → 不算分叉**（monitor 是 CRLF、fleetkit 是 LF，裸 diff 报 714 行，
不归一化的话这道检查落地第一次跑就 100% 假阳）。

### 一处我自己改掉的数字

派出去测量的 subagent，**逐函数的判词是对的，汇总行是错的**：它写
「6 IDENTICAL / 12 DIVERGENT」，与它自己那张表对不上（照表数 8 个 IDENTICAL）。
我用 `ast` 逐函数比归一化源码复算：**shared 18、源码不同 8、源码相同 10，
其中 2 个（`stale_lanes`/`territories_busy`）源码逐字节相同却仍然行为分叉**
（通过 `LANE_OWNER` 全局）——**所以行为上的分叉是 10 处**。
数字已按跑出来的改，`FINDINGS.md` 里也记了这次更正。
`test_the_measured_divergence_count_is_pinned` 把 18/8/10 钉死，动了就红。

## 要求 3：**没做，因为不是我的领地**

条目要求把 `LANE_OWNER` 那句假 docstring 改真或删掉。**那在 `fleetkit/` 领地里，
而 S40 声明的 territory 是 `monitor`**（`gates.territories()` 确认 `fleetkit`
是独立领地）。红线是「只写领到的条目所声明的 territory」，所以：

* monitor 这边能做的是**不让这个claim被忘掉**：
  `test_the_false_docstring_is_still_there_and_still_false` 断言那句话还在、
  且 `LANE_OWNER` 在包里仍然没有任何写入。**有人把它修好的那一刻这条测试会红**
  ——那正是它该红的时刻，提醒去更新 `DECLARED` 与这条测试本身。
* 真正的修复（docstring、`_PREFIX` 接线、`__main__.py` 缺失、README 那行
  `ported: ... lanes, sweep`）已自供成 **`S42`**，territory `fleetkit`。

**这是本条目唯一没有按字面完成的要求，原因不是难度是权限，已写明。**

## 验收

* `python -m pytest monitor/tests/test_fleetkit_drift.py` —— **12 passed**
* `python -m pytest fleetkit/tests` —— 6 passed（基线，未被本件改动）
* `python fleetkit/verify.py` —— green（基线）
* `python -m pytest monitor/tests/` —— **3 failed**，全部在
  `test_standing_reflex_no_third_value.py`，**与本件无关且是先存的**：
  本 worktree 只有两个新增未跟踪文件，那三条测的是 `reflex.py`，
  我一行没碰。**基线 `origin/master` = 60def5cb 上就是红的**，已上总线报。
