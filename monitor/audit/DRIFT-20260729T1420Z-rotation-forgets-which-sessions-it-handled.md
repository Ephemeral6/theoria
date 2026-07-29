# DRIFT-rotation-forgets-which-sessions-it-handled

severity: high
dimension: 7（单向门）——兼 5（流程漂移：新分支零负样本）
audit range: `9bc8c880..ad778386`（3 提交），周期 37，OPS-A
utc: 2026-07-29T14:20Z

## claim

`ad778386` 给 `quota.check()` 加的**轮换成功分支**（`quota.py:383-386`）在返回前
**不写回 registry**，于是它对「这几个会话我已经处理过了」的记忆只存在于内存里。
后果不是漏一次，是**每五分钟复发一次**：同一条陈旧的限额日志会被反复归因到同一个
账号头上，把它的重开时刻一次次往后推——**入口每跳都走一遍，出口（到点自动开窗）
每跳都被推翻**。同一分支排进 `requeue` 的会话也永远不会被重发，因为 `resume()`
只在 hold 那条路上可达。

这条分支是这次提交的**主路径**（「舰队转到其余账号继续」），也是全仓
**唯一一条零测试**的新路径。

## evidence

**一、写回被跳过（可逐行核）**

```
quota.py:374     entry["reaped"] = "quota-requeued"     ← 只改内存里的 reg
quota.py:376     st["requeue"].append(pid_str)
quota.py:382     rotated = _rotate_on_limit(hits, fresh, reg)
quota.py:383-386 if rotated == "rotated": save_state(st); print(...); return 0
quota.py:398     json.dump(reg, open(.../registry.json, "w"), ...)   ← 只在 383 没返回时才到得了
```

`save_state()`（`quota.py:180`）写的是 `quota_state.json`，**不是** registry。
registry 的唯一写点是 398 行，被 386 行的 `return 0` 跳过。

**二、下一跳一定会重新命中（反证已做）**

我先试图证伪这条：`reflex.py:151` 在配额检查之前先跑 `dispatch.py --reap`，
如果 reap 会删掉死条目，我这条就不成立。它不删——`dispatch.py:149` 把死会话标成
`reaped="exited"` 并落盘（`:155`）。而 `quota.py:371` 的跳过判据是
`if entry.get("reaped") == "quota-requeued"`，**只跳过这一个字面量**，`"exited"` 照进
`hits`。所以：reap 落盘 `exited` → 轮换分支不写回 → 下一跳 `hits` 原样重现。
今天树上的 registry 68 条里 14 条是 `quota-requeued`、4 条未标记——**那 14 条正是
非轮换分支写回过的**，对照组就在同一个文件里。

**三、出口被反复推翻（不是「慢一点」，是「不会到」）**

每次重新命中都会走到 `_rotate_on_limit` → `quota.py:335 _acct.mark_limited(acct, until, hint)`，
而 `until` 由 `reopen_at({"detected_at": now_utc(), ...})` 现算（`quota.py:332-334`）：

- `quota.py:165-166`：`if when <= local: when += 1 day`——提示里的时刻一旦走过，
  期限跳到**明天**的同一时刻；
- `quota.py:143`：上限 `cap = detected + MAX_HOLD_HOURS`（`:100`，6 小时），
  而 `detected` 每跳都是**当下**。

所以有效期限是一个**每五分钟向前滚动的 6 小时**。一条旧日志就能把一个窗口早已
重开的账号按住不放，而 `accounts.log` 只会一行行地记 `LIMITED`，看起来像是那个
账号真的在反复撞限；`limits_seen` 同步虚增（`accounts.py:171`）。

**四、requeue 有入无出（同一个形状，搬了个家）**

`reflex.py:161` `if q.returncode == 2:` 才 ping、才 `resume()`。轮换分支返回 **0**。
于是 `st["requeue"]` 里的会话没有任何自动路径去重发。`reflex.py:158-160` 的注释
逐字写着这笔学费已经付过一次（「The hold had no exit: nothing ever called resume,
so a session-limit at 09:35 kept the fleet frozen long after its 20:20 reset」）——
新分支把同一个形状原样复制了一份。

**五、零负样本，而且是被自己的文档点名的那一处**

```
grep -rn "rotate\|rotated\|no-pool\|account_of_log" monitor/tests/*.py   →  无输出（20 个测试文件）
```

提交信息宣称「Seven negative samples」，七条全在 `monitor/tests/test_accounts.py`，
测的是 `accounts.pick` 的选号逻辑；`quota.py` 那侧的 `_rotate_on_limit` /
`account_of_log` / 轮换早返回**一条没有**。而 `test_accounts.py:3-7` 的模块 docstring
自己写着：「**轮换器尤其需要**——它平时不动，只在撞限那一刻动一次，而那一刻没人在看。」
判据与覆盖面对不上，就写在同一个文件的头上。

**六、为什么至今没人看见：这条分支还没真正跑过**

`accounts_state.json` 里 `b` 那行（`limited_until` / `limits_seen: 1`）不是它写的——
见同批第二份报告 `DRIFT-...-pool-ledger-first-entry-is-hand-written.md`。
**分支已上膛、尚未击发**，所以一到五全是静态可核的事实，不是已发生的事故。
这也正是现在报的理由：下一次真限额就是它的第一次运行。

## suggest

1. **把 registry 的写回移到早返回之前**，或让轮换分支和 hold 分支共用同一个收尾
   （`json.dump(reg, ...)` + `save_state(st)`）。这一条修完，二、三、四同时消失。
2. **`_rotate_on_limit` 只该在「这次新归因到的」命中上开火**：已经 `quota-requeued`
   的条目不该再次进入 `hits`（判据从 `== "quota-requeued"` 放宽到「已被本机制处理过」）。
3. **轮换分支也要有出口**：要么让 `check()` 在有 requeue 时返回一个 reflex 认得的码，
   要么在轮换成功时就地按新账号重发 requeue——否则「转到其余账号继续」这句话在
   代码里没有对应物。
4. **补三个负样本**（按本仓 S13 口径，每个都要能让它变红）：
   (a) 轮换一次之后，第二跳不得再次 `mark_limited` 同一个账号；
   (b) 轮换分支必须把 `reaped` 落盘（读文件断言，不读内存）；
   (c) 归因不出账号时不得关任何账号（`account_of_log` 返回 None → 状态文件零改动）。
5. 顺带：`accounts.py:171` 的 `limits_seen` 目前是「被标记次数」而不是「撞限次数」，
   修完 1、2 之后两者才会相等；在那之前盘面上这个数不可信。
