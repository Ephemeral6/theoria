# MANIFEST_DRAFT.md · Phase 4 冻结清单（草案）

**状态**：草案 v0.1，S4 起草，**未冻结**。
**上位文本**：[Theoria.md](../Theoria.md) Phase 4「冻结清单（首局开跑前提交，全部哈希）」
——十三项，逐条列在下面。
**勘察基线**：`master` = `7cb6775`（2026-07-28）。下面的路径与版本串按该提交勘定；
真正冻结时全部重勘一遍并附 sha256。

**这份文件回答一个问题**：Theoria.md 说「全部哈希」的那十三样东西，今天在树上分别是
什么、有没有一个版本号可以指、缺的缺在哪。**缺的照写缺**——冻结清单最危险的失败模式
不是缺一项，是把一项含混地写成「有」。

---

## 0. 一眼看完

| # | 项 | 判定 | 一句话 |
|---|---|---|---|
| 1 | 内环代码 | **PARTIAL** | 目录齐整，但零版本把手，只能按 SHA 冻 |
| 2 | DSL 语法（两本书） | **PARTIAL** | 契约文本自称「冻结于携带此行的 tag」，**那个 tag 不存在** |
| 3 | 生成器 | **PARTIAL·歧义** | 「生成器」有两种读法，须先裁决指哪一个 |
| 4 | 提示词 | **PARTIAL** | 无 `prompts/` 目录，提示词是源码里的字符串常量 |
| 5 | 引擎清单与版本 | **PARTIAL（十三项里最完整）** | 八台引擎一一对应已有 tag |
| 6 | 戳探策略 | **PARTIAL** | 策略散在两轨道的 docstring 里，无单一文档 |
| 7 | 规划器配置 | **PARTIAL** | **没有配置文件**，每个旋钮都是源码字面量 |
| 8 | 指标电池 v1 | **PARTIAL·版本冲突** | 「v1」已经指不出唯一状态（v1/v2/v2.1 三处打架） |
| 9 | 变体算子库 | **PARTIAL·两套** | 两个互不相干的算子代数，须裁决冻哪个 |
| 10 | 统计裁决规则 | **本轮补齐** | 机器有（`battery/audit/stats.py`），规则文本本轮才写 |
| 11 | claim 逐字文本与双结局 | **本轮补齐** | 此前**完全不存在** |
| 12 | 预算表 | **PARTIAL** | 价目表与闸门齐备；Phase 4 的三个数仍是 ⟨…⟩ |
| 13 | 每格重复数 ⟨n⟩ | **MISSING·被别的活挡住** | 见 [PENDING_FIVE.md](PENDING_FIVE.md)，不是文书问题 |

**没有一项是 READY。** 十一项 PARTIAL、一项本轮补齐、一项被上游活挡住。这不是坏消息，
是这份草案存在的理由：Phase 4 的门是「全部哈希」，而今天连「哈希什么」都还没定完。

---

## 1. 内环代码

| | |
|---|---|
| 路径 | `theoria-arm/inner/`（`loop.py` `theorize.py` `certify.py` `probe.py` `plan.py` `commit.py` `books.py` `surprise.py` `grammar_card.py`）；外围 `theoria-arm/harness/`、`world/`、`armtools/` |
| 版本把手 | **无**。无 `__version__`、无 tag。`theoria-arm/STATUS.md` 记里程碑 P-8，base `df9f748`，46 项测试 |
| 判定 | **PARTIAL** |

内环五拍（theorize → certify → probe → plan → commit）一拍一个模块，边界与 Theoria.md
1.10(d) 对得上，这一项的**内容**是齐的。缺的是把手：冻结只能按 commit SHA。

**冻结前须办**：切一个 `theoria-arm-freeze-v1` tag；把 `theoria-arm/GAPS.md`（未清的
契约回读项）逐条了结或明确标为「带着缺口冻结」。

## 2. DSL 语法（两本书）

