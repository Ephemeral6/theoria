# ADVERSARIAL · 对 V18 冻结前复核的对抗复核

被审对象：本目录 `REVIEW_TABLE.md` 与 `ENDPOINTS.md`，**版本 `c43ad74`**
（"battery V18: three self-corrections found before the adversary got to them"，
2026-07-29 11:09:58 +0800）。V18 在本复核进行期间自我更正过一次；下文所有指控都对
`c43ad74` 这一版成立，第 1 节明确记下哪几条被它抢先修掉了。

工作纪律：零 API、零网络、未读 `.env`、未接触封存堆任何游戏材料。只写本文件。
所有临时脚本在 scratchpad，未落进 `battery/`。

判决取值：`推翻 / 部分推翻 / 站得住 / 查不出`。

---

## 0. 总判决

| 指控 | 判决 |
|---|---|
| (a) 「70 条仍与当前定义完全对应」 | **部分推翻**——V18 自己的 §6 把 V9 的 D1/D2/D3 定性为口径变更，§3/§4/§7 却一条都没登记；另有纯算术错，`70` 由它自己的表算出来是 `68` |
| (a) direction / `MIN_TURNS` / `polyfit_r2` / `45169a6` / `efc21d1` | **站得住**——V18 在 `c43ad74` 里抢先查完了，且结论与我独立复核一致 |
| (b) 「85/87 可证伪」 | **部分推翻**——判据 0.3 少了一条。X3、P2、K7 三条我各造出一个**满足预测且零能力**的臂，全部落地 |
| (c) 漏报 | **推翻**——**至少 4 条预测已被盘上现存数值证伪，`REVIEW_TABLE.md` 一条都没报**，其中 K7 与 M5 的证伪值恰好就是 V18 自己写下的那个反例值 |
| (c) 87 这个数 | **部分推翻**——总数可辩护，但 §3 小计 17/17、§7 的标注分项、可证伪 85 三处算术不自洽 |
| (c) O-4 指控 | **部分推翻**——**这条指控应当降格**，不应计入「未声明的先验知识 = 1」 |
| (c) 三主终点裁决 | **部分推翻**——判决题一条要改（`exam/` 里有可执行的方向预注册且带硬阻断）；U3 一条的「落点」断言查实为假 |

---

## 1. 先说 V18 抢先修掉的（站得住，不重复指控）

`c43ad74` 新增的 §3a / §3b / §6a / §6b 独立命中了本工单 (a) 里的四项。我做了同样的
检查，结论一致，**不再作为指控**：

* **`direction=` 从未改过。** 我的独立复核（逐 commit 解析 `@metric(...)`）：
  ```
  for c in 0be176c e82558b 5f85971 520dc5d HEAD; do
    git grep -h -oP '@metric\("\K[A-Z]\d+|direction="\K[a-z]+' $c -- battery/metrics/ | paste - -
  done
  ```
  `0be176c` 29 条、其后 38 条，方向变更 **0 处**。V18 §6a 第三行正确。
* **`45169a6` 与 `efc21d1` 都没动 `battery/metrics/`。**
  `git show --stat 45169a6` / `efc21d1` 证实：前者 12 个文件全在 `audit/` `tests/`
  `artifacts/` `METRICS.md`；后者 14 个文件，`METRICS.md` 只动 8 行，全是 tier
  归属（`E1` main→reference、`M3` main→reference、主表 2→0）。**工单预设的
  「`efc21d1` 又动了口径」不成立，查不出，因为它一行指标体都没碰。**
* **`MIN_TURNS_FOR_SHAPE = 8` / `polyfit_r2` 从未变过。**
  `git show 0be176c:battery/metrics/economy.py | grep -n MIN_TURNS_FOR_SHAPE` → 第 35 行，
  首次实现即为 8，其后三次改动均未触及；`polyfit_r2` 函数体 `0be176c` 与 HEAD
  **逐字节相同**（`git log -S"def polyfit_r2"` 只有一个 commit）。V18 §3b 已登记。

**一处附带发现，不算指控但冻结前该修**：`battery/METRICS.md:35` 把 **M3 列在
`Reference (38)` 里**，而 `v9_gaming_audit.json` 的 `verdict.undetermined = ["M3"]`、
`efc21d1` 的 commit message 也写「M3 moves from `main` to a new `undetermined`
tier」。**生成的文档与生成它的裁决artefact在 M3 的 tier 上不一致**，而
`METRICS.md` 开头声称 `tests/test_docs.py` 会在两者不一致时失败。这是 V9/`docs.py`
的账，不是 V18 的，但 V18 §0.4 依赖的正是这个 tier，登记。

---

## 2. 指控 (a)：口径 —— **部分推翻**

### 2.1 V18 §6 与 §3/§4/§7 自相矛盾（主指控）

`REVIEW_TABLE.md:265-267` 白纸黑字：

> V9 的 D1/D2/D3 在**全部四批预注册之后**（`520dc5d`，2026-07-29T10:11）给 12 条指标
> 加了拒答路径：D1 → K1/K2/K4/K8/K12/M6，D2 → M1/M4，D3 → E1/E2/E3/E5。
> **这是口径变更。**

我核过这 12 条，属实。`git show 520dc5d --format='' -- battery/metrics/` 显示
`unsound()` 拒答分支被插进：

