# release/ — P-19 计划：把「可复现」从口号变成一条命令

基准：[Theoria.md](../Theoria.md) Phase 4「裁决与释出」一句——

> 释出清单——全部账本、两本书(各形态)与 Lean 证明、候选箱、探针日志、电池代码与回算结果、
> 冻结清单、incident ledger、复跑说明。规模与开放性够到 Schema 的地板(全公开集 + artifacts),
> 这些台账就是我们在地板之上叠的层。

本文件是**开工前的地图**：释出清单九项，逐项落到树上哪个路径、缺什么。它不粉饰。
写完这张表之后才动手做清单器与复跑器，两者都以本表为规格。

树的规模（HEAD `dc9fad1`，worktree `agent/p19-release-kit`）：**1098 个受追踪文件，62.1 MB**。

---

## 释出清单 · 九项对照表

图例：**✅ 齐** = 有具体产物且可入清单 · **⚠️ 半** = 有产物但有缺口 · **❌ 缺** = 树上没有

### 1. 全部账本 — ⚠️ 半

| 路径 | 内容 | 可离线复算？ |
|---|---|---|
| `proxy/LEDGER_FORMAT.md` `proxy/ledger.py` `proxy/canon.py` `proxy/cost.py` | 账本规范 v1.0 与其可执行形态 | 规范，非数据 |
| `proxy/tools/validate_ledger.py` `upgrade_ledger.py` | 读侧校验 / 迁移 | ✅ |
| `baseline-arms/ledger.jsonl` | 560 行，5.2 MB，三臂基线；185 行带完整 64×64 帧 | ❌ 活体 API 产物 |
| `arc-recon/data/recon_ledger.jsonl` | 1214 行，3.9 MB，HTTP 全捕获；180 行带帧 | ❌ 活体 |
| `theoria-arm/runs/*/ledger.jsonl`（9 个） | 241 行，proxy canon v1.0；g50t 首次接触 | ❌ 活体 |
| `cold-start-a2/artifacts/loop_ledger.json` | 177 行内环节拍账 | ✅ |
| `battery/tests/fixtures/ledger_fixture.jsonl` | 384 行，冻结夹具（dev 堆 ar25） | ✅ |
| `arc-recon/data/contamination_log.jsonl` `canary_runs.jsonl` | 污染台账 / 金丝雀 | 台账 ✅ / 金丝雀 ❌ |

**缺口 L-1**：`baseline-arms/harness/ledger.py` 仍是旧方言，F-16 已裁定须迁到 proxy canon，未迁。
释出时两种方言并存，清单必须写明哪一份账本是哪种方言。
**缺口 L-2**：`proxy/var/` 被 gitignore（"格式受追踪，运行产生的数据不受"），
所以 proxy 自己**从未有活体运行的账本**进释出集；`proxy/runs/p9-shell-harden/` 只是跨会话确定性证据。

### 2. 两本书（各形态） — ⚠️ 半

书源 42 个 `.dsl`；四形态生成目录 16 个，**全部受追踪，无一进 gitignore**。

| 生成目录 | py | lean | pddl | md |
|---|---|---|---|---|
| `cold-start-a0/theory/generated/`、`generated_no_button/`、`prime/theory/generated/` | ✔ | ✔ | ✔ | ✔ |
| `cold-start-a2/theory/generated/`、`_holed/`、`_repaired/` | ✔ | ✔ | ✔ | ✔ |
| `cold-start-a3/theory/generated_l1/`、`_l1_vacuous/`、`_l2/`、`_l2_scratch/`、`_l2neg/`、`_l2rew/` | ✔ | ✔ | ✔ | ✔ |
| `cold-start-a0/prime/theory/generated_seeded/` | ✔ | — | ✔ | ✔ |
| `cold-start-a2/theory/generated_repaired_stale/` | ✔ | ✔ | — | — |
| `theoria-arm/runs/…-first-contact/books/generated/` | ✔ | — | ✔ | ✔ |
| `a0-spike/artifacts/`（平铺） | ✔ | ✔ | ✔ | — |

