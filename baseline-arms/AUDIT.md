# baseline-arms — 既存状态审计（第 0 步）

审计时间：2026-07-28
审计者：`baseline-arms` 轨道
仓库 HEAD：`b364296`（arc-recon: determinism precheck is INCOMPLETE -- INC-002 blocks all gameplay）

本文件是**在写任何一行生产代码之前**做的强制审计。结论按工单三项列出，
最后一节记录审计过程中产生的、与工单预期不符的事实。

---

## 1. 关键词全文检索：ADR-0014 / INC-0008 / 复现战役 / 切堆 / 污染登记

检索范围：仓库内全部 `.md` / `.json` / `.jsonl`（排除 `.git`、`node_modules`、
Lean 工具链），外加 `Theoria.md` 全文与所有 `.py`。

| 关键词 | 命中 | 结论 |
|---|---|---|
| `ADR-0014` | **0 处** | 本仓库**不存在**任何 ADR 编号体系。没有 `ADR-*` 文件、没有 `docs/adr/` 目录。 |
| `INC-0008` | **0 处** | 不存在。本仓库的事件编号体系是 `INC-001 / INC-001a / INC-002 / INC-003`（四位数编号从未使用过）。 |
| 「复现战役」/「25 局」/ Schema 复现 | **0 处操作性记录** | 见 §1.2。Schema 复现**尚未开始**。 |
| 「切堆」/ dev heap / seal heap | **命中，且已落刀** | 见 §3。 |
| 污染登记 | **命中** | `arc-recon/data/contamination_log.jsonl`，4 行。 |

### 1.1 事件（incident）体系的实际状态

`arc-recon/data/incidents.jsonl`，4 条，全部属于 `arc-recon` 轨道：

| id | 严重度 | 标题（撮要） |
|---|---|---|
| `INC-001` | blocking | API key 不覆盖整个公开集：开发堆 4 局有 3 局 RESET 返回 400 |
| `INC-001a` | blocking | 修正诊断：可用性是**间歇的**，不是干净的权限边界 |
| `INC-002` | blocking | RESET 与下一次调用之间游戏消失：ACTION 0/8 成功，「整个在线 API 路线受阻」 |
| `INC-003` | process | 自伤：第一版预检把两次都失败的运行报成 PASS（比较器缺陷，已修） |

**INC-0008 不存在，且编号空间离它还很远。** 工单给的线索关键词与本仓库的实际
编号体系不匹配——见 §5 的疑虑登记。

### 1.2 Schema 复现的实际状态：**尚未开始，无任何既存数据**

`Theoria.md` 里 Schema 复现只以**占位符**形式出现，没有任何数据、代码或账本：

* 1.12 主表（`Theoria.md:271`）：
  `| Schema（复现口径） | 98.98%（上游）/ ⟨复现值⟩ | ~10⁸（实测 2.04–3.41 亿） | world_model.py（重放级） |`
  ——`⟨复现值⟩` 是**尖括号占位符，未填**。
* `Theoria.md:301`、`:311` 提到「复现桶轨迹」作为 Phase 2/3 的材料来源，
  但仓库里**不存在任何复现桶**：没有 `world_model.py`、没有 Schema 轨迹、
  没有对应的账本或 artifacts 目录。
* `Theoria.md:412` 有一句结论性表述「19 局满分只有 14 局真的复现了历史」——
  这是**对上游 Schema 论文的引述**，不是本项目复现的产出。

**判定：不存在既有的 Schema 复现战役，因此不存在「两份互不知情的权威数据」
的风险来源。本轨道是这项工作的第一次开工，不是重复劳动。**

（工单担心的分叉场景在本仓库的对应物是 `INC-003`：同一轨道内比较器缺陷导致
两次失败的运行被记为 PASS。教训已被 arc-recon 记录并修复，与本轨道无冲突。）

---

## 2. `/arc-gateway/`：**不存在**

```
$ ls -d arc-gateway
ls: cannot access 'arc-gateway': No such file or directory
```

