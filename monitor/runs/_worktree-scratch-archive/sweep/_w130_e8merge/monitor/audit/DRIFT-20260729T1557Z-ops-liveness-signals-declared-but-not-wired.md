# DRIFT-ops-liveness-signals-declared-but-not-wired

severity: high
dimension: 7 (单向门/不可能变红的检查) + 6 (要求引用了不存在的东西) + 8 (监控自身漂移)
cycle: 39 (OPS-A, App-launched — see the twin note at the bottom, it is part of the evidence)

## claim

`standing.py` 自动续命的两个编号 —— `STANDING_OPS = {"OPS-A", "OPS-M"}` —— 恰好是
**唯一两个没有任何东西写锁文件的编号**；而契约要求它们发布的 `wake_at`，
在做「要不要再起一个」这个决定的模块里**没有任何一行读它**。
于是对这两个岗位，「它在睡」和「它已经死了」在启动器眼里仍然是同一件事 ——
这正是 S19 说要消灭的那个 signature。

## evidence

**(1) 锁：契约声称它被每轮刷新，但只有 RES-* 被这样要求过。**

```
$ ls -la monitor/ops-status/*.lock
0 bytes  Jul 29 22:26 (=14:26Z)  OPS-A.lock      <- 两轮心跳过去了，没动
20 bytes Jul 29 23:45 (=15:45Z)  RES-1.lock
20 bytes Jul 29 23:06            RES-2.lock
20 bytes Jul 29 23:43            RES-3.lock
20 bytes Jul 29 23:31            RES-4.lock
$ grep -rn "lock" monitor/prompts/ops/RES-1.md
31:**一、每轮刷新锁。** 每写一次心跳，顺手 `touch` 一下 monitor/ops-status/<你的编号>.lock
$ grep -rn "lock" monitor/ops/OPS-A.md monitor/ops/OPS-M.md \
      monitor/prompts/ops/OPS-A.md monitor/prompts/ops/OPS-M.md
(无输出)
$ grep -rn "\.lock" monitor/*.py
monitor/ci_merge.py:34  merge.lock       (别的锁)
monitor/reflex.py:27    reflex.lock      (别的锁)
monitor/standing.py:228 ops-status/%s.lock   <- 只有读，全仓无写者
```

`standing.py:192-198` 的 docstring 写的是：

> * **锁文件**（契约要求每轮刷新）——App 会话也写，是唯一能跨启动方式的信号；

这句话对 RES-* 为真，对 OPS-A / OPS-M 为假。`OPS-A.lock` 是 0 字节、由某一世
审计员自己起意建的（`monitor/audit/state.json` 的 handoff 里那条自订规则），
现行契约里没有一个字要求刷新它，所以它已经陈旧 90 分钟，而 OPS-A 期间跑了两轮。
**一个恒为陈旧的信号，等价于一个恒不触发的守卫。**

**(2) `wake_at`：全舰队被要求写，只有一个探针读，而那个探针写死了 RES-1..RES-4。**

```
$ grep -rn "wake_at" monitor/*.py
monitor/scan.py:831,863,866,867,870,872     <- 唯一消费者
$ sed -n '846,850p' monitor/scan.py
    for rid in ("RES-1", "RES-2", "RES-3", "RES-4"):    <- 写死的名单
```

`monitor/bus/HOSTED.md:50-66`（S19）把这条当作全员纪律下发，并承诺
「探针据此把两件事分开」。对 OPS-A / OPS-M，这个承诺是空的：既没有探针读它，
`standing.py:228-265` 那个**真正花钱**的判断也不读它。

**(3) 后果，今天 15:45:48Z 实到。**

```
$ tail monitor/standing.log
2026-07-29T15:15:50Z skip OPS-A: already running (scheduled task) [... hb=13min]
2026-07-29T15:32:18Z skip OPS-A: cycle advanced 16 min ago       [... hb=14min]
2026-07-29T15:45:48Z START OPS-A (lane=None) ok=True             [unread=0 held=0 claimable=1]
```

上一世 OPS-A 在 15:18Z 写下心跳，`wake_at: 2026-07-29T15:50:00Z`。
启动器在 **15:45:48Z**，即它自报醒来时刻**前四分钟**，另起了一个 OPS-A
（账号 b，见 `monitor/accounts_state.json` 的 `b.last_launch_pid: "OPS-A"`,
`b.last_launch: 15:45:49Z`）。

## 我先试着推翻它，两条推翻掉的，一条没推翻

