# pagoda_certificate_v0.1.md

**Version:** 0.1 · **Status:** 草案，等 `theory-compiler` 会签。
**两端都已实现** —— 这份契约是补写规格，不是提议新格式。见《谁写哪一半》。

**Schema id:** `lp_potential/pagoda_certificate@1`

**发射端可执行形态**：`engine-rig/interop/certificate_export.py`（`build` / `write`），
再生驱动 `engine-rig/interop/export_certificates.py`。
**发射端参考读取器**：`engine-rig/interop/pagoda_reader.py`（仅标准库，
`engine-rig/tests/test_pagoda_reader.py` 23 项）。文档与它们不一致时，以代码为准
并把文档当缺陷。

---

## 为什么需要这份契约

`lp_potential/pagoda_certificate@1` 是本仓**最早**的跨轨道格式，也是**唯一一份
一直没有写下来的规格**。`ic3_certificate_v0.1.md:15-17` 已经点了这件事：

> `engine-rig/interop/certificates/` 里现在只有 pagoda 文档，schema
> `lp_potential/pagoda_certificate@1`，没有写下来的规格。那对一份格式就够了；对
> 两份不够。

现在是三份，而且**这一份是三份里唯一两端都跑通的**：贵方
`theory-compiler/src/theory_compiler/certificate.py:38` 钉着这个 schema 串，
`gen_lean.py` 从它出权重、出 Lean；本方 `interop/certificates/` 里有三份文档。
另外两份格式（ic3、deadlock）的发射端至今未实现，规格却先写好了；这一份反过来，
两端先跑通，规格欠着。**欠着的那一半是本文。**

补写规格不是形式主义。没有规格的时候，「格式对不对」只能靠读两边的代码互相比对，
而两边的代码**都是当事人**：发射端的 `certificate_export.verify()` 迭代的是文档
自己给的动作表，消费端的读取器是另一条轨道的私有实现。契约要钉死的正是两边
**都不许说了算**的那部分。

---

## 文档格式

```json
{
  "schema": "lp_potential/pagoda_certificate@1",
  "claim": "unsolvable_11011_to_01000",
  "conclusion": "no goal state is reachable from 11011",
  "invariant": "I(s) := potential(s) <= 0, where potential(s) = sum of w[i] over occupied i",
  "produced_by": "engine-rig/engines/lp_potential",
  "n_pos": 5,
  "initial_state": "11011",
  "goal_states": ["01000"],
  "weights_integer": [-1, 1, 0, 1, -1],
  "weights_rational": ["-1", "1", "0", "1", "-1"],
  "initial_potential": 0,
  "verified": true,
  "obligations": { "inv_init": {…}, "inv_closed": {…}, "goal_break": {…} }
}
```

| 字段 | 含义 | 必需 |
|---|---|---|
| `schema` | 必须精确等于上面那个字符串 | 是 |
| `n_pos` | 棋盘格数，位置是 `0 .. n_pos-1`，且必须等于每个位串的长度 | 是 |
| `initial_state` | 长度 `n_pos` 的位串，`"1"` 为占据 | 是 |
| `goal_states` | 位串数组，**非空**；主张是**没有一个**可达 | 是 |
| `weights_integer` | **按位置**一格一个整数，`weights_integer[i]` 是第 i 格的权重 | 是 |
| `initial_potential` | **声明的界** b。不变式是 `I(s) := potential(s) <= b` | 是 |
| `weights_rational` | LP 解出的精确有理数，字符串形式 | 否，**但给了就必须与整数权重差一个正的公倍数** |
| `claim` / `conclusion` / `invariant` / `produced_by` | 人读的，消费端只用于报错文本与出处 | 否 |
| `verified` | 生产方自己的判决 | 否，**且不予采信** |
| `obligations` | 生产方自己的义务记录，含逐条见证 | 否，**且不予采信**，见下 |

`potential(s) := Σ { weights_integer[i] : s[i] == "1" }`。权重是**整数**：LP 解出的
是有理数，按分母的最小公倍数整体放大再除以最大公约数。约束是齐次的，所以放大
保持有效性，而整数字面量正是生成的 Lean 证明想操作的东西。

