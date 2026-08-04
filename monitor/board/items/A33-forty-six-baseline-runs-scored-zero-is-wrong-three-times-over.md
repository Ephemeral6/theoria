priority: 1
cell: A33
territory: baseline-arms
deps: none
spend: none

# A33-forty-six-baseline-runs-scored-zero-is-wrong-three-times-over · 「46 条基线 run 最高分 0」这句话，盘上没有一处支持它

登记 #14（`monitor/spec.py:524`）写着：**「46 条基线臂 run（裸 CC 三档模型）
最高分 0、通关 0」**。这句话被当成决定性事实的一半在用。我把它逐条对着
`baseline-arms/runs/` 重算了一遍，**三处都不成立**，而且错的方向都是把证据
说得比它实际更强。

## 一 · 46 不是 run 数

`baseline-arms/runs/MANIFEST.json` 自己的计数，逐字：

```
"by_kind": {"excluded": 1, "fetch": 1, "migration": 1, "run": 43}
"total": 46
```

**46 是清单里所有条目，43 才是 run。** 另外三条是一次被排除的记录
（`s1-full-run-not-archived`）、一次抓取（`fetch-schema-traces-path-a`）
与一次账本迁移（`migration-ledger-v0-to-v1.0`）——它们没有玩过游戏。

## 二 · 「分数 0」是无中生有：`score` 这个键根本不存在

逐个打开 43 份 `run.json` 的 `summary`：**36 份有 summary，
没有一份含 `score` 键**。基线臂从来没有记录过分数。
`levels_completed` 有，且这 36 份全是 `0`。

所以真话是「**36 条 run 记录了零通关**」；「最高分 0」是把
`levels_completed: 0` 读成了分数。分数在这些 run 上是**缺席**，不是零——
而缺席正是本项目反复写下不许当成零的那件事。

## 三 · 另外 7 条根本没有 summary，它们的通关数是缺席

`MANIFEST.json` 的 `by_outcome`，逐字：

```
{"api_unusable": 8, "budget_exhausted": 20, "gave_up": 2,
 "model_error": 5, "no_reset_window": 1, "no_summary": 7}
"dead_runs": 14
```

七条 `no_summary`（全部是 haiku：`bare_cc-ar25-...-55ea5593`、
`bare_cc-g50t-...-069d86f8`、`bare_cc-sk48-...-36c386d1` / `-4f5d7ddb` /
`-b1ae92a0` / `-b3e5c758`、`bare_cc-tn36-...-1b9b5309`）**没有 summary，
因此没有 `levels_completed`**。清单自己说 14 条是 dead run：8 条
`api_unusable` + 5 条 `model_error` + 1 条 `no_reset_window`——这些不是
「玩了没赢」，是**没玩成**。把它们计入「零通关的证据」，等于拿网络故障
当能力证据。

## 四 · 最要命的一条：没有任何一条基线 run 被允许走到 78

逐 run 读 `budget`：

```
30 个动作 x 22 条 run
20 个动作 x 14 条 run
缺失      x  7 条 run
```

实测 `actions_ok` 的最大值是 **30**，36 条合计 **573** 个动作。
g50t 关卡 1 需要 **78**。

**所以基线臂的零通关不是关于能力的测量，它是关于 30 个动作预算的测量。**
一条被给了 30 个动作、去打一个需要 78 个动作的关卡的 run，通关 0 是
**设计保证的结果**，不是发现。论文若拿这 43 条 run 当「裸 CC 打不过」的
对照，那是一个不可能失败的对照——本仓库对这种东西已有名字
（`monitor/audit/DRIFT-20260730T0428Z-two-published-certifications-that-cannot-fail.md`）。

## 欠的是什么

1. **订正 `spec.py:524` 的那句话**，改成盘上能复算的形式：
   「43 条 bare_cc run，36 条有 summary 且 `levels_completed` 全为 0，
   7 条无 summary（通关数缺席），14 条为 dead run；分数从未被记录；
   每条 run 的动作预算为 20 或 30，对 g50t 关卡 1 的 78 个动作基线。」
2. **给基线臂加 `score` 列，或明确写下它不可得。** 两者都行，静默缺席不行。
3. **一条给足动作的基线对照。** 若要让基线臂的零通关成为一个能失败的对照，
   它至少需要一条 ≥78 个动作预算的 run。这条要花钱，属于 A26 同一批预算问题,
   **本件不执行，只把它写成一个明码标价的缺口**：按 bare_cc 实测
   $3.441054 / 30 个动作 = $0.1147/动作，78 个动作约 **$8.95** 一条
   （出处 `runs/bare_cc-g50t-claude-opus-5-6a39afc2/run.json`，opus 档）。
   这是全项目最便宜的一次「能不能赢」实验，比 A26 的 $120 便宜一个数量级。

## 验收

一个离线核对器读 `runs/*/run.json` 与 `MANIFEST.json`，打印上面四节的每一个
数，且 `spec.py` 与任何引用它的论文段落改成核对器能复算的措辞；核对器进
`baseline-arms` 的套件。

## 负样本，两条

* 把七条 `no_summary` 之一手工塞进一个 `levels_completed: 0`，核对器必须
  **变红**并指名该 run——它的职责就是不让缺席被补成零。
* 造一条 `budget: 100` 的 mock run，核对器必须把它从「预算不足以通关」那一
  节里排除并单列；如果它照样被算进「结构性不可能」，那这个核对器只是在
  复述结论。

---

## 对账 2026-08-04（监控·board hygiene）· 核对器落地了，被它订正的那句话没有

2026-08-02 的交付（`baseline-arms/harness/audit_zero.py` 241 行 +
`tests/test_audit_zero.py` 151 行 + `runs/.../audit_zero.json`，合入 master 于
`b27dd1e2`）**满足了本件验收的前半**，并且比正文多查了一层：分数不是没被读，
是**基线臂从不把权威分数写进自己的归档**——63 次观测（57 个 run_id）的记分卡
体全部 `score: 0.0`、`level_scores` 全零，所以零是真的；但
**43 份 `runs/bare_cc-*/run.json` 里 0 份持有那个分数**，下游读到的一直是
`levels_completed`。今天两者恰好都是零，这是巧合不是设计。交付把它记为 gap
而非 incident，理由是没有一个已发表的数是错的——这个界线划得对。

**未落地的是验收的后半**：

```
$ grep -c "46 条基线臂 run" monitor/spec.py     -> 1
```

`spec.py:525` 登记 #14 的原句一字未动，仍写着「46 条基线臂 run（裸 CC 三档
模型）最高分 0、通关 0」——本件正文逐条证伪的那句话。同一处还挂着 A30 证伪的
「15 条腿平均 15.3 个动作」。**本件保持 open，范围收窄为这一句的订正**
（正文「欠的是什么」第 1 条），以及第 2 条（给基线臂加 `score` 列或明写不可得
——`audit_zero.py` 已能恢复它，但 `run.json` 仍不持有它）。第 3 条那条 $8.95
的实验按 A34 的次序排在第 2 步，不由本件执行。

**认领冲突提醒**：本件在主树里已被 W-9207 认领（`monitor/board/claimed/`，
2026-08-04 未提交）。本节只对账不动状态；若 W-9207 正在做的就是上面这两条，
交付时把本节一并关掉即可。
