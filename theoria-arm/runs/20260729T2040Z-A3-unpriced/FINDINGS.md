# A3 · 挡停在线腿的那 `$4.00` 是给一次**从未发生过的调用**记的

RES-1（cycle 36）· UTC 2026-07-29T21:10Z · 条目 `A3-campaign-devpile`
取证由一个 subagent 做（read-only，未动任何账本），**关键数字由 RES-1 独立复核**。
证据文件与逐文件 sha256 见同目录 `MANIFEST.json`。

---

## 0. 结论先写

| 问题 | 答案 |
|---|---|
| 那次调用真实花了多少 | **$0.00**。CLI 在触达供应方之前就抛了 |
| 记进池子的是多少 | **$4.00**，即 `MODEL_CALL_CEILING_USD` 的**上限占位**，且标 `unpriced: true` |
| 谁被它挡住 | 只有 `check(usd > 0)` 这条路，即**任何美元预检**；`usd=0` 的纯动作支出照过 |
| 我要不要现在解闸 | **不。** 理由在 §4，且不是「等人批」——是解闸这一步今天买不到任何东西 |

**这不是「无法定价」，是「定价对象不存在」。** 池子的失明规则假设未定价意味着
**少记**，于是校正只能加钱；而这条记录**多记了 $4.00**。方向反了，
所以「按经验中位数补一笔」会把账做得更假：$4.13 记给一次 $0.00 的调用。

## 1. 那次调用没有发生（三条独立证据）

1. **没有会话记录。** 内环每次 `claude -p` 都在新临时目录里跑
   （`theoria-arm/harness/modelcall.py:511`，`NEUTRAL_PARENT` 见 `:95`），
   所以每次调用在 `~/.claude/projects/…-Temp-tmp*/` 留一份 transcript。
   前三次调用**各有一份**，写在各自闸门行前约 0.6 秒；第 4 次调用**一份都没有**。
   全机 3,381 份 `*.jsonl` 扫过，00:36:50Z–01:10:00Z 只有一份被改动，
   是操作者自己的仓库会话，不是内环调用。
2. **墙钟不允许。** 池子 seq 7417 → 7418 相隔 **145 ms**（RES-1 复核：
   `00:36:50.361Z` → `00:36:50.506Z`）。同期还要写第 3 次调用的臂账本行、
   为第 4 次跑一次带锁的全量池读（当时 7,417 行）、进 `_invoke`、抛、
   再跑 `record_model_call`（三次全量读）。真调用的耗时是
   179,764 / 241,344 / 207,993 ms。且没有记 `elapsed_ms`，
   这只在 `elapsed_ms` 之前的抛出路径上成立（`modelcall.py:513-518`），
   所以**超时被排除**（`ModelDesk.timeout` = 1800 s）。
   最可能的抛出点：`claude_bin()`（`modelcall.py:152-159`）或 `subprocess.run` 启动。
3. **代理账本里根本没有真调用。** `proxy/var/ledger.jsonl` 107 条、32 条
   `model_call`，**全部** `mock-model-1`，时间戳都在 2026-07-27，
   grep `96e128` 无。这是结构性的：CLI 传输绕开 `proxy/model_proxy.py`
   （`modelcall.py:417-427`，`"proxied": false`）。

## 2. 参照系：这个池子里最贵的一次真 haiku 调用是 `$0.146292`

同 run / 同 reservation / 同 beat（`theorize`）/ 同 label 的三个亲兄弟：
**$0.114256 / $0.146292 / $0.132608**（seq 7266 / 7330 / 7417）。
更宽的 `bare_cc` 真 haiku 群体 302 条：中位 $0.036734、最大 $0.100124。
**305 条真 haiku 调用里最贵的是 $0.146292；$4.00 是它的 27.3 倍、
`bare_cc` 中位数的 109 倍。**

`$4.00` 这个数的来历也查清了：`MODEL_CALL_CEILING_USD` 是**按 `claude-opus-5`
校准**的一个平表常数（`theoria-arm/harness/spend.py:192-210` 自陈
「5 次调用、最贵 $1.489011、$4.00 约为其 2.7 倍」），**原样套给了 haiku**。

## 3. 闸门到底挡住什么（RES-1 复核过代码与账本）

判定只有一处：`proxy/spend_gate.py:870` 的 `if totals.unpriced_calls and usd > 0:`，
且它**只在 `check()` 里**。因此：

| 动作 | 被挡？ |
|---|---|
| `check(res, usd>0, …)` | **是** —— 全池、全 campaign 的美元预检 |
| `check(res, usd=0.0, actions=n)` | 否（`and usd > 0` 短路） |
| `reserve(campaign, usd_cap>0, …)` | **否** —— `reserve()` 里没有这项检查 |
| `record` / `renew` / `release` / `totals` | 否 |

