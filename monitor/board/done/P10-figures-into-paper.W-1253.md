priority: 2
cell: P2
territory: figures
deps: none

# P10 · 图进正文：六张图现在只是脚本，论文里还是文字

`figures/` 已有确定性生成脚本与 P8 的账单形状流水线，`papers/PAPER.md` 已到 v0.2 并
补完 §7。但两者没接上——图在 figures/ 自成一体，正文里引的还是文字描述。

做：(1) 逐图产出发表规格的 SVG+PNG（论文用双主题、无障碍色板），命名与 §编号对应；
(2) 每张图配一段 caption，写明数据来自树上哪个文件、哪次 run；(3) 在 `papers/figures/`
建索引（图号→生成脚本→数据源→sha256），让任何人能一条命令重生成全部图；
(4) 正文里把「见图 X」的位置补齐，缺数据的图如实标 pending 并说明缺什么。
**不改 papers/ 之外的东西**，与 papers 领地的会话通过 PARTNER_SYNC 协调。
