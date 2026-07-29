# 引擎：cegis_miner

seam：`props/cegis_miner.py:_mine`。**四条不变式全部共用它**，没有一条绕开——每条
的第一句都是 `result, transitions, _split = _mine(world)`，之后只用
`atoms.evaluate` 自行重算，不再回引擎。所以一个 seam 覆盖整个模块。

seam 返回的是三元组 `(MiningResult, transitions, split)`，corrupt 拿到的是元组，
改的是元组里的 `MiningResult` 字段。八个变异体全部改字段，没有一个 shadow 方法，
因此不需要 `mut.touched`（顺带说明：元组是 immutable，`touched()` 在这个 seam 上
根本用不了，要 shadow 方法只能去改 `MiningResult` 的方法而不是 seam 的返回值本身）。

世界数：**30**（`python -m fuzzlab.mutation --engine cegis_miner --worlds 30`，
seed `0x00005eedc1e4f002`，engine-rig HEAD `baf1671`，全程 16 秒）。
基线：**干净**——没有出现 `BASELINE NOT CLEAN`，`baseline_dirty_worlds: 0`，
`worlds_confounded` 八个变异体全是 0。

## 逐不变式检出力

| 不变式 | 变异体 | 预注册命中？ | killed/eval | 首杀世界数 | inert | raised-only | skipped 变化 |
|---|---|---|---|---|---|---|---|
| frontier_guards_are_consistent | `cm-frontier-guard-inconsistent` (unsound) | ✅ 命中，且无意外命中 | 29/29 | **1** | 1 | 0 | 0（构造上不可能） |
| frontier_is_complete_to_size | `cm-drop-frontier-guard` (incomplete) | ✅ 命中 | 16/16 | **1** | 14 | 0 | 0 |
| frontier_is_complete_to_size | `cm-empty-frontier` (incomplete) | ❌ **survivor**（已预注册预测会活） | 0/29 | — | 1 | 0 | 0 |
| frontier_is_complete_to_size | `cm-truncation-alibi` (incomplete) | ❌ **survivor**（已预注册预测会活） | 0/16 | — | 14 | 0 | 0 |
| applicable_equals_support | `cm-inflate-applicable` (unsound) | ✅ 命中 | 29/29 | **1** | 1 | 0 | 0 |
| applicable_equals_support | `cm-shrink-lifted-support` (incomplete) | ❌ **survivor**（已预注册预测会活） | 0/16 | — | 14 | 0 | 0 |
| guards_partition_the_evidence | `cm-weaken-ground-guard` (unsound) | ✅ 命中（互斥分支） | 29/29 | **1** | 1 | 0 | 0 |
| guards_partition_the_evidence | `cm-drop-rule` (incomplete) | ✅ 命中（覆盖分支） | 29/29 | **1** | 1 | 0 | 0 |

五个预测会死的全死了，`predicted_but_missed` 为空；三个预测会活的全活了，
`unexpected_kills` 八个变异体**全部为空**——没有一个变异体打中它没瞄准的不变式。
四条不变式各自至少被一个变异体杀死过，`invariants_no_mutant_kills` 是空的：
**没有一条不变式是永远不会响的**。三个 survivor 的 `raised_only` 也全是 0，
即 `survived_all_detection: true`——不是"崩溃算抓到"，是完全没反应。

**首杀世界数全部是 1，杀死率全部是 100%（killed == eval）。** 这对战役规模是个
明确的结论：对这四条不变式已经写出的这几类缺陷，**30 个世界是奢侈的，500 个更是**；
标准战役的 500 世界不是靠这四条不变式的灵敏度正当化的。反过来说，500 的正当性只能
来自"世界形状的多样性"，而这次测量恰恰显示 gridworld 世界之间在这几条不变式眼里
几乎没有差别。

## skipped 的影响（本引擎专有）

**结论：这个 seam 上没有任何变异体能改变 skipped，一个也不能，这是构造性的。**

