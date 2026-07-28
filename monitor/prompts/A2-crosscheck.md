# A2-crosscheck · 双 A0 交叉复核：两条独立实现互考对方的世界

背景：这个仓库有两条**独立写成**的 A0 冷启动实现——`cold-start-a0/`（theory-compiler 轨道）与 `a0-spike/`（engine-rig 轨道），各自的世界、流水线、说明书。这是天然的实现无关性实验：把 A 的流水线跑 B 的世界（只给轨迹与动作语义，不给真值与对方说明书），反之亦然。基准 `Theoria.md`（1.11 held-out 与移交的精神；§8 单一实现偏置是要披露的局限——本实验直接压缩它）。
开工仪式：读 `CLAUDE.md`、两个 A0 目录的 README/THEORIZE_LOG，跑双方测试绿了开工。
分支制：`agent/a2-crosscheck` + 独立 worktree；push 分支不碰 master。领地：新建顶层 `crosscheck/`（两个 A0 目录只读 import）。

目标与度量：

1. **A→B 与 B→A 各一跑**：产出说明书 + certify + plan；裁判 subagent 持双方真值，主线对真值盲（同 A2 纪律）；
2. 度量并列表：规则集恢复率（与对方真值比）、重放精确度、held-out 预测、plan 是否解出、两条流水线在同一世界上的**分歧点清单**（分歧 = 有人错或世界歧义，逐条裁决归因）；
3. 分歧里最有价值的东西：**两实现都错在同一处** = 框架级盲区候选，单独成节写 `crosscheck/FINDINGS.md`；
4. 结论一句话回答：Theoria 的冷启动能力是框架的性质，还是某个实现的运气？

技巧：两方向并行 subagent + 裁判独立上下文；分歧归因用对抗式双辩。留痕 `crosscheck/runs/<UTC>-a2x/`。收工：RUN_STATE + MANIFEST(prompt_id: A2-crosscheck) + PARTNER_SYNC + push。全程自主。
