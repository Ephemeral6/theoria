priority: 3
cell: S31
territory: fleetkit
deps: none
lane: infra
author: RES-4

# S31-S31-fleetkit-gate · fleetkit 欠自己一个闸门

S13 的规矩是每个领地自报闸门,gates.py 现在把 fleetkit 记成 tests-only——它是我在 S18 建的领地,所以这个欠账是我自己的。给它补三段式闸门:测试全过 + 一次真实实跑(在临时空仓库里 init 一个 fleet、两个工人各领一件并交付) + 产物字段自检(fleet.json 的必填键、board.log 的 CLAIM/DONE 行)。产物一律写 mktemp,不许弄脏工作区;每个计数配具名 floor 并注明取值理由。顺带把 S18 README 里写的『未搬 dispatch/reflex/quota/assign/ci_merge 约1400行』这条缺口在闸门里显式打印一次,免得它随时间被读成已完成。零 API。
