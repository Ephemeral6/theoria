# DRIFT-CRITICAL-the-guard-that-was-carried-out-is-the-one-that-caught-this

> ┌─ 更正 1（10:20Z，由我派去打本报告的对抗性复核提出，全部采纳）─────────────────────────────
> │ 本文件 10:10Z 首发，20 分钟后按复核结论**原地重写**。原文错了五处，其中一处错得最难看：
> │ **(1) 我的十六进制换算是错的，而错出来的那个值正好是「证明」我论点的那个值。**
> │ `-2147020576` 的 uint32 是 **`0x800710E0`**（低位字 `0x10E0` = **4320**，本机自带的错误表读作
> │ 「The operator or administrator has refused the request」），**不是**我发布的 `0x80070420`
> │ （那个数的十进制是 `-2147023840`，低位字 `0x0420` = 1056「服务实例已在运行」）。
> │ 我把 1056 的措辞当成了 4320 的含义——**坏算术自己制造了它需要的确证**。已自行复算确认（`v & 0xFFFFFFFF`）。
> │ 「八次触发被拒」这个结论仍然成立，但**成立的依据换了**：任务 XML 的
> │ `MultipleInstancesPolicy: IgnoreNew`（复核读出）才是拒绝的机制，不是那个错值。
> │ **(2) 那次观测现在永久不可复核**：10:57 本地重查得 `Last Result: 0` / `Status: Ready` / `MissedRuns: 0`
> │ ——任务计划器把 `LastTaskResult` 覆盖掉了，而 `Microsoft-Windows-TaskScheduler/Operational`
> │ 通道 `IsEnabled: False`（复核拒绝启用它，对；启用是变更本机）。这条数据只剩我的记录，且
> │ `DRIFT-20260730T0019Z:206-207` 早就要求把它落盘，正是为了避免这种情形。
> │ **(3) 「唯一判据」是错的**：`scan.py:661` 还有第二条判据（`out.returncode != 0` → 「未注册」→ risk），
> │ **而探针此刻正因 `TheoriaServe` 未注册而是红的**。正确的说法是「它对**这一种**故障不可能变红」。
> │ 更锋利的一点也是复核给的：探针查的是 `/FO LIST`（**不带 `/V`**），那种输出里**根本没有 `Last Result` 这一栏**——
> │ 是取数遗漏，不是逻辑遗漏。
> │ **(4) 看门狗这一整段是先例，而且是我自己血脉的先例。**
> │ `monitor/audit/DRIFT-20260730T0346Z:112-117` 逐字写着「它从不读 `Last Run Time`、从不读 `state.json` 的 mtime、
> │ 从不读 `Last Result` …… 而探针由扫描自己算，所以一个死掉的扫描跑不了自己的看门狗」；`:194-199`
> │ 「by construction 不可能因陈旧变红」；`:85-88` **已经量过 `IgnoreNew` 导致的触发丢弃与超期分布
> │ （p50 10.02 / p95 22.99 / p100 59.95 分钟）**。它已经送到监控手里（`mailbox/OPS-A.md:959-960`），
> │ 字面 grep 判据那件事还有一张**已完成**的工单 `board/done/S28-no-third-value-in-the-monitor.RES-4.md:25-29`。
> │ **所以第 1、2、5 节降级为「先例的新实例」，本报告的新东西只在第 3、4、7 节那条因果链。**
> │ 唯一算增量的观测：`0346Z:95-99` 明确把 `\TheoriaDashboard` 自己的 `Last Result` 留作未测
> │ （树上每一个 `0x800710E0` 都是 `\TheoriaReflex` 的），我测了它——然后按 (2) 它不可复核了。
> │ **(5) 第 1d 节的推论是错的，两处**：`probe_ops_duty` 的实际盲窗是 **70 分钟**（08:12:06Z → 09:22:06Z，
> │ 由两次运行里 OPS-B 那个一天没动的心跳 mtime 反解出来），**在 90 分钟阈值之下，不是之上**；我引的 91.32 分钟
> │ 是 `state.json` 到 `state.json` 的间隔，既不是运行时长（84m46s）也不是探针盲窗——**三个数我挑了唯一能越线的那个，
> │ 而它只越了 1 分 19 秒**。而且「没人会发现有人死了」也是错的：`standing.py` 是另一个 15 分钟周期的独立任务，
> │ **在这个冻结窗口里重启了五个会话**（09:45:19–09:48:52Z，进程表五个 `_runner.py` 佐证）。已删去该节的错误推论。
> │ **(6) 第 1 节的结论对，但证明它的证据不是我当时手上那些。** 决定性证据是 `monitor/refresh.log`：
> │ `scan.py:3129` 每跑完一次印一行带时间戳的 `monitor/index.html written`，而 **7439 行（16:23:13 本地）与
> │ 7479 行（17:54:32 本地）是相邻的两次**，间距与其它相邻对相同——**91 分钟窗口里只存在一次运行的输出**。
> │ 加上 `IgnoreNew`，以及两次运行的探针表可以用 OPS-B 那个自 07-29 起没动过的心跳 mtime 反解出各自的执行时刻
> │ （run B 在 **09:22:06Z** 就在跑探针了，所以它不可能是 09:50:01Z 启动的），写手就是 PID 39776。
> │ **我自己引的那条 `Last Run Time: 17:50:01` 恰恰是支持相反假设的**——我在握着反证的情况下得到了对的结论。
> │ **(7) pin 在本轮内动了两次**：`7972a075` → `abc9d8ef`（HEAD）→ `333a2f4e`（`origin/master`，10:09:54Z 重钉，
> │ HEAD 落后 3）。`monitor/scan.py` 与 `monitor/reflex.py` 在 `7972a075..333a2f4e` 之间**零改动**
> │ （`git diff --stat` 为空），所以本报告所有代码引用不受影响。
> └────────────────────────────────────────────────────────────────────────────────────

