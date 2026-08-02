# S46 · 位置下标和回合标签不再进同一个桶

**工单**：`S46-turn-costs-mixes-two-axes`（板上 priority 2，territory `battery`，
`spend: none`）
**分支**：`agent/s46-turn-costs-mixes-two-axes`，worktree
`.worktrees/s46-turn-costs-mixes-two-axes/`
**基线提交**：`d10788f7`
**工人**：`W-9205`
**API 花费**：零。全程离线，不碰 `.env`，不碰封存堆。

来源：`freeze` 于 2026-08-01T03:00Z 经 `monitor/inbox/` 派单，登记为
`freeze/RESIDUALS.json` 的 `E2-AXIS`（`kind: register_limitation`，
`owner.territory: battery`）。裁定文本在 `freeze/STATS_RULES.md` §3.0，
缺陷本身写在 §3.0.2 第 4 步。

---

## 0. 先说一件与工单无关、但挡在前面的事

领到工单时 `battery/` 的测试套件**本来就是红的**：9 条失败，无一条由本工单引起。
全部是 `theoria-arm/` 动了而 `battery/` 没跟上：

* `82e8e25e` 重写了四条腿的 `curves.json`（r3：30 → 31 行，
  $11.761053 → $13.439862，轴 31 → 35 步），顺手重算了两个产物，
  但没有重渲冻结记录，也没有动钉在这些数上的常量；
* 此后又落了八条腿（R1 / R1b / R2 / R2b × g50t、sk48），于是活重算看到 14 条腿，
  已提交的产物里只有 6 条。

红的树上做不出可读的对照，所以先单独一提交把它推绿（`7befaef7`），本工单的行为
**一个字节都不在那一提交里**。四条陈旧常量按「动它的是什么」逐条注释后更新；
其中 `test_curves_json_shortfall_is_reported_not_absorbed` 钉的是一处上游已修的
不一致，它自己的 docstring 要求这种情况下**重写而不是删除**，因此改钉同类缺陷
今天还活着的那条腿（`20260731T231654Z-R1-sk48-b`）。
`artifacts/gaming_audit.json` 按 `PREREG_V9.md` §5 保持漂移，不重写。

结果：453 passed，`verify.py` 八条全绿。

---

## 1. 缺陷，以及它今天到底有没有在开火

`battery/model.py:284-301` 的旧实现：

```python
turn = call.turn if call.turn is not None else i
buckets[turn] = buckets.get(turn, 0.0) + (call.cost_usd or 0.0)
```

`i` 是枚举下标，与真实回合标签共用同一个 `buckets`。**先测量再动手**，两个探针
（`probe_blast_radius.py`、`probe_live_legs.py`，产物同目录）在 106 个可加载 run
和 14 条活腿上的读数：

| | exact | partial | absent | 无带价调用 |
|---|---|---|---|---|
| 离线语料（106 run） | **99** | 0 | 0 | 7 |
| 去掉适配器的行序捏造之后 | **99** | 0 | 0 | 7 |

**零个 run 的判定发生位移。** 每一条被加载的 ledger 里，每一个带价调用都带着
`step_idx`——`adapters/ledger_jsonl.py:241` 的 `else i` 那条路**可达但从未承重**。
这一条是本工单最重要的一个事实：它把「修复」和「悄悄改口径」区分开。

活腿上则不是这样。`20260731T231654Z-R1-sk48-b`：**3 个带价调用，0 个回合标签**
（join 来源逐字 `unjoined: curves.json counts 0 billed call(s), the ledger has 3`，
`join_confidence: degraded`）。今天 `turn_costs()` 把它压成 0,1,2 三个桶，
E2/E3 之所以没给出一个数，**只是因为 3 < `MIN_TURNS_FOR_SHAPE` = 8**——
被一条毫不相干的闸救下。同样形状再多五个调用就会读出一个数。

顺带一处佐证（跨领地复核给出）：只改 `model.py` 而不加指标闸时，这条腿上
E1 报 **$7.6085275**，E2/E3 却会说 "total cost is zero"。那是一句假话，
而 `verify.py` 第 8 条只禁止非 `ok` 的格子**带值**，抓不到它。
指标层的闸就是为这句假话加的。

---

## 2. 改了什么

1. **`battery/model.py`** — 新增 `TurnAxis` 与 `Run.turn_axis()`，四态：
   `exact` / `partial` / `absent` / `no-calls`，**对全部调用**而非只对带价调用发问
   （未定价的调用一样占一个键，旧回落下一样会占掉某个真实回合的键）。
   `turn_costs()` **不再回落**：轴不是 `exact` 就返回空表。
2. **`battery/metrics/economy.py`** — E2、E3 新增 `_axis_refusal`：
   `partial` → `unsound`，`absent` → `thin`。位置在**价格完整性闸之后**
   （未定价是更基本的缺陷，也是更能行动的理由）、**`total <= 0` 之前**
   （轴不可重建时的 total 为零只是本次拒答的副产物，说「花费为零」是撒谎）。
   不发明第四个 status——`metrics/__init__.py` 的三态是下游写死的合同。
