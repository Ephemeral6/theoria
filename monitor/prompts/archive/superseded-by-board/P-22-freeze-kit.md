# P-22 · 冻结包起草：Phase 4 开跑前必须提交哈希的一切

基准 `Theoria.md`（Phase 4 冻结清单 13 项 + 统计裁决规则 + 冻结前待定五项——原文逐字是你的需求书）。开工仪式：读 `CLAUDE.md`、PARTNER_SYNC 尾十段、`baseline-arms/BUDGET_REPORT.md`（n 由包络方差定的原料）、`battery/PREDICTIONS.md`，绿了开工。
分支制：`agent/p22-freeze-kit` + 独立 worktree；push 分支不碰 master。领地：新建顶层 `freeze/`。

目标：把封存战役的预注册材料从条款变成可哈希提交的文件包（起草，不冻结——冻结动作留给人）：

1. `freeze/MANIFEST_DRAFT.md`：13 项逐条→树上对应物路径 + 版本；缺的标缺并指向在飞工单；
2. `freeze/STATS_RULES.md`：统计裁决规则逐字草案——三主终点（U3 达成率/判决题准确率含特异度/前载指数配对差）、Wilcoxon 配对、n 的定法（引包络实测方差，含 ar25 degraded 的敏感性处理）、其余指标一律标探索性；
3. `freeze/CLAIMS_TEXT.md`：C1–C5 逐字文本 + **双结局**（成立怎么写/不成立怎么写，两版都先写死）；
4. `freeze/PENDING_FIVE.md`：待定五项现状表——已可定的给出建议值与依据（模型版本串可实测；预算可从包络外推），真需要用户拍板的明确标 needs_human。

最难的裁决（n 的取值、主终点措辞）用最深思考（ultrathink 级），并派对抗性子代理攻击草案（「这条规则事后能被钻空子吗」——抗游戏审计的精神）。**Stop-hook 收工**：`freeze/verify.sh` = 13 项清单逐条有落点或有标注，无一遗漏。
留痕：`freeze/runs/<UTC>-p22/` 边跑边写。收工：RUN_STATE + MANIFEST(prompt_id: P-22) + PARTNER_SYNC + push。全程自主。
