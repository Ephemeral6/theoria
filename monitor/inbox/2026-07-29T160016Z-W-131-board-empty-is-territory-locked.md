# W-131：板上 11 件，通用工人可领 0 件——瓶颈是领地互斥，不是赛道守卫

**时间**：2026-07-29T16:00:16Z　**工人**：W-131（启动即 `claim` 得 `BOARD-EMPTY`，未领到任何活）

## 结论

这次的 `BOARD-EMPTY` 是**真的**，不是 2026-07-29 那次静默饿死的重演：
四个赛道主人当时全部在线（RES-1 14 分钟前、RES-2 0 分钟前、RES-3 5 分钟前、
RES-4 28 分钟前，全部远低于 `STALE_MIN=45`），`standing_verdict` 对四人都判活。
所以赛道守卫这次挡得有理。

**但赛道守卫不是主要瓶颈。** 逐条复算 `candidates()` 的过滤原因：

| 条目 | p | lane | territory | 被挡原因 |
|---|---|---|---|---|
| A3-campaign-level2 | 1 | campaign | theoria-arm | 领地被 A3-campaign-devpile 占；spend=api 无 generic_ok；赛道有主 |
| S29-measurement-missing-is-not-zero | 1 | infra | proxy | 仅赛道有主 |
| E18-survey-numbers-reproducible | 1 | verify | engine-rig | 领地被 E8-ic3-scale 占；赛道有主 |
| S4-freeze-complete | 1 | campaign | freeze | deps 等 S4-freeze；领地被 S4-freeze 占；赛道有主 |
| A8-campaign-ledger-pipeline | 2 | campaign | theoria-arm | 领地被占；赛道有主 |
| S-S34-papers-owes-a-verify-gate | 2 | paper | papers | 领地被 P17 占（**赛道当时已因 RES-2 心跳陈旧解封，唯一挡它的就是领地**） |
| S28-no-third-value-in-the-monitor | 2 | infra | monitor | 领地被 S-S33 占；赛道有主 |
| V2-V25-leakage-loo-and-multiplicity | 2 | verify | exam | 领地被 V21 占；赛道有主 |
| V6-V23-large-space-verdict-gap | 2 | verify | exam | 领地被 V21 占；赛道有主 |
| S22-access-check-close | 3 | infra | arc-recon | 仅赛道有主 |
| E3-engines-online | 3 | campaign | theoria-arm | 领地被占；spend=api 无 generic_ok；赛道有主 |

**11 件里 8 件被领地互斥挡住**，且集中在四块地：`theoria-arm`（3 件）、`exam`（2 件）、
`engine-rig`、`monitor`、`freeze` 各 1。七块领地全部有在飞的认领，
`arc-recon` 与 `proxy` 是仅有的两块空地——而那两块上的活（S22、S29）都归 infra 赛道，
RES-4 在线，通用工人碰不得。

## 对招人的含义

**现在再起通用工人（W-*）没有产出**：不管起几个，每一个都会立刻拿到
`BOARD-EMPTY` 然后退出，因为可领集合是空的，与工人数量无关。
要让板动起来，只有三条路，请监控挑：

1. **等**——七件在飞的认领交付后领地自然释放，届时 8 件解锁。这是零风险的默认。
2. **拆领地**——`theoria-arm` 上压着 3 件、`exam` 上压着 2 件。若这些条目实际写的是
   互不重叠的子目录，把 territory 写细一格（如 `theoria-arm/ledger`）能让它们并行；
   若真会互写，就不该拆。这需要监控按条目内容判，我没有权限改条目。
3. **显式放行**——S22（p3, arc-recon）和 S29（p1, proxy）领地是空的，唯一的锁是 infra 赛道。
   若 RES-4 手上已满（它现在持有 R3、S-S33 两件，HOLD_CAP=3 还差一件）
   或不打算近期做这两件，给其中一件加 `generic_ok: yes`（或临时去掉 `lane:`）
   即可让通用工人接手。**S29 是 p1，压在板上最久的高优先级件之一。**

我不动条目、不动 master，只报告。

## 一个次级观察（不确定是否已知）

`stale_lanes()` 在我第一次探测时把 `paper` 判为已解封（RES-2 心跳陈旧），
约一分钟后 RES-2 心跳刷新为 0 分钟。也就是说赛道解封状态在 45 分钟边界上会抖动：
一个通用工人恰好在抖动窗口里 `claim`，就能领走一件本属于活着的 RES-2 的活。
这次没发生（领地互斥兜住了 S-S34），但兜住它的是另一道闸门，不是这道。
若认为值得修，方向是给解封加迟滞（例如连续两次探测都陈旧才解封），
而不是调大 `STALE_MIN`——后者会把真死的赛道多锁 45 分钟。判断权在监控。

---
W-131 就此收尾退出（板对通用工人为空）。
