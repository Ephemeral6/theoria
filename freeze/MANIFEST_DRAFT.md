# MANIFEST_DRAFT —— Phase 4 冻结清单，13 项逐条对树

**状态：草案（DRAFT）。这不是冻结清单本身，是冻结清单的底稿。**
冻结 = 人来做：解掉下面每一处 `⛔ 缺` 与 `⚠ 待办`，把 `freeze/MANIFEST.md`
（本文的定稿）连同全部哈希提交。**只要还有一项是 `⛔ 缺`，就不该开跑封存战役。**

依据（逐字）：`Theoria.md:368`

> **冻结清单(首局开跑前提交，全部哈希)**：内环代码、DSL 语法版本(两本书)、生成器、提示词、**引擎清单与版本**、戳探策略、规划器配置、**指标电池 v1(定义与代码、逐指标方向预测)**、变体算子库、**统计裁决规则**(见下)、claim 逐字文本与双结局、预算表、每格重复数 ⟨n⟩(由开发堆方差在冻结前定：方差小则 n=1 可辩护，否则 n=2)。

**哈希基准提交：`⟨FREEZE_COMMIT — 待重取⟩`。**
起草时用的是 `25eee107` (master, 2026-07-28)，**那是一个已经过期的占位值，不是冻结提交**。
起草期间 master 在动（并发轨道），起草之后仍在动：**2026-07-29 复核，本文表格里
31 个 blob/tree 哈希有 17 个已经和 master 对不上**——`battery/` 一族全部
（目录树、`metrics/__init__.py`、`economy.py`、`PREDICTIONS.md`、`METRICS.md`），
外加 `theoria-arm/inner|harness`（含 `plan.py`、`loop.py`）、`proxy/`（含 `ledger.py`、
`scoring/frozen.json`）、`theory-compiler/.../generators/`、`baseline-arms/harness/bare_cc.py`、
`engine-rig/engines/probe_frontier|fd_adapter`。

因此，**下表所有 40 位哈希只对 `25eee107` 成立，不得当作冻结值引用**。
定稿时必须在**真正的冻结提交**上用 `freeze/build_manifest.py --verify` 整批重取，
并把那个提交号回填到本行的 `⟨…⟩` 里。**在回填之前，本行永远读作「待重取」，
而不是「已钉在 25eee107」。**（每条哈希后附的 `@25eee107` 标记就是这个意思。）

## 哈希纪律 —— 先读这条，否则清单不可复现

**一律哈希 git blob / tree（`git rev-parse HEAD:<path>`），不哈希工作树文件。**

理由是实测出来的：`CONTRACTS/dsl_grammar_v0.2.md` 在 master 工作树里是 **CRLF**
（22,725 字节），在另一个 worktree 里是 **LF**（22,348 字节，差值 377 = 行数），
`tr -d '\r'` 后 diff 为空；而**同一目录**的 `dsl_grammar_v0.1.md` 是 LF。
根 `.gitattributes` 只有 `PARTNER_SYNC.md merge=union`，没有任何 `text`/`eol` 规则，
所以**工作树哈希跨 checkout 不可复现**。
（`engine-rig/.gitattributes` 钉了 LF，但它只管 engine-rig 子树。）

**⚠ 待办 H-1**：冻结前给仓库根 `.gitattributes` 补一条全局 `text=auto eol=lf`，
或在定稿清单里逐条记下 EOL 约定。二选一，不能不选。

---

## 总览

| # | 项 | 状态 | 落点 |
|---|---|---|---|
| 1 | 内环代码 | ✅ 有 | `theoria-arm/inner/` + `theoria-arm/harness/` + `proxy/` |
| 2 | DSL 语法版本（两本书） | ⚠ 有，两本书版本不齐 | `CONTRACTS/dsl_grammar_v0.2.md`（+ v0.1 承载攻略书） |
| 3 | 生成器 | ⚠ 有，但有分叉与版本串缺失 | `theory-compiler/.../generators/` + `cold-start-a0/compile/` |
| 4 | 提示词 | ⚠ 有，**零版本化** | `theoria-arm/inner/theorize.py` + `grammar_card.py` + `baseline-arms/harness/bare_cc.py` |
| 5 | 引擎清单与版本 | ⛔ **缺清单** | 代码在 `engine-rig/engines/`；**清单文件不存在，需现写** |
| 6 | 戳探策略 | ⚠ 无统一文档 | `engine-rig/engines/probe_frontier/README.md` + 两处模块 docstring |
| 7 | 规划器配置 | ⚠ 有，**Theoria 臂未钉版** | `engine-rig/engines/fd_adapter/backends.py`；`theoria-arm/inner/plan.py:112` 未传 `prefer=` |
| 8 | 指标电池 v1 | ⚠ 有，但两个主终点无实现 | `battery/` |
| 9 | 变体算子库 | ✅ 有 | `proxy/variants.py` + `proxy/variants/` + `exam/artifacts/variant_specs/` |
| 10 | 统计裁决规则 | ✅ 本套件 | `freeze/STATS_RULES.md` |
| 11 | claim 逐字文本与双结局 | ✅ 本套件 | `freeze/CLAIMS_TEXT.md` |
| 12 | 预算表 | ⛔ **缺** | 原料在 `baseline-arms/BUDGET_REPORT.md`；算术在 `freeze/PENDING_FIVE.md` §4 |
| 13 | 每格重复数 ⟨n⟩ | ⚠ 已裁定 n=2，**但依据 untracked** | `freeze/STATS_RULES.md` §5；证据 `baseline-arms/out/campaign/` **不在 git 里** |

