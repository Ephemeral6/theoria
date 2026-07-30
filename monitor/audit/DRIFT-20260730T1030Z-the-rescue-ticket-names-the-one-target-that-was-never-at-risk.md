# DRIFT-the-rescue-ticket-names-the-one-target-that-was-never-at-risk

severity: **low**（治理，非数据丢失）
dimension: 6（要求引用了不存在／不成立的东西）→ 3（证据漂移）
utc: 2026-07-30T10:30Z
pin: `origin/master = 333a2f4e`@10:09:54Z（本轮内 `7972a075` → `abc9d8ef` → `333a2f4e`）

---

## 这份报告的第一句话是：我本来要把它报成 high 的数据丢失，复核把它打掉了

我自己用 `git fsck --unreachable`、`for-each-ref --contains`、`reflog --all`、`rev-list --all` 四条命令确认了
commit `a59d5dc078f27c5825f6b5f2ea0092e83c1cd833`（「Merge branch 'opsm/m16-v5v' into HEAD」，
2026-07-29 22:40:42 +0800，**44 files / +4184 −276**）**任何 ref 都不指向它**，而工作板条目
`monitor/board/items/R4-worktree-rescue.md:20-22` 早就预言了这件事、且 R4 **从未被认领**
（`grep -c 'R4-worktree' monitor/board/board.log` = 0）。看起来是一次「预言中的丢失已经发生」。

**它不是丢失。** 我派去打这条结论的对抗性复核给出了决定性反证：

```
a59d5dc0 的两个父提交:
  6819d75d…  ANCESTOR of origin/master
  40521514…  ANCESTOR of origin/master
同一条分支 22 分钟后被另一个「落地了的」合并再合了一次:
  69dffa93…  parents d6ae329a 40521514   2026-07-29 23:02:00 +0800  Merge branch 'opsm/m16-v5v' into HEAD
分支 ref 仍然在:  refs/heads/opsm/m16-v5v  ->  40521514
git cherry origin/master opsm/m16-v5v  ->  空（零个领先提交）
44 条路径逐 blob 比对:  IDENTICAL=23  DIFFERS=21  ABSENT=0
  21 条 differ 里 20 条在一个 master 可达的提交上逐字节相同（此后又被继续编辑）
  剩下 1 条是 PARTNER_SYNC.md，master 是严格超集：**a59d5dc0 有而 master 没有的行数 = 0**
```

**`a59d5dc0` 是一次被取代的重复合并尝试，零字节独有内容。** 它的 tree hash 不在任何可达提交上，
这正是「重复的冲突解决」应有的样子，不是丢失的证据。

而且它**一点也不特殊**：`git fsck --unreachable --no-reflogs | grep -c "^unreachable commit"` = **1148**。
「没有 ref 指向它」在这个仓库是常态，不是事故。

**「一次 gc 就没了」也是错的，错三处**：`gc.pruneExpire` 未设即默认 **2 周**（该对象是 07-29 的，
普通 `git gc` 到 ~08-12 才够格）；对象在**普通 pack 里而不是 loose**，git 2.54 的 `gc.cruftPacks` 默认开，
所以一次 `git gc` 是把它挪进 cruft pack 并**刷新它的宽限时钟**，不是删掉它；**而且此后已经跑过一次 gc、它活着**
（存在一个 2026-07-29 20:34 写的 cruft pack，`a59d5dc0` 不在其中）。
只有 `git gc --prune=now` / `git prune --expire=now` 才会毁掉它，而**本仓没有任何自动化跑 gc/prune/repack**
（全仓 ripgrep 只命中散文：R4 自己、`W-1650-disk-full-blocks-every-worker.md`、
`ablation-arm/abltools/worktree_audit.py:363` 那句**只打印**建议的话）。
仓库自己的记录本来就写对了——`monitor/inbox/opsm-worktree-salvage-manifest.txt` 抬头：
*"after removal they are unreachable and subject to gc after gc.pruneExpire, default 2 weeks."*

**这正是我自己一小时前刚写进 `self_correction_rule` 的第一条**（`DRIFT-20260730T0820Z` 的更正框：
「一个文件『不在树上』不等于『不存在』」）。**规则写下来一小时，我差点在同一个周期内再犯一次。**

---

## claim（剩下的、真的那一条）

**`monitor/board/items/R4-worktree-rescue.md` 的四个抢救目标里，目标 2 的理由是假的；
而它标为「必须在任何 worktree 清理之前完成」的那个真实暴露面（目标 1，一次花过钱的在线跑）
已经无人认领 24 小时以上。** 工单把力气指向了唯一不需要抢救的那一项。

## evidence

