# P-14 · battery v1：吃下全部新材料，区分力工序第一跑

基准文件是 `Theoria.md`（Phase 2 四道工序）。开工仪式：读 `CLAUDE.md`、PARTNER_SYNC 最后十段、`battery/STATUS.md` 与 REPORT_V0、`PREDICTIONS.md`，跑 battery 测试，绿了开工。
分支制：`agent/p14-battery-v1` + 独立 worktree；push 分支不碰 master。
领地：`battery/`。其余只读；PARTNER_SYNC 只追加。注意：P-12 正在别的分支迁移 baseline 账本、P-9 在定正典守卫——**不要依赖它们的未合并产物**，以 master 上现有材料为准，接口留好对齐位。

目标：v0 → v1，三件：

1. **吃新材料**：cold-start-a2 的轨迹与修复回路账（认识族：修复回路的六拍成本正是 U4 的度量原料）、a0-spike 的 held-out 与 adapt 数据（机制族：检测延迟/修复成本/连带作废）、包络首局 ar25×haiku 的真账本（经济族 + 探索族的 degraded 案例——它对指标是好样本不是坏数据）。全量回算，REPORT_V1 落盘。
2. **区分力工序第一跑**：现在有了真对照材料——裸 CC（试点+包络）vs Theoria 离线臂（A0 系列）。逐指标算效应量；注意这还不是 Theoria.md 要求的 CC vs Schema 对照（Schema 路 A 材料未齐），如实标注口径并在指标表加一列「验证材料」。
3. **去冗余**：相关性聚类首跑，每族留代表，聚类依据入 audit/。

红线：零 API 零模型调用；封存护栏照旧；PREDICTIONS.md 只许追加（v1 新指标先预注册再回算——顺序是纪律）。

技巧：三件并行 subagent；每个新指标过一遍「怎么刷它」对抗审计；确定性 diff 循环把关。

收工仪式：runs/ 归档（prompt_id: P-14）；STATUS 更新；PARTNER_SYNC 追加；push 分支。全程自主，不停下来问。
