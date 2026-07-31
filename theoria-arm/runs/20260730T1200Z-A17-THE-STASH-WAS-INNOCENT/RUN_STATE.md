# A17 订正：stash 是清白的，把提交塞进 provenance 扫描的是我自己的 `filter-branch` 残留

`runs/20260730T0855Z-A17-MEASUREMENT/FINDINGS.md` 第一节的数字和归因都错了。
一个对抗性 subagent 推翻了它，我逐条复验，它是对的。**这不是措辞收紧，是撤回。**

## 一、错在哪

### 1. 减法减错了对象

原文：

> | `--branches --tags --remotes`（**即除掉 `refs/stash`**）| 1211 |
> * **67 个提交只经由 `refs/stash` 进入扫描。**

括号里那句是假的。`--branches --tags --remotes` 减掉的不只是 `refs/stash`，
还减掉 HEAD、**其他 266 个工作树各自的 detached HEAD**、以及 `refs/` 下
任何非 heads/tags/remotes 的引用。这个差值量的是「所有不在分支/标签/远程上的东西」，
其中 stash 只占一小块。

正确的问法是直接问：

```bash
git rev-list refs/stash --not --branches --tags --remotes   # -> 4
```

**4 个，不是 67 个。**

而且那个 67 本身是**浮动的**——今天复测是 **78**。它随工作树数量变，
所以它连作为「非分支可达提交总量」的读数都不稳定。

### 2. 我点名的四个提交根本不在 stash 里

原文点名 `58866ec6` / `5e7df05e` / `8be51b74` / `b3ede869`，说它们携带的
`theoria-arm` 子树在别处看不到。复验四个全部：

* `git merge-base --is-ancestor <c> refs/stash` → **全部 NO**
* `git for-each-ref --contains <c>` → 全部只命中
  **`refs/original/refs/heads/agent/a3-campaign-devpile`**

`refs/original/` 是 **`git filter-branch` 的备份引用**——是**我自己**在这条分支上
改写历史留下的。仓库里非 heads/tags/remotes 的引用总共只有两个：
`refs/original/...` 和 `refs/stash`。我把其中一个的账记到了另一个头上。

**这一条比数字错得更要命，因为它换了 owner 也换了修法。** 按原文去修，
会去防一个清白的 stash，而放过真正把提交塞进扫描输入的两样东西：
我自己的 `refs/original/` 残留，和 266 个工作树的 detached HEAD。

### 3. 「4 个 arm version 只因为存在一个 stash 而存在」= 0

真正只经由 stash 进入的四个是 `1bd7eea2` / `823e4064` / `70e910ca` / `7e1dd930`，
而它们**四个携带同一个 arm 子树 `26ec0239`**——该子树在普通分支提交
（例如 `a29e3dc0`）上同样存在。

所以 `git stash drop` 会从答案里删掉的 arm version 数是 **0**，不是 4。
原文那句加粗的结论句——「`git stash drop`，一个纯粹的清理动作，会把 4 个
arm version 从答案里删掉」——**不成立，撤回**。

## 二、还成立的是什么

**前提成立**：`refs/stash` 确实在 `rev-list --all` 里（复验：真）。
所以「provenance 扫描的输入集合包含没人认为是『发布』的引用」这个问题是真的，
A17 这件活该做。

**错的是量级和归因**——而恰恰是量级和归因决定了该修什么。
这就是这次订正的全部价值：修法的目标变了。

## 三、这次是怎么错的（值得记下的那部分）

不是算错，是**用一个近似当成了等式**。我需要「只经由 stash 进入的提交数」，
手上有 `--all` 和 `--branches --tags --remotes` 两个现成的数，
就把它们的差当成了答案，并在括号里写下「即除掉 `refs/stash`」——
**那句括注是我给自己的近似发的证书**，而 git 有一条直接问法（`--not`），
成本一样，我没用。

第二层：拿到差值之后我去找「哪些提交的 arm 子树在别处看不到」，找到四个，
就把它们归给了 stash——**因为差值是我以 stash 之名算的**。
一个错误的标签让四个证据看起来在支持它。

**判据**：一个数如果能被直接问出来，就不要用两个数相减得到它；
相减得到的数，它减掉了什么必须**逐项写出来**，而不是在括号里断言。

## 四、状态

* 复测产物：`remeasure.json`（可重跑，全部是 `git` 只读命令）
* 原文件 `20260730T0855Z-A17-MEASUREMENT/FINDINGS.md` 顶部已插入订正块并指向这里；
  正文原样保留，不修改——错的判断留在原处，供审计看见它错过。
* **未 drop 任何 stash、未删任何 `refs/original/`、未建 tag。** A17 仍是测量阶段。
* 下一步（留给认领 A17 的人）：真正该决定的是 `armversion.scan()` 读哪个引用集合。
  现在有了正确的输入清单——`refs/original/`（历史改写残留）与工作树 detached HEAD
  才是主体，stash 是边角。
