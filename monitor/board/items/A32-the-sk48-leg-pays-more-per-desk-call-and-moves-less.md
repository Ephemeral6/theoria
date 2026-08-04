priority: 2
cell: A32
territory: theoria-arm
deps: none
spend: none

# A32-the-sk48-leg-pays-more-per-desk-call-and-moves-less · 两条腿的钱花在了不同的地方，而轮次制把它们平均掉了

R2b 的裁决书自己把这条挑了出来（`runs/_rounds/R2b-VERDICT.md`）：

> The legs disagree and the disagreement is not noise: sk48 fired three probes
> to g50t's twenty-four, at $3.38 per desk call against $2.08, and advanced
> nine actions against twenty-nine. Whatever sk48's manual is doing, it is
> doing it in the desk rather than in the world. n=3 on that leg is too thin
> to read as a containment rate and is reported as a count.

裁决书写对了，但它把这条留成了一段散文。从 `runs/*/run.json` 的
`summary.budget` 与 `summary.bill` 重算，这不是 R2b 一轮的事——**sk48 每一轮
都是这样**：

| leg | actions_ok | probes | desk_calls | usd | usd/desk_call | usd/action |
|---|---:|---:|---:|---:|---:|---:|
| `R2b-g50t-a` | 29 | 24 | 9 | 18.736008 | **2.082** | 0.646 |
| `R2b-sk48-b` | 9 | 3 | 6 | 20.303224 | **3.384** | **2.256** |
| `R1b-g50t-a` | 25 | 14 | 9 | 17.749106 | 1.972 | 0.710 |
| `R1b-sk48-b` | 5 | 0 | 6 | 17.390721 | **2.898** | **3.478** |
| `R1-g50t-a` | 13 | 5 | 4 | 7.603419 | 1.901 | 0.585 |
| `R1-sk48-b` | 5 | 0 | 3 | 7.608528 | 2.536 | 1.522 |

三轮三次同向：**sk48 的每次桌面调用贵 30%–46%，每个动作贵 2.6–4.9 倍，
而且 R1 与 R1b 两轮的 sk48 腿探针数是 0**——它付了 6 次桌面调用的钱，一次
都没换成对世界的提问。$25 的腿上限在 sk48 上买到的是 **5 个动作**。

这件事对通关阻塞的意义是直接的：轮次制把两条腿的钱与动作**加总**记进
`round.json.totals`，于是「一轮 $35 走了 34 个动作」掩盖了「其中一条腿
$20 走了 9 个」。用总计去外推 A26 的长腿预算，会按两条腿的均价定价，而
真实的单价取决于跑哪一局——差 3.5 倍。

## 为什么贵，两个可查的候选，本件要把它判到一个

* **提示更长。** sk48 的 `books/` 更大 → 每次桌面调用的输入 token 更多。
  可查：`runs/*/desk_log.json` 与 `theorize.json` 里逐次调用的 token 数，
  以及 `books/snapshots/` 的字节数。零 API。
* **重试更多。** `armtools/refusal.py` 已经把拒绝波分过类；sk48 若落在高拒绝
  率窗口，同一次「调用」会计费多次。可查：`ledger.jsonl` 的
  `model_call` 记录数 vs `summary.bill.desk_calls`。

两个都在盘上，不需要新腿。**判到一个之前，不许把 sk48 的单价写进任何预算表。**

## 验收

一份 `runs/<UTC>-sk48-desk-cost/` 的离线归约，逐腿给出每次桌面调用的
input/output token 与计费次数，把上表的 `usd/desk_call` 差价分解成
「提示长度」与「重试」两项，并说明哪一项占主；`round.json` 增
`legs[*].usd_per_desk_call` 与 `usd_per_action`（两列都由现成键相除，零花费），
使下一轮读记分板的人看得见腿间差异而不是只看得见总计。

## 负样本

一条 `desk_calls = 0` 的腿（`20260731T1240Z-A3-level2-carried` 就是，5 个动作
0 次桌面 $0）必须读出 `usd_per_desk_call = null`，**不是** 0.0——0 美元每次
调用会让一条从未叫过桌面的腿在记分板上排成最便宜的那条。同理
`actions_ok = 0` 的 R2 两条腿的 `usd_per_action` 必须是 `null`。

---

## 对账 2026-08-04（监控·board hygiene）· 两个候选都被判死了，第三个才是对的；两列仍未落地

2026-08-02 的交付（`theoria-arm/armtools/desk_yield.py` + `prompt_census.json`，
`runs/20260802T2100Z-R2b-DESK-YIELD/`，合入 master 于 `366174bc`）
**回答了本件「判到一个」的要求，而答案是「两个都不是」**：

| | g50t-a | sk48-b |
|---|---|---|
| 最大发出提示 | 128,759 字符 | **85,904 字符** |
| 最后一次写入时的手册 | 72,299 字符 | **32,522 字符** |

**sk48 发的提示更小，付的钱更多**——「提示更长」这个候选被反向证伪，
而不是被排除。leg 内部，提示长度对账单的解释力 `r² = 7.6e-6`（六次调用）。
真正的去处是**输出侧**：最小二乘从各腿自己的账单反解出费率
（g50t cache_write $10.65/Mtok、output $25.07/Mtok；sk48 $11.11 / $24.59，
最坏残差 $0.0045 / $0.0124），**输出 token 承担两条腿各 69% 的账单**；
耗时是输出 token 的线性函数（15 次调用相关 0.996，中位 86 tok/s），
那次 22 分钟的调用是 109,763 个输出 token，不是挂起也不是网络。

所以本件正文里的两个候选（提示更长 / 重试更多）**都不是主因**，第三个是：
sk48 的桌面在写长回复，而臂把这些回复扔了——它的钱花在桌面里，不在世界上。
这与裁决书那句散文一致，但现在有出处。

**未落地的是本件验收的后半**：

```
$ grep -n "usd_per_desk_call\|usd_per_action" theoria-arm/armtools/round.py
（无输出）
```

`round.json` 的 `legs[*]` 仍然没有 `usd_per_desk_call` 与 `usd_per_action`
两列，本件那条负样本（`desk_calls = 0` 的腿必须读 `null` 不读 `0.0`）因此
也还没有被任何测试钉住。**本件保持 open，范围收窄为这两列与那条负样本**；
诊断部分已交付，不必重做，引 `runs/20260802T2100Z-R2b-DESK-YIELD/` 即可。
