priority: 3
cell: S18
territory: fleetkit
deps: S17-fleet-evidence-capture
lane: infra

# S18-fleetkit-extract · 把舰队内核抽成可复用工具包

1723 行的内核（board/bus/dispatch/reflex/quota/assign/ci_merge）是仓库无关的，混在里面的 Theoria 专有物只有三处：spec.py 的 PAPER_PLAN 与 GRID、agents.py 的 PLAIN_ITEM 人话映射、CHARTER 的赛道定义。

做成 `fleetkit/`：内核原样搬过去，专有物抽成一个 `fleet.config.py`（项目名、
赛道表、领地表、人话映射、完成度模型的钩子）。验收线只有一条、但很硬：**在一个全新的空仓库里初始化 fleetkit，起 2 个工人，让它们从板上领两件玩具任务并交付**——跑通才算数，不跑通就是没做完。

顺带清理今天暴露的坑（都写进 README 的『已知陷阱』）：Windows 下 schtasks 输出 GBK、子进程文本别按 UTF-8 解、闸门产物要写 mktemp、快照对比在并发下必然误报、schtasks /TR 有 261 字符上限、claude 的 .cmd 外壳会吃掉多行 UTF-8 argv（提示词必须走 stdin）。

不追求通用到任何场景——**先能被第二个项目用起来**，再谈第三个。
