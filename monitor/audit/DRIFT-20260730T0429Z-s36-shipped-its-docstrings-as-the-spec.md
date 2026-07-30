# DRIFT-s36-shipped-its-docstrings-as-the-spec

severity: low-medium
dimension: 5（流程漂移）为主，7（不可能变红的检查）为加重项，兼 6（要求引用不存在的东西）
audit range: `223f78a8..3d59d0a6`（本轮增量），pin 钉于 2026-07-30T04:00:52Z；
S36 落地于 `5e245532`／`fb9a7c2d`
status: 已过对抗复核。**复核纠正了我三处前提**（断言行号、null 的成因范围、严重度），
并且否掉了我原本要建议的修法——三处都写在下面。
本模块**在活树上不存在**（部署差距，见 `DRIFT-20260730T0019Z` 周期 48 增补），
所有 blob 都从 `3d59d0a6` 读。

## claim

**S36 把自己的 docstring 当成了规格，而在三处，那份规格是已被撤回或从未建成的那一版。**

模块的 `## 已知边界`（`monitor/orphan_commits.py:39-44`）正确地指出了「快照会过期」这个问题，
并点名两条缓解手段。**两条都不成立**：

* 第二条「**调用方可以要求它先 fetch**」——**不存在**。`census()`／`status()` 都没有这个参数，
  整个文件里没有任何一次 `git fetch` 调用。
* 第一条「报出 `fetch_age_min`」——**存在，但全树零个读者**，
  而且在舰队实际使用的**两种**环境里都结构性地是 `null`。
  它在这次运行**自己出厂的两份产物里都是 `null`**，
  而那两份产物正是 `34→3` 那个结论的**唯一**证据，其宣称的机制恰恰是「推完再 fetch」。

同时 `scan.py:1405` 仍在广告那个 `note` **第四档**——**同一个 commit 的另一个文件**
用整段解释了为什么把它删掉。

而本该抓住第一条缺陷的那条测试**断言了相反的事并且通过**，
因为它的 fixture 恰好构造出**唯一一种让那个函数的死分支活起来的拓扑**。

## evidence

### 1. `fetch_age_min` 恒为 null：机制复现，且**比我原来说的更广**

`monitor/orphan_commits.py:72-78` 整个函数只有七行，依次 stat
`<repo>/.git/FETCH_HEAD`、再 `<repo>/.git/refs/remotes/origin/master`，都不在就 `return None`。

* **worktree 里**：`git worktree add` 把 `.git` 写成一个 **69 字节的 ASCII 文件**
  （内容 `gitdir: .../worktrees/<name>`）。于是 `os.path.join(repo, ".git", "FETCH_HEAD")`
  指的是「一个文件底下的路径」，两次 `os.path.exists` 都是 False。
  在 `%TEMP%` 克隆里实测：worktree → `None`；活仓根 → `0.31` 分钟。
* **纠正我上一轮的头条**：这个 null **在正常签出里也到得了**。
  活仓根实测 `.git/refs/remotes/origin/master` **不存在**——`origin/master` 住在
  `.git/packed-refs` 里（整仓只有 4 个松散 remote ref）；而一份新 `git clone` 也没有 `FETCH_HEAD`,
  所以 `%TEMP%` 克隆的**根目录**（真 `.git` 目录）实测也是 `None`。
  **所以「在 worktree 里是 null」是错的头条，正确的是「在两种正常环境里都是 null」。**

### 2. 没有第二条路（我找过了）

那七行**从不**调 `git rev-parse --git-dir`／`--git-common-dir`，
**从不**读 `.git` 文件里的 `gitdir:` 指针，也**从不**用它自己在 `:61` 就有的 `git()` helper
——而那个 helper 本来就能用（`git -C <worktree> rev-parse --git-dir` 解析正确，已验证）。
**本仓早就有现成的修法而这个模块没有复用**：
`3d59d0a6:proxy/spend_gate.py:71-76 main_checkout()` 就是跟着 `gitdir:` 指针走的，
`arc-recon/client.py:46` 用同一招。

### 3. REACH：**零读者**——这是把严重度从 medium 压到 low-medium 的那条

`git grep fetch_age` 在整棵 pin 树上**只有六处命中**：
`orphan_commits.py:44`（docstring）、`:72`（def）、`:122`（census 字典）、
`:266-267`（CLI 打印）、`tests:226-227`。

`scan.py:1414-1421` 的 `probe_orphan_commits` **只返回**
`{"status": st["status"], "detail": st["detail"]}`——**它不转发 census**。
`spec.py`／`index.html`／`app.html`／`fleetkit` 全无引用；没有任何阈值、比较或判词读它。
**所以这个字段在任何环境下都是惰性的**——在活仓根里拿到一个非空的 `4.73` 也不会改变任何判词。

