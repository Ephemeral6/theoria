priority: 2
cell: P2
territory: papers
deps: none
lane: paper

# P7 · 论文第 7 节 + 把过时的电池章节改对

PAPER.md 已到 v0.2（三块新成果已进正文）。两件遗留：

(1) **§7 相关工作**：世界模型三波谱系、规划的证书与启发（势启发/LM-cut/PDB）、
CEGIS 与 ILP、Petri 不变量与 IC3、证明携带代码、LLM+定理证明。每条 3–8 篇**真实**
文献，交叉核实题录（查不到宁可不引——杜撰题录是本仓库最不可原谅的漂移）；
每篇一句「它做了什么」+ 一句「我们的 delta」。

(2) **电池章节已过时**：W-1610 报告 §7 相关段落停在 battery v0，而电池已到 v2
（见 `battery/` 与 `monitor/inbox/` 那条提案）。按当前 REPORT 改写，数字全部指回文件。

顺带把 `papers/REVIEW.md` 的未清项列成清单，标明哪些需要新实验、哪些只是写作。
