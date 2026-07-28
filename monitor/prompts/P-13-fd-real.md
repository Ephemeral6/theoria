# P-13 · engine-rig：Fast Downward 真接入，三档阶梯补全

基准文件是 `Theoria.md`（1.10b 规划一行：「不自研，白捡二十五年规划工程」；三档阶梯）。开工仪式：读 `CLAUDE.md`、PARTNER_SYNC 最后十段、`engine-rig/STATUS.md` 的 FD 尝试日志、`cold-start-a0` 里 Fast Downward blocker 的记录（commit b1a1feb，只读），跑 engine-rig 测试，绿了开工。
分支制：`agent/p13-fd-real` + 独立 worktree；push 分支不碰 master。
领地：`engine-rig/`。其余只读；PARTNER_SYNC 只追加。

目标：把 `fd_adapter` 的 backend 从 BFS 桩换成真 Fast Downward，调用方零改动（接口 `solve(domain, problem)` 不变，桩保留为 fallback）。

1. **获取 FD**：源码编译（Windows：CMake + VS Build Tools 或 MSYS2，官方支持）或可信预编译。下载来源 URL + 版本 + 哈希入 runs/ 的 MANIFEST——工具链也要溯源。装到领地内或用户目录，`FAST_DOWNWARD` 环境变量接入（现有查找逻辑已支持），不进仓库。
2. **三档阶梯打通**：BFS 桩（保留）→ A* + LM-cut/iPDB（最优档）→ LAMA（满意档）。skip 掉的那条 FD 专用测试自动生效，再补：三档在同一 problem 上答案一致性（最优档间）与档位选择逻辑。
3. **实测红利**：M9 的死锁剪枝在真 FD 上重跑节点数对比；A0/A2 的 domain.pddl 喂 FD 求解与桩对拍。
4. 若 Windows 编译死磕两小时仍不通：如实记 blocker（试了什么、卡在哪、可行替代），不许用桩冒充 FD——诚实的失败报告也是合格交付。

技巧：编译与适配并行两个 subagent；对拍用 fuzz 循环（随机小 problem 桩 vs FD 逐一比对最优长度）。

收工仪式：runs/ 归档（prompt_id: P-13）；STATUS/DECISIONS 记一笔；PARTNER_SYNC 追加；push 分支。全程自主，不停下来问。