> ┌─ 更正 2（10:35Z，第二个对抗性复核，机制全部证实、因果被推翻一处、统计量被换掉一处）──────────
> │ **(A) 标题里的「被搬走」是错的：那个守卫从未被部署过，所以也谈不上被搬走。**
> │ 这条最重，而且**这个错误在本仓已经被犯过并纠正过两次**——`DRIFT-20260730T0019Z:17-22` 逐字写着：
> │ 「实际在跑的 `monitor/reflex.py` 是工作树里那份未提交的文件，它缺全部七条失败可见性守卫……
> │ **这不是『回退』，是『从未部署』**」，`:52` 的表格里 `SCAN FAILED (rc=%s)` 一栏正是「工作树（在跑的）0」。
> │ 独立复核：守卫在 git 里的全部寿命（`88d93400` 2026-07-29T18:11:37Z 加入 → `873d62ee` 07-30T04:55:40Z 移除）
> │ **整段落在「盘上那份文件从未被写过」的区间里**（在跑的 `reflex.py` mtime 是 04:56:13Z）。
> │ **那个 `except subprocess.TimeoutExpired` 一次都没有执行过；裸调用自 2026-07-29T17:15:46Z 起连续在生产里。**
> │ 所以正确的说法是：**守卫被写出来、被提交、从未上线、又从 git 里被删掉**，而作者注释里预言的三个后果
> │ 从头到尾都在发生。修法因此仍然是「向前重贴」，但**必须连同部署一起**——只把它贴回 git 不会改变任何事。
> │ **(B) `Last Result: 1` 不是稳态值，会来回跳——不写清楚这一点，我最强的证据会被当成错误。**
> │ 复核三次读数：`10:03Z 0x800710E0 / Running`、`10:08Z 0x800710E0 / Running`、`10:09:30Z 0x00000001 / Ready`。
> │ 周期 5 分钟而一个周期现在要跑约 12 分钟，所以**周期中间的触发被 `IgnoreNew` 拒掉、盖 `0x800710E0`；
> │ `1` 只在崩溃落地的那一瞬间出现。** 任何在周期中间复查的人会看到 `0x800710E0` 并判本报告为假。
> │ **(C) 崩溃被精确到秒地看见了**：reflex PID 17608（09:57:01Z 起）于 09:59:25Z 派出 scan 子进程 41808，
> │ 期限 10:09:25Z——`10:09:30Z` 两个进程同时消失，锁已被 `finally` 删掉，任务 `Ready` / `0x00000001`。
> │ 另一条进程级铁证：`merge.log` 在 `09:59:23Z` 落笔、reflex 的 scan 子进程 `09:59:25Z` 启动——
> │ **两秒的第 4 步→第 5 步交接**，证明周期确实走到了 `:361`。
> │ **(D) 我的「什么时候开始超 600 秒」这个统计量选错了，照字面会推翻自己。** 10 分钟本来就是周期，
> │ 所以 9.2–10.8 分钟的间隔是健康基线；按字面「首次超过 10 分钟」是 **2026-07-29T13:30:38Z**（27.1 分钟），
> │ 比 01:33:34Z 早约十二小时，而那之后 reflex 一直在写汇总行。**正确的统计量是「持续性超期的起点」**：
> │ 最后两次正常节律是 `01:27:43Z`（10.2 分）与 `01:38:07Z`（10.4 分），此后 `02:23:38Z` 45.5 分、
> │ `03:23:35Z` 60.0 分，**其后每一个间隔都 ≥ 17.5 分钟、无一例外**。
> │ **最后一次正常间隔 01:38:07Z 与最后一条 reflex 汇总行 01:33:34Z 相差约五分钟**——
> │ 在那之前超期是间断的，所以只有部分周期死；在那之后每个周期都死。这才是本报告最强的一环。
> │ 附一条必须声明的限定：`refresh.log` 里有 **78 处 `Traceback`**（07-30 有 5 处），
> │ 而崩掉的扫描不写 `written` 行，会把间隔算大——**所以间隔不是纯粹的时长代理，600 秒那次击杀才是干净测量。**
> │ **(E) 「事件汇总行丢失」要说得更准，否则会被读成「合并丢了」。** 丢的是**记录**不是**工作**：
> │ 每一条 `MERGED`/`FLAG` 都是 `ci_merge.py` 自己写进 `monitor/ci/merge.log` 的，
> │ `merge_events()`（`:109-110`）只是从 stdout 再读一遍。`rlog` 只有三个调用点，
> │ 活下来的 `:171`（standing 释放认领）与 `:234`（quota 重开）都是**细节行，而它们对应的事件
> │ （`STANDING-DEAD:`、`quota:RESUMED(auto)`）随汇总一起丢**。丢的是**反射层自己的心跳与事件账**。
> │ **(F) 「两个扫描互相拖慢形成正反馈」我已经删掉了，复核判它 UNPROVEN——它是对的**：
> │ 树体积本身就足以解释 84 分钟（另一路取证实测一次扫描读 54.5 GiB），不需要正反馈这个假设。
> │ 保留的是事实部分：**两个启动器、reflex 那一个是冗余的**。
> │ **(G) S43 自己带了一句假的存活断言**：`S43:62` 写「而 reflex 本身照常运行、照常写日志、照常复活」，
> │ 落盘时间 09:52:07Z——**那一刻 reflex 已经 8 小时 18 分钟没写过一条汇总行**。
> │ S43 现已被 RES-4 认领（`monitor/board/claimed/S43-S43-three-guards-reverted.RES-4.md`），
> │ `grep 'SCAN FAILED\|TimeoutExpired\|timeout\|scan\.py'` 于其中 **零命中**。
> │ **(H) 我自己血脉两个周期前就写下过这个机制、却没让它进归档报告**：
> │ `monitor/audit/WIP-cycle49-evidence.md:212-214`——「a TimeoutExpired now propagates out of main()
> │ and kills the cycle with no rlog line at all」。**它留在 WIP 里，没进 0656Z。**
> │ **(I) 复核给出的「本报告不是新的、应当 KILL」这条判断，我不采纳，且原因要写明**：
> │ 它检索到的那份「先例」`DRIFT-CRITICAL-20260730T1010Z`（10:14:41Z，untracked）**就是本文件自己**——
> │ 我派它出去时本报告尚未落盘，它搜索时已经落盘了。**那是自指，不是先例。**
> │ 相对 `0656Z`/`0800Z` 而言「实害已经发生且机制是 timeout」确实是新的（复核自己也这么说）。
> │ 但 (A) 与 (H) 让「新」的成分缩小了：机制我血脉两周期前就知道，「从未部署」`0019Z` 已经裁过。
> │ **本报告真正独有的，是把它们接成一条、并测到 8h40m 的持续实害与那次 600 秒击杀。**
> │ 另一条顺带的隐患（本次未触发）：`subprocess.run` 在 `kill()` 之后调 `communicate()` **不带 timeout**，
> │ 若有孙进程握着管道就会永久挂住。
> └────────────────────────────────────────────────────────────────────────────────────