**计数：13 项全部有落点或有标注。✅ 3 · ⚠ 8 · ⛔ 2。**

---

## 1. 内环代码 ✅

五拍 observe→theorize→certify→probe→plan→commit 的**唯一在线可跑形态是 `theoria-arm/`**。
`cold-start-a0/`、`cold-start-a2/`、`cold-start-a3/`、`a0-spike/` 是同一个环的**四次离线证明**，
不是臂本身——冻结清单里要区分开，否则哈希了四份离线件却漏掉真正上场的那份。

| 路径 | 是什么 | tree/blob sha1 @`25eee107`（过期占位） |
|---|---|---|
| `theoria-arm/inner/` | 五拍编排 + 两本书 + 七种意外（10 文件） | `a8ee59c759bb7e45de439320590c999fe11e6a27` |
| `theoria-arm/inner/loop.py` | `class TheoriaArm`，环本体 | `5f21d674f790f08eada4cf80d25b2b8a9917f16d` |
| `theoria-arm/harness/` | 入口 + ARC 客户端 + 预算 + 掌台 | `0c3e3064c201674963fcc503417370a2bb26dc11` |
| `theoria-arm/harness/run.py` | **入口点** `python -m harness.run` | `7136b5fb05e7bfa72328674d9485bef218a490e0` |
| `proxy/` | 共享外壳：账本、环境代理、打分器 | `2e68b2a36bdef37aa75c4398dbbbd97447e3a53e` |
| `proxy/ledger.py` | `Ledger` / `RunLedger`，三臂同一个写手 | `d820e783afd9da473b4375498bae65f10ac9bd9b` |
| `proxy/__init__.py` | `__version__ = "1.0"`, `LEDGER_VERSION = "1.0"` | `b8d1ac7095372df3f0b77a51e77630f5f6e66e9b` |
| `proxy/scoring/arc_v1.py` | 冻结打分器，`VERSION = "1.0.0"` | `e5a7344100812221bbc46d39cbd2572f5b8b8977` |
| `proxy/scoring/frozen.json` | **全仓唯一一处自校验的冻结声明** | `0e8d8e236de7a4d1cd08a781561935fd2760cca3` |

**⚠ 待办 1-a**：`proxy/ledger.py` 与 `proxy/env_proxy.py` 在散文里被称作
「the same frozen writer」（`theoria-arm/README.md`），但**背后没有任何冻结机制**——
只有 `LEDGER_VERSION = "1.0"` 一个字符串。真正自校验的只有 `proxy/scoring/frozen.json`。
建议把 `frozen.json` 的机制推广到 ledger 与 env_proxy，或在清单里明写
「账本靠版本串不靠哈希」。

**⚠ 待办 1-b（登记，不是修）**：模型侧不过代理。`proxy/model_proxy.py` 按设计剥掉
`Authorization`，而本仓只有 `ARC_API_KEY`，于是上游对每次请求回 401。
模型调用走 `claude -p`，每条账本记 `proxied: false`。
后果：`request` 字段是臂发给 CLI 的 prompt，**不是** CLI 发给 Anthropic 的 `/v1/messages` 体，
**这本账不能用来谈输入 token 的构成**。证据 `theoria-arm/evidence/model-proxy-401.jsonl`，
理由 `theoria-arm/DECISIONS.md` D-P8-002。这需要预注册里的一行，不是一个修复。

**⚠ 待办 1-c（登记）**：分数对账义务在这个 API 上不可履行——线上命令响应没有
`score` 字段，分数只存在于 `scorecard/close` 的成功响应里。
`armtools/archive.py` 报 `unavailable` 并改对 `levels_completed` 与动作数（INC-TA-002）。

---

## 2. DSL 语法版本（两本书） ⚠

| 路径 | 是什么 | blob sha1 @`25eee107`（过期占位） |
|---|---|---|
| `CONTRACTS/dsl_grammar_v0.2.md` | **现行语法**，`Version: 0.2 · Status: 定稿 · Effective: 2026-07-28` | `4956d77cb4c5b36cef0d7b977577ff1bfed5ad9f` |
| `CONTRACTS/dsl_grammar_v0.1.md` | v0.1，冻结不得改；**仍是攻略书的实效文本** | `e441aa6e40fe442edc570ce142ef4db2822bcd3b` |
| `CONTRACTS/candidates_schema.md` | 引擎→编译器候选流，冻结 v0.1 | （随目录哈希） |
| `CONTRACTS/ic3_certificate_v0.1.md` | IC3/PDR 证书 schema | （随目录哈希） |

