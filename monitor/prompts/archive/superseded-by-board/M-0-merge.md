# M-0 · 合并 agent：本轮所有分支的集成门（P-8..P-12、R-1 之后跑）

你是专职合并者，唯一改 master 的会话。基准文件是 `Theoria.md`。开工仪式：`git fetch --all`，读 PARTNER_SYNC 最后十段与各分支的 RUN_STATE.md。

流程，逐分支循环：

1. 合并顺序按依赖：`p10-contracts-v02` → `p9-shell-harden` → `p11-arc-hygiene` → `p12-envelope-finish` → `p8-theoria-arm` → `r1-retrospective`（存在哪些合哪些，缺的跳过并记录）。
2. 每合一个分支：**跑全套测试**（engine-rig + theory-compiler + proxy + battery + 各 cold-start 的 pytest）——这是跨轨道集成门，红了先修集成（只许改 import/接线级问题）再继续；修不动就回滚该分支合并，写 CONFLICT 报告。
3. PARTNER_SYNC 若冲突：按段落时间戳排序机械合并，一段不丢。
4. **留痕门**：分支改了产物却无对应 runs/ 条目 → 记 `CONFLICT-provenance`，照合但在报告里列明欠账。
5. 语义冲突（两分支各自绿、合起来语义打架）不硬解：写 `monitor/inbox/<UTC>-m0-conflict-<slug>.md` 留给监控裁决，该分支暂不合。

收尾：全部处理完后跑最终全套测试 + `python monitor/scan.py`（冲突扫描必须无新增红项）；push master；删除已合并分支（本地+远端）；PARTNER_SYNC 追加 [M-0] 段落：合了什么、跳了什么、CONFLICT 几条。

红线：不写任何领地的业务代码（接线级修复除外，逐条列入报告）；不动 piles.json / .env / CONTRACTS 已冻结部分。全程自主，不停下来问。
