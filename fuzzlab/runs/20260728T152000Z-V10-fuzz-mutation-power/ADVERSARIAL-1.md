# 对抗性复核 1：zero_space + cegis_miner

复核对象：`fuzzlab/MUTATION.md`（`zero_space` 一节）、
`runs/20260728T152000Z-V10-fuzz-mutation-power/partials/cegis_miner.md`、
`out/mutation.{zero_space,cegis_miner}.json`、`mutants/{__init__,zero_space,cegis_miner}.py`。
工作树 `.worktrees/v10-fuzz-mutation-power`，engine-rig HEAD `baf1671`。
除本文件外未修改任何文件；实验脚本写在系统临时目录。

**标记约定**：〔实测〕= 我跑了代码；〔读码〕= 只从源码推导。

## 判决摘要

| 被复核的结论 | 我的判决 | 强度 |
|---|---|---|
| `cm-empty-frontier` 是真缺陷（引擎承诺"未截断⇒frontier 非空"） | **推不翻**（并且我把"实测 0 例"升级成了构造性证明） | 实测 + 读码 |
| `cm-truncation-alibi` 是真缺陷（truncated 是可验证的客观事实） | **推不翻** | 读码 |
| `cm-shrink-lifted-support` 是真缺陷 | 缺陷本身**推不翻**；"从没被任何人审过"的措辞**削弱** | 实测 + 读码 |
| 13 个 kill 都是真检出（不是 raised 冒充 violated） | **推不翻**（结构上不可能混淆） | 读码 |
| 由"首杀=1、杀死率 100%"推出"500 世界是奢侈的" | **削弱**：kill 是构造性必然，这组数字测不了灵敏度 | 读码 |
| `expect_kill` 是跑之前写的 | **无法证明**，且未按姊妹文档的标准自陈 | 实测（mtime/git） |
| inert 会计把"没真的注入"排除在分母外 | **推翻一条**：`survived` 不要求 `worlds_evaluated > 0` | 实测 |
| `rank_nullity` 第三分支构造上不可证伪 | **推不翻**，并加强（它在 git 里从出生就是死的） | 实测 + 读码 |
| lifted 规则被发布却无人审（78 条） | 事实**推不翻**；两处理由**削弱** | 实测 + 读码 |
| （新）`zero_space` "5 变异体 0 survivor" | **削弱**：我写的第 6 个变异体 25/25 全活 | 实测 |

---

## 逐点详述

### 1. survivor 是真缺陷吗

我的任务是站在反方：**引擎从没承诺过这件事，所以杀不死是对的，是变异体写错了。**
三个 survivor 我都试着这么打，三个都没打倒。

#### 1.1 `cm-empty-frontier` —— 打不倒，而且原报告的论证还不够强

反方论点：`mine` 里写着 `best = frontier[0] if frontier else guard`，**引擎自己给空
frontier 留了兜底分支**，可见引擎认为空 frontier 是可能的；既然引擎自己都不排除，
不变式豁免它就是照着能力边界走，变异体越界。

我去证伪这个反方论点，结果反方输了。构造性论证〔读码〕：

* `enumerate_frontier` 的候选集 `consistent = {a : positives & ~masks[a] == 0}`
  （对每个正例都真的原子）。一个规则组按 `(action, effect.key())` 分组，**组内所有
  正例共享同一个 action A**。`build_vocabulary` 无条件放入 8 个 act 原子
  （4 方向 × 正负）。若 `A ∈ DIRECTIONS`，`act==A` 对每个正例为真；若不是，四个
  `!act==D` 全部对每个正例为真。**所以 `consistent` 恒非空。**
* 设 CEGIS 最小化后的守卫长 `L`。`L > 3` ⇒ `truncated = True`（就是 truncated 的
  定义）。`L ≤ 3` ⇒ `size = min(max(L,1),3) ≥ L`，而 `enumerate_frontier` 从
  size 1 遍历到 max_size，`guard ⊆ consistent` 且 `_mask_of(guard) & negatives == 0`，
  所以 guard 本身（或它的某个更小子集）必然进 `found`。
* `L == 0` ⇒ negatives 为空 ⇒ size=1 的任意 consistent 原子都合格，而 consistent 非空。

结论：**"未截断 ⇒ frontier 非空"不是经验观察，是定理。** 那个 `if frontier else guard`
是死分支，不是能力边界的自陈。原报告只说"实测 120 世界 0 例"，这比它能说的弱。

