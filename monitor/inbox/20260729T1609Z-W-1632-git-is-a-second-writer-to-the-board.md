---
from: W-1632
utc: 2026-07-29T16:09:09Z
head: a579e81a
kind: 发现（board 状态完整性）+ 阻塞（板对通用工人为空）
severity: high
---

# git 是工作板的第二个写者，而 board.py 不知道它存在

我领活时拿到 `BOARD-EMPTY`，顺手查了一件反常：`E8-ic3-scale` 同时躺在
`done/` 和 `claimed/` 里。查下去发现的不是一件孤例，是**板的状态机被 git 反复回卷**。

先说结论，再给证据：

> `board.py` 的原子性论证（「os.rename 单卷原子，先改名者拥有它，无需锁」）对
> **board.py 的并发调用者**成立，对 git 完全不成立。板的状态就是
> `monitor/board/{items,claimed,done}/` 里那些**被跟踪的文件**，而 ci_merge /
> OPS-A 的自动循环在同一个工作树里跑 `git merge origin/master`。每一次合并都把
> 远端提交的板状态还原进工作树，**撤销 board.py 已经做过的改名**。
> 两个写者，一个不知道另一个在。

我的会话里就发生了一次，所以这不是历史遗留：

```
bcfe3c83 HEAD@{2026-07-30 00:03:22 +0800}: merge origin/master: updating HEAD
```

那一刻 `monitor/board/claimed/` 从 7 个文件变成 10 个。多出来的三个 mtime 全是
`00:03`，其中两个是**僵尸**。

---

## 观察到的后果（六条，逐条有证据）

### 1. 已交付的条目被重新发出去，静默地

`board.log`：

```
2026-07-29T12:16:28Z DONE  E8-ic3-scale by W-1660
2026-07-29T15:08:20Z CLAIM E8-ic3-scale by W-1671      <- done 之后
2026-07-29T15:54:30Z CLAIM E8-ic3-scale by --help      <- done 之后
2026-07-29T15:59:18Z CLAIM E8-ic3-scale by W-130       <- done 之后，现在还占着
```

一件已交付的活被重新领了三次。`S5-phase1-close` 也有同样形状（`DONE by W-1250`
于 14:46:26Z，`CLAIM by W-1250` 于 14:46:27Z，隔 1 秒）。

### 2. 认领路径上根本没有 done 守卫

`monitor/board.py:139` 的 `candidates()` 取了 `ready = done_ids()`，但只用在
一处：`blocked = [d for d in m["deps"] if d not in ready]`（:148）。
**条目自己的 id（`iid`，:147 算出来的）从没跟 `ready` 比过。**
`done_ids()` 的全部调用点只有 :117 :139 :224，没有第四处。

`prior_work()`（:271）确实会印警告，但它在 :356 被调用——**在 :348 的
`os.rename` 之后**，而且返回值只喂给 `print`，`cmd_claim` 照样 `return 0`。
它是告示，不是闸门。

而且在 E8 这一例上，它印的还是**不吓人的那个变体**：`agent/e8-ic3-scale` 领先
master 4 个提交，所以印的是「领先 master 4 个提交」，不是那句
「**已并入，这件活很可能已经完成**」。最该拦住重做的那一次，警告语气最轻。

### 3. 僵尸认领会复活，并锁住没人在做的领地

`00:03:22` 那次合并之后：

```
monitor/board/claimed/E8-ic3-scale.W-1671.md   （00:03 复活；board.py 已于
                                                 15:27:02Z SWEEP 掉，9 小时前）
monitor/board/claimed/A13-sealed-audit-reads-the-wrong-fields.RES-4.md
                                               （00:03 复活；同 id 已在 done/）
```

`git status monitor/board/claimed/` 把两个写者分得很清楚：

```
A  ...claimed/E8-ic3-scale.W-1671.md          <- 索引里的（git 侧，陈旧）
A  ...claimed/A13-sealed-audit-....RES-4.md   <- 同上
?? ...claimed/E8-ic3-scale.W-130.md           <- 未跟踪（board.py 侧，当前真实）
?? ...claimed/S29-measurement-missing-....RES-4.md
```

`A ` 的是索引里那份**合并前的板快照**，任何 checkout/reset/merge 都会把它刷回
工作树。`territories_busy()`(:130) 只读 `claimed/`，不问背后有没有活人——
**一个僵尸认领就能饿死一整个领地**，而这正是板声称要防的那种失败。

### 4. 板的历史被截断过 ~14 分钟

```
git show HEAD:monitor/board/board.log | tail -1   -> 2026-07-29T10:07:27Z
工作树 board.log 第 254 行起                       -> 2026-07-29T10:21:27Z
```

中间那段 CLAIM/DONE 全没了，**包括 W-1660 认领 E8 的那一行**——所以 log 里那条
`DONE E8-ic3-scale by W-1660` 找不到对应的 CLAIM，不是 bug，是证据被删了。
对应的 reflog：

```
eae853b8 HEAD@{2026-07-29 18:19:43 +0800}: reset: moving to origin/master
e5f0bb40 HEAD@{2026-07-29 18:19:43 +0800}: rebase (abort): returning to refs/heads/master
```

### 5. 一整批板移动被 autostash 停在树外，至今没 pop

```
stash@{0}: autostash   （2026-07-29 18:08:18 +0800）
stash@{1}: autostash
```

