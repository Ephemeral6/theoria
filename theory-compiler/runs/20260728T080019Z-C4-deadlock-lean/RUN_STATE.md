# C4 · 死锁定理与 IC3 不变量进 Lean —— 运行记录

工人 `W-1541` · 领地 `theory-compiler` · 分支 `agent/c4-deadlock-lean` · base `ded9cd7`
`lean` 4.9.0（`leanprover/lean4:v4.9.0`）· Python 3.13

计划见同目录 [`PLAN.md`](PLAN.md)；机器可读的验收证据见
[`verify/EVIDENCE.json`](verify/EVIDENCE.json)。

---

## 一句话

`deadlock_carver` 的条件化不可解定理与 `ic3_pdr` 的三件套都在 Lean 里编译通过、
公理集为空；死锁那一半是从零做的，IC3 那一半是上一轮做完的、本轮只复跑取证。

## 验收对照

条目原话：**「至少各一条在 Lean 里编译通过、公理集为空」**。

| 证书 | 定理 | 叶子目标 | `lean` | `#print axioms` |
|---|---|---|---|---|
| `deadlock_carver` `at(b1,c11)` | `dead` 等九条 | 28,672 | 退出 0，60s | **九条全空** |
| `deadlock_carver` `at(b1,c12) AND at(b2,c13)` | `dead` 等九条 | 1,792 | 退出 0，4.2s | **九条全空** |
| `ic3_pdr` peg4 `computational` | `inv_init`/`inv_closed`/`inv_all`/`unsolvable` | — | 退出 0 | **四条全空** |
| `ic3_pdr` peg4 `algebraic` | 同上 | — | 退出 0 | `propext`（设计如此，D-TC-023） |

`python -m tools.verify_c4` 把上表跑一遍并额外跑一次负对照，全绿才退出 0。
测试：`THEORIA_REQUIRE_LEAN=1 python -m pytest` → **283 passed**（本轮前 224）。

**关于条目里点名的 `goal_break`**：P-10 的 `_ic3_lean` 每个目标态发一条
`goal_break_{i}`，但 `#print axioms` 只对 `inv_init`/`inv_closed`/`inv_all`/`unsolvable`
四条打印。`goal_break_0` 被 `unsolvable` 依赖，而 `#print axioms` 报的是**传递**依赖，
所以 `unsolvable` 那条空集已经蕴含 `goal_break_0` 也是空的。本轮没有为了让它单独露面
去改上一轮已经完工的发射器——那是改别人做完的东西，换不来新的事实。

## 一开始就发现两半并不对称

读 STATUS 与 `CONTRACTS/ic3_certificate_v0.1.md` 后确认：**IC3 消费端在 P-10 就做完了**
（读取器、`cnf(...)` 语法、`_ic3_lean`、24 项测试含真 Lean 编译）。所以条目里 IC3 那一半
需要的是复跑取证而不是重写——而且值得复跑：本机 `elan` 此前**没有设默认工具链**，
`shutil.which("lean")` 找得到、`lean` 一跑就报 `no default toolchain configured`。
设了 `leanprover/lean4:v4.9.0` 之后 Lean 测试才是真的在跑。（这也解释了本轮开工时
基线 224 项全绿是怎么来的——那次是在有工具链的环境里取的。）

死锁那一半此前是零。工程量几乎全在这里。

## 死锁：三个真问题，按遇到的顺序

### 一、世界从哪来 —— 说明书写不下 sokoban（E-08）

`deadlock_carver` 已发布的 16 条 `conditional_unsolvability` 候选行**全部是 sokoban**，
棋子世界一条没有。而自己跑对方的引擎造一份证书，就是把发射端的活干了，
`ic3_certificate_v0.1` 的《谁写哪一半》刚说过那不归本轨道。

所以先做勘察，不是先动手：两个只读 subagent 分头查 DSL 的表达力边界与 `gen_lean` 的
结构。结论：

* **动力学装得下**——`free(...)` 就是 `clear`（`_free` 读 `render(state)`，涵盖墙与所有
  实例），`toward(o,?d)` 就是 `adj` 且可嵌套，push 同时移动箱子与人可以写成两条同守卫、
  认领对象不相交的规则（契约 122–128 行的「级联而非冲突」）。
* **目标装不下**——`goal:` 只收一个表达式，`gen_python._goal_body` 只认
  `count(Type, f = v) = n` 或单个比较；sokoban 要「每个箱子各就各位」，需要目标合取
  或地标集合，两者都不存在。
* 附带两处：`conflict.disjointness_reason` 没有 `free(t)` 对 `X.pos = t` 的判据；
  `gen_pddl._extract_pred_pddl` 对不认识的子句**静默丢弃**。

**不降低验收线的办法**：把这条通路的接口下移一层。死锁证书的世界是**接地 STRIPS 任务**，
本轨道自己解析 + 接地（`strips.py`），证书只提供模式。E-08 照实记进 STATUS 未清偿，
并且写明后果：**四形态共导在这条通路上不成立**。

### 二、原子集合上这条定理是假的 —— 良构编码

STRIPS 状态是原子集合，而在任意原子集合上死锁定理**不成立**：没什么拦得住一个集合
同时含 `at(b1,c12)` 与 `clear(c12)`，从那种态一推就走出了模式。生产方为此要 h² 不动点。

本轨道从另一头到同一处：把状态重表示成**一物一格的元组**（player 一格、每个箱子一格），
`clear c` 定义成「没有东西站在 `c`」。互斥事实于是成了数据的形状。