仓库根目录只有：`CONTRACTS/`、`arc-recon/`、`cold-start-a0/`、`engine-rig/`、
`theory-compiler/`。`PARTNER_SYNC.md` 里也没有任何 `[arc-gateway]` 段落，
没有对应的 git tag。env_proxy / model_proxy / 账本三件套**均未开工**。

**结论：采用工单给定的「独立记账 schema」**，落在
`baseline-arms/ledger.jsonl`，两种记录形状严格照工单字面：

```
env_step    {"game_id","run_id","arm","model","action","frame","step_idx","timestamp"}
model_call  {"run_id","provider","model","usage","timestamp"}
```

诊断类记录（API 探测、重试统计）另落 `baseline-arms/probe_log.jsonl`，
**不混进 `ledger.jsonl`**，以便日后 arc-gateway 就绪时整份 ledger 可以逐行
直接并入。理由记于 `DECISIONS.md` D-003。

与 `arc-recon/data/recon_ledger.jsonl` 的格式对齐情况：它记的是 HTTP 层
（method/url/redacted headers/status/body），本轨道的 `probe_log.jsonl` 沿用了
**同样的字段名与 `<redacted>` 约定**，两者可直接拼接。

---

## 3. 开发堆 / 封存堆切分：**已存在，已落刀，本轮严格遵守**

`arc-recon/data/piles.json`，`cut_version: v1`，
sha256 `3feca53e5ede695cfa46ae994cb95fd6b43abb9d97295e8c87e6302b41bbc19a`
（与 `CLAUDE.md` 记录一致，未被篡改）。

**开发堆（4 局，本轮唯一允许触碰的集合）：**

| game_id | 标签 | baseline_actions（关卡数 / 总动作） |
|---|---|---|
| `ar25-0c556536` | keyboard_click | 8 关 / 848 |
| `g50t-5849a774` | keyboard | 7 关 / 878 |
| `sk48-d8078629` | keyboard_click | 8 关 / 1070 |
| `tn36-ef4dde99` | click | 7 关 / 317 |

**封存堆（21 局，本轮零接触）：** `bp35-0a0ad940`, `cd82-fb555c5d`,
`cn04-2fe56bfb`, `dc22-fdcac232`, `ft09-0d8bbf25`, `ka59-38d34dbb`,
`lf52-271a04aa`, `lp85-305b61c3`, `ls20-9607627b`, `m0r0-492f87ba`,
`r11l-495a7899`, `re86-8af5384d`, `s5i5-18d95033`, `sb26-7fbdac44`,
`sc25-635fd71a`, `sp80-589a99af`, `su15-1944f8ab`, `tr87-cd924810`,
`tu93-0768757b`, `vc33-5430563c`, `wa30-ee6fef47`。

切分规则（`piles.json` 内 `rules` 字段，逐字遵守）：封存局不玩、不看、不读，
**含上游释出的 artifacts**；切分文件在开局后被修改即视为事故。

### 3.1 本轨道的执行方式：把纪律写成代码，而不是写成注意事项

`harness/arc_client.py` 在 import 时加载 `piles.json`，任何指名封存局的调用在
**打开 socket 之前**抛 `SealedGameError`；前缀匹配，避免调用方漏掉版本后缀绕过。
本轨道**只读**这份文件，绝不修改（切分归 `arc-recon`，且改动即事故）。

本轮实际触碰的 game_id 持续追加到 `TOUCHED_GAMES.md`。

---

## 4. 环境实际可用的模型矩阵（探测所得，非预设清单）

工单要求「由你在 M1 审计阶段探测环境实际可用的模型配置后如实列出」。探测结果：

### 4.1 凭据

| 变量 | 状态 | 用途 |
|---|---|---|
| `ARC_API_KEY` | 已配置（`.env`，已 gitignore） | ARC-AGI-3 API |
| `ANTHROPIC_API_KEY` | 环境中已设置 | 见下：**不能直接调 API** |

**没有任何第三方 provider 的凭据**（无 OpenAI / Gemini / Mistral / xAI /
DeepSeek / OpenRouter / Together）。按工单，不新开通、不索取，因此跨模型矩阵
只能在 Anthropic 一家之内构成。