〔实测〕120 世界 / 115 可挖掘 / **552 条 ground 规则：truncated 0 条，未截断且
frontier 为空 0 条**。与定理一致，补上的那条检查零误报。

#### 1.2 `cm-truncation-alibi` —— 打不倒

反方论点有两个，都不成立：

* "`BUGS.md` 明文豁免了 frontier 完备性" —— 豁免的原文是"no cegis frontier
  completeness **beyond `rule.frontier_max_size`**"，讲的是 *size 界*。相信引擎自报的
  `frontier_truncated` 是另一件事，没有任何文档承诺过。原报告已经区分了，我核对
  `BUGS.md`「What was deliberately not asserted」六条，确认没有第二条能豁免它。
* "flag 是引擎的内部状态，外部不可验证" —— 不成立。`truncated = len(guard) >
  max_frontier_size`，而 `guard` 原样存在 `rule.cegis_guard` 上（`miner.py:350`），
  `MAX_FRONTIER_SIZE` 是模块常量。**可验证，只是没人验。**

**一处必须记的限定（原报告没写）**：拟补的
`rule.frontier_truncated == (len(rule.cegis_guard) > engine.MAX_FRONTIER_SIZE)`
把模块常量写死了，而 `mine(transitions, max_frontier_size=...)` 是**带参数的**。
`props/cegis_miner.py:_mine` 走默认值所以现在成立；任何调用方改了这个参数，这条
新不变式就会误报。正确写法应该拿 `rule.frontier_max_size` 反推，或者显式记下
"本电池只判定默认参数下的挖掘"。

#### 1.3 `cm-shrink-lifted-support` —— 缺陷打不倒，措辞要削弱

缺陷本身成立〔读码 + 实测〕：`lift()` 把 support 和 applicable 都建成成员的并集
（`miner.py:245-246`），每条成员满足 applicable == support，所以 lifted 也必然
n/n；〔实测〕120 世界 78 条 lifted 规则，`set(applicable) != set(support)` 的是
**0 条**。而 `candidates()` 发的是 `all_rules`。砍掉一个下标 ⇒ 发布一条 coverage
为 (n-1)/n 的候选。这是真缺陷，反方无话。

**要削弱的是"全部无人审"**：`engine-rig/tests/test_cegis_miner.py:38` 有
`assert push.coverage == "%d/%d" % (n_moves, n_moves)`，而 `push` 的守卫是
`["act==?dir", "free(strip(?dir))"]`、`lifted_from` 四条——**它就是一条 lifted 规则，
而且被断言了 applicable == support**。所以正确的说法是：*lifted 规则在 Fixture A 上
被 engine-rig 自己的一条测试审过一次，在 fuzzlab 的 3000 世界语料上从未被审过*。
"从没被任何不变式审过"读起来像"这个引擎的这半边输出从来没人看过"，那是过头的。

补充一条对该发现**有利**的证据（原报告没查）：`tools/validate_candidates.py` 对
coverage 只校验 `<k>/<n>` 形状、分母非零、`k <= n`。**support 被砍成 (n-1)/n 是
合法 schema**，所以契约校验器也不会兜住它。

### 2. kill 是真检出吗

#### 2.1 有没有 `raised` 被算成 `violated`

**没有，结构上不可能**〔读码〕。`violated` 只由 `finding.violated()` 显式构造；
`run_invariants` 捕获的异常一律走 `finding.raised()`；`run_mutant` 的
`by_kind[VIOLATED]` 只收 `f.kind == VIOLATED`，`raised_only` 还额外做了差集。
13 个 kill 的 `raised_only` 全 0〔实测 JSON〕。这条打不倒。

#### 2.2 每个 kill 到底是"发现缺陷"还是"破坏了自洽簿记"

逐条看杀死它的那一行断言：

