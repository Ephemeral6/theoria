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

## [engine-rig] 2026-07-27T16:13:10Z phase1-INC-001
状态：切堆经用户确认后开始接触开发堆，一次 RESET 即定下四项接入核查结论：frame 是**帧列表**（RESET 返回 1 帧，64x64）——级联语义在结构上已裁决，step 必须建模"动作→帧序列"；level 是响应字段（levels_completed / win_levels，且 win_levels 7 == baseline_actions 长度 7），无需由 score 跳变推导；RESET 返回 guid 会话句柄；available_actions=[1,2,3,4,5]（该 keyboard 局无 ACTION6，与标签一致）。
阻塞：**INC-001（阻塞级）**——/api/games 列出 25 局，但开发堆 4 局中有 3 局 RESET 返回 400 "game not found"，仅 g50t-5849a774 可玩。切堆前提（25 局皆可玩）不成立，开发堆实际只有 1 局。封存堆可玩子集未知且**故意不探测**：成功的 RESET 会返回首帧，逐局探测等于把可玩的封存局全部烧掉。piles.json 保持哈希锁定未改，事件记于 incidents.jsonl，污染登记移至 contamination_log.jsonl。**封存堆零接触。**
下一步：待密钥访问范围澄清；在此期间确定性预检可仅在 g50t 上先跑。

## [engine-rig] 2026-07-27T16:35:02Z phase1-INC-002
状态：g50t 确定性预检**未通过——是无法完成**。RESET 48 次成功 4 次（间歇可用），紧随其后的 ACTION 8 次成功 0 次，一律 400 "game not found"。已逐条排除：请求体形状（同一可用窗口内试了 4 种）、会话过期（用存活 guid 调 ACTION 同样失败，错误键在 game_id 而非会话）、未关闭的 scorecard（关闭无效）。有效结论一条：两次独立 RESET 的首帧哈希完全相同（801726dc499f3f52），初始态跨会话可复现、无残留——但仅止于首帧。另记 INC-003（自身缺陷）：compare() 曾把两侧都缺哈希的错误步判为一致，导致两次均失败的运行被报成 PASS；已修（哈希须两侧俱在，且 PASS 额外要求整条序列跑完），用原数据重新评分为 INCOMPLETE 2/21。
阻塞：**INC-002（阻塞级）**——零次成功动作即无轨迹、无账本，整个在线 API 路线受阻，非仅预检。需账号侧确认游戏是否真正可运行。
下一步：等待 INC-001/002 澄清；期间可转 A0（自建世界、零 API，Theoria.md 列为第一优先）。

## [engine-rig] 2026-07-27T16:47:12Z interop-lp-certificates
状态：应 theory-compiler M8 记录中"需接入 engine-rig 的 LP 输出"的请求，engine-rig/interop/ 交付 LP 求解的 pagoda 证书（整数权重 + 每条义务自带见证，Lean 只需检查；inv_closed 覆盖全状态空间的所有跳吃实例）。**重要负面结论**：贵方 peg fixture（5 格 11011）的不可解主张经枚举确认为真（可达集最少 2 子，永不到 1），但其所写目标 `goal count(Peg, alive=true) = 1` **不存在线性 pagoda 证书**——在权重界 10/100/10000 下均不可行，而同一求解器对可证实例仍能给出证书（对照组通过），故为真实结论而非求解器局限。把目标收窄到具体格位则可证：目标格 1 与 3 有证书 w=[-1,1,0,1,-1]，格 0/2/4 无。原因是 pagoda 需对**所有**目标态同时满足 potential(g) > potential(s0)。含义：`invariant pagoda_weight [status: proven]` 在 count=1 目标下并未被 pagoda 兑现（实际是贵方 Lean 的 BFS 枚举在承担）；若要代数证明，需收窄目标（证书已就绪于 interop/certificates/）或扩展不变量语言——后者按冻结契约须记入表达力台账，不得静默扩展。此为 DECISIONS D-014 所记 pagoda 可靠但不完备的一次真实咬合。
测试：pass 161/161，skip 1（新增 interop 11 条，含证书篡改的双向负向测试）。
阻塞：无（本项）。在线 API 仍卡在 INC-002。
下一步：待 INC-001/002 澄清；cold-start-a0/ 有另一轨道未提交的在途修改，本轨道未进入以免冲突。

## [baseline-arms] 2026-07-28T00:55:00Z baseline-arms-m1-audit
状态：第 0 步审计完成。三项结论：(1) 仓库内**不存在** ADR-0014 / INC-0008 / 任何 Schema 复现战役——`Theoria.md:271` 主表里 Schema 那格仍是占位符 `⟨复现值⟩`，本轨道是这项工作的第一次开工，无重复劳动、无双权威数据风险；(2) `/arc-gateway/` 不存在，改用工单的独立记账 schema，`ledger.jsonl` 严格只含 env_step / model_call 两种形状，诊断另落 probe_log.jsonl，保证日后可逐行并入 gateway 账本；(3) 切堆已落刀且哈希未变，本轮只用开发堆 4 局，封存堆纪律写成 import 时加载 piles.json 的守卫代码，指名封存局在打开 socket 前抛错。模型矩阵探测所得（非预设）：`ANTHROPIC_API_KEY` 直连 api.anthropic.com 401，故走 `claude -p` 无头 CLI——这对「裸 Claude Code」这一列反而是保真而非将就；三档实测可用 claude-haiku-4-5-20251001 / claude-sonnet-5 / claude-opus-5，环境里四个 `ANTHROPIC_DEFAULT_*_MODEL` 别名全部指向一个 404 模型，必须写全 id。
测试：模型三档各跑通一次真实调用；封存堆守卫按前缀匹配生效。封存堆本轮触碰 0 局。
阻塞：无。
下一步：M2 裸 CC harness + 记账管线。

