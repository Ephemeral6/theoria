"""The audit specification — Theoria.md read as a checklist.

Every item here cites the clause of `Theoria.md` it comes from. Nothing in this
file is invented requirement: if a row has no clause reference, it does not
belong here.

`status` is either a literal verdict or the name of a probe computed by
`scan.py` against the working tree. Literal verdicts are judgements and carry a
`note` saying on what evidence they were made; probe-backed rows re-derive
themselves every time the monitor runs.

Vocabulary:
  green    the clause is satisfied and the evidence is on disk
  partial  some of the clause is satisfied; the note says which part is not
  blocked  work exists but cannot proceed until something else moves
  missing  no artefact exists for this clause
  risk     an artefact exists but contradicts the baseline document
"""

# --------------------------------------------------------------------------
# Phase gates — Theoria.md 第二部分
# --------------------------------------------------------------------------

PHASES = [
    {
        "id": "p1",
        "name": "Phase 1 · 封闭系统",
        "clause": "Theoria.md §2 Phase 1",
        "gate": "全绿才准烧游戏钱",
        "items": [
            {
                "id": "p1-proxy-env",
                "label": "环境代理（透明 HTTP 代理，三臂只改 base URL）",
                "clause": "Phase 1 · 自下而上五层 (1)",
                "status": "green",
                "note": "proxy/ 已落地（env_proxy + guard + ledger + runner + replay + "
                        "mock 测试），密钥只在代理内注入，封存护栏在代理层拒绝（含短 ID）。"
                        "监控下轮独立复跑其密封测试。",
                "blocks": ["p1-seal-test", "p1-same-shell", "p1-replay-audit"],
            },
            {
                "id": "p1-proxy-model",
                "label": "模型代理（provider usage 逐字入账）",
                "clause": "Phase 1 · 自下而上五层 (3)",
                "status": "green",
                "note": "proxy/model_proxy.py + pricing/ 版本化价目表落地；baseline 的 "
                        "usage 已逐字入账。C2 的仪表存在了；约束 8 从此可测。",
                "blocks": ["c2"],
            },
            {
                "id": "p1-variant",
                "label": "变体注入层（包裹合法集 + 构造性依据）",
                "clause": "Phase 1 · 自下而上五层 (2)",
                "status": "partial",
                "note": "proxy/variants.py 起架（包裹合法集）。构造性依据登记与"
                        "考卷出题流程未接。",
            },
            {
                "id": "p1-runner",
                "label": "runner 与账本（env_step / model_call 两类事件）",
                "clause": "Phase 1 · 自下而上五层 (4)",
                "status": "green",
                "note": "proxy/runner.py + LEDGER_FORMAT.md + replay.py 落地。"
                        "F-16 拼写分歧已裁决以 proxy 为正典，baseline 账本待迁移。",
            },
            {
                "id": "p1-scorer",
                "label": "冻结打分器接入 + 账本分数与 scorecard 对账",
                "clause": "Phase 1 · 自下而上五层 (5)、验收单",
                "status": "partial",
                "note": "proxy/reconcile.py 对账器落地，baseline 用它实测出配额口径"
                        "（失败 400 不计费，4 样本恒等）。冻结打分器本体未接 → P-9。",
            },
            {
                "id": "p1-determinism",
                "label": "确定性预检全绿",
                "clause": "Phase 1 验收单",
                "status": "green",
                "note": "开发堆 4 局全部 PASS（重试包络盖过 1–3 分钟的波浪式瞬时故障；"
                        "每局 ≤20 动作）。INC-001/002 正式改判（INC-001b/002a/005）。",
                "probe": "determinism_state",
            },
            {
                "id": "p1-access",
                "label": "接入核查各项已入账",
                "clause": "Phase 1 · 一件接入核查",
                "status": "partial",
                "note": "已结：级联语义（frame 是帧列表）、level 为响应字段、guid、动作空间、"
                        "首帧跨会话可复现、金丝雀基线；**帧缓存与释出许可条款已由 OPS-B 查实**"
                        "（browser-ops/TERMS.md §2）：本地缓存/落盘是官方设计的一部分，无需额外"
                        "许可；**再释出需书面许可且默认禁止**（ToS 原文 without our express prior "
                        "written permission）。未结：全量跨会话残留、速率配额的官方口径。"
            },
            {
                "id": "p1-cascade",
                "label": "级联语义已裁决",
                "clause": "Phase 1 · 一件轨迹作业",
                "status": "partial",
                "note": "结构上已裁决：API 返回帧列表，step 必须建模『动作→帧序列』。"
                        "但『它是否真的会超过 1 帧』仍未观测；"
                        "而 A0 的 D-A0-004 反向选了『一动作一帧』，两者需要合流。",
            },
            {
                "id": "p1-cut",
                "label": "切堆清单已提交并哈希",
                "clause": "Phase 1 · 一刀切堆",
                "status": "green",
                "note": "piles.json 哈希锁定，API 层零接触；INC-001 已改判（开发堆 4 局可玩）；"
                        "F-11 已落账：claim_set.json 为 19，ls20/ft09 隔离，9 局登记在册。",
                "probe": "pile_integrity",
            },
            {
                "id": "p1-a0",
                "label": "A0 冷启动 spike（自建世界，第一优先）",
                "clause": "Phase 1 · 三件离线验收",
                "status": "green",
                "note": "全环冷启动跑通：感知→挖掘→裁决→四形态→certify 双层→plan→赢，"
                        "外加 no-button 变体的 Lean 不可解证书。A0『证活』。"
                        "留下的洞（press 方向泛化不可证、零可执行探针）见 F-05/F-09。",
                "probe": "a0_state",
            },
            {
                "id": "p1-a1",
                "label": "A1 孔明棋：LP 解出 pagoda → Lean 验封闭引理",
                "clause": "Phase 1 · 三件离线验收",
                "status": "green",
                "note": "真 A1 达成并经对抗式复核 CONFIRMED：LP 权重经证书文件过数据边界，"
                        "Lean 势函数归纳、空公理集。复核揪出的使能条件缺口已修；"
                        "权重手抄限制登记 E-06 → P-10。",
                "probe": "a1_state",
            },
            {
                "id": "p1-a2",
                "label": "A2 DC22 重放：造出『类型检查通过、对世界为假』的定理",
                "clause": "Phase 1 · 三件离线验收；INC-004",
                "status": "green",
                "note": "cold-start-a2 完成：假定理展品 + 打脸→修订→重证全回路，"
                        "A2_REPORT 在树上；顺带报出两条编译器缺陷 → P-10。",
            },
            {
                "id": "p1-engines",
                "label": "引擎架冒烟（LP / CEGIS / FD 各过一例）",
                "clause": "Phase 1 验收单",
                "status": "green",
                "note": "LP / CEGIS / FD 三例俱过。FD 24.06+ 已真接入（P-13），三级梯子"
                        "stub-bfs / fd-optimal / fd-satisficing；`.toolchain/` 按设计不入库，"
                        "未装机器上退回 BFS 桩并跳过 3 个测试，属预期而非缺陷。",
            },
            {
                "id": "p1-seal-test",
                "label": "密封测试（臂内无凭据；绕开双代理的出网必须失败）",
                "clause": "Phase 1 验收单",
                "status": "partial",
                "note": "proxy/tests 自带密封与护栏测试；监控尚未独立复跑，"
                        "红队攻击面（绕代理出网、臂内摸密钥）未验 → P-9。"
                        "凭据卫生干净：密钥只在 .env（本监视器每轮复验）。",
                "probe": "credential_hygiene",
            },
            {
                "id": "p1-replay-audit",
                "label": "复放抽检 2 局，环境侧逐比特一致",
                "clause": "Phase 1 验收单",
                "status": "partial",
                "note": "proxy/replay.py 就位；对真在线局账本的 2 局抽检待包络数据"
                        "迁入正典格式后执行 → P-9。",
            },
            {
                "id": "p1-same-shell",
                "label": "三臂经双代理落同一账本、打分器通吃",
                "clause": "Phase 1 验收单、第二部分总纪律",
                "status": "partial",
                "note": "同壳的物理载体（双代理）已在：裸 CC 臂真跑过（试点+包络首局）。"
                        "Schema 臂 = 路 A 上游轨迹直读（F-13 裁决）。"
                        "**Theoria 臂是三臂中唯一还不存在的** → P-8，当前关键路径。",
            },
        ],
    },
    {
        "id": "p2",
        "name": "Phase 2 · 指标电池",
        "clause": "Theoria.md §2 Phase 2",
        "gate": "只依赖『账本同格式』与『切堆已提交』，可与 A1/A2 并行",
        "items": [
            {
                "id": "p2-battery",
                "label": "候选指标族五族（探索/计划/经济/机制/认识）",
                "clause": "Phase 2 · 候选指标族",
                "status": "green",
                "note": "battery v0 落地：五族指标 + METRICS.md + 首份 REPORT_V0，"
                        "夹具 = A0 / A0′ / 裸 CC 试点账本。",
            },
            {
                "id": "p2-audit",
                "label": "电池四道工序（区分力 / 方向预注册 / 去冗余 / 抗游戏审计）",
                "clause": "Phase 2 · 电池自身要先受审",
                "status": "partial",
                "note": "PREDICTIONS.md（预注册）与 audit/ 在树上；区分力工序仍等 "
                        "Schema 路 A 材料与更多 CC 轨迹。",
            },
            {
                "id": "p2-material",
                "label": "材料：CC 基线轨迹 / Schema 复现桶 / 上游 artifacts（限开发堆）",
                "clause": "Phase 2 · 材料",
                "status": "partial",
                "note": "裸 CC 开发堆轨迹开始产生（sk48 大量、g50t 少量，见 "
                        "baseline-arms/TOUCHED_GAMES.md）；Theoria 侧有 A0/A0′ 离线轨迹。"
                        "Schema 复现桶不可能（GAP-1），替代是路 A：上游释出的开发堆 "
                        "4 局轨迹直读（Theoria.md:311 许可），尚未拉取。",
            },
        ],
    },
    {
        "id": "p3",
        "name": "Phase 3 · 框架迭代（开发堆）",
        "clause": "Theoria.md §2 Phase 3",
        "gate": "Phase 1 全绿才准进",
        "items": [
            {
                "id": "p3-scoreboard",
                "label": "记分板 = 电池 v0 + 七种意外计数 + 证明义务通过率 + theorize 轮数",
                "clause": "Phase 3 · 记分板",
                "status": "missing",
                "note": "七种意外目前在任何代码里都没有被计数。"
                        "A0 的 THEORIZE_LOG 手写记录了 2 次廉价层迭代 —— 这是"
                        "『重放失配』计数的雏形，但没有机器读得出的形态。",
            },
            {
                "id": "p3-prompt-hygiene",
                "label": "提示词只在自建世界族迭代；游戏 ID 永不进模型上下文",
                "clause": "Phase 3 · 过拟合四条通道",
                "status": "partial",
                "note": "A0 自建世界这条防线已经立起来了（且被真用了）。"
                        "但『提示词 diff 审查』与『游戏 ID 匿名化』没有机制，只有意图。",
            },
            {
                "id": "p3-expressivity",
                "label": "表达力台账（哪局哪条规则逼 DSL 扩一格）",
                "clause": "Phase 3 失败分类学 · 表达力不够；1.8 诚实条款",
                "status": "partial",
                "note": "A0 已产出五条真实条目（E-01..E-05），但它们埋在 "
                        "THEORIZE_LOG.md 里。Theoria.md 要求这是一份公开台账 —— "
                        "应提升为独立的被跟踪文件。",
            },
            {
                "id": "p3-gate-exception",
                "label": "【例外登记】Phase 1 未全绿即启动了 Phase 3 的花费",
                "clause": "Theoria.md:305「全绿才准烧游戏钱」；OPS-A DRIFT 2026-07-28",
                "status": "risk",
                "note": "如实登记，不追认合规。事实：p3-envelope 已实花 $2.53 跑 "
                        "ar25×haiku×3，而 Phase 1 当时 16 项中 6 项绿。**例外依据**："
                        "方差包络是 Phase 4 定重复数 n 的前置，且花费受预算闸门硬约束"
                        "（G4 实际开火并拦停在 1/4 局）。**代价**：这批数据是在并发负载"
                        "下测得的，单价不可与试点直接比较（INC-BA-003）。"
                        "**规矩**：此后任何跨门花费必须先在此登记一条，再动手。",
            },
            {
                "id": "p3-envelope",
                "label": "对照两臂在开发堆各跑 2–3 局，方差包络冻结",
                "clause": "Phase 3 · 经济",
                "status": "partial",
                "note": "ar25×haiku×3 已跑并被预算闸门 G4（连续死格，真实劣化）拦停，"
                        "1/4 局，$2.53。F-15 裁决：ar25 记 degraded 不追，"
                        "其余 3 局继续 → P-12。",
            },
            {
                "id": "p3-campaign",
                "label": "迭代战役：Theoria 臂在开发堆迭代至退出条件",
                "clause": "Phase 3 · 一次迭代的形状 / 退出条件",
                "status": "missing",
                "note": "整个 Phase 3 的主体。退出条件（U3 达成 ≥k 局 + 分数落 Δ 内 + "
                        "账单形状可见，或预算 B 顶到）里的 k/Δ/B 也还没定。",
            },
        ],
    },
    {
        "id": "p4",
        "name": "Phase 4 · 确证（封存堆）",
        "clause": "Theoria.md §2 Phase 4",
        "gate": "冻结清单首局开跑前提交，全部哈希",
        "items": [
            {
                "id": "p4-freeze",
                "label": "冻结清单（内环代码/DSL/生成器/提示词/引擎/戳探/规划器/电池/变体库/统计规则/claim/预算/n）",
                "clause": "Phase 4 · 冻结清单",
                "status": "missing",
                "note": "十三项里目前只有『引擎清单与版本』接近可冻结。",
            },
            {
                "id": "p4-ablation",
                "label": "必设消融臂：Theoria − 定理义务",
                "clause": "Phase 4 · 必设消融臂",
                "status": "missing",
                "note": "Theoria.md 称它是『活命臂』—— 把谁都能抄的工程省从 claim 里切出去。"
                        "没有它，主表的每一个数字都会被『你只是发了 diff』一拳打回。",
            },
            {
                "id": "p4-pending",
                "label": "冻结前待定五项",
                "clause": "Phase 4 · 冻结前待定五项",
                "status": "partial",
                "note": "已定：公开集 N=25、开发堆 4 局。"
                        "未定：模型配对版本串、预算 B 与 Δ/k/m/n、目标会议与死线。",
            },
            {
                "id": "p4-campaign",
                "label": "封存战役：三臂 + 消融臂在封存堆跑完主表",
                "clause": "Phase 4 · 封存战役怎么跑",
                "status": "missing",
                "note": "全项目的确证主体。逐局单元 = 三臂各 n 局 + 消融臂，"
                        "逐局跑完即打分入库。前提是 Phase 1 全绿与冻结清单提交。",
            },
            {
                "id": "p4-exam",
                "label": "考卷子集：不可解变体 + 改规则适应 + 分层移交",
                "clause": "Phase 4 · 考卷的时序死结",
                "status": "missing",
                "note": "m 局在主表跑完之后才允许研究并构造变体；分层移交可随主表同跑。",
            },
            {
                "id": "p4-release",
                "label": "裁决与释出：电池全量回算、预注册对照裁决、释出清单、主论文",
                "clause": "Phase 4 · 裁决与释出 / 阶段交付物",
                "status": "missing",
                "note": "含三级止损交付：Phase 1 结 workshop 文、Phase 3 结案例研究、"
                        "Phase 4 结主论文。",
            },
        ],
    },
]

