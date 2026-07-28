# STATUS — theory-compiler track

## C4 达成：死锁定理与 IC3 不变量都进了 Lean，公理集为空 (2026-07-28)

分支 `agent/c4-deadlock-lean`，base `ded9cd7`，工人 `W-1541`。全文见
[`runs/20260728T080019Z-C4-deadlock-lean/RUN_STATE.md`](runs/20260728T080019Z-C4-deadlock-lean/RUN_STATE.md)。

```
theory-compiler   288 passed   (THEORIA_REQUIRE_LEAN=1，含 11 项真 Lean 编译)
                  224 -> 288   （+64，全部本轮新增）
python -m tools.verify_c4      四个案例全绿，含一次负对照
```

### 验收：两类证书各至少一条，`lean` 4.9.0 实跑

| 证书 | 定理 | 叶子目标 | 编译 | `#print axioms` |
|---|---|---|---|---|
| `deadlock_carver` `at(b1,c11)`（`no_deleting_action`） | 三条 + 两件展品 | 28,672 | 60s | **九条全空** |
| `deadlock_carver` `at(b1,c12) AND at(b2,c13)`（`deleting_actions_blocked`） | 同上 | 1,792 | 4.2s | **九条全空** |
| `ic3_pdr` peg4 `computational` | `inv_init`/`inv_closed`/`inv_all`/`unsolvable` | — | <1s | **四条全空** |
| `ic3_pdr` peg4 `algebraic` | 同上 | — | <1s | `propext`（设计如此） |

无 `sorry`，无 `native_decide`，无 `Classical.choice`。

### 两半并不对称：IC3 那半上一轮就做完了

P-10 已经把 ic3 消费端做全（读取器、`cnf(...)` 语法、`_ic3_lean`、24 项测试）。
本轮对它做的是**复跑取证**：本机此前 `elan` 没有默认工具链，`shutil.which("lean")`
找得到而 `lean` 跑不动，历史上的绿是在别的机器上取的。设了默认工具链后重跑，四条
公理集实测落盘在 `runs/.../verify/EVIDENCE.json`。**一行没重写。**

工程量几乎全在死锁那一半，那一半此前是零。

### 死锁：条件化定理，以及它带来的三个新问题

```lean
theorem dead : ∀ (r s : St), wf r = true → Pat r = true → ReachFrom r s → Goal s = false
```

`ReachFrom r` 从**任意** `r` 起步而不是从 `s₀`——这就是「条件化」在 Lean 里的形状，
与 pagoda / ic3 那两份全局不可达定理唯一的量词差别。Theoria 1.9 的原话是「整局
不可解是稀罕事，死角遍地都是」。

**问题一：世界从哪来。** 16 条死锁候选行全部是 sokoban，而说明书写不下 sokoban。
勘察结论（两个只读 subagent，独立复核）：DSL 的**动力学**装得下——`free(...)` 就是
`clear`，`toward(o,?d)` 就是 `adj`，push 同时移动箱子与人可写成两条同守卫、认领对象
不相交的规则；装不下的是**目标**，`goal:` 只收一个表达式，没有合取也没有地标集合，
而 sokoban 要「每个箱子各就各位」。于是接口下移一层：本轨道自己解析 + 接地 PDDL
（`strips.py`），证书只提供模式。这条缺口记为 **E-08**，不是绕过，是照录。

**问题二：原子集合上定理是假的。** 没什么拦得住一个集合同时含 `at(b1,c12)` 与
`clear(c12)`。生产方为此要 h² 不动点；本轨道从另一头到同一处，把状态重表示成
**一物一格的元组**，互斥事实成了数据的形状。这一步穷举核对：3360 良构态 × 112 动作
= 376,320 对，守卫与效果逐对对齐，且 3352 个可达态全部良构。

**问题三：良构不是装饰。** 丢掉它，闭包对那条 pair 模式就是**假的**——两个退化态
（人站在被推的箱子里）能推出模式。所以 `wf` 作为假设进了定理，并有一项测试盯着那两个
反例还在。

