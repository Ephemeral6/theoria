priority: 2
cell: E11
territory: engine-rig
deps: none
lane: verify

# E11-engine-crosscheck-deep · 六引擎交叉复核（互当对方的检查器）

六个引擎各自有断言，但没人验过它们**互相**是否一致。派六个 subagent，每个拿一个引擎的输出用另一个引擎的方法独立复核：零空间的守恒律用 LP 独立验、LP 的势函数用小空间穷举验、CEGIS 前沿用暴力枚举验、死锁定理用可达图验、MDL 分割用重建原帧验、探针熵用暴力划分验。目标不是再跑一遍，是找**只有交叉才暴露的不一致**。发现写 inbox，不改 engine-rig。零 API 花费。