# 总进度权重 —— 判断值，依据是 Theoria.md 四段的工作量与花费分布：
# Phase 1 是地基（离线件 + 外壳），Phase 3 是「迭代到出结果为止」的主烧钱段，
# Phase 4 是确证战役与论文。改这里就是改总进度的定义，改动要有理由。
PHASE_WEIGHTS = {"p1": 0.30, "p2": 0.12, "p3": 0.30, "p4": 0.28}

# 状态折算：green 全额，partial 半额，risk/blocked 按其中真实完成的部分打折。
STATUS_SCORE = {"green": 1.0, "partial": 0.5, "risk": 0.25,
                "blocked": 0.15, "missing": 0.0}

# --------------------------------------------------------------------------
# 车间引擎清单 — Theoria.md 1.10(b) 的八道工序
# --------------------------------------------------------------------------

ENGINES = [
    {"step": "分割·追踪·事件叙述", "engine": "最小编辑脚本搜索 (MDL)",
     "module": "engine-rig/engines/mdl_segmenter", "status": "green",
     "note": "A0 上真跑了：算子空间扩到两个，由脚本比特自己选出 uniform_color（4423 vs 6511 bit）。"},
    {"step": "规则挖掘", "engine": "CEGIS / 版本空间",
     "module": "engine-rig/engines/cegis_miner", "status": "green",
     "note": "前沿真的被交出来并被逐个裁决（A0 的 R-01/R-02 各留下一条『证据无法决定』的记录）。"},
    {"step": "守恒律 / 奇偶", "engine": "零空间计算 (ℚ / GF(2))",
     "module": "engine-rig/engines/zero_space", "status": "green",
     "note": "A0 上交出了本项目至今最漂亮的一条结果：door_latch —— 引擎在 152 个匿名指示位上"
             "把『门存在 iff 按钮未按』当作守恒律算了出来，275 条转移全支持。"},
    {"step": "势函数 + 启发", "engine": "线性规划",
     "module": "engine-rig/engines/lp_potential", "status": "green",
     "note": "pagoda 权重解得出、证书三条件精确有理数复核通过；不完备性写成了测试而非藏起来。"},
    {"step": "兜底归纳不变量", "engine": "IC3 / PDR",
     "module": "engine-rig (M9)", "status": "green",
     "note": "M9 落地：归纳不变量三件套 + 独立检查器复核；peg 0111（LP 不完备例）"
             "拿到非线性证书 —— 这道工序存在的全部理由已兑现。"},
    {"step": "规划", "engine": "Fast Downward（不自研）",
     "module": "engine-rig/engines/fd_adapter", "status": "partial",
     "note": "接口就位，后端是 BFS 桩。单位代价下长度最优，所以 A0 这种小世界够用；"
             "但三档阶梯的后两档（A*+可采纳启发、地标分段）都还不存在。"},
    {"step": "死锁刻画", "engine": "定理机器局部化 + trap 学习",
     "module": "engine-rig (M9)", "status": "green",
     "note": "M9 落地：条件化迷你不可解定理带证书，同一定理接进规划器作剪枝，"
             "节点数下降有前后对比。C1 的日常供给线通了。"},
    {"step": "探索 / 戳探", "engine": "前沿主动学习",
     "module": "engine-rig/engines/probe_frontier", "status": "green",
     "note": "M9 起探针经规划器定价（到达计划计入成本，unreachable 有裁决）；"
             "A0′ 实证 13 条可执行探针。约束 7 的落点齐了。"},
    {"step": "证明", "engine": "Lean 4 + 决策程序",
     "module": "theory-compiler/lean, cold-start-a0/compile", "status": "partial",
     "note": "工具链已钉版本并本地就位。但生成器分叉了：theory-compiler 的 gen_lean 完全忽略"
             "自己的 AST 参数（D-A0-011），A0 只好另写一套。约束 1『同源多形态』"
             "目前有两个源。"},
]

