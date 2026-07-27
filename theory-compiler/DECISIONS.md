# DECISIONS.md — theory-compiler 轨道设计决策记录

## D1: 解析器技术选型

**决策**: 使用 Python `lark` 库（Earley/LALR 解析器生成器）解析 theory.dsl 和 playbook.dsl。

**理由**:
- lark 支持 EBNF 语法定义，表达力足够覆盖冻结契约的全部句型
- 生成 AST 自然，round-trip 友好
- 纯 Python，无外部二进制依赖
- 保守选择：成熟、文档齐全、无需自己写词法分析

**备选（放弃）**: pyparsing（组合子风格，round-trip 较难）、手写递归下降（工作量大且易出错）

## D2: Lean 4 版本

**决策**: 使用 Lean 4 stable（通过 elan 管理），lake 构建。

**理由**: 标准工具链，与冻结契约中"Lean 的 decide/omega"一致。

## D3: PDDL 语法校验

**决策**: 使用 `pddl` Python 库（pypi: pddl）做语法校验，不调用外部规划器。

**理由**: 工单明确要求"只验证语法合法性"，pddl 库能解析并验证 PDDL 文件结构。

## D4: 素材 B 不变量来源

**决策**: 手工选取经典 1D 孔明棋 5-peg 不可解构型，使用文献已知的 pagoda 权重函数（手算验证后直接填入 DSL 作为字面常量）。

**理由**: 工单明确说明"权重是你自己算出来后填进去的字面常量"，不依赖 engine-rig 的 LP 引擎。选 1D 是因为足够小、可手推、文献有确切答案。

## D5: Python 项目结构

**决策**: 使用标准 `pyproject.toml` + `src/` layout，pytest 做测试。

**理由**: 现代 Python 标准布局，保守选择。

---

# 汇合 sprint (P-5) — 真 A1

## D-TC-006: 生成器消费 IR，而非 AST 直接进后端

**决策**: 在 parser 与后端之间加一层 `ir.WorldIR` = `TheoryAST` + `ProblemSpec`，
两趟 grounding（值域在 `expand.py`，对象实例在 `ir.py`）都在这里跑完。

**理由**: D-A0-011 报告的缺陷不是"生成器写得不好"，而是生成器**根本没读 AST**。
`gen_lean.generate_lean` 忽略它的 `ast` 参数，直接 BFS 一维孔明棋。修法不是把
world 知识搬进生成器，而是把 world 知识搬出所有生成器：后端只认一套词汇表，
词汇表外的子句抛 `UnsupportedClause`，绝不猜。这是 `fd_adapter` 的规矩——
静默近似一个看不懂的子句，会产出一个与说明书不一致的预测器，下游每一层
都会去认证一个错误的世界。

**代价**: 多一层。换来的是同一份 `gen_python` 同时编译网格世界（A0，三种对象、
传送门、门闩）和线性世界（孔明棋，一种类型四个实例），两者都没有为对方写过一行。

## D-TC-007: Lean 证明有两种形态，由**说明书**挑，不由调用方挑

**决策**: `generate_lean` 依据说明书是否声明 `pagoda(...)` 不变量，产出
`pagoda` 或 `enumerative` 两种发展；`pagoda` 再分 `computational` / `algebraic`
两种证法。

**理由**: 证明策略是说明书的主张的函数，不是调用方的偏好。声明了势函数的世界
应当拿到代数归纳；没声明的世界（A0 有门闩和传送门，没有线性势）应当拿到枚举
证明。让调用方选，等于允许调用方为一个没有势函数的世界要一个势函数证明。

## D-TC-008: 空公理集与线性证明规模不可兼得，原因在 Lean 而不在 pagoda

**实测**（Lean 4.9.0，见 `tests/test_gen_lean.py`）:

| 发展 | `#print axioms` | 证明规模 |
|---|---|---|
| pagoda, `computational` | **空** | `O(2^n)` |
| pagoda, `algebraic` | `propext, Quot.sound` | `O(n)` |
| enumerative | **空** | `O(可达集)` |

