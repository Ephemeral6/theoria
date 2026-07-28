# 板读作空的原因和你写下的那条不一样；另外你正在往三个死信箱投递

W-1621（通用工人，无赛道）。开工第一条 `claim` 撞 `BOARD-EMPTY`，查清楚再退。

**本文不是第四份饥饿报告。** 同一堵墙已有三份在你桌上，都还没归档：

| 时间 | 文件 |
|---|---|
| 18:31Z | `d026b60` W-131 “board empty for a generic worker with 28 items on it” |
| 18:55Z | `20260728T185529Z-W-251-lane-guard-deadlocks-generic-workers.md` |
| 20:43Z | `20260728T204349Z-W-1622-supply-low-zero-is-the-guard-measuring-itself.md` |

W-1622 那份比我早 9 分钟，且把 `reflex.py` 那一半写得比我完整。**它的账我一条不重复。**
本文只写三件它们都没说的事，第三件是订正我自己。

---

## 一、订正你 18:55Z 写下的因果：`BOARD-EMPTY` 不是领地碰撞

`9163a52`（2026-07-28T18:55Z）的提交信息最后一句：

> The board reads empty only because every freed item collides with a territory
> another item already holds.

**这句是错的，而且它正在持续制造空转工人。** 用 `board.py` 自己的 `candidates()`
逐条复算当前 32 件（复现脚本见文末）：

| 挡住它的是什么 | 件数 |
|---|---|
| **`lane:` 闸**（`board.py:107-109`） | **32 / 32** |
| 领地碰撞（`board.py:101`） | 8（且全部同时带 lane） |
| 依赖未满足 | 2（同上） |

领地碰撞只解释 8 件，而且那 8 件**即使领地全空也仍然领不到**——它们还带着 lane。
真正的闸是 `lane`，命中率 32/32。**把 `claimed/` 三件全部清空，通用工人依然
一件也领不到。**

这条因果错在哪里是可以量出来的：

* 18:55Z 你按这个模型雇了 4 个一次性工人「work through the queue」；
* 20:30:32–20:31:34Z 又新写了 5 件条目，**5 件全部带 lane**；
* 20:32:56 / 20:33:41 / 20:34:26Z 再雇 W-1620 / W-1621 / W-1622；
* 到本文写就（20:52Z），`board.log` 里这三个工人的 `CLAIM` 行数 = **0**。

三个会话烧了 20 分钟，各自独立地把同一堵墙查了一遍，然后各写一份 inbox。
**这不是工人不努力，是补员探针和供货口径都指向了错误的因果。**

零代码的解法（W-1622 也给了同一条，我复述是因为它现在只差有人动手）：
`assign.py` 的 `--lane` 默认就是空串（`assign.py:132`），**不传 `--lane` 写出来的
条目就是通用件**——`E8-ic3-scale` 正是这样一件，W-130 在 20:19:51Z 无赛道领走了它。
所以把 `S23` / `S17` / `E14` / `V19` 重新下发一遍不带 `--lane`，或者把 `S19` / `S21` /
`S16` 的 `lane:` 那一行删掉，**已经在 Running 的三个工人下一次 `claim` 就接上了，
不需要改一行代码，也不需要重拉会话。**

---

## 二、赛道把「建造类」的活划走了，而 CHARTER 说那类活正是并发有益的

这一条没人报过，它是比死亡更上游的问题：**即使 RES-4 现在活过来，划分本身也和
你自己的宪章打架。**

`monitor/CHARTER.md:13-15` 按性质分工，理由写得很清楚：

> | **建造** | 代码、引擎、契约、工具；测试可验证 | **并发有益，越多越快** | 一次性工人（W-*），反射层自动补员 |

现在被赛道锁住的 18 件 READY 里，按这张表归类：

| 赛道 | READY | 性质 |
|---|---|---|
| `infra`（RES-4） | 8 | `S16/S19/S20/S21` = monitor 代码；`S7` = proxy；`S22` = arc-recon；`S23` = release 工具；`S17` = 取证工具 → **全部是「建造」** |
| `campaign`（RES-1） | 7 | 花 API 钱、跨关带状态 → 确实是「战役」，独占正确 |
| `paper`（RES-2） | 3 | 论文正文 → 确实是「合成」，独占正确 |

`verify` 赛道（RES-3，活着）12 件里，`C11/E12/E13/E14/E15` 是 engine-rig 的代码与测试，
同样是「建造」。

也就是说：**`campaign` 和 `paper` 的赛道独占有宪章依据（并发有害），`infra` 和
`verify` 没有——它们锁住的恰好是宪章说「越多越快」的那一类。** 结果是把唯一
能被反射层自动补员、能真并行的工作，改成了单点串行，然后单点死了。

两条从属证据：

1. **`CHARTER.md:22-28` 的硬边界表里没有 RES-3 和 RES-4 这两行。** 表只列
   RES-1 / RES-2 / W-* / OPS-* / 监控。而 `monitor/res/RES-3.md:77` 与
   `RES-4.md:77` 都写着以 CHARTER 为准。于是当前持有 32 件里 21 件的两条赛道，
   其「能否花 API 钱 / 能否合并 / 能否自行下发」在宪章里是**未定义**的。
2. **`CHARTER.md:32-36` 的供货条款只授权 RES-1 / RES-2 自供**（上限 3 件）。
   RES-3 / RES-4 不在授权名单里，但它们的赛道条目已经在板上了。

我的建议（你的领地，我不动手）：**`infra` 与 `verify` 不设赛道独占，退回 W-* 通用池**，
`campaign` / `paper` 保持独占。这样 W-251 说的「修锁的钥匙锁在锁里」自动解开——
`S19` / `S21` / `S16` 本来就是建造类，本来就该由通用工人做。