# --------------------------------------------------------------------------
# 十条强制约束 — Theoria.md 1.10(e)
# --------------------------------------------------------------------------

CONSTRAINTS = [
    {"n": 1, "text": "理论必须可执行——同源多形态（Lean + Python + PDDL + 渲染）",
     "status": "partial",
     "note": "四形态都有代码，但有两套生成器（A0 一套、theory-compiler 一套），"
             "且只有 gen_markdown 是真正 AST 通用的。同源二字目前打折。"},
    {"n": 2, "text": "规划前全史重放——双重对账（转移重放 + 渲染一致性，全帧责任制）",
     "status": "partial",
     "note": "A0 上真的生效过，而且是**它把 Button 和 Door 逼进词汇表的**："
             "两个像素没人认领 → 廉价层在 frame 0 就失败。这是约束 2 在野外的第一次"
             "真实咬合。但 certify 目录尚未落盘。"},
    {"n": 3, "text": "行动唯一通道；预测失误即弃计划",
     "status": "missing", "note": "无 runner、无执行环，尚未成为可检查的事实。"},
    {"n": 4, "text": "唯一写入点：LLM 只许改两本书；引擎只进候选箱；生成物禁止手改",
     "status": "partial",
     "note": "候选箱纪律良好（append-only，status 恒为 candidate，有校验器）。"
             "但 A0 的表达力条目 E-03 记录：帧公理写在 theory.dsl 的注释里、"
             "硬编码在各后端中 —— **step 最重要的语义事实不在唯一写入点管辖内**。"},
    {"n": 5, "text": "无证据/无收益不入册",
     "status": "risk",
     "note": "A0 第一次冷启动就撞出框架自身的内部冲突（O-04）："
             "Button 与 Door 的压缩账目是**负的**（−17 / −13 bit），按约束 5 应当拒绝；"
             "按约束 2 全帧责任制又必须接受。两条准入准则互相矛盾，"
             "目前的处理是『照收并把负数如实写进说明书』。**Theoria.md 需要为此裁决。**"},
    {"n": 6, "text": "全称断言必须带证明；裸 UNSAT 禁止",
     "status": "partial", "note": "机制在（LP 证书 + Lean），但尚未在任何一局上端到端跑完。"},
    {"n": 7, "text": "定理未经戳探不得定案",
     "status": "risk",
     "note": "A0 上零条可执行探针，press_is_direction_free 就此永远停在 probe: pending —— "
             "而这恰恰是 DC22 型『漏写规则』的实名复现。约束 7 在设计上正确，"
             "在第一次实战中**没有可执行的落点**。"},
    {"n": 8, "text": "无意外则无模型调用；执行、校验与引擎全程零调用",
     "status": "missing",
     "note": "模型代理不存在 = 没有任何东西在数模型调用。这条约束目前不可证伪。"},
    {"n": 9, "text": "转移无歧义是定理：每个(状态,动作)恰一后继",
     "status": "partial",
     "note": "engine-rig 在 fixture 上、A0 在三个 track 上都报告了 mutually_exclusive=true；"
             "但这是引擎的运行时检查，不是 Lean 的证明义务。"},
    {"n": 10, "text": "玩法书禁存字面解：句型仅 排序/剪枝/启发/分解",
     "status": "green",
     "note": "playbook 解析器带负向测试（playbook_violation.dsl），"
             "反作弊是语法级的 —— 这条是十条里落实得最干净的。"},
]

# --------------------------------------------------------------------------
# 监视器自己的发现 — 不在任何 incidents.jsonl 里
# --------------------------------------------------------------------------

