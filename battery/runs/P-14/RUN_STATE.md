# RUN_STATE — P-14 · battery v1

`prompt_id: P-14` · branch `agent/p14-battery-v1` · base `master` at df9f748

Snapshot of the artefacts as published, with `MANIFEST.json` carrying the
sha256 of every one of them and of every input they were computed from.

## Contract, item by item

| asked | delivered | evidence |
|---|---|---|
| 吃下 cold-start-a2 的轨迹与修复回路账 | ✅ 4 runs, 1 六拍回路, U4 材料入 `Repair`/`Beat` | `adapters/a2.py`, K12=1.0 / K13=0.262 on `a2-probed` |
| 吃下 a0-spike 的 held-out 与 adapt 数据 | ✅ 1 run, 4 变体, 检测延迟/修复成本/连带作废 | `adapters/a0_spike.py`, M4=12.0 / M5=0.75 / M6=0.75 |
| 吃下包络首局 ar25×haiku 的真账本 | ✅ 3 cells 分档标签, 且发现 v0 一直在混池 | `campaign="phase3-variance-envelope"`, D-B-013 |
| 全量回算, REPORT_V1 落盘 | ✅ 31 runs / 4 arms / 38 metrics / 417 values | `REPORT_V1.md`, `capability_spectrum.json` |
| 区分力工序第一跑, 逐指标效应量 | ✅ `arm_contrast.json`, 7/38 有重叠 | 见下「口径」 |
| 指标表加「验证材料」列 | ✅ 且是**从回算生成**的, 不是手写 | `METRICS.md`, `audit/validation.py` |
| 去冗余首跑, 聚类依据入 audit | ✅ 全量 703 对 ρ 与共享局数入产物 | `redundancy.json` `matrix` |
| PREDICTIONS 只许追加, 先注册后回算 | ✅ 提交 104908c, 早于任何指标实现 | `git log battery/PREDICTIONS.md` |
| 零 API 零模型调用 | ✅ | `MANIFEST.json`: 0/0/$0.00 |
| 封存护栏照旧 | ✅ 每次加载重算 piles 摘要, 0 次封存读取 | `guard.py`, provenance in every artefact |

## 口径声明 — 区分力这一跑不是 Theoria.md 的工序 1

`Theoria.md` Phase 2 工序 1 写死：**验证只用对照两臂，与 Theoria 无关**。所以

* `discrimination.json` 是工序 1，只用对照臂，**未被本次新材料污染**；
* `arm_contrast.json` 是**结果**，不是验证。每条目带 `confounded_by_world:
  true`，文件头一句话写明「此处无一条为任何指标背书」；
* `METRICS.md` 的「验证材料」列只喂第一个文件。

而且这一跑是**非配对**的：裸 CC 打 ARC 局，Theoria 离线臂打自建世界，没有可配
对的局。臂与世界完全共线，无法分离。里面几个 p<0.05 是丢掉配对换来的名义检验
力，不要读。

## 自报完成 ≠ 已核实

本文件是**自报**。可独立核实的部分：

```bash
python -m pytest battery/tests -q          # 117 passed
python -m battery.run_battery              # 与 runs/P-14/ 逐字节相同
python -m battery.docs                     # METRICS.md 不变则一致
```

不可由本轨道核实的：指标定义本身是否合理（W-1，仍是最严重的开放弱点），以及
修复族的全部数字（W-11，自出自评，`Theoria.md` 已定 U4 为排座次且不当证据）。

## 本跑自己找出来的三个坏消息

1. **X6 被自己的预注册证伪**（1.000 到处都是，模型阶梯上还反向）。
2. **E7 被同一次回算的去冗余否掉**（E4~E7 ρ=+0.991）。
3. **K14 在 a0-no-button 上被自己的抗游戏条目证伪**（单概念词表，min=max=+1001）。

三条都留在产物与报告里，没有事后改定义。
