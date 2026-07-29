# 引擎：probe_frontier

seam：**框架假定的 seam 不存在，我自己装了一个。** 其余五个 props 模块都把引擎调用
收在一个私有 helper 里（`props/zero_space.py:_analyse`），`mutants/__init__.py` 的
seam 契约就是那个。`props/probe_frontier.py` 没有：它直接写
`engine.partition_for(...)` 和 `engine.rank_probes(...)`。该模块上仅有的两个私有名
`_truth_partition` / `_class_weights` 是 **oracle 侧**（fuzzlab 自己从
`world.predictions()` 重算真值），在它们上面注入是骗判官不是骗引擎，**我没有碰**。
`engine` 确实是 props 模块上的属性，但它是**模块对象、不可调用**，`mut.applied` 的
`callable(original)` 检查会直接 `TypeError`，所以它**不能**直接当 seam
（已实测确认，不是推测）。

我的做法，**不改框架、不改 props 源文件、不碰 engine-rig**：
`mutants/probe_frontier.py` 在 import 时给 props 模块**装上**两个转发函数
`_call_partition_for` / `_call_rank_probes`，并把 `props.engine` 换成一个透明代理——
除这两个入口外全部 `__getattr__` 直透真引擎，这两个入口则**在调用时**按名字从 props
模块取，于是 `mut.applied` 的 rebind 能被看见。引擎本身只被读、从未被 patch，谎言仍然
说在「引擎与 property 之间」，正是 `mutants/__init__.py` 指定的位置。
分成两个 seam 而不是一个：只有 `partition_matches_truth` 走 `partition_for`，另外三条
走 `rank_probes`；合并成一个 seam 会让每个 partition 变异体同时污染三条排序/熵不变式，
per-invariant 归因就没了。

代价（如实报告）：这是 import 时对另一个模块命名空间的运行时改写，不是框架给的能力。
`python -m pytest fuzzlab/tests` 65 项在装了 shim 之后**全过**，基线也干净，但这属于
「我绕过去了」而不是「框架支持」。见文末。

世界数：**40**（默认）；基线：**干净**（0/40 dirty，0 confounded）。
命令：`python -m fuzzlab.mutation --engine probe_frontier --worlds 40`
产物：`fuzzlab/out/mutation.probe_frontier.json`

## 逐不变式检出力

| 不变式 | 变异体 | 预注册命中？ | killed/eval | 首杀世界数 | inert | raised-only |
|---|---|---|---|---|---|---|
| partition_matches_truth | pf-partition-merge-two-classes | ✗ | 0/34 | — | 6 | **34** |
| partition_matches_truth | pf-partition-move-one-hypothesis | ✗ | 0/34 | — | 6 | **34** |
| partition_matches_truth | pf-partition-drop-one-hypothesis | ✗ | 0/40 | — | 0 | **40** |
| partition_matches_truth | pf-partition-relabel-class | ✗ | 0/40 | — | 0 | **40** |
| entropy_matches_bruteforce | pf-entropy-shift-1e-16 | ✗（预告存活） | 0/31 | — | 9 | 0 |
| entropy_matches_bruteforce | pf-entropy-shift-1e-12 | ✗（预告存活） | 0/40 | — | 0 | 0 |
| entropy_matches_bruteforce | pf-entropy-shift-1e-9 | ✓（部分） | **26/40** | 1 | 0 | 0 |
| entropy_matches_bruteforce | pf-entropy-shift-2e-9 | ✓ | 40/40 | 1 | 0 | 0 |
| entropy_matches_bruteforce | pf-entropy-shift-1e-6 | ✓ | 40/40 | 1 | 0 | 0 |
| entropy_matches_bruteforce | pf-entropy-shift-1e-3 | ✓ | 40/40 | 1 | 0 | 0 |
| ranking_is_sound | pf-rank-swap-adjacent | ✓ | 40/40 | 1 | 0 | 0 |
| ranking_is_sound | pf-rank-best-to-last | ✓ | 40/40 | 1 | 0 | 0 |
| ranking_is_sound | pf-rank-drop-action | ✓ | 40/40 | 1 | 0 | 0 |
| splits_flag_is_honest | pf-splits-collapse-partition | ✓ | 34/34 | 1 | 6 | 0 |
| splits_flag_is_honest | pf-splits-fabricate | ✓ | 12/12 | 1 | 28 | 0 |
| ranking_is_sound (owner) | pf-flatten-reported-costs | ✗（预告存活） | 0/35 | — | 5 | 0 |
| partition_matches_truth (owner) | pf-probevalue-partition-relabel | ✗（预告存活） | 0/40 | — | 0 | 0 |
| partition_matches_truth (owner) | pf-probevalue-partition-move | ✗（预告存活） | 0/28 | — | 12 | 0 |

