# DRIFT-first-parent-lost-two-adjudicated-crossings

severity: medium
dimension: 监控自身漂移（一个判据在拓扑变化后静默改口）／**这条判据是我 cycle 15 主张的，责任在我**

**先交待用户点名要看的那件事，它是好消息**：`HELD` 出来了，而且效果比我预期的大。见文末「附：改动的生产验证」。

**这条报告说的是另一件事：我给 `probe_append_only` 提的判据，今天自己把两条已裁决的越线弄丢了。**

evidence: 审计基准 `de90ba90`（10:06Z）。

**一、计数从 3 掉回 1，探针从 risk 变回 green。**
```
git log --first-parent --numstat -- PARTNER_SYNC.md   →  累计删除 1 行（cycle 30 时是 3）
probe_append_only（state.json）                        →  green
```

**二、两条越线并没有被修复，它们只是离开了被测量的那条路径。**
```
63ef0bf  baseline-arms 那次   仍在 first-parent 上：True
64157c1  merge s17（cycle 27 报）  仍在 first-parent 上：**False**   而 reachable from master：**YES**
87a1e63  merge e16（cycle 30 报）  仍在 first-parent 上：**False**   而 reachable from master：**YES**
```

**三、成因是一次回并（back-merge），可逐行看：**
```
git log --first-parent --oneline master
  …
  28ced40e audit: cycle 32 …
  fec3f106 Merge branch 'master' into agent/a7-envelope-finish     ← 主线的一等父从这里拐进了分支
  98b89780 Merge branch 'master' into agent/a7-envelope-finish
  54fe59fc PARTNER_SYNC: address the Theoria track directly …
```
`a7-envelope-finish` 把 master 并进了自己，随后这条线成了 master 的一等父路径。于是**此前在主线上的提交整体挪到了二等父那一侧**，`64157c1` 与 `87a1e63` 一起被挪走了。没有人删除任何东西，没有人改写历史——**只是「主线」这个词指向了另一串提交**。

claim: `--first-parent` 不是「这段有没有公开过」的稳定身份。回并会让它整体改口，而它一改口，纪律台账就少了两条**已经发生、已经被裁决**的记录，且探针会从红变绿——**变绿的原因不是问题解决了，是问题走出了取景框**。这正是我这一晚反复报的那个形状（一个自信、但已与所指之物断开的判据），而这次是我在 cycle 15 力主的那条判据，我当时用它否掉了监控原本的豁免表方案。**这一条的责任在我。**

suggest:
1. **判据改成「可达性 + 发布时点」，不要用一等父**。对每一笔删除提交问一句：**被删掉的那一行，在这笔提交落地之前，是否已经从 master 可达？** 是则越线，否则是合并前的自我订正。这个问法不受拓扑重排影响，因为它问的是历史事实而不是当前视角。可用 `git merge-base --is-ancestor <删除所在提交的父> <当时的 master>` 之类固化，或更简单：**记录裁决当时的判断结果，而不是每次重新推导**。
2. **豁免表按 SHA 记，不要按计数记**。`BASELINE = {"PARTNER_SYNC.md": 1}` 这种「允许 N 行」的写法有两个毛病：计数会因拓扑漂移，而且它不说明**豁免的是哪一次**。监控最初写的就是 SHA 加理由，我把它改成了计数——**那一步是我改错了方向**，建议改回去：`{"63ef0bf": "同窗口自我订正，2026-07-28 裁决"}` 这种形态既稳定又自解释。
3. **这两条已裁决的越线要留在台账上**。它们的结论（「规矩不可知，根因是分支无法查证自己是否已发布」）没有因为拓扑变化而失效；`ci_merge` 那边的修法（我这轮已落地的 hold）也没有解决「作者怎么知道自己发布了」这一半。建议把两条连同定性写进一份固定的记录，不再依赖任何 git 查询去重建。
4. 顺带：这也解释了为什么第 3 条重要——**今天之后，任何想复核这段历史的人，跑一次 `--first-parent` 会得到「只发生过一次」的答案**，而真实是三次。

---

## 附：`HELD` 的生产验证（用户点名要看的那件事）

**出来了，53 条**，最近一条 `09:58:51Z HELD 13 unchanged since last verdict: …`。取前后各 6 小时的对照窗口：

| 窗口 | FLAG 行 | 涉及分支 | HELD | MERGED |
|---|---|---|---|---|
| 改动前 6 小时（22:00–04:00Z） | **462** | 29 | 0 | 35 |
| 改动后 6 小时（04:35–10:35Z） | **6** | 5 | 53 | 22 |

**FLAG 行 462 → 6，约 77 倍**，而合并仍在进行。

**没有分支被错误地长期扣住**：逐个 flag 文件比对记录的 tip 与分支当前 tip——**14 个 tip 未变（扣得对），0 个「tip 已变却仍卡着」**。这是 hold 能松开这一性质在生产上的验证，不只是单元测试里的。

一个要说清楚的限定：`MERGED` 从 35 降到 22。**我不认为这是 hold 造成的**——等待的分支本来就少了（积压在这段时间被清掉大半）——但我没有办法把这两个原因彻底分开，所以如实写在这里，不当作改动的功劳，也不藏。

（红线：本区间 102 文件，封存 ID 仅 PARTNER_SYNC 的污染登记；密钥零命中；`battery/PREDICTIONS.md` +95 行为纯追加。判据脚本 `scratchpad/redline.py` 本轮随会话丢失后已按 state.json 的交接说明重写——那条「脚本会消失但逻辑很短可重写」的笔记今天第一次被用上。）
