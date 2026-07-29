# P-10 · CONTRACTS v0.2：契约演化窗口（一次开窗，全部清偿）

基准文件是 `Theoria.md`。开工仪式：读 `CLAUDE.md`、PARTNER_SYNC 最后十段（engine-rig 的 enum 挂旗、cold-start-a2 的两条缺陷上报、自己轨道的 E-06）、`CONTRACTS/` 两份契约、`cold-start-a0/proposals/dsl_grammar_v0.2_semantics.md`，跑本轨道测试，绿了开工。
分支制：`agent/p10-contracts-v02` + 独立 worktree；push 分支不碰 master。
领地：`theory-compiler/` 与 `CONTRACTS/`（candidates_schema 的 v0.2 升版已由监控裁决 F-14 授权：**只做加法**，v0.1 校验器保留）。

清偿清单（全部是别的轨道排队等你的）：

1. **candidates_schema v0.2**：新增 M9 两引擎的 kind 枚举值 + 可选字段，v0.2 校验器新增、v0.1 保留；变更逐条注明哪台引擎逼的；PARTNER_SYNC 挂会签请求（engine-rig 回签后生效——异轨道异步会签，不等待，先落草案）。
2. **dsl_grammar v0.2 定稿**：`semantics:` 提案裁决落文（若 P-5 已采纳则补正式版本号与迁移说明）；E-06（证书权重自动注入，消灭手抄）实现进编译链。
3. **cold-start-a2 上报的两条缺陷**：修复 + 负向测试（缺陷内容见 PARTNER_SYNC 94a8202 与 cold-start-a2/DECISIONS.md）。
4. **回归**：peg、cold-start-a0、a0-spike、cold-start-a2 四份 DSL 全部过新编译链——契约升版不许弄坏任何既有消费者。

技巧：四份 DSL 的兼容验证派四个并行 subagent；v0.2 草案写完派一个「engine-rig 视角」subagent 只读草案模拟会签审查，它挑出的刺先修再挂签。

收工仪式：runs/ 归档（prompt_id: P-10）；STATUS 更新；PARTNER_SYNC 追加（含会签请求）；push 分支。全程自主，不停下来问。