（措辞精确一句：两条义务**搜索**的是 3360 个良构态，**判定**发生在模式接受的那些态上
——pair 14 个、corner 210 个；Lean 那边的分裂是「未钉住槽位的取值 × 112 个动作」。
「在 3360 个态上重算」是省略说法，展开是这个。）

### 最该记住的一条：检查链断在最后一步，是对抗式复核找出来的

完工后跑了一次对抗式复核（只读，只许证伪）。它**没能推翻定理**——独立重写了一个
sokoban 接地器，独立数出 112 / 3360 / 3352，对**已发射的** `pair.lean` 逐对核对
376,320 组守卫与效果，0 处不符——但它找到一条真的断链，并用变异实验证明了：

`verify` 检查编码对任务，`recheck`/`cross_check` 检查证书对编码，而**从编码到发射出去
的 Lean 文本之间那一步渲染，没有任何东西在读**。复核只改了 `_world` 一行，让每条
`push` 的 `applyMove` 分支发 `=> s`：`verify` 过、`cross_check` 过、`recheck` 过、
`lean` 退出 0、`dead` 公理集**为空**——一条关于「箱子永远不动的世界」的漂亮定理，
全套非 Lean 测试一个都没抓到。**与 D-A3-007 同形**：上次是不变式退化成 `true`，
这次是转移关系退化成恒等。

已加 `gen_lean_deadlock.reread`：用发射时的文法把文本**解析回来**，逐项与已检查的
编码比对（构造子表、每条 `legal` 守卫、每条 `applyMove` 赋值、`St.clear`、`wf`、
`Pat`、`Goal`、`s0`），并在全部 4096 个可编码态上求值比对 `wf`/`Pat`/`Goal`；
生成器还拒绝对未经 `verify` 的编码发射。四项变异测试留在 `TestEmissionIsRead`。
同一次复核指出负对照红得不是地方，也已改成整份重新生成——详见 D-TC-028。

### 另一条：条件化定理有它专属的「绿而假」

D-A3-007 那份 `I := true` 的教训是：空公理集分辨不出没证东西的证明。条件化定理的
同形失效模式是**条件无人满足**——每条义务空空地全过，`#print axioms` 打印空集。
`recheck` 因此要求良构见证，生成物里发 `pat_witness`。

还有一层：在一局本来就输定的关卡上证死区定理，句句为真、什么也没说明。所以夹具选的是
**可解的** `sokoban-open4far`，生成物里发 `theorem level_is_winnable`，附一条 11 步
逐步 `by decide` 的通关，与 `dead` 并排。

**负对照**：换一个不是死区的模式（`c12,c13` → `c22,c23`）**整份重新生成**，`lean`
退出码非零、`sorryAx` 出现，失败点落在 `closed_pinned` 上——正是那几条能把箱子分开的推。
空公理集这条检查因此不是摆设。（为什么不能「在成品里改一处再编译」，见 D-TC-028。）

### 交叉核对：账对不上就拒绝

证书的 `coverage` / `n_deleting_actions` / `blocked_actions` **一个都不参与义务重算**，
只用于核对两边谈的是不是同一个任务：本轨道接地出 112 个地面动作（48 move + 64 push），
必须等于 `evidence.coverage` 的分母；证书点名的 4 个被挡 push 必须逐个在本轨道的动作
集里解析得到且确实删除模式原子；本轨道数出的删除动作一个都不许被漏掉不谈。十项负向
测试覆盖这些路径。

### 新增交付

| 文件 | 角色 |
|---|---|
| `CONTRACTS/deadlock_certificate_v0.1.md` | schema 草案 + 会签请求（**发射端仍是 engine-rig 的**） |
| `src/theory_compiler/strips.py` | 独立的 typed-STRIPS 解析 + 接地，子集外一律报错 |
| `src/theory_compiler/strips_encoding.py` | 一物一格编码 + 穷举忠实性核对 + 最短通关 |
| `src/theory_compiler/deadlock_certificate.py` | 读取器、两条义务重算、交叉核对、`bite` 账 |
| `src/theory_compiler/generators/gen_lean_deadlock.py` | Lean 发射器（只有 `computational`） |
| `tools/transcribe_deadlock_certificates.py` | 从候选行转录夹具，可执行、被测试重跑 |
| `tools/build_deadlock_lean.py` / `tools/verify_c4.py` | 单条构建 / C4 验收全跑 |
| `tests/test_strips.py` / `test_deadlock_certificate.py` / `test_gen_lean_deadlock.py` | 64 项，含 `TestEmissionIsRead` 的四条变异 |

