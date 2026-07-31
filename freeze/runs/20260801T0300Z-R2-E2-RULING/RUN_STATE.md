# R2 · 对 battery 的 E2 裁决作出裁定 —— 前载终点撤出确证家族

**UTC**: 2026-08-01T03:00Z ｜ **分支**: `r2/freeze-e2` ｜ **基线**: `af138a0d`
**领地**: `freeze`（`battery/` 只读；跨领地请求走 `monitor/inbox/`）
**花费**: $0.00。零 API 调用，零封存堆接触，零线上跑。全程离线读产物。

---

## 一 · 裁的是什么

battery 的 E2 复核是一条**关于冻结包**的发现，不是关于某个数的发现。
把它的三段读完之后，结论只有一个可选项：

> **主终点三（前载指数配对差）撤出确证家族，降为探索性。
> 三个席位不动，可主张的只剩两个：U3 达成率、判决题准确率（含特异度）。
> Holm 的除数仍为 3。**

落点：`STATS_RULES.md` §3.0（新）、§3.2/§3.3 顶部的身份横幅、§4.3、§8、
§9.9 的注记、§9.23/§9.24 两行、§10 的三行与「三条封不死」；
`CLAIMS_TEXT.md` C2 的身份声明段、三版逐字文本各一句强制声明、
结局三 B-2 的降级注记、脆弱点第 0 条；
`MANIFEST_DRAFT.md` 第 10 项的注记；
`MANIFEST.json` 的 `endpoints` 块与 `verdict.statement`。

## 二 · 证据链（全部离线可复算）

1. **V9 的 38 降 38 是一条发现被说了 38 遍。** `battery/audit/threat.py`
   的模块文档：攻击者写的是零参数构造函数，**攻击者就是记录方**；
   每条指标都是 `Run` 的全函数，于是「能不能推过门槛」退化成
   「门槛能不能被任何一份记录达到」——门槛的性质，不是指标的性质。
2. **收窄被语料审过，两个方向都被看见说过话。** 10 条候选不变量跑过
   **106 个真实 run**，丢掉 2 条并留下反例（I7 ← `bare_cc-g50t-…-29065be4`；
   I8 ← `a0-spike`），留 8 条；112 个攻击 T-REC 落 95、T-ARM 落 80；
   `assert_not_vacuous()` 同时拒绝「全清」与「没清」。
3. **battery 自己打掉了这次清白。** `frontload_e2l.json`：
   `batched-turn-label-coherent` → `breaks: []`、`arm-reachable`、
   `poverty_certified: true`、**value 0.973387097 ≥ target 0.95**；
   `first-turn-bill-coherent` → E2 与 **E2L 同时 1.0**。

## 三 · 为什么不是「换一个可辩护的阈值」

* 本终点**没有阈值**：它是 Wilcoxon/符号检验 + Holm。0.95 是 V9 自己的成功门槛。
* 坏的是**轴的效度**：`Call.turn` 是记录方的标签，跨臂约定在冻结包里没被钉死；
  `battery/model.py:284-301` 的回落还会把枚举下标与真实标签装进同一个桶。
* **定不出标**：`process_1_material` 逐字 `n_paired_games: 0`、
  `control_arm_legs: 0`。`PREREG_V9.md` 自陈门槛从未定标，且 31 条有方向的指标里
  15 条已有诚实 run 达到「被刷成」的门槛——那些指标上 S2 量的是可达性。
* 一个选出来的阈值在这里**比没有阈值更坏**：它让读者以为定标发生过。

## 四 · 为什么不换成 E2L（四条，任何一条都够）

R1 只降不升；E2L 未过工序 1 且不在 `REGISTRY`；**E2L 自己被
`first-turn-bill-coherent` 刷到 1.0**（arm-reachable + 贫困证书通过）；配对局数 0。
并且在看到攻击结果之后把新指标提进主终点，正是 §8/§10 标着 ✅ 封死的那一行。

## 五 · 这条裁定的价格，写在它自己身上