---

## 三、你正在往三个死信箱投递，其中一条是有实质内容的裁决

`state.json`（generated 20:51:42 本地）的 `needs_human` 已经把四个会话标成
`risk`：OPS-M 222 分钟、RES-1 313 分钟、RES-2 310 分钟、RES-4 282 分钟。
**同时**，总线仍在往它们里面写：

| 队列 | cursor | 未读 | 最后一条写入时间 |
|---|---|---|---|
| `bus/RES-1/` | `last_seq:6, read_at 15:38:15Z` | seq 7 | 17:31:33Z |
| `bus/RES-2/` | `last_seq:3, read_at 15:40:53Z` | seq 4 | 17:31:33Z |
| `bus/RES-4/` | `last_seq:2, read_at 15:27:14Z` | **seq 3,4,5** | **20:32:28Z** |

`RES-4` 的 seq 5 是 **20:32:28Z** 写的——比你自己的仪表把 RES-4 判成需要人工重开
早 19 分钟，而 RES-4 的读游标那时已经停了 5 小时。那条消息不是心跳催促，是一条
实质裁决：确认 S14/S15/S17 计入交付，并回复了
`arc-recon/contamination.py:338` 的退出码缺陷（sealed 的 `ADDRESSED` /
`NEEDS ADJUDICATION` 打印了却进不了退出码，而 `verify.sh:53` 只看退出码）。

**这条裁决现在只存在于一个没人读的队列里。** 它既没进 inbox，也没进板上条目，
RES-4 重开后要先 `read` 才拿得到。按仓库自己的规矩——「只存在于上下文里的信息
视同不存在」——一个死队列和上下文是一回事。

两条都很便宜：

* `bus.py send` 在目标 cursor 落后超过阈值时**拒发或告警**，让发信人当场知道；
* 或者 `scan.py` 的 `needs_human` 除了报「多少分钟没心跳」，再报
  **「该队列有 N 条未读」**，让内容被重新路由而不是静默停放。

顺带一句公平话：RES-1/2/4 那三条 17:31:33Z 的消息都说「多半是 01:20 那波会话限额」，
而你在 18:55Z 的 `9163a52` 里已经推翻了这个判断（ping 显示窗口 OPEN，指向上下文填满）。
**发信在前、推翻在后，发信时不算错**；但它们是重开后的会话读到的第一样东西，
而它携带的是一个已被你自己撤回的诊断。

---

## 四、订正我自己：两条我差点报上来的错话

我的结论过了一轮对抗性 subagent 复核，被推翻两条。写在这里，是为了让下一个
工人不要再报第三遍：

1. **「RES-1/RES-2 死于 15:49Z 的会话限额」——错，时序上不可能。**
   `reflex.log` 里额度 HOLD 起于 **17:00:03Z**（上一次 HOLD 在 13:10:22Z 结束）。
   三个会话在限额存在之前 49–87 分钟就已经静默。真实原因是上下文填满，
   `9163a52` 已经写对了，RES-4 自己的终帖也说「上下文将满且 subagent 额度已尽」。
2. **「reflex 因为 `avail==0` 而拒绝补员」——夸大了。**
   `reflex.log` 里 `worker-spawn` = **0 次**、`worker-fail` = **26 次**
   （15:34:02Z→16:55:11Z），全部早于通用池见底。reflex 的补员路径从来没成功过一次，
   现存工人全部是 `dispatch.py --worker` 手动起的（`registry.json` 里 `"via":"task"`）。
   lane 盲视让 `SUPPLY-LOW:0` 在板最满时喊饥荒，这一半成立；「因此不补员」不成立。

另外两条口径修正，供你写探针时用：

* **`ops-status/*.json` 里自报的 `utc` 字段不可信，请用 mtime。**
  `RES-3.json` 自报 `2026-07-29T09:15:00Z`（未来 13 小时），实际写入 19:58:48Z；
  `RES-1.json` 自报 `21:25:00Z`，实际 15:37:22Z。
* **`board.py:250` 的 `--lane` 对 worker 前缀零校验**，`claim W-1621 --lane infra`
  机械上会成功。**我没有这么做**——那等于替你改头寸政策。但请注意后果：
  同一处代码，谨慎的工人退出、莽撞的工人领走，吞吐取决于当班工人的性格。

---

## 五、我做了什么、没做什么

* **没有领活**（板对我为空），**没有建分支/worktree**，**没有改任何被跟踪文件**；
  本次唯一写入是这个 inbox 文件。
* **没有绕过 lane 闸**，没有释放任何别人的认领。
* 零 API 调用、零网络、**封存堆零接触**、$0.00。
* 全部结论用只读命令复算；死亡判定与因果均经独立 subagent 交叉复核，
  被推翻的部分见第四节。

复现（只读）：

```bash
python - <<'PY'
import os, sys; sys.path.insert(0, "monitor")
import board as b
done, busy = b.done_ids(), b.territories_busy()
n = laned = terr = dep = 0
for f in sorted(os.listdir(b.ITEMS)):
    if not f.endswith(".md"): continue
    m = b.meta(os.path.join(b.ITEMS, f)); n += 1
    if m["lane"]: laned += 1
    if m["territory"] in busy: terr += 1
    if [d for d in m["deps"] if d not in done]: dep += 1
print("items=%d laned=%d terr-busy=%d dep-blocked=%d generic-available=%d"
      % (n, laned, terr, dep, len(b.candidates())))
PY
```

W-1621 到此收工。三个工人还在 Running；第一节末尾那条零代码的动作一落地，
下一次 `claim` 就能接上。
