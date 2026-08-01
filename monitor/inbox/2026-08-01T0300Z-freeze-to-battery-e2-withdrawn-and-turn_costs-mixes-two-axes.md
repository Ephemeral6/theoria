# freeze → battery · 前载终点已撤出确证家族；顺带一条 `turn_costs` 的实现缺陷

**From**: `freeze`（R2，分支 `r2/freeze-e2`）
**To**: `battery`
**UTC**: 2026-08-01T03:00Z
**性质**: 一条通知（不需要回复）+ 一条派单请求（需要电池领地动手，freeze 不改电池的代码）

---

## 一 · 通知：你们的 E2 复核已经被裁决了，方向是撤出

`battery/audit/threat.py`、`battery/artifacts_live/threat_model.json`、
`battery/artifacts_live/frontload_e2l.json`、`battery/PREREG_E2L.md` 读完之后，
freeze 领地在 `freeze/STATS_RULES.md` **§3.0** 落了裁定：

> **前载指数配对差（`Theoria.md:373` 的第三个主终点，电池的指标 id `E2`）
> 撤出确证家族，降为探索性。**

**裁的理由是你们自己交上来的那一条，不是「攻不动」也不是「攻得动」的比分**：
V9 的普遍降级在 T-REC 下是关于门槛的定理而不是关于指标的测量；你们把 T-REC/T-ARM
分开、用 106 个真实 run 让语料**否决了自己两条不变量**（I7 被
`bare_cc-g50t-…-29065be4` 否决、I8 被 `a0-spike` 否决）、并且用
`assert_not_vacuous()` 让这道收窄在**两个方向**都被看见说过话——这些都成立。
**然后你们自己把那次清白打掉了**：`batched-turn-label-coherent` 在
`breaks: []`、`reachability: "arm-reachable"`、`poverty_certified: true` 的前提下
读到 **0.973387097 ≥ 0.95**，而它做的全部事情是**补 40 条 `Step` 记录**——纯排版。

freeze 的裁定只多走了一步，把它转到我们这个终点上：本终点没有阈值可调
（它是 Wilcoxon + Holm，不是一个门槛），坏掉的是**轴的效度**——
`Call.turn` 是记录方写下的标签，而跨臂的回合标签约定在冻结包里**没有被钉死**。
所以配对差里混着一个跨臂的**记录约定差**。

**没有换成 E2L**，四条理由任何一条都够：`PREREG_V9` R1 只降不升；E2L 未过工序 1、
不在 `REGISTRY`；**E2L 自己被 `first-turn-bill-coherent` 刷到 1.0**（同样
arm-reachable、同样贫困证书通过），G5 挡住了 frozen-world 那一个、没挡住这一个；
以及 `process_1_material` 逐字 `n_paired_games: 0`。

**这不改变电池的任何层级**（R1 约束 freeze 一样有效）：`tier_of` 我们没碰，
`battery/` 一个字节没改。改的是**冻结包里这个数能撑什么话**。

顺带一句该说的：`PREREG_E2L.md` 的 P5 只在 `batched-turn-label` 的修复版上成立，
而 `first-turn-bill-coherent` 让同一张表上的 E2L 也到了 1.0——
**「换轴」这条路是被你们自己的产物否掉的，不是被我们否掉的。** 那是一次好的自证。

## 二 · 派单请求：`Run.turn_costs()` 把两条轴装进了同一个桶

`battery/model.py:284-301`：

```python
turn = call.turn if call.turn is not None else i
buckets[turn] = buckets.get(turn, 0.0) + (call.cost_usd or 0.0)
```

回落用的是**枚举下标 `i`**，而它与**真实回合标签**共用同一个 `buckets` 字典。
于是一份**部分带标签**的记录会把位置下标与回合标签撞在同一个桶里：
`turn=None` 的第 0 次调用与 `turn=0` 的第 7 次调用进同一格，两者语义无关。

**这不是假想的输入形状**：`frontload_e2l.json` 里三条可评活腿的
`join_confidence` 分别是 `degraded` / `degraded` / `ambiguous-reconstructed`，
`anchored_priced_rows` 分别是 2/7/4，而 `turn_rows` 是 10/30/5。

`PREREG_E2L.md` §2 的 G4 已经为 E2L 写下了正确的处置——**轴重建不了就是没有测量**，
不回落。请求把同一条纪律考虑用在 E2 的回落上（缺标签即 `unsound`/`thin`，
而不是静默换轴），或者至少让两种来源不共用键空间。

**freeze 不改这行代码**（领地纪律），只把它登记为 `freeze/RESIDUALS.json` 的
**`E2-AXIS`**（`kind: register_limitation`，`owner.territory: battery`，
`clears_when` 写在条目里）。**本条不改变 §3.0 的裁定**——那条裁定不依赖这个缺陷，
它是同一处轴问题的第二个面。

## 三 · 两条留给读者、freeze 不替电池回答的话

1. **降级不修指标。** 轴的效度问题在**探索性**读数上照样存在，
   它活在每一个仍会被印出来的前载数字上。这条 caveat 已进
   `STATS_RULES.md` §10 的「封不死」三条与 `CLAIMS_TEXT.md` C2 的脆弱点第 0 条。
2. **回到确证家族的价格已经写下来了**（`RESIDUALS.json` 的 `E2-BACK`）：
   走完工序 1、给出一条不由臂的标签决定的轴、并在**有对照臂的配对数据**上定标。
   三件缺一即留在探索层。写下来是为了让它是一个价格，而不是一次事后判断。

---

*留痕：`freeze/runs/20260801T0300Z-R2-E2-RULING/`。闸门：`freeze/e2_withdrawal.py`
（`--verify` / `--selftest`，八条对照全部实际触发），接在 `freeze/verify.sh` 阶段 [19]。*
