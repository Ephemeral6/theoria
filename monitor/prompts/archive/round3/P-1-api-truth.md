# P-1 · arc-recon 官方状态改判 + 污染登记续账

基准文件是 `Theoria.md`，所有裁量以它为准；先读它的 Phase 1 与 `CLAUDE.md`。
领地：`arc-recon/`。其余只读；`PARTNER_SYNC.md` 只追加；提交只 add 自己领地（多会话并行中）。

三件账务，全部有据可查：

1. **INC-001/INC-002 正式改判**：baseline-arms 已独立复核（`baseline-arms/AUDIT.md` §6、DECISIONS D-005：400 是瞬时故障，重试即过）。在 `incidents.jsonl` 追加 superseded 条目（不改旧行），README 同步。
2. **确定性预检重跑**：带退避重试在开发堆上跑到每局有判决（PASS/FAIL/UNPLAYABLE）。注意保留短 ID↔全 ID 映射（版本后缀是环境指纹）。每局动作预算 ≤20。
3. **INC-BA-001 落账**：baseline-arms/INCIDENTS.md 报告检索子代理读到 9 局封存局机制（ls20/ft09 实质）。把 9 局的污染级如实写进 `contamination_log.jsonl`（登记是事实问题）；**主张集是否缩至 19 局是所有者的决定，标注 pending-owner-ruling，不要替他决**。

技巧要求：预检的 4 局各派一个并行 subagent 跑（互不等待，结果汇总裁决）；对 API 的间歇故障用带退避的循环推进而不是人工重试；改判文本写完后，派一个**对抗性 subagent** 只读 incidents 原文与新证据、专门试图推翻你的改判措辞，过了它再落账。

红线：封存堆 21 局 API 零接触；密钥只在 `.env`，值不进被跟踪文件。
全程自主，不停下来问。完成即提交 + PARTNER_SYNC 追加一段。
