# 对抗性复核：zero_space 的量词结论

RES-3 派出的对抗性复核员。任务是**试图推翻** `partials/zero_space-via-lp.md`。
worktree：`.worktrees/e11-engine-crosscheck-deep/`。**未修改 `engine-rig/`、`fuzzlab/`、
`CONTRACTS/` 的任何字节**；本文件是本次复核唯一的写入。临时脚本在系统临时目录
（`scratchpad/adv.py`、`adv_e11b.py`），不在仓库内。无网络，封存堆零接触。

---

## 判决摘要

| 被复核的结论 | 我的判决 | 强度 |
|---|---|---|
| 13 个世界、102 条律在某条合法转移上增量为奇（数字本身） | **推不翻**——逐位复现：13 个种子完全相同，102 条、1832 vs 1788 完全相同 | 实测 |
| 这 102 条的反例是**合法**转移 | **推不翻**——`apply_operation` 无前置条件，任意 (state, op) 都合法；3 个反例逐步手验 | 实测 |
| 引擎维数恒 ≥ 真维数，从无反向；"消元没错，错的是量词" | **推不翻**——1832 vs 1788，200/200 无反向 | 实测 |
| 分层 k=2 时 0/135、k≥3 时 13/65 | **推不翻**——四格数字完全相同 | 实测 |
| 证据不独立：`verify` + fuzzlab 四条全部从 `world.states` 重算 | **推不翻**——四条逐条读码确认，含 `law_space_is_complete` 的 oracle | 读码 |
| `scope: cell_local` 里 329/1271 是真子集、无一落在 `cell_local_subspace()` 内 | **数字推不翻**（1271/942/329/0 完全相同）；**理由部分推翻**——"15 个测试全在 Fixture B" 是错的 | 实测 |
| **「这是 `zero_space` 的缺陷」这个定性** | **削弱（应降级）**——D-003 已白纸黑字豁免了这个现象 | 读码 |
| 主管补充的「`coverage` 恒 n/n 构造上不可能表达证据有限，是引擎的错」 | **推翻**——按冻结契约自己的注解，n/n 是**正确**的；但问题换了个位置仍然存在，且更严重 | 读码+实测 |

**一句话**：所有数字我都推不翻，一个也没推翻。**但"缺陷"这个词推翻了**——
引擎从未承诺过被证伪的那件事，`DECISIONS.md` D-003 提前三个月写下了这个现象并称其
"still sound"。真正的缺陷在别处，而且比报告说的更严重（见「我另外发现的」）。

---

## 1. 引擎到底承诺了什么（带出处原文）

**反方（豁免）证据，按份量排序：**

**① `engine-rig/DECISIONS.md` D-003（决定性）**——这条直接命名了本次"发现"的机制，
并且预先裁定它不是缺陷：

> **Context.** The GF(2) null space recovered by `zero_space` depends on which
> difference vectors were observed. If a pair never fires, the observed difference
> space is smaller and the recovered invariant space is correspondingly larger
> (**still sound**, but weaker than the ground truth `(#Red) mod 2`).
> …`zero_space` itself makes no assumption about which pairs appear.

"observed difference space 小 ⇒ recovered invariant space 大 ⇒ **still sound**"——
这正是 102 条律的成因，逐字。引擎作者知道、写下了、并明确把它归类为
**soundness 保持、completeness 相对 ground truth 变弱**。

**② `zerospace.py:106` `contains()` 的 docstring**——量词写在方法签名上：

> Is this vector one of the conservation laws **the evidence supports**?

**③ `fuzzlab/props/zero_space.py` 的不变式名与表格**——soundness 的定义就是轨迹上的：

> `laws_hold_on_trajectory` | **soundness.** Every law returned really does have
> constant parity **along the trajectory**

**④ `engines/zero_space/README.md:50`**——"`verify()` re-evaluates every reported law
directly **against the trajectory**"。

**正方（过度断言）证据：**

- `zerospace.py:6-7` / `README.md:13`：`a · x(t) = a · x(0)` **for all t**。
  这里 `t` 索引的就是轨迹，**这句话在数学上是真的**，不构成过度断言。
- 但 `README.md:20` 与 D-012 都说 global 律 "**says something about the *world***"，
  `Law` 的类名、"conservation law" 这个词、`kind="invariant"`——**这一层是世界级的读法**，
  而底下的数学只支持证据级。

**判决：削弱，要求降级。** 引擎的**数学陈述全部正确且量词标注正确**；越界的是**解释层**
（"about the world" / "conservation law" / "invariant"）。把它报成 `zero_space` 的
soundness 缺陷是**假阳性**——D-003 是一份提前写好的豁免书。

