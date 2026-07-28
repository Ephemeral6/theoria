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

## 增补五份（与上表零冲突，可立即加开五个会话）

| # | 干什么 | 领地 | 分支 |
|---|---|---|---|
| P-13 | Fast Downward 真接入，三档阶梯补全 | `engine-rig/` | `agent/p13-fd-real` |
| P-14 | battery v1：吃 a2/a0-spike/包络新材料 + 区分力首跑 | `battery/` | `agent/p14-battery-v1` |
| P-15 | 考卷构造器：held-out/移交/改规则/判决题四题型 | 新建 `exam/` | `agent/p15-exam-builder` |
| P-16 | Phase 1 结 workshop 文初稿（数字全部指回树上文件） | 新建 `papers/phase1-workshop/` | `agent/p16-workshop-paper` |
| P-17 | A3 两关世界：C3 迁移的第一份离线证据 + 负对照 | 新建 `cold-start-a3/` | `agent/p17-a3-transfer` |

这五份的分支由**下一次 M-0**（或重跑当前 M-0 时追加清单）合并；依赖序：
P-13/P-15/P-16/P-17 互相独立，P-14 不依赖未合并分支、以 master 现有材料为准。

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
