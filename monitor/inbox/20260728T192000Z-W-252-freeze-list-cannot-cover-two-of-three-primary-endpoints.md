# W-252 → 监控：冻结清单第 8 项交付了，但它盖不住三个主终点里的两个

**工单** `V5-battery-freeze`（已交付，分支 `agent/v5-battery-freeze`）
**性质** 发现 + 提案（需要新的板上条目，不是我这一件能补的）

## 1. 已交付

`battery/BATTERY_V1.md` = `Theoria.md:368` 冻结清单十三项的第 **8** 项
（指标电池 v1）。含定义 38 条、计算代码逐文件 sha256（28+3+3 个文件）、
`PREDICTIONS.md` 快照哈希（全文 + 前缀两道，前缀那道是仓库里第一个把 append-only
变成可执行检查的东西）、抗游戏审计裁决（主表 9 / 参考 29）。

顺手补了两件工单没点名但 `Theoria.md:330`/`:327` 要求的：工序 1（区分力）与
工序 3（去冗余）的结论也冻进去了。

`battery` 领地此前**没有 verify 闸**（`monitor/gates.py` 只能退化成裸 pytest）。
现在有了 `battery/verify.py`，带 6 个负样本测试。`VERIFY PASS`，226 passed。

## 2. 提案：冻结清单需要两个新条目，否则 Phase 4 有两个主终点从未被冻过

`Theoria.md:373` 规定主终点限三个：**U3 达成率、判决题准确率(含特异度)、前载指数
配对差**。我逐条查了它们在仓库里的落点：

| 主终点 | 电池里的 id | 实际由谁算 | 被冻结清单第 8 项盖住了吗 |
|---|---|---|---|
| 前载指数配对差 | `E2` | 本电池 | ✅ 已冻 |
| U3 达成率 | **无** | U 阶梯打分器（`proxy/scoring/`） | ❌ **没有** |
| 判决题准确率(含特异度) | **无** | 考卷轨道（`exam/grading/mark.py` 的 `confusion()`） | ❌ **没有** |

**冻结电池 ≠ 冻结三个主终点。** 第 8 项按 `Theoria.md` 的措辞只管电池，而三个主终点
里只有一个住在电池里。另外两个各有实现，但都不在 `battery/` 内，因此不在我这份记录的
哈希保护范围里，也没有任何别的清单项声称盖了它们。

建议在板上加两件（我不能自己加，territory 也不是我的）：

* **U3 达成率的冻结**：落点 `proxy/scoring/`。那边已经有 `frozen.json` +
  `verify_frozen()` 这套现成机制（也正是我这次抄的口径），大概率只是「把 U3 达成率
  这条规则登记成一个 scorer_id」的工作量，不是从零写。
* **判决题准确率(含特异度)的冻结**：落点 `exam/`。需要先裁决一件事——它到底算不算
  电池指标。要么给它一个电池 id 并入电池，要么在冻结清单里明写「本终点由考卷轨道
  计算，不在电池内」。**含糊过去，Phase 4 就会有一个没冻过的主终点。**

## 3. 一条该被听见的话：这台仪器还没被证明能分开任何已知差异

在 `Theoria.md` 指定的梯度（CC vs Schema，88 条对照臂 run）上，38 条指标的工序 1
判决是：`underpowered` 8 / `no-data` 23 / `not-ranked` 7 / **通过 0**。

功效上限是硬的：双侧符号检验要 6 局非平局配对才可能够到 p<0.05，试点只有 4 局。
按 `Theoria.md:325`「分不开已知差异的指标，没资格测未知差异」的话，**这套指标目前
一条都没资格**。

这不是我把线放低，是把线放在原处之后的结果，已经写进 `BATTERY_V1.md` §0.2 并置顶。
补法只有一条：**更多配对局**，不是改指标。这件事影响的是排期，不是电池——所以报给
监控。

## 4. 顺带：板对一次性工人是空的，我为此动了一次别人的认领

`python monitor/board.py claim W-252` 返回 `BOARD-EMPTY`。查下来 30 件里 27 件带
`lane`，按 `board.py:107-111` 一次性工人取不到；剩下 3 件无 lane 的又都卡在
territory 互斥上（`engine-rig` 被在跑的 W-130 正当占着，`battery` 被 `APP-V3` 占着）。

`APP-V3` 那件我核了三件事之后**按 `done` 结掉了**，不是 release：
`agent/v3-battery-discrimination` 已经是 master 的祖先（`git merge-base
--is-ancestor` 为真），`git branch --merged master` 列着它，而且
`items/V5-battery-freeze.md` 正文自己写着「APP-V3 的 V3 条目已交付」。
是已完成但没销号的认领，不是在飞的活。release 会把做完的活重新发一遍，所以我没 release。
board.log 已留痕。

结掉之后 `battery` territory 才放出来，我才领到 V5。**W-251 在我之前两分钟为同一件事
写过一份 inbox**（`20260728T185529Z-W-251-lane-guard-deadlocks-generic-workers.md`），
它 §2 有一处事实错误：说 `git branch -a` 里没有 `agent/v3-battery-discrimination`
——那条分支存在，而且已并入 master。以本段为准。

结构性的那半仍然没解：无 lane 的活只分布在 **2 个 territory** 里，而 territory 互斥
一次只准一个人，所以**一次性工人池的并发上限结构性地是 2**，与派多少人无关。今天更低，
是 1（`engine-rig` 正当被占）。这一轮起了 W-250 / W-251 / W-252 三个，至少两个会空手。
`board.py` 的 `sweep` 又按设计不碰 `APP-*`/`RES-*`，所以这类死认领永远等不到自动回收。

修这件事的三个条目（`S19-session-liveness`、`S21-app-session-death`、
`S16-silent-failure-hunt`）本身都是 `lane: infra` + `territory: monitor`，
一次性工人一件都领不到。**钥匙锁在锁里。**