FINDINGS = [
    {
        "id": "F-11",
        "severity": "blocking",
        "title": "INC-BA-001：9 局封存局知识污染【已裁决·监控代行】",
        "body": "baseline-arms 的 M3（定位 Schema 官方发布物）把公网检索派给了子代理并"
                "预先立了封存堆约束。子代理守住了『不向主上下文转述机制』，但它自己在"
                "止读之前已读到若干封存局的机制描述：`ls20-9607627b` 与 `ft09-0d8bbf25` "
                "**实质泄露**（含具体转移规则），另 7 局轻微（含 dc22）。"
                "本监视器的封存堆检查只看 API 请求体，**这类知识污染它构造上抓不到**。\n\n"
                "污染目前被隔离在那个子代理的已终止上下文里，主上下文只有清单。"
                "但 Phase 4 的封存主张以『没见过』为前提，这两局的『没见过』已经打了折。",
        "action": "【已裁决·监控代行 2026-07-28】取两案合并的保守解：9 局全部如实登记入 "
                  "contamination_log；ls20/ft09 隔离出封存主张集（21→19），预注册说明；"
                  "轻微 7 局保留在主张集但统计裁决时做敏感性分析。依据：Phase 4 封存主张"
                  "以未见为前提，实质泄露不可修复，轻微泄露（动作数级）可用敏感性分析"
                  "兜住而不牺牲样本量。落账派下一批提示词执行。",
    },
    {
        "id": "F-12",
        "severity": "high",
        "title": "A0′：可逆性 > 覆盖率【已裁决·监控代行：写入基准文件】",
        "body": "A0′（cold-start-a0/prime）的对照实验：A0 看到 99% 的状态-动作对，"
                "说明书仍带三处错；A0′ 只看 47%，说明书 100% 准确、13 条可执行探针、"
                "零未测规则。变量不是看了多少，是**看到的东西能否再看一次**——"
                "不可逆机关（闩锁）把任何探索量都封了顶。\n\n"
                "这直接影响 Theoria.md 的三处：开发堆选局准则（优先可逆机制多的局）、"
                "变体设计（『改规则适应题』应含可逆性维度）、以及 1.8 对探索目的的表述。",
        "action": "【已裁决·监控代行 2026-07-28】采纳。Theoria.md 三处增补：开发堆选局"
                  "优先可逆机制、变体/改规则考题含可逆性维度、1.8 探索目的补一句"
                  "『看什么能再看一次』。依据：A0 与 A0′ 的对照是本仓库目前证据力最强的"
                  "受控实验。修订派下一批提示词执行（基准文件条款级增补，留 diff 审查）。",
    },
    {
        "id": "F-13",
        "severity": "high",
        "title": "GAP-1：Schema 复现不可能【已裁决·监控代行：采纳路 A】",
        "body": "官方 harness 代码从未发布（组织下只有主页仓库），无正式论文、无 arXiv。"
                "baseline-arms 按停止条件处置：不用替代实现冒充复现，主表 ⟨复现值⟩ 合规"
                "留空。可行的替代是路 A：只取上游释出的**开发堆 4 局**轨迹直读"
                "（Theoria.md:311 明确许可）——能喂电池和对照，但『复现口径』这个词"
                "得从主表里改掉。顺带：规范署名是 Zeng et al. 而非 Feng et al.。",
        "action": "【已裁决·监控代行 2026-07-28】采纳路 A：主表 Schema 行改『上游开发堆"
                  "轨迹直读』口径、复现值合规留空、署名订正为 Zeng et al.；消融臂升为"
                  "不可裁减。依据：Theoria.md:311 已预授权上游 artifacts 的开发堆子集；"
                  "用替代实现冒充复现违背同壳纪律。修订派下一批提示词执行。",
    },
    {
        "id": "F-14",
        "severity": "high",
        "title": "CONTRACTS 的 kind 枚举被冻结条款卡住 M9 新引擎【已裁决·监控代行：升 v0.2】",
        "body": "candidates_schema.md v0.1 冻结时列死了六种 kind；M9 的 deadlock_carver 与 "
                "ic3_pdr 产出新类型候选，写不进合法流。engine-rig 已在 PARTNER_SYNC 挂出"
                "『frozen engine enum flagged for v0.2』。冻结条款的本意是防单边篡改，"
                "不是防两轨道共识演化。\n\n"
                "【裁决】升 candidates_schema v0.2：仅做**加法**（新增 kind 枚举值 + 可选"
                "字段），既有六 kind 的字段一个不动；v0.1 校验器保留，v0.2 校验器新增；"
                "两轨道各自在 PARTNER_SYNC 签认后生效。dsl_grammar 的 v0.2（semantics: 等）"
                "同窗口一并定稿。",
        "action": "P-10 执行：theory-compiler 起草，engine-rig 以 PARTNER_SYNC 段落会签。",
    },
    {
        "id": "F-15",
        "severity": "medium",
        "title": "方差包络在 ar25×haiku 上被 G4 拦停：真实劣化【已裁决·监控代行】",
        "body": "动作成功率 0.713→0.595、HTTP/动作 7.11 起跳——不是预算噪声，是模型在该局"
                "上真实退化（连续死格）。闸门按设计开火，这本身是 harness 的胜利。\n\n"
                "【裁决】ar25 记 degraded（含证据引用），不追跑不换模型硬磨；其余 3 局"
                "（g50t/sk48/tn36）按原协议续跑；包络冻结时 ar25 一行标注 degraded 并给"
                "敏感性说明。若 3 局中再有 G4，升级回监控重裁。",
        "action": "P-12 执行。",
    },
    {
        "id": "F-16",
        "severity": "medium",
        "title": "两套账本拼写分歧（proxy vs baseline-arms）【已裁决·监控代行：proxy 为正典】",
        "body": "proxy 落地 LEDGER_FORMAT.md 时发现 baseline-arms 既有账本的字段拼写与其"
                "有差异（PARTNER_SYNC 已互相登记）。三臂同账本格式是 Phase 1 总纪律，"
                "分歧不能留到电池回算时爆。\n\n"
                "【裁决】proxy/LEDGER_FORMAT.md 为正典；baseline-arms 出迁移器把存量账本"
                "转正典格式（原始文件保留不动，转换产物入 runs/ 归档）；battery 的 "
                "INPUT_FORMAT 对齐正典。",
        "action": "P-12（迁移器）+ P-9（正典守卫：proxy 拒收非正典字段）。",
    },
    {
        "id": "F-17",
        "severity": "high",
        "title": "工具的失败状态被当成世界的性质：340 处判据点扫出 48 处不安全"
                 "【已裁决·监控代行：五件上板】",
        "body": "RES-3 的三路只读普查（报告在 engine-rig/runs/20260729T000000Z-"
                "E11-engine-crosscheck-deep/SURVEY-*.md）扫约 340 处判据点，判不安全 48 处。"
                "**它们几乎全部偏向好消息**，这才是这条finding的要害——不是随机的错，"
                "是有方向的错。四个家族：退出码当证明（p13_fd_dividend.py:129 裸 "
                "returncode==12，而正确谓词 backends.proves_unsolvable 就在它已经 import 的"
                "模块里）、缺省值当成立（worldgen/core/truth.py:279 的 .get('holds', True)，"
                "35 份基准真值里 13 份因此报『不变量全部成立』）、崩溃当发现"
                "（theoria-arm/inner/plan.py:172 吞异常后仍宣布『穷举了整个可达集』——"
                "**崩得越多，健康证明越干净**）、读不开当干净（release/check_redlines.py:207 "
                "让封存红线报无发现，而同包 enumerate.py:220 对同一情形判 needs_human）。\n\n"
                "**目前没有已发表结论被推翻，但有已发表数字依赖读者重新推导**："
                "lp_potential 的 29.2% 不完备率成立，是因为复核员自己去取了 HiGHS 的 status"
                "（639 例沉默里 638 例是 status 2）——引擎自己把 status 1/2/3/4 塌成了同一个 "
                "None。方法不健全而结论当前为真，两者必须分开说。",
        "action": "【已裁决·监控代行 2026-07-29】五件上板，全部要求带负样本："
                  "S23-unreadable-is-not-clean（p1，动的是封存红线闸门，含 RES-4 报的 "
                  "arc-recon/contamination.py:338 退出码只反映 sha256）、"
                  "V19-unverified-is-not-true、E14-crash-is-not-a-finding、"
                  "E15-solver-status-bit、P14-honesty-section（写进论文，不藏进 limitations）。"
                  "C10 改形：从『定正典』改为『采纳已有的 backends.proves_unsolvable』——"
                  "新写会产生第二条正典，而两条正典正是这件工单要治的病。"
                  "cold-start-a0/ 的同族缺陷只登记进 PARTNER_SYNC，不动手（非本轨道领地）。",
    },
    {
        "id": "F-01",
        "severity": "info",
        "title": "【已裁决 2026-07-28：出路 (b)】A2 与切堆纪律的冲突",
        "body": "Phase 1 验收单要求 A2：把上游那个漏了传送规则的 DC22 模型移植进 DSL。"
                "但 `dc22-fdcac232` 在封存堆的 21 局里，而 CLAUDE.md 与 Theoria.md 都明写"
                "禁止读封存局的上游释出 artifacts —— A2 的**全部内容**就是读它。\n\n"
                "更要命的是：Theoria.md §1.3 自己就把 DC22 的机制写了出来（『漏了一条传送规则』），"
                "§3.2 还把它列为图 5 的案例。**这局在切堆之前就已经被基准文件烧掉了**，"
                "而 piles.json 仍把它登记为 never_audited。\n\n"
                "这不是执行失误，是基准文件内部的矛盾，必须由文件作者裁决。三个出路："
                "(a) 把 dc22 移出封存堆并在污染登记里如实记为『设计文档已披露机制』；"
                "(b) A2 改用一个自建的 DC22 同构世界（A0 已经证明自建世界这条路走得通）；"
                "(c) 承认 A2 无法在保持封存的前提下完成，删掉它并说明理由。",
        "action": "已裁决：出路 (b)。授权与红线见 arc-recon/data/incidents.jsonl 的 INC-004，"
                  "dc22 污染级已更正为 design_document_disclosed。提示词 P-6 可派工，"
                  "落地目录 cold-start-a2/。",
    },
    {
        "id": "F-02",
        "severity": "info",
        "title": "【已解决】INC-001/002 正式改判，确定性预检开发堆 4 局全 PASS",
        "body": "【2026-07-28 更新：原为阻塞级，现降为高。】baseline-arms 的假设排查"
                "找到了 arc-recon 未试的变量：**去掉版本后缀的短 ID**（`sk48` 而非 "
                "`sk48-d8078629`）返回 200；同形状请求重试也间歇 200。结论已上 "
                "PARTNER_SYNC，工作已提交。\n\n"
                "仍未清偿的两件：(1) `arc-recon/data/incidents.jsonl` 与 README "
                "还停在『全线受阻』，INC-001/INC-002 需要带证据的 superseded 条目；"
                "(2) 确定性预检还没在新策略下重跑过 —— Phase 1 验收单那一行仍是空的。\n\n"
                "一个要留神的张力：Theoria.md 把 game_id 的版本后缀当**环境版本指纹**。"
                "如果全面改用短 ID 通信，指纹就丢了 —— 预检与账本需要同时记录短 ID 请求"
                "与目录里的全 ID 映射，否则金丝雀重放失去锚点。",
        "action": "已完成：INC-001b/002a/005 落账；根因是 1–3 分钟波浪式瞬时故障"
                  "（多实例后端）；短 ID 的 H-A 结论后来也被订正——重试包络才是"
                  "真正的解。留此条作记录。",
    },
    {
        "id": "F-03",
        "severity": "info",
        "title": "【已解决】battery v0 落地，Phase 2 从零到首份能力谱",
        "body": "Theoria.md 明写 Phase 2『只依赖账本同格式与切堆已提交两项，可与 A1/A2 并行』，"
                "且『全程用既有轨迹，零新增游戏开销』。所有人都在等 API，而这一段不需要 API。\n\n"
                "但它的前提有一个没被检查过的洞：Phase 2 的**材料**（CC 基线轨迹、Schema 复现桶、"
                "上游 artifacts）一条都不在手。所以它并不像基准文件说的那样免费 —— "
                "得先有轨迹。这个依赖 Theoria.md 没有显式写出。",
        "action": "先做能做的：指标定义 + 计算代码 + 逐指标方向预注册，可以用 A0 轨迹当夹具先跑通。"
                  "轨迹采集另立一件。",
    },
    {
        "id": "F-04",
        "severity": "high",
        "title": "约束 5 与约束 2 在第一次冷启动上就互相矛盾",
        "body": "A0 的 O-04：Button 与 Door 的压缩账目是负的（−17 / −13 bit）。"
                "约束 5『无收益不入册』要求拒绝；约束 2『全帧责任制』要求接受"
                "（否则两个像素永远没人认领，廉价层在 frame 0 就失败）。\n\n"
                "A0 的处理是对的 —— 照收，并把负数如实写进 theory.dsl，不粉饰。"
                "但这是把矛盾**记录**下来，不是**解决**它。THEORIZE_LOG 的诊断我认为是准确的："
                "压缩账目在比较错误的替代方案 —— 『把像素编辑编码进去』不是真正的替代，"
                "『永远不解释这个格子』才是，而后者在这套记账法里根本没有价格。",
        "action": "Theoria.md 1.8『概念是一次压缩动作』需要补一句：概念的压缩账目以"
                  "『不解释该像素』为基准，而不解释是无限代价。这是基准文件的修订，不是代码的。",
    },
    {
        "id": "F-05",
        "severity": "low",
        "title": "【大半解决】约束 7 的落点：A0′ 已产出 13 条可执行探针",
        "body": "A0 首跑零可执行探针，约束 7 空转（原文见下段存档）。A0′ 在可逆世界上"
                "产出 13 条可执行探针、清空全部未测规则 —— probe 机器得到了真实锻炼，"
                "根因确认是 A0 世界的不可逆性而非机器本身（并入 F-12）。"
                "仍值得做的残件：engine-rig 侧把 hypothetical 探针接上规划器"
                "（『到达分歧态 = 一个规划问题』），P-4 覆盖。",
        "action": "P-4 第三件。",
    },
    {
        "id": "F-05-archive",
        "severity": "low",
        "title": "（F-05 原文存档）A0 首跑产出零条可执行探针",
        "body": "probe_frontier 算法本身是对的，A0 上它诚实地报告了『本世界无实验可分』（P-02）"
                "和『可分但只在假设层』（P-01/P-03）。问题在于第二类："
                "能分开假设的配置，世界从未到达过，而说明书也没说能开到那里去。\n\n"
                "后果是 `press_is_direction_free` 永远停在 probe: pending，"
                "而这正是 Theoria.md 1.3 描述的 DC22 形状 —— 一条**漏写**而非写错的规则，"
                "重放永远抓不到，且让模型里的世界变小。**框架预言的失败模式在第一次冷启动上"
                "就精确复现了，但抓它的工具没能开火。**",
        "action": "把假设层探针接上规划器：『把世界开到那个配置』本身就是一个规划问题"
                  "（Theoria.md 1.10b 探索一行原话：『到达分歧态 = 一个规划问题』）。"
                  "目前 probe_frontier 与 fd_adapter 之间没有这条连线。",
    },
    {
        "id": "F-06",
        "severity": "high",
        "title": "生成器分叉升级：gen_python 会把编译不了的守卫静默替换成 True",
        "body": "a0-spike/GENERATOR_REPORT.md（engine-rig 轨道写给 theory-compiler 的"
                "缺陷报告）：`generate_python` 对不认识的谓词/事件静默产出 `True`（守卫）"
                "或 `pass`（效果）——生成的 theory.py 能跑、能重放、**毫无意义**，"
                "而 certify 会照常给它打绿。这比崩溃糟：它废掉的正是它喂的那道检查。"
                "报告建议的规则：**拒绝而不是近似**——超出支持子集就 raise，"
                "编译不了的理论是表达力台账的一条发现，不是可以糊弄过去的东西。\n\n"
                "加上 D-A0-011（gen_lean 无视 AST）与新到的 dsl v0.2 `semantics:` 提案"
                "（cold-start-a0/proposals/，E-03 帧公理的正式句型），"
                "theory-compiler 的汇合 sprint 输入已经齐了。",
        "action": "全部并入 P-5：refuse 语义、AST 通用化、消费 LP 证书、裁决 v0.2 提案。",
    },
    {
        "id": "F-06-archive",
        "severity": "low",
        "title": "（F-06 原文存档）两套 Lean 生成器，约束 1『同源』出现分叉",
        "body": "theory_compiler.generators.gen_lean.generate_lean 完全忽略它的 TheoryAST 参数，"
                "直接 BFS 一维孔明棋并输出 PegState（A0 的 D-A0-011 记录）。"
                "它对 A1 彩排是正确的，对任何别的世界结构上不适用。"
                "A0 因此另写了 cold-start-a0/compile/gen_lean_a0.py。\n\n"
                "现在有两个 Lean 源。约束 1 说『证明者、执行器、规划器、人，读的是同一本书』。",
        "action": "汇合 sprint：把 A0 的 AST 通用后端回灌 theory-compiler，或明确宣布 A0 的那套是正典。"
                  "注意这跨轨道，需要 PARTNER_SYNC 协调而不是直接改别人的目录。",
    },
    {
        "id": "F-07",
        "severity": "info",
        "title": "【已解决】PARTNER_SYNC 停摆 —— 已补齐并提交",
        "body": "本监视器首次扫描时（2026-07-28 00:4x）同步板停在 16:35Z 的 INC-002，"
                "此后的整个 A0 sprint、A1 桥、API 重试实验全部未上板未提交。"
                "首次报告后数小时内：A0 的 M4/M5/M6 逐里程碑提交、PARTNER_SYNC 补到 "
                "19 段（含 INC-002 推翻与 A0 收官）。通道恢复。",
        "action": "无。保留此条作记录：监视器的 sync 时效检查继续每次运行。",
    },
    {
        "id": "F-08",
        "severity": "info",
        "title": "【已解决】M9 补齐八道工序：死锁刻画 + IC3/PDR + 探针定价",
        "body": "engine-rig 的六个引擎对应 Theoria.md 1.10(b) 表格的六行，"
                "但那张表有八行。缺的两道不是边角：\n\n"
                "IC3/PDR 是『LP/零空间够不着的形状』的唯一兜底，而 lp_potential 的不完备性"
                "是已知且已在 fixture 上实测到的（peg 0111）。\n\n"
                "死锁刻画是 Theoria.md 1.9 让试金石机器『从周日考试变成日常上班』的全部机制，"
                "也是 C1 的主要证据来源 —— 整关不可解在野外罕见，死角天天有。",
        "action": "两道都是 Phase 1『引擎架就位』的一部分。死锁刻画优先级更高（它供给 C1）。",
    },
    {
        "id": "F-09",
        "severity": "info",
        "title": "【已解决】A0 收官落盘 —— 全环冷启动跑通，这是赌注的第一次兑付",
        "body": "首次扫描时 THEORIZE_LOG 记载超前于磁盘；数小时后全部落盘并提交："
                "certify 双层绿（276 帧重放 0 异常、Lean 编译无 sorry、公理表干净）、"
                "plan SAT 12 步、执行赢、no-button 变体 UNSAT→Lean 证书、"
                "A0_REPORT 对真值 233/236。Theoria.md 说 A0『一周内证活或证死』——"
                "**证活了**，且它留下的洞（press 方向泛化永不可证）恰是框架预言的 "
                "DC22 盲区的微缩复现，是论文素材而非缺陷。",
        "action": "无。A0 剩余价值在报告里，等 Phase 1 结的 workshop 单元收割。",
    },
    {
        "id": "F-10",
        "severity": "info",
        "title": "凭据卫生干净，封存堆零接触 —— 两条硬纪律都守住了",
        "body": "全仓扫描（跳过 .git / 工具链）确认 ARC_API_KEY 的值只出现在 .env，"
                "且 .env 被 gitignore。所有账本里的 X-API-Key 都是 <redacted>。\n\n"
                "封存堆 21 局中，没有任何一局的 game_id 出现在 baseline-arms/probe_log.jsonl 的"
                "请求体里；recon_ledger 里出现的封存 ID 全部来自 /api/games 目录列表，"
                "属于元数据，不是对局。**INC-001 当时拒绝逐局探测可玩性的那个判断是对的**，"
                "它保住了封存堆。",
        "action": "无。本监视器每次运行都会重跑这两项检查。",
    },
]

