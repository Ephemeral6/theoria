# P-12 · baseline-arms：包络续跑 + 账本正典迁移 + 留痕补档

基准文件是 `Theoria.md`（Phase 3 经济、1.12 主表）。开工仪式：读 `CLAUDE.md`、PARTNER_SYNC 最后十段、本领地全部文档（尤其 `BUDGET_REPORT.md` §11 的 G4 判决），跑本领地测试，绿了开工。
分支制：`agent/p12-envelope-finish` + 独立 worktree；push 分支不碰 master。
领地：`baseline-arms/`。其余只读；PARTNER_SYNC 只追加。

三件：

1. **包络续跑**（F-15 裁决执行）：g50t/sk48/tn36 按原协议（×3 重复）续跑；ar25 记 `degraded` 不追跑，包络表单独一行注明证据；预算闸门照旧硬性；若再出 G4，停下记录并在 PARTNER_SYNC 标注请监控重裁（这是唯一允许的停）。
2. **账本正典迁移**（F-16 裁决执行）：存量账本按 `proxy/LEDGER_FORMAT.md` 出迁移器转正典（原始文件不动，转换产物 + 迁移器版本入 runs/）；battery 的 INPUT_FORMAT 若有出入在 PARTNER_SYNC 向其登记。
3. **留痕补档**：本领地历史产物（试点、包络首局、schema_traces）补建 `runs/` 档案与 MANIFEST（prompt_id 用回溯标注 `retro:P-7`）——失败 run 同等归档。

红线：封存堆双零接触（API + 内容，下载守卫保持 fail-closed）；密钥只经 proxy；预算闸门优先于一切「再跑一局」。

技巧：三局包络用循环推进（跑完一局→审计 subagent 复核账本自洽→过闸门→下一局）；迁移器写完用 fuzz 循环对拍（原始 vs 迁移后逐字段）。

收工仪式：runs/ 归档；BUDGET_REPORT/TOUCHED_GAMES 续账；PARTNER_SYNC 追加；push 分支。全程自主，不停下来问。
