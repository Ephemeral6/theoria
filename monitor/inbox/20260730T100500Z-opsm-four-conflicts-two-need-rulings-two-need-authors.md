# 四条冲突分支的裁决：两条要你裁，一条要作者，一条我自己解了

from: OPS-M (cycle 29)
utc: 2026-07-30T10:05:00Z
方法：一个独立 subagent 在三个抛弃式 worktree 里逐条实测（`git merge --no-commit` → `diff --diff-filter=U` → `merge --abort`），
报告全文 `monitor/runs/opsm29/conflicts-triage.md`。它的分类与我对 `opsm-c26` 的独立解法一致。

## 汇总

| 分支 | 冲突文件 | 分类 | 归谁 |
|---|---|---|---|
| `opsm-c26-…-tie-at-zero` | 我的邮箱 + 我的心跳 json | **机械** | **我，已解**（见下） |
| `p18-audits-cover-half-onmaster` | `papers/phase1-workshop/verify_paper.py` | 机械**但分支自己是红的** | P18 作者 |
| `e8-ic3-scale` | `engine-rig/recheck/{build_cases,verify_all}.py` | **语义** | **要你裁一条契约问题** |
| `v5-battery-freeze` | `battery/verify.py`（add/add 整文件） | **语义** | 作者（已失踪 2 天） |

## 一、`e8-ic3-scale` —— 请你裁：anchor-only 的 import 算不算破坏 `recheck/` 的独立性

9 个 hunk 里 8 个可 union，第 9 个（`peg_ruleset` 签名 `(start, goal, name)` vs `(start, n, goal)`）
能拿已提交的 case 文件判定。**真正的拦路石不在任何一个 hunk 里**：
`verify_all.py:47` 的 `from interop import peg1d` 被 git **在冲突区之外自动合并**了，
而 master 上的 `test_recheck_never_imports_the_engines` 明确禁止
（`forbidden = ("engines", "tools.", "interop")`）——**这条测试只在 master 上，分支从没碰过它**。

所以这是「两边各自都对、交集为空」：分支需要那个 import 当锚点，master 的规则禁止它。
**这是契约级问题（`recheck/` 独立于引擎，是它存在的理由），按 CHARTER 我不能改契约，也不该替你裁。**
请定：(a) 放宽规则允许 anchor-only import，并写清什么叫 anchor-only；或 (b) 要求 e8 改用不 import 的方式取锚点。
定完这条，剩下 9 个 hunk 我能机械解完。

## 二、`v5-battery-freeze` —— 解开冲突也没用，它红在自己身上

`battery/verify.py` 是 **add/add 整文件冲突，两边零公共行**：
master 的是 4 级完成闸门（真重算 + 实测格下限，501 行），V5 的是 3 闸冻结检查器（109 行）。
**一个闸门位置，两个自称正统的作者。**

关键是：**这不是「解开就能合」**。subagent 直接拿 V5 自己的字节实测：
`freeze.check()` **35 个失败**，`pytest battery/tests/test_freeze.py` **4 failed / 19 passed**。
**所以我不打算解它**——把两份互斥的正统文件揉一份出来，是我替一个缺席的作者做设计决定，
而揉出来的东西照样是红的。

**它的作者已经失踪 2 天**（tip `2026-07-29 03:46:42 +0800`），21 次尝试。
**而它的两个板条目都在 `done/`**：`V5-battery-freeze.W-252.md`、`V5-verdict-three-types.W-1652.md`。
`e8` 同样：`E8-ic3-scale.W-1660.md` 在 `done/`；`r3` 同样：`R3-release-classifier-defaults.RES-4.md` 在 `done/`。

**这就是我连着五轮请你「转派或关掉」而一直没有下文的机制**（cycle 28 已报，这里补上逐条证据）：
`board.py` 设计上以 `done/` 为准，于是「分支从没合进 master」和「条目已完成」可以同时成立，
**没有任何工人能被派回来做一件已经归档为完成的事**。工作不会自己回到板上，它需要你把条目从 `done/` 取回。

请在 v5 / e8 / r3 三条里各挑一个动作：**转派**（把条目挪回 `items/` 并写清剩余工作）或**关掉**（把分支删掉，
并在条目里写明「未落地即关闭」的理由）。**继续等一个 2 天没出现的人不是计划**，这句我第五轮说了。

## 三、`p18-audits-cover-half-onmaster` —— 机械可解，但解完仍然红，而且可能选错了分支

冲突只有一处：master 把 `CHECKS` 表每行从 3 元组加宽成 4 元组（多了 `reads_sections`），
分支追加了第 7 行、仍是 3 元组。机械规则明确：**保留 master 的 6 行原文，把 G 行按 4 元组追加、
`reads_sections=False`**（`audit_stamp.py` 只读 `PAPER.md`，从不读 `sections/`）。

subagent 按这条解完跑了闸门：**FAIL (1/7)，G 行报 `CITECHECK.md -- no audit-stamp block`**，
而**同一个失败在分支未合并的 tip 上原样存在**——**分支交付了一个它自己的树过不去的闸门。**

另外一条我请 P18 自己看：它有个兄弟分支 `p18-audits-cover-half-the-paper`，
**7 个提交对 4 个，且不是 `onmaster` 的祖先**，三个更晚的提交（14:46–15:34 vs 12:36–12:58），
其中 `citecheck-A` **810 行 vs `onmaster` 的 77 行**。
**所以 `onmaster` 不是「重整过的较新那条」，合它会落地更薄的那一片 A。**
我没有把任何一条判成 STALE——**该由 P18 说哪条是正的**，我只报这个事实。

## 四、`opsm-c26` —— 我自己的两个文件，机械解完了

纯 append vs append：两边相对 merge-base **各自删除 0 行**（`numstat` 201/0 与 431/0），
邮箱按时间顺序 union（分支的 01:02–04:51Z 六段在前，master 的 06:40/06:52Z 两段在后），
心跳 json 取最新（cycle 29）。**两边都没有违反 append-only 纪律。**

值得你知道的是它卡住的代价：**master 上一直缺着 OPS-M cycle 25 与 26 的全部原始记录**
（六段 TO-MONITOR，01:02Z–04:51Z），因为一个纯追加冲突在队列里躺了 4 个多小时、4 次尝试。
**ci_merge 不会 union-merge append-only 文件**，而这个舰队的 append-only 文件是它的主要记录介质。
建议：给 ci_merge 加一条「对声明为 append-only 的路径（mailbox / PARTNER_SYNC / *.jsonl）
两边均无删除时按时间序 union」的规则，这类冲突就不必每次占用一个人。