| 指标 | 新增拒答条件 | 文件:行（HEAD） |
|---|---|---|
| E1 / E2 / E3 / E5 | `_unpriced(run)` 非零即拒 | `battery/metrics/economy.py:55-70, 93-96, 130-134, 153-157, 205-209` |
| K1 | `agree < 0 or agree > pairs` | `battery/metrics/epistemic.py:35-40` |
| K2 | 同上 | `epistemic.py:75-77` |
| K4 | `coverage_num > coverage_den` | `epistemic.py:100-105` |
| K8 | `executable > designed` | `epistemic.py:168-171` |
| K12 | `closed > required` | `epistemic.py:264-271` |
| M1 | `min(delays) < 0` | `battery/metrics/mechanism.py:41-47` |
| M4 | 同上 | `mechanism.py:118-120` |
| M6 | `invalidated > theorems_before` | `mechanism.py:174-183` |

而 `REVIEW_TABLE.md` §0.1 的 D 判据是：「该指标自预测写下之后，其**计算规则**没有
变；变过则记 `口径已变`」。一条新增的拒答分支，就是计算规则的变化——**V18 §6 自己
就是这么定性的**。

**但 §3 的表里，这 12 条中的 8 条一个 D 都没拿到**：

| 指标 | §3 的「对应」列（`REVIEW_TABLE.md` 行号） | 应为 |
|---|---|---|
| K4 | `:135` 「同名；V9-D1」→ **对应** | 标注·D |
| K8 | `:139` 「同名；V9-D1」→ **对应** | 标注·D |
| M4 | `:145` 「同名；V9-D2」→ **对应** | 标注·D |
| M6 | `:147` 「同名；V9-D1」→ **对应；`neutral`** | 标注·D |
| K1 | `:132` 「同名；V9-D1 加一致性拒答」→ 标注·**A** | 标注·A**+D** |
| M1 | `:129` 「同名；V9-D2 加了负值拒答」→ 标注·**A** | 标注·A**+D** |
| E5 | `:128` → 标注·**A**（V9-D3 完全未提） | 标注·A**+D** |
| E1 | 34 条表里无 E1 行（v0/v1 未预测 E1），但 §4 的 38 条里有 | 见下 |

**V18 把 V9 的改动写在「今天的名字」那一列里，然后在「对应」那一列判它对应。**
一条指标的名字没变、口径变了，按它自己的 §0.1 就该记 `标注·D`。§7 的
「D 口径已变 **6**（X4、E2、E3、P4、K2、K12）」漏掉了 K1、K4、K8、M1、M4、M6、E1、E5
**八条**。

### 2.2 §4 的 38 条 v2 预测，D 判据一次都没跑

`REVIEW_TABLE.md:217`：「**对应**：38 条全部点名今天仍存在的指标 id，**无 N 类问题**」
——只查了 N，没查 D。

v2 预注册 `19eafb2` 是 2026-07-28 14:20。我验过祖先关系：

```
git merge-base --is-ancestor 19eafb2 5f85971   # 0
git merge-base --is-ancestor 19eafb2 520dc5d   # 0
```

即 v2.1（`5f85971`，15:07）与 V9（`520dc5d`，次日 10:11）两轮口径变更**全部发生在
v2 预注册之后**。受影响的指标并集：

`{E2, K2, K12, P4}` ∪ `{E1, E2, E3, E5, K1, K2, K4, K8, K12, M1, M4, M6}`
= **13 条**：E1、E2、E3、E5、K1、K2、K4、K8、K12、M1、M4、M6、P4。

**§4 的 38 条里至少 13 条应记 `标注·D`，V18 全部判为「对应」。**

### 2.3 「70」这个数，按 V18 自己的表算出来是 68，再扣完是 ≤ 51

**先是纯算术。** §3 的表（`REVIEW_TABLE.md:117-150`）共 34 行，逐行数：

* 标记 `标注` 的：X1 X2 X3 X4 P1 P2 P3 P4 E2 E3 E4 E5 M1 M2 M3 K1 K2 K5 K12 = **19 行**
* 标记 `对应` 的：K3 K4 K6 K7 K8 K9 K10 X6 E6 E7 M4 M5 M6 K13 K14 = **15 行**

19 + 15 = 34 ✓。而 `REVIEW_TABLE.md:209` 的小计写的是「对应 **17**；标注 **17**」。
§7 自己的分项也对不上：A 类 11 + D 类 6（E2/E3 的 N 与其 D 重叠）+ D′ 1 + D″ 1
= **19**，不是 17。

于是 `REVIEW_TABLE.md:317`「仍与当前定义完全对应 **70**」应为 **68**（15 + 38 + 15）。

**再是实质扣减**，按 §2.1 与 §2.2：

| | 数 |
|---|---|
| V18 报的 | 70 |
| 按它自己的表更正算术 | 68 |
| 扣 §3 里 K4/K8/M4/M6 四条（口径已变仍判对应） | 64 |
| 扣 §4 里 13 条（v2 预注册后口径变更） | **51** |
| （若一并扣 §5 里 E2/K2/K12 相关的 9 条——V9-D1/D3 在 `58e5f6b` 之后仍改了这三条） | 42 |

**「70 条仍与当前定义完全对应」这个数不能进冻结说明书。可辩护的上界是 51。**

