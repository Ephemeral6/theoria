# REPORT · V9 抗游戏审计（盲、预注册、可复核）

> 一个能被刷的指标，在论文里就是负资产。 — 工单 V9-battery-gaming-audit

判据：[`PREREG_V9.md`](../../PREREG_V9.md)（**先于任何攻击落盘并提交**）。
盲化：[`BLINDING.md`](../../BLINDING.md)。产物：[`battery/runs/20260729T021247Z-V9-battery-gaming-audit/`](../../runs/20260729T021247Z-V9-battery-gaming-audit/)。

## 0. 一句话

**38 条指标，37 条被盲攻击刷到了预注册门槛，105 次攻击里 91 次落地。**
唯一没被刷动的是 **M3**，而它攻不动的原因是**它根本不会返回数字**——不是稳健，是没实现。
B14 留下的 9 条主表指标倒了 8 条；三道防法落地，但没有一道能把它守着的指标救回主表。

## 1. 这一轮和已有的 B14/B15 是什么关系

工单说这道工序「一直没做」。**这句不准确**，且我把不准确留在这里：
`battery/audit/gaming.py` 与 `battery/audit/exploits/` 早就在，B14 把主表从 19 压到 6，
B15 上了四道防御。V9 补的不是工序本身，是那批工作**没有的三条纪律**：

1. **盲**。B14 的攻击者和 `gaming.py` 在同一棵树里，而 `gaming.py` 逐条写着
   `how_to_game` 与 `defence`——照着提示找答案，测不出登记簿没写到的攻击面。
2. **预注册**。B14 没有先写死「什么算刷成功」。
3. **变异体多于测试**。B15 的防御没有这条约束。

两轮的结论**分开记账**：一致是弱证据，不一致才是发现。`gaming.tier_of` 现在先查盲轮，
且**只向下**（R1）。B14 的判决用 `tier_before_v9()` 仍然可读，两者可 diff。

## 2. 逐指标攻击表

「刷法」一栏是**实跑过的**攻击的 `claim`，得分是 `evaluate()` 真返回的值，不是作者写的。
全部 105 次攻击的完整记录（含贫困证书逐条结论、失败的攻击、拒答的理由）在
`v9_gaming_audit.json`。

