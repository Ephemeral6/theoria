# 引擎：fd_adapter

**本次跑在哪一档**：`stub-bfs` —— 两条独立证据，第二条比第一条重要得多。

1. 这台机器上没有 Fast Downward：`backends.find_fast_downward()` 返回 `None`。
2. **就算装了也还是 stub-bfs。** `props/fd_adapter.py` 调的是
   `engine.solve_parsed(domain, problem)`，不传 `domain_path=` / `problem_path=`，
   于是 `backends.choose_tier` 走第 3 条（`backends.py:184`，"an instance that
   exists only in memory forces `stub-bfs`"——FD 只读文件）。实测
   `choose_tier(on_disk=False)` → `('stub-bfs', None)`。30 个世界里凡是有 plan 的，
   `plan.backend` 全是 `stub-bfs`，`plan.optimal` 全是 `True`。

**这限定了什么**：本报告全部是关于**自带 BFS** 的检出力；两个 FD 档在 fuzzlab
里从未被执行过，所以本文任何一行都不能读成对 `fd-optimal` / `fd-satisficing` 的结论。
反过来这也**放宽**了一件事：`stub-bfs` 是被文档承诺 length-optimal 的
（`backends.py:9` 表、`search.py:4`），`Plan.optimal` 在它上面恒为 `True`
（`__init__.py:135`），所以本引擎写"计划不最优"的变异体是**真缺陷**、不是假阳性——
这句话若换到 `fd-satisficing` 档就完全反过来，而那一档在这里根本到不了。

seam：

* **选了 `_parsed`**（唯一活着的 seam），并且在它上面加了一个**视图分叉**
  `_EngineView`：**引擎**拿到被改过的实例，**oracle 拿到原封不动的真相**，靠栈上最内层
  `fuzzlab.props.fd_adapter` 帧的函数名区分（`_model` 是 oracle 入口，其余是不变式函数、
  也就是引擎路径）。方向是反着骗的：判官永远看真世界，错的是引擎。
* **`_solve` 没选，因为它是死代码。** `props/fd_adapter.py:84` 定义了它，
  **一次都没被调用**：三条不变式在 104 / 131 / 165 行直接调 `engine.solve_parsed`。
  对比 `props/lp_potential.py`，那里 `_solve` 是四个调用点的活 seam。后果是
  **整个"伪造答案"缺陷类注入不了**——掐掉 plan 最后一步、翻 `Plan.optimal`、
  返回一个凭空的动作串，全都没有落点。派单里建议的"plan 掐掉最后一步 /
  插入一个前置条件不满足的动作"因此**无法实现**，只能用"让引擎为一个稍有不同的实例作答"
  来近似。这是本次最重要的框架级发现，并用 `fd-solve-seam-is-dead` 实测成 `eval=0`。
* **`_model` 是 oracle 侧，我一个字节没动。** 在那里注入等于改判官的真相表，
  测出来的只是"判官能不能被骗"，不是"电池有没有检出力"。唯一一个碰到 oracle 的变异体是
  `fd-shared-grounder-blind-spot`，它**故意不分叉**——那是负对照，见下文。

世界数：**30**（`--worlds 30`，seed `0x00005eedc1e4f002`，engine-rig head `baf1671`，
全程 6 个变异体共 2.7 秒，规划器慢不是这里的瓶颈）。
基线：**干净**（`baseline_dirty_worlds = 0`，而且基线一条 finding 都没有——
没有 `violated`、没有 `raised`、**也没有 `skipped`**）。

## 逐不变式检出力

先给基线覆盖，下表才有分母意义（30 世界：sokoban 16 / abstract 14，`PddlError` 0 个）：

| 不变式 | 基线真正走到 oracle 的世界数 | 为什么其余的没走到 |
|---|---|---|
| `plan_replays_to_the_goal` | **6 / 30 (20%)** | 24 个世界无解，`plan is None` 时直接 `return []` |
| `optimal_rungs_are_optimal` | **6 / 30 (20%)** | 同上；`not plan.optimal` 这个闸门一次都没关过（恒 stub-bfs） |
| `no_plan_means_unsolvable` | **24 / 30 (80%)** | 6 个有解的世界直接 `return []` |

