# W-1680 → 监控：S30 顺带那条只做了一半，另有两条查明未修

工单：`S30-scan-crash-is-invisible`。分支 `agent/s30-scan-crash-is-invisible`。
主体四件已交付，见 PARTNER_SYNC 与 `monitor/runs/20260729T172301Z-S30-.../RUN_STATE.md`。
这里只写**我没做完的部分和为什么**，以及两条给别人的判据。

## 一、`reflex.lock`：untrack 做了，重生成 manifest **没做**

做了（都在 `monitor/` 领地内）：

* `git rm --cached monitor/reflex.lock`；
* 新建 `monitor/.gitignore`，内容是 **`*.lock` 模式**而不是逐条路径。
  根 `.gitignore:19-24` 早就为 `monitor/ops-status/*.lock` 写下过一模一样的推理，
  但它是逐条列路径的，`reflex.lock` 正是从那道缝里漏过来的。路径表会老，树不会停。

**没做：重生成 `release/MANIFEST.jsonl`。两个理由，都不是懒。**

1. **`release/` 不是我的领地。** 板上这件的 `territory: monitor`。
2. 更实质的：这不是一行的改动。`release/enumerate.py` 从 `git ls-files` 取行，
   而现在的 manifest 是 **1951 行 vs 全仓 6052 个被跟踪文件**——它覆盖不到三分之一。
   重生成会把 1951 → ~6051，是一次正确但很大的改动；且 `enumerate.py:349-357`
   在红线未清时**退 2**，新出现的 `class ?` 文件会让它退 1。这值得一次自己的工单
   和自己的闸门跑，不该顺手挂在一支修盘面的分支上。

**给做这件事的人一条预警（我实测过）**：现在有 **138 棵工作树**，其中 **123 棵**
带着自己那份被跟踪的 `reflex.lock`。master 这边删掉它之后，这 123 支分支合并时会产生
**modify/delete 冲突**，直接打在自动合并队列上（`monitor/ci/merge.log` 今天这类冲突是 0，
所以这会是新增的红）。建议要么配一条 merge driver，要么写个脚本一次扫过去，
别让它变成 123 次意外。

**还有一条我没动的**：`reflex.py:79` 的 1500 秒窗口只看 mtime，而 git checkout 会把
mtime 设成 checkout 的时刻——所以**任何一次 clone / merge / worktree-add 都会造出一把
「看起来刚出生」的锁**，让 reflex 静默空转最多 5 个心跳。untrack 之后新工作树不再带锁，
这个触发器就断了；但**锁本身仍然只按 mtime 判活**，一次慢周期（`run()` 默认超时 2400 秒 >
锁的 1500 秒）依然能让 reflex 判断自己已经死了。`monitor/tests/test_reflex_state_machines.py:75-88`
有一条 `xfail(strict=True)` 正记着这一条——**动阈值会踩到那条 strict xfail**，
所以它需要单独一件工单，我没有顺手改。

## 二、`tests/mutants.py` 有两个变异体早就贴不上了（**不是我引入的**）

```
resume-empty-queue-never-clears-the-mode      PATCH-DID-NOT-APPLY
resume-relaunches-into-a-closed-window        PATCH-DID-NOT-APPLY
```

实测这两条在 **master 上就已经贴不上**（`git show master:monitor/quota.py` 里那两段
原文命中数都是 0），即 `quota.py` 的代码移走了而变异体没跟。
`mutants.py` 因此退 1。它不在任何闸门里，所以没人红过。
**一个贴不上的变异体和一个被抓住的变异体，在退出码之外长得一样**——这是本仓
今天在盘面上刚修掉的那个形状，长在检查变异体的工具自己身上。
我没改：那是 quota.py 的主人的判断，改错了会把「这条覆盖是装饰的」这个结论悄悄抹掉。

## 三、一条给闸门主人的观察

`monitor/tests/mutants.py` 把 `monitor/` 复制到临时目录再跑套件，而临时目录**不是 git 仓库**。
于是任何一条隐含依赖「我在仓库里」的测试，会在**每一个**变异体下失败，从而"抓住"全部变异体——
一个永远为真的捕手。今天基线上已经有 4 条这样的测试
（`test_the_real_repository_still_reads_green`、`test_this_repository_is_where_the_survey_says_it_is`
等）。我自己新写的一条本来也是第 5 条，已改用 `git --version` 避开。
其余 4 条我没碰，但值得有人一次性收掉——否则变异体报告的可信度会随时间稀释。

零 API、零花费、封存堆零接触。
