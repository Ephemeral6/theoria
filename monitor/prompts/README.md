# prompts 第 4 批 — 分支制生效的第一批

上一批（P-1..P-7）已全部落地并核实（见监视器回路账）。本批六份：五份并行 +
一份合并，**分支制从本批开始**——每个 agent 独立分支 + worktree，master 只由
M-0 改。

## 派工

| # | 干什么 | 领地 | 分支 |
|---|---|---|---|
| P-8 | **Theoria 臂在线化（关键路径）**：内环第一次真 API 对局 | 新建 `theoria-arm/` | `agent/p8-theoria-arm` |
| P-9 | 外壳收口：冻结打分器、密封红队、正典守卫、复放抽检 | `proxy/` | `agent/p9-shell-harden` |
| P-10 | CONTRACTS v0.2 演化窗口 + E-06 + a2 报的缺陷 | `theory-compiler/` `CONTRACTS/` | `agent/p10-contracts-v02` |
| P-11 | F-11 落账 + 金丝雀重放 + 接入核查清尾 | `arc-recon/` | `agent/p11-arc-hygiene` |
| P-12 | 包络续跑（F-15）+ 账本正典迁移（F-16）+ 留痕补档 | `baseline-arms/` | `agent/p12-envelope-finish` |
| R-1 | harness 回顾第一跑（只读全仓，提案入 inbox） | `monitor/inbox/` | `agent/r1-retrospective` |
| M-0 | **最后跑**：逐分支合并 + 全套测试集成门 | master | — |

P-8..P-12 与 R-1 同时开跑；全部 push 分支后跑 M-0。

## 本批统一模板（每份内已含）

开工仪式（读 SYNC 尾 + 本领地 STATUS + 跑测试）→ 分支/worktree → 干活
（技巧：并行 subagent / 对抗复核 / 循环推进 / 低配模型做机械校验，扇出一批
≤10）→ 收工仪式（runs/ + MANIFEST(prompt_id, branch, base_commit, seed) +
RUN_STATE + PARTNER_SYNC + push 分支）。验收标准是合同，不许自降；做不到
如实报 gap。全程自主。

## 监控代行裁决（本批携带执行的）

F-11（主张集 21→19，P-11 落账）· F-14（schema v0.2 加法式升版，P-10）·
F-15（ar25 记 degraded，P-12）· F-16（proxy 账本为正典，P-9/P-12）。

旧批在 `archive/round3/`。