变异体表（`killed/eval` 中 eval 是驱动器的分母；"首杀世界数"是
`worlds_to_first_kill`，按已评估世界计；skipped 一列是相对基线的变化）：

| 不变式 | 变异体 | 预注册命中？ | killed/eval | 首杀世界数 | inert | raised-only | skipped 变化 |
|---|---|---|---|---|---|---|---|
| `plan_replays_to_the_goal` | `fd-engine-plans-for-a-weaker-goal` (UNSOUND) | ✅ 命中 | **17 / 30** | 1 | 0 | 0 | 0（基线 0，变异后 0） |
| `optimal_rungs_are_optimal` | `fd-engine-plans-for-a-weaker-goal` | ✅ 命中 | **17 / 30** | 1 | 0 | 0 | 0 |
| `optimal_rungs_are_optimal` | `fd-engine-overshoots-the-goal` (DEGRADED) | ✅ 命中，且**只**命中它 | **2 / 23** | 5 | 7 | 0 | 0 |
| `optimal_rungs_are_optimal` | `fd-engine-loses-operators` (DEGRADED) | ❌ **预测错**（见下） | 0 / 17 | — | 13 | 0 | 0 |
| `no_plan_means_unsolvable` | `fd-false-unsolvable` (UNSOUND) | ✅ 命中 | **6 / 30** | 5 | 0 | 0 | 0 |
| `no_plan_means_unsolvable` | `fd-engine-loses-operators` | ✅ 命中 | **1 / 17** | 3 | 13 | 0 | 0 |
| （seam 探针） | `fd-solve-seam-is-dead` (UNSOUND) | 预测 `eval=0`，✅ 命中 | **0 / 0** | — | **30** | 0 | 0 |
| （负对照） | `fd-shared-grounder-blind-spot` (INCOMPLETE) | 预测**杀不死**，✅ 命中 | **0 / 30** | — | 0 | 0 | 0 |

`invariants_no_mutant_kills = []`：三条不变式**每一条都被至少一个变异体杀死过**，
没有一条是纯装饰。`unexpected_kills` 全空，`raised_only` 全 0——**所有检出都是
`violated`（强意义），没有一次是靠崩溃**。

**分支级证据**（下面几条判决全靠它，用一次性脚本按 violation 的 detail 串分类，
未落盘进仓库）：

| 不变式内部分支 | 被触发次数（30 世界，全变异体合计） |
|---|---|
| `optimal_rungs_are_optimal`：`best is None`（引擎给了 plan，BFS 说无解） | 11 |
| `optimal_rungs_are_optimal`：`len(plan) != best`（**真的比长度**） | **8**（weaker-goal 6 + overshoot 2） |
| `optimal_rungs_are_optimal`：`not exhausted` → skipped | **0** |
| `plan_replays_to_the_goal`：`goal unmet` | 17 |
| `plan_replays_to_the_goal`：`no such action` / `preconditions unmet` / `negative pre` / `negative goal` | **0 / 0 / 0 / 0** |
| `no_plan_means_unsolvable`：`BFS finds a N-step plan` | 7 |
| `no_plan_means_unsolvable`：`not exhausted` → skipped | **0** |

**最有意思的一条已经落地**：`fd-engine-overshoots-the-goal` 让引擎多背一个初始原子当目标，
返回的计划**合法、用真算子、也真的达成了真目标**，只是比最优长 3 步，而且仍然自称 optimal。
`plan_replays_to_the_goal` 全程沉默（正确），`optimal_rungs_are_optimal` **杀掉了它**
（2 个世界，都是 LENGTH-MISMATCH 分支）。所以"optimal 档真的最优"**不是装饰品**，
它对"合法但更长"这个最难的形状有真检出力。

## 杀不死的变异体（逐个裁决，注意区分档位承诺）

