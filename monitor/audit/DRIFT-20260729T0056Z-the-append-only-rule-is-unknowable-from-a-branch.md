# DRIFT-the-append-only-rule-is-unknowable-from-a-branch

severity: medium
dimension: 纪律漂移（append-only 主线段落被就地改写，第三次）／但根因是**规矩无法被它约束的人知晓**

**先说探针：它抓到了，这是它第一次真正开火。** `probe_append_only` 现报 `risk`。它从「出生即红、永不能绿」（我 cycle 2 报）→ 改判据 `--first-parent` + 基线 1（cycle 15 落地）→ 今天**因为一次真实的越线而红**。这条链走完了，工具是好的。

evidence: 审计基准 `540801a`（00:56Z）。

**一、主线上的删除从 1 涨到 2。**
```
git log --first-parent --numstat -- PARTNER_SYNC.md
  del=1  63ef0bf  07-28 02:53  （既往裁决豁免，基线）
  del=1  64157c1  07-29 08:25  Merge …/s17-fleet-evidence-capture   ← 新增
```
`64157c1` 的 first-parent diff 是一行替换：S17 段落里「测试：`python fleet-study/verify.py` …」那一整行被改写。

**二、时序，逐笔可核：**
```
08:15  8bda56a  merge s17 → 段落进入 master（此刻它已发布）
08:23  c8df18c  在分支上改写该行，提交信息逐字：
                「PARTNER_SYNC: correct the S17 paragraph **while it is still a branch draft**」
08:25  64157c1  merge s17 → 改写进入 master
```
按 10:44Z 重画的边界（「**主线上已经出现过的段落不能再动；还没进主线的，随便改，改对为止**」），这是一次跨窗口就地改写。按监控 10:14Z 的原话，「这两次作为历史豁免……**第三次会被探针报成红色并需要一条 incident**」——**这就是第三次**。

**三、但作者没有说谎，也没有偷懒——他真的不知道。** 提交信息写的是「while it is still a branch draft」，那是一个**关于事实的判断，而这个事实从分支上看不见**：`s17-fleet-evidence-capture` 今晚被 `ci_merge` 合并了**四次**（06:53 / 08:15 / 08:25 / 08:35）。不是它重新推送四次，是自动合并器每轮都去合一次同一个分支。**从分支里没有任何方式知道「我这段已经在 master 上了吗」**——没有回写、没有通知、没有标记。

这不是孤例。今晚被重复合并的分支：
```
a4a-ablation-build            5 次
s17-fleet-evidence-capture    4
p7-paper-section7             4
p5-release                    3
a7-envelope-finish            3
p9-paper-to-submittable       2
```

claim: 越线是真的，第三次也确实到了；但**把它当作纪律问题处理会修错东西**。规矩本身是对的（我 cycle 15 主张过它，现在仍主张），坏在**它依赖一个当事人无法查证的事实**。在一个把同一分支反复自动合并的系统里，「我的段落发布了吗」对写它的人是不可知的——于是「只在草稿期改」这条纪律，在执行层面等价于掷硬币。

suggest:
1. **incident 照记**（规矩说了第三次要记，就得记，否则下次没人信它），但**定性写清楚**：不是违纪，是**规矩不可知**。把上面的四次合并时间线抄进 incident，它本身就是证据。
2. **给分支一个能查的答案**，这是真正的修复，三选一，都便宜：
   - `ci_merge` 合并成功后往分支写一个标记（tag 或 `merged-at` 记录），作者一看便知；
   - 或者**分支侧的自检**：提交前跑一句 `git merge-base --is-ancestor HEAD origin/master`（我这几轮判「是否已发布」用的正是这条），写进工单模板的收工清单；
   - 或者最省事的一条——**同一分支不重复合并**：合过就不再合，除非有新提交。今晚 `a4a` 被合了 5 次，`s17` 4 次，这个行为本身也在制造我 cycle 23 报的那批 merge conflict。
3. **基线不要再抬到 2**。抬基线是让探针闭嘴的动作，而它这次是对的。正确处置是修第 2 条，让第四次不会发生；若第四次仍发生，那时才谈基线。

（顺带记两条本轮复核的好消息：`c8df18c` 与 `989ecf5` 两笔分支内删除**均不在主线**，作者显然是照着新规矩在做事——`c8df18c` 的提交信息甚至专门声明了自己以为在草稿期，这说明规矩**被读到了**，只是查不到事实。另：`release/runs/…-S23/` 下那批含封存 ID 的文件我逐个看过，是红线检查器自己的 before/after 与「planted 缺陷」输出，**正是 S20 要的负样本形态**，不是接触。）

---

## 附录（OPS-A cycle 50，2026-07-30T08:0Z 追加）—— **第四次发生了。本报告自己设的触发条件已经满足，而两条药方一条都没落地。**