后三行的缺角**都是自报的、有理由的**，清单要照抄理由而不是补齐：
`generated_repaired_stale/` 是**故意的红件**（README:56）；theoria-arm 缺 Lean 是
`inner/books.py:38` `LEAN_STATE_CEILING = 200_000` 在真关上主动放弃证明层，
`certify.expensive` 报 `available: false`——"不可用的证明层永远不算通过的证明层"。

**缺口 B-1（真缺口）**：四个生成器只吃 `TheoryAST`。
`grep playbook theory-compiler/src/theory_compiler/generators/*.py` → 零命中。
**玩法书没有任何生成形态**，只有 DSL 源。`exam/handover_bundles/*/PLAYBOOK.md` 是手写的
（`MANIFEST.json` 里 `written_for: "this exam"`），而同目录 `MANUAL.md` 是
`render_manual` 生成、`model_calls: 0`。所以「两本书（各形态）」目前是
**说明书四形态 + 玩法书一形态**。释出清单必须逐字这样写。

### 3. Lean 证明 — ✅ 齐（真工具链，非桩）

| 路径 | 说明 |
|---|---|
| `theory-compiler/lean/lean-toolchain` | `leanprover/lean4:v4.9.0`，钉死 |
| `theory-compiler/lean/lakefile.lean` `lake-manifest.json` | `"packages": []`——无 Mathlib，`lake build` 离线 |
| `theory-compiler/lean/TheoriaLean.lean` | 旗舰证明，逐字节可复现（pagoda `w=[-1,1,0,1,-1]`，来自 LP 证书） |
| `a0-spike/artifacts/A0.lean` | 核心 Lean 4，sokoban 奇偶 |
| 15 × `*/theory/generated*/theory{,_latch}.lean` | 逐臂生成 |

真编译的证据：`tests/test_gen_lean.py` `subprocess.run([LEAN, target])` 断言 `returncode == 0`；
`conftest.py` 的 `THEORIA_REQUIRE_LEAN=1` 把「PATH 上没有 lean」从 skip 升成 `UsageError`；
`cold-start-a0/certify/lean_check.py` 独立解析公理集与 `sorry`；负控真跑过（把 `w.p1` 从 1 改成 7，
`lean` 报 `decide proved … is false`，四条定理全部 `depends on axioms: [sorryAx]`，退出码 1）。

**缺口 X-1**：**没有任何命令重新生成 `lean/TheoriaLean.lean`**。
`test_gen_lean.py:274` 说"去 README 看怎么重生成"，README:41-55 给的片段却写去 `Theory.lean`（另一个文件名）。
测试注释自陈"没有东西会自己重生成它——所以它会静默漂移。它漂过。"
陈旧性测试是唯一守卫。**复跑器必须把这条当作已知缺口显式报出，不能装作四形态全可重生。**

### 4. 候选箱 — ✅ 齐

契约 `CONTRACTS/candidates_schema.md`（冻结 v0.1）+ 两个独立可执行形态：
`engine-rig/tools/validate_candidates.py`（v0.1）、`theory-compiler/tools/validate_candidates_v02.py`（v0.2，互不 import）。

主流：`engine-rig/artifacts/candidates.jsonl`（44 行，八引擎六 kind，逐字节稳定）。
另有 `cold-start-a0|a2|a3/artifacts/candidates*.jsonl` 与 `theoria-arm/runs/*/candidates.jsonl`（2959 行，唯一活体）。

**缺口 C-1**：`theoria-arm/runs/*/candidates.jsonl` ——树上唯一的活体候选流——
**没有任何地方调用过校验器**。清单器要顺手把它验一遍，验不过就如实记。
**缺口 C-2**：`CONTRACTS/candidates_schema_v0.2.md` 与 `ic3_certificate_v0.1.md` 仍是 **draft，未会签**。