### 未清偿

* **E-08：说明书写不下 sokoban。** 目标合取（或地标集合）缺失是硬阻塞；附带
  `conflict.disjointness_reason` 缺 `free(t)` 对 `X.pos = t` 的判据，
  `gen_pddl._extract_pred_pddl` 仍对不认识的子句静默丢弃。在补上之前，这条通路以
  接地任务为界而不是以说明书为界，**四形态共导在这条通路上不成立**。
* **发射端**——两份契约（`ic3_certificate_v0.1`、`deadlock_certificate_v0.1`）都还是
  草案，`engine-rig` 未会签，`interop/certificates/` 里没有这两类文档。本轨道不代写。
* **只有一个谓词签名。** 编码只认 `at-player/1` + `at/2` + `clear/1`；16 条死锁候选行
  也全是 sokoban。这条通路的普适性不由本轮证据支持，已在契约里作为请求写给对方。
* **规模。** 叶子数随未钉住槽位指数增长，16 格 3 槽已经 60s。要上大棋盘，需要的是别的
  证明形状，不是更大的预算。
* P-10 的三条未清偿照旧（三个 `semantics:` 取值无后端；共享 `gen_pddl` 不消费
  `ProblemSpec`；`theory_grammar.lark` 是死文件）。

### 跑法

```bash
cd theory-compiler && THEORIA_REQUIRE_LEAN=1 python -m pytest    # 288 passed
cd theory-compiler && python -m tools.verify_c4                  # C4 验收，含负对照
```

`lean` 不在 PATH 时 Lean 测试自动跳过，其余照常。

---

## 契约演化窗口 (P-10) 达成 (2026-07-28)

分支 `agent/p10-contracts-v02`，base `edb3c37`。全文见
[`runs/P-10/RUN_STATE.md`](runs/P-10/RUN_STATE.md)。

```
theory-compiler   224 passed   (THEORIA_REQUIRE_LEAN=1，含真 Lean 编译)
cold-start-a0      56 passed   (LEAN=… 时)
```

九项清偿：

| # | 交付 | 状态 |
|---|---|---|
| 1 | `CONTRACTS/candidates_schema_v0.2.md` + 独立 v0.2 校验器 | **草案**，等 engine-rig 会签 |
| 2 | `CONTRACTS/dsl_grammar_v0.2.md` 定稿 + 迁移说明 | 定稿（本轨道独有，无需会签） |
| 3 | E-06 的转录那一半（证书权重注入编译链） | 清偿 |
| 4 | cold-start-a2 上报的两条缺陷 | 修复 + 8 项负向测试 |
| 5 | 四份 DSL 回归 | 四个 subagent 全部 PASS |
| 6 | `conflict` 证明义务（追加） | 清偿，两条路线；当场抓到 **E-07** |
| 7 | **E-07 本身**（再追加） | 清偿——`unique` 字段修饰符；七份说明书**全部**直接判绿 |
| 8 | **E-06 的证明那一半**（再追加） | 清偿——第二种证明方法，两条论证分开署名 |
| 9 | **`ic3_pdr` 证书**（再追加） | **消费端**完成；发射端是 engine-rig 的文件，未写 |

### 本轮最该记住的三件事

**契约草案被对抗式复核判过 REFUSE，三条 blocker 全部属实。** 最要命的一条是：
第一稿的 v0.2 校验器加了「id 不得重复」，既超出契约文本，又把 engine-rig 一个
**正在通过的**测试判红——而理由本身是反的，确定性 id 是内容地址，重复恰恰证明两行
逐字节相同。另两条是悄悄丢掉 v0.1 的零分母与空行规则（在一份自称「不改变既有字段
含义」的文档里），以及把会签成本低估约一个数量级。现在有 `TestAdditive` 每次跑：
两个校验器读同一份语料，凡 v0.1 收的 v0.2 必须收。**「加法」最容易在实现里悄悄
变成「顺手也收紧一点」。**

