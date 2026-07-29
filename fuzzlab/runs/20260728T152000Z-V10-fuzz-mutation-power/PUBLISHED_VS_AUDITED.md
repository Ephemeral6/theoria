# 发布面 vs 审查面：六引擎

分析员：RES-3 / V-10 横切。工作树 `.worktrees/v10-fuzz-mutation-power/`，只读。
本文件是本次唯一写出的产物；未修改任何既有文件（含 `CONTRACTS/`）。

## 方法与计量单位

**单位 = payload 的叶字段路径**（`mdl.baseline_bits`、`events[].bits`、
`reach.status` 各算一个；纯容器节点 `events`、`mdl`、`effect` 不计）。

**发布面** 由两条独立途径得到并互相对账：

* 读码：`engine-rig/engines/<engine>/__init__.py` 的 `to_payload()` /
  `candidates()`，再顺着各 dataclass 的 `as_json()`；
* 实测：在 fuzzlab 自己的世界族上真跑 `candidates()`，把 payload 递归展平成叶路径
  （脚本写在系统临时目录，未落仓库）。两者一致。

**审查面** 不靠读码猜，用**属性访问记录器**实测：把 props 模块从引擎拿到的返回对象
包一层录制代理（只在进程内 patch，磁盘未动），跑 25 个世界，记录不变式**实际读到**
的每一个属性。没有被读到的属性，就是没有被任何不变式碰过。

> 一处必须说明的方法学边界：只在**违规分支**里被读的字段（例如
> `props/zero_space.py` 只在 `finding.violated(...)` 的 kwargs 里读 `law.scope`），
> 在干净跑批里不会出现在记录中。这正是应有的判定——**只用来描述失败、从不参与断言的
> 字段，不算审查**。凡属这一类，下文逐条注明。

`CONTRACTS/candidates_schema.md`（冻结 v0.1，只读）只规定信封
（`id/engine/kind/payload/evidence/status/timestamp`），payload 形状明确
"由各引擎 README 定义"。其可执行形式 `engine-rig/tools/validate_candidates.py`
的模块 docstring 写得很直白：**"says nothing about payload internals"**。
所以对本文的每一个字段，schema 校验的覆盖率是 **0**。

---

## 汇总

| 引擎 | 发布字段数 | 被不变式断言 | 仅作索引/门控/聚合 | 未被审 | 其中被下游代码机械消费 | 别处有审吗 |
|---|---|---|---|---|---|---|
| mdl_segmenter | 18 | 8 | 2 | **8** | 2（`color`, `shape`） | 6/8 在 engine-rig 单测（固定 fixture 钉值）；`segment_operator`、`events[].at` 无 |
| cegis_miner | 20 | 3 | 3 | **14** | 5（`effect.*`） | `effect.*`/`lifted_from`/`cegis_trace` 有 fixture 单测；`guard_cost_bits`/`frontier_truncated`/`cegis_iterations` 无 |
| zero_space | 11 | 3 | 3 | **5** | 0 | `scope`/`support`/`form`/`modulus` 有 fixture 单测；`coefficients` 无 |
| lp_potential | 26 | 4 | 8 | **14** | 0 | `admissibility_check[].admissible` 有 fixture 单测；`weights_float`/`goal_potentials`/`initial_potential`/`claim`/`rendering` 无 |
| fd_adapter | 7 | 3 | 0 | **4** | 0 | 4 个全部有 fixture 单测（`test_fd_adapter`/`test_fd_ladder`） |
| probe_frontier | 29 | 4 | 6 | **19** | 0 | executable 那 12 个有 `test_probe_reach.py`（sokoban 固定盘面）；`hypotheses[].weight`/`ranking[].n_classes` 无 |
| **合计** | **111** | **25** | **22** | **64** | **7** | — |

外加一条不能用字段计量的缺口：**`cegis_miner` 发布 `result.all_rules`，四条不变式
只遍历 `result.rules`**。实测 39 个可挖掘 gridworld：发布 224 条规则，其中
**35 条 lifted 规则（15.6%）从未进入任何不变式**——不是某个字段没被读，是整条候选
从头到尾没被看过一眼。

