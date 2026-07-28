# C2-semantics-migrate · a0-spike 的 v0.2 迁移：master 已红 9 小时

**这是 master 上的现行故障**，由 OPS-M（合并裁判）与 OPS-R（回顾员）各自独立报出：
`a0-spike` 全套 32 条 FAILED/ERROR，同一根因——`theory_compiler.parser` 已按 dsl_grammar v0.2 要求 `semantics:` 段，而 `a0-spike/theory/theory.dsl` 还是 v0.1 没有该段。合并裁判判「不硬解、留给监控」，正确：这是语义修订，不是合并冲突。

开工仪式：读 `CLAUDE.md`、PARTNER_SYNC 尾十段、`monitor/inbox/20260728T035214Z-opsm-conflict-a0spike-semantics.md`（冲突全文与它的诊断）、`CONTRACTS/dsl_grammar_v0.1.md` 的 v0.2 修订记录与 `cold-start-a0/proposals/dsl_grammar_v0.2_semantics.md`（该段的设计意图）。
分支制：`agent/c2-semantics-migrate` + 独立 worktree；push 分支不碰 master。领地：`a0-spike/`。

目标：让 a0-spike 在 v0.2 契约下全绿，且**迁移是有语义的、不是让测试闭嘴**：

1. 给 `a0-spike/theory/theory.dsl` 补 `semantics:` 段——帧公理、冲突策略、级联形状三项必须**如实反映该世界的真实语义**（a0-spike 是推箱子式世界，真值在 `a0-spike/world/`），不是抄 cold-start-a0 的。逐项在 THEORIZE_LOG 记明依据；
2. 全套测试转绿（`cd a0-spike && python -m pytest`），四形态重新生成并过 certify；
3. 若发现 v0.2 的表达力不足以说出这个世界的语义，**不要硬凑**——记进表达力台账并在 PARTNER_SYNC 向 theory-compiler 轨道报告；
4. 顺带清偿 OPS-A 报的留痕缺口：`a0-spike/runs/` 按正典建档（`MANIFEST.json`，字段见 CLAUDE.md Conventions）。

前沿工具：先出迁移计划再动手（最难的是"这个世界的真实语义是什么"，用最深思考）；派对抗性 subagent 检查「补上的 semantics 是否真的描述了这个世界」而非只让解析器满意；Stop-hook 收工：`a0-spike/verify.sh` = 测试全绿 + 四形态重生成一致。
留痕：边跑边写 `a0-spike/runs/<UTC>-c2/`。收工：RUN_STATE + MANIFEST + PARTNER_SYNC + push 分支。全程自主，不停下来问。