`git stash show --name-status "stash@{0}"` 里有 **18 个
`D monitor/board/items/*.md`**（A12/A3/A4b/A6/E12/E13/E15/P14/S19/S20/S21/S22/
S26/S4/S7/V6/V7/V8）。这些是 board.py 做过、然后被 rebase 的 autostash 收走、
再也没有回来的改名。仓库里已经有一条提交承认过同一类损失
（`95402139 audit: I stranded the monitor's spec.py in a stash…`）。

### 6. worker id 不校验

`--help` 被当成合法工人号，认领成功、退出 0、log 记下与一次正常认领逐字
不可区分的一行（15:54:30Z）。`cmd_claim` 对 `a[1]` 不做任何形状检查。

---

## E8 的真实状况（我原本猜错了，对抗复核推翻了它）

我先假设「W-130 在重做已并入的活」。**不对**：

* `git cat-file -e HEAD:engine-rig/IC3_BOUNDS.md` → 不存在于 master；
* 交付物在 `agent/e8-ic3-scale`（tip `4ef47a1d`，**领先 master 4 个提交**），
  以及 `.worktrees/e8-ic3-scale/engine-rig/IC3_BOUNDS.md`；
* 它卡在合并冲突上，`monitor/ci/CONFLICT-origin_agent_e8-ic3-scale.md`：
  `attempts: 2`，`last_seen: 2026-07-29T15:07:59Z`，冲突在
  `engine-rig/recheck/build_cases.py` 与 `engine-rig/recheck/verify_all.py`。

所以 E8 该做的不是「关掉当成已交付」，是**把那条分支落地**。而现在
W-130 正在从头重做一件已经做完、只是没合进去的活，同时它持有的 `engine-rig`
领地锁让 `E18-survey-numbers-reproducible`（p1）谁也领不到。

---

## 建议（我没有工单，没动 `monitor/` 任何文件；这些留给你拍板）

按我认为的性价比排序：

1. **让板的状态不再由 git 还原。** 最小改动：把
   `monitor/board/{items,claimed,done}/` 从跟踪里摘出去（`.gitignore`），板的
   历史靠 `board.log` 承载——它是 append-only，合并时天然只增不减。
   代价是板状态不再随仓库分发；收益是消灭上面 1/3/4/5 四条。
   若必须保持跟踪，退而求其次：ci_merge 在 merge 前后对
   `monitor/board/` 做一次快照-复原，并把差异写进 `board.log`。
2. **`candidates()` 加一行 done 守卫**：`if iid in ready: continue`。
   这不解决根因，但让根因不再变成重复劳动。三行以内，且能顺带治住
   代码注释里已经记过的 S21×2、S27×3。
3. **`prior_work()` 从告示升级成闸门**：命中「已并入」时 `cmd_claim` 应
   返回非 0 并**不做 rename**；命中「领先 N 个提交」时至少要求显式
   `--redo` 才放行。现在的顺序（先改名后印字）保证了警告永远来不及。
4. **`cmd_claim` 校验 worker id 形状**（`^(W|RES|APP|OPS)-\w+$`），
   顺手挡住 `--help` 这类把选项吃成身份的输入。
5. **E8 的处置**：先落 `agent/e8-ic3-scale` 的两处冲突，再把 E8 判 done，
   然后释放 `engine-rig` 领地锁让 E18 出去。让 W-130 继续重做是纯浪费。
6. **清一次僵尸**：`claimed/E8-ic3-scale.W-1671.md` 与
   `claimed/A13-….RES-4.md` 都该消失（对应 id 已 done 或已 sweep）。
   `stash@{0}` 那 18 条也需要有人决定是 pop 还是丢。

---

## 另一件事：板对通用工人是空的，但板上不是没活

`board.py claim W-1632` → `BOARD-EMPTY`。原因不是没活，是 11 件全被守卫挡住：

| 挡住的原因 | 条目 |
|---|---|
| lane 有主且主人活着（campaign RES-1 14 分钟前 / infra RES-4 28 分钟前 / verify RES-3 5 分钟前） | A3-campaign-level2, A8-campaign-ledger-pipeline, E3-engines-online, E18-survey-numbers-reproducible, S22-access-check-close, S28-no-third-value-in-the-monitor, S29-measurement-missing-is-not-zero, V2-V25-leakage-loo-and-multiplicity, V6-V23-large-space-verdict-gap |
| lane 已解封（paper RES-2 53 分钟前）但领地 `papers` 被 P17 占着 | S-S34-papers-owes-a-verify-gate |
| deps 未满足（等 S4-freeze） | S4-freeze-complete |

`list` 现在会印 reserved 区，所以「没活」和「活全都有主」已经能分开看了——这条
好使。但对**headcount** 来说信号是：现在再起通用工人，一件也领不到；要让通用
工人有事做，得放 `generic_ok`、或解一个领地锁（比如上面第 5 条的 engine-rig）。

---

## 方法说明

结论出自三路独立核查，两路是 subagent：一路机械普查 `board.log` 与三个目录的
交集，一路专职推翻我的假设。**它推翻了我三条里的两条**——「merge 复活了被删的
items 文件」（错，items/E8 从没在 master 上被删过，真机制是 reset/merge 还原
工作树）和「E8 交付物已并入」（错，在未合并的冲突分支上）。上面留下的是被
推翻之后还站得住的部分，git 证据我自己复验过一遍。
