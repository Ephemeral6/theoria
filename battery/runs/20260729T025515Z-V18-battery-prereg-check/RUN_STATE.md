# RUN_STATE · V18-battery-prereg-check

`Theoria.md` Phase 2 工序 2（方向预注册）的**冻结前复核**。
零 API、零网络、零模型调用、封存堆零接触。只写 `battery/`。

## 工单三问，三个答

| 问 | 答 |
|---|---|
| 1. 每条预测是否仍与当前指标定义对应？ | **87 条里 70 条对应，17 条标注。** 逐条见 [`REVIEW_TABLE.md`](REVIEW_TABLE.md) §3–§5 |
| 2. 是否有指标已回算、而预测写在回算之后？ | **git 层 0 条**，四批次均由 `--is-ancestor` 双向证明。**先验知识层 1 条未声明**（O-4）、5 条已声明。见 §1–§2 |
| 3. 三主终点的预测是否具体到能被证伪？ | **两条不可证伪（根本没有预测），一条可证伪但当前判不了、且反例已被满足。** 见 [`ENDPOINTS.md`](ENDPOINTS.md) |

**没有删除任何一条预测。** `PREDICTIONS.md` 正文一个字节没改，只在末尾追加了一段
标注（§5）。工单的话：**冻结一份被删干净的预注册，等于没有预注册。**

## 什么跑了

```
$ python -m battery.run_battery --out battery/runs/20260729T025515Z-V18-battery-prereg-check/recompute
runs           48 (4 games, arms: bare_cc, theoria_a0, theoria_a0_spike, theoria_a2)
metrics        38 registered, 681 computed values
main table     
reference      E1 ... X6   (38 条)
process 1      bare_cc (weaker) vs schema_repro (stronger) | schema arm available: False | 0 of 38 metrics pair on >=2 games
unvalidated    21 metrics never computed on a control arm
power          a two-sided sign test needs 6 non-tied paired games to be able to reach p<0.05 at all; the pilot has 4
exit code 0
```

`--out` 指向本 run 目录，**`battery/artifacts/` 未被触碰**（`git status battery/artifacts/`
干净）。这次没有喂 `--baseline` / `--schema`，所以 48 run 是已提交的 95 run 的子集，
两者不可直接相提并论——**只在 31 个交集 run 上做了逐值比对**（§6）。

```
$ python -m pytest battery -q
319 passed in 3.91s
exit code 0
```

完整输出留痕在同目录 [`pytest.txt`](pytest.txt)，重算输出在
[`recompute_stdout.txt`](recompute_stdout.txt)。

## 顺序，可证

```
$ git merge-base --is-ancestor 50d144c 0be176c ; echo $?   # v0 预注册 -> v0 回算
0
$ git merge-base --is-ancestor 0be176c 50d144c ; echo $?   # 反向
1
```

四批次同样两条命令，退出码全部 `0 / 1`——**顺序严格成立，四次**：

| 批次 | 预注册 | 回算 | 正向 | 反向 |
|---|---|---|---|---|
| v0（25 条） | `50d144c` | `0be176c` | 0 | 1 |
| v1（9 条） | `104908c` | `e82558b` | 0 | 1 |
| v2（38 条） | `19eafb2` | `82a6925` | 0 | 1 |
| v2.1（15 条） | `58e5f6b` | `5f85971` | 0 | 1 |

三个预注册 commit **各只动 `PREDICTIONS.md` 一个文件**；`50d144c` 动了 12 个文件但
**没有 `battery/metrics/`**。V9 今晚正是栽在这一项上（裁决实现不在预注册 commit
里），所以这一项是按同一把尺子查的，不是照抄自述。

**「预测写在回算之后」这一类顺序违规：0 条。**

## 一条未声明的先验知识 —— O-4，登记而不删除

v2 的 E2 行注册「CC vs Schema **不分开**」，并自带反例：*若 E2 干净地分开 CC 与
Schema，则 E2 量的是能力而不是前载，它作为 C2 签名的地位就有麻烦*。

而在 v2 预注册（`19eafb2`，14:20）之前，`battery/artifacts/discrimination.json`
（落盘于 `0be176c`，02:33，**已验为严格祖先**）里已经写着：

```
E2  cliffs_delta: 1.000   4 wins / 0 losses / 0 ties
    agrees_with_declared_direction: true   verdict: "underpowered"
```

模型阶梯 haiku → sonnet → opus，harness 固定，**三个臂一个理论都没有**。
v0 的 commit message 也已写明这句话。

**v2 的封条段没有声明这一条。** 它声明了上游目录名带分数、文件字节数两处泄漏，
没提这个。登记。

两种读法都写下来，不替任何一种辩护：**不利**——明知能力本身就前载，仍把 E2 注册为
C2 的签名而封条不提；**有利**——明知有反证仍注册一条会被打脸的预测，是更强的纪律。
两种读法都不改变裁决：**这条预测自己写下的反例，在另一条梯度上已经被满足了。**

## 三主终点：两条根本没有预测