**这条结论应该降级成什么**（三句，可直接替换报告的"一句话结论"）：

> `zero_space` 的输出在其**声明的量词（观测轨迹）下完全正确**，200/200 个世界的消元
> 与独立 oracle 一致。当把量词加强到"世界的全部合法转移"时，13/200 个世界的 102 条律
> 不再成立——这是 D-003 已记录的"证据越少、空间越大"现象在 k≥3 上的定量测量，
> **不是新缺陷**。真正的新事实有两条：(a) `parityworld` 生成器的自审注释在 k≥3 上是假的；
> (b) 契约的 `coverage` 字段对全称量词型 candidate 恒为满，无法承载这个量词差。

---

## 2. `kind=invariant` 与 `coverage=n/n`（对照冻结契约）

**主管的质疑错了，我把话说精确。**

`CONTRACTS/candidates_schema.md`（冻结 v0.1）只规定形状 `"coverage": "<k>/<n>"`，
不定义 k、n 的语义。语义定义在契约的可执行形式旁边，`engine-rig/common/candidates.py:75-76`：

> `coverage` is the literal `"<k>/<n>"` string the contract asks for: **k supporting
> transitions out of n transitions where the proposal's guard applies.**

分母是「**guard 适用的转移数**」，不是「世界的全部转移数」。一条不变式的 guard 是恒真的，
它适用于全部 n 条**已观测**转移，且全部支持它。**所以 n/n 在契约下是正确的**，
`tools/validate_candidates.py` 也只校验 `k ≤ n`。同族引擎的用法一致：
`cegis_miner` 的 `len(support)/len(applicable)` 才是 k<n 的情形，因为它的 guard 有条件。

`kind="invariant"` 同样是契约第 6 行明列的合法枚举值，payload 形状由引擎自己的 README
定义并保持稳定——`zero_space/README.md` 第 55-70 行定义了，稳定。**契约层无违规。**

**但问题没有消失，它换了位置，而且这一格才是真正要报的：**
`coverage` 的语义是**guard 适用性**，对一条全称量词的不变式**结构上恒等于 100%**。
于是契约里**没有任何字段能表达"这条律背后有多少证据"**。这不是 `zero_space` 能修的——
在冻结契约内无法修。它是**契约的表达力缺口**，归属 `/CONTRACTS/`，需要两个 track 共同处理。

严重性由下面这个实测数字决定，不是由 parityworld 决定。

---

## 3. 那 102 条反例的合法性（我重算了哪几个）

**这是最可能让数字整个作废的地方。我没能作废它。**

**根因（读码）**：`fuzzlab/worlds/parityworld.py::apply_operation` 全文如下，
**没有任何前置条件**——它对每个 `cell in operation.cells` 无条件做
`colors[(index[out[cell]] + shift) % k]`。任何颜色都能加 shift 取模，
所以**任意 (state, operation) 对都是合法转移**，不存在"枚举出世界里不可能发生的转移"这回事。
`generate()` 里的 script 也只是从同一个 op 列表里随机取，没有可用性筛选。
复核员那句"parityworld 的每个 operation 在每个状态上都合法"是对的。

**我重算的 3 个反例**（`adv.py` PART B，逐步验证）。每个都独立于 `apply_operation`
手工重算了后继（`manual[cell] = colors[(cmap[c]+shift)%k]`），并核对起点是否真在轨迹上、
op 是否真在该世界声明的 op 列表里：

| seed | k | 律 | 起点 | op | 后继 | 手算一致 | 起点在轨迹上 | op 已声明 | 奇偶 |
|---|---|---|---|---|---|---|---|---|---|
| 111 | 3 | `(C@0 + B@1) mod 2 = 0` | `AACA` | cells [0,1,2,3] shift 2 | `CCBC` | ✔ | ✔ | ✔ | 0→1 奇 |
| 126 | 4 | `(B@0+D@0+B@1+D@1+C@2) mod 2 = 0` | `BBAA` | cells [0,1,2,3] shift 2 | `DDCC` | ✔ | ✔ | ✔ | 2→3 奇 |
| 12 | 4 | `(D@1+C@2+D@2+B@4+C@4+D@4) mod 2 = 0` | `ABAAAB` | cells [0,1,2,3,4] shift 1 | `BCBBBB` | ✔ | ✔ | ✔ | 0→1 奇 |