### 2.4 查不出的

* **`efc21d1` 有没有再动指标口径** → **查不出，因为它一行 `battery/metrics/` 都没碰**
  （`git show --stat efc21d1`）。它改的是 tier 与裁决规则。
* **`45169a6`** → 同上，只动 tier（主表 19→6）。
* **`thin()` 门槛 / `polyfit_r2` / `direction=`** → 见 §1，全部未变，V18 已自查。

---

## 3. 指控 (b)：可证伪性 —— **部分推翻**

V18 的 §0.3 只有三条：F1（有指标算得出）、F2（**写得出一个让它算错的取值**）、
F3（在所述臂上能算出 `ok`）。

**F2 只问「有没有一个值能让它错」，不问「有没有一个零能力的臂能让它对」。**
这两件事不是同一件事。一条预测若能被一个**明显没有任何能力的臂满足**，它即使可证伪
也**无信息**——它不是在测能力，它是在测一个跟能力无关的形状。

我按工单指定的三条各造了反例臂。构造只用 `battery.model` 的构造器 + 列表排布，
喂给 `battery.metrics.evaluate`，无搜索、无外部输入（与 `battery/audit/v9/attacks/`
同一写法）。**三条全部落地。**

复现（把下面的 builder 存成任意 `.py`，在 worktree 根跑）：

```python
import sys; sys.path.insert(0, r"C:\Users\user\Desktop\theoria\.worktrees\v18-battery-prereg-check")
from battery.model import Run, Step, Call, Concept, Theory
from battery.metrics import evaluate
```

### 3.1 X3 `novelty_frontload` —— V18 夸它「这条写得最好」

预测（v0）：`theoria > schema ≈ bare_cc`，反例判据「曲线不塌 = 理论从未闭合」。

**反例臂：撞墙卡死的臂。** 前 8 步各走一个新格（全部首见），后 24 步顶着一堵墙
重复同一个动作、停在同一个 state：

```python
def build_X3_stuck_in_a_corner():
    steps  = [Step(idx=i, action="a%d" % i, state_key="s%d" % (i+1)) for i in range(8)]
    steps += [Step(idx=i, action="bump",    state_key="wall")        for i in range(8, 32)]
    return Run(run_id="adv-X3-stuck-in-a-corner", arm="attacker",
               source="adversarial", steps=steps)
```

实测：

```
X3   status=ok   value=1.0    support={'first_quarter': 1.0, 'last_quarter': 0.0, 'transitions': 32}
X1   status=ok   value=0.71875     X4   status=ok   value=0.71875     X5   status=ok   value=9.0
```

**X3 = 1.000，理论最大值**，来自一个 24 步一动不动、没赢、没学到任何东西的臂。

**意外版（accidental，不需要任何恶意）**：API 在跑到一半开始 500，harness 把重试
写成了 ledger 行：

```python
def build_X3_crash_tail():
    steps  = [Step(idx=i, action="move%d" % i, state_key="t%d" % i) for i in range(12)]
    steps += [Step(idx=i, action="move11",     state_key="t11")     for i in range(12, 40)]
    return Run(run_id="adv-X3-crash-tail", arm="attacker", source="adversarial", steps=steps)
```
→ `X3 = 1.0`（`first_quarter 1.0 / last_quarter 0.0 / transitions 40`）。

**结论：X3 分不开「理论闭合了所以不再意外」和「跑崩了所以在原地打转」。**
两者产生**逐字相同**的 X3。V18 引以为最好的那个反例判据（「曲线不塌」）只堵住了
一个方向：**曲线塌下来这件事，一个死掉的臂做得比一个懂了的臂还漂亮。**
判决：**X3 可证伪，但可满足且无信息。**

### 3.2 P2 `actions_per_call_trend` —— V18 说「判据写在预测里」

预测（v0）：`theoria > 0`，`schema ≈ 0`，`bare_cc ≈ 0`。

**反例臂：写死的批量时刻表。** 前 10 次调用各 1 个动作，后 10 次各 9 个动作；
每一个动作都是同一个 `press`，打在同一个冻结的盘面上：

```python
def build_P2_batch_schedule():
    steps, calls, idx = [], [], 0
    for c in range(10):
        calls.append(Call(idx=c, step_idx=idx, cost_usd=0.01))
        steps.append(Step(idx=idx, action="press", state_key="frozen")); idx += 1
    for c in range(10, 20):
        calls.append(Call(idx=c, step_idx=idx, cost_usd=0.01))
        for _ in range(9):
            steps.append(Step(idx=idx, action="press", state_key="frozen")); idx += 1
    return Run(run_id="adv-P2-batch-schedule", arm="attacker",
               source="adversarial", steps=steps, calls=calls)
```

实测：

```
P2   status=ok   value=8.0   support={'first_rate': 1.0, 'second_rate': 9.0, 'basis': 'step_idx'}
P1   status=ok   value=5.0        P3   status=ok   value=1.0 (undos 98/98)     P5   value=0.0
```

**P2 = +8.0**，来自一个盘面从未改变、100 步全是同一个动作的臂。

**意外版**：限流。客户端跑到一半开始合并动作以压住配额，臂本身一个字没变：

```python
def build_P2_rate_limit_coalesce():   # 8 次 ×1 动作，然后 8 次 ×4 动作
    ...
```
→ `P2 = +3.0`。

