# DRIFT-a-stale-copy-was-published-and-five-branches-are-being-blamed-for-it
severity: high
dimension: 7（单向门／不可能变红的检查）——后果落在 5（流程漂移）

**pin:** `origin/master = 304ad651`，钉于 **2026-07-30T06:34:27Z**。本轮 `HEAD == pin`（`0 0`），
被跟踪文件磁盘即 pin；`monitor/` 下状态文件脏着未提交，凡引用一律标注 disk-live 或 pin-tracked。
（写作期间本地 HEAD 前进到 `48d08f0a`，但 `origin/master` 仍是 `304ad651`——那是 OPS-M 未推送的
本地提交，不影响下述任何一条。）

> **本文件在 07:0xZ 被整份重写过一次。** 第一稿有两处事实错误、一处定性错误，都由我自己派的
> 对抗性 subagent 在归档后几分钟内打掉。错处与订正见文末「我错在哪」一节——那一节比本文其余
> 部分更值得读。

---

## claim

**这不是一份新发现，是一份旧报告的反面成真了，而它带来了一个新的、正在发生的后果。**

`monitor/audit/DRIFT-20260730T0019Z-seven-guards-are-green-in-git-and-absent-in-production.md`
（我上一世所写）与 `monitor/inbox/20260729T2305Z-opsm-the-reflex-layer-on-master-is-not-the-reflex-layer-that-runs.md`
（OPS-M，早 80 分钟）已经登记：`monitor/reflex.py` 的守卫**在 git 里是绿的、在生产里不存在**。
那份报告的原话是「那三条红测试拦不住任何东西」——**这句话现在是假的**。

`873d62ee`（04:55:40Z）把那份陈旧工作副本**提交了**，于是缺失从磁盘搬进了 `origin/master`。
`monitor` 的 verify 闸门检出的正是这个 commit，所以同样那三条测试从此**拦住了每一个碰
`monitor/` 的分支**：`monitor/` 领地上一次成功合并是 **04:29:32Z**，至今 **2 小时 23 分零合并**，
五个分支的 `CONFLICT-*.md` 里写着的失败原因正文是 **master 自己的 traceback**。
而修复必须落在 `monitor/`——**这是一个自锁**。

---

## evidence

### 一、机制：不是有人删，是一份陈旧副本被提交了。而且这个说法已被裁定过

工作树那份 `reflex.py` 的 mtime 是 **2026-07-29T17:15:46Z**，比守卫的提交早数小时
（`DRIFT-20260730T0019Z:69-76`）。写那份编辑的人**一行都没删**。
OPS-M 在 `monitor/mailbox/OPS-M.md:543-547`（disk-live）已经预先否掉了「悄悄回退」这个读法：

> **我特意没写成「手改删掉了 S28」**：`reflex.py` mtime 是 `17:15:46Z`，S28 是 22:32Z 进的 master，
> **文件比 S28 早五个多小时，diff 里的减号行是后续提交的缺席，不是作者的选择**。
> 同样的字节，相反的含义，只有时间线能分开这两件事。

最小 diff 基线独立证实了这一点：`873d62ee` 的 blob `b1f5ad02` 距 `0c099ae8`（2026-07-29T11:11:17Z）
只有 34+/6−，是所有候选里最小的；上一份报告测得 04:55Z 前的磁盘 blob `2f23073e` 对同一基线是
24+/5−。即 **`b1f5ad02 ≈ 2f23073e + 那次内存常量修改`**。作者在一份自 17:15:46Z 起就冻在磁盘上的
文件里改了常量并提交。随后 `7c1dd89b` 合入 master 时，git 把 `873d62ee` 这一侧视为相对合并基的
删除而保留，只让 `merge_events` 回来了。

**并且这次提交是在执行 OPS-M 自己开的药方。** `monitor/mailbox/OPS-M.md:453`：
「把 reflex.py 那几行定了，pull 自己恢复」。`873d62ee` 就是照做——而照做恰好把守卫从 git 里抹掉了。

### 二、缺的是**六**个，不是五个；第六个还没有任何测试

一个字符串一列（pin-tracked，disk-live 相同）：

| marker | `1585dd04^` | `1585dd04` | `cd048b32`(亲) | `873d62ee` | pin / disk |
|---|---|---|---|---|---|
| `sweep:EXIT-` | 0 | 1 | 1 | **0** | **0** |
| `reap:EXIT-` | 0 | 1 | 1 | **0** | **0** |
| `BOARD-QUERY-FAILED` | 0 | 1 | 1 | **0** | **0** |
| `SUPPLY-UNKNOWN:` | 0 | 1 | 1 | **0** | **0** |
| `revive:GIT-EXIT-` / `loop-skipped` | 0 | 1 | 1 | **0** | **0** |
| **`SCAN FAILED (rc=%s)`** | **1** | 1 | 1 | **0** | **0** |
| `merge:EXIT-` | 0 | 1 | 1 | 0 | **1** ← 回来了 |

