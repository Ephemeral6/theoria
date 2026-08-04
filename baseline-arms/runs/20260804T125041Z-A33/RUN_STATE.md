# A33 — 「46 条基线 run 最高分 0」逐条重算

* prompt_id: `A33-forty-six-baseline-runs-scored-zero-is-wrong-three-times-over`
* worker: W-9207
* branch: `agent/a33-forty-six-baseline-runs-scored-zero`
* base_commit: `4846e66dee64940b3bb457b408db13775728915c`
* utc: 2026-08-04T12:50:41Z

Running notes; written as the work happens.

## 12:50Z — 四节数字全部复现

直接对 `baseline-arms/runs/*/run.json` 与 `runs/MANIFEST.json` 重算，工单的四节
逐个成立（下表是第一手输出，不是转述）：

| 工单声称 | 重算 | 判定 |
|---|---|---|
| 46 是清单条目数，43 才是 run | 磁盘 46 个 `run.json`，`kind=="run"` 的 43 个；另 3 条 `excluded`/`fetch`/`migration` | 成立 |
| 36 份有 summary，无一含 `score` 键 | 36 有 summary，`"score" in summary` 命中 **0** | 成立 |
| 36 份 `levels_completed` 全为 0 | `Counter({0: 36})` | 成立 |
| 7 条无 summary，通关数缺席 | 7 条，`outcome == "no_summary"`，且 `game_id` 也是 `null` | 成立 |
| dead_runs 14 | `api_unusable` 8 + `model_error` 5 + `no_reset_window` 1 = 14，且这 14 条**都有** summary | 成立 |
| budget 分布 30×22 / 20×14 / 缺失×7 | 一致 | 成立 |
| `actions_ok` 最大 30、合计 573 | 一致 | 成立 |

七条无 summary 的 id（全部 haiku、全部 `reconstructed_from_ledger: true`）：
`bare_cc-ar25-…-55ea5593`、`bare_cc-g50t-…-069d86f8`、`bare_cc-sk48-…-36c386d1`
/ `-4f5d7ddb` / `-b1ae92a0` / `-b3e5c758`、`bare_cc-tn36-…-1b9b5309`。

## 12:52Z — 先手发现：A28 已经答过「分数」那半个问题

`harness/audit_zero.py`（A28）已经证明：ARC 的 gameplay 响应
（`RESET` / `ACTIONn`）**根本不带 `score` 字段**，只带 `state` /
`levels_completed` / `win_levels`；分数只在 scorecard body 上。63 份归档
scorecard 观测里 card/run/level 分数全零、`levels_completed>0` 零次。

所以工单第二节的「无中生有」判词要收紧一档：`score` 不是被漏记，是
**这条采集路径上不存在**。缺席仍然是缺席，但它是有原因的缺席，登记的措辞
必须把这个原因写进去，否则读者会以为补记一下就有了。

## 12:53Z — A28 也留下一个反例，必须写进措辞

`audit_zero` 第 3 节：以 **scorecard 观测的 `actions`** 计，ar25 最好一次走到
**67**（其 level-1 基线 32，209%），tn36 走到 **32**（100%）。所以
「没有任何一条基线 run 被允许走到关卡基线」这句话，**只在 run 的 `budget`
这一层为真**（36/36 的 budget < 该局 level-1 基线），在 scorecard 累计动作
那一层为假。工单第四节针对 g50t（基线 78、budget 最大 30）成立，但不能推广
成全局措辞。核对器必须两层都打印。

## 13:10Z — 三路并行调查回来，工单的三处措辞要改

三个 subagent 各带独立上下文查完，三条都不是小修：

**一 · 分数是可得的，20/43 条，离线。** 权威分数在 scorecard body 的
`response_summary.environments[].runs[].score`，经 `opaque.run_id` 回连；本臂把
一部分归档进了 `probe_log.jsonl` 与 `out/shards/probe_log*.jsonl`。所以工单欠项
二不该选「写下它不可得」，该选「把列建出来」——`harness/score_column.py` 做了：
`recorded` 20（**全部 0.0**）／`unobtainable` 15（卡已永久 404，D-015 实测过
8 次重试）／`absent` 8（从未记过 card_id，含七条无 summary 的）。20+15+8 = 43。
于是「最高分 0」这句话是**可以救的**，但只在 20 条这个分母上，而且必须带上
另外 23 条是洞、不是零。

**二 · `level_baseline_actions` 不是下界。** `theoria-arm/inner/scoreboard.py`
明写：「它不是下界，超过它正是整件事的目的，所以这里没有任何一句话说某关不可
达。」工单第四节的「设计保证的结果」「结构上不可能」因此是**推断，不是证明**。
核对器把那一档命名为 `budget_below_level_1_baseline`，不叫 impossible；订正措
辞里也降级成「没有给到足以期待通关的预算」。

**三 · 「没有一条 run 被允许超过 30 个动作」是假的。** m4 试点期有 16 条
bare_cc run 超过 30 个动作（g50t 最高 **73**，ar25 **67**），它们**没有
`run.json`**，只活在 ledger 与 probe log 里。真话只有窄的那一句：**g50t 上没有
任何一条基线 run 走到过 78**。

