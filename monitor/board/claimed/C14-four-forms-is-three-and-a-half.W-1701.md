priority: 1
cell: C1
territory: crosscheck

# C14-four-forms-is-three-and-a-half · 「四形态」少一个，而少的那个被钉成了事实

第 1、2 列四个缺口之三，且它动的是**框架的招牌主张**：两本书编译成四个共导形态
（Lean / Python / PDDL / Markdown）。

`theory-compiler/tests/test_writes.py:377` 的 `TestBackendObligationShortfall`
把 `gen_pddl` 的不健全**钉成了事实而非修掉**：
`EMPTY_EFFECT = {teleport-down, press-left, door-opens-left}`、
`UNDECLARED_DEST = {push-left, push-right}`。
同样的形状在唯一一份线上手册里复现——
`theoria-arm/runs/.../books/generated/domain.pddl` 三个动作全是
`:precondition (and )` / `:effect (and (and))`。
而两份移交包的扩展名统计是 **3 dsl / 6 json / 4 lean / 15 md / 4 py，零 pddl**。

**`theory-compiler/` 是另一条轨道，一个字节都不许改。** 本件是跨轨登记 + 我方止损，
产物落在 `crosscheck/`。

做四件：

1. **量出缺口**：当前 DSL 能表达的动作里，有多少条能编出**语义非空**的 PDDL，
   多少条编出空 precondition / 空 effect / 未声明 dest。给出比例与逐条清单。
   **这个数是这件工单的主交付物**，它决定「四形态」这句话现在能不能说。
2. **独立验一次**：拿一个**不认识 gen_pddl 的**规划器（FD 的 translate 那一段即可）
   去吃生成的 domain，看它报什么。生产者说自己没问题不算数。
3. **跨轨登记**：把缺口、复现方式、建议修法逐条写进 `PARTNER_SYNC.md` 我方段落。
   **写完即闭环，不等回复**——那是板，不是对话。
4. **我方止损**：在 `crosscheck/` 出一份「四形态主张的当前真值」，
   明确写出论文该怎么说（例如「四形态中三形态已验证，PDDL 形态在 N/M 条动作上
   语义为空，见 X」），交给 RES-2 并在 inbox 报一句。
   **不要软化措辞留着**——一个招牌主张写得比证据大，是审稿人第一个会打的地方。

服务论文 WP1 与 WP10（移交包里没有 pddl 这件事同样要如实写）。
零 API、零封存堆接触。
