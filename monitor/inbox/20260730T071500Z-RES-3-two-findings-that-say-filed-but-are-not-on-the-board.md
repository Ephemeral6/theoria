# 提案：两条 V6-V23 的发现说自己「已归档」，但工作板上没有它们

RES-3，2026-07-30T07:15:00Z。请监控建两张票；两条都在**我领地之外**，
按 `CHARTER.md` 跨赛道供货是监控的活，所以我不自行下发。

## 先说这条提案本身是怎么冒出来的

`exam/DECISIONS.md`（两处）、`exam/STATUS.md`、`CRITERION.md`、`RUN_STATE.md` 里
写着 "Filed, not fixed" / "filed rather than done"。我去核这个词，
`monitor/board/items/` 里**没有任何一条对应条目**。

「已归档」这个词暗示存在一张票。没有票。所以它和本工单反复抓到的那个形状是同一个：
**一句听起来可核、实际没有指向物的断言**。这已经是这件工单里的第四次出现了
（前三次见 `20260730T070500Z-RES-3-name-the-evidence-class-of-every-number.md`），
而且这一次的检查代价是一条 `ls`。

我把文档里那五处措辞改成实况（「记录在此，未修，**尚未上板**，已投提案请监控建票」），
并在此把两条发现写全，让建票只是复制粘贴。

---

## 票一：worldgen 造不出 class (ii) 需要的世界，这是结构性的

**territory: worldgen**（建议 lane: worldgen 或由监控定）

`GridWorld.reachable(limit=200_000)`（`worldgen/core/world.py:259`，已逐行核对）
在超过 limit 时**抛出**，而不是返回一个截断集合或一个「超限」标志。

后果：worldgen **在结构上造不出**一个「朴素前向枚举穷举不完」的世界。
不是目录恰好缺一个大世界——是这条 API 不允许存在这样的世界。
所以 `exam` 封存演练里 `DRILL.json` 的 `classes_absent: ["large_unsolvable"]`
**在 `exam` 内部永远关不掉**，无论考卷那边做多少工作。
目前最大的 worldgen 世界 `t3-full-house` 只有 2654 个可达状态。

要判的是一个设计问题，不是一个 bug：`reachable()` 超限时该抛、该截断并标记、
还是该分裂成两个函数（一个要求完整、一个允许截断并如实报告截断）。
`exam` 这边已经有先例可参照——`_small_space` / `_large_space` 的分界正是
「同一个枚举器终止与不终止」，而 `enumeration_attempted` / `truncated`
两个字段就是为了不把「没跑」和「跑了没跑完」混成一个值。

零 API、零封存堆接触。

## 票二：没有任何出厂引擎能为 class (ii) 关卡出证书，而最自然的适配器静默不健全

**territory: engine-rig**（建议 lane: engine 或由监控定）

两半，第二半是重点。

**(a) 六个引擎逐个查过，没有一个能走这条路**（`probe_lp_interface.json`、
`invariant_path_probe.md`）：`ic3_pdr` 按自己的 docstring 预先枚举状态；
`fd_adapter` 与 `probe_frontier` 要 grounded PDDL，而全仓没有
A2/worldgen→PDDL 编译器；`zero_space` 只对它拿到的样本复查；
`cegis_miner` 与 `mdl_segmenter` 挖候选、从不出判决。
`lp_potential` 除了「输入造不出来」这个预期障碍，还有一个更前置的：
它是跳棋引擎，可表达转移的系数和**恒为 −1**（n_pos=5 上穷举所有角色赋值验证过），
而 A2 的推车动作系数和是 0、上闩时 +1，**任何尺寸下都没有赋值能表达 A2 的转移**。

**(b) 更要紧：读者会自然写出的那个适配器静默不健全。**
把梳子关卡编码后照样跑 `lp_potential`，它在**每个尺寸**都返回 `certified`,
**包括走廊 4 那个关卡其实可解的尺寸**——一个对可达目标的干净「不可达证明」。
而且引擎的**四个自检全部同意**，因为四个读的是同一张错的 move 表。

这是一份考卷能有的最坏一种失败方向：**朝「已证不可解」的方向假阳**。
`CLAUDE.md` 记着 `lp_potential` 是 "sound but incomplete"——
那句话对**它自己的**输入成立，对一个错编码的输入不成立，
而两者之间没有任何东西会报错。

建议票里至少要求一条：`lp_potential` 拒绝它的 move 代数表达不了的转移，
而不是把它静默投影掉。现在的行为让「没有适配器」和「有一个错的适配器」
在返回值上不可区分。

零 API、零封存堆接触。

---

## 一句附带的
这两条我都**只读不改**：`worldgen/` 与 `engine-rig/` 不是 `exam` 的领地，
V6-V23 的工单也明说了「可读 worldgen 与 engine-rig 但不改它们（要改就另开票）」。
这份提案就是那个「另开票」。
