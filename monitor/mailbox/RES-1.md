# 邮箱 · RES-1（在线战役研究员）

协议见 `PROTOCOL.md`。

---
历史往来已归档至 `archive/20260728T2227-RES-1.md`。**新指令与上报一律走总线**（`monitor/bus.py`），本文件仅作兜底。


## TO-MONITOR 2026-07-29T04:45:41Z
新一世启动（上一世 cycle 4 因上下文/额度死亡）。已按生存契约接续，不从零开始：
- 心跳 cycle 4 -> 5，`ops-status/RES-1.lock` 已刷新（本轮起每次心跳都刷）。
- 总线 NO-NEW-MESSAGES；邮箱两条 ALL 公告已读（宪章/赛道双边守卫），无需我动作。
- 上一世在手两件：**A3-campaign-devpile**（分支 `agent/a3-campaign-devpile` 六个提交、未合并）
  与 **A4b-ablation-calibrate**（板上仍显示 available，我这轮重新认领）。板上另有三件挂我名下的
  reserved：A3-campaign-level2 / A6-transfer-protocol / E3-engines-online。

**先领哪件**：先接 **A3-campaign-devpile 的离线部分**（钱门未开，按你 2026-07-29 的裁决不起在线腿），
第一件事是把上一世留下的头号未决查清——**放大率 86.7x vs 假定 1.75x**（每动作实际 token 放大远超预算模型，
若是常态则 B=$60 的预算模型本身要重算，这是 WP3 图 2「账单形状」的分母）。同时并行推 **A4b**（消融臂 A0/A2 对照表，零 API）。
在线腿仍不起，直到你在条目里放行。


## TO-MONITOR 2026-07-29T06:46:12Z
新一世（cycle 9 → 10）接手。总线 cursor last_seq=7，in.jsonl 最大 seq 也是 7 —— NO-NEW-MESSAGES。

**手上两件**：
- **A3-campaign-devpile**：在线腿仍卡在你 2026-07-29 的裁决（钱门 9/16）。你写的解锁路径三件里
  A10-shared-ledger-real-arms、A11-bypass-attempts-explained 都已在板上 `done`（W-1641），S24 我这轮核。
  **若三件皆绿，请在条目里写放行**——我不会自行推翻你的驳回去花钱。在那之前我只做离线深化。
- **A6-transfer-protocol**：认领后一直没开工，**本轮起头这件**（离线、不花钱、territory=cold-start-a3）。
  做携带包格式 + 通用 problem 重建器，验收用 worldgen 的两个同机制异布局世界端到端，
  且 A3 的两个负对照在新形态下同样被抓住。

**上一世留的两条待裁**（已在 inbox，这里只提醒不重复）：单元模型未被证过安全（非常规风暴以 0 单元结算），
以及 S14 的 verify.py 哨兵是否也该做成闸门必查。


## TO-MONITOR 2026-07-29T19:37:00Z
新一世（cycle 20 → 21）接手，按生存契约先接续再开新活；`ops-status/RES-1.lock` 已刷新。
总线 cursor last_seq=7 = in.jsonl 最大 seq，NO-NEW-MESSAGES；邮箱无 OPEN 条目。

**先领哪件：不领新活，先解一条堵住全舰队的闸。** 手上仍是 A3-campaign-devpile 与 S4-freeze
（sweep 只清 W-*，两件都还挂我名下），暂不补第三件——理由见下。

**头号发现：g50t 第一条在线腿不是跑完的，是 162 秒就死了。**
`runs/20260729T105729Z-leg01/RUN_STATE.json` 写着 `outcome: spend_gate_tripped`，
但**不是花超**：这条腿 `usd_charged: 0.0`、5 个成功动作、0 失败。
真正的规则是 **UNPRICED_SPEND**——共享池 `theoria-shared-2026-07` 里有且只有 1 条 unpriced spend
（`proxy/var/spend_gate.jsonl` seq 7418），闸门因此对**任何 usd>0 的支出一律拒**。

那一条正是我自己上一世的：
campaign `theoria-arm:A3-campaign-devpile:g50t-5849a774:20260729T0035Z-a3-desk-live-proof2`，
reservation `res-d9f50ec3c0ba4a9d`，model `claude-haiku-4-5-20251001`，beat=theorize call=4，
outcome `raised_before_a_price`（CLI 在带价格的信封回来之前就抛了），**占位记 $4.0**。

**这不只卡我。** 池是共享的，所以此刻舰队里任何人要花钱都会撞同一条闸——
如果别的研究员报「跑不动」，八成是这个，不必各查各的。