**这同时打掉 `METRICS.md:82` 给 P2 记的那条「已实现」防法**：

> *Defence:* An *increasing* batch size is a deliberate schedule; **a harness that
> batches does so at a constant rate, which cancels in the difference.** (implemented)

一个**中途改变批量速率**的 harness——限流、退避、上下文压缩，全都会——就把这条防法
的前提直接证伪。它不是实现了的防法，它是一个未经检验的假设。
判决：**P2 可证伪，但可满足且无信息；且其登记为 `implemented` 的防法前提为假。**

### 3.3 K7 `negative_gain_concepts` —— V18 说「本文件最好的一条」

预测（v0）：`theoria > 0`，且**这是预期而非缺陷**。

**反例臂：一本只写了一个词、这个词还不划算的说明书。**

```python
def build_K7_one_bad_word():
    return Run(run_id="adv-K7-one-bad-word", arm="attacker", source="adversarial",
               steps=[Step(idx=0, action="press", state_key="a")],
               theory=Theory(concepts=[Concept(name="Thing", compression_bits=-1)]))
```

实测：`K7 = 1.0`（`of_concepts: 1`）、`K5 = 1`、`K3 = 0`、`K10 = 0`、`K9` 拒答。
**没有定理、没有子句、没有探针、没有 playbook，K7 的预测照样满足。**

更糟的是**反向不对称**。V18 说「一个 0 值就把 O-04 冲突判为 A0 的偶然」——但那个 0
最廉价的臂**拿不到**：

```
build_K7_empty_manual()        (0 个概念)              → K7 insufficient-data
build_K7_unaccounted_manual()  (500 个概念，全无账目)  → K7 insufficient-data
```

即：**满足这条预测只要 1 个负数概念；证伪它却要求一本至少给每个概念都算了账、且每
一笔都为正的说明书。** 廉价的臂只能确认，不能证伪。这是一条单向的预测。

（顺带：V9 的 `K7/silence` 攻击已经证明反面同样可刷——400 个概念里 399 个不填账目，
K7 = 0，`v9_gaming_audit.json` → `verdict.metrics.K7.attacks[1].low_value = 0.0`。
**K7 的两个方向都能由「标注工具坏了」而不是「理论好不好」决定。**）

判决：**K7 可证伪，但可满足且无信息。**

### 3.4 判据 0.3 缺的那一条

三条全中，且两条（X3 撞墙、P2 限流）的意外版本不需要任何恶意，只需要一次超时。
**V18 的判据 0.3 少了一条，应补：**

> **F4** 不存在一个**明显不具备该预测所指能力**的臂，能使这条预测成立。
> F4 不过 = **`可满足但无信息`**——它可证伪，但它的成立不构成证据。

按 F4 重判，「可证伪 85」这个数不能单独出现在冻结说明书里，因为 85 里已经确证有
**至少 3 条**是可满足但无信息的（X3、P2、K7），而这三条恰是 V18 亲手挑出来当范本的
三条。**范本不合格，说明这个数不是 85 里的少数派问题。**

---

## 4. 指控 (c)：漏报、降级、过度指控 —— **推翻（主）+ 部分推翻**

### 4.1 主指控：**至少 4 条预测已被证伪，§3 一条都没报** ← 最重

`REVIEW_TABLE.md` §5（v2.1）有 **实测** 一列。**§3（34 条臂梯度预测）没有这一列。**
全文只承认两条证伪（X6、K14），且两条都是预注册或 `REPORT_V1.md` 早已自报的。

我去查了盘上现存的 artefact。**下面每一条都是 V18 自己在同一行里写下的那个反例值，
而它没去看那个值。**

#### (i) M5 `change_detection_rate` —— 被自己写下的天花板判据翻掉

V18 `REVIEW_TABLE.md:146`：

> **可证伪，天花板是判据**：预测 `< 1.0`，**1.0 即错**

实测（`battery/artifacts/capability_spectrum.json`）：

```
a0-spike   arm=theoria_a0_spike   M5 = 0.75   {'detected': 3, 'episodes': 4, 'undetected': ['nocross']}
a2-probed  arm=theoria_a2         M5 = 1.0    {'detected': 1, 'episodes': 1, 'undetected': []}
```

v1 的预测是 ``theoria > 0.5`` 但 ``< 1.0``，没有限定哪个 theoria 臂。
**`a2-probed` 上 M5 = 1.000。按 V18 自己写的判据，这条预测在盘上已经被证伪。
V18 的「对应」列判它 `对应`，可证伪性列判它「可证伪」，实测——没有实测列。**

#### (ii) K7 —— 同上，而且是同一个 run 上 V18 已经用过的那个证据

V18 `:150` 对 K14 写：「**已在 v1 被证伪**（**单概念说明书**上翻掉）」。
它指的是这个 run：

```
a0-no-button   arm=theoria_a0   source=cold-start-a0
   K5 = 1.0        K6 = 1001.0     K14 = +1001.0 (worst_concept 'Cart')
   K7 = 0.0        of_concepts = 1
```

**同一个 run，同一本单概念说明书，K7 = 0.000。**
而 V18 `:138` 对 K7 写的是：「**可证伪，且是本文件最好的一条**……**一个 0 值就把
O-04 冲突判为 A0 的偶然**」。