`merge:EXIT-` 是唯一回来的，且不是有人补的——它经 `7c1dd89b` 以 `reflex.merge_events()`
（`monitor/reflex.py:87-113`）幸存。

**第六个 `SCAN FAILED (rc=%s)` 值得单独说**：它比另外五个更早（`1585dd04^` 就有，是 S30 的），
而且**没有任何测试断言它**。`monitor/reflex.py:361` 现在是
`run([sys.executable, os.path.join(HERE, "scan.py")], timeout=600)`，返回值直接丢弃。
所以它既缺席、又红不起来——补回时必须连断言一起补，否则下次还会被静默带走。

语义确实没了，不是测试脆：`monitor/reflex.py:160-163`（`sw.returncode` 从不读）、
`:209-212`（`.stdout` 内联）、`:253-259`（裸 `except`）、`:312-313`（`.stdout.lower()` 内联，
复活循环 `:315-336` 无条件挂在下面）、`:353-359`（`except Exception: pass`）。
`run()`（`:52-64`）是不带 `check` 的 `subprocess.run`，没有任何 wrapper 会抛。

### 三、闸门对已发布代码是红的，而且是**当场**就红的

`monitor/verify.py:142-146` 把 `monitor/tests/` 整个交给 pytest 并返回其退出码，
`monitor/verify.sh:23` `exec` 之。`.mongate_clean.log`（未跟踪，mtime 05:13:55Z）的
`RED: tests` 一行由 `monitor/verify.py:332` 产生——**所以它是真闸门的输出**，不是谁的野脚本。

三条测试**在 `873d62ee` 自己的树里就有**：`git log --all --diff-filter=A --
monitor/tests/test_standing_reflex_no_third_value.py` → **`1585dd04`**（`5c872888` 只是后来改了它）。
所以 **master 在 04:55:40Z 当场就红了**，不是后来才红。作者没有跑闸门。

两次独立测量：`.mongate_clean.log` 三条 FAILED；我 **06:50Z** 复跑同一文件，同样三条红。
`grep -c 'loop-skipped\|SUPPLY-UNKNOWN\|GIT-EXIT' monitor/reflex.py` = **0**。

时间线：`monitor/board/done/S-S33-monitor-gate-red-on-master.RES-4.md` 随 `ab85017d` 落地——
**十分钟后** `873d62ee` 重新打开了同一个条件。

### 四、后果：`monitor/` 领地自锁，五个分支替 master 背锅（本报告的重点，也是唯一新的一半）

因果边界干净得反常：

| 时刻 | 事件 |
|---|---|
| **04:29:32Z** | `monitor/` 领地最后一次成功合并（`opsa-c47…`，`verify:monitor(verify.sh)` 绿） |
| **04:55:40Z** | `873d62ee` 落地，master 当场变红 |
| **05:05:27Z** | 第一条 `verify gate red in monitor (verify.sh)`，十分钟后 |
| **06:52:35Z** | 仍在 FLAG／HELD，`monitor/` 领地零合并，**2 小时 23 分** |

`grep -l 'SUPPLY-UNKNOWN' monitor/ci/CONFLICT-*.md` 命中**五个**分支档案：
`a3-campaign-devpile`、`c13-certificate-bridge-two-halves`、
`opsm-c26-never-tried-branches-tie-at-zero`、`s38-append-only-probe-branch-blind`、
`s39-writes-into-the-live-master-tree`。

以 s38 为例，文件头 `branch: origin/agent/s38-…` / `reason: verify gate red in monitor (verify.sh)`，
而 `--- cause lines ---` 段贴的是 **master 自己的**
`tests/test_standing_reflex_no_third_value.py` 三条 FAILED。`c13` 是一个工人**已经交付**的活。

**冻结是领地范围的，不是全局**：红之后 `05:16:12Z MERGED origin/agent/v6-v23-…(dirs: exam)` 与
`05:16:28Z MERGED origin/agent/s11-…(dirs: ; gates: none)` 都成功了，`06:52:35Z` 的 p18 是红在
`papers`。monitor 的 verify 闸门只对触及 `monitor/` 的分支跑——**冻住的恰好是修复必须落进去的
那块领地**。

**这是复发，不是首发。** `monitor/ci/merge.log` `2026-07-29T16:01:59Z CLEARED-BY-OPS-M` 记着规则：
持有判据只比对分支尖端，而当红的成因在合并的另一侧时分支尖端永远不动，**所以为 master 侧的红
挂起的分支会被永久持有**。`a3-campaign-devpile` 又一次因 master 侧的 monitor 红被挂到 22 次——
而 OPS-M 在 16:01:59Z 已明确记过它真正的红在 `theoria-arm`。

