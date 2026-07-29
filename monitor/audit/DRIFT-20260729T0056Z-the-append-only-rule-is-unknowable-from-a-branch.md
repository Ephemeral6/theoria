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
