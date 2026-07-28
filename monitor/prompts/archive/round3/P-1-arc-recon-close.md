# P-1 · arc-recon：接手在途改动，收尾并提交

基准文件是 `Theoria.md`；先读它 Phase 1 与 `CLAUDE.md`。
领地：`arc-recon/`。其余只读；`PARTNER_SYNC.md` 只追加；提交只 add 自己领地（多会话并行）。

**开工第一步是 `git diff arc-recon/`**：`precheck.py`、`incidents.jsonl`、`contamination_log.jsonl`、`recon_ledger.jsonl` 都有前一会话留下的未提交改动。你的任务是**接着完成，不是重做**——审查在途改动的意图，补全它，落账提交。

收尾清单（以在途改动实际覆盖了多少为准）：

1. INC-001/INC-002 的 superseded 条目（依据：`baseline-arms/AUDIT.md` §6 与 D-005——400 是瞬时故障，重试即过）；README 同步；
2. 确定性预检在开发堆跑到逐局有判决（PASS/FAIL/UNPLAYABLE），短 ID↔全 ID 映射入账（版本后缀是环境指纹），每局动作 ≤20；
3. INC-BA-001 的 9 局封存知识污染如实登记进 `contamination_log.jsonl`（ls20/ft09 实质、7 局轻微，来源 `baseline-arms/INCIDENTS.md`）；**主张集缩不缩到 19 局标 pending-owner-ruling，不替所有者决**。

技巧要求：预检各局派并行 subagent；间歇故障用退避循环推进；所有改判文本落账前，派一个只读旧 incident 与新证据的**对抗性 subagent** 试图推翻你的措辞，过了再提交。

红线：封存堆 API 零接触；密钥只在 `.env`。全程自主，不停下来问。完成即提交 + PARTNER_SYNC 追加。
