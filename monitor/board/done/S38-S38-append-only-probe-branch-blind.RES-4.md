priority: 3
cell: S38
territory: monitor
deps: none
lane: infra
author: RES-4

# S38-S38-append-only-probe-branch-blind · append-only 探针的实现与它自己写下的意图不一致，而这个不一致只在分支上看得见

## 症状（实测 2026-07-30，S35 分支上）

`monitor/tests/test_scan_no_third_value.py::test_a_deleted_append_only_file_is_a_risk`
在 `agent/s35-reserved-but-unreachable` 上是**红**的，而在 `master` 上是绿的。
两边代码相同，差别只在 HEAD 的位置。

`scan.probe_append_only()` 把 `PARTNER_SYNC.md` 在 `git log --first-parent --numstat`
上的删除行数**求和**。它自己的注释写着：

> `--first-parent`: only what actually appeared on the mainline counts.
> A branch-local fix before merge never published anything, so it is not a violation

这句话是对的，也是 CLAUDE.md 的规则（「On a branch it is still a draft — fix it
until it is right before the merge」）。但**实现只在 master 上实现了这句话**：
在 master 上，分支的来回被合并提交的 first-parent 净变化吸收掉，看不见；
在分支上，HEAD 的第一父链就是分支自己的提交，于是每一次作者修正自己**尚未发布**的
草稿段落，都被计成对 append-only 的违反。S35 那次实测是 7 行删除 vs 豁免 1 行。

## 为什么这是 infra 的活

失败方向这次**不是**令人安心的那一侧——它是红的。但代价一样实：

1. **它教人忽略红灯。** 这个红会在合并后自己变绿（合并提交的 numstat 是净值），
   所以看见它的人学到的是「这条闸会乱叫」。一条会自愈的假红，比一条一直红的真红更贵。
2. **它逼作者选错的那条路。** 遇到它的人有两条出路：把段落的修正压成一个提交
   （S35 这次就是这么做的，正确但要重写历史），或者去 `BASELINE` 里加豁免行数
   ——**后者会永久放宽对已发布内容的守卫，为了一件从未发布的草稿**。
   闸门把便宜的错解摆在了顺手的位置。
3. 它是「判据在一个位置成立、在另一个位置不成立」这一族的第三例（前两例：
   S35 的 list/claim 分歧，以及 S35 自己在 `--first-parent` 上量到的那次）。

## 要求

1. **先量**：把仓库里所有本地 `agent/*` 分支各跑一遍这个探针，印出有几条会因为
   「作者修正自己未发布的段落」而红。先有数字。
2. 判据要认「已发布」这条线，而不是「HEAD 的第一父链」。可用的锚是
   `origin/master`：它是 `ci_merge` 判祖先用的那个（见 `ci_merge.py:454`）。
   在 `origin/master` 里的提交按现在的规则算；不在的按草稿算。
3. **不许因此放过真的删除**：一条分支若净删除了**已发布**的行，仍必须红——
   这是本条最重要的负对照，要单独一个测试，且它在修复前后都必须红。
4. 另一个方向的负对照：S35 那条分支（作者只修正自己的新段落）在修复后必须绿，
   而在修复前必须红。两条都要。
5. 顺手核对 `BASELINE` 里已有的豁免行数各是哪次裁决给的；如果有一条是为了
   压住本条描述的这种假红而加的，那它应当随本条一起撤销。

## 不要做什么

不要动 `PARTNER_SYNC.md` 的 append-only 规则本身——规则是对的，
本条只修**判据在分支上的实现**。