### 4.2 重要发现：`ANTHROPIC_API_KEY` 不能直接用于 Messages API

```
POST https://api.anthropic.com/v1/messages   →  401 invalid x-api-key
GET  https://api.anthropic.com/v1/models     →  401 Unauthorized
```

该 key 是 Claude Code harness 的宿主凭据，不是裸 API key。
**结论：本轨道的模型调用必须走 `claude -p` 无头 CLI，而不是 SDK 直连。**
这对本轨道恰好是**正确**的：工单要的是「裸 Claude Code」基线，
`claude -p` 就是字面意义上的裸 Claude Code，保真度比 SDK 复刻更高，
且 `--output-format json` 直接给出 `usage` 与 `total_cost_usd`。

### 4.3 环境里的模型别名变量是**陈旧的**（会 404）

| 变量 | 值 | 实测 |
|---|---|---|
| `ANTHROPIC_MODEL` | `Vendor2/Claude-4.6-Opus` | **404 模型不存在** |
| `ANTHROPIC_DEFAULT_OPUS_MODEL` | `Vendor2/Claude-4.5-Opus` | **404** |
| `ANTHROPIC_DEFAULT_SONNET_MODEL` | `Vendor2/Claude-4.5-Opus` | **404** |
| `ANTHROPIC_DEFAULT_HAIKU_MODEL` | `Vendor2/Claude-4.5-Opus` | **404** |

四个别名全部指向同一个不存在的模型。**直接后果：不能用 `--model haiku`
这类别名，必须写全 model id**；也说明「便宜/中/贵」三档不能靠别名区分。

### 4.4 实测可用的模型矩阵（每个都跑通了一次真实调用）

| 档位 | model id | 实测 | 单次 "Say PONG" 成本 | in/out tokens |
|---|---|---|---|---|
| 便宜 | `claude-haiku-4-5-20251001` | ✅ 可用 | $0.044015 | 10 / 58 |
| 中 | `claude-sonnet-5` | ✅ 可用 | $0.199069 | 2690 / 5 |
| 贵 | `claude-opus-5` | ✅ 可用 | $0.125219 | 2690 / 5 |
| — | `claude-fable-5` | ❌ 不可用（请求被拒绝） | — | — |

两点必须写进预算报告，否则外推会错：

1. **sonnet-5 的实测单价高于 opus-5**（$0.199 vs $0.125），与直觉相反。
   不要按「sonnet 比 opus 便宜」外推。
2. **haiku 的 input_tokens 是 10，opus/sonnet 是 2690**——同一句 prompt。
   差异来自 harness 注入的系统提示与缓存行为不同。这意味着**每档的固定开销
   必须分别实测，不能用一档的单价乘系数推另一档**。

---

## 5. 与工单预期严重不符之处（如实登记）

工单要求：若审计结果与预期严重不符，如实记录疑虑，但不因此停下。以下三条登记，
**均不构成停止条件**（无封存堆误用、无数据冲突）：

1. **工单给的线索关键词在本仓库不存在。** `ADR-0014`、`INC-0008` 命中 0 次；
   本仓库的事件编号是三位数 `INC-001..003`，ADR 体系压根没有。工单描述的
   「此前很可能已经有一个 Schema 复现战役在进行或已完成」在本仓库**不成立**。
   最可能的解释：工单是针对**另一个分支/另一份仓库**的历史写的。
   **处置：按本仓库的实际状态执行，不去凑一个不存在的 ADR 编号体系。**

2. **「两份互不知情的权威数据」的风险在本轮是零。** 因为 Schema 复现根本没有
   第一份数据。真正需要防的是反向风险：本轨道产出的账本必须从第一行起就与
   未来的 `arc-gateway` 格式兼容，否则**我们自己**会制造那个分叉。
   已按 §2 处置。

3. **本轨道独立复核后，推翻了 `INC-002` 的诊断。** 见 §6。这不是数据冲突
   （arc-recon 的 ledger 与我的 probe log 都是真实观测，互不矛盾），
   是同一现象的更好解释。按 PARTNER_SYNC 协议在我自己的段落里报告，
   **不修改 arc-recon 的任何文件**（含 `incidents.jsonl`）。