## [baseline-arms] 2026-07-28T00:55:00Z INC-002-独立复核（供 arc-recon 参考，未改其任何文件）
状态：**不继承 INC-002 的结论，独立复核后推翻其诊断。** INC-002 记「ACTION 0/8，整个在线 API 路线受阻」。本轨道只在开发堆上复核，试了 arc-recon 未试的四个假设：H-A 去掉版本后缀（`sk48` 而非 `sk48-d8078629`）→ **200**；H-B 只传 guid → 400 `game_id not provided`（否证）；H-C 同形状连续重试 → **200**；H-D 路径大小写 / ACTION0 → 404（否证）。H-A 与 H-C 同时成功，说明决定性因素**不是请求形状而是重试**。带线性退避重试（每步上限 8 次）对 sk48 实跑：RESET 第 4 次开窗，15 步中 11 步成功推进，guid 会话内保持有效，state=NOT_FINISHED 逐步前进。**修正诊断：400 "game <id> not found" 是瞬时故障（很可能多实例后端只有部分实例持有会话），不是权限边界、不是会话丢失；正确处置是重试。** 代价：平均 5.07 次 HTTP 调用换 1 次成功动作，这个 5× 放大必须进任何配额外推。另两条副产物：响应无 `score` 字段，计分字段是 `levels_completed` / `win_levels`；`ACTION6` 传 `data={"x","y"}` 返回 500，data 形状待定。另：arc-recon 记 sk48 RESET 0/6，本轮 sk48 成功开窗多次——可用性不是按局固定的。
测试：probe_api.py（开发堆 4 局各 2 轮）+ probe_action_variants.py（四假设）+ 重试策略确证，共 161 条 HTTP 记录落 probe_log.jsonl。
阻塞：无。在线 API 路线未被封死。
下一步：本轨道据此按 D-005 实现重试策略；INC-002 的处置归 arc-recon 自行判断，本轨道不修改其 incidents.jsonl。

## [cold-start-a0] 2026-07-28T02:10:00Z cold-start-a0-m6-report
状态：A0 冷启动六个里程碑全绿，全环第一次真实跑通——感知→引擎提案→LLM 裁决→certify 两层→plan→赢，再加一个构造性不可解变体的完整定理（Lean `#print axioms` 空表）。判决：**证活**。但最有价值的产出是一处**故意留下的漏洞**：`press_left` 未被推广到其余三个方向（证据为零，constraint 5 不许入册），因此说明书对世界的三个 (状态,动作) 对是错的，而全史重放**永远看不见**——这正是 Theoria 1.3 的 DC22 构造性盲区，在自建世界上小尺度复现，且诊断写在测量之前。能补这个洞的唯一机制（戳探）在 A0 里**无法执行**：按钮闩锁不可逆，这一关只能按一次。三条引擎级实证：zero_space 从 152 个匿名指示位里把 Button↔Door 依赖恢复成守恒律 `[（3,2）为8] + [（4,5）为5] ≡ 1 (mod 2)`，275 条转移支撑（规则挖掘只有 1 条见证）；CEGIS 单见证给出语义正确的守卫 `act==LEFT ∧ tcolor(LEFT)==7`，前沿大小 1；MDL 用脚本长度自己裁决了分割算子（色不可知连通域碎成 90 条轨迹，均色算子 3 条，6511 vs 4423 bits）。
测试：26 passed（含 4 条变异测试：故意改坏说明书必须被 certify 抓到——首跑即绿的检查器必须自证非空转）。`python run_all.py` 八步全绿约 6 秒。重放 276/276 帧、22356/22356 像素、0 异常；对地面真值 233/236 = 98.73%，held-out 3 对 0/3；变体 92/92 = 100%；Lean 两条义务公理表皆空。candidates.jsonl 29 行 + 变体 13 行，全部通过冻结 schema 校验。
阻塞：无。
下一步：本轨道工单范围内已完成。给框架的四条建议按优先级记在 A0_REPORT.md §7：(1) DSL 缺**框架公理**句型——"无规则触发则对象不变"这条 step 语义最重要的事实目前只活在注释和三个后端里，单独编译 theory.dsl 的第二个读者会得到不同的世界，这是表达力台账里最该先补的一格；(2) 概念入册的压缩账应对"责任完备的最短描述"计价而非逐对象像素基线——按现行口径 Button/Door 的账分别是 −17/−13 bit，压缩准则说拒、全帧责任制说必须收，两条框架自有准则在此打架；(3) 下一个自建世界要设计成机制可反复见证（无单向闩锁或提供复位）且至少有一条前沿可被真实动作分开，并**以修订轮数为主指标**——A0 的修订轮数是 0，那不是成绩，是内环没被跑到；(4) 接 Fast Downward 复跑 M4 确认适配器是零改动。

## [cold-start-a0] 2026-07-28T02:10:00Z 上游发现（仅记录，未修改任何上游文件）
状态：`engine-rig` 与 `theory-compiler` 全程只作库使用，**一个文件都没改**。三处发现留档：其一，`theory_compiler.parser.theory_parser._parse_func_call` 用 `r'(\w+)\(([^)]*)\)'` 匹配参数表，遇到第一个 `)` 即止，因此规则 `then` 子句里出现嵌套调用或元组时（如 `then jumped(Cart, (1, 1))`）第二个参数会被**静默**解析成畸形名 `(1, 1`，不抛错、AST 直接是错的；守卫走 `_parse_expr`（贪婪）不受影响。此为真实缺陷（DECISIONS D-A0-013），本轨道绕过而非修复，未影响任何已打 tag；任何需要在事件里放坐标的 DSL 都会中招。其二，`theory_compiler.generators.gen_lean.generate_lean` 完全忽略传入的 TheoryAST，直接 BFS 一维孔明棋并发出 `PegState`；`gen_python` 硬编码 `moved`/`teleported` 两种事件且假设每个对象类型只有一个实例。两者对 A1 彩排是对的，对任意世界不通用——本轨道复用 parser（冻结语法的可执行形态）、自写三个后端（D-A0-011），记为**覆盖面缺口而非缺陷**。其三，`mdl_segmenter` 的色不可知连通域算子在物体相邻的世界里会把它们并成一块（A0 上碎成 90 条轨迹）；本轨道按 Theoria 1.8 的"分割算子假设空间"补了均色算子并**用脚本长度裁决**，实现上只在一次调用期间重绑 `connected_components` 再还原，不落盘改动。本 sprint 进行中贵方已原生加入 `split_by_color` 开关——`pipeline/segment_operators.py` 现已探测签名优先走原生实现，本地算子保留为对 `engine-rig-m8-integration` 那一版的回退路径。
测试：见上条。
阻塞：无。
下一步：无（本条仅供两条上游轨道参考，不请求任何动作）。

## [cold-start-a0] 2026-07-27T17:15:00Z m6-独立复核
状态：对 A0_REPORT.md 的九项定量主张做了独立复核——不信任落盘 JSON，逐项重算：certify 廉价层（276 帧 / 22 356 像素 / 0 异常，内存重放一致）、两条 Lean 义务（本地 lean.exe 重跑，公理表皆空、无 sorry）、行为准确率 233/236 与 held-out 0/3（对活世界模型重算一致，3 个失配对恰为 trace_summary 登记的 3 个不可覆盖对）、变体 92/92、候选流 29+13 行重过冻结 schema 校验、plan SAT 12 步三方一致、theory.dsl 重新解析计数吻合。**九项全部确认，无一失配。**上游回归：engine-rig 161 pass / 1 skip，theory-compiler 49/49。补充一条给 engine-rig 的漂移细节（上一条只提了 split_by_color）：贵方工作树的未提交改动还包括 `fd_adapter/pddl.py` 的静态前件剪枝（接地期丢弃静态前件为假的实例，防接地爆炸）及 `search.py` 配套改动；经核对该剪枝纯属优化、不改变任何计划（applicable() 在展开期仍复查全部前件），fresh clone 在 HEAD 上可完整复现本轨道全部产物——但**这批漂移在贵方套件里零测试覆盖**（无任何测试引用 split_by_color 或 static_predicates），提交前建议补上。
测试：见上（独立重算 + 两条上游套件全绿）。
阻塞：无。
下一步：本轨道收束。六个里程碑 tag（cold-start-a0-m1-world … m6-report）均已核对指向正确的提交。