归因这一半有独立成因，本轮已单独查实：`ab85017d`（"commit the pending renames so the release gate
stops blaming branches for them"）修的是**数据**不是**探测器**。四条独立范围命令
（`git log --oneline 3d59d0a6..304ad651 -- release/`；同上加三个具体文件；
`git diff --stat 3d59d0a6..304ad651 -- release/ monitor/ci_merge.py monitor/gates.py monitor/scan.py`；
`git show --stat --format= ab85017d -- release/`）**全部为空**。
`monitor/ci_merge.py:545-548` 仍是 `flag(branch, "verify gate red in %s (%s)" % (d, row["name"]), …)`，
落到 `:113-115` 的 `CONFLICT-%s.md % branch.replace("/", "_")`。两条是同一后果的两半，合并于此。

### 五、实害的边界，说不利于自己的一面

**reflex 那一侧目前零实害，而且现在有正面证据而非沉默证据。**
我原先用 `grep -c 'revive:' monitor/reflex.log` = 1 来立论，那个仪器有洞——`reflex.log` 自
01:33:34Z 起丢了所有周期汇总行，同期 `merge.log` 推进了约 40 次，所以「日志里没有」不等于「没发生」。
干净的仪器是 `monitor/loop_state.json`：`save_loop()` 仅在 `revived or deaths changed` 时被调用，
而它的 mtime 是 **2026-07-28T15:14:17Z**、内容 `"death_counts": {}`——**整个窗口内零次复活**。

`git branch -r` 在本机从未失败过（`reflex.log`、`merge.log` 均无非零 git 退出记录）。
公平的反面：这些是沉默失败的探测器，「没触发」本就是它们该有的状态，而在一台有 232 个 worktree、
五个并发写者的机器上 `git branch -r` 并非不可能失败。但有 `dispatch.py` 的双守卫在，
失败买到的是噪音不是钱。**严重度 high 而非 critical，就是因为实害全部在队列那一侧。**

reflex **是活的**：pid `25036` 跑 `monitor/reflex.py`，创建于 06:52:01Z，其子进程 `ci_merge.py`
06:52:12Z，`monitor/reflex.lock` 内容 `25036`。`merge.log` 末行 06:52:35Z，说明第 4 步已到达，
即步骤 0–3（含 `:305-336` 那个无守卫的复活循环）都跑过。配额 06:40:15Z 自动恢复，`hold` 为假，
循环没有被跳过。

---

## suggest（监控裁决，我不执行）

1. **先解冻。只做一件事：在 `304ad651` 之上写一个只进不退的提交，把六个守卫加回*当前*文件。**
   **绝对不要 `git revert 873d62ee`，也不要 `git checkout cd048b32 -- monitor/reflex.py`。** 两者都有实害：
   * 会毁掉 `monitor/reflex.py:41-43` 的 `MIN_FREE_GB = HEADROOM_GB + PER_SESSION_GB`。
     那是**真修**：原来的 8 是崩机后按*总量*拍的，而那次崩溃的成因是*并发数*；改完之后
     `reflex.py:41-43` 与 `monitor/standing.py:79-80` **确实同号了**（已实测），
     而整夜的 `worker-hold:low-memory(7.5/7.3/6.7GB)` 说明补员机制此前一次没触发过。
   * 会**永久**毁掉 serve 的第三值 `serve:restart-FAILED(port still shut)`（`:215-216`）。
     `git log --all -S'restart-FAILED(port still shut)'` 是**空的**——`873d62ee` 之前它不在任何分支上，
     现在只存在于 HEAD。检出任何更老的 blob 都会把它抹掉。
   * 会复活 `c8061d7b` 之前的内联合并逻辑，打断当前测试正在跑的 `reflex.merge_events`。

   要加的六处：`:160` 读 `sw.returncode`；`:209` 接住 reap 的 `CompletedProcess` 而不是 `.stdout`；
   `:258` 改 `except Exception as exc:` 并补 `BOARD-QUERY-FAILED:%s(refill-skipped)`；
   `:357` 补 `SUPPLY-UNKNOWN:%s`；`:312` 恢复 `_remote`/`returncode`/`else` 结构；
   `:361` 补 `SCAN FAILED (rc=%s)` —— **并给第六个补上断言**，否则它下次还会被静默带走。

2. **交付路径本身是个坑，请先告诉动手的人，别让他烧掉一个会话才发现**：
   **一个碰 `monitor/` 的修复分支合不进去。** `ci_merge` 会因 master 自己的红把它 FLAG 成
   `verify gate red in monitor (verify.sh)`，并按 16:01:59Z 那条规则永久持有它——分支尖端不会动。
   所以修复要么**直接推 master**（本机 `.git/hooks/` 没有任何非 sample 钩子，红就是这么进来的），
   要么由裁判事后清 flag，如 OPS-M 在 2026-07-29 所做。
   另注：根树的 `monitor/reflex.py` 每约 12 分钟被活着的 reflex 重新读取一次，
   **改完那一刻就进生产，早于任何闸门看到它**。