**那个 0 值就在盘上，在 V18 已经打开过、并且据以宣告 K14 被证伪的那一个 run 里。
V18 报了 K14 的证伪，漏了 K7 的。**（a0-base / a2-probed / a2-play-record / a2-sweep
上 K7 = 2，a0-spike 上 `insufficient-data`。所以严格说是「theoria 臂上并非
一律 > 0」——这正是 K7 那条预测所声称的东西。）

#### (iii) X1 与 (iv) X2 —— `separates-against`，且 `REPORT_V1.md` 早就印出来了

V18 `:117` 对 X1 写：「可证伪（**theoria ≥ bare_cc 即错**）；schema 分支不可判定」。

实测 `battery/artifacts/arm_contrast.json`：

```
X1   theoria_median = 0.781   bare_cc_median = 0.282   d = +0.361   verdict = "separates-against"
X2   theoria_median = 0.869   bare_cc_median = 1.000   d = -0.573   verdict = "separates-against"
X4   theoria_median = 0.0737  bare_cc_median = 0.0625  d = +0.041   verdict = "no-effect"
P3   theoria_median = 0.0946  bare_cc_median = 0.0     d = +0.068   verdict = "no-effect"
X3   theoria_median = 0.140   bare_cc_median = 0.0     d = +0.592   verdict = "separates"   ← 唯一成立的
```

* **X1**：v0 预测 `bare_cc > schema > theoria`（direction lower，theoria 应最低）。
  实测 theoria 是 bare_cc 的 **2.8 倍**。**V18 写下的证伪条件「theoria ≥ bare_cc」
  已经被满足，它没说。**
* **X2**：v0 预测 `theoria > schema > bare_cc`（direction higher）。实测 bare_cc 更高。
  **证伪。** V18 `:118` 只写了「短跑自动得 1.0 已被 v0 自己记为缺陷」——把一条**已经
  翻掉的**预测，写成了一条**有已知缺陷的**预测。
* **X4、P3**：方向同样反着走，只是效应量可忽略。**未获证实**，V18 均无实测。

**而这两条不是我挖出来的隐蔽结论**——`battery/REPORT_V1.md:41` 与 `:43` 就是一张表：

```
| X2 | exploration | −0.765 | 6 vs 17 | 0.869 vs 1.000 | separates **against** |
| X1 | exploration | +0.637 | 6 vs 17 | 0.781 vs 0.143 | separates **against** |
```

V18 在别处引用过 `REPORT_V1.md`（§5 那条「已经带 frame 是假的」）。**这份报告它读过，
两条 `separates against` 没有进复核表。**

**要写的公道话**：`arm_contrast.json` 每一条都带 `confounded_by_world: true`——theoria
的 6 个 run 全在自建世界、bare_cc 的 71 个全在 ARC 上。所以这些证伪是**被世界混淆
的**。但 V18 不能两头占：它在「可证伪性」列判 X1「**可证伪**」（即 F3 过），就等于
承认这个量在所述臂上算得出 `ok`；算得出、算出来了、方向反了，那就得报。要么把 X1
改判「F3 不过，因为臂与世界不可分」，要么报出证伪。**现在这一版两样都没做。**

#### 小结与结构性成因

**§3 少了一整列。** §5（v2.1，15 行）有 `实测`；§4 有整批的实测概述；**§3 的 34 行
一格实测都没有。** 于是「可证伪」被当成了终点，而工序 2 的终点是「证伪了没有」。

按盘上现存数据，34 条臂梯度预测的实测应至少是：
**证伪 4（X1、X2、K7、M5）+ 已知证伪 2（X6、K14）+ 成立 4（X3、M4、K13、P4）+
未获证实 2（X4、P3）+ 其余不可判定。**

### 4.2 有没有把预测标成「不可判定」来回避证伪？—— **有，两处**

* **X1**（`:117`）：「可证伪（theoria ≥ bare_cc 即错）；**schema 分支不可判定**」。
  一句话里既写出了证伪条件，又把注意力引向那个永远判不了的分支。**能判的那半判了，
  而且翻了；不能判的那半被拿来当整行的注脚。**
* **K1**（`:132`）：判「**可证伪，当前不可判定**（schema 侧永远 N/A）」。但 v0 的 K1
  预测是复合的：`schema ≈ theoria`，**且 both `> 0.95`**。后半在 theoria 侧完全
  判得了：a0-base 0.987、a0-no-button/a0-spike/a2-* 均 1.0，**成立**。
  这一次结论对预测有利，V18 一样没报。所以这不是偏袒，**是同一个结构缺陷：
  复合预测被整行归一，能判的那半被整行的不可判定吞掉。**

### 4.3 过度指控：O-4 —— **这条指控应当降格**

V18 `:96` 把 v2 的 E2 预测记为整份复核里**唯一一条**「未声明的先验知识」，
`:315` 计为 `1`。我认为**这条不成立为「未声明」，应当撤出该计数**，理由三条，全部
可查：