> **口径提醒（本报告的价值全在这两条区分上）**
> 1. "仅作索引/门控" **不算未审**，但也不算已审。`zero_space` 的
>    `result.features` 只用来建 `(cell,color)→bit` 索引（props 的 docstring 明说
>    这不是调用引擎的算法）；`cegis` 的 `frontier_truncated` 只用来**跳过**这条规则。
>    两者都单列。
> 2. "engine-rig 单测审了" **不等于** "fuzzlab 审了"。fuzzlab 的房规是
>    **oracle 不得调用它所审的引擎**，且跑随机世界批量；engine-rig 单测没有这条房规，
>    且几乎全是**单一 fixture 上的钉值断言**（`payload["color"] == 6`、
>    `payload["domain"] == "gripper"`）。所以下文"别处审了吗"一栏里写"有"的，
>    含义是"**这个字段在一个世界上被钉住了**"，不是"这个字段是对的"。

---

## 逐引擎详述

### mdl_segmenter

**发布面**（出处：`engine-rig/engines/mdl_segmenter/__init__.py:to_payload()` +
`segmenter.py:Event.as_json()`）— 18 个叶字段（实测，40 个 gridworld）：
`object_id, segment_operator, color, shape, cells, first_frame, anchors,`
`events[].t/.type/.track/.bits/.dy/.dx/.at, mdl.script_bits/.baseline_bits/.gain_bits/.ratio`

**审查面**（出处：`fuzzlab/props/mdl_segmenter.py`，四条不变式；实测属性读取，25 世界）

| 不变式 | 实际读到的引擎属性 |
|---|---|
| `masks_partition_the_foreground` | `Segmentation.tracks`, `Track.mask_at`, `Track.track_id` |
| `masks_follow_anchors` | `Track.masks`, `Track.anchors`, `Track.rel_cells`, `Track.track_id` |
| `events_agree_with_tracks` | `Segmentation.events`, `Event.t/.type/.track/.params`, `Track.anchors` |
| `script_bits_identity` | `Segmentation.script_bits/.declaration_bits/.n_frames`, `Event.bits`（**只求和**） |

记录器完整输出（25 世界）：`Segmentation` 只读到
`declaration_bits/events/n_frames/script_bits/tracks`；`Track` 只读到
`anchors/mask_at/masks/rel_cells/track_id`。
**`Track.color`、`Track.shape`、`Track.first_frame`、`Segmentation.baseline_bits`
零次读取。**

**差集**

| 字段 | 进手册？ | 错了会怎样 | 别处审了吗 | 证据 |
|---|---|---|---|---|
| `segment_operator` | 进（LLM 读整行） | **已经是错的**：`to_payload` 无条件写死 `"connected_components(4)+bipartite_common_fate"`，而 `Segmentation` 根本不记录跑过哪个算子。手册会把用 `split_by_color=True` 切出来的对象记成用色盲算子切的 | **没有**（`grep segment_operator engine-rig/tests` 零命中） | 实测：同一世界 `split=False` 出 23 条 track、`split=True` 出 6 条，两行 payload 的 `segment_operator` 字符串完全相同 |
| `color` | 进，且**被代码机械消费** | 手册按颜色给对象命名（`NAME_BY_COLOUR = {7: Button, 5: Door, 6: Cart}`），色号错 → 整个对象被叫错名字，之后所有引用它的律与规则都挂在错的名字上 | engine-rig 有：`test_mdl_segmenter.py:26`（`track.color == CART_COLOR`）、`:180`（`payload["color"] == 6`）。均为单 fixture 钉值 | `cold-start-a0/pipeline/concept_account.py:226` `payload.get("color")` → `name_by_colour.get(colour)` |
| `shape` | 进，且**被代码机械消费** | 被拿去算 declaration bits，错了整条 MDL 账目错 | `test_mdl_segmenter.py:27`（单 fixture） | `concept_account.py:147-148` `payload["shape"][0]`, `[1]` |
| `first_frame` | 进 | 对象"何时出现"记错；appear 时刻的因果推断跟着错 | `test_mdl_segmenter.py:163`（单 fixture） | 读码 |
| `events[].at` | 进 | `appear` 事件的位置。`events_agree_with_tracks` 只核对 `move` 的 `dy/dx`，appear 只核对"有没有这个 type"，位置从不核对 | 没有找到 | 读码 `props/mdl_segmenter.py:154-166`（`if event.type != "move": continue`） |
| `mdl.baseline_bits` | 进 | 压缩率的分母。膨胀它 → `gain_bits`、`ratio` 一起假高 → 手册把一个不划算的对象假设当成划算的 | **engine-rig 有，且是实审**：`test_mdl_segmenter.py:99` `test_baseline_is_computed_from_the_actual_pixel_diffs` 从实际像素差重算。注意它复用引擎自己的 `CostModel`，所以审的是**逐帧求和**，不是单帧定价 | 读码 + 记录器零命中 |
| `mdl.gain_bits` | 进 | 同上（= baseline − script） | `test_mdl_segmenter.py:182` 只断言 `> 0`（符号） | 读码 |
| `mdl.ratio` | 进 | 同上 | `:88` 断言 `<= 0.5`（单 fixture） | 读码 |

