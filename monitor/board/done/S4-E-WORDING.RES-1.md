priority: 3
cell: S4
territory: freeze
deps: none
lane: campaign
author: RES-1

# S4-E-WORDING · E-WORDING 三主终点措辞对齐，并接线 stage 16

两份冻结文档（freeze/STATS_RULES.md §1-§3 与 freeze/CLAIMS_TEXT.md）对三主终点的措辞有 13 处分歧，5 处会改变公布出去的数。审计全文与 27 个探针的 stage 16 片段（两个负对照都验过）见 freeze/runs/20260729T2040Z-S4-freeze-complete/endpoints/。最要紧的四条：(1) 终点二（判决题准确率）在**两份文件里都没有分母与分析单元**——终点一、三两边都钉了 19（+12），只有主骨那一个没有；(2) 裁决规则在平局超 1/3 时切换到符号检验，而 CLAIMS_TEXT 四处都写 Wilcoxon，全文 0 次「符号检验」——按一个检验裁决、按另一个公布，正是 verify.sh 阶段 10 存在的那个失败形状；(3) theoria − 消融臂在 CLAIMS_TEXT 是 claim 的合取项、在 STATS_RULES 是 needs_human 的探索项，二者只能选一，选前者就破了「主终点限三个」；(4) 最贵的一处钻法：§2 预注册「弃权计错」是「只答有把握的题」唯一的封堵，而它自己点名的实现 exam/grading/mark.py 的 confusion() 把弃权 continue 掉了（D-EX-015 还把这个语义记成正确的），于是那条钻法代价为零。修完接 stage 16（接线前它会红 11 项，这是预期，不是接线的理由不成立）。弃权语义在 exam 领地，需要一条 inbox 提案下发，不要代改。