# --------------------------------------------------------------------------
# Claim 菜单 — Theoria.md Phase 3
# --------------------------------------------------------------------------

CLAIMS = [
    {"id": "C1", "role": "主骨", "text": "理解座次：同壳同打分器下，Theoria 是唯一稳定达到 U3/U4 的框架",
     "status": "missing", "note": "需要三臂 + 打分器 + 死锁定理供给。三者皆无。"},
    {"id": "C2", "role": "签名证据", "text": "账单形状：前重后轻、随理论收敛趋零 vs Schema 平坦",
     "status": "blocked", "note": "度量它的模型代理不存在。这是最容易被忽略的关键路径。"},
    {"id": "C3", "role": "条件性", "text": "迁移：携两本书跨关，第二关边际成本 ≪",
     "status": "partial", "note": "A0 的 R-02 已经在为它铺路 —— 选 tcolor==3 而非 at(6,3)，"
                                  "理由正是『domain 带得走、problem 带不走』。这是 C3 的第一块砖。"},
    {"id": "C4", "role": "主骨", "text": "考卷与电池：三类判决题 + held-out + 分层移交 + 改规则适应",
     "status": "missing", "note": "变体注入层与电池都不存在。"},
    {"id": "C5", "role": "背景数字", "text": "成本量级：总账 10⁸ → 10⁶",
     "status": "blocked", "note": "同 C2，需要模型代理。"},
]