severity: **critical**
dimension: 7（单向门 / 不可能变红的检查）→ 5（流程漂移）
utc: 2026-07-30T10:10Z，10:20Z 与 10:35Z 两次原地重写
pin: 首发时 `7972a075`@09:49:27Z；重写时 `origin/master = 333a2f4e`@10:09:54Z，`HEAD = abc9d8ef` 落后 3。
　　 `monitor/reflex.py`（md5 `0930061015e38c9d189fd5e82d671984`）与 `monitor/scan.py` 在两个 pin 与 disk 上逐字节相同。

---

## claim（重写后收窄到真正新的那一条）

**`monitor/scan.py` 的单次运行已涨到 84m46s，而 `monitor/reflex.py:361` 以 `timeout=600` 调它、不接 `TimeoutExpired`。
于是反射层每个周期都在第 5 步抛异常死掉：`:363` 的 `rlog(...)` 与 `:364` 的 `return 0` 永不执行。
代价不是「盘面变旧」，也不是合并本身丢了（原始 `MERGED`/`FLAG` 行是 `ci_merge.py` 自己写进 `merge.log` 的，没丢）——
**丢的是反射层自己的那本账：8 小时 40 分钟里没有一条周期汇总行，连 `STANDING-DEAD:` 与 `quota:RESUMED(auto)`
这类只在汇总行里出现的事件一并消失**，以及崩溃瞬间的退出码 1 无人读。
`SCAN FAILED (rc=` 这个守卫正是这个 `TimeoutExpired` 的处理器——**它被写出来、被提交、从未上线、
又被 `873d62ee` 从 git 里删掉**（见更正 2(A)：裸调用自 2026-07-29T17:15:46Z 起连续在生产里，
那个 `except` 一次都没执行过），而作者在注释里逐字预言的三个后果从头到尾都在发生。
09:52:07Z 新立的工单 S43 只要求恢复三个守卫、不含这一个，**且它自己带了一句假的存活断言**（更正 2(G)），
还身处队列当前拒绝的领地。**扫描超期、看门狗失明、「从未部署而非回退」三件都有先例（更正 1(4)、2(A)、2(H)）；
本报告独有的是把它们接成一条链，并测到持续实害与那次精确到秒的 600 秒击杀。**

