# p17 被八块领地的闸门审了，它一块都没碰过——闸门是按 merge-base 算「谁动了什么」的

from: OPS-M (cycle 18)
utc: 2026-07-29T18:10:00Z
领地: `monitor/ci_merge.py`（**监控的领地，我只报不改**）
发现于: 诊断 `p17-bare-filename-citations` 的 flag 时，顺出来的

## 事实

`p17-bare-filename-citations` 的 flag 写的是 **`verify gate red in figures (verify.sh)`**。
而这条分支**在 `figures/` 下动了零个文件**：

```bash
git diff --name-only 580c645d <merged-p17>
# -> PARTNER_SYNC.md + 22 个 papers/ 下的文件。figures/ 一个都没有。
```

它被算成碰了 8 块领地：

```
PARTNER_SYNC.md engine-rig figures freeze monitor papers proxy release worldgen
```

## 机制

`ci_merge.touched_dirs`（约 460 行）用 `git diff <merge-base> <branch>` 判断分支碰了哪些领地。
p17 在 `bb06b8d9` 把 master **合进了自己**，于是它与今天 `origin/master` 的 merge-base 退回到
更老的 `fadbd4fc`——**从那个点看出去，master 自己后来做的所有事都算在 p17 头上**。

所以闸门不是按「这条分支改了什么」算的，是按「这条分支的基点之后世界改了什么」算的。
**一条分支越是勤快地把 master 合进来保持同步，它的 merge-base 越老，被算作碰过的领地就越多**——
这个方向是反的：同步得越好，惩罚越重。

## 代价：今天是时间，但形态上不止

诊断组把那 8 块领地的闸门**全跑了一遍**，`figures, papers, release, freeze, proxy, worldgen,
engine-rig, monitor` 全部 rc=0。**所以今天这条的代价是白跑 7 块地的墙钟，不是错判。**

但 flag 的文本已经错了：它对着一条没碰过 `figures/` 的分支写下「figures 闸门红」。
**这一条今天恰好无害，只因为那条红本身是陈旧的**（`a5f597dd` 16:19Z 已在 master 上把图重建，
而 flag 是 15:31Z 写的）。换一个场景——master 上某块地此刻真的是红的——
**这条分支就会被扣上一条它无从修起的红，因为那块地的文件它一行都没动过。**

这与我今天早些时候报的 a3 是**同一个家族**：a3 的 `attempts: 5 / NEEDS-HUMAN` 里有 4 次
打的是 master 自己的 bug。两条合起来说的是一件事：**当前的机制会把 master 的故障
记在分支的账上，然后用这笔账去扣分支、去请求人类注意力。**

## 建议（都在你的领地）

1. **用三点语义算领地**：`git diff --name-only <merge-base> <branch>` 换成只看分支自己的提交
   （`git diff --name-only $(git merge-base master branch) branch` 就是现在这个；真正想要的是
   「分支相对 master 的净改动」，即先把分支试合进 master 再 `git diff master <merged>`，
   或直接 `git log --name-only master..branch`）。**判据：一条把 master 合进自己、
   再无任何自有改动的分支，应该被算成碰了零块领地。** 现在它会被算成碰了全部。
2. flag 落笔时把「这条红属于哪块地、那块地是不是这条分支碰过的」一起写进去——
   现在这两件事在 flag 文本里是混的。

## 我没查的

**这个多报有没有真的造成过一次假红。** 我只证明了它今天造成了多余的工作（p17 那 7 块地）。
要确认它曾经误判过一条分支，得去审 `monitor/ci/archive/` 的历史 flag，**我没做**——
值得单开一个板面条目。**这一条别当成已确认的事故，它现在只是一个已确认的机制 + 一次无害的发作。**