---

## 6. 独立复核结果：`INC-002` 是**可绕过的**，在线 API 路线未被封死

`INC-002` 的结论是「零次成功动作即无轨迹、无账本，整个在线 API 路线受阻」。
若成立，本轨道的工作一（裸 CC 基线）就无处可跑。因此**不继承该结论，独立复核**。
全部复核只在开发堆上进行，封存堆零接触（守卫代码保证）。

### 6.1 复现（`harness/probe_api.py`）

开发堆 4 局各 2 轮 RESET：`ar25` 0/2，`tn36` 0/2，`g50t` 1/2，`sk48` 1/2。
紧随的 ACTION 全部 400 —— **与 INC-002 现象一致**。
但有一条新事实：**`sk48` RESET 成功了**，而 arc-recon 记录它 0/6。
可用性不是按局固定的。

### 6.2 三个不同方向的尝试（`harness/probe_action_variants.py`）

arc-recon 已排除的（请求体四种形状、会话过期、未关闭 scorecard、card_id 处理）
不重复。本轨道试的是它没试的四个假设：

| 假设 | 做法 | 结果 |
|---|---|---|
| H-A 版本后缀 | ACTION 传 `sk48` 而非 `sk48-d8078629` | **200 成功** |
| H-B 只传 guid | 省掉 game_id | 400 `game_id not provided`（否证） |
| H-C 负载均衡假象 | 同一形状连续重试 | **重试后 200 成功** |
| H-D 路径大小写 / ACTION0 | `/api/cmd/action1`、`/api/cmd/ACTION0` | 404（否证） |

H-A 与 H-C 都成功，说明**决定性因素不是请求形状，而是重试**。

### 6.3 确证：带退避重试可以驱动真实对局

对 `sk48-d8078629` 实跑（每步最多 8 次重试、线性退避）：

```
RESET 第 4 次尝试成功
15 步中 11 步成功执行（73%）
每次成功动作的平均 HTTP 调用数：5.07
返回体键：action_input, available_actions, frame, full_reset,
          game_id, guid, levels_completed, state, win_levels
state = NOT_FINISHED，逐步推进，guid 在会话内保持有效
```

**修正诊断：`400 "game <id> not found"` 是瞬时故障（很可能是多实例后端中
只有部分实例持有该会话），不是权限边界，也不是会话丢失。正确处置是
「对 400 重试」，而不是「判定路线受阻」。**

副产物两条，写给未来的 harness：
* `score` 字段不存在；计分字段是 `levels_completed` 与 `win_levels`。
* `ACTION6`（点击）在传 `data={"x":32,"y":32}` 时返回 500，data 形状待定；
  纯键盘动作 `ACTION1..4` 正常。

### 6.4 代价：这条修正把 HTTP 开销放大约 5 倍

平均 5.07 次 HTTP 调用换 1 次成功动作。这个乘数**必须**进
`BUDGET_REPORT.md` 的外推，否则动作配额与墙钟时间都会低估 5 倍。

---

## 7. 审计结论

| 项 | 结论 | 对本轮的影响 |
|---|---|---|
| 既有 Schema 复现战役 | **不存在** | 本轨道是第一次开工，无重复劳动、无冲突结论风险 |
| ADR-0014 / INC-0008 | **不存在** | 工单线索与本仓库不匹配，已登记 |
| `/arc-gateway/` | **不存在** | 用独立记账 schema，格式向前兼容 |
| 开发堆/封存堆切分 | **已存在并落刀** | 本轮只用开发堆 4 局；守卫写进代码 |
| 模型矩阵 | 三档可用（haiku-4.5 / sonnet-5 / opus-5），走 `claude -p` | 别名变量陈旧，必须写全 id |
| 在线 API | **未被封死**，需重试策略，约 5.07× HTTP 放大 | 工作一可以真跑 |

**停止条件检查：** 无一触发。凭据齐备；封存堆零接触；`INC-002` 经三个不同方向
尝试后**已推进**（非「三次尝试仍无法推进」）；M4 尚未达成。继续 M2。