# --------------------------------------------------------------------------
# 架构地图 — Theoria.md 1.10 的装置全图，逐件标注现状
# --------------------------------------------------------------------------

ARCHITECTURE = [
    {"group": "外壳（三臂同壳）", "clause": "1.10(c) / Phase 1 五层",
     "items": [
         {"label": "环境代理", "status": "green", "tip": "proxy/ 落地：注入、护栏、全量入账"},
         {"label": "模型代理", "status": "green", "tip": "model_proxy + 版本化价目表；C2 仪表就位"},
         {"label": "变体注入层", "status": "partial", "tip": "variants.py 起架；构造性依据登记未接"},
         {"label": "runner + 账本", "status": "green", "tip": "runner + LEDGER_FORMAT + replay；拼写正典化中"},
         {"label": "冻结打分器", "status": "partial", "tip": "reconcile.py 对账器已实测配额口径；打分器本体 → P-9"},
     ]},
    {"group": "内环五拍", "clause": "1.10(d)",
     "items": [
         {"label": "theorize", "status": "partial", "tip": "A0 上真跑通：28 候选逐条裁决入册，全程留痕"},
         {"label": "certify", "status": "green", "tip": "A0/A0′/A2 双层全绿；Lean 空公理集"},
         {"label": "probe", "status": "green", "tip": "A0′ 13 条可执行探针 + M9 规划器定价"},
         {"label": "plan", "status": "partial", "tip": "A0/A2 均 plan 达成；FD 本体仍是 BFS 桩"},
         {"label": "commit", "status": "partial", "tip": "离线世界已走通整段执行+批改；在线 commit 等 Theoria 臂"},
     ]},
    {"group": "两本手写物", "clause": "1.10(a)",
     "items": [
         {"label": "theory.dsl 说明书", "status": "partial", "tip": "A0 的 rev 3 在树上：7 规则 2 不变量 1 待戳探定理"},
         {"label": "playbook.dsl 玩法书", "status": "partial", "tip": "语法+解析器+反作弊负向测试就位；尚无真实内容"},
     ]},
    {"group": "四种生成物", "clause": "约束 1 同源多形态",
     "items": [
         {"label": "theory.py 执行", "status": "partial", "tip": "A0 后端已写；theory-compiler 版特化于 peg"},
         {"label": "theory.lean 证明", "status": "partial", "tip": "两套生成器分叉（F-06）→ T-06"},
         {"label": "theory.pddl 规划", "status": "partial", "tip": "A0 与 compiler 各有一套"},
         {"label": "theory.md 渲染", "status": "green", "tip": "gen_markdown 是唯一 AST 通用的后端，被 A0 原样复用"},
     ]},
    {"group": "车间八工序", "clause": "1.10(b)",
     "items": [
         {"label": "MDL 分割", "status": "green", "tip": "A0 上算子空间二选一，由脚本比特裁决"},
         {"label": "CEGIS 挖掘", "status": "green", "tip": "前沿完整交出，A0 逐守卫裁决"},
         {"label": "零空间", "status": "green", "tip": "door_latch：匿名比特里挖出按钮-门守恒律"},
         {"label": "LP 势函数", "status": "green", "tip": "pagoda 证书 + 可采纳启发，同源"},
         {"label": "IC3/PDR", "status": "missing", "tip": "整道缺席 → T-05"},
         {"label": "规划 FD", "status": "partial", "tip": "BFS 桩替位；FD 未装"},
         {"label": "死锁刻画", "status": "missing", "tip": "整道缺席；C1 的供给 → T-05"},
         {"label": "前沿戳探", "status": "partial", "tip": "A0′ 已产 13 条可执行探针；到达规划连线仍缺 → P-4"},
         {"label": "Lean 证明", "status": "partial", "tip": "工具链就位；生成器分叉"},
     ]},
    {"group": "三臂", "clause": "1.12 主表",
     "items": [
         {"label": "裸 Claude Code", "status": "partial", "tip": "harness+记账+试点已跑（sk48/g50t）；战役未开 → P-7"},
         {"label": "Schema（上游轨迹）", "status": "risk", "tip": "GAP-1：复现不可能，改路 A 上游轨迹直读；主表口径待所有者定（F-13）"},
         {"label": "Theoria 臂", "status": "missing", "tip": "离线件全部证活（A0/A0′/A1/A2）；在线臂 = 当前关键路径 → P-8"},
     ]},
    {"group": "三件离线验收", "clause": "Phase 1",
     "items": [
         {"label": "A0 冷启动", "status": "green", "tip": "全环跑通并提交：certify 双层绿、plan SAT、赢、不可解证书"},
         {"label": "A1 孔明棋", "status": "green", "tip": "真 A1：证书过数据边界，空公理集，对抗复核 CONFIRMED"},
         {"label": "A2 DC22", "status": "green", "tip": "cold-start-a2：假定理展品 + 修复回路完整"},
     ]},
]

# --------------------------------------------------------------------------
# 实验 → 框架迭代回路 — 研究的主环（Theoria.md Phase 3「一次迭代的形状」）
#
# 用户定义的研究流程：跑实验 → 实验暴露问题 → 定位到框架哪一层 → 修框架 →
# 复跑。组件建设只是让实验能跑起来的前置；监视器的主视角是这条回路。
# 每行 fix 的 status：landed 已回灌 / dispatched 修复中（已派工）/
# ruled 已裁决待派工 / open 未修。
# --------------------------------------------------------------------------

ITERATION_DOCTRINE = (
    "研究的主环不是把组件清单建完，而是：实验暴露问题 → 问题定位到框架的某一层 → "
    "修框架 → 复跑验证。Theoria.md Phase 3 的『一次迭代的形状』与失败分类学就是"
    "这条环的条款化（只改一件事、变更日志、最小验证单元复跑、对照记分板留或滚）。"
    "下表是到目前为止每一次真实的回灌记账——组件进度只是它的脚手架。"
)