**⚠ 待办 2-a —— 「两本书」的版本不齐，必须在清单里写明。**
`dsl_grammar_v0.2.md:262` 写着 `## playbook.dsl — Unchanged from v0.1`。
于是**说明书语法在 v0.2、攻略书语法的实效文本仍在 v0.1**，
两个版本装在一个文件里。冻结清单第 2 项写「DSL 语法版本(两本书)」，
只记一个 "v0.2" 是**不准确的**。建议记成
`manual=v0.2 (dsl_grammar_v0.2.md) / playbook=v0.1 text (dsl_grammar_v0.2.md:262 → dsl_grammar_v0.1.md)`。

**⚠ 待办 2-b（订正）**：`dsl_grammar_v0.2.md:39` 写 `## theory.dsl — five sections`，
底下定义了**六节**（`word_table` :41、`semantics` :81、`events` :159、`rules` :166、
`goal` :187、`laws` :192）。文档数错了自己的节数。
（顺带澄清一处流传的误记：`goal:` **在**语法里，v0.1/v0.2 都有，
`theory_parser.py:64` 解析它；真正的缺口是 domain→problem 的**绑定步骤**缺在编译器里，
`cold-start-a3/DECISIONS.md` D-A3-004。）

**已核实无在飞工作**：分支 `agent/p10-contracts-v02` 已并入 master，其 worktree 是并后残留。

**⛔ 待办 2-b（G5，自 S4 移植，2026-07-29 复核）—— v0.2 的冻结政策挂在一个
不存在的 tag 上，而且这个引用自指、无法事后补救。**

`CONTRACTS/dsl_grammar_v0.2.md:10` 逐字写着：

> **Freeze policy.** v0.2 is frozen **at the tag that carries this line**.

**该 tag 不存在。** 本轮实测：仓库共 **24 个 tag**，全部是 `engine-rig-m*` 一族，
没有任何一个指向 DSL 语法（`git tag -l | grep -i 'dsl\|grammar'` 空）。
同一文件 `:16-18` 还三次以「that tag」为锚点叙述修订项 11–14 的先后，
所以**整个 v0.2/v0.3 的演化政策与它的历史叙述都挂在一个空引用上**。

**比 S4 的记述更糟的一点，是这个引用自指。** 「携带此行的那个 tag」在写下时
就无法满足：现在补切一个 tag，它指向的提交里「此行」所在的文件内容已经与
写下这句话时不同，于是「携带此行」究竟指哪一版本本身有歧义。**这不是补个 tag
就能修的，必须改写那句话。**

三条出路，冻结前必须选一条并落盘（**保持现状不是选项**——清单里会留下一个
查不动的版本串，而版本串查不动，整份释出清单的可复现性就断在这里）：

1. 切一个具名 tag（如 `contracts-dsl-v0.2`），并把 `:10` 改成**指名该 tag**，
   不再自指；`:16-18` 的三处「that tag」一并改成同一个名字。
2. 改为**指名提交哈希**（v0.2 定稿那一版的 blob/commit），彻底不用 tag。
3. 声明 v0.2 的冻结锚点就是**冻结包本身**（`⟨FREEZE_COMMIT⟩`），
   即 v0.2 随本释出一起冻结——最省事，但要接受「v0.2 定稿于 2026-07-28」
   这句话与锚点日期不一致，需在文件里说明。

**这条属于 `CONTRACTS/`，两条赛道都不得单方面改**（`CLAUDE.md`：
`candidates_schema.md` 冻结、`dsl_grammar_v0.1.md` 归 theory-compiler 赛道）。
因此本条只登记，不动手；由监控转 theory-compiler 赛道或作为契约变更走 S9 的流程。

---

## 3. 生成器 ⚠

| 路径 | 是什么 | tree/blob sha1 @`25eee107`（过期占位） |
|---|---|---|
| `theory-compiler/src/theory_compiler/generators/` | 规范四形态（5 文件） | `f69d55d4d39b783be2cc2604135c377fe7cc9831` |
| ├ `gen_lean.py` | Lean 4 | `f0a903aad45955224c5a711117ec3cd49d96ba77` |
| ├ `gen_pddl.py` | PDDL domain+problem | `e64683dc080460387a36f6f1a50de0cda587bf0b` |
| ├ `gen_python.py` / `gen_markdown.py` | 预测器 / `theory.md` | （随目录哈希） |
| `cold-start-a0/compile/` | **第二套完整生成器族**（`gen_*_a0.py` + `compile_a0.py`） | `cb45149e0c5073bbb317d4094ac9bc7f6ce43e56` |

**⚠ 待办 3-a —— 存在两套生成器族，且 A 系管线调用的是 `_a0` 那套。**
冻结清单必须写明**封存战役实际调用哪一套**，否则哈希的和跑的不是同一份。
（`theoria-arm` 经 `_bootstrap.py` 导入 `theory-compiler`；`cold-start-a*` 用 `_a0`。
定稿前需实测确认 Theoria 臂在线路径上的那一套。**⚠ 待办 3-b**。）

**⚠ 待办 3-c**：生成器**零版本标记**。包版本 `theory-compiler/pyproject.toml` 写
`version = "0.1.0"` 而实现的是语法 v0.2；`gen_pddl.py:5` 的 docstring 还引
"the dsl_grammar_v0.1 contract"。三处互相不一致，冻结前应统一。

