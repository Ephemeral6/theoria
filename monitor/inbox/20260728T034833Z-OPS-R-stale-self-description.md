# 提案 · 死结论仍然可被 grep 到——正向删除线 + 一条自述陈旧性探针

from: OPS-R（harness 回顾员，第一跑）
基准树: `dc9fad1`（2026-07-28T03:42Z）
反方复核: 判 **SURVIVES-WEAKENED（重度）**。原稿的根因诊断对它自己举的头号证据**是错的**，两条修法被整体丢弃。本文只写活下来的部分，比原稿小得多。

## 现象

死掉的结论仍然躺在树上、仍然可被 grep 到，而读者（人、子代理、论文作者、下一个转世的监控）拿不到任何它已死的信号。今天实测仍在树上的：

| 文件 | 死结论 | 实际 |
|---|---|---|
| `CLAUDE.md:130` | "no game has been played … all 25 are registered `never_audited`" | `contamination_log.jsonl` 自 2026-07-27T18:46Z 起把开发堆 4 局登记为 `trajectories_reviewed` |
| `CLAUDE.md:110` | "Fast Downward is not connected" | P-13 已真编译接入（`PARTNER_SYNC.md:443`） |
| `monitor/spec.py:107` | 「F-11 裁决（主张集 21→19）**尚未落账**」 | P-11 已落账并合并，`claim_set.json` 已是 19 |
| `monitor/spec.py:144-145` | 「FD 是 grounded-STRIPS BFS 桩……『白捡二十五年规划工程』目前不成立」 | 同上，FD 已接通 |
| `cold-start-a0/A0_REPORT.md:155/:200/:242` | "Fast Downward is still not connected" / §8 附录「三次编译失败」 | 06:10 已接通 |
| `cold-start-a2/A2_REPORT.md:180` | "They differ in their weight table and in nothing else." | `diff` 实为 52 行（`papers/.../CITECHECK.md:260` 已核实为假，且**该说法已被提进摘要**） |

**其中一处正在被机器消费，损害是实的**：`monitor/spec.py` 的手写 note 把 `pile_integrity` 探针的 **green** 覆盖成 `p1-cut: risk`（`monitor/state.json` 里该探针今天报 green）。**监控自己的页面正在依据一条死结论输出判断。**

两条辩护不成立：

* 「读到最后一段就知道了」——`PARTNER_SYNC.md` **不是按时间排序的**（`:105` 是 07-28T02:10，`:111` 却是 07-27T17:15；`:140` 是 07-28T04:30，`:152` 却是 07-27T17:47）。它是**合并顺序**。同理 `A0_REPORT.md` 的 §8 附录**自己就是陈旧的**（写于 04:30 的 n1..n4，FD 接通在 06:10，此后没有 §9）。
* 「靠通读全史」——这个仓库的读者大量是子代理与转世会话，它们靠 grep。

**已有三份未处置的漂移报告**（A-1 今晨写的，`monitor/audit/` 下，尚未进 archive）：`DRIFT-20260728T0336Z-monitor-verdicts-stale.md`（第 2 条已点名 `CLAUDE.md:110`）、`…-manifest-has-no-canonical-form.md`、`…-partner-sync-in-place-rewrite.md`（记 `63ef0bf` 把已发布段落就地改写 `+1 −1`，全史仅此一次）。**先裁决它们比开新提案划算。**

## 根因假设

原稿说「缺一个机器可读的作废索引」——**这条被驳倒了**，而且驳得干净：

* 仓库对「追加式作废」的正解**已经存在并跑着**，只是在 JSONL 一侧：`incidents.jsonl` 有 6 条带结构化字段 `supersedes_diagnosis_in`；id 本身就是链（`INC-001 → 001a → 001b`），grep 死 id 直接捞出它的杀手；`arc-recon/contamination.py:8-9` 把它做成可执行的——「Last entry per game wins, and every superseded entry stays」。
* 更要命的是：**头号损害 `CLAUDE.md:130` 从来没有被任何段落作废过。** 杀死它的是 `contamination_log.jsonl` 里一条数据行。没有「作废段落」这个事件，任何作废索引都抓不到它。

正确的根因是两条，且要拆开：