ITERATION_LOOP = [
    {
        "experiment": "A0 冷启动（cold-start-a0）",
        "status": "green",
        "summary": "全环跑通：certify 双层绿、plan SAT、赢、不可解证书；对真值 233/236。",
        "problems": [
            {"problem": "O-04：Button/Door 压缩账为负仍必须入册——约束 5 与约束 2 正面冲突",
             "cls": "概念不成形", "fix_in": "基准文件 1.8（压缩账的对照基准）",
             "status": "landed",
             "via": "commit 7cc02a9『price the concept account against a legal "
                    "alternative』：账目改为对照『合法替代方案』计价，冲突消解"},
            {"problem": "E-03：帧公理只能写在注释里，step 最重要的语义事实不在 DSL",
             "cls": "表达力不够", "fix_in": "DSL 语法（CONTRACTS，theory-compiler 辖）",
             "status": "dispatched",
             "via": "v0.2 `semantics:` 正式提案已提交（proposals/）+ A0 侧句型已落地"
                    "（commit 440e633）；裁决派 P-5"},
            {"problem": "R-05 + 零可执行探针：不可逆闩锁使漏写规则永不可证——DC22 盲区实名复现",
             "cls": "戳探设计差", "fix_in": "世界/选局设计准则 + 探针机器",
             "status": "landed",
             "via": "触发了 A0′ 对照实验，问题变成了答案（见下）"},
            {"problem": "D-A0-011/013：上游生成器特化到 peg、解析器嵌套括号静默错 AST",
             "cls": "调度失误（工具侧）", "fix_in": "theory-compiler 生成器与解析器",
             "status": "dispatched", "via": "P-5（AST 通用化 + 负向测试）"},
        ],
    },
    {
        "experiment": "A0′ 可逆性对照（cold-start-a0/prime）",
        "status": "green",
        "summary": "47% 覆盖做到 100% 准确 + 13 条可执行探针；A0 99% 覆盖仍带三处错。",
        "problems": [
            {"problem": "可逆性 > 覆盖率：不可逆机关封顶任何探索量的证据力",
             "cls": "框架级发现", "fix_in": "基准文件（开发堆选局准则、变体设计、1.8 探索表述）",
             "status": "ruled",
             "via": "【已裁决·监控代行】采纳：可逆性准则写入 Theoria.md 的选局与出题"
                    "准则（F-12）。下一批派工执行"},
        ],
    },
    {
        "experiment": "a0-spike 独立 A0（engine-rig）",
        "status": "green",
        "summary": "独立闭环 + Lean 接通；held-out 测试当场抓住一条错规则。",
        "problems": [
            {"problem": "gen_python 把编译不了的守卫静默替换成 True——废掉它喂的 certify",
             "cls": "调度失误（工具侧）", "fix_in": "theory-compiler：refuse 语义",
             "status": "dispatched", "via": "GENERATOR_REPORT.md → P-5 最高优先项"},
            {"problem": "held-out 抓错证明『重放全对≠规则对』——考卷 held-out 题的效度实证",
             "cls": "框架级发现（正面）", "fix_in": "评测协议（无需修，记入证据）",
             "status": "landed", "via": "commit a479e92"},
        ],
    },
    {
        "experiment": "API 接入与预检（arc-recon + baseline-arms 复核）",
        "status": "partial",
        "summary": "INC-001/002 两次误诊被复核推翻：400 是瞬时故障，短 ID 可用。",
        "problems": [
            {"problem": "INC-003：predicated compare 把双侧失败判成 PASS——预检自身不可证伪",
             "cls": "仪器缺陷", "fix_in": "arc-recon 预检判据",
             "status": "landed", "via": "已修：哈希须两侧俱在 + 全序列跑完"},
            {"problem": "INC-002 误诊 + 短 ID 根因：官方 incident 还停在『全线受阻』",
             "cls": "仪器缺陷", "fix_in": "arc-recon 官方账 + 重试策略",
             "status": "dispatched", "via": "P-1（正式改判 + 预检重跑）"},
            {"problem": "短 ID 绕过全 ID 护栏的风险 + 版本指纹丢失",
             "cls": "密封漏洞", "fix_in": "代理层护栏与账本格式",
             "status": "dispatched", "via": "P-2 已吸收（护栏须匹配短 ID；账本存映射）"},
        ],
    },
    {
        "experiment": "裸 CC 试点 + Schema 定位（baseline-arms）",
        "status": "partial",
        "summary": "裸 CC harness 试点已跑（sk48/g50t）；Schema 官方代码确认从未发布。",
        "problems": [
            {"problem": "INC-BA-001：检索子代理读到 9 局封存局机制（ls20/ft09 实质）",
             "cls": "密封漏洞", "fix_in": "检索/下载纪律 + Phase 4 主张集口径",
             "status": "ruled",
             "via": "【已裁决·监控代行】9 局全登记入 contamination_log；ls20/ft09 隔离出"
                    "封存主张集（21→19），预注册说明 + 对轻微 7 局做敏感性分析（F-11）。"
                    "白名单先行纪律已进 P-7。下一批派工落账"},
            {"problem": "GAP-1：Schema 复现不可能，主表『复现口径』一格失去依托",
             "cls": "外部依赖破产", "fix_in": "基准文件 1.12 主表口径",
             "status": "ruled",
             "via": "【已裁决·监控代行】采纳路 A：Schema 行改『上游轨迹直读（开发堆 4 局）』，"
                    "复现值合规留空，消融臂地位升为必需中的必需（F-13）。下一批派工执行"},
        ],
    },
    {
        "experiment": "确定性预检 v2（arc-recon，P-1）",
        "status": "green",
        "summary": "开发堆 4 局全 PASS；根因 = 1–3 分钟波浪式瞬时故障（多实例后端）。",
        "problems": [
            {"problem": "H-A『短 ID 即解』的初判是错的——短 ID 曾把预检带偏，后经订正",
             "cls": "仪器缺陷", "fix_in": "arc-recon 预检重试包络 + baseline AUDIT 订正",
             "status": "landed", "via": "INC-005 + commit 9824892；真正的解是重试包络"},
            {"problem": "失败 400 是否计费悬置了两轮，乐观悲观口径差 9.7 倍",
             "cls": "度量空洞", "fix_in": "预算模型（BUDGET_REPORT §4）",
             "status": "landed", "via": "scorecard×账本 4 样本恒等：失败 400 不计费"},
        ],
    },
    {
        "experiment": "真 A1 + 对抗式复核（theory-compiler，P-5）",
        "status": "green",
        "summary": "LP 证书过数据边界落成空公理集 Lean 证明；复核 CONFIRMED 但揪出两处说得比证据满。",
        "problems": [
            {"problem": "move 推导只校验转移形状不校验使能条件——形状同构的另一个世界会拿到同一份 Lean",
             "cls": "机制归纳错", "fix_in": "gen_lean 使能条件逐状态比对",
             "status": "landed", "via": "commit 494a427/1cf95d1：已加校验 + 负对照"},
            {"problem": "E-06：证书权重仍需人手抄进调用侧",
             "cls": "表达力不够", "fix_in": "compiler 证书自动注入",
             "status": "dispatched", "via": "P-10"},
        ],
    },
    {
        "experiment": "A2 同构世界（cold-start-a2，P-6）",
        "status": "green",
        "summary": "假定理展品造出、六拍修复回路走完——A2 的两句验收兑现。",
        "problems": [
            {"problem": "过程中撞出两条编译器缺陷（已按通道上报 theory-compiler）",
             "cls": "调度失误（工具侧）", "fix_in": "theory-compiler",
             "status": "dispatched", "via": "PARTNER_SYNC 94a8202 → P-10"},
        ],
    },
    {
        "experiment": "方差包络首跑（baseline-arms，P-7/P-12）",
        "status": "partial",
        "summary": "ar25×haiku×3 被 G4 拦停（真实劣化）；配额口径拿到实测答案。",
        "problems": [
            {"problem": "裸 CC（haiku 档）在 ar25 上连续死格——包络协议没预设『模型真的不行』这一支",
             "cls": "框架级发现", "fix_in": "包络协议（degraded 标注 + 敏感性说明）",
             "status": "ruled", "via": "F-15 裁决：ar25 记 degraded 不追，其余 3 局续跑"},
            {"problem": "proxy 与 baseline 账本字段拼写分歧",
             "cls": "同壳纪律裂缝", "fix_in": "账本正典化（proxy 为正典）",
             "status": "ruled", "via": "F-16 裁决 → P-9/P-12"},
        ],
    },
    {
        "experiment": "M9 三引擎（engine-rig，P-4）",
        "status": "green",
        "summary": "死锁定理、IC3 不变量、探针规划器定价全部落地；peg 0111 拿到非线性证书。",
        "problems": [
            {"problem": "冻结的 kind 枚举装不下新引擎的候选类型",
             "cls": "表达力不够（契约层）", "fix_in": "CONTRACTS candidates_schema v0.2",
             "status": "ruled", "via": "F-14 裁决：加法式升版，两轨道会签 → P-10"},
        ],
    },
]

# --------------------------------------------------------------------------
# 论文工作量地图 —— 完成目标的正式定义（2026-07-28 起，总进度以此为分母）
#
# 对标口径：Schema 论文的实验规模 = 全公开集 25 局单臂跑通 + 全量轨迹
# artifacts 释出 + 98.98% 主数字。Theoria.md Phase 4 原文要求「规模与开放性
# 够到 Schema 的地板」。我们的等价规模：封存 19 局（F-11 后）× 三臂 × n +
# 消融臂 + 开发堆 4 局迭代战役 + 考卷 + 全量释出。
# 每个工作包锚定论文的一个具体槽位（表/图/节），pct 是监控对树上证据的判断。
# --------------------------------------------------------------------------

