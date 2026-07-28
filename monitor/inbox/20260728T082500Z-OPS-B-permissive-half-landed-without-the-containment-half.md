# 提案 · 宽松的那一半落地了，封存的那一半没有 —— 兼 D-1 的实测升级

from: OPS-B（浏览器专员）· utc: 2026-07-28T08:25Z
re: 本轨道上一份提案 `20260728T061513Z-OPS-B-terms-vs-arcrecon.md` 的落地核查
出处：`arc-recon/ACCESS_CHECK.md` 第 8 项（commit `0a71c1c`，"the last two access-check items close"）

---

## 0. 先报好消息，再报那半件事

上一份提案的 §B 与 §D-2 的**经济/许可**半边，arc-recon 已经采纳并结案：

* 第 8 项状态改为 **"closed, and less restrictive than we first read it"**，
  "Settled by" 一栏直接引了 `browser-ops/TERMS.md`；
* 释出清单被切成两栏（我们的分数/指标/哈希/方法 = Testing Policy 明文允许，附三句披露；
  ARC 的帧/轨迹/游戏源码/题面 = 需书面许可），**正是提案 §B 建议的形状**；
* 结论 1 被改写为 **"caching ARC data locally for our own analysis is permitted,
  and no permission needs to be sought for it."**
* 他们还额外写了一段「双方都是我们自己人的分歧记录」，把两次读法的差别留了痕。
  这一段做得比我提议的更好，照录不议。

**但采纳的是一半。另一半——封存那一半——没有跟着落地，而两半是同一个发现的两个方向。**

---

## A. 风险：一句真话被放在一个会被误读的位置

`ACCESS_CHECK` 第 8 项结论 1 现在这样写（原文）：

> "The Kaggle starter's own troubleshooting text says games 'are cached in
> `environment_files/` and you're fully offline', and the local-vs-online page
> advertises unlimited local instances with no key. … **One line: caching ARC data
> locally for our own analysis is permitted, and no permission needs to be sought
> for it.**"

**这句话在许可维度上完全正确，我不主张改它。** 问题是它**独自出现**：
同一段里没有任何一句说明**那个缓存里装的是什么**。全仓 grep，
`environment_files` 只在这一处出现，且是作为**许可论据**出现的。

`browser-ops/TERMS.md` §4.2 记的另一半是：

* `docs.arcprize.org/arc-prize-2026` 原文：首跑会 "download **the game source**"；
  `make list-games` 的说明是 "Print every game id available"；
* `docs.arcprize.org/swarms` 原文：`--game` **缺省即 "plays all available games"**；
  `make play-local` 的说明是 "Runs your agent against **every game in the dataset**"。

即：**照着那句"permitted，无需申请许可"去做的第一件事，默认会把全部 25 局的游戏源码
拉到磁盘上，并且默认会把它们全部跑一遍。** 按 INC-BA-001 的制度性后果那一段的判据
（"读封存局的这些文件比玩那一局更糟——它直接给出机制的成品答案"），
`environment_files/` 里的**源码**比上游 Schema 数据集的**轨迹**还要靠前一档。

**这不是说 arc-recon 写错了。** 许可结论是对的，我提供的原始材料本身也是分两半的，
而落地时只有一半有归宿——因为第 8 项的题目是「licensing」，封存那半没有它的格子。
**这正是缺口所在：一个发现被按文件的章节切开，只有一半找得到家。**

**建议（一句话就够，不需要改结论）**：在结论 1 那句后面补一句限定，形如

> 缓存是被允许的；被缓存的东西不是。首跑会取回全部 25 局的**游戏源码**，
> 官方 runner 与 `make play-local` 默认对全部 25 局运行。启用本地模式前必须先立
> 正向白名单守卫（形状照 `baseline-arms/SCHEMA_PATH_A.md` §3），并 gitignore 该目录。

---

## B. D-1 从"政策原文推出"升级为"实测观察"

上一份提案的 §D-1（任意一局的逐帧 replay 无需 key、无需登录即可公开观看）
**至今没有落进任何红线清单**（全仓 grep：`arcprize.org/scorecards/*` 零命中，
除了 `ACCESS_CHECK` §3 里那条讲 15 分钟自动关闭的文档引用）。

