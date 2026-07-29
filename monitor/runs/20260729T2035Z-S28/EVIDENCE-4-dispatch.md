# S28 条目 11 —— `dispatch.py` / `_runner.py`

做的人：RES-4 主会话（本组原定派给 subagent；连同另外七次尝试全被 API 529 打死）。
零 API 花费：没建过一个计划任务、没起过一个会话。所有取证都在只读数据与
monkeypatch 上做。

---

## 11c 先说，因为它最值钱：那个没人读的账本

条目说 `dispatch-logs/exits.json` 已记录 27 次非零退出而全仓无一处读取。
`grep -rn "exits.json" --include=*.py` 证实：**只有 `_runner.py` 自己**
（写入端）出现，没有任何读取端。

### 接上它的第一件事，是发现它坏了

第一次用 `json.load` 读这个文件：

```
json.decoder.JSONDecodeError: Extra data: line 581 column 2 (char 11665)
```

第 579-585 行长这样——**一个完整的 JSON 对象，后面跟着另一个对象的尾巴**：

```
    }
  ]
}120,
      "log": "W-1671-20260729T143043Z.log",
      "ended": "2026-07-29T15:22:45Z"
    }
  ]
}
```

### 病因，就在写入端那一行

`_runner.py:29` 旧写法：

```python
tmp = EXITS + ".tmp"
json.dump(data, open(tmp, "w", encoding="utf-8"), indent=2)
os.replace(tmp, EXITS)
```

**所有会话共用同一个临时文件名。** 两个同时退出的会话各自以 `"w"` 打开
`exits.json.tmp`、在各自的偏移上写，于是 `os.replace` 搬过去的是两次写入的叠加。
文件头的注释写着 `own file, no registry race`——而这个 race 是它**和自己**的。

### 第二层后果：账本已经死了 4.9 小时，没有任何人知道

`record_exit` 整个包在 `except Exception: pass` 里。文件一坏，
`json.load` 在 try 里抛出，于是**此后每一次写入都被静默丢弃**。实测：

```
last written (UTC): 2026-07-29T15:59:01Z
now         (UTC): 2026-07-29T20:50:07Z
silent for: 4.9 hours

session logs last written AFTER the ledger froze: 62
   2026-07-29T20:37:17Z  Z0-permprobe-20260729T203717Z.log
   2026-07-29T20:47:21Z  Z0-permprobe-20260729T204721Z.log
```

**4.9 小时里 62 个会话退出，账本一条也没记上。** 那句 `pass` 的注释
（「观测不该带走会话」）是对的，但它连**失败本身**也一起吞了。

### 修

* **读**：`dispatch.read_exits()` / `dispatch.exit_summary()`。
  读不出来时 `ok=False` 并带 `problem`，**而且尽量把前缀救回来**——
  但救回来不等于没事，`ok` 仍是 False，因为写入端此刻正在丢记录。
* **写**：临时名改成 `exits.json.<pid>.tmp`（每个写者一个），race 从根上消失；
  救不回来的旧文件**隔离**（`.corrupt-<UTC>`）而不是覆盖，
  因为一整天的死因史比当下这一条记录值钱；写失败往
  `dispatch-logs/exits-write-failures.log` 记一行。
  `record_exit` 仍然保证不抛（有一条测试专门钉这一点）。

### 接上之后第一次读到的东西

```
  ok            False
  problem       corrupt: JSONDecodeError: Extra data: line 581 column 2
                (char 11665); recovered valid prefix, 98 trailing bytes discarded
  sessions      48
  runs          81
  nonzero       36
  short         20
  newest_ended  2026-07-29T15:55:55Z
```

**36 次非零退出**（条目写的是 27，那是普查当天的数），
**20 次「活了不到 60 秒」**——也就是「起来了，然后立刻死了」。

### 我自己的补丁犯了同一个病，记在这里

第一次跑 `exit_summary` 时我传了一个 Git-Bash 风格的路径，在 Windows 上
`os.path.exists` 为假，于是它印出：

```
ok=True  problem=None  sessions=0  runs=0
```

**「账本不存在」和「还没有人死过」收敛成了同一个健康答案**——
`read_exits` 里有 `missing` 标记，而 `exit_summary` 把它丢了。
这正是条目预告的第二层结论（出问题最多的是补丁本身）。已把 `missing` 传下去，
并留了一条测试 `test_a_missing_ledger_is_distinguishable_from_an_empty_one`。

### 给 `scan.py` 的补丁提案（**我没改，那是别人的文件**）

`probe_standing`（`scan.py:1146-1155`）现在数 `standing.log` 里 `" START "`
的行数，印成「累计起过 %d 次常驻会话」并保持 green。**崩溃循环每 30 分钟把这个
数字推高一次**——每次重启都是一行新的 START，所以那个数字**随故障单调上升
而颜色不变**。缺的那一半正是「起来之后怎么了」，现在有了：

```python
# scan.py, probe_standing 内，starts = [...] 之后
try:
    sys.path.insert(0, HERE)
    import dispatch as _d
    ex = _d.exit_summary()
except Exception as exc:
    ex = {"ok": False, "problem": "%s: %s" % (type(exc).__name__, exc)}
if not ex.get("ok"):
    deaths = "；死因账本**读不出来**（%s）" % (ex.get("problem") or "?")
    status = "risk"
else:
    deaths = "；其中 %d 次非零退出、%d 次活不到 60 秒" % (ex["short"], ex["nonzero"])
    # 崩溃循环：起过很多次，而多数都是短命的
    if len(starts) >= 5 and ex["short"] >= max(3, len(starts) // 2):
        status = "risk"
        deaths += "　→ **看起来是崩溃循环，不是正常轮换**"
```

