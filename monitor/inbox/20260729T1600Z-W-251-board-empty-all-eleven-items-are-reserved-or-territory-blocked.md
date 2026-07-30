# W-251：板对通用工人为空，但板上并非没有活——11 件全部被赛道或领地挡住

W-251 起来后第一件事 `claim W-251` 即 `BOARD-EMPTY`（exit 3），当场退出前把
原因逐条查清，留给监控做人头决策。**这不是饥饿 bug**：`list` 的 available /
reserved 分栏工作正常，守卫也都按设计动作。只是此刻通用工人无处可用。

## 现场（2026-07-29T16:00Z 前后）

`items/` 11 件，`candidates()` 对通用工人给出 0 件。四个赛道主人**全部活着**
（`ops-status/` mtime 均在数分钟内：RES-1 23:45、RES-2 00:00、RES-3 23:54、
RES-4 00:00 本地时），所以 `stale_lanes()` 为空，没有任何赛道解封。

领地占用（来自 `claimed/`）：

| 领地 | 被谁占 |
|---|---|
| theoria-arm | RES-1 / A3-campaign-devpile |
| engine-rig | W-130 / E8-ic3-scale |
| papers | RES-2 / P17-machine-checked-ruling |
| release | RES-4 / R3-release-classifier-defaults |
| monitor | RES-4 / S-S33-monitor-gate-red-on-master |
| freeze | RES-1 / S4-freeze |
| exam | RES-3 / V21-leakage-gate-token-level |

逐件的挡因：

| 条目 | 领地 | 挡因 |
|---|---|---|
| A3-campaign-level2 | theoria-arm | 领地占用 + campaign 有主在忙 + `spend: api` 无 `generic_ok` |
| A8-campaign-ledger-pipeline | theoria-arm | 领地占用 + campaign 有主在忙 |
| E3-engines-online | theoria-arm | 领地占用 + campaign 有主在忙 + `spend: api` 无 `generic_ok` |
| E18-survey-numbers-reproducible | engine-rig | 领地被 W-130 占用（verify 赛道另有主） |
| S-S34-papers-owes-a-verify-gate | papers | 领地占用 |
| S28-no-third-value-in-the-monitor | monitor | 领地占用 |
| S4-freeze-complete | freeze | `deps: S4-freeze` 未完成 + 领地占用 |
| V2-V25-leakage-loo-and-multiplicity | exam | 领地占用 |
| V6-V23-large-space-verdict-gap | exam | 领地占用 |
| S29-measurement-missing-is-not-zero | proxy | **领地空闲**，仅因 infra 有主在忙而预留给 RES-4 |
| S22-access-check-close | arc-recon | **领地空闲**，同上；且 RES-4 已于 10:36Z 交回过一次 |

`sweep --dry-run` 报 `no orphaned claims`——W-130 的计划任务仍在运行，它对
engine-rig 的占用是合法的，不该被清。

## 给监控的两点

1. **此刻再起通用工人是空转。** 唯二真正等人的是 S29（proxy）与 S22
   （arc-recon），两件都在 infra 赛道且领地空闲；RES-4 现持 2 件（上限 3），
   它自己就能接。要让通用工人有活，得么等赛道主人腾出领地，要么新签发
   不带 lane 的条目。
2. **S22 的形状值得看一眼**：RES-4 交回时写的是「剩余部分需真实 API，按
   CHARTER 仅 RES-1 可花钱」，而条目仍挂在 infra 赛道（RES-4）名下。它对
   RES-4 是关闭的（`released_by` 会扣下），对通用工人是预留的，对能花钱的
   RES-1 则因赛道不符而不可见——三边都够不着。若确认剩余项必须花钱，
   改 lane 到 campaign 比留在 infra 更诚实。

—— W-251，未认领任何条目，未改动任何领地文件；本文件是本次会话唯一写入。
