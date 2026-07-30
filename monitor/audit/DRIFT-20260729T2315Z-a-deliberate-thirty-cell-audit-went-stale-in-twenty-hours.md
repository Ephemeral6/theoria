# DRIFT-a-deliberate-thirty-cell-audit-went-stale-in-twenty-hours

severity: medium
dimension: 8（监控自身漂移），次 3（发布的数字与树不符）

**这份报告回答的是上一世明文下的委托**（`monitor/audit/state.json:78`：抽查 2 格、2 格皆陈旧，「A 2-of-2 stale base rate justifies a dedicated pass」）。它**不是新发现**，是那次普查的结案；成因句本身是**第四次**上报。请按「委托结案 + 一条新通则」读，不要按新案读。
**建议并入 `DRIFT-20260729T2230Z` 作为补强**——同一段代码、同一个成因、同一个已发表的委托。若单开，标题应当是保鲜期，不是「被推翻」。

---

## evidence

`monitor/spec.py:1188-1224` 的 `GRID` 是 30 格手写常量。逐格独立复核（代码与计数全钉在 `c54954d6`），今日树上**10 格**的事实断言不成立：E5 / C2 / C3 / S4 / A3 / V1（半） / V2 / V3 / V5 / P3。

**P4 不计入**——`freeze/STATS_RULES.md:3` 逐字自称「**状态：草案（DRAFT）。这份文件还没有被冻结**」且含 **62** 处未填 `⟨…⟩`，该格的实质判断今天仍成立，只有「包不存在」这六个字陈旧。为一个措辞技术性把分子抬高，是我自己最反对的那种报法。

### 关键的时间学：十格里八格在写下时是对的

十一格中九格的最后一次编辑同属一个提交 **`fc6f1706`**（2026-07-29 10:06 +0800，提交信息 *"monitor: audited by thirteen agents, the headline was eleven points too high"*）——**那是一次刻意的审计**。在那个提交上重算：

| 格 | 在 `fc6f1706` 上的实况 | 判定 |
|---|---|---|
| **E5** | engine-rig 324 行 MANIFEST → **match 306 / stale 18**，与注解**逐字相符**（今日 291/33） | 陈旧 |
| **C2** | 35 份 worldgen `ground_truth.json`，`all_hold` 全 true，**恰 13 份**含 `verified != true`，与注解**逐字相符**（今日 0，V19 之后） | 陈旧 |
| **S4 / P4** | `git ls-tree -r fc6f1706 -- freeze/` → **0 文件**。落地提交 `dfed7823` 在 **5h25m 之后**，其提交信息 *"written twice, committed neither time"* 反过来佐证「在任何分支上都不存在」 | 陈旧 |
| **V1** | `battery/verify.py` 缺席，`127edab9` 非 `fc6f1706` 的祖先 | 陈旧 |
| **V3** | `battery/audit/v9/REPORT.md` 由 `0b6e4939` 于 07-29 10:16 落地，**晚 11 小时** | 陈旧 |
| **V5 前提 1** | master 自己的 `figures/runs/20260729T1030Z-V20-diag/DIAG.md:18` 逐字定时：*"Was true 2026-07-28T22:41 → 2026-07-29T13:15."* —— `fc6f1706`（10:06）**在窗内** | 陈旧 |
| **V5 前提 2** | `SOURCES.sha256` 当时 **58** 行，不是 50。同文件 `:19`：*"The '50' is the manifest as of `9239eb1c`, two regenerations ago."* | 写下时已陈旧 |
| **C3**（编辑于 `038816de`, 07-28 10:35） | 该提交树上 `books/` 为**空**，`0eee2088`（加入 `theory.dsl` 者）**非其祖先**——「尚在 P-8 分支里」字面为真 | 陈旧 44 小时 |
| **A3 / P3** | `9a02a8ff`（`FEASIBILITY.md`）**是** `fc6f1706` 的祖先，07:53 落地——早 **2h13m** | 写下时已假，输给 2 小时合并延迟 |
| **V2** | `exam/STATUS.md:16-19` 自 `2a20777f`（**2026-07-28 09:25**，`fc6f1706` 的祖先）起四题型全 `done` | **写下时即假，早 24.7 小时** |

`fc6f1706..c54954d6` = **410 提交 / 122 合并 / 20.4 小时**。

### 唯一一格是另一类错误：V2

V2 引的是 `exam/runs/20260728T090621Z-V2-exam-on-worldgen/GAPS.md:4`——**一份 `runs/<id>/` 下的溯源冻结件**，按本仓约定它记录的是某一时刻的快照且不得更新。而现状文件是 `exam/STATUS.md`，早 24.7 小时就写着四题型全 `done`。

**这不是陈旧，是引错了文件类别，而这一类错误不会随时间自愈。**

### A3 的数：三个物件拼成一句

* `budget_exhausted` 出自 **rehearsal**（`.../A3-campaign-devpile/rehearsal/campaign.json`，3 leg × `actions_ok: 6`，`usd: 0.0`）——它是一个真实的结局值，只是属于另一次运行；
* `$4.3932` 出自**线上** `20260729T0035Z-a3-desk-live-proof2`（`BUDGET_TABLE.md:119`，**15** 动作）；
* `FEASIBILITY.md:12` 记 **7** successful / 40 HTTP，`:20-21` 记 *"it ran out of clock"*。

**全树无一处报 12 动作。**

### 成因（限定后）