`events[].bits` 单列：**只以 Σ 形式被读**（`script_bits_identity`）。对"单项错、总和同幅错"
构造上封闭——把某条事件的 bits 减 3、另一条加 3，这条不变式永远不动。
`object_id` 单列：只当身份键用（把 mask/event 归到某条 track），不被断言。

---

### cegis_miner

**发布面**（出处：`engines/cegis_miner/__init__.py:candidates()` → `to_payload()`
→ `miner.py:Rule.as_json()` + `Effect.as_json()`）— 20 个叶字段（实测）：
`name, action, guard, guard_cost_bits, effect.type/.dy/.dx/.to/.direction,`
`frontier, frontier_size, frontier_max_size, frontier_truncated, cegis_guard,`
`cegis_iterations, cegis_trace[].iteration/.added/.admitted_before/.counterexample, lifted_from`

**审查面**（`fuzzlab/props/cegis_miner.py`，四条不变式）

记录器完整输出（25 世界）：`MiningResult` **只读到 `.rules`**；`Rule` 只读到
`applicable / frontier / frontier_max_size / frontier_truncated / guard / name / support`。

| 不变式 | 读了什么 |
|---|---|
| `frontier_guards_are_consistent` | `rules[].support`, `rules[].frontier`（直接 evaluate，断言 fires == support） |
| `frontier_is_complete_to_size` | `rules[].frontier`, `.frontier_max_size`（当**枚举上界**用）, `.frontier_truncated`（当**跳过门控**用）, `.support` |
| `applicable_equals_support` | `rules[].applicable`, `.support` |
| `guards_partition_the_evidence` | `rules[].guard`（直接 evaluate）, `.name`（当身份键用） |

**`MiningResult.lifted` / `.all_rules` 一次也没被读。**

**差集**

| 字段 | 进手册？ | 错了会怎样 | 别处审了吗 | 证据 |
|---|---|---|---|---|
| **整个 `lifted` 规则类**（非字段） | 进，**这是手册里最想要的那一类**（`push(?dir)` 这种提升过的通用规则，正是 LLM 要写进 playbook 的东西） | lifted 规则的 `support` 是各成员 support 的并集、`guard` 是模板的 guard 做 `?dir` 代换。代换错、合并错、把两条本不同构的规则并成一条——四条不变式全都不会响 | engine-rig `test_cegis_miner.py:39` 只断言 `push.lifted_from == [四个方向]`，单 fixture | 实测 39 世界：ground 189 + lifted 35 = 发布 224，审查 189。`__init__.py:86` `for rule in result.all_rules` vs `props:127,161,209,236` `for rule in result.rules` |
| `effect.type/.dy/.dx/.to/.direction` | 进，且**被代码机械消费** | **本引擎最严重的一条**：规则说"发生了什么"。四条不变式全部在审 guard（**什么时候**触发），没有一条把 `effect` 和 transition 实际发生的效果比对过。guard 全对、effect 全错的规则集能干净通过整条电池，然后作为"世界的因果律"进手册 | engine-rig 有：`test_cegis_miner.py:72` `(rule.effect.dy, rule.effect.dx) == (dy, dx)`、`:35`、`:48-51`。单 fixture（cart world） | 记录器：`Rule.effect` 零命中；`props/cegis_miner.py` 全文无 `effect`。消费者：`cold-start-a0/prime/probe_runner.py:72` `rule_payload["effect"]` |
| `action` | 进 | 规则挂在错的动作上 | 间接（guard 里有 `act==UP` 这样的原子，但那是 `guard` 字段不是 `action` 字段） | 记录器零命中 |
| `guard_cost_bits` | 进 | MDL 口径下"这条规则多贵"，LLM 用它做取舍 | **没有**（tests 零命中） | 读码 |
| `cegis_guard` | 进 | CEGIS 收敛到的那个 guard，与 `frontier` 可能不一致而无人比对 | 部分（`test_the_cegis_guard_itself_separates_its_effect_class`） | 记录器零命中 |
| `cegis_iterations` + `cegis_trace[].iteration/.added/.admitted_before/.counterexample` | 进 | 推导轨迹。伪造它会让一条其实靠猜得到的 guard 看起来是被反例逼出来的——这是**证据强度**的谎，比结论的谎更难发现 | `cegis_trace` 在 `test_cegis_miner.py` 有命中，单 fixture | 记录器零命中 |
| `lifted_from` | 进 | 提升规则的来源清单错 → 溯源断裂 | `:39`（单 fixture） | 记录器零命中 |

