priority: 3
cell: C1
territory: theory-compiler
deps: none

# C9 · 关系词汇表切不开 count-lock 世界（表达力缺口，worldgen 实测）

W-1610 在 C1-worldgen 的质检层实测：把 worldgen 新造的 `t2-lock-fragile`
（count-lock + consumable 复合）喂给 `cold-start-a0/pipeline` 会**抛异常**——
a0 的关系词汇表说不出「集齐 k 个才开锁」这类计数条件，格式与 cold-start-a0 完全一致，
故不是接口问题而是**表达力缺口**（详见 monitor/inbox/archive 里那份提案）。

做：给守卫语言加计数谓词（`count(Type, pred) >= k` 一档，不要一步跨到全称量词），
过表达力台账登记（哪个世界逼的、加了什么、v1 语言原本说不出什么）；四份既有 DSL
不回归；worldgen 的 count-lock 世界跑通 cold-start-a0 流水线作为验收。
**这是 Theoria.md 1.8「表达力台账」条款的正例——扩一格要有出处。**