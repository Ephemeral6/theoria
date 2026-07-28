# P-10 · RUN_STATE

Prompt: `monitor/prompts/P-10-contracts-v02.md` · branch `agent/p10-contracts-v02` ·
base `edb3c37` · 2026-07-28.

一次开窗，五项清偿。契约两份、缺陷两条、回归四份，外加 `conflict` 证明义务。

---

## Delivered

### 1 · `CONTRACTS/candidates_schema_v0.2.md` — 草案，等 engine-rig 会签

`engine` 枚举 +2（`deadlock_carver` / `ic3_pdr`）、`kind` 枚举 +2
（`deadlock_theorem` / `pruning_account`）、三个可选字段（`evidence.basis`、
`derived_from`、`contract`）。v0.1 契约与 `engine-rig/tools/validate_candidates.py`
**一字未动**。v0.2 校验器是**另一份独立实现**
（`theory-compiler/tools/validate_candidates_v02.py`，66 项测试），不 import v0.1
校验器、不 import 任何 engine-rig 代码。

变更逐条注明是哪台引擎逼的，两条最硬的：

* `deadlock_theorem`——死锁定理的证明义务是**两条**（模式闭合、模式-目标互斥），
  不变量是**三条**；裁决方按 `kind` 派活会去找三条不存在的义务。且流里 16 条模式
  两两不同的行，合取起来直接矛盾。
* `pruning_account`——payload 里根本没有 `actions`，遍历 `kind == "plan"` 的消费者
  在那行拿 `KeyError`；而 M9 自报的「第三个实例省下 0」这条**诚实负结果**，在
  `plan` 名下长得像「找到了一个计划」。

`ic3_pdr` **不发**新 `kind`，照直写进契约：它的两个产物确实就是 invariant 和 plan。

### 2 · `CONTRACTS/dsl_grammar_v0.2.md` — 定稿

补版本号、生效日、冻结政策、v0.1→v0.2 迁移说明（含「v0.2 说明书在 v0.1 解析器下
**静默**编译成另一个世界」这条双向危害）。`semantics:` 提案在
`cold-start-a0/proposals/` 里挂上 ADOPTED 裁决，连同**两条没给的**：`conflict` 的
证明义务只声明未 discharge（**本轮稍后补上，见第 6 节**），`frame reset` /
`conflict priority:` / `cascade multi_frame` 三个取值无后端。

修订记录新增三条：#9 权重可来自证书（E-06 的转录那一半），#10 后端遇到不实现的
`semantics:` 取值必须报错，#11 `conflict` 必须被清偿而不只是被声明。

### 3 · E-06 的转录那一半 — 清偿；证明那一半 — 仍然 open

`build_ir(ast, problem, certificate=None)` 新增 `_resolve_weights`：证书填未填的
声明、关卡也给就必须相等、一份证书面对两个未填声明就**拒绝**。
`WorldIR.weight_sources` 记来源，`gen_markdown(ast, ir)` 把数字和出处渲染出来。
关卡文件里不再有任何手抄的权重。

**E-06 本身没清偿，也说清楚了为什么**：`goal count(Peg, alive) = 1` 证不出来，
五个单子终局里三个没有线性 pagoda 函数——engine-rig 自己的 `test_interop.py` 钉死
为此方法不可证。`CertificateGapError` 继续拒绝生成。下一步是 `ic3_pdr` 的证书导出，
在 engine-rig 那一侧。

### 4 · cold-start-a2 上报的两条缺陷 — 修复 + 负向测试

`cold-start-a0/tests/test_a2_reported_defects.py`，8 项，**写的时候全红**。

* **D-A2-006**：`gen_pddl_a0._addressable`——PDDL 的 cell 全集 = arena ∪ 任何被
  domain 点名的格子。修前 A0 自己就在犯：`markedcell` 类型在 domain 里声明了、
  `teleport-down` 拿它当参数，problem 的 `:objects` 里**一个实例都没有**，动作
  永远 ground 不出来。
* **D-A2-007**：`certify/lean_check.py` 改按字节读、显式 UTF-8 解码。顺带修了
  `run_all.py` 里的同类（并给子进程钉 `PYTHONIOENCODING=utf-8`）。

