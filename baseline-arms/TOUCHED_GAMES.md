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

试点开跑后，逐局在此追加。格式：

```
| <game_id> | <arm> | <model> | <run_id> | <动作数> | <是否读帧> | <污染等级> |
```

| game_id | arm | model | run_id | 动作数 | 读帧 | 等级 |
|---|---|---|---|---|---|---|
| _(M4 试点结果填入)_ | | | | | | |

---

## 给未来切堆决策的一句话

切分已在本轮之前落刀，本轮**没有**造成「跑过的局只能划进开发堆」的新约束——
本轮跑过的每一局本来就已经在开发堆里。封存堆保持 21 局全部 `never_audited`。
