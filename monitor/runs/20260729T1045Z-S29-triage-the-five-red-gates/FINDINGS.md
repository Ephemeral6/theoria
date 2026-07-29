# S29 · 五条 verify-gate-red 逐条复现（边跑边写）

闸门的真实调用方式（三个 subagent 独立确认的同一条链）：闸门跑在**合并结果**上，
不是跑在分支上。`ci_merge.py:319` 从 `origin/master` 建 detached worktree →
`:323` `git merge --no-ff --no-edit <branch>` → `:330` `gate_for` →
`gates.py:125` 找到该领地的 `verify.py` → `gates.py:83` `.py` 闸门用
`[sys.executable, path]`（**不走 bash，所以 S25 那个反斜杠类的假红在这里不可能发生**）→
`ci_merge.py:347-348` `sh(cmd, cwd=<wt>/<territory>, timeout=1800,
extra_env=gates.gate_env(wt))`。

---

## 1. `agent/e15-solver-status-bit`（engine-rig）—— **真红，今天仍可复现**

* 退出码 1（三级梯子的第 1 级；第 2、3 级随后跑完且是绿的 ⇒ `RED (1 problem(s))`）
* 首个错误逐字：
  `TypeError: Law.__init__() got an unexpected keyword argument 'scope_exhaustive'`
  （`heldout/zero_space_heldout.py:80`）
* 跑到多远：全程。导入干净、收集了约 530 个用例、5 个失败全在
  `tests/test_heldout.py`。没有 sys.path 问题、没有 bash、没有编码损坏、
  没有把工具链 skip 当成失败。

**成因是一次干净的语义合并冲突。** master 上
`engines/zero_space/zerospace.py:45` 把 `Law.scope_exhaustive` 声明为 dataclass
**字段**，E17 的 `heldout/zero_space_heldout.py:82` 用
`Law(..., scope_exhaustive=not truncated)` 构造。E15 把这个字段重构成由
`truncated_cells` 派生的**属性**，构造器关键字就不存在了。E15 从 `e942ee6d` 开分支，
**早于 E17 的 `heldout/` 落到 master**，分支里根本没有那个文件——
所以 git 认为两边不冲突（文件不相交）而合并干净，**合并出来的树是真的坏的**。
两半各自都好：`tests/test_heldout.py` 单独在 master 上退出 0。

**归类：真红，属 engine-rig 领地。** 修法只有一个调用点
（`heldout/zero_space_heldout.py:80` 改传 `truncated_cells=`），
**未代修——不越界。**

**附带的队列问题**：flag 文件记的 `tip: d2b75c26`，而分支现在在 `e17ab261`。
按 `ci_merge.py:480`，tip 变了就不算 held ⇒ **每个 tick 都会重试、重新失败、重新 flag**。
它是队列里一个持续的重复 flag 源。

## 2. `agent/e9-engine-paper-table`（engine-rig）—— **flag 当时是真红，现在是一个陈旧的幽灵**

* flag 时（2026-07-29T04:16:53Z）退出码 1
* 首个错误逐字：`AssertionError: ENGINE_TABLE.md disagrees with the runs under it.`
  （`tests/test_engine_table.py:29`），stderr `engine_table: 3 fact(s) disagree with their artifacts`

**成因是跨领地的产物漂移，数字可以对上。** 在 e9 自己的 tip `139ed99c` 上，
`fuzzlab/out/campaign.json` 是 `worlds_per_engine: 500`，`tools/engine_table.py:325`
也期望 500——自洽。但 **fuzzlab 领地在这期间于 master 上重新生成了产物**
（`e27e0c09`、`404e1360` …）降到 60/64/14，而 e9 从没碰过 `fuzzlab/`。
合并把 master 的新数字和 e9 的旧期望放在一起，绊线**正确地**响了。
已由 `e0fd43a5` 修好（期望值改为 60/64/14）。

**但这条分支已经在 master 里了**：
`git merge-base --is-ancestor origin/agent/e9-engine-paper-table origin/master` 退出 0，
经由 `3e6d47be` 并入。往新的 master worktree 合它会说 `Already up to date`。

### 它暴露的 monitor 侧缺陷（这条属我方领地，可以就地修）

`monitor/ci/CONFLICT-origin_agent_e9-engine-paper-table.md` **永远不会被清除**，
而且它正在用一条**关于已经并入 master 的分支**的判决，虚增「verify gate red」的条数。

* `clear_flag()`（`ci_merge.py:181`）**只**在 `ci_merge.py:401` 被调用，
  即 `try_merge` 的成功路径里；
* `unmerged_branches()`（`ci_merge.py:252-261`）会把 `origin/master` 的祖先分支剔掉，
  于是 `try_merge` 再也不会对 e9 跑一次；
