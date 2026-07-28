# P-5 · theory-compiler 汇合 sprint：一个源、四种形态、真 A1、refuse 语义

基准文件是 `Theoria.md`（约束 1 同源多形态、A1 验收定义）；再读 `CLAUDE.md`、`theory-compiler/STATUS.md` 的差异清单，以及三份写给你的输入（只读）：`a0-spike/GENERATOR_REPORT.md`（gen_python 把编译不了的守卫静默替换成 True——它废掉的正是 certify）、`cold-start-a0/DECISIONS.md` D-A0-011/013、`cold-start-a0/proposals/dsl_grammar_v0.2_semantics.md`（帧公理句型的正式扩展请求）。
领地：`theory-compiler/` 与 `CONTRACTS/dsl_grammar_v0.1.md`（归你，修订须递增版本并记明哪条规则逼的；candidates_schema frozen 不碰）。提交只 add 自己领地。

目标：清偿全部已知债务——

- **refuse 语义**：生成器遇到超出支持子集的构造一律 raise，绝不静默近似（GENERATOR_REPORT 的建议规则，最高优先）；
- 生成器去特化：真正消费 TheoryAST。试金石：peg 不回归；`cold-start-a0/theory/theory.dsl` 与 `a0-spike/theory/theory.dsl` 都能生成类型正确的 Lean 和行为正确的 Python；
- 消费 `engine-rig/interop/out/` 的 LP 证书（跨轨道以数据文件为界），Lean 证明改 pagoda 代数归纳，真 A1 达成（无 sorry、依赖假设为空）;
- 裁决 v0.2 `semantics:` 提案：采纳则升版语法并实现，拒绝则书面说明理由回 proposals/；
- 修 `_parse_func_call` 嵌套括号静默错误，加负向测试。

技巧要求：**移交测试用 subagent 当真读者**——每轮生成器改完，派一个全新 subagent 只给 theory.dsl 与生成的四形态、不给任何上下文，让它回答「这个世界的 step 语义是什么、哪些名字是关卡数据」，答错即文档失败，修文档不修读者；两个 DSL 夹具（cold-start-a0 与 a0-spike 的）各派一个 subagent 并行做兼容验证；测试挂后台循环跑到 49 条全绿加新增。

全程自主，不停下来问。完成即提交 + PARTNER_SYNC 追加一段（写明消费与裁决了哪些输入）。
