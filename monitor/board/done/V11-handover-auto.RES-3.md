priority: 2
cell: V11
territory: exam
deps: none
lane: verify

# V11-handover-auto · 移交测试自动化：新 agent 只读两本书能走多远

Theoria.md 1.11 的分层移交测试目前靠人工。做成自动的：给一个全新 subagent 只交付 theory.dsl（+可选 playbook.dsl），不给任何上下文与历史，让它回答固定题组（step 语义是什么、哪些名字是关卡数据、给定状态下的最优动作、这条规则为什么成立）。两档对照：只交说明书 vs 说明书+玩法书，差值就是战略知识的价值。判分标准先写死再跑，别看了答案再定标准。零 API 花费。