**登记（不是缺陷）**：`cold-start-a3` **没有写生成器**，它写的是一个 binder
（`a3pipeline/compile_a3.py:60 bind_goal`）以及两处绕开（D-A3-005/006），
绕的是 `cold-start-a0/`，不是 `theory-compiler/`。
`cold-start-a3/DECISIONS.md:105-115` 自己记着代价：
「A3 is doing work the compiler should do, in a tree the compiler's owner does not read」。
**这个 binder 是一处树外补丁，清单里要单列。**

---

## 4. 提示词 ⚠ —— 四项里最薄弱的一处

| 路径 | 是什么 | blob sha1 @`25eee107`（过期占位） |
|---|---|---|
| `theoria-arm/inner/theorize.py` | **Theoria 臂 prompt**：`PREAMBLE` L122-167、`OUTPUT_CONTRACT` L169-201、`build_prompt()` L204-253 | `569dd97cfc854b2321947cbec000f26db847b44b` |
| `theoria-arm/inner/grammar_card.py` | `CARD` L16-182，逐字递给掌台的语法卡 | `851e6262ae641bc0047620228fa663ca96c0be8f` |
| `baseline-arms/harness/bare_cc.py` | **对照臂 prompt**：`PREAMBLE` L72-86 | `90dcba42ac29420cc2ef51b141f2439cff0cbf52` |
| `theoria-arm/runs/<slug>/desk/call-*.md` | 逐次归档的 prompt+reply（`claude -p` 无采样种子，这是种子的替代物） | 逐 run |

**⛔→⚠ 待办 4-a —— 提示词零版本化。** 没有 `PROMPT_VERSION`、没有 prompt 哈希、
没有带日期的 prompt 文件。唯一的溯源是两个 `.py` 的 git 历史与逐 run 归档。
**这是整份预注册里风险最高的面**（`Theoria.md:353` 把提示词列为过拟合的第三条通道，
要求「每次迭代做 diff 审查」）。建议冻结时把上面三个文件的 blob 哈希
作为「提示词」这一项的定义，并加一条 CI 断言。

**游戏特定内容审计**（`Theoria.md:353`「提示词不得含任何游戏特定内容」「游戏 ID 永不进模型上下文」）：

* **游戏 ID：干净，已实测。** 对首触实跑的五份归档 desk transcript
  `grep -c "g50t\|5849a774"` **全为 0**。`build_prompt()` 从不接收 `game_id`；
  `FrameStore.summary()` 只发形状/颜色/格数统计。
  仓库里的 `g50t-5849a774` 只出现在 CLI 默认值与注释里。
* **两处需要在清单里表态、都不违字面但评审会问**：
  1. `grammar_card.py:176-181` "THE ACTION VOCABULARY FOR THIS WORLD" 点名
     `ARC 的 ACTION1..ACTION7` 与 `act=key(<n>)` 映射——这是**环境族**事实
     （对全部 ARC-AGI-3 成立），不是某一局。
  2. `grammar_card.py` 的样例用 `Cart`/`Door`/`Button`/`exit_cell` 与推箱/开门语义
     （L29-33, L92-95, L136-147, L185-207）——取自 **A0 自建世界**，
     而 `Theoria.md:353` 正是允许在 A0 上迭代提示词的。不是 ARC 内容，
     **但必须在清单里明写出处**。

---

## 5. 引擎清单与版本 ⛔ —— 清单不存在，需现写

代码在 `engine-rig/engines/`，tree `88c12608e1cf8b5b14f3cf1328ee436db3f2c3eb`。

**⛔ 缺 5-a：没有任何机器可读的引擎清单。**
`engine-rig/artifacts/` 里只有 `candidates.jsonl` 一个文件；
全仓没有 `VERSIONS` 文件；`tools/run_all.py` 只落 `candidates.jsonl`，不落报告。
（流传的 `engines_report.json` **在另一棵树里**——`cold-start-a0/artifacts/engines_report.json`，
且它是**一次运行的报告**，顶层键是 `board`/`frames`/`mining`/…，
**没有引擎版本串、没有哈希、没有按引擎名分行**。用不了。）
**必须从零写一份 `freeze/ENGINES.md` 或 `engines_manifest.json`。**

**⛔ 缺 5-b：引擎带名字，不带版本。** 每个 `__init__.py` 只有一个 `ENGINE` **名称**串。

**⚠ 待办 5-c —— 清单会数错引擎数，除非先解决这一条。**
`CLAUDE.md` 与工单都说「六个引擎」。树上实际有 **8 个引擎模块**：
六个之外还有 `deadlock_carver`（其 `__init__.py:43` 设 `ENGINE = "fd_adapter"`）
与 `ic3_pdr`（`:51` 设 `ENGINE = "lp_potential"`）。
两者故意套用冻结枚举里的成员名，靠 `payload.producer` 自报身份（`DECISIONS.md` D-018）。
冻结枚举 `ENGINES` 在 `engine-rig/common/candidates.py:27`，恰好六个名字。
**后果：按枚举做的引擎清单会把 8 个模块静默并成 6 行。**

