priority: 3
cell: V16
territory: worldgen
deps: none
lane: verify
author: RES-3

# V16-determinism-has-no-caller · 全仓最强的那条确定性主张，没有任何测试调用过它

V14 的对抗复核在核实一个假阳时挖到：worldgen/build.py 里的 check_determinism——换 hashseed 起子进程、逐字节 diff，是本仓库**最强的那条确定性主张**——**全树零测试调用**。V11 普查也独立标过它「无负控」。而 CLAUDE.md 写着「确定性是要求不是可选」，engine-rig/.gitattributes 专门为它钉了 LF。**一条被写进项目宪章的性质，其最强的检查器从没被演示过会红。**

这条还有一层：V14 因此把 worldgen/build.py 判成「有负控」（文件级），因为同文件里别的东西有测试——**文件级的 present 掩盖了函数级的空白**。所以修好这一条，同时也是给 V14 的粒度限制提供一个真实样例。

做三件：
1. **先确认现状**：check_determinism 到底检查什么、怎么检查、它能不能红（读代码找 sys.exit / raise / 返回值怎么被消费）。**有没有可能它其实被间接调用了**（经 verify.py / run_qc / 某个 CLI）？——V14 是靠静态扫说的零调用，**你要实测确认**，扫错了就照实说，那这条工单就此结束、写清楚即可。
2. **给它一个植入式负控**：构造一个**真的不确定**的生成器（例如让某处依赖字典遍历顺序 / 时间 / 未播种的 rng），断言 check_determinism **必须**报红且进程非零退出。样板是 figures/check_coverage.py --self-test 与 V12 刚落的 worldgen/tests/test_verify_qc_gate.py（同一领地，照抄形状）。
3. **证明这个负控不空转**：照 V12 的做法，把 check_determinism 临时改弱，证明那个植入的不确定性会被放过。**没有这一步的负控，本身就是又一盏后面没有东西的绿灯。**

**不许做的**：不要为了让它更容易测而放松 check_determinism 的判据；不要改任何已提交产物；不要碰 out/（V12 已实测：跑一次 verify 会弄脏 out/qc 下十个已提交产物，那是另一条已登记的账，别在这条里顺手动它）。

边界：只写 worldgen/。零 API、零网络、封存堆零接触。留痕 worldgen/runs/<UTC>-V16-determinism-has-no-caller/。
