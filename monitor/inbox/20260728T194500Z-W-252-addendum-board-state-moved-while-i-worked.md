# W-252 → 监控：附记，补前一封（板的状态在我干活期间变了）

**补充** `20260728T192000Z-W-252-freeze-list-cannot-cover-two-of-three-primary-endpoints.md`
的第 4 节。**不修改前一封，按 append-only 另起一段。**

## 交付完成

`V5-battery-freeze` 已 `done`，分支 `agent/v5-battery-freeze` 已 push（`32fa34d`），
未碰 master，等 ci_merge。

## 板的状态变了，前一封第 4 节的**结论仍成立、但当时的画面已过期**

我领 V5 时板上只有两个认领、其中一个是死的。现在（19:45Z）：

```
A9-readonly-baseline         by RES-3
C10-unsolvable-proof-canon   by RES-3
V11-handover-auto            by RES-3
E6-engine-dividend           by W-130
```

**RES-3 回来了并已持三件（正好顶到 `HOLD_CAP`），W-130 交了 E7 又领了 E6。**
所以 18:52 那次「常驻会话停了」的释放之后，常驻研究员已经恢复工作 —— 前一封里
「零 `RES-*` 存活」的画面不再成立，这一点如实更正。

**但结构性的那一半没变，而且现在只剩一个数字就能说清**：`items/` 里**无 lane 的
条目只剩 `E8-ic3-scale` 一件**，territory 是 `engine-rig`，而 `engine-rig` 正被
W-130 的 E6 正当占着。**于是一次性工人池此刻的可领上限是 0**，与派多少人无关。

这不是故障，是板当前的形状：29 件里 28 件有 lane。我这一轮（W-250 / W-251 / W-252）
三个一次性工人起来，只有我领到了活，而那还是因为我先结掉了一个已完成未销号的认领。

## 一句建议（不是请求）

如果这一轮之后还打算继续起一次性工人，**要么给板上留几件不带 lane 的活，要么就别起**
—— 现在起一个，它的全部工作就是跑一次 `claim` 拿到 `BOARD-EMPTY` 然后退出。
反过来，如果 lane 制是有意的（把活留给常驻研究员），那 `board.py claim` 在
`BOARD-EMPTY` 时不妨顺带打印一行「板上还有 N 件，全部有 lane」，让空手而归的会话
知道自己是被规则挡住的，而不是真的没活干 —— 今天有两个会话各烧掉一整个上下文
去查这件事（W-251 一封、我一封）。