| kill | 断言的那一行 | 判决 |
|---|---|---|
| `cm-frontier-guard-inconsistent` → `frontier_guards_are_consistent` | `_fires_on(guard, transitions) != support`，用 `atoms.evaluate` 独立求值 | 真检出 |
| `cm-drop-frontier-guard` → `frontier_is_complete_to_size` | 穷举词表子集重算最小一致守卫，比对 frontier | 真检出 |
| `cm-inflate-applicable` → `applicable_equals_support` | 两个字段比较，但来自两条不同代码路径（`_mask_of(best,…)` vs `sorted(t.index for t in members)`） | 真检出 |
| `cm-weaken-ground-guard` / `cm-drop-rule` → `guards_partition_the_evidence` | 直接求值重算，不调引擎的 `guards_are_mutually_exclusive()` | 真检出 |
| `zs-flip-law-value` → `laws_hold_on_trajectory` | 用 oracle 编码重算逐态奇偶 | 真检出 |
| `zs-bump-difference-rank` → `rank_nullity` | 分支 1 与 `gf2.row_echelon` 独立算出的 true_rank 比 | 真检出 |
| `zs-drop-basis-vector` / `zs-add-bogus-basis-vector` → `rank_nullity` | **分支 2，`dimension != n_cols - difference_rank`** | **只是基数簿记** |

最后一行是我要削弱的：这两个变异体改的是 `len(basis)`，`rank_nullity` 能响**只因为
基数变了**。一个把某条基向量换成同样数量的错向量的真实缺陷，`rank_nullity`
一声不吭（只有 `law_space_is_complete` 会响）。所以 MUTATION.md 表里
"`zs-drop-basis-vector` → `law_space_is_complete`, `rank_nullity` ✓ both"读起来像
两条不变式独立确认，实际上第二条确认的是**同一个数**。`rank_nullity` 自身的
load-bearing 由 `zs-bump-difference-rank` 单独证成，那条没问题——但"both"这个
✓ 含金量比字面低。

#### 2.3 更要紧的：kill 全是构造性必然，所以那组数字测不了灵敏度

〔读码〕八个 cegis 变异体里，五个"会死"的 corrupt **在注入前就用不变式自己的
违反判据去搜注入点**：

* `_frontier_guard_inconsistent` 找的是 `_fires_on([atom], transitions) != support`
  的原子——这**逐字就是** `frontier_guards_are_consistent` 的违反条件；
* `_weaken_ground_guard` 找的是 `_fires_on(weaker) > support`，而多出来的那些
  transition 必然属于别的规则的 support（基线互斥），双认必然发生；
* `_inflate_applicable` 在基线 applicable == support 上加一个下标，必然不等；
* `_drop_rule` 删一条规则，它的 support 必然无人解释（基线互斥）。

也就是说 **29/29、16/16、首杀=1 是设计的结果，不是世界的性质**。它证明了"不变式
接线是通的"（这正是本轮要证的），但**不能**用来说"这些缺陷在任何非退化世界上都
成立，所以 500 世界是奢侈的"。partial 的§"逐不变式检出力"末段那个关于战役规模的
推论，前提不成立：要谈规模，需要的是"只在稀有世界形状上才致命"的变异体——partial
自己在"我不确定的"第 2 条里说了没写这种变异体，那么规模结论就不该在上面先说出口。
（这是同一份文档里前后不一致，不是新事实。）

#### 2.4 一处小的口径不符

`MUTATION.md` 说 `worlds_to_first_kill` 是"how many worlds had to be **generated**
before the first kill"，代码存的是 `first_kill[name] = evaluated`，即**被评估过的
世界数**，inert 世界不计。对 `cm-drop-frontier-guard` 这类 14/30 inert 的变异体，
两个口径能差一倍。〔实测〕本次恰好 world 0 就被杀，两个口径都等于 1，所以**数字没
错，只是文档的定义错了**。

### 3. 预注册的证据

**这个仓库里没有任何东西能证明 `expect_kill` 写在跑之前。**

* 〔实测〕`git status`：`fuzzlab/mutants/`、`fuzzlab/mutation.py`、`fuzzlab/MUTATION.md`、
  `fuzzlab/out/mutation.*.json`、整个 run 目录**全部未跟踪**，一个 commit 都没有。
  没有提交时序可诉诸。
* 〔实测〕mtime 方向是**一致但无力**的：
  `mutants/zero_space.py` 23:18:17 < `out/mutation.zero_space.json` 23:18:27；
  `mutants/cegis_miner.py` 23:25:11 < `out/mutation.cegis_miner.json` 23:25:34。
  目录里没有更晚被改过的目录文件。但这个证据挡不住它要挡的那件事：
  **"先跑一遍 → 看结果 → 改 expect_kill → 再跑一遍"产生的 mtime 顺序一模一样**，
  而且输出文件名固定、后一次覆盖前一次，早先的运行不留痕迹。
