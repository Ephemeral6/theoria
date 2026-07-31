# Theoria 臂的成本口径，按 §14 重算

`baseline-arms` / APP-A7 · 2026-07-28

**territory 声明**：`/theoria-arm/` 不是本轨道的目录，CLAUDE.md 禁止改别的轨道的文件。
本文只**读**它的账本，算术做在本轨道，结论发到 `PARTNER_SYNC.md`（共享面）。
**没有修改 theoria-arm 的任何文件**，也不代它裁决。

---

## 0. 结论先说，因为它推翻了我自己发过的一句话

我在 2026-07-28T17:05 那条 `PARTNER_SYNC` 里写过：

> 「`$/调用` 上涨对**任何走 `claude -p` 的臂**都成立，**三臂对比不受偏袒**」

**前半句对，后半句错。** 上涨确实对两条臂都成立——Theoria 臂用的是同一个
`claude -p`（`theoria-arm/harness/modelcall.py`，`PROVIDER =
"anthropic-claude-code-cli"`，模型代理那条路因 OAuth bearer 被剥而走不通，
它自己的文档写明了）。

**但「不受偏袒」是错的**，因为这个开销是**每次调用的固定加项**，
而两条臂的单次调用成本差 14 倍：

| | 单次调用成本 | §14 加项（opus，+3,478 cache-write tok = $0.0217） |
|---|---|---|
| bare_cc × opus | $0.1168 | **18.6%** |
| Theoria 桌面调用 | $1.0935 | **2.0%** |

**固定加项对单价便宜的一方伤害大得多。** 它把两臂的单次调用比值从
约 14.1× 压到约 9.4×——**压缩了三分之一，而且方向对 Theoria 臂有利**。
这正是跨臂对比里最不该被当成中性的那类变化。

---

## 1. Theoria 臂实际花了什么（7 次桌面调用，$7.6547）

来源：`theoria-arm/runs/*/ledger.jsonl` 里带 `usage` 的记录，
用**它自己的**冻结价目表与成本函数算（`proxy/cost.py` + `pricing_v1`,
`sha256:27ce4bb4…`），不是我另写一套算术。

| 输出 tok | cache-write | $ / 调用 | 其中输出部分 |
|---|---|---|---|
| 43,066 | 20,736 | 1.2184 | 1.0767 |
| 19,957 | 20,786 | 0.6410 | 0.4989 |
| 46,248 | 16,519 | 1.2595 | 1.1562 |
| 26,200 | 19,896 | 0.7794 | 0.6550 |
| 46,357 | 24,799 | 1.3139 | 1.1589 |
| 48,144 | 26,557 | 1.3696 | 1.2036 |
| 35,745 | 28,699 | 1.0730 | 0.8936 |

**n=7 · 合计 $7.6547 · 均值 $1.0935/调用**

**成本构成——这一条解释了全部差异：**

| 项 | 占比 |
|---|---|
| 输出 token | **86.8%** |
| cache-write | 12.9% |
| cache-read | 0.3% |
| input | 0.0% |

**Theoria 臂的账单几乎全是输出 token**（每次调用写 2 万–4.8 万 token，
它在写理论与手册），而 `bare_cc` 的 opus 每次只回 **约 10 个 token**
（「只回一行」），所以它的账单几乎全是那段前缀。
**同一个固定加项，一个是 2%，一个是 18.6%，原因就在这里。**

逐 run：

| run | 桌面调用 | env_step | $ 合计 | $/调用 |
|---|---|---|---|---|
| 20260728T012311Z-g50t-first-contact-aborted | 1 | 85 | 1.2184 | 1.2184 |
| 20260728T014402Z-g50t-first-contact-aborted | 1 | 44 | 0.6410 | 0.6410 |
| 20260728T015354Z-g50t-first-contact | 5 | 40 | **5.7953** | 1.1591 |

---

## 2. 一个必须谨慎对待的巧合

那个跑完的 run：**$5.7953 / 40 个 env_step = $0.1449 每步**，
而 `bare_cc × opus` 的新单价是 **$0.1460 每成功动作**。**差 0.8%。**

**这不是一个结果，四个理由：**

1. **n = 1**，一个 run、一局（g50t）。
2. **`env_step` ≠ `成功动作`**，两者口径不同，不能直接并排。
3. 那个 run 是**带着 carry-books 起跑的**（`--carry-source-game g50t`），
   是热启动，不是从零。
4. `bare_cc` 的 27 格 **`levels_completed` 全为 0**，所以「每关成本」这个
   唯一有意义的对比量**两边都还没有**。

**照实登记为一个巧合，不是发现。** 写在这里是因为它很容易被下一个人
当成「两臂一样贵」的证据，而它不是。

---

## 3. Theoria 臂的桌面调用在 §14 变化的哪一侧？**不知道**

`baseline-arms` 的 opus 数据把变化夹在
**07-27 17:00（cache-write 6,700）** 与 **07-28 13:00（10,178）** 之间。
Theoria 那 7 次调用发生在 **07-28 01:23–01:53**——**正好在两者中间**。

而且**无法从它自己的数据判断**：它的 prompt 本身就带着书与证据，
cache-write 是 16,519–28,699，CLI 前缀那 3,478 个 token 淹没在里面，
分不出来。

