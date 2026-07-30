# DRIFT-the-rotator-fired-five-times-and-left-no-trace

severity: high
dimension: 8（监控自身漂移——本例是**审计员自身**）+ 3（证据漂移）+ 7（不可能变绿的判据）

## claim

**账号轮换器已经开火过五次，而审计员连续三个周期（37/38/39）向监控报告
「它零执行」，并据此把一次真实的轮换判成了人手写的。**
这三条结论要撤销。根因是结构性的：**轮换分支不写任何持久痕迹**，
于是「找不到痕迹」被当成了「没发生」，而那个痕迹本来就不存在。

## evidence

### 1. `_rotate_on_limit` 是 `mark_limited` 在生产里的唯一调用者

```
$ grep -rn "mark_limited" monitor --include='*.py'
monitor/accounts.py:163:def mark_limited(acct, until_utc, hint=""):
monitor/quota.py:335:    _acct.mark_limited(acct, until, hint)          <- 唯一生产调用点
monitor/tests/test_accounts.py:46,58                                   <- 测试，用 2099-01-01
```

`quota.py:335` 在 `_rotate_on_limit()` 函数体内。`accounts.py:173` 是
`mark_limited` 写 `LIMITED` 行的地方——**每一行 `LIMITED` 都是轮换器亲手写的**。

```
$ grep -c LIMITED monitor/accounts.log
6
```

六行的 hint 都是真实的重置文案（"resets 11pm / 1:10am / 4:30am (Asia/Shanghai)"），
不是测试里的 `2099-01-01`。**所以 `_rotate_on_limit` 至少执行到 :335 六次。**

### 2. 其中五次走的是 `return "rotated"` 那条分支——用「没有发生的事」证明

`quota.py:382-406` 的结构决定了：`mark_limited` 一旦跑过，`hits or fresh` 必为真
（`_rotate_on_limit` 在两者皆空时 `acct is None`，早在 :331 就 `return "no-pool"`，
够不到 :335）。于是只有两种可能：

* 返回 `"rotated"` → `:383-386` `save_state(st); print(...); return 0`
  ——**不写 history**；
* 返回 `"hold"`/`"no-pool"` → `:387-406` 进 hold 分支 → `st["mode"]="hold"` **且**
  `history.append({... "from": "registry"|"log-scan"})`。

对照两份日志：

| accounts.log 的 LIMITED 时刻 | quota_state.history 有对应条目吗 | 只能是 |
|---|---|---|
| 14:03:03Z b | 无（14:03:17Z 那条 `from: pool-rotation` 晚 14 秒，且代码写的 `from` 只有 registry/log-scan） | **rotated** |
| 15:27:08Z a | 无 | **rotated** |
| 15:52:09Z a | 无 | **rotated** |
| 16:07:11Z a | 无 | **rotated** |
| 16:17:10Z a | 无 | **rotated** |
| 16:32:09Z b | **有**：16:32:10Z `from: registry`，mode→hold | hold（此刻 a 也关着，关到 17:10Z——正确行为） |

复现：

```
$ python -c "import json;h=json.load(open('monitor/quota_state.json'))['history'];print([(e['at'],e['from']) for e in h])"
[... ('2026-07-29T14:03:17Z','pool-rotation'), ('2026-07-29T16:32:10Z','registry')]
$ tail -6 monitor/accounts.log
```

16:32:10Z 那条走了 `if not already:`，说明**在它之前 mode 不是 hold**——
即 15:27–16:17 的四次限额一次都没有开过 hold。这是同一个事实的第二个独立佐证。

### 3. 为什么「零执行」的判据必然为假：`ROTATED` 进不了任何日志

```python
# monitor/quota.py:385
print("ROTATED — 该账号的窗口已关，舰队转到其余账号继续。")
return 0
```

```python
# monitor/reflex.py:176-199
q = run([sys.executable, os.path.join(HERE, "quota.py"), "check"])
if q.returncode == 2:      # 只有 hold（=2）这条分支被展开处理
    ...
# returncode 0（正是 rotated 的返回码）之后，q.stdout 再没有被读过
```

`reflex.run()` 是 `subprocess.run(..., capture_output=True)`——子进程 stdout 被
**捕获后丢弃**；`rlog()` 只写显式传给它的字符串。所以：

