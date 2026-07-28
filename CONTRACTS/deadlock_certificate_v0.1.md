# deadlock_certificate_v0.1.md

**Version:** 0.1 · **Status:** 草案，等 `engine-rig` 会签。
**发射端未实现，且不由本轨道实现** —— 见《谁写哪一半》。

**Schema id:** `deadlock_carver/conditional_unsolvability_certificate@1`

**消费端可执行形态**：`theory-compiler/src/theory_compiler/deadlock_certificate.py`
（配 `strips.py` 与 `strips_encoding.py`）。文档与它不一致时，以它为准并把文档
当缺陷。

---

## 为什么需要这份契约

`lp_potential` 与 `ic3_pdr` 回答的是同一个问题：**从 `s₀` 出发能不能到目标**。
`deadlock_carver` 回答的是另一个，而 Theoria 1.9 已经说清楚哪个在野外更有用——
整局不可解是稀罕事，死角遍地都是，每一片剪枝区域都是一条**带条件的小型不可解
定理**：

```
<pattern>  AND  not-goal   =>   dead
```

「带条件」是关键词。本份证书对 `s₀` 一个字都不说。它说的是：**无论你在哪**，
只要模式成立，你已经输了。用的夹具 `sokoban-open4far` 恰恰是**可解的**——这正是
选它的理由。在一局本来就输定的关卡上证一条死区定理，句句为真，什么也没证明。

---

## 文档格式

```json
{
  "schema": "deadlock_carver/conditional_unsolvability_certificate@1",
  "claim": "every reachable state containing at(b1,c12) AND at(b2,c13) is dead",
  "conclusion": "at(b1,c12) AND at(b2,c13) AND not-goal => dead",
  "domain": "sokoban",
  "problem": "sokoban-open4far",
  "pattern": [["at", "b1", "c12"], ["at", "b2", "c13"]],
  "pattern_text": "at(b1,c12) AND at(b2,c13)",
  "closure": "deleting_actions_blocked",
  "n_deleting_actions": 4,
  "blocked_actions": [
    {"action": "(push c11 c12 c13 b1 right)", "action_atom": "clear(c13)",
     "pattern_atom": "at(b2,c13)", "reason": "mutex_with_pattern"}
  ],
  "goal_conflict": {"pattern_atom": "at(b1,c12)", "goal_atom": "at(b1,c42)",
                    "why": "mutex: the two can never hold in the same reachable state"},
  "coverage": "112/112",
  "produced_by": "engine-rig/engines/deadlock_carver"
}
```

| 字段 | 含义 | 必需 |
|---|---|---|
| `schema` | 必须精确等于上面那个字符串 | 是 |
| `domain` / `problem` | 定理所属的接地任务；与消费端自己接地的那份必须同名 | 是 |
| `pattern` | 合取的地面原子数组，每项 `[谓词, 参数...]` | 是 |
| `closure` | `no_deleting_action` 或 `deleting_actions_blocked` | 是 |
| `pattern_text` | 人读渲染 | 否，**但给了就必须与 `pattern` 一致**，见下 |
| `n_deleting_actions` / `blocked_actions` / `coverage` | 生产方的账 | 否，**且不予采信**，只用于交叉核对 |
| `goal_conflict` / `claim` / `conclusion` / `produced_by` | 人读的 | 否 |

**`pattern_text` 若与 `pattern` 不符是致命错误，不是笔误。** 读者相信的是那一行；
机器读的是另一行；两者打架时唯一安全的动作是拒绝。

**没有动作集字段，这是有意的**，与 `ic3_certificate_v0.1` 的「没有 `moves` 字段」
同一条纪律，理由也同一条：闭包只对**某个转移关系**才谈得上，关系不能来自断言闭包
的同一份文档——那等于让证书对着自己挑的动作集闭合。消费端自己解析并接地 PDDL
（`theory-compiler/src/theory_compiler/strips.py`，`:strips :typing` 子集，
子集外一律报错而不近似）。

---

## 两条义务，以及为什么生产方的账不算数

消费端在任何下游使用之前，把两条**重新算一遍**：

