priority: 1
cell: S24
territory: merge
deps: none
lane: infra

# S24-merge-conflict-drain · 九条已交付分支卡在真冲突上

闸门的假红已经修完（Git Bash + UTF-8，2026-07-29），六条卡在「unknown territory」
上的分支也已裁决准入并合入。**剩下的九条是真冲突**，`monitor/ci/merge.log`
每五分钟重刷一次同样的 flag，谁也不会自己好起来。

九条（以 `monitor/ci/CONFLICT-*.md` 为准，开工时重新列一遍，别照抄这里）：
`p10-figures-into-paper`、`s14-gates-for-all`、`s5-phase1-close`、
`s8-provenance-backfill`、`s9-contract-change-protocol`、`v12-worldgen-gate-deaf`
等。做四件：

1. **按依赖序逐条解**，不要批量 `-X theirs/ours`。冲突大多来自同一批文件被两个
   agent 各改一半（`PARTNER_SYNC.md`、`monitor/spec.py`、各 `STATUS.md`），
   **append-only 文件一律两段都留**，顺序按时间戳；代码冲突要读懂两边意图再合。
2. **每解一条就跑该领地的闸门**（`python -m monitor.gates` 会告诉你是哪个），
   绿了才推。闸门现在是真会跑的，红了就是真红。
3. **解不动的如实交回**：写清楚是哪两个提交、冲突在哪几行、你判断该由谁裁决，
   放 `monitor/inbox/`。九条里解出七条并说清另外两条为什么不能解，
   比硬合九条好。
4. 顺手统计：这九条各自积压了多久、冲突文件的分布。这个分布是下一轮**分支策略**
   的输入（是否该缩短分支寿命、是否该把 `PARTNER_SYNC.md` 改成一人一文件），
   写进 `runs/<id>/` 并在 inbox 提一句结论。

服务论文 WP2（多 agent 协作纪律的证据）与整条交付管线的吞吐。
零 API、零封存堆接触。
