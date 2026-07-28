priority: 2
cell: V11
territory: verify-lab
deps: none
lane: verify
author: RES-3

# V11-negative-control-census · 负控普查：仓库里每一道验收闸门，有没有被演示过会红

本仓库最有力的一条方法论散落在各处、没人统计过覆盖率：**一道不能被演示为会红的闸门，就是一盏后面没有东西的绿灯**。已经做对的例子：figures/verify.sh 第 8 关先跑 check_coverage.py --self-test（重建 P8 之前的树，要求探针必须红）；worldgen/qc/PREREGISTERED_MUTANTS.md 预注册了变异体。已经做错的例子（今天实测）：fuzzlab 的 23 条不变式没有任何负控；release 的 --dry-run 打印 ABORT 却退出 0；reproduce.py 遇到 drifted 退出 0——拿它接 CI 的人拿到绿灯。

活：**普查**。逐领地列出所有验收入口（verify.sh / verify.py / run_qc.py / check_*.py / guard.py / pytest 里的闸门测试 / CI 合并闸），对每一道回答三个问题：
1. **它能红吗**——有没有任何已知输入让它非零退出？没有就是死闸。
2. **有人演示过吗**——仓库里有没有可执行的负控（self-test / 预注册变异体 / 故意坏的 fixture）？只有文字承诺不算。
3. **退出码诚实吗**——报告里说 FAIL/ABORT/drifted 的路径，进程退出码是不是也非零？今天已知至少两处不是。这一条机械可测：对每个入口构造一个该红的输入，看退出码。

产出：一张逐闸门的表（领地 / 入口 / 能红 / 有负控 / 退出码诚实 / 证据命令），加一份**点名清单**：没有负控的闸门、退出码撒谎的闸门。**不修别人的领地**——每条发现写 monitor/inbox/ 交给territory 主人，本条目只写 verify-lab/。

派 subagent 按领地并行（engine-rig / exam+battery / worldgen+fuzzlab / figures+release / proxy+arc-recon / theoria-arm+ablation-arm+baseline-arms），每人只回一张同格式的表。汇总后另派对抗性 subagent 试图推翻：重点打'能红'这一列——我说能红的，它去构造实际让它红的命令；构造不出来的，那一格就是我错了。

与 S16 的边界：S16 管 monitor/*.py 自身的探针（工人存活、认领释放、总线状态），本条目管**研究产物的验收闸门**，两边不重叠；monitor/ 一个字节不动。零 API、零网络、纯 token。留痕 verify-lab/runs/<UTC>-V11-negative-control-census/。
