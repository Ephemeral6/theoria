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
