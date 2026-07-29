priority: 3
cell: E13
territory: engine-rig
deps: none
lane: verify

# E13-engine-section-numbers · 引擎章节的数字与表格定稿

论文引擎章节需要一张定稿表：六引擎 + FD 三档，每行给出「它解决什么、验证方式、实测数字、局限」。数字全部来自已有的 runs/（FD 三档定价、500 世界性质轰炸、死锁剪枝红利、IC3 在 peg 0111 的非线性证书），不新跑实验。局限那一列尤其重要——lp_potential 的不完备性、FD 的 .toolchain 不入库、探针的可达性依赖，都要如实写。写完派对抗性 subagent 逐行核对数字能否指回文件。
