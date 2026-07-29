# P3-case-study · 案例研究集：Phase 3 结的交付物提前起草

基准 `Theoria.md`（阶段交付物条款：「Phase 3 结：开发堆案例研究（概念诞生时间线 + 死锁定理集）」；3.2 图 5/图 6 的文字本体）。素材已经够写三个深案例，不必等在线战役。
开工仪式：读 `CLAUDE.md`、四份报告（A0/A0′/A2/A3 若在）与 THEORIZE_LOG 全文、engine-rig M9 的死锁定理产出，绿了开工。
分支制：`agent/p3-case-study` + 独立 worktree；push 分支不碰 master。领地：`papers/case-studies/`（papers 下新增子目录，不动其他分支碰过的文件）。

三个案例，各 800–1500 字 + 图表数据文件（图归 figures 工单，这里出数据与文字）：

1. **一个概念的诞生**：A0 的 Button/Door 从「两个没人认领的像素」到入册——压缩账为负仍必须收的准入冲突（O-04）、逼出它的是约束 2 而非直觉。逐步引 THEORIZE_LOG 原文；
2. **可逆性发现**：A0 vs A0′ 的受控对照——99% 覆盖带三错 vs 47% 覆盖零错，含 13 条可执行探针的前后对比；从「框架预言的盲区复现」到「设计准则入册」的完整回路；
3. **一条为假的真定理**：A2 的展品与六拍修复——两层真值制度的实物演示，含 Lean 空公理集的验证细节。

红线：**每个数字每句引文指回树上的文件与行**；没发生的不写；案例之间的交叉引用用相对路径。写完派「怀疑读者」subagent 逐案例核对引用（错一处退回重写该段）。
留痕 `papers/case-studies/runs/<UTC>-p3c/`。收工：RUN_STATE + MANIFEST(prompt_id: P3-case-study) + PARTNER_SYNC + push。全程自主。