`frontier_max_size` / `frontier_truncated` / `name` 单列为**门控与索引**：
`frontier_truncated` 尤其值得点名——`props:162` 是
`if rule.frontier_truncated or not rule.frontier: continue`，
即**这个字段一旦为真，`frontier_is_complete_to_size` 就整条静音**。
它是被读了，但读它的效果是关掉审查，不是审查它。

---

### zero_space

**发布面**（`engines/zero_space/__init__.py:to_payload()` → `zerospace.py:Law.as_json()`
再加 `space_dimension` / `difference_rank`）— 11 个叶字段（实测）：
`form, modulus, features[].cell, features[].color, coefficients, support, value,`
`scope, rendering, space_dimension, difference_rank`

**审查面**（`fuzzlab/props/zero_space.py`，四条不变式，oracle 是独立的
`fuzzlab/oracles/gf2.py`）

记录器输出（25 世界）：`ZeroSpaceResult` 读到
`basis / contains / difference_rank / dimension / features / laws`；
`Law` 只读到 `.vector` 与 `.value`；`Feature` 只读到 `.cell` 与 `.color`。

| 不变式 | 读了什么 |
|---|---|
| `laws_hold_on_trajectory` | `laws[].vector`, `laws[].value` — 断言 |
| `law_space_is_complete` | `basis`, `features`（索引） — 断言 |
| `rank_nullity` | `difference_rank`, `dimension`, `len(basis)` — 断言 |
| `membership_agrees` | `contains()`, `basis` — 断言 |

`features[].cell/.color` 归入**仅作索引**：props 的 docstring 已经把这条讲明白了
——"读引擎的 feature 列表不是调用它的算法，两套实现必须共享坐标系才可比"。
`coefficients` 归入**间接**：它是 `gf2.to_bits(self.vector, n)`，而 `vector` 被完整断言；
未被审的只是这一步编码本身。

**差集**

| 字段 | 进手册？ | 错了会怎样 | 别处审了吗 | 证据 |
|---|---|---|---|---|
| `scope` | 进 | `"global"` vs `"cell_local"`。把一条只在单格成立的守恒律标成全局守恒律，手册会把它当成整盘的不变量用；这是**把局部真理升格为普遍律**，是最典型的会让 LLM 做错推理的错法 | engine-rig `test_zero_space.py:155` 按 `scope=="global"` 过滤并断言恰好 1 条（单 fixture）；`cold-start-a0` 只发布 `zs.global_laws()`，靠的正是这个字段 | 记录器：`Law.scope` 只出现在 `finding.violated(...)` 的 kwargs 里，干净跑批零读取 |
| `support` | 进 | 律的人类可读支撑集（`"R@3"` 这类名字）。手册引用的就是这些名字 | `test_zero_space.py:161` `sorted(payload["support"]) == ...`（单 fixture） | 同上，只在失败消息里 |
| `rendering` | 进 | `"(#R) mod 2 = 0"` 这句话就是 LLM 直接抄进手册的那一行。它和 `coefficients`/`value` 不一致，无人发现 | `test_integration.py:98` 断言等于固定串（单 fixture） | 记录器零读取 |
| `form` / `modulus` | 进 | 常量字面量，只能因改代码而错 | `test_zero_space.py:158-159` | 读码 |

---

### lp_potential

**发布面**（`engines/lp_potential/__init__.py:candidates()`，两条候选）
— 26 个叶字段（实测，40 个 jumpgraph，15 个出证书）：

*invariant*（15）：`form, weights, weights_float, initial, initial_potential,`
`goal_states, goal_potentials{}, margin, max_decrease, conditions.inv_init/.inv_closed/.goal_break,`
`claim, rendering, move_instances`
*heuristic*（11）：`form, weights, max_decrease, goal_states, formula, admissible,`
`rendering, admissibility_check[].state/.h/.true_distance/.admissible`

**审查面**（`fuzzlab/props/lp_potential.py`，oracle 是独立 BFS `fuzzlab/oracles/search.py`）

