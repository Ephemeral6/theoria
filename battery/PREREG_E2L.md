# PREREG_E2L — 步轴前载指数（E2L）的预注册

> 一个只能靠标签取胜的终点，不是终点。

本文件在 **E2L 的任何数值产生之前**落盘并提交。可证顺序：

```bash
git merge-base --is-ancestor <this-commit> <results-commit>
```

命令与输出留痕在 `battery/runs/<UTC>-E2L-frontload-step-axis/`。

---

## 0. 为什么另立一条，而不是修 E2

`Theoria.md:319` 把前载指数定义为「前 k% **回合**花掉的成本占比」。电池的
`E2` 照此实现，回合轴取 `Call.turn`——而 `Call.turn` 是**记录方写下的标签**。
V9 盲攻击 `batched-turn-label` 把 30 次等额调用统统标成 `turn=0`，E2 读出
0.973，而那笔开销在时间上完全没有前载。攻击成立，E2 因此在参考层。

`PREREG_V9.md` R1 写死：**V9 只降不升**。所以 E2 不会因为「换个威胁模型它就干净了」
回到主表，本文件也不试图让它回去。E2L 是**新指标**，从工序 1 开始重走四道工序，
与 E2 并列公布，冲突留在明面上。

## 1. 定义（写死，之后不得改）

设一次 run 的**步轴**为记录方为每个环境动作盖的序号 `Step.idx`；设每次模型调用
`Call` 携带 `step_idx`——该调用是在第几个动作处做出的决策。

* 头部长度 `h = n_steps * k`，`k = 0.25`，**不取整**；
* 把每次调用的花费记在它的 `step_idx` 上，得到逐步花费序列 `c[0..n_steps-1]`；
* `E2L = cost_through(c, h) / sum(c)`，`cost_through` 沿用 `battery/metrics/
  economy.py::_cost_through` 的插值口径（整步全计，边界那一步按比例计）。

插值不是新发明：E2 v2.1 已经换过，理由是 `ceil` 让**平坦**的 run 随长度在
0.333 与 0.250 之间摆动。同一口径下平坦 run 在任何长度上恰好 0.250。

**与 E2 的唯一实质区别是分母轴**：E2 按 `Call.turn` 分桶，E2L 按 `Call.step_idx`
分桶。回合标签由 harness 的批处理约定决定，动作序号由环境的应答决定。

## 2. 拒答条件（每一条都不许退化成数字）

按 `PREREG_V9.md` §1 S1 的精神——**电池拒答就是防御生效的样子**，拒答不算被刷动。

| 代号 | 条件 | 返回 |
|---|---|---|
| G1 | 任一 `Call.cost_usd is None` | `unsound`（沿用 V9-D3：未定价调用不是免费调用） |
| G2 | 总花费 `<= 0` | `thin` |
| G3 | `n_steps < 8` | `thin`（沿用 E2 的早死下限 `MIN_TURNS_FOR_SHAPE`） |
| G4 | **任一带价调用的 `step_idx is None`** | `unsound` |
| G5 | 头部之后新到达的相异 `state_key` 少于 2 个 | `thin`（「付完就不动了」不给分） |

**G4 是本条指标存在的理由**，必须写在这里而不是注释里：E2 在 `turn is None`
时回落到「一次调用一个回合」（`Run.turn_costs()`），于是标签缺失被静默地换成
另一个轴。E2L **不回落**。轴重建不了就是没有测量，不是有测量而值可疑。

**G5 是防法，不是修辞**：`first-turn-bill` 那类攻击（第一回合付清、其后 39 步
免费）在任何按成本份额定义的前载指数上都得 1.0，而按 `Theoria.md` 的读法
（「买了理论然后滑行」），滑行必须**还在前进**。G5 只用 run 自己记的
`state_key`，不引入真值。

G5 是**升级性防法**，按 `PREREG_V9.md` R2 要付双倍价：变异体数须严格多于测试数，
且变异体须覆盖防法条件之外的形态。不满足则 E2L 在本轮裁决表里记 `reference`，
并写明「防御未达 R2」。计数由 `battery/tests/` 从磁盘数出，不写死在表里。

