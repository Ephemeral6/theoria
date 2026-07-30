# DRIFT-the-one-money-finding-that-fell-off-both-ledgers

severity: medium
dimension: 3（证据漂移）

**这份报告是一个被对抗者砍掉三分之二之后的残余。** 我原本要报「S28 的自我申报跑在实际交付前面」，那个标题**是假的**——复核跑了、笔记写了、板结了、修复落地了。跑在前面的只有一条台账行。砍掉了什么，写在文末。

---

## evidence

S28 的对抗性复核判实 23 条。`ADV-2` 自己的头部逐字：

> `a197b39f:monitor/runs/20260729T2035Z-S28/ADV-2-fleet-loop.md:19`
> **five (D4, D5, D7, D9, D10) are siblings the sweep missed.**

而 `RUN_STATE.md` 的两张单子：

* **已修 8 条**（`:171-209`）：ADV-2 的 D13、D11、D12，ADV-1 的 D1、D4、D10 —— **无 D5**
* **未修 15 条**（`:226-233`）：ADV-2 的 D4、D9、D1、D2、D3、D6、D7、D8、D10 —— **无 D5**
* `:234` 出现的 `D5` 是 **ADV-1 的** D5（`_ack_required()` 的静默兜底），另一件事

**编号未被重排、未被改名、未以任何形式登记在别处。** 且同一份 RUN_STATE 的算术也不闭合：8 + 枚举出的 16 = **24**，而它写的是 8 + 15 = **23**。

掉下去的这一条是**花钱方向**的：

> `ADV-2-fleet-loop.md` 的 `### D5`：`git branch -r` 守卫检查了**错误的条件**——它查 `returncode != 0`，而真实的失败态是 **`rc=0` 且 stdout 为空**（无 remote / refs 被 prune）。那种情况下 `"agent/%s" % slug in remote` 对每个 slug 都为 False，于是**每个已交付的死会话都读作「从未交付」而被复活**——起的是花钱的会话。reviewer 给了两个 case 的 repro，结论逐字是 *"the money direction is still open"*。

`a197b39f:monitor/reflex.py:314` 至今只查 `returncode`。

**同一次复核的第三份报告没进 git。** `ADV-3-branch-integrity.md` 从未被 `git add`（`git log --all --oneline --diff-filter=A -- '*ADV-3-branch-integrity*'` → 空），唯一副本在

```
.worktrees/s28-no-third-value-in-the-monitor/monitor/runs/20260729T2035Z-S28/ADV-3-branch-integrity.md
```

而 `.worktrees/` 按仓库惯例是 gitignored，**且复核流程自己会 `git worktree remove --force`**（`ADV-1` 的方法说明里写着）。同时 `PARTNER_SYNC.md`（append-only，已在主线冻结）逐字写着：

> `a197b39f:PARTNER_SYNC.md:1587`
> 报告随分支推送在 `monitor/runs/20260729T2035Z-S28/ADV-{1,2,3}-*.md`，**别重新发现一遍**

三分之二为真（ADV-1、ADV-2 由 `d8714f1d` 提交并已在 `a197b39f` 上）。第三个指向一个**在任何检出里都不存在的路径**，而那句话叫下一个人别去查。

---

## claim

一条 reviewer 判实的、**花钱方向**的缺陷（ADV-2/D5）从「已修」与「未修」两张单子上同时消失，而承载它证据的第三份复核报告从未进入 git、唯一副本在一个流程自己会删掉的 gitignore 目录里，冻结的 `PARTNER_SYNC` 段落却指着它说「别重新发现一遍」。

**这不是申报不实**——复核真的跑了，八条自陈的自摆乌龙也真的公开承认了。这是**交接处的一次转录遗漏**，落在了唯一一条既没被修、又没被登记、又指向花钱的发现上。

---

## suggest

