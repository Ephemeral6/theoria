priority: 2
cell: S13
territory: monitor
deps: none
lane: campaign

# S13-verify-gate-enforced · 把收工闸门变成合并门的机器检查

根因：工单里「写一个 verify 脚本」是自觉条款，于是十个领地只有三个真有闸门（exam/worldgen/proxy），而 A4a 声称有 ablation-arm/verify.sh 却没造——审计员第六维度抓到的正是这类「要求引用了不存在的东西」。做三件：(1) ci_merge 合并某领地的分支前，若该领地存在 verify.sh/verify.py 就必须跑它并要求绿，缺失则在 merge.log 显式打印「该领地无闸门，未设门」——让敞开可见而不是默认；(2) 给缺闸门的领地各补一个最小闸门（测试 + 一次实跑 + 产物字段自检三段式，参考刚补的 ablation-arm/verify.sh）；(3) 工单模板里「写 verify」改为「若领地无闸门则必须新建」，并让 verify_gates 探针区分「声称有却没有」与「本来就没有」。注意闸门自己不能弄脏工作区：产物写 mktemp -d（ablation-arm 那个第一版就because往 artifacts/ 落文件把只读测试自己弄红了）。