| | |
|---|---|
| 路径 | `CONTRACTS/dsl_grammar_v0.1.md`、`CONTRACTS/dsl_grammar_v0.2.md`（两本书都在：`theory.dsl` 在前，`playbook.dsl` 在 §L262）；可执行形态 `theory-compiler/src/theory_compiler/parser/theory_parser.py` + `playbook_parser.py` |
| 版本把手 | 文档头 `**Version:** 0.2 · Effective: 2026-07-28`；v0.1 声明未改一字 |
| 判定 | **PARTIAL** |

**一处必须点名的缺陷**：`dsl_grammar_v0.2.md` 写着 v0.2「冻结于携带此行的 tag」——
**该 tag 不存在**。整个 v0.2/v0.3 的演化政策挂在一个空引用上。冻结前要么把 tag 切出来，
要么改掉那句话；**保持现状等于清单里有一个查不动的版本串**。

**另一处**：`theory-compiler/src/theory_compiler/parser/theory_grammar.lark` 是**死文件**
（自带的头注释写明「NOT THE PARSER IN USE」，且没有 `semantics:` 产生式）。
清单里必须**显式排除**它，否则读者会以为语法的权威形态是那份 lark。

## 3. 生成器

**这一项要先裁决歧义，再谈冻结。** 树上有两样东西都叫「生成器」：

* **(a) 编译器后端** —— `theory-compiler/src/theory_compiler/generators/`：
  `gen_python.py`、`gen_lean.py`、`gen_lean_deadlock.py`、`gen_pddl.py`、`gen_markdown.py`。
  版本把手 `theory-compiler/pyproject.toml` `version = "0.1.0"`。
* **(b) 世界生成器** —— `worldgen/generate.py` + `worldgen/catalog/*.json`（20 个世界，
  逐世界整数种子 101–302）+ `worldgen/mechanisms/`（7 个机制族）。无版本号，靠种子与
  逐字节可复现建构。

**建议裁决：Theoria.md 此处指的是 (a)。** 依据是 Phase 4 冻结清单的上下文——它列的是
「内环代码 / DSL 语法 / 生成器 / 提示词」，这是 1.10(a)「两件手写物，一组生成物」那条
链上的生成器，即 DSL → 四形态的编译后端。**(b) 属于 A0 自建世界族，是 Phase 3 的开发
用具，不进封存战役的因果链。**

**若采纳该裁决**，(a) 今天即可冻；**若不采纳**，(b) 另有一处未了：
`worldgen/RUN_STATE.md` 记录 QC 门槛**没达到**，证据在 `worldgen/qc/QC_REPORT.md`。

## 4. 提示词

| | |
|---|---|
| 路径 | **没有 `prompts/` 目录。** 活的提示词是 Python 字符串常量：`theoria-arm/inner/theorize.py` 的 `PREAMBLE`(L122)、`OUTPUT_CONTRACT`(L169)、`build_prompt()`(L204)；`theoria-arm/inner/grammar_card.py` 的 `CARD` |
| 版本把手 | **无** |
| 判定 | **PARTIAL** |

**一处结构性风险**：Theoria.md Phase 3 的防过拟合硬规是「提示词不得含任何游戏特定内容，
每次迭代做 diff 审查」。树上**没有执行这条规则的检查**——`tests/test_grammar_card.py`
只做编译检查，不做泄漏检查。冻结一份没有泄漏检查的提示词，等于把那条硬规交给自觉。

**冻结前须办**：把提示词抽成数据文件（或至少抽成可 dump 的常量），加一条泄漏检查
（游戏 ID、局名、机制名的黑名单扫描），检查本身进冻结包。

## 5. 引擎清单与版本

| | |
|---|---|
| 路径 | `engine-rig/engines/` 八台：`mdl_segmenter`、`cegis_miner`、`zero_space`、`lp_potential`、`fd_adapter`、`probe_frontier`、`deadlock_carver`、`ic3_pdr`。名册表在 `engine-rig/STATUS.md`。冻结输出流 `engine-rig/artifacts/candidates.jsonl`（44 条，逐字节稳定） |
| 版本把手 | 逐引擎**无版本字段**，但一一对应已有 tag `engine-rig-m2` … `engine-rig-m9` |
| 判定 | **PARTIAL（十三项里最完整的一项）** |