**没有任何一个 unexpected kill**：18 个变异体里每个被杀的都只杀掉它预注册的那一条。
四条不变式互相独立、不串味——这是本次唯一一个纯正面结果。

### 头条：`partition_matches_truth` 是**死代码**，它一次也响不了

四个 partition 变异体全部 `raised`、零 `violated`。原因不是不变式弱，是它的**报告路径
根本调不通**：

```
props/probe_frontier.py:91
    finding.violated(ENGINE, "partition_matches_truth", world, detail,
                     action=action, engine=normalised, truth=expected)
                                    ^^^^^^^^^^^^^^^^^
finding.py:58
    def violated(engine, invariant, world, detail, **data)
```

`engine` 已经是第一个位置参数，`**data` 里再传一个 `engine=` →
`TypeError: violated() got multiple values for argument 'engine'`。
**这条不变式一旦发现不一致就抛异常，永远无法产出 violated。**
已用不经过我任何代码的独立最小复现确认（直接调 `finding.violated(...)`），
不是我的 shim 的产物。

这正是 `mutants/__init__.py` 开篇写的那句话的实例：「一条永远不会响的不变式和一条被满足
的不变式，在 `out/campaign.json` 里长得一模一样」。3000 世界里 `partition_matches_truth`
的 0 违反，与引擎对不对**无关**。

比较逻辑本身是好的。我在内存里跑了反事实（不改任何文件，直接复算 got vs want）：

| 变异体 | 修好后会杀 | 首杀 |
|---|---|---|
| pf-partition-merge-two-classes | 34/34 | 1 |
| pf-partition-move-one-hypothesis | 34/34 | 1 |
| pf-partition-drop-one-hypothesis | 40/40 | 1 |
| pf-partition-relabel-class | 40/40 | 1 |

所以修复是把那个关键字改名（`engine=` → 例如 `engine_partition=`），改完这条不变式
100% 检出、第 1 个世界就杀。我**没有改**——props 不在我这次的交付范围内。
顺带：同一函数里 `costs = world.cost_map()` 是没人用的死局部变量（`partition_for`
不吃 costs）。另外三条不变式的 `violated(...)` 关键字没有撞名，已逐一核对。

## 分辨率：每条数值不变式能抓到的最小偏差（本引擎重点）

| 不变式 | 最小可检出偏差 | 这个数从哪来 |
|---|---|---|
| entropy_matches_bruteforce | **> 1e-9 绝对**；1e-9 本身是 26/40 的抛硬币带；2e-9 起 100% | `props/probe_frontier.py:49` 的常量 `EPS = 1e-9`，判据 `abs(value.entropy - expected) > EPS`。**绝对**阈值，不随熵大小缩放。 |
| entropy_matches_bruteforce（浮点地板） | ~1.1e-16 | 实测 40 世界共 154 个 action 熵，非零者落在 [0.391, 1.933]，最大 ulp **2.22e-16**。1e-16 的偏移只有 86/154 个条目在浮点上真的落得下（其余被舍入吞掉，9/40 世界整体 inert）。 |
| ranking_is_sound | **一次相邻对换**（无容差） | `keys != sorted(keys)` 是精确比较，排序键 `(-value, -entropy, cost, str(action))` 因 `str(action)` 收尾且同一世界内 action 名唯一而是**严格全序**，不存在并列可换。 |

**这一格的结论**：EPS 把可用分辨率丢掉了约 **7 个数量级**。浮点本身能分辨 1e-16 级的谎，
不变式只肯从 1e-9 开始看。1e-9 那一档 26/40 的部分命中是纯舍入现象：判据是
`fl(e + 1e-9) - e > 1e-9`，这个差按 e 的 ulp 舍入后可能落在 1e-9 两侧，实测 154 个条目
里 72 个越线（一个世界只要有一个 action 越线就被杀，于是 26/40）。

值得说明 EPS 并非无理由：引擎 `entropy_of` 与 oracle `partition_entropy` 是同序同权重的
两份独立实现，实际求和噪声在 1e-16 量级，所以 EPS 大约有 **7 个数量级的余量**。
把 EPS 收到 1e-12 仍远高于噪声，且会把 `pf-entropy-shift-1e-12` 从存活变成命中——
这是一个有具体数字支撑的收紧建议，不是审美意见。

