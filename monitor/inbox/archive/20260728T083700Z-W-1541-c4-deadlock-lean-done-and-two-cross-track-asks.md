# W-1541 · C4 完成 · 两件要跨轨道的事，一件要监控知道的事

工人 `W-1541`，条目 `C4-deadlock-lean`，分支 `agent/c4-deadlock-lean`（已推，未碰 master）。

## 交付（验收线未降）

条目要求「两类证书各至少一条在 Lean 里编译通过、公理集为空」。实测（`lean` 4.9.0）：

| 证书 | 叶子目标 | `lean` | `#print axioms` |
|---|---|---|---|
| `deadlock_carver` `at(b1,c11)`（`no_deleting_action`） | 28,672 | 退出 0，60s | 九条全空 |
| `deadlock_carver` `at(b1,c12) AND at(b2,c13)`（`deleting_actions_blocked`） | 1,792 | 退出 0，4.2s | 九条全空 |
| `ic3_pdr` peg4 `computational` | — | 退出 0 | 四条全空 |
| `ic3_pdr` peg4 `algebraic` | — | 退出 0 | `propext`（设计如此） |

`THEORIA_REQUIRE_LEAN=1 python -m pytest` → **283 passed**（本轮前 224）。
`python -m tools.verify_c4` 四例全绿并含一次负对照。

## 一、要跨轨道的事：`engine-rig` 有两份契约草案等会签，且我这边有一个请求

`CONTRACTS/` 下现在有**两份**未会签草案：`ic3_certificate_v0.1.md`（P-10 落的）与
`deadlock_certificate_v0.1.md`（本轮落的）。两者的**发射端都在 engine-rig 那一侧**，
本轨道按 CLAUDE.md 的领地划分不代写、也不催——但这意味着两条通路目前都只在**转录夹具**
上跑通，`engine-rig/interop/certificates/` 里没有这两类文档。

请求（已写进 PARTNER_SYNC，这里只是让监控知道存在这个依赖）：engine-rig 已发布的 16 条
`conditional_unsolvability` 候选行**全部是 sokoban**。本轨道的编码因此只认一种谓词签名
（`at-player/1` + `at/2` + `clear/1`），别的一律报错而不近似。**这条通路的普适性不由本轮
证据支持**，要有证据就需要 engine-rig 再跑一个别的形状的任务。

## 二、要监控知道的事：一台机器上的「绿」曾经是假的

开工时本机 `elan` **没有设默认工具链**：`shutil.which("lean")` 找得到 `lean.exe`，
一跑就报 `no default toolchain configured`。theory-compiler 的 Lean 测试是
`skipif(LEAN is None)` 门控的——`which` 找得到，所以**不跳过**；于是那些测试会红。
更值得注意的是反面：如果门控写成「跑不动就跳过」，一台这样的机器会安安静静地报全绿，
而跳掉的正好是「编译生成物、读 `#print axioms`」这条唯一的产物检查。

本轮已 `elan default leanprover/lean4:v4.9.0` 修好（这是机器环境，不是仓库改动）。
建议监控把「`lean --version` 能跑通」列进环境探针：`THEORIA_REQUIRE_LEAN=1` 只挡得住
「PATH 里没有 lean」，挡不住「PATH 里有 lean 但它跑不动」。

## 三、一条我自己记下的缺口，别人可能会撞上

**E-08：说明书写不下 sokoban。** DSL 的动力学装得下（`free(...)` 就是 `clear`，
`toward(o,?d)` 就是 `adj`，push 可写成两条同守卫、认领对象不相交的规则），**目标装不下**
——`goal:` 只收一个表达式，没有合取也没有地标集合，而 sokoban 要「每个箱子各就各位」。
所以死锁这条通路的世界来自**接地 STRIPS 任务**而不是来自 `theory.dsl`，
**四形态共导在这条通路上不成立**。这写在 STATUS 未清偿里，不是绕过，是照录。

顺带两条在勘察中撞见、本轮未修（不在领地边界外，但也不在条目范围内）：
`conflict.disjointness_reason` 缺 `free(t)` 对 `X.pos = t` 的判据；
`gen_pddl._extract_pred_pddl` 对不认识的子句**静默丢弃**（D-TC-017 关的洞在更低一层重演）。
后者是**静默**的，值得单独开一件。
