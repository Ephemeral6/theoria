# 本轮触碰的 game_id 登记

切分**已经存在**（`arc-recon/data/piles.json`，sha256 `3feca53e…41bbc19a`），
所以本文件不是「未来切堆的依据」，而是**污染登记的续账**：记录 baseline-arms
轨道在开发堆上又推进到了什么程度，供 Phase 2/3 判断哪些局的哪些关卡还干净。

**封存堆 21 局：本轮触碰数 = 0。** 由 `harness/arc_client.py` 的
`assert_playable()` 在打开 socket 之前强制，非人工纪律。

污染等级沿用 `arc-recon/data/piles.json` 的三级：
`never_audited` < `scores_only` < `trajectories_reviewed`。

---

## 开发堆

| game_id | 本轮触碰 | 本轮后污染等级 | 说明 |
|---|---|---|---|
| `sk48-d8078629` | ✅ 大量 | `scores_only` | 见下 §sk48 |
| `g50t-5849a774` | ✅ 少量 | `scores_only` | 见下 §g50t |
| `ar25-0c556536` | ❌ RESET 被拒 | `never_audited` | 4 次 RESET 全部 400，未返回任何帧 |
| `tn36-ef4dde99` | ❌ RESET 被拒 | `never_audited` | 4 次 RESET 全部 400，未返回任何帧 |

### sk48-d8078629 — 本轮污染增量最大的一局

* 阶段：M1 审计的 `INC-002` 独立复核（`probe_api.py` / `probe_action_variants.py`
  / 重试策略确证）。
* RESET 成功若干次；成功执行的 ACTION 约 19 次（`ACTION1..4` 与 `ACTION7`）。
* 全部动作是**盲打**：按固定轮转序列 `1,2,3,4` 发出，
  **没有任何模型或人读过返回的帧像素**。帧在 `probe_log.jsonl` 里只以
  `"<1 frame(s)>"` 的形状摘要存在，像素未落盘、未渲染。
* 观测到的语义信息仅限：`available_actions=[1,2,3,4,6,7]`、
  `state=NOT_FINISHED`、`levels_completed` / `win_levels` 字段存在、
  `ACTION6` 传 `{"x","y"}` 返回 500。**均为 API 形状，不是关卡机制。**
* 因此等级定为 `scores_only` 而非 `trajectories_reviewed`：
  轨迹被产生了，但没有被**审阅**。
* 从未通关，`state` 始终 `NOT_FINISHED`，关卡 1 被推进了未知步数。

### g50t-5849a774 — 增量很小

* 阶段：`probe_api.py`、`probe_action_variants.py`（后者 10 次 RESET 全部 400，
  未开窗）。
* RESET 成功 1 次，返回首帧；紧随的 1 次 ACTION 失败。
* 帧同样只存了形状摘要，像素未读。
* arc-recon 已在 2026-07-27 将其登记为 `scores_only`（一次 RESET，首帧）。
  **本轮未提升其等级。**

---

## 试点阶段（M4）新增

试点跑了 4 局 × 3 模型 = 12 格，另加 sonnet 的 2 次重跑，共 14 格。
**四局全部成功开局**——包括 `arc-recon` 记为「RESET 全部 400」的 `ar25` 与 `tn36`。
这再次印证 `AUDIT.md` §6 的修正诊断：可用性是瞬时波动，不是按局固定的权限边界。

| game_id | arm | model | 成功动作 | 失败动作 | 结局 | 通关 |
|---|---|---|---|---|---|---|
| `ar25-0c556536` | bare_cc | haiku-4.5 | 15 | 5 | budget_exhausted | 0 |
| `ar25-0c556536` | bare_cc | sonnet-5 | 0 | 0 | model_error | 0 |
| `ar25-0c556536` | bare_cc | opus-5 | 7 | 10 | api_unusable | 0 |
| `g50t-5849a774` | bare_cc | haiku-4.5 | 14 | 6 | budget_exhausted | 0 |
| `g50t-5849a774` | bare_cc | sonnet-5 | 13 | 7 | budget_exhausted | 0 |
| `g50t-5849a774` | bare_cc | opus-5 | 14 | 6 | budget_exhausted | 0 |
| `sk48-d8078629` | bare_cc | haiku-4.5 | 15 | 5 | budget_exhausted | 0 |
| `sk48-d8078629` | bare_cc | sonnet-5 | 2 | 4 | model_error | 0 |
| `sk48-d8078629` | bare_cc | opus-5 | 14 | 6 | budget_exhausted | 0 |
| `tn36-ef4dde99` | bare_cc | haiku-4.5 | 13 | 7 | budget_exhausted | 0 |
| `tn36-ef4dde99` | bare_cc | sonnet-5 | 0 | 2 | model_error | 0 |
| `tn36-ef4dde99` | bare_cc | opus-5 | 0 | 10 | api_unusable | 0 |