外部工具链的钉版见 §14。

**注意 Theoria.md 主表里写的是六台引擎**，树上是八台（多出 `deadlock_carver` 与
`ic3_pdr`，都是 M9 的产物）。**清单要写八台，并注明设计文档的六台是早于它们的文本**
——这不是矛盾，但不点破会被当成矛盾。

## 6. 戳探策略

| | |
|---|---|
| 路径 | 分在两轨道：`theoria-arm/inner/probe.py`（消融前沿、单位成本熵、先写预测再行动）+ `engine-rig/engines/probe_frontier/`（`frontier.py`、`reach.py`、`scenario.py`、`sokoban_probe.py`、`README.md`） |
| 版本把手 | **无** |
| 判定 | **PARTIAL** |

**没有单一的策略文档**：策略以 docstring 的形式活在两个互不 import 的包里。冻结这样
一项，读者拿到的是两份可能已经分叉的说法。

**冻结前须办**：写一页 `PROBE_POLICY.md`，把两边的实际行为对齐成一份文本，分叉处照录。

## 7. 规划器配置

| | |
|---|---|
| 路径 | `theoria-arm/inner/plan.py`（三档阶梯；`BFS_NODE_CAP = 120_000` 与一个墙钟 deadline，两个都是模块常量）+ `engine-rig/engines/fd_adapter/`（`search.py` `backends.py` `pddl.py` `validate.py` `domain.pddl` `problem.pddl`）+ `engine-rig/bench/ladder.py`、`fdrun.py` |
| 版本把手 | **无配置文件**，每个旋钮都是源码字面量 |
| 判定 | **PARTIAL** |

**两个已记录的洞，都影响封存战役**：

* **没有 LP 求解器**（CMake 报 `Could NOT find Cplex`）。于是 `lp_potential` 与任何
  `seq-opt` / `diverse_potentials` 的 FD 配置**不可用**。
* **FD 的时间/内存上限在 Windows 上强制不了**（`preexec_fn` 抛 ValueError）。

两条都在 `engine-rig/runs/p13-fd-real/TOOLCHAIN_MANIFEST.md` 的「Known limitations」里。
**冻结一个强制不了资源上限的规划器配置，等于冻结了一个可以无声超时的单元**——这会直接
污染 §STATS_RULES §1.4 的缺格统计。冻结前须补一层可移植的看门狗，或把该限制写进清单
正文而不是脚注。

## 8. 指标电池 v1（定义与代码、逐指标方向预测）

| | |
|---|---|
| 路径 | `battery/METRICS.md`（由 `python -m battery.docs` 自动生成，`tests/test_docs.py` 守着）、`battery/metrics/{exploration,planning,economy,mechanism,epistemic}.py`、`battery/PREDICTIONS.md`、`battery/audit/gaming.py` |
| 版本把手 | **三处打架** |
| 判定 | **PARTIAL·版本冲突** |

版本冲突照录：

* `battery/METRICS.md` 标题写 **battery v1**；
* `battery/run_battery.py:290` 发的是 `"battery_version": "v2"`；
* `battery/__init__.py` 的 `__version__ = "0.1.0"`；
* 报告有 `REPORT_V0/V1/V2.md`，`PREDICTIONS.md` 一路做到 **v2.1**。

**「v1」已经指不出唯一状态。** Theoria.md 写的是「指标电池 v1」，而树上的 v1 是一个
更早的状态，不是现在要冻的那个。

**建议裁决：冻 SHA，不冻标签**，并在清单正文写明「Theoria.md 所称的『电池 v1』，在
冻结时对应 `run_battery` 自称的 v2 / `PREDICTIONS.md` 的 v2.1 一节」。含糊过去，日后
没人能复原冻的是哪一版。

**这一项的好消息**：`PREDICTIONS.md` 的方向预测是**只追加**的，且写在回算之前——
Phase 2 工序 2 要的正是这个，它是十三项里证据链最漂亮的一项。

