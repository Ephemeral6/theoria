# probe_frontier via brute force — and against cegis_miner's frontier

工单 **E11-engine-crosscheck-deep**，RES-3 (verify) 交叉复核一路。
基准提交 `ed592a6`（worktree `.worktrees/e11-engine-crosscheck-deep`）。
**只读复核：`engine-rig/` 与 `fuzzlab/` 一个字节未改。** 全部脚本写在会话
scratchpad，不入仓库。无网络，未读 `.env`，封存堆零接触。

---

## 1. 链路与独立性

被查的链路，以及每一步用了谁的代码：

| 步 | 代码归属 |
|---|---|
| 轨迹 → 分割 | `engine-rig/engines/mdl_segmenter`（**引擎的**，照单全收） |
| 分割 → 规则 + frontier | `engine-rig/engines/cegis_miner.mine`（**引擎的**，照单全收） |
| frontier → 假设集 | `probe_frontier.hypotheses_from_guards`（**被测**） |
| 假设集 + 状态 + 动作 → 划分/熵/排序 | `probe_frontier.{partition_for,entropy_of,probe_value,rank_probes,best_probe,run}`（**被测**） |
| 排序 → payload → candidates | `probe_frontier.{to_payload,candidates}` + `common.candidates`（**被测**） |
| 期望值（划分/熵/排序/价值） | **本次自写**，见下 |

**独立性纪律。** 期望值一律不经 `probe_frontier` 的任何计算函数。引擎的这些
函数只被调用来取“引擎说了什么”，从不被调用来构造“应该是什么”。

熵的公式**故意与引擎不同**。引擎逐类累加

    H = -Σ_c (w_c/W)·log2(w_c/W)

本次独立实现用代数等价、数值不等价的

    H = log2(W) - (1/W)·Σ_c w_c·log2(w_c)      （`math.fsum` 求和）

两式一致才算证据；若照抄引擎的写法，一致只证明抄对了。
排序键也自写、自排，不读 `rank_probes` 的 key。

对照的“真值划分”读**原始预测表** `{(hyp_id, action): observation}`，不调用
`Hypothesis.predict`——否则等于让输入给输出打分。

**与 `fuzzlab/props/probe_frontier.py` 的关系。** 该模块已有同名的四条不变式
（`partition_matches_truth` / `entropy_matches_bruteforce` / `ranking_is_sound` /
`splits_flag_is_honest`）。本次**没有导入 fuzzlab 的任何东西**——生成器、oracle、
不变式全部另写，`hypset` 世界一个也没用。重复的那一半（1–3 行）只用来独立确认；
本路的产出在第 5、6 节。

---

## 2. 共享依赖清单（不省）

无法消除的共享，按风险从高到低：

1. **`engines.cegis_miner.atoms.evaluate` / `Atom` / `State` / `strip_cells`** ——
   guard 的语义本身。交叉的一半完全建立在它之上：我判断“guard i 在状态 s 下
   是否 fire”用的就是这个函数，`hypotheses_from_guards` 用的也是它。
   **若 `evaluate` 错，两侧同错，本报告的交叉一致性结论会报“通过”。**
   这是本路最大的单点。
2. **`engines.cegis_miner.mine` + `mdl_segmenter.segment_trajectory`** ——
   frontier 里有哪些 guard，是照单全收的。“frontier 本身对不对”不在本路射程内。
3. **`engines.probe_frontier.frontier.Hypothesis`** —— 引擎的输入类型，必须用它构造。
   但 `predict` 闭包是自写的，`weight` 是自赋的。
4. **`math.log2` / `math.fsum`** —— 对数是同一个 libm 调用；只有求和结构不同。
5. **`fixtures.cart_world`（轨迹）、`fixtures.pair_flip`** —— 数据本身。
6. **`common.jsonio.{read_jsonl,dumps}`、`common.candidates.{make_candidate,emit}`** ——
   第 4 节 F3 那条走的是真实发射路径。