三条律都通过 `verify` 的形状检验（在各自轨迹的全部 4 / 8 / 18 个状态上取值恒定）。

**我另外把报告自己那个"可以用手核对"的例子也验了**（seed 111）：
该世界 ops = `[([0],1), ([0,1,2,3],2), ([0,1],2)]`，colors `A,B,C`，
轨迹 `AACA → BACA → ACBC → CBBC`。`op {cells:[0,1], shift:2}` **确实在声明列表里**；
`AACA` **确实是轨迹第 0 个状态**；`AACA --op--> CCCA` 与报告一致；
律 `(B@1+C@1+C@3)` **确实在引擎 basis 内且是逐字发出的一条 law**；奇偶 0→1。
**报告写在纸面上的那个例子，手算无误。**

**判决：推不翻。** 合法性这条路封死了。

**一处数字瑕疵**（不影响结论，反而对报告不利）：报告称 102 条中 **91** 条的反例起点在轨迹上。
我按"存在一个起点在轨迹上的反例"重算得 **100/102**。差异应是报告只看了各自枚举序中
第一个反例。91 是保守低估，改成 100 更准。

---

## 4. 证据不独立这条元结论

**逐条读码核实，四条全部成立，没有例外。**

| 不变式 | 证据源 | 用了别的证据源吗 |
|---|---|---|
| `laws_hold_on_trajectory` | `_analyse(world)` → `world.states`；`encoded = [_encode(s) for s in world.states]` | 否 |
| `law_space_is_complete` | 同上；`differences = [x ^ encoded[0] for x in encoded[1:]]` → `gf2.null_space` | **否** |
| `rank_nullity` | 同上 → `gf2.row_echelon` | 否 |
| `membership_agrees` | 同上 → `result.basis` + `gf2.in_span` | 否 |

四条的第一行都是 `result = _analyse(world)`，而 `_analyse` 就是
`engine.analyse(world.states, world.colors)`。**没有一条碰过 `world.spec.operations`。**

`law_space_is_complete` 的 oracle（`fuzzlab/oracles/gf2.py`）我也读了：它是纯线性代数
（bitset 高斯消元 / RREF / 回代），只对**传进去的行**运算，自己不取任何证据。
`oracles/__init__.py` 的房规"an oracle may not call the engine it judges"管的是
**实现独立**，一个字也没管**证据独立**。

一个**加强报告**的细节：oracle 用的是"与首状态的差" `x_t ^ x_0`，引擎用的是"逐对差"
`x_t ^ x_{t+1}`——**两套算法确实不同**，但张成同一子空间（互为线性组合）。
所以 200/200 的一致不是巧合而是**定理**：它们必然相等。报告说"按定义两者必然相等"，
准确。这恰恰说明 `law_space_is_complete` 在这个方向上**信息量为零**。

**判决：推不翻，且这是全篇最扎实的一条。** 「这类伪律在数学上不可能被现有检验发现」
是可证的，不是经验观察。`fuzzlab/BUGS.md` 的 "Verdict: no engine defect found"
在这个方向上确实没有证据支持——但注意 BUGS.md 自己已经先认了这一点：
"absence of evidence over one corpus is not a proof"，且整节"The findings are about
the generators, not the engines"。**本次发现正好落进它自己划的那一类。**

---

## 5. scope 分类

**数字推不翻，理由部分推翻。**

**数字**（`adv.py` PART E，200 世界）：`cell_local` 共 **1271** 条，整组 **942** 条，
真子集 **329** 条，其中落在 `cell_local_subspace()` 内的 **0** 条。**与报告逐位相同。**
报警世界里被证伪的 51 条 `cell_local` 律，**51/51 全部出自真子集那一类**，也相同。

**机制读码确认**：`local_laws()` 枚举每个 cell 特征组的**全部非空子集**（`k ≤ 4`，
组大小 ≤ 4，恒走完全枚举分支，`> 8` 的剪枝从不触发），凡落在 basis 内即标 `cell_local`；
而 `cell_local_subspace()` 只造**整组**向量。两者定义确实不同，`analyse()` 用前者商掉、
`equivalent_modulo_encoding()` 用后者商掉，同一模块内两把尺子——这条属实。

**但报告说的理由是错的。** 报告称"`engine-rig/tests/test_zero_space.py` 的 15 个测试
全在 Fixture B 上跑，看不见这个分叉"。实测：

- Fixture B 确实**无单色格**（monochrome cells = `[]`），两个子空间
  `span_equal = True`——**合流属实**；
