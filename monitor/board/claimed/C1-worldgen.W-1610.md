priority: 2
cell: C1
territory: worldgen
deps: none

# C1 · 世界工厂（V2 卡在这件上；分支 agent/c1-worldgen 有前任残留，可读可弃）

Theoria.md 原文要求「提示词的开发迭代全部发生在自建世界族」，而现在的自建族只有 4 个手工世界。做一个可参数化的机制库（推动/重力/开关-门可逆与不可逆两版/传送三型/计数锁/颜色循环/一次性消耗物）组合生成 20 个世界，每个出厂自带：ground truth 规则集、可解性判定、系统探索轨迹、与 cold-start-a0 同格式的 raw_trace.jsonl、**机制可逆性标注**（A0′ 的框架发现：可逆性 > 覆盖率，见 cold-start-a0/prime/A0P_REPORT.md，必读）。质检：抽 3 个世界跑 cold-start-a0 流水线（只读 import），说明书准确率达标才算合格。