## 3. 成功判据（沿用 V9 §1，逐字）

方向 `higher`，值域有界 `[0,1]` → 按 `PREREG_V9.md` §1.2 的规则表，
**门槛 `TARGETS["E2L"] = 0.95`**。攻击 A 对 E2L 刷成功当且仅当 S1（电池答了）
∧ S2（`value >= 0.95`）∧ S3（贫困证书通过，`battery/audit/v9/check.py` 原样）。

**外加一条本轮新增、比 V9 严的判据 S4**：攻击构造的 `Run` 必须通过
`battery/audit/threat.py` 里**经真实语料校验后留存**的全部记录方不变量
（T-ARM）。理由：V9 的攻击者同时是记录方，那个威胁模型下**任何**读自述账本的
被动仪器都可刷，普遍降级是定理不是测量。S4 把「臂能不能自己走到这个分数」与
「生产者能不能写下这个数」分开——`STATUS.md` W-12 说论文里必须分开说，这是它的
可执行形式。

**S4 不是豁免**：不变量先由真实语料证伪（任何真 run 违反的一条立即丢弃并记下
反例），且若 T-ARM 把全部攻击都清掉，`threat.assert_not_vacuous` 拒绝出结论。

## 4. 方向性预测（写在算出任何 E2L 数值之前）

**诚实标注 `[seen]`**：写本文件之前，我已经读过四条活腿 `curves.json` 的
**逐回合 `usd` 序列**（为了确认 `step_idx` 字段是否存在，我把整份 rows 打印了
出来）。因此下列涉及活腿数值的预测**不是盲的**，按 `PREDICTIONS.md` 的
W-1 程序性修法逐条打标。只有 P4/P5 两条是结构性的、与数值无关。

| # | 预测 | 盲否 |
|---|---|---|
| P1 | 四条活腿里**只有 1 条**能算出 E2L（其余触 G3 或 G2）| `[seen]` |
| P2 | 能算出的那条，E2L **在 0.20–0.40 之间**，即**几乎不前载** | `[seen]` |
| P3 | E2L 与 E2 在同一条腿上**不相等**（两条轴不是一回事）| `[seen]` |
| P4 | `batched-turn-label` 的 T-ARM 修复版（补上 40 个 `Step`）**能刷动 E2**（≥0.95）且通过贫困证书与全部不变量 | `[blind]` |
| P5 | 同一个修复版**刷不动 E2L**（值 < 0.95），因为轴不再由标签决定 | `[blind]` |
| P6 | E2L 的**配对局数为 0**：四条活腿没有对照臂，工序 1 无法执行 | `[seen 结构]` |

以上六条的对错逐条写进 `battery/runs/<UTC>-E2L-frontload-step-axis/RUN_STATE.md`，
**包括我错的那些**。

## 5. 不做什么

* 不改 `battery/artifacts/`（PREREG_V9 §5 的冻结基线），产物一律写
  `battery/artifacts_live/`；
* 不改 `battery.audit.gaming.tier_of`，不移动任何既有指标的层级——R1 约束本文件；
* 不改 `battery/adapters/theoria_live.py`：给 `Call.step_idx` 填值会同时改动
  `P2` 在活腿上的读数（`battery/metrics/planning.py:50` 读它），那是另一张工单；
* 不打网络、零 API 花费、零封存堆接触。

---

*预注册人：battery（E2 前载终点工单）。落盘时间见本文件的 commit。*


---

## 修订

本文件 §1 写着「写死，之后不得改」，§2 的五道闸同理。以下这一条是**在看到
全部数值之后**发生的，因此按 `PREREG_V9.md` §0 的修订协议追加在这里，而不是
回去改上面的正文。`PREREG_V9.md` 的修订 1 是同型先例，连它的自我评价一起适用：
方向上把规则改**严**了（`PREREG_V9.md` R1 只降不升的安全方向），程序上仍然
是一次失守，因为本文件 §0 钉的是
`git merge-base --is-ancestor <本文件的 commit> <出数的 commit>`，
而一条修订必然是出数那个 commit 的**后代**——本文件自己的仪器会说它没有祖先。
写下来是为了让它是一次可查的失守，而不是一次看不见的编辑。