记录器输出：`Certificate` 只读到 `goal_states / initial / margin / moves / weights`；
`Move` 只读到 `src / over / dst`；**`Heuristic` 只读到 `.value`（方法）**——
heuristic payload 上的 11 个字段，一个都没被当字段读过。

| 不变式 | 读了什么 |
|---|---|
| `certificate_implies_unreachable` | `cert`（存在性）, `initial` — 断言（与 BFS 对质） |
| `three_conditions_hold` | `weights`, `moves[].src/.over/.dst`, `initial`, `goal_states`, `margin` — 用精确 Fraction **独立重算** inv_closed / goal_break |
| `heuristic_is_admissible` | `heuristic.value(s)` — 对全状态断言 h ≤ 真距离 |
| `infinite_means_unreachable` | `heuristic.value(s)` — 断言 inf ⇒ 真不可达 |

这里要给引擎一个公道：**事实层面审得比字段层面厚**。`conditions.inv_closed` /
`.goal_break` 这两个布尔从未被比对，但它们声称的事实被独立重算了；`admissible: true`
这个布尔也没被比对，但它声称的事实被全状态扫过。这类我记作**事实等价审**，
不计入未审。真正的未审是下面这些——它们声称的东西**没有任何地方重算过**。

**差集**

| 字段 | 进手册？ | 错了会怎样 | 别处审了吗 | 证据 |
|---|---|---|---|---|
| `weights_float` | 进 | 与精确有理 `weights` 并排发布的浮点近似。两者不一致，手册就同时拿到两套互相矛盾的权重，而 Lean 那一路只会用一套 | **没有**（tests 零命中） | 记录器零读取 |
| `initial_potential` | 进 | 势函数在初始态的值。它是"目标势 > 初始势"这个论证的**左端**，写错就是把论证写反了还看不出来 | 没有（`test_interop.py:133` 那条是另一个产物 `certificate_export` 文档的键名存在性检查，不是本 payload） | 记录器零读取 |
| `goal_potentials{}` | 进 | 同上，右端 | 没有 | 记录器零读取 |
| `move_instances` | 进 | `[m.name() for m in cert.moves]`。props 审了 move 的**几何**（src/over/dst），没审这些**名字**——名字错则手册里的招式清单与几何对不上 | 没有 | 记录器：`Move.name` 零命中，`.src/.over/.dst` 各 102 次 |
| `claim` / `rendering` | 进 | `"goal unreachable from 0111"` 与那一整句自然语言解释——**这是 LLM 抄进手册的那句话本身** | 没有 | 记录器零读取 |
| `conditions.inv_init` | 进 | props 明说不查：它是 `potential(init) <= potential(init)`，重言式 | — | props docstring（文档化的刻意不查） |
| heuristic `form/formula/rendering` | 进 | `formula` 是启发式的定义式。定义式写错而 `value()` 是对的 → 手册记的启发式和引擎跑的启发式是两个东西 | 没有 | 记录器零读取 |
| `admissibility_check[].state/.h/.true_distance/.admissible` | 进 | 整张"h vs 真距离"对照表。**`true_distance` 来自 `graph["distance_to_goal"]`，即生成器自己的预算表**——而 props 的 docstring 明确写着不信生成器的断言（"A fuzz battery that trusts the generator's asserted truth inherits whatever the generator got wrong"）。所以这张发布出去的表，用的正是 fuzzlab 拒绝相信的那个来源 | `test_lp_potential.py:186` `all(row["admissible"] ...)`（单 fixture） | 读码 `potential.py:265-282` + 记录器零读取 |

---

### fd_adapter

**发布面**（`engines/fd_adapter/__init__.py:to_payload()` → `Plan.as_json()`）— 7 个：
`domain, problem, backend, search, optimal, length, actions`

**审查面**（`fuzzlab/props/fd_adapter.py`，**三**条不变式；oracle 是独立
grounded-STRIPS BFS，但**共用引擎的 PDDL parser**，props docstring 已把这条残余风险写明）

记录器输出（25 blockworld）：`Plan` **只读到 `.actions`（16 次）与 `.optimal`（8 次）**。

| 不变式 | 读了什么 |
|---|---|
| `plan_replays_to_the_goal` | `plan.actions` — 断言逐步可执行且到达目标 |
| `optimal_rungs_are_optimal` | `plan.optimal`（门控）+ `plan.actions` — 仅当 `optimal` 为真时断言长度 == BFS 最优 |
| `no_plan_means_unsolvable` | `plan is None` — 断言 BFS 也找不到 |

`length` 记作已审：它就是 `len(self.actions)`，props 算的也是 `len(plan.actions)`，同源。

