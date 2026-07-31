# RUN_STATE — B-LIVE-ECONOMY（活臂经济族落地）

**时戳** `20260731T1731Z`（仓库按 UTC；会话本地日期 2026-08-01）
**分支** `p12/battery-live-arm`　**base** `73760dc8`
**领地** `battery`　**上游材料** `theoria-arm/runs/`（只读，零 API、零模型调用、零网络）

## 工单要的四件事，逐条对账

1. **把活臂作为独立臂标签吃进来** —— 已在 `arm: theoria` / `source:
   theoria-arm-live` 下入册，**没有**并进 `theoria_a0` / `theoria_a0_spike`。
   开工时这一步其实**已经存在**（前一会话的 `20260731T1740Z-LIVE-ARM-READINGS`
   落了 `adapters/theoria_live.py` + `audit/live_arm.py`），但 **committed 产物
   已经陈旧**：sk48 leg 的 harvest 在其后落盘，`python -m battery.verify` 开工时
   是 **RED（第 7 级）**、`python -m pytest` 是 **2 failed**。本次重算修复。
2. **重算每一族** —— 38 条 × 6 条活 leg = 116 个实测格；机制族结构性
   `not-applicable`（活局无 ground truth），K2 两个 held-out 字段留空并附
   `held_out_frame` 说明，都是 absent-with-reason，不是 0。
3. **经济族** —— 新 `battery/audit/live_economy.py` + `artifacts_live/
   live_economy.json` + `verify.py` 第 8 级 + `tests/test_live_economy.py`。
   数字与解读见 `BATTERY_V1.md` 附「2026-08-01 增补（三）」与 `STATUS.md` B18。
4. **尊重冻结** —— `battery/artifacts/` 七份冻结读数与冻结基线**一个字节未动**；
   新产物一律进 `artifacts_live/`；`freeze.check()` 为空。被编辑的冻结文件只有
   `freeze.py`（桶清单）与 `verify.py`（新增一级），即冻结机制自身——这正是
   `BATTERY_V1.md` 前两次增补立下的那条路。

## 本次实际动了什么

| 文件 | 动作 |
|---|---|
| `battery/audit/live_economy.py` | 新增（`code` 桶） |
| `battery/tests/test_live_economy.py` | 新增（`suite` 桶，22 条，含 6 条负控） |
| `battery/artifacts_live/live_economy.json` | 新增（`readings` 桶） |
| `battery/artifacts_live/live_arm_readings.json` | **重算**（陈旧 → 现行） |
| `battery/freeze.py` | 三个桶各 +1 条 |
| `battery/verify.py` | 新增第 8 级，1..7 级标签 `/7` → `/8` |
| `battery/BATTERY_V1.md` | 五个 `freeze:*` 块重渲；§2.2/§2.4/§2.6 标题份数改到真值（前一次增补漏改）；附增补（三） |
| `battery/STATUS.md` | 附 B18 |
| `monitor/inbox/20260731T1731Z-battery-to-theoria-arm-curves-shortfall.md` | 跨领地通报 |

## 关键设计取舍

**为什么另开一个经济族产物，而不是把数塞进 `live_arm_readings.json`。**
经济族里只有 E2/E3 走 turn 轴，而活臂账本没有 turn 索引，适配器读不到归档的 join
时会退化成「一次调用一回合」。退化轴与精确轴算出的 E2/E3 **在表格里长得一模一样**，
而前载指数是 Phase 4 的主要终点之一。新产物把两轴并列摆出来，并单独记录
「格子没动但轴长动了」的情形（r2：5 → 3 回合，两边都在 8 回合下限之下，于是返回
同一句 `insufficient-data`——那是算术，不是印证）。

**精确轴是抄来的，不是推出来的。** `bill_shape.json` 已经发布了逐调用的
`call_idx -> turn`；本模块把这个字段抄到 `Call.turn` 上，再跑**同一批冻结的指标
体**。`theoria_live` 的文档明写「join 的第二份实现就是 E2 输入的第二个无标签定义」
——本模块一行 join 逻辑都没有。抄之前先对账：调用数与金额必须与 proxy 账本相符，
否则整条轴拒绝（`partial` / `irreconcilable`），不做补全。

**「没有账单就没有账单形状」。** r1 与两条 2026-07-29 的 leg 零计费调用，经济族
整族 `not-applicable`。第 8 级闸门专门有一条：**status 非 `ok` 的格子带数字 → 红**。
零在成本曲线上读作「便宜」，不读作「没发生」。

## 诚实的残缺

* **n = 4 条 carried leg、2 局、1 天、同一个 harness**。C2 的三件证据里只有逐回合
  成本曲线是三条腿都有的；前载指数与收敛点是 **n = 1**。
* **四条 carried leg 全部 `spend_gate_tripped`、通关 0 层**，所以 E3 = 1.0 量的
  是预算闸门的位置，不是理论收敛点。任何引用都必须带上这句。
* **E5 从 0.682632 掉到 0.395290 是唯一朝 C2 方向动的数**，n = 2，同局同日，
  是观察不是效应。
* **E2/E3 在 V9 审计下是 `reference` 层**（冻结基线写 `main`，现行判定降级，
  分歧已在第 6 级披露），所以它们**不得承载任何排序结论**——不管数字多好看。
* **两条 leg 的 `curves.json` 少算了钱**（r2 −1.630485 USD、r3 −1.678809 USD）。
  这不是电池能修的，已通报 theoria-arm；本领地对它只报告不拦。
* 封存堆：本次写下的任何文件里没有 21 个封存 id 中的任何一个；活 leg 全部经
  `battery.guard` 正向白名单判为 `dev`，第 7/8 级各自再从 committed 行里复核一次。

## 闸门（原样）

```
cd battery && python -m pytest -q
430 passed in 21.11s

python -m battery.verify
battery: green -- freeze, suite, one real run, artefact fields, separation claim,
live tiers, live-arm readings, live-arm economy
```
