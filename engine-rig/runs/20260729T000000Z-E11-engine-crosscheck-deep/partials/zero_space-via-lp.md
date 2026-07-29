# 交叉复核：zero_space 的守恒律 ← lp_potential / 线性视角

工单 E11-engine-crosscheck-deep（RES-3 verify 赛道派出）。
worktree：`.worktrees/e11-engine-crosscheck-deep/`。engine-rig 与 fuzzlab 均未改动一字节。
临时脚本：`%TEMP%/claude/.../scratchpad/xcheck.py`（不在仓库内）。

**一句话结论**：两条路径**不一致**，且不一致是**单向**的——`zero_space` 报出的守恒律里，
有一部分被世界自身的转移关系证伪。200 个世界中 13 个受影响，共 **102 条被报为守恒律的
线性泛函，在一条合法转移上增量为奇**。其中 91 条的反例起点，是轨迹**自己走到过**的状态。

---

## 链路与独立性

`lp_potential` 的方法学要点写在 `engines/lp_potential/potential.py::check_exactly` 的注释里：
不变式的封闭性 "checked on the move instances, which is what makes the closure argument
**independent of which states are reachable**"，且用精确算术复核。
`zero_space` 的量词则是**观测到的那条轨迹**。本复核把前者的量词施加到后者的输出上。

| 步骤 | 用了谁的代码 | 独立吗 |
|---|---|---|
| 生成世界 | `fuzzlab/worlds/parityworld.py::generate` | 否——与 fuzzlab 电池共用；与 zero_space 自己的测试（engine-rig Fixture B）不共用 |
| 施加转移 / 建可达集 | `fuzzlab/worlds/parityworld.py::apply_operation` + 自写 BFS | 部分——`apply_operation` 与轨迹生成同源，见共享依赖 |
| 取得被检断言 | `engines.zero_space.analyse` | 否——它是被检者，必须调用 |
| 坐标约定 | 读 `result.features` 这个**列表**（不调用其算法） | 部分——见共享依赖第 3 条 |
| **判定守恒与否** | 自写 `increment_is_even`：`bin(a & x).count('1')`、`Fraction`，逐 move instance | **是**——只用 stdlib，是 `check_exactly::inv_closed` 的形状移植 |
| 计算"真"律空间维数 | `fuzzlab/oracles/gf2.py::null_space` | 是（相对 `engines/zero_space/gf2.py`）；相对 fuzzlab 电池否 |
| 内部一致性对照（发现 2） | `oracle.in_span` 判定 + `engine.cell_local_subspace` 作为**引擎自己的**编码律定义 | 刻意如此：问题就是"引擎是否自洽"，标尺理应用它自己的 |

**没有调用**：`zero_space.verify`、`engines/zero_space/gf2.py`、`equivalent_modulo_encoding`
（除上表最后一行的对照用途外）、`fuzzlab/props/zero_space.py`。

**没有调用 `lp_potential` 的代码，这一点必须说清楚**：`Move.delta` 硬编码为跳棋几何
（`w[dst] - w[src] - w[over]`），状态是 0/1 占据串，parityworld 两样都不是；
`solve_certificate` 无法作用于本族世界。我移植的是它的**条件形状**——精确算术、
逐 move instance 的增量约束、量词跨转移而非跨可达状态——不是它的实现。
因此这一路的独立性只等于这次移植的正确性，而不等于 `lp_potential` 已被验过的正确性。

---

## 共享依赖（不可避免的与本可避免的）

**不可避免**

1. `parityworld.apply_operation`：轨迹和我的可达集都由它产生。若它本身错了，两条路径会
   一起错向同一处。方向上这只能**掩盖**本复核的发现（发现属 soundness 方向：我在找
   引擎多报的律），不会**制造**它。
2. `result.features` 的坐标约定：两个实现必须共用一套坐标才可比。我按 `(cell, color)`
   对象取位序，与 `fuzzlab/props/zero_space.py` 的理由相同——自定顺序会把上游重排
   误判成引擎缺陷。读列表不等于跑它的算法。
3. `engines.zero_space.analyse`：被检者本身。

**本可避免但我接受了的**

4. 世界族只有 `parityworld`，与 fuzzlab 电池同源。它不是 zero_space 自己的测试夹具，
   所以相对被检者仍是新证据；但相对 fuzzlab 电池不是。
