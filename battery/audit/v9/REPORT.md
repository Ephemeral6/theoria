# REPORT · V9 抗游戏审计（盲、预注册、经对抗复核修正）

> 一个能被刷的指标，在论文里就是负资产。 — 工单 V9-battery-gaming-audit

判据：[`PREREG_V9.md`](../../PREREG_V9.md)（**先于任何攻击落盘并提交**，含事后 `## 修订` 三条）。
盲化：[`BLINDING.md`](../../BLINDING.md)。产物：`battery/runs/20260729T021247Z-V9-battery-gaming-audit/`。

## 0. 一句话

**38 条指标，37 条被刷到了预注册门槛；95 次攻击落地。主表从 9 条变成 0 条。**
唯一没被刷动的 M3 不进主表也不算「刷不动」——它记 `undetermined`，因为它根本不会返回数字。
三道防法落地，**没有一道能把它守着的指标救回主表**。

## 1. 这一轮和已有的 B14/B15 是什么关系

工单说这道工序「一直没做」。**这句不准确**，我把不准确留在这里：
`battery/audit/gaming.py` 与 `battery/audit/exploits/` 早就在，B14 把主表从 19 压到 6，
B15 上了四道防御。V9 补的是那批工作**没有的三条纪律**：盲、预注册、变异面宽于测试面。

两轮结论**分开记账**。`gaming.tier_of` 现在先查盲轮且**只向下**；B14 的判决用
`tier_before_v9()` 仍可读。**但 B14 的基线在裁决里是钉死的常量**
（`verdict.B14_BASELINE_MAIN`），不是实时重算——理由见 §9 (c)，那是对抗复核抓到的最硬的一条。

## 2. 逐指标攻击表

「刷法」一栏是**实跑过的**攻击的 `claim`，得分是 `evaluate()` 真返回的值。
优先展示被判为**无意可达**（`accidental=True`）的那一条，因为裁决只由它决定。
带 **※** 的来自 §9 的**非盲**复核轮（`attacks/a7_review.py`）。
全部攻击的完整记录在 `v9_gaming_audit.json`。

