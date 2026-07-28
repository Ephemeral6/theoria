priority: 2
cell: C3
territory: theory-compiler
deps: none

# C8 · 分层移交包：让说明书真的能被一个陌生 agent 读懂

Theoria.md 1.11 的移交测试要两档交付物：**只交说明书** / **说明书 + 玩法书**。
exam 侧已有判卷雏形，编译器侧还没有「可移交包」这个产物。做 `theory_compiler` 的
`handover` 生成器：给定一份 theory.dsl（+ 可选 playbook.dsl），产出一个自包含目录——
四形态 + 确定性 pretty-print 的自然语言渲染 + 词汇表索引 + **不含任何会话上下文**。

验收：拿 cold-start-a0 与 a0-spike 两份手册各出一个包，派一个**全新 subagent**
只读包（不给仓库其余部分）回答三问：这个世界的 step 语义是什么、哪些名字是关卡数据、
给定状态下的最优动作。答错即包不合格——修包不修读者。
