# S3-spend-gate · 共享花费闸门：现在就有两张在飞工单各算各的账

**这是 OPS-R 判定的最高优先在飞风险**（提案 `monitor/inbox/20260728T034833Z-OPS-R-shared-spend-gate.md`，反方复核判 SURVIVES，五条主张里唯一未被削弱的）。已发生的损害三次，其中一次不可修复：两个会话共用一份 ARC 配额与账单、各自的止损闸门看不见对方（最坏合计 $214.9），一份花过钱的方差包络被并发争用永久污染；`baseline-arms/ledger.jsonl` 一个文件混了两场战役、行内无从分辨。

开工仪式：读 `CLAUDE.md`、该提案全文、`baseline-arms/BUDGET_REPORT.md`、`baseline-arms/INCIDENTS.md` 的 INC-BA-003、`arc-recon/data/incidents.jsonl` 的 INC-011、`proxy/LEDGER_FORMAT.md`。
分支制：`agent/s3-spend-gate` + 独立 worktree；push 分支不碰 master。领地：`proxy/`（闸门本体归外壳）+ 只在 `baseline-arms/harness/ledger.py` 补 `campaign` 字段这一处跨界改动（PARTNER_SYNC 明示知会该轨道）。

目标：**花钱的闸门必须是一个函数，不是一份约定**。

1. `proxy/spend_gate.py`：单一共享账本上的原子花费登记 + 查询（跨会话、跨轨道可见）。任何一方开跑前 `reserve(campaign, usd_cap, action_cap)`，每次调用后 `record(...)`；闸门读的是**全局已花**，不是自己那份；
2. `campaign` 字段贯通：proxy 账本与 `baseline-arms/harness/ledger.py` 都必须写，历史行按可判定的规则回填（不可判定的显式标 `unknown`，不许猜）；
3. **fail-closed，无"可选"形态**（并入 OPS-R 第二份提案的裁决）：闸门缺依赖、账本不可写、reserve 未持有 → 拒绝出网并报错，绝不静默放行；
4. 并发测试：两个进程同时 reserve/record，断言总额不丢不重（原子性），断言任一方超总额即被拒；
5. 文档：`proxy/SPEND_GATE.md` 写明各方接入方式 + 为什么"约定"不够（引 INC-BA-003 的实际代价）。

前沿工具：并发正确性用 fuzz 循环压（多进程随机交错）；派对抗性 subagent 专门试图绕过闸门出网（绕过成功即验收失败）；Stop-hook 收工：`proxy/verify_spend.sh` 全绿。
留痕：`proxy/runs/<UTC>-s3/` 边跑边写。收工：RUN_STATE + MANIFEST + PARTNER_SYNC（含对 baseline-arms 的跨界知会）+ push 分支。全程自主，不停下来问。
