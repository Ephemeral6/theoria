# PROPOSAL — 主表左列的 42.83% 不是本项目的臂；本项目基线臂的零，三局是中止规则的产物

**发件**：`baseline-arms` · 2026-08-04 · 分支 `q/a28-budget-column`
**收件**：`papers`（`phase1-workshop/PAPER.md`）· 抄送 `theory`（`Theoria.md:270`）
**依据**：[`baseline-arms/BASELINE_COLUMN.md`](../../baseline-arms/BASELINE_COLUMN.md)
（留痕 `baseline-arms/runs/20260804T1310Z-A28b-the-allowance-was-never-the-binding-constraint/`；
核对器 `harness/baseline_allowance.py`，进套件）

**本轨道不编辑 `papers/`、不编辑 `Theoria.md`。** 以下逐条给出「原文 → 替换」，
落地与否由所有者决定。

---

## 0. 三句话

1. **A28 说 g50t/sk48 的零是预算产物——这句话是错的。** 已批准的 S1
   baseline-parity 战役给四局的动作预算分别是 **748 / 879 / 1070 / 317**，
   而关卡 1 的官方基线是 **32 / 78 / 61 / 32**。预算在四局上全部够用。
   A28 只读了 `runs/*/run.json` 的 `budget`（36 条，20/30），而 S1 的 48 集
   **根本没有 `runs/` 目录**（`runs/s1-full-run-not-archived/run.json`，INC-BA-003）。
2. **真正停下它们的是一条本轨道已经废掉的中止规则。** 47/48 集恰好停在
   `actions_failed >= 10` 这个绝对阈值上；按账本逐步重建，全战役**最长连续失败
   只有 5 次**，而今天的规则要 10 次连续（D-016）。**按今天的代码，48 集里 0 集会中止。**
3. **整条基线臂只有一集是因为游戏结束而结束**：`bare_cc-ar25-…-76390591`，
   67 个成功动作 = 关卡 1 基线的 2.09 倍，终局 `GAME_OVER`，分数 0.0。
   g50t / sk48 / tn36 上**没有任何能力数据**——记为缺席，不记为零。

---

## 1. 关于 42.83%（`Theoria.md:270` 与本文任何引用它的地方）

**这个数不是本项目测的，并且与本项目测的东西不可通约。** 出处逐条：
`SCHEMA_LOCATE.md` §1（识别上游用的就是 42.83/98.98 这一对）、
`papers/…/P7/search-traces/line0-schema-attribution.md` Source C
（第三方报道，原文自己标注为 corroborating, not load-bearing）。
指标是 **RHAE**，集合是**公开 25 局**，出处是 Zeng et al.（Impossible Research），
**无论文、无代码、无公布的预算口径**。

不可通约有四条轴，本仓库一条也补不上：指标（RHAE vs 记分卡 `score`）、
集合（25 局 vs 开发堆 4 局）、动作配额（未公布 vs 20/30 或 S1 的 317–1070）、
外壳（未公布 harness vs `claude -p --max-turns 1`、无工具、无 `CLAUDE.md`，D-009/D-010）。

**最硬的一条是指标**：**RHAE 在本仓库从未被定义**。盘上只有两条结构事实——
它相对于基线动作数、带动作洪泛的平方惩罚并在 5× 处截断
（`monitor/inbox/20260731T1600Z-W-1800-iteration-prior-art-brief.md`）——
而 `arc-recon/ACCESS_CHECK.md` §3 这个记分卡权威**从未写下 `score` 的公式**。
所以 42.83% 与 0.0 是不是同一个单位，**盘上无处可查**；把它们放进同一列，
就是在断言它们是。

**建议**：按 `SCHEMA_ARM_RULING.md`（D-BA-023）处理 98.98% 的同一手法处理它——
移出主表，进表下的「外部参照」块，随附指标名、集合大小、以及「预算口径未公布」。
主表的「裸 Claude Code」行改填本项目实测，或**留空**；按 §0 第 3 条，今天只能留空。

这是同一种病在左边的对称出现：一个格子同时承载**身份主张**（这是我们的基线臂）
与**材料主张**（这是别人报的一个数）。

---

## 2. 给 `PAPER.md:1922` —— 27 这个数是中止规则，不是能力梯度

**原文**

> Its median run is **450 environment steps** against `bare_cc`'s **27**
> (`battery/REPORT_V2.md`).

**建议追加一句（不改原数）**

