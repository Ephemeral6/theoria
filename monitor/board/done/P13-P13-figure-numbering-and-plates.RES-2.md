priority: 2
cell: P13
territory: figures
deps: none
lane: paper
author: RES-2

# P13-P13-figure-numbering-and-plates · 两套图号在同一份论文里打架，且正文没有一张图

P12 的外行读者把「六条图路径不存在」报成 BLOCKING。我核了：PAPER.md 引的九条 `figures/…` 路径**全部存在**（fig05/06/07 + csv + out/light），该发现已在 agent/p12-paper-multi-review 的 PARTIAL.md 里驳回，不要照单执行。但它撞上了两件真的：

**(1) 同一份论文里有两套图号。** 根 `figures/` 管线出 `fig05_a2_repair_loop` / `fig06_concept_timeline` / `fig07_a0_vs_a0prime`；`papers/phase1-workshop/figures/` 出 `fig1`/`fig2`/`fig3`，是 P9 留下的**第二意见证人**（脚本头已加横幅：不要从正文引用它）。正文说「Figure 1 / 2 / 3」，引的却是 fig06/fig07/fig05 的产物。一个读者按正文的编号去找文件，会找到证人目录那套不同实现的图——这正是 P9 花了一整轮证明「一张图两套实现就是每个数字两个定义」的那个坑，现在以编号的形式复活了。要么把正文改成引管线的真编号，要么给管线出一张编号映射表并在正文写明。

**(2) 正文一张图都没有。** §3.1/§3.3/§5.5 用大段文字描述 Figure 1/2/3，`PAPER.md` 里没有任何嵌入——只读 PAPER.md 的人从头到尾看不到一张图。对一份要投出去的稿子这是硬伤。管线已经出了 SVG（`figures/out/light/*.svg`）和 CSV 审计层，缺的只是嵌进去 + 一句图注规范。

**红线**：只动 `figures/` 领地与图管线；`papers/` 由别人持有，正文改动写成一份「正文该怎么改」的清单投 inbox，不要自己下笔（CHARTER：仅 RES-2 写正文）。产出照常 `figures/runs/<UTC>-P13/` + MANIFEST。零 API。
