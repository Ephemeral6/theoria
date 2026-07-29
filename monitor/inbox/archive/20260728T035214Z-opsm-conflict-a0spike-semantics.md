# 语义冲突 · a0-spike 的说明书还是 v0.1，而解析器已经按 v0.2 拒绝它

from: OPS-M（合并裁判，本轮）
基准树: `dc9fad1`（2026-07-28T03:52Z，九个分支合完之后）
处置: **不硬解，留给监控裁决。** 理由见文末「为什么我不动手」。

## 现象

`a0-spike` 整套挂掉：32 条 FAILED/ERROR，全部同一个根因。

```
theory_compiler.parser.theory_parser.SemanticsError: theory.dsl has no
`semantics:` section. The frame axiom, the conflict policy and the cascade
shape are facts about the world, not constants of the framework, and this
parser will not assume them: a v0.1 manual read under an assumed default
compiles silently to a different world. Declare all three:
see CONTRACTS/dsl_grammar_v0.2.md.
```

两边各自都对：

* **theory-compiler 轨道**把 `semantics:` 从可选升成必填（E-03），并拒绝替调用方假设默认值。解析器要求 `frame` / `conflict` / `cascade` 三项齐全，缺一即 `SemanticsError`（`theory-compiler/src/theory_compiler/parser/theory_parser.py:70`、`:126`）。这条改动本身是对的，而且正是 PARTNER_SYNC:141 那条「v0.1 解析器静默跳过不认识的行 → 解析成另一个世界」的修法。
* **engine-rig 轨道**的 A0 冷启动 `a0-spike/theory/theory.dsl` 是 v0.1 写成的，没有 `semantics:` 段。它最后一次改动是 `27e0047`，早于契约 v0.2。

## 这不是本轮合并造成的回归

已实测确认，避免误挂在本轮九个分支头上：

| 树 | a0-spike | cold-start-a0 |
|---|---|---|
| `1a76087`（本轮合并之前的 master） | **已经红**（同一个 SemanticsError） | 绿（47 passed, 3 skipped） |
| `dc9fad1`（本轮合并之后） | 红（32 条） | 红 → 已由本会话修好，见 PARTNER_SYNC |

也就是说 `semantics:` 必填在本轮开始前就已经在 master 上（`1a76087` 的解析器里已有 10 处 `semantics`），**a0-spike 在合并浪潮之前就是红的**。本轮的合并没有让它变坏，也没有让它变好——它只是一直没人看，因为 `monitor/ci_merge.py` 的测试门只跑「这个分支碰过的目录」，而没有任何分支碰过 `a0-spike`。

> 顺带一条给监控的仪器观察：这就是**每分支门跑不出跨轨道集成门**的实例。九个分支全部各自绿灯合入，合完的树上有两个目录是红的。建议在 `ci_merge.py` 之外加一道定期的全量门（本会话是手跑发现的）。

## 修它要做什么决定

给 `a0-spike/theory/theory.dsl` 补一段：

```
semantics:
  frame <...>
  conflict <exclusive | priority: r1 > r2 ...>
  cascade <CASCADE_VALUES 之一>
```

三项都不是接线，是**对 A0 那个世界的断言**：帧公理怎么写、两条规则同时可用时谁赢、推箱子滑两格算不算级联。解析器的报错本身就在说这句话——「facts about the world, not constants of the framework」。选错了，编译出来的是另一个世界，而且会静默地通过。

A0 的既有证据够不够定这三项，我没有把握：`a0-spike` 的规则里有 `walk` / `blocked_*` / 推箱滑两格，`stayed(o)` 事件是被 certify 逼出来的（见 `theory/theory.dsl` 注释），`conflict` 到底是 `exclusive` 还是要一个优先序，得看 341 条转移里有没有两条规则同时可用的情形——这是裁决，不是对齐。

## 为什么我不动手

OPS-M 的红线是**不写业务代码**，只做接线级修复（import / 路径 / 接口对齐）。补 `semantics:` 是在替 A0 的世界作三个事实声明，落在红线外侧。同一轮里另一处红（`cold-start-a0`）我直接修了，因为那是纯字面量对齐——`fd_adapter` 的 Plan 报的是**梯级 id**（`fd-optimal`），下游还在比老的 `"fast-downward"`；两者的区别就是这条线画在哪。

## 请监控裁决

1. 这三项由谁定——A0 的归属是 engine-rig 轨道，但解析器和契约 v0.2 是 theory-compiler 的；
2. 定完之后，`a0-spike` 是补 `semantics:` 跟上 v0.2，还是钉在 v0.1 解析器上（若后者，需要一个显式的版本选择点，否则下次还会这样撞）；
3. 要不要给 CI 加全量集成门（上面那条仪器观察）。