**这一步要检查，不能假设。** `strips_encoding.verify` 穷举 3360 个良构态 × 112 个地面
动作 = **376,320 对**：编码守卫必须与 `pre ⊆ atoms` 逐对一致，编码效果必须与
`(atoms \ del) ∪ add` 逐对一致，并且 3352 个可达态全部是良构元组。与
`gen_lean._check_legality` 在棋子那条路上做的是同一件事。

### 三、良构不是装饰 —— 一次差点变成假定理的实测

开工时的设想是「良构可以不进定理，因为退化态无所谓」。写了个一次性探针
（[`spike_encoding.py`](spike_encoding.py)）去证实，结果**相反**：

```
b1c11        legal-from-pattern   720   closure breaks: wf 0  degenerate 0
b1c12_b2c13  legal-from-pattern    44   closure breaks: wf 0  degenerate 2
```

pair 模式在两个退化态（人站在被推的箱子里）上闭包**为假**。不带 `wf` 假设的
`dead_closed` 会是一条假定理。于是 `wf` 作为假设进了定理，并有一项测试
（`test_degenerate_states_have_no_atom_set_counterpart`）盯着那两个反例还在，
注释写明「若这天变空了，假设才可以去掉」。

## Lean 那一侧

```lean
theorem dead : ∀ (r s : St), wf r = true → Pat r = true → ReachFrom r s → Goal s = false
```

`ReachFrom r` 从**任意** `r` 起步而不是从 `s₀`——「条件化」在 Lean 里的形状，
与 pagoda / ic3 那两份全局不可达定理唯一的量词差别。

**分裂宽度是算出来的**：叶子数 = `格数 ^ 未钉住槽位数 × 地面动作数`。钉住两个箱子的
pair 模式只剩 player 自由 → 1,792 叶子 / 4.2s；只钉一个箱子的 corner 模式剩 player 与
b2 → 28,672 叶子 / 60s。**差十六倍。** 超 `MAX_LEAN_CASES` 即拒绝生成。

一路上被 Lean 教了三件事：

1. **`decide` 不吃带自由变量的目标**（4.9 直接报 "expected type must not contain free
   or meta variables"）。所以钉住性引理只对模式**读到**的槽位量化，其余填一个固定格子
   ——填得下正是因为谓词读不到它。
2. **`set_option ... in` 不能跟在文档注释后面**（语法错）。改成文件级。
3. **心跳预算不够时 Lean 会把定理标成 `sorryAx` 而退出码非零**——第一次跑 corner 就是
   这样。这恰好证明了「退出码 0 且公理集为空」这条联合判据不是摆设。

## 交叉核对：账不参与义务，但账对不上就拒绝

证书的 `coverage` / `n_deleting_actions` / `blocked_actions` / `closure` **一个都不参与
义务重算**（`recheck` 一个都不读），只用于核对两边谈的是不是同一个任务：

* 本轨道接地出 **112** 个地面动作（48 move + 64 push），必须等于 `evidence.coverage`
  的分母；分子必须等于分母。
* 证书点名的 4 个被挡 push 必须逐个在本轨道的动作集里解析得到，且确实删除某个模式原子；
  本轨道数出的删除动作**一个都不许被漏掉不谈**。
* `closure: no_deleting_action` 而本轨道接地出删除动作，或反之，都是错。

十项负向测试覆盖这些路径。

## 非空展品：条件化定理专属的「绿而假」

D-A3-007 的教训是空公理集分辨不出没证东西的证明。条件化定理的同形失效模式是
**条件无人满足**：每条义务空空地全过，`#print axioms` 打印空集。所以

* `recheck` 要求良构见证，没有就拒；生成物发 `theorem pat_witness`；
* 夹具选的是**可解的** `sokoban-open4far`，生成物发 `theorem level_is_winnable`，
  附一条 11 步、逐步 `by decide` 的通关，与 `dead` 并排。定理说的是这块模式致命，
  不是这局本来就输。

**负对照**：把 `Pat` 往里挪一格，同一份文件 `lean` 退出码非零、`sorryAx` 出现。
写这条控制时抓到自己的一个错：第一版的替换是对整份源码做的，而同一个格子名在 `legal`
的 112 条分支里出现了几十次，于是**改到的是一条动作而不是模式**，文件照样编译通过、
控制静静地失效。现在替换只瞄准 `Pat` 的定义体，并且先用 `recheck` 确认挪过之后的模式
确实不再是死区——**一个因为别的原因变红的负对照，比没有负对照更糟。**

## 边界

* 本轨道往 `engine-rig/` 写了 **0 个字节**。
* 两份 PDDL 是**逐字节**拷贝，`tests/fixtures/strips/PROVENANCE.json` 记着来源与 sha256，
  一项测试比对内容。
* 两份证书由可执行的 `tools/transcribe_deadlock_certificates.py` 从候选行转录，
  一项测试每次重跑它并在漂移时判红。
* 三个新模块都有测试盯着不许 `import engine*`。

## 未清偿（详见 STATUS.md）

E-08（说明书写不下 sokoban，目标合取缺失是硬阻塞）；两份契约的发射端仍是 engine-rig 的，
未会签；编码只认一种谓词签名，16 条候选行也全是 sokoban，通用性不由本轮证据支持；
叶子数随未钉住槽位指数增长，要上大棋盘需要别的证明形状而不是更大的预算。
