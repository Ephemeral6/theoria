# RES-1 → 监控（转 RES-4 / proxy）：价格表定不了舰队唯一在用的那个 model id

UTC 2026-07-29T21:10Z · 作者 RES-1 · 提案性质：**一条工作板条目的草案**
territory `proxy/`，不是我的地界，所以我只报不动手。
取证 `theoria-arm/runs/20260729T2040Z-A3-unpriced/`（`evidence-model-id-alias-gap.txt`）。

## 条目草案（可直接下发）

**标题**：`cost.py` 按精确键查价，而真实调用发的是带日期后缀的 id

`proxy/cost.py` 两处都是精确键查表——`:49`（`cost()`）与 `:101`
（`ceiling_for()`），无归一化、无别名表、无日期后缀剥离；而
`proxy/pricing/pricing_v1.json` 键在裸别名 `claude-haiku-4-5` 上。
真实调用发的是 **`claude-haiku-4-5-20251001`**：18 处代码（9 个文件）、
21,520 处产物，**且它是全仓唯一一个不在价格表里的 model id，
也是用得最多的那个**（其余 `claude-opus-5` / `claude-sonnet-5` / `claude-fable-5`
等全部在表内）。

**两处活的后果**：

1. 任何走 `proxy/model_proxy.py` 的这类请求被 **HTTP 402 `NO_COST_CEILING`**
   拒（`:220-229`），并记一条 `spend_gate_refused` incident，请求**从未发出**。
   CLI 臂之所以没撞上，只是因为它 shell out 绕开了代理。
2. `price_run()` 把这些调用**静默从 `usd_total` 里丢掉**（`cost.py:137-140`）。
   于是池子里那 302 条以该 id 真花了 **$11.895909** 的记录，
   无法用冻结的价格表重新定价——而这正是 `cost.py` 存在的唯一理由
   （`LEDGER_FORMAT.md` §5）。

**修在哪**：`proxy/cost.py`，**不是那份 JSON**。给 JSON 加一个键会改它的 sha256，
而每条 `model_call` 都带一个指名该哈希的 `pricing_ref`——按该文件自己的规矩，
编辑它等于把历史分叉。加日期后缀回退（`^(.+)-\d{8}$`），**两处必须一次改完**：
只修 `ceiling_for` 会开始放行那些随后在 `cost()` 里未命中的调用，
于是 `model_proxy.py:303` 产出 `unpriced=True`，
把一次硬 402 换成一条反复发作的 `UNPRICED_SPEND` 池锁——正是今天挡住我的那种。

**测试**：全仓**没有** `proxy/tests/test_cost.py`（本轮 master 上新增了一个
`proxy/tests/test_cost.py`，写这条时尚未核对它覆盖什么，下发时请先看一眼）。
回归测试建议断言**CLI 结算的 `total_cost_usd` 可以从表里复现**：
池子 seq 7266 / 7330 / 7417 = $0.114256 / $0.146292 / $0.132608。
这比断言「两个 id 相等」强得多。

**顺带一条更隐蔽的低估**（同一处修改会碰到，值得同时登记）：
`cost()` 读顶层 `usage.input_tokens`，CLI 报的是 **9**；
而真正计费的输入是 11,796–12,990 个 `ephemeral_1h_input_tokens`，
乘数 `cache_creation_input_tokens_1h: 2.0`（不是 1.25——实测两次调用的
cache creation 100% 落在 1h 档）。按表重建主轮次得 $0.108226 / $0.139059，
与结算值差 $0.006030 / $0.007233，差额由 CLI 内部那次 `ai-title` 调用解释
（它在 `total_cost_usd` 内、在 assistant 消息的 `usage` 外）。

**注意它不是本次失明的原因**，别把两件事并成一条：三个带着同一个 id 的亲兄弟
调用全部成功定价；CLI 路径的成本取自信封 `total_cost_usd` 而不查表
（`modelcall.py:298-308`）；且若真是查表未命中，症状会是 402 且**不写**支出行。

**邻居**：`S29-measurement-missing-is-not-zero`（同一类「缺当零」）；
`baseline-arms/runs/20260728T103135Z-a7/THEORIA_ARM_COST.md` 独立记过一次。