* 框架的 `__post_init__` 强制 `expect_kill` 非空——那是强制**存在**，不是强制**时序**。
  MUTATION.md 把它写成"the constructor refuses a mutant without it"作为控制手段之一，
  在时序这件事上它一点都不管用。

**按姊妹文档的标准评判**：`worldgen/qc/PREREGISTERED_MUTANTS.md` 对同样的处境写了
自陈——"this file was untracked when both were written, so there is no commit ordering
to appeal to and the only evidence for 'before' is this sentence. A reviewer should
read it as an assertion, not a proof."。**V10 这边没有等价的一句话。**
`MUTATION.md`「Three controls」第 1 条的写法（"is written before the driver runs"）
是**断言**，读起来却像**已建立的控制**。按这个仓库自己已经写下的标准，这里应当补一
句自陈，或者把三个 survivor 的预注册状态降格为"作者的陈述"。

**一处对预注册有利的旁证**（不构成时序证明，但值得记）：三个 survivor 在
`mutants/cegis_miner.py` 的模块 docstring 里被点名预测会活，并且**给出了逐条机制**
（`continue` 的两条分支、`rules` vs `all_rules`）。事后补写这种带机制的预测，
代价明显高于把 `expect_kill` 改一改；partial §"预测错的地方"也主动说明了
`expect_kill` 为什么在这三条上填的是"本应负责的那条不变式"。这是**行为证据**，
不是**记录证据**，不能替代后者。

### 4. inert 会计

这一点我推翻了一条，另有两条削弱。

#### 4.1 〔实测，推翻〕`survived` 不要求 `worlds_evaluated > 0`

`run_mutant` 里 `"survived": not any(kills.values())`，与 `evaluated` 无关。于是：

```
E4  一个 corrupt 永远抛 RuntimeError 的变异体
   eval=0 inert=25 survived=True     <-- headline 说 SURVIVED
   raised_only: {}
```

驱动器的终端行也打 `SURVIVED`，`main()` 的 `survivors` 计数也把它算进去。
`corrupt` 抛出的非 `_Inert` 异常穿过 `patched` → 属性函数崩 → `run_invariants`
记成 `raised` → 但 `record` 是空的 → 世界判 inert → `continue`，**那个 raised 被
整个丢掉**。也就是说：**注入代码本身写错，输出长得跟"电池完全没反应"一模一样。**

这正是 `MUTATION.md`「The harness has its own negative control」承诺挡住的那一种失效：
"if injection silently stopped working, every mutant would be reported as a survivor
and the output would read as a devastating result about the battery"。控制 2 挡住了
*repr 相同* 那条路径，没挡住 *corrupt 崩溃* 这条。

修法一行：`"survived": bool(evaluated) and not any(kills.values())`，或者对
`evaluated == 0` 的行直接打 `UNMEASURED` 而不是 `SURVIVED`。

#### 4.2 〔实测〕负控制测试断言了除标题以外的一切

`tests/test_mutation.py::test_a_mutant_that_changes_nothing_is_inert_and_not_a_survivor`
断言了 `worlds_evaluated == 0`、`worlds_inert == len(worlds)`、
`predicted_but_missed == ["rank_nullity"]`——**唯独没断言 `row["survived"] is False`**。
我跑了那个 noop 变异体：

```
noop mutant -> survived = True | evaluated = 0 | survived_all_detection = True
```

**测试名里的 "and not a survivor" 是假的**，而且它是这份负控制里最贴近 4.1 那个洞的
一条。这条测试现在的作用是把洞钉在原地。

#### 4.3 〔实测/读码〕inert 的三个来源被压成一个计数器

`worlds_inert` 同时包含：(a) corrupt 主动 `mut.inert(reason)`（有 reason，且被记进
`record`）；(b) 引擎在 corrupt 之前就抛异常（cegis 的 `NoSeparatingGuard` /
`Unminable`，`record` 空）；(c) corrupt 自己崩了（`record` 空，reason 丢失）。
只有 (a) 是设计意图。JSON 里只有一个 `worlds_inert` 整数，`record` 里的 `reason`
字段**从不出现在报告里**。partial 手工把 cegis 的 14 拆成"1 skipped + 13 无注入点"，
拆得对〔实测复核见下〕，但那是靠人重算，不是驱动器给的。

#### 4.4 〔实测〕`repr` 判据在这两个 seam 上没有误判