| 指标 | 方向/门槛 | 最省力的刷法（实跑） | 实跑得分 | 攻/落 | B14 | **V9 裁决** | 防法 |
|---|---|---|---|---|---|---|---|
| **X1** | lower 0.05 | X1 = 0.0 while the board hash is literally constant across all 300 steps | `0` | 3/3 | reference | **reference** | — |
| **X2** | higher 0.95 | X2 = 1.0 on a 300-step run of which 297 steps were rejected spam | `1` | 3/3 | reference | **reference** | — |
| **X3** | higher 0.9 | X3 = 1.0 for a run that dies in an infinite loop over its whole second half | `1` | 2/2 | reference | **reference** | — |
| **X4** | lower 0.05 | X4 = 0.04 for a run that ends in a real 50-step dead stall | `0.04` | 3/3 | reference | **reference** | — |
| **X5** | neutral | X5 = 500 vs 1 from two runs that take the identical 500 actions | `500` | 1/1 | reference | **reference** | — |
| **X6** | higher 0.95 | X6 = 1.0 on 200 consecutive failures with a fresh action name each time | `1` | 4/4 | reference | **reference** | — |
| **P1** | higher 50 | P1 = 60.0 even though every model call is marked is_error=True | `60` | 3/3 | reference | **reference** | — |
| **P2** | higher 10 | P2 = 200.0 because the half-way boundary is read off a self-reported step_idx | `200` | 3/2 | reference | **reference** | — |
| **P3** | lower 0.05 | P3 = 0.0 while the agent repeats one no-op action 500 times | `0` | 3/3 | main | **reference** | — |
| **P4** | lower 1 | P4 = 0.05 after 10000 failed actions, against an honest optimal of 20 | `0.05` | 3/3 | main | **reference** | — |
| **P5** | neutral | P5 = 1.0 vs 0.005 on runs with identical actions and identical state keys | `1` | 1/1 | reference | **reference** | — |
| **E1** | neutral | E1 = 6.0 vs 0.60 with the same 50k-token context every turn; prompt caching is on in one run and … ※ | `6` | 6/5 | reference | **reference** | D3 |
| **E2** | higher 0.95 | E2 = 0.973 with spend that never front-loads at all -- 30 equal calls are simply all labelled tur… | `0.973387` | 3/2 | main | **reference** | D3 |
| **E3** | lower 0.05 | E3 = 0.0244 on a perfectly flat spend profile -- all 400 calls cost exactly $1.00; 360 of them ar… | `0.0243902` | 3/2 | main | **reference** | D3 |
| **E4** | lower 0.001 | E4 ~ 0.0 on a 20k-100k sawtooth: periodic compaction defeats both fits equally | `0` | 3/3 | reference | **reference** | — |
| **E5** | lower 0.001 | E5 = 0.000025 on a realistic $5.00 bill, purely by emitting 200000 cycling no-op actions | `2.5e-05` | 3/2 | reference | **reference** | D3 |
| **E6** | neutral | E6 = 3000.0 vs 2.0 from a single annotated step out of a thousand | `3000` | 2/2 | reference | **reference** | — |
| **E7** | lower 0.001 | E7 ~ 0.0 on a periodic 50k-320k prompt sawtooth | `0` | 3/3 | reference | **reference** | — |
| **M1** | lower 0.001 | M1 = 0.0 (perfect) on a run that used 1 of 100 mechanisms; M2 = 0.01 on the same run | `0` | 4/3 | reference | **reference** | D2 |
| **M2** | higher 0.95 | M2 = 1.0 from a one-element denominator | `1` | 4/4 | reference | **reference** | — |
| **M3** | lower 0.001 | 五次攻击全部拒答（`insufficient-data`） | **拒答** | 5/0 | main | **undetermined** | — |
| **M4** | lower 0.001 | M4 = 0.0 from one self-reported detection_actions=0 | `0` | 3/2 | reference | **reference** | D2 |
| **M5** | higher 0.95 | M5 = 1.0 from a single boolean the scored arm sets itself | `1` | 2/2 | reference | **reference** | — |
| **M6** | neutral | M6 = 1.0 vs 0.05 -- a factor of 20 -- from two runs identical except for two integers | `1` | 2/1 | main | **reference** | D1 |
| **K1** | higher 0.95 | K1 = 1.0 from a Theory carrying two integers and a run with no steps | `1` | 4/3 | reference | **reference** | D1 |
| **K10** | higher 100 | K10 = 1000000 'machine-checked proofs' declared by an integer, with proven=False everywhere (ther… | `1e+06` | 2/2 | reference | **reference** | — |
| **K11** | neutral | K11 = 1000 vs 1 for the same ten concepts; only the write granularity of the manual differs | `1000` | 2/2 | main | **reference** | — |
| **K12** | higher 0.95 | K12 = 1.0 (6/6 beats closed) on a repair episode that spent zero environment actions; the evidenc… | `1` | 4/3 | main | **reference** | D1 |
| **K13** | lower 0.001 | K13 = 0.0 from a Repair with no beats, no detection, no changed clause | `0` | 4/4 | reference | **reference** | — |
| **K14** | higher 1000 | K14 = 4096 bits over a manual of 512 concepts, 511 of which carry no compression account at all (… | `4096` | 3/3 | reference | **reference** | — |
| **K2** | higher 0.95 | K2 = 1.0 on 1 held-out pair; the sampling-frame guard is satisfied by any truthy string | `1` | 3/3 | reference | **reference** | D1 |
| **K3** | higher 100 | K3 = 250 from 250 byte-identical clauses (same name, same kind) | `250` | 3/3 | reference | **reference** | — |
| **K4** | higher 0.95 | K4 = 1.0 computed over 1 clause while 200 clauses carry no coverage at all | `1` | 3/2 | reference | **reference** | D1 |
| **K5** | higher 100 | K5 = 140 from 140 Concept records that carry a name and nothing else | `140` | 2/2 | reference | **reference** | — |
| **K6** | higher 1000 | K6 = 399808.0 bits/concept while 24 of the 25 concepts have negative gain | `399808` | 3/3 | reference | **reference** | — |
| **K7** | neutral | K7 = 1000 vs 0 on two manuals with the identical 1000 concepts; only the sign of a declared integ… | `1000` | 2/2 | main | **reference** | — |
| **K8** | higher 0.95 | K8 = 1.0 from a theory that designed exactly one probe and ran it | `1` | 3/2 | reference | **reference** | D1 |
| **K9** | higher 100 | K9 = 100000 from a theory whose every other field is empty: no concepts, no clauses, no revisions | `100000` | 2/2 | reference | **reference** | — |

## 3. 「攻不动」的那一条，为什么记 `undetermined` 而不是 `main`

**M3 是全表唯一一条 S1 都过不了的指标**，五次攻击（盲轮 2 + 复核轮 3）全部拒答。
理由在 `battery/metrics/mechanism.py`：`cross_level_first_use_delay`
**没有任何一条路径调用 `ok(...)`**。它对一条真正有跨关迁移能力的臂，
返回的东西和对攻击者一模一样。

初稿把它记成 `not_gameable` **且** `main`——正是预注册 R4 想拦的那个标签，而 R4
当时只有散文、没有代码。现在 `decide_tier()` 里有第三层 `undetermined`：
**所有攻击都没让指标答话 → 不进主表。** 复核还证明了更难看的一点：把 M3 按唯一
显然的方式实现出来（照 M1 的形状限制到跨关机制），三个攻击当场落地，其中
`fifty-levels-negative` 正是 D2 已经在同一个文件里防着的那条负延迟记录。
**M3 不是守住了，是还没开门。**

## 4. 三道防法，和它们的天花板

| id | 防法 | 变异体（须被拒） | 测试 | 变异面 > 测试面 |
|---|---|---|---|---|
| D1 | a value declared unit="share" may not exceed one, and a numerator may not exceed its denominator; such a record is refused as incoherent rather than reported as excellent | 10 | 5 | 是 |
| D2 | a first-use or detection delay may not be negative; a mechanism used before it was visible is two counters with different origins, not a fast arm | 5 | 3 | 是 |
| D3 | an unpriced model call is not a free one: the economy family refuses a partial bill instead of reading `cost_usd or 0.0` | 7 | 3 | 是 |

* **D1 · 声明为 `share` 的值不得大于一。** 盲轮打出来的不是好分数，是**不可能的分数**：
  K1=7.0、K4=3.0、K8=1000.0、K12=6.0、M6=1000.0，全部 `status="ok"`。
* **D2 · 首用/察觉延迟不得为负。** M1=−1000 在旧口径下是全电池最强的一条 run。
  M4 的 `notes["earliest_detection"]` 路径**没有任何攻击者试过**，是变异体先到的。
* **D3 · 没有价格的模型调用不是免费的调用。** `c.cost_usd or 0.0` 一行同时喂饱
  E1/E2/E3/E5 四条攻击。

**天花板：没有一道防法救回了任何一条指标。** D1 挡得住 7.0 的 share，挡不住一个
没干活的生产者直接声明 1.0；D3 挡得住残缺账单，挡不住 `E2 first-turn-bill`
（第一拍花 $1、后 39 拍诚实地花 $0，E2 = 1.0）。初稿曾说「唯一因防法回到主表的是
E1」——**那句话两处都错**，见 §9 (b)(c)。

变异体里另有 17 条是「防法**必须放过**」的记录（诚实的满分复放、诚实的零成本调用、
诚实的 6/6 修复回路），不计入攻击面。理由：一个把所有输入都拒掉的防法不是防法，
是把指标关了。

## 5. 预注册的五条预测，逐条对账（含我错的那条）

| id | 预测 | 结果 | 说明 |
|---|---|---|---|
| V9-P1 | at least 3 of the 9 current main-table metrics fall to a blind attack (main = E2 E3 K7 K11 K12 M3 M6 P3 P4) | 命中（严重低估） | 9 条主表指标**倒了 9 条**，预测说的是至少 3 条。 |
| V9-P2 | the blind attacks disagree with battery/audit/exploits/ on at least 5 metrics | 命中 | 与 B14 基线的层级判决在 **9 条**上不一致，预测说的是至少 5 条。 |
| V9-P3 | K12 falls: beats_required is fixed at 6 but the beat list comes from the source, so six closed beats can simply be asserted | 命中 | K12 被 `clause-tag` 刷到 1.0：六拍全 closed、零环境动作、只填一个 `changed_clause="c0"`。 |
| V9-P4 | M3 and K7 come back not-gameable for want of computability rather than for robustness | 半错 | M3 攻不动、理由正是「不可计算」——但**「不可计算」不等于「稳健」**，见 §3。**K7 错了**：可控性判据一击即破（1000 vs 0，同一批 1000 个概念只改 `compression_bits` 的符号）。 |
| V9-P5 | P4's `won` gate stops the old attack and not a new one: `won` is a bool on Step and can be set | 命中 | `won-but-failed`：唯一那一步同时 `failed=True, won=True`，分子 `len(ok_steps)` 变成 0，P4 得 **0.0**。 |

## 6. 攻击面的形状：这不是 37 个独立发现

盲攻击者互不通气，却各自撞上同一个结构：

1. **`state_key` 与 `action` 是臂自己提供的字符串，没有任何交叉校验。** a1 用一个
   换标签的约定同时满足 X1=0.0、X2=1.0、X4=0.0、X5=300、X6=1.0——**五条探索指标是一个发现。**
2. **认识族与机制族整族是「带 schema 的自述」。** 那七条指标没有一条读
   `run.steps` 或 `run.calls`；空 `Theory()` 即可开门。
3. **`failed` 标记同时是四条指标的橡皮擦和一条诊断项的分母。** 激励方向是少记日志。
4. **X2 与 X3 在各自门槛上互相排斥**（实例：X2=0.9616 时 X3=0.1538）。
5. **E4/E7 罚曲率不罚规模**：最差的上下文策略——第一拍拉满并保持——得满分 0.0。

## 7. 这一轮**没有**做到的

* **贫困证书是代理，不是判定**，且复核证明它**从未拒绝过任何一个攻击**
  （105/105 通过），所以它在本数据集上零选择性——「这些都是刷」是攻击者自律
  撑着的，不是 `check.py` 撑着的。见 §9 (a)。
* **威胁模型没有分层。** 91 条落地攻击里 51 条捏造生产者侧记录。一条**臂**能不能
  自己走到那里，和**适配器**写下那个值，是两件事。
* **门槛没有按真实数据校准**：31 条有方向的指标里 15 条已有诚实 run 达到门槛。
  见 `PREREG_V9.md` 修订段与 §9 (c)。
* **盲是程序性的，不是强制的**；**我（汇总者）不盲**。
* **已知缺陷未修**：裸跑 `run_battery` 会覆盖 `battery/artifacts/`。本轮**没撞到**
  （`run.py` 只写 `battery/runs/`），按工单登记而不顺手修。

## 8. 对工序 4 的建议（只记一笔）

主表是空的。这不该读成「电池没用」——37 条参考项照算照报，只是不进排序论断。
该读成的是：**Phase 4 三个主要终点里的 front-load index（E2）现在没有任何
过了工序 4 的指标托底。** 补法只有两条，都不在工序 4 里：给指标接上**行为侧对账**
（让自述必须与 `steps`/`calls` 一致），或把主表准入改成「工序 1 有效应量 **且**
工序 4 未被刷动」的合取。

## 9. 对抗复核，和它推翻了什么

交付前另派了一名**能看见全部材料**的对抗复核员，专打三条。它的判决：
**(a) 部分成立、(b) 完全成立、(c) 部分成立、(d) 盲化未被攻破（驳回）。**
下面逐条写明改了什么——**三条里有两条改变了结论本身，不只是措辞。**

### (a) 攻击者是不是其实做了真实工作 —— 部分成立

* **贫困证书从未拒绝过任何一个攻击**（105 次全过，0 次违规）。一个在唯一跑过的
  数据集上零选择性的检查器，提供不了证据。**结论没被推翻**（六个模块经复查确实
  干净：无 lambda、无带条件的推导式、无模块级计算、无嵌套定义），但**支撑它的
  是攻击者的自律，不是检查器**。这句话现在写在 `check.py` 里。
* **闭包漏洞（已修）**：`certificate()` 只读构造函数自己的源码，复核用一个在外层
  工厂里跑 BFS、返回闭包的构造器**通过了全部检查**并把 P4 刷到 1.0。
  新增 **C5：构造器必须是模块级函数**。
* **白名单足以搜索（已修）**：`min(..., key=lambda ...)` 加带条件的推导式就是
  生成–测试。现在 **lambda 与带 `ifs` 的推导式一律拒绝**。已交付的 105 个攻击
  一个都没用过这两样，所以**没有任何裁决因此改变**——规则是写给下一轮的。
* **威胁模型混同（未修，已升级为公开缺口）**：`Truth` 由标注者写、
  `Beat.env_actions` 由适配器**导出**（`model.py` 原话），而 K12 的降级攻击直接
  设 `Beat(env_actions=1)`。复核确认 P4 **不受**此指摩（它攻的是
  `len(ok_steps)` 与 `failed`/`won` 一对标记，臂侧可达）。

### (b) 「刷不动」是不是只是没想到 —— **完全成立，结论已改**

复核对 E1 写了四个**无意可达**的攻击并实跑：单位错（分对美元，48.0 vs 0.48）、
重试行（429 风暴每次 HTTP 一行，24.0 vs 2.0）、换模型（同一条 40 步轨迹、同样的
token，3.0 vs 0.10）、缓存开关（同样 50k 上下文，6.0 vs 0.60）。四条全部
S1∧S2∧S3 通过。**E1 因此离开主表**，`attacks/a7_review.py` 已收录并标注为非盲。
加上 M3 改记 `undetermined`，**主表由 {E1, M3} 变成空集**。

### (c) 降级裁决是不是循环 —— 部分成立，两处已修

* **R1 是死代码，而且是被它自己要防的机制绕过的（已修）。**
  `Exploit.proposed_tier` 对「不再成功」的 exploit 返回 `main`，于是 D3 关掉
  E1 的 B14 exploit 之后，E1 的**基线**从 `reference` 翻成了 `main`；
  `adjudicate` 读到 `prior == "main"`，升级闸**根本不会被求值**。实测：
  `R1_promotion_refused` 对 38 条全是 `False`——**R1 一次都没触发过。**
  修法两条：基线钉成常量 `B14_BASELINE_MAIN`（照抄预注册 §4），以及把整个层级
  判决抽成纯函数 `decide_tier()`，由 `test_v9_verdict_rule.py` 穷举 64 种输入
  组合，**包括那条死掉的分支**。
* **`NOT defended` 项的折叠是事后改规则（已按协议补记）。** 方向上改严了，程序上
  违反了预注册自己的修订协议——整个 `verdict.py` 根本不在预注册那个 commit 里。
  记在 `PREREG_V9.md` 修订 1，**不回去改正文**。
* **R2 的比值可被改名规避（已修）**：原先按测试名前缀数测试，改个名字就能
  改比值。现在测试按**函数体里实际提到哪些指标**归属，变异体只数**必须被拒**的
  那些：D1 17→10、D2 8→5、D3 12→7；测试 5/3/3。三道防法在改严后的口径下仍满足 R2。
* **门槛校准（未改，已标注强弱）**：复核拿 95 个真实 run 对了一遍，31 条有方向的
  指标里 **15 条已有诚实 run 达到门槛**。事后改门槛就是事后改判据，所以门槛不动，
  但降级的证据强度必须分层：

  | 强度 | 指标 | 理由 |
  |---|---|---|
  | **强** | E2、E3、K12 | 诚实值域离门槛很远（E3 诚实最小 0.885 对门槛 ≤0.05；E2 诚实最大 0.297 对 ≥0.95），K12 是结构性绕过（`changed_clause` 填一个空格即可） |
  | 中 | P3、P4、E1 | 攻击是臂侧可达的真缺陷（P3 只认周期 2；P4 的 `failed∧won` 清空分子），但门槛落在诚实 run 已能达到的带内 |
  | **弱** | K7、K11、M6 | 完全建立在 §1.1 的可控性判据上，而该判据对计数型诊断项近乎必然成立 |

### (d) 盲化有没有守住 —— 驳回（盲化守住了）

复核全量比对了仓库专名、层级词汇、汇总者预测词汇、防法名与产物数值：
**tier 知识、其它攻击者的存在、`V9-P*` 预测、`D1/D2/D3`、`unsound(` 全部零命中。**
118 个构造的 `Run` 一律 `arm="attacker"`、`source="v9"`，没有任何适配器名、
`game_id`、`campaign`、`pile` 或 `model`。

发现两处需登记而非定性为泄漏：`a5` 用了 `39960` 与 `"3 adversarial gaps"`——
**两者都逐字写在 K2 的 `thin()` 字符串里**，而那条字符串**不在**
`make_blind.NEUTRALISE` 名单上，随剥除后的树进了攻击者手里。这是
`BLINDING.md` §3 漏登记的一个泄漏面，已补记。另一处（`a5` 某个
`held_out_frame` 自由文本里出现「sealed pile」字样）是装饰性文字，零优势，登记不追。

### 复核认为**成立**的部分（同样如实记）

预注册顺序真实可验；门槛由值域带生成并有测试钉死，逐条调门槛这条解释不可用；
盲化守住；**裁决里除 `accidental` 之外没有任何字段是作者断言的**；九条降级全部
R3 合规（各指向一个 run、一个实测值、一份证书）；E2、E3、P3、P4、K12 是复核
推翻不了的实缺陷。
