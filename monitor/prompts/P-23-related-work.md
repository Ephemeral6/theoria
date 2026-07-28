# P-23 · 相关工作与引文库：§7 的弹药

基准 `Theoria.md`（3.1 三波谱系 + 3.2 第 7 节的六条线：世界模型三波、规划的证书与启发、CEGIS/ILP、Petri 不变量与 IC3、证明携带代码、LLM+定理证明）。开工仪式：读 `CLAUDE.md`、`papers/phase1-workshop/`（P-16 的初稿，你的下游），绿了开工。
分支制：`agent/p23-related-work` + 独立 worktree；push 分支不碰 master。领地：`papers/related-work/`（papers 下新增子目录，不动 P-16 的文件——它的分支可能未合并）。

目标：六条线各一节 + BibTeX 库：

1. 每条线：3–8 篇真实文献（可用 WebSearch/WebFetch 核实题录——**只查学术文献，不碰任何 ARC 游戏攻略/机制页面**，封存红线在检索场景同样生效，前车之鉴 INC-BA-001）；每篇一句「它做了什么」+ 一句「我们的 delta」；
2. `references.bib`：逐条经两个来源交叉核实（标题/年份/venue 对得上才收；核不实的挂 unverified 段落，不混入正库）；
3. `RELATED.md`：可直接并入论文的行文草稿，贯穿 Theoria.md 的主轴句（每波升级的是检验制度）；
4. 特别核实一条：Schema 的规范署名（baseline-arms 已发现应为 Zeng et al. 非 Feng et al.）与正确引用格式。

证据纪律最高优先：**查不到的文献宁可不引**，杜撰题录是这个仓库最不可原谅的漂移（A-1 会抽查）。子代理按六条线并行，各自附检索留痕；对抗性子代理抽查 20% 题录复核。
留痕：`papers/related-work/runs/<UTC>-p23/`（每次检索的 query 与结果落盘）。收工：RUN_STATE + MANIFEST(prompt_id: P-23) + PARTNER_SYNC + push。全程自主。
