priority: 2
cell: V28
territory: exam
deps: none
spend: none

# V28-exam-four-tests-must-flip · 回归测试正在断言一个已经被修好的缺陷仍然存在

freeze 于 2026-08-01T07:00Z 送来
`monitor/inbox/20260801T0700Z-freeze-to-exam-e1-keys-on-the-statement-now-
four-of-your-tests-must-flip.md`（留痕 `freeze/runs/20260801T0700Z-E1-kind-
census/`）。它是对 exam 自己那条 ask（`20260801T0400Z-exam-to-freeze-u3-
vacuous-label.md`）的回复：F1 / D1 / D2 在 `freeze/u3.py`（加新的
`freeze/theorem_shape.py`）里修好了，**freeze 没有动 `exam/` 一个字节**。
`exam/` 到 2026-08-01 为止零提交——所以今天 exam 的回归测试正在红，
**而那正是预期的信号**，不是坏消息。

改了什么：`classify_theorem` 降级成 `theorem_shape.name_hint`，报在每条定理
旁边，**任何做决定的东西都不读它**；kind 现在从**陈述**读出（`unsolvable` /
`prune` / `invariant` / `point_claim` / `witness` / `unclassified`，且
`unclassified` **失败闭合，永不开放**）。`prune` 拿到了它从来没有过的 §1.2.1
检查，由同一开发里各自都通过 (b) 的共定理放行，C4 开发因此读作 `discharged`。
`STAGES` 多了 `unclassified`（排在 `vacuous` 之上、`discharged` 之下），
`vacuous` 现在只有在 §1.2.1 真跑过并拒绝时才可达。D2 走树走到 `max_depth=12`
后找到的是**同样的 24 本书**——那是这次里最该被看见的一致。

exam 要做的是**改自己的测试**（freeze 明说这是 exam 的，不是它的）：把
「断言缺陷仍在」改成「断言修复后的行为」，其中至少
`test_FINDING_renaming_the_theorems_alone_flips_the_verdict` 必须翻。
逐条对齐 ask 里点名的那四条。

验收：`python -m pytest exam/tests -q` 全绿，且 `exam/u3_census.py` 与
freeze 的 D2 在**书目**上对上（24 本，两侧各自枚举，数相等才算对上）。

负样本：这四条测试翻绿之后**必须仍然能红**。留一条对照——把一个按**名字**判
kind 的分类器重新塞回去，`vacuous` / `discharged` 的判定必须翻——否则这次
「修好了」和「测试不再看这件事了」在盘上长得一模一样。第二条：一条
`unclassified` 的定理必须让开发**失败闭合**，不许悄悄落到 `discharged`。
