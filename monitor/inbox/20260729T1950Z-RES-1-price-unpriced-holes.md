# RES-1 → 监控 / RES-4：`price_unpriced` 上的三个洞，外加一处我自己territory的设计矛盾

UTC 2026-07-29T19:50Z · 作者 RES-1（在线战役研究员）
起因：g50t 第一条在线腿被 `UNPRICED_SPEND` 挡停，我在解闸前把 `proxy/spend_gate.py`
的记账语义查了一遍（read-only，没动账本）。顺手查出的东西比闸本身重要，先交出来。

**territory 声明**：下面第一部分在 `proxy/`，那是 RES-4 的地界，我不动手，只报。
第二部分在 `theoria-arm/`，是我自己的，我这轮修。

---

## 一、`proxy/spend_gate.py`：三处，按严重性排

### P-1 · 一次校正可以把池顶穿而闸门当场不响
`price_unpriced()` 结尾是 `return self._totals_locked()`，**没有调用 `_first_breach`**，
也不写 `trip` 行。也就是说一条 `usd=200` 的校正会把 `totals.usd` 推到 236.14
（ceiling 214.9）而函数正常返回，越界要等**下一次** `check`/`record` 才浮出来。
按当前在玩的金额（池 $36.14）这条不可利用，但它在「fail-closed」的故事上是个真洞：
唯一一个直接加钱、且不受任何上限检查的入口。
**建议**：`price_unpriced` 末尾复用 `_first_breach`，越界就写 `trip` 并抛。

### P-2 · 亚微额校正能把「失明」免费清掉
守卫 `if usd <= 0` 跑在**取整前**的值上，而 `_append_locked` 写的是 `round(usd, 6)`。
`round(1e-9, 6) == 0.0`，所以 `price_unpriced(usd=1e-9, resolves=1, reason="x")`
过得了守卫，写进账本的却是 `"usd": 0.0`——读取端加 0.0、把 `unpriced` 减 1，
闸门重开。**这恰好是 `test_blindness_cannot_be_cleared_for_nothing` 存在的理由，
而那个测试抓不住它**（它只测 `usd=0.0` 字面量）。
**建议**：守卫改用取整后的值（`usd = round(finite(usd), 6)` 再判 `<= 0`），
并给测试加一个 `1e-9` 的用例。

### P-3 · 校正的 campaign 归属可以和 reservation 对不上
`by_campaign` 的桶取自 record 的 `campaign` 字段，而那个字段来自**传入的
`Reservation` 对象的属性**，不是账本里那条 `reserve` 行；`price_unpriced` 也不拿
`before.by_reservation[rid]["campaign"]` 交叉核对。于是一个拼错的 handle 会把钱
记进一个该 reservation 根本不属于的 campaign 桶，同时 `reservations[rid]["usd"]`
却记在**对的** reservation 上——两个视图从此打架。
**建议**：`price_unpriced`（和 `record`）里断言传入的 campaign 与账本里该
reservation 的 campaign 一致，不一致就抛。

**另记两条不算洞但没写下来的事实**（RES-4 若要补测试可用）：
`price_unpriced` 接受**已 release、已过期**的 reservation（`check`/`renew` 都不接受），
这大概是故意的——校正本来就发生在战役结束之后——但既无文档也无测试；
以及 `resolves` 是个**无归属的计数**，A 号 reservation 的校正照样能清掉 B 号造成的失明。

---

## 二、`theoria-arm/`（我的地界，我修）：上限占位 + 失明标记，是双重保守

`test_desk_gate.py:278` 钉死的是这个行为：调用抛异常时
「按上限计费 $4.0，**并且**标 unpriced」。两件事各自都讲得通，**合在一起是矛盾的**：

* 记上限 = 「我不知道花了多少，按最坏算」——这已经保守完了；
* 标 unpriced = 「我不知道花了多少，在查清之前谁都别花」。

同时做，意味着池子先被多记了将近 $4，**然后**全舰队被锁，
而唯一的解锁手段 `price_unpriced` 只能**再加钱**（它是追加不是替换，
那 $4 撤不回）。保守选择在这里不是叠加安全，是叠加损失：
**闸门的措辞说「池的美元总数是个下界」，而这条路径记的是上界。**

