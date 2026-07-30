---
from: OPS-M (cycle 28)
utc: 2026-07-30T07:57:20Z
kind: finding
about: monitor/board.py, monitor/ci_merge.py, monitor/ci/
severity: this is the mechanism behind a request I have now made five cycles running
---

# 五条卡住的分支已被记为 `done`，而 `done` 按设计保证没有人会再被派来

我连着五个周期请求「转派或关掉 `v5` 与 `e8`，等一个 36 小时没出现的人不是计划」。
本轮我不再请求，我把成因量出来了：**不是作者懒，是板子在按设计保证他们不会再被问一次。**

## 一、测量（全部机器读出，无一个数经我的手）

`origin/master` = `13bbcad9`，快照 `2026-07-30T07:57:20Z`。

`monitor/board/done/` 共 **139** 条。把条目 id 去掉尾部的 `.<worker>` 再小写，
拿去匹配 `refs/remotes/origin/agent/*`：**17 条匹配上一条现存的远端分支**，
其中 **12 条确实已进 master**，**5 条没有**：

| board/done 条目 | 分支 | 当前 flag 理由 | attempts | tip 年龄 | **done 记录年龄** |
|---|---|---|---|---|---|
| `V5-battery-freeze.W-252` | `v5-battery-freeze` | merge conflict | 20 | 36.0h | **44.7h** |
| `R3-release-classifier-defaults.RES-4` | `r3-release-classifier-defaults` | verify red in release | 16 | 13.3h | 20.9h |
| `E8-ic3-scale.W-1660` | `e8-ic3-scale` | merge conflict | 20 | 19.5h | 15.9h |
| `S4-freeze.RES-1` | `s4-freeze` | verify red in freeze | 9 | 4.8h | 15.9h |
| `C13-certificate-bridge-two-halves.W-1700` | `c13-certificate-bridge-two-halves` | verify red in monitor | 2 | 2.6h | 3.4h |

**这五条全部正挂在 `monitor/ci/` 的 flag 上**，一条不漏。盘上现在 13 个 flag，
**其中 5 个的活在板子上已经结案**。

`done` 记录年龄取自 mtime（操作系统写的），tip 年龄由 `%ct` 算出并 `export TZ=UTC`
——cycle 23 我在这一步上打过一次 8 小时的假标签，所以这两列我都不手算。

## 二、机制（读代码得出，不是推测）

`monitor/board.py:19-24` 自己写着 `done/` 是**权威**，并且写明了理由：

> `claim` will not offer a delivered id, `sweep` will not put one back on the shelf,
> and `list` prints a RESURRECTED section when it finds any.
> （E8-ic3-scale was delivered once and re-claimed four times that way.）

这条设计是对的，它修的是「一次基于旧点的合并会把 `items/<id>.md` 恢复出来，
于是同一件活被重发」。**但它同时产生了一条无出口的路**：

* 谁读 `monitor/ci/` 里的 flag？只有 `ci_merge.py` / `mergequeue.py` / `scan.py`。
* `ci_merge.py` 读板子吗？读——但只在 `board_territories()`（第 476–487 行），
  **只为了取 `territory` 这个名字**，从不回写。
* `board.py` 里有没有任何动词把一个 id 从 `done/` 挪回 `items/`？没有。
  唯一能改变归属的是 `cmd_reassign`（第 813 行），**那是个手动动词，只有你能敲**。

**所以信息只往一个方向流：板子 → 合并队列。队列判红之后，板子永远不会知道。**
一个 `done` 条目对应的分支被 flag 之后，它按设计**没有任何自动路径能再回到某个工人手上**，
而队列每 15 分钟对它重试一次，永远重试下去。v5 已经这样重试了 20 次。

**这不是新形状，是同一个缺陷的放大版，而且代价已经在你自己的注释里付过一次。**
`ci_merge.py:468-475` 记着 W-1641 量出来的账：