我怀疑的是 `repr(deepcopy(x)) != repr(x)`（含 id 型 repr 会让每个世界都被误判成
"changed"，从而把 inert 世界塞进分母、人为制造 survivor）。实测两个 seam 都为
`True`（相等），因为 `MiningResult`/`Rule`/`Effect`/`Transition`/`State`/`Atom`/
`ZeroSpaceResult`/`Law`/`Feature` 全是 dataclass，repr 按字段值。**这条打不倒。**
`touched()` 的覆盖也正确：`zs-contains-always-true` 影子化方法后 repr 不变，靠 MARK
进的分母，`test_touched_marks_a_change_repr_cannot_see` 钉住了它。

#### 4.5 〔读码〕`any(r["changed"])` 的聚合在这两个引擎上无害，但理由要写对

`module.check(world)` 跑 4 条不变式 ⇒ seam 被调 4 次 ⇒ `record` 有 4 条。
`any(...)` 把"四条里只要有一条被改到"算成整个世界 evaluated。**在这两个引擎上不会
失真**：两个 props 模块的每条不变式都用同一个参数 `world` 调 seam 一次，`_mine` /
`_analyse` 确定性，corrupt 每次拿到相同的 deepcopy，四条 record 必然一致。
但这是**这两个模块的性质，不是驱动器的保证**——任何 props 模块只要对不同不变式
用不同参数调 seam（例如按不变式裁剪世界），`any` 就会把"一条被注入"记成"四条都被
注入"，而 killed 是按不变式分别计的，分母就虚了。

#### 4.6 〔读码〕`args`/`kwargs` 没有被深拷贝

`applied()` 的注释说"The corruption works on a copy: an in-place edit of the engine's
own return value would leak into whatever else holds a reference to it"。只有**返回值**
被 deepcopy，`args`（`args[0]` 就是 world）原样传给 corrupt。一个改了 `args[0]` 的
corrupt 会污染同一世界后续三条不变式，且不留痕迹。本次 13 个变异体都没这么干
（我逐个读过），但注释承诺的隔离比实际强。

### 5. `rank_nullity` 第三分支

**推不翻，并且我把它加强了。**

我试了四条推翻路径〔实测 E1 + 读码〕：

1. **实例属性覆盖**：`r.dimension = 99` → `AttributeError: property 'dimension' of
   'ZeroSpaceResult' object has no setter`。property 是数据描述符，实例字典盖不住。
2. **子类**：`ZeroSpaceResult.__subclasses__()` 为 `[]`；`analyse()` 硬编码返回该类。
3. **两次读取之间 basis 被改**：`len(result.basis) != result.dimension` 是单表达式，
   左右两侧读同一个列表对象，中间没有回调、没有 `__len__` 副作用（`basis` 是 `list[int]`）。
4. **缓存**：不是 `functools.cached_property`，是普通 `@property`，每次现算。

唯一能让它为真的构造是：让 corrupt 返回一个**根本不是 `ZeroSpaceResult` 的鸭子对象**
（框架允许 corrupt 返回任意对象）。但那不再是"假设引擎返回了这个"——引擎无法返回
这种东西，因为 `dimension` 是派生的。所以 MUTATION.md 的措辞"false for every
possible input"严格说该是"for every possible **engine output**"，这是措辞而非结论。

**那句更狠的问题：它在 git 历史里有没有哪个版本是能红的？没有。**〔实测〕
`engine-rig/engines/zero_space/zerospace.py` 只有一个 commit（`b4f0b41`，M4），
那一版的 `dimension` 就已经是 `return len(self.basis)`；
`fuzzlab/props/zero_space.py` 只有一个 commit（`1845e26`，E4），那一版第 159 行
就是现在这行，且工作树未修改。**这条断言从出生那天起就是死的，从没有过能红的版本。**
MUTATION.md 把它归到 V11 census 的那个形状（"a verdict computed correctly and wired
to nothing"）是对的，而且这里比 census 的一般情形更彻底：不是后来失效，是从未生效。

### 6. lifted 规则无人审

**核心事实全部核实，成立。两处理由要削弱。**

〔读码〕核实链：
`cegis_miner/__init__.py:76-87` 的 `candidates()` 遍历 `result.all_rules`；
`MiningResult.all_rules` 是 `self.rules + self.lifted`（`miner.py:276-277`），是**超集**，
`rules` 与 `lifted` 不相交（lifted 是新构造的 `Rule` 对象）。
`props/cegis_miner.py` 四条不变式的循环分别在第 127、161、209、236 行，**全部是
`for rule in result.rules`**，没有一条碰 `all_rules` 或 `lifted`。

