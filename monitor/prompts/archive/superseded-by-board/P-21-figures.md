# P-21 · 论文图表流水线：数据在树上，图还不存在

基准 `Theoria.md`（3.2 的图清单：图2 账单形状、图3 能力谱、图4 迁移、图6 概念诞生时间线）。开工仪式：读 `CLAUDE.md`、PARTNER_SYNC 尾十段、`battery/REPORT_V0.md`、各 THEORIZE_LOG（只读），绿了开工。规划先行：`figures/PLAN.md` 先列每张图的数据源路径与形态。
分支制：`agent/p21-figures` + 独立 worktree；push 分支不碰 master。领地：新建顶层 `figures/`。

目标：每张图一个**确定性生成脚本**（数据→CSV 中间层→图，同输入两跑逐字节同图）：

1. 图6 概念诞生时间线——cold-start-a0 THEORIZE_LOG 的修订史 + 触发事件，带时间轴；
2. A0 vs A0′ 覆盖-准确率对照（论文最强受控实验的主图）；
3. 图2 账单形状（初版）——baseline 试点/包络账本的逐回合成本曲线，theoria-arm 一有账本即可加列（接口留好）；
4. 图3 能力谱（初版）——battery REPORT 的族×臂矩阵；
5. A2 修复回路六拍账目流。

样式统一：无障碍色板、双主题、SVG+PNG 双出。**Stop-hook 收工**：`figures/verify.sh` = 全部图重生成两遍 diff 为空 + 每张图的数据源哈希记录在旁。子代理按图并行；发现可复用的画图流程沉淀 `.claude/skills/`。
留痕：边跑边落盘 `figures/runs/<UTC>-p21/`。收工：RUN_STATE + MANIFEST(prompt_id: P-21) + PARTNER_SYNC + push。全程自主。
