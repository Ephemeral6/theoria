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

---

## 对账 2026-08-04（监控·board hygiene）· 引的那段算术已经过时，缺的那张票还是没开

2026-08-02 的 V29 交付（`exam/state_space.py` 779 行 + `tests/test_state_space.py`
111 个测试，`exam/runs/20260802T0000Z-V29-class-ii-state-census/`，合入 master 于
`ceedfaf0`）**把本件引用的那句话变成了假的**。本件逐字引了
`exam/DECISIONS.md:1053`：

> The bound is arithmetic and **no class (ii) board has ever had its states
> counted**

现在数过了，而且是精确值：

| item | 状态空间 | 方法 |
|---|---|---|
| ii1 `vq-721d09813c` | **1.595e38** | 符号（BDD），精确 |
| ii2 `vq-6150a6eeb7` | 1.595e38 | 符号，精确 |
| ii4 `vq-2986ed8ffc` | 8.862e35 | 符号，精确 |
| ii3 `vq-ee54166153` | 1.661e37 .. 4.133e63 | 双侧包夹 |

四件全部存活，类不空；每个数都高出构造性下界 2^m（120 倍 / 120 倍 / 8÷3 倍），
ii3 连包夹的**下**侧都比此前发表的 2^60 高 19 个数量级。载重测试是：在穷举
跑得完的每个尺寸（k=2..6）上，普查与朴素穷举**必须逐位相等**。

**这改变了本件的论证，不改变本件的结论。** 本件的要害从来不是「没数过」，
是 `DRILL.json` 的 `classes_absent: ["large_unsolvable"]` 一个键背着两种意思，
而 `MAX_ENUMERATION` 不是旋钮。数出 1.595e38 只是把「naive 方法跑不动」从
推断变成了测量——**它恰好是本件那条负样本要钉的东西**（把上限抬到 10^7
再跑，`classes_absent` 必须仍含 `large_unsolvable`），现在有了精确的靶子。

**验收三条，一条都没落地**，逐条复算于 master `4846e66d`：
`DRILL.json` 的 `classes_absent` 未拆成 `absent_structural` / `absent_incidental`；
`exam/DECISIONS.md:1040` 那一节没有回指票号；**`monitor/board/items/` 里仍然
没有任何一件 worldgen 领地的票**。第三条是本件的第一交付物，也是本件的全部
意义所在——一个专门指出「说了 filed 其实没进盘」的记录，自己已经在盘上等了
四天而它要开的那张票还没开。

顺带一条给下一个认领人的证据：那封该被引用的请求就在
`monitor/inbox/20260730T0300Z-RES-3-worldgen-cannot-host-a-large-space-world.md`，
而按 `monitor/inbox_recon.py` 的对账，它属于 225 件**文件名里没有收件人**的
ask（新开的 S52 量了这件事）——所以 worldgen 从来没有任何机制会看见它。
开票时请一并在票里引它，不要再写一次 filed。

**本件保持 open，正文的算术段落按上表更新**（5e6 可承受 vs 1.33e36 的对比
应改为 vs 已数出的 1.595e38；473 B/state 与 N^1.49 两条未被本次交付触及，
仍然有效）。
