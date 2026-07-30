# W-2400 · `claim` 报 BOARD-EMPTY，而板上有 11 件活；`list` 只肯露出 3 件

from: W-2400
utc: 2026-07-29T16:00:51Z
base_commit: 7852ef30
kind: 阻塞 + 发现（board.py 可见性）

## 我做了什么

`python monitor/board.py claim W-2400` → `BOARD-EMPTY`（exit 3），且**没有**
「N 件被扣下」的后缀，所以不是我自己交回过的那条路径。我没有开工，没有建分支，
没有动任何领地。

## 一、阻塞：板确实对我全关，但不是因为空

`monitor/board/items/` 里有 **11 件**未认领的活。逐件跑 `board.py` 自己的
`candidates()` / `territories_busy()` / `stale_lanes()`，结果如下（vis = 是否
出现在 `list` 的任何一节里）：

| 条目 | vis | territory | lane | 被谁占住 | 未决 deps |
|---|---|---|---|---|---|
| A3-campaign-level2 | 否 | theoria-arm | campaign | A3-campaign-devpile | — |
| A8-campaign-ledger-pipeline | 否 | theoria-arm | campaign | A3-campaign-devpile | — |
| E18-survey-numbers-reproducible | 否 | engine-rig | verify | E8-ic3-scale | — |
| E3-engines-online | 否 | theoria-arm | campaign | A3-campaign-devpile | — |
| S-S34-papers-owes-a-verify-gate | 否 | papers | paper | P17-machine-checked-ruling | — |
| S22-access-check-close | 是 | arc-recon | infra | — | — |
| S28-no-third-value-in-the-monitor | 否 | monitor | infra | S-S33-monitor-gate-red-on-master | — |
| S29-measurement-missing-is-not-zero | 是 | proxy | infra | — | — |
| S4-freeze-complete | 是 | freeze | campaign | S4-freeze | S4-freeze |
| V2-V25-leakage-loo-and-multiplicity | 否 | exam | verify | V21-leakage-gate-token-level | — |
| V6-V23-large-space-verdict-gap | 否 | exam | verify | V21-leakage-gate-token-level | — |

**8 件被领地互斥挡住**（七个领地全被在飞的认领占着：theoria-arm / engine-rig /
papers / release / monitor / freeze / exam），**2 件被赛道预留**（S22、S29 都是
infra，主人 RES-4 心跳 0 分钟前，活着，赛道不解封），**1 件被 deps 挡住**
（S4-freeze-complete 等 S4-freeze）。

`stale_lanes()` 返回空集：RES-1 心跳 15 分钟前、RES-2 0 分钟、RES-3 6 分钟、
RES-4 0 分钟，四个赛道主人全活着。`sweep --dry-run` 与
`sweep --dry-run --include-standing` 都报 `no orphaned claims`，六个常驻认领
全部 KEPT——**没有可回收的僵尸认领**，包括 W-130 占着 engine-rig 的那件
（E8-ic3-scale，注意 done/ 里已经有一份 `E8-ic3-scale.W-1660`，可能重复，但它的
计划任务确实在跑，所以我没碰）。

结论：这不是「没活了」，是「活全都有主，而通用工人的可领集合恰好为空」。**再派
通用工人来也领不到东西**，除非先释放领地或显式开放赛道。可动的旋钮我看到三个，
挑哪个是你的事：把 S22 / S29 标 `generic_ok` 无用（它们卡的是赛道不是花钱），
真正有效的是（a）给 infra 赛道的 S22/S29 临时去 lane，（b）把某些条目改到没被
占住的领地，（c）什么都不做，等在飞的六件交付后自然松开。

## 二、发现：`list` 把 8/11 件活变成了不可见

`cmd_list` 只打三节：`available`（= `candidates()`）、`reserved`（= 各 lane 的
`candidates(lane)` 差集）、`blocked`（deps 未决）。**被 `territory in busy` 过滤
掉的条目一节都不进**——`candidates()` 在赛道判定之前就 `continue` 了，所以它既
不在 available，也不在 reserved。于是刚才那 11 件里只有 3 件在 `list` 输出中露过面。

这正是 `stale_lanes()` 的注释里已经写下的那个教训的第二个实例：那次是「主人在忙」
和「主人已死」被当成同一件事；这次是「板上没有这件活」和「这件活的领地正被占用」
被当成同一件事。`board.py` 里 `cmd_claim` 的 withheld 分支专门为此写过一段话——
「nothing to do」和「nothing I will show you」必须长得不一样——而 `cmd_list`
和 `cmd_claim` 的 BOARD-EMPTY 都还没照做。

具体后果不是理论上的：一个刚起的通用工人跑 `claim` 得到 `BOARD-EMPTY`，跑 `list`
看到 available 0 / reserved 2，会合理地判断「板快空了，收尾退出」，而实际情况是
板上压着 8 件被领地锁住的活。派更多工人不会有产出，但看板的人无从知道。

建议（我没有改，monitor 领地不是我的，且 S28 与 S-S33 都在改这一带的代码，我改
会撞车）：

1. `cmd_list` 加第四节，例如 `=== territory-locked（领地被占，等其交付 N） ===`，
   逐条印 `territory` 与占住它的条目 id。实现上只要在 `candidates()` 之外单独扫
   一遍 items/ 与 `territories_busy()`，不必动过滤逻辑本身。
2. `cmd_claim` 的 BOARD-EMPTY 同样带上计数，例如
   `BOARD-EMPTY（板上仍有 11 件：8 件领地被占，2 件赛道预留，1 件等 deps）`，
   与 withheld 分支一样的写法。exit code 保持 3 不变。
3. 若两条都做，与 S28「监控自己也没有第三个值」是同一族：这里的第三个值是
   「板空」/「板不空但你领不到」，今天编码成同一个字面量 `BOARD-EMPTY` + 同一个
   exit 3。

## 我的下一步

按 brief，`BOARD-EMPTY` 即收尾退出。我不重做任何在飞条目，不碰 master，没有
建分支或 worktree。上面第二条若你希望我来做，把它签成一件 `territory: monitor`
的工单挂上板，我下次心跳就能领。
