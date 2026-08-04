priority: 2
cell: V31
territory: exam
deps: none
spend: none

# V31-class-ii-cannot-be-built-and-the-request-to-build-it-was-never-boarded · 一个自己承认「不在盘上」的缺口，至今仍然不在盘上

`exam/DECISIONS.md:1040` 起，逐字：

> ### Not closed: the sealed drill's class (ii) gap is structural
>
> `GridWorld.reachable(limit=200_000)` (worldgen/core/world.py:259) **raises**
> above the limit, so worldgen cannot build a world whose state space
> exhaustive search cannot reach — the catalogue does not merely happen to
> lack one. `DRILL.json`'s `classes_absent: ["large_unsolvable"]` therefore
> cannot be closed from inside `exam`. Not done here; it needs a worldgen
> change. **Not on the board either** — "filed" was written before any ticket
> existed, which is this ticket's own defect class at one more remove.

**它是对的，而且它今天仍然是对的。** 那条 inbox 请求
（`monitor/inbox/20260730T071500Z-RES-3-two-findings-that-say-filed-but-are-not-on-the-board.md`）
写下三天后，`monitor/board/items/` 里没有任何一件叫 worldgen 建一个大空间
不可解世界。**一个专门用来指出「说了 filed 其实没进盘」的记录，自己没进盘。**
本件就是那张缺失的票。

## 缺的是什么，以及为什么它不是抬个上限就能了事

`exam/DECISIONS.md:1053-1058`，逐字：

> The bound is arithmetic and no class (ii) board has ever had its states
> counted; the affordable ceiling on this hardware is ~5e6 states against
> ii1's 1.33e36, with memory binding harder than time (~473 B/state, so 10^12
> alone wants ~473 TB) and the enumerator's own cost curve running at N^1.49
> rather than N because it copies a command path per state. Raising
> `MAX_ENUMERATION` is not a lever: **there is no cap between 200,000 and
> 10^12 at which class (ii) becomes enumerable.**

这段话把懒办法提前掐死了：`MAX_ENUMERATION` 不是旋钮。而
`DECISIONS.md:1228` 说已发货的每个 class (ii) 条目「clears it by 6 to 24
orders (smallest bound 2^60 = 1.15e18)」——**已发货的 class (ii) 全部靠构造性
下界，没有一个被数过状态**。这在逻辑上没有问题（下界是被展示出来的，不是断
言的），但它意味着 `DRILL.json` 的 `classes_absent: ["large_unsolvable"]`
是一句**关于演练目录的真话，且这句真话永远不会自己变假**。

## 因此本件的形状是跨领地，不是 exam 内部

* **worldgen 侧**：造一个状态空间超过 `reachable(limit=200_000)` 的世界，
  且它的不可解性由**构造**给出（不是由穷举给出——按上面的算术，穷举永远给
  不出）。这是 `worldgen/` 的活，不是 `exam/` 的。
* **exam 侧**：让 `DRILL.json` 的 `classes_absent` 能在这样的世界出现时**变**，
  并且在它出现之前，把「结构性缺席」与「碰巧没有」在产物里分开——
  今天 `classes_absent` 这一个键承担了两种意思。

**本件挂 exam 领地，因为 exam 是那个记录被读的地方**，但它的第一件交付物是
一封写进 `monitor/inbox/` 的、给 worldgen 的具名请求，附上上面那段算术
（5e6 可承受 vs 1.33e36 所需、473 B/state、N^1.49 曲线），好让 worldgen 一眼
看出为什么不能靠抬上限。**这一次要在盘上留下票号，不是再写一次 "filed"。**

## 验收

`monitor/board/items/` 有一件 worldgen 领地的对应票（本件交付时创建，
本件不代它做事）；`DRILL.json` 的 `classes_absent` 拆成
`absent_structural` 与 `absent_incidental` 两个键，`large_unsolvable`
落在前者并带一条指向 `world.py:259` 与上述算术的理由字符串；
`exam/DECISIONS.md:1040` 那一节加一行回指票号。

## 负样本，两条

* 把 `MAX_ENUMERATION` 调到 10^7 再跑演练：`classes_absent` 必须**仍然**
  含 `large_unsolvable`，且理由字符串不变。若它因为一个上限变动而消失，
  那这个键测的是配置不是世界——`DECISIONS.md:1058` 已经预言了这一点,
  本条负样本是把预言变成测试。
* 造一个**碰巧**没有大空间不可解世界的小目录（结构上做得到，只是这次没做），
  它必须落进 `absent_incidental`。两种缺席读出同一个值的那天，这个键
  就又只是一个字符串了。
