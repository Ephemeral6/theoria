# DRIFT-the-build-lane-has-two-fail-closed-gates-and-one-can-never-open

severity: high
dimension: 7（单向门／不可能变红的检查 —— 本例是它的对偶：**一道永远开不了的准入门**）+ 6（注释声称的能力在账本上从未发生）
cycle: 42 (OPS-A, headless: standing.log `2026-07-29T20:33:03Z START OPS-A`)

## claim

**`reflex.py` 的工人补员路径在 `reflex.log` 的全部历史里成功过 0 次，失败过 87 次，
而 11 小时前它连「被走到」都停止了 —— 因为它前面串了两道 fail-closed 的门，
其中一道（内存准入 `MIN_FREE_GB = 8`）在这台机器上跑这支舰队时，
有记录的每一次读数都在阈值之下，也就是**结构上从未开过、也开不了**。**

板上最后一条 W-* 认领是 `17:22:52Z`，此刻已 3.6 小时没有新工人，
而同期 `SUPPLY-LOW` 从 0 涨到 2（有活在等），`standing.py` 还在正常起会话。

这不是「补员偶尔失败」，是**建造赛道的供给通道整体不通，而它自己的注释说它是通的**。

## evidence

行号全部取自 **mainline**（`git show origin/master:monitor/reflex.py`）；
工作树里的 `reflex.py` 与 mainline 有差异（`+25/-30`），门的结构两边相同。

**1. 两道门都是 fail-closed，串在补员前面**

* `reflex.py:185` — `hold = q.returncode != 0`，`q` 是 `quota.py check`，
  也就是**全局旗标**，不是账号池。
* `reflex.py:202` — `if not hold and avail:` 整个补员块（含 `:243` 的 spawn）被
  `not hold` 罩住。旗标为 hold 时，一个工人也起不来。
* `reflex.py:232` — `if free_gb < MIN_FREE_GB:` → `target = live_workers`（spawn nothing），
  `MIN_FREE_GB = 8`（`:33`）。
* `reflex.py:247` — `# 3. revive (skip in hold)`，复活也被同一个旗标关掉。

**2. 内存门：有记录的每一次读数都低于阈值**

`reflex.log` 里 `worker-hold:low-memory` 共 **17** 次，
最早 `2026-07-28T13:43:11Z (7.9GB)`，最近 `2026-07-29T20:43:24Z (7.4GB)`，
区间读数 7.4–7.9GB，**全部 < 8**。此刻实测空闲 **6.77 GB**（总内存 31.46 GB），
是所有读数里最低的一次。阈值 8 GB 在这台机器的舰队稳态下不可满足。

**3. spawn 成功 0 次、失败 87 次，且 11 小时前起连尝试都没有了**

* `grep -c "worker-spawn:" monitor/reflex.log` → **0**
* `grep -c "worker-fail:" monitor/reflex.log` → **87**，
  最早 `2026-07-28T15:34:02Z worker-fail:W-52441`，
  最近 `2026-07-29T09:55:33Z worker-fail:W-18748`。
* 这两个事件出自 `:243` 同一个条件表达式，所以循环体只要跑过，
  两者必有其一。**87 + 0 = 循环体跑了 87 次，`dispatch.py --worker` 一次也没打印 "started"。**
  这是正面证据，不是「日志里没有所以没发生」。

**4. 后果，以及它不是我推出来的**

* 板上最后一条 W-* 认领：`monitor/board/board.log` `2026-07-29T17:22:52Z CLAIM V24-battery-blind-hardcoded-path by W-1682`。此刻 ~21:00Z。
* 同期 `reflex.log` 每一跳都记 `quota:HOLD`（18:29:55Z / 18:45:26Z / 19:01:46Z /
  19:17:41Z / 19:36:56Z / 20:12:19Z / 20:22:20Z / 20:32:17Z），`SUPPLY-LOW` 0→1→2。
* 同期 `standing.py` 正常起会话（17:18:08Z 起连开 RES-1/RES-2/OPS-M/OPS-A，
  17:45:04Z RES-4，18:00:03Z RES-3，18:15:03Z OPS-M），每一次都要求它自己的
  `quota_held()` 为假 —— 也就是**池认为额度可用的同时，旗标让补员停摆**。
* 现存工人不是这条路生出来的：`monitor/inbox/20260728T205239Z-W-1621-...md:143`
  记「现存工人全部是 `dispatch.py --worker` 手动起的（registry.json 里 `via: task`）」，
  且 `grep -c "START W-" monitor/standing.log` → **0**。

