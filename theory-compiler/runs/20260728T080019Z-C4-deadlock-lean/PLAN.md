# C4 · 死锁定理与 IC3 不变量进 Lean — 开工计划

工人 `W-1541`，领地 `theory-compiler`，分支 `agent/c4-deadlock-lean`，base `ded9cd7`。

## 领到的两半，状态并不对称

| 半边 | 上一轮留下的状态 | 本轮要做的 |
|---|---|---|
| **IC3 → `inv_init`/`inv_closed`/`goal_break`** | **消费端已完成**（P-10）：`ic3_certificate.py`、`cnf(...)` 语法、`_ic3_lean` 发射器、24 项测试含真 Lean 编译 | 复跑取证（本机 `lean` 4.9.0 之前没有默认工具链，历史绿是在别的机器上取的），把公理集实测重新落盘；不重写 |
| **死锁 → 条件化不可达定理** | **零** | 全部 |

所以本轮的工程量几乎全在死锁那一半。

## 死锁那一半：世界从哪来

`deadlock_carver` 的定理是**接地 STRIPS 任务**上的命题：

```
<pattern>  AND  not-goal   =>   dead
```

engine-rig 已发布的 16 条 `conditional_unsolvability` 候选行全部属于 **sokoban**
（`candidates.jsonl`，`payload.producer == "deadlock_carver"`）。棋子世界没有一条。
所以要么消费 sokoban，要么无证可消费——而自己跑对方的引擎造一份证书，就是把
发射端的活干了，`ic3_certificate_v0.1` 第《谁写哪一半》节刚刚说过那不归本轨道。

### 说明书写不下 sokoban（本轮实测的边界，记为 E-08）

本轮先做了一次只读勘察（两个 subagent，独立复核过），结论：DSL 的**动力学**装得下
sokoban——`free(...)` 恰好就是 `clear`，`toward(o,?d)` 恰好就是 `adj`，push 同时移动
箱子与人可以写成两条同守卫、认领对象不相交的规则（契约里「级联而非冲突」那一条）。
装不下的是**目标**：`goal:` 只收一个表达式，`gen_python._goal_body` 只认
`count(Type, f = v) = n` 或单个比较，而 sokoban 的胜利条件是「每个箱子各就各位」，
需要目标合取或者「landmark 集合」这种当前语法没有的东西。附带两处：
`conflict.disjointness_reason` 没有 `free(t)` 对 `X.pos = t` 的判据；
`gen_pddl._extract_pred_pddl` 对不认识的子句**静默丢弃**。

**不降低验收线的办法**：不假装说明书能写 sokoban，也不因此不做定理。把接口下移一层——
死锁证书的世界是**接地 STRIPS 任务**，本轨道自己**独立**解析 + 接地一份 PDDL
（域与问题都是从对方 `fixtures/data/` 逐字转录的数据文件，带 provenance），
再对着自己接地出来的动作集重算两条义务。E-08 照实记在未清偿里。

### 纪律：转移关系不许来自证书

与 pagoda / ic3 读取器同一条：证书只提供**模式**，不提供动作集。
交叉核对是硬的——本轨道自己接地出的 ground action 数必须等于证书
`evidence.coverage` 的分母（`112/112`），证书 `blocked_actions` 点名的每一个动作
都必须在我们自己的动作集里找得到、且我们自己能独立给出它被挡住的理由；
对不上就拒绝生成。

### Lean 编码

`St` 是 `(player, b1, b2)` 三个 `Cell` 字段的结构体，`clear c` 定义成
`c ∉ {player, b1, b2}`。这样 h² 互斥事实（一格只放一样东西、一个箱子只在一处）
在**类型层面就是真的**，Lean 不必再证——与棋子那边把 `St` 定成「每格一个 Bool」
完全同构的一步。编码是否忠实于 STRIPS 任务，由 Python 端穷举核对（全部可编码态 ×
全部 ground action，与 `gen_lean._check_legality` 同一条纪律）。

三条定理：

```lean
theorem pat_closed : ∀ s m, Pat s → legal s m = true → Pat (applyMove s m)
theorem pat_no_goal : ∀ s, Pat s → ¬ Goal s
theorem dead : ∀ r s, Pat r → ReachFrom r s → ¬ Goal s     -- 条件化不可达
```

`dead` 是**条件化**的：不从 `s₀` 出发，从任何含该模式的态出发。这正是 Theoria 1.9
的「条件化小型不可解定理」，与 ic3 那份**全局**不可达定理形状相同而量词不同。

## 步骤

1. 运行目录 + MANIFEST（本文件同目录）。
2. `strips.py`：独立 PDDL 解析 + 接地，必须自己数出 112。
3. Lean 试打：手工生成一份，编译，量分支代价，定死战术形状。
4. `deadlock_certificate.py`：读取器 + 两条义务重算 + `covers`。
5. `gen_lean.generate_deadlock_lean`：computational / algebraic 两形态。
6. 夹具转录 + 漂移测试。
7. `CONTRACTS/deadlock_certificate_v0.1.md` 草案 + 会签请求。
8. 测试，含负对照（篡改模式必须让 Lean 红、让读取器拒）。
9. IC3 那一半复跑取证。
10. verify 脚本、RUN_STATE、DECISIONS、STATUS、PARTNER_SYNC、monitor inbox、推分支。
