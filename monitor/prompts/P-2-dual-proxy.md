# P-2 · 双代理：把「封闭系统」从纪律变成构造（上一批未落地，本批重发）

基准文件是 `Theoria.md`；先读它 Phase 1「自下而上五层」(1)(2)(3)(4) 与验收单，再读 `CLAUDE.md`。
领地：新建顶层 `proxy/`。其余只读；`PARTNER_SYNC.md` 只追加；提交只 add 自己领地。

目标不变：环境代理（三臂只改 base URL；`ARC_API_KEY` 只在代理内注入；全量入账；**封存堆护栏在代理层强制拒绝**，白名单数据源 `arc-recon/data/piles.json`——短 ID 也要能匹配，baseline-arms 已证明 API 接受去后缀短 ID，护栏若只匹配全 ID 就是筛子）；模型代理（usage 逐字入账、价目表版本化）；统一账本格式 `LEDGER_FORMAT.md` 先行——**注意 `baseline-arms/harness/ledger.py` 已经在产真账本，你的格式要么兼容它要么给出迁移器**；密封测试、分数对账器、变体注入层起架。

验收：mock 下一臂经双代理跑通假局、账本可复放、密封测试绿、护栏测试对全 ID 与短 ID 的封存局请求都拒绝并记录。

技巧要求：建造与攻击分离——红队 subagent 独立写密封攻击（绕代理出网、臂内摸密钥、短 ID/大小写变体混护栏），全挡住才算绿；mock 重放用随机动作序列循环 fuzz；格式定稿前派一个 subagent 以 Phase 2 电池作者视角审字段。

红线：零真 API；密钥值不进被跟踪文件。全程自主，不停下来问。完成即提交 + PARTNER_SYNC 追加。
