priority: 2
cell: S46
territory: battery
deps: none
spend: none

# S46-turn-costs-mixes-two-axes · 位置下标和回合标签进了同一个桶

freeze 于 2026-08-01T03:00Z 把这条派单请求送进
`monitor/inbox/2026-08-01T0300Z-freeze-to-battery-e2-withdrawn-and-turn_costs-
mixes-two-axes.md`，并登记为 `freeze/RESIDUALS.json` 的 **`E2-AXIS`**
（`kind: register_limitation`，`owner.territory: battery`）。freeze 不改电池的
代码，`battery/` 一个字节没动；到 2026-08-01 为止 `battery/model.py` 也没有
任何提交——**这条 ask 无人认领。**

`battery/model.py:284-301`：

```python
turn = call.turn if call.turn is not None else i
buckets[turn] = buckets.get(turn, 0.0) + (call.cost_usd or 0.0)
```

回落用的是**枚举下标 `i`**，而它与**真实回合标签**共用同一个 `buckets`。
于是一份**部分带标签**的记录里，`turn=None` 的第 0 次调用与 `turn=0` 的第 7 次
调用会落进同一格，两者语义无关。

**这不是假想的输入形状。** `battery/artifacts_live/frontload_e2l.json` 里三条
可评活腿的 `join_confidence` 是 `degraded` / `degraded` / `ambiguous-
reconstructed`，`anchored_priced_rows` 是 2 / 7 / 4，而 `turn_rows` 是
10 / 30 / 5——正好是「大部分行没有标签」的形状。

要的纪律，`PREREG_E2L.md` §2 的 G4 已经为 E2L 写下了：**轴重建不了就是没有
测量**，不回落。请把同一条用在 E2 的回落上（缺标签即 `unsound`/`thin`），
或者退一步，至少让两种来源不共用键空间。

顺带记住 freeze 的第一句提醒：**降级不修指标。** 前载指数已于 2026-08-01 撤出
确证家族（`STATS_RULES.md` §3.0），但轴的效度问题在**探索性**读数上照样存在，
活在每一个仍会被印出来的前载数字上。所以这件不是「反正降级了，无所谓」。

验收：一份部分带标签的记录被判 `unsound`/`thin`，`turn_costs` 不再静默换轴；
`frontload_e2l.json` 那三条腿重算后，判定与它们各自的 `join_confidence` 一致。

负样本，两条：一份**全部带标签**的记录必须照常通过并给出与今天相同的数
（否则这是一次静默的口径变更，不是一次修复）；一份**完全没有标签**的记录必须
被拒绝而不是退回成 0..n-1 的紧凑编号——那正是今天让人看不出钱少了一截的
那条路。缺席记为缺席。