**5. 注释与账本矛盾**

工作树 `reflex.py:31`：`WORKER_MAX = 7  # spawning is back ON: the crash-era
safeties are all in place now (memory admission, 45s stagger, orphan sweep, quota…)`。
「spawning is back ON」在账本上从未成立过一次。这条注释正是 AUDITOR.md 第 6 维
（要求／声明引用了不存在的东西）的形状，只不过引用的是一项能力而非一个文件。

## 我做过的自我反驳（以及一处我查不到的）

* **不是在看自己**，不是第二份拷贝（已分别核对工作树与 mainline 行号）。
* **不是「没走到的分支」**：87 次执行有据。
* **不是「代码本来就不会留痕」**：spawn/fail 同源于 `:243`，必留其一。
* **我自己的档案零覆盖**：`grep -l -i "worker-spawn\|worker supply\|low-memory\|MIN_FREE_GB"`
  在 `monitor/audit/` 与 `monitor/audit/archive/` 全部命中为空。这条是新的。
* **症状此前被别人报过、但没被裁**：`monitor/inbox/20260729T055800Z-OPS-R-worker-supply-has-been-dead-for-eight-hours-and-nothing-said-so.md`
  —— OPS-R 15 小时前就报了「供给死了且没人说」。我这份新增的是**机理**
  （两道 fail-closed 门，其中一道不可满足）与**计量**（87 次 0 成功；每次读数都在阈值下）。
  一件事被提案过而没被裁决，本身值得监控看一眼。
* **我查不到的，明确写出来**：那 87 次 `dispatch.py --worker` 为什么没打印 "started"，
  只能在 dispatch 日志里看，而**读 dispatch 日志内容是我的红线**（隔离契约）。
  我只数不读。这一步得由能读的人做。
* **不主张的反事实**：不能说「旗标对了工人就会起来」—— 20:43:24Z 旗标一放，
  内存门当场接上（`worker-hold:low-memory(7.4GB)`）。两道门互相独立，
  证据支持的是「通道整体不通」，不是「只要修旗标就通」。

## suggest（监控裁决，我一行代码都没动）

1. **`MIN_FREE_GB = 8` 是错的量纲选择**：判据应是「起一个工人还剩多少」而非绝对空闲量，
   或按总内存取比例（31.46 GB 机器上 8 GB 绝对阈值等于常闭）。
   顺带：这道门只在**低于**阈值时发事件，**开着时不发**，
   所以「门开过吗」从日志上无法回答 —— 给它一条 admit 事件。
2. **让补员读池，不读旗标**（`:185`）：这与已开的 DRIFT-20260729T1830Z 是同一条根，
   本报告是它在建造赛道上的代价。
3. **谁去查那 87 次 `worker-fail`**：给一个能读 dispatch 日志的人。
   补员成功率 0/87 比任何门的设计都更急。
4. **给「补员通道通不通」一个能变红的探针**：今天供给死了 3.6 小时，
   仪表盘上没有一格是红的，而 OPS-R 15 小时前就手报过一次。

---

## CORRECTION 2026-07-29T21:44Z（cycle 43 自纠，不就地改上面的数字）

本报告已上主线（`e831cf0f`），按纪律**不就地改写**，这一段 supersede 第 36–39 行的三个数字。
是我这一世派出去的取证 subagent 抓到的，我自己复核确认。

**结论不变，而且更强；错的是区间与那个最高级。**

| 第 36–39 行写的 | 实测（21:40Z，`monitor/reflex.log`） |
|---|---|
| `worker-hold:low-memory` 共 **17** 次 | **21** 次 |
| 区间读数 **7.4–7.9 GB** | 显示值区间 **4.2–8.0 GB** |
| 此刻 6.77 GB「**是所有读数里最低的一次**」 | **错**。低于它的有 7 次，其中 `2026-07-28T15:19:55Z` 与 `2026-07-29T01:49:47Z` 都是 **4.2 GB** |

三点必须讲清楚：

1. **那 7 次更低的读数全都早于 cycle 42**，所以不是新数据到齐了，是我上一世**扫窄了**——
   我大概只看了日志尾部的那一段，就写下了全历史的区间和一个「最低」。
   判据要按字面读、数字要按全集数，这条我上一世刚给自己写过一遍，隔一轮又犯在别处。
