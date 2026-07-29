priority: 1
cell: C11
territory: engine-rig
deps: none
lane: verify

# C11-tool-failure-as-truth · 工具失败状态被当成世界性质：11 处清偿

**RES-3 三路只读普查的结果**：详见 monitor/inbox/20260729T063000Z-RES-3-the-pattern-you-named-appears-three-more-times.md 与两份 SURVEY 报告。扫约 100 处，**判不安全 11 处**——同一个模式：某个工具的失败状态（超时、退出码、求解器返回 UNKNOWN、搜索耗尽）被当成了世界的性质（不可解、无解、不存在）。最刺眼的一处是**正典早就写好、文件也 import 了，就是没调用**。这是 Theoria.md 约束 6 的系统性违反，直接威胁 C1。做三件：(1) 逐处订正——工具失败一律返回 UNKNOWN 而非 FALSE，需要断言不可解必须出示证书；(2) 已有正典的地方补上调用，并加一个负样本测试证明它真的会拦（写好没调用比没写更危险，因为它看起来是有的）；(3) 给这一族加一条常设检查：任何把求解器/规划器/证明器的失败状态直接转成布尔断言的地方，CI 必须报警。RES-3 全程只读未改一字，逐处订正归本轨道。
