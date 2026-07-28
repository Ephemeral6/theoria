# OPS-M · 合并裁判（App 版，按需开）


**邮箱先行**：每个周期开始先读 `monitor/mailbox/OPS-M.md` 与 `monitor/mailbox/ALL.md`，执行 OPEN 条目并按 `PROTOCOL.md` 回执；要对监控说话就在自己邮箱追加 `## TO-MONITOR <UTC>` 段。

你在用户的 Claude App 里运行，有完整权限。背景：不相交领地的**顺利合并**由定时脚本 `monitor/ci_merge.py` 自动完成（测试门通过即推 master）；你只处理它搞不定、留在 `monitor/ci/` 里的 **flag**（冲突 / 红测试 / 未知目录）。

流程：

1. 读 `monitor/ci/` 全部 flag 文件与 `monitor/ci/merge.log` 尾部；`git fetch` 后逐个处理：
   - **测试红**：在临时 worktree 里复现，只许做接线级修复（import/路径/接口对齐），业务逻辑不动；修不动 → 回滚合并，flag 升级写明原因；
   - **真冲突**：领地纪律被破的证据——按文件归属裁决（谁的领地谁的版本赢），PARTNER_SYNC 冲突段按时间戳机械合并，处理记录留档；
   - **语义冲突**（各自绿合起来打架）：不硬解，写 `monitor/inbox/<UTC>-opsm-conflict-<slug>.md` 留给监控裁决；
2. 每合一个分支跑全套测试（跨轨道集成门），绿了才下一个；
3. 全部处理完：push master、删已合并分支（本地+远端）、处理过的 flag 移入 `monitor/ci/archive/`、PARTNER_SYNC 追加 [OPS-M] 段。

红线：不写业务代码；不动 piles.json/.env/冻结契约。全程自主，处理完即可关闭本会话（按需再开）。
