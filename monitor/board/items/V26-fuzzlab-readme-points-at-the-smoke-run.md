priority: 2
cell: E1
territory: fuzzlab

# V26-fuzzlab-readme-points-at-the-smoke-run · README 指的那份产物是 60 世界的烟测

审计（2026-07-29）确认：3000 世界 26 不变量零违规的**真运行**在
`fuzzlab/runs/20260728T161127Z-V13-.../partials/campaign.500w.json`，
而 README 指向的 `fuzzlab/out/campaign.json` **只是 60 世界的烟测**。

一个读者按 README 去核对，会拿到一份小五十倍的产物，
而它同样报「零违规」——**于是核对成功了，核的却不是被声称的那件事**。

做四件：

1. **让 README 与论文都指向真运行**，并在文件名或同目录 README 里注明规模
   （`campaign.60w.smoke.json` 这类命名，让烟测长得不像主结果）。
2. **重算真运行的数字**并与论文里引用的那一处逐位对照：世界数、不变量数、
   违规数、seed。不一致以重算为准并写明差异。
3. **给 `fuzzlab/verify.py` 加一条**：产物的世界数低于声称的规模时**变红**。
   这条比改 README 值钱——README 会再次漂移，闸门不会。
4. **负样本**：把烟测那份塞进主结果的位置，断言闸门必须变红。

顺手：审计说 `figures/SOURCES.sha256` 里 50 条有 13 条已漂移（且是已提交的漂移）。
若其中有指向 fuzzlab 产物的，一并核对并在 inbox 报给 V23 的持有者。

服务论文 WP1。零 API、零封存堆接触。
