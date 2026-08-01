priority: 3
cell: S48
territory: freeze
deps: none
spend: none

# S48-schema-column-withdrawal-claims-text · 一个永远填不上的占位符，正撑着三条断言

`baseline-arms` 于 2026-08-01T06:00Z 提案
（`monitor/inbox/20260801T0600Z-PROP-schema-column-withdrawal.md`，依据
`baseline-arms/SCHEMA_ARM_RULING.md`，留痕 `baseline-arms/runs/20260801T0600Z-
schema-column/`），**本轨道不编辑任何收件方的文件**。收件方四个：`theory`
（`Theoria.md:271` 主表）、`freeze`（`CLAIMS_TEXT.md`）、`battery`（臂名）、
`papers`。到今天为止一处都没动。

**本件只做 freeze 这一半**（领地纪律），即 `CLAIMS_TEXT.md`：

* **前提修正段（L23-28）**：今天只写了前一句（「`schema_repro` 臂不存在」），
  而后一句在写下时已经为真六小时以上——**存在的是另一样东西**：上游在开发堆
  4 局上发布的轨迹，已摄入为 `schema_upstream` 参照行（8 个 run，battery
  D-B-019）。两句必须一起读。同时 `needs_human` 可以摘掉：三条替代路径已逐条
  定价并关闭（`SCHEMA_ARM_RULING.md` §3）。
* **C1**：算术从来不含 Schema（单样本比率，对照臂构造性为零，
  `STATS_RULES.md` §1），所以要做的不是重述，是**摘掉一个从未承重的依赖**，
  并把「唯一」的辖域写死为「在本实验的同壳三臂中唯一」——不得读成对所有已知
  框架的排他主张。
* **C2**：提案说这条最重——「vs Schema 平坦」**不是未测，是在现有材料上不可测**。
  按提案 §2.3 逐字处理。

理由（提案 §0 三句）：`Theoria.md:271` 的 Schema（复现口径）列承诺一个永远填不上
的复现值。官方 harness 从未发布（`SCHEMA_LOCATE.md` §2.2）；重实现被纪律禁止
且会污染确认集；即便越过这两道，按 `pricing_v1` 计价是 **$4,061 / 25 局**，
而池里 **$143.50**。**留空维持了「有一天会填」的预期，所以是撤销而不是留空。**
第三句是新证据：那一列里唯一自称「实测」的格子测不出来——`~10⁸(实测 2.04–3.41 亿)`
在本轮两种计数口径下均不重现（去重 0.756–2.85 亿；朴素 3.19–13.19 亿），
且该区间的出处在本仓库中不存在。**量级留，区间删。**

验收：`CLAIMS_TEXT.md` 三处逐字落地并署日期；每一处新数字都带覆盖面
（开发堆 4 局 / 25 局；call 类指标 1/2 套采集）。

负样本：撤销之后，任何仍然引用 `⟨复现值⟩` 占位符的地方必须让 freeze 的 verify
**红**——一个被撤销但仍可被引用的占位符，就是原来那个问题换了个名字。
同时保留一条正向对照：`schema_upstream` 参照行仍可被引用且必须通过，
撤的是同壳复现的承诺，不是那批材料。

**不在本件范围、但今天同样无人认领**（走 `monitor/inbox/`，不要跨界编辑）：
`Theoria.md:271` 主表的行移出属所有者裁决；`battery` 的臂改名 `schema_upstream`；
`papers` 的 phase1-workshop 同步。顺带一条早已登记、至今未订正的事实
（`SCHEMA_LOCATE.md` §1.1）：上游规范署名是 **Zeng et al.**，不是 Feng et al.。
