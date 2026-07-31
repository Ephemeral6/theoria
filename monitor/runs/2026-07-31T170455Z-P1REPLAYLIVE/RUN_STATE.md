# RUN_STATE — P1REPLAYLIVE · Phase 1/2 收口：复放抽检落真在线账本 + 全板扫重裁

分支 `closeout/p1-replay-live`，基 `d854632`（开工时最新 master）。两段式收口：
第一段**执行**了 p1-replay-audit 一直欠着的真在线抽检（不是纯裁决——真跑了仪
器）；第二段对 Phase 1/2 余下 partial 全板扫，按盘上证据重裁 6 项。全程离线、
零 API 调用、$0.00、零封存堆接触、无凭据值（凭据仅由对抗复核经 client.py 的
mask() 比对，未打印）。

## 第一段 · 复放抽检落真在线正典账本（S31 起）

材料（全部开发堆；inputs.json 逐一 sha256）：

* **g50t-5849a774**：theoria 臂三条真腿（A3 level2-carried r1/r2/r3，已提交
  正典 v1.0 账本，env_upstream 全为 three.arcprize.org）。
* **ar25-0c556536**：S31 真臂探针（bare_cc）的单条 RESET，proxy/var/ledger.jsonl
  （gitignored），四条记录逐字节摘录入 `evidence/s31_ar25_ledger_excerpt.jsonl`。
* 档案基线：P-9（ar25 16 局）与 P1-replay-spotcheck-2（g50t 26 局）经
  `upgrade_ledger` 从 tracked shards 重建正典后逐位复现（regression match）。
* **排除**：`20260731T1500Z-A3-sk48-carried-l1` ——开工时正在飞行
  （RUN_STATE finished=false，文件开工前 2 分钟仍在写）；其后由属主会话收官
  入库，本件仍不把它计入两局主张。

方法：`spotcheck_live.py`（本目录，monitor 领地；只读 import proxy 的
replay_spotcheck/ledger，一字未改 proxy/）。臂账本开局全是占据 step_idx 的重试
400，裸喂 clean_prefix 得零可用会话——适配器按 sessions_from_recon 先例：成功
RESET 开新 pass、位置按成功命令连续编号。适配器的三条诚实性前提已断言并发布
（adapter_honesty.json，violations=0）：失败步必无帧（646/646）、无被弃命令
（0/646）、每账本单 run_id。

数字（summary.json；各报告 comparisons[] 可逐位核）：

| 检查 | 局数 | 位置 | 成对比较 | 失配 | 判定 |
|---|---|---|---|---|---|
| g50t 活腿互比 | 3 | 10 | 22 | 0 | PASS |
| g50t 档案+活腿 | 29 | 6 | 1304 | 0 | PASS |
| ar25 档案+S31 | 17 | 9 | 388 | 0 | PASS |
| sk48 补充（S31 前真腿，不计入两局） | 5 | 5 | 34 | 0 | PASS |
| 回归：ar25 16/9/372、g50t 26/6/971 | — | — | — | — | match |

* **活证据深度如实**：ar25 的活贡献只有位 0 一帧（388 对中 16 对涉 S31）；
  两局主张的主力是 g50t（三条独立活腿 10 位逐比特一致）。报告内已披露。
* 完整性：1315 个带帧步的 frame_hash 从存储帧重算 **0 不符**
  （integrity_hash_recompute.json）——「逐比特」是对帧本体的陈述。
* 档案输入钉子 9/9 逐字节吻合；重建正典摘要 5/5 漂移，**真因是
  upgrade_ledger 把调用路径写进 lifted.source**（路径依赖，非 shards 移动；
  已派 proxy 领地工单），regression_vs_archive.json 内 pinned_digest_comparison
  为证。
* **r3 遗留 replay_mismatch 裁定**（adjudication_r3_replay_mismatch.json）：
  certify.py 拿手册预测对单次观测，结构上与环境确定性无涉；6 条记录中 5 条
  恰在环境跨局逐比特复现的位置上，第 6 条（r2 t=9）在共享前缀之外，无跨局
  证据（两个方向都没有）。
* **对抗复核**：3 个独立怀疑者（适配器诚实性/数字与溯源/红线与措辞），对
  报头数字的反驳：零；所有 material/minor 发现（排除清单键空间 bug、硬编码
  结论句、漂移归因错误、NOTES 游戏名笔误、inputs 缺项）已修复后重跑，
  OVERALL PASS。怀疑者 2 曾把全部四份报告在 comparisons[] 级逐字节独立复现。

## 第二段 · 全板扫重裁（16+3 项逐一对条款）