**测试一直在测另一棵树。** 可编辑安装记的是绝对路径，worktree 里
`import theory_compiler` 解析到原目录。一次 163 项全绿之前的那次 149 项全绿，
对旁边磁盘上的改动一个字都没测。已加 `conftest.py`；同类的
`THEORIA_REQUIRE_LEAN=1` 也补上了，因为默认 `pytest -q` 会在半秒内绿着跑完、
**一次 `lean` 都没调**，而跳掉的正是 A1 的验收项。

**`gen_pddl` 读了 `semantics:` 却不校验它。** 实测：`frame reset` +
`cascade multi_frame` 的说明书，`gen_python` 拒绝、`gen_lean` 拒绝、`gen_pddl`
照发不误——它只读 AST。这是 `semantics:` 段自己要关的洞在低一层重演。已补守卫。

### 追加：`conflict` 的证明义务已清偿，并当场抓到 E-07

`theory_compiler/conflict.py`，两条路线：**守卫分析**（六条可判定理由，健全不完备）
与**穷举扫描**（拿预测器跑每一个**可表示**状态，不是可达状态——D-TC-012 的教训）。
义务**按对象**成立，所以 A0 那对守卫完全相同的级联规则（`press_left` /
`door_opens_left`，一个 claim Button 一个 claim Door）正确地不算冲突。

七份说明书里六份直接判绿。**第七份是发现**：孔明棋说明书声明 `conflict exclusive`
而**没有蕴含它**。`jump_right` 是双实例模式，接地出的
`(?a=Peg_0, ?b=Peg_1)` 与 `(?a=Peg_0, ?b=Peg_3)` 都 claim `Peg_0`，只要两枚棋共格
就同时触发。穷举实测：

| 扫描范围 | (状态,动作) 对 | 一个对象被 claim 两次 |
|---|---|---|
| 全部可表示状态 | 80,000 | **600** |
| 限制到「没有两枚活棋共格」 | 59,560 | **0** |

**与 A1 那个错同形：规则作为 problem 解是对的，作为 domain 是错的**；可达集里两枚
棋从不共格，所以重放永远看不见它。

### E-07 已清偿：给说明书一个地方写下它

不是把检查放松，是加 `unique` 字段修饰符（契约修订记录第 12 条）。
`object Peg { pos: Int unique, alive: Bool }` 说出了世界一直为真、而说明书一直没处
可写的那件事；有了它，守卫分析把 228 对重叠规则**全部**直接判绿，条件路线不再走到。
**七份说明书现在全部 green。**

`unique` 自己也是义务：`certify_uniqueness` 证初始态成立 **且** `step` 保持
（59,560 条良构转移全扫）。只证前一半的话，就是 `semantics:` 要关的那个洞在低一层
重演。加它时抓到两个同形隐患：字段正则未锚定导致修饰符**静默消失**，以及漂亮打印器
不发 `unique`、于是 round-trip 之后得到一份**不再蕴含自己 `conflict exclusive`** 却
看起来完全正常的说明书。都已修，round-trip 测试改成比字段而不是比名字。

条件路线**保留**：需要该条件却不声明的说明书，仍然只拿到具名的有条件结论加一个反例。

### E-06 的证明那一半已清偿：换一种证明方法，不是换一种说法

`goal count(Peg, alive) = 1` 现在**证出来了**。证书排除得了的目标走代数论证，
排除不了的（`lp_potential` 对其中三个根本不存在线性 pagoda）交给**穷举可达集**——
从 `11011` 出发只有 5 个可达态，没有一个是单子局面。`lean` 4.9.0 实跑退出码 0，
`inv_all` 与 `unsolvable` **双双空公理集**。

**两条论证在生成物里分开署名**，逐个目标写清是谁扛的。第一版表头写成「其余四个
**根本不存在**线性 pagoda」——**假的**，`01000` 自己有一份证书，只是这次编译没拿到。
「本证书没排除它」是关于证书的事实，「不存在线性 pagoda」是关于方法的事实。已改。

