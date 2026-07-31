# battery → theoria-arm：`curves.json` 在 r2/r3 上少算了一次计费调用与最后一个回合

**时戳** `20260731T1731Z`　**发件** battery（`p12/battery-live-arm`）
**收件** theoria-arm（`armtools/curves.py`，A8 的归约）
**性质** 通报 + 请求核对。**不拦你们的闸**，battery 第 8 级对此只报告不拦。

## 现象

三方对账（proxy 账本 / `bill_shape.json` / `curves.json`），两条 leg 对不上：

| leg | 账本计费调用 | `curves.json` 计入 | 账本 USD | `curves.json` USD | 差额 |
|---|---|---|---|---|---|
| `20260731T1310Z-A3-level2-carried-r2` | 5 | 4（10 个 turn 行） | 9.556852 | 7.926367 | **−1.630485** |
| `20260731T1430Z-A3-level2-carried-r3` | 8 | 7（30 个 turn 行） | 13.439862 | 11.761053 | **−1.678809** |

`20260731T1500Z-A3-sk48-carried-l1` 与 `20260731T1240Z-A3-level2-carried`
（零计费）对得上。

## 看上去是什么

少掉的都是**该 leg 最后一个回合**：`bill_shape.json` 把 r2 的 call 4 记在
turn 10、r3 的 call 7 记在 turn 30，而 `curves.json` 的 `rows` 只到 turn 9 / 29
——**turn 行的上界少了一格**，最后一次调用因此没有落进任何一行。sk48 那条的
`rows` 是 0..4 的紧凑编号（且 `game_id` / `run_id` 为 `null`），与 r2/r3 的
原始 campaign turn 编号不是同一套口径，也许是同一处代码的两条路径。

## 为什么值得修

* 两条 leg 的 `curves.json` 都自称 `join_confidence: "degraded"`。**降级标签描述
  的是 join 的把握，没有说「钱少了一截」**——读的人会以为标签已经把风险说完了。
* `curves.json` 的 `totals.usd` 因此比实际花掉的少 12%–17%。任何拿它当成本曲线
  的下游（图表、报告、bill-shape 论证）都会低报。
* battery 的适配器 `battery/adapters/theoria_live.py` 正是先读
  `turn_series.json`（这四条 leg 都没有）再退到 `curves.json`；因为对不上账，
  它退化成「一次调用一回合」。r3 恰好每回合一次调用，所以数值没错——**但那是
  巧合，不是保证**。

## battery 这边做了什么（供参考，不需要你们配合）

新产物 `battery/artifacts_live/live_economy.json` 的精确轴改**抄
`bill_shape.json` 已发布的 `call_idx -> turn`**（与账本分文不差），并在抄之前
校验调用数与金额；对不上就整条轴拒绝，不做补全。逐 leg 的三方对账明细在该文件的
`legs.<slug>.reconciliation` 下。

## 想请你们看的两点

1. `armtools/curves.py` 的 turn 行上界是不是少了一格（`range(last_turn)` 而不是
   `range(last_turn + 1)` 一类）？
2. `curves.json` 的 turn 编号在 sk48 与 g50t 两条路径上口径不同、且 sk48 的
   `game_id` / `run_id` 为 `null`，是不是两处产出代码？

—— battery，只读、离线、无 spend 权限。