## [engine-rig] 2026-07-27T17:12:42Z a0-spike
状态：A0 冷启动在 **/a0-spike/**（新建目录；发现 cold-start-a0/ 有贵轨道未提交的在途修改，故未进入，避免冲突）跑通全环：感知→挖掘→裁决→certify→规划→赢 + 一条守恒定理。世界为自建 sokoban 变体（推箱滑**两格**），由此得到真实守恒律：箱子 (row+col) 奇偶不变。两关只差目标格：match 规划 2 步取胜（与 BFS 最优一致），mismatch 由定理一步判死、**完全不调用规划器**，两者判决均与地面真值一致。341 条转移 replay 逐条精确、每步恰一后继。
三条值得看的发现：(1) 首轮 push 规则「replay 全对但错」——单见证下守卫缺 box_beyond_free，正是 DC22 形状；改为按**情境**而非**结果**规划探索后修正（代价 341 动作）。(2) blocked 类天然是析取（墙挡 / 箱子推不动），单条合取无法覆盖，cegis_miner 正确抛 NoSeparatingGuard；改用序贯覆盖学成多条合取规则，**不动冻结语法**。(3) zero_space 返回零空间维数 2——两坐标奇偶各自守恒，比我裁决的 (row+col) 更强，已改入册：引擎纠正了裁决者。
引擎侧两项改进（engine-rig/DECISIONS D-016/D-017）：fd_adapter 改为 join 式 grounding（静态谓词早剪 + 按静态原子决定绑定序），grounding 16.4s→0.03s、求解 49s→0.05s，输出完全一致；mdl_segmenter 增加按颜色切分的分割算子（选哪个由该局说明书记录）。
**给贵轨道两条**：(a) a0-spike/theory/theory.dsl 可被贵方 parser 正常解析；(b) 但 `compress: -39B` 会被 parser 拒（int() 解析失败），而冻结契约与 Theoria.md 示例写的是 `compress: -412B` 带 B 后缀——契约与实现不一致，我这边改写为无后缀绕过，请裁定以哪边为准。
测试：engine-rig 161 pass / 1 skip；a0-spike 18 pass。
阻塞：无（本项）。在线 API 仍卡 INC-002。
下一步：视需要把 A0 的 certify 接到贵方 gen_python 生成的执行态上。

## [engine-rig] 2026-07-27T17:23:35Z a0-certify-generated
状态：A0 的 certify 已接到「由 theory.dsl 编译出的执行态」上，341 帧逐帧比对（比的是 render() 出来的帧，不是内部状态，满足全帧责任制），exact=True。预测机只此一台，符合"预测无侧门"。
**立刻抓到一个我自己的裁决错误**：blocked_wall/blocked_box 我写成 `then moved(Player, dir)`，生成的执行态照此把玩家推出棋盘；挖掘出的规则本身是对的（效果就是 (0,0)），错在我把它写进说明书时事件语汇里没有「什么都没发生」这一项。已加 `stayed(o)` 并改正。用挖掘规则重放永远发现不了这个——只有编译出的说明书才对说明书负责。
**给贵轨道一份报告**：a0-spike/GENERATOR_REPORT.md。要点——gen_python 对 A0 说明书（贵方 parser 可正常解析）**静默降级**：不认识的守卫编译成 `True`，不认识的事件编译成 `pass`。实测后果：`step(player=(0,0), "move(Player, up)")` 得到 (0,-1) 出界且不报错；`render()` 恒返回全零网格。这比崩溃更糟——certify 的全部职责就是抓「说明书与世界不符」，而静默降级会产出一个能跑能重放、但什么都不意味的 theory.py。建议：编译不了就 raise，记入表达力台账，不要近似。另附 6 条具体缺陷、2 条 parser 问题（`not <pred>` 未被解析成否定节点而是塞进 NameRef 文本；`compress: -39B` 被 int() 拒但契约与 Theoria.md 示例都带 B 后缀）、以及 A0 逼出的 3 条表达力台账项（beyond(o,dir)、一条规则只能有一个事件而推箱可见地动了两个对象、缺无操作事件）。
我这边的 pipeline/gen_exec.py 只是权宜之计（只覆盖 A0 子集，不认识就抛 UncompilableTheory），gen_python 一旦支持即可弃用。
测试：a0-spike 24 pass；engine-rig 161 pass / 1 skip。
阻塞：无（本项）。在线 API 仍卡 INC-002。

## [engine-rig] 2026-07-27T17:36:13Z a0-lean
状态：A0 的 Lean 证明已接上。artifacts/A0.lean 为 Theoria 1.10a 的正典骨架（inv_init / inv_closed / goal_break ⇒ unsolvable），纯 core Lean 4 无 Mathlib，四条定理全部通过。**三重把关**：(1) 编译通过；(2) `#print axioms unsolvable` = [propext, Quot.sound]，无 sorryAx，且补了非平凡性（Goal 可满足、Reachable 非空——否则「可达者皆非目标」是白送的）；(3) Lean 的 step 与 Python 执行态在全部 9408 个格局上逐一比对完全一致——否则就是 A2 展品：类型检查通过、对世界为假。
**接 Lean 的过程中，留出的判别测试抓到一个真错**：certify 在 1966 条转移上全绿，但把理论拿到**全部良构状态**上比对（held-out），出现 8 处不符——push2 只要求箱子**落点**空，漏了箱子**经过的那格**。关键在于：这个错在 match 关里**不可能**被发现——箱子经过的格子恒为奇宇称，而该关所有墙都在偶宇称格上，该情形不是「没见到」而是「不可达」；8 处不符全部落在从 s0 不可达的状态上，在 315 个可达状态上理论本来就精确。换言之规则作为**problem 解**是对的，作为 **domain** 是错的——正是冻结契约自己划的那条线。已加四关（每方向一关，墙放在奇宇称格上使该情形可达），证据跨关汇集，四个方向的守卫都补上 box_ahead_free，blocked_box 拆成 crossing / landing 两条合取。现在 5 关 39960 个良构状态 0 不符，代价是 1966 动作（原 341）。
**给贵轨道**：gen_lean 无法用于 A0——签名是 (ast, board_size, initial_config: list[bool], pagoda_weights: list[int])，写死了孔明棋，双对象 sokoban 无从表达。但它是**按签名硬失败**，比 gen_python 的静默降级好得多。另：本轨道用的 Lean 4.9.0 来自贵方 cold-start-a0/.toolchain/（只读调用，未改动任何文件）；若贵方删除该目录，我这边的 Lean 阶段会自动跳过而非失败。
测试：a0-spike 29 pass；engine-rig 161 pass / 1 skip。

## [cold-start-a0] 2026-07-28T04:30:00Z cold-start-a0-n1..n4（A0_REPORT §7 四条建议全做）
状态：四条全部执行，三条完成、一条一半。**(1) 框架公理进 DSL**——`/CONTRACTS/dsl_grammar_v0.1.md` 冻结不可改，故在本目录实现方言 `semantics:` 三句（`frame persist|reset` / `conflict exclusive|priority: r1 > r2 ...` / `cascade single_frame|multi_frame`），四个后端全部读它，`theory.md` 渲染成人话、`theory.lean` 头部记录、`theory.py` 带 `SEMANTICS`；正式扩展请求写在 `cold-start-a0/proposals/dsl_grammar_v0.2_semantics.md`，**请 theory-compiler 轨道过目**。关键请求：v0.2 应把这一节设为**必填**并对缺失**报错**——v0.1 解析器会静默跳过不认识的行，于是带该节的说明书在上游仍能解析、但解析成**另一个世界**，这正是要堵的洞而非优雅降级。`cascade single_frame` 同时钉死"所有守卫读前态、效果同时施加"，本轮真实踩过这个坑（press 先把按钮改成 8，door 规则再读守卫就不触发了）。**(3) 概念账改为对"责任完备"替代方案计价**——旧口径给对象记 21 bit 声明费、给替代方案记 0，修正后 Button −17→−5、Door −13→−1、Cart +2967→+2125，三者判定均为 `mandatory`（因为 `door_mirrors_switch` 这类律以**对象计数**写成，不变量语言没有像素级改写）。冲突被**收窄而非消解**：一个 275 步里只有 1 个事件的对象，在**轨迹**上确实不划算；它划算在**说明书**上，而这正是 Theoria 1.8 的原话。**(4) 接 Fast Downward——只完成一半**：适配器的 FD 代码路径已端到端验证（经 `$FAST_DOWNWARD` 发现、按 FD 命令行调用、解析 `sas_plan`、独立重接地校验、`backend` 上报，`solve()` 无需 `prefer=` 提示即选中 FD 并给出同一条 12 步最优解——"装上 FD 调用方零改动"成立）；但 FD 本体**编译不出来**，C++ 编译器三次尝试全失败（Lean 自带 clang 无标准库头 / conda m2w64-toolchain 撞 setuptools RemoveError / winlibs 直链 404 且 GitHub API 限流）。cmake、ninja 已装，downward 已 clone，只差编译器——按工单停止条件记录并等待人工介入，未无限期消耗。用的是 conformance stand-in（照 FD 协议说话、委托给自带 BFS），它**对 FD 的搜索本身一无所证**，这一点在文件、报告与测试里都写明。
测试：44 passed（原 26 + 新 18）。`python run_all.py` 与 `python -m prime.run_prime` 均从空目录可完整复现，全部工件字节稳定。
阻塞：**Fast Downward 编译器（人工介入项）**。其余无。
下一步：见下条 A0′ 结果；框架层建议已合并进 `A0_REPORT.md` §8 与 `prime/A0P_REPORT.md`。

## [cold-start-a0] 2026-07-28T04:30:00Z cold-start-a0-n2-a0prime（A0′：可逆性胜过覆盖率）
状态：**A0′ 用 47% 的状态-动作覆盖率得到 228/228 = 100% 的说明书**，A0 是 99% 覆盖率得到 233/236 = 98.73%。**决定性变量不是看到了多少，而是看到的东西能不能再看一次。** A0 的按钮是不可逆闩锁，`press_left` 只有一个见证且永远补不到第二个，constraint 5 因此逼着说明书带着一个已知的洞出厂；A0′ 换成可翻转开关后，四方向×两极性八种组合各有自己的见证，同一条推广就从"类比"变成"枚举证据"，直接入册。**这条结论比 A0_REPORT §7.2 原来的说法强，且应当影响开发堆关卡的挑选：不可逆机制会给"任何探索量能确立什么"设上限。** 另有两项：其一，**内环修复被证明可用**——往 A0′ 说明书里种一条故意错误且**重放不可见**的子句（`push_onto_crate`：小车可走上颜色 4；轨迹从未推向板条箱，故全史重放 GREEN，正是 DC22 形状），覆盖率戳探把它抓出来（该规则有 2 个触发态、无一在轨迹里 → 用说明书导航 3 步 → 先写预测 Cart→(2,4) → 执行 → 观测小车没动 → 打脸），Lean 形态**另行独立**抓到（`ArenaEscape`：step 把小车送到棋盘未列为竞技场的格子——这一条是意外收获，是遍历状态空间时掉出来的，把一个 KeyError 变成了有类型的 certify 诊断），一轮修订后准确率 0.9912→1.0000。仍未测到的是：既不逃出竞技场、也不落在未测试子句上的更隐蔽错误，以及需要多轮的修复。其二,**`mdl_segmenter` 第二个能力缺口**——它只做 t 与 t+1 的匹配，物体消失后再出现会被当成全新轨迹；A0 的门只开一次所以从未暴露，A0′ 的门反复开关，原始分割给出**五扇门**。`pipeline/reidentify.py` 按"同模板 + 生命期不相交"合并并**用脚本长度裁决**（7→3，省 48 bit；色不可知算子 68→6）。这是 Theoria 1.8 算子空间里的模板匹配，定价而非断言；**建议 engine-rig 考虑把跨消失的重认领纳入引擎能力**（本轨道未改上游任何文件）。
测试：44 passed，含 A0′ 两轮的端到端断言与 reidentify 的独立断言。
阻塞：无。
下一步：本工单及其四条后续全部完成。留给后来者的两条空白写在 `prime/A0P_REPORT.md` §5：多轮修订（"修订抖动"那一行仍然是空的）与规模（57 个可达态，Lean `decide` 在 10⁶ 上不成立）。

## [engine-rig] 2026-07-27T17:47:04Z a0-variant-injection
状态：A0 变体注入完成——把世界动力学抽成数据（Rules），每个变体只改**一条**规则，测「改一条规则多快适应回来」。四个变体全部修复到 replay-exact，且挖出的效果与注入的改动一致。
结果表（检测延迟 / 受影响定理 / 旧判决是否仍正确）：
  ghost（墙不再挡人，改 walk 守卫）    match 6 动作   任意关 6 动作   无定理受影响   仍正确
  push1（箱滑 1 格，改效果）           match 18 动作  任意关 18 动作  unsolvable_mismatch  **判决翻转**
  push3（箱滑 3 格，改效果）           match 18 动作  任意关 18 动作  unsolvable_mismatch  仍正确
  nocross（箱可穿过被挡格，改守卫）    match **341 动作内从未察觉**  任意关 6 动作  unsolvable_mismatch  仍正确
三条结论：(1) 检测延迟取决于该规则**触发频率**而非改动大小——walk 几乎每步都触发故 6 动作即败露；nocross 只在「箱被经过格挡住」时才不同，而该格局在 match 里**不可达**，于是改过的世界重放了 341 步毫无异样。(2) **看哪里决定能否察觉**：同一个 nocross 改动，把 crossing_* 关纳入后 6 动作即被抓到——与 T-9 是同一条奇偶论证的反面（那边是一关证据无法**钉住**规则，这边是无法**证伪**规则）。(3) **push1 是要害**：守恒律随之失效，被说明书证明不可能的 mismatch 关变成可解，旧理论会继续断言一个假的「不可能」。察觉预测失配本身并不告诉你某条**定理**已死；把它拎出来重审的是 `theorem unsolvable_mismatch [depends: push2]` 这条依赖声明——这正是整套架构要防的失败（自信、有据、且错误的不可能性断言），而依赖边是唯一的拦阻。
测试：a0-spike 38 pass；engine-rig 161 pass / 1 skip。

## [baseline-arms] 2026-07-28T02:10:00Z baseline-arms-m2-harness
状态：M2 达成。裸 CC harness 跑通单局单模型完整对局：RESET（带重试）→ 渲染 64x64 帧为 hex → `claude -p` 无头调用 → 解析 `ACTION n [x y]` → 执行（带重试）→ 逐步 env_step/model_call 落账。三条纪律是结构性的而非提醒式的：臂在**仓库外**的临时目录里跑（Claude Code 会向上找 CLAUDE.md，在仓库内启动会读到 Theoria.md 全部设计与切堆清单——读过理论的基线不是基线）；子进程环境删掉 ARC_API_KEY；工具全关。建 harness 过程中被两个「静默走错模型」的坑咬到，均已修并记入 DECISIONS.md D-010：(1) argv 里的多行 prompt 经 Windows claude.cmd shim 会让 `--model` 失效、静默回退到陈旧别名并 404——单行 prompt 两种传法都正常，所以这个 bug 藏到第一帧真实数据才暴露，改走 stdin；(2) 清掉 ANTHROPIC_* 别名变量会让 CLI 内部调用回退到另一个默认模型，其安全分类器把 64x64 hex 墙判成可疑内容——`--model` 已能覆盖别名，不要删。
测试：sk48 单局 5 步端到端跑通，ledger 两种记录形状 100% 合规（env_step 8 / model_call 5，零违规）。
阻塞：无。
下一步：M3 Schema 定位 + M4 试点。

## [baseline-arms] 2026-07-28T02:10:00Z baseline-arms-m3-schema-locate
状态：M3 达成，判定为「如实记录找不到」这一支。**Schema 官方 harness 代码从未发布**——`schema-harness` GitHub 组织下只有项目主页仓库本身，主页无任何代码发布承诺，没有正式论文、没有 arXiv id（唯一发表物是一篇网页 + `@misc` BibTeX）。轨迹 artifacts 倒是公开了（HF，逐局分目录，两套共 50 条覆盖全部 25 局，含成品 world_model_v*.py 与作者 notes.md），但**复现需要的是代码**。按工单停止条件 3 处置：记录缺口，继续做裸 CC，**不用替代实现冒充复现**，`Theoria.md:271` 的 `⟨复现值⟩` 保持空白。两条给 theory 侧的订正线索（本轨道不代改 Theoria.md）：规范署名是 **Zeng et al.** 不是 Feng et al.（Haiwen Feng 是末位作者）；不要编一个 arXiv id，没有可引的，正确引法是 @misc + 项目主页 URL。闸门后唯一低成本合规路径见 SCHEMA_LOCATE.md 路 A：按目录名精确只取开发堆 4 局的上游轨迹（`Theoria.md:311` 已明确许可），成本 ≈ $0。
测试：GitHub org API 与 HF 数据集元数据直查，非仅搜索摘要；98.98 / 42.83 / world_model.py / 重放检验 / RHAE 五项交叉验证身份，排除同名巧合。
阻塞：工作二（Schema 复现）合规留空，非本轨道可解。
下一步：M4 试点 + 预算闸门。

## [baseline-arms] 2026-07-28T02:10:00Z INC-BA-001 封存堆污染（需 arc-recon 处置）
状态：**M3 检索 Schema 发布物的过程本身污染了 9 局封存游戏。** 执行检索的子代理被预先给了明确的封存堆约束，也遵守了（未向本轨道转述任何机制内容），但 Schema 项目主页把游戏内容放在很靠前的位置，在它判断出页面不安全并停止阅读之前，正文已描述了若干封存局的机制：`ls20-9607627b`（该页贯穿示例，含具体转移规则）与 `ft09-0d8bbf25`（明确点名隐藏机制）属**实质泄露**；`re86`/`ka59`/`m0r0`/`dc22`/`lf52`/`sb26` 属轻微；`bp35` 可忽略。注意 `dc22-fdcac232` 是 `Theoria.md:416` 指定的图 5 案例展品。污染局限在该子代理上下文，本轨道主上下文只有「哪几局被污染」这份清单，没有机制内容；该子代理上下文已判定对封存堆工作不安全、不复用。**本轨道对封存堆的 API 调用仍为 0。** 防不住的原因是任务自带的张力：判断一个页面是否安全需要先读它，而 M3 的任务恰恰是「去找」。建议处置（归 arc-recon 与人工，本轨道不代改 piles.json / contamination_log.jsonl）：上调这 9 局的污染等级（ls20/ft09 至少到 trajectories_reviewed）；**切分不要改**（rules 第 3 条，开局后改动即事故），受影响的局单独标注为「已污染的封存局」而非搬进开发堆；考卷选点避开这 9 局。制度性后果一条：上游 Schema artifacts 是「读了就全污染」的物件，整包拉取 = 21 局全废，任何下载都必须先有一个只允许 4 个开发堆 game_id 前缀的守卫。
测试：不适用（事件登记）。
阻塞：对受影响封存局为 blocking；对本轮开发堆试点无影响。
下一步：等待 arc-recon / 人工对污染登记的处置。

## [baseline-arms] 2026-07-28T02:10:00Z baseline-arms-m4-pilot-gate
状态：M4 达成，**预算闸门：等待人工批准全量基线采集**。试点跑满开发堆 4 局 × 3 模型档位 = 12 格（另 2 格 sonnet 重跑），实际花费 **$9.84 / 109 个成功动作 / 960 次 HTTP 调用**。单价：haiku-4.5 **$0.0342/动作**（7.11 HTTP/动作，动作成功率 71.3%）、sonnet-5 **$0.1672**（10.73，53.6%）、opus-5 **$0.1459**（11.20，52.2%）。**四局全部成功开局**，包括 arc-recon 记为「RESET 全部 400」的 ar25 与 tn36——再次印证可用性是瞬时波动而非权限边界。三条反直觉但必须进外推的观察：sonnet 每动作比 opus **更贵**（失败率把有效成本推上去，虽然单次调用更便宜）；haiku 每动作只有 opus 的 23% 且成功率最高，但 output_tokens 是 opus 的 270 倍（无视「只回一行」指令）；**12 格全部 levels_completed = 0**，20 步对这些局远远不够，连第一关都没过。全量外推（开发堆 3014 个基线动作 × 三档）：S1 基线动作数上限 **$1,047 / 8.8 万次 HTTP / 并行 45 小时**；S2 双倍上限 **$2,094 / 17.5 万次 HTTP / 并行 89 小时**。只跑 haiku 单档为 $103–206。动作配额给了上下界且相差 **9.7 倍**（失败的 400 是否计入配额无从非破坏性测出）——**批准前建议先问清 ARC 侧配额口径**。Schema 复现那一半外推 **$0**，因为跑不了（见上条）。建议：砍掉 sonnet 档省 $504–1008；haiku 单档先行拿第一条完整曲线。已如实登记不可用项：sonnet-5 在本 harness 下约 40–50% 调用返回 is_error 且 result 为空（钱照扣），三个不同方向尝试后仍只有 1/4 格跑完，判为模型侧间歇故障而非 harness 缺陷，单价照实记录不粉饰；被重跑取代的 2 格在汇总里单独列出、花费计入总账，无静默截断。
测试：ledger.jsonl 两种记录形状零违规；封存堆 API 调用 0 次。
阻塞：**预算闸门——等待人工批准后方可扩大规模。** 另：开发堆 4 局污染等级应升至 trajectories_reviewed（模型已逐帧读像素并据此决策），登记归 arc-recon。
下一步：停止，等待批准。批准后按 BUDGET_REPORT.md §6 的取舍顺序执行。

## [cold-start-a0] 2026-07-28T06:10:00Z cold-start-a0-n5-fd-connected
状态：**Fast Downward 装上并接通了**（用户授权后由本轨道执行）。路线：winlibs mingw-w64 gcc 16.1.0 免安装 zip 解到 gitignore 的 `.toolchain/`，再直接用 CMake+Ninja 构建——**不能走 `build.py`**，它在 `os.name == "nt"` 下硬编码 `NMake Makefiles`（要 MSVC）；直接 `cmake -G Ninja -S src -B builds/release` 即可，产物正好落在 `driver/util.py` 期望的 `builds/release/bin/`。235/235，约 90 秒，无补丁，gcc 16 编译 FD 源码全清。结果：`a0-base` SAT/12、`a0p-base` SAT/10（两者与自带 BFS **计划逐条相同**）、`a0-no-button` **UNSAT**（"Completely explored state space — no solution!"）。**设 `FAST_DOWNWARD` 就是全部集成，调用方零改动**——这正是 A0_REPORT §7.4 要验的那句话。变体那一行最重要：FD **独立证明**了不可解，M5 的不可解定理与规划器现在是互相印证，而不是其中一个被默认采信。
测试：47 passed（含真 FD 三实例的断言，无 FD 时自动 skip）。全流水线仍从空目录字节复现；`run_all.py` / `prime.run_prime` **故意保留 `prefer="stub"`**（D-A0-021），使入库工件与本机是否装了规划器无关，FD 对照单独落在 `artifacts/fd_real.json`。
阻塞：无（原编译器阻塞已解除）。
下一步：接第二个实现立刻抓出两个缺陷，见下条。

## [cold-start-a0] 2026-07-28T06:10:00Z 接通 FD 抓出的两个缺陷（一个是我们的，一个是 engine-rig 的）
状态：**其一（本轨道的，已修）**：我们生成的 PDDL **不合标准**——域文件写 `(:types buttoncell doorcell markedcell - cell)` 却从未声明 `cell` 本身。`fd_adapter` 自带的解析器很宽容，整个 sprint 都接受了它；FD 的 translator 直接 `KeyError: 'cell'` 死掉。已在 `compile/gen_pddl_a0.py` 修（先发 `cell - object` 再发子类型），并加了断言测试。**含义比一个 bug 大：自带 stub 一直在替我们掩盖一个可移植性缺陷，今天之前本生成器产出的任何域文件都会被任何合规规划器拒绝。** 建议 engine-rig 考虑让 `pddl.py` 对"用了却未声明的父类型"报错而非静默接受——宽容的解析器会让下游误以为自己合规。
**其二（engine-rig 的，本轨道未改上游）**：`fd_adapter` 在 FD 路径上**无法表达"已证明不可解"**。自带 BFS 抛 `RuntimeError("no plan exists for …")`；FD 是 exit 12 + 不产出 plan 文件，`backends.run_fast_downward` 把它变成 `RuntimeError("Fast Downward produced no plan file (exit 12): …")`——与 FD 真崩溃时抛的**是同一种异常**。于是 FD 路径上的调用方分不清「规划器证明了无解」（constraint 6 下触发证书义务、整个 M5 由它启动）与「规划器挂了」（这是 incident）。这恰好是不可解工作存在的**唯一那个区分**，不该留给各调用点的字符串匹配。本轨道在 `certify/fd_unsat.py` 里收口（`plan_stage` 与 `fd_conformance` 共用），**exit 13（`SEARCH_UNSOLVED_INCOMPLETE`）刻意不算 UNSAT**——不完备搜索没找到不是证明，把它洗成证明正是 constraint 6 禁止的裸 UNSAT。**建议上游修法**：`solve()` 在 exit 12 时返回 `None`，或抛一个可区分的 `NoPlanExists`，与 stub 的语义对齐。
测试：`test_fd_unsat_tells_a_proof_apart_from_a_crash`、`test_generated_pddl_declares_every_type_it_uses`。
阻塞：无。
下一步：无请求；两条仅供 engine-rig 参考。

## [cold-start-a0] 2026-07-28T06:10:00Z 致 theory-compiler：`semantics:` 已被采纳，本轨道改为委托
状态：注意到贵方 parser 已实现 `semantics:`（三句、同样的封闭值域、同样"缺失即报错"，并引用 `CONTRACTS/dsl_grammar_v0.2.md` 与台账 E-03）——与 `cold-start-a0/proposals/dsl_grammar_v0.2_semantics.md` 的请求一致，**谢谢采纳**。本轨道的 `compile/dialect.py` 已改为**特征探测后委托上游**，本地实现退为回退路径（与 `mdl_segmenter` 的 `split_by_color` 同一模式），以便本目录仍能对贵方 M8 那一版运行。一处设计取舍备案：上游的拒绝是**答案**而非回退理由，故不吞掉，但会以本模块自己的 `SemanticsError` 重抛——调用方不该需要知道是两个实现里的哪一个回答的。另注意到贵方新增了 `LandmarkDecl` / `WeightsDecl` / `DomainDecl` / `VarRef`，看起来分别对应台账 E-04（板面地标）、E-05（权重向量）、E-02（`?dir` 提升）——若 `?dir` 真的落地，A0′ 那 16 条开关子句可以塌回 2 条，这是本轨道表达力台账里代价最大的一格。
测试：47 passed，委托路径与回退路径均已覆盖。
阻塞：无。
下一步：无请求。另记一条协作事实供两条轨道参考：本轮有一次 pytest 中途报 3 failed、随后同一份代码 47 passed，还有一次直接在贵方 `pretty_printer.py` 的 SyntaxError 上整体报错、几分钟后自愈——都是在读贵方**写到一半**的文件。判定方法是 stash 掉自己的 diff 重跑已提交状态。在这棵树上把一次红色直接当信号之前，值得先做这一步。

## [battery] 2026-07-28T06:40:00Z battery-v0
状态：新建顶层 `battery/`——Theoria.md Phase 2 的落地。五族 29 条指标 + 电池自身四道工序，全量回算 26 runs / 4 局开发堆 / 2 臂（`bare_cc` 账本 + A0 两个实例）。**被动仪器：只开文件，零 API、零模型调用、零网络。** 护栏先行且单独一个 commit：封存局按全 ID、去后缀短 ID、大小写全部拒绝，两堆都不属的 ID 也拒绝；另外每次加载都重算 `piles.json` 自published 的摘要，切堆漂了就拒绝打分，产物逐份带着校验过的摘要。方向预注册 `PREDICTIONS.md` 在**任何指标代码存在之前**就提交了（commit 50d144c，树里当时只有护栏和适配器），顶部有封条声明逐条写明作者当时已看过什么。
测试：61 passed。两次回算字节相同（合成夹具跑真管线——实盘账本本会话被隔壁追加了 20 行，D-B-008）。统计量手写不走 scipy，为的是跨机同位。
阻塞：无。
下一步：v1 等更多配对局；详见 `battery/STATUS.md` 七条已知弱点，W-1 是指标定义与预测出自同一人。

## [battery] 2026-07-28T06:40:00Z 致 baseline-arms 与 proxy：三条能用得上的观察（无请求，仅供参考）
状态：**其一（给 baseline-arms）**：试点账本里 **27–45% 的 `env_step` 是失败步**（HTTP 500 与 "game not found"），逐模型分别为 haiku 27% / sonnet 36% / opus 45%。这一项**完全解释**了"每次模型调用摊到的动作数"在模型阶梯上的方向——它算的是成功动作除以全部调用，与失败率相关 ρ = −0.83，于是基础设施更差的跑法看起来像计划更差。本轨道加了 `P5 step_failure_rate` 把混杂因子摆到明面，但账本健康度不归本轨道修。在失败率降下来之前，**任何从这批账本读出的行为族数字都要打折**。
**其二（给 proxy / `LEDGER_FORMAT.md`）**：`battery/INPUT_FORMAT.md` 以 Phase 2 电池读者的视角列了 5 条缺口——(1) `model_call` 行没有 `arm`，只能从同 run 的 `env_step` 回填，纯思考不动作的一局会落成 `unknown`；(2) `game_id` 在 `model_call` 上非必填，护栏因此只能靠 `env_step` 筛，理想是两类都必填、账本不必重组即可筛；(3) 成本是标量 `total_cost_usd`，没有 `price_list_version`，重算无法重新计价（Phase 1 说成本是换算不是记录，那就需要那个字段）；(4) 没有关卡边界事件，只能从 `levels_completed` 跳变推；(5) 没有独立于 `step_idx` 的回合索引，经济族按回合定义却只能拿模型调用序当回合轴。本轨道已按现状写好适配器，格式定稿时改一个文件即可。
**其三（给 arc-recon，只是个提醒）**：`CLAUDE.md` 写 `piles.json` 的 "sha256 `3feca53e…`" 读起来像文件哈希，实际是**去掉 `sha256` 字段后规范 JSON 的哈希**（文件本体是 `d3140eff…`）。切堆本身完好、自首次提交起从未改动，只是描述有歧义。共享地界，本轨道未代改，记在 `battery/DECISIONS.md` D-B-011。
测试：不适用（观察，非改动）。
阻塞：无。
下一步：无请求。

## [cold-start-a2] 2026-07-28T08:05:00Z a2-exhibit-and-loop
状态：新建顶层 `cold-start-a2/`——Phase 1 验收件 A2，按 **INC-004** 的裁决走「自建 DC22 同构世界」路线（option b，2026-07-28）。**全程零 API、零网络、零接触封存堆；同构性论证只引用 Theoria §1.3 已写下的结构描述，未读任何上游 DC22 产物，那局的 ID 本目录里一个字节都没有（`tests/test_a2.py::test_no_dc22_artifact_is_present` 按字节把关）。** 世界是 9×9 推车关：目标房间被第 5 列整列墙封死，唯一入口是传送口。流水线从全量扫描归纳出完整说明书后，人工删去 `teleport_down` 一条得到 `theory_holed.dsl`。**展品**：有洞说明书对游玩记录重放 184/184 帧、0 异常，规划器 UNSAT，Lean 4.9.0 `decide` 签下 `unsolvable` 且 `#print axioms` 为空——而世界 18 步就解出来了。比 §1.3 本身更强的一点：游玩记录是全量扫描的**前缀**（切点是唯一那次非相邻移动，从帧的几何读出），覆盖左房间 164 个可达 (状态,动作) 对里的 163 个，唯独漏掉触发被删规则的那一对。近乎穷尽的证据，洞照样在——这不是覆盖率问题。**回路**：打脸（18 步通关局，以帧交付）→ 定位（§1.4 三选一全跑：看错棋盘否、终点判断否、某步预测**是**，t=11）→ 戳探（设计 5 条、执行 4 条、预测全部先写；1 条如实记为本世界不可分辨）→ 修订 → 重证（被推翻的证书按修订后的 step 重新生成并**留作红色产物**，Lean 在 `theory.lean:769` 报 `decide proved that the proposition ... is false`；同形状的真定理接替）→ 解出。头号产物是**一对 Lean 文件**：权重表以外完全相同——同生成器、同 `decide`、同空公理表——一条对世界为假，一条为真。
测试：44 passed；`run_all.py` 约 17s 全绿，两次干净运行产物逐字节相同；六份候选流全部通过 `CONTRACTS/candidates_schema.md` 校验，`status` 恒为 `candidate`。
阻塞：无。
下一步：无请求。

## [cold-start-a2] 2026-07-28T08:05:00Z 致 theory-compiler：编译后端两处缺陷，已在本目录绕开，未代改
状态：本轨道复用了 `cold-start-a0/` 的编译后端与 certify 层（只读、未改一字；`tools/verify_readonly` 对 `cold-start-a0`/`engine-rig`/`theory-compiler`/`CONTRACTS` 四棵树共 258 个文件取哈希、跑完整条流水线、再取哈希，**0 files changed**）。在第二个世界上跑同一套仪器，暴露出两处 A0 结构上看不见的问题。**其一（真的会给错答案）**：`gen_pddl_a0._problem` 只为 `problem.arena` 里的格子发 cell 对象和邻接事实，而 `compile/problem.py::derive` 的 arena 只收地板与动态格——**静态的有色格（传送口）两边都不在**。于是 `teleport-down` 的 `?p - markedcell` 参数没有实例，动作永远 ground 不出来，规划器对一份**含有传送规则**的说明书返回 UNSAT。A0 看不见这一点：A0 的目标经门可达，没有哪条计划需要 jump 动作 ground——缺陷是潜伏的，靠运气给出了正确答案。A2 的目标只能靠传送，第一次编译控制组说明书就撞上了。本轨道的绕法只动 PDDL 一侧（`a2pipeline/compile_a2.py::pddl_addressable`：PDDL 的 cell 全集 = arena ∪ 任何守卫按颜色点名的格子；`_problem` 本来就不给 markedcell 发 `(passable ...)`，所以移动动作依然踩不上去——这些格子是**可寻址、不可占据**）；Lean 与 Python 两个形态保持未扩充的 arena，因为它们的 arena 意思是"小车可能在的状态"，而小车从不在传送口上。**其二**：`certify/lean_check.check` 用 `subprocess.run(text=True)`，即按进程 locale 解码工具链输出；Lean 的**报错**里有 U+2019 和 ⟨⟩，本机 locale 是 GBK，于是读取线程恰好在证明失败时抛 `UnicodeDecodeError`，诊断信息就此丢失。A0 从来没有过一份红色的 Lean 文件，所以碰不到；A2 有一份，而且是故意留的。本轨道自己按字节读、显式 UTF-8 解码，但**解析规则（两条公理正则与 green 判据）仍从贵方 import 而非重写**，免得两处对"什么算绿"各说各话。两处都记在 `cold-start-a2/DECISIONS.md` D-A2-006 / D-A2-007，未代改贵方文件。
测试：不适用（观察 + 本目录内的绕开）。
阻塞：无。
下一步：无请求。

## [proxy] 2026-07-28T09:20:00Z p2-double-proxy
状态：新建顶层 `proxy/`——Phase 1 的记录面。两个 HTTP 代理夹在臂与外界之间，臂各改一个环境变量、两把钥匙一把也拿不到，于是「封闭」的三条从纪律变成构造：**记录完备**（两代理把每个请求与响应全量入账）、**可复放**（帧整存并哈希，`replay.py` 按账本重演、逐步比对）、**不可绕行**（`tests/test_seal.py` 把同一个请求逐字节发两遍——直连 401、过代理 200，差别只是臂从未持有的那把钥匙）。`LEDGER_FORMAT.md` 先于代码写成并作规范：两类事件 `env_step` / `model_call`，三臂与 Phase 2 电池共用；**账本里不写一个美元数**——usage 逐字入账，成本是对哈希过的版本化价目表做换算，日后调价是重新计价而非与历史矛盾。封存堆护栏从「各调用方自觉检查」搬到臂唯一的那条通道上：直接读 `arc-recon/data/piles.json` 本体而非副本、按刀自带的摘要校验完整性、两堆之外的 id 一律拒、扫整个请求而不只是它预期的那个字段；一次拒绝记三处，因为「没试过」和「试了被拦」不能长得一样。变体层只收包裹层可证做得到的算子（禁动作/重映射/限步/观测判负/胜利加严），拒收没有构造性依据的规格；三不可解一可解——只有不可解题的考卷分不开「我没做出来」与「它做不出来」。
测试：70 passed，全离线、零 API、零网络。每条检查都配一条伪造账本、断言它变红的对照——从未见其失败的检查不构成任何东西通过了的证据。
阻塞：无。未接触 `/theory-compiler/`、`/cold-start-a0/`、`/cold-start-a2/`、`/engine-rig/`、`/baseline-arms/`、`/battery/`、`/monitor/`；`arc-recon/` 只读。
下一步：接一臂真跑（配置而非改码：`runner.run_game` 收 `arm_factory`，独立代理只需两个环境变量）；写 `LEDGER_FORMAT.md §7` 已规范但尚未实现的 v0→v1.0 提升工具，否则 `baseline-arms/ledger.jsonl` 与本账本还拼不到一起。

## [proxy] 2026-07-28T09:20:00Z 致 baseline-arms：账本格式已冻，两处拼写不同
状态：`proxy/LEDGER_FORMAT.md` v1.0 与贵方 `harness/ledger.py` 的两形态在含义上是超集关系，但拼写有两处不同，直接 concat 会坏：`frame` → `frames`（**恒为列表**——precheck 观测到单个命令返回过 7 帧，把 action→单帧写进类型的 harness 会静默丢观测）、`timestamp` → `ts`（毫秒精度）。§7 规定了 `tools/upgrade_ledger.py` 来提升旧记录并打 `lifted_from` 标记，**该工具尚未实现**，本条即是登记这个缺口。另外贵方 D-003 把诊断分到另一个文件、我这边分到同一文件的不同 `event` 值——两条路走到同一个结论（`env_step` 只有一个形状），我选同文件是为了留住 `seq` 的全序。无需贵方改动；等提升工具写好再合流。
测试：不适用（格式登记）。
阻塞：无。
下一步：无请求。
