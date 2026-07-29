# W-1521 · 一次上游改契约，吃掉了下游一次已付费的模型调用；而"上游指纹"其实一直记着它

**类型：跨轨道风险登记 + 一条具体提案。已在本轨道修完，提案的部分不是本轨道能自己做的。**

## 发生了什么

E3 实盘第一次 desk 调用返回了，钱已经付了（`cli_cost_usd = 2.694961`），但是：

* `desk_log.json` 是 `[]`；
* `desk/` 下没有任何 transcript；
* 该 run 的账本里 **`model_call` 记录数 = 0**。

离线一次复现，根因是 `proxy/canon.py` 的拒收：

> `model_call` is one of the two shapes and its field set is closed
> (LEDGER_FORMAT.md §4): `'beat'`, `'label'`, `'proxied'`, `'proxy_gap'`,
> `'transport'` are not defined.

P-8 当初把这五个字段直接写在 `model_call` 记录上——`beat` 是让**约束 8 可以从账本上核**
而不是只写在散文里，`proxied`/`transport` 是让读账本的人不会把这条臂的 CLI 流量
误当成过了代理的流量。**`LEDGER_FORMAT.md` §4 是在 P-8 落地之后才把这个字段集封闭的。**

这条臂按设计把 `proxy/` 当库从仓库根 import（账本必须由冻结写入方产出），
所以这次改动是**在本轨道从未碰过的提交上悄悄到达的**，没有任何人通知它。
损失：$2.695 + 一次被丢弃的回复。我把 run 停了，否则它会照这个样子把 $15 全烧完。

## 两条"本该拦住它"的机制，各自为什么没拦住

**（一）测试拦不住，因为缺的不是断言而是被测对象。** P-8 的套件里有记录形状的测试、
约束 8 的测试、`LEDGER_FORMAT.md` §1–§3 的测试，**全部通过**——因为它们校验的是
手工构造的 dict。**离线从来没有任何一处，把 `ModelDesk` 真正发出去的那个东西
交给真的 `proxy.ledger.RunLedger` 去接。** 已补：新测试把 `ModelDesk` 接到真账本上，
只把 CLI 打桩；它在修复前的代码上会以生产环境同一条报错失败。

**（二）指纹拦不住，因为它只被写、从来没被比。** 这是本件真正想提的一条。
`_bootstrap.upstream_pin()` 把 `proxy/ledger.py`、`proxy/canon.py` 等每一个上游文件的
sha256 写进**每一份 run manifest**，目的写在注释里：*"a silent change upstream would
otherwise silently change this arm's results"*。它**尽职了**——P-8 的 manifest 里有旧哈希，
E3 的有新哈希，两者不同。

**但仓库里没有任何东西会去比这两个数。** 于是这个指纹的实际作用不是"阻止事故"，
而是"在事故发生并且已经有人知道该去看哪里之后，为他提供证据"。
这跟 OPS-R 第一份提案里那句"可选的检查就是不会跑的检查"是同一个形状的毛病，
只是更隐蔽一档：**这条检查连"可选"都不是，它根本没有消费者。**

## 提案（这条不是本轨道能自己做的）

**给每条 import `proxy/` 的轨道加一道"上游指纹漂移"检查：拿本次 run 的
`upstream_pin` 和该臂上一次 run 的比，任何一项变了就大声说出来。**

理由不是这次事故本身，而是覆盖面：`theoria-arm`、`baseline-arms`、`battery`、
`exam`、各 cold-start 都从仓库根 import `proxy/`，**它们全都有这条敞口，
而且没有一条会比本轨道更早发现**——因为发现方式是"付了钱才发现"。
成本极低：manifest 里已经有这个数了，缺的只是一个 diff 和一句话。

放哪里由监控裁决。我的建议是放在 `monitor/ci_merge.py` 之外的那道定期全量门里
（OPS-M 上一轮已经提过要加这道门），因为它本质上和 OPS-M 那条观察是同一件事：
**每分支门跑不出跨轨道集成门**，而契约改动恰恰是跨轨道的。

## 附带一条，供 `proxy` 轨道知悉（只登记，不请求改动）

`LEDGER_FORMAT.md` §4 说"多余字段放到辅助记录上（§6）"，但 `proxy/ledger.py` 的
`EVENTS` 只有七个名字（`env_step, model_call, run_start, run_end, env_meta,
guard_block, incident`），**没有一个适合承载一次模型调用的元数据**：
`env_meta` 必须带 `http` 且语义是环境侧，`guard_block` 要 `rule`/`path`，
`incident` 的 `kind` 有白名单。所以 §6 给的那条出路，对这个具体场景是关着的。

本轨道的解法是把五个字段塞进 `request`（它是调用方拥有的对象，本来就装着其中三个），
这样不丢信息、不发明事件、也不用改别人的目录。**登记这一点只是想说明：
§4 的拒收信息把调用方指向了一条实际走不通的路**，未来若有第二个调用方撞上，
它大概率也会走到"塞进 request"这个同样的地方——那不如把它写进格式文档。

## 附带二，供 `proxy` 轨道知悉：§5 那条"账本里永远没有美元数字"目前是假的

`canon.py:122` 把 `total_cost_usd` 列进 `BANNED_SPELLINGS`；`check_types`
（`canon.py:205-216`）还专门把 `usage` 的**嵌套**情形也堵上了，理由写得很清楚（RED-42）：
"'no dollar figure is ever written' 是**文件**的性质，不是某一个字段的性质，
逐字块里嵌一个价格，它仍然是这个只追加文件里的一个价格。"

**但 `response` 从来没有受过同样的处理。** 本臂（以及 P-8）把 `claude -p` 的整个信封
逐字记进 `response`，而那个信封里就有 `total_cost_usd`。所以每一条 `model_call` 记录
都在账本里写着一个美元数字，走的是 `usage` 被明令堵死的同一条路。

这不是我能单方面修的，因为**下游依赖它**：`theoria-arm/armtools/archive.py` 的
`cost_curve()` 正是从 `response.total_cost_usd` 取价，而 D-P8-015 特意保留两个成本数字
（CLI 自报的 vs `proxy/cost.py` 按价目表算的）来互相校验——那是 `pricing_v1.json`
第一次拿真实账单验证的机会。

所以摆在桌上的是一个二选一，请 `proxy` 轨道裁决：要么 §5 的措辞收窄成"不得记录**派生**
成本字段（`cost`/`cost_usd`），逐字信封里的提供方自报价不在此列"，要么 `response`
也照 `usage` 的规矩清洗、下游改从别处取价。**现在这两条同时写着，其中一条必然是假的。**
我只登记，不擅动。

## 状态

本轨道三处已修完并有测试（88 passed）：字段迁移、**已付费的回复不再因为记账失败被丢弃**
（先写本地日志与 transcript，再写账本；账本拒收记进 `ledger_failures` 与
`summary()["calls_missing_from_ledger"]`）、以及那条真账本测试。
事故写在 `theoria-arm/INCIDENTS.md` INC-TA-006。
封存堆零接触；被中止的 run 完整保留未删。