那条当时只有政策原文作依据。本轮补了一次**零内容探针**：

* **做法**：在**应用内浏览器**（干净会话，无登录态、无 API key、无 cookie）打开
  `https://arcprize.org/scorecards/00000000-0000-0000-0000-000000000000`
  ——一个必然不存在的全零 UUID，所以不会渲染任何一局的任何内容。
* **观察**：页面**正常渲染**，正文为 `‹ SCORECARDS` + **`404 fetching scorecard`**；
  **没有跳转到 `/login`**，也没有任何鉴权拦截。
* **判读**：该路由**不是鉴权门后的**。它在无凭据的浏览器里直连后端查询记分卡；
  换成一个**存在的** id，它就会渲染那张卡与它的 replay。

**这把 D-1 从"官方文档这么说"变成了"我们自己看到路由是开的"，且封存内容接触为 0。**

**为什么这条比它看起来重要**：`contamination.py` 的账本审计是对
「every call ever made」做的——它审的是**我们的 API 调用**。
而这条路径**不产生任何 API 调用、不用 key、不进任何账本**。
一个会话在浏览器里点开一局封存游戏的 replay，**审计一片绿，污染已经发生**。
现有守卫在结构上看不见它。

**建议**：把下面两行写进封存红线的明文清单（`CLAUDE.md` 的切分段落或
`piles.json` 的 rules，归 `arc-recon` 与人工决定，本轨道两处都只读）：

1. 不得访问 `arcprize.org/scorecards/*` 与任何 replay 页面，
   除非该记分卡是我们自己产出且只含开发堆；
2. 官方文档与政策页正文中出现的 replay 链接一律不点
   （`arcprize.org/policy` 正文挂着 `re86` 的回放，
   `docs.arcprize.org/` 首页与 quickstart 挂着 `ls20` 的）。

---

## C. 两条小的，仍未动（上一份提案的 §C 与 §E，重申一次即可）

* **§C**：`ACCESS_CHECK` §6 关于 per-key 配额的措辞未变，仍是
  "Absence from the documentation is not absence from the implementation,
  so this stays an assumption rather than a finding."
  面板实查提供的是**产品面**证据（账户界面里根本没有配额/用量字段，
  key 的全部属性只有 KEY/GAMES/CREATED，权限维度只有游戏集合）。
  建议改为两层口径：**文档没写 + 产品的账户界面里也不存在这个概念**；
  仍不等于实现里没有，但比单层强。
* **§E**：`arc-recon/data/recon_findings.json` 未动，仍写着
  `refused_of_dev_pile: [ar25, sk48, tn36]`（已被 INC-001b 推翻）与
  `not_yet_checked` 含 "rate limits and action quota"（第 6 项已答）。
  **第 2、7、8 项刚刚改状态，正是顺手加 `superseded_by` 指针的时候。**
  它是机器可读的那一份，下游按 JSON 读会拿到已被推翻的图景。

---

## D. 请裁决

| # | 事项 | 我的建议 | 不做的后果 |
|---|---|---|---|
| A | 第 8 项结论 1 补一句缓存内容的限定 | **做**，一句话 | 有人照"permitted 且无需许可"启用本地模式，25 局源码落盘，封存堆一次报销 |
| B | replay 页写进封存红线明文清单 | **做** | 存在一条不经过账本、审计看不见的污染路径 |
| C | §6 per-key 配额措辞改两层口径 | 可做可不做 | 无损失，只是证据没用上 |
| E | `recon_findings.json` 加 `superseded_by` | 建议做 | 机器可读的那份持续散播已推翻的结论 |

A 与 B 都属**不可逆损害**那一类（封存局烧了就没了），C 与 E 只是账目质量。
**本轨道对 `arc-recon/`、`CLAUDE.md`、`piles.json` 一律只读，以上不代劳。**

---

## 附：本轮取证边界

* 新增页面访问 **1** 次（全零 UUID 的记分卡路由），**零游戏内容加载**，
  无 API 调用、无计费动作、封存堆接触 **0**、无登录态。
* 登记在 `browser-ops/runs/2026-07-28-visits.md` 第 21 行。
