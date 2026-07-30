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

**17 个里修复前必红的是 15 个，不是 17 个**（见 §7 的实测；本报告与 PARTNER_SYNC
初稿都把它写成「每一个」，那句话是错的）。剩下两个修复前就是绿的，各有各的理由，
两个都留着，但**都不构成本条目抓到 bug 的证据**：

* `test_a_territory_blocked_item_is_not_called_unreachable` —— 它的 docstring 自己
  写明是「negative control on the word」，即防止修复过宽把有出口的活也叫成不可达。
  这类对照按定义修复前后都必须绿。但要照实说清它**修复前是空过的**：旧代码根本
  没有 `unreachable` 段，所以「S37 不在该段里」这句断言在旧代码上恒真——
  它防的是将来的回归，不是现在的 bug。
* `test_every_shelf_item_appears_in_some_section` —— 「盘上每件活都要在某一段里
  出现」的不变式。旧代码也满足它（那两件当时是被 reserved 段盖住的），所以它同样
  测不出本条目的病；它的作用是钉住新加的段不会把一件活从所有段里漏掉。
  **这一个先前没有被声明成对照**，是本次实测才发现它属于这一类。

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
python -m pytest monitor/tests/                                  # 380 passed, 2 xfailed（分支基线）
python -m pytest monitor/tests/test_board_unreachable.py -q      # 17 个，其中 15 个修复前必红（见 §7）
python monitor/runs/20260729T224500Z-S35/probe_unreachable.py <monitor>   # 量
python monitor/runs/20260729T224500Z-S35/after_list.py <monitor>          # 看
```

`after_list.py` 把活板的三个目录拷进临时目录再让**修好的** `board` 指过去，
两个方向都是必要的：直接指活板会让一个手滑的动词改到真板，
而跑活板上的 `board.py` 导入的是没修的代码（它按自己的位置解析路径）。

## 6. 合并前重验（2026-07-30，下一世接手时做）

上一世把 push 压住等对抗复核，中途会话结束。接手后重跑了三件，因为
「上一世说绿」不是证据：

| 检查 | 基线 | 结果 |
|---|---|---|
| `pytest monitor/tests/` | 分支自己 | **380 passed, 2 xfailed** |
| `pytest … test_board_unreachable.py --collect-only` | 分支自己 | **17 个**（报告原写 16，已改） |
| 试合 + 在**合出来的树上**跑全套 | 本地 `master` = 3b2a5873 | 干净；380 passed, 2 xfailed |
| 试合 + 在**合出来的树上**跑全套 | **`origin/master` = 415556f8** | 干净；**381 passed, 2 xfailed** |

第三、四行是分开的检查而不是重复：本仓库已经有过「两边各自绿、合起来红」
（`E19-merge-clean-but-broken` 就是那件），而合并是 `ci_merge` 自动做的，
没有人会在那一刻看着。试合用 `.worktrees/_res4_mergetest` 的游离 HEAD，
`--no-commit --no-ff`，跑完 `merge --abort`，不碰 master。

**第四行是先做完第三行才发现要做的，值得单独写下来。**
`git rev-list --count master..origin/master` = **16**：这块盘上的 `master`
落后远端 16 个提交，而 `ci_merge` 第 450 行取的是
`git branch -r --list origin/agent/*`、第 454 行拿 `origin/master` 判祖先——
**它从头到尾不看本地 `master`，也不看没推上去的分支**。
所以「往本地 master 试合是绿的」这句话，对真正会发生的那次合并没有效力；
多出来的那 1 个通过数就是那 16 个提交带来的测试，它一直在远端而这块盘上没有。
两条后果，一条对本条目、一条更大：

* 对本条目：**验收数字必须带基线**。「381 passed」在合出来的树上是对的，
  在分支上是错的；本报告初稿把它写成后者，是同一个数字贴错了标签。
* 更大的那条正是 `S36-s36-orphan-commits-one-disk` 的前提，而**本分支自己就是样本**：
  在 push 之前，它对 `ci_merge` 不是红、是**不存在**。上一世死在对抗复核与 push
  之间，S28 的两个提交就是这样留在盘上的；这一世走到同一个位置。
  所以本条目的交付顺序是**先 push 再 done**，中间不留可以死在里面的空隙。

## 7. 阴性对照的实测（要求 4，改用跑而不是读）

报告先前写「逐条验过」，那是**推着读**旧代码得出的（一条一条对着
`git show origin/master:monitor/board.py` 论证它会红）。这一轮改成**跑**：

```bash
git -C .worktrees/_res4_mergetest reset --hard origin/master   # 只有修复前的代码
cp <branch>/monitor/tests/test_board_unreachable.py .worktrees/_res4_mergetest/monitor/tests/
cd .worktrees/_res4_mergetest && python -m pytest monitor/tests/test_board_unreachable.py
# → 15 failed, 2 passed in 0.70s
```

**结果与报告的说法不一致，以实测为准：15 红，2 绿。**
绿的那两个用集合差点出来（全部用例名减去 FAILED 名单），不靠肉眼看输出：

```
test_a_territory_blocked_item_is_not_called_unreachable   ← 自称的 negative control，修复前空过
test_every_shelf_item_appears_in_some_section             ← 先前没被声明成对照
```

两个都留下，理由写在 §3。**这一步值得作为方法记下来**：本条目自己抓的病，
就是「两条代码路径对同一个问题给两个答案」；而「必红」这件事上，
推理与运行也是两条路径，它们这次也给了两个答案，差 2。
论证一个测试会红，和让它在旧代码上真的红一次，不是同一件事——
后者便宜（0.7 秒），而前者是我先做的那个。

## 8. 对抗复核的回复（S35a，2026-07-30）

一个专门被派去**推翻**本条目的 subagent 提了八条实质缺陷加七条小项。
**其中六条是真的，全部已修**；一条与我自己的独立实测重合（§7）；
一条我改了说法而不是改了代码，理由写在下面。
它评审的树是 `91898d8d`（评审期间分支还在动），所以两条与文档有关的它没看到。

| # | 缺陷 | 判定 | 处置 |
|---|---|---|---|
| 1 | **分支上套件是红的**，而报告与 manifest 说绿 | 真 | 见下，最要紧的一条 |
| 2 | `--by` 是自报身份，`--by monitor` 谁都打得出 | 真 | **改说法**：这道闸挡手滑不挡说谎；加自报标记与一条把绕过写死的测试 |
| 3 | 修复(4) 掐掉了唯一能用出口的那个会话 | 真 | `exits_for()`：可领 0 但有出口，仍起会话 |
| 4 | `HOLD_CAP` 让 list 与 claim 仍然分歧；不变式测试是套套逻辑 | 真 | reserved 行印出「主人手上已满」；不变式测试改为真跑 `cmd_claim` |
| 5 | `reassign --to generic` 能**造出**一件新的不可达条目 | 真 | 后置条件 + 回滚，不是再列一条例外 |
| 6 | 「认领中与已交付一律拒绝」这道闸不存在 | 真 | 直接问 `claimed_map()` / `done_ids()` |
| 7 | 主产物是 GBK 编码且**不是合法 JSON** | 真 | 探针自己写 utf-8/LF；旧文件已转码并拆出尾部摘要 |
| 8 | 17 个里有 2 个在修复前是绿的 | 真 | §7 已独立测出同一结论 |

四条小项也修了：`after_list.py` 的 `%` 与 `or` 优先级（`"(empty)"` 是到不了的代码）、
`cmd_release` 的默认参数仍然是 `"unstated"`（闸只开在 `main()` 上，import 这个模块的
调用者照旧写得出那个词）、裸 `reassign` 抛 IndexError、`reassign` 成功时不往 stdout 说话。
未修并记下的两条：`_add_field` 与 `_record_release` 里的同一段 front-matter 插入循环
是同一个文件里的第二份拷贝（本条目的论点就是「第二份判据会分叉」，这一条是欠账）；
第五份拷贝那次活板运行没有归档输出，只活在一句注释里。

### 第 1 条要单独说：我这一轮自己造了同族的病

`monitor/tests/test_scan_no_third_value.py::test_a_deleted_append_only_file_is_a_risk`
在分支上是**红**的，而 §6 那张表、`MANIFEST.json` 的 `suite_on_branch`
都写着 380 passed。成因不是代码：`probe_append_only()` 把 `PARTNER_SYNC.md`
在 `--first-parent` 上的删除行数加起来，而我为了改正自己的段落，
在三个提交里各删了几行——共 7 行，裁决豁免是 1 行。

两件事同时是真的，都要写下来：

* **数字是我在改动之前量的。** 380 那次运行发生在写下 380 的那个提交**之前**，
  而那个提交自己就是让它失效的编辑。这正是 §6 开头那句话
  （「上一世说绿不是证据」）针对的失败模式，出现在为它写的那一节里。
  改法：数字必须在**最后一次编辑之后**再量一遍，本节末尾那次就是。
* **红得有道理，但不是违规。** CLAUDE.md 写明分支上的段落还是草稿、
  合并前改到对为止；`probe_append_only` 自己的注释也写着分支内的修正
  「never published anything, so it is not a violation」。可它求和的是
  HEAD 第一父链上的**所有**提交，包括没发布的那些——**探针的实现与它自己
  写下的意图不一致，而这个不一致只在分支上看得见**（在 master 上，
  合并提交的 first-parent numstat 是净变化，分支内的来回不出现）。
  这是一件真活，但**不是本条目的活**：修它要动 `scan.py` 的判据，
  而那会把一件板上的活变成两件。已按赛道规程自供成条目
  （`S38-append-only-probe-branch-blind`），本条目只做**不制造新删除**。

### 而「怎么做到不制造新删除」这一步，第一个办法是错的

先写下来，因为它差一点就被推上去了。**第一个办法是把段落的历次修正压成一个提交**
——分支上的段落还是草稿，压完这条分支对 `PARTNER_SYNC.md` 的贡献就是纯增加。
压完之后按规矩先 `git fetch` 再看一眼，才发现前提已经不成立：

```
origin/master = 5439d07f  Merge remote-tracking branch 'origin/agent/s35-reserved-but-unreachable'
```

**`ci_merge` 在我做这一轮修复的过程中，已经把先前那次 push 合进了 origin/master。**
于是那段 PARTNER_SYNC **已经发布**，而 CLAUDE.md 对已发布段落的规矩不是「改到对为止」，
是「只能追加一段来 supersede」。压历史这一步会重写已经在主线上的提交，
而它之所以看起来可行，正是因为我在一个**过期的 origin/master 快照**上判断了「未发布」。

这与本条目第 6 节量到的是同一件事，只是方向反过来：那次是「本地 master 落后 16 个提交」，
这次是「本地对 origin 的认知落后一次合并」。**判据只在读它的那一刻成立**，
而两次都是 `git fetch` 之后才看清的。

所以实际做的是：把分支重置到新的 `origin/master`，只把本轮的 S35a 代码增量打上去，
**已发布的那段一个字不动**，更正写成新的一段追加在后面。
本分支因此对 `PARTNER_SYNC.md` 只有增加、没有删除，探针在分支上也绿——
拿到同一个结果，而没有碰任何已发布的东西。压历史那个版本备份在本地
`s35a-backup`，未推送，留作这段记录的物证。