### 5 · 四份 DSL 回归 — 四个并行 subagent，全部有独立复核

| DSL | 结论 | 要点 |
|---|---|---|
| peg | **PASS** | 四种形态**逐字节**与改动前相同；Lean 两种发展都 exit 0，公理集与测试断言完全一致 |
| cold-start-a0 | **PASS** | 九步全绿；`teleport-down` 从 ground 不出来变成 118 个接地动作里的 1 个并**真的触发**；计划**不变**，原因经几何核实（传送出口在起始那一侧，走它是绕路）；BFS 穷举确认传送口**永不被占据** |
| a0-spike | **PASS-WITH-EXPECTED-REJECTION** | 因缺 `semantics:` 被拒——契约自己的规矩（E-03）；HEAD 链上**同样报错**，本轮改动零影响 |
| cold-start-a2 | **PASS** | 展品**完好**：有洞说明书仍是 UNSAT + 空公理集的 `unsolvable`；A2 的本地绕法与上游修复算出**同一个** cell 集，绕法变成可证的 no-op |

### 6 · `conflict` 的证明义务（追加清偿）

上面「未清偿」里原本记着一条：v0.2 让说明书说清它 claim 哪条路线，而没有任何东西
去证。已补上 `theory_compiler/conflict.py`。

义务**按对象**成立，这是全部难点：朴素读法「所有守卫两两互斥」会**否掉 A0 那份正确
的说明书**——`press_left` 与 `door_opens_left` 守卫逐字相同，是级联，一个 claim
Button 一个 claim Door。所以只在 claim 集相交的规则对上要求互斥。

两条路线，报告说明是哪条付的账：**守卫分析**（五条可判定理由，健全不完备）与
**穷举扫描**（预测器跑每一个**可表示**状态，不是可达状态）。`build_ir` 只警告不报错
——`gen_python` 是穿过 `build_ir` 造预测器的，在那里报错等于把穷举路线要用的预测器
一起否掉；致命判定在 `certify_conflict`，也正是契约原文说的位置。

**七份说明书六份判绿，第七份是本轮第二个真发现：E-07。** 孔明棋说明书声明
`conflict exclusive` 而没有蕴含它——`jump_right` 是双实例模式，接地出的两条规则都
claim 同一枚跳棋，只要另外两枚共格就同时触发。80,000 个可表示 (状态,动作) 对里
**600** 次冲突；限制到「没有两枚活棋共格」的 59,560 对里 **0** 次。说明书说不出那个
条件（要在守卫里对实例做量化，v0.2 没有，契约禁止手工扩），所以结论是**有条件
成立**：条件具名、两半都由机器给（干净扫描 + 带见证的反例）。

**与 A1 那个错同形**：规则作为 problem 解是对的，作为 domain 是错的。可达集里两枚棋
从不共格，所以任何重放都永远看不见它。

---

## 复核抓到的东西（本轮的主要产出之一）

**契约草案被以 engine-rig 视角的对抗式复核判过 REFUSE**，三条 blocker 全部属实，
已逐条核对代码与测试后修掉：

1. 第一稿的 v0.2 校验器加了「id 不得重复」——既超出契约文本，又把 engine-rig
   一个**正在通过的**测试判红（`test_a_second_full_run_only_adds_lines` 把同一次
   run 写两遍）。而且理由本身是反的：确定性 id 是**内容地址**，重复恰恰证明两行
   逐字节相同。已删，并把理由写进契约。
2. 第一稿悄悄丢掉了 v0.1 的两条规则（`coverage` 分母为零、空行是错误）——在一份
   自称「不改变既有字段含义」的文档里。已恢复，并加 `TestAdditive`：两个校验器读
   同一份语料，凡 v0.1 收的 v0.2 必须收。
3. 第一稿把会签成本说成「每台引擎改一行」，低估约一个数量级，并给了一条**做不到**
   的 append-only 处置建议——`artifacts/candidates.jsonl` 被字节相等测试钉死，
   发射端一改 `kind`，44 行必须全部重生成，且 18 行的 id 会变。已换成逐位置的
   真实改动面表。