**差集**

| 字段 | 进手册？ | 错了会怎样 | 别处审了吗 | 证据 |
|---|---|---|---|---|
| `backend` | 进 | 哪一级梯子出的答案。这是 `optimal` 那个布尔的**唯一溯源**——引擎 docstring 自己说"a length that came from a satisficing planner cannot be mistaken for an optimum"，靠的就是这个字段诚实 | engine-rig `test_fd_adapter.py:198` `payload["backend"] in backends.TIERS`（只查枚举成员，不查是不是**这次真跑的**那一级）、`test_fd_ladder.py` | 记录器零读取；props 只在 `violated(...)` kwargs 里带上它 |
| `search` | 进 | 那一级实际跑的搜索配置（`"bfs"` / FD 的 config 串）。错了就无法复现 | `test_fd_adapter.py:199` `== "bfs"`（单 fixture）、`test_fd_ladder.py` | 同上 |
| `domain` / `problem` | 进 | 这个计划是给哪个问题的。错了 → 手册把 A 问题的解挂到 B 问题上 | `test_fd_adapter.py:214` `== "gripper"`（单 fixture） | 记录器零读取 |

`optimal == False` 的情形不被断言——这是**文档化的刻意留白**（satisficing 那一级
本来就不承诺最优），不计为缺口。

---

### probe_frontier

**发布面**：这个引擎有**两种 payload**。

*hypothetical*（`to_payload()`，17 个叶字段）：
`action, entropy_bits, value_bits_per_cost, cost, n_hypotheses,`
`hypotheses[].id/.description/.weight, partition, state, rendering,`
`ranking[].action/.entropy_bits/.cost/.value_bits_per_cost/.n_classes/.partition`

*executable*（`executable_payload()`，在上面基础上再加 12 个）：
`configuration, tier, setup_cost, path_cost, verdict,`
`reach.status/.problem/.goal/.plan/.length/.expansions/.backend`

**审查面**（`fuzzlab/props/probe_frontier.py`，四条不变式，family = `hypset`）

记录器输出（25 hypset）：`ProbeValue` 只读到 `action / cost / entropy / splits / value`。

| 不变式 | 读了什么 |
|---|---|
| `partition_matches_truth` | 调 `engine.partition_for(...)`，与世界自带的观测表比对 — 断言 |
| `entropy_matches_bruteforce` | `rank_probes()[].entropy` — 与独立熵计算比对，断言 |
| `ranking_is_sound` | `[].action`（完备性，断言）+ `[].value/.entropy/.cost`（只作排序键） |
| `splits_flag_is_honest` | `[].splits` — 断言（但 `splits` 不是 payload 字段，它只决定发不发） |

`partition` / `ranking[].partition` 记作**间接已审**：读码确认
`probe_value()` 构造 `ProbeValue.partition` 用的就是 `partition_for()`，
而 `partition_for` 被逐动作对着真值表断言过。

`cost` / `value_bits_per_cost` / `ranking[].cost` / `ranking[].value_bits_per_cost`
单列为**只作排序键**：`ranking_is_sound` 读它们，只断言
`(-value, -entropy, cost, action)` 这个元组序列是有序的——**一个整体系统性错误的
cost（比如永远返回 1.0）照样有序**。没有任何不变式把 `cost` 与
`world.cost_map()` 比对过。

**差集**

| 字段 | 进手册？ | 错了会怎样 | 别处审了吗 | 证据 |
|---|---|---|---|---|
| **executable 的 12 个**（`tier, verdict, reach.status/.plan/.length/.expansions/.backend, configuration, setup_cost, path_cost, reach.problem/.goal`） | 进 | **fuzzlab 对这条路径的覆盖是零**：`hypset` 世界族没有 planner，props 从不调 `design()` / `run_with_planner()`。而 `verdict` / `reach.status` 正是"这个实验到底能不能做"的答案，`reach.plan` 是去做它的那串动作。错了 → 手册收录一个物理上做不到的实验，或反过来丢掉一个能做的 | engine-rig **有，且相当实**：`test_probe_reach.py` 对 sokoban 固定盘面逐条钉 `tier/reach.status/reach.length/cost/value`，`:84` 还把 `reach.plan` 交给 `fd_adapter.validate_plan` 验过 | 记录器：`ExecutableProbe` 类在 props 全流程零出现；`props/probe_frontier.py` 全文无 `design`/`reach`/`tier` |
| `n_hypotheses` | 进 | 这条探针在几个假设之间做区分——熵的语义全靠它 | `test_probe_frontier.py:206`（单 fixture） | 记录器零读取 |
| `hypotheses[].id/.description/.weight` | 进 | 发布出去的假设清单。`description`（`"act==UP AND free(strip(UP))"`）是 LLM 直接读的那句；`weight` 是熵的权重，篡改它可以让一条无用探针看起来信息量最高 | `.description` 在 `test_probe_frontier.py:162-163` 有子串断言；`.weight` **没有** | 记录器零读取（oracle 的权重取自 `world.hypotheses()`，不是取自 payload） |
| `ranking[].n_classes` | 进 | 分类数与 `partition` 不一致而无人发现 | 没有 | 记录器零读取 |
| `state` / `rendering` | 进 | `rendering` 是那句 `"probe UP: it splits 2 hypotheses into 2 outcome classes (1.000 bits)"`——句子里的数字与同一 payload 里的字段不符，没有任何检查会响 | `test_probe_frontier.py:209` 只查 `state`（单 fixture） | 记录器零读取 |

