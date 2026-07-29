# S28 条目 6 与条目 10 —— `standing.py` / `reflex.py`

做的人：RES-4 主会话（本组原定派给 subagent，该 subagent 与另外五个一起被
API 529 打死，见本文件末尾「扇出失败」一节）。

规矩照条目原文：**逐条修、逐条先给「修之前这个假信号确实存在」的证据。**
下面每一条的「修之前」都是真跑出来的输出，不是复述。

---

## 条目 6 · 板查询崩溃被写成 0

`standing.py:307-310`（原文记 223）：

```python
try:
    claimable = len(board_mod.candidates(lane))
except Exception:
    claimable = 0
```

### 修之前（实测）

把 `candidates()` 换成必抛的函数，拿一个既无未读也无认领的编号——
即 `claimable` 单独决定这个编号会不会被拉起来的情形：

```
--- A: healthy board, genuinely empty lane ---
   {'unread': 0, 'held': 0, 'claimable': 0, 'any': False}
--- B: board query CRASHES, real lane that does have work ---
   {'unread': 0, 'held': 0, 'claimable': 0, 'any': False}

A == B : True
```

**A == B 为真**：「量过了，这条赛道没活」与「根本没量到」返回**逐字节相同的字典**。
两者都走 `sweep` 的 `not w["any"]` 分支，印出同一句

```
skip RES-9: no work (unread=0 held=0 claimable=0)
```

而异常对象被丢掉，`standing.log` 里没有任何痕迹。注意 B 用的是**真的有活**的
infra 赛道——所以这不只是「没报告故障」，是**报告了一句关于板的假断言**，
而板恰恰是刚才没读成的那个东西。

一个中途的自我纠正记在这里，因为它本身就是这类 bug 的样子：我第一次取证用的是
`RES-4` 自己，它有 `unread=1 held=1`，于是 `any` 早已为真、根本走不到那个分支，
我的第一版输出把分支名印错了。换成一个真正空手的编号才拿到上面这对。

### 修之后

`claimable` 有了第三个值 `CLAIMABLE_UNKNOWN = -1`，并且：

* 异常**记一行** `BOARD-QUERY-FAILED lane=... agent=... <类型>: <消息>`；
* `any` 从 `bool(unread or held or claimable)` 改成 `... or claimable > 0`。
  这一步是必须的，且是这个补丁最容易写错的地方：**Python 里 `-1` 是真值**，
  照抄哨兵而不改 `any`，会让「测不到」直接变成「有活」；
* `sweep` 里给 -1 单开一条 skip 理由，排在 `not any` 之前。

**为什么 -1 不当作「有活」也不当作「没活」。** 把测不到算成有活，会让一块坏板
在夜里每一跳都拉起一个花钱的会话，而那个会话读的是同一块坏板；算成没活就是
原 bug 本身。所以走第三条路：**不起会话，但在日志里留一条自己的记录。**
条目要求的是 -1 不许被静默地当成「少于 N，所以什么也不做」——它现在不静默了。

**哨兵的消费者全查过**：`grep -rn "work_for\|claimable" --include=*.py` 在
`monitor/` 下除 `standing.py` 自己外**零命中**（唯一的命中是一个测试的函数名）。
所以 -1 不会漏到别处被当成计数。这一点重要——一个没人区分的哨兵，
是同一个 bug 换了个数字。

### `reflex.py` 里的同一条（两处）

`reflex.py:196-206` 的 `except Exception: avail, claimed = 0, 0`，与
`reflex.py:296-303` 的 `except Exception: pass`。实测：

```
crashing board -> events=[]  (an empty board would have emitted SUPPLY-LOW:0)
crashing board -> avail=0, so the worker-refill loop is skipped in silence
```

第二处是这个 bug 最锋利的形态：**一块坏板比一块空板更安静**——空板至少发
`SUPPLY-LOW:0`，坏板一个字都不发。现在发 `SUPPLY-UNKNOWN:<类型>`。

第一处的**动作不变**（补员的目标人数由板深度算出，而板深度正是没读到的那个数，
所以跳过仍然是对的），改的是它上了记录：`BOARD-QUERY-FAILED:<类型>(refill-skipped)`。
这里我**撤掉了自己的第一版**：我一开始在这里也塞了 -1 哨兵，然后立刻 `avail = 0`
把它抹掉——那是为了形式上的一致而增加的风险，而 `claimed` 变量赋值后全文再没被
读过。补丁越短越好，尤其在这个仓库里，普查的第二层结论就是补丁自己最容易出问题。

---

## 条目 10 · 只看 ci_merge 的 stdout，不看返回码

`reflex.py:298-301`（原文记 271）。

### 修之前（实测，三种命运一个观察结果）

```
clean no-op (exit 0, nothing to merge)     returncode=0 -> events=[] -> reflex.log: 'quiet'
CRASH (exit 1, traceback on stderr)        returncode=1 -> events=[] -> reflex.log: 'quiet'
killed / timeout-ish (exit 3)              returncode=3 -> events=[] -> reflex.log: 'quiet'
```

返回码在那个调用点**连名字都没绑**，所以后面任何一行都无法把它捞回来。

### 先确认这条告警不会喊狼来了

