# STATUS — theory-compiler track

## 契约演化窗口 (P-10) 达成 (2026-07-28)

分支 `agent/p10-contracts-v02`，base `edb3c37`。全文见
[`runs/P-10/RUN_STATE.md`](runs/P-10/RUN_STATE.md)。

```
theory-compiler   191 passed   (THEORIA_REQUIRE_LEAN=1，含真 Lean 编译)
cold-start-a0      56 passed   (LEAN=… 时)
```

四项清偿：

| # | 交付 | 状态 |
|---|---|---|
| 1 | `CONTRACTS/candidates_schema_v0.2.md` + 独立 v0.2 校验器 | **草案**，等 engine-rig 会签 |
| 2 | `CONTRACTS/dsl_grammar_v0.2.md` 定稿 + 迁移说明 | 定稿（本轨道独有，无需会签） |
| 3 | E-06 的转录那一半（证书权重注入编译链） | 清偿；**证明那一半仍 open** |
| 4 | cold-start-a2 上报的两条缺陷 | 修复 + 8 项负向测试 |
| 5 | 四份 DSL 回归 | 四个 subagent 全部 PASS |
| 6 | `conflict` 证明义务（追加） | 清偿，两条路线；当场抓到 **E-07** |

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

`theory_compiler/conflict.py`，两条路线：**守卫分析**（五条可判定理由，健全不完备）
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

说明书说不出那个条件——要说得能在守卫里对实例做量化，v0.2 没有，且契约禁止手工扩。
所以状态是 **conditional**：条件具名 `distinct_positions`，两半都由机器给（条件下
干净 + 无条件下带见证的反例），记 **E-07**。**与 A1 那个错同形：规则作为 problem
解是对的，作为 domain 是错的**；可达集里两枚棋从不共格，所以重放永远看不见它。

`tests/test_conflict.py::TestInventory` 把七份说明书的状态逐一钉住，peg 那条同时
断言「有条件成立」与「无条件下确实失败」，所以 conditional 不会悄悄退化成 green。

### 未清偿

* **会签未到手**——契约是草案。
* **E-06 的证明那一半**：`goal count(Peg, alive) = 1` 仍证不出来。五个单子终局里
  三个没有线性 pagoda 函数。下一步是 `ic3_pdr` 的证书导出，在 engine-rig 那一侧。
* **E-07**：守卫语言无法表达实例互斥，孔明棋的 `exclusive` 只能有条件成立。
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
