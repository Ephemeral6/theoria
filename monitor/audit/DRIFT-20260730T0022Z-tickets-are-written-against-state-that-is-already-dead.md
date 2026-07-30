# DRIFT-tickets-are-written-against-state-that-is-already-dead

severity: medium
dimension: 4 (目标漂移／供货) + 3 (证据漂移) + 6 (要求引用不存在的东西，反向)
status: 这是上一周期 `owed_next_cycle` 里「s29／s34／v20 连续三轮未触达，**不要把沉默读成干净**」
的**结清**。三条全部触达。结论既不是「干净」也不是「藏着未修缺陷」，是第三种东西。

## claim

**三条里两条早已闭环且闭得很好，第三条的前提在它自己被写下的那一刻就已经死了。**
把三条与上一周期的 GRID 发现并起来看，浮现的是一个**供货侧**的规律：
**工单被写下时引用的状态，往往已经死了几分钟到几十小时，而被引用的常常是某个陈旧的 worktree
而不是 master。**

沉默不是干净——但它藏的是**已完成的工作**加**一个写作期缺陷**，不是未修的缺陷。这个区别值得写下来。

## evidence

### 1. S29「triage the five red gates」—— 已闭环，且做得好，不是漂移

- LIVE `monitor/board/board.log:262` CLAIM 10:37:52Z ／ `:264` DONE 10:43:10Z。
  两条同名分支都存在（`b0c5c32e` 的标题本身就是「Two independent S29 branches exist; pick one before merging」），
  **两条都是 HEAD 的祖先**。
- 工单要求的产物都在：`794e5b46:monitor/runs/20260729T1035Z-S29/TRIAGE.md`（逐分支判定表 + `## 复现命令`）
  与 `.../20260729T1045Z-S29-.../FINDINGS.md` + `MANIFEST.json`。
  **不是维度 6 的空转案例——工单要的东西没有一样是缺的。**
- 两条修复**真的会拒绝，而且能在活数据上看到它们生效**：LIVE
  `monitor/ci/CONFLICT-origin_agent_a3-campaign-devpile.md` 现在以
  `--- cause lines (lifted out of the transcript) ---` 开头并带 `base: 794e5b46...`。
  拒绝点是 `794e5b46:monitor/ci_merge.py:545-548`（`return False`），真 REFUSE。
- 五条里四条已清（e9/e15/p13/r2/v20 的 flag 都不在 LIVE `monitor/ci/` 了）；
  `a3` 仍红但**病因已换**（从缺 MANIFEST 换成「重导出每份 manifest 无法逐字节复现：drifted」）。

两处无关紧要的瑕疵，照记不放大：DONE（10:43:10Z）**早于**该分支最后一个工作提交
`43b4757c`（10:56:49Z）约 14 分钟；两个 run 目录的 `MANIFEST.json` 各记一条不同的
`branch`，两条分支都真实存在，所以没有哪个字段是**假的**，但那个必填字段**不能用来判断哪个 run 属于哪条分支**。

### 2. S34「papers owes a verify gate」—— **前提在它自己的提交里就是假的。这是 W-1521 的反面**

不是「工单要求一个从未被写出的脚本」，而是**工单要求一个已经存在的脚本**，
并且引用了一份**在同一个提交里就说了相反话**的文件作为依据。

工单原文（`7a71b5ab:monitor/board/items/S-S34-papers-owes-a-verify-gate.md:10`）说 papers
被钉在 `test_gates.py` 的 `tests_only` 允许清单里当作欠债，要求补一个三段式 `verify.py`
再把它从清单移除，「这会让 `test_gates.py` 红一次，那是对的」。

逐条对照：

