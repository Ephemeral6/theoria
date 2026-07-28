# P-18 · 消融臂：Theoria − 定理义务（评审口中的『活命臂』）

基准 `Theoria.md`（Phase 4「必设消融臂」：把谁都能抄的工程省从 claim 里切出去）。开工仪式：读 `CLAUDE.md`、PARTNER_SYNC 尾十段、`cold-start-a0/` 与 `cold-start-a2/` 的流水线（你的母体，只读），跑其测试绿了开工。**先出计划再动手**：把消融的精确刀口写进 `ablation-arm/DESIGN.md`（砍什么、留什么、为什么这一刀恰好分离『工程省』与『理解省』），这一步用最深的思考（ultrathink 级）——刀口切错，整个消融白跑。
分支制：`agent/p18-ablation-arm` + 独立 worktree；push 分支不碰 master。领地：新建顶层 `ablation-arm/`。

目标：实现 Theoria−定理义务臂并在离线世界上标定。

1. **刀口**（DESIGN.md 定稿后照做）：保留 DSL、对象化、重放层 certify（廉价层全保）；砍掉全部证明义务——无 Lean、无证书、UNSAT 裸信、玩法书定理级条目降为经验级。其余内环与引擎调用一字不改（差异可归因）。
2. **离线标定**：A0 与 A2 世界各跑一遍全环，与全量 Theoria 的既有结果并排：分数、重放精确度、以及**它错在哪**——A2 的假不可达定理这一臂应当照信不误（没有证明义务就没有打脸机制），把这个预期失败真实展示出来，它就是消融臂存在的意义。
3. 接口对齐 proxy 账本格式，在线就绪（但本工单零 API）。

前沿工具要求：子代理分工各持上下文（实现 / 标定 / 对抗审查三线）；**Stop-hook 式收工**——写 `ablation-arm/verify.sh`（跑两世界全环 + 断言与全量臂的差异恰为设计的刀口），不绿不许收工；测试挂后台循环；发现可复用流程沉淀成 `.claude/skills/`（只增不改）；收尾做一轮 simplify 式质量清理。

留痕：边跑边落盘，开工即建 `ablation-arm/runs/<UTC>-p18/`，每步增量写入；上下文里的信息视同不存在。
收工：RUN_STATE + MANIFEST(prompt_id: P-18) + PARTNER_SYNC + push 分支。全程自主，不停下来问。