| 义务 | 重算内容 | 失败时 |
|---|---|---|
| **闭包** | 每个含该模式的良构态，每个在该态合法的地面动作，落点仍含该模式 | 拒绝，**并给出见证**（哪个态、哪个动作、落到哪、共几条逃逸） |
| **排除目标** | 没有一个含该模式的良构态是目标态 | 拒绝，并给出那个态 |

**「良构」而不是「可达」。** 生产方的主张是关于可达态的，而只在可达集上复核会让
闭包义务**循环**——你所闭合的那个集合正是靠闭合算出来的，这与 `ic3_certificate`
拒绝在可达集上验归纳是同一条理由。所以两条义务跑在整个**良构**状态空间上：
每样东西各占一格、没有两样东西同格。本夹具上良构态 3360 个，可达态 3352 个。

**良构不是方便，它就是 h² 的内容。** 生产方从动作集用 h² 不动点导出「一格至多放
一样东西、一个箱子只在一处」；消费端从另一头到达同一处——把状态**重新表示**成
一物一格的元组（`strips_encoding.py`），于是那些互斥事实成了数据的形状而不是待证
的引理。这一步本身要检查，不能假设，`strips_encoding.verify` 穷举核对：3360 个良构
态 × 112 个地面动作 = 376,320 对，编码的守卫必须与 `pre ⊆ atoms` 逐对一致，编码的
效果必须与 `(atoms \ del) ∪ add` 逐对一致，且每个可达态都必须是良构元组。

**良构在本夹具上是有承重的。** 把它丢掉，闭包对 `at(b1,c12) AND at(b2,c13)` 就是
**假的**：两个退化态（人站在被推的箱子里）能推出模式。所以它作为假设进了 Lean
定理，而不是被悄悄抹掉。

**模式无人满足的证书一律拒。** 两条义务会空空地全过，`#print axioms` 会打印空集，
而它什么也没说。本仓库已经从另一个方向撞过一次这种「绿而假」（D-A3-007），
`recheck` 因此要求一个良构见证。

---

## 交叉核对：账不是义务，但账对不上说明谈的不是同一个世界

上表里「不予采信」的三个字段有另一种用途。它们不参与义务重算（`recheck` 一个都不
读），但 `cross_check` 会拿它们跟本轨道自己接地的结果对：

* `coverage` 的**分母**必须等于本轨道接地出的地面动作数（本夹具 112）；分子必须
  等于分母——只查了一部分的闭包主张不是闭包主张。
* `n_deleting_actions` 必须等于本轨道数出的「删除列表触及模式」的动作数。
* `blocked_actions` 点名的每一个动作，必须在本轨道的动作集里解析得到，且确实删除
  某个模式原子；本轨道数出的删除动作里，**一个都不许被漏掉不谈**。
* `closure: no_deleting_action` 而本轨道接地出删除动作，或反之，都是错。

任何一条对不上都抛错。理由：一条在**别的任务**上证出来的真定理，放到这个任务上是
一条关于错误世界的真定理。

---

## Lean 那一侧

三条定理，加两件非空展品：

```lean
theorem dead_closed  : wf s → Pat s → legal s m → wf (applyMove s m) ∧ Pat (applyMove s m)
theorem pat_no_goal  : Pat s → Goal s = false
theorem dead         : wf r → Pat r → ReachFrom r s → Goal s = false   -- 条件化不可达
theorem pat_witness       : 模式确实有良构态满足
theorem level_is_winnable : 这一局**是**能赢的，附一条 11 步的通关
```

`ReachFrom r` 从**任意** `r` 起步，不从 `s₀` 起步——这正是「条件化」在 Lean 里的
形状，也是与 pagoda / ic3 那两份**全局**不可达定理唯一的量词差别。
`level_is_winnable` 与 `dead` 并排放着：定理说的是这块模式致命，不是这局本来就输。

实测（`lean` 4.9.0，proof mode `computational`）：

| 模式 | 闭包形态 | 叶子目标 | 编译 | `#print axioms` |
|---|---|---|---|---|
| `at(b1,c11)` | `no_deleting_action` | 28,672 | 60s | **九条全空** |
| `at(b1,c12) AND at(b2,c13)` | `deleting_actions_blocked` | 1,792 | 4.2s | **九条全空** |

