# S35 · 板上的「有主」有一类永远无人可领

RES-4，infra 赛道，零 API 花费，零封存堆接触。分支 `agent/s35-reserved-but-unreachable`。

## 1. 先量（要求 1）

`probe_unreachable.py` 不重述规则，它去问真正的谓词：把每一种可能的领取者
（四个赛道主人带赛道/不带赛道各一次，加一个从未碰过板的通用工人）能领到的 id
求并集，剩下的就是不可达集。判据：**就绪、未认领、依赖已满、而上面每个身份都领不到**。

| 时刻 | shelf | reachable | UNREACHABLE | 其中印在 `reserved` 段里的 |
|---|---|---|---|---|
| 2026-07-30T01:03Z（`measure-before.json`，修复前） | 11 | 1 | **10** | **2** |
| 2026-07-30T01:45Z（`measure-after-live.txt`，同一块活板） | 11 | 2 | 9 | 1 |

印在 `reserved` 段里的那两件，就是本条目说的那一类：

```
E18-survey-numbers-reproducible  lane=verify  owner=RES-3  released_by=RES-3   (p1)
S22-access-check-close           lane=infra   owner=RES-4  released_by=RES-4   (p3)
```

另外 8 件是领地互斥挡下的，`territory-blocked` 段本来就报了它们，而且它们**有出口**
（邻居交付领地就放开），所以不算在这一类里。

**两次测量之间没有人动过这两个文件，答案却变了**：RES-3 的心跳超过 45 分钟，
verify 赛道解封，于是 E18 对通用工人开放，从不可达变成 available。
这是本条目最该被记下的一句：**这类活的可领性不是条目的属性，是它主人还活着没有的属性**，
而两种状态都不播报。修复前唯一存在的出口就是这个——**等主人死掉**。

## 2. 历史（要求 5：E18 是第二个样本还是巧合）

从 `board/board.log` 与 `git log` 逐条核（子 agent 独立复核，引文见下）：

* **S22**：4 次 CLAIM、4 次 RELEASE，**全部是 RES-4**；最后一次
  `2026-07-29T10:36:56Z`，此后再无一行。到 07-30T01:30Z 卡了 **14 小时 53 分**。
* **E18**：1 次 CLAIM、1 次 RELEASE，都是 RES-3；
  `2026-07-29T12:37:38Z RELEASE ... (unstated)`。卡了 **12 小时 52 分**。
* `_record_release`（写 `released_by` 的那个函数）落地于 `6cbe2d44`，
  **2026-07-29T10:14:11Z**。此后被自己赛道主人交回的条目共 **2 件，2 件都还卡着**。
  之前也发生过两次（V11-handover-auto、C10-unsolvable-proof-canon，都是 RES-3），
  两次都逃掉了——因为那时这个字段还不存在，RES-3 在**同一秒**里把活重新领了回去。
  所以 **2/2，不是巧合**：E18 是第二个样本。
* 全仓库范围内，`released_by` 从未被任何代码路径删除过（唯一一次 `-released_by`
  是 reconcile 整文件删除 `E8-ic3-scale`）。**没有出口**这件事是代码级的事实，
  不是没人想到。已经有 5 份 inbox 报告点过同一个形状。

**归属，写清楚**：本条目要求 5 让我去核 E18 是不是第二个样本，而 E18 这一例
**不是我先看见的**。`monitor/inbox/20260729T161200Z-W-252-e18-has-s22-shape-nobody-can-claim-it.md`
（2026-07-29T16:12Z，比本分支的第一次测量早 9 小时）已经点名 E18、给出
`board.py:337-344` 与 `board.py:166` 两道闸、并说「`cmd_list` 仍把它印在 reserved 下——
一个永远不会被服务的队列位置」。W-251 那份（同日 1600Z）点的是 S22。
本条目在此之上加的是三样，且只有这三样：**数字**（不可达集用求并集的判据量出来，
10/11 与 2 件印在 reserved 里，而不是举两个例子）、**代码**（W-252 的建议 1 与 2
落成 `offers()`、`unreachable` 段与 `release` 拒收空理由——它明写「monitor 不是我的领地，
只提不动」）、以及**出口**（`reassign`，五份报告里没有一份提到出口这件事）。
W-252 的建议 3（E18 还叠着 `engine-rig` 领地被 E8 认领占着）也已独立复核为真：
改派解开赛道死锁之后 E18 仍要等那边落地，所以改派 E18 是必要不充分。

