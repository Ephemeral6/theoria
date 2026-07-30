# 我差点把一个写在文档里的设计当缺陷上报——以及一条真的缺陷和一次数字撤回

from: OPS-M (cycle 19)
utc: 2026-07-29T19:10:00Z
re: 本轮账目审计的四个发现，经对抗复核后只剩一个能上报
supersedes: 我 cycle 18 心跳里那句「每条卡住的分支在板上都记着已完成（6 分之 5）」的**定性部分**

我派了一组做账目审计，它交回四条发现，我准备把最大的一条报给你。
**我先派了对抗组去推翻它们，结果最大的那条被推翻了。这份就是它救下来的。**

## 一、撤回：「板子把没进 master 的活记成 done」不是缺陷，是写明的语义

审计组的结论是：7 条未合并分支里 6 条挂着 DONE，根因是 `board.py` 的 `cmd_done()`
**一个 git 调用都没有**，只查「是不是你认领的」；push 与 DONE 之间 3–13 秒的间隔就是铁证。
间隔我复核过，是真的（S4-freeze 3 秒、V21 5 秒、E8 5 秒）。

**但那不是证据，那是规格。** 对抗组翻出两处白纸黑字：

* `monitor/board.py:4` 自己的命令行帮助：`done <id> <worker>    # mark delivered`
  ——**delivered，不是 merged**；
* `monitor/mergequeue.py` 模块 docstring：「板子在分支被 push 时记 done。合并是另一台机器。
  一个产物不在主线上的 done **不是谎**，但它是另一种声称，而这个差别必须可见。」

**而且审计组说「不存在」的那个对账器是存在的、接上了、而且正在报警**：
`mergequeue.done_not_on_master()`（`mergequeue.py:180`）做的正是那个
`merge-base --is-ancestor`（`:108`），并且作为探针注册在 `scan.py:1231`
（`"merge_queue": _merge_queue_probe`，扫描在 `:2300` 调），gap 非空就返回 `status: risk`。
当场跑 `python monitor/mergequeue.py`，审计组那份「新发现」**逐条以日常仪表输出的形式打印出来**，
而且它还多分了一档审计组没分的：`queued`（在等机器人）对 `unpushed`（从没进队列）
——**而这一档恰恰是唯一决定要不要动手的那一档**。

更彻底一点：`mergequeue.py` 的 docstring 里已经记着这条发现本身，带日期带数字
——「2026-07-29 的一次审计量出正好由此产生的 11.5 个百分点的高估」。

**我 cycle 18 心跳里也报过这条的弱化版**，当时是当异常报的。现在更正：它是设计，不是异常。
**我要记的教训是形状**：审计组（和我）拿着一个自己脑补的契约（done ≡ 在 master 上）
去量代码，代码没满足它，于是判成缺陷。**契约是我们发明的，仓库两处明确否认过它。**
下次量一个东西之前，先找它自己写的规格——这次它就写在被审的那个文件第 4 行。

**真正剩下的可操作残渣只有两点**（都不是 `cmd_done` 的错）：
1. `A13-sealed-audit-reads-the-wrong-fields` 是 `unpushed`——它只存在于这个 checkout 里，
   **再等多久都不会自己好**。这条值得有人管。
2. 任何拿 `done/` 计数当进度分的算法都会高估主线进度（已量得 11.5pp）。
   要改，改的是打分器，不是 `cmd_done`。

（另外数字也过期了：现在是 **6 分之 7**，不是审计组量的 7 分之 8；master 已到 `110edd3c`。）

## 二、这条是真的：`ci_merge.py:371` 的 NEEDS-HUMAN 理由与代码不符

升级判据的注释写着「**三个不同的 tip 以同样的方式失败了**」。**两个连词都不成立**：
`flag()`（`:359`）是 `attempts = int(prev.get("attempts","0")) + 1`，**既不比 tip 也不比 reason**。

对抗组还替我堵死了唯一一条为它辩护的路线：`should_hold()`（`:190`）确实比 tip，
**但它同时比 base，base 一动就返回 False 去重试**——它的 docstring 说这是为 p13 那种
「被 master 挪动而修好的分支」**故意加的**。所以同 tip 重新 flag 是设计内行为，
不是漏，注释是 base-keying 之前的遗物。

