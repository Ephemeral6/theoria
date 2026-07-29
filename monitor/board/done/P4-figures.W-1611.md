priority: 3
cell: V5
territory: figures
deps: none

# P4 · 论文图表流水线（数据都在树上，图还不存在）

每张图一个确定性生成脚本（数据 → CSV 中间层 → 图，同输入两跑逐字节同图）：图6 概念诞生时间线（cold-start-a0 THEORIZE_LOG 修订史 + 触发事件）；A0 vs A0′ 覆盖-准确率对照（本仓库最强受控实验）；图2 账单形状初版（baseline 账本逐回合成本，theoria-arm 有账本即可加列）；图3 能力谱（battery REPORT 的族×臂矩阵）；A2 修复回路六拍账目流；A3 迁移对照（携书 vs 从零，cold-start-a3/artifacts 有现成数据）。仓库已有 `deterministic-figures` skill，先读它。样式：无障碍色板、双主题、SVG+PNG 双出。verify.sh = 全部图重生成两遍 diff 为空 + 数据源哈希记录在旁。
