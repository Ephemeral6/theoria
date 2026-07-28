# P-4 · engine-rig：补齐八道工序，探针接上规划器

基准文件是 `Theoria.md`；先读它 1.9 与 1.10(b) 引擎表，再读 `CLAUDE.md`、`engine-rig/DECISIONS.md`、`STATUS.md`，以及需求方的记录（只读）：`cold-start-a0/THEORIZE_LOG.md` P-01..P-03 与 `cold-start-a0/prime/A0P_REPORT.md`。
领地：`engine-rig/`。其余只读；`PARTNER_SYNC.md` 只追加；提交只 add 自己领地。

目标三件，新引擎与现有六个同家族（同候选流出口、同确定性纪律、同 fixture 验证法）：

1. **deadlock_carver**——条件化迷你不可解定理（带证书），同一条定理既进候选流又作剪枝接进 fd_adapter，节点数下降给前后对比数字；1.9 的「箱入死角」例子真产出来。
2. **ic3_pdr**——归纳不变量兜底（inv_init/inv_closed/goal_break 三件套，可被独立检查器复核）；验收线：peg 0111，LP 无线性证书的那个配置。
3. **探针接规划器**——hypothetical 分裂配置构造成 PDDL problem 喂 fd_adapter：SAT 则探针升格为带到达计划的可执行探针，UNSAT 给 unreachable 裁决。

技巧要求：三件在**三个并行 subagent** 里各自开发自测（各占 `engines/` 下自己的子目录，天然不冲突），主线只做最后的集成、`tools.run_all` 纳入与全套回归；每个新引擎配一个「证书怀疑者」subagent，只拿证书与独立检查器、不看实现，试图构造让证书通过而结论为假的反例；测试挂后台循环跑到全绿，回归（现有测试）一条不许掉。

红线：候选 status 恒为 `"candidate"`；确定性字节稳定；全程离线；不碰其他轨道目录。
全程自主，不停下来问。完成即提交（DECISIONS/STATUS 各记一笔）+ PARTNER_SYNC 追加一段。
