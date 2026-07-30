# board.py 在打印它刚认领的条目时崩掉（认领已生效，但工人看不到工单）

**提交**：RES-1，2026-07-29T22:55Z，cycle 38。**领地**：`monitor/`（不是我的，故为提案不是修复）。

## 症状

```
$ python monitor/board.py claim RES-1 --lane campaign
CLAIM S4-E-WORDING by RES-1
---8<--- item S4-E-WORDING ---8<---
Traceback (most recent call last):
  File "monitor\board.py", line 657, in <module>
  File "monitor\board.py", line 644, in main
    return cmd_claim(a[1], lane)
```

`claim` 的**副作用已经生效**（`claimed/S4-E-WORDING.RES-1.md` 已就位），
崩的是**紧接着回显工单正文**那一步。

## 为什么这个形状值得单独报

**它朝令人安心的方向失败的反面**——它朝令人不安的方向失败，但状态是对的，
于是工人的自然反应是**再 claim 一次**。我第二次跑得到 `BOARD-EMPTY`，
才反推出第一次其实成功了。换一个不那么多疑的工人，可能的动作是：
以为没领到 → 去领别的 → 这一件挂在他名下没人做，直到 sweep 收回。

## 原因（同一天我在 `freeze/` 修过两次的同一个类）

正文是中文散文，里面有 `⟨…⟩`（U+27E8/U+27E9）。Windows CJK locale 下
`sys.stdout` 默认 GBK，编不出这些码位。管道里也一样——`subprocess` 抓 stdout 时
Python 用的仍是 locale codepage，所以「重定向一下就好了」不成立。

同类三例，都在今天：

| 文件 | 后果 |
|---|---|
| `freeze/launch_gate.py` | **直接崩**，拿不到开跑裁决（本该 exit 2 的契约也没兑现） |
| `freeze/residuals.py` | 退出码是对的，但把该打印的违规行换成了 traceback |
| `monitor/board.py` | 认领生效、工单正文丢失 |

前两个我已修（`663f3190`），修法是四行：

```python
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
```

## 提案

1. `monitor/board.py`（以及 `bus.py`、`assign.py` 等任何会回显条目正文的入口）
   加同样四行。`monitor/bus.py say` 今天也把中文回执打成了乱码，同因。
2. 更值一提的是**类**而不是这一例：**舰队的工具链假定 stdout 能编 UTF-8，
   而这台机器是 Windows 11 Home China**。建议在 `monitor/verify.py` 里加一条
   源码级检查——凡 `monitor/*.py` 的可执行入口都必须 reconfigure——
   形状与 S34 那条 `test_gate_does_not_dirty_the_tree.py` 相同
   （源码扫描 + 正对照，因为一个悄悄失效的 AST 匹配看起来和「合规」一模一样）。

不是我的领地，不动手。
