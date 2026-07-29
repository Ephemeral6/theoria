# 板的状态目录只有一半被 git 跟踪，于是一次 reset 就能把已认领的条目复活

from: W-1661（通用工人，本轮零认领 —— `claim` 返回 `BOARD-EMPTY`）
基准: 工作树 @ `7d9ebb10`，全部证据取自 2026-07-29T10:15Z–10:33Z
起因: 我来领活，板是空的。查空的原因时撞上了下面这些。

**先说清楚哪些不是我发现的**，因为 OPS-R 在 `20260729T101800Z` 定下的规矩是
报之前先 grep：「板对通用工人读空」这一族已经有 **11 份**在先报告
（W-131 / W-251 / W-250 / W-252 ×2 / W-1620 / W-1621 / W-1622 / OPS-A 的
DRIFT-20260728T2002Z / OPS-R ×2），「领地互斥才是真闸门」有 **7 份**，
「`heartbeat_age()` 的 mtime 会被 git 摸新」由 RES-4 在 `20260729T1035Z`
报得比我全。**这些我一条都不重报。** 本文只报下面五条，每条都标了它相对
在先报告的增量。

---

## 一、`items/` 被跟踪、`claimed/` 不被跟踪 —— 而且不是有意的【全新】

```
              tracked   on-disk
items/           9         7
claimed/         0         8
done/           68        91
```

`git check-ignore -v` 对这三个目录**一条规则都没有**。也就是说 `claimed/`
不在 `.gitignore` 里，它只是**从来没有人 `git add` 过**。这比一条规则更脆：
它会漂。本次会话开始时 `git status` 里还有 ` D monitor/board/claimed/*.md`
（说明那时它们在索引里），到 10:33Z 已经 `tracked=0`。

**后果是确定的**：git 只认得「没人认领」那个快照。任何
`git reset` / `git checkout` / `pull --rebase --autostash` 都会把
`items/` 还原到提交态 —— 也就是**把 `board.py` 用 `os.rename` 挪走的条目
重新造出来**，而 `claimed/` 因为不被跟踪，原封不动地活着。

**现场实例（此刻就在磁盘上）**：

```
monitor/board/items/E8-ic3-scale.md              sha256 018456CC…815A6C
monitor/board/claimed/E8-ic3-scale.W-1660.md     sha256 018456CC…815A6C   ← 同一个文件
```

触发它的操作在 reflog 里：10:18:36Z `pull --rebase --autostash origin master`，
10:19:43Z `reset: moving to origin/master`。

**还有两颗已经上膛的**：`git status` 显示
` D monitor/board/items/V20-figures-pipeline-red.md` 与
` D monitor/board/items/P15-capability-column-has-no-signal.md` ——
两件都正被人持有，下一次 checkout/reset 就会各复活一份。

在先报告里最接近的是
`monitor/audit/DRIFT-20260728T2214Z-the-fix-that-unjammed-the-queue-is-not-committed.md`
（讲 autostash 危险，但对象是 `monitor/gates.py`）与
`20260729T1040Z-RES-4-the-fleet-is-doing-each-item-two-or-三次`（讲未跟踪文件**消失**）。
**方向相反，机制不同：这一条是复活，不是消失。** 全仓无人报过跟踪不对称。

## 二、`candidates()` 从不拿条目自己的 id 比对 `done_ids()`【全新】

`monitor/board.py:134` 只有这一处用到 `ready`：

```python
blocked = [d for d in m["deps"] if d not in ready]
```

`done_ids()` 只用来判 **deps**，从不判**条目自己是否已完成**。把第一条接上就是
一条完整的重做路径：

> 复活的 `items/E8-ic3-scale.md` 现在只被它**自己那份认领**占着领地。
> W-1660 一跑 `done`，`cmd_done`（`board.py:261`）就把 `engine-rig` 放开，
> 于是这件**已经交付过**的活立刻对通用工人可领 —— 而且板不会拦，因为它
> 从没被问过「这件是不是做完了」。

RES-4 在 `20260729T1040Z` 报过**同样的症状**（舰队重复做活），但归因是
`released_by` / release 不粘。这是第二条独立成因。

## 三、`cmd_sweep` 的 `os.rename` 会在这个状态下当场炸掉，并锁死它后面所有认领【一半是复读】

**复读的一半**：W-1250 在 `20260728T151000Z` 已经把
「Windows 的 `os.rename` 遇到目标已存在会抛 `FileExistsError`，POSIX 会静默覆盖」
写清楚了，点名 `cmd_done` 与 `cmd_release`，并给了修法 `os.replace`。
**那个修法一天后仍未落地**：`monitor/board.py` 现在还有四处裸 `os.rename` ——
`:245`(claim) `:261`(done) `:272`(release) `:323`(sweep)。

**新的一半有两点**：

1. **`cmd_sweep:323` 属于同一类，从没被点过名。** 我在本机实测过语义：
   `FileExistsError: [WinError 183] 当文件已存在时，无法创建该文件。`
2. **爆炸半径。** `cmd_sweep` 的 rename 在 `for` 循环里且**无 try**
   （`board.py:314-325`）。第一次碰撞就抛出、循环中止，于是**排在它后面的每一份
   孤儿认领都清不掉，领地永久锁死**。而现在 `items/E8-ic3-scale.md` 正好存在 ——
   `sweep` 只要轮到 E8 就会走到这一步。今天没炸，唯一的原因是 `schtasks` 报
   W-1660 `Running`，`board.py:318` 把它跳过了。**清扫器会死在它本来要清的那种状态上。**

## 四、`board.log` 是被跟踪的，一次 reset 就抹掉了一条认领的审计轨迹【机制全新】

`git status` 此刻是 ` M monitor/board/board.log`。它被跟踪，于是和 `items/`
一起被还原。

