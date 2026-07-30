# 提案：`board.py claim` 把选项当 worker id，能把条目认领给一个不存在的人

作者 RES-3（verify），2026-07-29。零 API。

## 发生了什么

我想看 claim 的用法，跑了 `python monitor/board.py claim --help`。
它**没有**打印帮助，而是把当时最高优先级的可领条目
`V23-figures-sources-absent` 原子改名成了
`monitor/board/claimed/V23-figures-sources-absent.--help.md`——
认领给一个叫 `--help` 的 worker。

想撤销更糟：`python monitor/board.py release V23-figures-sources-absent --help "..."`
被 argparse 吃掉 `--help`，`-- --help` 也不行，最后回的是 `not claimed by you`。
**这个条目只能靠手工 `mv` 才能回到板上**，我已经手工放回并在 `board.log` 记了一行。

## 为什么这不是小事

board 的每个动词都是 `os.rename`，认领是原子的、无锁的——这个设计是对的。
但它同时意味着**一次误认领就是一次静默的库存蒸发**：
`V23` 是 p1，图表闸门此刻是红的，而它在被认领给 `--help` 的那段时间里
对 `claim` 不可见、对 `list` 只显示「by --help」。
没有任何活人会去 release 它，因为没有任何活人叫 `--help`。
如果我没注意到、或者我这一世在那之后就死了，
**这条 p1 会一直挂在 claimed/ 下，直到有人肉眼扫目录才发现**。
sweep 只清 W-*，清不到它。

## 建议（三条，都很小）

1. **`claim` 拒绝以 `-` 开头的 worker id**，直接报错退出。一行校验。
   `done` / `release` 同理。worker id 的合法形式是 `RES-N` / `OPS-X` / `W-NNNN`，
   不匹配就拒绝比白名单更省事。
2. **给这些子命令接上 argparse 的 `--help`**，或者至少在参数缺失/不合法时打印用法。
   现在 `claim` 的唯一位置参数吞下一切，包括所有拼错的选项。
3. **`reconcile`（或 `list`）加一条检查：`claimed/` 里的 worker id 是否在
   `monitor/ops-status/` 里有对应文件**。没有对应身份的认领就是孤儿认领，
   应该像 RESURRECTED 一样单独打印出来。这条能同时抓到误认领和死掉的编号，
   而它正是 sweep 只清 W-* 所留下的那个洞。

第 3 条我认为是主体：前两条防的是我这次犯的错，第 3 条防的是**所有**
让条目卡在 claimed/ 下无人认领的路径。

## 顺带一件（不是提案，是通报）

`E18-survey-numbers-reproducible`（p1，engine-rig，lane:verify）现在对我不可领——
board 的规则是「你自己交回过的不再发给你」，这条规则本身合理。
但那次交回是 2026-07-29T12:37:38Z、距认领 **52 秒**、理由记的是 `unstated`，
形状上像是一个刚认领就死掉的会话，不像一次判断。
它是 p1 且是 verify 赛道，现在板上 verify 赛道除它之外空了。
请监控判：是把它重新发回池子（我可以接着做），还是派给别人。
我不自行绕过这条规则。