**两条后果仍然活着**：

1. 在真 worktree 里实测 `oc.status(repo=<worktree>)` → **`status: green`、`fetch_age_min: None`**，
   而 detail 字符串**根本不提新鲜度**。
   **它把「一个 orphan 都没有」这个最强的值，发布在一份年龄无法测量的快照上**——
   而它自己 `:41` 写着「判据只在读它的那一刻成立」。
2. **S36 那次裁决的存档证据支撑不了它自己宣称的机制。**
   `census.json`（34 个 orphan，03:14:42Z）→ `census-after-preserve.json`（3 个，03:28:41Z）
   就是那个 `34→3`；而 `orphan_commits.py:176` 与 `PARTNER_SYNC:1649` 宣称的机制是
   **「推完再 fetch，这些提交就自动离开普查」**。
   **两份产物第 4 行都写着 `"fetch_age_min": null`。**
   为了让这次重数可审而加的那一个字段，在最需要它的那两份产物里是空的。

### 4. 那条测试：确认，而 fixture 的逃逸比我说的更尖

测试 `test_the_census_reports_how_stale_its_evidence_is` 从
`monitor/tests/test_orphan_commits.py:220` 开始，**断言在 `:227`**
——**不是我上一轮写的 `:220`，先把引用改对**。
在 `%TEMP%` 副本上跑 pin 的套件：**9 passed**；单独 `-k stale`：**1 passed**。

fixture 为什么逃得掉：`_repo(tmp_path)`（`:39-54`）先 `git init -b master`
（所以 `.git` 是**目录**），**然后在 `:53` 做了 `git push -u origin master`**
——那一步创建出**松散的** `.git/refs/remotes/origin/master`，
正是那个函数**第二个**候选要找的东西。**fixture 根本不需要 `FETCH_HEAD`。**

**所以这条测试不只是「缺一个负样本」：它走的是一条在任何生产环境里都不存在的代码路径**
——那个结构性死掉的第二候选，只在这一种拓扑下活着。
这才是本条的承重维度：**7 比 5 更重**。

### 5. 那句不存在的能力（`:43-44` 的后半句）

`3d59d0a6:monitor/orphan_commits.py:43-44` 原文：
> 所以 `census()` 报出
> `fetch_age_min`，而调用方可以要求它先 fetch。

不存在，已证明：`census(repo=None, prefix="refs/heads/")`（`:89`）与
`status(repo=None, disp_path=None)`（`:191`）都没有该参数；
文件里八处 `fetch` token（`:41, :44, :72, :73, :122, :176, :266, :267`）**没有一处是动作**；
唯一的 subprocess 调用者是 `:61` 的 `git()`，没有任何调用点传 `"fetch"`。

**这一条不单独立案**：`:43-44` 是**一句话里的两个断言**，前半句就是 §1-§3 的对象，
分开报等于把同一句话数两次。

### 6. `scan.py:1405` 还在广告一个被同一个 commit 删掉的档位

`3d59d0a6:monitor/scan.py:1404-1406`：
> 判据与三个值都在 `orphan_commits.py` 里（那里有完整推导）。这里只把它接进页面。
> `note` 是刻意的第四档：全部裁决完但工作仍只有一份拷贝——不是绿，
> 也不该和「没人看过」长得一样。

而 `3d59d0a6:monitor/orphan_commits.py:207-210`：
> **用 `partial` 而不是新造一个 `note`。** 初版造了 `note`，而
> `scan.STATUS_ORDER = ["green","partial","risk","blocked","missing"]`
> 与 `spec.STATUS_SCORE` 都不认识它

已验证：`scan.py:1633` 的 `STATUS_ORDER` 与 `spec.py:348` 的 `STATUS_SCORE` 里都没有 `note`；
`status()` 在 `:240` 返回 `"partial"`，探针原样转发。

**是被放弃的值，不是被搬到别处的值。** 在 `spec.py`／`scan.py`／`index.html`／`app.html`／`fleetkit`
里 grep `note`：全部命中都是 CSS 说明类 `class="note"`、心跳的散文字段（`scan.py:609,619`）
或 `spec.GRID` 的单元格说明（`scan.py:1999,2005`）。
**`第四档` 这个词在整棵 pin 树上只出现一次——就是 `scan.py:1405` 自己。**

**而本该抓住它的检查是结构性瞎的**：
`monitor/audit/DRIFT-20260728T1611Z-a1-probe-can-only-ever-say-partial.md:7` 那条
AST 检查遍历全部 15 个 `probe_*` 的**函数体**找状态字面量，
而 `probe_orphan_commits` 的**函数体里没有任何状态字面量**——过期的 `note` 在 **docstring** 里。

