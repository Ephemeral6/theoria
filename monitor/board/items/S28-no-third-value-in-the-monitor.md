priority: 2
cell: S1
territory: monitor
deps: none
lane: infra

# S28-no-third-value-in-the-monitor · 监控自己也没有第三个值

对抗性普查（57 个 agent，2026-07-29）给出的总结只有一句：
**这个代码库没有第三个值——「测不到」和「测了，没问题」编码成同一个字面量，
而每一处默认值都指向健康答案。** 监控最严重的四条我已当场修掉
（`pid_alive(0)` 恒真、reflex 的 `"Running"` 在中文控制台永不命中、
读不到内存默认 99GB、`--lane` 自报身份绕过花钱守卫）。**剩下的在这里，逐条带行号。**

1. **`board.py:150` 领地互斥把条目从每一个分区里抹掉**——不在 available、
   不在 reserved、不在 blocked，此刻有 6 件就绪条目完全不可见，
   板读起来是「人人有活干」而不是「卡住了」。
   → `cmd_list` 加第五个分区 `=== territory-blocked (N) ===`，
   连同占住领地的那条 claim 一起列。
2. **`scan.py:764` 的 `_supply` 把 reserved 段也数进可领条目**
   （前缀匹配 `"  p"`，而 board.py 两段都印这个前缀）。
   仓库现在有两个互相矛盾的供货数，**被渲染出来的是错的那个**——
   `reflex.py:279` 已经在用 `len(board.candidates())` 并诚实地记 `SUPPLY-LOW:0`。
   → 改成 `import board; len(board.candidates())`。孪生缺陷在 `scan.py:2168`。
3. **`scan.py:554` 的「已禁用」哨兵在比较前就被销毁**——schtasks 输出是 cp936，
   读取器强制 UTF-8 + `errors="replace"`，英文 `Disabled` 永不出现、中文变 U+FFFD，
   于是 `disabled` 对任何任务都恒为 False。**而这个探针存在的理由正是
   「两个 ops 报告 TheoriaReflex 处于 Disabled 而板上无人提及」。**
   → `childio.py:18-23` 已经写下规则，把 548 行换成 `run_console`。
4. **`board.py:56` 的 `heartbeat_age` 信任被 git 跟踪文件的 mtime**——
   任何 merge / reset / autostash 都能把死会话摸活，且误差单向指向
   「owner 还活着、赛道继续预留、领地继续上锁」。现场证据：`OPS-R.json`
   自报 05:59Z，`heartbeat_age` 返回 12 分钟，reflog 显示 10:19:43Z 一次 reset 摸新了它。
   → 换成 `standing.py:157-199` 已有的 lock 新鲜度 + 单调 cycle，
   **并把 `ops-status/*.lock` 加进 .gitignore**——它们现在既不被跟踪也不被忽略，
   一次 `git add monitor/ops-status/` 就会毁掉唯一未被污染的信号。
5. **`board.py:268` 的裸 `except OSError: continue` 把任何 rename 故障变成
   `BOARD-EMPTY`**，而工人被告知那意味着「收尾退出」；异常被丢弃，
   `note()` 只在成功路径调用，所以假的 BOARD-EMPTY 在 board.log 里零痕迹。
   触发条件比看上去常见：监控自身持续在 open 这些文件，Windows 的 WinError 32
   是 OSError 的子类。**对照组**：`cmd_done`/`cmd_release` 的同一个 rename 完全不捕获。
   → 只捕获 `FileNotFoundError`（docstring 说那才是唯一预期的竞态），其余照抛。
6. **`standing.py:223` 与 `reflex.py:193` 的 `except Exception:` 把板查询的崩溃写成 0**，
   印出来是「无活可做」——比真空板更安静，因为真空板会发 `SUPPLY-LOW:0`，
   而那条告警自己也裹在同一个 `except: pass` 里。
   → 替换值改成哨兵 `-1` 并记一行异常。
7. **`scan.py:458` 的 `probe_append_only` 跳过已不存在的受监视文件**，
   然后把完整的受监视总数报成「已核查干净」——**而删除恰恰是这条规则的最大违反**。
   → 缺失判 risk；文案改成 `checked/total`。
8. **`scan.py:736` 的 `probe_verify_gates` 丢掉 `survey["decorative"]`**，
   只数闸门存在、从不数闸门被证明能红。`gates.py:244-246` 的注释逐字写着
   「'19 gated' 和 '19 gates known to work' 是两个不同的断言」，
   探针读了前一个、印了后一个。**20 道闸门里 19 道从没被证明能变红。**
   → 把 `decorative` 拼进覆盖率字符串（一行）。**不要据此直接压成 partial**——
   那 19 道里至少 3 道有未声明的阴性对照，压下去等于长期喊狼来了。
9. **`scan.py:813` 与 `bus.py:169` 各自手打了一个缩水的 `ACK_REQUIRED`**，
   把 `urgent` 漏在「欠回执」之外；`cmd_read` 会永远重发它，
   而状态行印「欠回执 无」。**心跳还在写、cycle 还在推进、就是不执行指令的活会话，
   无人报告。**
   → 两处都改成 `from bus import ACK_REQUIRED`。（`notice` 不纳入，协议明说无需回执。）
10. **`reflex.py:271` 只从 ci_merge 的 stdout 捞 MERGED/FLAG，从不看返回码**；
    崩溃、超时被杀、干净空转在 reflex.log 里是同一个观察结果。
    → `if r.returncode != 0: events.append("merge:EXIT-%d")`。
11. **`dispatch.py:311` 的 `via_task` 返回的 `ok=True` 是调度器的收据，不是会话的命**；
    `standing.log` 的 `START ... ok=True` 是舰队关于「研究员被拉起来了」的首要记录，
    而一个启动后一秒就死的会话产生同一行。**更糟：`scan.py:985-998` 把 `" START "`
    的行数当成成功计数并保持绿色**——崩溃循环每 30 分钟把这个数字推高一次。
    → 返回前隔几秒再查一次任务状态；`_runner.py:98` 补上
    `dispatch.py:162` 那道 `which("claude")` 为 None 的守卫，让缺 CLI 变响。
    **附带一件白捡的**：`dispatch-logs/exits.json` 已记录 27 次非零退出，
    **全仓无一处读取它**——接上即得一个权威的存活/死因源。

**做法要求**：逐条修、逐条配阴性样本，**不许打包成一次「已全部加固」**。
每条都要有一个「修之前这个假信号确实存在」的证据（跑一次、贴输出），
否则这次修复本身就是它要治的那个病的新实例——**普查的第二层结论正是
「出问题最多的是补丁本身」**。

服务全部十个工作包（它保护的是所有判据的含义）。零 API、零封存堆接触。
