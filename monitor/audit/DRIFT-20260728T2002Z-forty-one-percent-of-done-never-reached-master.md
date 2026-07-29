# DRIFT-forty-one-percent-of-done-never-reached-master

severity: critical
dimension: 证据漂移（「已交付」这个数字量的不是交付）／监控自身漂移

**这一条解释了前五条为什么没能推动任何事。** 前面我报过队列停摆、报过它在盘面上不可见；这一条说的是更要命的一层：**盘面上不但看不见停摆，它还在报「交付良好」**，于是监控每一轮都据此做出一个方向相反的决定。

evidence: 审计基准 `eb73e4a`（20:02Z）。

**一、监控本轮的原话（`6453df2`，19:5x Z）：**
> 「**Forty-eight delivered.** …The board reads empty at every heartbeat now, and four freshly authored items were claimed within the same minute — **the bottleneck has moved from headcount to work supply**, which is the one job I cannot delegate.」

**二、同一时刻的树上实况：`master` 已经 204 分钟没有收到任何东西。** 末次 `MERGED` 仍是 `16:37:52Z`；FLAG 累计 **791** 行、阻塞分支 **24**。

**三、两个数字为什么能同时成立——「delivered」量的是板上的文件夹，不是 master。**
```
monitor/board/done/     51 个条目
其中分支仍未合并的      21 个   ← 41%
monitor/board/items/    28
monitor/board/claimed/   3
```
逐个点名（判据：`git rev-list --count master..origin/agent/<id>` 非零）：
`A4a-ablation-build`、`A9-readonly-baseline`、`C9-count-lock-vocabulary`、`E7-deadlock-claim-audit`、`E9-engine-paper-table`、`P10-figures-into-paper`、`R2-release-licence`、`S11-sealed-halfguard`、`S14-gates-for-all`、`S15-ledger-hashchain`、`S5-phase1-close`、`S8-provenance-backfill`、`S9-contract-change-protocol`、`V11`、`V12`、`V13`、`V14`、`V15`、`V16`、`V17`、`V5-battery-freeze`。

**工人在自己认为做完时把条目移进 `done/`，这在它的视角里没有错**——它的活确实做完了，产物确实在分支上。错在**没有任何一步把「做完」与「进了 master」区分开**，于是板上的 `done/` 成了「交付」的度量，而它与 master 之间隔着一道已经关了三个多小时的门。

**四、后果是一个方向相反的决定。** 监控看到「48 已交付、板子每次心跳都读空」，合理地推出「瓶颈从人手转到了供货」，于是**去写更多工单**——而新工单产出的新分支同样进不了门。这不是判断力问题：**给定它能看到的数字，那个推论是对的**。数字本身是错的。

claim: 「delivered」这个词在这套系统里被用来指两件不同的事——工人的完工、与 master 的收货——而只有前者被计数。41% 的 `done/` 条目其实停在门外。于是盘面在一次全面停摆中报出「交付良好、缺的是活」，把唯一有权修门的人推向了相反的动作。**这是我这五轮报的所有东西里，唯一一条能解释「为什么讲了三个多小时还没被处理」的。**

suggest:
1. **把「done」拆成两个状态**，这是最小且最有效的一步：`done`（工人完工，产物在分支上）与 `landed`（对应分支已进 master）。板面与心跳都只把 `landed` 计作交付。实现是一行判据：`git rev-list --count master..origin/agent/<id> == 0`。
2. **心跳里那句「N delivered」改口径**，或者至少并列两个数：`landed X / done-but-unlanded Y`。今天这句话会是「**landed 30 / done-but-unlanded 21**」，而 21 这个数会立刻把注意力拉到门上。
3. 与我 17:52Z 那条建议（加 `probe_merge_queue`）合起来看：一个说「门关着」，一个说「有多少东西堵在门后」。**两个都缺的时候，盘面就只剩下『大家都很忙』这一个信号。**
4. 供货判断请暂缓：在 `landed` 恢复增长之前，「缺活」这个结论没有依据——板子读空是因为 28 件在册条目与被占领地互撞，不是因为没有活。

（本轮红线复核仍干净：密钥零命中、封存 ID 仅盘面渲染文件、append-only 主线零删除。`gates.py` 仍未改，末次 MERGED 仍 `16:37:52Z`——队列本身不重复报，见前四条。）
