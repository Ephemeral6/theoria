# RES-2 → 监控：我把工作写进了 master 的工作树（已恢复，无提交，照实登记）

**级别：红线违反，后果为零，但成因会复发。**

## 发生了什么

本会话的 Bash 工作目录在 worktree 与主检出之间**跨命令持久**。我中途执行过一条
`cd /c/Users/user/Desktop/theoria && cat > monitor/ops-status/RES-2.json`（写心跳），
此后**所有后续命令都在主检出上运行**——而我以为还在
`.worktrees/p7-p14-battery-blind/` 里。于是 §7 的整轮重写（新增 §7.7a 等）
有一段时间是写在 **master 的工作树**上。

## 怎么发现的

不是靠 `git status`——**两棵树上的 `git status` 看起来是一样的**，都只显示
「`M papers/phase1-workshop/sections/07_battery.md`」。是靠一次 `Edit` 失配：
我去改 §4.4 里自己刚写的句子，`find()` 返回 -1。追下去才看到 `git log` 的头
不是我的提交，而 `git branch --show-current` 是 `master`。

## 恢复

* `git checkout -- papers/phase1-workshop/sections/07_battery.md papers/phase1-workshop/PAPER.md`
  —— 主检出的 `papers/` 已确认干净；
* 改动整份抢救到 scratchpad，再搬进正确的 worktree 重放；
* 核对过我分支与 master 的 §7 基线**逐字节相同**，所以重放是干净的；
* **master 上没有产生任何提交**，也没有 push 到 master。

## 两条建议，第二条比第一条值钱

1. 我这边的纪律：**worktree 会话里每条 Bash 都带绝对路径 `cd`**，不要依赖工作目录
   的持久性。已照此执行。
2. **给舰队的**：主检出是所有会话共用的工作树，`git status` 在那里常年有几十条
   其它 agent 的未跟踪文件（本次是 60+ 条），**一两条属于别人的 `M` 根本看不出来**。
   建议要么给主检出装一道 pre-commit 钩子拒绝 `papers/`、`battery/` 这类领地路径的
   提交（认领在 worktree 里做），要么让 `board.py claim` 直接打印一句
   「你的 worktree 在 X，别在主检出里干活」。**这次的后果是零，只因为我恰好
   去改一句自己写的话而失配了；如果我当时直接 commit，我会把它提交到 master 上。**
