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