**所以 §1 的 2.0% 是「这个加项值多少」，不是「它的账单涨了 2%」。**
若它的 7 次调用已在变化之后，那 2% 已经含在上表里；若在之前，
它的未来调用会比上表贵约 2%。**两种情形下结论都一样**——
对 Theoria 臂而言这是个二阶量——但话要说准。

---

## 4. 给 Theoria 轨道的三条（建议，不是裁决）

1. **它的成本口径不需要按 `bare_cc` 的 +53% 重算。** 那个百分比是
   `bare_cc` 的，源于它每次只回 10 个 token。Theoria 臂的对应数字是
   **约 +2%**，在它自己的方差里。
2. **但跨臂的「每次调用成本」对比已经被污染了**，且偏向 Theoria 臂
   （比值从 14.1× 压到 9.4×）。若论文要出跨臂成本对比，
   **应当按每关卡/每结果算，而不是每调用**；且必须声明这段包装层变化
   两边不等地影响了它。
3. **`bare_cc` 侧的对比列已经就位**：§13.1 是 jar 开的三档单价，
   §3.5 是外推，§12 是 ⟨n⟩ = 3。**唯一还缺的是能力面的可比量**——
   27 格零通关，所以「每关成本」两边都给不出。

---

## 复现

```bash
python - <<'PY'
import sys,json,glob,os,collections
sys.path.insert(0,'.')
from proxy.cost import PriceTable
pt=PriceTable.load()
rows=[]
for p in sorted(glob.glob('theoria-arm/runs/**/ledger.jsonl',recursive=True)):
    for l in open(p,encoding='utf-8',errors='replace'):
        try: r=json.loads(l)
        except: continue
        if isinstance(r.get('usage'),dict): rows.append(r)
tot=0; lines=collections.Counter()
for r in rows:
    c=pt.cost(r['model'],r['usage']); tot+=c['usd']; lines.update(c['lines'])
print('n=%d total $%.4f mean $%.4f'%(len(rows),tot,tot/len(rows)))
print({k:'%.1f%%'%(100*v/tot) for k,v in lines.most_common()})
u={'input_tokens':0,'output_tokens':0,'cache_creation_input_tokens':3478,
   'cache_read_input_tokens':0,
   'cache_creation':{'ephemeral_1h_input_tokens':3478,'ephemeral_5m_input_tokens':0}}
print('S14 delta $%.4f/call'%pt.cost('claude-opus-5',u)['usd'])
PY
```

---

## 5. 补记：§3 的「不知道」部分解决了，因为我先前漏了数据

写完 §1–§4 之后又查了一遍，**上面的 n=7 不是它的全部实测数据**。
遗漏的原因值得记下来：A3 战役的产物在 **它自己尚未合并的 worktree** 里
（`.worktrees/a3-campaign-devpile/`），master 上没有，所以第一遍扫 `theoria-arm/runs/`
扫不到。

补上之后：

**(a) `A3-campaign-devpile` 本身不含花费。** `rehearsal/campaign.json` 是
`spent_usd = 0.0`、`elapsed_s = 1.9`、mock desk 的**排练**。
它的 `levels_completed = 0` 与 `stopped = 「3 legs in a row completed no level」`
**不能读作能力信号**——桌面是假的。

**(b) 但有三次真实的 haiku 桌面调用，且在 §14 变化之后**
（`20260729T0035Z-a3-desk-live-proof2`，07-29 00:29–00:36，**晚于 07-28 13:00**）：

| 输出 tok | cache-write（1h） | $ / 调用 |
|---|---|---|
| 16,925 | 11,796 | 0.114256 |
| 22,614 | 12,990 | 0.146292 |
| 19,406 | 13,777 | 0.132608 |

**均值 $0.1310/调用，构成仍是约 86% 输出 token。**
所以 §3 的问题对 haiku 档**有答案了**：变化之后它的桌面调用仍是输出主导，
§14 加项在这一档值 **$0.0055（约 4.8%）**。opus 那 7 次仍在夹缝里，仍未知。

**(c) 一个可操作的缺陷（属于它的轨道，我不改）**：CLI 报的模型 id 是
`claude-haiku-4-5-20251001`，而 `pricing_v1` 的键是 `claude-haiku-4-5`——
**没有这个带日期的别名**，于是 `proxy/cost.py` 对上面三次调用一律返回
`usd: null, unpriced: "model ... is not in pricing_v1"`。
它的闸门另有一条路（取 CLI 自报的 `total_cost_usd`），所以**池子里的数是对的**；
但**冻结价目表无法重算这三次**，而按该表自己的说明，能重算正是它存在的理由
（「a later price change re-prices history」）。**是缺别名，不是价错了。**

**(d) 一个我差点误报为异常、查了之后确认不是的东西。** 池子里那笔
**$4.00 整、`actions=0`、无模型**的记录，看着很像手工塞进去的数。它不是：

```
"outcome": "raised_before_a_price",  "unpriced": true,
"why": "the CLI raised before an envelope carrying a price came back"
```

**CLI 在带价格的信封回来之前就抛了，于是按保守价 $4.00 记账**——
fail-closed，宁可把未知成本记贵也不记 0。这与本轨道 D-017 的纪律是同一条。
**记在这里是因为「看着像异常」本身会被下一个人重新发现一次**，
而结论是：不必再查，它是对的。

**对 §1 结论的影响：无。** 两个档、两批数据，构成都是输出主导，
固定加项都是小量（opus 2.0%、haiku 4.8%），偏袒方向不变。
