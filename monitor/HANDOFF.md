# HANDOFF — 监控会话的转世文件

**读者：下一个监控会话（可能就是失忆后的我）。** 读完本文件 + 记忆里的
`monitor-role-workflow` 即可无缝接管，不需要历史对话。每次心跳重写本文件；
最后更新见文末时间戳。

## 你是谁、规则在哪

- 角色：Theoria 仓库的监控实例。只监控不执行；`Theoria.md` 是唯一基准。
- 规则全集：用户记忆 `monitor-role-workflow.md`（分支制、留痕、隔离契约、
  跑完即杀、配额熔断、审计员、前沿工具提示词、GitHub 同步、决定代行）。
- 完成目标：可发表论文（spec.py 的 PAPER_PLAN，Schema 规模对标）。

## 反射层已接管机械动作（TheoriaReflex 计划任务，每 5 分钟）

reap / quota check / 三振限内复活 / ci_merge 合并即交付 / 页面轻刷——
全部由 `monitor/reflex.py` 零 token 自跑。心跳**不要重复做这些**。

## 每次心跳的固定动作（只剩判断）

1. 读 `monitor/reflex.log` 新行 + `dispatch-logs/exits.json`（死因）+
   `monitor/ci/`（合并 flag：红测试/冲突留给判断）+ `monitor/audit/`
   （DRIFT 报告，裁决后归档）
2. `git log` 看 ci_merge 落了什么 → **合并即补位**：为刚合并的产物写
   消费它的新工单（坐标编号，机械型加 `<!-- model: sonnet -->`），
   dispatch 发射；关键路径（A3/theoria-arm）闲置立即抢发
3. 三振名单（reflex 报 three-strikes 的）：重写或拆分该工单再发
4. needs_human / CONFLICT → 该转用户的转用户
5. **前端判定**：master 变了 / 关键事件 / 3h 硬底 → 全量更新
   （spec + scan + push + 发给用户）；否则不动（轻刷反射层已做）
6. 更新 loop_state 与本文件；commit + push；`ScheduleWakeup`
   （正常 1800s；hold 3600s）

## 当前态势快照（2026-07-28T11:45Z）

- **舰队**：8 个无头板工人（W-*，一次性、做完接着领）+ 2 个常驻研究员（RES-1/RES-2，
  各守一条 lane）+ 4 个运维（OPS-A/B/M/R，App 常驻）+ 用户 App 里的研究会话。
- **工作板**：`monitor/board/`——工人自助领活（原子改名领取、领地互斥、deps 门、
  lane 归属）。监控只管**出活**与**控人数**，不逐件派单。
- **自动件**：`TheoriaReflex`（5 分钟，reap/quota/复活/ci_merge/刷页面，**已启用**）、
  `TheoriaDashboard`（10 分钟跑 scan.py）、`TheoriaServe`（本地 :8787 服务前端）。
- **前端**：`monitor/app.html` 每 20 秒拉 `state.json`；后端改判断即自动生效。
- **论文完成度** 39%；封存堆零接触；配额窗口开。

## 转世纪律（用户 2026-07-28 指令）

- 监控自身约每 3 小时（≈6 个心跳）做一次**完全重写本文件**的深度换血：
  重新盘点在飞/完成/悬案，不从上下文抄——从磁盘和 git 重新求证。
- 若因 5h 限额被掐：什么都不用做，wakeup 会在窗口刷新（≈5h）后把你带回来；
  醒来第一件事重读本文件与 loop_state，然后走心跳固定动作。
- 用户新开会话说「继续」时：等同转世，照本文件接管即可。
