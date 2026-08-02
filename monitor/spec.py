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
                        "2026-07-31 封印升级（merge b375a9bd）：EnvProxy 移入独立子进程"
                        "（theoria-arm/harness/proxy_process.py），臂父进程无钥匙"
                        "由整局 mock 对局证明（ARC_API_KEY 不在父环境、read_secret 抛错，"
                        "哨兵仍从子进程到达上游）。这就是 RES-1 密封合取项之争"
                        "（inbox 20260730T1240Z）的进程读法答案——按构造成立，不再靠裁决。",
                "blocks": ["p1-seal-test", "p1-same-shell", "p1-replay-audit"],
            },
            {
                "id": "p1-proxy-model",
                "label": "模型代理（provider usage 逐字入账）",
                "clause": "Phase 1 · 自下而上五层 (3)",
                "status": "partial",
                "note": "改判 2026-07-31，依 S32 裁决（verify-lab/DUAL_PROXY.md，inbox "
                        "20260731T1800Z）：**一个代理在真实流量上已验，一个已建成未验**。"
                        "模型代理已建（proxy/model_proxy.py + pricing/），边界行为有记录，"
                        "但真实供应商上 0/65 次请求成功（全 401：代理按设计剥客户端凭据，"
                        "仓库无供应商钥匙可注入）；2026-07-31 起臂的模型调用走 vendor CLI "
                        "直连，逐调用记 proxied: false（D-P8-002，声明缺口）。"
                        "此前的 green 把『仪表存在』读成了『仪表已验』——降回 partial。\n\n"
                        "【在案裁定·未采计】同日另有一份改定义结案论证，全文照录；"
                        "板面判决仍取 partial——Theoria.md:290 的设计原文是模型流量"
                        "**过代理**入账，CLI 包络路径达成的是记账而非过代理，把义务"
                        "改写成已达成的那一半再结案，正是本仓库其它地方点名要防的移动："
                        "**史实**（S32 复算的分母，每轮由 dualagent/count.py 重算）："
                        "环境代理 924 条真实端点腿在账（1009 条代理腿中，其余 85 条打"
                        "回环夹具）；模型代理 65 条 model_call **全部 401（65-of-65）**，"
                        "**0 条 2xx**。**(a) 当下不可达，且非工程缺陷**：DUAL_PROXY §4 "
                        "六步清单第 1 步要求 .env 里有 ANTHROPIC_API_KEY，而 .env 只有 "
                        "ARC_API_KEY——补它是所有者出资动作，任何代理不得代办；第 2 步"
                        "要换掉 theoria-arm D-P8-002 特意选定的 claude -p 订阅传输，"
                        "等于为凑数而弱化既定设计。**已达成的一半**：usage 块经 CLI "
                        "包络逐字写入 run 账本，每条 model_call 标 proxied:false 并带 "
                        "proxy_gap 注明原因，无人能把它误读成代理流量；账面明写的损失"
                        "照旧：request 是臂发给 CLI 的提示词而非上游 /v1/messages 体，"
                        "入token构成不可由此账本得出结论。**留权**：模型代理仍是任何"
                        "未来 API 传输臂的**强制通路**；六步清单为常设升级路径，触发"
                        "条件是所有者决定出资配 API key，届时 count.py 的 "
                        "model_proxy_succeeded 转非零并须同一 commit 改判本条。\n\n"
                        "【所有者裁决·2026-08-01】决策点已答复。所有者在线原话："
                        "『我这个全部都走的claude账号额度，剩下四个继续推』——即不另配 "
                        "ANTHROPIC_API_KEY，模型调用走 Claude 订阅额度（正是 D-P8-002 "
                        "的 claude -p 订阅传输），此为所有者认可的常态运行事实而非"
                        "临时缺口。依 P1READJ（2026-07-31T15:53Z）下一步既定分支执行"
                        "『否则本项封存』：**本项封存**（closeout/p1-owner-ruling，"
                        "留痕 monitor/runs/2026-08-01T023624Z-P1PUSH4/）——DUAL_PROXY "
                        "§4 六步单转休眠档（非删除：所有者若日后改判出资，原样复活并"
                        "按原文与改判同 commit）；论文用 DUAL_PROXY §3 三句话原文"
                        "（verify-lab/DUAL_PROXY.md:122-134）。板色保持 partial："
                        "封存≠达成，Theoria.md:290 的设计原文未改，本条不再是开放"
                        "决策点而是已裁的诚实披露。",
                "blocks": ["c2"],
            },
            {
                "id": "p1-variant",
                "label": "变体注入层（包裹合法集 + 构造性依据）",
                "clause": "Phase 1 · 自下而上五层 (2)",
                "status": "green",
                "note": "改判 2026-07-31（closeout/p1-replay-live 全板扫，留痕 "
                        "monitor/runs/2026-07-31T170455Z-P1REPLAYLIVE/）。条款三问俱清："
                        "包裹合法集冻结且默认拒绝（proxy/variants.py:43-45,108-114，"
                        "五算子白名单，集外算子拒载并给理由）；构造性依据装载即强制"
                        "（:94-100，无依据或 <40 字符拒载）且经独立验证——exam 密封演练"
                        "出题→判卷→归档全回路，构造真值对穷举 oracle 10/10 一致"
                        "（exam/SEALED_DRILL.md；proxy 4 + exam 17 + 演练 10 份规格全带"
                        "依据，verdict.py 经 proxy 校验器注册并对象/文件双哈希）；"
                        "规格文件+哈希入账（Variant.reference→每条 env_step、"
                        "fingerprint→run_start，proxy/LEDGER_FORMAT.md:201,440，"
                        "test_e2e.py 钉死）。D-032 追加 win_tighten 退化记账与读取工具。"
                        "42+53 测试绿。与 p1-proxy-model 的 0/65 不同类：本层有端到端"
                        "账本证明与 oracle 交叉验证。残差如实：win_tighten 对无分游戏"
                        "是废除而非收紧（先决条件已写，D-032）；observation_loss 只作用"
                        "frames[-1]，对帧突发响应是到达即失真，其上的割集论证不健全"
                        "（对 ARC 是活风险，开发堆最长 113 帧）；构造真值仅在 2 世界 "
                        "10 变体上验证过；从未改写过真实 ARC 流量（所有 run.json "
                        "variant: null）——条款不要求活用，Theoria.md:372 将封存局变体"
                        "构造明令排进 Phase 4。",
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
                "note": "注记重写 2026-07-31（closeout/p1-replay-live 全板扫+监审复算；"
                        "原注『冻结打分器本体未接 → P-9』已失实）。已成的一半：打分器"
                        "本体已冻结（proxy/scoring/ + frozen.json 自校验哈希记录，漂移"
                        "即拒评，指纹入 run_start/run.json；freeze/MANIFEST_DRAFT.md:87 "
                        "称其为全库唯一逐字节自校验冻结件）；对账相等处处成立——monitor "
                        "复算 37 run 过冻结打分器 --all：**26 PASS、0 FAIL、11 "
                        "UNDETERMINED**（含 4 条 theoria 真腿全 PASS——两臂通吃的实证；"
                        "UNDETERMINED 全为 D-015 类丢卡，卡关后不可再取，只可说『留卡"
                        "的全过』不可说比例；留痕 score_corpus.json，--no-incident "
                        "--no-artifact 防账本变异，DELIVERY_RULING §5 有六条重复 "
                        "incident 前车之鉴）。未成的一半（留 partial 的理由）：『跑完"
                        "一局即打分』从未在活局执行——无臂 harness 在 run_end 调 "
                        "score_run，唯一经 proxy/runner.py 的活局在 run_end 前崩"
                        "（S31）；事后批扫正是 Theoria.md:371 禁的口径。接线缺口归 "
                        "DELIVERY_RULING.md §4（两行 open·unassigned，与 p1-same-shell "
                        "同源）；ablation 臂无活账本（D-AB-004），通吃至多 2/3 臂。"
                        "若所有者裁『一台冻结打分器读遍各臂账本+有卡处处相等』即为"
                        "达成，本项可绿——此收窄须明判，不得静默（S32 先例）。\n\n"
                        "2026-08-01 A18 落地（merge 7c61d107）：『跑完一局即打分』"
                        "接线完成——harness/run.py 在 run_end 后调冻结打分器"
                        "（生产语义：incident/artifact 全开，判定入 run 目录与 "
                        "run.json 带指纹，漂移降级 UNDETERMINED 不抛栈），负控为"
                        "连贯伪造（卡总数同改、唯账本拆穿，FAIL 证真），--ledger "
                        "转发落地且默认真腿入共享账本（D-A18-002）。未成的只剩"
                        "**活证据**：下一条真腿的 score.json 是第一条『跑完即打分』"
                        "的活记录，届时本项复裁。臂领地套件既有 2 红与本项无涉"
                        "（A29 在案）。",
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
                "status": "green",
                "note": "改判 2026-07-31（closeout/p1-replay-live 全板扫；W-1250 inbox "
                        "2026-07-28 早已提议，一直未执行）。八行核查全部已入账"
                        "（arc-recon/ACCESS_CHECK.md:9-20，README:159-199 为索引），原注"
                        "两个未结项均在注记写下之后关闭：**全量跨会话残留**——2026-07-30 "
                        "两次 full 剖面扫（canary_runs.jsonl 末两条：20/20 帧、四局全 "
                        "PASS，对照 2026-07-28 另一会话封存的期望；commit e0db135f，"
                        "S22 item 1）；**速率配额官方口径**——600 RPM 原文两处在案"
                        "（ACCESS_CHECK.md:233-236 引 docs.arcprize.org/rate_limits；"
                        "browser-ops/TERMS.md:31 逐字），配额则产品无此概念"
                        "（TERMS.md §7.5 登录面板实证：无配额/用量/计费界面），"
                        "rate_budget.py 预算峰值 432/600 rpm 经 arc-recon/verify.sh "
                        "复算，实测 60.88/62.02 rpm。残差如实带上：429 退避曲线"
                        "文档有、实测无（3736 请求 0 次 429；client/canary 均不处理 "
                        "429；故意触限 = 花费+账号风险，不主动买）；残留仪器深 "
                        "6/3/6/5 步，step 7 起的残留在一切仪器之外；ar25 预检 "
                        "run_a/run_b 墙钟重叠，测的是并发隔离非顺序隔离；『失败不计费』"
                        "是我方 19 样本归纳非官方承诺；ToS §3(3) 自动化函件未发"
                        "（browser-ops/LETTER-TO-ARC-draft.md，所有者动作）；金丝雀"
                        "日程从未安装（schtasks 无任务，所有者动作——第 2 行的依据是"
                        "八次一致复放而非常设仪器）。",
            },
            {
                "id": "p1-cascade",
                "label": "级联语义已裁决",
                "clause": "Phase 1 · 一件轨迹作业",
                "status": "green",
                "note": "改判 2026-07-31（closeout/p1-replay-live 全板扫；W-1250 inbox "
                        "2026-07-28 早已提议，一直未执行）。原注三句全部失实：裁决在盘上"
                        "——arc-recon/CASCADE_RULING.md（2026-07-28，S5 收口件，"
                        "PARTNER_SYNC:649 布告，board done）：**渲染突发而非内部 tick**"
                        "（板级量化在 4、批内恒定增量两个签名均指离 tick），step 冻结为 "
                        "S→A→S、S=frames[-1]（Frozen，改判仅凭 incident），theory.pddl "
                        "无需 derived predicates，帧弃置显式强制（n_frames 必录）。"
                        "『是否超过 1 帧』在原注写下前一天就已观测（precheck.json "
                        "2026-07-27 max_frames_per_action=7）；今日树上四开发局实测 "
                        "494 个多帧批（g50t 287、sk48 207；最长 113 帧已入 tracked "
                        "ledger.g50t.jsonl:752；ar25/tn36 在线全单帧），真在线正典账本"
                        "复证：r2/r3 腿 ACTION2/5 返回 7/9 帧、sk48-l1 腿 2 帧。与 "
                        "D-A0-004 无冲突需合流：cascade 是 per-world 事实"
                        "（dsl_grammar_v0.2:335-340），A0 自建世界与 ARC 各判各的"
                        "（CASCADE_RULING §114-129 明文处理；a0-spike THEORIZE_LOG "
                        "T-11c 以 47040 对照独立同判 single_frame）；前身 "
                        "cascade/VERDICT.md 留取代横幅未静默改写。cascade/verify.sh "
                        "本收口离线复跑 PASS（27 步/4 局/0 未发现账本）。残差如实："
                        "G-1 tick 判据从未直测（§3 是两个反向签名非 tick 之测）；"
                        "G-2 全部真在线步仍在 level 0，批长随关卡变化不可答；G-3 113 帧"
                        "批只点过数未逐格读；§5 反驳计数器是 Phase 3 必做而未实现"
                        "（theoria-arm 领地，已派单）；grammar_card.py:25 值对理由错"
                        "（按后端能力立 per-world 事实，两次在案仍未修）。",
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
                # The probe counts ten artefacts on disk. It never runs the
                # pipeline, never checks certify passed, never checks the plan
                # was SAT -- "10/10 landed" is not "感知→…→赢". File presence
                # can show something is missing; it cannot show A0 worked.
                "probe_scope": "partial",
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
                "status": "green",
                "note": "改判 2026-08-01（A19/A20 交付后，均已并入 master 且套件"
                        "在合并树上复验绿：baseline-arms 552、proxy 497）。"
                        "**左合取项（臂内无凭据）三臂俱清**：theoria 按构造"
                        "（merge b375a9bd，EnvProxy 入子进程，test_seal_process.py）；"
                        "bare_cc 由 A19 照同一模板拆分（merge f9a61c0c：凭据只在"
                        "转发子进程，19 个 mock 测试证父进程环境无 ARC_API_KEY、"
                        "旧直读路径抛错、哨兵仍经子进程达 mock 上游；GAP-5 从只登记"
                        "改为已拆分，**bare_cc 恢复飞行资格——本条即该裁决**）；"
                        "ablation 无活客户端，从不持环境凭据（空满足）。供应商凭据："
                        "仓库与 .env 一律不存在，A20 的变量名白名单测试塞入即变红。"
                        "**右合取项（绕开双代理出网必须失败）两侧俱有负样本**："
                        "环境侧 test_bypass_negative.py 照旧；bare_cc 侧 A19 双闸"
                        "（无钥客户端拒非回环目标于 socket 前，子进程对带钥请求答 "
                        "400 ARM_SENT_A_KEY 而非转发）；模型侧 A20 "
                        "test_model_side_seal.py 在所有者已批的订阅传输读法下"
                        "（2026-08-01 裁决，见 p1-proxy-model 注记）：代理剥凭据必 "
                        "401（65-of-65 史实入档），无凭据出网不可能通过认证。"
                        "残差如实：各臂证据是 mock 负样本而非活体红队；ablation 为"
                        "空满足；vendor 侧认证按 D-P8-002 活在 CLI 层臂外——臂读不"
                        "读得到 CLI 自己的凭据库未被测试；封存堆护栏"
                        "（21 ID+词干，SealedPileBreach 致死）照旧。"
                        "凭据卫生干净：密钥只在 .env（本监视器每轮复验）。",
                "probe": "credential_hygiene",
                # The item is a conjunction and this probe tests one half: it
                # looks for the key's value in the tree and never attempts an
                # egress bypass. proxy/tests/test_seal.py is the check for the
                # other half and the board does not run it. So the probe may
                # report a problem here, but it may not call the item done.
                "probe_scope": "partial",
            },
            {
                "id": "p1-replay-audit",
                "label": "复放抽检 2 局，环境侧逐比特一致",
                "clause": "Phase 1 验收单",
                "status": "green",
                "note": "改判 2026-07-31（closeout/p1-replay-live，留痕 monitor/runs/"
                        "2026-07-31T170455Z-P1REPLAYLIVE/）。两局档案抽检在盘上：ar25 "
                        "16 局/9 位/372 对/0 失配（P-9，proxy/runs/p9-shell-harden/"
                        "replay_spotcheck_ar25.json）、g50t 26 局/6 位/971 对/0"
                        "（proxy/runs/20260731T154336Z-P1-replay-spotcheck-2/）。本次收口"
                        "把 S31 起的真在线正典账本并入同一仪器：g50t 三条 theoria 真臂腿"
                        "（A3 level2-carried r1/r2/r3）活腿互比 10 位/22 对/0，与档案合比 "
                        "29 局/1304 对/0；ar25 S31 真臂 RESET（proxy/var 账本，摘录入留痕 "
                        "evidence/）与档案合比 17 局/388 对/0——活证据仅位 0 一帧，如实"
                        "注明；附 sk48 补充 5 局/34 对/0（S31 前真腿，不计入两局）。"
                        "1315 个带帧步 frame_hash 从存储帧重算 0 不符；两份档案报告经"
                        "重建正典逐位复现（回归 match；正典摘要漂移系 upgrade_ledger "
                        "路径依赖，输入钉子 9/9 吻合，已派单修复）。臂侧 replay_mismatch"
                        "（theoria-arm/inner/certify.py：手册预测对单次观测）与本项无涉，"
                        "6 条中 5 条恰在环境跨局逐比特复现的位置上。抽检为开局共享前缀"
                        "而非全轨迹；对抗复核三员通过（留痕 NOTES.md）。",
            },
            {
                "id": "p1-same-shell",
                "label": "三臂经双代理落同一账本、打分器通吃",
                "clause": "Phase 1 验收单、第二部分总纪律",
                "status": "partial",
                "note": "2026-07-31 两件实质推进：(1) 共享账本收下**第一条真臂记录**"
                        "（S31 探针，proxy/runs/20260731T104757Z-S31/FIRED.md：双轴同证"
                        "——env_step 带 arm: bare_cc × run_start 带真上游 "
                        "three.arcprize.org；2 动作 $0.00，登记簿 #9 先登记后开火）。"
                        "(2) **Theoria 臂已存在且真飞过**：A3 level2 战役两腿实花 "
                        "$9.5569 / 18 动作（登记簿 #10 已结算），P-8 那句『唯一还不"
                        "存在』作废。仍 partial 的理由：一条探针记录 ≠ 三臂例行经由"
                        "（FIRED.md 自己写明 DELIVERY_RULING.md §4 的三领地接线缺口"
                        "仍开放）；模型侧 CLI 直连使『双代理』只有一半（D-P8-002）；"
                        "打分器通吃仍待 p1-scorer。\n\n"
                        "2026-08-01 推进（仍 partial，但缺口在收窄）：A18 把 theoria "
                        "真腿计费默认接进共享账本（--ledger 转发，§4 axis 1 的 "
                        "theoria 份，D-A18-002）；A21 给 ablation 记账名（ledger.ARMS "
                        "收 ablation，合同变更 C-008——『三臂』在词汇表层首次可能，"
                        "D-AB-004 前提消解、改名归其属主，名字分歧 theoria_ablate "
                        "vs ablation 已在 D-A21-001 挑明交属主）；bare_cc 经 A19 "
                        "封印但按其 D-026 走自有转发子进程与自有账本（双重计费与"
                        "双帐格式之虑，在案不隐）——『三臂经双代理落同一账本』"
                        "照字面仍未达，例行活腿与 ablation 换名是剩余两步。",
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
                "note": "注记重写 2026-07-31（closeout/p1-replay-live 全板扫；原注"
                        "『区分力仍等路 A 材料与更多 CC 轨迹』双重失实：路 A 2026-07-27 "
                        "已拉取且已被电池消化——B11 Schema 臂接入、B12 在 Theoria.md "
                        "指定梯度 CC vs Schema 上按局配对执行；S1 战役已把 CC 材料 13 "
                        "倍化并被消化，且同 4 局再多 CC 轨迹统计功效为零——"
                        "discriminate.py 每局折一数，只有新局加对）。四道工序全部已执行"
                        "且机器闸门化：预注册 PREDICTIONS.md 冻结 append-only"
                        "（prefix-sha256，freeze 级强制）；去冗余 B10/B13"
                        "（redundancy.json，一族一代表）；抗游戏 B14 38 exploits → B16 "
                        "V9 盲测 105 攻击（37/38 可游戏）→ B17 对抗复审主表 0/38，V24 "
                        "钉住盲化步 sha 9892d23c；区分力 B9/B12 执行——结果 0/38 可分，"
                        "且这是设计天花板非测量失败：4 局配对最小可达 p=0.125"
                        "（audit/stats.py:166），预注册在先于回算（PREDICTIONS.md:"
                        "385-387）。留 partial 的理由（Theoria.md:325：分不开已知差异"
                        "的指标没资格测未知差异）：工序 1 的通过判定在 4 局开发堆上"
                        "结构性不可达，须 ≥6 局非平局配对（现实 12–17 局）= Phase 4 "
                        "封存堆开局，人间闸门的花费决定（W-13 在案）；预注册确认候选"
                        "今日仅 E4 与 P3。verify 7 级含分离声明真伪门与活臂门；活臂"
                        "读数已到 6 真腿/115 格（measurement-only，不入判别）。",
            },
            {
                "id": "p2-material",
                "label": "材料：CC 基线轨迹 / Schema 复现桶 / 上游 artifacts（限开发堆）",
                "clause": "Phase 2 · 材料",
                "status": "partial",
                "note": "注记重写 2026-07-31（closeout/p1-replay-live 全板扫；原注两处"
                        "失实：『路 A 尚未拉取』——2026-07-27T18:31Z 已拉，"
                        "baseline-arms/SCHEMA_PATH_A.md 收据在案：165 文件/87.7MB 限"
                        "开发堆 4 局，885 个封存局文件经正向白名单默认拒绝"
                        "（fetch_schema_traces.py + 19 例测试），payload gitignored 仅 "
                        "MANIFEST 入库，且已被电池消化（B11/B12）；『sk48 大量/g50t "
                        "少量』——那是 M1 探针表，TOUCHED_GAMES.md 其后已录 "
                        "M4/M5/P-12/S1：四局全 trajectories_reviewed，S1 战役 48 "
                        "episode/1453 动作/$48.39）。三类材料现况：CC 基线成体量；"
                        "上游 artifacts 已拉且受控；Theoria 活轨迹已存在并被电池读取"
                        "（6 真腿/115 格，theoria-arm/runs/ 已提交 A3 legs——本注记"
                        "开始把它计入第三类材料）。留 partial 的理由：标签点名的 "
                        "Schema 复现桶永久不可能（GAP-1：上游从未释出 harness 代码，"
                        "baseline-arms/STATUS.md:335 复核仍立），Theoria.md:311 认可的"
                        "替代（上游轨迹直读）已交付并消化——按 S32『不改定义结案』"
                        "先例，标签字面未清则不绿；若所有者裁定替代即清偿，随判随绿。"
                        "两条已记录的可选网络残项归 baseline-arms：score_trajectories"
                        ".py 未取（SCHEMA_PATH_A §2.2 须另行论证）、上游许可未宣"
                        "（Phase 4 引用/再释出前须结，§7.1）。",
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
                        "**规矩**：此后任何跨门花费必须先在此登记一条，再动手。\n\n"
                        "【补登 2026-07-31·清理战役】编号接续：#1 = 本条上文 $2.53，"
                        "#2 = F-19(5) 的 W-1640 $4.39。以下六笔跨门花费此前未按规矩"
                        "先登记，现补登；补登不是追认。\n"
                        "**#3 M4 试点 $9.8427**（2026-07-27/28；BUDGET_REPORT §2：14 格"
                        "含 2 格被重跑取代照记入账、109 成功动作、960 次 HTTP）。"
                        "**例外依据**：有工单、范围照工单写死（§1）、§8「报告写完即停」"
                        "被遵守；且它先于本登记簿成文。**代价**：jar 关传输层的单价"
                        "已被 §13 取代，引用须走 §13。\n"
                        "**#4 方差包络完成 $10.5364**（2026-07-28，工单 A7；BUDGET_REPORT "
                        "§12：g50t/sk48/tn36 ×3 九格全活、零闸门触发；连同 #1 的 ar25 "
                        "$2.5275，战役全程 $13.0639 = G1 上限的 26%）。**例外依据**："
                        "F-15 裁决「其余 3 局继续 → P-12」，且 §11.5 两件前置"
                        "（跨会话共享闸门、中止阈值）修毕后才续跑。**代价**：⟨n⟩=3 "
                        "必须连同 §12.2 的三条限定（levels_completed 无信号、局间散布"
                        "远大于格内、仅 6 自由度）一起被引用。\n"
                        "**#5 §2.1 重测 $19.83**（2026-07-28，工单 A7；BUDGET_REPORT "
                        "§13：只买 opus/sonnet 两档六格，便宜档复用包络九格未重买，"
                        "事前估 $20.28）。**例外依据**：D-019——战役中途换传输层，"
                        "§2.1 描述的是已不存在的仪器，外推乘数必须重测。**代价**："
                        "opus/sonnet 每档每局仅 1 格、无格内方差，可信度低于 haiku 行。\n"
                        "**#6 $/调用复测 $1.3595**（2026-07-28；BUDGET_REPORT §14，"
                        "共享池 phase3-unit-price-recheck 单列分账）。**例外依据**："
                        "§6 建议 6——批大额前先花约 $2 关掉 $/调用 悬项；预测先写死"
                        "再花钱。**代价**：实测落在预设三分支之外（高侧 6sd），"
                        "分支集合不完备一并照实记录。\n"
                        "**#7 S1 全量战役：自报 $48.39，实际全成本 $50.39**"
                        "（2026-07-28 02:22 UTC+8 起，另一会话四进程并发跑裸 CC "
                        "haiku 档开发堆四局；STATUS.md A14 节、INC-BA-003）。差额 "
                        "$2.0071 是两次被放弃的 harness 启动被重启归零抹掉的"
                        "（GAP-4，runs/20260729T100000Z-a14/RECONCILIATION.md）。"
                        "**例外依据**：有其自己的工单（INC-BA-003 载明两场战役各自"
                        "正当）。**代价**：两套闸门互不可见即开跑，已记为事故 "
                        "INC-BA-003；$50.39 内部精确、外部未经验证（无独立钱账本，"
                        "spend_gate 最早记录晚 6.5 小时）；重启归零缺陷只记未修；"
                        "四场战役当时无 MANIFEST.json，A14 事后补记并标明。\n"
                        "**#8 transport A/B $1.3544**（2026-07-28T02:55Z，arc-recon "
                        "代跑 ar25×haiku×20 两格，PARTNER_SYNC INC-011 段）。"
                        "**例外依据**：所有者指令直接跑；每格 $2.00 上限未接近；"
                        "对方两个 append-only 账本一字节未动。**代价**：账本走 "
                        "untracked 分片（BASELINE_ARMS_SHARD=transport-ab），干净"
                        "检出上读不到——按 A14 自己的标准，它还不算证据。\n"
                        "**对账附记**：BUDGET_REPORT §0/§14.4 的累计 $41.57 漏了 #1 "
                        "的 $2.5275；逐笔合计 #1+#3..#6 = $44.10，另有 #8 的 $1.3544 "
                        "不在该报告任何累计里。#2/#7 记在别的账（theoria-arm / "
                        "对方会话）。该差异归 baseline-arms 领地订正，此处只登记。\n\n"
                        "【预登 2026-07-31·舰队恢复】本次为**先登记后动手**的正身："
                        "所有者当日在会话中批准（「放行包批准，level2 和 S31 探针都烧」）。\n"
                        "**#9 S31 真臂探针**：上限 $0.05 / 10 动作（rung 1 零模型花费，"
                        "4 次 ARC 请求），经 spend_gate.reserve(campaign="
                        "s31-live-arm-probe)，证的是共享账本双轴（真臂身份 × 真上游）。\n"
                        "**#10 A3-campaign-level2**：g50t 第二关带书腿，声明预算 "
                        "$12 / 300 动作（单腿硬顶 $25 之内，池余 $92.42 的 13%），"
                        "经 spend_gate.reserve()；闸门红即停并写 inbox；"
                        "做不完交阶段结果，不降记录标准。"
                        "【#10 结算 2026-07-31】两腿实花 $9.5569 / 18 成功动作，"
                        "两次拦停均为钱闸按设计工作；阶段结果见 "
                        "monitor/inbox/20260731T1420Z-W-1800-level2-carried-phase-result.md。\n"
                        "【#11 结算】33 动作 / 8 调用 / $13.44，闸门按调用天花板拦停；重放失配 4→1、28/29 意外转为主动戳探——但零通关。根因由五路诊断查明：戳探前沿用消融构造，在删子句下向下封闭，构造上不可能含手册所缺的机制（47/52 落在前沿之外）；且 56/56 次 plan 返回 no_goal_declared，零计划零 commit，臂从未试图取胜。\n"
                        "**#14 Phase 3 轮次制**（2026-07-31 起，所有者会话批准「phase3加速迭代」并授两账号额度）：每轮只改一件事、双账号并行两腿、记分板判去留（armtools/round.py 强制 --change，缺则拒跑）。单腿申报 $15 / 300 动作，单轮上限 $30；池余 $143.50 支持约四轮。离线噪声地板已量：21 个记分板列全部零方差，故离线差异即信号，活体方差另计。"
                        "**编号更正 2026-08-02**：本条原以 #12 落盘（af138a0d，23:16:47Z），与 f6a95719（15:06:17Z）已在册的 #12「Phase-3 加速迭代战役」撞号。按 baseline-arms/INCIDENTS.md:7-13 的先例——被外部引用的那条保号、另一条原地改号、撞号记为事件而不是抹平——PARTNER_SYNC.md:1898 与 monitor/runs/20260731T155302Z-P1READJ/RUN_STATE.md:18 两处引用都写在 af138a0d 之前且都指向加速迭代战役，故本条改为 **#14**，位置不动。撞号记为 INC-MON-002；它不只是排版，见该条。\n"
                        "【#14 结算】R1 花 $15.21 却什么都没改——`--change` 是散文、不绑 argv，两条腿跑的是默认值；工具已修（`--knob` 直传 argv，round.json 并排记录散文与 argv）。R1b 真开了开关：臂开始提议目标（3 次/1 次）、模式由沉默转为 exploring_no_goal，但桌面一次未写回手册，plan 状态 16/16 仍是 no_goal_declared、零通关——按预注册判据**未达成**，开关留树默认 off，不作为改进采纳。**R1b 实花 $35.1398，超本条 $30 单轮上限 17%**：g50t-a $17.7491、sk48-b $17.3907，两腿均超 $15 申报值。"
                        "**破口只有一处，在美元轴**：执行者以 --ceiling 25 覆盖了 theoria-arm/armtools/round.py:126 的默认 15.0，预留据此开到 usd_cap $29.00（= 25 + 单次调用余量 $4），见 proxy/var/spend_gate.jsonl:16228/:16229；两腿最后都是撞 $29 被拦停，$15 从未有机会生效。"
                        "**动作轴没有破口**：action_cap 5616 是申报的 300 次动作按池的计量单位（一次出站 ARC HTTP 请求，非记分卡成功动作数）换算的结果，36 + ceil(300 × 9.3 × 2.0) = 5616；合规结算的 #10、#11 同为 5616。**把 5616 除以 300 读成 18.7 倍是两种单位相除**，本行写下这句是为了让那个误读不被重新推导出来。\n"
                        "**#13 超上限续跑裁决（2026-08-01，所有者会话指令「不管预算，全额推进」）**：BUDGET_TABLE 当日实测 programme $250.07 （含 R1b 后约 $285）对 $214.90 上限，remaining_measured_usd 由正转负；钱闸只看得见其中 $113.28，$136.79 是它的盲区（基线臂战役与早于共享池的花费）。已向所有者完整陈述三个选项（认账停火／按 spend_policy 规矩抬上限／裁决口径），所有者选择继续。**如实登记，不追认合规**：$214.90 是 INC-BA-003 算出的两会话合并最坏暴露，越过它意味着那条界限此后不再是界限，论文与释出清单引用预算纪律时必须连同本条一起引。**代价**：freeze/MANIFEST 第 12 项（预算表）不得在超支状态下报 ready；钱闸仍按其可见口径执行（$101.62 余量），它不会因本裁决放宽。"
                        "**数字订正 2026-08-02**：本条引用的 $250.07 / $113.28 / $136.79 / $101.62 取自一份**跑到 R1b 中途**的 BUDGET_TABLE 快照（它把 R1b 两腿记作 $14.7780 / $11.7357，且完全没有 R2b）。按当期账本现算，闸门可见总额为 **$160.9480**（17,329 行，末行 2026-08-02T12:19:04.949Z）；`python freeze/build_budget_table.py --verify` 当期即报 THE BALANCE MOVED。金额以 monitor/money.json 为准。"
                        "**本条不申报任何数字**，所以它不构成后续任何一轮的信封——R2b $39.0392 是记录上最大的一轮而没有自己的额度。#13 是否解除 #14 的 $15/$30 与 #12 的 $75/2500，登记为 needs_human。\n"
                        "**R1 的一件事**：goal_protocol=propose。propose 把目标提议挂在一次由意外已付费的 theorize 调用上，不增加模型调用；预测：plan 状态不再恒为 no_goal_declared，出现非空 tiers 或首个 commit。不达则按失败分类学重分类，不为了有产出而改口径。\n"
                        "**#11 A3-campaign-level2-r3**（2026-07-31，所有者会话批准"
                        "「level2-r3 携 r2 新书继续烧」）：携 r2 修正后成书续腿，"
                        "声明预算 $15 / 300 动作，经 spend_gate.reserve()；"
                        "规矩同 #10：先登记后动手、闸门红即停、"
                        "做不完交阶段结果。\n"
                        "**#12 Phase-3 加速迭代战役**（2026-07-31，所有者会话批准"
                        "「phase3 加速迭代，两个号全部额度」）：多腿多局（仅开发堆"
                        "四局）、双 CLI 账号并行、每腿仍单独经 spend_gate.reserve() "
                        "申报（单腿 ≤$15/300 动作）。**批量上限**：本战役累计 CLI "
                        "$75 / ARC 2500 动作；**止损底线**：池实测余额跌破 $40 即停"
                        "（为 Phase 4 确证留钱）。框架改动照 Theoria.md Phase 3 "
                        "纪律：一次只改一件、变更日志、最小验证复跑；跑腿收数据"
                        "不算框架改动。逐腿花费在各 run 的 MANIFEST 与共享池"
                        "账本自动落账，不再逐腿补登本簿。\n"
                        "**#15 R2 / R2b —— 事后登记**（写于 2026-08-02，花费发生在 2026-08-01）："
                        "R2（04:37Z）两腿 g50t-a / sk48-b 均 reset_failed，理由逐字 "
                        "「RESET did not return 200 after 40 attempts」，0 动作、0 desk 调用、"
                        "0 关、**$0.0000**——**而两腿退出码都是 0**，这条写下来是因为「退出 0」"
                        "在本仓库已经不止一次被当成健康。R2b（04:46Z）实花 **$39.0392**"
                        "（g50t-a $18.7360、sk48-b $20.3032），预留 spend_gate.jsonl:16838/:16839，"
                        "usd_cap 29.0，与 R1b 同、仍高于 #14 申报的 $15 + $4。"
                        "**先登记后动手是本簿的规矩，这两轮违反了它**：#13 落盘于 R2 预留前约 15 秒，"
                        "但它不申报任何数字，所以不是信封。如实记为事后登记，不追认合规。"
                        "**金额以 monitor/money.json 为准**，本条只写判断。",
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
        "id": "F-18",
        "severity": "high",
        "title": "engine-rig 全仓没有留出验证——「已验证」在很多格里的意思是"
                 "「在拟合它的数据上自洽」【已裁决·监控代行：论文改词 + 两件上板】",
        "body": "对偶普查（RES-3 第四路，约 105 处判据点，判不安全 8 处）的最重一条："
                "`grep -ril \"held_out|held-out\" engine-rig/engines engine-rig/tools` "
                "**零命中**，而 `zero_space.verify` 是在**拟合它的同一条轨迹上**复验的——"
                "按 GF(2) 的构造那近乎恒真，那句 AssertionError 几乎不可能触发。\n\n"
                "三条独立发现指向同一件事：DECISIONS 的 D-003 明写 zero_space 只承诺"
                "在观测证据上守恒（边界，不是缺陷）；E9 把 g50t 放在该边界的**已测**一侧，"
                "而那一侧从来没有东西检查过正确性；本轮发现整个 rig 没有留出验证。\n\n"
                "**同一路的正面结果同等重要，不许只报病例**：「求解器返回计划就认定可解」"
                "在本仓库**没有发生**——`fd_adapter` 三档全部无条件 validate_plan()，"
                "且 `validate.py` **刻意不 import `search`**：验证器不认识搜索器，"
                "这是结构保证而非承诺。这是「引擎提议、LLM 裁决」少有的硬证据。\n\n"
                "对偶的真实形状不是「没验」，是**「验了、写进产物、然后不拿它把关」**："
                "`lp_potential/potential.py:255` 的 `\"admissible\": True` 是字面量，"
                "而真检查躺在同一份 payload 的 `admissibility_check` 里；"
                "`deadlock_carver.run()` 是 carve→report→emit 中间没有一个 if，"
                "于是一条定理和一份证伪它的报告并排发布，谁也不压过谁。",
        "action": "【已裁决·监控代行 2026-07-29】(1) 论文改词：在 E17 交付之前，"
                  "正文凡写「已验证」处一律改为「在观测证据上自洽」——不是措辞保守，"
                  "是那些格子当前的真实含义；已写进 P14-honesty-section。"
                  "(2) 两件上板且**不许合并**（验收线一个是接线、一个是新数字）："
                  "E16-verdict-must-gate（两处判决接到头条字段 + 负样本）、"
                  "E17-held-out-validation（ENGINE_TABLE 边界列先写实话，再给 "
                  "zero_space/lp_potential 各补一次真留出验证）。"
                  "依据：RES-3 自己提出的切法，与 A9/V16 同一条——"
                  "把验收线切到能被复核的大小。",
    },
    {
        "id": "F-19",
        "severity": "blocking",
        "title": "Phase 3 钱门 9/16，开发堆战役驳回；k/Δ/B 由监控定"
                 "【已裁决·监控代行 2026-07-29】",
        "body": "W-1640 领到 A3 后没有开跑，先把两件事查清楚再问——停得对。\n\n"
                "**一、钱门红的那几项不是形式主义，是买回来的数据不能用。**"
                "`proxy/var/ledger.jsonl` 里只有 mock_arm 与 replay，**零条真臂记录**，"
                "而 A3 的全部产出就是论文图 2 的账单形状；没有三臂同账本，"
                "那张图跨臂对不上账。真臂另有 **66 条 `bypass_attempt`**，"
                "而封存保证恰恰要在会去打真 API 的那条臂上成立。"
                "级联裁决则自相矛盾：`CASCADE_RULING.md` 只在未合并分支上，"
                "master 的 `ACCESS_CHECK.md:105` 还写着相反的结论。\n\n"
                "**二、对账义务当前不可清偿**：分数字段 API 不返回，而规则要求逐条比分。"
                "一条做不到的义务留在纸上，等于让这道门永远红着而没人知道为什么。\n\n"
                "**三、INC-TA-001 仍未修**（两个会话各算各的账），提议的跨会话锁不存在。"
                "RES-1 已死九小时，把战役交给开放工人池正是产生那条规矩的场景。\n\n"
                "**四、退出条件的三个数在 Theoria.md:357 全是尖括号占位符**，"
                "且 Δ 的分母从未消歧——而 F-13 已裁定 Schema 复现不可能、主表复现值"
                "合规留空，所以「Schema 复现值」这个强读法**在我们自己的裁决下无分母可用**。",
        "action": "【已裁决·监控代行 2026-07-29】(1) 驳回现在花游戏钱；A3 保持 "
                  "`spend: api` 且不下放通用工人。(2) 解锁路径上板："
                  "A10-shared-ledger-real-arms（含把对账口径改为成本×动作数×回合数"
                  "三元组，分数改为各臂自报并标注不可交叉核验）、"
                  "A11-bypass-attempts-explained（66 条逐条分类，真绕过当场修+负样本，"
                  "结论与 proxy 侧分列两行）；两条搁浅分支由 S24 合并。"
                  "三件绿了立刻在 A3 写 `generic_ok: yes` 放行。"
                  "(3) k/Δ/B 暂定：**k=3**（四局中三局达 U3，留一局作堆内留出）；"
                  "**Δ=10 个百分点**，基线改用上游释出的开发堆四局轨迹分数（F-13 的路 A），"
                  "逐局算不出则退到裸 CC 42.83% 并在论文写明此时 Δ 是地板上的余量、"
                  "不是天花板下的让步；**B=$60**（$214.90 上限中划给开发堆），"
                  "留足封存确认跑——那一跑才是 Phase 4 的主终点，不能被开发堆饿死。"
                  "(4) 三个数写进 Theoria.md 的动作另派，本条留 diff 审查。"
                  "(5) **跨门花费已发生，按 p3-gate-exception 的规矩在此登记**："
                  "W-1640 于 00:29–00:37Z 在 g50t（开发堆，非封存）上花了 **$4.39**"
                  "（四笔，最后一笔 $4.00），全部经 `spend_gate` 记账、逐笔可查。"
                  "**授权是我签的**——上一跳我在认领文件里写了 `generic_ok: yes` 并写明"
                  "批准理由，工人照办，它没有越权。我是在读到它这份升级件之后才发现"
                  "钱门红在「买回来的数据不能用」上，于是反悔。所以这条要记的教训不是"
                  "「工人乱花钱」，是**我在信息不足时签了字，而签字比撤销快**："
                  "此后 `spend: api` 的批准必须先看该条目自己的阻塞清单，不能只看余额。"
                  "(6) **订正（同日第二次）：驳回的第一条理由被 W-1641 用文件行号推翻，撤回。**"
                  "`figures/fig02_bill_shape.py` 读四个来源，没有一个是 "
                  "`proxy/var/ledger.jsonl`，`_classify()` 还明确拒绝 v1.0 是第三种方言，"
                  "消融臂在图 2 里根本没出现——「没有三臂同账本⇒图 2 对不上账」不成立。"
                  "驳回仍然有效，但只剩三条：66 条 bypass_attempt、级联裁决自相矛盾、"
                  "以及门本身 9/16 加 INC-TA-001 未修。"
                  "**对账口径也订正**：`turns` 字段账本里不存在（INPUT_FORMAT gap 5），"
                  "我用一条不可清偿的义务替换了另一条；口径改为 cost × actions，"
                  "turns 记为显式缺口且不投票。分数**不是整体不可核验**——记分卡 close "
                  "响应带 score（SCORING.md:40-44，32 张真卡），缺的只是 per-step。"
                  "(7) 顺带记一条同族教训（W-1641 也自陈犯过）：**工单不得引用只存在于"
                  "未合并分支上的文件**——把另一条分支的产物当成树上的现状，"
                  "会让实现者按一份不存在的规范施工。",
    },
    {
        "id": "F-20",
        "severity": "blocking",
        "title": "十三个 agent 的独立审计：监控高估约 11.5 个百分点，50.0 → 38.6"
                 "【已裁决·监控代行：数字已改】",
        "body": "六个子系统各一名审计员从仓库独立重推进度，每份结论再交一名对抗性复核员"
                "默认认为它错去反驳。**系统性偏差有明确形状**：把「造好了并自检通过」"
                "记成「已验证」，把落在**未合并分支**上的交付物记成 done。\n\n"
                "落在未合并分支上却已按 done 计分的：`ENGINE_TABLE.md`（E9 已归档 done）、"
                "`BATTERY_V1.md` 与 `battery/verify.py`（V5-battery-freeze 已归档 done）、"
                "`arc-recon/local_engine_guard.py`（封存护栏另一半）、13 份基准真值的修复"
                "（`23ec179`）。**工作板的 done 与 master 的内容是两件事，而计分只看了前者。**\n\n"
                "最大的三处：**WP8 55→15**——`freeze/` 目录在**任何分支上都不存在**，"
                "`S4-freeze` 自己点名的四个交付物一个也没有；**WP2 95→73**——"
                "「双代理」实为一个，`theoria-arm/evidence/model-proxy-401.jsonl` 131 条里"
                "65 条 model_call 全是 401，哈希链只覆盖 33/387 条且**全部写在本地 mock 上**，"
                "所有打真 API 的账本 verify_chain 返回 UNCHAINED；**WP5 90→71**——"
                "考卷四题型只上线一型（`exam/runs/.../GAPS.md:4` 原文 One shipped. Three did not），"
                "区分力跑完分离出的指标数是 **0**（23 no-data / 8 underpowered / 7 not-ranked）。\n\n"
                "**两处监控低估**：S5 20→45（台账 26 条 + 1951 行 MANIFEST + 负控制先跑的 "
                "verify.sh，全在 master）、E3 5→25、E5 20→45。"
                "**五处审计员的下调被复核员驳倒**（C5/A1/A2/A5/V3），保持原值——"
                "其中 A2 的下调依据是过期的，C5 的清单不全是枚举时序而非漏收。\n\n"
                "**最锋利的一条自指**：`scan.py:199-216` 的 `probe_a1_state` 算出 `bridge` "
                "与 `consumed` 两个布尔量、塞进 detail 字符串，然后**无条件返回 partial**——"
                "两个布尔量从不参与判定。而 Phase 1 这道门后面挂着 WP6+WP7+WP8 共 0.31 权重。"
                "**一个关不上的门就是一个会被跨过去的门**，而它确实被跨了。",
        "action": "【已裁决·监控代行 2026-07-29】(1) GRID 十八格与 PAPER_PLAN 八项已改成"
                  "审计值，headline 50.0 → **38.6**（审计自述精度不高于 ±3 点，"
                  "但方向比小数点可靠）。(2) 计分口径改正：**一件交付只有进了 master 才计分**，"
                  "板上 done 只代表工人交了活；差额由合并队列负责，不该由计分掩盖。"
                  "(3) 上板：S25-probe-the-merge-queue（21 个探针没有一个读 merge.log，"
                  "所以五条分支被重刷 FLAG 十小时在仪表盘上完全不可见）、"
                  "S26-phase1-gate-must-decide（probe_a1_state 那个无条件 return）。"
                  "(4) 我核过审计的一处告警并推翻它：那条「还在写盘的 leg」自 00:40Z 起"
                  "1282 条记录**花费 $0.0000**，全是 pytest 夹具与金丝雀，总额仍是 $36.14。"
                  "没有钱在动，不需要人介入——**审计员在正确的方向上把急迫性说大了**。",
    },
    {
        "id": "F-21",
        "severity": "blocking",
        "title": "这个代码库没有第三个值：28 处「测不到」被写成了「测了，没问题」"
                 "【已裁决·监控代行：四处当场修，其余四件上板】",
        "body": "57 个 agent 的对抗性普查（每条候选都由一名默认认为它错的复核员反驳过）"
                "留下 28 条。**它们全是同一件事的不同写法**：计数器的默认是 0"
                "（无活可做／无违规／板见底），布尔的默认是 True（还活着／干净／"
                "没被禁用／未超支），集合的默认是空（无欠回执／无越界分支），"
                "异常处理的默认是 `pass`。**没有一处区分「我看了，是零」和「我没看成」。**\n\n"
                "最重的三条：`dispatch.pid_alive(0)` **恒为真**"
                "（tasklist 会返回 System Idle Process 那一行），而任务表在本机不给 "
                "PID 字段、抓取循环无声退回 0——66 条注册项里 62 条读作「还在跑」；"
                "`arc-recon/contamination.py:163` 用 HTTP 账本的字段去读只有 `game_id` "
                "的 episode 账本，于是 560 条记录读出零接触并印成「sealed ADDRESSED: NONE」，"
                "**而这个绿灯已经落进 `claim_set.json`**；`release/enumerate.py:123` 的空 id "
                "列表让 33 个 B→A、223 个 C→A 全部滑向「可发布」。\n\n"
                "**第二层规律更刺眼：出问题最多的是补丁本身。** dispatch 的 pid 抓取"
                "**正是为了修 `pid: 0`** 而加的，它在本机的失败模式是返回同一个 0；"
                "`check_redlines` 建了 `json_shaped` 按字节判类，`enumerate` 没接上；"
                "`check_sealed` 补了 piles 形状守卫，`_arc_game_ids` 没补；"
                "`bus.py` 声明了 `ACK_REQUIRED`，两个消费端各自手打了缩水的元组。"
                "**修复恢复了症状，同时让问题看上去已被处理。**",
        "action": "【已裁决·监控代行 2026-07-29】(1) 四处当场修并跑过："
                  "`pid_alive` 加 pid<=0 守卫且 quota 改为引用同一份实现；"
                  "reflex 认「正在运行」（中文控制台里 `\"Running\"` 一次也没命中过，"
                  "于是 live_workers 恒 0、补员循环每跳按满员拉人）；"
                  "reflex 读不到内存改为 0.0 并发 `mem-unreadable` 事件（原为默认 99GB 的 fail-open）；"
                  "`--lane` 自报身份不再能绕过花钱守卫（`claim W-9999 --lane campaign` "
                  "此前可领走真 API 战役且日志与批准过的认领逐字相同）。"
                  "(2) 其余上板四件：A13-sealed-audit-reads-the-wrong-fields（p1，封存守门人）、"
                  "S29-measurement-missing-is-not-zero（proxy 的三处「量不到=0」）、"
                  "R3-release-classifier-defaults（释出分类器的默认值全指向可发布）、"
                  "S28-no-third-value-in-the-monitor（监控自己剩下的 11 处）。"
                  "(3) 全体要求：**逐条修、逐条配阴性样本，不许打包成一次「已全部加固」**——"
                  "本仓 20 道闸门里 19 道从没被证明能变红，而普查的第二层结论正是"
                  "「出问题最多的是补丁本身」。",
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
    {"id": "WP1", "name": "框架本体与离线验收", "weight": 0.15, "pct": 91,
     "slot": "§3 框架 · 图5 DC22案例 · 图6 概念时间线",
     "scale": "对标：Schema 的 world_model.py 方法论一节。我们：DSL+四形态+六/八引擎+A0/A0′/A1/A2 四件离线验收",
     "evidence": "六引擎 + M9 + FD 三档定价 + 500 世界 23 不变量零违规；世界工厂 20 世界；契约 v0.3；A0/A0′/A1/A2/A3 五件离线验收全绿"},
    {"id": "WP2", "name": "封闭系统与外壳可信度", "weight": 0.08, "pct": 73,
     "slot": "§2 方法可信度（密封/复放/对账）",
     "scale": "Schema 无此层（其复现失败正是教训）。我们：双代理+护栏+对账+复放抽检",
     "evidence": "双代理 + 花费闸门（对抗测试先破五种绕法）+ 金丝雀日检 + 预检 4/4 + 熔断器自动出闩；留痕正典化"},
    {"id": "WP3", "name": "Theoria 臂在线迭代战役（开发堆）", "weight": 0.20, "pct": 18,
     "slot": "§5 实验主体 · 图2 账单形状（Theoria 列）",
     "scale": "对标：Schema 25 局全集单臂全跑。我们：4 局 × 迭代至退出条件（U3≥k 局 + Δ 内 + 账单形状可见）",
     "evidence": "臂在线链路通、preflight 零计费；战役第二关在跑（RES-1 常驻推进）"},
    {"id": "WP4", "name": "对照臂数据（CC 包络 + Schema 路A + 消融臂）", "weight": 0.08, "pct": 45,
     "slot": "表1 主表另两列 · §6 消融",
     "scale": "CC：4 局×3 重复；Schema：上游 artifacts 开发堆子集直读（F-13 口径）；消融臂：−定理义务",
     "evidence": "裸 CC 包络 + 上游 165 文件 + 消融臂建成并有闸门（a0 可解 / a2 不可解判决正确）"},
    {"id": "WP5", "name": "评测两器：电池冻结 + 考卷构造器", "weight": 0.10, "pct": 78,
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
    {"id": "WP8", "name": "预注册与统计裁决（冻结清单 13 项）", "weight": 0.05, "pct": 40,
     "slot": "§5 统计口径 · 双结局文本",
     "scale": "三主终点（U3 达成率/判决题准确率/前载指数）+ Wilcoxon 配对 + n 由包络方差定",
     "evidence": "冻结包起草 + Phase 1 收口交付；统计规则草案在盘"},
    {"id": "WP9", "name": "论文写作（workshop 文 → 主文）", "weight": 0.05, "pct": 67,
     "slot": "全文（3.2 的八节骨架）",
     "scale": "Phase 1 结 workshop 文（P-16 在跑）→ Phase 3 结案例研究 → 主文",
     "evidence": "PAPER.md 2512 行成稿，含引文核查、评审分诊、待办清单；五视角评审在跑"},
    {"id": "WP10", "name": "释出包（Schema 地板对齐）", "weight": 0.03, "pct": 55,
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
    "E2": {"pct": 95, "note": "held_out 已进 engine-rig；ENGINE_TABLE 边界列在 master", "active": ["P-13"]},
    "E3": {"pct": 25,  "note": "引擎在线供货（经 theoria-arm 调用）", "active": []},
    "E4": {"pct": 0,  "note": "封存战役中的引擎供给", "active": []},
    "E5": {"pct": 45, "note": "MANIFEST 中 engines/ 40 文件全 class A releasable；306 哈希 match / 18 stale", "active": []},

    "C1": {"pct": 75, "note": "四手册探针 4/4、4/4、2/4、2/4；gen_pddl 不健全被自家测试钉成事实", "active": ["C1-worldgen", ]},
    "C2": {"pct": 90, "note": "三态不变量已在 master（unverified 与 holds 分开），世界工厂基准真值不再把未检查写成成立", "active": []},
    "C3": {"pct": 20,  "note": "在线两本书：首局的 theory.dsl 尚在 P-8 分支里", "active": []},
    "C4": {"pct": 0,  "note": "封存局的证书生产线", "active": []},
    "C5": {"pct": 60, "note": "四形态 + Lean + 移交包随释出", "active": ["P-19"]},

    "S1": {"pct": 80, "note": "模型代理零真实流量（131 条 401 存档）；proxy 账本零真臂记录", "active": []},
    "S2": {"pct": 70, "note": "封存零接触已独立复算属实；但护栏另一半不在 master、金丝雀日检只跑过一天", "active": ["P-20"]},
    "S3": {"pct": 70, "note": "花费闸门是全仓最真的东西；但哈希链只覆盖 33/387 且全是本地 mock，链头从未发布", "active": []},
    "S4": {"pct": 45, "note": "freeze/MANIFEST_DRAFT.md 已在 master——审计当时它在任何分支上都不存在", "active": ["P-22"]},
    "S5": {"pct": 45, "note": "台账 26 条 + 1951 行 MANIFEST + 负控制先跑的 verify.sh，全在 master（监控此前低估）", "active": []},

    "A1": {"pct": 88, "note": "裸 CC 全套 + 消融臂建成并带闸门", "active": ["P-18"]},
    "A2": {"pct": 95, "note": "五个自建世界 + 双 A0 互考 + 消融对照", "active": ["A2-crosscheck", "P-17"]},
    "A3": {"pct": 12, "note": "唯一真跑 12 动作、$4.39、budget_exhausted；全树零 RUN_STATE 有 level>1", "active": ["P-12"]},
    "A4": {"pct": 0,  "note": "封存战役（门槛：Phase1 全绿 + 冻结提交）", "active": []},
    "A5": {"pct": 0,  "note": "主表三列 + 消融列", "active": []},

    "V1": {"pct": 85, "note": "电池真跑 95run×5臂×38指标；但 BATTERY_V1.md 与 battery/verify.py 不在 master", "active": []},
    "V2": {"pct": 80, "note": "考卷泄漏闸门已有 token 级检查（master 可见），整值分桶不再是唯一判据", "active": []},
    "V3": {"pct": 70, "note": "区分力为零这个结论已写进产物并可引用（separating 在 master 可见）", "active": []},
    "V4": {"pct": 0,  "note": "封存回算 + 判决题实考", "active": []},
    "V5": {"pct": 70, "note": "SOURCES.sha256 里已无 ABSENT0000，四份实盘账本入库后哈希已重登记", "active": ["P-21"]},

    "P1": {"pct": 85, "note": "方法论与骨架", "active": []},
    "P2": {"pct": 82, "note": "papers 已自带 verify.py 闸门；正文与审计的覆盖差距由 P18 在处理", "active": ["P-23"]},
    "P3": {"pct": 35, "note": "四样材料三样是离线的，第四样不在正文；线上只有 preflight 与一局首触", "active": ["P3-case-study", ]},
    "P4": {"pct": 15, "note": "预注册包不存在；k/Δ/B 由监控在工单里暂定——工单里的决定不是预注册", "active": []},
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
