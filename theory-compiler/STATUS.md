# STATUS — theory-compiler track

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