**1. `fd-solve-seam-is-dead` —— `eval=0`，`inert=30`。判决：(b) 我注入不了，
   不是电池没看见。**
   这不是"变异体没被抓到"，是"变异体从未发生"。`props/fd_adapter.py:84` 的 `_solve`
   无人调用，patch 上去的函数一次也没进过。它证明了一件**关于电池架构**的事：
   `mutants/__init__.py` 的设计前提"每个 property 模块把引擎调用汇到一个私有 helper"
   对 fd_adapter **不成立**，因而"伪造答案"整类缺陷（掐 plan、翻 optimal 位、
   捏造动作串）在当前代码下**无法被变异分析覆盖**。
   **怎么补**：不是补不变式，是补 seam——把三条不变式里的
   `engine.solve_parsed(domain, problem)` 换成已经写好的 `_solve(world)`
   （它的实现与那三行等价），`_solve` 立刻变活，上面整类变异体就能注入了。
   我没有改它，因为派单红线是只交两个文件、不动 props/框架。**这是我最想提交的一条修改建议。**

**2. `fd-shared-grounder-blind-spot` —— `eval=30`，杀 0，且连一条 `raised` /
   `skipped` 都没多出来。判决：(a) 不变式不够，而且这是个**构造性盲区**，
   不是我的变异体写错了。**
   它注入的缺陷是真的、且明确违背引擎的白纸黑字承诺
   （`pddl.py:305` "every ground instance that could ever fire"）：grounder 少给算子，
   于是 `solve_parsed` 的 `None` 成了**假的不可解证明**，直接抵触
   `__init__.py:86-102`（"a run that only failed to find a plan stays a hard error
   on purpose"）。它杀不死的唯一原因是 `props/fd_adapter.py:_model`（第 66 行）
   **用引擎自己的 `ground_actions` 造 oracle 的真相表**，所以 grounder 一撒谎，
   判官和被告一起撒同一个谎，三条不变式全部安静。
   这正是 `props/fd_adapter.py:7-10` 自己写下的 residual risk，现在从"声明"变成了"实测"。
   **怎么补**：只有一条路——让 oracle 从 `world.problem_text` / `world.spec`
   自己算出算子集合，而不是从引擎的 grounder 拿。属于 fuzzlab 侧的工作量，
   等于给 blockworld 写一个独立的 grounder。在那之前，
   **"3000 世界 0 违反"对 fd_adapter 的解析/接地层是零信息**。

**3. `fd-engine-loses-operators` 对 `optimal_rungs_are_optimal` 杀不死
   （`predicted_but_missed`）。判决：(b) 我的变异体写错了——它压根没制造出
   "更长的合法计划"这个条件。**
   直接测过：30 世界里它非 inert 的 17 个中，只有 3 个世界本来就有解；其中 1 个被它
   变成了不可解（这一个被 `no_plan_means_unsolvable` 杀了），另外 2 个计划长度**丝毫未变**。
   **零个世界产生了更长的合法计划**（N=120 复测同样：1 个变不可解、3 个长度不变、0 个变长）。
   所以这是"变异体没响"，不是"不变式没看见"——把它当成检出力缺口报出去就是伪造发现。
   在 sokoban 里删掉一个 `adj` 原子，要么把实例切断、要么无关痛痒，很少刚好把最短路顶长。
   这也正是我为什么补了第二个 DEGRADED 变异体 `fd-engine-overshoots-the-goal`
   ——它按构造保证"合法但更长"，然后它**杀死了**那条不变式。

**没有一个变异体是因为"档位不承诺"而幸存的。** 我特意检查过这条假阳性风险：
两个 DEGRADED 变异体断言的都是 length-optimality，而本次全程 `stub-bfs`
（`backends.py:9` 明写 length-optimal: yes，`Plan.optimal=True`），承诺是实打实的。
`fd-satisficing` 不承诺最优——但它在 fuzzlab 里**一次都没跑过**，所以这里没有
"给不承诺最优的档写不最优变异体"这种错误存在的空间。

## 构造上不可证伪的检查

