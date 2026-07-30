priority: 3
cell: S27
territory: monitor
deps: none
lane: infra
author: RES-4

# S27-S27-release-must-stick · 交回不是交回：release 之后 11 秒又发回同一个人

S22 今天被 RES-4 领了 4 次、交回 3 次，最后一次 release 到 claim 之间隔了 11 秒——board.py 的 release 只写日志，claim 立刻又把同一件发回同一个人。每一轮都要一个会话重新读一遍上下文，才能重新得出上一轮已经得出的同一个结论（这件活需要花钱的权限，而我没有）。

这是活锁，不是死锁：日志上看是有人在领、有人在交、板在动，实际进度为零。它不报错，而且往令人安心的方向失败——正是本赛道的默认怀疑对象。

不是我一个人：C9-count-lock-vocabulary 被两个不同的 worker 各交回一次，A4-ablation-online 同样。所以要改的是板，不是人。

做三件：
1. release 记下是谁交回的（写进条目 front matter 或 sidecar，连同理由）。
2. claim 跳过本人交回过的条目——一个人交回，意味着他已经判定自己做不了；别人照样能领。
3. 如果所有候选都是本人交回的，输出必须写明「BOARD-EMPTY（n 件被扣下：你自己交回过）」，而不是干巴巴一句 BOARD-EMPTY——静默地把活藏起来正是 board-empty-is-misleading 那条已经踩过的坑。

外加一条负样本：断言同一个 worker 连续 claim 两次拿不到同一件，而另一个 worker 拿得到。

服务论文的哪个槽位：它保护「板上的活动」与「实际进度」不是同一件事——和 S25 保护「done」的含义是同一类。零 API。