`NoSeparatingGuard` 和 `Unminable` 都在 `_mine` **内部**抛出，也就是在
`applied()` 的 `original(*args)` 里抛出；异常直接向上穿过 `patched`，`corrupt`
根本没被调用，`record` 保持为空，驱动器的 `if not any(r["changed"] ...)` 判定
这个世界 **inert**。所以：

* skipped 的世界被**排除在分母之外**，不会被冒充成"电池没抓到"——这个记账是对的；
* 但也意味着**检出力只在可挖掘的残余上被测过**。30 个世界里 1 个 skipped
  （八个变异体的 inert 都至少是 1，那 1 就是它）。放大到 120 个世界：
  **115 可挖掘 / 5 Unminable（4.2%）/ 0 NoSeparatingGuard**。
* 4.2% 与 `BUGS.md` B1 记的 20/500（4%）一致，成因也一致：两个分割算子都无法把
  世界叙述成 move/none。
* **B2（`NoSeparatingGuard`）在这个语料上 120 个世界一次都没触发。** 它在
  `_skip_no_guard` 里有专门的分支和专门的措辞，但这个 corpus 从没走到过那条分支。
  这不是缺陷，是覆盖率事实：`BUGS.md` 把 B1 和 B2 并列成两条能力边界，实测只有
  B1 是活的。

另外要注意 inert 的**第二个**来源，它和 skipped 完全不同、绝不能混：
`cm-drop-frontier-guard` / `cm-truncation-alibi` / `cm-shrink-lifted-support`
的 inert=14 = 1 个 skipped + 13 个"这个世界没有可注入的位置"。已独立核对：
30 个世界里恰好 **16 个**世界存在"未截断且 frontier ≥2 条"的规则，也恰好 **16 个**
世界存在 lifted 规则（两个 16 是巧合，不是同一批世界的同一个条件）。
29-16=13，账对得上。这三个变异体的分母是 16 而不是 29，是真的 16。

## 杀不死的变异体（逐个裁决）

### 1. `cm-empty-frontier` —— 裁决：(a) 不变式不够

把一条规则的 frontier 整个清空。29 个世界全部 survive，零 raised。

**引擎确实承诺过 frontier 非空**：`mine` 里 `size = min(max(len(cegis_guard), 1),
max_frontier_size)`，而 `cegis_guard` 本身就是一条 size ≤ size 的一致守卫，
`enumerate_frontier` 不可能返回空；`best = frontier[0] if frontier else guard`
只是个兜底。所以"未截断的规则 frontier 为空"是引擎的自相矛盾，不是能力边界。

**为什么没抓到**：`frontier_is_complete_to_size` 第一句就是
`if rule.frontier_truncated or not rule.frontier: continue`（props/cegis_miner.py:162），
frontier 为空的规则被明文豁免；而 `frontier_guards_are_consistent` 遍历
`rule.frontier`，空列表上是**空真**。两条 frontier 不变式一起对空 frontier 失明。

**怎么补**（一行）：把那句 `continue` 拆开，对 `not rule.frontier` 的情形，
在 `rule.frontier_truncated` 为假时判 violated——"未截断的规则必须有非空 frontier"。
实测支持：120 个世界里 `frontier_truncated` 为真的规则数是 **0**，所以这条新检查
在真实输出上不会误报。

### 2. `cm-truncation-alibi` —— 裁决：(a) 不变式不够，但优先级低于 1

和 `cm-drop-frontier-guard` **注入完全相同的缺陷**（丢掉同一条 frontier 守卫），
只多做一件事：把 `frontier_truncated` 置为 True。同样的 16 个世界：
不加这个 flag 是 16/16 全杀，加了这个 flag 是 0/16 全活。**差分把免责机制锁死在
这个 flag 上**，不需要靠读代码推断。