3. **`battery/adapters/ledger_jsonl.py`** — 无 `step_idx` 的行不再拿到行序当标签；
   `notes["turns"]` 的 `or len(call_rows)` 同理换成 `or None`。
4. **`battery/tests/test_turn_axis.py`** — 新文件，验收与两条负样本。

### 拒答用哪个词

`unsound` 与 `thin` 在注册表里都落成 `insufficient-data`（`metrics/__init__.py`
的三态合同），区别在 reason 前缀。分法：**部分带标签是记录自相矛盾**
（它声称有回合轴又不提供），走 `unsound`，reason 带得上 `incoherent record: `
这个 grep 把手；**完全没有标签不是矛盾，只是没测**，走 `thin`。
工单写的是「缺标签即 `unsound`/`thin`」，两个词都用上了。

---

## 3. 没有买到任何豁免（本工单最该被怀疑的一处）

`battery/audit/gaming.py:383` 读 `v9_demotions()`，而它**对着活指标重算**，
不是读一份钉死的裁决。所以一道让 V9 攻击不再落地的闸，不只是拒了一份坏记录，
它会**上移 `tier_of`**——而 `PREREG_V9.md` R1 是「只降不升」。
`PREREG_E2L.md` §5 也逐字说了不许碰 `tier_of`。

`probe_tiers.py` 在 master 与本分支上各跑一遍：

| | master | 分支 |
|---|---|---|
| V9 降级数 | 38 | **38** |
| `reference` 层指标数 | 38 | **38** |
| 消失的降级（= 提升，禁止） | — | **[]** |
| 层级位移 | — | **{}** |

**零提升，零层级位移。** 另有一处独立佐证：跨领地复核把 `run_battery` 在两棵树上
各跑一遍，`artifacts/capability_spectrum.json` **逐字节相同**（771908 字节）。
`gaming_audit.json` 会变，但它的 `main`（`[]`）与 `reference`（38 条）两个键不变，
而该文件本就按 `PREREG_V9.md` §5 冻结、明面漂移、不重写。

V9 的 mutant 套件里有两条失配（`E2-flat-and-complete`、
`E3-padded-with-real-zeros`），它们是「防法**必须接受**」的记录，写的时候用
`turn=None` 表达「一次调用一个回合」——那正是被撤掉的那条回落。处置写在下一节。

---

## 4. 跨领地

* `theoria-arm/tests/test_turn_series.py:489`（`run.turn_costs() ==
  archive.frontload_input(doc)["turn_costs_billed_only"]`）：它构造的 5 个调用
  **每一个都带 `turn`**，轴为 `exact`，两边都读 `[3.626608, 2.69105]`。
  35 passed，不受影响。
* `run.notes["turns"]`：**全仓零消费者**。改成 `None` 只影响两个零调用 run。
* `figures/`：读的是**已提交**的 `capability_spectrum.json`，而它逐字节未变；
  `figures/verify.sh` 里没有 E2/E3 的计数常量。

---

## 5. 验收第三条：我没有按字面做，理由和证据在这里

工单验收第三条逐字是：

> `frontload_e2l.json` 那三条腿重算后，判定与它们各自的 `join_confidence` 一致。

最直白的读法是「`degraded` / `ambiguous-reconstructed` 一律拒答」。**我先照这个
方案做了设计，然后一个对抗性复核把它否掉了，我认为它否得对。** 四条证据：

1. **`degraded` 的成因逐条查过，全部是回合脊，不是步轴。** 失败的检查是同一条
   `every billed theorize invocation was claimed by a turn`，未认领的分别是 r2 的
   turn 4、r3 的 turn 29、R2b 的 turn 26。而这些腿的**步轴完好**：
   `anchored_priced_rows == priced_rows` 逐条成立。
2. **那样做会把 E2L 拴回它被造出来就是为了摆脱的那条轴。** `PREREG_E2L.md` §1
   逐字：「**与 E2 的唯一实质区别是分母轴**……回合标签由 harness 的批处理约定
   决定，动作序号由环境的应答决定」。
3. **它会在看到方向之后把 6 条不利读数改成沉默。** 那 6 条是
   0.0 / 0.115685 / 0.0 / 0.064934 / 0.083959 / 0.0，全部远低于平坦值 0.250，
   即**活臂在步轴上是后载的**——与 C2 预注册方向相反的探索性证据。
   `freeze/STATS_RULES.md` §8 第一条与 §3.0.6 都逐字封死这一步：
   **探索性读数照报，包括方向与预注册相反的**。
4. **而且它连验收本身都做不到。** `R1-sk48-b` 是 `degraded`，在那个方案下仍旧
   停在 `thin` —— 真正错的那一条恰好漏掉。

### 改为做了什么

