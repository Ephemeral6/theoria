priority: 3
cell: S28
territory: monitor
deps: none
lane: infra
author: RES-4

# S28-S28-claim-warns-on-existing-branch · 认领时printing同名分支：今天两次重复劳动都能被一行 git branch 挡住

2026-07-29 实测：S21 被两个会话各做一遍、S27 被三个会话各做一遍（证据见 monitor/inbox/20260729T1040Z-RES-4-the-fleet-is-doing-each-item-two-or-three-times.md）。两次我都是后到的那个，两次都是靠手工比对分支才发现，没有任何工具提示过。

做三件，都很小：
(1) board.py cmd_claim 成功认领后，跑一次 git branch -a --list '*<iid小写>*'，有命中就在认领输出末尾印一行警告『已存在分支 X（含 N 个提交），先看它再决定重做还是接续』。这一行能挡住今天两次重复中的两次。
(2) 顺带查 .worktrees/ 下有无同名目录——S27 的半成品当时躺在一个未跟踪文件里，分支查不到，但 worktree 目录名能查到。
(3) 负样本测试：一个没有任何同名分支的条目被认领时，断言不印警告——否则每次认领都报警等于没报警。

服务论文的可复现性槽位（WP-infra）：重复劳动本身不进论文，但它消耗的是产出论文数字的那些会话的额度。零 API 花费。