7. **`tools.validate_candidates.validate_rows`** —— 只用来**记录它的判定**，
   不用来推导真值。
8. **`engines.zero_space.analyse` / `gf2`** —— 第 6 节，照单全收。
9. **一个实例写了生成器、oracle 和判据**（与 `fuzzlab/BUGS.md` 第 4 条同样的
   系统性风险）。共同盲点无法自查。

**明确未共享**：`partition_for` / `entropy_of` / `probe_value` / `rank_probes` /
`best_probe` 的计算逻辑；`fuzzlab` 全部（本次一次也没 import）。

---

## 3. 方法与规模

**A. 合成语料暴力对照。** 自写生成器：1–9 个假设 × 1–7 个动作 × 1–5 种观测的
随机预测表；权重抽自 `{0.5,1,2,3,7}`；代价抽自 `{0, 0.25, 1, 2, 5, 12}`（**零代价
按 2/9 的比重刻意生成**）。**4000 个世界**，逐世界逐动作比对划分、熵、代价、
排序，以及 `best_probe` 与实际 payload。

**B. cegis frontier 交叉。** `cart_world` 轨迹 → `mine` → 取 `len(frontier) ≥ 2`
的 **9 条规则**（guard 数 2…21）。状态空间**穷举**：12×12 盘面上 (2,3) 物体的
每个锚点 × 每个单障碍位置 = **15 290 个状态**，× 4 个动作 = 每条规则 61 160 次
探针求值，合计约 **55 万次**。对每个状态：引擎排第一的探针到底切开了 frontier 里
哪些 guard 对；哪些对在整个空间的**某处**可分；哪些对**处处不可分**。

**C. 定 payload / 契约。** 零代价最小复现 + `validate_candidates` 判定 + 严格
JSON 重读。

**D. zero_space 侧。** `pair_flip` 轨迹 → `analyse`，并用 `inspect.signature`
枚举 `probe_frontier` 的全部公开入口，查有没有消费 law/vector/basis 的通路。

---

## 4. 结果表

### A. 合成语料（4000 世界）

| 检查项 | 不一致数 | 判定 |
|---|---|---|
| 划分 = 预测表分组 | **0** | 一致 |
| 熵 = 独立公式（bits） | **0**（最大偏差 `1.11e-15`） | 一致 |
| `ProbeValue.cost` = 调用方给的 cost | **0** | 一致 —— 线索 3a 确认为**盲区不是缺陷** |
| `payload["partition"]` = 真值划分 | **0** | 一致 —— 线索 3b 同上 |
| `payload["cost"]` = 调用方给的 cost | **0** | 一致 |
| 排序序列 | 35 / 4000 | 见下，**0 例真不一致** |
| `best_probe` 说“无”但确有可分动作 | **82 / 4000（2.05 %）** | **缺陷 E11-PF-1** |
| 发射的 candidate 含 `Infinity` | **1633 / 4000** | **缺陷 E11-PF-3** |

**排序的 35 例已全部定性**（第 4 点“并列不是承诺”的假阳性来源，逐例查过）：

* 10 例：在引擎自己的键上**完全并列**，只差 `str(action)` 兜底 —— 非缺陷；
* 25 例：价值差 `< 1e-12` 的浮点近并列，源头是**我的公式**而非引擎 —— 非缺陷；
* **0 例真实重排。** 其中 18 例排第一的动作不同，但全部落在上面两类里。

**关于 `EPS` 与浮点地板（独立测量，不重做已有工作）。**
`fuzzlab` 用绝对阈值 `EPS=1e-9`。本次两个代数等价公式之间实测的最大分歧是
**`1.11e-15`，约 5 ULP**（1.0 处 ULP = `2.22e-16`），不是 1 ULP。
单类划分处引擎给**精确 `0.0`**，逐份累加的写法在退化情形下比对数差分式更准。
结论：`1e-9` 安全且有约 6 个数量级余量；但**把阈值收到 `2.2e-16` 会产生假阳性**，
可用的最紧绝对阈值在 `1e-14` 量级。这是独立复算得到的数，与已有量测同向、
但把“地板”从 1 ULP 修正到约 5 ULP。

