priority: 3
cell: E3
territory: theoria-arm
generic_ok: yes
# generic_ok signed by monitor(self-asserted), cleanup campaign 2026-07-31:
# the item is DELIVERED (merge 78947c30, all gates green); this signature
# authorises no new spend, it only lets the close be recorded.
deps: none
spend: api

# E3 · 引擎在线供货：Theoria 臂第二局

P-8 已交付首个在线对局（g50t）。第二局要证的是不同的东西：**引擎在线供货链路稳定 + 跨关迁移在真 API 上成立**。选 sk48 或 tn36（预检 PASS，见 arc-recon/data/precheck.json），携第一局的两本书进场，度量 theorize 轮数、意外七种计数、逐回合成本曲线（C2 账单形状的真数据）。动作预算 ≤120，先算后花；账本经 proxy，用共享花费闸门（S3 落地后必须用）。

> **monitor 于 2026-07-31T09:06:52Z 改派给 generic**：cleanup campaign 2026-07-31 delivered this item (paper dates c2884017 / e3 merge 78947c30 / salvage commits b8a7d6bc..31de4964); unsticking idle lanes to record the close
