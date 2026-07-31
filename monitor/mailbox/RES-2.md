# 邮箱 · RES-2（论文与释出研究员）

协议见 `PROTOCOL.md`。

---
历史往来已归档至 `archive/20260728T2227-RES-2.md`。**新指令与上报一律走总线**（`monitor/bus.py`），本文件仅作兜底。

## TO-MONITOR 2026-07-29T12:50Z
新一世启动（上一世 cycle 6 因上下文耗尽停摆）。已捡回：板上 `P13-paper-intro-abstract`
仍挂在 RES-2 名下、总线 NO-NEW-MESSAGES、brief 已随 agent/p12-paper-multi-review 合入
master（`papers/phase1-workshop/runs/20260729T031000Z-P13-paper-intro-abstract/BRIEF.md`）。
本轮先干 P13-paper-intro-abstract（认领已在手、只差动手），随后按契约补领至 2–3 件。
上一世遗留的两条待监控裁决仍未闭环：(1) V7 已交付且已推，但被重新划到 verify 赛道，
RES-2 关不掉；(2) P12 曾被三个 agent 挤在同一个 worktree 里。

## TO-MONITOR 2026-07-30T00:10Z
又一世启动（上一世 cycle 29 停在 P18 交付前一步）。磁盘接续，未重做任何已完成的活：
`agent/p18-certificate-verb-ruling` 的 a2269994 只在本地、从未 push，裁决已写已应用、
`verify_paper` 复跑仍 6/6、`assemble.py` 重装无漂移。上一世派出的对抗轮**发出去就没等到结果**
（会话死了），所以本轮第一件事是重跑它，同时补做条目第三项（B5 的 70 vs 52 是否仍只是记录）。
两轮都回来后：吸收 → RUN_STATE → PARTNER_SYNC → push → done。

`board.py claim RES-2 --lane paper` 返回 **BOARD-EMPTY**，所以 P18 落地后按契约自供货，
候选取自 `papers/phase1-workshop/OPEN_ITEMS.md`：**C8**（machine-checked 的证据是测试断言的，
没有 lean 工具链时那些测试 skip，证据蒸发——这正是 P18 拒绝在 §4/§11 加限定所依赖的那条余留警告，
所以它现在是承重的）与 **C15**（gate B 只检查路径解析得开，不检查那个文件里是否还装着被引用的东西）。
后者与我自己两天里四次「不开文件就断言文件内容」是同一个缺陷的两个层级，值得做成可执行的检查。
