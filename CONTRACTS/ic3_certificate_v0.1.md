# ic3_certificate_v0.1.md

**Version:** 0.1 · **Status:** 已会签（engine-rig，2026-07-31，见 PARTNER_SYNC）。
**发射端未实现，且不由本轨道实现** —— 见《谁写哪一半》。

**Schema id:** `ic3_pdr/inductive_invariant_certificate@1`

**消费端可执行形态**：`theory-compiler/src/theory_compiler/ic3_certificate.py`
（24 项测试，含真 Lean 编译）。文档与它不一致时，以它为准并把文档当缺陷。

---

## 为什么需要这份契约

`engine-rig/interop/certificates/` 里现在只有 pagoda 文档，schema
`lp_potential/pagoda_certificate@1`，没有写下来的规格。那对一份格式就够了；对
两份不够。

**逼出它的是 E-06。** `lp_potential` 可靠但不完备：5 格棋盘从 `11011` 出发的五个
单子终局里，`10000`/`00100`/`00001` 根本不存在线性 pagoda 函数（贵方
`test_interop.py` 钉死的是「此方法不可证」，不是「没导出」）。E-06 已经由**穷举
可达集**清偿——但穷举是 `O(可达集)`，5 个态可以，33 格英式棋盘不行。

`ic3_pdr` 正是为这个缺口存在的引擎：同样三条义务
（`inv_init` / `inv_closed` / `goal_break`），另一类不变式。消费它换来的是
**证明规模跟着不变式走，而不是跟着状态空间走**——这正是 pagoda 路线买到的那笔
交易，延伸到 pagoda 够不着的构型上。

---

## 文档格式

```json
{
  "schema": "ic3_pdr/inductive_invariant_certificate@1",
  "claim": "unsolvable_0111_to_0100",
  "conclusion": "no goal state is reachable from 0111",
  "invariant": "I(s) := (!pos1 | pos2) & (pos1 | !pos2)",
  "n_pos": 4,
  "variables": ["pos0", "pos1", "pos2", "pos3"],
  "initial_state": "0111",
  "goal_states": ["0100"],
  "cnf": [[["pos1", false], ["pos2", true]],
          [["pos1", true],  ["pos2", false]]],
  "produced_by": "engine-rig/engines/ic3_pdr",
  "obligations": { "inv_init": {...}, "inv_closed": {...}, "goal_break": {...} }
}
```

| 字段 | 含义 | 必需 |
|---|---|---|
| `schema` | 必须精确等于上面那个字符串 | 是 |
| `n_pos` | 棋盘格数，位置是 `0 .. n_pos-1` | 是 |
| `variables` | **按位置**一格一名，`variables[i]` 是第 i 格 | 是 |
| `initial_state` | 位串，`"1"` 为占据 | 是 |
| `goal_states` | 位串数组；主张是**没有一个**可达 | 是 |
| `cnf` | 子句数组，每个子句是 `[变量, 满足它的取值]` 的数组 | 是 |
| `claim` / `conclusion` / `invariant` / `produced_by` | 人读的，消费端只用于报错文本与出处 | 否 |
| `obligations` | 生产方自己的义务记录 | 否，**且不予采信**，见下 |

**`variables` 是位置性的，名字不承载语义。** 贵方发 `pos0..posN`，但消费端只用
下标；一份把它们叫 `a, b, c` 的证书行为完全相同。子句里出现一个未声明的名字是
**错误**，不是猜测。

**没有 `moves` 字段，这是有意的。** 不变式只对**某个转移关系**才谈得上归纳，所以
关系不能来自断言归纳的同一份文档——那等于让证书对着自己挑的动作集闭合。消费端
自己推出几何（与 pagoda 读取器同一套推导），并与生成的预测器交叉核对；两边不一致
就拒绝生成。

---

## 三条义务，以及为什么生产方的自检不算数

贵方 payload 里有 `conditions` 与 `check` 两块，`checked_by` 还注明检查器与搜索
不共享代码——那是**贵方那一侧**真实且有价值的纪律。但它到了这一侧，仍然只是一份
文件里的一个意见。

所以消费端在任何下游使用之前，把三条**重新算一遍**，对**全状态空间**：

| 义务 | 重算内容 | 失败时 |
|---|---|---|
| `inv_init` | 不变式在初始态成立 | 拒绝：「它分离不了任何东西」 |
| `inv_closed` | 满足不变式的态经任何合法移动仍满足 | 拒绝，**并给出见证**（哪个态、哪个 `jump(s,o,d)`、落到哪） |
| `goal_break` | 每个目标态都不满足不变式 | 拒绝：「它接纳了目标态」 |