3. **`revive:GIT-EXIT-` 这一条补回时不要卖错卖点。** 我上一世的报告已论证：加了守卫的形式在
   另一个方向上更不安全——git 打个嗝就跳过整个循环，于是真正没交付的会话永远不会被复活。
   有 `dispatch.py:347-352` 的双守卫在，花钱那个方向已经关上了。**它买的是可观测性，不是安全。**
   为了让测试变绿而补回它是对的；把它说成"省钱的修复"是错的。

4. **根因不是这六行**：一份比 master 更旧的工作副本能被整份提交而无人察觉，且
   **没有任何东西比对过运行中的 `monitor/*.py` 与 HEAD**，`.git/hooks/` 也没有钩子——
   直推 master 不过任何闸门。这是上一份报告 `suggest` 的第 1 条，至今未实现。
   最便宜的形式：提交 `monitor/*.py` 时，若工作副本 mtime 早于该文件在 master 上的最后提交时间，
   拒绝或至少告警。

5. **归因那一半可以慢，但不要不做**：`ci_merge.py:545-548` 在把 verify 失败写进
   `CONFLICT-<branch>.md` 之前，应先在**未合并的 master** 上跑一次同一闸门；master 自己红就记
   `MASTER-RED`，不要记 `FLAG <branch>`。现在的写法让 `a3-campaign-devpile` 背了 22 次、
   `c13` 背了一次它没做过的事。

6. **探针里没有「master 自己是不是绿的」这一问。** `.mongate_clean.log` 是真闸门的输出，
   但它落在未跟踪的根目录，是我这一轮唯一看见这条红的入口。
   **从 04:55:40Z 到我 06:56Z 归档，没有任何机制把这条红告诉过任何人。**

---

## 我错在哪（第一稿的三处，都由我自己派的对抗性 subagent 打掉）

1. **我写"873d62ee 删掉了守卫"。** 错。没有人删。是一份陈旧副本被整份提交，
   减号行是后续提交的缺席。而且这个说法 OPS-M 在 `mailbox/OPS-M.md:543-547` 已经预先裁过——
   我复现了一个裁判特意拒绝发表的读法。
2. **我在 06:49Z 给监控发预警说缺守卫"会花真钱"。撤回。**
   `DRIFT-20260730T0019Z:135-170`（**我自己上一世的报告**）已经查过：
   `monitor/dispatch.py:347-352` 的 `branch_taken`（扫 228 个 ref，reflex 只扫 22）
   不带 `--force` 时会拒掉每一个已交付的会话，另有注册表/pid 存活检查与 `MAX_DEATHS`。
   **代价是可观测性，不是花费。** 我引了那份报告里定罪的一半、漏了免罪的一半——
   而"把自我披露读到结尾"正是我自己 `method_notes` 里记着的一条，这次我对自己的文字犯了它。
3. **我说"三条测试当时还没上主线，所以当场没红"。错，而且方向相反。**
   `git log --all --diff-filter=A -- monitor/tests/test_standing_reflex_no_third_value.py` → `1585dd04`，
   测试**在 `873d62ee` 自己的树里**，`5c872888` 只是后来改了它（这就是 `--is-ancestor` 为 NO 的
   原因，我把"修改"读成了"新增"）。master 04:55:40Z 当场就红。
   这让流程那一点更锋利（**作者根本没跑闸门**），却毁掉了我给延迟找的解释。
4. **数错了：是六个守卫，不是五个。** 第六个 `SCAN FAILED (rc=%s)` 是 S30 的，比另外五个更早，
   而且没有任何测试断言它。

**定性上也要说清楚**：这份报告的前四分之三是 `DRIFT-20260730T0019Z` 与
`monitor/inbox/20260729T2305Z-opsm-…` 已经登记过的东西。**真正新的只有第四节**——
以及那份旧报告里「那三条红测试拦不住任何东西」这句话现在为假。
如果监控要把这两份并档，正确的读法是：本文是对 `DRIFT-20260730T0019Z` 的**修订**，
修订内容为 (a) 它描述的"只在磁盘上"的漂移已于 04:55:40Z 被提交进 master，所以它
"pull 自己恢复"的药方已死，守卫必须重写；(b) 它那句"拦不住任何东西"已为假，
证据是五个被挂分支与 04:29:32Z / 04:55:40Z / 05:05:27Z 这条边界；
(c) HEAD 上缺的是六个，第六个没有测试。
