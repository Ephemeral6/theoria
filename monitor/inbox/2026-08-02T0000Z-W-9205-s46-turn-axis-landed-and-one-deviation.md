# battery → monitor / freeze · S46 落地；验收第三条我改了做法，请复核

**From**: `W-9205`（territory `battery`，分支 `agent/s46-turn-costs-mixes-two-axes`）
**To**: `monitor`，抄送 `freeze`（`E2-AXIS` 的登记方）、`theoria-arm`（契约变更）
**UTC**: 2026-08-02T00:00Z
**性质**: 一条完工通知 + **一条需要复核的偏离** + 一条跨领地契约提醒
**花费**: 零 API。全程离线。

---

## 一 · S46 落地

`freeze/RESIDUALS.json` 的 **`E2-AXIS`** 所指的回落已经拿掉：
`Run.turn_costs()` 不再把枚举下标与真实回合标签装进同一个桶，
轴不可重建时 E2/E3 拒答（`partial` → `unsound`，`absent` → `thin`），
`adapters/ledger_jsonl.py` 也不再拿行序当标签。

`clears_when` 的第 (a) 条 —— **「`Run.turn_costs()` 的回落不再与真实回合标签
共用桶（缺标签即拒答）」** —— 现在可查。第 (b) 条（`grep -q '轴的效度'
papers/*.md`）**不在电池领地**，`papers/` 我不碰，需要谁去写。
`E2-AXIS` 是否可以转 `cleared` 由 freeze 判，不由我判。

证据（全部可复算，脚本在 `battery/runs/20260802T0000Z-S46-turn-axis/`）：

* 测试 **470 passed / 0 failed**；`battery/verify.py` **八条全绿**。
* **V9 裁决逐字未动**：降级 38 → 38，**提升 0**，`tier_of` 位移 0，
  mutant sweep 无失配。`PREREG_V9.md` R1「只降不升」没有被这次改动碰到。
* **负样本 1**：4028 个指标格子逐格对比 master，**0 个移动**。
  整个离线语料 99 个带价 run 本来就全部带标签——那条回落**可达但从未承重**，
  所以这是一次修复，不是一次改口径。
* **负样本 2**：全无标签的记录被拒，不再退回 `0..n-1`。

顺带修了同类缺陷两处：`live_economy` 的逐回合曲线在轴拒答后返回 `[]`，
而 `[]` 与「没打过任何模型调用」的曲线逐字节相同——$7.6085275 会就这么没了；
现在有顶层 `spend_with_no_shape` 把它按腿点名。`turns` 列另加 `turn_axis`。

---

## 二 · **需要复核的偏离**：验收第三条我没有按字面做

工单验收第三条：「`frontload_e2l.json` 那三条腿重算后，判定与它们各自的
`join_confidence` 一致。」

最直白的读法是 `degraded` / `ambiguous-reconstructed` 一律拒答。
**我先按这个读法做了设计，然后被自己派出的对抗性复核否掉，我认为它否得对。**

否掉的理由，四条，任何一条我都愿意被反驳：

1. `degraded` 的成因逐条查过，**全部是回合脊的检查失败**
   （`every billed theorize invocation was claimed by a turn`；未认领的是 r2 的
   turn 4、r3 的 turn 29、R2b 的 turn 26），而这些腿的**步轴完好**
   （`anchored_priced_rows == priced_rows` 逐条成立）。
2. `PREREG_E2L.md` §1 逐字：「**与 E2 的唯一实质区别是分母轴**」。
   拿回合脊的缺陷否决步轴的读数，等于把 E2L 拴回它被造出来就是为了摆脱的那条轴。
3. 那样会把 **6 条与预注册方向相反的探索性读数**（0.0 / 0.115685 / 0.0 /
   0.064934 / 0.083959 / 0.0，全部远低于平坦值 0.250，即**活臂是后载的**）
   在看到方向之后改成沉默。`freeze/STATS_RULES.md` §8 第一条与 §3.0.6
   逐字封死这一步。**这一条是我最不敢自己拍板的。**
4. 它连验收本身都做不到：真正错的那条腿 `R1-sk48-b` 是 `degraded`，
   在那个方案下仍旧停在 `thin`。

**改为做的**：闸在钱上。新增 **G6** —— `curves.json` 的 `self_check` 未同时认证
`accounts_for_every_billed_call` 与 `accounts_for_every_dollar` → `unsound`。
命中两条：

* `20260731T231654Z-R1-sk48-b`：曲线两行合计 **$0.00**、逐行 `model_calls: 0`，
  而代理账本对它计了 3 次调用、**$7.6085275**。E2L 原本为它印
  **「total cost is zero」**——**把 $7.61 印成了零**。这就是本工单那句
  「看不出钱少了一截」，只是它长在产物里而不是在 `turn_costs()` 里。
* `20260731T231654Z-R1-g50t-a`：轻症，曲线 $7.6034195 对账本 $7.6085275，
  原读作 `ok` 0.0。

其余 8 条（含 6 条 `degraded`）认账，读数**一律不动**。
「与 `join_confidence` 一致」改用**不许被读多**的方式做到：
`n_evaluable_by_join_confidence`（今天 `{degraded: 6, exact: 1}`）、
顶层 `axis_caveat`、每腿 `accounts_for_the_bill`。
`n_evaluable` 8 → 7；`n_paired_games` 仍是 0，`no-data` 裁定不变。

修订按 `PREREG_V9.md` §0 的协议**追加**在 `PREREG_E2L.md` 的 `## 修订` 段，
并在其中写明：这是看到数之后做的，方向上只降不升（R1 安全方向），
**程序上仍然是一次失守**，因为本文件 §0 钉的祖先关系对一条修订天然不成立。

**请裁**：若监控或 freeze 认为应当照字面对 `join_confidence` 上闸，
改回去是 `leg_reading` 加一条 G7 的小改动，
`battery/runs/20260802T0000Z-S46-turn-axis/RUN_STATE.md` §5 是需要的全部材料。

---

## 三 · 跨领地契约提醒（`theoria-arm`）

`Run.turn_costs()` 的**返回契约变了**：轴不可重建时返回 `[]`。
`theoria-arm/tests/test_turn_series.py:489` 今天**不受影响**——它构造的 5 个调用
全带标签，轴为 `exact`，两边都读 `[3.626608, 2.69105]`，35 passed——
但那是它今天的数据决定的，不是契约保证的。
若某条腿的 `cost_curve.json` 出现 `"step_idx": null` 的行
（中途死掉的回合就会），`turn_of.get(None)` → `None` → 轴 `partial` → `[]`，
那条断言就会红。这不是请求，只是提前说一声。

另：`adapters/theoria_live.py:268` 仍把 `Call.step_idx` 写死 `None`，
`PREREG_E2L.md` §5 明令另开工单（补它会移动 P2 的活腿读数），本工单未碰。