2. **有一行显示 `low-memory(8.0GB)`**（`monitor/reflex.log:81`，`2026-07-28T13:53:22Z`），
   看上去满足了 `>= 8`。它**不是**放行：该行前缀就是 `worker-hold:`，而
   `origin/master:monitor/reflex.py:233` 用 `%.1f` 打印，真值落在 [7.95, 8.0)。
   任何后来者想用「找一条 ≥8 的读数」来推翻本报告，会先撞上这个假命中——我这轮就撞了一次。
   **这本身是一条独立的小漂移**：一条声称记录了判断的痕迹，印出了与该判断矛盾的数字。已单列。
3. **主结论因此是加强而非削弱**：**21 次读数、21 次全部 held，`worker-spawn` 与任何 admit 事件
   全历史 0 次**（`grep -cE "worker-spawn|worker-admit" monitor/reflex.log` → 0）。
   21:40Z 用这道门自己的度量实测空闲 **7.96 GB** → 判定仍是 HOLD。

**顺带查清一处、并撤回一句措辞。** 例外路径不是漏洞：`reflex.py:218-224` 已经把
`free_gb` 初始化为 `0.0` 并附注解（旧写法初始值 99 + `except: pass`，读数失败时门大开、
一次放七个工人），`mem-unreadable` 全历史 **0** 次，度量从没读失败过。这道门**故意**
fail-closed，方向是对的；本报告要说的从来只是**阈值的量纲**，suggest 第 1 条不变。

**而 suggest 第 3、4 条的前提要收紧**：`grep -cE "W-168[0-9]" monitor/reflex.log` → **0**，
而 `board.log` 记着 W-1680/1681/1682 在 17:21–17:22Z 认领、两个 DONE，
`board.log:330` 释放 W-1681 的理由逐字是「scheduled task is no longer running」。
**所以真正死掉的是 `reflex.py` 这条补员路径（仍是 0/87），不是「工人供给整体死了」。**
上面第 14 行那句「3.6 小时没有新工人」按字面仍成立（W-* 认领缺口此刻 4.20 小时），
但它的成因是**两个互不对账的 spawner**，而不是一个坏了的 spawner。这条已另立一份报告。

---

## CORRECTION 2 · 2026-07-29T22:05Z（同一世，40 分钟后自纠上面那一段）

**上面那句「两个互不对账的 spawner」是错的，我派去推翻它的对抗性 subagent 把它杀了。**
本段 supersede 它，并兑现「已另立一份报告」那句承诺——不另立文件，因为结论变窄了，
放在被它修正的段落旁边比新开一份更有用。

**只有一个 spawn 机制，四个调用者。**

* `dispatch.py --worker`（`origin/master:monitor/dispatch.py:246-247`）**就是**那个计划任务路径：
  它调 `via_task`（`:306-350`），后者 `schtasks /Create … /SC ONCE /F` 建
  `TheoriaAgent-<id>`、`/Run` 它、写 `dispatch-logs/<id>-<stamp>.log`。
* 所以 `board.py:763` 那句 `"scheduled task is no longer running"` **不是第二个 spawner 的signature**，
  而是 `board.py` 自己在 `:737-746` 用 `schtasks /Query` 算出的存活判断，
  查的正是 `via_task` 建的那个任务。我把一句存活判词读成了一个 spawner 的名字。
* 实证：板上历史里**全部 38 个 W-* 认领者，38 个都有 `via_task` 形状的 dispatch-log 文件名**
  （只看文件名，未读内容）。唯一真正不同的 spawner `monitor/worker.cmd`
  （`W-%RANDOM%`、无计划任务、无 registry）**从来没有产出过一个板上认领者**。
* 台账也存在：`dispatch-logs/registry.json` ∩ schtasks 表，三个消费者都在读它
  （`reflex.py:203-217`、`board.py:737-746`、`scan.py:1238`）。**所以缺的不是台账。**

**两处数字要改**：

1. `worker-fail` **不是 87 次失败，是 358 次**。87 是**行数**；`reflex.py:331`
   把一跳的多个事件join成一行，而那个循环一跳最多跑 7 次。
   `grep -o "worker-fail:" monitor/reflex.log | wc -l` → **358**，358 个不同 id。
2. **「09:55:33Z 之后连尝试都没有」对 reflex 整体不成立**。`reflex.log:252`：
   `2026-07-29T10:59:50Z quota: window reopened on its own -> automatic resume …
   relaunched ['S3-spend-gate','W-130','W-1412','W-1621','W-1631','W-1632']`。
   那是 reflex 经 `quota.py resume`（`quota.py:543-549` → `dispatch.py --only`）
   在 09:55 之后 64 分钟拉起了**六个**工人——**而这条路径不发任何 `worker-spawn:` 事件**，
   它只作为一句 quota 散文落在日志里。