| 指标 | 方向/门槛 | 最省力的刷法（实跑，盲攻击） | 实跑得分 | 攻/落 | B14 | **V9 裁决** | 防法 |
|---|---|---|---|---|---|---|---|
| **X1** | lower 0.05 | X1 = 0.0 while the board hash is literally constant across all 300 steps | `0` | 3/3 | reference | **reference** | — |
| **X2** | higher 0.95 | X2 = 1.0 on a 300-step run of which 297 steps were rejected spam | `1` | 3/3 | reference | **reference** | — |
| **X3** | higher 0.9 | X3 = 1.0 for a run that dies in an infinite loop over its whole second half | `1` | 2/2 | reference | **reference** | — |
| **X4** | lower 0.05 | X4 = 0.04 for a run that ends in a real 50-step dead stall | `0.04` | 3/3 | reference | **reference** | — |
| **X5** | neutral | X5 = 500 vs 1 from two runs that take the identical 500 actions | `500` | 1/1 | reference | **reference** | — |
| **X6** | higher 0.95 | one poverty-certified run clears the X1/X2/X4/X6 thresholds simultaneously | `1` | 4/4 | reference | **reference** | — |
| **P1** | higher 50 | P1 = 60.0 even though every model call is marked is_error=True | `60` | 3/3 | reference | **reference** | — |
| **P2** | higher 10 | P2 = 200.0 because the half-way boundary is read off a self-reported step_idx | `200` | 3/2 | reference | **reference** | — |
| **P3** | lower 0.05 | P3 = 0.0 while the agent repeats one no-op action 500 times | `0` | 3/3 | main | **reference** | — |
| **P4** | lower 1 | P4 = 0.05 after 10000 failed actions, against an honest optimal of 20 | `0.05` | 3/3 | main | **reference** | — |
| **P5** | neutral | P5 = 1.0 vs 0.005 on runs with identical actions and identical state keys | `1` | 1/1 | reference | **reference** | — |
| **E1** | neutral | E1 is whatever number I write in cost_usd; identical run shape, 12 calls either way, values 3000.… | `3000` | 2/1 | main | **main** | D3 |
| **E2** | higher 0.95 | E2 = 0.973 with spend that never front-loads at all -- 30 equal calls are simply all labelled tur… | `0.973387` | 3/2 | main | **reference** | D3 |
| **E3** | lower 0.05 | E3 = 0.0244 on a perfectly flat spend profile -- all 400 calls cost exactly $1.00; 360 of them ar… | `0.0243902` | 3/2 | main | **reference** | D3 |
| **E4** | lower 0.001 | E4 ~ 0.0 on a 20k-100k sawtooth: periodic compaction defeats both fits equally | `0` | 3/3 | reference | **reference** | — |
| **E5** | lower 0.001 | E5 = 0.0 -- one nanocent call, 2000 identical no-op actions that never change the state key | `0` | 3/2 | reference | **reference** | D3 |
| **E6** | neutral | E6 = 3000.0 vs 2.0 from a single annotated step out of a thousand | `3000` | 2/2 | reference | **reference** | — |
| **E7** | lower 0.001 | E7 ~ 0.0 on a periodic 50k-320k prompt sawtooth | `0` | 3/3 | reference | **reference** | — |
| **M1** | lower 0.001 | M1 = 0.0 from a single hand-written annotation; the run has 3 steps and no mechanism use in them | `0` | 4/3 | reference | **reference** | D2 |
| **M2** | higher 0.95 | one 12-step run hits M1=0.0, M2=1.0, M4=0.0, M5=1.0, M6=1.0 simultaneously | `1` | 4/4 | reference | **reference** | — |
| **M3** | lower 0.001 | 两次攻击都被拒答：the run never reached a second level; transfer cannot be measured with | **拒答** | 2/0 | main | **main** | — |
| **M4** | lower 0.001 | M4 = 0.0 while support says undetected_on_own_level=40 -- the manual noticed nothing, instantly | `0` | 3/2 | reference | **reference** | D2 |
| **M5** | higher 0.95 | M5 = 1.0 over 500 episodes with zero beats, zero detection_actions and zero theorems | `1` | 2/2 | reference | **reference** | — |
| **M6** | neutral | M6 = 1.0 vs 0.05 -- a factor of 20 -- from two runs identical except for two integers | `1` | 2/1 | main | **reference** | D1 |
| **K1** | higher 0.95 | K1 = 1.0 with a 39960-pair denominator that no step in the run supports | `1` | 4/3 | reference | **reference** | D1 |
| **K10** | higher 100 | K10 = 1000000 'machine-checked proofs' declared by an integer, with proven=False everywhere (ther… | `1e+06` | 2/2 | reference | **reference** | — |
| **K11** | neutral | K11 = 1000 vs 1 for the same ten concepts; only the write granularity of the manual differs | `1000` | 2/2 | main | **reference** | — |
| **K12** | higher 0.95 | K12 = 1.0 (6/6 beats closed) on a repair episode that spent zero environment actions; the evidenc… | `1` | 4/3 | main | **reference** | D1 |
| **K13** | lower 0.001 | K13 = 0.0 from a Repair with no beats, no detection, no changed clause | `0` | 4/4 | reference | **reference** | — |
| **K14** | higher 1000 | K14 = 4096 bits over a manual of 512 concepts, 511 of which carry no compression account at all (… | `4096` | 3/3 | reference | **reference** | — |
| **K2** | higher 0.95 | K2 = 1.0 with frame literally set to '3 adversarial gaps' -- the case the code's own thin() text … | `1` | 3/3 | reference | **reference** | D1 |
| **K3** | higher 100 | K3 = 250 from 250 byte-identical clauses (same name, same kind) | `250` | 3/3 | reference | **reference** | — |
| **K4** | higher 0.95 | K4 = 1.0 computed over 1 clause while 200 clauses carry no coverage at all | `1` | 3/2 | reference | **reference** | D1 |
| **K5** | higher 100 | K5 = 140 from 140 Concept records that carry a name and nothing else | `140` | 2/2 | reference | **reference** | — |
| **K6** | higher 1000 | K6 = 1000000.0 bits/concept from three integers nobody recomputed | `1e+06` | 3/3 | reference | **reference** | — |
| **K7** | neutral | K7 = 1000 vs 0 on two manuals with the identical 1000 concepts; only the sign of a declared integ… | `1000` | 2/2 | main | **reference** | — |
| **K8** | higher 0.95 | K8 = 1.0 at a million designed probes, with 50 clauses still flagged probe_pending and none proven | `1` | 3/2 | reference | **reference** | D1 |
| **K9** | higher 100 | K9 = 100000 from a theory whose every other field is empty: no concepts, no clauses, no revisions | `100000` | 2/2 | reference | **reference** | — |

**读这张表的三个注意事项：**

* **「攻/落」的第二个数是通过 S1∧S2∧S3 的攻击数。** 落地数少于攻击数不代表指标强——
  多数情况是同一个攻击者故意留了一个**对照**（比如 a2 的 `P2 proportional-floor`
  跑遍 calls 4–40 × steps 1–3000，最大只到 0.667，证明那条分支够不着门槛；
  a6 的 `K12 no-trace` 证明 B15 的 `unevidenced` 闸确实会拦）。
* **`neutral` 指标（E1 E6 K7 K11 M6 P5 X5）的门槛是可控性**，不是「更好」：
  两个都通过贫困证书的 run，读数差 10 倍即判刷得动。M6 的 `dial` 只差 20 倍、
  K11 的 `bookkeeping` 差 1000 倍，两个 run 的其余内容逐字节相同。
* **防法一栏写着 D1/D2/D3 的指标，仍然大多是 `reference`。** 防法关掉的是一类攻击，
  不是这条指标。见 §4。

## 3. 攻不动的那一条，以及它为什么不算好消息

**M3 是全表唯一一条 S1 都过不了的指标。** a4 给了它两个 run（两层 + 完整跨层标注 /
单层），两次都拿到 `insufficient-data`。R4 要求写出「是什么结构挡住了攻击」，答案是
`battery/metrics/mechanism.py` 里 `cross_level_first_use_delay` 的最后一行：

```python
return thin("M3", "multi-level runs exist but the cross-level annotation "
                  "schema is not yet defined; see STATUS.md")
```

**函数体里没有任何一条路径调用 `ok(...)`。** 它对一条真正有跨关迁移能力的臂，会返回和
对攻击者一模一样的东西。这不是防御，是未实现——预注册 V9-P4 就是这么写的，也是这么中的。
**M3 留在主表是记账的产物，不是证据。** 任何引用主表的地方都必须写明这一点。

## 4. 三道防法，和它们的天花板

| id | 防法 | 变异体 | 测试 | 变异面 > 测试面 |
|---|---|---|---|---|
| D1 | a value declared unit="share" may not exceed one, and a numerator may not exceed its denominator; such a record is refused as incoherent rather than reported as excellent | 17 | 5 | 是 |
| D2 | a first-use or detection delay may not be negative; a mechanism used before it was visible is two counters with different origins, not a fast arm | 8 | 3 | 是 |
| D3 | an unpriced model call is not a free one: the economy family refuses a partial bill instead of reading `cost_usd or 0.0` | 12 | 4 | 是 |

* **D1 · 声明为 `share` 的值不得大于一。** 盲轮打出来的不是「好分数」，是**不可能的分数**：
  K1=7.0、K4=3.0、K8=1000.0、K12=6.0、M6=1000.0，全部 `status="ok"`。
  这是一次**健全性**修复，不是抗游戏修复——代价一次比较。
* **D2 · 首用/察觉延迟不得为负。** M1=−1000（用在看见之前一千步）在旧口径下是全电池
  最强的一条 run。M4 的 `notes["earliest_detection"]` 路径也补了同一道闸，
  **那条路径没有任何攻击者试过**，是变异体先到的。
* **D3 · 没有价格的模型调用不是免费的调用。** `economy.py` 的
  `c.cost_usd or 0.0` 一行同时喂饱了 E1/E2/E3/E5 四条攻击。缓存命中、流式响应、
  报错调用都会让 provider 不回 usage，所以这是最「无意中」的一条。

**天花板要说清楚：三道防法没有一道能把它守着的指标救回主表。**
D1 挡得住 7.0 的 share，挡不住一个没干活的生产者直接声明 1.0；
D3 挡得住残缺的账单，挡不住 a3 的 `E2 first-turn-bill`（第一拍花 $1、后面 39 拍
诚实地花 $0，E2 = 1.0）。**唯一因防法回到主表的是 E1**，而 E1 是 `neutral` 诊断项，
它剩下的那个攻击（`dial`，把单价写成 250 或 0.0001）我按 R2 判为**故意造假而非无意**，
不是「攻不动」。E1 的升级是有证据的（防法 + 12 个变异体 > 4 个测试），但它不该被当成
一条被验证过的排序指标。

**变异体里有约三分之一是「防法必须放过」的记录**（诚实的满分复放、诚实的零成本调用、
诚实的 6/6 修复回路）。理由：一个把所有输入都拒掉的防法不是防法，是把指标关了——
那是伪造工序 4 最省事的办法。

## 5. 预注册的五条预测，逐条对账（含我错的那条）

| id | 预测 | 结果 | 说明 |
|---|---|---|---|
| V9-P1 | at least 3 of the 9 current main-table metrics fall to a blind attack (main = E2 E3 K7 K11 K12 M3 M6 P3 P4) | 命中（低估） | 9 条主表指标里**倒了 8 条**，预测说的是至少 3 条。 |
| V9-P2 | the blind attacks disagree with battery/audit/exploits/ on at least 5 metrics | 命中 | 与 B14 的层级判决在 **8 条**上不一致，预测说的是至少 5 条。 |
| V9-P3 | K12 falls: beats_required is fixed at 6 but the beat list comes from the source, so six closed beats can simply be asserted | 命中 | K12 被 `clause-tag` 刷到 1.0：六拍全 closed、零环境动作、只填一个 `changed_clause="c0"`。 |
| V9-P4 | M3 and K7 come back not-gameable for want of computability rather than for robustness | 半错 | M3 确实攻不动，且理由正是我预测的「不可计算」——它的函数体里没有任何一条路径调用 `ok(...)`。**K7 预测错了**：它被可控性判据打穿（1000 vs 0，同一批 1000 个概念只改 `compression_bits` 的符号）。 |
| V9-P5 | P4's `won` gate stops the old attack and not a new one: `won` is a bool on Step and can be set | 命中 | `won` 是 `Step` 上的一个布尔，摆上去即可。更难看的是 `won-but-failed`：唯一那一步同时 `failed=True, won=True`，分子 `len(ok_steps)` 变成 0，P4 得 **0.0**。 |

## 6. 攻击面的形状：这不是 37 个独立发现

盲攻击者互不通气，却各自撞上同一个结构，这比任何单条攻击都重要：

1. **`state_key` 与 `action` 是臂自己提供的字符串，没有任何东西交叉校验。**
   a1 用一个换标签的约定同时满足 X1=0.0、X2=1.0、X4=0.0、X5=300、X6=1.0——
   **五条探索指标是一个发现，不是五个。**
2. **认识族与机制族整族是「带 schema 的自述」。** a5：这七条指标没有一条读
   `run.steps` 或 `run.calls`；`Theory()` 空对象即可开门。a4：M1/M2/M4/M5/M6
   只读 `truth.mechanisms` 与 `repairs`，从不与行为对账。
3. **`failed` 标记同时是四条指标的橡皮擦和一条诊断项的分母**（a2）。P1/P2/P3/P4
   都走 `ok_steps`，P5 只排不评——**激励方向是少记日志。**
4. **X2 与 X3 在各自门槛上互相排斥**（a1 给了证明与实例：X2=0.9616 时 X3=0.1538）。
   同时报这两条的记分卡在报一个矛盾。
5. **E4/E7 罚的是曲率不是规模**（a3）：最差的上下文策略——第一拍拉满并保持——得满分 0.0。

## 7. 这一轮**没有**做到的

* **贫困证书是个代理，不是判定。** C3 用「白名单之外一个调用都不许」近似「没干活」。
  两条边都写在预注册里、都没有在看到结果之后改：过严（需要 `itertools` 的诚实攻击
  得改写成摆数据）、过松（`sum`/`sorted` 原则上能拼出一点算术）。
* **威胁模型没有分层。** 很多攻击直接捏造 `Theory` / `Truth` / `Repair`。
  一条**臂**能不能自己走到那里，和**生产者/适配器**写下那个值，是两件事。
  本轮把两者都算作「刷得动」，因为电池对这两者一视同仁地信任——但论文里必须分开说。
  这是我认为本报告最该被人接着打的地方。
* **盲是程序性的，不是强制的。** 见 `BLINDING.md` §3.4。
* **我（汇总者）不盲。** §5 的预测是有先验的预测，只用来检验我自己的判断。
* **已知缺陷未修**：裸跑 `run_battery` 会覆盖 `battery/artifacts/`。本轮**没有撞到**——
  `battery/audit/v9/run.py` 只写 `battery/runs/`，从不碰 `artifacts/`——按工单要求
  登记而不顺手修。

## 8. 对工序 4 的建议（不在本工单范围内，只记一笔）

主表现在是 `{E1, M3}`，而这两条一条是诊断项、一条是未实现。**照字面读，主表是空的。**
这不该被读成「电池没用」——29 条参考项照样算、照样报、照样进相关矩阵，只是不进排序论断。
该被读成的是：**Phase 4 的三个主要终点里，front-load index（E2）现在没有一条通过
工序 4 的指标托底。** 补法只有两条，都不在工序 4 里：给指标接上**行为侧对账**
（让 `Theory` 的自述必须与 `steps`/`calls` 一致），或者承认电池是被动仪器、
把主表的准入门槛改成「工序 1 有效应量 **且** 工序 4 未被刷动」的合取——
现在这两个集合几乎不相交，`REPORT_V2.md` 第 3 条早就指出来了。
