# monitor 的崩溃档案

`monitor/refresh.log` 是 gitignore 的。2026-07-29 的清理审计拦下一次删除，理由是
那里面有 **55 个 UnicodeDecodeError traceback**——`scan.py` 崩溃的唯一存活记录。
理由成立，但结论只对了一半：只要记录活在一个不被跟踪的文件里，它就永远只是
「下一次清理还没轮到它」。所以分类结论写在这里，新发生的崩溃逐条追加进
`monitor/crashes.jsonl`（被跟踪）。

分析于 2026-07-29（S30，W-1680）。`refresh.log` 当时 721,723 字节 / 6,259 行 /
覆盖 `2026-07-28 14:21:29` — `2026-07-30 01:22:02`，**195 次记进了这个日志的**成功运行。
（不是 195 次全部运行——见文末「未解释的异常」：`history.jsonl` 证明窗内至少还有两次
扫描完整跑完却一个字都没进 `refresh.log`。**这份日志不是扫描运行的完整普查。**）

---

## 结论先说：那 55 次崩溃**没有**让扫描停下

工单 S30 的前提是「崩溃时 `state.json` 与 `index.html` 根本不写，于是页面显示
上一次成功扫描的内容」。**对这 55 个 traceback 而言，这个前提是错的**，实测：

| 判据 | 实测 |
|---|---|
| traceback 总数 | 55 |
| 其中 `UnicodeDecodeError` | 55（100%，没有第二种异常） |
| traceback 里出现 `scan.py` 帧 | **0** |
| 每个 traceback 之后是否仍打印 `index.html written` | **55 / 55**（中位相隔 11 行，最多 23 行） |

**这份文档里的每一个数字都由一个脚本重算**，不是手抄的：

```bash
python monitor/runs/20260729T172301Z-S30-scan-crash-is-invisible/classify_refresh_log.py
# 在 worktree 里跑要把主检出的日志路径当参数传进去（refresh.log 是 gitignore 的，
# worktree 里没有）：... classify_refresh_log.py C:/Users/user/Desktop/theoria/monitor/refresh.log
```

本轮实测输出存在同目录的 `classify_refresh_log.out`。日志被清理之后脚本会说
「已经没有了」并退 2，而不是打印一串零——**缺输入不等于干净结果**，这正是本仓
一直在立的那条规矩。

页面从来没有变陈旧。它每一轮都被正常写出——**带着一个伪造的绿。**

## 唯一的一类：一个死在 reader 线程里的解码错误

55 次全是同一类，同一个最内层帧：

| 字段 | 值 |
|---|---|
| 异常 | `UnicodeDecodeError: 'gbk' codec can't decode byte 0xNN in position N` |
| 编解码器 | `gbk`（cp936，宿主 `locale.getpreferredencoding()`），55/55 |
| 出错字节 | `0xa1`×12 / `0xac`×12 / `0x80`×9 / `0x94`×9 / `0xa8`×8 / `0xaa`×5，合计 55（一次崩溃一个）——即 `—`（U+2014 = `e2 80 94`）与中文字符的 UTF-8 后续字节 |
| 最内层帧 | `subprocess.py:1615`，函数 `_readerthread`，语句 `buffer.append(fh.read())` |
| 调用链 | `threading.py:_bootstrap_inner` → `threading.py:run` → `subprocess.py:_readerthread`。**整条链在工作线程里，所以 traceback 中一个 `scan.py` 帧都没有**——这正是这份日志看起来无法归属的原因 |
| 实际来源 | `scan.py` → `probe_conflicts()` → `git()` → `subprocess.run(...)` → `Popen._communicate` → reader 线程 |
| 出错的子命令 | `git log --name-only --format=%h%x01%s -40`（按 `(字节, position)` 指纹逐条比对，55/55 命中、38/38 个不同签名命中） |
| 时间窗 | `2026-07-28 14:21` — `23:21`，**连续 55 次运行**（编号 0–54，运行间隔 8.65–11.35 分钟，中间没有漏掉的周期）；之前 0 次，之后 26 小时 0 次 |
| 分布 | **不是一轮一次**：第 38 轮有两个（见下「未解释的异常」），**第 49 轮一个都没有** |

### 为什么它是静默的（这才是要害）

