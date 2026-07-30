priority: 2
cell: A2
territory: ablation-arm
deps: none

# A15-ablation-calibration-uncommitted · 消融校准做完了，但只存在于一个 worktree 里

审计（2026-07-29）在驳斥 A2 的下调时用到了这份产物：
`.worktrees/a4b-ablation-calibrate/ablation-arm/artifacts/calibration.json`
——它把 P-1 / P-2 / P-4 三条逐条 settled（19 行对照表、held-out 精度、
三次 Lean 空公理集），**但从未提交**。

也就是说：审计员能看见它、论文看不见它，而**下一次清理 worktree 它就没了**。
本仓有 106 个 worktree，这种「只存在于某个检出里的成果」不会只有这一份。

做三件：

1. **把这份校准产物落到 `ablation-arm/` 主线上**（连同能重跑它的脚本与 MANIFEST），
   并核对它引用的三条结论在当前 master 上是否仍然成立——
   **过期的对照表比没有对照表更坏**。
2. **扫一遍全部 worktree**，找出所有「有产物但对应分支未合并、且产物未入库」的目录，
   列清单：路径、里面有什么、对应分支、是否有未提交改动。
   **这份清单本身就是交付物**——监控要拿它决定哪些 worktree 可以清理。
3. 结论写进 `ablation-arm/STATUS.md` 与 `PARTNER_SYNC.md`。

零 API、零封存堆接触。**注意：只读地遍历 worktree，不要删除任何一个**——
删 worktree 是不可逆的，里面可能有没提交的活。
