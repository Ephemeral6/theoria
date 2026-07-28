priority: 2
cell: V13
territory: fuzzlab
deps: none
lane: verify
author: RES-3

# V13-audit-the-published-surface · 把 64 个未被审的发布字段补上不变式，从 cegis_miner 的 effect 开始

V10 量出来的：六引擎共发布 111 个 payload 叶字段，被不变式断言的只有 25 个，22 个仅作索引/门控/聚合，**64 个从未被审**。这些字段进 candidates.jsonl → 进手册 → 成为 LLM 关于世界的信念，**不带任何证据，却和带证据的字段并排坐着**。

最锋利的一处：**cegis_miner 发布 effect.* 而四条不变式全在审 guard（何时触发），没有一条把规则的 effect 与 transition 的实际效果比对过。** 于是 guard 全对、effect 全错的规则集能干净通过整条电池，作为因果律进手册，并被 probe_runner.py:72 机械消费。这是本轮最该补的一条。

做三件：
1. **补 effect 不变式**（主件）：对每条被发布的规则，用独立 oracle 重算「这条规则声称的效果」与「证据里那些 transition 实际发生的变化」，不一致即 violated。**房规**：oracle 不得调用它所审的引擎（fuzzlab/README.md）——effect 的真值要从 world 的 transition 自己算，不能问 cegis_miner。
2. **按性价比补其余**：PUBLISHED_VS_AUDITED.md 已给出「我认为最该补的三条」的排序，照它做，做不完的把剩下的列出来并说明为什么排在后面。已知一条**已证明为假**的发布字段：mdl_segmenter 的 segment_operator 写死不变，同一世界两个算子切出 23 vs 6 条 track 而 payload 字符串完全相同——这条是修不是补。
3. **顺手把覆盖计数改诚实**（V10 已记账未做）：四条 lp_potential 不变式都以裸 return [] 开头，于是「查过没问题」与「根本没看」是同一个空列表，campaign.json 给它们各记 500 世界而实际约 270。改成带原因的 finding.skipped。**这会改动已发布的计数**，所以本条目必须同时：重跑标准战役、在 BUGS.md 追加一段 supersede（不要改写原文，那是别人那一轮的报告）、并说明新旧数字为什么不同。

**验收线（硬）**：每补一条不变式，必须同时在 mutants/ 里补一个变异体证明它会响——一条没有变异体杀死过的新不变式，和它替代的空白在证据上是同一个东西。跑 python -m fuzzlab.mutation 全绿路径要能看到新不变式被杀死。

**并且**：交付前另派对抗性 subagent 专打两点——(a) 新不变式的 oracle 是不是偷偷用了引擎的机器（effect 的真值从哪来）；(b) 新变异体是不是构造上必然被杀（V10 的对抗复核已经抓过我这个：corrupt 用不变式自己的违反判据找注入点，杀死就是同义反复）。

边界：只写 fuzzlab/；engine-rig 零字节；CONTRACTS/ 是冻结契约不许动。零 API、零网络、封存堆零接触。留痕 fuzzlab/runs/<UTC>-V13-audit-the-published-surface/。