## 9. 变体算子库

**两套互不相干的算子代数**：

* **(a) `proxy/variants.py`** —— `LEGAL_OPERATORS = ("forbid_action", "remap_action",
  "step_limit", "observation_loss", "win_tighten")`，`CLAIMS = ("solvable",
  "unsolvable", "unchanged")`；规格文件 `proxy/variants/v001..v004*.json`，逐个带
  `variant_id`。**这一套对应 Theoria.md Phase 1「变体注入层」的包裹合法集。**
* **(b) `exam/papers/adaptation.py` 的 `_VARIANT_GRID`** —— 6 个变体，作用在 a0 /
  a0-prime 自建世界上；`exam/model.py` `SCHEMA_VERSION = "exam/v0.1"`，规则摘要按源码
  哈希（`exam/grading/registry.py`）。

**建议裁决：Phase 4 冻的是 (a)。** 依据：判决题的真值必须来自**构造性依据**，而
Theoria.md 把构造性依据绑在代理层的包裹合法集上；(b) 是自建世界上的改规则适应题，
属于考卷的另一道题，应当**另列**而不是混进同一项。

**两套都要哈希，但要分开命名**，否则日后读者会以为变体算子库有两个版本。

## 10. 统计裁决规则

| | |
|---|---|
| 路径 | 机器：`battery/audit/stats.py`（手写的确定性符号检验与 Wilcoxon，精确、不依赖 scipy；docstring 已引 Theoria.md Phase 4）。规则文本：**本轮补齐** → [`freeze/STATS_RULES.md`](STATS_RULES.md) |
| 判定 | **本轮补齐（草案）** |

冻结前须把 `STATS_RULES.md` 里的三个主终点定义**接到 `battery/audit/stats.py` 的实际
函数上**，并加一条测试证明两者算的是同一件事。今天它们是两份互相引用但没有对账的文本。

## 11. claim 逐字文本与双结局

| | |
|---|---|
| 路径 | 此前**完全不存在**（`Theoria.md` 里只有 C1–C5 的**菜单**；`arc-recon/data/claim_set.json` 是同名假朋友，它是 19 局封存名册，不是 claim） |
| 判定 | **本轮补齐（草案）** → [`freeze/CLAIMS_TEXT.md`](CLAIMS_TEXT.md) |

## 12. 预算表

| | |
|---|---|
| 路径 | `baseline-arms/BUDGET_REPORT.md`（§9 是**可执行**闸门：`baseline-arms/harness/run_campaign.py`，证据 `baseline-arms/out/campaign_gate.json`）、`proxy/pricing/pricing_v1.json`、`theoria-arm/harness/budget.py`、`proxy/cost.py` |
| 版本把手 | `pricing_v1.json`：`"table": "pricing_v1"`、`"effective": "2026-07-28"`，账本按哈希以 `pricing_ref` 引用（`proxy/LEDGER_FORMAT.md` §5）。模型 id 已钉：`claude-opus-5`、`claude-sonnet-5`、`claude-haiku-4-5-20251001` |
| 判定 | **PARTIAL** |

价目表与花费闸门是这一项里做得最实的部分——成本是**换算**不是记录，账本按哈希引价目表，
这条纪律已经落地。缺的是 Theoria.md 点名的三个数：⟨$/局硬顶、总局数、止损⟩，仍是空位，
进 [PENDING_FIVE.md](PENDING_FIVE.md)。

## 13. 每格重复数 ⟨n⟩

| | |
|---|---|
| 路径 | 尚未定值。输入：`baseline-arms/DECISIONS.md` D-011（包络设计：只用 haiku、每局 3 次、30 动作）、`baseline-arms/STATUS.md` §M5、`baseline-arms/INCIDENTS.md` INC-BA-003 |
| 判定 | **MISSING·被上游的活挡住，不是文书问题** |

定 n 的**规则**已在 [`STATS_RULES.md`](STATS_RULES.md) §6 写死；缺的是**输入数据**。
详情与建议值见 [PENDING_FIVE.md](PENDING_FIVE.md)。

---

