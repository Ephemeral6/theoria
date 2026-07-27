# T-02 · 【已作废 2026-07-28】A0 收尾已由另一会话完成

本工单起草时 A0 停在「前半环通、certify/plan 未落盘」；起草后数小时内另一
会话已完成全部内容并提交：certify 双层绿（276 帧重放 0 异常、Lean 无
sorry）、plan SAT 12 步、执行赢、no-button 变体 UNSAT→Lean 证书、
`A0_REPORT.md` 对真值 233/236，且经过了独立复核（`run_all.py` 全量重生成）。

**不要执行本工单。** 若要在 A0 之上继续，两个真实的残留物：

1. **表达力台账独立成文**：A0 的 E-01..E-05（尤其 E-03 帧公理不在 DSL 里）
   目前埋在 `cold-start-a0/THEORIZE_LOG.md`。Theoria.md 1.8 诚实条款要求它是
   一份公开台账。把它提升为顶层被跟踪文件 `EXPRESSIVITY.md`（或
   `CONTRACTS/expressivity_ledger.md`，注意该目录的所有权规则），逐条注明
   哪局哪条规则逼的 —— 这是 T-06（语法修订）的输入。
2. **A0 发现回灌基准文件**：O-04（约束 5 vs 约束 2 的准入冲突）需要
   Theoria.md 作者裁决记录（见 monitor spec 的 F-04）。

这两件都小，可并进 T-06 的会话做。