引擎对这个 flag 的定义是客观事实而非许可：`truncated = len(guard) > max_frontier_size`
（miner.py:mine）。而 `rule.cegis_guard` 就挂在规则上，`engine.MAX_FRONTIER_SIZE`
是模块常量——**这个 flag 是可验证的，只是没人验证**。

**怎么补**：加一条 `truncation_flag_is_earned`：
`rule.frontier_truncated == (len(rule.cegis_guard) > engine.MAX_FRONTIER_SIZE)`。
一个不肯自证的引擎就无法再用自己的 flag 把完备性检查关掉。

**必须同时说清楚的限制**：120 个世界里没有一条规则真的被截断，所以这条免责路径
在**真实**输出上目前不可达——只有"同时篡改 flag"的缺陷才走得到。这降低了它的
紧迫性，但不改变裁决：`BUGS.md` 明文写了"no cegis frontier completeness beyond
`rule.frontier_max_size`"是**故意不断言的**，那是关于 *size 界* 的；
"相信引擎自报的 truncated"是另一回事，没有任何文档承诺过它。两者不能混。

### 3. `cm-shrink-lifted-support` —— 裁决：(a) 不变式不够，且这是本次最实的发现

砍掉一条 lifted 规则 support 里最小的那个下标。16 个世界全部 survive。

**为什么这是真缺陷而不是越界指控**：`lift()` 把 support 和 applicable 都建成
成员规则的并集，而每条成员规则都满足 applicable == support，所以 lifted 规则的
`coverage` 也必然是 n/n；而 `cegis_miner/__init__.py:candidates()` 发出的是
**`result.all_rules`**——lifted 规则和 ground 规则一样会带着 coverage 写进
`candidates.jsonl`。所以一条 support 被砍过的 lifted 规则，是一条**已发布的、
带着错误 coverage 的候选**。

**为什么没抓到**：四条不变式全都遍历 `result.rules`，没有一条遍历 `all_rules` 或
`result.lifted`。**lifted 规则在这个电池里是完全未被判定的。**
115 个可挖掘世界产出 78 条 lifted 规则，全部无人审。

**怎么补，以及为什么只能补这一条**：把 `applicable_equals_support` 的循环从
`result.rules` 改成 `result.all_rules`。已实测这个扩展是安全的：120 个世界、
78 条 lifted 规则，`set(applicable) != set(support)` 的数量是 **0**，零误报。

**不要顺手把另外三条也扩过去。** lifted 规则的守卫里带 `?dir` 变量，
`atoms.evaluate` 遇到它会 `raise ValueError('?dir')`（`strip_cells` 不认识 `?dir`）——
我实测触发过。所以 `frontier_guards_are_consistent` / `frontier_is_complete_to_size` /
`guards_partition_the_evidence` 排除 lifted 是**正确的作用域决定**，不是漏洞；
只有纯字段比较的 `applicable_equals_support` 可以扩。我特意让这个变异体和
`cm-inflate-applicable` 是**同一种形状的缺陷、只换了容器**，就是为了让"活/死"的
差别只能归因于作用域，不能归因于缺陷形状。

## 构造上不可证伪的检查

逐条不变式看内部分支，找到两处，等级不同：

1. **`frontier_is_complete_to_size` 的两条 `continue` 分支**（上面 survivor 1、2）。
   这不是"永远相等"型的不可证伪，是"被显式豁免"型：进入这两个分支的规则完全不被
   检查，而分支条件由**引擎自己**（`frontier_truncated`）或引擎的输出形状
   （空 frontier）决定。一条不变式把是否检查自己的决定权交给被检查方，就是可以被
   一个缺陷关掉的检查。这是本引擎最实的构造性弱点。