### B. cegis frontier 交叉（9 规则 × 15 290 状态）

| 规则 | guard 数 | 可区分世界数 | 有可分动作的状态 | 其中**引擎首选真的切开了 frontier** | “说无但有” |
|---|---|---|---|---|---|
| `blocked_DOWN` | 2 | 2 | 300 | **300 (100 %)** | 0 |
| `blocked_LEFT` | 2 | 2 | 198 | **198 (100 %)** | 0 |
| `blocked_RIGHT` | 6 | 6 | 1727 | **1727 (100 %)** | 0 |
| `blocked_UP` | 14 | **12** | 1551 | **1551 (100 %)** | 0 |
| `push_DOWN` | 2 | 2 | 300 | **300 (100 %)** | 0 |
| `push_LEFT` | 2 | 2 | 198 | **198 (100 %)** | 0 |
| `push_RIGHT` | 3 | 3 | 1588 | **1588 (100 %)** | 0 |
| `push_UP` | 2 | 2 | 300 | **300 (100 %)** | 0 |
| `teleport` | 21 | **18** | 2957 | **2957 (100 %)** | 0 |

---

## 5. 交叉一致性：探针排序与 cegis 前沿指向同一批不确定性吗？

**主结论：指向同一批。** 在全部 9 条规则、55 万次求值里，引擎排第一的探针
**没有一次**是“切不开任何东西”的。工单假设的那个失败模式
（“排序高的探针切不开任何东西”）在这条链路上**不存在**——
因为 `value = entropy / cost`，而这条链路上 cost 恒为 1.0，排序退化成按熵排序，
熵 > 0 与“至少切开一对 guard”是同一件事。这是一个真结论，也是一个**脆弱**的
结论：它成立仅仅因为代价是常数。代价一旦不是常数，第 6 节的 E11-PF-1 就是同一
个失败模式的实例。

但交叉暴露了三处**方向不同**的地方：

### 5.1 cegis 数 guard，probe 也数 guard —— 于是 cegis 的记账方式在替 probe 选实验

`cegis_miner` 按 D-002 **刻意**把外延相等的谓词保留成不同的原子
（`free` / `in_bounds` / `clear` 在单物体盘面上无法区分），理由是“证据区分不了
它们”本身就是知识状态。`hypotheses_from_guards` 把 frontier 每条 guard 变成一个
假设，**权重一律 `1.0`**（实测 `hypothesis_weights_seen == [1.0]`，9 条规则全部如此）。
熵按假设**条数**加权。

后果可测：

* `teleport`：**21 条 guard，只有 18 个可区分世界**（3 对在穷举出的 15 290 个
  状态里处处同真同假）；
* `blocked_UP`：**14 条 guard，12 个可区分世界**（2 对处处不可分）；
* 把每个等价类算作一票（而不是每条 guard 一票）后，
  `teleport` 的 argmax **在 16 个状态上改变**，最大熵差 **0.0617 bit**；
  `blocked_UP` 最大熵差 **0.0584 bit**，argmax 未变。

具体一例（`teleport`，锚点 (0,1)、障碍 (0,0)）：

| | 引擎（每 guard 一票） | 每个可区分世界一票 |
|---|---|---|
| 1st | **UP** 0.9852 | **DOWN** 0.9641 |
| 2nd | DOWN 0.9183 | RIGHT 0.9641 |
| 3rd | RIGHT 0.9183 | UP 0.9183 |
| 4th | LEFT 0.7919 | LEFT 0.8524 |

引擎推荐 UP；按“世界”计票 UP 掉到第三。两边各自内部自洽：cegis 保留重复原子
是对的，probe 对给定假设集算熵也是对的。合起来，**决定下一步做哪个实验的，
是 cegis 的原子去重策略，而不是世界**。

### 5.2 cegis 给了 guard 的 MDL 先验，probe 扔掉了它