1. **它声明过，只是不在 v2 的封条段里，而在同一作者 12 小时前的已发布报告里。**
   `battery/REPORT_V0.md:74-82`，独立一节，标题就是
   **「The front-load index has a confound worth worrying about」**：

   > Within `bare_cc`, on this pilot, **the more capable model front-loads more** —
   > haiku 0.20, sonnet 0.25, opus 0.28, δ = +1.000 in the declared direction. No
   > arm here has a theory. If capability alone produces front-loading, then
   > front-loading is not specific to *having a theory*, and C2's evidence weakens…

   同一段还进了 `0be176c` 的 commit message（V18 自己引了）。
   **预注册透明度要求的是「这件事在做预测之前已经在案」。它在案，而且在案的形式
   是一份带小标题的公开报告，外加一条 commit message，外加 `REPORT_V0.md:140` 把它
   列为下一轮第 2 项待办。** 「未声明」三个字与这个事实不符。

2. **两条梯度不是同一条，而且已知的那条指向的是预测会失败。**
   模型阶梯（haiku→sonnet→opus，harness 固定、三臂皆无理论）与 CC-vs-Schema 是两条
   不同的梯度。已知「能力本身就前载」，再加上封条里已声明的「Schema 是 98.98 的
   SOTA、bare_cc 是一次性 CLI 基线」，**推出来的应当是「E2 会分开 CC 与 Schema」**。
   而 v2 注册的是「**不分开**」。
   **先验知识条款存在的目的，是防止预测者靠已知答案白拿信用。这里已知的东西让注册
   的预测更难成立，不是更容易。没有可白拿的信用，就没有这条条款要防的害。**

3. **V18 自己已经写下了这个有利读法（`:106`），却仍把它计入违规栏。**
   `:102` 说「本表两种读法都写下来，不替任何一种辩护」，然后 `:315` 的合计表把它
   记成 `未声明的先验知识 = 1`。**读者只会带走那个 1。** 合计表与正文的中立姿态
   互相矛盾，而合计表是会被抄进冻结说明书的那一个。

**建议改判**：从「未声明的先验知识」移到一条新的登记项——
**「已在别处公开声明，v2 封条段未复述（`REPORT_V0.md:74-82`；且已知证据指向预测
失败）」**，`未声明的先验知识` 计数归 **0**。
§3d（`ENDPOINTS.md:158-162`）关于「反例已在模型阶梯上被满足」的实质裁决**不受影响，
站得住**——那是一条独立且正确的判断，`discrimination.json` 的 E2 条目（d = 1.000、
4 胜 0 负 0 平、`agrees_with_declared_direction: true`、`verdict: underpowered`）
我逐字复核过，属实。

### 4.4 三主终点：判决题一条要改，U3 一条的「落点」是假的

我委派了一次只读的全仓搜索（`exam/` 166 个文件、`proxy/` 68 个文件全量枚举，
仓库级不分大小写 grep：`U3` `达成率` `attainment` `判决题` `specificity` `特异度`
`sensitivity` `预注册` `prereg` `PREDICTION` `hypothes`）。

**(A) 判决题准确率（含特异度）—— `ENDPOINTS.md:54` 判「不可证伪（F1、F2 均不过）」，
应改为「部分成立」。**

`exam/grading/calibration.py` 里有**可执行的、带硬阻断的方向预注册**：

* `calibration.py:33` —— 「The expectations below are **pre-registered**: bands
  written down as part of the protocol, not fitted to what the fakes turned out
  to score.」
* `:118-120` —— `("verdict", "bluffer"): Band(0.0, 0.50, "always answering
  \`unsolvable\` buys perfect sensitivity and zero specificity; the score must
  reflect the pair, not the sensitivity")`
* `:130-131` —— `"verdict_bluffer_pair": ("the bluffer must show sensitivity 1.0
  and specificity 0.0")`
* `:286-292` —— 执行：`if sens != 1.0 or spec != 0.0: failures.append(...)`
* `:39` —— 「**A failed calibration blocks real grading.**」

**F2 明确成立**：「写得出一个让它算错的取值」不但写得出，而且写成了一行断言，
算错就阻断真实评分。`exam/DECISIONS.md:153`（D-EX-010，一条预注册的 band 在首次
接触时被证伪并被替换而非放宽）独立证明这些 band 确实先于数字。

另有一处跨臂方向预注册：`ablation-arm/DESIGN.md:235` 的 `## 8 · 预注册(方向先于结果)`
下，`:245` P-5、`:246` P-6，并在 `:256` 明确按 `Theoria.md:259` 的三类判决题组织
「灵敏度与特异度一起打分」，`:280` 点名了第 (iii) 类特异度失败的最坏形态。
祖先关系已验（`DESIGN.md` 在 `5959a80`，`verify.json` 在 `b4b8425`，
`--is-ancestor` 退出码 0）。

**这些不足以救回这个主终点**——calibration 的 band 管的是四个**合成假考生**
（oracle / null / memoriser / bluffer），P-5/P-6 管的是消融臂上两个手工构造的展品
（各 n=1）；**没有任何一处预注册三臂在一份真实考卷上的准确率与特异度，全仓也不存在
任何形如「specificity > 0.9」的数值门槛。** 但 V18 那句
「**F2 不过。无预测，无反例**」（`ENDPOINTS.md:65`）**是错的，必须改**。
正确的写法是：**「电池侧确认没有；`exam/` 侧存在方向预注册，但其作用域是标定假考生
与消融展品，不是主终点所要的跨臂准确率」**——V18 自己也写了「本复核只做了目录与
关键词层面的检查，没有逐文件读」（`:77`），那句诚实的免责现在有了结果，应当兑现。

