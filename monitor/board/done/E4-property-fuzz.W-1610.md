priority: 4
cell: E1
territory: fuzzlab
deps: none

# E4 · 性质测试战役：500 个随机世界轰炸六引擎

hypothesis 或自写生成器驱动，参数化生成确定性网格世界（seed 全记录）。逐引擎 ≥3 条不变量：mdl_segmenter 分割覆盖全帧且脚本可逆放回原帧；cegis_miner 前沿内每个守卫与全部证据一致、前沿外无一致守卫；zero_space 每条律在全轨迹守恒；lp_potential 证书三条件独立复核恒过、可采纳启发恒 ≤ 真实距离（小空间 BFS 验证）；fd_adapter 返回的计划合法且最优（对拍）；probe_frontier 分裂熵与暴力枚举一致。失败案例最小化后归档（失败是战利品），**不修 engine-rig**——bug 写 fuzzlab/BUGS.md 并 PARTNER_SYNC 知会。目标 ≥500 个世界过全套，seed 表可复演。