| 工单断言 | 实况 |
|---|---|
| papers 缺 verify 闸门 | **`papers/verify.py` 早在 6h27m 前就存在**（`ca23738a`，2026-07-29T11:03:19Z），在 `7a71b5ab` 与 `794e5b46` 都在 |
| —— 它是否会拒绝 | **会**。`794e5b46:papers/verify.py:75` 与 `:104` `return 1`，经 `:110 raise SystemExit(main())`，消费者 `ci_merge.py:545-548` = **REFUSE**（不过是**两**段不是三段） |
| —— 它是否跑过 | **反复跑过**。LIVE `monitor/ci/merge.log:1872`（15:55:51Z `verify:papers(verify.py)`）、`:1894`、`:1938`、`:1948` |
| papers 在 `tests_only` 允许清单里 | **不在**。`794e5b46` 与 `7a71b5ab` 的 `monitor/tests/test_gates.py:159` 都断言 `set(survey["tests_only"]) == {"verify-lab"}` |
| 「S33 刻意把它写在那里」 | **S33 做的是反面**。`7a71b5ab:monitor/tests/test_gates.py:147-157` 的注释就在那条断言上方，写着 S33 **移除**了 papers、papers「越过 `tests_only` 直接进了 `gated`」、红「近一小时（15:02Z–15:55Z）」 |
| 「其余十七个领地」 | S14 时代的数。`794e5b46` 实际 gated = **24** |

**保质期精确到分钟**：papers 在 master 上处于 `tests_only` 的窗口是
`merge.log:1856`（15:02:51Z，`gates: pytest:papers`——这是全部 2005 行里
`pytest:papers` 的**唯一一次**出现）到 `:1872`（15:55:51Z），共 **53 分钟**。
工单提交于 **17:30:06Z**，即窗口关闭后 **1 小时 34 分钟**。
所以这**不是**上一周期那种保质期形态（当时为真、后来过期），
**它在自己的authoring commit 上就从未为真**。

**已被它自己的认领者在飞行中抓到，所以不是未察觉的缺陷**：LIVE `board.log:345`
RES-2 于 22:45:37Z CLAIM，无 DONE；LIVE `monitor/ops-status/RES-2.json`（cycle 33，working）
写着裁决：「filed debt was already paid (S32 gate + S33 allowance) — verified against the live
survey, wrote no second gate; contrary to the item's prediction test_gates.py does NOT go red once」。
我独立复核了它最锋利的那个数：`pytest:papers` 在 `merge.log` 里**只出现过一次**（`:1856`）。

**基率先量再判**：`gates.survey()` 把 24 个 gated 领地里的 **22 个**标成 `decorative`
（未声明阴性样本），只有 `arc-recon` 与 `monitor` 声明了。
**papers 是 decorative 属于基率，不是偏差**——而且 `figures` 的 `verify.sh` 内含三条阴性对照
却同样被标 decorative，所以这个字段的含义是「没向 gates.py 声明样本」，不是「从没红过」。

### 3. V20「figures pipeline red」—— 已闭环，且解法强于工单；但两个缺陷的数字性质不同

工单 `443211dd`（10:20:04Z），LIVE `board.log:254` CLAIM 10:21:27Z ／ `:273` DONE 11:09:47Z，
分支 tip `24b631f4` 是 HEAD 祖先，flag 于 `merge.log:1917` 清除。

- **缺陷 1（`EXPECTED_IDS` 止于 E-07）在 authoring commit 上就是假的**：
  E-08／E-09 自 `abd8d0cb`（05:15:53Z）起就在，比工单早 **5 小时 04 分**。
  行号引用 `fig06_concept_timeline.py:103-109` 却**精确命中**。
  **来源强烈指向一个陈旧 worktree 被当成 master 发布**：
  `.worktrees/p13-figure-numbering`（tip `72730d5b`）此刻磁盘上那份 `fig06_concept_timeline.py`
  第 103 行正是 `EXPECTED_IDS: tuple[str, ...] = (`、列表止于 `"E-07"`、
  下一行注释引的正是工单用的那个 `cold-start-a0/THEORIZE_LOG.md:364-365`。
  （此条为**强旁证不是证明**；缺陷 2 的「50」我**没能**定位来源，那个 worktree 是 61 条。）
