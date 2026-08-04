priority: 2
cell: S52
territory: monitor
deps: none
spend: none

# S52-the-inbox-is-a-drop-box-nine-of-ten-addressed-asks-were-never-seen · 跨领地唯一的通道没有投递、没有回执、没有过期，而它今天比早上更糟

`CLAUDE.md` 把 `monitor/inbox/` 定为跨领地请求的唯一通道。它是一个**投件箱**：
发件方写一个文件，**没有任何东西把它送到收件方手上**——没有投递、没有回执、
没有过期。今天早上一次手工对账报了 21 件里 11 件收件方从未看见；本件把那次
对账做成可复算的，并回答它有没有好转。

## 今天的数，可复算

`python monitor/inbox_recon.py`（本件交付，`monitor/tests/test_inbox_recon.py`
七条测试，含三条负样本），2026-08-04 于 master `4846e66d`：

```
open asks          : 235
archived (swept)   : 37
addressed by name  : 10
no addressee       : 225
cited elsewhere    : 225
uncited            : 10   (upper bound on asks that went nowhere)
seen by addressee  : 1
NOT seen by it     : 9
no addressee named : 225   (absent, not zero -- nobody could sweep)

addressee          open  cited  uncited   seen  unseen
battery               1      0        1      0       1
exam                  3      3        0      0       3
freeze                1      1        0      1       0
proxy                 1      1        0      0       1
theoria-arm           4      3        1      0       4
unaddressed         225    217        8      0       0
```

**十件写明了收件人的 ask，九件收件方领地里一个字节都没提过它。**
唯一被看见的是 `20260801T0400Z-exam-to-freeze-u3-vacuous-label.md`
（`freeze/` 里有引用）。四件积在 theoria-arm 门口，三件积在 exam 门口。

「有没有好转」的答案：**没有，而且分母变大了。** 早上那 21 件是手数的近期切片；
按同一把尺子（收件方领地里是否提过）今天是 10 件里 9 件未见。更重的一条是
另一个数：**235 件里 225 件的文件名里根本没有收件人。** 它们不是被忽略，
是**没有人可以忽略它们**——即使明天就有人来扫箱子，也扫不出这 225 件该给谁。
所以这 225 件按 `None` 记，不按 `False` 记：缺席不是零，这是本仓库的规矩，
也是这个工具的三条负样本之一钉住的东西。

## 「未被引用」不等于「没被读」，而这条反例本身就是本件的论据

工具量的是**引用**，不是阅读，方向已知：它**高估**未见。今天就有一个现成的
反例：`20260731T1731Z-battery-to-theoria-arm-curves-shortfall.md` 报了
`curves.json` 少算最后一次计费调用（r2 −$1.63、r3 −$1.68，总额低报 12%–17%），
工具读它 UNSEEN；而 `theoria-arm/armtools/curves.py` 的
`82e8e25e`（2026-08-01）标题正是「the turn that died in flight took the leg's
most expensive call with it」——**臂修了，只是没有引用那封信**。

**这不是工具的失败，这正是要修的东西。** battery 至今无从知道自己的通报被
采纳了。一个没有回执的通道，发件方唯一能做的是隔几天自己去读对方的代码。

## S45 就是这个病的临床样本

`S45-launch-blockers-915-916-and-the-reason-floor`（freeze 领地）逐字写着：
exam 于 2026-08-01T00:00Z 把 9.15/9.16 的实现连命令一起送进
`monitor/inbox/20260801T0000Z-exam-endpoint2-prereg-and-two-launch-blockers.md`，
`freeze/launch_blockers.json` 与 `STATS_RULES.md` **至今零提交**——「这条 ask
无人认领」。整个冻结队列停在一件已经交到门口的东西上。S45 存在，是因为有人
碰巧读到了那封信；本件是要让下一封不必靠碰巧。

## 欠的是什么

1. **收件人成为格式的一部分。** `monitor/inbox/README.md` 今天的格式是
   `<UTC>-<from>-<slug>.md`，收件人是发件方自愿加的 `-to-<territory>-` 中缀。
   把它变成必填，并让一个检查在收件人缺失或不是已知领地时拒绝。
2. **回执是一行，不是一次会面。** 收件方在自己领地的任一被跟踪文件里引用该
   文件名即算已读——这已经是本工具的判据，把它写进 README 当作约定，就把一个
   事后统计变成一条双方都知道的规矩。
3. **积压进入监控的常规扫描。** `monitor/scan.py` 已经每轮扫仓库；
   `inbox_recon` 的 `unseen_by_addressee` 与最老一件的年龄挂进去，超过阈值就
   在板上开件——**这是本件唯一真正改变机制的一条**，前两条只是让它可测。

## 验收

`inbox_recon` 的 `unseen_by_addressee` 进入监控的常规扫描输出；README 的格式
写明收件人必填与回执约定；对今天这九件各开一件板上工单**或**在 README 记明
为什么某一件不需要（例如已由代码修掉的 curves 那件——记明它，正好也把回执的
形状示范一遍）。

## 负样本，两条（工具侧的三条已在 `tests/test_inbox_recon.py`）

* **一封收件人为空的 ask 必须被格式检查拒绝，而不是被记成「收件人 = 监控」。**
  今天 225 件是这个形状；如果新规矩把它们默认归给监控，那监控的门口一夜之间
  堆起 225 件，而其中绝大多数根本不是给监控的——把无主变成有主，比无主更坏。
* **一封被收件方**在自己领地外**引用的 ask 必须仍读作未见。**
  监控的 audit 文件今天引用了 217 件；一个把这些算成投递成功的对账器，
  会把监控自言自语报成一条健康的通道。这条已由
  `test_a_citation_from_the_wrong_territory_is_not_delivery` 钉住，
  格式改动后必须仍绿。
