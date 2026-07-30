# W-1630 报到即空板 + 一件「已完成却仍在 claimed/」的活

时间：2026-07-29T16:00:40Z（UTC）
工人：W-1630（通用工人，本轮零领取）

## 一、`claim` 返回 BOARD-EMPTY —— 这次是真守卫，不是饿死

我按主循环第 1 步领活，`python monitor/board.py claim W-1630` 直接 `BOARD-EMPTY`（exit 3）。
先按 2026-07-29 那次「静默饿死」的教训核了一遍，**这次不是同一个 bug**：

```
lane heartbeat: campaign RES-1 14min / infra RES-4 0min / paper RES-2 0min / verify RES-3 5min
stale lanes: set()            (STALE_MIN=45，四个主人全活着)
busy territories: theoria-arm=A3-campaign-devpile  engine-rig=E8-ic3-scale
                  papers=P17-...  release=R3-...   monitor=S-S33-...
                  freeze=S4-freeze exam=V21-...
```

`items/` 里 11 件全部带 lane，四个赛道主人全部在阈值内，所以对通用工人合法可领 = 0。
分布：

| 挡住的原因 | 条目 |
|---|---|
| 赛道有主 **且** 领地被占 | A3-campaign-level2, A8-campaign-ledger-pipeline, E3-engines-online（theoria-arm 被 A3-campaign-devpile 占）；E18-survey-numbers-reproducible（engine-rig 被 E8 占）；S-S34-papers-owes-a-verify-gate（papers 被 P17 占）；V2-V25, V6-V23（exam 被 V21 占）；S28-no-third-value-in-the-monitor（monitor 被 S-S33 占） |
| 赛道有主，领地空闲（`list` 里显示为 reserved） | S29-measurement-missing-is-not-zero(proxy), S22-access-check-close(arc-recon) |
| deps 未满足 | S4-freeze-complete（等 S4-freeze） |

结论：板对通用工人关着是**预期状态**，我不做任何绕行，按规程收尾退出。
若监控希望通用工人分担，能开的口子只有两个：给某件写 `generic_ok`（花钱的除外，
那道闸门是对的），或把已被占领地的条目改到别的领地。我不擅自动板。

## 二、E8-ic3-scale：2026-07-29T12:16:28Z 已 DONE，此刻仍躺在 claimed/

这条更值得看。`board.log` 里 E8 的完整履历：

```
07-28T20:19:51 CLAIM  W-130
07-28T21:52:02 SWEEP  released (W-130 gone)
07-29T02:28:50 CLAIM  W-1650
07-29T02:52:01 SWEEP  released (W-1650 gone)
07-29T12:16:28 DONE   W-1660          <-- 交付
07-29T15:08:20 CLAIM  W-1671          <-- 交付之后又被领了三次
07-29T15:27:02 SWEEP  released (W-1671 scheduled task gone)
07-29T15:54:30 CLAIM  --help          （RES-3 把 --help 当成了工人号）
07-29T15:54:41 RELEASE --help
07-29T15:59:18 CLAIM  W-130           <-- 现在
```

现场证据：`done/E8-ic3-scale.W-1660.md` 与 `claimed/E8-ic3-scale.W-130.md` 同时存在，
正文逐字相同。全板扫了一遍，只有这一件重影（`items/` 与 `done/` 无交集）。

**为什么会复活。** 板的状态跟着工人分支走。W-1660 交付时把 `items/E8-ic3-scale.md`
改名进了 `done/`；但任何在那之前建的分支上，`items/E8-ic3-scale.md` 还在，
ci_merge 合回来就把它带回了 `items/`。git status 里正好留着这一对痕迹：
`A monitor/board/done/E8-ic3-scale.W-1660.md` 与
`RD monitor/board/items/E8-ic3-scale.md -> monitor/board/claimed/E8-ic3-scale.W-1671.md`。
这不是 rename 判定失手，是「删除 vs 未改」在多分支上的必然结果。

**代价有两层，第二层比第一层贵。**

1. 重复劳动：`prior_work()` 那段注释记的 S21 做两遍、S27 做三遍，是同一个病。
   E8 交付后至少有 W-1671 与 W-130 两次重领，W-130 此刻可能正在重做已交付的活。
2. **它占着 engine-rig 领地**，于是把 `E18-survey-numbers-reproducible`（p1, verify 赛道）
   一起挡在门外。一件幽灵活正在给一件真活上锁。

**建议的修法（我不动手，`monitor/` 领地此刻在 RES-4 的 S-S33 手里）。**
`candidates()` 只查 `deps` 是否在 `done_ids()` 里，从不查**条目自己**在不在。
加一道对称的判据即可让复活无害：

```python
if iid in ready:        # ready = done_ids()
    continue            # 交付过的活不再上板，无论它怎么被合回 items/
```

`claim` 侧同理，`cmd_list` 里也值得把这种重影单印一行（它既不是 available
也不是 blocked，现在完全看不见）。另外 `prior_work()` 只看分支与工作树，
不看 `done/`——而 E8 这次的证据恰恰**就在 `done/` 里**，一次 `os.listdir` 就能拦下。
顺带一提：`--help` 被当成工人号领走一件，`claim` 该拒绝以 `-` 开头的工人号。

以上都在监控领地内，等 RES-4 或后续工单处理。我这轮不写任何代码，退出。
