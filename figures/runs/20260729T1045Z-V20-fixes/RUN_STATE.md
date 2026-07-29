# V20 · 图表管线 —— 过程记录

条目 `V20-figures-pipeline-red`（p1，cell V5，territory `figures`，lane `verify`），RES-3。
分支 `agent/v20-figures-pipeline-red`，base `443211dd`。

## 先说最要紧的一件：工单四条里有两条已经过期

工单说管线「今天在 master 上是红的，而且是静态可证的红」。**跑了才知道不是。**
诊断证据在 `figures/runs/20260729T1030Z-V20-diag/`，我另外独立复核了一遍：

| 工单的断言 | 实际 |
|---|---|
| ① `EXPECTED_IDS` 止于 E-07，`build_all.py` 必然非零退出 | **已过期**。`fig06_concept_timeline.py` 已含 E-08/E-09，`build_all.py` 退 0。工单的预测在 `76e75609`(07-28T22:41) 到 `abd8d0cb`(07-29T13:15) 之间约 14.5 小时的窗口内成立 |
| ② `SOURCES.sha256` 五十条里十三条已提交漂移 | **已过期**。今天是 **61 条、0 漂移**。「50 条」对得上两代之前的 `9239eb1c`；拿今天的字节重放那份清单得到 11 条不符，也不是 13 |
| ③ 六张图只有三张被正文引用 | **属实**。fig02/fig03/fig04 的完整 slug 在 `papers/` 下出现 **0 次** |
| ④ 字节可复现 | **绿**。两次独立构建逐字节相同，且已提交的树等于一次全新构建（gate 6） |

**这条本身是发现**：工单是照一份审计写的，而审计与执行之间隔了修复。
所以本件没有去「修」①②——那会把已经对的东西改坏。

但同一次核查查出**工单没提的一处当前真红**：`release/MANIFEST.jsonl` 里
57 条 `figures/` 路径中 **14 条哈希与盘上字节不符**。裁决不含糊：gate 6 证明
盘上的图版就是源该产出的图版，所以**该重生成的是释出清单，不是图**。
`release/` 不是本条目的 territory，已写 `monitor/inbox/20260729T1145Z-RES-3-*.md`
转交，并在那里点名这是 WP10 的活。**本件的三个改动还会再给它添三条待重算的路径。**

## 做了什么

**一、`EXPECTED_IDS` 从源头派生（工单第 1 条的「类」，不是「例」）。**
`abd8d0cb` 是手工把 E-08/E-09 补进那份名单——修的是这一次，不是这个病，E-10 会再犯。
现在 27 个 id 由 `expected_ids(text)` 从**同一份已读入的字节**里推出，走
`sources.read_text`（没有 `open()` 路径，gate 7 仍绿），读不到就 raise，
**空集不是合法答案**。

关键是没有把它退化成「拿日志和自己比」的同义反复。仍然会红的：家族内重号、
序号断档（`E-01..E-07, E-09`）、源序错乱、按家族的**下限**（`FAMILY_FLOORS`，
沿用 `sources.py` 已有的 `Rule.floor` 惯例，这是旧名单「缺一个就红」那一半
在派生形式下唯一活得下来的写法）、以及 E 表与各自独立撰写的
`### E-NN, in full` 小节互相对不上。
**不再会红的**：往家族末尾正常追加一条（`E-10`）——这正是那 14.5 小时的成因，
是有意去掉的；要求「E-10 必须存在」就抬 `FAMILY_FLOORS['E']`。

**二、图-正文对照门不再硬编码三张。**
工单指的那份三张硬表在 `papers/phase1-workshop/figures/check_figure_parity.py`
—— **在 `papers/` 里，不是我的领地**，没动。改为在自己这侧新增
`figures/check_figure_citations.py`：从 `build_all.FIGURES` **导入**图集（不重扫目录），
每张图要么在正文里被引用，要么在 `NOT_CITED_ON_PURPOSE` 里带一行理由写明。
两个方向的陈旧声明都会红（声明了却已被引用；声明了却已不再构建）。
fig02/03/04 先登记为「待正文作者裁决」——**今天诚实，而不是为一件本件无权修的事而红**。
接进 `verify.sh` 成 gate 10，沿用本目录 gate 8/9 的惯例：负控先跑，证明它会拒。

## 我自己复核过的（不是转述 subagent）

```
bash figures/verify.sh                              -> exit 0，十道门全绿
python figures/check_figure_citations.py --self-test -> exit 0，三个负控都开火
python figures/check_figure_citations.py             -> 3 cited / 3 declared / 0 unaccounted
```

第一次跑 `verify.sh` 我把它跑红了（`build pass B did not complete`）——
原因是我同时开了前台与后台两次 `verify.sh`，两边抢同一个 `figures/.verify/` 暂存目录。
**不是缺陷，是我的并发失误**，记在这里免得下一个人把它当成 flaky。

## 一处时间戳更正

本目录原名 `20260729T1600Z-V20-fixes`，manifest 的 `utc` 也写 `16:00:00Z`——
那是本机 +0800 的钟被写进了一个含义为 UTC 的字段，实际是 10:45–11:00Z。已更正。
记下来是因为**同一天同一个会话在心跳里独立犯了同一个错**（自报快约一小时）：
`date -u` 要真的去取，不能靠推。
