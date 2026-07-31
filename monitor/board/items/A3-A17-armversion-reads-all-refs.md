priority: 2
cell: A3
territory: theoria-arm
deps: none
lane: campaign
author: RES-1
released_by: CLEANUP

# A3-A17-armversion-reads-all-refs · provenance 扫描的输入会被任何人建一个 tag 改掉

**同一条句子的第二个实例，第一个刚在 A3 上花了 23.6 小时。** 今天关掉的那条是 archive.costs() 依赖 proxy/cost.py 未声明的返回形状；这一条是 armtools/armversion.py::scan() 读 `git rev-list --all`，于是**任何人建一个 tag、推一条分支，都在改 provenance 扫描的输入**。归档产物依赖一个没有被声明为契约的外部东西——形状一模一样。

**今天它贡献零，这一点要照实说，别把它写成正在冒烟。** OPS-M §8.7 测过：`--all`（1204 commits / 47 arm versions）与仅 `HEAD`（1049 / 22）给出**完全相同**的漂移集合，master 与合并树都是；本轮 7 条漂移全部 `verdict: no_match` 且 `commits` 为空，所以那 35 个 tag 没有咬到任何东西。**它是潜伏项，不是缺陷现场。** 这也是它 p2 而不是 p1 的理由。

**为什么它仍然属于 campaign 赛道而不是随便谁的清理活**：A3 的全部产出是「有 provenance 背书的账单形状」（论文图 2）。一次真花钱的战役跑完之后，它的 `base_commit` 是由 `armversion.scan()` 反推的；如果那次反推的输入取决于**别人那天有没有打 tag**，那么战役的 provenance 就不是战役的属性。**在花 $60 之前把它钉住，比花完再发现便宜。**

## 要求

1. **先量，别先修。** 造一个能让它真的咬人的场景：`scan()` 在 `--all` 下把某个 `arm_version` 判成 `ambiguous`（多个提交同哈希）或把 `verdict` 从 `no_match` 翻成 `matched`，而仅 `HEAD` 下不会（或反之）。**如果构造不出来，那结论就是「今天不可触发」，如实写，不要为了有产出而把它说成危险。** 一个报告说「我试了这四种触发方式、都没成，理由是 X」比一个含糊的「有风险」有用得多。
2. **判定该读什么。** 候选至少三个：仅 `HEAD`、仅 `origin/master` 的第一父链、或清单自己记下的一个显式引用集合。**每一个都要说清它在什么情况下答错**——只读 HEAD 会漏掉一个合法的、在别的分支上的历史提交；读 `--all` 会把别人的 tag 算进来。这是取舍，不是对错，要的是被论证过的选择而不是投票。
3. **别把归档清单重写一遍来达成绿。** 今天那趟迁移是带机械守卫的（逐个点名 slug、默认 `--check`、diff 超出声明范围即拒写、账本写前写后各哈希），照那个样子做；`python -m armtools.backfill --all` 仍然禁止。如果这条修法**不需要**动任何归档清单，那更好，明确写出来。
4. **测试要带反向对照。** 至少一条：在一棵**新建 tag 之后**的树上，扫描结果必须不变。这条测试要建**真的** git 仓库（`git init` + 裸仓当 origin），不要假造一层 git 的壳——假造的壳测到的是那层壳。
5. **交付前在一棵不含未跟踪产物的新工作树里复跑闸门**（`git worktree add --detach`）。今天正是这条差别把一条 24 小时的红藏了起来：check 8 在造出产物的机器上绿、在 `ci_merge` 建的克隆里红。

## 边界

零 API、零花费（这件完全离线）。封存堆零接触。只动 `theoria-arm/`。
`proxy/` 与 `figures/` 只读不改；若结论要求改它们，写 inbox 提案，不要越界。

> **CLEANUP 于 2026-07-31T09:07:44Z 交回**：cleanup campaign 2026-07-31: not in scope