撤一个终点是**有收益**的动作：除数从 3 掉到 2，Holm 最紧那级从 α/3 松到 α/2，
按 §4.1 的算术符号检验的进带价从 **k ≥ 7** 降到 **k ≥ 6**——
**撤掉一个自己刷不动的终点，恰好给剩下两个买回一局。**
所以裁定第 2 条把除数钉死在 3，席位保留、不出 p 值。
这不是新规矩：§4.4.3 与阶段 [16] 的 `*/family` 探针已经为「不可结论」写过同一条，
本轮只是把它扩到「撤出」这一种触发方式，并给它一道自己的闸。

## 六 · 闸门与阴性对照

`freeze/e2_withdrawal.py`，接在 `freeze/verify.sh` 阶段 **[19]**。
`--selftest` **8/8**，七条变异每一条都被要求实际把检查变红，外加一条正向对照
（未变异的真文件必须过）；**建不出来的对照记为失败，不记为跳过**。

```
PASS positive control: the real files pass unmutated
PASS control fires: drop the identity sentence from ONE C2 block -> W4/不成立版
PASS control fires: drop the Holm divisor from 3 to 2 -> W3/divisor
PASS control fires: restore §8's `除 E2 外` exception -> W5/noexempt
PASS control fires: delete the axis-validity caveat from CLAIMS_TEXT -> W6/caveat
PASS control fires: demote §3.0 from a ruling to a note -> W1/head
PASS control fires: blur the measured attack value -> W7/value
PASS control fires: re-declare the family as two -> W8/neg
8/8
```

## 七 · 闸门位移（`bash freeze/verify.sh`）

| | 基线（`af138a0d`） | 本轮 |
|---|---|---|
| 结论 | DRAFT INCOMPLETE — **3** failed | DRAFT INCOMPLETE — **2** failed |
| [12] MANIFEST.json | **FAIL**（drift） | **PASS**（本轮重生成，且 `endpoints` 块是新的） |
| [15b] BUDGET_TABLE | FAIL | FAIL（**未动**，见下） |
| [18] locations | FAIL | FAIL（**未动**，见下） |
| [19] 撤出闸 | 不存在 | **PASS + PASS**（8/8 对照） |
| [4] [5] [8] [10] [16] [17] | PASS | PASS（本轮改动没有把任何一条已绿的探针弄红） |

**[15b] 与 [18] 本轮不修，理由要写下来而不是留给读者猜**：

* **[15b]** 读 `proxy/var/spend_gate.jsonl`（gitignored，每次代理调用都在长），
  而**此刻有一轮线上 R1 正在跑**。这一红是闸门在正常工作
  （生成器自陈「余额移动是唯一必须让冻结预算表失效的事件」）。
  在一轮线上跑的中途重生成，等于把一个正在移动的余额钉进冻结包。**留红。**
* **[18]** 全部 11 条都在别人的领地（`theoria-arm/runs/…`、`proxy/runs/…`、
  `arc-recon/runs/…`），其中四条正是 R1 的活腿目录。**不是本轨道的东西，不碰。**

## 八 · 诚实的残余（三条，登记而不假装解决）

1. **降级不修指标。** 轴的效度问题在探索性读数上**照样存在**，
   活在每一个仍会被印出来的前载数字上（`RESIDUALS.json` 的 **`E2-AXIS`**）。
   §10 的「封不死」由两条变三条，正是为了不让这次撤退冒充一道闸。
2. **两个存活的终点今天一个也算不出来。** U3 卡 §9.2/§9.14/§9.17–§9.20，
   判决题卡 §9.15/§9.16。`MANIFEST.json` 的 `endpoints` 块逐字写着
   **3 席位 / 2 在家族 / 今天 0 个可算**。「撤了一个」不等于「剩下的好了」。
3. **判据只被验证过一次说「不」。** §3.0.5 的判据（值若是臂自写记录的全函数则
   不可确证）对本终点说了不、对另外两个说了是。**它对另外两个说「是」这件事
   本身没有被独立检验**——它只排除这一种病，不体检。

## 九 · 纪律

* `battery/` 全程只读；请求走 `monitor/inbox/2026-08-01T0300Z-freeze-to-battery-…md`。
  **已知限制**：worktree 里的 `monitor/` 是这条分支自己的副本，
  这封信在分支合上主线之前不会被任何人读到。写在这里，免得被当成已送达。
* `PARTNER_SYNC.md` 只追加、只写本轨道的段落。
* 零 API、零花费、零封存堆接触；未触碰任何含 `R1` 的目录。
