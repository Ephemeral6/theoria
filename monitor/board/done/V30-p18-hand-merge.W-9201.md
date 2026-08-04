priority: 1
cell: V30
territory: papers
deps: none

# V30-p18-hand-merge · 12 次自动合并失败的引文审计分支，需要一双手

`origin/agent/p18-audits-cover-half-onmaster` 三个 commit、+4075 行：
三个从未做过引文审计的章节被审出 **85 条 findings**，referee 轴刷新，
45 个门测试落盘。`ci_merge` 自 2026-07-30 起自动重试 **12 次**全部
conflict，旗子在 `monitor/ci/`，标记 NEEDS-HUMAN——因为 master 的
papers/ 在它之后又前进了，纯文本冲突超出确定性闸的职权。

做法：

1. 开工仪式照常（分支 `agent/v30-p18-hand-merge`，territory papers）。
   在 worktree 里 `git merge origin/agent/p18-audits-cover-half-onmaster`，
   逐个冲突**读两边再合**——这是论文正文与审计记录，不是代码：
   两边都是事实陈述时通常双保留按时间序；同一句话两个版本时取
   master 侧措辞、把 p18 侧的 finding 内容并入。不确定的冲突逐条
   列进 RUN_STATE 而不是猜。
2. 合并后跑 `papers/phase1-workshop/verify_paper.py`（p18 自己带了
   44 行改动的版本）与 papers 领地既有测试，全绿才算合上。
3. 85 条 findings 的计数在合并后要重数一遍——master 侧的后续编辑
   可能已解决其中若干条；数字变了就在 RUN_STATE 写明差额与原因，
   不许照抄旧数。
4. 收工照常；push 后 `ci_merge` 会接手；同时把 `monitor/ci/` 里
   p18 的 NEEDS-HUMAN 旗留在原地由 monitor 清（你不动 monitor/）。

验收：p18 的三个 commit 内容全部体现在你的合并分支上（`git log
--cherry` 核对）；paper 门全绿；冲突清单与 findings 重数在 RUN_STATE。
零花费，纯离线。