**A. `no_plan_means_unsolvable` —— 部分不可证伪，边界很精确。**
派单担心的是"它只在引擎说无解时才验，而验的方法又依赖引擎自己"。分两半看：

* **搜索这一半是独立的，可证伪**：`fuzzlab/oracles/search.optimal_plan_length`
  与 `engines/fd_adapter/search.py` 不共享一行代码，实测被杀 7 次（
  `fd-false-unsolvable` 6 次 + `fd-engine-loses-operators` 1 次）。
* **接地/解析这一半是共享的，不可证伪**：oracle 的动作集来自引擎的 `ground_actions`
  （`props/fd_adapter.py:66`）。凡是源头在 parser/grounder 的假不可解，
  两边同时失明——`fd-shared-grounder-blind-spot` 就是这个的实测证据（eval=30，杀 0）。

所以准确的说法不是"这条不变式不可能红"，而是：**它对 search 层的缺陷有检出力，
对 parse/ground 层的缺陷检出力恒为零。**

**B. `optimal_rungs_are_optimal` 的 `not plan.optimal` 闸门在 fuzzlab 里是死分支。**
恒为 stub-bfs ⇒ `plan.optimal` 恒 True ⇒ 那个"satisficing 档豁免"的 `return []`
一次都没走过。它的 docstring 写得很讲究（拒绝对不承诺的档提 bug），但在这个电池里
是**未被执行的代码**。真正的后果不是不变式弱，而是：**fuzzlab 从来没有测过任何一个
FD 档**，而 CLAUDE.md 说 FD 是"真连上了"的。要测到它，property 必须把 PDDL 落盘再调
`engine.solve()`（`choose_tier` 第 3 条决定的，这是关于后端的事实不是选择）。

**C. 两条 `skipped` 分支（`STATE_BUDGET` 60000 未耗尽）在 30 世界里从未触发，
`_skip_pddl` 也从未触发。** 基线 0 个 skipped，六个变异体跑完仍是 0 个 skipped。
所以派单担心的"变异体把世界推进 skipped、看起来像没抓到其实是没测"
**在本引擎本次没有发生**，一次都没有。这条我可以肯定地排除。

**D. `plan_replays_to_the_goal` 的验证器有 5 个失败分支，只有 1 个被打到过。**
`goal unmet` 17 次；`no such action` / `preconditions unmet` /
`negative preconditions violated` / `negative goal violated` 各 **0** 次。
这不是不可证伪，是**未测**：这四个分支正是"计划里插一个前置条件不满足的动作"
那类变异体该打的地方，而那类变异体正好卡在死掉的 `_solve` seam 上（发现 1）。
两个发现在这里合流：**修好 `_solve` 才能测到 `validate_plan` 的另外四个分支。**

## 预测错的地方

1. **`fd-engine-loses-operators` 我预注册了 `optimal_rungs_are_optimal` +
   `no_plan_means_unsolvable`，只中了后者。** 原因如上：它从未真的让计划变长。
   预测错的是"删掉最忙的静态原子会把最短路顶长"这个物理直觉，实际上在 sokoban
   小格子里它要么切断要么无感。照实记：`predicted_but_missed = ['optimal_rungs_are_optimal']`。
2. **补写的顺序必须交代清楚，否则就是"一直写到有一个响为止"。**
   `fd-engine-overshoots-the-goal` 是在看到上一条 0 杀之后才写的。写它的理由不是
   "换个变异体去撞不变式"，而是先测出**上一个变异体根本没产生 DEGRADED 条件**
   （0 个世界出现更长的合法计划），也就是那一格是"没测"而不是"没抓到"。
   新变异体的 `expect_kill=("optimal_rungs_are_optimal",)`（**只**这一条，
   并预测 `plan_replays_to_the_goal` 保持沉默）是在跑之前写死在文件里的，
   结果两条都对上了。这个先后顺序也写进了该变异体的 `description`，不是只写在这里。