- 但 15 个测试里只有 **10** 个用 Fixture B。另外 **2** 个是手搭世界，
  **两个都有单色格、两个都 `span_equal = False`**：
  `test_parity_is_not_recovered_from_a_world_that_breaks_it`（单色格 `[1,2,3]`，
  7 条 cell_local，分叉）与 `test_a_world_with_no_actions_at_all_yields_every_law`
  （4 条 cell_local，分叉）。剩下 **3** 个是纯 GF(2) 工具测试，不涉及世界。

所以**分叉其实已经被两个测试的输入触发过了**，只是**没有任何断言去看它**——
唯一涉及 `scope` 的断言是 `test_exactly_one_law_says_something_about_the_world` 里的
`len(result.cell_local_laws()) == 8`，一个 Fixture B 上的**计数**，不检验标签语义。

**结论不变，理由要改**：不是"测试全在无单色格的 fixture 上"，而是
"**没有任何测试对 `scope` 标签的语义做断言**"。报告若照现在的写法提交，
engine-rig 领地一跑就会发现"15 个测试全在 Fixture B"是假的，**整条会被连带质疑**。
这一句必须改。

---

## 我另外发现的

**这是本次复核最重的一条，比 parityworld 那 102 条重得多，而且报告没查（它自己承认
"不知道有没有伪律流到下游…超出本工单范围"）。我查了。**

`grep` 全仓库已落盘的 `candidates*.jsonl`：**3449 行 `engine: zero_space`**，
分布在 `cold-start-a0`、`cold-start-a2`、`cold-start-a3`、`theoria-arm`、`worldgen`、
`engine-rig/artifacts`。抽样 2925 行统计：

- **2925/2925 行 `coverage` 的 k == n**（100%），一条例外都没有；
- 分母（= 已观测转移数）众数：**5**（1448 行）、**6**（1098 行）、**7**（365 行）；
- scope：`cell_local` 2352，**`global` 573**。

最极端的一批在 `theoria-arm/runs/20260728T015354Z-g50t-first-contact/candidates.jsonl`
——**真实 ARC 游戏**（g50t 属开发堆，无封存违规）：

```
coverage 5/5   space_dimension 362   n_features 365   difference_rank 3
```

**365 个特征、5 条观测转移、报出 362 维"守恒律"，每一条都盖着 `coverage: 5/5` 的满章。**
5 条转移的秩至多为 5，所以 dim ≥ 360 是**算术必然**——这批 candidate 里几乎整个特征空间
都被标成了"不变式"，其中 573 条打着 `scope: global`，按 README 的读法即
"says something about the *world*"。

三点为什么这比报告的发现严重：

1. **parityworld 是 fuzz 世界，g50t 是产物。** 报告的 102 条活在测试语料里；
   这 3449 行躺在 arm 的产物里，是 LLM 裁决的输入。
2. **k=2 的免疫在这里不成立。** 报告实测 k=2 世界 0/135 干净，是因为 k=2 时差分向量与
   状态无关。ARC 状态的差分向量**必然依赖当前状态**，即 k≥3 那一侧。
3. **`coverage` 恒满在这里从"语义争议"变成"实害"**：一条 5 条转移支撑的 362 维空间，
   与 Fixture B 上 40 条转移支撑的 9 维空间，在契约的每一个字段上**不可区分**。
   第 2 节说的表达力缺口，代价就是这个。

我**没有**去判定这 573 条 global 律里具体哪些是伪律——那需要 ARC 世界的可达性枚举，
离线做不到，也超出复核范围。**我断言的只是：证据饥饿的签名在产物里客观存在，量级是
362 维 / 5 条转移。** 这一条建议单独开工单，不要塞进 zero_space 的结论里。

**次要一条**：`fuzzlab/worlds/parityworld.py:131-133` 那句自审注释

> "Every operation is witnessed once before the random tail, so the observed difference
> matrix spans what the world can actually do rather than what a short random draw
> happened to sample."

**在 k≥3 上是假的**（实测 13/65 反例）。它是把 `DECISIONS.md` D-003 给 Fixture B（k=2）
的论证**照抄到任意 k** 造成的——D-003 的论证在 k=2、shift=1 下正确（差分向量与状态无关），
推广到 k≥3 不成立。这是 **fuzzlab 生成器的缺陷**，与 `BUGS.md` 已有的 G1–G4 同类，
建议编为 **G5**，报给 fuzzlab 而非 engine-rig。**这才是本工单真正抓到的那个 bug。**

---

## 我打不倒的（以及为什么）

