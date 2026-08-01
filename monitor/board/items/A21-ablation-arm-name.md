priority: 2
cell: A21
territory: proxy
deps: none

# A21-ablation-arm-name · 给 ablation 臂一个记账名——三臂同帐的分母修正

`p1-same-shell` 的「三臂」分母今天只能到 2/3：ablation 臂的记录以
`arm: "theoria"` 出账（`ablation-arm/DECISIONS.md` D-AB-004，重建自
`ablcore/ledger_abl.py:9-30`），原因是 `proxy.ledger.ARMS` frozenset
没有 ablation 的名字，而加名字要动别的轨道的文件——每个臂 README 都禁。
这是词汇表缺口，不是 ablation 的错，也只有 proxy 领地能修。

做两件：

1. **proxy 侧**：`proxy/ledger.py` 的 `ARMS` 增加 `"ablation"`（或
   contracts 里既定的名字），带测试；`LEDGER_FORMAT.md` 同步一行。
2. **交接**：inbox 通知 ablation-arm 领地——D-AB-004 的前提消失，
   由其属主决定何时改用新名并在 DECISIONS.md 记 supersession
   （本件不碰 ablation-arm 的文件）。

验收：ARMS 含 ablation 名 + 测试绿；inbox 件已投。零花费。
绿了之后 p1-same-shell 的「三臂」在词汇表层面首次可能成真；
ablation 何时换名由其领地自定（D-AB-004 明文是登记而非偏好）。