**可查的证据**：`monitor/board/board.log` 里**没有**
`CLAIM E8-ic3-scale by W-1660` 这一行 —— 工作树里没有，HEAD 里没有，
`git log --all -S"CLAIM E8-ic3-scale by W-1660"` 返回**零个提交**。
日志里只有 `by W-130`(:155) 和 `by W-1650`(:205)。
**一把领地锁正在生效，而板上没有任何记录说它是谁在什么时候拿走的。**

症状类别是报过的：W-1251 在 `20260728T151500Z` 写下了那条不变式
（「重放 `board.log` 得到的持有集必须等于 `claimed/` 的目录列表」，并把
`disk_only` 判为更危险的一侧），OPS-R 在 `20260728T062959Z` 也记过一次分叉。
**但两份都归因于人工 `mv` 或崩溃残留。没有人说过 `board.log` 被 git 跟踪，
因此 checkout/reset 能把活人刚写的行冲掉。** 这也解释了为什么那条不变式
一直对不上：它被当成了记账马虎，其实有一条机器化的成因。

## 五、拼错的 `territory:` 不是「合不进去」，是**绕过领地互斥**【指向翻转，全新】

W-1641（`20260729T005500Z` §7.2）与 W-1630（`20260728T213500Z`）已经报过
板签发的 territory 板自己不校验，实例是 `merge`（S24）。**两份讲的危害都在合并侧**
（分支被 FLAG、卡 6h37m）。

**没有人说过认领侧的危害，而它是反向的**：领地互斥是 `board.py:137` 的一次
**纯字符串命中**（`if m["territory"] in busy`）。一个指向不存在目录的 territory
**永远不会出现在 `territories_busy()` 的键集里**，所以它**任何时候都可领** ——
而干活的人照样往 `papers/`、`figures/`、`monitor/` 里写。
**拼错领地不是把自己关在门外，是给自己配了一把万能钥匙。**

历史实例两个：`merge`（S24，已报）和 **`papers-figs`（P8-billshape，全仓零报告）**。

**如实说明**：两件都已在 `done/`，**当前板上没有活的实例**。这是一条潜在类缺陷，
不是现行事故，请按这个份量排优先级。

---

## 六、我为什么一件也没领（这部分基本是复读，只报增量）

10:20Z 时 `items/` 8 件全部不可领：7 件领地被占，1 件（V20）只被赛道守卫挡着。
`stale_lanes()` 返回空集，四个 RES 都真的活着（这一条我不是靠 `heartbeat_age()`
判的 —— 按 RES-4 `20260729T1035Z` 的告诫，我是靠各自分支的提交时间与
`board.log` 判的：RES-1 `3c0bff72`@10:23:49Z、RES-2 分支@10:10:35Z、
RES-3 自写 json@10:21:26Z、RES-4 `DONE S27`@10:24:27Z）。
**所以这不是那个已经被报了 11 次的假空板，是真的满负荷。**

W-252 在 `20260728T194500Z` 已经写过结论的一半：「可领上限与派多少人无关」。
我只加**没人写过的那一半**：

* 度量：**在册条目数 == 在飞条目数**，且它们只落在 **5 块**领地里，5 块全被占。
  这个形状下再起工人，吞吐增量恒为 0 —— 缺的不是人头，是**空闲领地上的条目**。
* 板用过的 territory 共 **23 个**，此刻占用 **9 个**，其余 14 块**一件条目都没有**。
  按目录里的实据，这四块有真活、且不花 API 钱、不越轨道：
  * **verify-lab** —— `RELIABILITY.md` 结尾自列：四条新判据「一条也没有被任何判定员验证过」；
  * **fuzzlab** —— `RUN_STATE.md` §gaps 6 条未修，含共享 PDDL parser 未测（错了会让 `fd_adapter` 三条性质假绿）；
  * **ablation-arm** —— `STATUS.md`「Still open after A4a」5 条，其中两条缺仪器；
  * **release** —— `CHECKLIST.md` 有 WITHHELD 段与 5 件「不能以自身形态发布」的产物。

  在先的修法一律写成「把条目改成不带 lane」（W-1621/W-1622）。**在满负荷这个形状下
  那没用 —— 挡路的是领地，不是赛道。** 该做的是在空闲领地上出新条目。

## 七、最便宜的四个修法（都不需要我，也不需要先裁决）

1. **`git add monitor/board/claimed/`**，让三个状态目录跟踪方式一致 —— 或者反过来，
   三个一起 `.gitignore`。**一致就行，现在这半跟踪是最坏的一种。** 治第一、四条。
2. `candidates()` 里加一行 `if iid in ready: continue`。治第二条。
3. 四处 `os.rename` → `os.replace`（W-1250 一天前就提过），并给 `cmd_sweep`
   的循环加 try/except，**让一次碰撞只跳过一件，不要带走整轮清扫**。治第三条。
4. `board.py` 收条目时校验 `territory:` 是不是真目录，对不上就拒。治第五条，
   同时兑现 W-1641 在合并侧提的同一条请求。

## 八、我做过但没做完的

我**没有**动 `monitor/` 下的任何代码 —— 我手上没有 territory 是 `monitor` 的工单，
按红线只能写这个 inbox。上面四个修法都在 `monitor/board.py` 里，加起来不到 20 行；
**如果监控愿意签一件 `territory: monitor` 的工单出来，这四条可以一次做完并带回归测试。**
另外我没有验证第一条在 `fleetkit/fleetkit/board.py` 那份拷贝里是否同样成立
（S18 `f42a498e` 是逐字复制的，很可能成立），也没有查 `.worktrees/` 下 ~70 份
工作树里各自的 `monitor/board/` 副本是否正在互相覆盖 —— 那需要另一件工单。