诚实地列出来——这些我认真试过，没打倒：

1. **全部定量结果。** 13 个种子、102 条、1832/1788、0/135 与 13/65、1271/942/329/0、
   51/51——我用自写脚本从头复现，**逐位相同**。报告的实验是可复现的。
2. **反例合法性。** 我原以为这是最脆的一环（枚举出世界里不可能发生的转移）。
   `apply_operation` 无前置条件，这条路封死。3 个反例逐步手验通过，报告纸面上那个也通过。
3. **"消元没错"。** 200/200 与独立 oracle 同张成。引擎的线性代数没问题。
4. **证据不独立（X-1）。** 四条不变式逐条读码，全部只吃 `world.states`。
   而且我发现它比报告说的更强：oracle 与引擎算的是两组差分向量，张成必然相等，
   所以 `law_space_is_complete` 的通过是**恒真的**，不是证据。
5. **两把尺子（X-2 的机制部分）。** `local_laws()` 收任意子集、`cell_local_subspace()`
   只收整组，确实是同一模块内的两种定义。

打倒/削弱的只有三处：**"缺陷"这个定性**（D-003 豁免）、**`coverage` 的契约违规指控**
（契约自己的注解支持 n/n）、**"15 个测试全在 Fixture B"这个事实陈述**（10/15，
且两个手搭世界恰好触发了分叉）。

---

## 如果要 escalate，诚实的措辞应该是什么

给 engine-rig 领地的一段，不夸大也不含糊，可直接用：

> **`zero_space` 没有缺陷，`parityworld` 有，契约有一个缺口。**
>
> 我们用 `lp_potential` 的条件形状（精确算术、逐 move instance、量词跨转移而非跨可达状态）
> 复核了 `zero_space` 在 200 个 `parityworld` 上的输出。结果：**引擎在其声明的量词下
> 完全正确**——200/200 个世界的消元与独立 GF(2) oracle 同张成，无一反例。
> 把量词加强到"世界的全部合法转移"后，13/200 个世界的 102 条律不再成立
> （k=2 时 0/135，k≥3 时 13/65；反例转移经三例逐步手验合法）。
>
> **这不是缺陷报告。** `DECISIONS.md` D-003 已经记录了这个现象——"observed difference
> space 小则 recovered invariant space 大，still sound but weaker than ground truth"
> ——本次工作是它在 k≥3 上的定量测量，不是新发现。同样地，`coverage` 恒为 `n/n`
> 符合 `common/candidates.py` 对该字段的定义（guard 适用的转移数），**不是违规**。
>
> 需要你们处置的有三件，按轻重：
>
> 1. **（不在你们领地，仅知会）** `fuzzlab/worlds/parityworld.py:131` 的自审注释
>    "the observed difference matrix spans what the world can actually do" 在 k≥3 上
>    可证为假。它照抄了 D-003 对 Fixture B（k=2，差分向量与状态无关）的论证并推广到任意 k。
>    建议 fuzzlab 编入 `BUGS.md` 的 G 系列。
> 2. **（值得单开工单）** 全仓库已落盘 candidates 中有 3449 行 `engine: zero_space`，
>    `coverage` 的 k==n 占 2925/2925；`theoria-arm` 的 g50t 真实对局里，
>    **365 个特征、5 条观测转移、报出 362 维守恒律**（其中 573 行标 `scope: global`）。
>    我们**未判定**其中哪些是伪律（需 ARC 可达性枚举，离线做不到）；我们断言的是
>    **证据饥饿的签名客观存在，量级为 362 维 / 5 条转移**。
> 3. **（`/CONTRACTS/` 层，两个 track 共同）** 冻结契约的 `evidence` 只有
>    `transitions` 与 `coverage`，而 `coverage` 对全称量词型 candidate 结构上恒为满。
>    于是"5 条转移支撑的 362 维空间"与"40 条转移支撑的 9 维空间"在契约的每个字段上
>    不可区分。这个缺口 `zero_space` 在冻结契约内无法自行修补。
>
> 另有两条给 `zero_space` 的**文档级**建议（非缺陷）：README 第 20 行 global 律
> "says something about the *world*" 与 `kind="invariant"` 的世界级读法，
> 强于底下数学支持的证据级量词；`local_laws()`（任意子集）与 `cell_local_subspace()`
> （仅整组）是同一模块内的两种"编码律"定义，200 世界中 1271 条 `cell_local` 有 329 条
> 是真子集且无一落在后者张成内，而现有 15 个测试无一对 `scope` 标签的**语义**做断言。