### 5. 探针日志 — ⚠️ 半

`baseline-arms/probe_log.jsonl`（1945 行 HTTP 转录）、`theoria-arm/runs/*/probes.jsonl`（2 行，两条都 `phase: "unrunnable"`）、
`cold-start-a2/artifacts/probes.jsonl`（5）、`probed_trace.jsonl`（196）、`probe_report.json`、
`cold-start-a0/prime/artifacts/probes_runB.jsonl`（1）、`probes_runA.jsonl`（**0 行，空文件**）、
`arc-recon/data/stickiness_probe.json`。

**缺口 P-1**：探针日志**异构、无统一 schema**（候选箱有契约，探针没有）。
`baseline-arms/probe_log.jsonl` 是 HTTP 转录，其余是探针设计记录，两者字段不交。
本轮不造契约（越界），但清单必须按方言分组列出，不能假装是一种东西。

### 6. 电池代码与回算结果 — ✅ 齐（本清单最强的一项）

```
python -m battery.run_battery      # 31 runs, 4 arms, 38 metrics -> battery/artifacts/
python -m pytest battery/tests -q  # 117 tests
python -m battery.docs             # 从注册表重生成 METRICS.md
```

完全离线（"Nothing here opens a socket"），逐字节确定（无墙钟，只存输入摘要；统计手搓不用 scipy），
`tests/test_determinism.py` 对四件产物做 sha256。产物 6 个 JSON + 归档 `battery/runs/P-14/`。

**已自报的弱点照抄进释出说明**：38 个指标中 21 个从未在对照臂上算过；
当前数据下无一指标达 p<0.05（W-3）；经济族在任何"有理论"的臂上零数据（W-5）。

### 7. 冻结清单 — ❌ 缺（13 项里 2 项齐、2 项全无）

`freeze/` 目录不存在。`arc-recon/data/campaign_freeze.json` 是金丝雀漂移闸，与 Phase 4 冻结无关。
P-22 是它的工单，尚未落地。逐项：

| # | 冻结项 | 树上 | 状态 |
|---|---|---|---|
| 1 | 内环代码 | `theoria-arm/inner/` | ✅ 有，未哈希 |
| 2 | DSL 语法版本（两本书） | `CONTRACTS/dsl_grammar_v0.{1,2}.md` | ✅ |
| 3 | 生成器 | `engine-rig/fixtures/generate_all.py`、`cold-start-a0/world/`、`cold-start-a2/a2world/` | ⚠️ 散落，无总表 |
| 4 | 提示词 | **无 `theoria-arm/prompts/`**；提示词内联在 `inner/theorize.py` | ⚠️ 未隔离 |
| 5 | 引擎清单与版本 | `validate_candidates.py:22-29` 的 `ENGINES` 集 | ⚠️ 有清单，**无版本串** |
| 6 | 戳探策略 | `theoria-arm/inner/probe.py`、`engines/probe_frontier/` | ⚠️ 有码，无冻结规格 |
| 7 | 规划器配置 | `engines/fd_adapter/backends.py`、`runs/p13-fd-real/TOOLCHAIN_MANIFEST.md` | ⚠️ FD 二进制在 gitignore 的 `.toolchain/` |
| 8 | 指标电池 v1 | `battery/` 全套 | ✅ |
| 9 | 变体算子库 | `proxy/variants.py`、`exam/artifacts/variant_specs/`（17）、`a0-spike/pipeline/adapt.py` | ⚠️ 三套不相交 |
| 10 | 统计裁决规则 | 只在 Theoria.md 散文里 | ❌ |
| 11 | claim 逐字文本与双结局 | C1–C5 在散文里；**双结局文本全树无** | ❌ |
| 12 | 预算表 | `baseline-arms/BUDGET_REPORT.md`、`browser-ops/TERMS.md` | ⚠️ 只有分臂包络 |
| 13 | 每格重复数 n | `summarise_campaign.py` 能算，**值未写死** | ⚠️ |

