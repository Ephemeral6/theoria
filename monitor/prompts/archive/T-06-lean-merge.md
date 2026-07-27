# T-06 · theory-compiler 汇合 sprint：AST 通用生成器 + 消费 LP 证书 = 真 A1

你在 Theoria 仓库的 **theory-compiler 轨道**，只碰 `theory-compiler/`（及
`PARTNER_SYNC.md` 自己的段落）。先读 `CLAUDE.md`、`Theoria.md` 的 A1 验收
定义与 1.10(a) 同源多形态，再读 `theory-compiler/STATUS.md` 的「与正式 A1
验收的差异」一节 —— 这个工单就是那三条差异的清偿。

## 背景

M8 彩排用了手算常量 `[1,2,3,2,1]` 和 BFS 枚举证明。同时 A0 那边记录了
D-A0-011：`gen_lean.generate_lean` **完全忽略它的 TheoryAST 参数**，直接
硬编码一维孔明棋；`gen_python` 也近乎特化。于是仓库里长出了第二套生成器
（`cold-start-a0/compile/`），约束 1 的「同源」出现分叉。engine-rig 已把
桥搭到你门口：`engine-rig/interop/certificate_export.py` 导出整数化的
pagoda 权重 + 逐义务的算术，`interop/out/` 里有现成的证书 JSON。

## 任务

1. **消费 LP 证书**：`gen_lean` 增加从 engine-rig 证书 JSON 读权重的入口
   （读它的 `out/` 文件，不 import 它的代码 —— 跨轨道以数据文件为界）。
   Lean 证明从 BFS 枚举改为 pagoda 代数归纳：inv_init / inv_closed /
   goal_break 逐条由证书里的算术离散化（omega / decide / norm_num），
   Lean 只查不搜。
2. **生成器去特化**：`gen_lean`、`gen_python` 改为真正消费 TheoryAST。
   两个试金石：(a) 现有 `peg_theory.dsl` 产物不回归；(b) 拿
   `cold-start-a0/theory/theory.dsl`（只读，别改它）能生成**类型正确**的
   Lean 与可运行的 Python —— 不要求把 A0 的证明打完，要求结构上不再
   硬编码 PegState。A0 的 `compile/gen_*_a0.py` 是现成的参考实现，
   读它、超过它，但不修改它。
3. **D-A0-013 修复**：`theory_parser._parse_func_call` 的
   `r'(\w+)\(([^)]*)\)'` 在嵌套括号/元组参数上静默产出错误 AST
   （`jumped(Cart, (1, 1))` → 参数名 `"(1, 1"`）。修成递归或配对计数解析，
   加负向测试。
4. A1 正式验收重跑：孔明棋规格 → DSL → LP 权重（来自证书文件）→ Lean 验
   封闭引理，依赖假设为空。`STATUS.md` 把「与正式 A1 的差异」清零或
   如实缩减。
5. 提交 + `PARTNER_SYNC.md` 追加一段（写明消费了 engine-rig 哪个文件的
   哪个哈希，这是两轨道第一次真正的数据接合，值得记清楚）。

## 红线

- 不改 `engine-rig/`、`cold-start-a0/` 的任何文件 —— 跨轨道只读。
- `CONTRACTS/dsl_grammar_v0.1.md` 归你的轨道所有，但改语法要递增版本号并
  在文件内记明哪条规则逼的（表达力台账纪律）；`candidates_schema.md` frozen，
  不许碰。
- Lean 工具链版本钉死在 `lean-toolchain`，不升级。

## 验收

- `python -m pytest`（theory-compiler）绿，49 条不回归。
- A1 链条端到端：LP 证书文件 → gen_lean → `lake build` 绿，无 sorry、
  无 BFS 枚举。
- 对 A0 的 theory.dsl 生成不抛异常且 Lean 类型检查通过。
