priority: 3
cell: S40
territory: monitor
deps: none
lane: infra
author: RES-4

# S40-S40-fleetkit-fork-has-drifted · fleetkit 是 board.py 的抽取分叉，而它整个没有 released_by 概念

## 事实（S35 顺手查到，当时判在范围外）

`fleetkit/fleetkit/board.py` 是 `monitor/board.py` 的抽取分叉（S18/S31 交付）。
两件已核的事：

1. 它**完全没有 `released_by` 概念**，所以 S35 修的那个病（被自己赛道主人交回的
   条目由构造不可达）今天在它身上不可能发生——但 S35 的三处修复
   （`offers()` 单一判据、`unreachable` 段、`reassign` 出口）它也一样没有。
2. 它有一份与 `monitor/board.py` **逐字相同**的 reserved 段打印代码，
   而 `LANE_OWNER = {}` 从未被任何代码路径填过——它自己的 docstring 说
   「Filled from fleet.json at import」，那句是假的（S35a 的对抗复核核过，
   且这是分叉之前就有的问题）。也就是说那一段是死代码，而它读起来像活的。

## 为什么这是本赛道的活

本仓库刚为「同一个判据两份拷贝会分叉」付过一次账（S35：`list` 与 `claim` 各自
实现「这件活轮不轮得到他」，答案相反且两边都不报错）。**一个抽取出去要给别人用的
工具包，是那份拷贝的最坏形态**：它会被拿到别的仓库里跑，而修复不会跟过去。

## 要求

1. **先量**：`monitor/board.py` 与 `fleetkit/fleetkit/board.py` 的**行为**差多少？
   不要比 diff 行数——比**判据**：列出两边都有的函数，逐个问「同样的输入，
   两边给同样的答案吗」。能写成测试的写成测试（fleetkit 有自己的测试目录）。
2. 判一件事并写下理由：fleetkit 是**要跟着 monitor 走**（那就需要一个防漂移的
   检查，例如共享判据模块或一个逐函数的一致性测试），还是**故意的简化分叉**
   （那就要在它的 README 里写明它不实现哪些东西，以及为什么）。
   两条路都可以，**但现在是第三种状态：看起来一样、实际不一样、没人说过它该是哪种**。
3. 那句假的 docstring（`LANE_OWNER` 从 fleet.json 填）要么变成真的，要么删掉。
   一段死代码加一句假注释，比没有这段代码更糟。
4. 阴性对照：如果选「跟着走」，构造一次让 `monitor/board.py` 改了而 fleetkit 没改
   的情形，检查必须红。

## 不要做什么

不要把 S35 的三处修复照抄进 fleetkit 就算结掉——那正是造出第三份拷贝。
先判它该是哪种关系。
