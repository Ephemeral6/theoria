priority: 1
cell: S3
territory: proxy
deps: none

# S3 · 共享花费闸门（最高优先：E3 已带着 $18 在没有闸门的情况下上线）

W-1521 开工时实查确认：`proxy/spend_gate.py` 不存在，`agent/s3-spend-gate` 分支停在基线，`proxy/` 14 个模块无一做跨会话花费登记。它已自建 `theoria-arm/armtools/spend_check.py` 作临时替代（在则加载、不在则记录并降级），**读它作为接口参考**，然后把真闸门补上：单一共享账本上的原子 `reserve(campaign, usd_cap, action_cap)` / `record(...)`，闸门读的是**全局已花**而非自己那份；`campaign` 字段贯通 proxy 与 `baseline-arms/harness/ledger.py`（历史行不可判定处显式标 unknown，不许猜）；**fail-closed 无"可选"形态**（缺依赖/账本不可写/未持有 reserve → 拒绝出网并报错）。并发正确性用多进程 fuzz 压（总额不丢不重、超额即拒），派对抗性 subagent 专门试图绕过（绕成即验收失败）。写 `proxy/SPEND_GATE.md` 说明各方接入方式与 INC-BA-003 的实际代价。
