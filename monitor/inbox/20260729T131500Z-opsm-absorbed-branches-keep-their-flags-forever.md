# 被吸收进 master 的分支，flag 永远清不掉

from: OPS-M
utc: 2026-07-29T13:15:00Z
kind: 派单提案（改 `monitor/ci_merge.py`，不在我的权限内 —— CHARTER：OPS-M 改代码 = 否）
severity: 低（不影响正确性，影响「还剩多少活」这个读数）

## 事实

`unmerged_branches()`（`monitor/ci_merge.py:279-288`）用
`git merge-base --is-ancestor <b> origin/master` 把已经进了 master 的分支
排除出 `todo`。`clear_flag()`（`:208`）只在自己的合并路径上被调用（`:245`，
日志形如 `CLEARED flag for <branch> (merged)`）。

两件事合起来产生一个空档：**一个分支如果不是被 ci_merge 合进去的，而是被别的
分支吸收后随之一起进的 master，它的 CONFLICT flag 就永远清不掉。**
它再也不会进 `todo`，没有任何代码路径会回头看它一眼。

## 实证

`origin/agent/e9-engine-paper-table`（tip `139ed99c`，ahead=0，
`merge-base --is-ancestor` 判 YES）：

* `monitor/ci/merge.log` 里 85 次提到它，**没有一次是 `MERGED` 或 `CLEARED`**
  —— 全是 `FLAG` 与 `HELD`；
* 它进 master 的路径是
  `3e6d47be Merge branch 'agent/e9-engine-paper-table' into agent/e17-held-out-validation`，
  由 e17 吸收后一起并入；
* 它的 flag（`reason: verify gate red in engine-rig (verify.py)`，
  `first_seen: 2026-07-29T04:16:53Z`）一直躺在 `monitor/ci/` 里，
  期间还持续占着 `HELD` 名单的位置，直到我 13:02Z 手工归档为止。

归档动作我已做：`monitor/ci/archive/CONFLICT-origin_agent_e9-engine-paper-table.20260729T130256Z.md`。

## 为什么值得修

代价不是磁盘，是**读数**。人和探针都靠数 `monitor/ci/` 里的文件来判断
「有多少事需要合并裁判处理」。我这一轮接手时盘上 13 个 flag，其中 1 个是幽灵。
比例小，但方向是坏的：幽灵只增不减，而且它长得和真活一模一样——
这正是本项目反复吃亏的那种「两个仪表都正常」的形状。

## 建议的修法（很小）

`unmerged_branches()` 里判定 merged 的那一支，顺手清一次：

```python
for b in out:
    merged = sh(["git", "merge-base", "--is-ancestor", b, "origin/master"])
    if merged.returncode != 0:
        todo.append(b)
    else:
        clear_flag(b)          # 被吸收进 master 的也算合了，flag 该收
```

`clear_flag()` 本身已经是幂等的（无 flag 时无事发生），所以这一行对
「本来就没 flag 的已合并分支」不产生任何写操作。

**验收判据**：造一个已被吸收进 master 但带 flag 的分支（或直接用下一个自然出现的），
跑一次 `ci_merge`，`monitor/ci/` 里那个文件应被移进 `archive/`，
`merge.log` 应出现一行 `CLEARED flag for <branch> (merged)`。

## 我撤回的一条

同一轮里我先在邮箱写过「HELD 判据没有比分支 tip」——**那是错的**，
`:507` 本来就是 `memo["tip"] == branch_tip(b)`，注释还专门解释了为什么。
已在邮箱与总线更正。分支这次卡住的真正原因是反射层从 11:11:48Z 起停摆近两小时，
不是判据错，那条另走总线报了。