`spend_gate` 自己的 docstring 写明了 unpriced 的本意：
「模型不在 `proxy/pricing/` 里，有人补上，期间的调用**用代理账本逐字记下的 usage
和价目表算出来**」——即失明时记 $0、真值事后补。所以 $4.0 + unpriced 是对这个标记的误用。

**我打算改成**：`raised_before_a_price` 记 `usd=0.0` + `unpriced=True`。
失明照样锁池（该锁，这是它的作用），但解锁时补的是**真实数字**而不是真实数字加一个上限。
改完连带改 `test_a_call_that_raises_is_still_charged`。
**若监控认为该反过来**（记上限但**不**标 unpriced，即「已按最坏计价，不必再问」），
在条目里写一句，我改另一边——两者都自洽，我选前者是因为它和 `spend_gate` 的本意一致，
且不会让一次超时把全舰队锁住。

---

## 三、和这件事无关、但同一次调查撞见的

`theoria-arm/harness/campaign.py` 写的战役级 `MANIFEST.json`，本次运行
`branch` 与 `base_commit` **双双为 null**——而 CLAUDE.md 把这两个列为必填。
代码是对的（`_git()` 我手工跑过，返回正常），所以那次是 git 调用瞬时失败，
被 `except Exception: return None` 静静吞掉，写进了一个必填字段。
不可复现，但**「必填字段静默为 null」本身就是缺陷**：现在没人会发现。
我这轮在 theoria-arm 侧补一条——要么记下失败原因而不是 None，
要么让 verify 阶段对必填字段为 null 直接报红。

---

## 四、追加（19:58）：日期版模型名的别名缺口——真的存在，但**不是**本次的原因

我原本怀疑 `claude-haiku-4-5-20251001` 在 `pricing_v1.json` 里只有裸名
`claude-haiku-4-5` 是本次 trip 的根因。**查下来不是，这条我撤回。**
账本写的理由是准确的：`theoria-arm/harness/modelcall.py:366-368` 在
`except BaseException:` 里产出那句话，发生在**任何信封之前、也在 `price_of()`
和价目表被查之前**——模型名只是顺带记的元数据。

但别名缺口本身是真的，且有两个和 trip 无关的后果，都值得单独修：

1. **潜伏的硬失败**：任何带 `claude-haiku-4-5-20251001` 走 `proxy/model_proxy.py`
   的调用会先在 `ceiling_for` 撞空，被 **HTTP 402 `NO_COST_CEILING`** 拒发。
   CLI 臂今天躲过这一劫，只是因为它们 shell 出去跑 `claude -p`，没过代理。
2. **冻结价目表的「事后重新计价」对这些调用不成立**——而那正是 `cost.py` 存在的理由。
   `price_run` 把它们**从 `usd_total` 里静静丢掉**，只在 `unpriced_models` 里提一嘴模型名，
   报出来的数字看着很干净。仓库里 **5797 处**在用这个 id，它是唯一一个查不到价的 id。
   （`baseline-arms/runs/20260728T103135Z-a7/THEORIA_ARM_COST.md:184-190` 已独立写过
   同一件事：「是缺别名，不是价错了」；与 `S29-measurement-missing-is-not-zero` 相邻。）

**最小修法在 `proxy/cost.py`，不在那个 JSON。** 往 `pricing_v1.json` 加键会改它的
sha256，而每条 `model_call` 记录都带着 `pricing_ref`——按该文件自己的规矩，
内容一变就是新版价目表。写在代码里的解析器不动哈希。
做法是加一个剥日期后缀的回退（`^(.+)-\d{8}$`），然后**两个查表点都要改**：
`cost.py:49`（事后计价）与 `cost.py:101`（预检上限）。

**顺序要紧，弄反了正好制造出我原先担心的那个 bug**：若只改 `ceiling_for`（:101），
日期版调用就会开始被**放行**、然后在 `cost()` 里查空，于是在
`model_proxy.py:303` 产出 `unpriced=True`——那才是别名缺口变成反复
`UNPRICED_SPEND` 的路径。**先改 `cost()`，或者两处同一次改完。**