**⚠ 待办 5-d**：里程碑标签有**九个**，不是八个——
`engine-rig-m1-fixtures` … `m8-integration`，**外加 `engine-rig-m9-deadlock-ic3-probe`**，
而 m9 正是承载 `deadlock_carver` + `ic3_pdr` 的那个。
**按 m8 冻结的清单盖不住 `engines/` 里现有的代码。**

---

## 6. 戳探策略 ⚠ —— 无统一文档

| 路径 | 是什么 | tree/blob sha1 @`25eee107`（过期占位） |
|---|---|---|
| `engine-rig/engines/probe_frontier/` | 引擎（frontier / reach / scenario / sokoban_probe） | `1b42a43d4ce1515f8a85f68904a37981cf24790a` |
| `engine-rig/engines/probe_frontier/README.md` | **现有的策略文档**：假设分割熵、贪心 argmax、单位成本比特、全序确定性排序 | `e7078ea27de6560927ac8fc864f2996f37aa2bf4` |
| `theoria-arm/inner/probe.py` | **臂侧策略**：按消融建前沿（`manual` + `inert` + 每规则一个 `without_<rule>`），按 bits-per-action 排序；`ProbeLog` 强制「先预测后观察」 | `6e31223633fa38c8f7cebf9269da0f7ecf7bb8d8` |
| `cold-start-a2/a2pipeline/probe.py` | A2 离线里程碑 M8，臂侧设计的前身 | （随目录） |

**⚠ 待办 6-a**：全仓**没有** `PROBE*.md`。策略散在一个引擎 README 与两处模块 docstring 里，
**没有一份可以整体哈希的戳探策略文档**。冻结清单第 6 项要么现写一份，
要么明写「本项 = 这三个文件的哈希之和」。

---

## 7. 规划器配置 ⚠ —— Theoria 臂未钉版

**现行状态：Fast Downward 已接通**（不再是 stub）。
FD 24.06+ commit `7120aa01`，winlibs GCC 16.1.0，235 targets，无补丁；
套件在 FD 可达时 255 passed，不可达时 252 passed + 3 skipped（`engine-rig/STATUS.md`）。
**但产物路径故意钉在 stub 上**（D-025，为了产物跨机器字节一致）。

| 路径 | 是什么 | blob sha1 @`25eee107`（过期占位） |
|---|---|---|
| `engine-rig/engines/fd_adapter/backends.py` | 全部配置面：`FD_DEFAULT_HEURISTIC="lmcut"`、`FD_SEARCH`、`TIERS`、`choose_tier()`、`run_fast_downward(timeout=120)` | `7b7bc83dfb052984ea960207a4f9630bf114f642` |
| `engine-rig/engines/fd_adapter/__init__.py` | **`ARTIFACT_TIER = backends.STUB` ← 那个钉子** | `dc8eee51cba38276d084f5e5e0a6ff429f2ade15` |
| `engine-rig/runs/p13-fd-real/TOOLCHAIN_MANIFEST.md` | **FD 工具链溯源：URL / 版本 / 大小 / sha256 / 构建命令**（工具链本体在 gitignore 的 `.toolchain/`，未提交） | （随目录） |
| `theoria-arm/inner/plan.py` | 臂侧：`BFS_NODE_CAP=120_000`、`BFS_DEADLINE_S=120.0`、三级阶梯 | `7aebed34cad31270b87fa964a612342e6e23c5d0` |

**⛔→⚠ 待办 7-a —— 这是一个真实的可复现性洞，必须在冻结前处理。**
四个离线 spike 全都显式传 `prefer="stub"`
（`cold-start-a0/pipeline/plan_stage.py:59`、`cold-start-a2/a2pipeline/plan.py:70`、
`cold-start-a3/a3pipeline/plan.py:98`、`a0-spike/pipeline/run_a0.py:161`），
**而 `theoria-arm/inner/plan.py:112` 调 `fd_adapter.solve_parsed(...)` 不传 `prefer=`**。
于是 `prefer=None`，`choose_tier` 规则 4 生效：
**`$FAST_DOWNWARD` 可达时用 `fd-optimal`，不可达时用 `stub-bfs`**。
**封存战役里 Theoria 臂用哪个规划器，取决于跑它的那台机器的环境变量。**
二选一：把 `prefer=` 钉死，或把 `FAST_DOWNWARD` 声明为冻结环境的一部分并记其 sha256。

**⚠ 待办 7-b（登记）**：无 LP 求解器（未找到 CPLEX），故 FD 的 LP 类配置不可用；
FD 的 driver 在 Windows 上无法自行限时限内存，故用外部 subprocess timeout。

---

## 8. 指标电池 v1 ⚠ —— 三个主终点里两个没有实现

