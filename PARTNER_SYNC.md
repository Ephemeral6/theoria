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

## [engine-rig] 2026-07-27T11:26:01Z engine-rig-m7-probe
状态：probe_frontier 完成——对手造场景（h_empty vs h_nonlethal，两者与既有证据全部一致，仅在"良性非空色"格局下分歧）计算各候选动作的划分熵，输出 UP / 1.000 bit，与手算一致，其余三个动作 0 bit。三假设情形给出 2-1 划分 0.918 bit，并可顺序戳探（观测 move 后剩两条，下一次探针再分 1 bit）。路径成本以 bits-per-cost 计入排序。probe 直接消费 cegis_miner 的前沿：D-002 里 free/in_bounds 的不可分辨，由一次进入"格内非空"格局的探针分开。
测试：pass 116/116，skip 1。
阻塞：无。
下一步：M8 集成与 schema 校验。

## [engine-rig] 2026-07-27T11:28:42Z engine-rig-m8-integration
状态：M8 达成，六个引擎端到端各跑一遍，产出 24 条候选写入单一 append-only candidates.jsonl，全文通过 schema 校验器（tools/validate_candidates.py），无崩溃、无格式违规；六种 kind 全部覆盖。确定性模式下两次运行字节级相同；重复运行只追加、不改写已有行。
测试：pass 148/148，skip 1（FD 专用）。
阻塞：无（唯一偏差为 FD 未接通、按工单允许改用桩实现，已记入 STATUS.md）。
下一步：本轨道工单范围内工作已完成。

## [theory-compiler] 2026-07-27T11:45:00Z theory-compiler-m8-a1-rehearsal
状态：M8 达成。全部 8 个里程碑完成。手写 DSL（Cart + 1D 孔明棋）→ 四种生成物（Python / Lean / Markdown / PDDL）+ playbook 解析器（含反作弊负向测试）全部通过验收。
测试：pass 49/49。
阻塞：无。
下一步：本轨道工单范围内工作已完成。与正式 A1 验收的差异：权重为手算常量（非 LP 引擎求解），Lean 证明使用 BFS 枚举可达集（非 pagoda 代数证明），后续汇合 sprint 需接入 engine-rig 的 LP 输出并重构 Lean 证明策略。

## [engine-rig] 2026-07-27T16:00:21Z engine-rig-m8-integration (artifact)
状态：M8 产出的 candidates.jsonl 已提交进仓库（engine-rig/artifacts/candidates.jsonl，24 条，六引擎六 kind 齐全）。采用确定性模式生成（冻结时间戳 + uuid5 内容哈希），保证字节稳定、重生成零 diff；日常运行仍走真实 uuid/挂钟时间并写入未跟踪的 out/。新增测试断言仓库内文件与新鲜一次确定性运行逐字节相同，防止陈旧。
测试：pass 150/150，skip 1。
阻塞：无。
下一步：本轨道工单范围内工作已完成。

## [engine-rig] 2026-07-27T16:08:52Z phase1-access-check
状态：ARC API 已接通并完成只读接入核查（base https://three.arcprize.org，X-API-Key；公开集 25 局，标签族 keyboard_click 13 / click 7 / keyboard 4 / 无标签 1；game_id 均带版本后缀；baseline_actions 长度即关卡数，全集 17135 动作）。发现一条 scorecard 语义：open 返回 card_id，但零对局的卡 retrieve/close 均 404，卡在首次对局后才落地。**切堆已落刀**（arc-recon/data/piles.json，sha256 3feca53e…41bbc19a）：开发堆 4 局（ar25/g50t/sk48/tn36，跨三个标签族），封存堆 21 局（含唯一无标签局）。切堆依据仅为目录元数据，未观察任何机制，25 局全部登记 never_audited。凭据存于 gitignore 的 .env，全流程不入任何被跟踪文件，ledger 中一律 redacted。
测试：engine-rig 150 pass / 1 skip 不变。
阻塞：无。等待切堆确认后方可开始烧动作配额（RESET 语义、单动作多帧、level 字段、确定性预检均需对局）。
下一步：确定性预检 + 级联语义裁决（仅在开发堆上）。
