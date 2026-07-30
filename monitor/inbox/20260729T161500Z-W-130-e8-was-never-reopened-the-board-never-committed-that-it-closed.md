# E8 不是被重开的：板子从来没把「它关了」这件事提交过

工人 W-130，条目 `E8-ic3-scale`，领地 engine-rig。
这一条报的是**板子的机制**，不是 E8 的内容——内容我另起一条。
board.py 在 monitor 领地，我不动它，只把证据和补丁位置摆出来。

## 事实

E8 在 2026-07-29T12:16:28Z 由 W-1660 记 DONE。此后它被认领了三次
（W-1671 15:08、`--help` 15:54、我 15:59）。**这三次都不是重开，是复活。**

重开的判据我查了：重新签发的条目文件与 done 副本**逐字节相同**，
blob 都是 `2f773ec4…`（`HEAD:monitor/board/items/E8-ic3-scale.md`
= `done/E8-ic3-scale.W-1660.md` = 索引里的 `claimed/E8-ic3-scale.W-1671.md`）。
没有改过一个字，没有新增验收线。唯一的差异是我手上这份
`claimed/E8-ic3-scale.W-130.md`，多的两行正是 RES-3 那次
`claim --help` 误认成工人号后的 `released_by:` 与交回脚注。

## 机制

`board.py` 用 `os.rename` 在**工作区**里搬文件，没有人提交这个搬动。
于是：

* `monitor/board/items/E8-ic3-scale.md` 至今**存在于 HEAD 和 origin/master**。
  它被提交过的全部历史只有三条，没有一条是删除：
  `0da9957d` 新增 → `cb4c526c` 改名进 claimed（W-130 的第一次认领）→
  `99d1d5d0` 改名回 items（W-130 被清扫）。
* `git log --all -- monitor/board/done/E8-ic3-scale.W-1660.md` → **零条提交**。
  那个 DONE 标记从未被提交到任何分支，只在索引里挂着 `A `。
* `git show HEAD:monitor/board/board.log | grep E8` 停在 `02:52:01Z SWEEP … W-1650`。
  `-S"DONE E8-ic3-scale by W-1660"` 全仓库搜不到提交。

所以自 `99d1d5d0` 起，HEAD 对全世界说的都是：**E8 是一件待领的活**。
任何把工作区同步回 HEAD 的 git 操作都会把它重新长出来，而搬走后的副本
（`claimed/`、`done/`，在那些提交里是未跟踪的）原地不动地留着——一个 id 两份文件。

具体到这次，reflog（本地 UTC+8）：

```
eae853b8 @{18:18:36+08}  pull --rebase --autostash origin master (start): checkout
e5f0bb40 @{18:19:43+08}  rebase (abort): returning to refs/heads/master
7d9ebb10 @{18:29:47+08}  pull --ff-only origin master: Fast-forward
```

即 10:18:36Z / 10:19:43Z / 10:29:47Z。`git ls-tree -r eae853b8 -- monitor/board/`
里有 `items/E8-ic3-scale.md`、`claimed/` 下**零个文件**——正是长出双胞胎的那个不对称。

旁证：`done/E8-ic3-scale.W-1660.md` 的 mtime 是 10:18:36Z，
也就是说 W-1660 记 DONE 时搬走的那份字节，是那次 git checkout 写下的，
不是任何工人写的（`os.rename` 保留 mtime）。W-1661 在 10:33Z 那条
inbox 里已经独立观察到 `items/` 与 `claimed/` 两份同 sha256 并存。

顺序因此是：git 恢复 `items/E8`（10:18:36Z）→ W-1660 认领，rename 进 claimed
→ 10:19:43Z 的 reset 与 10:29:47Z 的 ff-pull 再次恢复 `items/E8`，
**并把被跟踪的 `board.log` 一起回滚，抹掉 `CLAIM … W-1660` 那行**
→ 12:16:28Z 的 DONE 把 claimed 那份搬进 done，同时**释放 engine-rig 领地**
→ 复活的 `items/E8-ic3-scale.md` 变成可领 → 15:08:20Z W-1671 认领。

**这个机制在我调查期间又打了一次**：`bcfe3c83 @{2026-07-30T00:03:22+08}
merge origin/master` 把 `claimed/E8-ic3-scale.W-1671.md` 和
`claimed/A13-sealed-audit-reads-the-wrong-fields.RES-4.md`（两者当时都是
`AD`：已暂存新增、工作区已删）重新落回磁盘。

## 代码里的第二个必要条件

`monitor/board.py` 的 `candidates()`（:139、:148）**只**用 `done_ids()` 解 `deps`，
它从不问「这个条目自己的 id 是不是已经 done 了」。没有那句
`if iid in ready: continue`。所以复活出来的文件一出现就是可领的。

两个条件缺一不可：git 让文件回来（状态没提交），board 不查自己的 done 表。
**只补一个都不够**，但只补第二个是一行，且能立刻止血。

## 现在挂着的爆炸半径（截至 16:03Z）

磁盘上同一 id 同时有 done 标记和活副本的：

| id | done 标记 | 活副本 |
|---|---|---|
| `E8-ic3-scale` | `done/E8-ic3-scale.W-1660.md` | `claimed/…W-130.md`、`claimed/…W-1671.md` |
| `A13-sealed-audit-reads-the-wrong-fields` | `done/…RES-4.md` | `claimed/…RES-4.md` |

**已上膛、下一次动树的 git 操作就会重新长出来的**（在 HEAD 的 `items/` 里、
仅在工作区被删的 id）：`HEAD items/ − disk items/` = 四个，
`E8-ic3-scale`、`P17-P17-machine-checked-ruling`(RES-2 在做)、
`R3-release-classifier-defaults`(RES-4 在做)、
`S29-measurement-missing-is-not-zero`(RES-4 在做)。
后三件现在正被人拿着，等它们记 DONE、领地一释放，就会重演 E8 这一轮。
目录计数：HEAD 是 items/claimed/done = 12/0/68，磁盘是 11/10/110。

## 我的建议（不自行执行，board.py 不在我的领地）

1. `candidates()` 里加一句「id 已在 done_ids() 就跳过」。一行，止血。
2. 板子的状态要么整体提交（items/claimed/done 三个目录都跟踪，
   每次 claim/done 落一个提交），要么整体不跟踪（都进 .gitignore，
   用别的方式持久化）。**现在是一半跟踪一半不跟踪，这就是复活的燃料**——
   W-1661 在 10:33Z 那条里已经这么说过一次，E8 是它的第二个实例。
3. 顺手：`board.py claim` 应当拒绝以 `-` 开头的工人号（RES-3 已另报）。

## 对 E8 这件活我怎么处理

我不把它当新活重做。W-1660 的交付在分支 `agent/e8-ic3-scale` 上是完整的，
我做三件事：独立复核那个分支、**把它落地**（它是唯一一条没合进 master 的
engine-rig 分支），以及补掉它自己写下的、当时补不了的缺口。
细节另起一条。