### 修订 1（2026-08-02，S46）· 新增 G6：曲线不认账，它的零就不是零

**起因**：工单 `S46-turn-costs-mixes-two-axes`（`freeze` 经 `monitor/inbox/`
派单，登记为 `freeze/RESIDUALS.json` 的 `E2-AXIS`）。

**改了什么**：`leg_reading` 在 G2 之前新增一道闸——

> **G6**：`curves.json` 的 `self_check` 未同时认证
> `accounts_for_every_billed_call` 与 `accounts_for_every_dollar` → `unsound`。

**为什么必须在 G2 之前**：G2 说的「total cost is zero」是关于**曲线自己那些行**
的和，而 E2L 把它当成关于**这条腿**的事实发表。两句话只有在曲线认账的前提下
才是同一句话。`20260731T231654Z-R1-sk48-b` 不认账：它的曲线在两行上合计
$0.00、逐行 `model_calls: 0`，而代理账本对这条腿计了 3 次调用、$7.6085275。
E2L 为它印的是 `status: thin` / `reason: "total cost is zero"`——
**把 $7.61 印成了零**。这正是本工单开出来要修的那句「看不出钱少了一截」，
只是它出现在产物里而不是在 `Run.turn_costs()` 里。
另一条 `20260731T231654Z-R1-g50t-a` 同样不认账（曲线 $7.6034195，
账本 $7.6085275），今天读作 `ok` 0.0；G6 之后两条都记 `unsound`。

**为什么闸在钱上，不闸在 `join_confidence` 上**（这一条是本次最该被质疑的判断，
所以把否掉的那个方案也写下来）：工单的验收原文是「那三条腿重算后，判定与它们
各自的 `join_confidence` 一致」，最直白的读法就是 degraded / ambiguous 一律拒答。
**这个读法被证据否掉了**：

* `degraded` 的成因逐条查过，全部是同一条**回合脊**的检查失败
  （`every billed theorize invocation was claimed by a turn`，未认领的分别是
  r2 的 turn 4、r3 的 turn 29、R2b 的 turn 26）；而这些腿的**步轴是完好的**，
  `anchored == priced` 逐条成立。
* 本文件 §1 逐字写着「**与 E2 的唯一实质区别是分母轴**……回合标签由 harness 的
  批处理约定决定，动作序号由环境的应答决定」。拿回合脊的缺陷去否决步轴的读数，
  等于把 E2L 重新拴回它被造出来就是为了摆脱的那条轴。
* 后果也不对：会把 6 条读数（0.0 / 0.115685 / 0.0 / 0.064934 / 0.083959 / 0.0，
  全部远低于平坦值 0.250，即**活臂在步轴上是后载的**）在看到方向之后改成拒答。
  那是与预注册方向相反的探索性读数，而 `freeze/STATS_RULES.md` §8 第一条与
  §3.0.6 都逐字封死了这一步：**探索性读数照报，包括方向与预注册相反的**。
* 而且它连验收本身都满足不了：`R1-sk48-b` 是 `degraded`，在那个方案下仍旧
  停在 `thin`——真正错的那一条反而漏掉了。

**改为怎么做到「判定与 join_confidence 一致」**：不是拒答，是**不许被读多**。
`paired_material` 新增 `n_evaluable_by_join_confidence`，让 `n_evaluable` 不能
被当成那么多条干净的腿读；产物新增顶层 `axis_caveat`，逐字带上轴的效度问题
（`freeze/RESIDUALS.json` `E2-AXIS` 的 `clears_when` 第 (b) 条要的就是这句话）；
每条腿的 `join_confidence` 照旧随数一起走，另加 `accounts_for_the_bill`。

**方向**：G6 只会把 `ok` 变成 `unsound`，不会把任何东西变回 `ok`。
`tier_of` 未动，`battery/artifacts/` 未动，§5 的四条约束全部照旧。

**代价**：`n_evaluable` 由 8 降到 7。`n_paired_games` 仍是 0，
`process_1_material` 的 `no-data` 裁定不因此改变——它从来不依赖条数。