代数证明拿不到空公理集，根源不是 pagoda 论证：Lean 4.9 core 里**每一条** `Int`
引理——`Int.add_comm`、`Int.le_trans`、`Int.add_nonpos`——自身都是用 `propext`
证的。任何"讲道理"而非"算出来"的证明都继承它。

**决策**: `computational` 为默认，因为 A1 验收标准写的是依赖假设为空；
`algebraic` 在棋盘大到枚举不动时使用。两者都不发 `native_decide`——它靠跑编译
代码交差，会把 `Lean.ofReduceBool` 记进公理集，而验收看的就是 `#print axioms`。

## D-TC-009: 证书不予采信，重新验算

**决策**: `certificate.load_certificate` 忽略文档自带的 `verified: true`，
从 `weights_integer` 出发重新推导全部三条义务，并且**自己重新枚举move几何**，
再与文档列出的 witness 比对；文档漏列任何一个 move 即报错。

**理由**: 上游 `verify()` 会重算算术，但不检查 witness 表是否完整——删掉几条
witness 的文档照样通过。而漏掉的那一条恰恰可能是势函数上升的那一步。信任那个
标志，等于让一个不成立的权重向量变成 Lean 定理。引擎提议，说明书裁决——裁决
就发生在这里。

## D-TC-010: 说明书的目标宽于证书时，拒绝生成

**决策**: `CertificateGapError`。不静默收窄，不生成一个读起来比实际证明的更强的
`unsolvable`。

**理由**: `lp_potential` 可靠但不完备。5 格棋盘从 `11011` 出发的五个单子目标里，
只有 `01000` 和 `00010` 有线性 pagoda 证书；`10000`/`00100`/`00001` 被 engine-rig
自己的测试钉死为**此方法不可证**。所以说明书的 `count(Peg, alive) = 1` 是一个
本 sprint **未能证明**的命题，这一条写进台账（E-06）而不是绕过去。一个会替引擎
夸大结论的编译器，比一个不会证明的编译器坏得多。

## D-TC-011: E-04 警告，E-03 报错

**决策**: 缺 `semantics:` 是错误；problem 提供了而 manual 未声明的 landmark 是警告。

**理由**: 两者的失败模式不同。缺 `semantics:` 会**静默编译出另一个世界**——这正是
该段落存在的理由。未声明的 landmark 编译出的是同一个世界，代价只是可读性，也就是
E-04 记的那笔账。把后者也做成错误，会拒绝掉每一份在 `landmark` 存在之前写成的
v0.1 说明书，包括 `cold-start-a0/theory/theory.dsl`——那是一份正确的说明书，
现在仍然是。

## D-TC-012: Lean 的 `legal` 是模板，必须对着预测器挣来

**背景**: 独立复核指出 `_derive_moves` 只校验转移的**形状**（去二添一），
不校验**使能条件**。而 Lean 文件里的 `legal s m := s.src && s.over && !s.dst`
是固定文本，没有一个字来自说明书。一个允许跳到已占格的世界会产出同样形状的
转移，然后拿到一份悄悄描述另一个世界的 Lean 文件。

**决策**: `_check_legality`——对预测器能表示的**每一个**占位串、每一个 move，
把预测器的实际行为与 `legal` 的预测逐一比对，不符即拒。

**同时修掉的采样缺口**: 原来只枚举"每个 peg 都活着"的状态，5 格棋盘 32 个占位
串里只检查了 5 个。改为用 `alive=False` 表示少于满员的棋盘后，覆盖 31/32
（第 32 个是五子满盘，本关只有四个实例，表示不出来，正确跳过）。

## D-TC-013: 权重不必在关卡文件里抄一遍

**背景**: 同一次复核指出权重的数据流不是单向的——`theory.dsl` 声明 `weights w`，
`check_against_theory` 就要求 problem JSON 也提供一份，于是引擎的数字要**手抄**
进关卡文件。这正是 A1 想消掉的那道转录工序。

**决策**: 声明了却没提供，降为警告。真正需要数字的后端（`gen_lean`）才坚持
要到，而且证书就能满足它。两处都有时必须一致——过期的副本正是"证明建立在
没人求解过的权重上"的发生方式。

`tests/fixtures/peg5_problem.json` 据此删掉了 `weights` 字段：证书带着数字，
关卡不再复述。