5. `fuzzlab/oracles/gf2.py`：相对 `engines/zero_space/gf2.py` 是独立实现（前者行列表
   RREF + pivot 列表，后者 dict 键 pivot），相对 fuzzlab 电池不独立。
   **缓解**：发现 1 的每一条"证伪"判决**完全不经过 oracle**——判决出自
   `increment_is_even`（stdlib 位运算 + `Fraction`）。oracle 只用来算表格里的
   `true_dim` 一列。所以即使 oracle 全错，发现 1 仍成立。

**一致性对照（非发现）**：200/200 个世界中，`oracle.null_space` 从同一条轨迹算出的律空间
与 `result.basis` 张成同一子空间（`oracle.same_span` 判定）。也就是说——
**消元本身没有错**。错的是挂在结果上的断言。

---

## 方法与规模

- N = **200** 个 `parityworld` 世界，种子 **1..200 连续**，在看任何结果之前选定，未挑种子。
  构成：`planted`/k=2 共 99，`free`/k=2 共 36，`free`/k=3 共 34，`free`/k=4 共 31。
- 对每个世界：
  1. `engine.analyse(world.states, world.colors)` 取全部律；
  2. 从 `world.states[0]` 出发 BFS，用 `apply_operation` 展开**全部可达状态与全部可达转移**
     （每个 operation 在每个状态上都合法，故转移数 = |可达状态| × |ops|）；
     200/200 个世界的可达集均 ≤ 512 状态，无一触及 400k 上限，**无跳过**；
  3. 对每条律 a，逐转移检查整数势 `P(x) = |supp(a) ∩ x|` 的增量是否为偶——
     这正是 GF(2) 律"支撑集奇偶和不变"的势函数形式，也是 `inv_closed` 的形状。
- 追加实验：对 13 个报警世界，用同一批 operations 随机走 **20,000 步**重跑 `analyse`，
  看律空间是否收敛到真空间。

---

## 结果

一致性：**187/200 世界一致，13/200 不一致**。不一致全部单向——引擎的律空间维数
**恒 ≥** 真律空间维数（合计 1832 vs 1788），从无反向。

按 (flavour, k) 分层，报警世界数 / 世界总数：

| flavour | k | 世界数 | 出现伪律 |
|---|---|---|---|
| planted | 2 | 99 | **0** |
| free | 2 | 36 | **0** |
| free | 3 | 34 | 5 |
| free | 4 | 31 | 8 |

k=2 完全干净，k≥3 有 13/65 出问题——这不是巧合，见下节。

13 个不一致世界（`eng_dim` = 引擎报的律空间维数，`true_dim` = 全可达转移上真正守恒的维数）：

| 世界种子 | k | 格数 | 轨迹步数 | zero_space 说 | 独立检验说 | 一致？ | 谁错 |
|---|---|---|---|---|---|---|---|
| 12 | 4 | 6 | 18 | dim 11，11 条律全部 `gf2_linear`，coverage 18/18 | dim 10；1 条在某合法转移上增量为奇 | 否 | zero_space |
| 21 | 4 | 8 | 12 | dim 23 | dim 18；9 条被证伪 | 否 | zero_space |
| 35 | 4 | 7 | 26 | dim 15 | dim 14；1 条被证伪 | 否 | zero_space |
| 60 | 4 | 8 | 9 | dim 25 | dim 21；**22** 条被证伪 | 否 | zero_space |
| 64 | 4 | 6 | 17 | dim 12 | dim 10；6 条被证伪 | 否 | zero_space |
| 80 | 4 | 8 | 16 | dim 23 | dim 18；10 条被证伪 | 否 | zero_space |
| 86 | 4 | 7 | 7 | dim 22 | dim 13；18 条被证伪 | 否 | zero_space |
| 92 | 3 | 7 | 7 | dim 17 | dim 13；13 条被证伪 | 否 | zero_space |
| 98 | 3 | 5 | 7 | dim 9 | dim 7；4 条被证伪 | 否 | zero_space |
| 111 | 3 | 4 | 4 | dim 9 | dim 6；7 条被证伪 | 否 | zero_space |
| 126 | 4 | 4 | 8 | dim 9 | dim 5；6 条被证伪 | 否 | zero_space |
| 142 | 3 | 4 | 13 | dim 7 | dim 6；2 条被证伪 | 否 | zero_space |
| 156 | 3 | 6 | 13 | dim 11 | dim 8；3 条被证伪 | 否 | zero_space |

