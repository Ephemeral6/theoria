priority: 1
cell: C2
territory: worldgen

# V25-worldgen-unchecked-is-not-holding · 十三份基准真值把「没检查」写成了「成立」

审计（2026-07-29）按 HEAD 的 blob 重扫复现（**不是工作树脏**）：
`worldgen/out/**/ground_truth.json` 共 35 份，其中 **13 份**带着没有 `holds` 键的
不变量，却都报 `invariants_all_hold: true`。成因是 `core/truth.py:279` 的
`all(i.get("holds", True) for i in invariants)`——缺省值指向「成立」。

审计还说：修复提交 `23ec179` **不在 master 上**。所以这一件先查状态再动手。

做四件：

1. **先判现状**：`git show 23ec179 --stat`、它在哪条分支上、为什么没合。
   已经修好只是没合，就把合并卡点写清楚并推动；没修就修。
2. **三态取代布尔**：`holds` / `violated` / `unverified` 各自成一类，
   `invariants_all_hold` 只在「全部 holds 且 unverified 为空」时为真。
   **任何机器读的字段不得比同一份 Markdown 更乐观**——
   这一处的 Markdown 渲染一直是诚实的，只有那个布尔在说谎，而消费判决的是布尔。
3. **重生成那 35 份并报数**：多少份从 true 翻成非 true，逐份列出。
   翻了多少不是坏消息，**那是这次修复的全部证据**。
4. **负样本两条**：一条只有散文、没有 `holds` 的不变量（断言不得算成立）；
   一条真违规（断言仍然报违规，别把保守修成一律拒绝）。

顺手查同族：`worldgen/` 里其它 `.get(..., True)` / `.get(..., 0)` 形状的缺省值，
**缺省值指向好消息的地方都是候选**。

服务论文 WP1（世界工厂可信度）与 WP5（考卷与电池所依赖的基准真值）。
零 API、零封存堆接触。
