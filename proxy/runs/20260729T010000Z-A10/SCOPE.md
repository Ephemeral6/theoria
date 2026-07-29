# A10 范围裁定：工单的四条前提里，两条不成立、一条越界、一条无效

W-1641，2026-07-29T01:1xZ。三个 subagent 并行普查与实现，本文件是主上下文的裁定。
**先落盘，因为这四条比代码更重要，且它们改变了这件活该怎么做。**

工单要求四件事。逐条对照实际的树之后：

## 1. 「三条真臂billing 进同一份账本」——**跨领地，本工单权限不够**

本工单 `territory: proxy`。但三条臂各自**有意**写自己的账本：

| 臂 | 写到哪 | 用 proxy 的 writer 吗 |
|---|---|---|
| theoria-arm | `runs/<slug>/ledger.jsonl`（`harness/run.py:97`） | 是 |
| ablation-arm | `<out>/episode.jsonl`（`run_arm.py:410`） | 是，但在自己的目录 |
| baseline-arms | `baseline-arms/ledger.jsonl` 或 `out/shards/`（`harness/ledger.py:63-85`） | **否**，另一套 v0 方言 |

**ablation-arm 是明写的设计决定，不是疏漏**（`ablcore/ledger_abl.py:9-25`）：
「`proxy.ledger` 的 writer 直接用在**本臂自己 run 目录**里的路径上，
和 `theoria-arm` 一样（`runs/<slug>/ledger.jsonl`，**never `proxy/var/`**）」。
它还记了一条 D-AB-004：`ledger.ARMS` 是 frozenset，
`{bare_cc, schema_repro, theoria, probe, replay, mock_arm}` **没有消融臂的名字**，
而「加一个名字意味着编辑另一条赛道的文件，仓库里每份 arm README 都禁止这件事」，
所以它的记录暂时挂在 `arm: "theoria"` 名下，并已在 PARTNER_SYNC 上
**挂了一条注册 `theoria_ablate` 的请求，至今没有回复**。

**裁定**：改这三条臂的源码不在 `proxy` 领地内，且要推翻一条已登记的设计决定。
本工单做 proxy 侧的**使能**（见 §2、§3），臂侧改线**如实记为 gap**，
并建议拆成三件各自领地的工单；`theoria_ablate` 的注册请求请一并裁决——
那一条恰好在 `proxy` 领地内，是本工单唯一可以顺手清掉的部分。

**注意 theoria-arm 不需要改源码**：`harness/run.py:230,238-244` 已经把
`ledger_path` 作为参数向上传，指到共享账本是**配置，不是代码改动**。

## 2. 「分数字段 API 不返回，所以对账义务不可清偿」——**口径过宽，会丢掉一个真的能用的检查**

正典早就写着（`LEDGER_FORMAT.md:184-188`）：`score` 是**命令响应**不返回的字段，
API 回的是 `levels_completed` 与 `win_levels`。
**出处是 INC-TA-002**（`theoria-arm/INCIDENTS.md:64,71-78`），
比 W-1640 的那句早约 21 小时；W-1640 那句（`20260729T002000Z-W-1640-a3-spend-proposal.md:16-17`）
**没有附证据**，而它自己的 run 产物反倒正确引用了 INC-TA-002。
字节级复核：`arc-recon/data/recon_ledger.jsonl` 里 196 条成功命令响应，
**零条带 `score` 键**——claim 本身是真的。

**但记分卡 close 响应是带 `score` 的**（`proxy/SCORING.md:40-44`，
`proxy/tests/fixtures/scorecard_corpus.json` 里有 32 张真卡）。

**所以缺的是「每步分数」，不是「每局分数」。** 每局分数可交叉核验。
工单说「分数改由各臂自报并标注为不可交叉核验」——照做会**放弃一个真的能用的检查**，
正好和本工单的目的相反。已发指令给实现者：标注只覆盖 per-step，
per-run 记分卡比对保留为真检查。

## 3. 「对账改为 cost × actions × turns 三元组」——**同样不可清偿，只是换了个理由**

* **cost**：可导出，**有意不记录**（`canon.py:110-134` 明令禁止
  `cost`/`cost_usd`/`total_cost_usd` 等拼写；`LEDGER_FORMAT.md:271-286`）。
  每条 `model_call` 由 `usage` + `pricing_ref` 经 `proxy/cost.py:48` 导出。
* **actions**：**有记录**。每个 ARC 命令一条 `env_step`，`step_idx` 单调，RESET=0。
* **turns**：**根本不存在**。`battery/INPUT_FORMAT.md:72-76` gap 5 写着
  「No turn index distinct from `step_idx`. Still open upstream.」
  theoria-arm 的回合轴在账本**之外**的 `turns.json` 里，靠
  `armtools/archive.py:689 turn_series()` 结构化 join，并且**自带一个
  `join_confidence`，因为这个 join 不精确**。ablation 的回合数在 `run_report.json`，
  baseline 任何层级都没有回合数。

**结论：这个三元组 per-record 对谁都算不出来**；per-run 只有 theoria 齐全，
baseline 缺 turns，ablation 只有 actions。

**这是本工单最该记的一条**：那条裁决**用一个不可清偿的义务替换了另一个**，
而这正是它自己要逃离的陷阱。已发指令：只按**当前真的记录得到**的量重新定键，
把 turns 明写成缺口（§8 允许加**可选**字段而不动 `v`，`canon.py:38-45` 有先例），
**既不伪造一个不存在字段上的比对，也不悄悄把这条要求删掉**。

## 4. 「绿了之后图 2 的第一道锁就开了」——**图 2 根本不读这份账本**

`figures/fig02_bill_shape.py` 读四个来源，**没有一个是 `proxy/var/ledger.jsonl`**：
`baseline-arms/ledger.jsonl`、`baseline-arms/out/shards/ledger.*.jsonl`、
`baseline-arms/out/pilot_*.json`、`theoria-arm/runs/*/{cost_curve.json,MANIFEST.json}`
（`figures/sources.py:70-74,350-395`）。
而且 `_classify()`（`fig02:236-260`）只认两种方言、要求顶层 `total_cost_usd`，
**明确拒绝 v1.0 是「第三种方言」**（`fig02:40-48`）——theoria 是绕道
`cost_curve.json` 进去的。**消融臂在图 2 里根本没出现。**

**裁定**：即使共享账本填满，图 2 也不会消费它，除非改 `figures/`（又一块别的领地）。
所以「A10 绿 ⇒ 图 2 解锁」这条因果**不成立**，如实记录。

## 本工单实际交付什么

在 `proxy` 领地内、且确实有价值的部分：

1. **修好账本分叉**（必做，且是本工单的前置条件——见 `MANIFEST.json`
   的 `blocking_dependency`）。工单要把**三个**写者指向一份账本，
   而今天**两个**并发写者就会分叉链条。不先修，A10 只会让问题更严重。
2. **对账重新定键**到真正记录得到的量 + 每条腿的负样本（必须能变红）。
3. **把 turns 缺口、score 口径、臂侧越界、图 2 不读账本**四条写成 gap，不降验收线。

**不做的**：不编辑另外三块领地的源码；不伪造 turns 比对；
不把可交叉核验的 per-run 分数标成不可核验。