---

## 一条越界发现（不在六引擎清单内，但同一形状且更糟）

`CONTRACTS/candidates_schema.md` 的 `engine` 枚举只有六个名字，所以另外两个引擎
**借名发布**：

```
16 行  engine="fd_adapter"   payload.producer="deadlock_carver"  form="conditional_unsolvability"
 1 行  engine="fd_adapter"   payload.producer="deadlock_carver"  form="pruning_account"
 1 行  engine="lp_potential" payload.producer="ic3_pdr"          form="inductive_invariant"
```
（实测，`engine-rig/artifacts/candidates.jsonl` 44 行里的 18 行）

`fuzzlab/props/` 下**没有 `deadlock_carver.py`，也没有 `ic3_pdr.py`**。
这 18 行携带 `pattern / mutexes / blocked_actions / closure / cnf / clauses_dropped /
converged_at_frame / states_blocked …` 等约 30 个字段，**fuzzlab 覆盖率为 0**，
而且因为它们顶着 `fd_adapter` / `lp_potential` 的名字进流，
按引擎名做的覆盖统计会把它们算进"已有属性电池的引擎"里。
它们在 engine-rig 侧有 `test_deadlock_carver.py` / `test_ic3_pdr.py`
和 `CONTRACTS/deadlock_certificate_v0.1.md` / `ic3_certificate_v0.1.md`。

---

## 我认为最该补的三条不变式（按性价比排序）

### 1. `cegis_miner` — `effects_agree_with_the_evidence`（并把遍历改成 `all_rules`）

**补在哪**：`fuzzlab/props/cegis_miner.py`，第五条不变式；同时把现有四条的
`for rule in result.rules` 改成 `for rule in result.all_rules`。

**断言什么**：对每条规则、对 `rule.support` 里的每个 transition index `i`，
`transitions[i].effect` 与 `rule.effect` 一致（lifted 规则则按其 `action`
做 `?dir` 实例化后一致）。这只需要 `transitions` 里已有的信息，
**不调用 miner 的任何算法**，符合 fuzzlab 的 oracle 房规。

**为什么比别的值**：
一是它同时补上两个缺口——`effect.*`（5 个字段，且是**被下游代码机械消费**的字段）
和整个 lifted 规则类（实测占发布量 15.6%）。
二是**这是唯一一条"规则说了什么"的缺口**。现有四条不变式合起来是一个完整的
guard 理论，但一条规则进手册后被当作因果律使用的部分是 effect，而 effect
现在只有单 fixture 钉值。三是改 `rules` → `all_rules` 是一行的事，
却把从未被看过的一整类候选拉进审查范围。

### 2. `probe_frontier` — `cost_and_value_are_the_world's`

**补在哪**：`fuzzlab/props/probe_frontier.py`，第五条不变式。

**断言什么**：对 `rank_probes` 的每个返回项，
`value.cost == world.cost_map().get(action, 1.0)`，
且 `value.value == value.entropy / value.cost`（cost > 0 时）。

**为什么比别的值**：
`value_bits_per_cost` 是这个引擎**唯一的输出语义**——它存在的理由就是回答
"下一个实验做哪个"。现在 `cost` 和 `value` 被读了，但只当排序键；
一个系统性错误的 cost（例如永远 1.0，把 `probe_frontier` 悄悄退化成纯熵排序）
能让四条不变式全绿。这条不变式两三行，却是把该引擎的主输出从
"内部自洽"提升到"对着世界正确"。
（executable 那 12 个字段缺口更大，但补它需要给 fuzzlab 造一个带 planner 的世界族，
性价比低一个量级；engine-rig 的 `test_probe_reach.py` 目前是唯一防线，
这个事实本身应当写进 `ROBUSTNESS.md`。）