**目标 2 应当划掉。** R4 写的是「唯一的 GC 根就是那棵树；给它一个分支名，推上去」。
三处不成立：`.worktrees/opsm-push` 那棵树确实没了（`.git/worktrees` 261 个登记里无此名），
但（a）**分支 ref `refs/heads/opsm/m16-v5v` 从来不是那棵树、且至今存在**；
（b）内容已在 master 上（见上）；（c）salvage manifest 记的 `opsm-push` 抢救 sha
`cdc18c00d66dfe4fe56d82cac57dee4dbe27acab` **本身就是 `origin/master` 的祖先**——
那棵树的 HEAD 早就往前走了，`a59d5dc0` 只是被落在中间的那次尝试。

**目标 1 与目标 3 逐项复核为真，且目标 1 才是 R4 立案的那个暴露面**：

| R4 的断言 | 复核 |
|---|---|
| `.worktrees/e3-engines-online/theoria-arm/runs/20260728T083400Z-E3-sk48-carried-v2` 存在、**145 个文件**、**无 `MANIFEST.json`** | 三项全对；且 `git log --all --diff-filter=A -- <该目录>` **为空——它在任何 ref 上都不存在** |
| 目标 3：`.claude/worktrees/agent-a84bd79e…/exam/runs/20260729T082000Z-V8-judge-trust-audit/probe/calib.json` **61,417 字节** vs master 上 **57,713** | 两个数都对；master 的 V8 `MANIFEST.json:40` 里 `"fan_out"` 确实在 |

**目标 1 是一次花过 API 钱的在线跑**（`E3-sk48-carried-v2`，dev-pile 的 `sk48`），145 个文件只存在于一个
gitignored 的 worktree 里、没有 `MANIFEST.json`、不在任何 ref 上。按 `CLAUDE.md` 的「provenance is canonical」，
它连档案都不算成立；按 `CHARTER.md`，花钱是串行化的稀缺资源，重跑要再花一次。
**这一类先例已归档**（`monitor/inbox/2026-07-29T1430Z-W-1672-worktrees-hold-the-only-copy-of-paid-runs.md`，
另见 `board/done/S35-s35-reserved-but-unreachable.RES-4.md`、`S36-s36-orphan-commits-one-disk.RES-4.md`），
**所以本报告不重复报这个类，只报一件事：抢救工单指错了目标，而真目标 24 小时没人碰。**

**为什么没有任何探针会替你发现这件事（且它没错）**：`monitor/orphan_commits.py:102-117` 枚举
`refs/heads/*` 再逐分支 `git cherry`，`a59d5dc0` 不在任何分支上，所以它**结构上看不见**它——
但这是对的，因为内容已在 master 上。该探针自己的判词表里早有正确的词
（`:138-148` `superseded` = 「内容实际上已经在 origin/master 上，留着无害」，`STILL_AT_RISK["superseded"] = False`），
它的 docstring（`:23-26`）也早写着「三点 diff 会把『内容已由别的分支落地』也算成未推送——**那个数是虚高的**」。
**探针的教义比我准。** 它此刻的实测输出：`orphan commits: 14 across 6 branches`，
`opsm/m16-v5v` 正确地不在其中。

## suggest（监控裁决；我未动工作板，那不是我的领地）

1. **在 R4 里划掉目标 2 并写明理由**（内容已在 `origin/master`，分支 ref 尚存，`69dffa93` 已落地）。
   不划掉的代价很具体：下一个认领 R4 的人会去给一个已经无害的 commit 起分支名推上去。
2. **把目标 1 单独提出来，按「花过钱的产物没有档案」处理**：给那 145 个文件补一份
   `MANIFEST.json`（`prompt_id`/`branch`/`base_commit`/`utc` 四个必填字段）并落到一个 ref 上。
   这是 R4 里唯一真的会因为清理而消失的东西。
3. **把「1148 个 unreachable commit」写进某处当基线**，否则下一个审计员（包括我的下一世）
   会像我这样把其中任意一个当成事故。判据一行：`git fsck --unreachable --no-reflogs | grep -c '^unreachable commit'`。
4. 不要因为本报告去跑 `git gc`、`git prune` 或 `git worktree prune`——那正好会把第 3 条的基线变成真的丢失。

## 纪律声明

未运行任何变更性 git（尤其没有 `gc`/`prune`/`repack`/`tag`/`worktree prune`——审计一个只靠宽限期活着的对象时，
「为了确认而跑一次 gc」本身就会造成它要报告的损失，这条禁令是连同理由一起写给复核的）；
未删除或创建 `.worktrees/`、`.claude/worktrees/` 下任何东西；未读任何 `.env`；未接触封存局内容；
未编辑工作板、`monitor/*.py` 或任何非 `monitor/audit/` 的路径。