**`initial_potential` 是声明，不是导出量。** 消费端必须把它当作界 b 读进来，然后
检查 `potential(initial_state) <= b`；**不许**自己从 `initial_state` 重算出 b。
这一条不是风格问题：`certificate_export.build` 恰好是把 b 写成 `potential(initial)`
的，所以生产方那一侧的 `inv_init` 读起来是「x <= x」——它自己的注释就这么写
（`certificate_export.py:109-112`）。把 b 当声明读，这条义务才重新变成一个检查；
把 b 重算出来，它就只是一个恒真式。**篡低了 b 的证书，只有前一种读法拦得住。**

---

## 三条义务，以及为什么生产方的自检不算数

消费端在任何下游使用之前，把三条重新算一遍，对**全状态空间**：

| 义务 | 重算内容 | 失败时 |
|---|---|---|
| `inv_init` | `potential(initial_state) <= initial_potential` | 拒绝：初始态就不在不变式里 |
| `inv_closed` | **自行接地的**每一条合法移动都满足 `w[dst] - w[src] - w[over] <= 0` | 拒绝，**并给出见证**（哪条 `jump(s,o,d)`、把势抬高了多少） |
| `goal_break` | 每个目标态都满足 `potential(g) > initial_potential` | 拒绝：不变式接纳了目标态 |

三条全过，蕴含的是**归纳不可达**：初始态在不变式里，不变式对每条合法移动封闭，
目标态都不在不变式里，所以目标态不可达。这是全部论证，不需要枚举可达集。

**为什么发射端自己的 `verify()` 不能当这个检查用。** `certificate_export.verify()`
会重算算术、忽略 `holds` 标志——这抓得住算错的和数，抓不住**前提**：它迭代的
动作表是**同一份文档自己给的那张表**，函数从头到尾没见过规则集。所以一份**删掉
了不方便的那条动作**的文档，它返回 `[]`。

这不是猜想。`engine-rig/tests/test_pagoda_reader.py::test_the_omission_forgery_passes_the_producer_and_fails_the_reader`
把它做成了一份具体的伪证：`pagoda_5_11011_to_01000` 的 `weights_integer[2]` 从 `0`
改成 `-1`，六条跳跃里 `jump(1,2,3)` 与 `jump(3,2,1)` 就都把势抬高 1，把这两条见证
从 `obligations` 里删掉，再把剩下四条的 `w_src/w_over/w_dst/delta/holds` 重算一遍、
`n_checked` 改成 4、`checked_over` 改成「the 4 move instances this document lists」
（E16 之后这句话是**诚实的**）、`weights_rational[2]` 同步改成 `"-1"`。界不用动
（`potential(11011)` 里没有第 2 格），目标态也不用动（`potential(01000)` 就是 `w1`），
于是 `inv_init` 与 `goal_break` 照旧成立。这份文档**内部完全自洽，并且是错的**：

```
certificate_export.verify(forged)              -> []            # 通过
pagoda_reader.check(forged, geometry=文档自带的动作表) -> []            # 通过
pagoda_reader.check(forged)                    -> ['inv_closed: jump(1,2,3) raises the potential by 1',
                                                   'inv_closed: jump(3,2,1) raises the potential by 1']
```

中间那一行是这条纪律的非空性证明：**同一个读取器，只把「动作从哪来」换掉，判决就
翻转**。所以规格里写死的不是「要检查 inv_closed」，是**「动作关系必须由消费端自己
接地」**。

（贵方读取器 `certificate.py:155-166` 已经更进一步：它把文档列出的见证与自行接地
的集合**双向**比对，缺一条就拒，并且报错文本里写着「The producer's own verifier
does not check witness completeness, so this reader does」。这一条本契约不要求，
但记录在案——它抓得住的是同一类攻击，而贵方先做到了。）

---

## 没有规则集字段，这是有意的

文档里**没有**动作集、没有邻接表、没有规则。与 `ic3_certificate_v0.1` 的「没有
`moves` 字段，这是有意的」同一条纪律，理由也同一条：不变式只对**某个转移关系**
才谈得上归纳，所以关系不能来自断言归纳的那份文档——那等于让证书对着自己挑的动作集
闭合。

那么关系从哪来？**从带外。** `@1` 这个版本覆盖的是**一族**世界：`n_pos` 格的一维
孔明棋，跳跃关系为

```
{ (src, src+1, src+2) : 0 <= src+2 < n_pos } ∪ { (src, src-1, src-2) : 0 <= src-2 < n_pos }
```

一条移动把 `src` 与 `over` 清空、把 `dst` 填上。`n_pos` 定死这一族里的哪一个。
读取器把这段几何**自己写一遍**（`pagoda_reader.py:jump_moves`，与
`interop/peg1d.py:move_instances` 是两份独立的实现，重复是故意的），并把这个假设
**声明出来**（`pagoda_reader.GEOMETRY == "peg1d_jump"`），而不是假装文档已经把它
定了。

