# HANDOFF — 监控会话的转世文件

**读者：下一个监控会话（可能就是失忆后的我）。** 读完本文件 + 记忆里的
`monitor-role-workflow` 即可无缝接管，不需要历史对话。每次心跳重写本文件；
最后更新见文末时间戳。

## 你是谁、规则在哪

- 角色：Theoria 仓库的监控实例。只监控不执行；`Theoria.md` 是唯一基准。
- 规则全集：用户记忆 `monitor-role-workflow.md`（分支制、留痕、隔离契约、
  跑完即杀、配额熔断、审计员、前沿工具提示词、GitHub 同步、决定代行）。
- 完成目标：可发表论文（spec.py 的 PAPER_PLAN，Schema 规模对标）。

## 每次心跳的固定动作（顺序执行）

1. `python monitor/dispatch.py --reap`（跑完即杀）
2. `python monitor/quota.py check`——返回 2 = hold：跳过 4-6，只做 ping/resume
3. 读 `monitor/audit/` 新的 DRIFT-*.md → 裁决 → 移 archive/；A-1 死了就
   `dispatch.py --only A-1` 重拉
4. `git fetch` 对照 `monitor/loop_state.json` 记完成（分支到 origin）
5. 完成≥5 → 按仓库实况写 5 份新工单（模板见 prompts/README + 记忆 7b）并
   `dispatch.py` 发射；完成≥10 → 完整监控循环（spec 更新 + scan.py + push）
6. 读 B-* 的 needs_human 与 M-0 的 CONFLICT 报告 → 该转用户的转用户
7. 更新 loop_state.json 与本文件；`git add monitor/ && commit && push`
8. `ScheduleWakeup`（正常 1800s；hold 期 3600s）

## 当前态势快照（2026-07-28T09:35Z 心跳外手动更新）

- 在飞 13：P-8/9/12/13/15/17（用户开的 app 会话）、P-18/19/20、R-1、B-1、
  M-0、A-1（后七个是 dispatch 的，pid 在 dispatch-logs/registry.json）
- 已交付 4：P-10、P-11、P-14、P-16（分支在 origin，待 M-0 合并）
- 配额：normal；论文完成度 26.8%；下一个已排 wakeup：见会话调度
- 悬而未决：B-1 第三次发射存活中（前两次无声早夭）；M-0 首跑结果未收
- 特别注意：工单原文在 monitor/prompts/（含 A-1 的契约 AUDITOR.md）

## 转世纪律（用户 2026-07-28 指令）

- 监控自身约每 3 小时（≈6 个心跳）做一次**完全重写本文件**的深度换血：
  重新盘点在飞/完成/悬案，不从上下文抄——从磁盘和 git 重新求证。
- 若因 5h 限额被掐：什么都不用做，wakeup 会在窗口刷新（≈5h）后把你带回来；
  醒来第一件事重读本文件与 loop_state，然后走心跳固定动作。
- 用户新开会话说「继续」时：等同转世，照本文件接管即可。
