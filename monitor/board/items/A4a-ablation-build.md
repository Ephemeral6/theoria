priority: 2
cell: A1
territory: ablation-arm
deps: none
lane: campaign

# A4a · 消融臂：只做实现（两个工人先后在整件 A4 上撞上下文墙，故拆半）

W-1611 与 W-1540 先后领走整件 A4 又交回：前者证明前提（P-18 离线标定）从未跑过，
后者读完验收门后判断一个上下文装不下。**本条只要实现，不要标定。**

刀口（DESIGN.md 若已存在则以它为准，冲突处以本条为准）：保留 DSL、对象化、
重放层 certify（廉价层全保）；砍掉全部证明义务——无 Lean、无证书、UNSAT 裸信、
玩法书定理级条目降为经验级；**其余内环与引擎调用一字不改**（差异才可归因）。
先读 `ablation-arm/STATUS.md` 与分支 `agent/a4-ablation-online` 里的抢救物。
验收：`ablation-arm/verify.sh` 绿 = 能在 A0 世界跑完一遍全环并产出与全量臂
可并排比较的账目；标定与对照留给 A4b。