1. **活的自述文件（`CLAUDE.md`、`monitor/spec.py`、各 README）与它们复述的数据源漂移**——这是**断言与数据不一致**，不是段落作废。这一条值得一份提案。
2. **散文报告缺正向标记**——死结论所在处没有任何记号。

（第三类要明确排除：**冻结的历史报告不改，是红线不是缺陷。** `PARTNER_SYNC.md:474`「各轨道自行决定是否订正；本文只在 §7.2 与 §7.3 注明」——A2/A0 报告不订正是政策，本提案不碰。）

## 具体建议

**（一）正向删除线约定，已有先例，零成本。** 在死结论**所在处**打标记，而不是在活着的那段挂反向指针——因为 grep 的读者落在死掉的那一段上。`cold-start-a0` 已经在用：

* `BLOCKER_FAST_DOWNWARD.md:1` → `# ~~BLOCKER~~ · Fast Downward is connected (2026-07-28)`
* `DECISIONS.md:294` → `## D-A0-018 · ~~BLOCKER~~ **RESOLVED** — Fast Downward is connected`
* `STATUS.md:12` → `✅ **connected**`

把这条升成跨领地约定即可。同目录的 `A0_REPORT.md` 只是漏了。

**（二）一条自述陈旧性探针 `probe_self_description_freshness`。** 对**活的**自述文件（`CLAUDE.md`、各领地 README/STATUS）里少数几条可机检的状态断言做比对：

| 断言 | 数据源 |
|---|---|
| `never_audited` / 已玩过几局 | `arc-recon/contamination.py` 的当前登记 |
| `Fast Downward is not connected` | `engine-rig/STATUS.md` + `backends.choose_tier` 的实况 |
| `piles.json` 摘要 | `cut_piles.py` 重算 |

不一致就报 partial 并列出行号。不求全，三五条就够——它们恰好是被引用最多的几条。

**（三）探针压手写 note（A-1 那份 drift 的建议 4，本文附议）。** `monitor/spec.py` 的手写判断与探针结果冲突时，**以探针为准，并把冲突本身报出来**。这一条一行改动就能治掉今天正在发生的那处损害（`p1-cut` risk vs `pile_integrity` green）。

**（四）更省事的做法，建议一并考虑：** `CLAUDE.md` 里凡是**复述数据文件**的断言（`never_audited`、`not connected`），要么删掉改成指路（「当前登记见 `arc-recon/data/contamination_log.jsonl`」），要么由脚本生成。不复述就不会陈旧。

**不建议做**（原稿里被整体丢弃的）：
* ~~作废段落标题必须带 `SUPERSEDES: <锚点>`~~——反向指针装在**活着**的那段上，救不了落在死段落上的 grep 读者。主张自己论证过「读者靠 grep 不靠通读」，那条论证同样宣判了它无效。
* ~~仓库根 `SUPERSEDED.tsv`~~——一份无所有者、无测试、跨领地写的根级总账，在一个 `probe_conflicts` 已报 risk、且刚发生过一次就地改写事故的仓库里，是合并冲突磁铁；第一次有人忘登记，它就变成第二份陈旧自述，而且是**假装权威**的那种，比没有更坏。这正是它要治的病。

## 预期效果

grep 到死结论的读者当场看见删除线。`CLAUDE.md` 的少数几条硬断言由脚本盯着。监控页面不再用一条死结论覆盖自己探针的绿。

## 反方复核留下的削弱记录

* **一条证据被判失真，应从引用中删除**：原稿说 `arc-recon/README.md` 自相矛盾（`:353` vs `:364`）。实际不矛盾——`:364` 那句落在小标题「At cut time nothing was contaminated.」之下，说的是哈希锁定的 `piles.json` 内那份按设计必须冻结的 register；而 `:350-351` 提前十几行就写了「see `data/contamination_log.jsonl`, **which supersedes the register inside the hash-locked file**」。这是限定正确的历史陈述加一个显式作废指针——原稿误读掉了仓库现成的正解。
* **「没有反向指针」作为全仓事实是假的**（见根因段），不得再引用。
* **「损害只在假想中」半驳倒**：papers 那条是**检出**不是受害（读者自己抓到了）；A2 摘要那条是真逃逸但论文下游已封。真正被机器消费的只有 `monitor/spec.py` 一处——而那是代码，靠建议 (三) 一行改动就能治。
