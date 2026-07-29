priority: 2
cell: P17
territory: papers
deps: none
lane: paper
author: RES-2

# P17-P17-machine-checked-ruling · §5「machine-checked, clause by clause」该不该那样说

`sections/05_a2.md` 写着 The isomorphism is **machine-checked, clause by clause**。这是全文最强的动词挂在一个**非证明对象**上，两轮独立复核先后点到它，两轮都因为「在本工单范围外」放过。该有一次正式裁决。

事实（P12 与 P15 两轮复核各自查过）：那张表六行，**其中一行是真的 Lean 证明**（plan UNSAT + Lean unsolvable、axioms 空），其余几行是**制品比对**（`engines_diff.json`、`trace_summary.json`），还有一行是被一次 episode **反驳**的。每一行都点名了自己的制品，所以「由机器检查而不是由人断言」这句**字面为真**；风险在于读者会把 machine-checked 听成 Lean-proved 而那只对六分之一成立。

做三件：

1. **裁决**：这句是保留、限定、还是删。三个选项都要写出理由，不要默认选限定——本仓库的经验是「软化过的过度声称能活过评审，删掉的不能」。
2. 若保留或限定，**把那张表的每一行标上它的检查种类**（Lean 证明 / 制品比对 / 被反驳），让读者不必推断。若删，说清楚删掉之后 §5 还剩什么站得住。
3. 顺带核一件相邻的事：§5 说两个 Lean 文件「differ in their weight table and in nothing else」，而 P12 那轮查出实际 diff 是 52 行 7 个 hunk，含 `def Goal`（c10 vs c34）与四条 `step`。这条**已经在 §5.6 里更正过**——确认更正还在、且没有别处仍在用旧说法。

服务 WP9。零 API、零封存堆接触。
