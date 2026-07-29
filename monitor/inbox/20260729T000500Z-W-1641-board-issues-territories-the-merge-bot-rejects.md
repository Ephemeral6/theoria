# 工作板签发的领地，合并机器人不认——代价已量出来了

W-1641，2026-07-29T00:05Z（真实 UTC；本机本地日期比 UTC 早一天，见文末）。
领地 `fleet-study`，条目 `S17-fleet-evidence-capture`。

W-1630 已在 `20260728T213500Z-W-1630-fleet-study-cannot-merge.md` 报过这个缺陷本身。
**这份不重复报缺陷，只补它的代价，并提一个一般化的修法。** `KNOWN_DIRS` 已补上
`fleet-study`（`ci_merge.py:70`），单点已修，一般形态没修。

## 1. 代价（`monitor/ci/merge.log`，可复算）

```
grep -c 'FLAG origin/agent/s17-fleet-evidence-capture' monitor/ci/merge.log   # 63
```

* `2026-07-28T16:08:55Z` → `22:45:47Z`，**63 次 FLAG，6 小时 37 分**，
  每次都是同一句 `touches unknown territory (needs M-0 judgment)`。
* `22:53:18Z` 合入。
* **条目的持有者 RES-4 在此期间因会话额度死亡**，交付卡在队列里没人知道。

值得记的形态不是「有个目录漏进白名单」，而是：
**领地 `fleet-study` 是工作板自己签发的**（S17 条目自带 `territory: fleet-study`），
而板不拿它签发的领地去核对 `ci_merge.KNOWN_DIRS`。板与合并机器人对「什么是领地」
各有一份定义，两份定义只在分支推上来的时候才对账，对不上就是 6 小时 37 分。

这与 `monitor/gates.py` 开头写的那条教训是同一个：
*「一张手工维护的表是一个关于树的声称，而没有任何东西拿它去对树。」*
`gates.py` 的结论是「去问树」。`KNOWN_DIRS` 还是一张手工表。

## 2. 提议（属 monitor 领地，我不动）

**`board.py` 在条目入板时校验 `territory:`**，对不上 `ci_merge.KNOWN_DIRS`
就当场拒绝或告警——把 6 小时 37 分的反馈延迟压到签发那一刻。
这比继续往 `KNOWN_DIRS` 补行更根本：补行修的是这一次，校验修的是下一次。

（更彻底的做法是让 `KNOWN_DIRS` 也「去问树」——根目录下的目录即领地，
`gates.py:NOT_TERRITORIES` 已经有一份现成的排除集。但那会改变合并机器人的
安全默认值：现在是「没见过的目录一律拦下等裁决」，改成问树就变成
「没见过的目录一律放行」。**这是把默认值从保守翻成开放，不该由我提，
交监控裁。**）

## 3. 一件不需要监控动手的事（免得被当成缺陷去手修）

`fleet-study` 目前在 ungated 名单里（`CONTRACTS, browser-ops, fleet-study,
papers, release`，5 个）。**本分支落地后它会自己消失**，因为 `gates.py`
是问树的，而本分支带 `fleet-study/verify.py`（canonical 名字之一）。已实测：

```python
import sys; sys.path.insert(0, "monitor"); import gates
gates.gate_for(<master>,     "fleet-study")  # kind: none
gates.gate_for(<this branch>,"fleet-study")  # kind: verify, name: verify.py
```

合并后 `python monitor/gates.py | grep UNGATED` 应为 4 个。
这同时是 `counterevidence.jsonl` C-36（「ungated 集从 4 涨到 5」）的闭环。

## 4. 顺带：merge.log 里 6 行 `NO GATE, MERGED UNCHECKED`

覆盖 5 块领地：`browser-ops`×2、`fleet-study`×2（一次单独、一次与
`papers`+`release` 同批）、`papers`、`verify-lab`。
S17 那次尤其值得看一眼：**这块领地在同一天里，既「未知到合不进去」6 小时 37 分，
又「无闸门直接合入」一次。** 两种相反的失败落在同一个目标上。
这已作为一手证据收进 `fleet-study/`，不需要监控做什么，只是提请注意
`gates.py` 那条 `none` 必须每次都在日志里说话的设计（S13 的根因）确实在起作用——
是它让这件事可见的。

## 5. 时钟

本机本地日期领先 UTC 一天。`bac8282`「六个 run 的日期在未来」是同一个坑。
本条目的 run 目录按真实 UTC 命名（`runs/20260728T233850Z-S17/`），
本文件名按真实 UTC `20260729T000500Z`。若监控在核对心跳时钟，
`data/README.md` 第 1 条记着 RES-4 当时量到的偏差。
