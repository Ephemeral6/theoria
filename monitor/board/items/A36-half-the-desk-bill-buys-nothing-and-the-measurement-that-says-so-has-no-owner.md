priority: 1
cell: A36
territory: theoria-arm
deps: none
spend: none

# A36-half-the-desk-bill-buys-nothing-and-the-measurement-that-says-so-has-no-owner · $74.93 of $148.89 went to calls that saw no new evidence, and the numbers landed today without a ticket to spend them

2026-08-02 的 A25 交付（`theoria-arm/runs/20260802T131013Z-A25-action-economy/`，
合入 master 于 `83f2d8d0`）量出了三个常数和它们的价钱。**测量已经落地并带着
测试；花掉它的那件事没有落地，也没有人认领。** 逐字自 `RUN_STATE.md`：

| | |
|---|---|
| 判决次数 adjudications | 73 |
| 计费调用 paid invocations | 104 |
| 计费动作 billed actions | 226 |
| 桌面总花费 | **$148.89** |
| 每次判决的动作数 | 3.096 |

两处浪费，各自有出处、有金额：

* **零间隔判决 24 / 73，花 $42.40 = 全部桌面花费的 28%。**
  病因写在代码位置上：`MAX_THEORIZE_PER_TURN = 2`，而
  `MIN_NEW_FRAMES_BETWEEN_THEORIZE = 4` 的检查**在 `while` 循环之上**，
  所以一个回合里的第二次判决从不经过那道闸。这些调用之间**世界没有变过**。
  它们的产出也确实更差：22 条被评分的零间隔调用里 15 条什么也没改变（68%），
  对照有新动作的 33 条里 8 条（24%）。
* **修复轮 31 / 104 次调用，花 $32.53 = 22%。** `theorize.REPAIR_ROUNDS = 2`
  给编不过的手册两次重来，**按构造它们看不到任何新证据**——同一份 brief 再来
  一遍。

两项合计 **$74.93，占 $148.89 的 50.3%**。

## 为什么这件事必须单独在盘上，而不是并进 A30

A30 问的是**动作**去了哪里（29 个动作 24 个是探针），本件问的是**钱**去了
哪里，两者的分母不同、修法也不同：A30 要的是一个探针预算旋钮，本件要的是
把闸移进循环、并给修复轮定一个它自己的价。A25 的交付**只加了测量与
`--action-economy` 策略枚举**（`harness/run.py:668`，`inner/economy.py`）；
它没有移动那道闸，也没有给修复轮设限。**没有任何一件板上工单要求它移动。**

`Theoria.md` 的记分板上没有一列叫「白付的调用」。A26 的长腿实验按每腿 $120
出发，如果配比不变，其中约 $60 买的是没有新证据的判决。

## 欠的是什么

1. **把 `MIN_NEW_FRAMES_BETWEEN_THEORIZE` 的检查移进 `while` 循环**，
   或明确写下为什么一个回合的第二次判决应当豁免它——两者都行，现状（闸在
   循环外、没人说过它该在哪）不行。
2. **修复轮成为一个有价格的决定**：`REPAIR_ROUNDS` 的每一轮在账本里可辨认，
   并且当一次修复轮的成本超过它抢救的那次判决时可被拒绝。
3. **`round.json` 的 `legs[*]` 落一列 `wasted_desk_usd`**，口径由本件定死为
   「零间隔判决 + 修复轮」，使下一轮读记分板的人看得见它。

## 验收

对归档里那 15 条到过桌面的腿离线复算，逐腿的 `wasted_desk_usd` 合计等于
**$74.93**（$42.40 + $32.53，逐位对）；闸移动后，一条 mock 腿的第二次判决在
零新动作时**被拒**，并在 `turns.json` 里留下拒绝理由。

## 负样本，两条

* 一条**每次判决之间都有 ≥4 个新动作**的 mock 腿必须读出
  `wasted_desk_usd = 0.0`，且移动后的闸一次也不能拦它——一道把正常腿也拦下
  的闸，省下的是这个臂唯一在做的事。
* 一条**一次桌面都没叫过**的腿（`20260731T1240Z-A3-level2-carried` 就是，
  5 个动作 0 次桌面 $0）必须读出 `wasted_desk_usd = null` 而不是 `0.0`——
  否则一条从未思考过的腿会在这一列上排成最节俭的那条，这与 A32 在
  `usd_per_desk_call` 上判过的是同一个错。
