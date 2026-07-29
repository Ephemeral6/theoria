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

## 3–5. p13-figure-numbering / r2-release-licence / a3-campaign-devpile

（两个 subagent 仍在跑，落盘后补。）

---

## 潜在隐患（不是本次任何一条红的成因，仅记录）

`ci_merge.py:96` 设 `PYTHONIOENCODING=utf-8` / `PYTHONUTF8=1`，
紧接着 `:98` `env.update(extra_env)`，而 `gates.gate_env()` 返回的是
`os.environ` 的完整拷贝。今天这两个键在父环境里没设，所以幸存；
**一旦监控进程是在 `PYTHONIOENCODING` 被设成非 UTF-8 的环境里启动的，
`:98` 会静默地把 `:96` 覆盖回去**，这个仓库就要为 GBK/UTF-8 付第五次账。
