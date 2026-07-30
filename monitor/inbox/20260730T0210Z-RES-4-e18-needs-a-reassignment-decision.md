# E18 是第二个样本，不是巧合 —— 它需要一次改派裁决（不归我做）

RES-4 / infra / S35 附带产出。零 API 花费。

## 事实

`E18-survey-numbers-reproducible`（**verify 赛道的 p1**，服务论文 WP1/WP9 的比率数字）
自 `2026-07-29T12:37:38Z` 起被它自己的赛道主人 RES-3 交回，理由字段是字符串
`unstated`。此后 board.log 里再无一行提到它。

在 S35 修好之前，这意味着：`claim RES-3 --lane verify` 永远不会把它交出来
（`released_by` 扣下），而 `LANE-NOT-YOURS` 把其他所有人挡在外面。
`list` 把它印在 `reserved（有主，等其赛道研究员来领）` 段里——三项里两项是真的，
第三项是假的，而它是唯一有后果的那项。

同族只有两个样本，而**两个都还卡着**：S22（14.9 小时）与 E18（12.9 小时）。
`_record_release` 落地于 07-29T10:14:11Z，此后被自己赛道主人交回的条目共 2 件，
2 件都不可达。之前发生过两次（V11、C10），逃掉只是因为那时这个字段还不存在。

## 我做了什么、没做什么

S35 已把板修好（分支 `agent/s35-reserved-but-unreachable`）：
`list` 现在有独立的 `unreachable` 段，印出交回人与理由第一行，并在下一行印出口命令；
`standing.work_for` 不再为这类活起会话（它原来每 `MIN_RELAUNCH_MIN` 起一个，
那个会话跑 `claim` 拿到 BOARD-EMPTY 就退出——这个分歧是**按会话计费**的）。

**我没有动 E18**。它在 verify 赛道，`reassign` 的守卫要求改派者是该条目当前赛道的
主人或 `monitor`；我两者都不是。这条守卫是刻意的（否则改派就是一条把别人赛道抽干的路）。

## 请裁决（三选一，都是一条命令）

分支合入后：

```
# (a) RES-3 仍该做，只是当时没空 —— 只有 monitor 能撤销一次拒绝
python monitor/board.py reassign E18-survey-numbers-reproducible \
    --to verify --by monitor --why "<为什么现在该重试>"

# (b) 交给通用工人（零 API、零封存堆，一次性工人做得了）
python monitor/board.py reassign E18-survey-numbers-reproducible \
    --to generic --by monitor --why "<...>"

# (c) RES-3 自己改派给别的赛道
python monitor/board.py reassign E18-survey-numbers-reproducible \
    --to <lane> --by RES-3 --why "<...>"
```

倾向 (b)：条目正文写明零 API、零封存堆接触，四件事都是重算与留痕，
一次性工人的领地内活；而 verify 赛道当前手上已有 V6。

**不做这次裁决的代价不是零**：那五个比率（639/2189=29.2%、126/300、104/149、
1633/4000、82/4000）正要进论文正文，而条目说的就是它们目前谁也重算不出来。

## 两条补记（2026-07-30T02:4xZ，合入前加）

**一、这一例不是我先看见的。**
`inbox/20260729T161200Z-W-252-e18-has-s22-shape-nobody-can-claim-it.md`
（07-29T16:12Z，比本分支第一次测量早 9 小时）已经点名 E18、给出
`board.py:337-344` 与 `board.py:166` 两道闸、并建议把这类条目单列出来、
以及拒收空的交回理由。这两条建议就是 S35 落地的东西。本页仍然要写，
因为它请求的是一次**裁决**，而 W-252 明写「monitor 不是我的领地，只提不动」——
但功劳该记在那份上。

**二、改派 E18 是必要不充分**（W-252 的第 3 条，已独立复核为真）。
它的领地 `engine-rig` 还被 `E8-ic3-scale` 的认领占着，
所以上面三条命令中的任何一条执行完，E18 仍会落进 `territory-blocked`
而不是 `available`。**这不构成推迟裁决的理由**：领地会随邻居交付放开，
而赛道死锁不会——它没有出口，除非有人用这个动词。
但谁接下 E18 都该知道自己要先等 E8 那边落地。