其余 187 个世界：**没找到**任何不一致。这是一个真结果。

### 一个可以用手核对的反例（seed 111，k=3，4 格）

`zero_space` 报出（`scope: global`，payload `form: gf2_linear`，`coverage: 4/4`）：

```
(B@1 + C@1 + C@3) mod 2 = 0
```

轨迹只有 4 个状态，这条律在这 4 个状态上确实恒为 0。独立检验给出反例：

- 起点 `AACA` —— **轨迹自己走到过的状态**；
- 世界在该状态上提供的合法操作 `{cells: [0,1], shift: 2}`（parityworld 的每个 operation
  在每个状态上都合法）；
- 后继 `CCCA`；
- 支撑集在 `AACA` 上的重数为 0（偶），在 `CCCA` 上为 1（奇）。增量为奇 ⇒ 该泛函不守恒。

轨迹走到了 `AACA`，但在那里选了别的操作，于是这条律活了下来。
**谁错**：`zero_space`。不是消元错——我的独立 oracle 在 200/200 个世界上复现了它的 basis。
错在**断言的量词**：`Law`、README（"one linear conservation law each"）与
`candidates()` 发出的 `coverage = "n/n"` 都把"在这条采样轨迹上不变的向量"呈现为
"世界的守恒律"。同一个对象放进 `lp_potential` 的 `inv_closed`（跨 move instance、
与可达性无关）会被拒。

### 为什么恰好是 k≥3

k=2、shift=1 时，一个 operation 的差分向量与当前状态**无关**（每个被作用格的两个指示位
同时翻转），因此"每个 operation 至少被见过一次"确实张满了世界能做的一切。
k≥3 时，格子从颜色 i 走到 i+d，差分向量是 `e_(c,i) + e_(c,i+d)`——**依赖当前颜色**。
见过一个 operation 一次，只见到了它众多差分中的一个。

这直接推翻了 `fuzzlab/worlds/parityworld.py::generate` 里写下的那句自审：

> "Every operation is witnessed once before the random tail, so the observed difference
> matrix spans what the world can actually do rather than what a short random draw
> happened to sample."

对 k=2 成立，对 k≥3 不成立。实测：k=2 世界 0/135 受影响，k≥3 世界 13/65 受影响。

### 采样够长能不能补上

能，但引擎不知道自己够没够。对 13 个世界各随机走 20,000 步后重跑：

| seed | 原轨迹步数 | 原 dim | 20k 步后 dim | 真 dim |
|---|---|---|---|---|
| 111 | 4 | 9 | 6 | 6 |
| 126 | 8 | 9 | 5 | 5 |
| 86 | 7 | 22 | 13 | 13 |
| 60 | 9 | 25 | 21 | 21 |
| 21 | 12 | 23 | 18 | 18 |

13/13 全部收敛到 `true_dim`。所以这不是"引擎算错了"，而是
**引擎没有表达"证据不足"的位置**：`coverage` 字段填的是
`n_observed/n_observed`，恒等于 100%，与证据量无关。一条只被 4 个状态支持的律，
和一条被全可达空间支持的律，发出的 candidate 在这个字段上无法区分。

---

## 只有交叉才能暴露的不一致

这是本工单真正要的那一条。**有两处，两处都在两套测试的盲区内，且盲区是结构性的。**

### X-1 · 量词缺口：两套检验用的是同一份证据

- `engines/zero_space/__init__.py::run` 调 `verify(result, states)`，
  `verify` 在**同一条 `states`** 上重算每条律。README 称之为
  "Soundness has an independent check on top"——独立于消元，不独立于证据。
- `fuzzlab/props/zero_space.py` 四条不变式（`laws_hold_on_trajectory`、
  `law_space_is_complete`、`rank_nullity`、`membership_agrees`）**全部**从
  `world.states` 重算。它的 GF(2) 实现确实独立（`oracles/gf2.py` 的文件头把这条纪律
  写得很清楚），但**证据集合与被检者完全相同**。
  `law_space_is_complete` 拿引擎的 basis 去比 `gf2.null_space(轨迹差分)`——
  按定义两者必然相等，我也实测 200/200 相等。

