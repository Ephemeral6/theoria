# M3 — Schema 官方发布物定位结果

**结论：官方 harness 代码从未发布，因此「跑一遍 Schema」在任何合规意义上都不可能。
轨迹 artifacts 有发布，且覆盖全部 25 局——但那是别人的账本，不是我们的复现。**

工单的前提纪律：复现必须基于官方公开发布的代码/artifacts 跑，不允许凭训练记忆
重新实现一个类似的东西冒充复现。本节记录定位结果与由此产生的缺口。

---

## 1. 身份确认

`Theoria.md` 全文**没有任何引用**——无 arXiv id、无 URL、无参考文献节
（已 grep `feng|arxiv|github|引用|参考文献|References`，0 命中）。定位只能靠公网检索。

找到的系统在多个独立维度上都对得上，不是同名巧合：

* **98.98** 这个数字逐字出现，且与 `Theoria.md` 主表的另一个数字 **42.83%**
  （裸 Claude Code 基线）成对出现，增量 +56.15pp——与 `Theoria.md:393` 的
  「+56pp 全部来自过程而非权重」一致。
* `world_model.py` 确认存在（发布的 artifacts 里有 55 个 `world_model*.py`）。
* 重放检验确认：对完整转移历史 `run_backtest`，模型内 `run_bfs` 搜索，
  `commit_actions` 是通往环境的唯一通道——与 `Theoria.md:218` 的「外环与 Schema
  完全同壳」及约束 3「行动唯一通道」逐条对上。
* ARC-AGI-3、25 局公开集、RHAE 指标。

### 1.1 署名更正

工单与 `Theoria.md` 都写作 **Feng et al.**，但规范署名是 **Zeng et al.**：
Guanning Zeng, Jiani Wang, Wenjie Ma, Shaofeng Yin, Chenyang Wang, Shichen Liu,
Angjoo Kanazawa, Wode Ni, Xiuyu Li, Andrea Zanette, Haiwen Feng
（Impossible Research / UC Berkeley / CMU）。Haiwen Feng 是**末位作者**。

`Theoria.md` 不属本轨道，不代改；此处记录，供 theory 侧订正。

---

## 2. 四问四答

### 2.1 官方论文：**不存在**

没有 arXiv id、没有会议论文、没有 PDF。唯一的发表物是一个网页，
其自带的 BibTeX 是 `@misc`、`howpublished = {Impossible Research}`、`year 2026`、
url 指向项目主页。

**给 theory 侧的一条硬约束：不要在 `Theoria.md` 里编一个 arXiv id，没有可引的。**
正确的引法是 `@misc` + 项目主页 URL。

### 2.2 官方代码仓库：**不存在**

直接查 GitHub org API，`schema-harness` 组织下只有**一个**仓库，
即项目主页本身（`schema-harness.github.io`）。**没有 harness 代码。**
HF 组织下 0 个 model、0 个 space。项目主页**没有任何代码发布承诺**，
连 "coming soon" 都没有。

这也是该工作在公开讨论里被批评的主要点：拿不到 harness，就无法判断有多少人类
智能被烘焙进了脚手架里——ARC Prize 方面公开表达过同样的意思。

### 2.3 释出的 artifacts：**有，而且是逐局的、覆盖全部 25 局**

HF 数据集 `schema-harness/arc-agi-3-schema-traces`，公开、未 gated、
约 2356 次下载、无声明许可证。

结构（仅元数据层面，**本轨道未下载、未读取内容**）：1058 个文件，
两套采集各 25 个轨迹目录，**每局一个，game_id 精确对应 `piles.json` 的 25 局**。
每个目录含 `run.json` / `events.jsonl` / `sessions/*.jsonl` / `notes.md` /
`snapshots/cleared_level_*.py` / `world_model_v*.py`。顶层有 `score_trajectories.py`
与逐套的 `evaluation_results.csv` / `baseline_actions.csv`。