解码在 reader **线程**里抛出，线程里的异常不会往上传播。`subprocess` 随后执行
`stdout = stdout[0] if stdout else None`——缓冲区是空的，于是
`CompletedProcess.stdout` 变成 `None`。`git()` 里的 `out.stdout.strip()` 抛
`AttributeError`，被那句 `except Exception: return ""` 吞掉。`probe_conflicts`
拿到空字符串，找不到跨领地提交，**返回 green**。

实测这条因果链每一次都成立：

| 周期 | conflict_scan 判决 |
|---|---|
| 带 traceback 的 54 个周期 | **green 54 / risk 0** |
| 不带 traceback 的 141 个周期 | green 51 / **risk 90** |

也就是说：这个探针在正常周期里有 64%（90/141）报红，而在它瞎掉的那 54 个周期里
**一次都没报过红**。日志里那句原话是

> `conflict_scan green 三类检查全空：无冲突标记、无未合并路径、近 40 个提交无跨领地改动。`

——一句声称三项检查都通过的话，印在**其中一项**根本没跑成之后。

（**只有一项**，不是两项。(b) `git ls-files -u` 在索引干净时返回 0 字节，空字节
GBK 解码不会出错，所以那次 `""` 是真的答案。两处 git 调用都瞎的话，一个周期里会有
两个 reader 线程 traceback，而实测每个周期只有一个。本件仍然把 (b) 和 (c) 一起
改用 `git_or_none`——(b) 今天没被这个缺陷打中，不代表它不是同一个判决口，
超时和 git 不存在照样打得中它。）

### 窗内那一次天然对照

第 49 轮（`2026-07-28 22:30:51`）是这 55 次运行里**唯一没有 traceback 的一次**，
而它也是**窗内唯一报了 `risk` 的一次**（`跨领地提交…aeee50e…`）。
它两侧的第 48、50 轮都带着 traceback、都报绿。

同一份代码、同一个仓库、相邻十分钟：**唯一的自变量是那次解码有没有崩**，
因变量就从 risk 翻成 green。这是这份日志里最接近对照实验的一段，
比 54/0 对 51/90 的相关性更硬。

## 修没修

| 层 | 状态 | 证据 |
|---|---|---|
| **解码本身** | **已修** | `scan.py` 的 `git()` 现在带 `encoding="utf-8", errors="replace"`。落在 `05947108`（2026-07-28 22:58:50，分支 `agent/s13-verify-gate-enforced`），经 `7f6aa876`（23:27:44）进 master——比最后一次崩溃（23:21:18）晚 6 分钟，这解释了为什么「修复提交已存在」之后崩溃还持续了 22 分 28 秒 |
| **全仓同形调用点** | **已清** | `monitor/*.py` 中不再有 `text=True` / `universal_newlines=True` 而不显式给 `encoding=` 的 `subprocess` 调用。`childio.py` 把规则固化成 `run_utf8()` / `run_console()` 两个入口 |
| **「空即是清白」的判断** | **本件修的就是这个** | 见下 |
| 输入侧 | **无需修，且仍然「敌对」** | 数据是 git 的 stdout，来自 commit 对象，是 UTF-8 且不可变。今天 `git log --name-only --format=%h%x01%s -200` 仍然 GBK 解码失败（`0x8a`；position 是**会漂的**——新提交把窗口往前推，2026-07-29 复核时是 29000，所以别把它当稳定判据，稳定的是「仍然失败」这件事）。`-40` 眼下碰巧能过，只因为最近 40 条 subject 恰好是 ASCII——这是巧合，不是治好了 |

### S30 补上的那一层

解码修好之后，**超时、git 不存在、非零退出**仍然产出空输出，而空输出仍然被读成
「干净」。所以本件把「拿不到答案」与「答案是空」分成两个值：

* `scan.git_or_none()` 失败时返回 `None`——包括 `returncode != 0`，也包括
  `stdout is None` 这个 2026-07-28 的确切形状（退出码 0、无输出、父进程里什么都没抛）；
* `scan.git()` 保留，把失败压平成 `""`，给那些只是**显示**结果的调用点；
* `probe_conflicts` 两处会被用来下判决的 git 调用改用 `git_or_none`，任一为
  `None` 时返回 **`missing`** 而不是 green，detail 里点名是哪一次调用瞎了。
  用 `missing` 不用 `risk`：没看成不等于看见了冲突，本仓不把「没有证据」画成红，
  也不画成零。

  **但顺序是有讲究的，第一版恰好写反了**：检查 (a) 扫的是磁盘上的文件，不依赖
  git，它找到的冲突标记不该被一次 git 失败撤销。第一版把 `missing` 放在
  `findings` 之前返回，于是「git 瞎了 + 树上真有冲突标记」会报 `missing`——
  而 `_VERDICT_RANK` 里 `missing`(1) 排在 `risk`(0) **之上**，那是一次
  **从最坏判决往上升**。同一个病，由它自己的修复亲手复现。
  现在 `findings` 先判，瞎掉的部分**并列**写进 detail，不取代它。