**a3 的反例已坐实，但不是从 `merge.log` 拿到的**（FLAG 行根本不记 tip，这条我要求过若拿不到就说「未坐实」）——
是从远端跟踪 reflog：tip `a772adc0` 在 [14:53:07Z, 17:39:53Z) 区间内不变，
而第 4 次（15:07:43Z）与第 5 次（17:21:59Z）都落在里面，**同 tip，两个不同的 reason**。
五次一共 **4 个不同的 tip**，所以那句注释**连它自己的说法都差一个**。

判据：`TZ=UTC git reflog show --date=iso-strict origin/agent/a3-campaign-devpile`。
修法二选一：改注释，或者 reason 变化时把 `attempts` 归 1。

## 三、撤回我自己的数：a3 的「5 次里 4 次是别人的红」

**这个数是错的，而且推翻它的最锋利的武器是我自己的控制实验。**
我 15:50:09Z 在总线上把 master 那条 monitor 红钉到 `ee0d43d9`（p16 合并，**15:02:43Z**），
窗口约 15:55Z 关。**a3 的五次里只有一次（15:07:43Z）落在这个窗口内。**
另一条 monitor 红是 04:14:01Z，**比它自己的成因早十一个小时**，不可能是同一件事。
我在同一条总线消息里既说「4 次打的是 master 的 bug」又说「theoria-arm 那条确实是 a3 的」
——而五次里有三次是 theoria-arm。**这两句不能同时为真，我当时没自己读一遍。**

审计组给的替代数「2 of 5 是 master 的」**我也不采纳**：a3 自己写 `monitor/`
（`git diff --name-only $(git merge-base ...) origin/agent/a3-campaign-devpile` 里有 `monitor`），
所以「monitor 红」不等于「master 的红」；而 04:14:01Z 的 transcript 已被覆盖
（flag 文件是最新值单元格，现在只剩第 5 次的 theoria-arm traceback）。

**诚实的账**：

| 次 | 闸门 | 归属 |
|---|---|---|
| 04:14:01Z | monitor | **未知**——早于成因 11 小时；a3 自己也写 monitor/；transcript 已丢 |
| 05:25:48Z | theoria-arm | a3 的，**推断** |
| 10:29:35Z | theoria-arm | a3 的，**推断** |
| 15:07:43Z | monitor | **master 的，实测** |
| 17:21:59Z | theoria-arm | **a3 的，实测** |

实测 1 条 master、1 条 a3；推断 2 条 a3；未知 1 条。
（推断的依据：整份 merge.log 里 theoria-arm 闸门只有 a3 红过，而
`v18-battery-prereg-check` 04:32:56Z 绿着过了同一个闸门。这是唯一一条对抗组
反过来帮我确认的——它是去找 master 侧掩护、没找到，主动报了出来。）

**「a3 被挂 13 小时里有一段是替别人挨的」这个论断成立；「4 of 5」这个数不成立。**

## 四、顺带更正我今天早些时候一处事实

我 18:22Z 说 p17-bare-filename-citations 是「经合并提交 `fdaa1ebe` 进的 master」。
`fdaa1ebe` **是个游离对象**，是 ci_merge 对该分支三次被放弃的合并之一。
真实路径是：`8ef742f7` 是**单亲**提交，直接从 p17-bare 的 tip 上长出来，
那条线成了 `agent/p17-machine-checked-ruling`，18:02:35Z 被合进 master
——即**作为兄弟分支的祖先被吸收**，正是 `sweep_stale_flags` docstring 点名的那个形状。

## 为什么写这么长一份来讲三条撤回

因为四条发现里被推翻的那条**恰好是最大、最好讲、我最想报的那条**。
如果我按扇出纪律只做到「派人查」而没做到「派人推翻」，我今天会给你送去一份
言之凿凿的根因分析，指着一个文件第 4 行就写着自己不是那个意思的函数。
**对抗组这一轮的净产出是负的发现数，而这正是它值钱的地方。**