**拒绝保留**：可达集超过 `MAX_ENUMERATED_STATES` 就退回 `CertificateGapError`。
**清偿的是那条命题，不是那个方法缺口**——33 格棋盘上同一份说明书照样被拒，
D-TC-008 的取舍一字未变。

### `ic3_pdr` 证书：消费端做完了，发射端**没做，也不该由本轨道做**

E-06 是用穷举清偿的，而穷举是 `O(可达集)`——5 个态可以，33 格棋盘不行。结构上的
答案是第三种方法，引擎已经存在。本轮做完了**消费端全套**：schema 草案
（`CONTRACTS/ic3_certificate_v0.1.md`）、读取器（三条义务对全状态空间重算，
生产方的 `conditions` 块不予采信）、说明书侧语法（`clauses` / `cnf(...)`，契约
修订记录第 14 条）、Lean 发展（**分动作**闭合，不枚举可达集）。

实测（peg4，`lean` 4.9.0）：`computational` **空公理集**；`algebraic` 只带
`propext`——比 pagoda 的代数形态便宜一条，因为 CNF 上不做整数算术。

**发射端一个字没写**：`engine-rig/` 是对方轨道的目录。夹具是从对方**已经发布的
候选行**逐字段转录的，`provenance` 记着来源与那一行的 `id`，并有测试盯着两者不许
漂移、以及 `engine-rig/interop/certificates/` 里不许出现 ic3 文档。

**一条限制照录**：「证明规模跟着不变式走」在这份 4 格 2 子句的夹具上**省不出钱**
（内层分裂是 4 格里的 2 格）。这是**结构**上成立的说法，要大棋盘才付得出，
本轮没有大棋盘可跑。

### 未清偿

* **会签未到手**——两份契约都是草案（`candidates_schema_v0.2`、
  `ic3_certificate_v0.1`）。
* **ic3 证书的发射端**——engine-rig 那一侧的小改动，本轨道不代写、不催。
* **方法缺口本身**：三种方法（pagoda / 穷举 / ic3）都够不着的构型仍然没有证明。
* 三个 `semantics:` 取值无后端（全部报错，不近似）；共享 `gen_pddl` 仍不消费
  `ProblemSpec`；`theory_grammar.lark` 是死文件（已钉警告）。

---


## 汇合 sprint (P-5) 达成：真 A1 (2026-07-28)

83/83 测试通过，其中 8 项真正调用 `lean` 编译生成物并读 `#print axioms`。

### A1 验收：LP 权重 → Lean 封闭引理

```
engine-rig/interop/certificates/pagoda_5_11011_to_00010.json
        ↓  (数据文件为界，不 import 对方代码)
theory_compiler.certificate   —— 不信 verified 标志，全部义务重新验算
        ↓
theory.dsl  invariant pagoda_potential pagoda(w) <= 0 [source: lp_potential]
        ↓
theory.lean  def w : Pos → Int | .p0 => -1 | .p1 => 1 | ...
        ↓
lean →  'inv_init'    does not depend on any axioms
        'inv_closed'  does not depend on any axioms
        'inv_all'     does not depend on any axioms
        'unsolvable'  does not depend on any axioms
```

无 `sorry`，无 `native_decide`，依赖假设为空。

### 与 M8 彩排的三条差异，逐条清偿

| M8 遗留 | 现状 |
|---|---|
| 权重是手算常量 `[1,2,3,2,1]` | 权重是 `lp_potential` 求解的 `[-1,1,0,1,-1]`，从证书 JSON 读入并重新验算 |
| Lean 证明是 BFS 枚举 5 个可达态 + `native_decide` | pagoda 势函数归纳；`native_decide` 一行不发 |
| 无 engine-rig 数据流 | 证书 JSON 是唯一接口；move 几何从生成的预测器反推，再与证书交叉核对 |

### 两块试金石