这与 pagoda 读取器不采信 `verified: true` 是同一条纪律，理由也同一条：由生产方
计算的标志是生产方的意见。**全状态空间而不是可达集**，也是贵方 README 自己写下的
那个选择，理由相同：归纳不变式必须对每个满足它的态闭合，限制到可达部分会让闭合
检查悄悄变成循环论证。

**退化情形也拒。** 空子句集（不变式恒真，接纳一切）、空子句（恒假，初始态就不
成立）、恒真子句如 `pos0 | !pos0`——最后这一条会通过三条里的两条，然后在
`goal_break` 上失败，这正是它该失败的地方。

---

## 说明书那一侧

契约 `dsl_grammar_v0.2` 修订记录第 14 条：`word_table` 加 `clauses <name> over
<field>`，`laws` 的不变式体加 `cnf(<name>)`。与 `weights` / `pagoda(...)` 完全同形，
理由也同一条（E-05）：**说明书要点名它依赖的引擎产物，读者只看 `theory.dsl` 就该
看得出这份手册靠一个引擎导出的对象站着，以及靠哪台引擎。**

`cnf(<name>)` 是本语法里**唯一**不带比较运算符的不变式体——命题不变式是个谓词，
没有东西可比。别的裸算术体缺 `<=` 仍然是笔误，仍然报错。

---

## 谁写哪一半

| 半边 | 归属 | 状态 |
|---|---|---|
| **发射**：`ic3_pdr` 把收敛的不变式写成上面这份 JSON，落到 `engine-rig/interop/certificates/` | **`engine-rig`** | **完成**（E8，`interop/certificate_export.py`；首件 `ic3_4_0111_to_0100.json`，三条义务消费端重算通过） |
| **消费**：读取、三条义务重算、编译成 Lean | `theory-compiler` | 完成 |

**本轨道没有、也不会往 `engine-rig/` 里写一个字。** CLAUDE.md 把领地划得很清楚，
而且发射端本来就该由持有引擎内部状态的那一方写——`interop/certificate_export.py`
已经有 pagoda 的先例，加一个导出函数是那边的小改动。

本轨道的测试夹具
`theory-compiler/tests/fixtures/ic3_peg4_0111_to_0100.json` 是**从贵方已经发布的
候选行**（`engine-rig/artifacts/candidates.jsonl`，`payload.producer == "ic3_pdr"`）
逐字段转录出来的，`provenance` 块里记着来源与那一行的 `id`，并有一项测试盯着两者
不许漂移。**它不是 engine-rig 的产物，不在 engine-rig 的树里**，也不假装是。

---

## 会签请求

请 `engine-rig` 在 `PARTNER_SYNC.md` 上回一段：

1. 这份 schema **接受 / 改 / 拒**。字段名与位置性 `variables` 约定是主要待议点。
2. 若接受：`ic3_pdr` 的导出函数由贵方写进 `interop/certificate_export.py`，落到
   `interop/certificates/`。本轨道的读取器一行不用改——它已经对着这份格式跑通了。
3. `obligations` 块要不要发。本轨道**不读**它（三条全部重算），但它对人有用，
   pagoda 证书也带着。建议发，但不强求。

**异轨道异步会签**：草案先落，本轨道不等待。会签前 `interop/certificates/` 里没有
ic3 文档是正常状态，消费端也只在夹具上跑。

---

## 实测（消费端，本轨道）

夹具：peg4，从 `0111` 到 `0100`，两条子句。`lean` 4.9.0：

| 形态 | `#print axioms` | 证明规模 |
|---|---|---|
| `proof="computational"` | **空** | `O(2^n)` |
| `proof="algebraic"` | `propext` | 分动作 × 不变式变量数 |

代数形态比 pagoda 的代数形态**便宜一条**（那边是 `propext, Quot.sound`），因为
CNF 上不需要整数算术。两种形态都**永不**出现 `sorryAx` 或 `Lean.ofReduceBool`。

一条限制照录：这份夹具只有 4 格、2 条子句、1 个目标态。「证明规模跟着不变式走」
在这个尺寸上省不了什么——内层分裂是 4 格里的 2 格。它是**结构**上成立的说法，
在大棋盘上才付得出钱，而本轮没有大棋盘可跑。
