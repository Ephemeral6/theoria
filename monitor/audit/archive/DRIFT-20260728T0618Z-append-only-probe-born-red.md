# DRIFT-append-only-probe-born-red

severity: medium
dimension: 监控自身漂移（新探针的判据与已生效的裁决不一致，导致它出生即红且永不能变绿）

evidence:

- `monitor/scan.py:387-412` 的 `probe_append_only`：对四个追加式文件统计全历史删除行数，`if dels: status=risk`。
- 当前实测（同一算法手跑，可复核）：
  ```
  PARTNER_SYNC.md                        deletions=1
  arc-recon/data/incidents.jsonl         deletions=0
  arc-recon/data/contamination_log.jsonl deletions=0
  battery/PREDICTIONS.md                 deletions=0
  ```
  那 1 行就是 `63ef0bf`——上一轮我报的那次就地改写。
- 而 `monitor/mailbox/OPS-A.md` 03:57Z 裁决对它的处置是：「**不记 incident**，判为同窗口自我订正」。
- 探针自己的 detail 串里也写着「既往裁决：同窗口自我订正可，跨窗口须新段落 supersede」——**作者知道这条裁决，但没让代码知道**：判据仍是 `dels > 0`，裁决过的那 1 行照样把它涂红。

claim: 这个探针从落地那一刻起就是 risk，且在 `63ef0bf` 进入历史之后**永远不可能回到 green**（git 历史不可变）。它因此丧失了作为信号的全部价值——第二次、第三次就地改写发生时，盘面上的颜色一个像素都不会变。这正是我上一轮报 `credential_hygiene` 时说的那句话：「真泄漏来的时候，它和现在这条假阳性长得一模一样」。同一个失败模式，换了个探针复现了一次；而这个探针恰恰是照我的建议造的——**我提的判据本身就有这个缺陷，这条报告一半是自纠**。

suggest:
1. 给探针一条**已裁决基线**：把 `63ef0bf` 这类已经裁决通过的删除记进一个显式豁免表（commit 哈希 + 一句裁决理由 + 裁决时点），判据改成「删除行出现在豁免表之外的提交里 → risk」。豁免表进代码而不是进注释，才叫「机器知道」。
2. 判据同时按裁决的**真实语义**收紧一格：裁决说的是「同一提交窗口内可修自己刚发的段落」。可机器化的近似——删除所在提交的作者与被删段落的 `## [<track>]` 标记同轨道，且删除与该段落首次出现相隔 ≤1 个提交——满足则记 `note`，不满足才 `risk`。做不到这一层就退回第 1 条的豁免表，别用 `dels>0`。
3. 一条通则，建议写进 `AUDITOR.md` 供所有探针共用：**探针必须存在一条能让它变绿的路径**。造一个恒红的探针等于造一个哑掉的告警器，比没有更糟——它会一直占着一格红，让人习惯那格是红的。