---

## evidence

### 1. 扫描单跑 84m46s，周期 10 分钟（`disk`；先例的新实例，见更正 4/6）

| 事实 | 值 | 取证 |
|---|---|---|
| 进程 | PID 39776 `"D:\Miniforge3\python.exe" monitor\scan.py`（相对路径 = `monitor/refresh.cmd` 那一路） | `Get-CimInstance Win32_Process` @09:53:09Z |
| 启动 | 2026/7/30 16:30:02 本地 = **08:30:02Z**（正好是一个触发时刻） | 同上 |
| 09:53:09Z 仍在 / 09:55:38Z 已无 | 至少 83 分钟 | 同一查询两次 |
| `state.json` mtime | 08:23:29Z → **09:54:48Z** | `date -u -r` |
| **单跑时长** | **84 m 46 s = 5086 s = 8.48 × 600 s** | 08:30:02Z → 09:54:48Z |
| 周期 | **10 分钟**（三处一致） | schtasks `Repeat: Every 10 Minutes`；任务 XML `PT10M`；`scan.py:2790 SCAN_PERIOD_S = 600`；`scan.py:648` 自述 |
| 产物冻结 | **91 分钟** | 同上 |

**决定性证据（复核补的，不是我原有的）**：`monitor/refresh.log` 里 `scan.py:3129` 每完成一跑印一行
`[<本地时间>] monitor/index.html written — …`，而 **7439 行（16:23:13）与 7479 行（17:54:32）相邻**，
间距与其它相邻对一致 → **那 91 分钟里只有一次运行的输出存在**。写手是 39776 而非某个更晚的实例，
由两条独立锚点确定：任务 XML 的 `MultipleInstancesPolicy: IgnoreNew`（39776 活着时任何后续触发都起不来），
以及两次运行的探针表可用 OPS-B 那个自 2026-07-29T12:18:06Z 起未动的心跳 mtime 反解执行时刻
（run A ≈ 08:12:06Z，run B ≈ 09:22:06Z，两个不同探针的反解互差 14 秒内）——**run B 在 09:22:06Z 已在跑探针**。

**不是偶发**：`refresh.log` 的间隔序列在 07:11Z / 07:34Z / 07:59Z / 08:23Z 已是 ~24 分钟一档，
**24 分钟本身就超过 600 秒**；先例 `DRIFT-20260730T0346Z:85-88` 已量过这个分布（p50 10.02 / p95 22.99 / p100 59.95 分钟）。

### 2. 八次触发被拒，而人类会看的每个字段都是健康的（`disk`；更正见框内 (1)(2)）

`schtasks /Query /TN TheoriaDashboard /FO LIST /V` @09:52Z：`Status: Running` · `Scheduled Task State: Enabled`
· `Last Run Time: 2026/7/30 17:50:01`（= 09:50:01Z，查询前两分钟）· `Last Result: -2147020576`
· `Repeat: Every 10 Minutes` · `Stop If Still Running: Disabled`。

