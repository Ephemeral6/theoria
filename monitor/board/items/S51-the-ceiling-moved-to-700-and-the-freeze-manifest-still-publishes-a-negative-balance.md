priority: 1
cell: S51
territory: freeze
deps: none
spend: none

# S51-the-ceiling-moved-to-700-and-the-freeze-manifest-still-publishes-a-negative-balance · 上限抬了，冻结清单还在按旧上限扣着第 12 项，而扣它的理由已经不成立了

2026-08-04，`c42f5ad4` 按 `proxy/spend_policy.json` 自己的 `raising_it` 条款把
池上限由 **$214.90 抬到 $700.00**、动作上限 24000 → 40000，登记于
`monitor/spec.py` 第 #15 条，并已追加 PARTNER_SYNC。冻结这一侧**一个字节都还
没动**。

## 监控欠的那句算术，先给出来

`freeze/BUDGET_TABLE.json` 的 `balance` 今天逐字：

```
ceiling_usd              214.9
programme_measured_usd   250.0687
programme_nominal_usd    254.0786
remaining_measured_usd   -35.1687
remaining_nominal_usd    -39.1786
action_ceiling           24000
actions_used              9490
actions_remaining        14510
```

同一个被减数，换上新上限：

| | 旧上限 $214.90 | 新上限 $700.00 |
|---|---:|---:|
| `remaining_measured_usd` | **−35.1687** | **+449.9313** |
| `remaining_nominal_usd` | −39.1786 | **+445.9214** |
| `actions_remaining` | 14510 | **30510** |

**所以对本件那道题的回答是：不，余额在新上限下不再是负的——但今天发表出去的
那个余额仍然是负的，因为表还没有按新上限重算过。** 这两句话必须同时说，
它们正是本件要修的那个差。

## 第 12 项因此不能再用「余额为负」扣着，但它仍然不能 ready

`freeze/MANIFEST.json` 的 `budget.consequence` 逐字：

> item(s) 12 may not read `ready` while `remaining_measured_usd` is negative
> — see `BUDGET_HOLD_ITEMS` in freeze/build_manifest.py.

这个 hold 的触发条件在新上限下**为假**。但第 12 项的 `status` 是 `blocked`，
而它自己记的理由**不是钱**，逐字：

> The three numbers `Theoria.md:377` actually asks to freeze — $/game hard cap,
> total games, stop-loss — are still written as ⟨…⟩. See PENDING_FIVE.md.

**两条阻塞，只解开了一条。** 本件要防的正是把它们混成一条：解开钱这条之后
第 12 项仍然 blocked，而如果重生成时只看 hold 标志、不看 `⟨…⟩`，第 12 项会
从 blocked 跳成 ready，凭的是一次跟它自己的阻塞理由毫不相干的预算调整。

## 抬上限**没有**做的事，重生成时必须一并保留

`spend_policy.json` 的 `raised_2026_08_02.what_it_does_not_do` 与登记 #15 都
写明：不退役钱闸、不放宽任何单 run 上限、**不追认钱闸从未见过的那 $136.79**
（`gate_blind_spot_usd`）。所以：

* `BUDGET_TABLE` 的 `gate_visible_usd` / `gate_blind_spot_usd` 两列不因本次
  调整而合并或消失——盲区仍是盲区，只是池子大了。
* `MANIFEST.json` 的 `verdict.statement` 里那句「a NEGATIVE balance」必须随
  重算改写，且改写后**必须继续引 #13 与 #15**：#13 记的是「越过 $214.90 意味着
  INC-BA-003 那条界限此后不再是界限」，这件事**不会**因为上限被抬到 $700 而
  变成没发生过。一个只写「余额为正」而不写「那条界限已被越过一次」的表，
  比现在这个诚实地报负数的表坏。

## 与 S50 的次序

S50 说 master 上 `freeze/verify.sh` 三项红，其中 [15] 是 BUDGET_TABLE 不再从
账本复算。本件与 S50 的第 2 条**必须一起做，且本件的口径优先**：先按 $700
重算，再让 [15b] 对新表复算，否则会先把表修到与旧上限自洽、再被本件推翻一次。
S50 已经写明排序要等 `origin/agent/m-1-money-single-truth` 落地——那条仍然成立，
本件排在它后面。

## 验收

`BUDGET_TABLE.{json,md}` 的 `ceiling_usd` 为 700.0、`action_ceiling` 为 40000，
`remaining_measured_usd` 为 **+449.9313**（由表自己的 `programme_measured_usd`
减出，逐位对）；`MANIFEST.json` 的 `budget.consequence` 记录 hold 已解除**及其
依据的登记条号**；第 12 项 `status` **仍为 `blocked`**，理由字段只剩 `⟨…⟩`
那一条；`bash freeze/verify.sh` 跑两遍都绿（第二遍防再生成物不定）。

## 负样本，两条

* **把 hold 解除写成「第 12 项 ready」的那一版必须红。** 造一份只清掉钱这条
  阻塞、把 `⟨…⟩` 原样留着的 MANIFEST，检查必须指名那三个占位符。一个因为
  预算变宽而变 ready 的冻结项，是这整份清单存在的反面。
* **把上限改回 $214.90 而不改花费，`remaining_measured_usd` 必须回到
  −35.1687 并重新扣住第 12 项。** hold 的解除必须是上限的函数，不是一次
  写死的编辑；今天没有任何测试证明它是前者。
