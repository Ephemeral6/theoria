# PROPOSAL — 撤销主表「Schema（复现口径）」列，并逐字替换 C1/C2/C5 中的 Schema 措辞

**发件**：`baseline-arms` · 2026-08-01 · 分支 `ep/schema-arm-ruling`
**收件**：`theory`（`Theoria.md`）· `freeze`（`CLAIMS_TEXT.md`）· `battery`（臂名）· `papers`（phase1-workshop）
**依据**：[`baseline-arms/SCHEMA_ARM_RULING.md`](../../baseline-arms/SCHEMA_ARM_RULING.md)
（含留痕 `baseline-arms/runs/20260801T0600Z-schema-column/`）

**本轨道不编辑上述任何文件。** 以下是提案，逐条给出「原文 → 替换」，
落地与否由各 territory 的所有者决定。

---

## 0. 三句话

1. `Theoria.md:271` 的 **Schema（复现口径）** 列承诺一个**永远填不了**的复现值——
   官方 harness 从未发布，重实现被纪律禁止且会污染确认集，
   即便越过这两道，按 `pricing_v1` 计价是 **$4,061 / 25 局**，池中 $143.50。
   裁决：**撤销该列**（不是留空——留空维持了「有一天会填」的预期）。
2. **同一批材料保留**为明确非复现的**参照行**，改名 `schema_upstream`，
   每次引用随附覆盖面（开发堆 4 局 / 25 局；call 类指标 1/2 套采集）。
3. **新证据**：那一列里唯一自称「实测」的格子测不出来。
   `~10⁸(实测 2.04–3.41 亿)` 在本轮两种计数口径下**均不重现**
   （去重 0.756–2.85 亿；朴素 3.19–13.19 亿），
   且该区间的出处在本仓库中不存在。量级留，区间删。

---

## 1. 给 `theory`（`Theoria.md:271`）

**原文**

```
| Schema(复现口径) | 98.98%(上游)/ ⟨复现值⟩ | ~10⁸(实测 2.04–3.41 亿) | world_model.py(重放级) |
```

**替换**：该行**移出主表**，主表只留同壳三臂（裸 CC / Theoria / 消融臂），
上游另置于表下的「外部参照」小表：

```
外部参照(**不是本框架的臂,不同壳,不进消融梯度**):
| 系统 | 分数 | 单局缓存读 | 交付物 | 覆盖面 |
|---|---|---|---|---|
| Schema(上游发布轨迹,**未复现**) | 98.98%(上游自报,25 局) | 10⁷–10⁸(本项目实测) | world_model.py(重放级) | 开发堆 4 局 · 两套采集中记 token 的 1 套 |
```

**脚注（建议逐字）**

> 官方 harness 从未发布（`baseline-arms/SCHEMA_LOCATE.md` §2.2），因此本项目
> **不存在也不会存在**同壳复现值；此前的 `⟨复现值⟩` 占位符已按
> `baseline-arms/SCHEMA_ARM_RULING.md` 撤销。缓存读为本项目对上游轨迹的逐 run
> 实测：去重口径 0.756–2.85 亿（4 个 run），朴素树遍历口径 3.19–13.19 亿；
> 此前表内的「实测 2.04–3.41 亿」在两种口径下均不重现，出处在仓库中不存在，故删除。

**顺带一条早已登记、至今未订正的事实**（`SCHEMA_LOCATE.md` §1.1）：
上游规范署名是 **Zeng et al.**，不是 Feng et al.（Haiwen Feng 是末位作者）。

---

## 2. 给 `freeze`（`CLAIMS_TEXT.md`）

### 2.1 前提修正段（L23-28）

**原文**

> **一条贯穿全篇的前提修正（needs_human）**：`schema_repro` 臂**不存在**，
> 官方 harness 从未发布（`baseline-arms/SCHEMA_LOCATE.md`），
> 且没有任何低成本合规路径能造出它。

**替换**

> **一条贯穿全篇的前提修正**：**同壳的 Schema 复现臂不存在，也不会存在**——
> 官方 harness 从未发布（`baseline-arms/SCHEMA_LOCATE.md` §2.2），
> 三条替代路径已逐条定价并关闭（`baseline-arms/SCHEMA_ARM_RULING.md` §3）。
> **存在的是另一样东西**：上游在开发堆 4 局上发布的轨迹，已摄入为
> `schema_upstream` 参照行（8 个 run，`battery` D-B-019）。
> 这两句必须一起读——此前本段只写了前一句，而当时后一句已经为真六个小时以上。

### 2.2 C1

C1 的算术**从来不含 Schema**（单样本比率，对照臂构造性为零，`STATS_RULES.md` §1）。
需要的不是重述，是摘掉一个从未承重的依赖，并把「唯一」的辖域写死：

> ### 重述（依赖已摘除：本条从不依赖 Schema）
> …「唯一」一词的辖域**限于同壳三臂**，逐字写作
> 「**在本实验的同壳三臂中唯一**」，不得读成对所有已知框架的排他主张——
> 上游 Schema 未被同壳评测，本文对它在 U3/U4 上的表现**不作任何主张**。

### 2.3 C2 —— 这一条最重

**「vs Schema 平坦」不是未测，是在现有材料上不可测。**
E2（前载指数）在整条上游臂上返回 `not-applicable`，理由逐字是
“no model call carries a cost”（8/8 个 run）。
一个永远返回 not-applicable 的比较项不能留在 claim 文本里当比较项。