**试点合计：109 个成功动作，全部落在开发堆 4 局的第 1 关，`levels_completed`
全程为 0——没有任何一局被通关，甚至没过第一关。**

### 试点后的污染等级

| game_id | 等级 | 理由 |
|---|---|---|
| `ar25-0c556536` | `trajectories_reviewed` | 模型逐帧读了像素并据此决策 |
| `g50t-5849a774` | `trajectories_reviewed` | 同上 |
| `sk48-d8078629` | `trajectories_reviewed` | 同上 |
| `tn36-ef4dde99` | `trajectories_reviewed` | 同上 |

四局全部升到最高级。与 M1 探测阶段不同——那时帧只是过了一遍网线、没人读；
试点里模型**真的读了帧并据此选动作**，轨迹也完整落进 `ledger.jsonl`。
这是开发堆的正当用途，不是事故。

登记归 `arc-recon` 的 `contamination_log.jsonl` 更新（本轨道不代改），
已在 `PARTNER_SYNC.md` 通报。

---

## 方差包络战役（M5，P-7）新增

`ar25-0c556536` × `claude-haiku-4-5-20251001` × 3 次重复，每次 30 动作预算。
闸门在本局跑完后判红（G4），**`g50t` / `sk48` / `tn36` 本轮未开跑**。

| game_id | arm | model | 重复 | 成功动作 | 失败动作 | 结局 | 通关 |
|---|---|---|---|---|---|---|---|
| `ar25-0c556536` | bare_cc | haiku-4.5 | 1 | 11 | 10 | api_unusable | 0 |
| `ar25-0c556536` | bare_cc | haiku-4.5 | 2 | 14 | 10 | api_unusable | 0 |
| `ar25-0c556536` | bare_cc | haiku-4.5 | 3 | 19 | 10 | api_unusable | 0 |

**本轮新增成功动作 44 个，全部落在 `ar25` 的第 1 关，`levels_completed` 全程为 0。**

### 污染等级：**无变化**

| game_id | 本轮后等级 | 理由 |
|---|---|---|
| `ar25-0c556536` | `trajectories_reviewed` | 试点已是顶格，本轮不再升 |
| `g50t-5849a774` | `trajectories_reviewed` | 本轮未触碰 |
| `sk48-d8078629` | `trajectories_reviewed` | 本轮未触碰 |
| `tn36-ef4dde99` | `trajectories_reviewed` | 本轮未触碰 |

### 路 A 材料（M6）：新增一种**非 API** 的开发堆触碰

本轮从上游拉取了开发堆 4 局的 Schema 轨迹（165 文件 / 87.7 MB，
见 [`SCHEMA_PATH_A.md`](SCHEMA_PATH_A.md)）。**但没有任何模型读过其中任何内容**——
下载器不解码、不打印、不总结，执行下载的子代理被明令不读，
主上下文只收到清单与哈希。

因此这批材料**当前**未提升任何一局的污染等级（四局本来也已顶格）。
真正要记的是给未来的一句话：**这些文件里有那 4 局的成品 world_model 与作者笔记。**
谁第一个打开它们，谁就在读该局的「答案」——对开发堆这是正当用途，
但那一刻应当在此续一笔，写明读了哪几局的哪些文件。

---

## 方差包络续跑（P-12）新增：只跑了 tn36 一局

闸门在本局跑完后第二次判红（G4），**`sk48` / `g50t` 未开跑**，
见 [`BUDGET_REPORT.md`](BUDGET_REPORT.md) §15（合并时由 §12 顺延，
与主线同日稍晚的 A7 §12 撞号）。

| game_id | arm | model | 重复 | 成功动作 | 失败动作 | 结局 | 通关 |
|---|---|---|---|---|---|---|---|
| `tn36-ef4dde99` | bare_cc | haiku-4.5 | 1 | 17 | 10 | api_unusable | 0 |
| `tn36-ef4dde99` | bare_cc | haiku-4.5 | 2 | 10 | 10 | api_unusable | 0 |
| `tn36-ef4dde99` | bare_cc | haiku-4.5 | 3 | **0** | 0 | **no_reset_window** | 0 |