**(B) U3 达成率 —— 裁决站得住，但 `ENDPOINTS.md:43` 那句「落点」查实为假。**

V18 写：「**落点在哪里（已独立查实）。** U3 达成率由 U 阶梯打分器算，落点
`proxy/scoring/`」。

实测：`grep -rn -i -E "U1|U2|U3|U4|ladder|attain|达成|证得|阶梯" proxy/` **零命中**。
`proxy/scoring/` 只有 `__init__.py`、`__main__.py`、`arc_v1.py`、`frozen.json`，
而 `proxy/SCORING.md:37-38` 明写它「publishes **the scorecard's own numbers**…
does **not** reimplement the ARC-AGI-3 percentage」。**`proxy/scoring/` 里没有 U 阶梯
打分器，「已独立查实」这四个字用错了地方。**

全仓唯一被机械化的 U 阶梯评估在 `ablation-arm/verify.py:176`（`u3_blocked = …`），
其方向预注册是 `ablation-arm/DESIGN.md:247` 的 **P-7「U 阶梯封顶 U2，是构造性的」**
——一条**单臂的构造性上限**，不是达成率，没有分母。
另：`Theoria.md:357` 的退出条件门槛 `⟨k⟩` 至今未绑定（`Theoria.md:383` 把它列进
冻结时才定的五项），`theoria-arm/runs/20260728T233900Z-A3-campaign-devpile/
EXIT_CONDITION.md:36-37` 独立记下「Theoria.md gives **no per-game rubric** for
scoring U3」。

**所以「U3 达成率从未被预注册过」这个结论站得住，但支撑它的那句落点断言要撤，
并应补上 P-7 这条唯一相关的方向预注册（它不满足主终点的要求，但存在）。**

### 4.5 87 这个数

* **总数可辩护。** v0 25 + v1 9 + v2 38（6+5+7+6+14）我独立数过，对。
  v2.1：`awk '/^# v2.1/,0' battery/PREDICTIONS.md | grep -c "Prediction:"` = **10**，
  加 5 条编号聚合 = 15。与 V18 `:313` 的推导一致。
* **但 §5 的表与这个 15 对不上。** §5 有 15 行，其中 **2 行不是预测**（第 3 行
  「P4 命名风险……不是预测，是自陈代价」、第 5 行「K2 适配器声明……自报缺陷」），
  而第 15 行把**聚合 3、4、5 三条预测压成了一行**。
  → 15 行 = 13 条预测 + 2 条非预测；加上被压掉的 2 条 = **15 条预测 + 2 条非预测
  = 17 条陈述**。
  于是 §7「非预测（自陈代价）**1**」少算一条（应为 2），
  「可证伪 **85**（33 + 38 + **14**）」的 14 应为 **13** → **84**。
* **另一处应当声明的口径**：多条预测是**复合**的，V18 一律按一行一条计
  （E5 的「整体 + 首四分位反转」、P4 的「排序 + 1.5× 以内」、K1 的「≈ + both > 0.95」、
  K2 的「theoria > schema + both < K1」、X6 的「> bare_cc + bare_cc < 0.5」、
  K13 的「a2 < a0_spike + a2 < 0.3」、M5 的「> 0.5 + < 1.0」）。
  **87 是「行数」，不是「可独立判真伪的陈述数」**，冻结说明书里应当这样写，
  否则 §4.2 那种「整行被不可判定吞掉」会继续发生。
* **没有任何一条预测被静悄悄漏掉。** 我逐条比对过：v0 的 25 条（X1–X4、P1–P4、
  E2–E5、M1–M3、K1–K10）与 v1 的 9 条（X6、E6、E7、M4、M5、M6、K12、K13、K14）
  在 §3 表里**一行不缺**。这一条 **V18 站得住**。

---

## 5. V18 必须改的地方

按严重程度排。

1. **给 §3 补 `实测` 一列，并报出已在盘上的证伪。**
   最少四条：**M5（`a2-probed` = 1.000，撞上 V18 自己写的天花板判据）**、
   **K7（`a0-no-button` = 0.000，撞上 V18 自己写的那个 0 值）**、
   **X1（`separates-against`，theoria 0.781 vs bare_cc 0.282）**、
   **X2（`separates-against`，0.869 vs 1.000）**；X4 与 P3 记「未获证实，方向相反」。
   来源：`battery/artifacts/capability_spectrum.json`、`battery/artifacts/arm_contrast.json`、
   `battery/REPORT_V1.md:41,43`。若认为世界混淆使这些读不得，就必须把 X1/X2 的
   F3 改判为不过，**不能既判 F3 过又不报结果**。

2. **把 V9 的 D1/D2/D3 落进 §3 与 §4 的「对应」列。**
   §3：K4、K8、M4、M6 由 `对应` 改 `标注·D`；K1、M1、E5 补 D。
   §4：38 条里 E1、E2、E3、E5、K1、K2、K4、K8、K12、M1、M4、M6、P4 共 13 条改
   `标注·D`（`19eafb2` 早于 `5f85971` 与 `520dc5d`，已验）。
   否则 §6 与 §3/§4/§7 自相矛盾。