排序那一格按要求测了两种强度：**相邻对换**与**冠军挪到末位**，检出力**完全相同**
（40/40，首杀均为第 1 个世界）。差异为零，原因是键是严格全序且比较无容差——
「排序可靠」这条没有分辨率问题。它的**盲区在别处**，见下。

## 杀不死的变异体（逐个裁决）

**(a) 不变式不够 —— 4 个**

1. `pf-partition-merge-two-classes` / `-move-one-hypothesis` / `-drop-one-hypothesis`
   / `-relabel-class`（4 个都算这一类）。裁决：**不变式不够，且是最严重的一种不够——
   它是死代码**。补法：`props/probe_frontier.py:91` 的 `engine=normalised` 关键字改名。
   证据：上面的反事实表，改完 100% 命中。

**(b) 我预告过会存活的「缺口探针」—— 3 个。它们不是我写错了，是电池确实没覆盖到这块**

2. `pf-flatten-reported-costs`（0/35 存活）。注入：引擎无视调用方的 cost map，
   对每个 action 都报 `cost = 1.0`，然后按引擎自己的键重排（所以返回序列内部自洽）。
   claim 有据：`frontier.py:rank_probes` 写 `cost=costs.get(action, 1.0)`，
   `ProbeValue.value` 的 docstring 是「Bits per unit of path cost」，README「Path cost」
   一节说成本由调用方给、planner 层还会把真实计划长度记进去。
   裁决：**不变式不够**。四条不变式里**没有任何一条把返回的 `cost` 与 `world.cost_map()`
   对过**——两个 property 甚至都算了 `costs = world.cost_map()` 传进引擎，却从不检查回来的
   `cost`。后果具体：payload 里的 `value_bits_per_cost` 对每个非单位成本 action 都是错的，
   而 `ranking_is_sound` 只做**内部自洽**检查（用返回对象自己的字段重算键），所以一个
   「对成本视而不见」的引擎能完美通过。
   补法：加一条 `cost_matches_the_cost_map`（逐 action 比 `value.cost` 与
   `world.cost_map()[action]`），顺带覆盖 `value == entropy / cost`（后者见下，是恒真的）。

3. `pf-probevalue-partition-relabel`（0/40 存活）
4. `pf-probevalue-partition-move`（0/28 存活，12 inert）
   注入：改 `ProbeValue.partition`（把一个观测类改名／在两类之间搬一个假设），
   **保持类数不变**，于是 `splits` 不变、`entropy` 字段不变。
   claim 有据：`frontier.py:probe_value` 令 `partition=partition_for(...)`，
   `as_json()` 输出它，`__init__.py:to_payload` 把它放进冻结的 `probe_design` payload
   （README「Payload shape (stable)」）。
   裁决：**不变式不够**。`partition_matches_truth` 检的是**另一次独立调用**
   `engine.partition_for(...)` 的返回值，而**进入 payload 的那一份
   `ProbeValue.partition` 从未与真值比对过**。`splits_flag_is_honest` 只读它的**类数**。
   所以任何保类数的分组错误全程隐形——而这份分组正是手册会照抄的东西
   （「观测到 X 就淘汰 h3」）。
   补法：`splits_flag_is_honest` 里已经算好了 `blocks = _truth_partition(...)`，
   把 `value.partition` 与它整体比一次即可，几乎零成本。

**(c) 按设计存活的容差阶梯 —— 2 个**

5. `pf-entropy-shift-1e-16`、6. `pf-entropy-shift-1e-12`。裁决：**不算缺陷报告**，
   它们是量尺的刻度，存活本身就是读数（见「分辨率」）。1e-16 一档另有 9/40 inert，
   因为偏移小于 ulp 时连注入都没发生——这正是 inert 机制该做的事。

## 构造上不可证伪的检查

`ProbeValue` 的三个量是 **property 而非字段**（`frontier.py:37-48`）：

* `value = entropy / cost`（cost 为 0 时 `inf`）
* `splits = n_classes > 1`，`n_classes = len(partition)`

所以：

1. **没有任何变异体能让 `value` 与 `entropy / cost` 不一致**，任何「value 算错了」的
   不变式都恒真、不可证伪——与 `zero_space` 的 `dimension == len(basis)` 同型。
   （代价：也因此测不出「引擎按原始熵而不是按 bits-per-cost 排序」这个经典 bug；能测的
   最接近的形态是 `pf-flatten-reported-costs`，而它存活。）
2. **没有任何变异体能让 `splits` 与它自己的 partition 不一致**。`splits` 只能**透过**
   partition 说谎，这就是 `pf-splits-*` 改 partition 而不是改 `splits` 的原因。
   `splits_flag_is_honest` 因此不是在查一个独立字段，而是在查
   「`len(ProbeValue.partition)` 落在 1 / >1 哪一侧」——**一个一比特的检查**。
   实测支持：`pf-probevalue-partition-move` 把分组改错但保住类数，它一个也没抓到。
