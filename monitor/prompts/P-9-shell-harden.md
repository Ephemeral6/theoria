# P-9 · 外壳收口：冻结打分器 + 密封红队 + 账本正典守卫

基准文件是 `Theoria.md`（Phase 1 五层 (5)、验收单、总纪律）。开工仪式：读 `CLAUDE.md`、PARTNER_SYNC 最后十段、`proxy/STATUS.md` 与 `DECISIONS.md`，跑 proxy 测试套件，绿了才开工。
分支制：`agent/p9-shell-harden` + 独立 worktree；push 分支不碰 master。
领地：`proxy/`。其余只读；PARTNER_SYNC 只追加。

四件收口：

1. **冻结打分器**：接入并冻结（版本 + 哈希入 run.json）；逐局跑完即打分入库，与 scorecard 对账，不等 = incident 自动落账。吸收 baseline 的实测口径：失败 400 不计费、`total_actions` = 成功动作数。
2. **密封红队复测**：派独立红队 subagent 写攻击集——绕代理出网、臂进程摸密钥、短 ID/大小写/变体后缀混护栏、伪造 scorecard——密封测试全挡住才算绿；攻击集本身入 tests 常驻。
3. **账本正典守卫**（F-16 裁决执行）：proxy 拒收非正典字段；给 baseline-arms 提供正典迁移器接口文档（迁移本体归 P-12）。
4. **复放抽检**：包络首局（ar25×haiku）的账本迁入正典后做逐比特复放抽检——Phase 1 验收单那行的第一个真实数据点。

技巧：建造与攻击分离（红队独立上下文）；fuzz 循环跑护栏；对账器边界用 battery 作者视角的 subagent 审一遍字段。

收工仪式：runs/ 归档（MANIFEST 含 prompt_id: P-9）；STATUS 更新；PARTNER_SYNC 追加；push 分支。验收是合同不许降线。全程自主，不停下来问。