**因此：一份 `@1` 文档只在读者已经知道它谈的是一维孔明棋时才有意义。** 别的规则族
要新的 schema id（`@2` 或另起一个），不许靠加字段悄悄扩张——加一个「规则集」字段
就是把关系放回文档里，那正是上面拒绝的事。

`inv_closed` 跑的是**全状态空间上的所有移动实例**，不是可达部分：一个只在你碰巧
到过的态上封闭的不变式，是靠假设它要证的东西来封闭的。

---

## 谁写哪一半

| 半边 | 归属 | 状态 |
|---|---|---|
| **发射**：`lp_potential` 把 LP 解出的权重写成上面这份 JSON，落到 `engine-rig/interop/certificates/` | **`engine-rig`** | **完成** |
| **消费**：读取、三条义务重算、编译成 Lean | `theory-compiler` | **完成**（`certificate.py` + `gen_lean.py`，自 `f58959e7`，2026-07-28） |

**这是三份证书契约里唯一两端都完成的一份。** 另外两份（ic3、deadlock）是贵方先写
规格、发射端在本方未实现；这一份是两端先跑通、规格欠着。三份加起来，跨轨道接口
这件事上两条轨道各欠对方一半，方向正好相反。

本方**没有、也不会往 `theory-compiler/` 里写一个字**。上表「消费」那一行的状态是
**读出来的**，不是本方做的：`engine-rig/tests/test_pagoda_reader.py::test_the_consumer_side_names_the_schema_we_stamp`
只读贵方那个文件、断言 schema 串还在，贵方的树不在时跳过。与 `recheck/anchors.py`
读贵方 Lean 步表同一条划法（D-030：读那边，写零字节）。

---

## 会签请求

请 `theory-compiler` 在 `PARTNER_SYNC.md` 上回一段：

1. 这份规格 **接受 / 改 / 拒**。它是照两端**已有**代码补写的，所以「拒」的真实
   含义是「本方读取器与这份描述不符」——那样的话请指出哪一条，以代码为准改本文。
2. **`initial_potential` 当声明读还是当导出量重算**，是主要待议点。本文要求前者，
   理由在《文档格式》末段：后者会让 `inv_init` 变成恒真式，篡低了界的证书就没人拦。
   贵方 `certificate.py:138-142` 现在是哪一种？
3. `@1` 只覆盖一维孔明棋跳跃族，这一条要不要写进 schema id 本身（例如
   `@1` 之外另立 `peg1d` 标签）。本方倾向不改——`@1` 已在两端的代码里钉死，
   改 id 是破坏性的；这条限制写在契约里就够。

**异轨道异步会签**：草案先落，本方不等待、不催。会签前这份文档的状态是「照两端
现状补写的规格」，不是「新提议」——两端的代码不因为没会签就停。

---

## 已知缺口（照录，不藏）

1. **线性 pagoda 可靠但不完备**（`engine-rig/DECISIONS.md` D-014）。有些确实
   不可解的构型没有任何线性 pagoda 函数，这个格式对它们**发不出证书**，而不是
   发一份说「未知」的证书。贵方那个 5 格夹具的原始目标 `count(Peg, alive=true) = 1`
   正好撞上这一条：不可解是真的，线性 pagoda 证不了，把目标收窄到具体格子（1 或 3）
   才有证书。全表在 `engine-rig/interop/README.md`。
2. **字节可复现的保证是有条件的**。`export_certificates.py --check` 在本机上三份
   文档逐字节重建成功，但 LP 走的是 `scipy.optimize.linprog(method="highs")` 的
   浮点解，再用 `Fraction.limit_denominator(1000)` 吸回有理数。买到的保证是
   「同一个 scipy/HiGHS 构建 ⟹ 同样的字节」，不是「哪儿都一样的字节」。
3. **本契约管不到「peg1d 是不是你要的那个世界」**。三条义务全过，蕴含的是
   「在上面那族跳跃关系下不可达」。这族关系是不是消费端关心的那个世界的规则，
   契约不裁决，读取器也不裁决——它只是把这个假设说出来。
4. **`interop/certificates/` 里三份文档，贵方测试只消费其中一份**
   （`pagoda_5_11011_to_00010.json`）。另外两份没有消费端。不是缺陷，是照录。
