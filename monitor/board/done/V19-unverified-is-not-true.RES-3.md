priority: 1
cell: V19
territory: worldgen
deps: none
lane: verify

# V19-unverified-is-not-true · 「我验不了这条」被静默写成了「这条成立」

`worldgen/core/truth.py:279`：

```python
"invariants_all_hold": all(i.get("holds", True) for i in invariants),
```

纯散文不变量根本没有 `holds` 键，于是默认值把**未验证**变成了**成立**，
再经 `build.py:166` 升级成清单里的 `invariant_failures: []`。
普查独立数过：`worldgen/out/**/ground_truth.json` 共 35 份，其中 **13 份**
带着没有 `holds` 键的不变量，却都报 `invariants_all_hold: true`。

**这一处的形状值得记住**：Markdown 渲染是诚实的（人读的那份如实显示「未验证」），
**只有机器读的那个布尔在说谎**——而消费判决的是机器。

做四件：

1. **三态取代布尔**：`holds` / `violated` / `unverified` 各自成一类，
   `invariants_all_hold` 只在「全部 holds 且 unverified 为空」时为真；
   任何机器读的字段**不得比同一份 Markdown 更乐观**。
2. **重生成那 35 份并报数**：多少份从 true 翻成非 true，逐份列出。
   翻了多少不是坏消息，是这次修复的全部证据。
3. **负样本**：造一条只有散文、没有 `holds` 的不变量，断言闸门必须拒绝把它
   算作成立；再造一条真违规，断言仍然报违规（别把保守修成一律拒绝）。
4. 顺手查同一份文件里其它 `.get(..., True)` / `.get(..., 0)` 形状的默认值——
   **缺省值指向「好消息」的地方，都是这个病的候选**。

RES-3 在 V16 里发现这条时**没有顺手改**，理由正确并已采纳：那会让 V16 的验收线
变成一件没人复核过的事。所以单开这一件。服务论文 WP1（世界工厂的可信度）与
WP5（考卷与电池所依赖的基准真值）。