| 项 | 前 | 后 | 依据（一句） |
|---|---|---|---|
| p1-replay-audit | partial | **green** | 两局档案抽检 + 本件真在线并入，数字见上表 |
| p1-cascade | partial | **green** | CASCADE_RULING.md 已把条款四问全裁掉；「未观测」在原注写下前一天即为假（precheck 2026-07-27 已见 7 帧）；cascade/verify.sh 本件复跑 PASS；W-1250 提议在案三天未执行 |
| p1-access | partial | **green** | 原注两个未结项均已关闭：全量残留 2026-07-30 两次 full 扫 20/20（e0db135f）；速率 600 RPM 官方原文两处 + 产品无配额概念（TERMS §7.5） |
| p1-variant | partial | **green** | 条款三问（合法集冻结/构造性依据强制/规格哈希入账）俱清且经密封演练 10/10 oracle 交叉验证；与 0/65 的模型代理不同类；「从未活用」如实入注但条款不要求 |
| p1-scorer | partial | partial·注记重写 | 冻结已成、对账 37 run 26 PASS/0 FAIL/11 丢卡（监审复算 score_corpus.json，含 4 条 theoria 真腿全过）；「跑完即打分」从未活局执行，归 DELIVERY_RULING §4；收窄结案须所有者明判（S32 先例） |
| p2-audit | partial | partial·注记重写 | 四道工序全部已执行且闸门化；真门槛是 ≥6 局非平局配对 = Phase 4 封存堆，不是「等材料」（原注双重失实） |
| p2-material | partial | partial·注记重写 | 路 A 四天前已拉且被消化、S1 1453 动作、活轨迹应计数；唯一缺口复现桶系 GAP-1 永久外部不可能——按 S32 不改定义，留所有者裁决点 |
| 其余 9 项 | — | 未动 | p1-proxy-env/runner/determinism/cut/a0/a1/a2/engines、p2-battery 原绿未触碰 |

**未动而有据的三个 partial**：p1-proxy-model（所有者出资点，S32 段落在案）、
p1-seal-test（右合取项系 D-P8-002 设计选择 + GAP-5，注记为 P1READJ 当日新写）、
p1-same-shell（DELIVERY_RULING §4 两行 open·unassigned，注记为 P1READJ 当日新写）。

**跨领地缺陷派单**（本件只登记不修）：① upgrade_ledger 路径依赖（proxy）；
② CASCADE_RULING §5 反驳计数器未实现 + grammar_card.py:25 值对理由错
（theoria-arm）；③ exam/verify.py 改写自己该比对的工件（exam）。

## Inputs（全部只读，一个未改）

18+ 项输入的 sha256 在 inputs.json；证据路径清单另见各报告的 sources 字段。
读过而未哈希的裁决依据：Theoria.md、CASCADE_RULING.md 及 cascade/、
ACCESS_CHECK.md、TERMS.md、SCHEMA_PATH_A.md、TOUCHED_GAMES.md、battery/
STATUS+BATTERY_V1+PREDICTIONS、exam/SEALED_DRILL.md、proxy/variants.py+
scoring/+DELIVERY_RULING.md、DUAL_PROXY.md、W-1250 inbox 件。

## 验收例外披露（--allow）

工单 verify.sh 的封存局红线对 monitor/spec.py、monitor/state.json、
monitor/index.html 三个路径 `--allow`：命中的三个封存 id（其一系 p1-a2 的
展品标签，另二系 p1-cut 注记里 F-11 的隔离登记——id 本体见该两条注记，此处
不复写）在基 `d854632` 的 spec.py 中即各有一处，本分支 diff 一处未增
（`git diff d854632 -- monitor/spec.py` 加行中三 id 计数为 0）；
state.json/index.html 为 scan 对 spec 的镜像。这些文件的职责本就包含登记
污染裁决，属技能文档明写的正当例外。

## Gate outputs, verbatim

* `python monitor/scan.py` exit 0，逐字
  `[2026-08-01 01:44:00] monitor/index.html written — Phase 1: 12/16 green`。
* `python -m pytest`（monitor，worktree 内）：**525 passed, 2 xfailed**，
  exit 0——与开工基线逐数相同（无测试钉死绿数，重裁不碰行为）。
* `spotcheck_live.py` 尾行 `OVERALL: PASS`；`score_corpus.py` 汇总
  `26 PASS / 0 FAIL / 11 UNDETERMINED`；`bash cascade/verify.sh`（worktree，
  THEORIA_ENV 指主检出 .env）`"verdict": "PASS"`。

## 收口结论

Phase 1 **12/16 绿**（9→12：三个翻绿全部是「证据早已在盘上、注记从未跟上」，
其中两个 W-1250 三天前就提议过）；Phase 2 1/3 绿不变（两 partial 注记重写为
真实门槛）。**「全绿才准烧游戏钱」的门照字面仍不满足**——余下 4 个 partial
中 3 个卡在所有者决策点（出资/收窄明判/改判标签），1 个卡在跨领地接线
（DELIVERY_RULING §4）；全部在案，无一是本件能替人做的。
