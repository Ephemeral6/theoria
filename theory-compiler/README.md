# Theory Compiler

Theoria DSL 编译链：将 `theory.dsl` 和 `playbook.dsl` 编译为四种生成物。

## 组件

| 组件 | 输入 | 输出 |
|------|------|------|
| DSL Parser | `.dsl` 文本 | AST |
| theory.py | AST | 可执行 Python 模拟器 |
| theory.lean | AST | Lean 4 证明框架 |
| theory.md | AST | 自然语言文档 |
| theory.pddl | AST | PDDL domain + problem |
| playbook parser | `.dsl` 文本 | Playbook AST |

## 开发

```bash
cd theory-compiler
pip install -e ".[dev]"
pytest
```

## Lean 项目

```bash
cd theory-compiler/lean
lake build
```