**本轮新增成功动作 27 个，全部落在 `tn36` 的第 1 关。** 第 3 格一个动作都没发出
——30 次 RESET 全部被拒，模型**没有看到过任何一帧**，所以它对污染的贡献是零。

### 污染等级：**无变化**（四局早在试点后就已顶格）

### 一条本轮实测、对未来选点有用的数字

`tn36` 的 RESET 在本轮的实测成功率是 **6/63 ≈ 9.5%**（56 次 400、1 次传输层错误）。
这不是污染登记，但它属于「这一局现在能不能玩」的事实，
下一个想碰 tn36 的会话应当先知道它。

---

## S1 全量战役（另一会话，本轮开工时仍在跑）——**登记，非本会话产出**

`harness/campaign.py` 的 S1 全量（haiku 单档，`BUDGET_REPORT.md` §3.4 批准）由
**另一个会话**驱动，于 `2026-07-28T01:20Z` 前后跑完，四局全部
`episode_limit_hit`（12 集上限），**没有一局通关**。

| game_id | 集数 | 成功动作 | 官方基线 | 最好关卡 | 成本 |
|---|---|---|---|---|---|
| `ar25-0c556536` | 12 | 413 | 748 | 0/8 | $11.56 |
| `g50t-5849a774` | 12 | 525 | 879 | 0/7 | $16.62 |
| `sk48-d8078629` | 12 | 287 | 1070 | 0/8 | $11.93 |
| `tn36-ef4dde99` | 12 | 228 | 317 | 0/7 | $8.28 |
| **合计** | 48 | **1453** | 3014 | **0/30** | **$48.39** |

**为什么写在这里**：这是本轨道迄今为止最大的一次开发堆推进——1453 个成功动作，
是 M4 试点（109）的 13 倍、P-7 包络（44）的 33 倍——而污染登记是**按轨道**记的，
不是按会话。产它的会话若不续这一笔，本文件就会漏掉本轨道绝大部分的实际触碰。
**本会话不代它写结论**，只登记可从 `out/campaign/campaign_*.json` 直接读出的事实。

### 污染等级：仍**无变化**

四局在 M4 试点后就已是顶格 `trajectories_reviewed`，没有更高一级可升。
但量级值得单说：试点是每局约 14 个动作的浅接触，这次是每局 228–525 个动作、
模型逐帧读过。**「顶格」这个标签从试点起就没变，它掩盖了两个数量级的差别。**
若 `arc-recon` 的三级制将来要细分，这是需要它的第一个实例。

一个对 Phase 2/3 有用的判断：**48 集、1453 个动作、0 通关。** 裸 CC 在官方基线
动作数的一半以内连第一关都没过，四局皆然。`BUDGET_REPORT.md` §3.2 把 S1 称作
「乐观下界」，这次实测把「乐观」二字坐实了——不是差一点，是一关都没有。

---

## 封存堆

**本轮对封存堆的 ARC API 调用：0 次。** 由 `harness/arc_client.py` 的
`assert_playable()` 在打开 socket 之前强制。

**本轮对封存堆的上游 artifacts 内容请求：0 次。** 由
`harness/fetch_schema_traces.py` 的正向白名单在发出内容请求之前强制：
885 个属于 21 局封存游戏的文件全部判 `deny_sealed`，一个字节都没请求。
落盘复核（主上下文独立执行）：**含封存 game_id 的路径 0 条**。

这是对 INC-BA-001 那条制度性后果的正面回应——那条写的是
「上游 Schema artifacts 是一个『读了就全污染』的物件，可行的安全用法只有一种：
按目录名精确挑出开发堆 4 局」。本轮就是那一种用法，且守卫是代码不是注意事项。

但**有一次非 API 途径的污染**：M3 检索 Schema 官方发布物时，子代理在判断出页面
不安全之前读到了 9 局封存游戏的机制描述（`ls20`、`ft09` 为实质泄露）。
详见 [`INCIDENTS.md`](INCIDENTS.md) INC-BA-001。**那不是本文件的范畴**
（本文件只记 API 触碰），但对封存堆的实际影响比任何 API 调用都大，故在此指路。

---

## 给未来切堆决策的一句话

切分已在本轮之前落刀，本轮**没有**造成「跑过的局只能划进开发堆」的新约束——
本轮跑过的每一局本来就已经在开发堆里。

真正需要记住的是反向的一条：**封存堆已不再是 21 局全部 `never_audited`。**
9 局因 INC-BA-001 被污染，考卷选点须避开它们。