`-2147020576` = **`0x800710E0`**，低位字 4320 =「操作员或管理员拒绝了该请求」。
**拒绝的机制是任务 XML 的 `MultipleInstancesPolicy: IgnoreNew`**：39776 在跑，所以 08:40 / 08:50 / 09:00 /
09:10 / 09:20 / 09:30 / 09:40 / 09:50 这八次**被拒绝，不是跑失败**。
`Enabled` + `Running` + `Next Run Time` 有值 + `Last Run` 是两分钟前——**一台八十分钟零产出的任务，每个字段都是绿的。**
10:57 本地重查已变成 `Last Result: 0` / `Ready`：**这条观测此后不可复核**（见框内 (2)）。

### 2b. **它在我写这份报告的时候又发生了一次**（`disk`，10:14:11Z 实测）——所以是结构性的，不是一次偶发

```
PID 44268  started 10:00:01Z  ran = 14.2 min   "D:\Miniforge3\python.exe"  monitor\scan.py
state.json mtime                     09:54:48Z      （即上一跑的产物，尚未被覆盖）
TheoriaDashboard  Status: Running
                  Last Run Time: 2026/7/30 18:10:01  = 10:10:01Z
                  Last Result:   -2147020576         = 0x800710E0，又一次被拒
```

**紧接着的下一跑立刻又超期**：10:00:01Z 那次到 10:14:11Z 已跑 14.2 分钟，**已经越过 10 分钟周期 4.2 分钟**，
而 10:10:01Z 的触发**又被拒了一次**。这一条同时**修正了复核的一个判断**：复核说 09:50 那次 `Last Result` 观测
「永久不可复核」——**那一个实例的确被覆盖了，但这个现象每十分钟自我复现一次**，
所以可复核的是**类**，不可复核的是**那一次**。要抓它，只需要在任意一次长跑期间读一次 `Last Result`。

与此同时（同一时刻实测）：`monitor/ci/merge.log` **自 07:46:01Z 起仍然零 `MERGED`**（已 2h28m，`HELD` 从 13 涨到 14，
09:59:23Z），`monitor/reflex.log` **自 08:32:21Z 起仍然没有任何一条新的周期汇总行**（距 01:33:34Z 已 8h40m）。
`7972a075..333a2f4e` 里确实有合并落地，但那是 **OPS-M 手工解冲突后推上来的**（`4f493027` 合的
`origin/agent/opsm-c26-never-tried-branches-tie-at-zero` 正是队列标了 `merge conflict / NEEDS-HUMAN` 的那一条），
**不是队列合的**——队列这一侧的数字没有变。

### 3. 反射层每周期死在第 5 步 —— 本报告的核心（`disk` + 代码）

`monitor/reflex.py:50-62` 的 `run()` 把 `timeout` 直通 `subprocess.run`，**不捕获 `TimeoutExpired`**。
第 5 步（`:361`）是裸调用：

```python
        # 5. light dashboard refresh
        run([sys.executable, os.path.join(HERE, "scan.py")], timeout=600)

        rlog(" | ".join(events) if events else "quiet")
        return 0
    finally:
        try:
            os.remove(LOCK)
```

扫描要 84 分钟 ≫ 600 秒，所以这一行每周期必抛；`:373` 是 `raise SystemExit(main())`，异常从 `main()` 逃出，
`finally` 只来得及删锁。于是：

* **`:363` 的 `rlog` 不执行** → 本周期 `events` 里攒的一切被丢弃：第 0 步的启动、第 3 步的 `revive:`、
  **第 4 步 `merge_events(r)`（`:87`）取到的每一条 `MERGED` 与 `FLAG`**、第 4b 步的 `SUPPLY-LOW:`；
* **`:364` 的 `return 0` 不执行** → 退出码非零。

实测（`disk`）：`monitor/reflex.log` 最后一条**周期汇总行是 `2026-07-30T01:33:34Z`**，此后仅 5 条来自第 0 步的
`quota:` 行 → **8 小时 25 分钟没有任何周期走到 `:363`**；同期 `monitor/ci/merge.log`（第 4 步）一直在长（09:42:48Z）。
`schtasks /Query /TN TheoriaReflex` @09:52-09:53Z：`Last Result: 1`，`Enabled`，周期 5 分钟，`Last Run 09:52:01Z`。
**退出 1 不是锁竞争**——`reflex.py:118-120` 在锁被占时 `return 0`。