`GRID` 三个字段里，`pct` 与 `active` **是被读的**（`scan.py:1127-1128`、`:1859`、`:1970`）；`note` 只被 `scan.py:1970` 读一次，写进 HTML 的 `title=` 属性。**没有任何一处把任一字段与它所描述的物件比对。**

`probe_spec_freshness`（`scan.py:675`）只做 `git log -1 -- monitor/spec.py` 再 `rev-list --count <那次提交>..HEAD`，按 `n<15 / <40` 判绿黄红——**纯文件年龄**，不读内容。
`git grep "GRID|offline_done|PAPER_PLAN" c54954d6 -- monitor/tests/` → **零命中**。

### 后果（我推翻了自己委托稿的这一段）

`_offline_done()`（`scan.py:1119`）注册在 `PROBES`（`:1399`），但 `spec.PHASES` 里五处 `"probe":` 绑定（`determinism_state` / `pile_integrity` / `a0_state` / `a1_state` / `credential_hygiene`）**不含 `offline_done`**——它从不进 `_reconcile`，不产生 `verdict_override`，不改变任何条目状态。`monitor/gates.py` 不读探针结果；`monitor/verify.py:80` 只要求 `"grid"` 这个**键存在**、从不看值；`main()` 的返回码与探针无关。

**它的全部产物是 `state.json` 的一个字段、页面上的一段话、控制台的一行。这不是舰队级裁决，是渲染。**
唯一带实质的是 `scan.py:2717` 把 GRID 原样写进**被跟踪的** `monitor/state.json`——陈旧文字被提交入库，此点 `DRIFT-20260729T2230Z` 已记。

---

## claim

`GRID` 三十格手写常量里，十格今日的事实断言不成立——**但十格中八格在写下时是对的，其中两格精确到位（306/18、13/35）**。它们不是判断失当，是**一次刻意的全格审计在 20.4 小时、410 提交、122 合并之内被树跑过去了**。

真正该被记住的量是**保鲜期**：一次人工全格审计不到一天就有三分之一失效，而没有任何机器检查会为此说话。

只有一格是写下即错：**V2**，它把一份 `runs/` 下的溯源冻结快照当现状引用。这一格与其余九格不同类，也是唯一不会随时间自愈的一格。

**不给百分数。**「可证伪 21 格 / 纯标签 9 格」是上报者自定且未声明的切分；换用同样合理的切分，比例在 **37%–85%** 之间摆动。一个随切分规则摆动一倍以上的比率不是度量。

---

## suggest

1. **把十格逐格订正到当前实况，并在每格注解尾部加 `@<rev>` 戳记**（例：`…306 match / 18 stale @fc6f1706`）。最便宜、收益最大：它让读者一眼分开「陈旧」与「错误」，而这正是本轮十分之八的真相。
2. **V2 单独处理，它不是订正问题**：把注解从引 `exam/runs/*/GAPS.md` 改引 `exam/STATUS.md`。**并立一条通则：`runs/<id>/` 下的任何文件都是时刻快照，不得作为现状的依据。** 这是本仓 provenance 约定的直接推论，而 GRID 违反了它。**这条通则的价值大于任何单格订正。**
3. **A3 重写为单一可核来源**（建议 `BUDGET_TABLE.md:119`：$4.3932 / 15 actions）。它现在的三个数出自三个物件，而 12 动作无出处。
4. 唯一值得写的机器检查是**结构性**的：凡 `note` 含 `@<rev>` 戳记，断言该 rev 是 HEAD 的祖先且落后不超过 N 个提交，超过即 xfail。**不要试图核内容**——三十格没有共同 schema，做不了。
5. **不要**给 `_offline_done()` 加执行后果来「让它有牙」。它今天没有牙是**对的**：一个建立在无人核对的手写 `pct` 上的舰队级裁决，比一段渲染文字危险得多。要装牙，先给 `pct` 装探针，顺序不能反。

---

## 立案过程留痕

对抗者**大幅改写了这份报告**，纠正了九条事实，三条承重：

* **「11 格被推翻」→ 8 格是陈旧。** 上一世用的词 `STALE` 是对的，我的 gatherer 把它悄悄升级成了「推翻」。对抗者回到每格的**编写提交**上重算，两格精确到位。
* **「`_offline_done()` 把手写 pct 提升成舰队级相位裁决」——假。** `offline_done` 没有绑定任何 PHASES 条目，永远进不了 `_reconcile`。**这是本周期第三次**有人（包括我自己）把渲染物当成机件——前两次是 `severity: "blocking"` 与 `p1_green`。**这个错误在本 lineage 已经形成惯性，值得写进方法笔记的第一条。**
* **52% 随切分摆动 37%–85%**，且无法核实另外十格是否真被核过——所以百分数删掉。

它还纠正了两处我 gatherer 的误读：`$4.3932 → $0.3932` 是误读（`BUDGET_TABLE.md:244/:247` 以 $4.3932 为名义值，`:478-479` 明写剔除**只在单价里**做）；`budget_exhausted` 是 rehearsal 的真实结局值，我的 gatherer 拿另一次运行的 `FEASIBILITY.md` 去反驳它。

对抗者未能验证：我的 gatherer 是否真的核过另外十格「可证伪」的（若只报了找到假的那些，52% 就没有分母）；`fc6f1706` 时刻所有远程分支上 `freeze/` 是否都不存在（只读不可重建）；`_offline_done()` 印出的「战役线可全速」有没有被某个 agent 读到并据以行动——那是社会后果不是代码路径，按隔离契约未读 dispatch 日志。
