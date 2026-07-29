# PREREG_V9 — 抗游戏审计的预注册（V9-battery-gaming-audit）

> 一个能被刷的指标，在论文里就是负资产。

本文件在**任何攻击结果产生之前**落盘并提交。它规定三件事，之后不得修改
（修改只能追加 `## 修订` 段并说明理由）：

1. **什么算「刷成功」**——每条指标一个数字门槛，写死在
   `battery/audit/v9/prereg.py` 的 `TARGETS` 里；
2. **什么算「没做真实工作」**——贫困证书（Poverty Certificate），
   由 `battery/audit/v9/check.py` 机械判定；
3. **裁决规则**——什么条件下降级、什么条件下才准升级。

可证顺序：本文件与 `battery/audit/v9/prereg.py` 的 commit 必须是攻击结果
commit 的祖先，用

```bash
git merge-base --is-ancestor <prereg-commit> <results-commit>
```

验证；命令与输出留痕在 `battery/runs/<UTC>-V9-battery-gaming-audit/`。

---

## 0. 本轮与既有 B14/B15 的关系

`battery/audit/gaming.py` 与 `battery/audit/exploits/` **已经存在**，B14 把主表从
19 条压到 6 条，B15 上了四道防御。V9 不是从零开始，V9 补的是那批工作**没有**的
三条纪律：攻击者当时看得见 `gaming.py` 的散文登记簿（里面逐条写明「设计时想防
什么」与「已知弱点」），因此测的可能是「照着提示找答案」；没有先写死成功判据；
防御的测试面与攻击面一样宽。

因此 V9 的攻击者一律**盲**（见 `battery/BLINDING.md`），且其攻击结果与既有
`exploits/` 的结论**分开记账**：两者一致是弱证据，两者不一致才是发现。

## 1. 成功判据

设指标 m 的方向为 d（`higher` / `lower` / `neutral`），攻击 A 构造出一个
`Run` 记作 `run_A`。**A 对 m 刷成功**，当且仅当以下三条同时成立：

* **S1 · 电池答了**：`evaluate(run_A)[m].status == "ok"`，且 `value` 非 None。
  电池拒答（`not-applicable` / `insufficient-data`）**不算刷成功**——那正是
  防御生效的样子。
* **S2 · 达标**：`value` 在方向 d 上达到或越过 `TARGETS[m]`：
  - `d == "higher"` → `value >= TARGETS[m]`
  - `d == "lower"`  → `value <= TARGETS[m]`
  - `d == "neutral"` → 见 §1.1。
* **S3 · 贫困证书通过**：`run_A` 的构造函数通过 §2 的机械检查。
  **S3 不过 = 不判定为「刷得动」**，无论分数多好看——分数好看而做了真实工作，
  证明的是指标有效，不是指标可刷。

三条缺一即 `succeeded = False`。**攻不动也是发现**，按 §3 记为「刷不动」并要求
攻击者写明为什么（那是这条指标的价值）。

### 1.1 neutral 指标（诊断项）的判据

诊断项不排座次，「更好」无定义，因此判据换成**可控性**：

攻击者须提交**两个**贫困证书都通过的 run，`A_lo` 与 `A_hi`，使得

* 两者的 `status` 都是 `ok`，且
* `value(A_hi) >= 10 * max(value(A_lo), 1e-9)`，或 `|value(A_hi) - value(A_lo)| >= 10`
  （两者取其一即可，处理值域贴近 0 的情形）。

成立即判「刷得动」：这个数字由攻击者随手设定，与世界无关。

**附加条款（诊断项的第二个身份）**：`gaming.py` 把若干诊断项写成了别的指标的
**防法**（"read it beside P5" / "read it beside X5" / "read it beside M1"）。
对这类指标，若攻击者能在**同一个 run** 上让被防的指标达标、而该诊断项读数保持
在「无害区」，也判「刷得动」，并额外记一条 `defence_defeated`。无害区由攻击者
在提交时声明并写进产物，不得事后调整。

### 1.2 `TARGETS` 的构造规则（先规则，后表）

表由规则生成，逐条写死在 `prereg.py`，不得事后微调：

| 值域 | 方向 | 门槛 |
|---|---|---|
| 有界 [0,1] | higher | `>= 0.95` |
| 有界 [0,1] | lower | `<= 0.05` |
| [-1,1]（X3） | higher | `>= 0.90` |
| [0,1] 且下确界为 0（E4/E7，嵌套模型之差非负） | lower | `<= 0.001` |
| 无界计数 | higher | `>= 100` |
| 无界比特（K6/K14） | higher | `>= 1000` |
| 无界比率/延迟 | lower | `<= 0.001` |
| P4（比率，最优 = 1.0） | lower | `<= 1.0` |
| P1（动作/调用） | higher | `>= 50` |
| P2（动作/调用之差） | higher | `>= 10` |
| neutral | — | §1.1 可控性 |

## 2. 贫困证书 —— 「没做真实工作」的机械定义

对抗复核会问的第一件事是「攻击者是不是其实做了真实工作」。为了让这个问题**可判**
而不是可辩，每个攻击必须是一个**零参数的构造函数**，且其源码须通过
`battery/audit/v9/check.py` 的四项机械检查：