## 13:12Z — 顺带纠正工单没提的第四处：43 也是个带限定词的数

scorecard body 里有 **57** 个不同 run_id，其中 **37** 个没有 `run.json`；
与 43 条已归档取并集是 **80** 个不同 run_id。80 正是论文 `bare_cc` 已在用的
分母（`07_battery.md:603`「the 67 of 80 bare_cc runs」）。两个独立来源撞上同一
个数，这条比单独任何一个都硬。

所以「43 才是 run 数」这句话，如果不带「**已归档**」三个字，就是下一个「46」。
核对器把 43 / 57 / 37 / 80 四个数一起打印，正是为了不让它复发。

## 13:15Z — 单价改报区间与合计口径

工单的 $0.1147/动作复算无误，且**恰是 opus 五条 run 的中位数**（不是挑的）。
但五条极差 1.74×，另有两条 opus run 花钱买到 **0** 个成功动作，中位数看不见它
们。核对器因此同时报中位数口径与**合计口径**（总花费 ÷ 总成功动作，含买到 0
动作的 run）：g50t×opus 78 动作 = $8.95（中位）/ **$11.38**（合计）。预算按合
计取。

而且工单选错了格子：要问「给足动作能不能赢」，该挑基线最低的局。ar25/tn36 的
level-1 基线是 32，不是 g50t 的 78。但这两局的卡**已经走到过基线**（67 与 32）
**且仍然 0 分**——那个实验部分做过了。所以最便宜的**未做过**的一格是
**sk48 × haiku，61 动作，约 $2.75**。

## 13:20Z — 落地清单

* `harness/audit_claim_14.py`：四节全打印，`recount()` 纯派生、`adjudicate()`
  对published 措辞比数。接进 `verify.py` 第三档。
* `harness/score_column.py`：欠项二。缺口两态永不出数字。
* `harness/audit_zero.py`：加一行前置过滤（`'"score"' not in line` 即跳过）。
  实测 38.0s → 18.7s，63 条观测 `==` 逐字相同（当场比过才改的）。
* `tests/test_audit_claim_14.py`：17 用例，含工单两条负样本，6.9s 绿。
* `STATUS.md`：:98 的「46 条」补上「条目 / 其中 43 条是 run」；:188 的
  「score 上游响应里就没有」补正为只对 gameplay 响应成立。
* `runs/20260804T125041Z-A33/CORRECTED_WORDING.md` + `monitor/inbox/…`：
  `spec.py:525` 的替换措辞。**这是本件的 gap**——`spec.py` 属 monitor 领地，
  本工单 territory 是 `baseline-arms`，故只提案不代改。

## 13:50Z — 跑套件时撞到两个与 A33 无关、但挡住验收的既有缺陷

**一 · `verify.py` 在报红的途中自己崩了。** 本机 console 是 cp936，而
`verify.py` 的 `sh()` 按 UTF-8 解码子进程输出；第一条引用了子进程输出的 FAIL
消息里带 `⁸`（上标 8），`fail()` 里的 `print` 直接抛
`UnicodeEncodeError`，**闸门在宣布红的那一刻死掉，红判没有落地**。这是闸门唯
一不能崩的时刻。已修：`main()` 开头把 stdout/stderr `reconfigure(errors=
"replace")`，不改编码、只把编不出来的字符换成 `?`。

**二 · `tests/test_schema_column.py` 在任何 linked worktree 里必红三条、
且第四条会真空变绿。** 该文件自己的 docstring 就写着「payload 是 gitignore 的，
**linked worktree 里没有**，所以跳过」，但 `_payload_or_skip()` 只查
`os.path.isdir(root)`。`schema_traces/` 里有一个**被跟踪的** `MANIFEST.json`
和八个**被忽略的** run 集合目录——于是 worktree 里目录在、载荷不在，`isdir`
放行，`measure_cache_reads()` 返回零条，三条测试在空数据上失败。

更糟的是第四条：`test_measurement_does_not_reproduce_the_published_interval`
断言两个 flag 为 False，而**没有数据时它们本来就是 False**，所以它在零数据上
**真空变绿**——正是这个文件用 negative-control-first 写法要防的东西。

证据（两处对照，不是推测）：主工作树 `schema_traces/` 下有
`claude_fable_opus` / `gpt_5_6_sol` 等集合目录，25 条全过；本 worktree 下只有
`MANIFEST.json`。且把本分支全部改动 `git stash` 到基线后重跑，三条**照样红**
——**与 A33 无关，是既有缺陷**。

已修：guard 改为查「至少有一个集合目录」，缺则**大声跳过**并指明
`SCHEMA_ARM_RULING.md` 里钉着的数与 `THEORIA_SCHEMA_TRACES` 环境变量。
本 worktree 现在 21 过 4 跳；主树载荷齐全，25 条照跑不误。