3. **`fd-engine-plans-for-a-weaker-goal` 杀 `optimal_rungs_are_optimal` 17 次，
   但其中 11 次走的是 `best is None` 分支（引擎给了计划、BFS 说压根无解），
   只有 6 次是真的比长度。** 我预注册时以为主要是比长度。这不是错判命中与否，
   但如果只看 `killed=17` 就会高估"长度比较"这条路径被测到的程度——所以上面
   单列了分支表。
4. 其余三个（seam 探针 `eval=0`、负对照杀 0、`fd-false-unsolvable` 中 6 次）
   预测全中。

## 我不确定的 / 框架挡住我的地方

1. **`_EngineView` 的栈帧判别是本报告最需要复核的地方。** 它靠"栈上最内层
   `fuzzlab.props.fd_adapter` 帧的函数名是不是 `_model`"来决定给真相还是给谎话。
   在当前的 `props/fd_adapter.py` 上这是精确的（oracle 只从 `_model` 进，引擎只从三个
   不变式函数进），但它**依赖 props 的内部结构**：如果哪天有人把 `_model` 内联进不变式、
   或者让引擎调用穿过 `_model`，判别就会静默失效，变成"两边都被骗"——也就是退化成
   `fd-shared-grounder-blind-spot` 那种恒不杀的形态。找不到时默认给**真相**
   （保守方向：宁可少骗引擎，也不误骗判官）。如果复核认为这太取巧，
   正确的替代不是换判别方式，而是**把 `_solve` 接活**，那样根本不需要分叉。
2. **框架挡住我的第一处：`expect_kill` 无法表达"我预测它杀不死"。**
   `Mutant.__post_init__` 强制非空，可两个最有信息量的变异体
   （seam 探针、共享 grounder 负对照）的**真实预注册就是"杀不死 / eval=0"**。
   我的处理是把真预测写进 `description` 并在这里再说一遍，但驱动器的
   `predicted_but_missed` 会把它们记成"预测了却没中"，读 JSON 的人会误判。
   建议框架加一个 `expect_survive: bool` 或允许 `expect_kill=()` 配一个 `expect` 理由字段。
3. **框架挡住我的第二处：`inert` 只按 `repr` 变没变 / `touched` 判定，
   分不清"注入没发生"和"注入发生了但这个世界本来就测不到"。**
   `fd-false-unsolvable` 的 eval=30 里有 24 个是本来就无解的世界，那 24 个上它**不可能**
   被抓到（引擎说无解、真相也是无解）。分母被稀释了，`6/30` 的真实含义是 `6/6`——
   6 个有解世界全中。`fd-engine-loses-operators` 同理（17 个里只有 3 个本来有解）。
   我没有把这些 `raise mut.inert(...)`，因为在 corrupt 里判定可解性就得先解一遍，
   等于让变异体自己当规划器。表里的 eval 请按这一条读。
4. **30 个世界里有 24 个无解**（sokoban 生成器有意为之，见 `worlds/blockworld.py`
   docstring）。后果是两条与"有计划"相关的不变式每 30 个世界只拿到 6 个真样本。
   我没有改世界数分布——那是 worldgen 的事——但站在检出力角度，
   `plan_replays_to_the_goal` 和 `optimal_rungs_are_optimal` 在标准 500 世界 campaign
   里的**有效**样本大约是 100，不是 500。
5. **本报告一个字都不适用于 `fd-optimal` / `fd-satisficing`。** 再说一遍是因为
   CLAUDE.md 与 `backends.py` 都强调 FD 已接通，很容易被读成"fuzzlab 测过 FD"。
   没有。`choose_tier` 第 3 条决定了 fuzzlab 永远拿不到那两档，
   这本身可能值得作为一条独立的覆盖缺口上报给 verify 赛道。

## 落盘位置

* 变异体目录：`fuzzlab/mutants/fd_adapter.py`（6 个变异体）
* 驱动器 JSON：按纪律"只写两个文件"，`--out` 指到了会话 scratchpad
  （`mutation.fd_adapter.json`），**没有**写进 `fuzzlab/out/`。复现：

```bash
python -m fuzzlab.mutation --engine fd_adapter --worlds 30
```
