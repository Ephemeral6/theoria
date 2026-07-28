priority: 2
cell: A3
territory: baseline-arms
deps: none
lane: campaign

# A7 · 方差包络续跑：闸门已就位，把 1/4 补成 4/4

包络停在 1/4 局（ar25×haiku×3，$2.53，G4 连续死格拦停，判为真实劣化）。现在
`proxy/spend_gate.py` 已落地（共享账本、跨会话可见、fail-closed），可以安全续跑。

做：g50t / sk48 / tn36 各 ×3 重复，**每次出网前必须过 spend_gate 的 reserve/record**
（这是硬门，不是建议——INC-BA-003 的代价是一份花过钱的测量被并发永久污染）。
ar25 保留 `degraded` 标注不追跑。跑完出包络表：逐局逐重复的成功率、HTTP/动作、
墙钟、花费，并给出 Phase 4 定重复数 n 所需的方差估计。预算硬顶按 BUDGET_REPORT 的
G1，触发任一闸门即停并记录。这是主表对照列与 Phase 4 冻结的共同前置。