Theoria.md「冻结前待定五项」（⟨N⟩、开发堆局数、模型版本串、⟨B,Δ,k,m,n⟩、目标会议与死线）——**五项皆无文件**。

**本轮的处置**：P-19 不越界去做 P-22 的活。清单器把第 7 项整块标 `MISSING`，
并把上表逐行写进 `MANIFEST.jsonl` 的 checklist 段，让缺口在释出物里可见而不是在某人脑子里。

### 8. incident ledger — ⚠️ 半

| 路径 | 条数 | 方言 |
|---|---|---|
| `arc-recon/data/incidents.jsonl` | 16（`INC-NNN`） | JSONL，正册 |
| `baseline-arms/INCIDENTS.md` | 3（`INC-BA-*`） | Markdown |
| `theoria-arm/INCIDENTS.md` | 5（`INC-TA-*`） | Markdown |
| `arc-recon/data/contamination_log.jsonl` | 24 | JSONL，裁定的更正/覆盖，兼作附册 |

**缺口 I-1**：**没有统一的 incident 台账**。三种 id 家族、两种 schema、四个文件。
`proxy/LEDGER_FORMAT.md` §6 还定义了一个从未被使用的 `incident` 记录类型——第四个面。
释出清单点名「incident ledger」单数，本轮的诚实做法是在 MANIFEST 里**显式声明这是四文件合集**，
并给出合并视图 `release/INCIDENTS_INDEX.md`（只做索引，不改原件——原件是各领地的，不越界）。

### 9. 复跑说明 — ❌ 缺 → 本轮的主交付

树上没有任何跨领地的复跑文档。各领地 README 各说各的，命令散在 10 个文件里。
**这正是 P-19 要造的东西**：`release/REPRODUCING.md` + `release/reproduce.py` + `release/verify.sh`。

---

## 附：runs 档案（释出清单未点名，但「这些台账就是我们在地板之上叠的层」要它）

10 个领地有 `runs/`，共 ≈33.5 MB，其中 theoria-arm 占 32.4 MB（97%），
而这 32.4 MB 里 30.0 MB 是三个 `candidates.jsonl`——生成的候选理论，不是 API 记录。

`theoria-arm/runs/*-salvage*/` 三个目录只有 4–12 行的 `ledger.jsonl` 残桩，
清单里单列一类 `stub`，让读者不必猜它们为什么是空的。

---

## 红线自检 — 清单器必须证明的两件事

### R-1 释出集里无 `.env` 值
先验结论（本轮 subagent 全树扫描）：**干净**。
3137 处 `"X-API-Key"` 全是 `"<redacted>"`（捕获时由 `arc-recon/redact_ledger.py` / `proxy/redact.py` 抹掉）；
`sk-ant-abcdef…` 一类只出现在 `proxy/tests/` 的红队夹具里；`.env.example` 的 `ARC_API_KEY=` 为空。
但**先验结论不算证明**——清单器要在每次跑时重算：读 `.env` 取真值，
对释出集每个文件做子串搜索，同时按形状（`sk-ant-`、长度 ≥ 24 的高熵 token）扫一遍。
真值本身**绝不落盘**，只落"未命中"的判定与被扫文件数。

### R-2 释出集里无封存局帧数据
`arc-recon/data/piles.json`（sha256 `3feca53e…41bbc19a`）：
开发堆 4 局 `ar25-0c556536` `g50t-5849a774` `sk48-d8078629` `tn36-ef4dde99`，其余 21 局封存。
先验结论：**每一帧都属于开发堆**（baseline-arms 185 帧、arc-recon 180 帧、theoria-arm 187 个 `env_step`、
battery 夹具 384 行，逐条解析 `game_id` 核对过）。清单器每次跑时重算这个核对。

**但有三件事清单器必须主动报出来，不能靠"没有帧"蒙混过去：**