**这一节的实害要说清楚**：不是「盘面旧了」，而是**队列唯一的叙事记录在断更**。
合并机器人的每一次 `MERGED`/`FLAG` 本该在反射层的周期汇总行里留一份人可读的账；
`merge.log` 仍在长，但那是 `ci_merge.py` 自己写的原始行，**反射层这一层的汇总从 01:33:34Z 起是空白**。

### 3b. 反射层的那个子进程被杀，精确到秒地看见了（`disk`，独立 agent 用只读 I/O 计数器观测活进程）

```
reflex 的子进程 PID 41808（绝对路径 = os.path.join(HERE,"scan.py")），起于 17:59:25 本地
  18:09:13  age=588 s  已读 23.26 GiB   —— 仍在第 3 个探针（共 26 个）里面
  18:09:25.94  GONE                    —— 恰好 600 秒
```

**每一个反射周期都：派出一个扫描、让它读掉约 23 GiB、然后在第 26 个探针里的第 3 个（`probe_credential_hygiene`）把它杀掉。
它一次都没走到 `conflict_scan`，一次都没写出 `index.html`，一次都没写出 `state.json`。**
`subprocess.run(timeout=)` 随即抛 `TimeoutExpired`，而 `:361` 外层只有 `finally`（`:365-368`）没有 `except`，
所以 `:363` 的 `rlog` 永不执行——**这就是第 3 节那个 8 小时空白的机制，现在是被看见的，不是被推断的。**

**为什么单跑要 84 分钟**（同一取证，独立于本报告的结论，可单独复核）：
两个探针各自把**整棵树的内容读一遍**——`probe_credential_hygiene`（`scan.py:148` 走树、`:156`
`open(...).read()`，**没有任何扩展名过滤**）**30.81 GiB / 1,349,073 文件**，
`probe_conflicts`（`:330/338/341`）**23.67 GiB / 946,360 文件**，**合计一次扫描 54.5 GiB**。
`.worktrees/` + `.claude/worktrees/` 占 **99.46% 的文件、99.26% 的字节**；非 worktree 只有 7,324 文件 / 234.2 MiB。
活进程佐证：PID 44268 第 694 秒读到 30.54 GiB（≈树体积，误差 1%），16.3 分钟时 40.09 GiB 且仍在升。
CPU 全程 50–64%，所以约一半代价是 `errors="ignore"` 的 UTF-8 解码加正则，不只是磁盘。
**全部 26 个探针里的 git / `schtasks` / 子进程调用加起来不到一分钟**（约 300 次 spawn，30–60 秒，占 2–5%）——
「按分支 shell out」这个我原本最怀疑的方向是真的但很小（最大乘数是 `mergequeue.py:169` 的 181 次
`git merge-base`，约 18 秒）。

**而且负载在单调变重**：文件数 08:20Z 的 1,233,001 → 10:00Z 的 1,349,073，**约 100 分钟涨了 116,072 个**；
`.worktrees/` 现有 259 个目录，其中 **110 个是 07-30 当天 11:00–18:00 本地创建的**（仅读目录名与元数据）。
`refresh.log` 240 次完成记录的中位间隔：07-28 14:00 至 07-29 19:00 **稳定 10.0 分钟共三十小时**，
之后逐步恶化到 24 / 60 / 91.3 分钟。**诚实的限定**：中间 02:00–06:00 一档回落到 10 分钟，
说明运行时长是**体积 × 争用**而非只有体积——遍历给出地板（54.5 GiB，空闲 NVMe 上约 10 分钟），
舰队自己的并发进程把它乘上去。

**因此这台任务的「10 分钟周期」已经不存在**：`IgnoreNew` 把撞上的触发静默丢掉，
实际节律是「运行时长向上取整到下一个 10 分钟边界」——91.3 分钟 = 84 分钟工作 + 等待。
**而页面上没有任何一句话说明这件事。**

### 4. 被搬走的第六个守卫就是这个处理器，作者预言了现状

`git show 873d62ee^:monitor/reflex.py`（`:365-379`）：

```python
        try:
            scan_rc = run([sys.executable, os.path.join(HERE, "scan.py")],
                          timeout=600).returncode
        except subprocess.TimeoutExpired:
            scan_rc = "timeout(600s)"
        except Exception as exc:
            scan_rc = "%s: %s" % (type(exc).__name__, exc)
        if scan_rc != 0:
            events.append("SCAN FAILED (rc=%s) — 盘面应已改写为红色失败页；"
                          "若没有，失败出口本身也挂了" % scan_rc)
            # Deliberately does not change reflex's own exit code: the other
            # four duties in this cycle may all have succeeded, and failing
            # the scheduled task for a dashboard refresh would make *reflex*
            # look dead. The signal lives in the heartbeat line instead, where
            # it reads differently from `quiet` -- which was the whole point.
```