### 3. `mdl_segmenter` — `mdl_accounting_is_closed`

**补在哪**：`fuzzlab/props/mdl_segmenter.py`，第五条不变式。

**断言什么**：三件事，一条不变式：
(a) `baseline_bits == Σ_t cost.baseline_transition_bits(|changed_pixels(f_t, f_{t+1})|)`
——由 fuzzlab 自己数变化像素，不复用引擎的 `CostModel` 聚合路径；
(b) `gain_bits == baseline_bits - script_bits` 且 `ratio == script_bits / baseline_bits`；
(c) `payload["segment_operator"]` 与实际使用的算子一致
（这一条现在**不可能通过**——`Segmentation` 不记录算子，`to_payload` 写死一个字符串。
这正是它该被断言的理由：它会把一个真实缺陷从"没人看"变成"每次跑批都响"）。

**为什么比别的值**：
现有 `script_bits_identity` 只锁住等式的一端。MDL 的整个用途是**取舍**——
手册靠 `gain_bits` / `ratio` 决定一个对象假设值不值得写下来——而分母
（`baseline_bits`）和两个导出量在 fuzzlab 侧完全无人读。
顺带把 `segment_operator` 那个写死的字符串变成一条会响的断言，
是本次分析里**唯一一个已经能证明为假的发布字段**，成本极低。

（第 2 名与第 3 名的排序我犹豫过：`mdl` 那条能立刻抓到一个真缺陷，
`probe` 那条防的是一个尚未发生的缺陷。我把 `probe` 排前面，
因为 `segment_operator` 的错法是"标签不精确"，
而 `cost` 的错法会让引擎的**排序结论**整体失真——后者更贵。）

---

## 我不确定的

1. **"进手册"我采用了宽口径，可能高估。** `cold-start-a0/THEORIZE_LOG.md`
   明写裁决是"从候选流、盘面图和轨迹"做出的，LLM 读的是**整行 payload**，
   所以严格说 111 个字段全部进入手册的输入。表格里"被下游代码机械消费"那一列
   （7 个）是我能拿证据钉死的窄口径。介于两者之间的（例如 `rendering`、`claim`
   这类"LLM 会直接抄"的句子）我按宽口径论述、按窄口径计数。
   如果 RES-3 要的是窄口径总数，那是 **7**，不是 64。

2. **属性记录器测不到"只在失败分支里读"的字段。** 25 世界跑批全部干净
   （无 violated），所以像 `law.scope`、`plan.backend` 这种只出现在
   `finding.violated(...)` kwargs 里的字段不会被记录。我逐条读码确认了它们
   确实只在失败消息里出现、不参与任何断言，但这一步是**读码**不是实测。

3. **`lp_potential` 的"事实等价审"这个口径可以被质疑。**
   我把 `conditions.inv_closed`、`admissible: true` 判为已审
   （理由：它们声称的事实被独立重算了），而没有判为未审
   （理由：字段本身从未被比对）。如果某个不变式重算出"条件不成立"而字段说
   "成立"，现有电池会因为**事实**不成立而报 violated，所以撒谎的字段在实践中
   躲不过去——这是我下这个判断的依据。但若有人坚持按字段计量，
   `lp_potential` 的未审数会从 14 涨到约 20。

4. **`test_interop.py` 我没有完全展开。** 它审的是
   `interop/certificate_export` 那份文档（另一个产物，有自己的冻结契约），
   不是 `candidates.jsonl` 的 payload。我据此没有把它算进任何字段的
   "别处审了吗"，但它确实是 `lp_potential` 输出的第三条审查通路，
   若 RES-3 关心 `initial_potential` 之类字段，值得单独派一次。

5. **`events[].at` 的引擎侧覆盖我没查实。** grep `"at"` 在 tests 里噪声太大
   （PDDL 谓词 `at` 大量命中），我只能确认 `props` 侧不审，
   engine-rig 侧标为"没有找到"而非"没有"。

6. **计数是叶字段路径口径，换一种口径数会变。** 例如把
   `goal_potentials{}` 的每个动态键算一个（实测能到 24 个），
   或把 `effect` 这类容器也计入，总数会明显不同。
   表里所有数字都用同一套口径，可以互相比较；跨报告引用时需要说明口径。