**闸在钱上，不闸在标签上。** `curves.json` 自己带着一张认账凭证
（`self_check.accounts_for_every_billed_call` 与 `accounts_for_every_dollar`）。
新增 **G6**（`leg_reading`，在 G2 之前）：不认账就 `unsound`。

| 腿 | join | 认账 | 之前 | 现在 |
|---|---|---|---|---|
| `R1-sk48-b` | degraded | **否** | `thin` /「total cost is zero」 | `unsound` |
| `R1-g50t-a` | exact | **否** | `ok` 0.0 | `unsound` |
| 其余 8 条（含 6 条 degraded） | — | 是 | 不变 | **不变** |

`R1-sk48-b` 就是本工单那句话在产物里的样子：它的曲线两行合计 $0.00、逐行
`model_calls: 0`，而代理账本对这条腿计了 3 次调用、**$7.6085275**，
E2L 为它印的是「total cost is zero」。**把 $7.61 印成了零。**
`R1-g50t-a` 是轻症：曲线 $7.6034195，账本 $7.6085275，差 $0.005，读作 `ok` 0.0。

**「与 join_confidence 一致」改用不许被读多的方式做到**：
`process_1_material` 新增 `n_evaluable_by_join_confidence`
（今天是 `{degraded: 6, exact: 1}`），产物新增顶层 `axis_caveat` 逐字带上轴的
效度问题——那正是 `RESIDUALS.json` `E2-AXIS` 的 `clears_when` 第 (b) 条要的话；
每条腿另加 `accounts_for_the_bill`，`join_confidence` 照旧随数走。

修订按 `PREREG_V9.md` §0 的协议**追加**在 `PREREG_E2L.md` 的 `## 修订` 段，
连同「这是看到数之后做的、方向上只降不升、程序上仍是一次失守」一起写在里面。

**这一条我可能判错，所以把否掉的方案、证据和代价都留在这里，并已走
`monitor/inbox/` 报给监控。** 若监控或 freeze 认为应当照字面上闸，改回去是一个
小改动（`leg_reading` 加一条 G7），本文件是它需要的全部材料。

---

## 6. 顺手补上的两处同类缺陷（不是工单要求，但不补就等于把洞挪了个地方）

1. **`audit/live_economy.py:198` 的曲线**。它直接读 `turn_costs()`，轴拒答之后
   返回 `[]`，而 `[]` 与「这条腿没打过任何模型调用」的曲线**逐字节相同**——
   $7.6085275 就这样从产物里消失，没有 status 也没有 reason。
   本模块自己的第三条承诺是「records absence with its reason, per leg and per
   metric, and never as a zero」。新增顶层 `spend_with_no_shape`
   （不放进 `absences`：那张表一格一指标、带的是指标状态，轴不是指标），
   每条腿另记 `turn_axis`。同一文件里 `labels` 长度不匹配就退回 `range()`
   的那条回落也一并删掉——它是同一个换轴动作的第三处。
2. **`run_battery.spectrum` 与 `audit/live_arm.py` 的 `turns` 列**。
   `len(...) or None` 把「没有决策」和「有决策但没标签」压成同一个 `null`，
   两条腿上两种形状都真实存在。各加一列 `turn_axis`。

---

## 7. 交付状态

| | |
|---|---|
| 测试 | **470 passed, 0 failed**（基线 9 红，见 §0） |
| `verify.py` | **八条全绿** |
| V9 裁决 | 降级 38 → **38**，提升 **0**，层级位移 **0**，mutant sweep 无失配 |
| 负样本 1（全带标签不变） | **4028 个格子逐格对比，0 个移动**（`probe_cells.py --diff`） |
| 负样本 2（全无标签必须拒） | `test_a_wholly_unlabelled_record_is_refused_not_renumbered` |
| 部分带标签必须拒 | `test_a_position_and_a_label_no_longer_share_a_bucket` |
| API 花费 | **0** |
| 封存堆 | 零接触；只读过 dev 堆的 g50t / sk48 |

### 遗留（gap，如实记）

* **`E2-AXIS` 的 `clears_when` 第 (a) 条已可查**（回落不再与真实标签共用桶），
  第 (b) 条（`grep -q '轴的效度' papers/*.md`）**不在本领地**——`papers/` 是别人的
  领地，本工单不碰。已在 inbox 里点名。
* `adapters/theoria_live.py:268` 仍把 `Call.step_idx` 写死 `None`
  （`PREREG_E2L.md` §5 明令另开工单，补它会移动 P2 的活腿读数）。本工单未碰。
* `battery/artifacts/gaming_audit.json` 按 `PREREG_V9.md` §5 继续明面漂移。
* `turn_costs()` 的**返回契约变了**（轴不可重建时返回 `[]`）。今天
  `theoria-arm/tests/test_turn_series.py:489` 不受影响（它构造的 5 个调用全带
  标签，两边都读 `[3.626608, 2.69105]`，35 passed），但那是它今天的数据决定的，
  不是契约保证的。已写进 `PARTNER_SYNC.md` 与 inbox。
