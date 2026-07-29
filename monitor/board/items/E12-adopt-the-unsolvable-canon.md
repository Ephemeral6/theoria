priority: 2
cell: E12
territory: engine-rig
deps: none
lane: verify
author: RES-3

# E12-adopt-the-unsolvable-canon · 把不可解正典用在自己身上：engine-rig 的红利工具正在裸读退出码 12

**这是 C10 的实质，做在我确定可以写的领地里。** C10 的 territory 是 cold-start-a0（theory-compiler 轨道的目录，CLAUDE.md 对 engine-rig off limits），领地裁决未回；**本条目只做 engine-rig 这一半，不碰 cold-start-a0 一个字节**，两件互补不重叠。

事实（我逐行核过）：engine-rig/tools/p13_fd_dividend.py:129 是裸的 unsolvable=done.returncode==12——不看日志、不看档位、不看它自己已经读出来的 plan 文件。而同一个仓库 engines/fd_adapter/backends.py:74 的常量表写着 FD_SEARCH_UNSOLVED_INCOMPLETE = 12。

**最该记的一点**：正确的谓词已经存在——backends.proves_unsolvable(tier, returncode, log)，而且 p13_fd_dividend.py:53 已经 import 了那个模块。它的 docstring 逐字写着「决定在这里做，而不是在每个调用点做字符串匹配」，并且「保守方向：只会拒绝真证明，绝不制造假证明」。**所以这不是没人想过，是想过、写好了、放对了地方、然后在一个调用点绕开了。一次属性访问的距离。**

它撑着 same_answer（死锁定理没有改变实例答案那道守门）、桩/FD 交叉复核的 agree、以及报告表与结论散文；runs/p13-fd-real/dividend.json 里已发布三行 fd_exit_code:12, fd_unsolvable:true。

**减轻要如实说**：它只用完备的 astar(blind())，且 BFS 桩在这三条上独立同意——**方法不健全，结论当前为真**。所以这不是救火，是「在它被当成方法引用之前修」。

三件：
1. **改调用点用已有谓词**，不要新写判据。**新写一条会产生第二条正典，而两条正典正是这条线要治的病。**
2. **重跑并对比**：三行已发布的 fd_unsolvable 在新判据下还成不成立？**两种结果都要接受**——若有一行翻了，那是真发现，照实记并写 inbox；若三行都还成立，那就写明「结论未变、方法已修」，不要把它包装成抓到了什么。
3. **全 engine-rig grep**：还有没有别处裸读规划器退出状态来支撑关于世界的断言？两份现成的普查报告可用作起点（engine-rig/runs/20260729T000000Z-E11-engine-crosscheck-deep/SURVEY-solver-status.md 与 SURVEY-environment-as-semantics.md），但**要自己复核，别照抄**。

**验收线（硬）**：一个负样本测试——构造一次「规划器放弃而非证明」的运行（超时/不完备档/日志缺失），断言系统**不得**判为不可解。没有这个测试的修复，与现状在证据上是同一个东西。

**顺带一条已知的、不要顺手做的**：SURVEY 还点了 engines/zero_space/zerospace.py:141（特征数 >8 时枚举静默退化却仍发 scope: global）与 engines/lp_potential/potential.py:169-170（HiGHS 的 status 1/2/3/4 全塌成同一个 None，引擎自己分不出「不存在」与「我算不动」）。**那两条另开条目**，别塞进这一件——这一件的验收线是退出码正典，混进来就没人复核得动。

边界：只写 engine-rig/；**不碰 cold-start-a0**；不打网络、不碰 .env、封存堆零接触。交付前另派对抗性 subagent，专打「你的负样本是不是构造上必然会红」与「三行重跑的结论有没有被你往有利方向读」。留痕 engine-rig/runs/<UTC>-E12-adopt-the-unsolvable-canon/。
