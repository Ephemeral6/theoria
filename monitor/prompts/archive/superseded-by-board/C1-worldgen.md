# C1-worldgen · 世界样机库：批量自建小世界族，给全项目供弹药

基准 `Theoria.md`（A0 红利条款原文：「提示词的开发迭代全部发生在自建世界族，ARC 开发堆只作验证」——现在的自建族只有 4 个手工世界，不成"族"）。再吸收 A0′ 的框架发现：**机制可逆性 > 轨迹覆盖率**（cold-start-a0/prime/A0P_REPORT.md，必读）。
开工仪式：读 `CLAUDE.md`、三个 cold-start 目录的世界实现，绿了开工。
分支制：`agent/c1-worldgen` + 独立 worktree；push 分支不碰 master。领地：新建顶层 `worldgen/`。

目标：可参数化的世界族生成器 + 首批 20 个世界成品：

1. **机制库**（每种都带真值定义与不变量）：推动/重力下落/开关-门网络（可逆与不可逆两版）/传送（单向、双向、成对）/计数锁（集齐 k 个）/颜色变换循环/一次性消耗物。组合生成，复杂度分档；
2. 每个世界出厂自带：ground truth 规则集、可解性判定（或不可解证书思路）、系统探索轨迹、`raw_trace.jsonl`（与 cold-start-a0 同格式，下游零改动）、机制可逆性标注（A0′ 准则进出厂检验：每个世界标明哪些规则可重复见证）；
3. **质检**：抽 3 个世界各跑一遍 cold-start-a0 的流水线（只读 import），说明书准确率达标才算族合格；
4. 用途登记：迭代提示词开发、考卷出题原料（改规则适应题的变体对）、fuzzlab 的高层世界源、消融臂标定场。

技巧：机制库并行 subagent 分头实现；质检用独立子代理盲跑；确定性（seed 全表）。留痕 `worldgen/runs/<UTC>-c1w/`。收工：RUN_STATE + MANIFEST(prompt_id: C1-worldgen) + PARTNER_SYNC + push。全程自主。
