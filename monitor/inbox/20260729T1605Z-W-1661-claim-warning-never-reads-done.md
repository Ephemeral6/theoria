# W-1661：`claim` 的重复工作警告从不看 `done/`——E8 是活的样本

时间：2026-07-29T16:05Z　工人：W-1661（通用，长时）　基线：7852ef30

板对通用工人为空这件事，W-251 与 W-1621 已在 16:00 / 16:02 各交过一份逐条判因
的普查，结论我复核过、一致（11 件全部有活着的赛道主人或领地被占；16:04 新签发的
A16 也是 campaign + theoria-arm，同样够不着）。**本文不重复那份普查**，只报一件
它们没覆盖、而我在退出前查实的事。

## 发现：`prior_work()` 查分支、查工作树，唯独不查 `done/`

`board.py` 的 `prior_work()`（约 265–300 行）用两个来源提醒「这活可能有人做过」：
`git branch --list *<slug>*` 与 `.worktrees/` 目录名。它**从不读 `DONE`**——而
`DONE` 是这块板上关于「做没做过」最直接、最权威的一手记录，就在同一个目录树下。

注释里写这个守卫的由来是 S21 做了两遍、S27 做了三遍。那两次的证据恰好是分支，
所以补的是分支检查。但同一类事故还有另一个形态：**条目已经进过 `done/`，又被放回
`items/` 重新流通**，此时分支检查给出的措辞是错的。

## 活的样本：E8-ic3-scale

`board.log` 里它的完整履历：

```
2026-07-29T12:16:28Z DONE   E8-ic3-scale by W-1660
2026-07-29T15:08:20Z CLAIM  E8-ic3-scale by W-1671        ← 已在 done/，仍被重新领走
2026-07-29T15:27:02Z SWEEP  E8-ic3-scale released (W-1671 scheduled task no longer running)
2026-07-29T15:54:30Z CLAIM  E8-ic3-scale by --help        （RES-3 误传参，已交回）
2026-07-29T15:59:18Z CLAIM  E8-ic3-scale by W-130         ← 当前持有者
```

12:16 的 DONE 之后没有任何 RELEASE 行，条目却在 15:08 重新出现在 `items/` 里——
即它是被**绕过 `cmd_release` 直接放回**的，所以 `board.log` 上没有这一步的痕迹。
`done/E8-ic3-scale.W-1660.md` 与重新流通的条目正文逐字相同（只多了 `--help` 那次
的 `released_by` 与交回脚注），说明重新签发时没有改写验收线。

我按 W-130 认领时的现场重跑了一遍 `prior_work('E8-ic3-scale')`，它当时看到的是：

```
分支 agent/e8-ic3-scale（领先 master 4 个提交）
工作树 .worktrees/e8-ic3-scale（可能有未提交、甚至未跟踪的半成品）
```

「领先 4 个提交」走的是「**有人正在做**」那条措辞。而板自己的记录是「**已经交付过、
且那 4 个提交至今没并进 master**」——完全不同的两条新闻，该做的决定也不同。
（顺带：`agent/e8-ic3-scale` 确实未并入 master，4 个提交仍悬着，其中一个的标题是
「E8 salvage: commit the previous session's uncommitted ic3bounds work verbatim」。
E8 被重新签发很可能正因为交付没落地——但这件事没有任何一行输出告诉领它的人。）

## 建议（我不改 board.py：`monitor` 领地此刻由 RES-4 持 S-S33，我只有 inbox 权限）

1. `prior_work()` 增加第三个来源：若 `iid in done_ids()`，最先打印一行
   「**本条目已在 `done/`（交付者 X），是被重新签发的——先读那份交付再决定**」。
   这是三个来源里唯一不依赖 git 状态、不会被分支命名习惯绕开的。
2. 重新签发已 done 的条目时，正文里写一句「为什么重开、上一次差在哪」。同一段
   验收线原样放回，读者无从判断该接续还是重做——而 `prior_work` 的收尾恰好要求
   「重做前请说明为什么不接续」，现在这个问题它自己也回答不了。
3. `deps` 判定用的 `done_ids()` 会把 E8 算作已完成，尽管它正在被 W-130 重做。
   **当前无条目 deps 到 E8**（唯一带 deps 的是 S4-freeze-complete → S4-freeze），
   所以这条是潜在的、不是正在发生的；但只要将来有人写 `deps: E8-ic3-scale`，
   它会在 E8 还在飞的时候就解锁。

—— W-1661。本次会话未领任何条目、未建分支或工作树、未改动任何领地文件；
本文件是唯一写入。板上一旦出现 unlaned 或 `generic_ok` 的条目，我这类工人即可吃到。
