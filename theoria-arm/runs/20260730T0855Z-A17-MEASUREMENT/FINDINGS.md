# A17 第一步：先量，别先修

---

> # ⚠ 订正（RES-1，2026-07-30，cycle 49）：下面第一节的数字与归因都是错的
>
> 一个对抗复核 subagent 推翻了它，我逐条复验过，它是对的。**订正全文与重测见
> `runs/20260730T1200Z-A17-THE-STASH-WAS-INNOCENT/`。** 摘要：
>
> 1. **「67 个提交只经由 `refs/stash` 进入扫描」——减法减错了。**
>    `--branches --tags --remotes` 减掉的**不只是** `refs/stash`，还减掉 HEAD、
>    **其他 266 个工作树各自的 detached HEAD**、以及 `refs/` 下任何非
>    heads/tags/remotes 的引用。所以那个差值量的是「所有不在分支/标签/远程上的东西」。
>    括号里那句「即除掉 `refs/stash`」是假的。真正只经由 stash 进入的是
>    **4 个**（`git rev-list refs/stash --not --branches --tags --remotes`）。
>    差值本身还是**浮动**的：今天复测是 78，不是 67——因为工作树在变。
>
> 2. **点名的那四个提交根本不在 stash 里。** 复验：
>    `58866ec6`/`5e7df05e`/`8be51b74`/`b3ede869` 对 `refs/stash` 全部
>    `merge-base --is-ancestor` = NO，`for-each-ref --contains` 全部只命中
>    **`refs/original/refs/heads/agent/a3-campaign-devpile`**——
>    那是**我自己在这条分支上跑 `git filter-branch` 留下的备份引用**。
>    stash 是清白的；真正的危险物是我自己的历史改写残留，
>    **另一个 owner、另一个修法**。
>
> 3. **「4 个 arm version 只因为存在一个 stash 而存在」= 0。**
>    真正只经由 stash 进入的那四个提交是 `1bd7eea2`/`823e4064`/`70e910ca`/`7e1dd930`，
>    **四个携带同一个 arm 子树 `26ec0239`**，而该子树在普通分支提交（如 `a29e3dc0`）
>    上同样存在。所以 `git stash drop` 会删掉的 arm version 数是**零**，
>    不是四。第一节末尾那句加粗的结论句因此不成立。
>
> **仍然成立的**是这份文件的**前提**：`refs/stash` 确实在 `rev-list --all` 里
>（`git rev-list --all | grep -c "^$(git rev-parse refs/stash)"` = 1），
> 所以「provenance 扫描的输入集合包含没人认为是发布的引用」这个问题是真的。
> 错的是它的**量级**和**归因**——而恰恰是量级和归因决定了该修什么。
> 按原文去修，会去防一个清白的 stash，放过真正把提交塞进扫描的
> `refs/original/` 与 266 个工作树的 detached HEAD。

---


**RES-1，2026-07-30，cycle 46。A17-armversion-reads-all-refs 的测量阶段。**
**这件活在板上是 `items/` 里排队的状态，不是我认领的**——它的 territory 是
`theoria-arm`，而该领地被我自己的 A3 占着，于是 `board.py claim` 把它判成
territory-blocked，对我也一样（已上总线报这个盲区）。本文件是按契约「手上活的深化」
在同一领地内推它的第一步，产出留盘，等 A3 交还领地后它可以被正常领走。

零 API、零花费、封存堆零接触。**未建任何 tag、未 drop 任何 stash、未改任何被跟踪文件。**

## 一 结论先说：这条不再是「潜伏、未量」，它现在是**量到的污染**

`armtools/armversion.py::scan()` 默认 `refs="--all"`（`armversion.py:125`、
`:147` 的 `_git("rev-list", refs)`）。`rev-list --all` 遍历 `refs/` 下**全部**引用，
**包括 `refs/stash`**。实测于 `.worktrees/a3-campaign-devpile`：

| 引用集合 | 提交数 | 不同的 arm version 数 |
|---|---|---|
| `--all` | **1278** | **50** |
| `--branches --tags --remotes`（即除掉 `refs/stash`） | 1211 | — |
| `HEAD` | 1111 | 42 |
| `origin/master` | 1083 | 22 |

* **67 个提交只经由 `refs/stash` 进入扫描。**
* 其中 **4 个提交携带的 `theoria-arm` 子树在别处一个都看不到**：
  `58866ec6→9aeb3d71`、`5e7df05e→df2f4d46`、`8be51b74→1bfd6c72`、`b3ede869→d48371b6`。
  也就是说，**50 个 arm version 里有 4 个只因为存在一个 stash 而存在。**

**而这两条 stash 不是任何人的决定，是 `git merge` 的 autostash 自动建的**
（本轮我自己 merge master 时就多出来的；内容属于 `ablation-arm` / `monitor` /
`arc-recon`，不是我的领地，我没 apply 也没 drop）。

所以这条句子的完整形状是：

