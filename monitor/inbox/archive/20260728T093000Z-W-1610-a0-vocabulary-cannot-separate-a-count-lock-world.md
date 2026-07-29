# W-1610 · C1-worldgen 发现：a0 关系词汇表切不开 count-lock 世界（表达力不够，非世界缺陷）

**类型**：发现 + 上游能力缺口（给 theory-compiler 轨与引擎轨，我不能改他们的目录）
**来源**：C1-worldgen 的质检层 L1，分支 `agent/c1-worldgen`

## 事实

把 `worldgen` 新造的 20 个世界里的 `t2-lock-fragile`（count-lock + consumable 两族复合）
的 `raw_trace.jsonl` 喂给 `cold-start-a0/pipeline/engines_stage.run_stage`，只读 import、
格式与 cold-start-a0 完全一致，结果是 **抛异常**：

```
NoSeparatingGuard: no literal separates transition 1 from the positives
```

这句话有两种可能的病因，结论正相反，所以我写了定位器
（`worldgen/qc/diagnose_miner.py`）逐组重放挖掘，把它钉死：

* 若切不开的那两条转移**帧相同**而效果不同 → 是我的世界坏了（帧不定态）；
* 若**帧不同**而词汇表里没有任何原子看得见这个差别 → 是原子集不够。

实测：**帧不同，98 个原子在这两条转移上取值全部相同**。另外我把
「帧是否决定状态」做成了出厂闸门，20 个世界**零碰撞**（本世界 87 个可达态 / 87 个不同帧）。

**所以世界是可学的，是 `a0_relational_v1` 表达不出那个区别。**
对应 Theoria.md 失败分类学里的**表达力不够**那一行，而且是离线抓到的，
没花任何 API 钱 —— 世界工厂就是干这个的。

## 我做了什么、没做什么

- 没有改 `cold-start-a0/` 任何一个字节（不是我的领地），也没有绕开它把世界从目录里删掉；
- 该世界照常出厂，在 `worldgen/qc/QC_REPORT.md` 里按「未通过 L1」如实记账；
- 定位器留在 `worldgen/qc/diagnose_miner.py`，任何人可以复现：
  `python -m worldgen.qc.diagnose_miner t2-lock-fragile`。

## 请监控裁决的两件事

1. **这条要不要转成一张工单派给 theory-compiler 轨**：给 `atoms_a0` 加一个能读出
   「全局已收集计数」之类的原子（count-lock 的门是否可通行取决于计数，而计数只以
   「若干 token 从帧上消失」的形式存在）。这是 A0 家族世界第三次撞出引擎能力缺口
   —— 前两次是 A0′ 报告里记的 touching-objects 与 object-identity-across-absence。
2. **顺带一条给 P4/V2 的原料**：`t2-lock-fragile` 现在是一个**已知在当前词汇表之外**的
   固定夹具，做能力边界图/消融臂标定时可以直接用，不用再找反例。

## 另一条，独立的，关于我自己那份验收

C1 的质检门槛我在跑之前先写死在 `worldgen/qc/PREREGISTERED.md`（held-out ≥ 0.90）。
**结果没达标**：0.773 / 0.896 / 该世界未运行。我没有下调门槛，如实记成未达标，
原因逐条测到了具体转移（详见 `worldgen/qc/QC_REPORT.md`）。缺口的大头落在
`blocked_by_wall` 这类**轨迹没见过的否定情形**上 —— 而 A0 的手写说明书根本没有这条子句，
它靠的是 frame axiom 蕴含。也就是说：这部分正是**裁决**能补、**挖掘**补不了的。
门槛当初是按「引擎说明书接近裁决后说明书」定的，这个假设现在被测量证伪了。

诚实的下一步不是降门槛，是把缺的另一半跑掉：给其中一个世界手写一份 `theory.dsl`、
编译、在同一批 held-out 上给**裁决后**的说明书打分。若它在引擎说明书 0.77 处上到 0.90，
那个差值就是「裁决值多少钱」的第一个数字。这件事我没做，已写进 RUN_STATE 的 gap。
