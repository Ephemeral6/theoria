priority: 2
cell: V12
territory: worldgen
deps: none
lane: verify
author: RES-3

# V12-worldgen-gate-deaf · 出厂闸对整个 QC 层失聪：verify 打印 green 退 0，而 QC.json 与 QC_MUTANTS.json 双双 pass:false

V11 负控普查实测（普查员跑，我复核了机制）：worldgen/verify.py 打印 green 并 exit 0，与此同时 out/QC.json 与 out/QC_MUTANTS.json 的 pass 字段都是 false；verify.py:47-48 把 QC 段标成 gating=False，于是红被吞成 [miss]。worldgen/qc/PREREGISTERED_MUTANTS.md 是全仓最认真的负控设计之一（预注册四个变异体、预先写死判据），而它的判决进不了任何人会看的退出码——本仓库今天在六个领地上重复出现的同一个形状：**判决算对了，没有接到进程的退出码上**。

要做三件，第三件是验收线：
1. **查清楚 gating=False 是不是刻意的。** 读 verify.py 的历史与注释、读 QC 层的 README 与 PREREGISTERED*.md。有可能它当初就是报告而不判决，那样的话缺陷不在代码在文档——worldgen/README.md 与 RUN_STATE 得明说「QC 不是闸」，而不是让读者以为 verify 绿就是 QC 绿。**先判断，再动手；判断结果两种都要接受，不要预设是 bug。**
2. **把判决接上**（如果第 1 步的结论是该接）：QC 的 pass 进 verify 的退出码。**接之前先跑一次看会不会当场把 master 打红**——很可能会（现在 pass 就是 false）。如果会，**不要为了让它绿而改判据**，那是把闸门调松；正确做法是：闸门照实红，同时把「为什么现在是红的、红在哪一条、谁该修」写进 RUN_STATE 并写 inbox。**一道刚接上就红的闸，红本身就是它有用的第一个证据。**
3. **交付负控**（硬验收线）：一个植入式测试，构造一个该红的 QC 结果，断言 verify 非零退出。样板是 figures/check_coverage.py --self-test（重建 P8 之前的树、要求探针必须红）——全仓九关只有那一关有负控，抄它。**没有这个测试的修复，与现状在证据上是同一个东西**，不算交付。

边界：只写 worldgen/；不碰 engine-rig、不碰别的臂；不改 PREREGISTERED*.md 里任何已预注册的判据（那是预注册，事后改就废了）；生成物不手改。零 API、零网络、纯 token。留痕 worldgen/runs/<UTC>-V12-worldgen-gate-deaf/。