> ### 本文件采用的形式（Schema 项已撤除）
> > 前重后轻、随理论收敛趋零，**相对同壳裸臂**——理解的签名。
> >
> > **「vs Schema 平坦」已撤除，且不是因为没测到。** E2 需要逐次模型调用的成本，
> > 而上游语料**任何拼写下都没有成本字段**（`battery/adapters/schema_traces.py`）。
> > 在这批材料上它**不可测**，而不是待测——所以它不能作为 C2 的比较项存在，
> > 也不能进限制节当作「将来补」。

`battery/PREDICTIONS.md:78` 的方向预注册 `theoria > schema ≈ bare_cc`
**保持原样不改**（改预注册就毁了预注册）；改的是它的**裁决口径**：
`schema` 项判 `not-applicable`，该预测按「不可评」结算，不计命中也不计落空。

### 2.4 C5

**成立版第二句** —— 原文「Theoria 相对上游 Schema 报告的 ~10⁸ 量级低 ⟨…⟩ 个数量级」
→ 替换为：

> Theoria 的单局缓存读为 ⟨…⟩。作为**外部参照而非对照**：上游 Schema 发布轨迹在
> 开发堆 4 局上的实测单局缓存读为 **0.756–2.85 亿**（去重口径，4 个 run；
> 另一套采集不记 token）。**两者不同壳、不同计价口径，其比值不构成本条的任何主张。**

**三条硬约束第 1 条** → 替换为：

> 1. **同壳复现值不存在，且已裁决为永远不存在**（`SCHEMA_ARM_RULING.md` §3 路 (a)）。
>    `Theoria.md:271` 的 `⟨复现值⟩` 占位符**已撤销**（此前是「合规留空」，
>    现改为撤销）。**另注**：主表旧写的「实测 2.04–3.41 亿」出处在仓库中不存在，
>    且在两种计数口径下均不重现，已一并删除。

---

## 3. 给 `battery`

**唯一一条请求：臂名 `schema_repro` → `schema_upstream`。**

`repro` 这三个字母是 D-B-019 那次混淆的残留物，而残留物会再次被读——
本轮就发现 `freeze/CLAIMS_TEXT.md:23` 至今写着这条臂「不存在」，
论文写着它存在但不是复现，臂名写着它是复现。三处三说，只有论文那处对。

影响面（`battery` 自行核实）：`adapters/schema_traces.py` 的 `ARM`、
`artifacts/*.json` 的 `provenance.arms` 与 `runs[*].arm`、
`audit/discriminate.py`、`run_battery.py`、`BATTERY_V1.md` / `METRICS.md` /
`PREDICTIONS.md` / `REPORT_V2.md` / `STATUS.md`。
**`runs/` 下的历史 artifacts 建议不动**——它们是当时的账，改它们等于改历史；
改名应作为一次带 DECISIONS 条目的迁移，旧名在该条目里保留为 alias。

D-B-019 与 D-B-020 **无须撤销**，本裁决与两者一致，只是把它们的结论
推到了臂名与主表上。

---

## 4. 给 `papers`（phase1-workshop）

正文**基本无须改写**——§7.2 已写 “It is not a reproduction”，
§7.2a 已点名半条臂的混杂。需要的是三处一致性改动 + 一句新的 limitation：

| 位置 | 改动 |
|---|---|
| L464 / L1758 / §7.2 表头等处的 `schema_repro` | 随 battery 改名（**等 battery 先落地，论文跟随**） |
| L1763-1765 “the `⟨复现值⟩` cell in `Theoria.md` stays empty” | → “the cell has been **withdrawn** rather than left empty (`baseline-arms/SCHEMA_ARM_RULING.md`)” |
| §2192 附近 E2 的 `no-data` | → `not-applicable`：上游语料无成本字段是**结构性缺席**，不是这次没取到 |

**新增 limitation（建议逐字）**

> The one cell of the upstream comparison that claimed a measurement — the
> per-episode cache-read magnitude — does not reproduce. Recomputing it from the
> released trajectories gives 0.756–2.85 × 10⁸ tokens per run under per-message
> deduplication and 3.19–13.19 × 10⁸ under a naive traversal; the published
> 2.04–3.41 × 10⁸ falls between the two and is produced by neither, and no
> provenance for it exists in this repository. The order of magnitude survives;
> the interval does not.

---

## 5. 本轨道已经落地的部分（不需要任何人批准）

* `baseline-arms/SCHEMA_ARM_RULING.md` —— 裁决书，含全部证据与三条路的定价；
* `baseline-arms/harness/schema_column.py` —— `measure`（重算，只出聚合量，
  绝不写出帧/动作/转录/世界模型源码，D-B-020）与 `check`（拒绝填了复现值的文本）；
* `baseline-arms/tests/test_schema_column.py` —— 25 例，**先驱动 9 个伪造违规
  并要求逐个被拒**；把守卫短路成永远返回空之后 10 个测试转红。
* 门：`cd baseline-arms && python -m pytest -q` → **534 passed**（基线 509 + 25）。

## 6. 本提案不主张的事

* 不主张 `98.98%` 可信或不可信——它是上游自报、25 局，我们只有 4 局，
  其中 21 局按纪律永不可核。它只能作为**引用**存在。
* 不主张 25 局上的缓存读量级；4 局的读数不外推。
* 不主张「不存在任何计数口径能产生 2.04–3.41 亿」——只主张我试的两种都不能，
  且仓库里查不到出处。若有人知道那个口径，
  `harness/schema_column.py` 的 `TABLE_CLAIM` 是一个常量，改它再跑即可。
