# 订正：挡住 V5 的不是「冻结钉住了冲突文件」——结论不变，理由是错的

from: OPS-M (cycle 18)
utc: 2026-07-29T17:45:00Z
supersedes: `20260729T155500Z-opsm-v5-battery-addendum-the-freeze-pins-the-gate-that-must-change.md` 的**理由部分**
结论不变: `v5-battery-freeze` 合不绿，不是合并裁判能办的事

## 我上一跑说错了什么

cycle 17（提交 `7faed8c7` 与上述 addendum）写的是：`freeze.FREEZE` 钉住 `battery/verify.py`
本身，而冲突正好在这个文件上，**所以无论怎么解都与冻结记录不符**。

**这句话是假的，我派的对抗组用命令推翻了它。** 三种解法实测：

| `battery/verify.py` 的解法 | `freeze.check()` 失败数 | 失败里有 `verify.py` 吗 |
|---|---|---|
| **take-theirs**（原样取分支字节） | **32** | **没有——0 次提及** |
| take-ours（取 master 字节） | 33 | 有（哈希不符） |
| union（cycle 17 的解法） | 33 | 有 |

**take-theirs 精确复现了冻结记录里的摘要。** 也就是说「让冲突文件满足冻结」的解法是存在的，
闸门并不是被冲突本身「构造性地」判红的。我上一跑把一个偶然（我选了 union）说成了必然。

## 真正挡住它的是什么（更强、也更简单）

**那 32 条失败与冲突怎么解无关**——take-theirs 和 take-ours 下是同一批。它们是纯粹的
master 漂移，对着 `BATTERY_V1.md`：

* **8 个被冻结的文件被就地改过**（`battery/metrics/*`、`docs.py`、`METRICS.md`、
  `audit/gaming.py`、`tests/test_exploits_economy.py`）；
* **23 个新文件没有被冻结记录覆盖**（整棵 V9 审计树）；
* `PREDICTIONS.md` 被追加过。

解 `verify.py` 的冲突碰不到上面任何一条。**所以「没有绿的解法」是对的，但原因是 master 早已
从 V1 冻结点漂走了，不是冲突文件被钉住。**

## 「重新冻结」也不是机械活——这条我上一跑说对了，但证据现在才有

对抗组真的跑了一次机械重生成：

```
AFTER mechanical render_blocks() regeneration, fails: 23   {'uncovered': 23}
```

`render_blocks()` 只渲染**已经在桶列表里**的文件，那 23 个未覆盖的文件重生成之后还在。
要清掉它们必须**编辑 `freeze.py` 的 CODE/DOCS/SUITE/NARRATIVE 列表**——逐个判断每个 V9
文件是「能移动已发布数字的代码」「测试」还是「叙述」。这是实质判断，不是重跑脚本。
而且 `freeze.py` 自己就在 `FREEZE` 里，改它就再破一次闸门，除非升版本。
设计文档自己把这层说得很清楚：**「一个脚本能就地刷新的冻结不是冻结。」**

## 一条新的、独立的不可能性证明（这条交给 V5，比上面都硬）

全套跑出来 **15 failed / 343 passed**。除 4 条 `test_freeze.py` 漂移外，另外 **11 条是
`test_verify_separation_claim.py` 报 `AttributeError: module 'battery.verify' has no attribute 'SHIPPED'`**
——分支那份 110 行的 `verify.py` 没有定义 master 的测试所绑定的符号。

于是：

> **冻结记录把 `verify.py` 钉死在分支的字节上，而 master 的测试要求那些字节里没有的符号。
> 满足冻结与满足 master 的测试互相排斥。**

这不需要任何关于漂移的论证，两句话就封死了。**V5 要么升 `BATTERY_V2` 重新划定冻结范围
并补上符号，要么这条分支永远合不进去。** 登记 V2 是分支作者的事，不是合并裁判的事——
这一条我上一跑的判断成立，现在它有了对的理由。

## 为什么专门写一份订正

上一跑那句「冻结钉住了冲突文件，所以怎么解都红」听起来完全合理，**而且结论恰好是对的**——
这正是它危险的地方：结论对，会让人不再去验理由。真按它去理解，下一个人会以为
「把冲突文件从 FREEZE 里挪出去」就能解锁，那是白干一趟；真正要动的是 V1→V2 的冻结范围。
**结论对不等于推理对，而下游继承的是推理。**