2. **`guards_partition_the_evidence` 的互斥判据按 `rule.name` 而不是按规则对象**：
   `if index in claimed and claimed[index] != rule.name`（props/cegis_miner.py:238）。
   两条**同名**的 ground 规则互相重叠会被静默接受。`structural_name` 只由形状决定
   （`teleport`、`blocked_<action>`、`push_<dir>`、`move_<dir>`），`teleport` 不带
   action 后缀，原则上可以在一次挖掘里出现两次。
   **诚实的限定**：120 个世界里同名 ground 规则出现 **0** 次，所以这是**潜在**盲点，
   不是观测到的盲点；我没有为它写变异体，因为"引擎必须给规则起唯一名字"不是引擎
   承诺过的事，照那个写会是假阳性。补法是把 `claimed` 的值换成规则的身份
   （`id(rule)` 或下标），改动比新增不变式更小。

3. 反过来记一条**没有**问题的：`applicable_equals_support` 比较的两个字段虽然都出自
   引擎，但走的是**两条不同代码路径**（`applicable = _mask_of(best, masks, universe)`
   vs `support = sorted(t.index for t in members)`），不是同一行算出来的两个名字，
   所以它是可证伪的——`cm-inflate-applicable` 29/29 全杀就是证据。

## 预测错的地方

**没有。** 五个预测会死的全死（`predicted_but_missed` 全空），三个预注册预测会活的
全活，八个变异体的 `unexpected_kills` 全空。

需要说明的是三个 survivor 的 `expect_kill` 怎么填的：框架要求 `expect_kill` 非空，
而这三个变异体**我事前就预测没有任何现存不变式会抓到**。我的处理是：`expect_kill`
填"按职责本应覆盖它的那条不变式"（前两个是 `frontier_is_complete_to_size`，
第三个是 `applicable_equals_support`），并把"预计会活、以及为什么"写进
`mutants/cegis_miner.py` 的模块 docstring，跑之前就落盘。于是它们表现为
`predicted_but_missed`，正是这个字段该表达的意思。这一点我写在这里，是因为
"预测会死却填了会活的不变式"和"预测会活但框架逼我填一条"在 JSON 里长得一样，
只有 docstring 能区分——**读 JSON 的人如果不读 docstring，会误以为我预测错了三次**。

## 我不确定的 / 框架挡住我的地方

1. **`mut.touched()` 在这个 seam 上不可用。** seam 返回元组，`touched()` 对元组
   `setattr` 会失败并按设计抛 TypeError。本次八个变异体都是改字段所以没被挡住，
   但**任何想 shadow `MiningResult` 方法的变异体**（例如让
   `guards_are_mutually_exclusive()` 恒真）在这里都要绕：只能去 `touched()`
   元组里的 `MiningResult` 而不是返回值本身，而驱动器只看返回值上的 MARK。
   我没有改框架。影响范围有限，因为四条不变式一个引擎方法都不调
   （invariant 4 的 docstring 明说是故意不调的）。

2. **首杀=1、杀死率=100% 太整齐了**，整齐到值得怀疑分母。我核对过：
   `worlds_confounded` 全 0、基线干净、inert 计数和独立重算的世界数完全对上
   （16/16、13+1=14），所以我认为这是真的——这些缺陷在任何一个非退化的 gridworld
   世界上都成立。但它也意味着**这批变异体测不出"需要多少世界"这个问题**：
   要回答它得写"只在稀有世界形状上才致命"的变异体（例如只在有障碍物、
   或只在 teleport 规则上生效的注入），我这次没写。

3. **没有测 `lift()` 本身的正确性。** 我只动了 lifted 规则的 support 字段。
   `_normalise` / `substitute_direction` 的 alpha 等价判断是否正确，这次没碰，
   而它同样会进 `candidates.jsonl`。

4. **skipped 的 4.2% 是这个 seam 测不到的黑箱。** 那 5/120 个世界里，
   四条不变式对引擎的行为一无所知，而且**没有任何 seam 上的变异体能改变这一点**——
   要测那部分，注入点必须在 `mdl_segmenter` 一侧，不在这里。