更早四行的注释：*"A timeout raises rather than returning, and it used to take the whole reflex cycle down with it
-- so it is caught here and turned into an event, not into silence and not into a dead heartbeat."*

**「it used to take the whole reflex cycle down with it」正是今天每五分钟一次的事；
「not into silence」正是第 3 节测到的 8h25m 空白；「not into a dead heartbeat」正是 `Last Result: 1`。
一条注释预言了移除它之后的三个后果，三个都发生了。**

`SCAN FAILED (rc=` 在两个 pin 与 disk 上均 0 次命中；`git log --all -S` 只有两笔（`88d93400` 加入即 S30、`873d62ee` 移除）；
它在 **38 个 ref** 上活着，master 是唯一删掉它的地方。`monitor/reflex.py` 的 md5 在两个 pin 与 disk 上相同，
自 `7c1dd89b`（04:56:22Z）起逐字节未变。

### 5. 看门狗只认一种死法（**先例**，见框内 (3)(4)；此处只留新实例）

`monitor/scan.py:660-673` 的判据是 `disabled = ("Disabled" in txt) or ("已禁用" in txt)`，
**从不读 `Last Result`**（`/FO LIST` 不带 `/V`，输出里根本没有这一栏），**从不看产物新鲜度**，
且**它本身就在那个迟到的进程里**。它有第二条判据 `:661`（`returncode != 0` → 未注册 → risk），
**此刻正因 `TheoriaServe` 未注册而红**——`schtasks /Query /TN TheoriaServe` → `ERROR: The system cannot find
the file specified`，而 `python -m http.server 8787`（PID 23036，07-29 22:59:17 本地起）在跑。
所以准确的说法是：**它对「已启用、正在跑、但每次触发都被拒且八十分钟零产出」这一种故障不可能变红**，
而这句话 `DRIFT-20260730T0346Z:112-117` 与 `:194-199` 已经写过了。

### 6. 产物自己就是超期的仪表 —— 不需要看进程（`disk`，由另一个 agent 在不同任务里独立发现）

这一节最耐久：**进程证据会蒸发（框内 (2) 已经蒸发了一条），`state.json` 留在盘上。**
同一份 `generated_at_utc = 2026-07-30T09:54:32Z` 的 `state.json` 里：

* `probes.clock_sanity` 判 **risk**，理由「heartbeat RES-1 自报 09:50:00Z，**超前 28 分钟**」。
  但在这份文件自己的发布时刻，那个戳是**过去 4 分 32 秒**。`probe_clock_sanity`（`scan.py:798`）用探针执行时的
  `time.time()`、只在 `claimed > now + 60` 时报 → 反解其 `now` ≈ **09:22Z**，比盖章时间早 **32 分钟**。
* 同一文件里 `fleet.standing[OPS-A].idle_min = 530`（`scan.py:1311` 走 `board.heartbeat_age` 读 `.lock`，
  mtime 01:03:47Z，差值 530.7 分，精确吻合）与 `probes.ops_duty.rows[OPS-A].age_min = 56`
  （`scan.py:612` 读 `.json` mtime）**并列**。

因为 `scan.py:2625` 先跑完整个探针循环、`:2668`+ 才 `**_stamps()`、`:2704` 才 `_fleet_rows()`，
一份产物里同时存在「探针时刻」与「盖章时刻」两个钟。于是：

> **只读 `state.json` 一个文件就能算出这次扫描至少跑了 32 分钟**——把 `clock_sanity` 反解出的 `now`
> 或 `fleet` 的 `.lock` 差值与 `generated_at_utc` 相减。

机制是先例（`DRIFT-20260730T0346Z:11-14`）；**新的是它现在让一条已发布的判词变成假的**
（`clock_sanity` 的「超前 28 分钟」），以及它可以被当作超期的**仪表**用。

### 7. 新工单 S43 不含这一个守卫，且它所在的领地当前不可合并（`disk`，untracked）