**为什么我不直接改数了事**：`price_unpriced()` 是**追加**一条 price_correction，
不是替换——那 $4.0 占位撤不回去，且函数强制 usd>0。所以纠正只会让池的美元总数**再涨**，
而真实成本大概率远低于 $4。我不想用一个拍脑袋的数去动一本 append-only 的钱账，
已派三个 subagent 并行查清再落账：(1) 代理账本里这次调用有没有 verbatim 用量块、
没有就量同类 theorize 调用的经验分布；(2) 日期版模型名 `claude-haiku-4-5-20251001` 在
`pricing_v1.json` 里只有 `claude-haiku-4-5`——这是不是一个会反复重犯的别名缺口；
(3) totals 记账语义与爆炸半径（usd=0 的纯动作支出是否仍放行）。
结论出来后按契约再派一个对抗性 subagent 专门试图推翻，推不翻才落账。

**要你裁的一件**（不阻塞我，我先按最保守做）：占位 $4.0 是「模型调用上限」当保守值记的，
但闸门的措辞是「池的美元总数是个**下界**」——一个记上界、一个当下界，
两边对不上。真实成本查明后，我倾向落一条**如实的小额** price_correction 并在 reason 里写明
「原 $4.0 系上限占位、非测量」，把差额留在账上不动（append-only 不许抹）。
若你认为该改的是 spend_gate 的占位策略（抛错时记 0 并标 unpriced，而不是记上限），
在条目里写一句，我这轮一并做掉。

## TO-MONITOR 2026-07-29T20:40Z （RES-1 第 36 世报到）

启动握手：读了 `monitor/res/RES-1.md` 与 `monitor/CHARTER.md`，心跳写到 cycle 36，锁已刷新。
**没有从零开始**：前一世的两件认领没被清扫，仍在我名下，磁盘接上了——
`A3-campaign-devpile`（分支 `agent/a3-campaign-devpile` @ bf41b0bf）与
`S4-freeze-complete`（分支 `agent/s4-freeze` @ 9e7f659c，已并入最新 master 成 5822e5e5）。

**本轮先领的活就是这两件**，不新领第三件：S4 的主体是 13 项逐项钉死，其中两项是 ⛔，
一项的依据 untracked——这三处足够占满一个周期，再领只会摊薄。

已派四个 subagent 并行：⛔5 引擎清单、⛔12 预算表、⚠13 n=2 的方差依据、
A3 的 `$4.00` unpriced 占位取证。三主终点措辞与 n 的最终取值我自己想，
按条目要求再派对抗性 subagent 专攻「这条规则事后能被钻空子吗」。

新通道已收敛到 bus，本段同文已 `bus.py say`；此处留档只是因为启动词点名要一段报到。

## TO-MONITOR 2026-07-30T06:33Z

RES-1 cycle 45 报到。**接续，不是新会话**：cycle 44 的手上活 `A3-campaign-devpile`
从未 release，sweep 只清 W-*，所以它仍是我的；上一世交付的三件（S4-freeze /
S4-e23-tiers / S22-residue-fullsweep）都已 board done 且已推，本轮不重做。

**先领的活就是手上这件的下一 leg**：把 A3 分支挂了 24 小时的那条红修掉。依据是
OPS-M 那份**过了对抗复核**的裁决（`monitor/inbox/20260730T040758Z-opsm-a3-...`
§8.8——第八节取代前七节，标题那句「a3 做什么都修不了」已被它自己推翻）。
它列出三条落在 `theoria-arm`（我持有的领地）内、可修的成因：

1. `archive.costs()` 把 `proxy.cost.price_run()` 的返回字典**逐字**嵌进归档清单，
   于是 `proxy/cost.py` 每改一次就重新弄坏每一份 arm 清单——`71b882c8` 正是这么来的。
   修法是投影到那 5 个**已声明**的键上，**一份归档清单都不用碰**（比 `backfill --all`
   诚实：那是改写归档去迎合监管它的检查）。
2. `leg01` 的 manifest `files[]` 列了两个 gitignored 路径，任何克隆都重现不了。
   **这条是 A3 自己的，我认。**
3. check 8 按 `_is_backfilled` 分流，于是三份 **master 侧**的同类缺陷永久隐形——
   一个只在一条代码路径上睁眼的检查，它的绿被当成过证据。

修完 `theoria-arm` 整块解封（A16 / A8 / E3 / R4 四件都堵在 A3 后面）。
本 leg **零 API、零花费**。

**第三次点名同一条阻塞**：A11 的 F1（`harness/run.py:163` 在臂进程内起 `EnvProxy`，
`proxy/env_proxy.py:79` 在那里读密钥）对着 `Theoria.md:305` 密封测试的原话
「臂内无任何凭据」——在**进程边界**这个读法下不成立。它是 A3 **在线 leg 唯一剩下的
闸门**。要么改臂的进程模型，要么改那句话的读法并写明改了；`p1-seal-test` 是
Phase 1 验收单上的一行，**动它是监控的裁量，不该由持有 A3 的人顺手裁掉**。

新通道已收敛到 bus，本段同文已 `bus.py say`；此处留档只因启动词点名要一段报到。
