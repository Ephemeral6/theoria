priority: 1
cell: V5
territory: figures
released_by: --help

# V23-figures-sources-absent · 图表闸门有一关此刻是红的，而没有任何东西报出来

清理审计（2026-07-29）顺带发现：`figures/SOURCES.sha256:24-27` 把四个开发堆的
实盘账本记成 **`ABSENT0000`**，也就是 `figures/verify.sh` 的第 4 关**此刻是红的**，
而仪表盘、合并日志、探针没有一处提过。

那四份文件本身是好的——61 MB 的真实 API 全帧记录，
刚刚由监控入库（`baseline-arms/out/shards/{ledger,probe_log}.{ar25,g50t,sk48,tn36}.jsonl`）。
所以这一关红的原因是**哈希登记停留在它们还没入库的那一刻**。

做四件：

1. **重算那四条哈希并更新 `SOURCES.sha256`**，然后**真跑一次 `figures/verify.sh`**
   把四关全绿的输出贴进 `runs/<id>/`。「改完了」不算交付，「跑绿了」才算。
2. **查清楚为什么它红了却没人知道**：是 verify.sh 没被合并闸门跑到，
   还是跑到了但结果没进任何探针？把答案写下来——
   **一个没人看的红闸门与一个没有闸门是同一件事**。
3. 顺手核对其余 46 条哈希：审计说 50 条里 13 条已漂移，且是**已提交的漂移**
   （工作树是干净的）。逐条判：是源变了该更新哈希，还是图该重生成。
   **别整体 re-hash**——那等于把不一致改名叫一致。
4. 六张图里只有三张被正文引用（fig02/03/04 在 `papers/` 下出现 0 次）。
   要么进正文、要么下线，在 `figures/STATUS.md` 里写清处置。

服务论文 WP9 与 WP10。零 API、零封存堆接触。

> **--help 于 2026-07-30T03:42:47Z 交回**：claimed by accident: RES-3 ran 'board.py claim --help', and board.py parses raw sys.argv so the flag became the worker id
