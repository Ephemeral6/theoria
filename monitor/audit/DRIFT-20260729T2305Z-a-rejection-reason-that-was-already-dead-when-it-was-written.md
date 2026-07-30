# DRIFT-a-rejection-reason-that-was-already-dead-when-it-was-written

severity: medium
dimension: 3（证据漂移），旁及 8（监控自身漂移）

evidence:

四处逐字带着同一句驳回理由（两个文件，rev `c54954d6`，在 `a197b39f` 上逐字不变）：

* `monitor/spec.py:597-598` —— F-19 的正文
* `monitor/spec.py:631` —— F-19 的**订正段**，「驳回仍然有效，但只剩三条：66 条 bypass_attempt、**级联裁决自相矛盾**、以及门本身 9/16 加 INC-TA-001 未修。」
* `monitor/board/claimed/A3-campaign-devpile.RES-1.md:34-35` —— 条目正文
* `monitor/board/claimed/A3-campaign-devpile.RES-1.md:74-75` —— 在「**仍然成立、驳回继续有效的理由：**」标题下作为第 2 条，并追加「（S24 在合）」

那句话是：「`CASCADE_RULING.md` 只在未合并分支上，master 的 `ACCESS_CHECK.md:105` 还写着相反的结论」。**两半都假，而且在写下时就已经假了 10 小时 19 分。**

```
$ git ls-tree origin/master --name-only arc-recon/ | grep -i cascade
arc-recon/CASCADE_RULING.md
$ git log --format='%h %aI' -- arc-recon/CASCADE_RULING.md
7a3fb304 2026-07-28T22:42:08+08:00
$ git log --format='%h %aI' -1 7b8d3d9b          # F-19 落盘的提交
7b8d3d9b 2026-07-29T09:01:56+08:00
$ git merge-base --is-ancestor 7a3fb304 7b8d3d9b && echo ancestor
ancestor
$ git ls-tree 7b8d3d9b arc-recon/CASCADE_RULING.md
100644 blob 36f4206e...
```

两个提交同为 `+0800` 且 `%aI == %cI`，Δ = 10h19m48s。**F-19 自己那次提交的树里就已经有这个文件。**

同一个 `7a3fb304` 把 `ACCESS_CHECK.md` 里那句相反结论划掉了。今天 master 上该文件四处与裁决**一致**，无一处相反：`:14`（行 4 引 `CASCADE_RULING.md`）、`:135`（「**The ruling is `CASCADE_RULING.md`**……Cite that; this section is the access-check row, not the adjudication」）、`:146-148`（`~~The environment has an internal tick……~~ **Withdrawn.**`）、`:158`（`step` 冻结为 `S → A → S` on `frames[-1]`）。

**行号本身有话说，这是本条最该被读到的一句：**

```
$ git show 7a3fb304~1:arc-recon/ACCESS_CHECK.md | sed -n '105p'
**2**. `frame` is always a list. The environment has an internal tick, so `step`
```

裁决**前**那一版的第 105 行，**逐字就是那句相反结论**。所以「`ACCESS_CHECK.md:105` 还写着相反的结论」不是虚构，是**对着一份被同一个 commit 取代掉的工作副本引用的**。作者引得准确，引的是死掉的那一版。（在 F-19 自己的树里，`:105` 已经是 `## 3 · Scorecard semantics`。）

claim:

一条 2026-07-28 22:42 就被 master 自己修掉的前提，**在写下时已过期 10 小时**，此后经**两轮订正仍被显式保留**为幸存驳回理由——`spec.py:631` 把它列进「只剩三条」，`A3:74-75` 把它列进「仍然成立」清单并追加「（S24 在合）」，即在订正的动作里重新断言了一遍假前提。订正机制照常运转，只是没人回去核前提。

**同时订正我自己上一世的判断（这半部比上半部更重要）**：cycle 43 的 `owed_next_cycle` 把这条记成「a spend gate held shut by an expired reason」。**那是错的。`severity: "blocking"` 在全仓没有任何执行后果。**