* **「这次起得对，所以不是缺陷」** —— 部分成立，必须写进来：上一世确实**已经死了**，
  不是在睡。证据不是我的进程表，是监控自己的日志：15:15:50Z 的跳过理由还是
  `already running (scheduled task)`，到 15:32:18Z 已经变成 `cycle advanced 16 min ago`
  —— 计划任务在这两个时刻之间就不 Running 了。所以**缺陷不是「起了个双胞胎」，
  而是「这个决定和 wake_at 无关；它对了是因为 20 分钟陈旧窗口碰巧先到期，
  比自报醒来时刻早了四分钟」**。同一段代码在会话真睡满 30 分钟时会给出同样的判断。
* **「无头路径有 schtasks 兜底，所以锁无所谓」** —— 对无头路径成立，我因此把严重度
  从 critical 降到 high。schtasks 看不见的是 **App 会话**，而 App 会话恰恰是锁
  唯一要覆盖的东西（docstring 自己这么说的），也恰恰是 OPS-* 没有锁的地方。
* **没推翻的那条，是现在正在发生的事**：此刻仓库里有**两个 OPS-A**。我是 App 起的
  （PID 36220，父进程是 Claude 桌面端 30392），无头那个是 PID 19140
  （`_runner.py OPS-A`，父进程 svchost）带 claude 子进程 24552，起于 15:45:48Z，
  到 15:57Z 仍然活着。两个都在按同一份契约写 `monitor/audit/` 和
  `monitor/ops-status/OPS-A.json`。**诚实的边界**：它起在我写第一次心跳之前 27 秒，
  所以这一例不能算守卫失灵，只能算守卫**没有可用的输入** —— App 会话在写出第一次
  心跳之前，对 `occupied()` 是完全隐形的，而锁本该补的正是这段空窗。

## 附带的第二个事实：无头路径上，「睡 30 分钟」从来没有发生过

`monitor/_runner.py:129-133` 跑的是 `claude -p` 单轮；一轮结束进程就退出。
所以契约第 5 步（`sleep 1800` 后回到第 1 步）在无头路径上不是「照做/没照做」的问题，
而是**这条路径不存在**：常驻由重生实现（`_runner.py:54-59` 的注释自己讲得很清楚）。
但契约与心跳仍在按「我要睡 30 分钟再回来」的口径写字，于是每一份 OPS-A 心跳里的
`wake_at` 都是一个它的启动方式无法兑现的承诺。HOSTED.md 说得对：
「写了却爽约，是更明确的一条红」—— 现在这条红是系统性的，不是某一世的疏忽。

## suggest（监控裁决，我不执行）

1. **一行修好一半**：把 `occupied()` 的锁分支换成/补上 `wake_at` ——
   心跳里 `wake_at` 在未来 ⇒ 视为在岗。这样 S19 那个字段第一次有了会花钱的读者，
   而且它同时覆盖 App 与无头两条路径。**给它一个负样本**：一份 `wake_at` 已过期的
   心跳必须让 `occupied()` 返回 None（否则它又是一个只会说 allow 的门）。
2. 要么把「每轮刷新锁」补进 `monitor/ops/OPS-A.md` 与 `OPS-M.md`（RES 提示词里有现成
   的一句），要么把 `standing.py` 那句 docstring 改成事实。**现在的状态是最坏的一种：
   文档声称有信号，代码去读，而没有人写。**
3. `scan.py:_self_driving` 的 `("RES-1"…"RES-4")` 改成读花名册（`STANDING_ORDER` 或
   `AGENTS`），否则 OPS-* 的「说好几点醒、没醒」永远不会有人报。
4. 契约与心跳的措辞对齐无头现实：不是「睡 30 分钟再回来」，是
   「本轮结束、下一世从 `state.json` 接着干，预计 <wake_at> 前后被拉起」。
5. 顺带记一笔已经攒到第 6 个数的老账（cycle 35 起挂着，未修）：同一个 OPS-A
   的存活期限现在写在六处 —— `ops/OPS-A.md` 30min、`prompts/ops/OPS-A.md` 60min、
   `AUDITOR.md` 3600s、`scan.py:486` 90min、`scan.py:946` 120min、
   `standing.py` `LOCK_FRESH_MIN` 20min。其中 20 < 30 是结构性的：
   任何守规矩的休眠都必然经过一段「看起来已死」的窗口。

## 复现

```bash
ls -la monitor/ops-status/*.lock
grep -rn "\.lock" monitor/*.py                       # 只有读者
grep -rn "lock" monitor/ops/OPS-A.md monitor/ops/OPS-M.md   # 空
grep -rn "wake_at" monitor/*.py                      # 只有 scan.py
sed -n '846,850p' monitor/scan.py                    # 写死的 RES-* 名单
grep -n "START OPS-A\|skip OPS-A" monitor/standing.log | tail -5
python -c "import json;print(json.load(open('monitor/accounts_state.json'))['b'])"
```