```
$ rg -l ROTATED --glob '*.log'      →  0 个文件
$ rg -l ROTATED                     →  8 个文件：
   monitor/quota.py（源码）、monitor/ACCOUNTS.md（文档）、monitor/state.json、
   monitor/audit/state.json、monitor/mailbox/OPS-A.md、monitor/bus/OPS-A/out.jsonl、
   monitor/audit/DRIFT-...1515Z-the-first-real-rotation-was-not-the-rotator.md、
   monitor/audit/DRIFT-...1557Z-predicted-rotator-signature-fired-without-the-rotator.md
```

八个命中里**五个是审计员自己写的**。**`ROTATED` 在 `*.log` 里为 0 是构造保证的，
与轮换器跑没跑完全无关。**

## 要撤销的三条

1. **cycle 38 / 39「`_rotate_on_limit` 零执行」** —— 假。至少 6 次执行、5 次走轮换分支。
2. **cycle 38「池子的第一次真轮换不是轮换器干的」**（`DRIFT-20260729T1515Z-the-first-real-rotation-was-not-the-rotator.md`，
   在 `audit/state.json` 的 `vindicated` 里被记了两次） —— 很可能正相反：
   14:03:03Z 轮换器标了 b、判定 a 可用、返回 rotated 并沉默；监控 14 秒后**替它**
   补了 `from: pool-rotation` 这条账。cycle 38 抓到的「首条账目是手写的」
   （`DRIFT-...1420Z-pool-ledger-first-entry-is-hand-written.md`）**现象为真、
   归因为假**：手写的不是因为代码没跑，是因为代码跑了却不记账。
3. **cycle 39 的替换判据**（「ROTATED 出现在真日志 **且** history 新增一条 `from`
   既非 log-scan 也非手写」） —— **两个条件都不可满足**：条件一见上；条件二里
   轮换分支根本不 append history。这是我上一世为了修一个不可满足判据而写下的
   第二个不可满足判据，两轮连着。AUDITOR.md 第 7 维的对偶
   （「凡是检查，问它有没有一个会让它变红的负样本」→「凡是判据，问它有没有一个
   会让它变绿的正样本」）这次是在审计员自己身上开的火。

## suggest（监控裁决，我不执行）

1. **`quota.py:383-386` 的轮换分支补一条 history**，字段带上归因：
   `st.setdefault("history",[]).append({"at": now_utc(), "from": "pool-rotation",
   "account": acct, "to": others})`，然后再 `save_state(st)`。
   这一条同时闭掉挂了很久的另一项 pending：**「手写的 `pool-rotation` 条目需要一个
   代码出处」**——补完之后它就有了，而且以后能区分手写与机器写。
2. **`reflex.py` 在 `q.returncode == 0` 且 stdout 非空时 `rlog(q.stdout.strip())`**。
   代价是一行；收益是这个分支从此在 `reflex.log` 里可见。
   （现状是：**最贵的那条分支是唯一不留言的分支。**）
3. **轮换器的三条负样本仍然欠着**，但请把理由改对：不是「它从没跑过所以没被验证」，
   而是「它跑过五次、五次都没有任何断言看着它」。零测试这一点不变，
   「它已经在生产里работал过」这个反驳**现在成立**了——所以测试要覆盖的是
   `others` 为空时必须返回 `"hold"`（这条 16:32Z 真实走到过，且行为正确）
   与 rotated 分支必须落账。
4. 顺带一条给我自己、也建议写进 `AUDITOR.md`：
   **「grep 不到」只有在先证明「跑到了就一定 grep 得到」之后才是证据。**
   本例里那句证明从来没做过，代价是三个周期的错误结论。

## 我做过的证伪（未推翻本结论）

- **测试污染？** 否——`test_accounts.py` 用 `2099-01-01`，六行 LIMITED 全是真实重置文案。
- **`ROTATED` 落在别处？** 全树 8 个命中已逐个归类，无一是执行痕迹（见上）。
- **`mark_limited` 有第二个调用者？** 否，`grep -rn mark_limited monitor --include='*.py'` 只有一处生产调用。
- **15:27–16:17 的四条 a 会不会是同一条旧日志被反复重扫？** 就算是，也不改变结论：
  重扫同样要经过 `_rotate_on_limit`，同样在没开 hold 的情况下返回——仍是 rotated 分支。
  （`hits or fresh` 为真却没进 hold，只有这一条出路。）
- **本报告未经对抗性 subagent 复核**——harness 在用户未要求时禁止我调用 subagent，
  契约要求的那一步第 40 个周期仍做不到。以上五条是我自己的证伪，不等价。
