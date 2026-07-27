# PARTNER_SYNC

追加式状态板。各轨道只写自己的段落。

## [engine-rig] 2026-07-27T10:55:01Z engine-rig-m1-fixtures
状态：三个合成 fixture(Cart / Pair-Flip / 4格孔明棋)的确定性生成脚本完成，同 seed 两次运行字节级相同。
测试：pass 17/17（tests/test_fixtures.py）。
阻塞：无。
下一步：mdl_segmenter（M2）。

## [engine-rig] 2026-07-27T11:00:09Z engine-rig-m2-mdl
状态：mdl_segmenter 完成——连通域提案 + 以比特为代价的二分图匹配 + 事件叙述（move/appear/vanish/recolor）；Cart 掩码逐帧与地面真值一致，编辑脚本 826 bit vs 逐像素基线 2888 bit（0.286）。
测试：pass 31/31（fixtures 17 + mdl 14）。
阻塞：无。
下一步：cegis_miner（M3）。

## [engine-rig] 2026-07-27T11:08:15Z engine-rig-m3-cegis
状态：cegis_miner 完成——反例引导综合出 push（守卫 act==?dir ∧ free(strip(?dir))，cov 41/41，四方向提升为一条参数化规则）与 teleport（守卫 at(0,0)，效果 move to (8,8)，cov 1/1）；九条地面规则守卫互斥且覆盖全部 49 条转移（约束 9 的微缩演练）。不可分辨的守卫（free/in_bounds）作为前沿全部保留，不做点猜测。
测试：pass 50/50（fixtures 17 + mdl 14 + cegis 19）。
阻塞：无。
下一步：zero_space（M4）。

## [engine-rig] 2026-07-27T11:12:26Z engine-rig-m4-zerospace
状态：zero_space 完成——(cell,colour) 指示特征 16 位，对状态差分在 GF(2) 上求零空间（差分秩 7，零空间维 9），规范化后得 8 条编码律 + 唯一一条世界律 (#R) mod 2 = 0，与地面真值一致。等价性用子空间恒等式判定（(#Blue) mod 2 亦通过），非字符串匹配。
测试：pass 65/65（+ zero_space 15）。
阻塞：无。
下一步：lp_potential（M5）。

## [engine-rig] 2026-07-27T11:17:08Z engine-rig-m5-lp
状态：lp_potential 完成——LP 解出 pagoda 权重 w=(-1,1,0,1)，对不可解配置 1110 给出证书（三条件 inv_init/inv_closed/goal_break 全部以精确有理数复核通过，约束覆盖全状态空间的所有跳吃实例），并与枚举结果交叉验证；对可解配置 1101 LP 不可行（可靠性）；同一权重导出的可采纳启发在所有可达状态上下界均不超过真实最短路。已把 pagoda 的不完备性（0111 不可解但无线性证书）写成测试而非掩盖。
测试：pass 81/81（+ lp 16）。
阻塞：无。
下一步：fd_adapter（M6）。

## [engine-rig] 2026-07-27T11:21:34Z engine-rig-m6-fd
状态：fd_adapter 完成，但 **FD 未接通，已用桩替代**（两次尝试均失败：PATH/环境变量/常见安装位置均无；pip 上不存在 downward / fast-downward 发行版，FD 是需源码编译的 C++ 项目，超出本 sprint 离线约束）。桩为 grounded-STRIPS 广度优先搜索，与 FD 的 astar(blind()) 同为单位代价最优，接口一致（solve(domain, problem)），payload 记录 backend 字段。最小 gripper 实例求得计划长度 5，与手工验证最优解一致，且由独立校验器与穷举（深度≤4 无解）两条独立路径复核。
测试：pass 97/97，skip 1（FD 专用测试，装上即自动生效）。
阻塞：无（FD 缺失已按工单允许的桩方案处理并记入 STATUS.md）。
下一步：probe_frontier（M7）。