两处都写在这里而不是悄悄修掉：它们不是 A33 的活，但 A33 的验收线是
「verify 脚本绿」，绕不过去。第二条本件**不修**：重新生成档案会改掉被
`freeze/MANIFEST.json` 第 12 项、`battery`、`figures/SOURCES.sha256` 引用的
哈希，而 A14 立的规矩是「被当作证据引用过、之后又被改动的产物，比从没入库
更糟」。已写 `monitor/inbox/20260804T140000Z-W-9207-baseline-arms-gate-is-red-
on-master-for-two-pre-existing-reasons.md` 请裁决。

## 14:30Z — 对抗性复核：15 处，其中 7 处是真的，已全部修掉并补测

派了一个专门**试图推翻**（不是复读）的 subagent。结果很值：

**一 · 最严重的一处——一个 5.0 可以躲在「最高分 0.0」底下。**
`score_column` 在同一条 run 的多份 body 分数不一致时把 `score` 写成**列表**，
仍算进 `recorded`，而求最大值时又用 `isinstance(..., float)` 把列表**过滤掉**。
于是那一行自己印着 `[0.0, 5.0]`，而列的汇总照报 `max_recorded_score: 0.0`，
核对器全绿。**这正是本模块存在的理由，在低一层重犯了一遍。**
已修：分歧独立成 `conflicting` 态，永不出数字；求最大值不再过滤非数字。

**二 · `dead_runs == 14` 只钉了总数，没钉分布。** 把一条 `model_error` 改成
`api_unusable`，总数不动、发布的措辞（「api_unusable 8、model_error 5、
no_reset_window 1」）已假，核对器全绿。已修：整个 `by_outcome` 直方图逐项钉。

**三 · 「22 条玩过并输掉」根本没钉。** 把一条 `budget_exhausted` 改成任意新值，
22 悄悄变 21，全绿。已修：钉 22，并加「22+14+7 必须等于 43」的分划检查。

**四 · `recount()` 的 `obs=` 参数被下一行无条件覆盖。** 第四节永远重扫真实
探针语料，注入无效——**而这直接使两条负样本变成真空断言**：测试传 `obs=[]`
本身就让 `adjudicate` 返回两条问题，于是 `assert problems` 在**未施加任何篡改
时**就已成立。已修，并补 `test_an_unmutated_clone_is_green` 作为对照。

**五 · `unobtainable` 是无证据认定的。** 只要有 `card_id` 就贴，从不检查是否
真有过失败的探测。已修：新增 `never_probed` 态。且 docstring 原先照抄 D-015
的「GET 与 close 各重试 8 次全 404」——**实际上 15 张卡里 13 张只有一次失败的
close，GET 对这 15 张一次都没发过**。措辞改成「一次拒绝 + 套用 D-015 在另外两
张卡上的发现」，即：这是建立在测量之上的推断，不是测量本身。

**六 · 探针归属靠巧合。** 只在 URL 与响应文本里刮 uuid，从不读
`request_body.card_id`，并且把 17 条 `scorecard_close_failed` 记录整个丢掉
——那正是 D-015 的字面证据（带 `last_status` 与 `tries`）。之所以今天还对，
只因为 404 的错误文案恰好回显了 uuid。已修。

**七 · 单价表按档池化、却按「局 × 档」标行。** 于是同档每局同价，还给
`tn36 × opus` 报了价——**该格两条 run 花 $1.8815 买到 0 个成功动作**。已改为
逐格计算，无成功动作的格报 `UNDEFINED` 并说明。

**八 · 「卡跨 reset 累计动作」是错的**：那六条观测 `resets` 全为 0。真正原因
是 16 条 m4 试点期 run 超过 30 动作且从未归档。已在 docstring 与
CORRECTED_WORDING 两处订正。

**九 · 初稿推荐的 `sk48 × haiku $2.75` 撤回。** 四处不成立（走到基线的六条卡
全是 haiku、tn36 那两条恰好等于基线而「等于参考成本」不等于「已有答案」、把
预算定成正好等于基线本身就重犯「基线当下界」的错、以及一边把 m4 试点 run 排除
出所有分母一边拿它们当决定性证据）。改推 **tn36 × haiku 取 2× 基线 64 动作
≈ $3.05**，量级结论不变。

**七处它推不翻的**（逐条实算过）：22/14/7 分划无重叠、并集恰为 43；四条篡改
用例全部正确变红；四局基线在 63 条观测里完全一致、零冲突；`scoreboard.py`
的引文准确；前置过滤在本语料上零遗漏（69 行含 `"score"`，63 条命中）；
`$0.1147` 确为 opus 中位数；`spec.py:525` 确为正确行号。

**一处它指出但仅为潜在**：前置过滤没有测试守着「过滤前后逐字相同」，将来若
写入端改用 `score` 之类的转义，它会**静默向下失败**（观测变少、更多
`unobtainable`、核对器仍绿）。今天不可能发生（本领地全部经 `json.dump` ASCII
路径），已记为潜在缺陷。

复核后：`python -m harness.audit_claim_14` 仍绿，`score_column` 三态计数
（20/15/8）与最大分 0.0 **一个都没变**——这些修复加固了逻辑，没有搬动任何一个
已发布的数。测试 18 → **25 条**全绿。
