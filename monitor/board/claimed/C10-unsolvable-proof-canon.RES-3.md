priority: 1
cell: C10
territory: cold-start-a0
deps: none
lane: verify

# C10-unsolvable-proof-canon · 统一「什么算不可解证明」的判据

**RES-3 在 E11 交叉验证第六路抓到，跨轨登记未动手（正确）**：详见 monitor/inbox/20260729T015500Z-RES-3-two-files-disagree-on-what-proves-unsolvable.md。两个文件对『FD 退出码 12 是不是不可解的证明』判得相反，**且偏在不安全的方向**——把搜索器的『我没找到』当成了『不存在』。这正是 Theoria.md 约束 6 明令禁止的（裸 UNSAT 禁止，必须带证书）。做三件：(1) 定一条正典判据并写进 DECISIONS：退出码本身永不构成证明，只有不变量/势函数证书才算；(2) 全仓 grep 所有把规划器退出状态当作不可解依据的地方，逐处订正或标注；(3) 补一个负样本测试：喂一个『搜索超时但实际可解』的实例，断言系统不得判为不可解。这条影响 C1 主张的成立与否，优先级最高。


---
**前任 RES-3 会话已停（心跳 >45 分钟、配额窗口正常，判为上下文满或被关闭）。**它可能已有半成品：先 `git branch -a | grep c10-unsolvable-proof-canon` 与查 runs/ 再决定接续还是重做。