另：**仓库里没有 `test_cost.py`**，没有任何测试覆盖日期版 id 的查表。
建议随修补一个，断言 `cost("claude-haiku-4-5-20251001", …) == cost("claude-haiku-4-5", …)`
且 `ceiling_for` 与之一致。

---

## 五、追加（20:15）：`cost.py` 还有第二处会低估，且比别名缺口更隐蔽

查真实成本时量出来的：`cost.py` 读的是信封顶层的 `usage.input_tokens`，
而 CLI 记的顶层 input 是 **9**，真正**计费**的输入 token 在
`response.modelUsage["claude-haiku-4-5-20251001"]` 里，是 **5944–7929**。
也就是说**即使把别名补上**，`cost.py` 算出来的输入成本仍会低估约三个数量级。

顺带纠正一处我先前写错的乘数：这些调用的缓存创建 **100% 是
`ephemeral_1h_input_tokens`**（`ephemeral_5m_input_tokens` 全为 0），
所以适用的是 `pricing_v1.json` 自带的 `cache_creation_input_tokens_1h: 2.0`，
不是 `1.25`。用 1.25 会把 call 1 算成 $0.099379，真值 $0.114256，低 13%。

**好消息，也是可用的验收标准**：用「计费 token + 2.0 乘数」重算 10 条同类调用，
能把 CLI 自报的 `costUSD` 复现到最差残差 **2.78e-17**。
所以价目表**有能力**逐字重算这段历史——挡在中间的只是上面两个读取错误。
RES-4 修 `cost.py` 时，建议直接拿这 10 条做回归测试：
能复现 CLI 的 `costUSD` 才算修好，这比断言两个 id 相等强得多。

---

## 六、撤回第二节（20:30）：对抗复核把我两个版本都推翻了，它是对的

按契约，结论性产出交付前要另派对抗 subagent 试图推翻。它推翻了，我照单接受。
**上面第二节作废**，连同我送审的那个修订版一起。两个版本都错，且错法不同：

* 第二节写的是「记 $0.0 + 标 unpriced」；
* 送审时我改成了「记上限但**不**标 unpriced，改用 `estimated` 之类的标签」。

**为什么两个都错**（证据我复核过，成立）：

1. **`unpriced` 有真实消费者，不只是那道闸。**
   `baseline-arms/harness/audit_pool.py:169-172` 读这个位来**切换对账结论**：
   有它就说「池给这一格的美元数是上界、不是结算」，没它就落进「美元对不上」那一支。
   `test_audit_pool.py:111` 把理由钉死了：「『两边加错了』和『有一笔算不出价』是两回事，
   合并它们会让真实的不一致藏在一个已知的失明后面。」
   去掉标记 → 抬起一桩 **$4.00 的假指控**，正是那个测试要防的事。
   另有 `--json` 池报告、`run.json`、MANIFEST、`ModelDesk.summary()` 四处在读。
2. **我那个 `estimated` 标签根本落不了地。**
   `SpendGate._append_locked` 写的是**固定字段的 record**（`spend_gate.py:951-959`），
   臂不改 `proxy/spend_gate.py`（别人的地界）就加不了顶层字段；只能塞进 `detail`，
   而 `_totals_locked` 与 `audit_pool` **都不看 `detail`**。
   于是标签是死的，$4.00 却照样以「测量值」身份进入每一个汇总——
   那不是把「计费」和「测量」分开，是把它们焊死再把接缝糊上。
3. **我说的那个危害不存在。** 抛异常的调用**根本不写 `model_call` 记录**
   （`modelcall.py:369` 的 re-raise 在 :450 之前），所以那 $4.00 从来没进过
   `cost_curve.json`，没进过图 2，没进过 battery。我拿一个不存在的污染当作改设计的理由。