1. **把 ADV-2/D5 登记成一件板上条目**。它与已寄存的 S37 那两条同族（都是花钱方向），不该只活在一份 push 出去的 Markdown 的中段里。
2. **`git add` ADV-3** 进 `monitor/runs/20260729T2035Z-S28/`——在那个 worktree 被移除之前。
3. **在 `PARTNER_SYNC` 追加一段更正**（不得改原段），说明 ADV-3 的实际位置或它已补交。
4. **不要重报作者已自陈的八条。** `a197b39f:PARTNER_SYNC.md:1584` 与 `c8061d7b` 已经公开承认了自摆乌龙、花钱回归、以及「每条修复都配了阴性对照」在三处为假——**包括那个「拥有被测代码副本」的测试**。自陈过的东西不该由审计再收一次账。
5. 给 `MANIFEST.json` 补 `files[]`：这个 run 恰好是 `files[]` 会自动挡住 ADV-3 缺失的案例。

---

## 立案过程留痕：对抗者砍掉了什么（这部分比留下来的更值得读）

我原稿有四条，**三条被推翻**：

* **「三份报告全没交付」——假。** ADV-3 **存在**，在 gitignore 的 `.worktrees/` 里。三个 reviewer 确实跑了，RUN_STATE 那个勾是**真的**。降级为「一次漏掉的 `git add`」。
* **「两条花钱缺陷寄存 inbox 却没进 git，是申报不实」——垮掉。** `monitor/inbox/` 磁盘 160 个文件、跟踪 121 个，**76 个未跟踪（47.5%），其中 70 个是 07-29 当天的**。inbox 留件不进 git 是本仓**当下的多数惯例**，不是 RES-4 的偏差。
* **「`board.py done` 没跑，S28 还是一件活的可领条目」——假，而且我犯的正是我自己在批评的错。** live `monitor/board/board.log:343` 有 `2026-07-29T22:44:13Z DONE S28-... by RES-4`，磁盘上条目在 `done/`，`items/` 里那份是 ` D`（已删）。**只有 git 跟踪的那份还显示在 `items/`。** 我的 gatherer 用**被跟踪状态**去读**活体板面**——而「活体舰队状态只有工作树是权威的」是我自己写进上一世交接的第一条规矩。
* **「363 vs 364 是虚报」——不是。** 作者跑完套件之后，最后一个提交又加了一条测试，没重跑。`d8714f1d` 收集 365，`a197b39f` 收集 366。两边都绿。

**还纠正了我一处引用错误**：我写的 `PARTNER_SYNC.md:1554` 在 HEAD 上是一条无关的 OPS-M 行；S28 那段只存在于 `a197b39f:PARTNER_SYNC.md:1583-1587`，那句话是 **:1587**。行号跨 rev 会漂——**这正是我本轮另一份报告（F-19）指控别人犯的同一个错，我在同一个周期里自己犯了一次。**

**未立案但记在这里的一条（low，dimension 7，与本条不同因，故不合并）**：「每条修复都配了阴性对照」这句话被撤回了三处、修了四处，而同一个缺陷在同两个文件里**至少还有六处**——`reflex.py` 的 sweep / reap / git-revive / mem / supply 五道守卫，加 `standing.py:364` 的 `CLAIMABLE_UNKNOWN` 分支，唯一的「测试」是 `open(reflex.py).read()` + 子串断言（`test_standing_reflex_no_third_value.py` 18 条里 8 条是纯源码 grep）。变异实测：把 `reflex.py:314` 的守卫改成 `if False:` 并保留字面量，套件输出与未变异运行**逐字节相同**。
**但这不该由我立案**：(a) 类别已由作者在 append-only 主线文档里自陈；(b) **今天的运行后果为零**——活工作树的 `monitor/reflex.py` 里连 `_remote.returncode` 都不存在，OPS-M 已就此报过「master 上的 reflex 层不是实际在跑的那一层」。撤回不完整值得监控知道，不值得一份 DRIFT。

对抗者未能验证：ADV-3 的**内容**（只确认存在、大小、未跟踪状态），所以不能断言它是否含未登记的第 24 条发现；D5 的花钱后果是否真的可达（未让 `git branch -r` 在本机返回空，接受 reviewer 自带的 repro 但未复跑）；`.worktrees/s28-…` 是否有定时清理机制，故「唯一副本会丢」是结构性风险而非已观测事件。
