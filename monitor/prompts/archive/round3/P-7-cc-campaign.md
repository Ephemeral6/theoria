# P-7 · baseline-arms：裸 CC 开发堆战役 + Schema 路 A 材料

基准文件是 `Theoria.md`（1.12 主表、Phase 2 材料、Phase 3 经济：对照两臂各 2–3 局出方差包络）；再读 `CLAUDE.md` 与本轨道全部文档：`baseline-arms/STATUS.md`、`AUDIT.md`、`DECISIONS.md`、`BUDGET_REPORT.md`、`TOUCHED_GAMES.md`、`INCIDENTS.md`。
领地：`baseline-arms/`。其余只读；`PARTNER_SYNC.md` 只追加；提交只 add 自己领地。

两件事：

1. **裸 CC 战役**：按既有 harness 与预算闸门，在开发堆上把裸 CC 臂跑出 Phase 3 要的方差包络（每局 2–3 次，逐局跑完即入账；TOUCHED_GAMES 续账）。预算闸门是硬的：BUDGET_REPORT 的止损条件触发就停并写明。
2. **Schema 路 A**：只拉取上游释出 artifacts 中属于**开发堆 4 局**的轨迹（Theoria.md:311 明确许可），落成与本轨道账本同格式的只读材料，来源与哈希入账。**下载器必须先按 piles.json 白名单过滤再读取任何内容**——INC-BA-001 的教训：检索与下载过程本身就能污染封存局。

技巧要求：战役用**循环自动推进**（一局结束→入账→对照预算闸门→自动下一局，闸门红则停），不要一局一停等人；每局跑完派一个审计 subagent 复核账本自洽（动作数、score 对得上、无封存 ID）后才进下一局；路 A 下载派独立 subagent 执行，主上下文只接收白名单过滤后的清单与哈希，不接收任何机制内容；模型调用的 usage 全量入账（这是 C5 的原料）。

红线：封存堆 API 与内容双零接触（白名单先行）；密钥只在 `.env`；预算闸门优先于任何「再跑一局」的冲动。
全程自主，不停下来问。完成即提交 + PARTNER_SYNC 追加一段。