（`status` 是 `probe_standing` 现有的那个变量；把 `deaths` 拼到 `detail` 末尾。
`exit_summary` 的返回字段名就是为这个调用点起的。）

---

## 11a · `via_task` 的 ok 是调度器的收据，不是会话的命

`dispatch.py:415` 旧写法 `ok = r.returncode == 0`，其中 `r` 是
`schtasks /Run`。**它在把任务交出去的那一刻就返回 0**，所以一个撞限额、
缺 CLI、或提示词读不出来而在一秒内死掉的会话，产生与健康会话
**逐字面量相同**的 `ok=True`。而 `standing.py:396` 的
`START <编号> ok=True` 是舰队关于「研究员被拉起来了」的首要记录。

取证不能真去 `/Run` 一个任务（那要花钱起会话），所以证据取自结构与真数据两头：

* 结构上：`task_state(task)` 这个函数**本来就在同一个文件里**（`dispatch.py:447`），
  `via_task` 从不调用它。判据与判据所需的工具之间只差一次调用。
* 真数据上：上面那 20 次「活不到 60 秒」的退出，每一次在
  `standing.log` / dispatch 的输出里都是一句 `started` / `ok=True`。

### 修

起完等 `LAUNCH_SETTLE_S = 8` 秒再问一次调度器，返回值从布尔改成**四个值**：

| 返回 | 意思 | 该找谁 |
|---|---|---|
| `running` | 真的在跑 | —— |
| `died-on-arrival(<状态>)` | 起来了，然后没了 | 查会话为什么死（`exits.json`） |
| `declined` | `schtasks /Run` 自己非零 | 查调度器为什么不收 |
| `state-unknown` | 查到了任务但认不出状态行 | 不许当成健康 |

`died-on-arrival` 必须与 `declined` 分开：**这两件事该找的人完全不同**，
而旧代码把它们和成功一起压成了一个 `True`。

两个连带的地方，都是这次修复自己会引入的新假信号：

1. **印出来的词是被 grep 的。** `reflex.py` 用 `"started" in r.stdout` 判断补员
   成功。所以只有 `running` 才准印 `started`，死在起跑线上的必须让那个 grep 落空。
2. **`standing.py:398` 的 `if ok:` 对任何非空字符串都为真。** 照原样留着，
   `"died-on-arrival(Ready)"` 会被记成一次成功启动——**同一个假信号平移两个文件**。
   已改成 `if ok == "running":`，并留了一条测试钉住它。
   （`standing.py` 本来是「别人的文件」，但那个组的 subagent 死了，
   这一轮由我自己在做同一个分支上的两个文件，不存在越界。）

中文控制台照顾到了：`schtasks` 印的是「正在运行」，`"Running"` 一次也不会命中。
这仓库为 GBK/UTF-8 已经付过五次账，其中一次把八个活着的工人报成死的。
两个词都认，有测试。

---

## 11b · `_runner.py` 缺 `which("claude")` 的守卫

`_runner.py:98` 取 `shutil.which("claude")` 就直接用；`dispatch.py:162` 早有这道
守卫。缺 CLI 时旧路径一路走到 `subprocess.run([None, ...])` 抛 `TypeError`，
被兜底的 `except Exception` 收成一句 `runner exception: TypeError(...)` 加 `code=-1`
——**一次环境缺失被记成一次普通的会话失败**，而这两件事该找的人完全不同。

修：命名它，给它自己的退出码 127（惯例的 command-not-found），
写一行 `=== runner abort ... ===` 进会话日志，并往账本记
`{"code": 127, "error": "claude CLI not on PATH (...)"}`。

**写的时候自己踩了一次同类的坑**：第一版写的是 `return 127`，
而文件末尾是 `if __name__ == "__main__": main()`——**返回值被丢掉，进程会退出 0**。
这就是本条目的病症降一层的样子。改成 `sys.exit(127)`，并留了一条测试
`test_the_guard_uses_sys_exit_not_return`。

---

## 测试

`monitor/tests/test_dispatch_no_third_value.py`，20 条，全绿：

```
monitor $ python -m pytest tests/test_dispatch_no_third_value.py -q
....................                                                     [100%]
```

阴性对照（「永远报警等于没报警」）：

* `test_a_running_session_still_reports_started` —— 健康启动必须仍然印出
  `started` 那个词，因为 reflex 在 grep 它；
* `test_a_valid_ledger_reads_clean` / `test_a_healthy_ledger_reports_zero_deaths_not_a_false_alarm`
  —— 干净账本 `ok=True problem=None`，长命的干净会话既不算短命也不算异常；
* `test_a_successful_write_leaves_no_complaint` —— 写成功时失败日志**必须不存在**；
* `test_record_exit_still_never_takes_the_session_down` —— 原来的保证不许被这次修复
  破坏：观测不许抛。

一条测试**先红，然后发现是测试错了而不是代码错了**：
`test_a_corrupt_ledger_is_quarantined_not_overwritten` 用「合法对象 + garbage」
当输入，但那种损坏是**可救的**，代码正确地救回前缀、追加新记录、不隔离。
把它拆成两条（可救的就地救活并留痕、不可救的隔离），
因为「可救时也隔离」本身就是数据丢失。

## 安全线

没有建/删/跑任何计划任务，没有起任何会话，没有花一分 API。
`via_task` 的测试把 `subprocess.run`、`task_state`、`LOGS`、`REGISTRY`、`PROMPTS`
全部 monkeypatch 到临时目录，并把 `LAUNCH_SETTLE_S` 设成 0。
**主检出的 `dispatch-logs/` 只读过，没写过**——包括那个已损坏的 `exits.json`：
它是未跟踪文件、属于活系统的运行时数据，我不手改生成物。
修复本身会在下一个会话退出时就地把它救活（前缀救回 + 追加），
这件事已 `bus.py say` 报给监控。
