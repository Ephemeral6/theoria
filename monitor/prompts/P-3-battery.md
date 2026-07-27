# P-3 · Phase 2 指标电池 v0（上一批未落地，本批重发；材料变多了）

基准文件是 `Theoria.md`；Phase 2 一节读两遍。再读 `CLAUDE.md`。
领地：新建顶层 `battery/`。其余只读；`PARTNER_SYNC.md` 只追加；提交只 add 自己领地。

目标：五族指标（探索/计划/经济/机制/认识）定义 + 计算代码 + 首份能力谱。**夹具比上一批多了**：`cold-start-a0/`（A0 + prime 的 A0′，认识族的概念时间线/压缩收益/定理数全有真数据）、`a0-spike/`（engine-rig 的独立 A0，含 held-out 与 adapt 数据——`pipeline/adapt.py` 的检测延迟/修复成本/连带作废三个量正是「改规则适应」考题的度量，电池机制族应吸收）、`baseline-arms/` 的裸 CC 试点账本（经济族与探索族的第一份真实臂数据）。方向预注册 `PREDICTIONS.md` 只许追加。格式与 `proxy/LEDGER_FORMAT.md` 对齐（不存在则以 baseline-arms 账本为最小公分母，标注待对齐）。

技巧要求：五族并行 subagent 独立实现自测，主线只做集成与去冗余聚类；抗游戏审计单独派对抗性 subagent 逐指标现场演示刷分（刷得动又防不住→降级参考项）；全量回算挂后台循环，确定性 diff 为空才达标；区分力接口用断言把 Theoria 数据挡在门外（只准 CC vs Schema）。

红线：零 API 零模型调用；封存堆 game_id 护栏先写。全程自主，不停下来问。完成即提交 + PARTNER_SYNC 追加。
