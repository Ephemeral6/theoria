# R-1 · harness 回顾（第一跑）：从五轮工作里挖重复失败模式

你是回顾者，不是执行者：**全仓只读**，唯一可写处是 `monitor/inbox/`（提案箱，一事一文件，命名 `<UTC>-r1-<slug>.md`）与自己的分支。基准文件是 `Theoria.md`。
分支制：`agent/r1-retrospective` + 独立 worktree；push 分支不碰 master。

材料：全部 incidents（arc-recon 与 baseline-arms 两本）、PARTNER_SYNC 全文（45+ 段）、各领地 DECISIONS/STATUS/THEORIZE_LOG、monitor/state.json 的发现区与回路账、git log。

问题：**哪些失败在跨轨道重复出现？** 已知线索（验证并扩展，别被锚定）：误诊后又被推翻的结论出过两次（INC-002、H-A 短 ID）——初判为什么总是过早定案？「说得比证据满」被对抗复核抓过一次（P-5）——哪些已入账结论还没被复核过？契约冻结与演化的张力出现两次（kind 枚举、dsl 语法）。子代理泄露封存机制一次（INC-BA-001）——还有哪些无护栏的信息通道？

产出：每个模式一份 inbox 提案——现象（引证据）、根因假设、对规则/提示词模板/监控探针的具体修改建议、预期效果。提案是给监控裁决的，不是指令；宁可少而扎实，别凑数。另出一份 `<UTC>-r1-summary.md` 总览。

技巧：按材料分片派并行 subagent 各自挖，再合并去重；每个候选模式派一个反方 subagent 试图证明「这只是巧合不是模式」，活下来的才进提案。

收工仪式：提案入 inbox；PARTNER_SYNC 追加一段（标 [R-1]）；push 分支。全程自主，不停下来问。
