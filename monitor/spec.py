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
                "status": "missing",
                "note": "arc-recon/README.md 第 6–9 行明确声明自己不是这个代理。"
                        "仓库内没有任何监听端口的进程。密封性目前靠自觉，"
                        "不是 Theoria.md 要求的『由构造成立』。",
                "blocks": ["p1-seal-test", "p1-same-shell", "p1-replay-audit"],
            },
            {
                "id": "p1-proxy-model",
                "label": "模型代理（provider usage 逐字入账）",
                "clause": "Phase 1 · 自下而上五层 (3)",
                "status": "missing",
                "note": "没有模型流量记录面。C2『账单形状』是主轴签名证据，"
                        "而度量它的仪表尚未存在 —— 约束 8 目前无法被验证，只能被相信。",
                "blocks": ["c2"],
            },
            {
                "id": "p1-variant",
                "label": "变体注入层（包裹合法集 + 构造性依据）",
                "clause": "Phase 1 · 自下而上五层 (2)",
                "status": "missing",
                "note": "判决题的真值来自构造。没有这一层，考卷第 (i)(ii)(iii) 类"
                        "变体都出不了题。",
            },
            {
                "id": "p1-runner",
                "label": "runner 与账本（env_step / model_call 两类事件）",
                "clause": "Phase 1 · 自下而上五层 (4)",
                "status": "partial",
                "note": "baseline-arms/harness/ledger.py 已起草；但没有 scorecard 对账，"
                        "没有 probe 专用 scorecard，没有 run.json。",
            },
            {
                "id": "p1-scorer",
                "label": "冻结打分器接入 + 账本分数与 scorecard 对账",
                "clause": "Phase 1 · 自下而上五层 (5)、验收单",
                "status": "missing",
                "note": "全仓 grep『scorer』零命中。对账义务（不等 = incident）无实现。",
            },
            {
                "id": "p1-determinism",
                "label": "确定性预检全绿",
                "clause": "Phase 1 验收单",
                "status": "risk",
                "note": "arc-recon 记为 INCOMPLETE（INC-002：0/8 次动作成功）。"
                        "但 baseline-arms/probe_log.jsonl 显示带退避重试后动作确实返回 200 —— "
                        "INC-002 的结论已被新证据推翻，而预检尚未在新重试策略下重跑。",
                "probe": "determinism_state",
            },
            {
                "id": "p1-access",
                "label": "接入核查各项已入账",
                "clause": "Phase 1 · 一件接入核查",
                "status": "partial",
                "note": "已结：级联语义（frame 是帧列表）、level 为响应字段、guid、动作空间、"
                        "首帧跨会话可复现。未结：全量跨会话残留、速率与配额、"
                        "金丝雀重放、帧缓存与释出许可条款。",
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
                "status": "risk",
                "note": "piles.json 哈希锁定，API 层封存堆零接触（本监视器每次复验请求体）。"
                        "但 INC-BA-001 带来了 API 之外的口子：检索子代理读到了 9 局封存局的"
                        "机制描述（ls20/ft09 实质），知识污染本检查构造上抓不到。F-11 已裁决"
                        "（监控代行）：主张集缩至 19 局，ls20/ft09 隔离，轻微 7 局敏感性分析。",
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
                "status": "partial",
                "note": "两半各自成立、尚未接通：engine-rig 的 LP 真解出了权重，"
                        "theory-compiler 的 Lean 用的却是手算常量 + BFS 枚举。"
                        "engine-rig/interop/certificate_export.py 正是那座桥，刚动工。",
                "probe": "a1_state",
            },
            {
                "id": "p1-a2",
                "label": "A2 DC22 重放：造出『类型检查通过、对世界为假』的定理",
                "clause": "Phase 1 · 三件离线验收；INC-004",
                "status": "missing",
                "note": "F-01 冲突已裁决（INC-004）：改为自建 DC22 同构世界，"
                        "在 cold-start-a2/ 完成。已解除封锁，提示词 P-6 可派工。",
            },
            {
                "id": "p1-engines",
                "label": "引擎架冒烟（LP / CEGIS / FD 各过一例）",
                "clause": "Phase 1 验收单",
                "status": "partial",
                "note": "LP 与 CEGIS 真过；FD 是 grounded-STRIPS BFS 桩，"
                        "接口同形但『白捡二十五年规划工程』这句话目前不成立。",
            },
            {
                "id": "p1-seal-test",
                "label": "密封测试（臂内无凭据；绕开双代理的出网必须失败）",
                "clause": "Phase 1 验收单",
                "status": "blocked",
                "note": "双代理不存在，故无从测起。凭据卫生本身是干净的："
                        "本监视器全仓扫描确认密钥只出现在 .env。",
                "probe": "credential_hygiene",
            },
            {
                "id": "p1-replay-audit",
                "label": "复放抽检 2 局，环境侧逐比特一致",
                "clause": "Phase 1 验收单",
                "status": "blocked",
                "note": "需要账本，账本需要 runner 与代理。",
            },
            {
                "id": "p1-same-shell",
                "label": "三臂经双代理落同一账本、打分器通吃",
                "clause": "Phase 1 验收单、第二部分总纪律",
                "status": "partial",
                "note": "裸 CC 臂已立：harness + 记账管线（baseline-arms M2）+ sk48/g50t "
                        "真动作试点，封存护栏在 client 层强制。Schema 臂被 GAP-1 判死"
                        "（官方代码从未发布，复现值合规留空，见 F-13）。Theoria 臂未搭。"
                        "『同壳』的物理载体（双代理）仍缺 → P-2。",
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
                "status": "missing",
                "note": "零代码。这是全项目**唯一一件既不烧游戏钱、又不被 INC-002 阻塞、"
                        "却完全没开始**的工作 —— 而 Theoria.md 明写它可以并行。",
            },
            {
                "id": "p2-audit",
                "label": "电池四道工序（区分力 / 方向预注册 / 去冗余 / 抗游戏审计）",
                "clause": "Phase 2 · 电池自身要先受审",
                "status": "missing",
                "note": "区分力验证只准用 CC vs Schema 两臂 —— 而这两臂的轨迹一条都没有。",
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
                "id": "p3-envelope",
                "label": "对照两臂在开发堆各跑 2–3 局，方差包络冻结",
                "clause": "Phase 3 · 经济",
                "status": "missing",
                "note": "裸 CC 臂与 Schema 复现桶的开发堆轨迹，一局都没有。"
                        "这既是 Phase 3 的方差包络，也是 Phase 2 电池区分力验证的"
                        "唯一合法材料。",
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
     "module": "—", "status": "missing",
     "note": "**八道工序里唯一整道缺席的**。全仓 grep『ic3』『pdr』只命中 Theoria.md 自己。"
             "LP 与零空间够不着的形状目前无人兜底 —— 而 lp_potential 的不完备性是已知的、"
             "并且已经在 A0 的 peg fixture 上真实发生过（0111 不可解但无线性证书）。"},
    {"step": "规划", "engine": "Fast Downward（不自研）",
     "module": "engine-rig/engines/fd_adapter", "status": "partial",
     "note": "接口就位，后端是 BFS 桩。单位代价下长度最优，所以 A0 这种小世界够用；"
             "但三档阶梯的后两档（A*+可采纳启发、地标分段）都还不存在。"},
    {"step": "死锁刻画", "engine": "定理机器局部化 + trap 学习",
     "module": "—", "status": "missing",
     "note": "Theoria.md 1.9 把死锁称作『野外的日常无解』，是试金石机器从周日考试变成日常上班的"
             "唯一途径，也是 C1 的主要供给。没有它，不可解性主张只能靠构造变体，"
             "而构造变体在封存堆上有时序死结。"},
    {"step": "探索 / 戳探", "engine": "前沿主动学习",
     "module": "engine-rig/engines/probe_frontier", "status": "partial",
     "note": "算法正确（A0 上算出 1.000 bit 的划分并给出『本世界无实验可分』的裁决）。"
             "但 A0 产出**零条可执行探针** —— 约束 7『定理未经戳探不得定案』"
             "在第一次冷启动上就没能真正生效。"},
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
        "severity": "high",
        "title": "INC-002 已被 baseline-arms 推翻并找到根因；官方 incident 记录仍待改判",
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
        "action": "T-01 收尾：带短 ID + 退避策略重跑预检，追加 incident 改判，"
                  "并在账本格式里保留全 ID 映射。",
    },
    {
        "id": "F-03",
        "severity": "high",
        "title": "Phase 2 完全没开始，而它是唯一不被阻塞的整段工作",
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
        "severity": "medium",
        "title": "八道工序缺两道：IC3/PDR 与死锁刻画",
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
         {"label": "环境代理", "status": "missing", "tip": "透明 HTTP 代理；密封由构造成立。未建 → T-03"},
         {"label": "模型代理", "status": "missing", "tip": "usage 逐字入账；C2 账单形状的仪表。未建 → T-03"},
         {"label": "变体注入层", "status": "missing", "tip": "判决题真值来自构造。未建"},
         {"label": "runner + 账本", "status": "partial", "tip": "baseline-arms/harness 有雏形；无对账、无 run.json"},
         {"label": "冻结打分器", "status": "missing", "tip": "全仓无 scorer；对账义务无实现"},
     ]},
    {"group": "内环五拍", "clause": "1.10(d)",
     "items": [
         {"label": "theorize", "status": "partial", "tip": "A0 上真跑通：28 候选逐条裁决入册，全程留痕"},
         {"label": "certify", "status": "partial", "tip": "廉价层在 A0 咬合过两次（逼出 Button/Door）；目录未落盘，Lean 义务未清"},
         {"label": "probe", "status": "risk", "tip": "A0 零可执行探针；约束 7 空转 → T-07"},
         {"label": "plan", "status": "partial", "tip": "fd_adapter 是 BFS 桩；A0 的 plan 阶段进行中"},
         {"label": "commit", "status": "missing", "tip": "脚本整段执行 + 逐帧批改，尚无实现"},
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
         {"label": "Theoria 臂", "status": "missing", "tip": "离线件已证活（A0/A0′）；在线臂等双代理"},
     ]},
    {"group": "三件离线验收", "clause": "Phase 1",
     "items": [
         {"label": "A0 冷启动", "status": "green", "tip": "全环跑通并提交：certify 双层绿、plan SAT、赢、不可解证书"},
         {"label": "A1 孔明棋", "status": "partial", "tip": "两半未接通 → T-06"},
         {"label": "A2 DC22", "status": "missing", "tip": "冲突已裁决（INC-004）：自建同构世界 → P-6"},
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
]