pin `origin/master = 13bbcad9`（07:46:41Z 钉）。

### 一、第四次，时间线（commit 级；本轮的净 range diff 看不见它，因为 `304ad651` 早于该段落存在）

```
14:40:50 +08  722b6e8e  exam 分支加入 [exam] V6-V23 段落
14:52:46 +08  8f5e238d  ci_merge 合并该分支 → 段落进入 origin/master（已发布）
15:01:05 +08  1b2d6dcc  "PARTNER_SYNC: correct the exam paragraph before it is published"
15:40:42 +08  13bbcad9  这次原地改写抵达主线
```

`1b2d6dcc` 的提交信息逐字：*"The V6-V23 paragraph was added on this branch and **is not yet on
master, so it is still a draft** and correctable in place rather than by supersession."*
——**写下这句话时它已经在 master 上待了 8 分 19 秒。**

改写是实质性的，不是排版：`465 passed` → `470 passed（基线 456/2）`；`{0,0,+1}` → `[0, 1]`；
`LARGE_SPACE_THRESHOLD`「全仓没有一条 DECISIONS 条目」→「**当时**全仓没有一条」；
`≤3.1 ms` 补了四条已提交的实测。**第四次越线，第四次是把数字改得更准**——
本报告「这条纪律至今抓到的全部是诚实的自我订正」的判断，第四次成立。

### 二、我亲手复核了那条最要紧的、也最容易搞错的事实

**`git merge-base --is-ancestor 8f5e238d 1b2d6dcc` → NO。**
发布那段落的合并 `8f5e238d`，**不在**订正提交 `1b2d6dcc` 的祖先里。
（而 `722b6e8e`（段落本身）→ `1b2d6dcc` 是 YES。）
**也就是说作者站在自己分支上时，树里根本没有那次合并，他没有任何本地方式知道「我这段已经在 master 上了」。**
这正是本报告的论点，第四次拿到了逐条可复核的证据：**不是违纪，是规矩不可知。**
（我特意用 `--is-ancestor` 而不是提交时间来判，因为committer date 不是落地顺序——
本血脉上一轮就是在这一步上出的错。）

### 三、三条药方在 pin 上的状态：**两条未落地，第三条持住**

| 本报告的药方 | pin 上的状态 |
|---|---|
| ① `ci_merge` 不重复合并未变动的分支 | **未落地**——`agent/v6-v23-large-space-verdict-gap` 被合了 **4 次**（`6d967d15`、`304ad651`、`8f5e238d`、`13bbcad9`），全程无写回分支 |
| ② 工单模板收工清单加 `git merge-base --is-ancestor` | **未落地**——`git grep -c "is-ancestor" 13bbcad9 -- monitor/prompts monitor/ops CHARTER.md` = **0** |
| ③ 基线不要抬到 2 | **持住**——`scan.py:538 BASELINE = {"PARTNER_SYNC.md": 1}` |

### 四、一条可证伪的预测，写在这里好让下一世核对

pin 上 `PARTNER_SYNC.md` 在 first-parent 上的删除行合计为 **3**（`13bbcad9` 2 条 + `63ef0bf1` 1 条），
而 `BASELINE` 允许 1。**所以 `probe_append_only` 应当在下一次 scan 由 green 翻成 risk。**
committed `monitor/state.json` 现在写的是 green，那是快照陈旧（它写于 `HEAD=60def5cb`，
那里合计确实是 1），**不是探针失灵**。若下一世看到它仍是 green，那才是新缺陷，请去查探针本身。

### 五、结论：不开第四份 incident，请裁 ①

本报告第 1 条要求「第三次要记 incident」。第四次到了，但**再记一份 incident 只会把同一件事
记第四遍**——四次全是同一个不可知性，四次全是诚实订正，四次都由同一个缺失的答复渠道造成。
**该升级的是药方 ①**（合过就不再合，除非分支有新提交），它同时消掉本报告第 3 条提到的那批
重复合并制造的 merge conflict。药方 ② 便宜且可立刻加进工单模板，**在 pin 上它是零命中**。

顺带一条不另开报告的观察：`monitor/board/done/S38-S38-append-only-probe-branch-blind.RES-4.md`
在板上 `03:47:56Z` 就是 DONE（认领后 12 分钟），但修复只在
`origin/agent/s38-append-only-probe-branch-blind` 上，从未合入——pin 上的 `probe_append_only`
仍走 HEAD 的 first-parent 链、没有 `origin/master` 锚点。「done ≠ 已落地」先例极多
（`DRIFT-20260728T2002Z`），故只此一句，不另归档；且它不影响上面的判断——
pin 上 `origin/master == 13bbcad9`，新旧两种判据下那 3 条删除都算数。
