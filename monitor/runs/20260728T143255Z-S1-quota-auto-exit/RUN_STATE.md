# S1 · 配额熔断加自动出口

**W-1250, 2026-07-28, branch `agent/s1-quota-auto-exit`, base `5defae7`.**
离线：零网络、零 API 花费、封存堆零接触。

## 开工先对账：三件里两件树上已经做完

| 工单要求 | 树上状态 |
|---|---|
| (1) reflex 每跳在 hold 下 ping，OPEN 即自动 resume（错峰、半池） | **已做**，`0d28e99`。半池与 90s 错峰在 `quota.py:resume` |
| (2) resume 按优先级重发 requeue，reflex.log 记明自动恢复 | **已做**，按 `PRIORITY` 排序；reflex 写 `quota:RESUMED` |
| (3) 全链路测试 | **没有**——而且 `monitor/board/items/S12-quota-hold-tests.md` 逐字要的就是这件事 |
| （正文末括号）hold 期间 ping 不高于每 20 分钟 | **没有**，而且反着来：reflex 每 5 分钟一跳、每跳都 ping |

所以本轮做的是**真正还缺的那两样**：括号里的限速，和 (3) 的全链路测试。(1)(2) 只
复核未重写。

## 唯一还在漏钱的那一条

`ping()` 是一次真的 `claude -p --model haiku`。`reflex.py` 是每 5 分钟一跳的计划任务，
自动出口接上之后**每跳都 ping，无条件**。于是：

> **熔断器为了问「我能用了吗」，在停机期间持续消耗它正在等待恢复的那个配额。**

今天这次 hold 从 09:35 到 12:45，按现状约 **37 次调用**，工单许可 **9 次**。而且
`reflex` ping 成功后调 `resume`，`resume` 自己**又 ping 一次**——每次出闩买两遍同一个
答案，相隔几秒。

做了三件：

1. **`MIN_PING_INTERVAL_MIN = 20` + `ping --if-due`。** 退出码 3 = 未到点、一分没花。
   reflex 改用这个拼法。
2. **`last_ping_at` 在每次尝试后无条件落盘**，OPEN/CLOSED 都写。只记成功等于
   「窗口关着时不限速」，而窗口关着正是唯一需要限速的时段。
3. **`window_is_open(st)`：新鲜的 OPEN 直接复用，不再买第二遍。**
   方向是**不对称**的，这点是刻意的：新鲜的 **CLOSED 绝不**短路成「继续冻着」——
   那样省钱但会用陈旧证据把舰队关在里面，正是原来那个 bug。省钱只在 OPEN 方向省。

限速闸放在 **reflex 一侧**（`--if-due`），不放进 `ping()`：人手敲
`python monitor/quota.py ping` 要立刻得到答案。限速是用来管住一个无人值守的五分钟
循环的，不是用来跟站在那儿的人争辩的。

## 测试

`monitor/tests/test_quota_autoexit.py`，10 条，**0.2 秒，零网络**。`claude` 在整个套件
里从不在 PATH 上——唯一会调它的函数被 stub，忘了 stub 的测试会因 `shutil.which` 返回
None 而挂，而不是安静地花钱。

最重要的两条断言的是**缺席**：不需要人介入，以及出口没有超支。

**三条负样本，每条都验过会红**（`verify_quota_exit.sh` 第 2 步自动跑）：

| 把代码改坏成 | 哪些测试开火 |
|---|---|
| `MIN_PING_INTERVAL_MIN = 0` | 限速、不买两遍、优先级重发 |
| 截止时间出口去掉 | 全链路、截止出口不依赖窗口 |
| 只记录成功的 ping | 限速、关窗也记账 |

`test_the_deadline_exit_does_not_need_the_window_to_answer` 把 `subprocess.run` 换成
会抛异常的东西：**任何一次 ping 尝试都是硬错误**，它通过是因为什么都没试。这是那条
「不会被它正在等待的停机堵住的出口」的可执行形式。

绿灯：`bash monitor/verify_quota_exit.sh` → **VERIFY OK**，四步。

## 领地字段与正文冲突（登记，不掩盖）

工单头写 `territory: proxy`，正文三次点名 `monitor/quota.py` / `monitor/reflex.py`，
描述的改动在别处无法完成。两种读法冲突，其中一种让这件事**不可能完成**。

处理顺序：先写 inbox 报告（`20260728T142000Z-W-1250-...`）并 `release` 交回板上；
**板把同一件原样发回**——我是当时唯一在领的工人，再 release 就是无限交接。于是按
正文的读法开工，把冲突记在这里、manifest 里和 PARTNER_SYNC 里，而不是悄悄越界。

`S12-quota-hold-tests.md` 的头也写 `territory: proxy`，同样是 monitor-only 的活，
看着是沿用了 S9 的字段。派单时值得校一下 territory 与正文点名的目录是否一致。

## 与 S12 的边界

S12 要的是更宽的迁移矩阵（hold 下 ci_merge 仍可跑、每条迁移一个负样本、外加一份
「只有入口没有出口」的状态机审计：`reflex.lock` 的 25 分钟窗口、三振计数器、board 的
claimed 悬挂）。本轮只写了 S1 点名的那条全链路，外加限速相关的迁移。**S12 仍然值得
单独做**，测试是可加的，不会撞。

## 缺口

1. **`reflex.py` 的其余部分没有测试。** 本轮只测 `quota.py` 的状态机；reflex 那 17 行
   改动由 `verify_quota_exit.sh` 的静态断言（AST 解析 + 拼法检查）守着，不是行为测试。
   给 reflex 写行为测试要能假造 dispatch/registry，是 S12 审计那一半的自然归宿。
2. **20 分钟是工单给的数字，不是测出来的。** 它合理（被观察的窗口有 5 小时，一小时
   问三次最多迟到几分钟），但没有实验支持，也没有自适应退避。
3. **`ping()` 与 `check()` 的状态文件写入仍可互相覆盖。** ping 后重读把窗口缩到最小，
   但两个进程各自整体 `save_state`，真正的修法是按键合并或加锁。5 分钟一跳的监控里
   概率很低，登记而不假装不存在。