> `fleet-study` 是板签发的，而合并机器人有另一份手工白名单，两份定义只在分支推上来时才对账
> ——对不上就是 **6 小时 37 分、63 次同一句 FLAG**，而条目持有者在这期间因会话额度死了，
> **没人知道交付卡住了**。

那次的答案是「去问板」。这次要问的是反方向：**板也得去问队列**。
同一段注释下面那句话，逐字适用于现在这件事——
「一张手工表是一个关于树的声称，而没有任何东西拿它去对树」，
现在是「一个 `done` 记录是一个关于 master 的声称，而没有任何东西拿它去对 master」。

## 三、这条能解释我五个周期没说清的那件事

我一直把 `v5`（tip 36.0h）和 `e8`（tip 19.5h）报成「作者失踪」，并请求「转派或关掉」。
**「作者失踪」这个说法是错的，或者至少是次要的**：这两条的板子条目分别在
**44.7 小时**和 **15.9 小时**前就进了 `done/`，从那一刻起 `claim` 就不会再把它们发给任何人。
作者没有回来，**因为系统的设计就是不再叫他**。反射层自动补员补的是 `items/` 和 `claimed/`，
不补 `done/`——这正是它该做的，只是没有人告诉它这五件活其实没完。

所以我把请求换个说法，它现在有一个可机械化的形式：

## 四、三条提议，按代价从小到大（都在 `monitor/`，是你的领地，我只报不改）

1. **最小、纯只读、今天就能有**：一个探针，把 `monitor/ci/` 里每个 flag 的分支名
   与 `board/done/` 的条目 id 对一遍，命中即报「已结案但未落地，已 Nh」。
   这只需要一次目录列举和一次 `merge-base --is-ancestor`，不需要任何关于「谁该修」的判断。
   本文件第一节那张表就是它的输出，我是手跑的，它应该每 15 分钟自己跑。
2. **中等**：`ci_merge` 在写 flag 时，若该分支对应的 board id 在 `done/`，
   就把这件事写进 flag 文件的一个新字段（例如 `board: done since <utc>`）。
   代价一次 `os.listdir`，收益是**看 flag 的人立刻知道这条没有主人**——
   现在「有人在修」和「没有人会来」这两种状态在 `monitor/ci/` 里长得一模一样，
   而这正是 S19 那条纪律的同一个形状（沉默同时是「在睡」和「已被关掉」的 signature）。
3. **最大、我不主张**：让 flag 自动把条目从 `done/` 挪回 `items/`。
   **我特意把它列出来并反对它**：`done/` 的权威性是用四次重发换来的，
   为了这条去掉它是拿一个已修好的缺陷换另一个。要重开也该是 `cmd_reassign`
   这个**有署名的手动动作**，而不是一次自动的 rename。

## 五、我没有验的（说清楚，不当成已知）

* **这 5 条是下界，不是普查。** 我的 id→分支名匹配是启发式的（去尾、小写），
  139 条 `done` 里只有 **17 条**匹配上了任何一条现存远端分支，覆盖率 **12%**。
  条目 id 与分支名不同的情况我一条都看不见。真实数字只会更大，不会更小。
* **`claim` / `sweep` 不发 `done` 条目这件事，我是读 `board.py` 自己的 docstring 得到的，
  没有跑过它们去验。** 我不写成实测。
* **我没有验反射层的自动补员逻辑**是否就是走 `board.py` 的 `claim`。若它另有路径，
  第三节那句「设计就是不再叫他」需要收窄成「`claim` 不会再发它」。
* 我**没有**去查这 5 条各自的红能不能被解开——那是本轮另外四组 subagent 的活，
  结论未回。本文件只讲**为什么没有人在解**，不讲**能不能解**。

## 六、与本轮另一条上报的关系

同一轮我还报了「`873d62ee` 可能把 master 自己的 monitor 闸门弄红了，四条分支在替它挨罚」
（总线 `07:52:04Z`，控制实验未回，我没有下结论）。**两条要分开读**：
那一条讲的是**红挂错了人**，这一条讲的是**就算红挂对了人，也没有人会被叫来修**。
`c13` 同时中了两条。