叶子数是 `格数 ^ 模式未钉住的槽位数 × 地面动作数`，所以**钉得越多越便宜**：钉住两个
箱子的模式比只钉一个的便宜十六倍。这是算出来的，不是写死的，超预算即拒绝生成，
不发一份编译不动的文件。

一条**负对照**照录：把 `Pat` 往里挪一格（`c12,c13` → `c22,c23`），同一份文件
`lean` 退出码非零、`sorryAx` 出现。「退出码 0 且公理集为空」因此不是摆设。

---

## 谁写哪一半

| 半边 | 归属 | 状态 |
|---|---|---|
| **发射**：`deadlock_carver` 把定理写成上面这份 JSON，落到 `engine-rig/interop/certificates/` | **`engine-rig`** | **未实现** |
| **消费**：解析 PDDL、自行接地、编码、两条义务重算、编译成 Lean | `theory-compiler` | 完成 |

**本轨道没有、也不会往 `engine-rig/` 里写一个字。** 与 `ic3_certificate_v0.1` 同一条
划法，同一条理由。

在发射端出现之前，本轨道的夹具
`theory-compiler/tests/fixtures/deadlock_open4far_*.json` 是**从贵方已经发布的候选行**
（`engine-rig/artifacts/candidates.jsonl`，`payload.producer == "deadlock_carver"`）
逐字段转录出来的；转录器
`theory-compiler/tools/transcribe_deadlock_certificates.py` 是可执行的，一项测试每次
重跑它并在漂移时判红。PDDL 域与问题两份文件也是**逐字节**拷贝，
`tests/fixtures/strips/PROVENANCE.json` 记着来源与 sha256，同样有测试盯着不许漂移。

---

## 会签请求

请 `engine-rig` 在 `PARTNER_SYNC.md` 上回一段：

1. 这份 schema **接受 / 改 / 拒**。主要待议点：`pattern` 用
   `[谓词, 参数...]` 数组还是用 `pattern_text` 那种渲染串（本轨道两者都读，但以
   数组为准）；以及 `coverage` 要不要从 `evidence` 提到顶层（本轨道两处都认）。
2. 若接受：`deadlock_carver` 的导出函数由贵方写进 `interop/certificate_export.py`，
   落到 `interop/certificates/`。本轨道的读取器一行不用改。
3. 一个**请求**而非要求：能否在 sokoban 之外再跑一个 `deadlock_carver`
   夹具？现在 16 条 `conditional_unsolvability` 候选行全部是 sokoban，
   于是本轨道的消费端也只在 sokoban 的谓词签名上跑通（其余签名一律报错，不近似）。
   多一个形状的任务，才谈得上这条通路是通用的。

**异轨道异步会签**：草案先落，本轨道不等待。会签前 `interop/certificates/` 里没有
deadlock 文档是正常状态。

---

## 消费端已知缺口（照录，不藏）

* **说明书写不下 sokoban（E-08）。** 本轨道的四形态是从 `theory.dsl` 共导的，而
  这条通路的世界来自 PDDL，不来自说明书。DSL 的**动力学**装得下 sokoban
  （`free(...)` 就是 `clear`，`toward(o,?d)` 就是 `adj`，push 同时移动箱子与人可写成
  两条同守卫、认领对象不相交的规则）；装不下的是**目标**——`goal:` 只收一个表达式，
  没有合取，也没有「地标集合」，而 sokoban 的胜利条件是「每个箱子各就各位」。
  在补上之前，这条通路以接地任务为界，而不是以说明书为界。
* **编码只认一种谓词签名**（`at-player/1`、`at/2`、`clear/1`），别的一律报错。
* **编码忠实性的那一步在 Python 里穷举，不在 Lean 里。** Lean 定理是关于**被编码
  系统**的；它与 STRIPS 任务一致这件事由 `strips_encoding.verify` 逐对核对。
  这与 `gen_lean._check_legality` 在棋子那条路上做的是同一件事，纪律相同，位置相同。
* **规模。** 叶子数随未钉住槽位指数增长，16 格 3 槽已经要 60s。本方法要上大棋盘，
  需要的是别的证明形状，不是更大的预算。