另外三条自查发现的：

* **`gen_pddl` 不校验 `semantics:`**。实测：一份改成 `frame reset` +
  `cascade multi_frame` 的说明书，`gen_python` 拒绝、`gen_lean` 拒绝（它继承守卫）、
  `gen_pddl` **照发不误**——它只读 AST，从不建 IR、从不建预测器。这是
  `semantics:` 段自己要关的洞在低一层重演。已补守卫 + 负向测试。
* **测试在测另一棵树**。可编辑安装记的是绝对路径，worktree 里 `import
  theory_compiler` 解析到**原目录**；一次 149 项全绿之后才发现它对旁边磁盘上的
  改动一个字都没测。已加 `conftest.py`。同类隐患顺手加了 `THEORIA_REQUIRE_LEAN=1`
  ——默认仍跳过，但需要 Lean 结果的运行可以要求它必须真跑。
* **`theory.md` 把 `## How a Turn Works` 渲染了两遍**，两种措辞，第二份孤零零挂在
  laws 后面。`compile_a0.render_markdown` 还在追加自己那份，而共享的
  `gen_markdown` 采纳 `semantics:` 之后已经渲染了一份。cold-start-a2 在第二个世界
  上跑这套后端时看出来的。已删重复 + 测试钉死。

---

## Not delivered / 仍然成立的限制

* **会签未到手。** 契约是**草案**，engine-rig 回签前不生效。异轨道异步，本轨道
  不等待。
* **E-06 的证明那一半仍然 open。** 见上。
* ~~**`conflict` 的证明义务无人校验。**~~ **本轮追加清偿**，见上面第 6 节。
* **E-07（新）**：守卫语言无法表达「两个同类实例不共格」，所以孔明棋说明书的
  `conflict exclusive` 只能**有条件**成立。不是检查器的不完备，是说明书说不出来。
* **`frame reset` / `conflict priority:` / `cascade multi_frame` 三个取值无后端。**
  全部报错，不近似。
* **共享 `gen_pddl` 不消费 `ProblemSpec`。** 它的签名是
  `(ast, problem_name, grid_width=2, grid_height=3)`，对 A0 产出的是 2×3 玩具网格
  而不是 A0 的关卡。旧问题（`gen_pddl_a0` 存在的理由就是这个，D-A0-011），本轮
  未动，但本轮的四形态回归里 PDDL 那一栏的意义因此有限。
* **`theory_grammar.lark` 是死文件**，且以误导的方式陈旧（没有 `semantics:` 产生
  式）。已在文件头钉上警告，未删。
* **A2 的 `upstream_pin.json` 会因本轮改动而失配**——它按 sha256 钉住
  `cold-start-a0` 的文件，本轮改了其中两个。那是 A2 轨道自己重新钉的事，本轨道
  未代改，已在 PARTNER_SYNC 里说明。

---

## Tests

```
theory-compiler          191 passed          (THEORIA_REQUIRE_LEAN=1，含真 Lean 编译)
theory-compiler          183 passed, 8 skipped   (无 lean 时的默认)
cold-start-a0             56 passed          (LEAN=… 时；无 lean 时 53 passed, 3 skipped)
```

一次**偶发**失败要照录：连跑三轮全套里有一轮 `test_several_goal_states_still_compile
[algebraic]` 的 `lean` 退出码非 0，单独重跑与随后两轮全套都通过，产物逐字节相同。
判断是工具链瞬时故障而非回归，但样本只有一次，未进一步定位。

跨轨道只读核对：`engine-rig/` 与 `a0-spike/` `git status` 全程为空；
`cold-start-a2/` 被回归 subagent 跑 `run_all.py` 时写脏 8 个文件，已逐一核对内容
（全是绝对路径与上游哈希）后 `git checkout --` 还原，最终 `git status` 该目录为空。

## Territory

改动只在 `theory-compiler/`、`cold-start-a0/`、`CONTRACTS/` 三处。
`CONTRACTS/candidates_schema.md` 与 `CONTRACTS/dsl_grammar_v0.1.md` 未触碰；
`engine-rig/tools/validate_candidates.py` 未触碰。