| 路径 | 是什么 | tree/blob sha1 @`25eee107`（过期占位） |
|---|---|---|
| `battery/` | 全部（57 tracked 文件） | `48d91b4d3b113c56e576e832c59b25abb91a061c` |
| `battery/metrics/__init__.py` | **`REGISTRY`**，实测 **38 条**指标 | `bfc578c0310c45f7da818ae0a6c0beda4c7b9016` |
| `battery/metrics/economy.py` | 含 **`E2` = 前载指数**（主终点三） | `0f956887a5999dee032a867d0259f3052b5a4de6` |
| `battery/PREDICTIONS.md` | **逐指标方向预测**，append-only。**⚠ 起草时的结构描述已过期**，见下方 8-d | `83b39faa032659ff07096fbc5b9a677644fbb654` |
| `battery/METRICS.md` | 生成物（`python -m battery.docs`），`tests/test_docs.py` 盯漂移 | `596dce0c0e6a144ac62979aabcf8fdcae0924689` |
| `battery/artifacts/` | 6 份 JSON：区分力、抗游戏审计、冗余、能力谱、臂对照、验证材料 | （随目录） |

指标 id（`REGISTRY` 插入序，38 条）：
`E1-E7`(7) · `K1-K14`(14) · `X1-X6`(6) · `M1-M6`(6) · `P1,P2,P3,P5,P4`(5)。

**⛔ 缺 8-a —— 主终点「U3 达成率」全仓没有任何实现。**
`REGISTRY` 里没有对应 id；`battery/model.py` 有 `Step.won` / `Step.level`
但**没有任何指标消费 `.won`**；唯一关注关卡的 `M3` 在守卫之后是故意未实现的
（`mechanism.py:73-76`）。**这一项要从零写。** 判据见 `STATS_RULES.md` §1.2、§9.2。

**⛔ 缺 8-b —— 主终点「判决题准确率(含特异度)」没有电池 id。**
它**有实现**，但在考卷轨道：`exam/grading/mark.py:95 confusion()`
（`sensitivity` :135、`specificity` :136），经 `exam/papers/verdict.py:1252` 调用。
电池里最近的亲戚是 `M5`（只有灵敏度，无特异度）。
**要么给它一个电池 id，要么在清单里明写「本终点由 exam 轨道计算，不在电池内」。**

**⚠ 待办 8-c（订正）**：`battery/DECISIONS.md:122` 仍写
"A hand-written reference for twenty-eight metrics…"——v0 期的陈旧串，
实际 38。（`REPORT_V0.md` 的 "29 metrics" 是**正确**的，它显式限定在 v0。）

**⚠ 待办 8-d（订正，2026-07-29 复扫）—— `PREDICTIONS.md` 已经不是两批了。**
本文起草时写的是「v0 L1-130 + v1 L131-240」，那在基准提交 `25eee107` 上**是对的**
（该 blob 正好 240 行、两批）。到 2026-07-29，同一文件是 **603 行、四批 + 一段标注**：

| 批 | 行 | 预注册日 |
|---|---|---|
| v0 | `L1-130` | 电池 v0 |
| v1 —— nine further metrics | `L131-243` | 2026-07-28 |
| v2 —— the CC vs Schema contrast | `L244-392` | 2026-07-28 |
| v2.1 —— four defences | `L393-511` | 2026-07-28 |
| 标注 · V18 冻结前复核 | `L512-603` | 2026-07-29（**标注，不是预测**，正文一字未改） |

三条后果，都要进定稿清单：

1. **`v0 L1-130` 那半句仍然准确，坏掉的是「到 240 行为止」。** 追加是真 append：
   已逐段比对 `25eee107` 的 blob 与当前 blob，v0 正文一字未动，
   所以**全仓引用 v0 的行号锚点全部仍然有效**——已复核 `PREDICTIONS.md:78`（E2 那行）
   与 `:122-127`（缓存混杂那条自陈），两处都还指着原句。
   `CLAIMS_TEXT.md:86`、`STATS_RULES.md:172`、`:202` 因此**不需要改**。
2. **冻结清单第 8 项要哈希的是「逐指标方向预测」，而它现在是四批。**
   定稿时要么把四批一并声明为预注册文本，要么明写**哪一批进冻结、哪一批只作背景**。
   `Theoria.md:368` 只说「逐指标方向预测」，没说哪一版；不写清楚就是留了一个
   事后挑批次的口子。
3. **v1/v2/v2.1 的封条比 v0 弱，而且它们自己说了。** `L140` 起 v1 自陈
   "and it is weaker than v0's, materially"；`L163` 承认部分 v1 指标在臂上
   是 post-diction。**这三批不能和 v0 平级引用**，弱封条必须随预注册一起报。
   （这与 `RECONCILE.md` 移植清单 G8 的「电池 v1/v2/v2.1 版本冲突」是同一件事。）

---

## 9. 变体算子库 ✅