3. **改三处算术。**
   §3 小计「对应 17；标注 17」→ **对应 15；标注 19**（逐行数 `REVIEW_TABLE.md:117-150`）；
   §7「仍与当前定义完全对应 70」→ **68**，再按第 2 条扣减后 **≤ 51**；
   §7「可证伪 85（33+38+14）」→ **84**，「非预测 1」→ **2**。

4. **在 §0.3 补 F4，并按 F4 重标 X3、P2、K7。**
   F4：不存在一个明显不具备该能力的臂能使预测成立。三条实测反例见 §3：
   X3 = 1.000（撞墙 32 步）、P2 = +8.0（写死的批量时刻表）、K7 = 1.0（一个负账目概念）。
   同时把 `METRICS.md:82` 给 P2 记的那条「(implemented)」防法改为未实现——
   它假设 harness 的批量速率恒定，限流/退避/上下文压缩都会破坏这个前提。

5. **降格 O-4，`未声明的先验知识` 计数改为 0。**
   证据：`battery/REPORT_V0.md:74-82`（独立小节，公开发布，早 12 小时，同一作者，
   并写明了对 C2 的威胁）+ `0be176c` commit message + `REPORT_V0.md:140` 的待办第 2 项。
   且已知证据指向注册的预测**会失败**，不存在可白拿的信用。
   §3d 关于「反例已在模型阶梯上被满足」的实质裁决**保留**。

6. **改 `ENDPOINTS.md` 主终点 2 的 F2 裁决。**
   「F2 不过。无预测，无反例」是错的。`exam/grading/calibration.py:130-131,286-292`
   写死了 `bluffer` 必须 `sensitivity 1.0 / specificity 0.0`，不满足则**阻断真实评分**
   （`:39`）；`ablation-arm/DESIGN.md:245-246,256,280` 有 P-5/P-6 与第 (iii) 类特异度
   失败的方向预注册。裁决应改为：**电池侧无；`exam/` 侧有方向预注册但作用域是合成
   假考生与消融展品，不覆盖跨臂准确率；全仓无任何数值门槛。**

7. **撤回 `ENDPOINTS.md:43` 的落点断言。**
   「U3 达成率由 U 阶梯打分器算，落点 `proxy/scoring/`（已独立查实）」——
   `proxy/` 全目录 U 阶梯关键词零命中，`proxy/scoring/` 只有 ARC 记分卡对账器
   （`proxy/SCORING.md:37-38`）。应改为：**该打分器尚不存在**；并补记全仓唯一相关的
   方向预注册 `ablation-arm/DESIGN.md:247` P-7（单臂构造性上限，非达成率）。
   主终点 1 的「从未被预注册过」结论本身**保留**。

8. **在 §7 声明 87 是行数不是陈述数**，并列出 7 条复合预测（E5、P4、K1、K2、X6、
   K13、M5），否则 §4.2 指出的「复合预测被整行不可判定吞掉」会继续发生。

9. **（不是 V18 的账，但冻结前要修）** `battery/METRICS.md:35` 把 M3 列进
   `Reference (38)`，与 `v9_gaming_audit.json` 的 `undetermined = ["M3"]` 及
   `efc21d1` 的 commit message 冲突；而 `METRICS.md` 声称 `tests/test_docs.py`
   会在文档与注册表不一致时失败。V18 §0.4 依赖这个 tier。

---

## 6. 站得住的部分，一并写下

对抗复核的义务是找错，不是否定一切。下列各条我独立复核过，**站得住**：

* **§1 顺序：四批次严格成立。** 四个预注册 commit 的日期与内容我复核过
  （`50d144c` 02:13 / `104908c` 08:38 / `19eafb2` 14:20 / `58e5f6b` 14:53），
  三个只动 `PREDICTIONS.md` 一个文件，`50d144c` 的 12 个文件里确实没有
  `battery/metrics/`。**这是全篇最硬的一节。**
* **§6a：`direction=` 全历史零变更；`45169a6` 与 `efc21d1` 未碰任何指标体。**
  我用独立方法（逐 commit 解析 `@metric`）复现，结论一致。工单预设的
  「`efc21d1` 又改了口径」**不成立**。
* **§6：V9 三条防法在 31 个交集 run 上没动过任何 `(status, value)`。**
  按 v2.1 自己的检验标准，防法通过；且「一条从不开火的防法不增加区分力」这个代价
  被写下来了，是对的。
* **§6b：4 条指标（X5、P5、E1、K11）入册时无方向预测**——工序 2 的字面覆盖缺口，
  找得准，且没有被夸大成顺序违规。
* **§3a：`frontload_index_25` 活在 `theoria-arm/armtools/archive.py`，主终点有两份
  实现、报数纪律不一致**——这是 V18 自己抓出来的，且比它初判的那句「名字从未存在」
  严重得多。自我更正记在案，这一条**加分**。
* **v0/v1 的 34 条预测在 §3 表里一行不缺。** 没有静悄悄的漏行。
* **`ENDPOINTS.md` §3d 关于 E2 的实质裁决**：E2 的反例判据已在模型阶梯上被满足
  （d = 1.000、4/0/0、三臂无理论、`agrees_with_declared_direction: true`），
  我逐字复核 `battery/artifacts/discrimination.json` 属实。**这是本次复核最重要的
  一条发现，与 O-4 的分类问题无关，不受第 5 条建议影响。**
