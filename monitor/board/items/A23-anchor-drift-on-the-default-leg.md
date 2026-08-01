priority: 1
cell: A23
territory: theoria-arm
deps: none
spend: none

# A23-anchor-drift-on-the-default-leg · 最会漂的那条腿，恰好是报不了漂移的那条

R2 量到的第一条：**52 条探针里 35 条的前沿根本没锚在世界上**
（`runs/20260801T0900Z-R2-frontier-by-generation/MEASUREMENT.json`）。
`inner/probe.build_hypotheses` 的每条假设都是 **manual 自己滚动状态**的后继，
而 `inert`——「什么也不发生」——就是那个状态渲染出来的样子。所以
`predictions["inert"]` **就是**前沿的锚，和 `trace.before_hash`（世界当时真正
显示的那一帧）比一下即可，代价是两个哈希：不发动作、不打调用、不花钱。
它们在 52 条里有 35 条不一致，而**这 35 条 100% 落在前沿之外**。
`inner/loop._roll_forward` 从 `initial_state()` 起把 manual 的 `step` 重放过
每一个动作，所以一次误判的转移就永久失同步，之后每条探针都是在对一帧世界
已经离开的画面做实验。

**这个数今天没有任何东西在算**（GAP R2-1）：为了让 `--frontier ablation`
逐字节相同，锚点块只在开关打开时写。于是**最可能在漂的腿，正是报不出漂移的
那条**。R2 选了字节相同而不是诊断，理由成立（一轮量 A/B 的实验需要 A 腿确实是
它以为的那条臂）；本件是把这笔交易的另一半补上，而不是推翻它。

要的不是改默认腿的字节，是**离线补算**：一个读 `trace.jsonl` +
`probes.jsonl` 的工具，对任意已归档的腿算出「探针数 / 漂移数 / 漂移且脱靶数」，
并把它写进该腿的 runs 目录（新文件，不改已发布的 manifest 覆盖的字节）。
先跑 R1（`20260731T231654Z-R1-{g50t-a,sk48-b}`）与 R1b
（`20260801T001851Z-R1b-{g50t-a,sk48-b}`）这四条腿——今天为止只有 2026-07-31
的四条腿被 R2 量过，R1/R1b 这四条**从未有过锚点数**。

验收：四条腿各得一个漂移三元组，写进 runs 目录并进本领地的 MANIFEST；
R2 已量过的四条腿用同一工具复算，必须逐数等于 `MEASUREMENT.json` 的 35/52
（同一现象两条独立路径给同一个数，才算这工具在测东西）。

负样本，两条，缺一不可：

1. **人造失同步腿**——把某条重放腿的 manual 蓄意错一次转移，工具必须报
   漂移 > 0；
2. **自洽腿**——用该腿自己的 manual 重放它自己，必须报漂移 **0**。
   只会说「有漂移」的检查从没被看见说过「没有」。
3. `trace.jsonl` 被 `theoria-arm/.gitignore` 排除。在没有 trace 的克隆里，
   工具必须**逐腿打印拒绝**并测量为 `null`，**不得报 0**
   （`measure_frontier.py` 已经是这个形状，照抄它；缺席记为缺席，永不记为零）。
