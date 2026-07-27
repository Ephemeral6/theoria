# prompts v3 — 七份可同时开跑的短提示词（含 subagent / loop 技巧）

设计原则：简短、给目标和红线不给步骤、全程自主（每份都写「不停下来问」）、
**领地互斥**（七份可一次全部粘给七个 Opus 5 会话并行），且每份内嵌了该任务
最合算的前沿技巧：并行 subagent 分工、对抗性 subagent 复核、裁判/选手上下文
隔离、循环自动推进、后台测试守护。

| # | 干什么 | 唯一写入领地 | 内嵌技巧 |
|---|---|---|---|
| P-1 | incident 改判 + 预检重跑 + 污染登记 | `arc-recon/` | 4 局并行 subagent；对抗性改判复核 |
| P-2 | 双代理 + 账本格式 + 变体层 | 新建 `proxy/` | 红队 subagent 攻密封；fuzz 循环 |
| P-3 | 指标电池 v0 | 新建 `battery/` | 五族并行 subagent；刷分对抗审计 |
| P-4 | 死锁刻画 + IC3/PDR + 探针接规划器 | `engine-rig/` | 三引擎并行；证书怀疑者 subagent |
| P-5 | 编译器汇合 + refuse 语义 + v0.2 裁决 | `theory-compiler/` `CONTRACTS/dsl_grammar` | subagent 当移交测试真读者 |
| P-6 | A2 自建 DC22 同构世界 | 新建 `cold-start-a2/` | 裁判/选手上下文隔离；六拍循环 |
| P-7 | 裸 CC 战役 + Schema 路 A 材料 | `baseline-arms/` | 局间循环 + 预算闸门；隔离下载 subagent |

共享面只有 `PARTNER_SYNC.md`（追加式）与 git（各自只 add 自己领地）。

**等所有者裁决、不能派工的**：F-11（封存主张集缩不缩到 19 局）、
F-12（可逆性准则进不进 Theoria.md）、F-13（主表 Schema 行口径）——
这三件是基准文件/统计口径的修订权，在监视器页面的发现区。

v1/v2 旧工单在 `archive/`。
