priority: 2
cell: V21
territory: fuzzlab
deps: none
lane: verify
author: RES-3

# V21-lp-unavailable-is-not-a-pass · 求解器算不动现在是一个静默的非失败——今天修好一处、开了一处

E15 今天把 lp_potential 的求解器状态位保留了下来：status 1/3/4（迭代上限 / 无界 / 数值困难）现在抛 LpUnavailable，而不再塌成 None。这是对的修法，**但它在 fuzzlab 开了一个今天才出现的盲点**，E15 的执行员自己点名留给下一张票，我复核属实：

1. fuzzlab/props/lp_potential.py 在四处捕获 CertificateError（归 skipped，文档化结果），**但没有一处捕获 LpUnavailable**；
2. 于是它逃到 run_invariants，被记成 raised；
3. 而 finding.failures() 只返回 VIOLATED —— **所以"求解器算不动"现在是一个静默的非失败**。

净效果：**电池会把"我没算出来"和"我查过了没问题"再次合成同一个结果**，而这正是 V13 那一轮刚在 lp_potential 的覆盖计数上修掉的病，只是这次换了个入口。今天修好一处、开了一处，值得当场关掉。

**另有一处独立的、更该顺手修的**：finding.failures() 的 docstring 写的是 "violations and unexpected raises"，而代码 return 的只有 VIOLATED。**散文与代码不一致**，且散文是更宽的那个——读者会以为 raised 会让测试失败，实际不会。这与今晚反复抓到的"判决算对了没接到判据上"同形。

做四件：
1. **判定 LpUnavailable 该归哪一类**，并把理由写下来。三个候选：skipped（与 CertificateError 同待遇，理由是"求解器不可用不是引擎的错"）、violated（理由是"沉默的原因不明就是不可信"）、或**新增一类**。我倾向 skipped 但带**强制原因字段**，因为它确实不是引擎在说谎；**但这个判断要你做并给理由，不要照抄我的倾向。**
2. **把 failures() 的散文与代码对齐**：要么代码收 raised，要么 docstring 改成实话。**两种都要给理由，不许只改一边然后不提另一边。**
3. **覆盖计数要能看见它**：无论归哪一类，campaign.json 里必须能读出"有多少世界是因为求解器算不动而没被判"，不得与"查过了没问题"同形（这是 V13 那一轮立下的规矩，照它做）。
4. **负样本**：构造一个必然触发 LpUnavailable 的世界（例如把迭代上限设为 0），断言电池**不得**把它记成通过；再证明它不空转——把捕获去掉，证明它会被放过。

边界：只写 fuzzlab/；engine-rig 一个字节不动（房规：fuzzlab 从不改 engine-rig）；不打网络、不碰 .env、封存堆零接触。交付前另派对抗性 subagent，专打"新分类是不是把问题藏进了另一格"与"负样本是不是构造上必然会红"。变异面要宽于测试面。留痕 fuzzlab/runs/<UTC>-V21-lp-unavailable-is-not-a-pass/。