* **R-2a `recon_ledger.jsonl` 第 1、24 行的 `GET /api/games` 响应，列出全部 25 局的
  `baseline_actions` 数组**（逐关人类动作数，如 `wa30-ee6fef47: [71,119,183,98,368,68,79,442,415]`）。
  这不是帧，是**封存局逐关难度的定量信号**，躺在一份要释出的账本里。需要一条明确裁定。
* **R-2b `dc22-fdcac232`（封存）的机制印在仓库里**，约 50 个文件：`Theoria.md:161` 给了 `teleport`
  规则和 `unsolvable_L3` 奇偶论证，`:416` 还计划了「图 5 DC22 案例」。
  已裁（`contamination_log.jsonl` 第 5 行 INC-004 → `design_document_disclosed`，
  `claims: retained_with_sensitivity_analysis`），不是新泄漏，但**释出清单必须把它顶到台面上**：
  一局封存游戏的失败结构随释出的散文与图一起出版，凡跨封存 claim 集的统计都背着敏感性分析义务。
* **R-2c `baseline-arms/TOUCHED_GAMES.md` 与 `ledger.jsonl` 自相矛盾**。文档为 `sk48-d8078629`
  的 `scores_only` 定级辩护时称"帧只以 `"<1 frame(s)>"` 的形状摘要存在，像素未落盘"——
  这对 `probe_log.jsonl` 成立，但 `ledger.jsonl` 里**确有 45 张 sk48 的完整 64×64 像素**。
  四局都在开发堆，**不是封存违规**，但定级理由写错了，评审会找到。清单器把它记成一条 finding。

---

## 本轮产物与验收

| 产物 | 是什么 | 判据 |
|---|---|---|
| `release/PLAN.md` | 本文件 | 九项逐项落到路径，缺口不粉饰 |
| `release/manifest.py` | 清单器 | 逐文件 sha256 → `MANIFEST.jsonl`；九项打勾/标缺；R-1/R-2 每次重算 |
| `release/MANIFEST.jsonl` | 释出集哈希册 | 每行一文件 + 尾部 checklist / redline 记录 |
| `release/CHECKLIST.md` | 九项对照的人读版 | 与 MANIFEST 同源生成 |
| `release/INCIDENTS_INDEX.md` | 四文件 incident 合并索引（只索引不改原件） | 条数对得上 |
| `release/reproduce.py` | 一条命令复跑 | 按领地重跑确定性产物，与 MANIFEST 比哈希 |
| `release/REPRODUCTION_REPORT.md` | 复跑报告 | 跑不了的按 `NEEDS_API` / `NEEDS_TOOLCHAIN` / `KNOWN_GAP` 分级，失败与成功同等归档 |
| `release/REPRODUCING.md` | 陌生人复跑指南 | 由一个**全新 subagent 照文档执行**验收；卡住就改文档 |
| `release/verify.sh` | 收工闸 | 复跑一遍 ∧ 哈希全对 ∧ 红线绿；不绿不收工 |
| `.claude/skills/reproduce-check` | 把复跑验证沉淀成技能 | 可被后续会话直接调用 |
| `release/runs/<UTC>-p19/` | 边跑边落盘 | 失败的跑与成功的跑一样归档 |

**分级词表**（复跑报告只准用这五个）：

* `REPRODUCED` — 重跑了，哈希逐字节对上。
* `REPRODUCED_UNSTABLE` — 重跑了，产物语义等价但字节不同（须写明差在哪个字段）。
* `NEEDS_API` — 需要活体 ARC / 模型 API 与配额，陌生人无法复跑，只能核账本。
* `NEEDS_TOOLCHAIN` — 需要仓库里没有的本地二进制（Lean 4.9.0、Fast Downward）。
* `KNOWN_GAP` — 树上根本没有重生成路径（如 X-1 的 `TheoriaLean.lean`）。

失败不许降级成"环境问题"。跑不绿就是跑不绿，写进报告。
