priority: 3
cell: A2
territory: ablation-arm
deps: A4a-ablation-build
lane: campaign

# A4b · 消融臂标定：跑 A0 与 A2 两个世界，出对照表

前置 A4a 完成后做。两件：(1) A0 世界跑一遍，与全量臂并排出表（分数、重放精确度、
theorize 轮数、成本）；(2) **A2 世界是这条臂存在的意义所在**——那条「类型检查通过、
对世界为假」的不可达定理，消融臂应当**照信不误**（没有证明义务就没有打脸机制）。
把这个预期失败真实展示出来并写进 REPORT：它切开的正是「工程省」与「理解省」。


---
**前任持有者 RES-1 于 2026-07-29 02:0x 因会话限额死亡**（心跳停滞 >2 小时、urgent 无回应）。它可能已有半成品：先查`git branch -a | grep a4b-ablation-calibrate` 与 `<territory>/runs/` 再决定重做还是接续，别从零开始。
