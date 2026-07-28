# W-1540 → 监控：reflex 现在每 5 分钟失败一次；顺带，金丝雀要一个按天的槽位

条目 `S2-canary-schedule`（territory `arc-recon`），分支 `agent/s2-canary-schedule`。
两件事，第一件是阻塞级的，且不在我的领地内，所以只报不动。

---

## 一 · `monitor/reflex.py` 自 `ab99697` 起每次运行都抛 `UnboundLocalError`

> **OPS-M 先到了**：`20260728T075952Z-opsm-reflex-still-dead-unboundlocal.md` 与
> PARTNER_SYNC `[OPS-M] 08:02Z` 已报同一处、同一诊断、同一补丁。我独立撞上后才看到，
> 这里只留**它没写的那部分**：一条运行时证据，和一条给 probe 的判据。结论一致，
> 算互证。

**证据三条，互相独立：**

1. 静态：`main()` 里 `hold` 是局部变量，**第 100 行 Load，第 143 行才 Store**。

   ```
   hold is a local of main(); Load at lines [100, 144, 148, 184] / Store at [143]
   first load before first store -> True
   ```

   第 100 行是 `if not hold and avail:`。`not hold` 先求值，所以 `avail` 是不是 0
   都不影响——短路救不了它。该行位于 `try` 块内但没有 `except`，异常直接穿出
   `main()`。

2. 运行时：`schtasks /Query /TN TheoriaReflex /FO LIST /V` →
   **`Last Result: 1`**，`Last Run Time: 2026/7/28 16:02`（本地时区）。任务在跑，
   每次都非零退出。

3. 日志：`monitor/reflex.log` 最后一行是 `2026-07-28T03:57:22Z quiet`。
   之后四个多小时、约五十次调度，**一行都没有**——因为写日志的
   `rlog()` 在第 194 行，永远到不了。

**后果**（第 100 行之后的每一步都没有在跑）：reap、quota 检查、revive、
**ci_merge**、dashboard refresh。其中 ci_merge 最要紧：**工人分支交付后没有任何东西
在合并它们**。我这条分支也会卡在这里，我不碰 master，所以请留意。

**最小修复**：把第 141–145 行的 quota 检查（`q = run([... quota.py, "check"])`；
`hold = q.returncode == 2`）整体移到第 0b 步之前。`hold` 的其余三处使用都在其后，
顺序上没有别的依赖。我没有改——`monitor/` 不是我的领地。

> 顺带一句判据，供 `probe` 用：这次故障的签名是**任务状态健康 + 日志静默**。
> 只看 `schtasks` 的 `Status: Ready` 会判它活着。真正的活体信号是
> `reflex.log` 的最后一行时间戳与当前时间之差 > 2 个周期。

---

## 二 · 金丝雀现在有可调度形态了，要一个**按天**的槽位（不是 5 分钟）

`arc-recon/canary_schedule.py`（在我的分支上，随合并进来）。

**不要把它挂进 reflex 的 5 分钟循环。** 每次全量扫要花 ARC 动作，5 分钟一次是
每天 3456 个动作，去看一件只在运营方发新版本时才会变的事。

正确的接法是两段式，reflex 只付得起便宜的那半段：

```bash
python arc-recon/canary_schedule.py due --profile quick   # 完全离线，零花费，退出 3 = 还没到点
python arc-recon/canary_schedule.py run --profile quick   # 到点了才买；12 个动作
```

`due` 不碰网络、不写文件、不花钱，所以问它 288 次和问 1 次一样便宜；它自己管
24 小时的节流。或者干脆独立挂一个每日任务，命令由
`python arc-recon/canary_schedule.py install` 打印（**它只打印，不执行
`schtasks`**——装不装是人的决定）。

**退出码就是接口**：`0` PASS · `1` 漂移（已开事故单 + 已冻结战役）· `2` 安全拒绝 ·
`3` 没到点/没事做 · `4` INCOMPLETE（API 够不着，不是漂移）· `5` 被闸门挡住
（战役冻结中，或共享花费闸门拒绝）。

**只有 `1` 需要叫人。** `4` 连续三次会自己开一张 `process` 事故单说"我瞎了"，
但不冻结战役——看不见不等于变了。

今天 07:57Z 已经真跑过一次：4/4 PASS，12 个动作，16 次 HTTP。

---

## 三 · 一条给别的工人的顺手修复

`arc-recon/client.py` 原先只在 `<repo>/.env` 找 key。**worktree 里没有 `.env`**
（它 gitignored，只存在于主检出），所以 arc-recon 里每一个联网工具在
`.worktrees/` 里都用不了——而工作约定要求所有人都在 worktree 里干活。我是想跑自己的
扫描时撞上的。现在 `client.main_checkout()` 会顺着 worktree 的 `.git` 文件里的
`gitdir:` 指针回到主检出去找，且只找那一处。若别的领地也有自己读 `.env` 的代码，
同一个坑在等着。

---

## 四 · 共享花费闸门：我这条路上目前记的是 `absent`

`proxy/spend_gate.py` 还没进 master（在 `.worktrees/wt-s3/` 里）。所以
`canary_schedule.open_spend_gate()` 现在往运行记录里写
`spend_gate: "absent"` **并把理由写全**，而不是把"没有闸门"当成"批准"。它一进
master 就会被自动用上——无开关、无 opt-out，闸门拒绝就不扫，有测试盯着。

反方向没做，需要 S3 那边知道：**闸门不知道金丝雀的存在**，所以谁在算战役余量时，
目前都没把每天 12 个动作算进去。
