# monitor — 方法论 v2（外部实践吸收记录）

2026-07-28 依据公开的多 agent 工程实践对本监控系统做的一轮系统性增补。
每条注明来源与它在本系统的落点。Theoria.md 仍是研究内容的唯一基准；
本文档只管**过程工程**。

## 吸收的外部实践 → 本系统落点

| # | 外部实践 | 来源 | 落点 |
|---|---|---|---|
| 1 | 开工仪式：每个新会话先读进度文件与 git log、跑冒烟测试，再开新活 | Anthropic《Effective harnesses for long-running agents》 | 每份提示词标准头：读 PARTNER_SYNC 尾部 + 本领地 STATUS + 跑本领地测试套件，绿了才开工 |
| 2 | 收工仪式 + 防"提前宣捷"：完成声明必须过独立验证 | 同上 | 标准尾：RUN_STATE.md + runs/ 归档 + PARTNER_SYNC + push 分支；**若本领地尚无收工闸门（`verify.sh`/`verify.py`）则必须新建一个**（见下 §收工闸门）；「自报完成」与「监控核实」在工作板上分列 |
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

## 收工闸门（S13，2026-07-28）

**旧写法「交付前写一个 verify 脚本」是自觉条款**，于是它按自觉条款的方式失效了：
没人食言，只是从来没人被要求过，而**合并日志里「跑过闸门」与「压根没有闸门」是同一行**。
DRIFT `stop-hook-verify-gates-are-decoration` 记的是另一半——C2 合并时点名了
`a0-spike/verify.sh`，那个文件从未被造出来，合并时无人发现。两种病症，必须分开报。

### 现在的机制（不是纪律，是机器）

1. **`monitor/gates.py` 是唯一真相源**。它问树、不问表：领地有 `verify.sh`/`verify.py`
   → `verify`；没有但有 `test_*.py` → `pytest`；两者皆无 → `none`。
   `ci_merge` 与 `scan.probe_verify_gates` 都读它——两份实现会漂移，这仓库为此付过一次账
   （手维护的表过期，509 个测试没跑；手写的修复在同一个提交里七条错了四条）。
   非规范名也认（`proxy/verify_spend.sh` 是真闸门），并在记录里写明它不规范。
2. **`ci_merge` 合并前跑该领地的闸门**，`verify` 优先于 `pytest`（每个闸门第一段本来就跑自己的套件，
   跑两遍等于把合并最慢的一段翻倍，而慢的合并机会被绕过）。verify 红 → 不合并，
   flag 里与「tests red」**分开命名**。
3. **无闸门的领地照常合并，但每次都写进 `merge.log`**：
   `NO GATE, MERGED UNCHECKED: <领地>`。让敞开可见，而不是默认。拒绝合并无闸门领地会把仓库整个卡死。
4. **闸门弄脏工作区也会被记下**：`a gate dirtied the worktree: <文件>`。不拦（有些闸门按设计
   重生成产物），但一个往被检查的树里写东西的闸门，能把**下一个**领地的闸门弄红，
   而红的理由与这条分支毫无关系。
5. **探针分开报两种病**：「声称有却没有」是 risk；「本来就没有」是 amber 的一句实话。
   把两者混成一个数字，要么冤枉老实人，要么放过漏洞。

### 写工单时

* 标准尾里那句现在是：**若本领地尚无闸门则必须新建**——`gates.py` 一跑就知道有没有。
* 闸门三段式（参照 `ablation-arm/verify.sh` 与 `monitor/verify.py`）：
  **测试 + 一次真跑 + 产物字段自检**。
* **闸门的产物写 `mktemp -d`**。`monitor/verify.py` 就是靠 `scan.build(out_dir=…)` 做到的；
  在此之前 `scan.build` 无条件往 `monitor/` 写三个文件，这个领地的闸门根本没法在不弄脏自己的
  前提下跑一次真扫描。
