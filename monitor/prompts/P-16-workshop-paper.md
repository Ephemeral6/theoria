# P-16 · Phase 1 结的最小可发表单元：workshop 文初稿

基准文件是 `Theoria.md`（阶段交付物条款：「Phase 1 结：A0–A2 + 电池对既有轨迹的回算，独立可成 workshop 文」；第三部分论文叙事是骨架）。开工仪式：读 `CLAUDE.md`、PARTNER_SYNC 全文、四份验收报告（`cold-start-a0/A0_REPORT.md`、`prime/A0P_REPORT.md`、`a0-spike/THEORIZE_LOG.md`、`cold-start-a2/A2_REPORT.md`）、`battery/REPORT_V0.md`。
分支制：`agent/p16-workshop-paper` + 独立 worktree；push 分支不碰 master。
领地：新建顶层 `papers/phase1-workshop/`。其余只读；PARTNER_SYNC 只追加。

目标：把已经真实发生的东西收束成一篇 workshop 短文初稿（Markdown 即可，图先做数据后做样式）。素材全在树上，一个数字都不需要新造：

- 钩子：预测满分与理解破产可共存（A0 的 R-05 洞 = DC22 盲区在自建世界的复现；A2 的假定理展品）；
- 主体：A0/A0′ 对照（可逆性>覆盖率——本仓库最强的受控实验）、真 A1（证书过数据边界、空公理集）、A2 修复回路六拍；
- 图 1：概念诞生时间线（cold-start-a0 THEORIZE_LOG 的修订史，带触发事件）；
- 图 2：A0 vs A0′ 覆盖-准确率对照；图 3：A2 打脸→重证回路的账目流；
- 电池一节：REPORT_V0 的能力谱 + 预注册纪律说明；
- 诚实条款逐条照录（Theoria.md 3.2 第 8 节的口径：仅确定性环境、语法脚手架披露、A2 是同构自建而非上游重放——引 INC-004）。

红线：**每个数字必须能指回树上的一个文件**（引用用相对路径）；没有的实验不许写「we show」；不代改任何报告原文；署名占位。

技巧：逐节并行 subagent 起草，一个「审稿人 subagent」拿评审视角（新颖性/证据/可复现）过一遍再改；图的数据抽取脚本入 `papers/phase1-workshop/figures/`，确定性可重生成。

收工仪式：runs/ 归档（prompt_id: P-16）；PARTNER_SYNC 追加；push 分支。全程自主，不停下来问。