* 净效果：**凡是经由 ci_merge 以外的路径并入的分支，它的 flag 文件永久留存。**

这正是 `clear_flag` 自己的 docstring 在 `ci_merge.py:186-196` 点名的失败模式——
「陈旧的 flag 不只是噪声，它是这个目录里最响亮的证据，而且它是错的」——
**从一条当初的修补没覆盖到的路径原样复发。**

**精确修法**：`main()`（`ci_merge.py:456`）算出 `todo` 之后，扫一遍 `CI_DIR` 的
`CONFLICT-*.md`，用已有的 `last_attempt()` 读出 `branch:`，对那些**不在 `todo` 里、
仍可解析、且是 `origin/master` 祖先**的分支调 `clear_flag()`。
复用现成机件，不需要任何新状态。

### 幽灵普查（只读，跑在真实 `monitor/ci/` 上）

修完之后我数了一遍，**不要把这个修补说得比它大**：

| 类别 | 条数 |
|---|---|
| **幽灵**（已在 master，flag 永不清除） | **2** —— `e9-engine-paper-table`、`s21-app-session-death` |
| 确实还没合并 | 12 |
| 无法解析 | 0 |

所以 `sweep_stale_flags` 退掉的是 14 条里的 2 条。**队列堵住主要不是幽灵造成的，
是十二条真的没合并的分支。** 这个修补消除的是噪声与误导，不是堵塞本身。

## 3. `agent/p13-figure-numbering`（figures）—— **flag 当时真红；现在红因已被 master 治好，而它仍被扣着**

* 退出码 1，输出与 flag 文件逐字节相同。首个错误：
  `FAIL: data on disk is not reaching the figures:`，随后 12 行 `COVERAGE: …`
* 成因：`figures/verify.sh:211-212` 调 `check_coverage.py`，其
  `_partial_theoria_dirs()`（`:121-138`）对任何「有 `MANIFEST.json` 但无
  `cost_curve.json`」的 `theoria-arm/runs/*` 目录判失败。**它自己的 docstring 说
  「今天一个都不存在」——现在有 12 个。** 这 12 个目录在 master 与分支上完全一样
  （分支根本没碰 `theoria-arm/`），所以这是从基座继承来的、figures 自己探针的真失败。
* **关键**：master 已在 `abd8d0cb`（05:15Z）把这个探针从「失败」改成「点名」。
  用同一条闸门跑当前 master：**退出 0，绿。** 而 flag 写于 04:18:41Z——早一小时。
* 步骤 3 与 6（`A vs B, byte for byte`、`committed tree matches a fresh build`）都过了，
  所以**不是 CRLF／字节可复现性的问题**。
* 重试时它真正会撞上的是一个 merge conflict（master 的 `abd8d0cb` 动了
  `figures/fig06_concept_timeline.py`）——那是分支主人的事。

## 4. `agent/r2-release-licence`（release）—— **真红，今天仍红，是基座漂移**

* 退出码 1。首个错误：
  `AssertionError: assert {...} == {...}` / `Extra items in the right set: 'release/.gitattributes'`，
  以及 `FAIL BUNDLE.jsonl is stale -- rerun release/bundle.py`
* 成因：分支在 merge-base `8d423734` 上按 1950 条清单生成了 shipped/withheld 划分；
  master 随后落了 `release/.gitattributes`（`fa597957`），清单变成 1951 条。
  合并后 master 的 1951 条 `MANIFEST.jsonl` 撞上分支的 1930 条 `BUNDLE.jsonl`，
  于是恰好有一个文件两边都不在。**教科书式的语义合并冲突：git 合得干净，产物不一致。**
* 分支单独是绿的（`release/` 里 pytest 退出 0）；红只存在于合并树里——
  **而合并树正是 ci_merge 会推的那棵，所以这个判决是对的。**
* 不是运行器缺陷：Git Bash 固定生效（闸门跑到了 5/5 步）、PYTHONPATH 有、无 mojibake、无缺工具。

## 5. `agent/a3-campaign-devpile`（theoria-arm）—— **真红，是分支自己的内容**

* 退出码 1。首个错误（`tests/test_arm.py:866`）：
  `AssertionError: ["every run has a MANIFEST.json: missing for ['20260729T004020Z-leg01'] …"]`
  与 flag 文件逐字节相同。
* 直接跑 `armtools.verify_provenance` 得到 **6** 条失败（pytest 截断了列表）：缺 MANIFEST、
  四个必填字段全无、账目对不上（账本 22 / 4 张已结算分卡 18）、花过动作的 run 指不到分卡、
  有孤儿分卡、5 个 manifest 重新推导不再逐字节一致。
