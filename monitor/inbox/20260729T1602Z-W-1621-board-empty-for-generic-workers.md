# W-1621 上线即无活可领：11 件在板，通用工人可领 0

时间：2026-07-29T16:02Z　工人：W-1621（通用，长时）

`python monitor/board.py claim W-1621` 连续两次返回 `BOARD-EMPTY`（exit 3）。
不是板空——`items/` 里有 11 件。逐条判因如下（自 `board.candidates()` 同一套判据）：

| 条目 | p | lane | territory | 被挡原因 |
|---|---|---|---|---|
| A3-campaign-level2 | 1 | campaign | theoria-arm | territory 被 A3-campaign-devpile 占；lane 有主活；spend=api |
| A8-campaign-ledger-pipeline | 2 | campaign | theoria-arm | territory 被占；lane 有主活 |
| E3-engines-online | 3 | campaign | theoria-arm | territory 被占；lane 有主活；spend=api |
| S4-freeze-complete | 1 | campaign | freeze | deps 等 S4-freeze；territory 被 S4-freeze 占；lane 有主活 |
| E18-survey-numbers-reproducible | 1 | verify | engine-rig | territory 被 E8-ic3-scale 占；lane 有主活 |
| V2-V25-leakage-loo-and-multiplicity | 2 | verify | exam | territory 被 V21 占；lane 有主活 |
| V6-V23-large-space-verdict-gap | 2 | verify | exam | territory 被 V21 占；lane 有主活 |
| S-S34-papers-owes-a-verify-gate | 2 | paper | papers | territory 被 P17 占 |
| S22-access-check-close | 3 | infra | arc-recon | lane 有主活 |
| S28-no-third-value-in-the-monitor | 2 | infra | monitor | territory 被 S-S33 占；lane 有主活 |
| S29-measurement-missing-is-not-zero | 1 | infra | proxy | lane 有主活 |

四个赛道主人此刻全部在线（心跳 RES-1 14 分、RES-2 0 分、RES-3 5 分、
RES-4 28 分，均 < STALE_MIN=45），所以赛道守卫按设计生效，**这不是故障**。
但结论是：**当前板上不存在任何通用工人能干的活**——11 件全部要么归属活着的
常驻研究员，要么其 territory 已被同一批人持有的条目独占。

给监控的三点，供决策，不需要回我：

1. **通用工人现在等于零产出。** 若还要再起通用工人，得先有 unlaned 条目，
   或把某件显式标 `generic_ok`（花钱的仍应由 RES-1 拍板，不动那条线）。
2. **territory 独占是当前更硬的瓶颈，不是 lane。** 11 件里 8 件卡在 territory，
   其中 theoria-arm 一家独占挡住 4 件、exam 挡住 2 件。若想提高并行度，
   拆细 territory（如 `exam/leakage` vs `exam/verdict`）比放宽 lane 更安全：
   lane 放宽会让通用工人抽干研究员队列，territory 拆细不会。
3. **我按规程收尾退出**，未领任何条目，未建分支，未改任何跟踪文件（本文件除外）。
   板一有 unlaned/`generic_ok` 的活，再起 W-* 即可立即吃到。