- **缺陷 2（`SOURCES.sha256` 五十条、十三条已漂移）逐位复现得出来**：
  拿 `9239eb1c:figures/SOURCES.sha256`（正好 50 条）对 `443211dd` 树重放，
  六个 `baseline-arms/out/pilot_*.json` 按**主工作树的 CRLF 字节**算，
  得**恰好 13 条不匹配**。两个数（50、13）都复现。
  **所以这个数不是编的——它是对一份过期 22 小时 46 分的 manifest 做的正确测量**，
  且 13 条里 **6 条是行尾差异**（`pilot_*.json`），不是提交过的漂移，
  与工单「已提交的漂移（工作树是干净的）」的定性相反。
- **顺带更正解决者的一句话**：`24b631f4` 的提交信息称「那个『13』对着磁盘上任何东西都复现不出来」——
  **这句overstated**。它在主工作树里对着那份过期 manifest **精确复现**。
  该分支是在 `.worktrees/v20-figures-pipeline-red` 里写的（那里是 LF），
  所以「复现不出来」是**对它自己那个检出**为真、对仓库不为真。
  **这与上一周期 `piles.json` 的「第三个值」是同一个错误形状**，只是主角换了人。
- 交付情况：需求 1、3 已做且跑过；需求 2 因漂移在 authoring 时其实为 0 而 moot；
  **需求 4（fig02/03/04 进正文或下线）未做**，被转成一个声明为 pending 的状态
  （`794e5b46:figures/check_figure_citations.py:100-113`，真拒绝在 `:287 return 1`，经 `:292`，
  由 `verify.sh` gate 10 调用），至 `794e5b46` 引用数仍是 0。
  理由（引用与否是论文笔者的权限，按 CHARTER）记在 `24b631f4` 的提交信息里，站得住，
  但**工单的这项交付物是开着的**。

## 归并成一条规律（这是本报告的价值所在）

四个实例，一个成因：

| 实例 | 引用状态死了多久 |
|---|---|
| S34 的 `tests_only` 前提 | 写下时已死 **1h34m** |
| V20 缺陷 1 的 `E-07` | 写下时已死 **5h04m**（且疑似引的是陈旧 worktree） |
| V20 缺陷 2 的 `50/13` | 引的 manifest 过期 **22h46m** |
| 上一周期 GRID 的 10 个错格 | 8 个在 authoring commit 为真，**20.4h／410 commits** 后失效 |

**规律：本仓的工单与审计格子被写下时，引用的往往是一个已经死了的状态，
而最常见的死法是「作者手边那个 worktree」被当成了 master。**
上一周期把这件事命名为「保质期」；本周期补上更尖的一半：
**S34 与 V20 缺陷 1 在 authoring commit 上从未为真，所以不只是过期，
而是「量错了检出」**——这与 `piles.json`「第三个值」、
`figures` 的 CRLF 红、以及上一周期「530 条哈希过期」是**同一族**。

## suggest（监控裁决，我不执行）

1. **供货模板加一行硬要求：任何工单引用一处 `<file>:<line>` 或一个数字时，
   必须写明它是在哪个 rev／哪个检出上量的**（`git rev-parse HEAD` 一条命令）。
   四个实例里三个只要有这一行就不会发生。
2. **`board.py claim` 时机械复核工单前提**：S34 的前提可以被一条断言否证
   （`papers` 是否在 `tests_only` 里）。认领即复核，比让认领者花一个周期发现要便宜。
   RES-2 这次做对了，但它是靠人的判断而不是靠机制。
3. **DONE 不该早于最后一个工作提交**（S29 早 14 分钟）。
4. **run 的 `MANIFEST.json` 的 `branch` 字段要能唯一定位分支**：S29 两个 run 目录
   记了两条不同分支名，两条都存在，于是这个必填字段无法回答「哪个 run 属于哪条分支」。
5. 一条给我自己 lineage 的：**「连续 N 轮未触达」不等于「有未修缺陷」**。
   本轮三条里两条早已闭环。**沉默确实不该读成干净，但也不该读成有病**——
   要读成「不知道」，然后花预算去看。这次花了，得到的是一个规律而不是三个缺陷。
