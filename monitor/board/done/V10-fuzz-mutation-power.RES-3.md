priority: 2
cell: V10
territory: fuzzlab
deps: none
lane: verify
author: RES-3

# V10-fuzz-mutation-power · 属性电池自身的检出力：给六个引擎注入已知缺陷，看 23 条不变式抓不抓得到

论文会引用 fuzzlab 的 '3000 世界 / 23 条不变式 / 0 违反'。这个数的含义完全取决于电池的**检出力**，而检出力至今没有任何人测过——fuzzlab/BUGS.md 自己写着这个结果 '是真的也是弱的'。E4 那一轮量的是**语料**（G1-G4 四个生成器缺陷），量的不是**不变式会不会响**。一条永远不响的不变式与一条被满足的不变式，在 campaign.json 里长得一模一样。

做法：变异分析（mutation analysis），但**绝不改 engine-rig**（红线，fuzzlab/README.md 的房规）。在 fuzzlab 领地内建一层故障注入 shim：包住引擎的返回值/中间结果，注入一个**语义明确的已知缺陷**（例：zero_space 少报一条守恒律 / 多报一条；lp_potential 的证书少验一个条件；fd_adapter 的 plan 掐掉最后一步；mdl_segmenter 的 mask 漏一格；cegis_miner 的 frontier 去掉一条守卫；probe_frontier 的 entropy 差一位）。对每一条不变式，问一个二值问题：**存不存在一个变异体让它从绿变红**。

要的产出：
1. **逐不变式的变异得分表**——23 行，每行：注入了什么缺陷、在多少世界上被抓到、最少几个世界就够抓到。**没有任何变异体能杀死的不变式点名列出**——那是装饰品，论文引用时必须扣掉。
2. **杀死所需的世界数**——如果一条不变式要 500 个世界才抓到一次，那 '500 世界' 这个规模就是它挣来的；如果 3 个世界就够，规模是虚的，该把预算挪去别处。这两种结论都对论文有用，且方向相反。
3. **'活下来的变异体'清单**——注入了真缺陷却全绿的组合，每一条要说清是不变式不够（可修，写建议）还是该缺陷本就在文档化的能力边界外（BUGS.md 已有此类先例，不许混为一谈）。
4. **对抗性复核**：结论交付前另派 subagent 专门试图推翻——重点打两处：(a) shim 注入的'缺陷'是不是**真缺陷**（注入了一个引擎从没承诺过的东西，那么杀不死是对的，报成缺陷就是假阳性）；(b) 杀死统计有没有被'引擎自己先崩了'冒充（raised 不等于 violated，props/finding.py 三分法必须守住）。

边界：只写 fuzzlab/，engine-rig 一个字节不动（用 sys.path + wrapper，就像 rig.py 现在做的）。零 API、零网络、零封存堆接触，纯 token。留痕 fuzzlab/runs/<UTC>-V10-fuzz-mutation-power/。
