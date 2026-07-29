# P-24 · 舰队技能库：把重复流程沉淀成 skill，加速之后的每一个会话

背景：这个仓库由多个并行 Claude Code 会话开发（读 `monitor/METHOD.md` 与 `monitor/prompts/README.md` 了解体制）。每份工单都在重复同样的仪式：建 worktree 分支、建 runs/ 档案写 MANIFEST、写 verify.sh、收工 PARTNER_SYNC + push。这些应当各成一个项目 skill，让以后每个会话开箱即用——**对舰队的每小时产出是乘法**。
分支制：`agent/p24-fleet-skills` + 独立 worktree；push 分支不碰 master。领地：`.claude/skills/`（共享地面，**只新增目录，不改任何已有 skill**）。

目标：四个 skill，各含 SKILL.md（触发条件写清楚）+ 辅助脚本：

1. `fleet-branch-ritual`：开工仪式一键化——从最新 master 建 agent 分支 + worktree、读 SYNC 尾部、跑本领地测试的标准流程；
2. `runs-archive`：留痕一键化——建 `runs/<UTC>-<slug>/`、增量写入辅助、MANIFEST 生成器（prompt_id/branch/base_commit/seed/逐文件 sha256）；
3. `verify-gate`：Stop-hook 式收工——按领地惯例生成并执行 verify.sh，不绿报清单；
4. `handoff-close`：收工仪式一键化——RUN_STATE 模板、PARTNER_SYNC 段落格式化（追加式校验：只许在文件尾加自己的段落）、push 分支。

每个 skill 在一个临时 worktree 里**真实演练一遍**（演练产物入 runs/ 作为 skill 的验收证据）；描述字段要让触发精准（照 skill-creator 的最佳实践）。写完派一个新子代理只按 SKILL.md 使用四个技能走完整流程——它卡住的地方就是文档缺陷，修文档不修使用者。
留痕：`.claude/skills/runs-p24/`（演练档案）。收工：PARTNER_SYNC + push 分支。全程自主。
