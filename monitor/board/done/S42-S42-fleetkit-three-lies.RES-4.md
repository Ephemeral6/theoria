priority: 3
cell: S42
territory: fleetkit
deps: none
lane: infra
author: RES-4

# S42-S42-fleetkit-three-lies · fleetkit 的三处谎：LANE_OWNER 假 docstring、_PREFIX 从未接线、__main__.py 不存在

S40 测量出来的、**在 fleetkit 领地里所以 S40 不能动**的部分。逐条都实测过，证据在 `monitor/runs/20260730T0625Z-S40/FINDINGS.md`。

## 三条，按危害排序

1. **`_PREFIX = ""` 从未被赋值** → `cmd_sweep` 的存活判据恒假 → `live` 恒空 →
   **每条 W-* 认领都被判成孤儿，把还在跑的工人的活抢走**。实测（注入合成 schtasks
   CSV）：monitor 只释放 Ready 的那个，fleetkit 两个都释放。**这是
   `fleetkit/KNOWN_TRAPS.md` 第 1 条一字不差**，潜伏在 ship 出这份警告的包自己身上。
   而 `config.py:78-83` 正为此校验 `task_prefix` 非空，**`board.py` 从不读 config**
   （`from fleetkit import config as _config` 在全文件只出现在 import 那一行）。
2. **`LANE_OWNER` 的 docstring 说「Filled from fleet.json at import」，错了两遍**：
   包里没有任何写入（4 处出现 = 1 赋值 + 3 读），`fleet.json` 全仓不存在，
   而且 `FleetConfig.lanes` 是 `List[str]`，**schema 表达不了 lane→owner 映射**。
   后果：任何带 `lane:` 的条目由构造不可达——不在 `list` 任何一段、领不走、没有出口。
   条目要求：**改真或删掉**。改真的前置成本是动 config schema（`THEORIA_EXAMPLE`
   与 `REQUIRED_CONFIG` 会跟着动），删掉更便宜也更诚实——但删掉要连带处理
   reserved 段那块「可达代码 + 不可达循环体」。
3. **`fleetkit/fleetkit/__main__.py` 不存在**，所以 `README.md:13` 与
   `__init__.py:8` 的第一行命令 `python -m fleetkit init --prefix MyFleet-`
   直接报 `No module named fleetkit.__main__`（实测）。`verify.py` 绕过 CLI
   直接调 `config.write_default()`，**于是闸门在一个坏掉的入口之上是绿的**。

## 顺带要改的一句文档

`README.md:23-32` 那张表写 `board.py | ~360 | ported: atomic claim, territory
exclusivity, lanes, sweep`——**`lanes` 与 `sweep` 两项实测都不工作**。

## 与 S40 的关系（别重做）

S40 已经在 monitor 侧建好 `monitor/tests/test_fleetkit_drift.py`：10 处分叉
逐条进了 `DECLARED` 表，判据是「分叉必须被声明，否则红」。**本条目每修好一处，
就要去删/改对应的 DECLARED 条目**——那边有测试专门盯着「已解决却还声明着」。
另外 `test_the_false_docstring_is_still_there_and_still_false` 会在第 2 条被修好
的那一刻变红，**那是设计好的提醒，不是回归**。

## 服务论文哪个槽位

「这台机器可不可信」：fleetkit 是唯一一个要交到别人手里、在别的仓库里跑的产物，
它带着一个会抢走活工人的活的 sweep，是可复现性论断上最外露的一处。
