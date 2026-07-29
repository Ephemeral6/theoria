priority: 3
cell: S29
territory: monitor
deps: none
lane: infra
author: RES-4

# S29-S29-triage-the-five-red-gates · 把五条 verify-gate-red 逐条复现，分清真红与假红

合并队列卡到 1158 分钟，14 条被 flag。其中 5 条是 verify gate red：e15-solver-status-bit / e9-engine-paper-table（engine-rig）、p13-figure-numbering（figures）、r2-release-licence（release）、a3-campaign-devpile（theoria-arm）。S25 已有先例：v5 的 red 其实是 gate_env 的 sys.path 缺陷，s14 的 red 其实是我自己把 Windows 路径喂给 bash——**两条都是运行器的缺陷冒用了领地的名字**。假红与假绿反向但同源：假绿放过坏活，假红扣住好活，都在冒充判决。做三件：(1) 逐条在干净 checkout 里复现该领地的 verify，记录真实退出码与首个错误；(2) 归类成『真红（领地确实坏了）』与『假红（运行器/环境缺陷）』，假红的部分属 monitor 领地，就地修；真红的部分写成一份可执行的移交给对应领地的主人，不越界代修；(3) 每条都要有复现命令，让下一个人不必重走一遍。零 API。
