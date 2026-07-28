# DRIFT-partner-sync-in-place-rewrite

severity: medium
dimension: 纪律漂移（append-only 文件的旧段落被就地编辑）

evidence:
- commit `63ef0bf` "baseline-arms: the variance envelope stops at 1/4, and the download guard fails closed"（2026-07-28 02:53:26 +0800），diff 对 `PARTNER_SYNC.md` 是 `+1 −1`：第 265 行区块内、已发布段落
  `## [baseline-arms] 2026-07-28T18:55:00Z 致 arc-recon / proxy：ARC 配额口径有实测答案了，失败的 400 不计费`
  的「状态：」整行被替换。
- 被删掉的原文（节选，可 `git show 63ef0bf -- PARTNER_SYNC.md` 复核）：
  「**3 个独立样本全部一致：只计成功动作，失败的 400 一次都不计**（试点 g50t×opus 14 成功/6 失败→卡记 14；包络 ar25 rep2 14/10→14；rep3 19/10→19）。……**两条限定别用过头**」
- 替换后的原文（节选）：
  「**4 个独立样本恒等于成功动作数**（……ar25 rep1 11/10→11、rep2 14/10→14、rep3 19/10→19）……**被否掉的是 §4 那条「每次 HTTP 尝试都计费」的悲观口径**……**三条限定，请勿用过头**」
- 对照检查（同一方法跑全历史）：`arc-recon/data/incidents.jsonl` 与 `arc-recon/data/contamination_log.jsonl` 的全部提交**零删除行**，append-only 守得干净。`PARTNER_SYNC.md` 全历史仅此 1 次删除。

claim: 同步板上一段已经发布、已被对方轨道可能读过的段落被就地改写——样本数从 3 改成 4、结论从「口径有实测答案」加强为「9.7 倍上界不成立」、限定从两条改成三条——而 `CLAUDE.md` 明写同步板是 append-only 状态板、「nobody replies」。改写本身是往更准的方向走（多一个样本、限定更紧），问题不在内容而在**形态**：读过旧版的轨道不会知道自己读的那版已被撤回，而修订理由与时点只存在于 git，不在板上。

suggest:
1. 判定这一次是否需要补一条 incident（本仓库对 append-only 破例的既往处置口径应保持一致）。若判为「无害的自我订正」，建议**明确写进纪律条款**：允许作者在同一提交窗口内修自己刚发的段落，超出窗口一律以新段落 supersede。
2. 更实的一条：把「旧段落零删除」做成机器检查。判据已经现成且零误报——`git log --numstat` 对 `PARTNER_SYNC.md` / `incidents.jsonl` / `PREDICTIONS.md` 的删除行数必须为 0。建议并入 `monitor/scan.py` 作为一个 probe（`append_only_integrity`），比人眼巡检可靠。
3. 板上补一段 baseline-arms 的订正说明（3→4 样本、结论加强），把撤回动作显式化。这条由监控决定是否派单，我不执行。
