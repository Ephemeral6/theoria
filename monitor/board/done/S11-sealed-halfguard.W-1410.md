priority: 1
cell: S2
territory: arc-recon
deps: none

# S11 · 护栏只装了宽松那一半：`environment_files/` 里装的是**游戏源码**

OPS-B 的核查（提案原文见 `monitor/inbox/archive/`）：`ACCESS_CHECK.md` 第 8 项已按它
上一份提案结案，切成「我们的分数/指标/哈希/方法可释出」与「ARC 的帧/轨迹/源码需书面
许可」两栏——**这一半做得好**。但**封存那一半没有跟着落地**，而两半是同一个发现的两个方向。

风险在于一句话的**位置**：结论 1 现在写「本地缓存 ARC 数据供自己分析是被允许的，无需
申请许可」——**这句在许可维度上完全正确，不要改它**。问题是它独自出现，同一段里没有
任何一句说明**那个缓存里装的是什么**。而 `browser-ops/TERMS.md` §4.2 记着另一半：
官方文档原文说首跑会 "download the game source"，`--game` 缺省即 "plays all available
games"，`make play-local` 是 "Runs your agent against every game in the dataset"。

**即：照着那句"无需许可"去做的第一件事，默认会把全部 25 局的游戏源码拉到磁盘上，
并默认全部跑一遍。** 按 INC-BA-001 的判据，源码比轨迹更靠前一档——它直接给出机制的
成品答案，比玩那一局更糟。

做三件：(1) `ACCESS_CHECK.md` 第 8 项**紧挨着**结论 1 补一句封存侧的话（许可 ≠ 安全：
缓存内容含封存局源码，取用必须先过白名单）；(2) 写一条**可执行的护栏**——任何拉取
`environment_files/` 或调用 `make list-games`/`make play-local`/swarms 的路径，必须
先按 `piles.json` 过滤到开发堆 4 局，缺省全量即拒绝并报错（fail-closed，不是文档提醒）；
(3) 把这条加进 `CLAUDE.md` 的封存纪律一节——它是全仓读者都要知道的。