| 主终点（`Theoria.md:373`） | 电池 id | 有方向预注册 | 可证伪 |
|---|---|---|---|
| U3 达成率 | **无** | **无** | **否** |
| 判决题准确率（含特异度） | **无** | **无** | **否** |
| 前载指数配对差 | `E2` | 有，三次 | **是，但当前 `no-data`** |

`grep -n "U3\|判决题\|特异度" battery/PREDICTIONS.md` 全部返回空。
文件里的 `verdict` 一律指电池自己的工序 1 判决，**与判决题（不可解变体考题）同名
不同物**。

代理也不合格：U3 最接近的 K3 / K10 是**计数**不是**率**，且两条都被 V9 判为可刷
（「`0 = 0` 也是定理」/「灌一堆平凡的 prune ⇒ dead」），K10 的辩护还是电池**外部**
的 Lean 义务，`METRICS.md` 自陈「the battery counts rather than checks」。

同一结论已由另一条工单线独立得出：
`monitor/inbox/20260728T192000Z-W-252-freeze-list-cannot-cover-two-of-three-primary-endpoints.md`。
**本复核证实那条提议。** 落点分别是 `proxy/scoring/`（U3）与
`exam/grading/mark.py` 的 `confusion()`（判决题），**都不在 `battery/` 内**。

`exam/` 侧本复核只做了目录与关键词检查，**没有逐文件读**，也无权替它下结论。
登记为：**battery 侧确认没有；exam 侧未找到。**

## V9 的硬约束，怎么落进这份复核

* **87 条预注册陈述里，86 条建立在 V9 判为「刷得动」的指标上。** 每一条都在
  `REVIEW_TABLE.md` 的 V9 列标了 `可刷`。**一条建立在可刷指标上的预测，即使方向对，
  也不构成证据。**
* **剩下那一条是 M3，单独点名。** V9 记它 `undetermined` 而不是 not-gameable：
  `cross_level_first_use_delay` **没有任何路径调用 `ok(...)`**，本次 48 run 重算
  全部 `insufficient-data` / `not-applicable`。**「攻不动」不等于「有区分力」**——
  它攻不动是因为它算不出数。M3 也因此是全文件**唯一一条不可证伪**的预测（判据 F1
  不过：算不出数，就不存在能让它算错的取值）。M3 承载的是**claim C3（迁移）**。
* **落在已证稳健指标上的预测：0 条。**
* **没有因为 V9 而删掉或降级任何一条预测。** v2.1 的三条「回主表」预测被 V9 直接
  推翻，照实记在 `REVIEW_TABLE.md` §5，正文一字未动。

## V9 三条防法：实测它们没动过任何已发布的数

D1/D2/D3（`520dc5d`，在全部四批预注册**之后**）给 12 条指标加了拒答路径。这是口径
变更，必须查它有没有动过被预测的值。

* **31 个交集 run 上，`(status, value)` 一处未变。**
* **48 个 run 上 `incoherent record:` 拒答触发 0 次。** 三条防法在仓库现有材料上
  一次都没开火，只被变异体与攻击套件打到。

按 v2.1 自己定的尺子——「**一条移动了已发布值的防法，是改了测量而不是护了测量**」
——V9 三条防法**通过**。代价一并写下：**一条在真实材料上从不开火的防法，不增加任何
区分力。**

## 撞到的 / 没做的

* **没有裸跑 `run_battery`。** 已登记的「裸跑会覆盖 `battery/artifacts`」缺陷本轮
  **没有撞到**，因为全程带 `--out`。按工单要求登记而不顺手修。
* **撞到一处冻结哈希冲突，登记而不修。** `origin/agent/v5-battery-freeze` 的
  `battery/BATTERY_V1.md` 把 `PREDICTIONS.md` 钉死成两道哈希：

  ```freeze:prereg
  sha256:9614abf2054bccb0e57ff590df21946ebca53924b0d58311b10cf68975882453
  prefix-bytes: 35087
  ```

  该文件当时正好 35087 字节，所以两道哈希**同值**。本次追加标注段后前缀完好、
  全文变了。BATTERY_V1 自己对这个情形有明文规定：

  > 前缀完好但全文变了 = 冻结之后**追加**了新预测。这是正当的工作、不正当的冻结：
  > 需要一个记录它何时到达的新冻结版本（`BATTERY_V2.md`），不能靠悄悄变长的同一份
  > 文件。

  **本 run 追加的是标注不是预测**，但 `freeze.py` 的 `check()` 分不出这两者。
  两条分支合流后 `check()` 会失败。**没有改 `BATTERY_V1.md`**（不在本树、不是本
  工单的文件），也没有悄悄改哈希。新全文 sha256 记在 `MANIFEST.json` 里，留给
  重新冻结的人。
* 没有 push，没有碰 master、主工作树或别的 worktree。
* 合并了 `origin/agent/v9-battery-gaming-audit`（工单建议），无冲突。

## 对抗复核

见 [`ADVERSARIAL.md`](ADVERSARIAL.md)。结论落进本记录的部分标在 §「对抗复核改了
什么」。
