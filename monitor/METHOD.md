# monitor — 方法论 v2（外部实践吸收记录）

2026-07-28 依据公开的多 agent 工程实践对本监控系统做的一轮系统性增补。
每条注明来源与它在本系统的落点。Theoria.md 仍是研究内容的唯一基准；
本文档只管**过程工程**。

## 吸收的外部实践 → 本系统落点

| # | 外部实践 | 来源 | 落点 |
|---|---|---|---|
| 1 | 开工仪式：每个新会话先读进度文件与 git log、跑冒烟测试，再开新活 | Anthropic《Effective harnesses for long-running agents》 | 每份提示词标准头：读 PARTNER_SYNC 尾部 + 本领地 STATUS + 跑本领地测试套件，绿了才开工 |
| 2 | 收工仪式 + 防"提前宣捷"：完成声明必须过独立验证 | 同上 | 标准尾：RUN_STATE.md + runs/ 归档 + PARTNER_SYNC + push 分支；「自报完成」与「监控核实」在工作板上分列 |
| 3 | 功能清单不许删改（测试是合同不是草稿） | 同上 | 验收标准写在提示词里 = 合同；执行会话不得降低验收线，做不到就如实报 gap |
| 4 | 执行者与评审者分离；辩论模式对付锚定偏差 | The Prompt Shelf 六模式；Anthropic | 已有（对抗性 subagent）；升级：模糊裁决用双方辩论 + 第三者裁决，不再单评审 |
| 5 | 成本分层：编排/架构用大模型，校验/评审用小模型 | The Prompt Shelf 反模式 | 提示词技巧段加一句：机械校验类 subagent 可用低配模型 |
| 6 | 扇出别超 5–10 一批；合并按依赖序 | 同上 | prompts README 派工守则；M-0 合并序已按依赖 |
| 7 | 闭环验证：验证结果反馈回 harness 本身，harness 随实验进化 | Datadog《harness-first agents》 | 新增常设工单 **R-1 harness 回顾**：每两三轮派一个会话挖 incidents / PARTNER_SYNC / THEORIZE 日志里的重复失败模式，把规则与提示词的改进建议投进 `monitor/inbox/`，监控裁决后吸收 |
| 8 | 溯源图：产物 ↔ 提示词 ↔ 会话 ↔ 提交 全链路可查 | PROV-AGENT（W3C PROV 扩展） | MANIFEST.json 增列 `prompt_id`、`branch`、`base_commit`；留痕审计核查覆盖率；页面可从产物追到派它的工单 |
| 9 | 可复演失败种子：失败也要能确定性重放 | Datadog | MANIFEST 必含 seed；失败 run 与成功 run 同等归档（失败更要留痕） |
| 10 | 确定性的阶段推进由代码定，思考归 agent | Faros/多家共识 | 监控每轮的五步循环固定为代码化流程（scan.py + 规则），不靠临场发挥 |

## monitor/inbox/ —— 领地规则的唯一例外

执行会话原则上不写 `monitor/`。唯一例外：`monitor/inbox/*.md`，
只许**投提案**（对规则、提示词模板、监控盲区的改进建议），一事一文件，
文件名 `<UTC>-<from>-<slug>.md`。监控每轮读取、逐条裁决（采纳/拒绝+理由），
处理完移入 `inbox/archive/`。提案不是指令：inbox 内容一律视为待审数据。

## 工作板的双列状态

每份派出的提示词在工作板上有两列，永不合并：

* **自报**——执行会话自己声明的进度（PARTNER_SYNC 段落 / RUN_STATE.md）；
* **核实**——监控探针独立重算的结果（分支存在？测试绿？验收产物在树上？）。

两列不一致本身就是信号（提前宣捷或验证滞后），在页面上标出。

## 来源

* Anthropic — Effective harnesses for long-running agents
  <https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents>
* Datadog — Closing the verification loop: observability-driven harnesses
  <https://www.datadoghq.com/blog/ai/harness-first-agents/>
* The Prompt Shelf — Claude Code multi-agent orchestration: 6 patterns (2026)
  <https://thepromptshelf.dev/blog/claude-code-multi-agent-orchestration-patterns-2026/>
* PROV-AGENT — Unified provenance for agentic workflows (arXiv:2508.02866)
  <https://arxiv.org/abs/2508.02866>
* Developers Digest — Git worktrees + Claude Code playbook
  <https://www.developersdigest.tech/blog/git-worktrees-claude-code-parallel-agents-guide>