**这对本项目是最高危的一类物件**，见 `INCIDENTS.md` INC-BA-001。
按 `piles.json` rule 2，读封存局的这些文件比玩那一局更糟：它直接给出成品答案
（该局的世界模型源码与作者笔记）。

### 2.4 能否离线跑：**harness 不能（无代码）；打分器能**

| 组件 | 能否跑 | 需要什么 |
|---|---|---|
| Schema harness 本体 | **不能** | 代码未发布 |
| 打分器 `score_trajectories.py` | **能，且纯离线** | Python 3.10+，仅标准库，无需 ARC key |
| 重跑原始实验 | **不能** | 需重新实现 harness + ARC key + 特定模型配对与回退规则 |

---

## 3. 缺口登记：工作二（Schema 复现）**合规地留空**

按工单停止条件 3——「Schema 官方 artifacts 确实找不到——记录缺口，继续做裸 CC
那部分，不要用替代实现冒充复现」。这里的情况比停止条件设想的更明确：

**artifacts 找得到，代码找不到。而复现需要的是代码。**

因此：

* ❌ **不会**凭训练记忆重新实现一个 Schema-like agent 再把它的分数填进
  `Theoria.md:271` 的 `⟨复现值⟩`。那个数字将无可比性，比空着更糟。
* ❌ **不会**下载封存局的上游轨迹。
* ✅ `⟨复现值⟩` 这一格**保持空白**，并在主表脚注写明「官方 harness 未发布，
  复现不可能；上游 98.98% 为唯一可引数字」。
* ✅ 记录一条唯一合规的替代路径，供闸门之后决策（见 §4）。

---

## 4. 闸门之后可选的三条路（本轮均未执行，仅登记）

按代价与风险排序。**三条都需要人工批准，本轨道不自行推进。**

### 路 A：只取开发堆 4 局的上游轨迹（**推荐**）

`Theoria.md:311` 已经明确许可：「Schema（复现桶 + **上游 artifacts 中属于开发堆
的局**）」。HF 数据集按 game_id 分目录，可以精确只下载
`ar25-0c556536` / `g50t-5849a774` / `sk48-d8078629` / `tn36-ef4dde99` 四局的目录。

* 得到：这 4 局的 Schema 侧真实轨迹、动作数、world_model 成品，可直接进 Phase 2
  的指标电池，作为「CC vs Schema 已知能力梯度」的对照臂（`Theoria.md:325` 要求）。
* 成本：≈0 美元、≈0 动作配额。
* 风险：**必须按目录名精确下载，不能整包拉取。** 整包 = 25 局全污染。
  需要一个只允许 4 个 game_id 前缀的下载守卫，写法与 `arc_client.assert_playable()`
  同构。
* 注意：数据集**未声明许可证**，Phase 4 释出前需确认可再分发性。

### 路 B：用另一个**有代码**的执行式世界模型系统作「第二波」对照

检索中另找到一个同架构、有正式论文、有公开 MIT 代码的系统
（arXiv:2605.05138，SingularityNET，58.12% 平均 RHAE）。它**不是 Schema**，
不能填 Schema 那一格，但可以诚实地作为「第二波·可运行版」另立一行。

* 得到：一个真正能跑、能改、能审计的执行式世界模型对照臂。
* 风险：其仓库同样含 run artifacts，同样有封存堆风险，需同样的下载守卫。

### 路 C：等 Schema 放代码

项目主页最后一次提交在 2026-07-18，无发布承诺。**不建议把任何进度依赖在这上面。**

---

## 5. M3 判定

| 里程碑要求 | 结果 |
|---|---|
| 找到并可跑 | ❌ harness 代码从未发布 |
| 或如实记录找不到 | ✅ 本文件 + `STATUS.md` 缺口条目 |
| 不用替代实现冒充 | ✅ `⟨复现值⟩` 保持空白 |

**M3 达成**（判定为「如实记录找不到」这一支）。