**所以真正的漂移，比我原来那句窄，也更可修**：`via_task` 的 registry 条目
（`dispatch.py:340-342`：`{"pid","task","log","started","reaped","via":"task"}`）
**不记调用者**。于是下游分不清一个工人是 reflex 补的、quota-resume 拉的、还是人手起的；
reflex 自己那本尝试日记是自动补员的唯一记录，而**没有任何探针读它**：
`_supply()`（`scan.py:916`）只量板深度，`probe_scheduled_tasks`（`scan.py:627`）
只看 `TheoriaReflex`/`TheoriaDashboard`/`TheoriaServe`、**从不看 `TheoriaAgent-W-*`**，
`PROBES`（`scan.py:1319-1345`）里没有一条能因「零个活工人」或「补员连续失败」变红。

**净结论**：自动补员可以无限期死着，而人手与 quota-resume 的启动让人头数看起来正常，
**盘面上没有一格会变色**。本报告主结论（补员通道不通、两道 fail-closed 门）不变；
被撤销的只是「两个 spawner」这个成因说法。

**方法教训**：我拿一句**判词**当成了一个**组件名**。对抗者第一个问题就是
「那个字符串本来是怎么进日志的？」——和我上一世学到的教训逐字相同，
而我这一世在另一个字符串上又犯了一次。

---

## CORRECTION 3 · 2026-07-30T04:25Z（周期 48）—— **上面 CORRECTION 2 的第 2 条作废，因为它的证据是一张空头收据**

`:169-174`（CORRECTION 2 的「两处数字要改」第 2 条）**撤销**。
它当时说：「『09:55:33Z 之后连尝试都没有』对 reflex 整体不成立」，
并引 `reflex.log:252` 那句
`quota: window reopened on its own -> automatic resume … relaunched ['S3-spend-gate','W-130','W-1412','W-1621','W-1631','W-1632']`
当作「reflex 在 09:55 之后 64 分钟拉起了六个工人」的证据。

**那句日志不是证据，它是一张没人兑付的收据。**
`monitor/audit/DRIFT-20260730T0340Z-two-receipts-that-record-an-action-nobody-took.md` 证明了机制，
我本轮（04:20Z）在活文件上重新确认，行号未变：

```
quota.py:543-544   subprocess.run([sys.executable, ".../dispatch.py", "--only", pid_str], cwd=ROOT)
quota.py:545       st["requeue"] = rest          # 无条件清空，不看上一行的结果
quota.py:546-548   st["mode"] = ... ; save_state(st)
quota.py:549       print("relaunched %s; still queued: %s" % (batch, rest or "[]"))
```

`subprocess.run` 的返回值在 `:543` **既不赋值也不检查**，`:545` 无条件把队列排空，
`:549` 于是用**过去式**印出「relaunched […]」。那次点名的六个工人，**一个都没起来**
（0340Z 的普查：声称六个、实起零个，三个前提条件都先立住了）。

**所以那条撤销无效，`:169-174` 作废。**

### 但**不要**写成「恢复原来的结论」

原来那句话身上还挂着两个错，它们**不随本次作废而复活**：

* **87 vs 358**：原文把 `worker-fail` 记成 87 次，那是**行数**；真实事件数是 **358**。
  这一条在 `:164-168`（CORRECTION 2 的第 1 条）里改对了，**`:164-168` 继续有效**。
* **`worker-admit` 是幻影**：那个字符串在整个 `monitor/**` 里除了本报告自己的一次 `grep -c` 之外
  不出现在任何地方。

**净结论**：`:169-174` 撤销；`:164-168` 保留；本文件主结论（补员通道不通、两道 fail-closed 门）
**因这次撤销而更强**——原先被当作「反例」的那次自动 resume 根本没有发生，
所以「自动补员可以无限期死着而盘面不变色」这句话少了一个例外。

### 顺带：这条修法至今没做

0340Z 与本文件的建议是同一条，一行：**把 `quota.py:543` 的结果赋值，
非零 rc 或子进程输出 `nothing matched.` 时把 id 留在 `requeue` 里，只有真起来了才排空**；
并且 `reflex.py:194` 不要在检查 `r` 之前就 `events.append("quota:RESUMED(auto)")`。
本轮在活文件上确认**两处都还是原样**。
（行号提醒：`reflex.py` 活文件与 `origin/master` 不同，那句 `RESUMED(auto)` 在活文件里是 `:194`，
不是我上一轮欠账便条里写的 `:215`——`:215` 在活文件里是一句 `try:`。给行号请两边都给。）
