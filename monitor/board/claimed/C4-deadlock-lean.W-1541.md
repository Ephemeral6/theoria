priority: 4
cell: C4
territory: theory-compiler
deps: none

# C4 · 死锁定理与 IC3 不变量进 Lean

engine-rig M9 产出了带证书的死锁定理与 IC3 归纳不变量，但它们还没走完「Lean 只查不搜」那一步。把两类证书接进生成器：死锁 → 条件化不可达定理；IC3 → inv_init/inv_closed/goal_break 三件套。跨轨道以数据文件为界（读 engine-rig 的证书 JSON，不 import 其代码）。验收：至少各一条在 Lean 里编译通过、公理集为空。
