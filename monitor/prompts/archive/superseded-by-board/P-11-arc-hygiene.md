# P-11 · arc-recon 卫生收口：F-11 落账 + 金丝雀 + 接入核查清尾

基准文件是 `Theoria.md`（一刀切堆、一件接入核查、金丝雀重放条款）。开工仪式：读 `CLAUDE.md`、PARTNER_SYNC 最后十段、`baseline-arms/INCIDENTS.md`（INC-BA-001 全文）、monitor 页面 F-11 的裁决文本，绿了开工（本领地无测试套件，跑一遍 `arc-recon/precheck.py --help` 冒烟即可）。
分支制：`agent/p11-arc-hygiene` + 独立 worktree；push 分支不碰 master。
领地：`arc-recon/`。其余只读；PARTNER_SYNC 只追加。

三件：

1. **F-11 裁决落账**（监控代行裁决已作出，你只执行）：contamination_log 追加 9 局的知识污染登记（等级按 INC-BA-001 的自报表）；ls20/ft09 标 `quarantined_from_claims`；新增一行 incident 记录裁决依据与主张集 21→19 的后果。piles.json 哈希锁定不动。
2. **金丝雀重放机制**：每局一条固定动作序列 + 期望帧哈希，存 `data/canary.json`；跑一次开发堆 4 局作基线（每局 ≤6 动作）；写好定期重跑脚本（漂移 = incident 并冻结战役的逻辑进代码）。
3. **接入核查清尾**：速率/配额一栏用 baseline 的实测口径归档；帧缓存与释出许可条款查官网文档落一行结论；跨会话残留用金丝雀基线顺带回答。

红线：封存堆 API 零接触；动作预算全工单 ≤30。

技巧：金丝雀 4 局并行 subagent 跑；落账文本先过一个对抗性 subagent（只读证据链，试图挑出「登记与裁决不符」处）。

收工仪式：runs/ 归档（prompt_id: P-11）；README 更新；PARTNER_SYNC 追加；push 分支。全程自主，不停下来问。