于是：一条"在采样轨迹上守恒、被世界的转移关系证伪"的律，
**`zero_space.verify` 与 fuzzlab 现有四条不变式在数学上都不可能发现**——
它们问的是"这个向量在这条轨迹上是否不变"，答案永远是"是"。
要发现它，必须引入轨迹之外的转移，而这正是 `lp_potential` 的量词所在。
`fuzzlab/BUGS.md` 的结论"Verdict: no engine defect found"在这个方向上没有证据支持。

### X-2 · `scope` 标签断言了一个它没验过的出处

`local_laws()` 按**支撑位置**分类（落在单个 cell 的颜色组内 ⇒ `cell_local`），
README 与 docstring 却按**出处**解释（"laws about the *encoding*"，
"cell 3 holds exactly one of {R, B}"）。两者只在支撑集是**整组**时重合。

实测（200 个世界，1271 条 `cell_local` 律）：

- **942** 条支撑集是整组——真的是编码律，恒真，我的检验也从未证伪其中任何一条（0/50 在
  报警世界里被证伪）；
- **329** 条支撑集是**真子集**（k=2 有 112 条，k=3 有 60 条，k=4 有 157 条）。
  用 `oracle.in_span` 对照引擎自己的 `cell_local_subspace()`：这 329 条**没有一条**
  落在编码律张成的空间里。它们是世界事实（"cell 2 从不为 A"），不是编码事实。
  在报警世界里，被证伪的 51 条 `cell_local` 律**全部**出自这一类。

后果有两层，都只有交叉视角看得见：

1. **真事实被藏起来**。`analyse` 把这些律归入 `cell_local`，消费者若按 README 读
   `global_laws()` 为"世界守恒什么"，就会漏掉它们。k=2 时它们是**真的**世界事实
   （k=2 轨迹空间 = 真空间，见上），被错误地当作编码噪声商掉。
2. **同一模块内两种"编码律"定义**。`analyse` 用 `local_laws()`（任意在张成内的子集）
   商掉；`equivalent_modulo_encoding` 用 `cell_local_subspace()`（只有整组）商掉。
   两个子空间在 Fixture B 上恰好相同（无单色格），于是
   `engine-rig/tests/test_zero_space.py` 的 15 个测试全在 Fixture B 上跑，
   看不见这个分叉。fuzzlab 那边则**从不对 `scope` 做任何断言**——
   它只把 `scope` 当作 finding 的元数据附带上去。

两套测试各自都不问"`cell_local` 这个标签是不是真的"。

---

## 打不出结论的地方（以及为什么）

- **只覆盖了 `parityworld`**。`gridworld` / `blockworld` / `hypset` / `jumpgraph` 未测——
  电池里也不喂给 `zero_space`。对 ARC 真实轨迹的行为，本复核**没有证据**。
- **没有做反方向**：`lp_potential` 的 pagoda 证书没有拿 GF(2) 视角复核。
  E11 的另一半（"lp_potential 的证书 ← zero_space/线性代数视角"）仍是空的。
- **我的"真"律空间量词比 `lp_potential` 的弱**。我量的是"从给定初态可达的全部转移"，
  `check_exactly::inv_closed` 量的是"全部 move instance，与可达性无关"。
  我选弱量词是为了让反例无可争辩（每个反例的起点都是真可达状态，91/102 更是轨迹自己
  走到过的）。代价：**102 这个数是下界**，用强量词只会更多。
- **不知道有没有伪律流到下游**。没有检查任何 arm 的 `candidates.jsonl` 里是否已经
  躺着这类律，也没有检查是否有 manual 继承了它。这需要翻主工作树的产物，超出本工单范围。
- **发现 2 的"世界事实"判定依赖 `cell_local_subspace()`**——引擎自己的定义。
  若这个定义本身就该改（比如编码律本就该包含任意子集），那 X-2 就退化为文档问题
  而非标签问题。我倾向前者（子集是偶然事实、整组是恒真），但这是判断，不是证明。
- **移植正确性未被第三方复核**。`increment_is_even` 是我写的，没有第二个实现对照。
  它只有三行，反例可手算复核（seed 111 那条我在上面逐状态写出了），但严格说，
  这一路的独立性上限就是这三行。