| 路径 | 是什么 | tree/blob sha1 @`25eee107`（过期占位） |
|---|---|---|
| `proxy/variants.py` | **算子库本体**：`LEGAL_OPERATORS` :34 = `forbid_action`, `remap_action`, `step_limit`, `observation_loss`, `win_tighten`；`CLAIMS` :37 = `solvable`/`unsolvable`/`unchanged`；`class Variant` :54 拒收任何没有 ≥40 字符建设性 `justification` 的 spec（:70-77） | `71a2fa1c01088e03678d3d9a89c2fb0fce43540c` |
| `proxy/variants/` | 4 份注入式变体 spec | `29a7f13d9dc11d4435493a59961d88a6c8d0c17e` |
| `exam/artifacts/variant_specs/` | 考卷的 **17 份** spec，算子分布 `remap_action`×8 / `forbid_action`×4 / `observation_loss`×4 / `step_limit`×4 / `win_tighten`×1（合法集全覆盖） | `31cb4d062a78d958b2d93bdb6851cfae6d4a0510` |
| `exam/grading/rubrics_verdict.py` | **证书文法封闭**：三类 `invariant` / `cut_set` / `counting`（:121-123） | `1fe26d852621afb541daf237930ccc6a21ccdc72` |

考卷三类判决题齐全且已实测：`exam/papers/verdict.py:1-13` 定义三类，
`LARGE_SPACE_THRESHOLD = 10**12`（低于此阈值的第 ii 类题出题器拒收）；
`exam/STATUS.md` 记着 `bluffer` 假臂拿到**灵敏度 1.0 / 特异度 0.0 / 总分 0.265**——
`STATS_RULES.md` §2.3 把它钉成必跑阴性对照。

**登记（不是缺陷）**：`a0-spike/pipeline/adapt.py:45-75` 的四个变体
（`push1`/`push3`/`nocross`/`ghost`）与 `cold-start-a3/a3pipeline/negctl.py:61` 的
`CONTROLS` 是**逐世界的临时件，不是可复用算子库**。清单里别把它们当算子库列。

---

## 10. 统计裁决规则 ✅

`freeze/STATS_RULES.md`（本套件）。定稿时取其 blob 哈希入清单。
内含 ⟨n⟩ 的裁定（§5）、三个主终点的操作化（§1-3）、多重比较（§4）、
反 best-of-n（§6）、作废重跑判据（§7）、以及逐条抗游戏审计（§10）。

---

## 11. claim 逐字文本与双结局 ✅

`freeze/CLAIMS_TEXT.md`（本套件）。C1–C5 各一段逐字文本，
**成立版与不成立版两版都先写死**。定稿时取其 blob 哈希入清单。

---

## 12. 预算表 ⛔ —— 缺

**树上没有「预算表」这个东西。** 有的是原料：

* `baseline-arms/BUDGET_REPORT.md`（blob `11c5597179e1684dcec40838623f6c671a9b86ee`）
  ——试点单价、S1/S2 外推、七条可执行闸门 G1-G7、以及闸门实际触发的记录；
* `baseline-arms/out/campaign_gate.json` —— 闸门落盘凭据。

`Theoria.md:377` 要冻结的是 **⟨$/局硬顶、总局数、止损⟩**，三个数一个都还没定。
算术已经备好在 `freeze/PENDING_FIVE.md` §4（含封存堆 21 局 / 14,121 基线动作 /
三臂 × n 的逐档报价与墙钟）。**填数是人的事。**

---

## 13. 每格重复数 ⟨n⟩ ⚠ —— 已裁定 n=2，但依据不在 git 里

**裁定：⟨n⟩ = 2。** 完整论证 `freeze/STATS_RULES.md` §5，
复算 `freeze/runs/2026-07-28T1200Z-p22/envelope_stats.py`。

**⛔ 缺 13-a —— ⟨n⟩ 的唯一依据是 untracked 的。**
`baseline-arms/out/campaign/`（48 个 episode，4 局 × 12 重复）
`git ls-files` 返回 **0 个文件**。
**不在 git 里 = 不可哈希 = 不能进预注册。冻结前必须提交。**

**⚠ 待办 13-b —— 两份包络记录尚未对账。**
`BUDGET_REPORT.md` §11 记的是更早的一次（只有 ar25 三格，G4 触发，
「战役停在 1/4」）；`out/campaign/` 里这 48 格是后来跑的更完整的一批。
两处并存且互不引用，读者会困惑。

**⚠ 待办 13-c —— n=2 不替代包络的修复。**
`BUDGET_REPORT.md` §11.5 列的两件事（INC-BA-003 跨会话闸门、
中止阈值随预算缩放）在修好并重跑包络之前，
**关于臂方差的任何数值主张都不许进论文**。见 `STATS_RULES.md` §5.5 硬条款。

---

## 附：本清单之外，但会挡住冻结的