`Rule.as_json()` 发布 `guard_cost_bits`，`guard_order_key` 按它排 frontier，
`mine` 还用 `frontier[0]` 当规则的正式 guard —— cegis 明确认为这些 guard
**不等概**。`Hypothesis.weight` 这个字段存在的意义正是承载先验，而
`hypotheses_from_guards` 从不设置它。

实测：把先验换成 `2^(-cost_bits/8)`，`teleport` 的首选动作在 **3 个状态**上改变。
（该先验是本次为了显示敏感性而选的，**不是仓库里的规范先验**；这一条的力度是
“排序对先验敏感且先验被丢弃”，不是“正确答案应该是别的”。）

### 5.3 跟着首选走，有些 guard 对永远拿不到证据

穷举出“在某处可分、但引擎首选探针在 15 290 个状态里从未切开”的 guard 对：

* `blocked_RIGHT`：`!in_bounds(strip(RIGHT)) ∧ act==RIGHT` vs `act==RIGHT ∧ at(10,9)`
* `blocked_UP`：`act==UP ∧ at(0,7)` vs `!in_bounds(strip(UP)) ∧ act==UP ∧ free(strip(LEFT))`

这是 `fuzzlab/BUGS.md` 已声明不测的“贪心 argmax 无全局最优性”的**具体实例**，
不是新缺陷类别；记在这里是因为它现在有了名字和可复现的坐标。

---

## 6. 只有交叉才暴露的

### E11-PF-1 —— 零代价的无用动作会让引擎宣布“此处无可做的实验”

`ProbeValue.value` 在 `cost == 0` 时返回 `float("inf")`（`frontier.py:44`：
`return self.entropy / self.cost if self.cost else float("inf")`）。
于是一个**熵为 0、代价为 0** 的动作拿到无穷大价值、排到第一；而
`best_probe` / `run` 取 `ranked[0]`，判 `ranked[0].splits` 为假，返回 `None`。

最小复现（两个假设，`UP` 值 1 bit / cost 1.0，`WAIT` 值 0 bit / cost 0.0）：

```
ranking : [('WAIT', 0.0, 0.0, inf, splits=False), ('UP', 1.0, 1.0, 1.0, splits=True)]
best_probe(...)                      -> None
run(...)                             -> None          # “此处推进不了前沿”
best_probe(去掉 WAIT)                -> 'UP'          # 1 bit 一直都在
```

**多给一个免费且无用的选项，就让引擎丢掉了一个 1 bit 的实验。**
合成语料里 **82/4000（2.05 %）** 的世界命中。

为什么只有交叉能看见：`fuzzlab` 的 `ranking_is_sound` 用
`keys = [(-v.value, -v.entropy, v.cost, str(v.action))]` **从引擎自己的
`ProbeValue` 重建键**再验有序——这是循环的，无论 `value` 定义成什么它都通过；
而 `best_probe` / `run` 根本没有任何 fuzz 不变式。`hypset` 生成器**明确按 1/11
的比重生成零代价**（其 docstring 说“零不是假设，排序要除以它”），语料里有，
判据里没有。引擎内部自洽，fuzz 内部自洽，缺口在两者之间。

### E11-PF-2 —— 同一个量，同一个引擎里两个相反的定义

同一个 `probe_frontier` 包内：

| | cost = 0 时的 value |
|---|---|
| `frontier.py:44` `ProbeValue.value` | `inf`（无限有价值） |
| `reach.py:146` `ExecutableProbe.value` | `0.0`（一文不值） |

两者都进各自的排序键。`reach.py` 的写法（`if self.cost == inf or self.cost <= 0:
return 0.0`）是对的，`frontier.py` 的不是；两个模块由同一作者写、各自的测试
各自通过。只有把两个假设层放在一起看才会看到它们对同一个退化情形给出相反答案。

### E11-PF-3 —— 发射到 `candidates.jsonl` 的不是合法 JSON，而契约校验器放行

