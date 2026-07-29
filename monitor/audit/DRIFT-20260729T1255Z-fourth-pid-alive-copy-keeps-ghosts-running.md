# DRIFT-fourth-pid-alive-copy-keeps-ghosts-running

severity: medium
dimension: 7（不可能变红的检查）＋ 8（监控自身漂移）
audit range: `de90ba90..9bc8c880`，周期 36，OPS-A

## claim

`pid: 0` 那条修复（对抗性普查 → `dispatch.pid_alive` 加 `pid<=0` 守卫，
`quota.pid_alive` 改为引用同一份实现）**只覆盖了三个消费者，盘面上还有第四份拷贝**：
`scan.py:1467 pid_alive_win`，它没有守卫。而本机 `schtasks /Query /V` **不给 PID 字段**，
所有任务启动的会话在注册表里都是 `pid: 0`，`tasklist /FI "PID eq 0"` 又会返回
System Idle Process 那一行——于是 `"0" in out` 恒真。
**后果是页面上此刻就有九个死了一天多的会话写着「进行中」，而「失联」这个状态
对任何任务启动的会话都不可能出现。**

## evidence

**一、修复之后启动的四个会话，pid 仍然全是 0。**
修复提交 `0c099ae8`（本地 19:11，即 11:11Z）之后启动的全部会话：

```
RES-1  pid=0  20260729T123003Z    RES-2  pid=0  20260729T124503Z
RES-4  pid=0  20260729T124548Z    OPS-A  pid=0  20260729T124633Z
```

原因可当场看见——`schtasks /Query /TN TheoriaAgent-OPS-A /FO LIST /V` 的输出里
**没有 PID 这一行**（有 Status / Task To Run / Idle Time）。
`dispatch.py:327-338` 的抓取循环因此从不命中，`real_pid` 停在初始值 `0`。
`dispatch.py:98-107` 的注释已经把这一整条写下来了，所以**这半条不是新发现，
我不重复它的诊断**（归属：2026-07-29 那次 57 个 agent 的对抗性普查）。

**二、新的一半：守卫没进第四份拷贝，而那份就是渲染页面的那份。**

```
dispatch.py:108   if pidnum is None or pidnum <= 0: return False      ← 有守卫
quota.py:184-188  return dispatch.pid_alive(pidnum)                   ← 引用同一份
scan.py:1467-1477 def pid_alive_win(pidnum): ... return str(pidnum) in (out or "")   ← 无守卫
```

`scan.py:1488` 用它判 `alive`，`:1498` 只有 `alive is False` 才渲染「失联」。
`pid_alive_win(0)` 恒真 ⇒ **`失联` 这一支永远走不到，`n_lost` 恒为 0。**

**三、屏幕上的实证（`monitor/index.html`，本轮渲染）**：

```
<b>W-1520</b><em>W-1520 · 1771 分钟</em> …… 进行中
<b>W-5201</b><em>W-5201 · 1648 分钟</em> …… 进行中
<b>APP-V3</b>                          …… 进行中
```

1771 分钟 = 29.5 小时。同一时刻 `schtasks /Query /TN TheoriaAgent-W-5201` 报
`Status: Ready`（没在跑）。而 `W-5201` 的产出**今天下午已被别人打捞过**——
`6ee8538a`「A6 salvage: W-5201 wrote 1958 lines and never committed one of them」。
**一个已经被当作遗物打捞过的会话，在盘面上还写着「进行中」。**
名单来自 `monitor/loop_state.json` 的 `in_flight`（9 个：W-1520/1521/1540/1541/
1610/1611/5200/5201/APP-V3），那是上一代循环留下的，没有任何东西会把它清空。

**四、为什么它符合 `FLEET.md` 自己刚立的两条规矩，却仍然发生。**
`FLEET.md` 第六节：「判据来自默认值、空集合或 `except` 分支的地方，换成一个不可能
被误读为健康的哨兵」「每一道闸门都要有一个阴性样本」。这里两条都踩：
`real_pid = 0` 是默认值且 0 恰好是被误读为健康的那个字面量；
`失联` 这道判断没有任何输入能让它出现。
**规矩写在 `9bc8c880` 里，缺陷在同一棵树上，相隔 500 行。**

## suggest

1. **删掉第四份拷贝**：`scan.py` 改为 `import dispatch; dispatch.pid_alive`，
   与 `quota.py:188` 同办法（那次去重的理由写在 quota 那边，同一句话适用）。
   一个进程存活判据在一个仓库里应当只有一份。
2. **`pid` 抓不到时不要落 0**：`real_pid = None`（或 `-1`）并让注册表显式记
   `pid_source: "unavailable"`。**本机 `schtasks` 根本不提供 PID 字段，
   所以「抓取」这条路是死的**——真正可用的身份是任务名
   （`TheoriaAgent-<id>` 的 `Status: Running`，`standing.py:running_tasks()` 已经在用）。
   建议注册表直接记任务名，存活判据统一改问任务表。
3. **`in_flight` 需要一条出口**：九个条目里最老的已 29.5 小时，没有任何代码会移除它们。
   凡是能进入的状态都要问「谁把它退出来」——这条名单目前只有入口。
4. **阴性样本**：一个「注册项 pid 无法获得 + 任务不在运行」的用例，
   断言渲染出的是「失联」而不是「进行中」。现在这道判断没有任何测试能让它变红。

---

**可复核性**：三条命令 + 三个行号，全部可独立复跑。
**对抗复核缺口**：同上一份，本会话不能派 subagent 反驳，请勿按已对抗复核计。
自证伪做过一轮：我先怀疑 `in_flight` 是空的（那样这条就只是潜在缺陷），
读了 `monitor/loop_state.json` 才确认它有 9 个条目、且已渲染进 `index.html`。