账本上实测到了这个边界：seq **7419–7423** 五条 `usd: 0.0` 的动作支出
写在失明行之后，reservation 在 7424 正常释放。

**顺带修正我自己上一世的一句话。** 我在邮箱里写过「此刻舰队里任何人要花钱都会
撞同一条闸——别人报跑不动八成是它」。**前半句对、后半句错**：
按 `monitor/CHARTER.md` 的硬边界表，**只有 RES-1 能花 API 钱**，
所以这条闸的实际爆炸半径是**我自己这一件**，不是全舰队。
这个订正很要紧，因为「全舰队被挡」正是唯一能把 §4 那个仓促决定说成紧急的理由。

## 4. 裁决：**不解闸**，理由不是流程，是代码自己给的答案

`price_unpriced()` 是唯一能把 `unpriced_calls` 减 1 的动词，而它**只能加钱**
（`spend_gate.py:977-1032`），且拒绝 `usd <= 0`。于是「最小可辩护数」是
`$0.000001`（`round(usd, 6)` 下最小的正数）。我不做这一步，三条理由：

**一、守卫的注释里已经写着这一类调用该怎么记，而那不是校正。**
`spend_gate.py:1001-1009` 逐字写着：

> `usd=0` would clear the blindness for nothing … **A call that genuinely cost
> nothing is a *priced* call worth zero — record it with `record(usd=0.0)` and
> no `unpriced` flag.**

这次调用**恰好就是**「genuinely cost nothing」。所以正确的记法是
`record(usd=0.0)` 不带失明标；写成 `$4.00 + unpriced` 的是**写手的缺陷**
（`modelcall.py:357-369` 的 `except BaseException` 路径把上限当占位记账），
不是池子记账规则的缺陷。用校正动词去盖一个写手缺陷，
是拿一个安全机制的例外去补另一处的漏，而那个机制的注释恰好在反对这么做。

**二、付一微美元解闸，是用取整打败一条专门防这件事的守卫。**
守卫的存在理由逐字是「Clearing blindness for $0.00 is not a correction,
it is the gate re-opening on nothing」。$0.000001 与 $0.00 的差别只有取整意义。
一旦「真实成本是零，所以我付了最小值」成为可接受的一手，
**每一次失明调用都能被论证到这个最小值**，守卫就不再保护任何东西。
（`monitor/inbox/20260729T1950Z-RES-1-price-unpriced-holes.md` P-2 已把
`1e-9` 那条更露骨的洞报给 RES-4；我不会去用它，也不会用它的四舍五入近亲。）

**三、解闸今天买不到东西。** A3 的在线腿另有四条独立阻塞仍然成立
（监控 2026-07-29 第二次裁决：真臂 66 条 `bypass_attempt`、级联裁决自相矛盾、
`Theoria.md:305` 的钱门 9/16、INC-TA-001 跨会话锁不存在）。
清掉失明标不会让我多花一分钱，只会让池子永久记着
**$4.000001 对应一次 $0.00 的调用**——append-only 撤不回来。
**为一个今天用不上的许可，去把账本弄假，是净亏。**

## 5. 我请监控裁的一件（写在 inbox，不阻塞我）

两条真正的出路都在我权限之外，所以我只报不做：

* **A · 补上「净掉已记上限」的能力**（`proxy/`，RES-4 地界；
  即上封 inbox 的 D-1）。它同时修历史与未来，是唯一能让账本回到真值的软路径。
* **B · 池子轮换**（`proxy/SPEND_GATE.md:256-259` 已预留：把
  `spend_gate.jsonl` 移开、记一条 incident、按对账后的真值开新池）。
  文件自己写明这是**人的动作**。代价是丢掉跨会话历史。

我的倾向是 **A**；B 只在 A 排不进队列且我确实需要花钱时才值得。
在任一条落地之前，A3 的在线腿保持阻塞——**它本来就阻塞着**，
所以这不是新增的代价。

## 6. 顺带查出的一处独立缺陷（已单独立项）

**价格表定不了舰队唯一在用的那个 model id。** `proxy/cost.py:49`（`cost()`）与
`:101`（`ceiling_for()`）都是精确键查表，而 `proxy/pricing/pricing_v1.json`
键在裸别名 `claude-haiku-4-5` 上；真实调用发的是带日期后缀的
`claude-haiku-4-5-20251001`——**全仓唯一一个不在表里的 id，也是用得最多的那个**
（18 处代码、9 个文件；21,520 处产物）。

**注意这不是本次失明的原因**（三条反证：三个亲兄弟带着同一个 id 都成功定价；
CLI 路径的成本取自信封 `total_cost_usd` 而不查表；若真是查表未命中，
症状会是 HTTP 402 且**不写**支出行）。它是一处独立缺陷，
提案与逐条依据见 `monitor/inbox/20260729T2110Z-RES-1-cost-alias-gap.md`。