零代价路径把 `inf` 写进 `payload["value_bits_per_cost"]`；
`common.jsonio.dumps` 用 `json.dumps` 默认 `allow_nan=True`，落盘成裸的
`Infinity` token —— **RFC 8259 里没有这个 token**。实测：

```
payload["value_bits_per_cost"]                 -> inf
落盘 JSON 含 "Infinity"                         -> True
tools.validate_candidates.validate_rows(rows)  -> []        # 无错误，放行
严格 JSON 重读（parse_constant 抛错）           -> REJECTED (Infinity)
```

合成语料里 **1633/4000** 的发射行命中。Python 自己的 `json.loads` 默认接受
`Infinity`，所以 rig 内部往返无感；任何严格读者（多数非 Python 实现、
`jq --seq`、Phase 4 发布清单的下游）会在这一行上失败。跨的是
`probe_frontier` × `common.candidates` × 冻结契约三方，单看任何一方都合规。

### E11-PF-4 —— `zero_space` 的残余歧义根本没有通向 probe 的路

`pair_flip` 上 `analyse` 给出：16 个特征、`difference_rank = 7`、零空间维数 9
（8 条 `cell_local` 由编码强制 + **1 条 `global` 是偶然的**——它成立只是因为轨迹
从未产生能证伪它的转移）。这与 cegis frontier 在结构上是同一种“证据未区分”的
残余。

但 `probe_frontier` 的全部公开入口（`inspect.signature` 枚举 28 个）里
**没有任何一个接受 law / vector / basis / ZeroSpaceResult**；
唯一的消费者入口是 `hypotheses_from_guards`，只认 cegis 的 guard 序列。
也就是说：**“下一步该问什么”这个问题，zero_space 的那一份残余无人问津**，
不是没测，是没有通路。

---

## 7. 打不出结论的地方

* **`evaluate` 的正确性没有独立验证**（共享依赖 #1）。整个第 5 节建立在它之上。
  若它错，交叉一致性会假报通过。这需要另一路对 cegis 语义单独下手。
* **frontier 的完备性没查**：`mine` 说 frontier 上有哪些 guard，我照收。
  `fuzzlab/BUGS.md` 已声明 `frontier_max_size` 以外不测，本路也没测。
* **“可区分世界数”只在我穷举出的状态空间里成立**：12×12、(2,3) 物体、**单**障碍。
  多障碍配置可能把某些“处处不可分”对分开，那会让 5.1 的差值变小而**不会**让它
  消失（等价类只会更细）。
* **5.2 的 MDL 先验是我选的**，仓库里没有规范先验。该条只证明“排序对先验敏感
  且先验被丢弃”，不证明“正确答案是别的”。
* **`run_with_planner` / `ExecutableProbe` 的排序没有暴力对照**：那条路要真
  Fast Downward 构建，本机 `.toolchain/` 不存在，只会走 `stub-bfs`。E11-PF-2
  是读代码 + 直接构造对象得到的，不是从规划器端到端跑出来的。
* **E11-PF-1 / PF-3 在当前仓库调用点是否可达，未确认**：`tools/run_all.py` 与
  `reach.py` 里代价来自计划长度 + `setup_cost=1.0`，恒 ≥ 1。两条缺陷是**公开
  API 上的**，`fuzzlab` 的生成器已经在踩，端到端跑批目前踩不到。按“宁可少报”
  记为：真缺陷，当前触发面限于直接调用方与 fuzz 语料。
* **没有跑 `engine-rig` 的 pytest 套件**（本路只读，不改不跑他人判据）。
  本报告不声称套件状态。

---

## 附：复现

脚本在会话 scratchpad（不入仓库），四个：
`bf_probe.py`（4000 世界暴力对照）、`bf_rank_triage.py`（35 例排序定性）、
`cross_cegis_probe.py` + `cross_dedup.py`（cegis 交叉与去重）、
`zs_cross.py`（zero_space 侧）。全部以 `engine-rig/` 为 cwd、
`sys.path` 只加 `engine-rig`，无写入、无网络。