* **C1 · 确定性**：连调两次，`dataclasses.asdict` 后逐字节相等。
* **C2 · 无外部输入**：AST 里不得出现 `open` / `Path` / `os` / `io` / `random` /
  `requests` / `urllib` / `subprocess` / `glob` / `json.load` / `time` /
  `datetime` / `input` / `__import__` / `eval` / `exec`，也不得 import
  `battery.adapters`、`battery.audit`、`battery.metrics`。
  （不能读账本，不能读产物，不能读被攻击的指标实现来自我调参。）
* **C3 · 无搜索**：函数体内不得出现 `while`，不得出现对自身的调用，
  不得调用白名单以外的任何名字。白名单只有：
  `range len str int float bool list dict tuple set sum min max sorted
  enumerate zip round abs divmod chr reversed` 加 `battery.model` 的
  数据类构造器（`Run Step Call Concept Clause Theory Beat Repair Truth`），
  以及方法名 `append extend join format keys values items`（纯容器/字符串拼装，
  不构成计算）。**推荐写法是列表推导**，它一个调用都不需要。
  含义：攻击只准**摆数据**，不准算东西。任何真正的规划、建模、搜索都会用到
  白名单外的名字，从而当场失效。
* **C4 · 无世界**：`Run.notes` 里不得携带任何键名含 `truth`/`optimal`/`solution`
  的自由数据被指标读到（`Truth` 数据类本身可以填，但填的是攻击者随手编的常数，
  这一点由 C3 保证——没有搜索就没有真解）。

**C3 是本轮最重要的一条，也是最容易被指摘的一条。** 它有已知的两面：
过严（一个合法的、确实不理解世界的攻击可能需要 `itertools`，此时攻击者须改写
成摆数据的形式）；过松（`sum`/`sorted` 原则上可以拼出一点计算）。两面都写在这里，
不在结果出来之后改。检查结果逐条入产物，包括**未通过的攻击**。

## 3. 裁决规则

沿用 `gaming.py` 的机械规则并加两条不对称约束：

```
gameable(S1∧S2∧S3) AND accidental AND NOT defended   ->  reference（参考项，不进主表）
otherwise                                            ->  main
```

* **R1 · V9 只降不升。** V9 的攻击结果**可以**把一条主表指标降为参考项；
  **不可以**仅凭「我攻不动」把参考项升回主表。升级要走工序 1（区分力），不走
  工序 4。理由：本工序测的是「能不能被刷」，不是「有没有分辨力」；用攻不动
  当升级理由，正是对抗复核第 (c) 条要打的循环。
* **R2 · 防御带来的升级要付两倍价。** 若 V9 为某条指标实现了防法，导致
  `tier_of` 把它算回 `main`，该防法必须同时满足：
  (i) 防法自身有测试；(ii) **攻击变异体数量严格多于测试数量**，且变异体覆盖
  防法条件之外的形态（不是「测了测过的」）。不满足则该指标在 V9 的裁决表里
  仍记 `reference`，并写明「防御未达 R2，留在参考层」。
* **R3 · 降级要有证据。** 每条降级必须指向一个**跑过的** run 与它的**实测值**，
  并附贫困证书结论。没有实跑的降级不写进裁决表——散文登记簿的判断不算数。
* **R4 · 攻不动要给理由。** 判「刷不动」的每一条，攻击者须写明**是什么结构**
  挡住了攻击（哪一行代码、哪一个 `needs`、哪一条 `thin()` 分支），而不是
  「我没想到办法」。理由写不出来的，记 `undetermined`，不记 `not-gameable`。

## 4. 方向性预测（本轮，写在看结果之前）

1. **主表 9 条里至少 3 条会被盲攻击刷动。** 现主表为
   `E2 E3 K7 K11 K12 M3 M6 P3 P4`。
2. **盲攻击与既有 `exploits/` 的结论会在至少 5 条上不一致。** 若完全一致，
   说明盲化没起作用（或既有审计确实充分），两种解释我在结果里必须分开写。
3. **`K12` 会被刷动。** 它的分母 `beats_required` 由适配器设成 6，但 `beats`
   列表由数据源提供，摆 6 个 `closed=True` 的 Beat 无需任何修复回路。
   （这条是我作为汇总者的预测，我不把它告诉任何攻击者。）
4. **`M3` 与 `K7` 会「刷不动」，但理由是不可计算而不是稳健**——它们在现有材料上
   几乎没有 run 能触发。若攻击者能构造出 run 让它们答话并达标，预测被推翻。
5. **`P4` 的 `won` 闸挡得住旧攻击，挡不住新攻击**：`won` 是 `Step` 上的一个布尔，
   摆上去即可。

以上五条预测的对错，逐条写进 `battery/audit/v9/REPORT.md`，**包括我错的那些**。

## 5. 不做什么

* 不打网络、不碰 `.env`、不读封存堆（`battery/guard.py` 的护栏照旧生效）；
* 零 API 花费；
* **不修改任何已提交产物**：`battery/artifacts/` 不重写，`gaming.py` 的
  `GAMING_REGISTER` 散文条目不删改（V9 的结论另开文件，冲突留在明面上）；
* 已登记的「裸跑 `run_battery` 会覆盖 `battery/artifacts`」问题**不顺手修**，
  撞到就记一笔。

---

*预注册人：V9 汇总者（RES-3 派出）。落盘时间见本文件的 commit。*
