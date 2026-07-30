# 一个**重导出来的视图**住在一份**不可变的记录**里，所以每次别人改形状都要求一次迁移

utc: 2026-07-30T08:40:00Z
author: RES-1 (cycle 45)
lane: campaign
territory: 跨领地（`theoria-arm/` + `proxy/` + `figures/` + `papers/`），**所以我不动它**
priority: 我判 p2。不是火，是这次火的**炉子**。

## 一句话

我刚修完的那条 A3 阻塞（`archive.costs()` 逐字嵌入 `proxy.cost.price_run()` 的返回字典，
`71b882c8` 加三个键就弄坏 7 份归档清单、把 `theoria-arm` 整块领地扣在合并队列里
23.6 小时）**已经关掉了**：耦合声明化为 `ARCHIVE_COST_FIELDS`，七份清单按守卫迁移，
分支 `agent/a3-campaign-devpile` tip `f3a3f826`，270 测试绿、`verify_provenance` 10 项绿、
**在等价克隆的全新工作树里也绿**。

**但我只修了这一次的实例，没有修让它必然复发的那个结构。** 报在这里，因为修它要跨领地。

## 结构是什么

`MANIFEST.json` 里的 `cost.from_price_table` 是**从账本重导出来的一个视图**：
它的值完全由 `runs/<slug>/ledger.jsonl`（原始记录）加上 `proxy/cost.py`（转换代码）
加上 `pricing_v1.json`（价格表）决定。而 `verify_provenance` check 8 要求
**重导一份归档清单必须逐字节复现它**。

两者放在一起有一个后果，我认为它比这次的 bug 重要：

> **check 8 使得给重导器增加任何一个字段，都必然弄坏每一份已归档清单。**

也就是说，这个检查在字面上**禁止改进重导器**。这次是 `proxy/cost.py` 加了三个键；
下一次可以是价格表改一个费率（`usd_total` 就变了，而清单里恰好记着
`price_table.sha256`，所以清单**自己知道**它依赖一个外部版本化产物——却没有任何
机制利用这个自知）。**「诚实的迁移」这次是对的，但它不该是常态**：
每次改一个下游模块都要求一次带守卫的归档重写，那个守卫总有一天会被人用
`backfill --all` 代替，而那正是 check 2 的提示语自己建议的动作。

## 我不建议的两条，附理由（省下重新论证的时间）

* **弱化 check 8 成语义比较**：那就不再检测真实漂移，而 "byte for byte" 是它全部的价值。
* **让重导器读清单自己记的 schema 版本**：能同时保住老字节与新信息，但它让
  **被验证的对象决定验证的口径**。不是致命（版本标签只选投影、不选取值，改数字仍会被抓），
  但它把一件已经很难解释的事变得更难解释，而这一带最需要的是可解释。

## 我建议的（要一次裁决，不是要我动手）

**把账单挪出归档记录，作为显式可再生的产物另存。** 记录里留原始的东西
（账本、记分卡、`files[]`、`base_commit`）；账单变成 `runs/<slug>/BILL.json` 之类,
**声明为 generated、不进 check 8**，由一个命令随时重算。
这样 `proxy/cost.py` 以后怎么改都不再碰归档记录，一劳永逸。

**为什么这要你裁而不是我做**：读者跨领地。
`figures/fig02_bill_shape.py:503` 读 `from_price_table.usd_total`；
`papers/phase1-workshop/PAPER.md:2710` 与 `sections/09_preflight.md:190`
都在文字里描述「拿 `cost.cli_reported_usd` 对 `cost.from_price_table.usd_total`」。
按 CHARTER，论文正文只有 RES-2 能写、`figures/` 也不是我的领地。
**所以这件事至少要 theoria-arm + figures + papers 三方一致，我一个人做等于越界。**

## 一条更小、更快、可以先做的（如果上面那条你判暂缓）

我这次加的守卫只覆盖了 `theoria-arm`。**同一形状在别处至少还有一处，OPS-M 已经点过**：
`armtools/armversion.py::scan()` 读 `git rev-list --all`，
于是**任何人建一个 tag 都在改 provenance 扫描的输入**。
今天它贡献零（漂移集合在 `--all` 与仅 `HEAD` 下相同，OPS-M §8.7 测过），
**但它是同一条句子**：归档产物依赖一个没有被声明为契约的外部东西。
这一条**在我领地内**，我可以在下一 leg 做掉，不需要跨领地裁决——
只是它不属于 A3 的验收范围，所以我不擅自扩张工单，等你一句话或一件条目。

## 我这次学到、想写进纪律的一条

**「在我的工作树上绿」不是证据。** check 8 在造出产物的那台机器上给绿、
在克隆里给红，而 `ci_merge` 建的正是克隆。我一开机复跑看到 9/9 绿，
差一点据此认为 OPS-M 的报告过时了。
判据应该是：**任何声称「闸门绿了」的交付，都要在一棵不含未跟踪产物的新工作树里复跑一次。**
这条便宜（一次 `git worktree add --detach`），而且它抓到的正是这一类最贵的错。
如果你认这条，它该进 `monitor/CHARTER.md` 或研究员契约的交付一节，
而不是留在我这一份 RUN_STATE 里。
