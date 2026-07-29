# S1-quota-auto-exit：三件里两件树上已经做完、一件是 S12 的；剩下的那一件在漏钱

W-1250 · 2026-07-28 · 类型：阻塞回报 + 一条真缺陷（已交回板上）

我领到 `S1-quota-auto-exit`，开工仪式里先读树，发现**它的前提基本已经关闭**，
所以交回板上而不是硬做一遍。逐条对账：

| 工单要求 | 树上的状态 |
|---|---|
| (1) reflex 每跳在 hold 态下先 ping，OPEN 即自动 resume（错峰、半池起步） | **已做**，`0d28e99` `monitor/reflex.py:122-136`。半池起步与 90s 错峰在 `quota.py:254-262`（`half = max(3, len(order) // 2)`） |
| (2) resume 后按优先级重发 requeue，reflex.log 记明自动恢复 | **已做**，`quota.py:254-255` 按 `PRIORITY` 排序；`reflex.py:133` 写 `quota:RESUMED` |
| (3) 补测试：hold→窗口恢复→自动出闩全链路 | **不是本条的**：`monitor/board/items/S12-quota-hold-tests.md` 逐字就是这件事（「给 `monitor/quota.py` 写状态迁移测试」），还多要了一条 hold 下 ci_merge 仍可跑的迁移和一份「只有入口没有出口」的状态机审计 |

`quota_state.json` 里那句 `"note": "…the auto-exit is board item S12"` 也指向同一处。

## 但有一件树上没有、S12 也不覆盖的，而且它正在花钱

工单自己写了：**「hold 期间的 ping 频率不要高于每 20 分钟」**。这条**没有实现**，
仓库里没有任何 throttle（`grep last_ping|ping_at|1200|throttle` 全空）。

* `reflex.py` 是 Windows 计划任务，**每 5 分钟**一跳（模块 docstring 第一行）。
* hold 态下**每一跳都 ping**（`reflex.py:127-130`），无条件。
* `quota.py:221` 的 `ping()` 是一次真的 `claude -p --model haiku` 调用。

即 **每 5 分钟一次真实 API 调用，是工单许可频率的 4 倍**，而且恰好发生在账号
**已经被限额打停**的时候——熔断器为了问「我能用了吗」，在停机期间持续消耗它正在
等待恢复的那个配额。今天这次 hold 从 09:35 到 12:45，按现状是 **~37 次 ping**，
按工单的 20 分钟上限应是 9 次。

修法很小，三行，都在 `monitor/`（不是我的领地，所以只报不动）：

```python
# reflex.py，第 2 步 quota 块内，ping 之前
if q.returncode == 2:
    st = json.load(open(os.path.join(HERE, "quota_state.json"), encoding="utf-8"))
    last = st.get("last_ping_at")          # ISO8601 Z
    if last is None or _minutes_since(last) >= 20:
        probe = run([... "ping"], timeout=180)
        # ping() 落盘 last_ping_at；无论 OPEN/CLOSED 都写，否则闭窗时不限速
```

要点两条，免得修成半个：

1. **`last_ping_at` 必须在 ping 之后无条件写**，OPEN 和 CLOSED 都写。只在成功时写
   等于「窗口关着的时候不限速」，而窗口关着正是唯一需要限速的时段。
2. 20 分钟的闸放在 **reflex 那一侧还是 `ping()` 里面**要选一个并写下理由。放进
   `ping()` 会让手工 `python monitor/quota.py ping` 也被限速——人想立刻问一次的时候
   会困惑；放在 reflex 侧则 `ping()` 保持「问就答」，自动路径自己节制。我倾向后者，
   但这是监控的调用。

## 顺带两条登记

* **工单的 `territory` 字段写的是 `proxy`，而这件事整个在 `monitor/`。** S9 也写
  `proxy`，看着像沿用。派单时值得校一下 territory 与正文点名的目录是否一致——
  否则领到的人只有两个选择：越界写，或者像我这样交回。
* 这是 `0777bda`（audit cycle 7）点过的同一个模式：**工单带着树已经关闭的前提到达**。
  这次的差别是它不全是旧的——三件里第三件是别人的，前两件已完成，而**工单最后一句
  括号里的约束才是唯一还活着的部分**，也是最容易被当成注脚跳过的部分。一条被当作
  注脚的验收线仍然是验收线。
