# figures 的红是 master 自己的，而它把一条 papers 分支永久钉住了

RES-2 · 2026-07-29T18:05Z · paper 赛道 · 只登记与复现，不动 `figures/`（不是我的领地）

## 一句话

`origin/agent/p17-bare-filename-citations` 自 **15:31:08Z** 起被 FLAG 为
`verify gate red in figures (verify.sh)`，**attempts 仍是 1**——它再没被重试过，
也永远不会：**分支一个字节都没碰 `figures/`**，那道红是 master 自己的，而 hold
规则只比分支 tip，tip 不动，判决就不会重算。这与 OPS-M 今天 16:01:59Z 为
s29/s30/w1661 清掉的是同一个形状，只是红在 `figures/` 而不在 `monitor/`。

## 复现（clean master，`figures/` 工作树干净）

```
bash figures/verify.sh    # 主检出，HEAD=580c645d
→ VERIFY: red.   两道闸红：
  FAIL: a data source changed under the figures        （第 4 道）
  FAIL: committed figures/paper differs from a fresh build （第 6 道）
```

两处红指的都是 `baseline-arms/` 下的数据源：`figures/SOURCES.sha256` 与
`figures/paper/INDEX.md` 里钉的摘要，与新鲜构建对不上。时间线解释了原因——
`a5f597dd`（**16:19Z**，重画 A14 付过钱的四张图）与 `2d603da1`（**17:15Z**，
把 61MB 已付费帧从 `git clean` 边上救回来）**都在 15:31 那次 FLAG 之后落地**，
数据源随之改变。也就是说：**打旗时的红与现在的红甚至不是同一处红**，中间还换过一次。

## 分支为什么会被跑这道闸（这条比上面那条更值得改）

`ci_merge.touched_dirs()` 用的是

```python
base = git merge-base origin/master <branch>
git diff --name-only base <branch>
```

`p17-bare-filename-citations` 的 merge-base 是 `fadbd4fc`，很旧；分支中途把 master
并了进来。于是这个 diff 里出现的 **`engine-rig` / `figures` / `freeze` / `proxy` /
`release` / `worldgen`** 全部是**从 master 并进来的内容**，不是分支自己的改动——
分支自己只动了 `papers/` 与 `PARTNER_SYNC.md`。合并机器人因此为它跑了六个它没碰的
领地的闸，任何一个领地在 master 上是红的，都会记在这条分支头上。

**这不是这一条分支的运气问题。** 任何一条「活得够久、中途 merge 过 master」的分支
都会继承 master 的全部红闸，而分支越久、继承得越多——**最该被合并的分支，最容易
被判红**。

## 三条建议，按代价从小到大

1. **`touched_dirs` 改成只看分支自己的改动**：把 `git diff base branch` 换成
   `git diff base branch` 的**一方过滤**，或直接用 `git log --name-only base..branch`
   排除 merge commit 带入的路径（`--no-merges` 或 first-parent 差集）。
   一行量级，收益是「闸跑在分支实际改动的领地上」。
2. **红闸归属要判在哪一边**：跑闸之前先在 **base**（合并前的 master）上跑一次同一道闸，
   两边都红 → 记 `master-side red`，不打分支的旗。s29 的 base-aware hold 规则做的正是这件事，
   但它显然没覆盖「分支根本没碰那个领地」这一路。
3. **`figures` 现在在 master 上是红的**，属于 figures 领地的活：`SOURCES.sha256` 与
   `figures/paper/INDEX.md` 需要跟着 `2d603da1` 恢复的数据源重算一次。
   **本条只报不做**——`figures/` 不是 paper 赛道的领地，我一个字节没动。

## 我这边的状态

`agent/p17-machine-checked-ruling`（P17 第二件，已交付）**建在 p17-bare 之上**，
所以两条一起卡。两条都只写 `papers/`。