* 同样的检查跑在 `origin/master` 上**一条都不失败**（两边 `theoria-arm` 树完全相同）。
  分支新增了 `runs/20260729T004020Z-leg01/`（4 个文件，**没有 MANIFEST.json**），
  并改了 `armtools/archive.py`——**manifest 的生成器**，这就是 master 上已有的 5 个
  manifest 不再能重新推导出来的原因。修法失败信息自己写了：`python -m armtools.backfill --all`。
* **零 API、零网络**，已确认：`verify.py:181-197` 的 `child_env()` 会剥掉
  `ARC_API_KEY`/`ANTHROPIC_API_KEY`，驱动断言 `--mock` 在、`--desk` 不在，
  实跑打印 `no key, no network`。

---

# 归类总表

| 分支 | 领地 | 判定 | 归属 |
|---|---|---|---|
| e15-solver-status-bit | engine-rig | **真红，今天仍可复现** | engine-rig |
| e9-engine-paper-table | engine-rig | 真红→已修，**flag 是幽灵** | monitor（已修） |
| p13-figure-numbering | figures | 真红→**红因已被 master 治好，判决过期** | monitor（已修）+ 分支主人解冲突 |
| r2-release-licence | release | **真红，仍红**（基座漂移） | release |
| a3-campaign-devpile | theoria-arm | **真红，仍红**（分支自己的产物） | theoria-arm |

**五条没有一条是 S25 那类假红。** `.py` 闸门经 `sys.executable` 跑、不过 bash，
所以「反斜杠被吃掉」那一类在这里根本不可能发生；`.sh` 闸门的 Git Bash 固定也生效了。
**运行器这次是清白的——但队列的记账不是。**

# 队列本身：没有 head-of-line 阻塞

**明确的否定答案，有代码为证**：`ci_merge.py:464-485` 的 `for b in todo:` 里唯一的
`break` 是 `done >= args.max`，而 `done` 只在**成功**时加一；`try_merge` 返回 False
直接落到下一条。每条分支各拿一个从 `origin/master` 新建的一次性 worktree
（`:317-323`），互不污染。实测：10:08:05Z–10:44:09Z 之间合并了 **4** 条，
同期有 10–13 条挂着 flag。**绿的会绕过红的。**

所以五条红是五个独立问题。**「1158 分钟」也不是队列停摆**：它由
`mergequeue.py:129` 现算，锚在 `p10-figures-into-paper` 的第一条 FLAG
（`merge.log:47`，2026-07-28T15:12:59Z），而那是一条**只有人能解的 merge conflict**。
把它当队列头条，读起来像系统停了，其实是一条等人的冲突在计时。

# 本轮在 monitor 领地修掉的三件

1. **`sweep_stale_flags`**：经 ci_merge 以外路径并入的分支，flag 永不清除（e9、s21）。
2. **瞬态失败不再被永久扣住**：`push rejected` / `worktree add failed` / `timed out`
   不是分支的属性，**所以分支怎么变都清不掉它**——这是一个没有出口的死锁。
   实测 `c10` 在未动的 tip 上被扣了 **5 小时 53 分、零次重试**，一被重跑就合并了。
   **但重试有上限**（`TRANSIENT_RETRY_CAP = 3`）：无限重试会重建 2026-07-28
   那个「915 条 FLAG、什么都没合并」的老问题，而反复发生的瞬态已经不是瞬态。
3. **判决现在同时记 `base`**：闸门判的是**合并树**，它同时取决于分支和 master。
   只按 tip 扣住，会让判决活得比它描述的那棵树更久——**p13 就是反例**，
   红因 05:15Z 在 master 上被治好，flag 六小时后还在说 red，零次重试。
   老 flag 没有 `base:` 一律读作「重试」。

`should_hold()` 现在是这条规则的**唯一副本**，主循环与测试都调它。
原来测试里有一份自己的拷贝——**S21 正是这么出事的**：docstring、提交信息、
reflex 注释都描述了一条代码里没有的第三判据，而十条测试编码的是代码不是规则。

**未做**：`monitor/ci/` 被 git 跟踪（`merge.log` 与全部 `CONFLICT-*.md`），
所以任何合并都可能改写这个状态机的记忆——这可能就是 p10 的 flag 说
`first_seen 04:17:13Z` 而日志记着 13 小时之前的原因。**存疑未证，留给下一手。**


---

## 潜在隐患（不是本次任何一条红的成因，仅记录）

`ci_merge.py:96` 设 `PYTHONIOENCODING=utf-8` / `PYTHONUTF8=1`，
紧接着 `:98` `env.update(extra_env)`，而 `gates.gate_env()` 返回的是
`os.environ` 的完整拷贝。今天这两个键在父环境里没设，所以幸存；
**一旦监控进程是在 `PYTHONIOENCODING` 被设成非 UTF-8 的环境里启动的，
`:98` 会静默地把 `:96` 覆盖回去**，这个仓库就要为 GBK/UTF-8 付第五次账。