| 试金石 | 结果 |
|---|---|
| peg 产物不回归 | 四种形态齐全；Lean 从枚举换成 pagoda 归纳，仍然编译、仍然 0 sorry、公理集从空到空 |
| `cold-start-a0/theory/theory.dsl` | 生成可运行 Python（7 条规则全部真的会触发）与类型正确的 Lean（59 个可达态，编译通过，公理集空） |

A0 的说明书**一字未改**即通过 v0.2 解析——它带的 `semantics:` 方言正是 v0.2 采纳的那一段。

### 已清偿的债务

| 债务 | 出处 | 清偿方式 |
|---|---|---|
| 生成器忽略 TheoryAST | D-A0-011 | `gen_lean`/`gen_python` 重写，经 `ir.WorldIR` 消费 AST + ProblemSpec |
| 一个类型只能一个实例 | D-A0-011 | `forall ?a in <ObjectType>` 按关卡实例 grounding；孔明棋 2 条规则 → 24 条 ground 规则 |
| 嵌套括号静默解析错误 | D-A0-013 | 平衡括号扫描；7 项正负测试 |
| E-01 守卫取反 | 台账 | `not <predicate>` |
| E-02 方向提升规则 | 台账 | `forall ?d in dir`，展开出的名字与手写的四条完全一致 |
| E-03 帧公理 | 台账（"最该先修的一条"） | `semantics:` 段，**强制**，缺失即报错 |
| E-04 地标声明 | 台账 | `landmark <name>`；未声明为警告，理由见 D-TC-011 |
| E-05 权重函数 | 台账 | `weights <n> over <f>` + `pagoda(<n>)` + `source:` |

契约升版：`CONTRACTS/dsl_grammar_v0.2.md`，修订记录逐条注明是哪条台账逼出来的。
v0.1 未改动一字。

### 未清偿：新增台账 E-06

**说明书的 `goal count(Peg, alive) = 1` 本 sprint 未能证明。**

5 格棋盘从 `11011` 出发有五个单子终局。`lp_potential` 只对 `01000` 和 `00010`
给得出线性 pagoda 证书；`10000`/`00100`/`00001` 被 engine-rig 自己的测试
(`test_interop.py`) 钉死为**线性 pagoda 方法不可证**——不是没导出，是导不出来。

该构型确实不可解（BFS 可达集 `{00111, 11100, 01001, 10010}`，最少 2 子），
但不变量语言（线性算术 / 计数 / 奇偶 / 有限权重）载不动这个结论。

编译器的处理是 `CertificateGapError`：**拒绝生成**，并指名哪几个终局没被覆盖。
不静默收窄成一个读起来更强的定理。这是本 sprint 唯一的开放问题，也是下一轮
该拿的东西——要么 engine-rig 扩不变量语言，要么这条命题保持 open。

### 独立复核

本轮结论经一次独立对抗式复核（只读，不许确认只许证伪），结论 CONFIRMED。
关键在于它跑了**负对照**：把 `w .p1` 从 1 改成 7 之后，`lean` 报
`decide proved ... is false`，四条定理全部变成 `depends on axioms: [sorryAx]`，
退出码 1。空公理集这条检查因此不是摆设。复核另确认 `gen_lean.py` 里没有任何
硬编码权重向量，move 集合确由预测器独立推出（交叉核对非循环）。

复核提出的两处缺口已修，见 D-TC-012（使能条件未校验，且占位串只采样了 5/32）
与 D-TC-013（权重需手抄进关卡文件）。

一条仍然成立的限制，照录：**"空公理集"与"证明规模线性"不同时为真。**
`computational` 空公理集但 `O(2^n)`，`algebraic` 线性但带 `propext, Quot.sound`。
33 格英式棋盘上前者是 2^33，跑不完。两条都诚实（永不出现 `sorryAx` /
`ofReduceBool`），取舍见 D-TC-008。另外，全部验证只跑在**一个** 5 格夹具上，
管线的普适性不由本轮证据支持。

### 阻塞

无。

### 跑法

```bash
cd theory-compiler && python -m pytest        # 83 passed（含 8 项真 Lean 编译）
```

`lean` 不在 PATH 时，8 项 Lean 编译测试自动跳过，其余 75 项照常。