〔实测〕120 世界：115 可挖掘、5 Unminable、**0 NoSeparatingGuard**；ground 规则 552 条，
**lifted 规则 78 条**（66 个世界产出）。与 partial 的数字**逐个对上**。
把 `applicable_equals_support` 扩到 `all_rules`：78 条 lifted 里
`set(applicable) != set(support)` 为 **0** —— 零误报，partial 的这个实测我复现了。

**削弱一：不是"从没被任何东西审过"。** 见 §1.3——`engine-rig/tests/test_cegis_miner.py`
在 Fixture A 上断言了 lifted `push` 规则的 `coverage == n/n`。正确表述是"在
fuzzlab 的语料上、被 fuzzlab 的不变式，从未审过"。

**削弱二（更重要）：不扩另外三条不变式的理由，在 78 条里只对 25 条成立。**
partial 说"lifted 守卫里带 `?dir`，`atoms.evaluate` 会 `raise ValueError('?dir')`，
所以排除 lifted 是正确的作用域决定"。〔实测〕把三条不变式的求值逻辑对 78 条
lifted 规则跑一遍：

```
raise = 25   evaluate-but-mismatch(会产生假 violation) = 53   agree = 0
```

只有 25 条真的抛异常（那是 `free/in_bounds/clear(strip(?dir))` 走到
`strip_cells` 的 `raise ValueError(direction)`）。另外 53 条**不抛**——因为
`substitute_direction` 只替换 `arg == action` 的原子，`at(r,c)` 保持具体，而
`act==?dir` 在 `_evaluate_positive` 里走 `return action == arg`，对 `?dir` 安静地
返回 False。于是 `_fires_on` 得到**空集**，与 support 不等，
`frontier_guards_are_consistent` 会报 **53 条假 violation**。

所以：**结论（别把另外三条扩过去）不仅成立，而且比 partial 说的更紧急**——失败模式
的多数不是响亮的异常，是安静的假指控，正是 `README.md`/`BUGS.md` 反复点名的那个
失败模式。但 partial 给的**理由**在 53/78 上是错的，照它写下去的人会以为"扩过去
最多是崩，崩了就知道了"。要扩必须先把 `?dir` 代回具体方向（每个成员一次），
或者只扩纯字段比较的那一条。

## 我另外发现的问题

### N1（最重）`zero_space` 的 "5 变异体 0 survivor" 是选样结果，不是电池强度

`MUTATION.md` 的 zero_space 一节说 "4 invariants, 5 mutants, **0 survivors**"、
"All four `zero_space` invariants are load-bearing"。这两句都对，但它们被摆在
一起，读起来像"这个引擎的输出面已经被覆盖了"。**没有。**

`zero_space/__init__.py:31-45` 的 `candidates()` 遍历的是 **`result.laws`**，
一条 Law 一个候选，`to_payload` 还在每条上盖了 `space_dimension = result.dimension`。
而 `law_space_is_complete` 审的是 **`result.basis`**；`laws_hold_on_trajectory`
只审 `result.laws` 的**可靠性**（每条返回的 law 是否真守恒），**没有任何不变式审
`laws` 的完备性**。`analyse()` 里 `laws` 和 `basis` 由同一批向量
（`locals_ + globals_`）构造，所以 `|laws| == |basis|` 是引擎的构造性承诺
〔实测 25/25 世界成立〕。

于是我按框架规则写了第六个变异体（`claim` 引 `candidates()` 与 `analyse()`，
`expect_kill=("law_space_is_complete",)`），只做一件事：`result.laws = result.laws[1:]`，
**`basis` 一个字节不动**。〔实测，用的是驱动器本身，不是我自己的判定〕：

```
E3  zs-drop-law
   eval=25 inert=0 survived=True survived_all_detection=True
   killed: {}   raised: {}
```

**25 个世界全活，零 raised。** 引擎少发布了一条守恒律候选，同时在剩下每条候选上
继续盖着"空间维数 = n"的印章，四条不变式一声不吭。

这与 §6 的 cegis 发现是**同一个形状**：*被审的对象不是被发布的对象*。
`cegis_miner` 审 `rules` 而发布 `all_rules`；`zero_space` 审 `basis` 而发布 `laws`。
一个引擎里出现叫巧合，两个引擎里出现，那是这套电池的**系统性盲区**，应当在
`MUTATION.md` 里升格成一条跨引擎结论，并且对其余四个引擎逐个查
"`candidates()` 发的是哪个字段、不变式审的是哪个字段"。