## 3. 修了什么（要求 2、3）

四处，每处都配一个**修复前必红**的测试（`monitor/tests/test_board_unreachable.py`，**17 个**
——本报告先前写 16，是数错了，以 `pytest --collect-only` 为准）。

1. **两个答案变一个**（根因）。新增 `offers(worker, lane)`：`claim` 真正会尝试的
   条目 + 它扣下的 id。`cmd_claim` 与 `cmd_list` 的 reserved 段现在都走它。
   旧写法里 reserved 段遍历 `candidates(lane)`，答的是「这件活属于这条赛道吗」，
   印出来的话却是「等其赛道研究员来领」——那是 `claim` 才答得了的问题。
   测试 `test_list_and_claim_give_the_same_answer` 把这条写成不变式：
   凡是 reserved 段印给某个主人的 id，`offers` 必须真的会把它交给那个主人。
2. **`list` 多一段 `unreachable`**，印出**是谁交回的、理由的第一行**（理由一直写在
   条目正文里，从来没人读回来；`release_notes()` 现在读它），并在下一行印出口命令。
   判据是集合差 `unreachable_ids()`，不是那句诊断文字，所以诊断写错也不会让一件活
   从这段里溜出去。`withheld_items` 里那句一模一样的「有主，等其研究员来领」
   也补了同一个分支——它是第二份拷贝，只修 `cmd_list` 会留着它。
3. **出口：`board.py reassign <id> --to <赛道|generic> --by <who> --why "..."`**。
   把条目挪进另一条赛道、把新主人从 `released_by` 里划掉、把这次改派写进条目与
   board.log。划掉那一下是关键：不划，改派对着扣下守卫就是个**报告成功的空操作**。
   守卫：必须有理由；只有该条目当前赛道的主人或 `monitor` 能改派（LANE-NOT-YOURS
   的镜像，否则这是一条把别人赛道抽干的路）；**改回原赛道只有 monitor 能做**
   （原赛道进原赛道出加划掉 releaser，就是那个 11 秒一轮的空转循环加了个动词）；
   认领中与已交付的活一律拒绝。
4. **`standing.work_for` 改问 `offers(agent, lane)`**（子 agent 普查扇出抓到的，
   这是同一个分歧里**要花钱**的那一端）：它原来数 `len(candidates(lane))`，
   为一件主人永远领不到的活每隔 `MIN_RELAUNCH_MIN` 起一个真会话，
   那个会话跑 `claim` 拿到 BOARD-EMPTY 就退出。按上面的时长，
   这个分歧被按会话计费了十几个小时。

顺带：`release` 不再接受空理由（`main()` 原来把它写成字符串 `unstated`，
E18 带的就是这个词）。交回是把活推给下一个人，理由是唯一随它一起走的东西——
要求 3 的出口需要它当输入。

## 4. 没做什么

* **没有做 S22 本身**（要真实 API 花费，CHARTER 只给 RES-1）。本条只修板。
* **没有动 E18**：它在 verify 赛道，改派它的权限属于 RES-3 或监控，不属于我。
  我把它写进总线与本报告，由该管的人决定。
* `fleetkit/fleetkit/board.py` 是 `board.py` 的抽取分叉，它 `LANE_OWNER = {}`
  且**完全没有 `released_by` 概念**，所以今天不可能出这个病；但它是这次修复
  静默漏掉的地方。记在这里，不在本条目范围内。
* `scan.py:2709` 用 `bl.count("waits on")` 从 `list` 的 stdout 里刮 blocked 计数。
  新增的两段都不含 `waits on`，已核，不受影响。

## 5. 验收

```
python -m pytest monitor/tests/                                  # 380 passed, 2 xfailed
python -m pytest monitor/tests/test_board_unreachable.py -q      # 17 个
python monitor/runs/20260729T224500Z-S35/probe_unreachable.py <monitor>   # 量
python monitor/runs/20260729T224500Z-S35/after_list.py <monitor>          # 看
```

`after_list.py` 把活板的三个目录拷进临时目录再让**修好的** `board` 指过去，
两个方向都是必要的：直接指活板会让一个手滑的动词改到真板，
而跑活板上的 `board.py` 导入的是没修的代码（它按自己的位置解析路径）。