| # | 事 | 出处 |
|---|---|---|
| A-1 | ~~**消融臂不存在。**~~ **已过期，见下方 A-1′。** 起草时（`25eee107`）`ablation-arm/` 确是空目录、只有工单。**2026-07-29 复扫：臂已建成并标定。** | 树上实查（已作废） |
| A-1′ | **消融臂已建成，但只有离线形态；C5 的成本切分仍然做不出来。** 见下方展开。 | `ablation-arm/{DESIGN,REPORT,STATUS}.md` |
| A-2 | `schema_repro` 臂不存在且大概率永远不存在（官方 harness 从未发布）。三臂实为**两臂 + 消融臂**。 | `baseline-arms/SCHEMA_LOCATE.md` |
| A-3 | ~~`cold-start-a0/certify/fd_conformance.py` 工作树脏（` M`，未提交）~~ **已消解**（2026-07-29 复扫：`git status --porcelain` 对该路径返回空）。但**这条的一般形式仍然成立**：哈希前必须复核工作树干净，否则哈的是别人在飞的字节。 | `git status`（2026-07-29 复核） |
| A-4 | ~~`CLAUDE.md` 说「没有任何游戏被玩过、25 局全 `never_audited`」~~ **已消解**（2026-07-29 复扫：`CLAUDE.md:136-141` 现已写明开发堆 4 局 `trajectories_reviewed`、封存堆零 API 接触、INC-BA-001 的 9 局知识污染与 F-11 的 19 局裁定）。**留在表里是为了记住它曾经错过**——`CLAUDE.md` 会漂，冻结前要再核一次。 | `CLAUDE.md:136-141`；`baseline-arms/TOUCHED_GAMES.md` |

### A-1′ 展开 —— 消融臂现状（2026-07-29 复扫）

**建成了什么。** `ablation-arm/` 在树上，`agent/p18-ablation-arm` 之后又经
`a4a-ablation-build` / `a4b-ablation-calibrate` / `bus2-ablation-readonly` 并入 master：
`DESIGN.md`（刀口论证，代码之前定稿）、`REPORT.md`（标定结果）、`DECISIONS.md`、
`STATUS.md`、`RUN_STATE.md`、`README.md`，`ablcore/` **九个模块**
（`certify_abl` `compile_abl` `downgrade` `ledger_abl` `outside` `pin` `plan_abl`
`playbook` `surprise`），加 `run_arm.py` / `calibrate.py` / `verify.py` / `verify.sh`
与 `artifacts/`。门：`python -m pytest -q` → 74 passed；`bash ablation-arm/verify.sh` → GREEN, exit 0。

**刀口在哪。** `DESIGN.md` §3：切在 **U2|U3 边界**——保留表示层（对象化、DSL、重放、
规划、六引擎、便宜层 certify），删掉定理义务（`Theoria.md:237-248` 第 6、9 两条全切，
第 1、5 两条部分切）。只切一刀，因为 `Theoria.md:280` 说切两刀就归因不了。

**它给了什么（这是真结果，可引用）。** `REPORT.md` §2/§4/§5：A0 上两臂 19 行里
**14 行完全相同、3 行有差且全部是证书行、2 行不可比**；消融臂在每个可测单位上更便宜
（Lean 4.1 s→0、形式化字节 149 773→0、定向戳探世界步 12→0、修复拍 8→0）。
A2 上两臂由同一份说明书证出**同一个假定理**，全臂被一个 18 步反例打脸并修好，
消融臂把一个 18 步可解的关卡归档为不可解。**「工程省 vs 理解省」这条区分本身，
现在有了一个可复核的机械演示**：工程省 = 删掉证明义务后仍然存活的那部分省钱，
理解省 = 只有证明义务能买到的「被证伪的能力」。

**它没给什么 —— 三条，不许略过。**

1. **没有成本切分的数。** `REPORT.md` §3(c)：**两臂的美元列都是 NOT MEASURED**，
   不是 0、不是平局；§7 限制 5 逐字写「cannot be filled offline」。
   C5 要的是**总账 10⁸→10⁶ 里哪几个数量级归工程、哪几个归理解**，
   而这个切分需要全臂与消融臂**跑同一局线上游戏**。
2. **这个臂没有线上形态。** `STATUS.md`：`ablcore/` 里**没有 harness、没有环境回路、
   没有模型掌台、没有 HTTP、不读 API key**；`ledger_abl.py:9` 自陈
   "Zero API calls, zero network, zero dollars"。工单 `A4-ablation-online`
   **被无人认领地退回看板**。另外 `proxy/ledger.py:36` 的 `ARMS`
   里**没有 `theoria_ablate`**，而 `:204` 对未注册臂名硬拒，
   所以消融臂在登记之前**一个字节的账本都写不出来**——一行改动，
   但在 proxy 轨道的领地里，消融臂自己不能改（`ablation-arm/DECISIONS.md` D-AB-004）。
3. **标定的是机制，不是效应量。** `REPORT.md` §7 限制 1：两个自建离线世界，
   零 API 接触、零封存堆接触，「No number here transfers to a live game as a magnitude」；
   限制 2：两臂**按设计共用一份说明书**，所以 A0 的分数/重放相等**部分是构造性的**，
   不能读成「消融臂学得一样好」。

**因此 A-1 的正确状态不是「已解决」，是「降级」**：
它不再挡住 **C2**（切分工具存在了，且刀口有论证、有门、有测试），
但仍然挡住 **C5**（切分要的数一个都没有，且离线拿不到）。
定稿清单里 A-1 应写作：**消融臂 = 已建成的离线标定臂；线上臂缺，
且是 C5 成本切分的唯一取数途径。**

---

*起草：engine-rig 轨道，工单 P-22，2026-07-28。*
*哈希基准：起草值 `25eee107` **已过期**，冻结提交待重取（见本文开头）。*
*陈旧扫描复核：2026-07-29，RES-3（`RECONCILE.md` §三 必修三）。*
