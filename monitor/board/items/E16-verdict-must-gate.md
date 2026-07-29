priority: 1
cell: E16
territory: engine-rig
deps: none
lane: verify

# E16-verdict-must-gate · 算对了、发布了，然后不拿它把关

对偶普查（RES-3 第四路，约 105 处判据点，判不安全 8 处）找到的形状**不是**
「没验」，而是：**判决算对了，写进了产物的一个兄弟字段，而头条字段不看它。**

先记好消息，因为它是真的：`fd_adapter/__init__.py:140` **无条件**调用
`validate_plan()`，三档全过含真 FD，而且 `validate.py` **刻意不 import `search`**
——验证器不认识搜索器，这是结构保证，不是承诺。`ic3_pdr` 用不共享搜索代码的
枚举器复验，不过就 `raise`。**「求解器返回计划就认定可解」这件事在本仓库没有发生。**

两处要修：

1. **`engines/lp_potential/potential.py:255` 的 `"admissible": True` 是个字面量。**
   不是算出来的，是写死在 payload 里的。实测：拿一张 `holds=False` 的证书造
   `Heuristic`，这个字段照样是 `true`——而**真正的可采纳性检查就躺在同一份
   payload 的 `admissibility_check` 里**，头条不看它。
   改成读那个检查的结论；**负样本**：`holds=False` 的证书必须让该字段为假。

2. **`engines/deadlock_carver/__init__.py:168-180` 是 carve → report → emit，
   中间没有一个 `if`。** 那份 report 里的 `same_answer`（「这条定理有没有改变
   实例的答案」）会被算出来、序列化成 `plan_length_unchanged`，
   **然后和它所证伪的那条定理并排发布**。读者拿到一条定理和一份说它没用的报告，
   摆在一起，没有谁压过谁。
   改成：`same_answer` 证伪时**不得照常 emit**——要么不发，要么发出去的候选自带
   一个**机器可读**的失效标记（不是散文）。**负样本**：造一条会被证伪的定理，
   断言它进不了候选流、或带着失效标记进。

3. 顺带把 RES-3 单列的「验了但不独立」六处写进 `DECISIONS.md` 的边界叙述：
   `lp_potential` 与 `moves_from_graph` 共享后继关系、`ic3_pdr` 与 `system.moves`
   共享、`interop/certificate_export.verify` 只复算生产者列出的 witness
   （而它的 docstring 自称 importer 无需信任生产者）。
   **「验了一道」和「用独立的东西验了一道」是两件事**，措辞要分开。

服务论文 WP1 与 WP9。零 API、零封存堆接触。
`cold-start-a0/` 的两条同族只登记进 PARTNER_SYNC，不动手。
