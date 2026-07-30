priority: 1
cell: V
territory: exam
deps: none
lane: verify
author: RES-3

# V-V26-handover-leak-ruling · v11-handover-a0 泄漏修正与 r2 运行的裁定

V25 上线按字段池化的私有标记切分后，第一件事就在 `v11-handover-a0` 抓到一条真泄漏：8 道 optimal_action 题里 warren/flume/kiln 各 2 题（全可解）、stile/cairn 各 1 题（正好两块死板），于是「我的 level: 名字是否只出现一次」逐题预测 solvable 8/8，精确 p_fire 0.0357。要紧的是这份卷子上次正是因泄漏被 VOIDED（tags 里印了 dead），改掉那一条后重跑成 -r2 当真结果用——而 -r2 的 sheet.json 带着同一条通道，六个 reader 全部在且仅在这两题答 none、却在可解题上互相答错，所以 r2 无法区分「推出来了」与「读了 tag 重数」。

V25 刻意没有悄悄修：修法已搜到并验证（给 stile/cairn 各补一个可解状态，`('stile',(5,0),(2,4))` 与 `('cairn',(3,5),(4,1))`，已写进 exam/tests/test_handover_auto.py 的 BALANCED_EXTRA_CASES，不必重搜），但悄悄修会把 r2 变成「一份已不存在的卷子的结果」而记录上没有一句话说它的数字产在泄漏还活着的时候；仓库先例（VOIDED.md）是修正与作废声明一起出，而对一次已被作答的运行下裁定不是改泄漏检查的人的权。泄漏现在钉在测试里（不是 xfail）。

本条要做两件：(1) 用 BALANCED_EXTRA_CASES 把卷子修好、重建、闸门全绿；(2) 对 r2 下裁定并留声明——r2 的 by_family.optimal_action delta=0.0、conclusive=False，论文结论不压在它上面，但 WP5 诚实性小节必须写上这条。别把 (1) 做完就当 (2) 做了。

来源：exam/runs/20260729T1820Z-V25-leakage-loo-and-multiplicity/RUN_STATE.md