## 14. 外部工具链钉版（跨项，单列）

Theoria.md 的十三项没有单列这一格，但它横穿第 1、3、5、7 项，且是复现性最先断的地方。

| 组件 | 钉在哪 | 值 | 备注 |
|---|---|---|---|
| Fast Downward | `engine-rig/runs/p13-fd-real/TOOLCHAIN_MANIFEST.md`，并由 `engine-rig/bench/toolchain.py` 的 `EXPECTED` 在运行时重新核对 | FD `24.06+`，commit `7120aa01…c7bd`，二进制 sha256 `645671ae…0aee1` | **`.toolchain/` 是 gitignore 的：二进制不在仓库里，也无法从仓库重建**。清单必须照抄这句话 |
| 编译工具 | 同上 | winlibs mingw-w64 GCC 16.1.0（UCRT/posix/SEH/r3），zip sha256 `42735651…c0b4`；cmake 4.3.3；ninja 1.13.2 | `-DCMAKE_EXE_LINKER_FLAGS="-static"` 是承重的 |
| Lean | `theory-compiler/lean/lean-toolchain` | `leanprover/lean4:v4.9.0` | `lake-manifest.json` **零外部包**（无 mathlib），所以没有别的要钉 |
| Python | 只在 FD 那份 manifest 的表里记着 | 3.13.13 | **全树没有 lockfile**（无 `requirements.txt` / `poetry.lock` / `uv.lock` / conda export）。`theory-compiler/pyproject.toml` 声明 `lark>=1.1`（**声明了但没用**，解析器是手写的）、`pddl>=0.4` |
| LP 求解器 | —— | **未安装** | CMake 报 `Could NOT find Cplex`；直接影响第 7 项 |
| 账本 / 打分器 | `proxy/__init__.py` `LEDGER_VERSION = "1.0"`；`proxy/scoring/frozen.json` 存打分器源码哈希，指纹写进 `run_start` 与 `run.json` | 1.0 | 这一项的纪律是全树最完整的之一 |

**冻结前的头号技术债：没有 Python 依赖锁。** 冻结包声称「全部哈希」，而运行这些代码的
解释器与依赖没有任何钉子；FD 二进制则连仓库都不在。这两条要么补上，要么写进清单的
「已知不可复现面」，不能默认。

---

## 15. 冻结前必办事项（从上面逐条抽出来）

| # | 事 | 卡住哪一项 | 归谁 |
|---|---|---|---|
| 1 | 切 `dsl_grammar_v0.2` 声称的那个 tag，或改掉那句话 | 2 | theory-compiler |
| 2 | 裁决「生成器」指编译器后端还是世界生成器 | 3 | 人 |
| 3 | 把提示词抽成可哈希的数据文件 + 加一条游戏特定内容泄漏检查 | 4 | theoria-arm |
| 4 | 写 `PROBE_POLICY.md`，对齐两轨道的实际行为 | 6 | theoria-arm + engine-rig |
| 5 | 给规划器补可移植的时间/内存看门狗（Windows 上 `preexec_fn` 用不了） | 7 | engine-rig |
| 6 | 裁决「电池 v1」到底冻哪个 SHA，并在正文写明标签与 SHA 的错位 | 8 | 人 |
| 7 | 两套变体算子库分开命名、分别哈希 | 9 | 人 |
| 8 | 把 `STATS_RULES.md` 的三个主终点接到 `battery/audit/stats.py` 并加对账测试 | 10 | battery |
| 9 | 填 ⟨$/局硬顶、总局数、止损⟩ | 12 | 人 |
| 10 | 重跑 baseline-arms M5 方差包络（现有的那份测的是 API 争用，见 INC-BA-003） | 13 | baseline-arms |
| 11 | 补 Python 依赖锁；把 FD 二进制不可从仓库重建这件事写进清单正文 | 14 | 人 + engine-rig |
| 12 | 八台引擎 vs 设计文档六台的错位，在清单正文点破 | 5 | 文书 |

**第 2、6、7、9 项需要人拍板**，其余是可以派出去的工。