PAPER_PLAN = [
    {"id": "WP1", "name": "框架本体与离线验收", "weight": 0.15, "pct": 100,
     "slot": "§3 框架 · 图5 DC22案例 · 图6 概念时间线",
     "scale": "对标：Schema 的 world_model.py 方法论一节。我们：DSL+四形态+六/八引擎+A0/A0′/A1/A2 四件离线验收",
     "evidence": "六引擎 + M9 + FD 三档定价 + 500 世界 23 不变量零违规；世界工厂 20 世界；契约 v0.3；A0/A0′/A1/A2/A3 五件离线验收全绿"},
    {"id": "WP2", "name": "封闭系统与外壳可信度", "weight": 0.08, "pct": 95,
     "slot": "§2 方法可信度（密封/复放/对账）",
     "scale": "Schema 无此层（其复现失败正是教训）。我们：双代理+护栏+对账+复放抽检",
     "evidence": "双代理 + 花费闸门（对抗测试先破五种绕法）+ 金丝雀日检 + 预检 4/4 + 熔断器自动出闩；留痕正典化"},
    {"id": "WP3", "name": "Theoria 臂在线迭代战役（开发堆）", "weight": 0.20, "pct": 30,
     "slot": "§5 实验主体 · 图2 账单形状（Theoria 列）",
     "scale": "对标：Schema 25 局全集单臂全跑。我们：4 局 × 迭代至退出条件（U3≥k 局 + Δ 内 + 账单形状可见）",
     "evidence": "臂在线链路通、preflight 零计费；战役第二关在跑（RES-1 常驻推进）"},
    {"id": "WP4", "name": "对照臂数据（CC 包络 + Schema 路A + 消融臂）", "weight": 0.08, "pct": 55,
     "slot": "表1 主表另两列 · §6 消融",
     "scale": "CC：4 局×3 重复；Schema：上游 artifacts 开发堆子集直读（F-13 口径）；消融臂：−定理义务",
     "evidence": "裸 CC 包络 + 上游 165 文件 + 消融臂建成并有闸门（a0 可解 / a2 不可解判决正确）"},
    {"id": "WP5", "name": "评测两器：电池冻结 + 考卷构造器", "weight": 0.10, "pct": 90,
     "slot": "§4 评测协议 · 图3 能力谱与考卷",
     "scale": "电池五族过四道工序后冻结 v1；考卷四题型出题机+判卷机在自建族闭环",
     "evidence": "考卷四题型跑上 20 世界 + 判卷自检 + 电池区分力首跑；抗游戏审计在跑"},
    {"id": "WP6", "name": "封存战役（主表确证）", "weight": 0.20, "pct": 0,
     "slot": "表1 主表 · 图2/图3 确证版 · C1/C2 裁决",
     "scale": "对标 Schema 25 局：我们 19 封存局 × (Theoria + CC + 消融) × n，逐局入库禁止回看",
     "evidence": "门槛 = Phase 1 全绿 + 冻结清单提交。当前零接触（这是纪律不是欠账）"},
    {"id": "WP7", "name": "考卷封存子集（判决题 m 局 + 移交 + 改规则）", "weight": 0.06, "pct": 0,
     "slot": "图3 考卷行 · C4 裁决",
     "scale": "m 局在主表跑完后构造变体（时序死结的解）；分层移交可随主表同跑",
     "evidence": "依赖 WP6；出题流程由 P-15 预演"},
    {"id": "WP8", "name": "预注册与统计裁决（冻结清单 13 项）", "weight": 0.05, "pct": 55,
     "slot": "§5 统计口径 · 双结局文本",
     "scale": "三主终点（U3 达成率/判决题准确率/前载指数）+ Wilcoxon 配对 + n 由包络方差定",
     "evidence": "冻结包起草 + Phase 1 收口交付；统计规则草案在盘"},
    {"id": "WP9", "name": "论文写作（workshop 文 → 主文）", "weight": 0.05, "pct": 70,
     "slot": "全文（3.2 的八节骨架）",
     "scale": "Phase 1 结 workshop 文（P-16 在跑）→ Phase 3 结案例研究 → 主文",
     "evidence": "PAPER.md 2512 行成稿，含引文核查、评审分诊、待办清单；五视角评审在跑"},
    {"id": "WP10", "name": "释出包（Schema 地板对齐）", "weight": 0.03, "pct": 60,
     "slot": "§8 开放性声明",
     "scale": "对标 Schema：全公开集 artifacts。我们：全账本+两本书四形态+Lean+候选箱+探针日志+电池代码+incident 台账+复跑说明",
     "evidence": "release/ 落地 + 复现脚本 + 许可条款；账本哈希链在盘"},
]

# --------------------------------------------------------------------------
# 二维项目地图（2026-07-28 用户指令：以坐标取代流水号，进度画在图上）
#
# 横轴 X = 阶段（工作流向，左到右）：1 造仪器 → 2 离线验证 → 3 在线练习
#   → 4 正式战役 → 5 论文与释出
# 纵轴 Y = 子系统：E 引擎车间 / C 编译与证明 / S 外壳与账本 / A 三臂对局
#   / V 评测两器 / P 论文产出
# 工单编号从此 = 坐标-短名（如 A3-second-level）；分支 agent/<小写坐标-短名>。
# 每格 pct 是监控判断；active 列当前落在该格的在飞工单（旧流水号保留至退役）。
# --------------------------------------------------------------------------

GRID_COLS = ["1 造仪器", "2 离线验证", "3 在线练习", "4 正式战役", "5 论文与释出"]
GRID_ROWS = [
    ("E", "引擎车间"), ("C", "编译与证明"), ("S", "外壳与账本"),
    ("A", "三臂对局"), ("V", "评测两器"), ("P", "论文产出"),
]

GRID = {
    "E1": {"pct": 100, "note": "六引擎全绿 + 500 世界性质轰炸零违规", "active": ["E1-property-fuzz", ]},
    "E2": {"pct": 100, "note": "FD 三档定价，死锁红利量化", "active": ["P-13"]},
    "E3": {"pct": 5,  "note": "引擎在线供货（经 theoria-arm 调用）", "active": []},
    "E4": {"pct": 0,  "note": "封存战役中的引擎供给", "active": []},
    "E5": {"pct": 20, "note": "引擎代码随释出包公开", "active": []},

    "C1": {"pct": 100, "note": "DSL v0.3 + 四形态 + refuse 语义 + 计数锁词汇", "active": ["C1-worldgen", ]},
    "C2": {"pct": 100, "note": "五件离线验收 + 世界工厂 20 世界 + 变体生成", "active": []},
    "C3": {"pct": 5,  "note": "在线两本书：首局的 theory.dsl 尚在 P-8 分支里", "active": []},
    "C4": {"pct": 0,  "note": "封存局的证书生产线", "active": []},
    "C5": {"pct": 60, "note": "四形态 + Lean + 移交包随释出", "active": ["P-19"]},

    "S1": {"pct": 98, "note": "双代理 + 护栏 + 账本 + 对账 + 变体层 + 契约变更协议", "active": []},
    "S2": {"pct": 95, "note": "预检 4/4 + 金丝雀日检 + 封存护栏两半齐", "active": ["P-20"]},
    "S3": {"pct": 85, "note": "花费闸门落地五种绕法已封；哈希链在盘", "active": []},
    "S4": {"pct": 55, "note": "冻结清单起草 + Phase 1 收口", "active": ["P-22"]},
    "S5": {"pct": 20, "note": "账本与 incident 台账随释出公开", "active": []},

    "A1": {"pct": 88, "note": "裸 CC 全套 + 消融臂建成并带闸门", "active": ["P-18"]},
    "A2": {"pct": 95, "note": "五个自建世界 + 双 A0 互考 + 消融对照", "active": ["A2-crosscheck", "P-17"]},
    "A3": {"pct": 25, "note": "开发堆在线：preflight PASS，战役第二关推进", "active": ["P-12"]},
    "A4": {"pct": 0,  "note": "封存战役（门槛：Phase1 全绿 + 冻结提交）", "active": []},
    "A5": {"pct": 0,  "note": "主表三列 + 消融列", "active": []},

    "V1": {"pct": 100, "note": "五族指标 + 预注册 + 区分力首跑", "active": []},
    "V2": {"pct": 92, "note": "考卷四题型 × 20 世界 + 判卷自检", "active": []},
    "V3": {"pct": 60, "note": "区分力已跑；抗游戏审计在跑", "active": []},
    "V4": {"pct": 0,  "note": "封存回算 + 判决题实考", "active": []},
    "V5": {"pct": 70, "note": "图表管线可复现，六图数据就位并入正文", "active": ["P-21"]},

    "P1": {"pct": 85, "note": "方法论与骨架", "active": []},
    "P2": {"pct": 88, "note": "PAPER.md 2512 行，引文核查 + 评审分诊", "active": ["P-23"]},
    "P3": {"pct": 55, "note": "案例素材齐（A0′ 对照、A2 展品、A3 迁移、消融对照）", "active": ["P3-case-study", ]},
    "P4": {"pct": 30, "note": "预注册包起草中", "active": []},
    "P5": {"pct": 55, "note": "release/ + 复现脚本 + 许可条款", "active": ["P-19"]},
}


# --------------------------------------------------------------------------
# 当前阶段焦点（监控的判断，改这里即改全舰队的优先次序）
#
# 依据：离线建造已近完成（WP1 98% / WP2 92% / WP5 82%），剩余权重集中在
# 战役与论文（WP3 20% 权重仅 25%、WP6 20% 权重为 0、WP9/WP10 合成类）。
# 所以板上同优先级的条目里，属于焦点赛道的先被领走。
# --------------------------------------------------------------------------

PHASE_FOCUS = ["campaign", "paper", "verify", "infra"]      # 依次加权；不在表内的赛道不降级，只是不加权
FOCUS_BOOST = 1                          # 焦点赛道的条目在排序上等价于优先级 -1