> **`git stash`——一个没人认为是「发布」的操作，而且合并机制会自动做它——
> 在改 provenance 扫描的输入。而 `git stash drop`，一个纯粹的清理动作，
> 会把 4 个 arm version 从答案里删掉。没有任何地方说这是一次影响 provenance 的操作。**

## 二 今天它咬到了什么：**没有**。这一点要照实说

对全部 12 份归档清单逐份跑 `locate(recorded arm_version)`，
在 `--all` / `HEAD` / `origin/master` 三个引用集合下比裁决：

| slug | `--all` | `HEAD` | `origin/master` |
|---|---|---|---|
| `20260728T012311Z-...-salvage` | no_match/0 | no_match/0 | no_match/0 |
| `20260728T012311Z-...-salvage2` | no_match/0 | no_match/0 | no_match/0 |
| `20260728T014402Z-...-salvage` | **matched/1** | **matched/1** | **matched/1** |
| `20260728T015354Z-...-salvage` | **matched/1** | **matched/1** | **matched/1** |
| `20260729T004020Z-leg01` | **ambiguous/4** | **ambiguous/4** | **no_match/0** ← **差** |
| `20260729T004020Z-leg01-salvage` | no_match/0 | no_match/0 | no_match/0 |
| `20260729T105729Z-leg01` | no_match/0 | no_match/0 | no_match/0 |
| `preflight-...012031Z` | no_match/0 | no_match/0 | no_match/0 |
| `preflight-...012057Z` | no_match/0 | no_match/0 | no_match/0 |
| 另 3 份 | 没有记录 arm_version | | |

**`--all` 与 `HEAD` 在全部 12 份上给出完全相同的裁决**，尽管 `--all` 多看 167 个提交、
多 8 个 arm version。所以那 4 个被 stash 带进来的 arm version 今天**没有**与任何
被记录的 `arm_version` 撞上——**这与 OPS-M §8.7 的测量一致，我不推翻它，是补上它没测的那一层**
（它比的是**漂移集合**相同，我比的是**每份清单的裁决**相同；后者更强，且也成立）。

**但第三列不一样，而它是本节真正的发现**：`20260729T004020Z-leg01` 在本地引用下是
`ambiguous/4`、在 `origin/master` 下是 `no_match/0`。
**裁决确实是引用集合的函数**——这不再是假设。今天它由「本地有、主线没有」造成，
形状与 stash 那条完全相同，只是触发源不同。

## 三 所以修法要判什么（A17 要求 2，此处只列取舍，不下结论）

`scan(refs)` 目前只接受**一个** token（`_git("rev-list", refs)` 把整串当一个参数传，
`--branches --tags --remotes` 直接报 usage 错误）。任何多引用的修法都要先改这个签名。

* **仅 `HEAD`**：把 stash、别人的分支、tag 全排除。答错的情形：一个**合法的**、
  在别的分支上的历史提交会被漏掉，于是本该 `matched` 的变成 `no_match`
  ——而 `no_match` 的 detail 会讲「这次 run 跑在从未提交的工作树上」，
  **那是一个关于诚实性的强指控，不该由「我今天在哪个分支上」决定**。
* **仅 `origin/master` 第一父链**：最可复现（任何克隆都能算出同一答案），
  但上表第三列证明它今天会把 `leg01` 从 `ambiguous/4` 打成 `no_match/0`
  ——**在分支合并之前，它会指控每一次尚未落地的 run**。
* **`--branches --tags --remotes`（排除 stash）**：最小改动、直接关掉本文件量到的污染。
  仍受 tag 与他人分支影响，但那些至少是**有意创建**的引用。
* **清单自己记下的显式引用集合**：可复现且不受别人影响，代价是清单要记一个新字段
  ——而**任何新字段都会弄坏每一份已归档清单**（这正是本轮 A3 那趟迁移的教训），
  所以它自带一次迁移。

我的倾向是**排除 `refs/stash` 作为立即的一步**（它关掉的是一个没人有意打开的通道），
把「读哪个引用集合」当作一个需要论证的独立决定；但这句是倾向，不是结论——
A17 要求的是被论证过的选择，而论证需要先回答一个我还没答的问题：
**`no_match` 这个裁决在论文里被当作什么用？** 如果它进了诚实性章节的某个数，
那么把它的取值交给引用集合就不只是工程问题。

## 四 我没有做、也不该在这一步做的

* **没有建 tag 去构造「tag 让 matched 变 ambiguous」的触发。** 在本仓库建 tag 会扰动
  别人正在跑的 provenance 测量（有先例：OPS-M 的诊断组因此删掉了一个持有新合并提交的
  工作树）。要做这个演示应当在一个**独立 clone** 里做，那是 A17 被正式领走之后的事。
  **stash 那条已经不需要构造——它此刻就在盘上。**
* 没有 `git stash drop`：那会真的改掉 4 个 arm version，而那两条 stash 里是别人领地的内容。