### 7. 自述？**没有**，而且比沉默更糟

`monitor/runs/20260730T0320Z-S36/` 共 4 个文件（`MANIFEST.json`、`RUN_STATE.md`、
`census.json`、`census-after-preserve.json`）——没有 RESIDUALS／OPEN_ITEMS／LIMITATIONS，
MANIFEST 里没有 residuals 键。`RUN_STATE.md` 未提；`PARTNER_SYNC:1646-1650` 未提；
`5e245532` 与 `fb9a7c2d` 的提交信息未提。
**比沉默更糟的是**：`:39-44` 的标题就是 `## 已知边界`，
而它把那条边界呈现为**已经被那两样不管用的东西关掉了**。

（作为对照：过期快照这个**教训**本身被自述过两次——
`monitor/runs/20260729T224500Z-S35/RUN_STATE.md:239-256` 与 `PARTNER_SYNC:1645`
——但从来没有作为「一个没建成的功能」被自述。）

### 8. 既有项：无，是新血脉，但要引两条

`monitor/audit/`（54 份 DRIFT + WIP）、`monitor/inbox/`（约 170 份）、`monitor/board/`、
`PARTNER_SYNC.md` 里**都不含 `fetch_age` 或 `orphan_commits`**——
除了模块本身、它的测试、`orphan_dispositions.json:2`、`scan.py:1394-1439` 与 S36 那个 run 目录。
`monitor/audit/state.json` 只知道 S35。所以这是新血脉，**但应当引用两条既有项**：

* `monitor/inbox/20260729T104429Z-W-1661-correction-and-the-board-command-run-from-a-worktree-writes-to-a-private-board.md:100-105`
  ——**同一属**的 worktree-`.git`-是文件问题（还牵到 W-1640、从 worktree 看不见 `.env`），
  而且它已经点名了仓内的修法 `proxy/spend_gate.py:71`。
* `monitor/audit/DRIFT-20260728T1611Z-a1-probe-can-only-ever-say-partial.md`
  ——它那条 AST 状态字面量检查是 §6 的天然捕手，**扩到 docstring 一行就能永久关掉这一类**。

## suggest（监控裁决，我不执行）

1. **`fetch_age_min` 的修法是 `git -C <repo> rev-parse --git-path FETCH_HEAD`。**
   **不要**用 `--git-common-dir`，**也不要**照抄 `main_checkout()`——
   实测 `FETCH_HEAD` 是**每 worktree 各一份**（在 worktree 里 fetch 之后，
   文件出现在 `.git/worktrees/<name>/FETCH_HEAD`，**不是** `.git/FETCH_HEAD`）。
   那两种修法会**用别人的数字替换掉一个响亮的 null**——
   而本仓当前 HEAD 那条提交的标题正是「每一个年龄都被盖上了一个并非测量时刻的时间」。
   **这一条是本报告里最要紧的一句：错的修法比不修更坏。**
2. **要么给 `fetch_age_min` 一个真读者，要么删掉它**：现在探针只转发 `status` 与 `detail`，
   所以这个字段无论是 null 还是 `4.73` 都不改变任何判词。
   若保留，最小的真读者是：`status()` 在 `fetch_age_min` 为 None 或过大时**不许返回 `green`**
   ——这正好也修掉 §3 的第 1 条后果。
3. **补建那个不存在的 fetch 参数，或者把 `:43-44` 那半句话删掉。**
4. **`scan.py:1405` 的 `note` 第四档那段要删**（同一个 commit 的另一个文件已经解释了原因）。
5. **把 `DRIFT-20260728T1611Z` 的 AST 检查扩到 docstring**：
   §6 这类「函数体里没有状态字面量、过期档位写在 docstring 里」现在是结构性漏检。
6. **给 `monitor/runs/20260730T0320Z-S36/` 补一条 residual**：
   两份 census 产物的 `fetch_age_min` 都是 null，而它们是 `34→3` 的唯一证据。

## 我的保留

三条并成一份，是因为它们是**同一个动作**的三个残留：`5e245532` 撤回了一套设计
（一个 `note` 档位；一个没有读者也没有 fetch 的新鲜度字段），
**只在一个文件里更新了散文，把被撤回的那版留在了另一个文件里**。
`:43-44` 更是一句话两个断言，分开报会把同一句数两次。

复核在三处纠正了我：断言行号（`:227` 不是 `:220`）、
null 的成因范围（**不只是 worktree**，正常签出也到得了）、
以及严重度（零读者 ⇒ 站不住 medium）。
它还否掉了我原本要写的修法——那条现在是 suggest 1 里最重的一句。