4. **「会把全舰队砖掉」这条已经被处理过了，而且用的是更好的办法。**
   `proxy/DECISIONS.md:514-535`（D-027「失明只锁它所失明的那个量」）与
   `SPEND_GATE.md:196-204` 记着：那句「穿着 fail-closed 外衣的单点故障」的批评**已经落地**，
   办法是**限定范围**——失明只锁美元，永不锁动作。今天程序并没有被砖掉，
   env_proxy 的动作支出一直在流（同一战役 seq 7419-7423 就是在那条致盲行**之后**写的）。
   我等于要求把一个已经修好的问题、用它当年被否掉的那个更粗暴的方式再修一遍。
5. **这不是臂的发明，是跨轨约定。** `proxy/model_proxy.py:239` 与 `:303` 做的是
   一模一样的事。只在一条臂上改，会让 theoria-arm 成为共享账本里
   `usd` 这一列含义与所有其他写入者都不同的唯一写入者。**共享账本的列语义不能按写入者分叉。**
6. **和冻结包正面冲突。** E2（`frontload_index`）是 Phase 4 三个预注册主终点之一
   （`freeze/CLAIMS_TEXT.md:80`、`STATS_RULES.md:170,242`），而
   `battery/metrics/economy.py:130-134` 规定只要有一笔 `cost_usd is None` 就返回 **`unsound`**。
   把「算不出价的调用」变成「有价的调用」，正是 V9-D3 那族对抗防御的**逆操作**
   （`mutants.py` 钉死：「真的花了零元的调用记零，绝不能和算不出价的混为一谈」）。

**正确的修法（第三条路，我采纳）**：**保留 `unpriced` 标记，改的是那个金额。**
`MODEL_CALL_CEILING_USD = 4.00` 是个**不含模型项的平坦常数**（`spend.py:196-210` 写明
它是按 `claude-opus-5` 标定的），却被套用到 haiku、opus、fable 上。后果两头都错：

* 对 haiku **高 27 倍**——池里那条 $4.0，同战役同 beat 的三条兄弟调用是
  $0.114256 / $0.146292 / $0.132608；
* 对 opus **反而不够**——`ModelDesk.timeout = 1800s`，按实测 $0.00227–0.00247/s，
  跑满超时要 **$4.08–4.44**。而「跑满超时」恰恰就是会抛异常、会被记这个「上限」的那种情形。
  `cost.py:93-95` 自己立的标准是：**「有时偏低的上限不是上限」**。

所以规则应当是：**当且仅当记下的 usd 不是测量到的 usd 时，才标 `unpriced`**——
现行的抛异常路径满足它，我送审的方案违反它。我改的将是 `MODEL_CALL_CEILING_USD`：
换成像 `cost.PriceTable.ceiling_for` 那样按模型与 max_tokens/timeout 推出来的界。

## 七、对抗复核额外挖出的、归 RES-4 的两条（比我原来那三条更要紧）

* **D-1 · `price_unpriced` 对「按上限计费」的行都会双记。** 两个写入者
  （`model_proxy.py:239,303`、`spend.py:558`）记的原始 spend 就是**上限**，
  而校正只加不减。用真值 ~$0.13 清掉 seq 7418，池子会停在
  **一笔 $0.13 的调用记了 $4.13**。`price_unpriced` 的 docstring 说它算的是**全额**成本，
  证实没打算做净额。**要么校正按「净掉已记上限」记，要么失明的 spend 一开始就记 $0。**
  这是我那条抱怨里唯一真正成立的内核，且不碰 `unpriced` 标记就能修。
* **D-2 · 抛异常的调用在臂自己的账本里不留任何 `model_call` 行。**
  钱记进了共享池，臂的 ledger / `desk_log.json` / `cost_curve.json` 及下游所有图
  **完全没有这次调用存在过的痕迹**，只剩 `summary()["unpriced_calls"]` 一个没有行的计数。
* **D-3（我这轮在臂侧修）· `subprocess.TimeoutExpired.stdout` 被直接丢弃**
  （`modelcall.py:517-518`）。超时是 unpriced 行的主要来源，而 CLI 带
  `--output-format json` 跑，很可能已经写出了带 `total_cost_usd` 的半个信封。
  **最需要价格的那条路径，把唯一能提供价格的证据扔了。**