* `blocking_findings`（`scan.py:2666`）**一写零读**——`state.json:907` 是数据，`papers/.../P-16.json:74` 是同名无关键。
* 唯二特判 `severity == "blocking"` 的消费点是首屏「需要你处理」横幅：`scan.py:1909` 与 `app.html:217-218`。**两处都额外排除标题含「已裁决/已解决」的条目**，而 F-19 的 title 正是【已裁决·监控代行 2026-07-29】——它连横幅都进不去。其余全部命中（`scan.py:1524` 计数、`:2058-2059` 与 `app.html:320-321` 的 HTML 徽章、`:2655` 排序键、`:3112-3113` 的 CLI 打印）都是渲染。
* `reflex.py` / `standing.py` / `quota.py` / `gates.py` / `verify.sh` 对 `FINDINGS`、`blocking` **零命中**。`monitor/spec` 只被 `scan.py` 与 `board.py` 导入，后者从不碰 `FINDINGS`。
* 真正的代码闸门是 `board.py:288-291`（`spend == "api"` 且 `generic_ok not in ("yes","true")` → `continue`），它读板上条目，不读 FINDINGS；且对 A3 今天不触发（A3 在 `claimed/`，而 `candidates()` 只遍历 `items/`）。

**这是本 lineage 第二次把渲染物读成机件**（上一次是 cycle 43 把 `board.py` 计算出的存活裁决短语读成一个竞争 spawner 的名字）。把这条写进方法笔记比修 F-19 更值钱。

suggest:

1. **在 `spec.py` F-19 的 action 段追加第三次订正，撤回「级联裁决自相矛盾」这条幸存理由**（驳回剩两条：66 条 `bypass_attempt`、门本身 9/16 + INC-TA-001 未修），并同步 `A3-campaign-devpile.RES-1.md:74-75`。一条已死的理由留在「仍然成立」清单里，下一个读它的人会照着施工。
2. **顺手修 `theoria-arm/harness/campaign.py:791`**：它把一个计算值「`monitor/state.json` currently reports p1_green 9 of 16」**硬编码进拒绝信息**。它长得像一道读 `state.json` 的闸门，其实不是（真实拒绝条件在 `:784`，是 `--i-have-authorisation` 这个静态旗标，helptext 自己写明「Neither is checked here」）。同一缺陷族：手抄的数没有任何东西交叉核对。
3. **不要为 `p1-cascade` 另立案。** 它的 note 三句话确实被 `CASCADE_RULING.md:17 / :57-66 / :114-129` 逐条推翻，但（a）这是**第三次出现**——`monitor/inbox/20260728T152500Z-W-1250-two-phase1-items-can-go-green-and-their-notes-are-stale.md` 43 小时前就逐条报过且仍未归档，`monitor/audit/state.json:80` 已把它列进「22 stale spec.py rows」；（b）`p1_green` / `p1_total` / `p1-cascade` 与 `severity: blocking` 一样**零执行消费者**，所以「它压着钱门」是假的；（c）裁决自陈 G-1..G-4 四个缺口未闭（`CASCADE_RULING.md:181-189`，§4 明确把 `cascade single_frame` 标为 **Ruled**（可被证据修订）而非 **Frozen**），**所以 `partial` 是站得住的**。按复发记录，不另立案。

---

## 立案过程留痕

本条经一个专门找反例的对抗者审过，**它推翻了 gatherer 的两个结论**，并把第三个削窄：

* **杀掉**「真正有闸门形状的是 `p1-cascade`」—— gatherer 自己的脚注写了「`p1_green` 也只被渲染消费」，结论却仍称它「真正有闸门形状」。**它把一个渲染物换成另一个渲染物，然后给新的那个起名叫闸门。**这正是本条 claim 半部在批评的错误，gatherer 当场又犯了一次。
* **杀掉**把 `p1-cascade` 的陈旧 note 当新报告（第三次出现，且第二次是我自己 lineage 的 `audit/state.json`）。
* **削窄**「一格该绿没绿」为「一段 note 写陈旧了」——G-1..G-4 未闭使 `partial` 可辩护。
* **补上** gatherer 漏掉的最强证据：`7a3fb304~1:105` 逐字就是那句相反结论。gatherer 只走到「今天 :105 不是那句话」就停了，那个版本既弱又不公平。

对抗者未能验证：F-19 的作者是否**真的**持有陈旧检出（行号吻合是很强的旁证，不是证明；按隔离契约未读任何 dispatch 日志或 transcript）；`S24` 的状态；监控是否会裁 `p1-cascade` 转绿（那是监控的判断权，不是可审计的缺陷）。