3. 我**故意没写**的两类变异体，因为它们注入的是引擎从未承诺的行为，杀不死才是对的：
   **并列顺序**（排序键含 `str(action)` 且 action 名唯一，根本不存在并列）；
   **partition 字典的插入顺序**（`as_json()` 输出前排序，键序不携带信息）。

## 预测错的地方

* **最大的一处**：我预测四个 partition 变异体会被 `partition_matches_truth` 干净地杀掉。
  实际 0 kill / 100% raised。我预测错的方向是「以为不变式活着」——而它是死的。
  这一条我事前没有任何征兆去怀疑：不变式的比较逻辑读起来完全正确，问题在报告调用上。
* `pf-entropy-shift-1e-9`：我在文件里写了「坐在边界上，杀不杀由每个世界的舍入决定」，
  实测 26/40，属于预测命中；但我没有预判到比例这么高（154 个条目里 72 个越线，
  接近一半，符合舍入对称的预期，事后看是合理的）。
* `pf-rank-swap-adjacent` vs `pf-rank-best-to-last`：我预期两者都 100%，实测确实都
  40/40。派单假设「检出力可能完全不同」——在本引擎**不成立**，原因已在分辨率一节给出
  （严格全序 + 无容差）。这是一个否定性回答，不是没测。
* `pf-splits-fabricate` 的 inert 率（28/40）比我预想的高：需要「某个 action 只有一个观测
  类且该类含 ≥2 个假设」，在 `hypset` 的 flavour 权重下不常见。它仍然 12/12 全杀、首杀
  第 1 个世界，所以结论不受影响；但若这类缺陷更稀有，40 个世界就不够了。

## 杀死所需的世界数

**所有能杀的变异体首杀都在第 1 个世界**（含只有 26/40 命中率的 1e-9 边界档）。
即：对这四条不变式而言，标准 500 世界的战役在**检出力**上买不到任何东西——第 1 个世界
就够。500 买到的是世界**多样性**（flavour、权重、零成本等角落），不是灵敏度。
唯一对世界数敏感的是 **inert 率**：`pf-splits-fabricate` 只有 30% 的世界能承载注入，
`pf-probevalue-partition-move` 70%，所以「40 个世界」在这里的真实含义是
「12–40 个可用世界」，报告里的分母必须按 eval 读而不是按 40 读。

## 我不确定的 / 框架挡住我的地方

1. **框架假定 seam 已存在，probe_frontier 上它不存在。** 我用 import 时给 props 模块装
   转发函数 + 换 `engine` 为透明代理绕过去了（65 项测试全过、基线干净），但这是**我在
   变异体目录里改另一个模块的运行时命名空间**，不是框架给的能力。更干净的做法是在
   `props/probe_frontier.py` 里加两个私有 helper（和另外五个模块一致），那需要动 props，
   不在我这次的授权范围内。**请你定：** 是接受这个 shim，还是让 props 补 helper、我改回
   常规 seam。
2. **`expect_kill` 不允许为空**（`Mutant.__post_init__`），所以**「设计上就该存活的缺口
   探针」无法如实登记**。我采用的约定写在模块 docstring 里、跑之前就写好了：
   `expect_kill` 填**拥有该 claim 的那条不变式**，凡 `description` 以
   `EXPECTED SURVIVOR:` 开头的都是我事前预测会存活的。代价是这 5 个变异体会污染
   `predicted_but_missed` 列——读那一列的人如果不读 description 会误判。
   建议框架加一个 `expect_survive` 或允许 `expect_kill=()` 配一段理由。
3. **`raised` 吃掉了一条不变式的全部信号，而汇总行看不出来。** 驱动的单行输出
   （`SURVIVED` / `killed by …`）只反映 `violated`，`raised_only` 只在 JSON 里。
   四个 partition 变异体在控制台上读作「4 个存活」，与「不变式弱」完全同形；
   实际是「不变式每次都崩」。我是去翻 JSON 才看见的。建议汇总行把
   `raised_only>0` 打出来——`SURVIVED (raised on 34)` 之类。
4. 我**没有**修 `partition_matches_truth`，也没有碰 `props/`、`mutation.py`、
   `mutants/__init__.py`、别的引擎的 catalog、`engine-rig`。只写了两个文件：
   `fuzzlab/mutants/probe_frontier.py` 和本文件。运行副产物：
   `fuzzlab/out/mutation.probe_frontier.json`。
