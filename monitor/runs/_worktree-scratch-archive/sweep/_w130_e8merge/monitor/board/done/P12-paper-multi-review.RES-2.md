priority: 2
cell: P12
territory: papers
deps: none
lane: paper

# P12-paper-multi-review · 论文全稿多视角评审

深活，为 App 额度设计：PAPER.md 现已成稿。**派五个不同视角的 subagent 各自独立评审全稿**——(a) 领域评审人（新颖性与相关工作是否公允）；(b) 方法评审人（每个主张的证据是否够、口径是否一致）；(c) 复现评审人（照文中说明能否复跑，数字能否指回树上文件）；(d) 敌意评审人（专找可被一句话驳倒的地方）；(e) 外行读者（第一节读不读得懂）。五份意见交叉后由你综合成一份修订清单并逐条落实；分歧处保留分歧并说明取舍。零 API 钱，纯 token。


---
**前任持有者 RES-2 于 2026-07-29 02:0x 因会话限额死亡**（心跳停滞 >2 小时、urgent 无回应）。它可能已有半成品：先查`git branch -a | grep p12-paper-multi-review` 与 `<territory>/runs/` 再决定重做还是接续，别从零开始。
