# Theory Compiler

一个源，四种形态。`theory.dsl`（域，跨关卡不变）加一份 problem 实例（关卡数据）
编译成 Python / Lean / PDDL / Markdown。

语法契约：[`CONTRACTS/dsl_grammar_v0.2.md`](../CONTRACTS/dsl_grammar_v0.2.md)。

## 组件

| 组件 | 输入 | 输出 |
|------|------|------|
| `parser/` | `.dsl` 文本 | `TheoryAST`（v0.2：`semantics`、`domain`、`landmark`、`weights`、`forall`、`not`） |
| `parser/expand.py` | AST | 值域 schema grounding |
| `problem.py` | JSON | `ProblemSpec` — 关卡数据，不 import 任何别的轨道 |
| `certificate.py` | engine-rig 的证书 JSON | `PagodaCertificate`，全部义务重新验算 |
| `ir.py` | AST + ProblemSpec | `WorldIR` — 实例 grounding、状态轴、说明书与关卡的一致性检查 |
| `generators/gen_python.py` | IR | 可执行预测器（系统里唯一的预测器） |
| `generators/gen_lean.py` | IR + 证书 | Lean 4 发展，0 sorry，不发 `native_decide` |
| `generators/gen_markdown.py` | AST | 确定性自然语言，无模型在链路上 |
| `generators/gen_pddl.py` | AST（+ 可选 ProblemSpec）| PDDL domain + problem |
| `handover.py` | theory.dsl（+ playbook.dsl）+ ≥2 份关卡 | 自足的移交包 |

## 移交包

```bash
python -m theory_compiler.handover --world-id w --theory theory.dsl \
    --level a=a.json --level b=b.json --out pkg/
python -m tools.build_handover_packages          # 本轨道发布的两个包
python -m tools.build_handover_packages --check  # 逐字节复算
```

一个目录，交给一个没有仓库的读者代替仓库（Theoria 1.11 分层移交）：四形态 + 确定性
英文渲染 + 词汇表索引 + 一次上下文扫描。**一包带两关**——三个形态是 grounded 的，
只带一关的包会教读者把那一关的家具当成世界律。生不成的形态在包首页照实公布，
连生成器自己的拒绝理由一起；PDDL 在被叫作 generated 之前先过 `strips` 复读一遍
（D-TC-032）。

`tools/handover_exam.py` 判卷：题目与答案都从包**自己**编译出来的预测器算，不碰仓库。

## Lean 发展有两种，由说明书挑

说明书声明了 `pagoda(w)` 不变量 → **pagoda 发展**：势函数代数归纳，权重来自
`lp_potential` 证书。没声明 → **枚举发展**：从生成的预测器抄出转移表，`decide`
收尾。调用方不能替一个没有势函数的世界要一个势函数证明。

公理预算，实测而非估计：

| 发展 | `#print axioms` | 证明规模 |
|---|---|---|
| pagoda, `proof="computational"`（默认） | 空 | `O(2^n)` |
| pagoda, `proof="algebraic"` | `propext, Quot.sound` | `O(n)` |
| enumerative | 空 | `O(可达集)` |

代数证明拿不到空公理集，原因在 Lean 而不在 pagoda：4.9 core 里每条 `Int` 引理
自身都用 `propext` 证。理由与取舍见 `DECISIONS.md` D-TC-008。

## 用法

```python
from theory_compiler.parser.theory_parser import parse_theory
from theory_compiler.problem import load_problem
from theory_compiler.certificate import load_certificate
from theory_compiler.generators.gen_lean import generate_lean
from theory_compiler.generators.gen_python import generate_python

ast     = parse_theory(open("theory.dsl", encoding="utf-8").read())
problem = load_problem("problem.json")

exec(generate_python(ast, problem))              # 预测器

cert = load_certificate("../engine-rig/interop/certificates/pagoda_5_11011_to_00010.json")
open("Theory.lean", "w", newline="\n").write(generate_lean(ast, problem, cert))
```

## 开发

```bash
cd theory-compiler
pip install -e ".[dev]"
python -m pytest          # 73 passed
```

Lean 编译测试需要 `lean` 在 PATH 上（4.9.0，无 Mathlib）；不在则自动跳过。