修之前先查了一件事，否则这个修复本身就是个新的假信号来源：
**`ci_merge.py` 全文没有一个 `sys.exit`。** 冲突、红闸门是以 `monitor/ci/` 下的
FLAG 文件 + stdout 的 `FLAG` 行报告的，不是以退出码报告的。所以非零只意味着
**合并器自己坏了**，不意味着「有一次合并被拒绝」——告警是干净的。
这条判断本身留了一个测试（`test_the_real_ci_merge_has_no_deliberate_nonzero_exit`），
将来谁给 ci_merge 加一个「无事可做就 exit 2」，那个测试会先红，
提醒把告警收窄，而不是让它开始喊狼来了。

### 修之后

`merge:EXIT-<n> <stderr 第一行>`。带上 stderr 第一行是因为退出码只说「坏了」，
第一行说「怎么坏的」。

### 顺带查出的三个同族现场（条目只要求「报告」，我修了，理由如下）

同一个文件里还有三处「抓输出、丢状态」，是同一个 bug 的同一张脸：

| 位置 | 原写法 | 崩了会读成 |
|---|---|---|
| `board.py sweep` | `sw.stdout` 里找 `freed from` | 「没有认领需要交回」 |
| `dispatch.py --reap` | `run([...]).stdout` **内联取** | 「没有工人需要回收」 |
| `git branch -r` | `run([...]).stdout.lower()` **内联取** | **「没有人交付过」** |

后两处是内联取 `.stdout`，所以返回码不是被忽略，是**不可恢复**。

第三处我原本只打算加一行日志，写完注释才发现方向反了，于是改了做法——
记在这里因为这正是条目要防的东西：`remote` 为空字符串时，下面每一个
`"agent/%s" % slug in remote` 都为假，于是**每个死掉的会话都读成「没交付过」，
循环会去重启那些其实已经干完活的会话**。这个假信号的失败方向**是花真钱的那一边**。
所以这里不能只记日志，必须跳过整个循环：git 查询失败时发
`revive:GIT-EXIT-<n>(loop-skipped)`，复活循环整段放进 `else`。
有一条测试专门钉住「revive 调用必须在 git 守卫的 else 里面」。

### 一处**故意不改**，理由写在测试里

`reflex.py:246` 的内存读数仍然内联取 `.stdout`，**但它不是这个 bug**：
`free_gb` 初值是 `0.0`（fail-closed，方向是少拉工人），powershell 失败时
stdout 为空、`int("")` 抛出、发 `mem-unreadable` 事件——它已经有第三个值了。
（它是普查当天当场修掉的四条之一，旧写法初值 99GB，读不到就把门大开。）

这个豁免是我自己的测试逼出来的：我先写了一条「文件里不许再出现
`]).stdout`」的宽断言，它红了，红在这个内存读数上。**代码是对的，断言太宽。**
所以断言收窄成只钉那两处真有问题的调用，并新增一条
`test_the_memory_read_is_exempt_and_this_is_why`，把豁免写成一个有记录的判断
而不是一次疏漏——`free_gb = 0.0` 或 `mem-unreadable` 哪天没了，它就红。

---

## 测试

`monitor/tests/test_standing_reflex_no_third_value.py`，14 条，全绿：

```
monitor $ python -m pytest tests/test_standing_reflex_no_third_value.py -q
..............                                                           [100%]
```

每条修复都配了**阴性对照**，因为「永远报警等于没报警」：

* `test_a_genuinely_empty_board_still_reads_as_zero` —— 本组最重要的一条。
  这次修的是「加第三个值」，不是「把第二个值改响」：**真空板必须仍然是 0，
  且一个字都不许记**；
* `test_a_board_with_work_still_reads_as_work` —— 反方向的对照；
* `test_a_successful_merge_is_unchanged` —— 干净合并的 events 必须与从前逐项相同；
* `test_a_crashed_merger_no_longer_reads_as_a_clean_no_op` 里 `clean == []`；
* `test_the_skip_reason_survives_a_cp936_console` —— `line.encode("cp936")`。
  这台机器的控制台是 cp936，本仓库已经两次在**已经改完状态之后**才抛
  `UnicodeEncodeError`；
* `test_reflex_and_standing_still_import_and_compile` —— 这两个文件此刻正在
  这台机器上跑（跑主检出）。一个语法错误合进去会停掉整个舰队，
  而能报告这件事的正是舰队本身。

## 安全线

零 API 花费，封存堆零接触。没有跑过 `standing.py` / `reflex.py` 的任何
会拉起会话、派计划任务、合并分支或写主检出的路径——全部用 monkeypatch 与
合成结果对象测试。取证用的子进程只有 `python -c "sys.exit(n)"`。

## 扇出失败（记录，因为它影响这件活的做法）

本组连同另外五个 subagent（board.py 组、scan.py 组、dispatch.py 组、
一个只读侦察、以及 board.py 组的一次重试）**全部以 API 529 Overloaded 立即死亡，
一个字节都没写**。所以 S28 从「四组并行 + 对抗复核」改成主会话串行推进。
没有工作损失，因为每组都被要求增量落盘——这次没落到盘的东西，
本来也确实不存在。已 `bus.py say` 告知监控：若其他会话报「没有进展」，
这是一个可能的上游原因。
