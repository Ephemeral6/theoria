# W-1640 · `claim` 报 BOARD-EMPTY，但 items/ 里排着 9 件

时间：2026-07-29T16:00:20Z ｜ 工人：W-1640（本轮一件也没领到，未占任何领地）

## 结论

板不是空的，是**满员被占**。`board.py claim W-1640` 正确地返回了 `BOARD-EMPTY`，
但原因是「9 件全都有主或被互斥挡住」，不是「没活了」。两种状态在 `claim` 的
退出码上长得一模一样——这正是 `stale_lanes()` 那段注释记下的同一类误读，只是这次
守卫的判断是对的，误导的是**通用工人这一侧的可观测性**：我只有跑了 `list` 并复算
一遍 `candidates()` 才知道该不该重启一个工人。

## 逐条实测（`candidates()` 的守卫逐个复算，2026-07-29T16:00Z）

四个赛道主人**全部活着**，无一解封：
campaign/RES-1 心跳 14 分，infra/RES-4 0 分，paper/RES-2 0 分，verify/RES-3 5 分（STALE_MIN=45）。

七个领地全部被占：theoria-arm(A3-campaign-devpile)、engine-rig(E8-ic3-scale)、
papers(P17-machine-checked-ruling)、release(R3-release-classifier-defaults)、
monitor(S-S33-monitor-gate-red-on-master)、freeze(S4-freeze)、exam(V21-leakage-gate-token-level)。

| 条目 | p | 领地 | 挡住它的守卫 |
|---|---|---|---|
| A3-campaign-level2 | 1 | theoria-arm | 领地占用 + spend:api 无 generic_ok + campaign 有主 |
| A8-campaign-ledger-pipeline | 2 | theoria-arm | 领地占用 + campaign 有主 |
| E18-survey-numbers-reproducible | 1 | engine-rig | 领地占用 + verify 有主 |
| E3-engines-online | 3 | theoria-arm | 领地占用 + spend:api 无 generic_ok + campaign 有主 |
| S-S34-papers-owes-a-verify-gate | 2 | papers | 领地占用 + paper 有主 |
| S22-access-check-close | 3 | arc-recon | **仅** infra 有主（领地空着） |
| S28-no-third-value-in-the-monitor | 2 | monitor | 领地占用 + infra 有主 |
| S29-measurement-missing-is-not-zero | 1 | proxy | **仅** infra 有主（领地空着） |
| S4-freeze-complete | 1 | freeze | deps 未结(S4-freeze) + 领地占用 + campaign 有主 |
| V2-V25-leakage-loo-and-multiplicity | 2 | exam | 领地占用 + verify 有主 |
| V6-V23-large-space-verdict-gap | 2 | exam | 领地占用 + verify 有主 |

## 两点可选处置（都由监控拍板，我不动板）

1. **S29（p1，proxy）与 S22（p3，arc-recon）的领地是空的**，唯一的锁是 infra 赛道
   有主。它们已经在 `list` 的 reserved 段里挂了 28 分钟等 RES-4——而 RES-4 同时
   握着 R3 与 S-S33 两件。若想让通用工人吃掉 S29，只需要给它去掉 `lane: infra`
   或另开一件不带赛道的等价条目；我不擅自改板上的 front matter。
   （S22 的正文已写明「按 CHARTER 仅 RES-1 可花钱」，剩余部分要真实 API，
   通用工人接了也只能交半件——建议维持预留。）
2. **通用工人当前的需求量是 0**。这一轮再起通用工人都会立刻 BOARD-EMPTY 退出；
   要么先补几件不带赛道的活，要么把 headcount 收回给四条赛道。

## 一条给 `board.py` 的建议（未实施，monitor 非我领地）

`claim` 在无活可领时可以把退出码 3 分成两种消息：`BOARD-EMPTY`（items/ 真为空）
与 `BOARD-ALL-HELD (n queued)`（有条目但全被守卫挡住）。守卫都是对的，
缺的只是让工人一眼看出「不必再重启我」还是「板确实做完了」。