* 同一条规矩，另外三个**拿 `git()` 结果下判决**的调用点也一起改了——它们各自
  都能凭空造出一个绿：`probe_spec_freshness`（空 → `"0"` → 「spec.py 一点不
  陈旧」）、`probe_append_only`（空 → 删除 0 行 → 「append-only 完好」）、
  `collect_metrics`（空 → `dirty: []` → 「工作树干净」）。
  和那 55 次的假绿是同一个形状，就在同一个文件里。

负样本在 `monitor/tests/test_scan_failure_exit.py`：
`test_a_blinded_conflict_probe_does_not_report_green`（红）、
`test_the_reader_thread_shape_is_the_one_that_is_caught`（退出 0 + `stdout=None` 的
那一支，只抓异常的守卫会漏掉它）、`test_a_probe_that_can_look_still_reports_green`（配套绿）。

## 仍未修的（如实记账）

1. **`git()` 的 `except Exception: return ""` 还在。** 这是有意保留的：十几个调用点
   只是显示结果，不下判决。风险是**新写的**调用点若用了 `git()` 又拿它下判决，
   同一个形状会复发。没有机器检查能拦住这一点。
2. **`probe_conflicts` 的 (a) 段**（扫文件里的冲突标记）里
   `except Exception: continue` 逐文件吞异常，一个读不出来的文件与一个干净的文件
   不可区分。本件没动它——它需要的是逐文件的 unreadable 计数，属于另一件工单的体量。
3. **窗内有第二个进程在跑 `scan.build()`，来源未查明。**

   两条互相独立的证据，指向同一件事：

   * 第 38 轮（`20:30:33`—`20:40:29`）有**两个** traceback，`Thread-1` 与 `Thread-33`，
     签名完全相同（`0xac`, position 27）。`Thread-1` 在整份日志里只出现这一次，
     它意味着那是该进程的**第一次** subprocess 调用——而一次完整的 `scan.build()`
     不可能，`collect_metrics()` 先跑，`probe_credential_hygiene` 的
     `git check-ignore` 也排在更前面。
   * 更硬的一条：`monitor/history.jsonl` 在崩溃窗内有两行
     （`2026-07-28 14:24:22`、`18:12:55`），而 `refresh.log` 里**没有对应的运行行**，
     两者都恰好落在两次已记录运行的中间。`append_history()` 是在 `build()` 内部调用的，
     而闸门跑 `scan.build` 时会把 history 导向临时 `out_dir`——所以这两行是**真实完成的、
     写进了真 `monitor/` 的扫描，却一个字都没进 `refresh.log`**。

   复算：

   ```bash
   python -c "
   import json,re
   h=[json.loads(l) for l in open('monitor/history.jsonl',encoding='utf-8') if l.strip()]
   lines=open('monitor/refresh.log','rb').read().decode('utf-8',errors='replace').splitlines()
   runs={re.match(r'\[(.*?)\]',l).group(1) for l in lines if 'index.html written' in l}
   print([r['ts'] for r in h if r.get('ts','').startswith('2026-07-28')
          and '14:21:29' <= r['ts'][11:] <= '23:21:18' and r['ts'] not in runs])
   "
   # -> ['2026-07-28 14:24:22', '2026-07-28 18:12:55']
   ```

   **由此得出一条限定，前面所有计数都要按它读**：`refresh.log` **不是扫描运行的完整普查**。
   本文档里的「195 次成功运行」应读作「195 次**被记进这个日志的**成功运行」。
   `reflex.py` 确实会调 `scan.py`，但它把子进程输出收进 `reflex.log`，解释不了这两次。

## 给下一个读到这里的人

`refresh.log` 仍然是 gitignore 的，仍然会被清理带走，这是对的——它是 721 KB 的
控制台流水。**但崩溃记录不再只活在那里**：`scan.py` 的失败出口每次崩溃向
`monitor/crashes.jsonl` 追加一行（被跟踪，一条一行，不含 traceback 正文），
页面同时被改写成红色失败页。