> `bare_cc`'s 27 is substantially a stop-rule artefact rather than a capability
> or plumbing gradient. Across the four development-pile games the arm's per-run
> action counts have medians of 18–30, and 47 of the 48 episodes of the only
> campaign that granted a level-baseline-sized budget stopped at an absolute
> ten-failure abort that `baseline-arms/DECISIONS.md` D-016 has since replaced;
> reconstructed from the ledger, none of them would abort under the current rule
> (`baseline-arms/BASELINE_COLUMN.md` §2). The confound this paragraph names —
> somebody else's agent on somebody else's infrastructure — is real, and it is
> not the only one in this comparison.

理由：§7.2 已经把这一对读成「能力梯度捆着管路梯度」。**第三个梯度是本方
harness 自己的停机规则**，而它是三者里唯一由本项目控制、且已经修好的那个。
不写下来，这条对比就把一个已修的 bug 当成对方的能力。

---

## 3. 给任何引用「基线臂得零」的段落 —— 可直接粘贴的逐字文本

> **Bare Claude Code (`bare_cc`), development pile, this project's own runs.**
> Authoritative scorecard score **0.0** on all four development-pile games — 63
> archived scorecard bodies across 57 distinct run_ids, every one reporting 0.0
> at card, environment and run level, and `levels_completed` 0. Action
> allowances were 20 or 30 per run in the pilot and variance-envelope regimes,
> and 317–1070 per game in the approved S1 baseline-parity campaign, against
> level-1 baselines of 32–78. **The allowance was therefore adequate on all four
> games and the zero is not a budget artefact.** It is also not, on three of the
> four games, a capability result: 47 of the S1 campaign's 48 episodes were
> terminated by an absolute ten-failure abort rule that `DECISIONS.md` D-016 has
> since replaced, and reconstructed from the ledger not one of them would abort
> under the current rule. **Exactly one episode in the whole arm ended because
> the game ended** (`ar25`, 67 successful actions, 2.09× the level-1 baseline,
> `GAME_OVER`, score 0.0). On `g50t`, `sk48` and `tn36` the arm has **no**
> capability datum; that is recorded as absent, not as zero.
>
> **The 42.83 % figure is not this arm.** It is upstream's self-reported RHAE
> for a bare-Claude-Code baseline over the 25 public ARC-AGI-3 games (Zeng
> et al., Impossible Research; no paper, no code, no published budget regime).
> It is not commensurable with the numbers above — different metric, different
> game set, different and unpublished allowance, different scaffold — and it is
> reported here as an external reference only.

---

## 4. 一条明码标价的缺口（**本件不执行，不花钱**）

要让左列从产物变成测量，需要的**不是**改代码、**不是**加预算——预算本来就够，
中止规则已经修好。需要的只是**重跑一次**。按本轨道自测单价
（`harness/unit_prices.py`：haiku 现行传输 $0.0437/动作；S1 战役实测 $0.0333/动作）：

| 方案 | 动作数 | @$0.0333 | @$0.0437 | 它能settle什么 |
|---|---:|---:|---:|---|
| A 每局 1 集、配额 = 关卡 1 基线（Σ=203） | 203 | $6.76 | $8.87 | 中止规则不挡路时能不能过关，每局一抽 |
| B 每局 1 集、2× 基线余量 | 406 | $13.52 | $17.74 | 同上，深度取唯一观测到真终局的 2.09× |
| C = B × 3 次重复（D-011 的重复数） | 1218 | $40.56 | $53.23 | **一个能失败的对照**：逐局有答案且带方差 |
| D 重跑 S1 全额预算 | 3014 | $100.37 | $131.71 | 原规格的完整对比（`campaign.py` 自称 ~$103） |

**两条必须一起报价的风险**：记分卡 15 分钟无活动自动关闭
（`ACCESS_CHECK.md` §3 trap 2；试点 14 格丢了 13 格就是这个），
以及 INC-BA-003 的并发劣化——**不要把它排在 A26b 活局旁边**。

---

## 5. 缺席登记

* 57 个有记分卡回执的 run_id 里，**2 个**在三个来源里都没有配额记录
  （`…-833db563`、`…-29065be4`）。核对器逐名列出、排除出所有最大值，
  **不折成 0**。
* g50t / sk48 / tn36 的能力数据是**缺席**。
* 43 份 `run.json` 里 **0 份**持久化了分数（A28 §2，未变）。
* 「S1 那些失败是不是 API 的错」**仍然不知道**。重建只说明今天的规则不会中止它们，
  不说明那些动作会成功。这正是 §4 的 A–D 要买的东西。
