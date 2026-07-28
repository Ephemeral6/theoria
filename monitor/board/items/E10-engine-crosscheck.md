priority: 3
cell: E10
territory: engine-rig
deps: none
lane: verify

# E10-engine-crosscheck · 六引擎交叉验证：互相当对方的独立复核器

深活：六个引擎各自有断言，但没人验过它们**互相**是否一致。派六个 subagent，每个拿一个引擎的输出去用另一个引擎的方法独立复核（如零空间报的守恒律用 LP 独立验、LP 的势函数用穷举小空间验、CEGIS 前沿用暴力枚举验、死锁定理用可达图验）。目标不是再跑一遍，是找**只有交叉才能暴露的不一致**。发现即写 inbox，不改 engine-rig。零 API 钱。