修法：`law_space_is_complete` 里补一句
`{law.vector for law in result.laws} == set(result.basis)`（两侧都是引擎自己的字段，
但由不同代码路径产生，可证伪）；或把完备性检查改成对 `laws` 的向量集做。

### N2 run 目录没有 `MANIFEST.json`

`fuzzlab/runs/20260728T152000Z-V10-fuzz-mutation-power/` 下只有 `partials/`（五份
`.md`），没有 `MANIFEST.json`，也没有 `RUN_STATE.md`。`CLAUDE.md`「Provenance is
canonical」要求每次实验写 `runs/<id>/MANIFEST.json`（`prompt_id`/`branch`/
`base_commit`/`utc`）。同目录的前一轮 `runs/20260728T085448Z-E4-property-fuzz/`
是有 `MANIFEST.json` + `files.json` 的。
这条和 §3 叠加：既没有 commit，又没有 manifest，这一轮**在磁盘上没有任何时间锚点**。

### N3 报告口径：`survived_all_detection` 在 eval=0 时同样为真

`"survived_all_detection": not any(kills) and not any(raised_only)`——同 4.1，
一个从未被评估的变异体拿到的是最强的那个标签。三个 cegis survivor 的
`survived_all_detection: true` 是真的（eval 分别是 29/16/16），但这个字段本身
在 eval=0 时不可信，读 JSON 的人无法只靠它区分。

## 我打不倒的（以及为什么打不倒）

诚实记录：我按任务要求逐条尝试了反方论证，下面这些我没能推翻，理由不是"看起来
合理"，是查到了否定反方的具体证据。

1. **三个 cegis survivor 都是真缺陷，不是能力边界。** 我为每一个都构造了"引擎从没
   承诺过"的反方论证：空 frontier 有兜底分支所以引擎自认可能（被 §1.1 的构造性
   证明否掉——`consistent` 恒非空，那个兜底是死分支）；truncated 是内部状态不可验证
   （被 `rule.cegis_guard` 就挂在规则上否掉）；lifted 规则本来就不接受同样的审查
   （被 `lift()` 的构造 + 78/78 实测 + `candidates()` 发 `all_rules` 否掉）。
   **三条假阳性，一条都没找到。**
2. **`raised` 没有被算成 `violated`。** 三分法在代码里是结构性的，不是靠纪律维持的。
3. **`rank_nullity` 第三分支确实不可证伪**，而且比原报告说的更彻底：git 里没有过
   能红的版本。
4. **`repr` 判据在这两个 seam 上没有误判**，deepcopy 稳定性实测通过。
5. **partial 里所有可核对的数字我都复现了**：115/5/0（可挖掘/Unminable/NoSeparatingGuard）、
   78 条 lifted、0 条 applicable≠support、0 条 truncated、0 个同名 ground 规则、
   30 世界里 16 个有 lifted 规则 / 16 个有"未截断且 frontier≥2"的规则。
   partial 说"两个 16 是巧合、不是同一批世界"——〔实测〕这两个谓词在 29 个可挖掘
   世界上有 4 个不一致（115 世界上 66/66/交 61），**它是对的**，我本来是想抓这一条的。
6. **`cm-drop-frontier-guard` 与 `cm-truncation-alibi` 的差分设计**（同样注入 + 只加
   一个 flag，16/16 全杀 vs 0/16 全活）是干净的对照，免责机制被锁死在 flag 上，
   不靠读码推断。这是本轮方法上最扎实的一处，我没有可打的。

---

**附：本次跑过的东西**（脚本在系统临时目录，未落入仓库）
`E1` dimension 覆盖尝试 · `E2` deepcopy/repr 稳定性 · `E3` 新变异体 `zs-drop-law`
（走 `mutation.run_mutant`，25 世界）· `E4` corrupt 崩溃时的报告口径（25 世界）·
`E5` cegis 120 世界结构扫描 · `E6` 三条不变式扩到 lifted 的后果（78 条）·
`E7/E8` 两个"16"是否同一批世界 · noop 变异体的 `survived` 字段 ·
`python -m fuzzlab.mutation --mutant cm-drop-frontier-guard --worlds 30 -v`
（`--out` 指向临时目录，未覆盖 `fuzzlab/out/`）。
