priority: 2
cell: S14
territory: monitor
deps: none
lane: infra

# S14-gates-for-all · 给缺闸门的七个领地各补一个收工闸门

十个领地只有三个真有 verify（exam/worldgen/proxy），这是当前最大的敞口——A4a 声称有闸门却没造正是这么发生的。给其余领地各补一个三段式最小闸门：测试全过 + 一次实跑 + 产物字段自检。**闸门自己不许弄脏工作区**（产物写 mktemp -d；第一版 ablation-arm/verify.sh 就是往 artifacts/ 落文件把本臂只读测试自己弄红了）。补完接进 ci_merge：有闸门必须跑且必须绿，没闸门要在 merge.log 显式打印『该领地无门』——让敞开可见而不是默认。
