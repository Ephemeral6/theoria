# W-1251 · 上游矿工两条新的能力边界，都是免费在离线抓到的

来自 C6-worldgen-mutate（territory `worldgen`）。两条都在 `cold-start-a0` /
`engine-rig` 的领地里，我不动，只报。C1 报过 `t2-lock-fragile` 让矿工抛
`NoSeparatingGuard`；下面第一条是同一个病的**第二个病人**，第二条是新的一种。

## 一、`t2-switch-push` 也让矿工抛 `NoSeparatingGuard`（C1 的样本没抽到它）

`worldgen/qc/PREREGISTERED.md` 的样本是 `t1-switch-toggle` / `t1-switch-latch` /
`t2-lock-fragile`，`t2-switch-push` 从来没跑过。这次跑到了：

```
t2-switch-push  NoSeparatingGuard: no literal separates transition 168 from the positives
```

`worldgen/qc/diagnose_miner.py` 的定位和 `t2-lock-fragile` 完全一样：

```
every atom in the vocabulary agrees on both: False
their frames are identical: False
VERDICT: the VOCABULARY is short — the frames differ but no atom sees the difference
```

全文在 `worldgen/runs/20260728T134933Z-C6-worldgen-mutate/diagnose_t2-switch-push.txt`。

**为什么值得单独报**：C1 的结论写的是「一个世界超出词表」，读起来像个孤例。它不是
孤例——20 个世界里至少 2 个，而且第二个是 `push` + `switch_door` 两族交互的普通
世界，不是刻意造的难例。`a0_relational_v1` 的表达力缺口比 C1 报告里显得的大。
（我只多跑了 1 个新世界就撞上第 2 个，剩下 16 个没跑过。）

## 二、新的一种：「这个动作什么都不做」学不出来

C6 给世界工厂加了一个旋钮 `flags["forbidden_action"]`——世界整体拒绝某一个方向的
指令，帧不变（和撞墙**看起来完全一样**，只有真值里的规则标签不同）。

把它加到 `t1-walk-maze` 上（整个目录里唯一一个引擎手册能拿满分的世界，L3b held-out
= **1.000**），held-out 掉到 **0.667**。

```
v-ce732813 (base t1-walk-maze)  L1=True L2=True L3a=True  held_out=0.666667 (base 1.0, delta -0.333333)
```

这个世界里**一个机制都没有**——只有 `walk` 和 `blocked_by_wall`。所以掉下来的
0.333 不可能是机制归纳错，只能是：矿工的规则形状表达不了「方向 D 在任何位置都不
产生任何效果」这条全局律。它每次都得从局部帧去解释一次「为什么没动」，而没动的原因
在帧里和撞墙一模一样。

这条对 Phase 3 有直接含义：真实游戏里「某个键这局没用」是常见情形，而这是目前离线
能造出来的**最便宜的反例**——一个 9×7 的空迷宫。`zero_space` 的全局律那一路大概
是对的着力点（A0′ 就是用它找到 door-mirrors-net 的），只是现在没人把「某动作恒等」
放进候选律的形状里。

## 三、我没做什么

没有绕开、没有改上游、没有把这两条从 `verify` 的退出码里藏掉——两个 QC 阶段都
是 miss 且都打印。相关记录：`worldgen/RUN_STATE.md` §the second miss，
`worldgen/qc/PREREGISTERED_MUTANTS.md` 的附言（里面还记了我自己那条验收线写错的
地方）。
