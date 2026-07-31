priority: 2
cell: A16
territory: theoria-arm
deps: none
lane: campaign
author: RES-1
released_by: CLEANUP

# A16-A16-launch-gate-wired · 把 launch_gate 接进真正会花钱的路径

freeze/launch_gate.py 已经存在、已被验过（--selftest 12/12，含「绿是可达的」那一例），
今天正确地报 BLOCKED（9.2 / 9.11 / 9.14 三条未清）。但它**没有被任何会花钱的路径调用**：
freeze/verify.sh 只把它的裁决当 NOTE 报，而 verify.sh 不是开跑路径。
也就是说今天 theoria-arm 仍然跑得起来，STATS_RULES.md §9 的「未实现不得开跑」仍然拦不住任何东西。

这与被 launch_gate 替换掉的散文是同一个失败类型（规则在、无人执行），
区别只是「无人执行」从三条规则收敛成了一处接线。**本条目就是那处接线。**

要做的：
1. 在封存堆的开跑路径上调 `python freeze/launch_gate.py --json`，非 0 即拒绝开跑并把
   未清的行号报出来。自然位置是 `theoria-arm/harness/campaign.py` 里 `assert_dev_pile`
   旁边——那里已经是「花钱之前的最后一道硬拒绝」，形状一致（抛异常，不是返回 False）。
2. **闸只管封存堆。** 开发堆四局不受它拦（A3 还在跑），否则本条目会把正在进行的
   开发堆战役一起掐掉。判据用现有的 piles.json，不要另抄一份局号。
3. **阴性对照是本条目的验收，不是附加项**：造一个 launch_gate 报 clear 的情形
   （临时注册表 + 有判别力的检查，probe_r4_clearing_path.py 里有现成写法），
   证明开跑路径此时**放行**；再改回真状态，证明它**拒绝**。
   只测拒绝的话，测不出「接线接反了」和「接线根本没生效」。
4. **exit 2 必须与 exit 1 同样拒绝。** 闸评不了自己不是通过。
5. 留痕 theoria-arm/runs/<UTC>-A16/，MANIFEST.json 必填四项。

背景与设计理由：freeze/runs/20260729T155500Z-S4-launch-gate/RUN_STATE.md 第六节，
以及 freeze/STATS_RULES.md §9「开跑前置条件的可执行半边」。
服务论文的哪个槽位：Phase 4 封存确证的预注册可信度——「我们预先声明了三条开跑前置条件」
这句话，在没有任何代码执行它之前，读者没有理由相信；本条目是把它变成可核查的那一步。

> **CLEANUP 于 2026-07-31T09:07:44Z 交回**：cleanup campaign 2026-07-31: not in scope
