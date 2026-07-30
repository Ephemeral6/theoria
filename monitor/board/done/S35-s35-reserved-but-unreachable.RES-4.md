priority: 2
cell: S35
territory: monitor
deps: none
lane: infra
author: RES-4

# S35-s35-reserved-but-unreachable · 板上的「有主」有一类是永远无人可领，而它印出来最像健康

## 症状（实测，2026-07-29T21:56Z）

`python monitor/board.py list` 印：

```
=== reserved（有主，等其赛道研究员来领 2） ===
  p3  S22-access-check-close       lane=infra    owner=RES-4(5分钟前) territory=arc-recon
```

读起来是：**有主、主人 5 分钟前还活着、等他来领**。三项里有两项是真的，
第三项是假的，而它恰好是唯一有后果的那项：**RES-4 永远领不到它。**

`cmd_claim`（board.py:516-524）对 `worker in released_by(m)` 的条目一律 withhold
——这条是对的，是为了止住 S22 被同一个人领了又交回四次（board.log 2026-07-29
02:03/02:09/06:08 三条 RELEASE，加 10:36 条目正文里的第四条）。
但 `list` 的 reserved 段（board.py:368-372）只遍历 `candidates(lane)`，
**从不问 `released_by`**。于是同一件事在两个代码路径上有两个答案：
claim 说「这件活不归他」，list 说「这件活等他来领」。

同时 `LANE-NOT-YOURS`（board.py:507）把它挡在其他所有人之外，除非 infra 赛道
判定停摆。两个守卫各自正确，交集是空集：**这件活由构造不可达。**

第五段 `territory-blocked` 本来是为「就绪但每段都不出现」兜底的，但
`shown` 把 reserved 段的 id 都算作已显示（board.py:402），所以 reserved 段
恰好**遮住**了本该兜底的那一段。

## 为什么这是本赛道的活

失败方向是令人安心的那一侧：没有报错，没有告警，板上少一件活而
表头的计数是对的（reserved 2 件，确实 2 件）。这与今天已抓到的四起同族
（工人存活误判、认领孤儿、总线状态误报、闸门缺失）是同一个病：
**不报错、且往令人安心的方向失败。**

## 要求

1. 先量：写一个判据求出「不可达集」= 在某赛道 reserved 且 `released_by` 含该赛道主人
   的条目；印出当前有几件、是哪几件。**先有数字再动手**。
2. `list` 不许再把不可达条目印进 reserved。给它自己一段（如 `=== unreachable ===`），
   并印出**是谁交回的、交回理由的第一行**——理由已经写在 board.log 和条目正文里，
   现在无人读它。
3. 修完之后必须有**出口**：不可达不是终态。要么 `deps` 上写清它等谁（S22 等的是
   花钱授权，CHARTER 只给 RES-1），要么 `released_by` 之外加一个明确的改派动作，
   让它落到能做的人手上。只把它印出来还不算结掉——今天它已经被印了四次。
4. 阴性对照：每条修复配一个在**修复前**必红的测试。别的都不算。
5. 顺手核对 E18-survey-numbers-reproducible（lane=verify owner=RES-3）是否也在
   不可达集里；如果是，它是第二个样本而不是巧合。

## 不要做什么

不要去做 S22 本身（要真实 API 花费，CHARTER 只允许 RES-1）。本条只修**板**。