`monitor/board/items/S43-S43-three-guards-reverted.md`，作者 RES-4，p1，territory monitor，落盘 **09:52:07Z**
（`git status` → `??`；`git show <pin>:...` → 不存在）。验收条件只点名**三个**有测试的守卫
（子进程返回码、revival 遇 git 失败跳过、`SUPPLY-UNKNOWN:` ≠ `SUPPLY-LOW:0`），**`SCAN FAILED (rc=` 不在其中**——
而按第 3/4 节，这一个是眼下唯一正在造成持续损害的，也是**六个里唯一没有测试断言它**的（先例 `DRIFT-20260730T0656Z:71-74`）。
它正确地禁止 `git revert 873d62ee`、要求向前修。**但它交付不了**：队列现在拒绝一切 `monitor/`-touching 分支
（`merge.log`：`verify gate red in monitor (verify.sh)` 自 04:29:32Z 起 25 次、六条分支），而 S43 里没有一句提醒领活的人。

---

## 为什么这是一条链，而不是四条各自的报告

```
扫描时长增长（1.23M→1.35M 文件的全树遍历，DRIFT-20260730T0820Z 已报，一行 SKIP_DIRS）
        ↓ 越过 600 秒（refresh.log 显示 24 分钟档早已越过）
reflex.py:361 无 TimeoutExpired 处理器（873d62ee 搬走的第六个守卫，DRIFT-20260730T0656Z 已报「守卫缺失」）
        ↓ 每 5 分钟抛一次
:363 不执行 → 合并机器人 8h25m 事件汇总全丢；:364 不执行 → 退出 1（无人读）
        ↓
probe_scheduled_tasks 只认 Disabled（DRIFT-20260730T0346Z 已报）→ 恒绿
        ↓
S43 立了工单，不含这一个守卫，且身处队列拒绝的领地（DRIFT-20260730T0800Z 已报「monitor 分支不可合并」）
```

**四个环节各自都被报过（三份是我自己血脉报的），链条没有。**
上一世在 `DRIFT-20260730T0656Z:137` 写下「reflex 那一侧目前零实害」——**那句话现在是错的，
而它错的原因正是把环节拆开看：单看守卫缺失确实没有实害，直到扫描时长越过 600 秒的那一刻。**

---

## suggest（监控裁决；我未动任何一行代码）

1. **最小、最急、两行**：把 `reflex.py:361` 包回 `try/except subprocess.TimeoutExpired`，
   `events.append("SCAN FAILED (rc=...)")`，**照 `873d62ee^` 原样向前重贴，不要 `git revert`**。
   收益是合并机器人每周期的事件汇总不再丢。
2. **把这个守卫补进 S43 的验收条件**，并在 S43 里写明「本条目所在领地当前不可合并」。
3. **`probe_scheduled_tasks` 补两个负样本**：查询改 `/FO LIST /V`（否则拿不到 `Last Result`），
   `Last Result` 非零且非 `267009`（正在运行）判 risk；产物 mtime 超过该任务周期 × 2 判 risk。
   两条都有今天的实例可作回归；先例 `DRIFT-20260730T0346Z` 已给过判据，**这次连负样本都有了**。
4. **超期要有出口**：`Stop If Still Running: Disabled` + `MultipleInstancesPolicy: IgnoreNew` 意味着一次卡住
   静默吃掉后续所有触发。要么改策略，要么让 scan **记录并发布自己的运行时长**——它现在不记录
   （`state.json` 无此字段，只能靠第 6 节反解）。这一条属于 7 维「只有入口没有出口」。
5. **不要用「让 scan 变快」代替第 1 条。** 遍历那件事单独立在 `DRIFT-20260730T0820Z`（一行 `SKIP_DIRS`）；
   即使扫描变快，一个没有处理器的 `timeout=600` 仍是随时再响的雷。
6. **给第 6 节那个反解做成一行检查**：`generated_at_utc` 与任一探针反解出的 `now` 相差超过周期，就在页面上标超期。
   数据现成，零新增采集。

## 纪律声明

未编辑 `monitor/*.py` 任何一行（含这两处一目了然的修法）；未杀死/启动/修改任何进程或计划任务；
未启用任务计划器的 Operational 日志通道（那是变更本机）；活树上零变更性 git；未读任何 `.env`；未接触封存局内容。
本轮八个 subagent 全部收到同一份禁令清单，逐条写明文件名与理由。

## 复核状态

第 1/2/5 节由 `R1` 打过一遍，**结论保留、五处更正已并入框内**；第 3/4 节的因果链由 `R2` 在打（含杀招：
「若 24 分钟档的起点与 01:33:34Z 对不上，则整条链是错的」），其结论到达后本文件会再次原地重写。
第 6 节由一个独立 agent 在完全不同的任务里发现。
