# DRIFT 2026-08-02T13:00Z · 通关阻塞已上盘，而它的三个前提里有三个不成立

**范围**：给 `monitor/board/items/` 补七件（A30–A34、S49、V31），并对今早三件
已交付的活做对账。**零花费、零封存接触、离线全程。**
不碰 `theoria-arm/runs/` 下任何含 `A26` 的目录（长腿实验在飞）。

## 一 · 新上盘的七件

| id | 领地 | 一句话 |
|---|---|---|
| `A30-the-arm-spends-its-actions-on-probes-not-on-the-level` | theoria-arm | 最长的腿 33 个动作里 28 个是探针；抬预算按现配比仍到不了 78 |
| `A31-the-win-detector-has-never-fired-and-the-round-total-turns-absence-into-zero` | theoria-arm | 22 个 `levels.jsonl` 全零字节；`round.py:188` 的 `or 0` 把缺席写成 0 |
| `A32-the-sk48-leg-pays-more-per-desk-call-and-moves-less` | theoria-arm | sk48 三轮同向：每次桌面贵 30–46%，每动作贵 2.6–4.9 倍 |
| `A33-forty-six-baseline-runs-scored-zero-is-wrong-three-times-over` | baseline-arms | 43 不是 46；`score` 键从不存在；7 条无 summary；预算 ≤30 对 78 |
| `A34-nothing-has-ever-completed-a-level-and-we-cannot-say-why` | monitor | 三条解释共用同一份证据，本项目最重要的开放问题 |
| `S49-the-12-d1-hole-is-two-rows-wide-and-the-aggregate-is-already-published` | freeze | 12-D1 的缺口是两行不是十九行，等的是一句监控裁定 |
| `V31-class-ii-cannot-be-built-and-the-request-to-build-it-was-never-boarded` | exam | 一份指出「说了 filed 没进盘」的记录，自己三天没进盘 |

## 二 · 登记 #14 的「决定性事实」，逐条重算的结果

`monitor/spec.py:524` 的那一段被当作决定性事实在用。四个数，我逐个对着盘上
文件重算。**一个对，三个不对，而且三个错的方向都是把证据说得比它实际更强。**

**对的那个：g50t 关卡 1 的 `level_baseline_actions` = 78。**
`arc-recon/data/games.json` 与
`theoria-arm/runs/20260728T015354Z-g50t-first-contact/run.json` 一致，
七级向量 `[78, 175, 179, 230, 96, 54, 67]`，合计 879。开发堆四局
（748 / 879 / 1070 / 317，合计 3014）与 `baseline-arms/BUDGET_REPORT.md:112-119`
逐字相符。**这个数是硬的，本次没有动摇它。**

**「15 条腿平均 15.3，最好 33」——腿数与均值都复算不出。**
按 `runs/*/run.json` 的 `summary.budget.actions_ok`：
非 mock 的腿 **22** 条，动作合计 **249**，均值 **11.32**；
排掉 R2 那两条 `reset_failed` 零动作腿后 **20 条，均值 12.45**。
**最大值 33 对得上**（`20260731T1430Z-A3-level2-carried-r3`）。
没有任何一个口径给出 15 条或 15.3，而这对数字只出现在 `spec.py` 里，
runs 目录中无出处。

**「46 条基线 run 最高分 0」——三处不成立。**
`baseline-arms/runs/MANIFEST.json` 自报 `"run": 43`（46 是含 excluded /
fetch / migration 的清单总数）；43 份里 **36 份有 summary，
没有一份含 `score` 键**——分数从未被记录，「最高分 0」是把
`levels_completed: 0` 读成了分数；另 7 份无 summary，通关数是**缺席**；
`dead_runs: 14`（8 `api_unusable` + 5 `model_error` + 1 `no_reset_window`）
根本没玩成。详见 A33。

**「$25 只够 32 个动作，到不了 78」——算术对，但分母错。**
那 32 个动作里，按 R2b g50t 腿的实测配比（29 个动作 24 个探针），
朝关卡走的约 5–6 个。抬预算不改配比，仍到不了。详见 A30。

**这一段不是要推翻登记 #14 的结论。** 零通关是真的，结构性到不了 78 也是真的。
要推翻的是它的**证据强度**：论文若照抄这一段，会引用一个不存在的 `score` 列、
一个凑不出的腿数、和一个把 14 条网络故障算成能力证据的分母。

## 三 · 今早三件的对账

**A23 锚点漂移 —— 已交付，无残留。**
`board.log` 2026-08-02T12:07:20Z `DONE ... by W-9202`，
`board/done/A23-anchor-drift-on-the-default-leg.W-9202.md` 在位。

**R2b 判决保留生成前沿 —— 活的一半交付，验收的一半没有。**
`theoria-arm/runs/_rounds/R2b-VERDICT.md` 三个预注册量全部达成
（宽度 2→6/8/9/10，脱靶 90.4%→22%，含答案率 9.6%→78%），
反驳条件未触发，`--frontier generated` 留树。**但 A22 的验收要的是
`round.json` 事前持有那张预测表**，而 R2 与 R2b 两份记录的 `prediction`
**都是 `null`**——事前的四行确实存在（R2 README §4），持有它们的是人不是机器。
**A22 因此不关**，正文已加对账节，范围收窄为「`round.py` 能事前收预测，
且拒绝对 R2/R2b 回填」。

**curves 缺口 —— 已修，已上 master，请求方无需再等。**
`82e8e25e`「the turn that died in flight took the leg's most expensive call
with it」是 `master` 的祖先。它答的是
`monitor/inbox/20260731T1731Z-battery-to-theoria-arm-curves-shortfall.md`：
r2 少 $1.63 / $9.56、r3 少 $1.68 / $13.44，根因是支出闸抛异常时在飞的 turn
从未 append，而 A8 自检看不见它（消失的 turn 没发过 ARC 指令，指令数因此
刚好平衡）。三层修：loop 停放在飞 turn、archive 重建无指令行并写明原因、
curves 校三个等式而非一个。`join_confidence` 保持 degraded——
「钱对上了」不许洗白 join 的把握。**这条缺口盘上没有对应 item，
所以没有可关的票；本节即它的结案记录。**

## 四 · 顺手修掉的一个静默陷阱

`A22` 的 `deps: A23` 与 `A26` 的 `deps: A24` 写的是**单元号**，而
`board.candidates()` 拿它去比 `done_ids()`，后者返回的是**完整 id**
（`A23-anchor-drift-on-the-default-leg`）。前缀永不相等，所以这两件**永远**
不会解锁——A23 今天已经交付，`board.py list` 仍然把 A22 印在 blocked 里。
两处 front matter 已改成完整 id。

代码侧同一件事另有分支在做（`agent/w-9203-board-dep-id-mismatch`）；
本次只动数据不动 `board.py`，两边不冲突：id 写全了，无论 `board.py`
将来是否接受前缀，结果都对。

## 五 · 本次没有做的，如实记下

* **没有裁 S49 的那句话。** 「19 行聚合算不算读封存局」需要一条编号的监控
  裁定进 `monitor/DECISIONS.md`；本次只把问题、量级（两行）与两个分支写清楚。
  开着的一天，`freeze/MANIFEST.json` 第 12 项就停在 partial 等一个不会自己
  来的数。
* **没有碰 `spec.py`。** 登记 #14 的订正措辞写进了 A33 与 A34 的验收，
  但登记本身是所有者与监控主检的文本，不由本次改。
* **没有读 A26 长腿的任何产物。** 它在飞。第三节的对账全部来自
  R1/R1b/R2/R2b 四轮的已归档记录。
* **`board.py list` 的验收在两处给出两个答案，两处都不是全的。**
  在本次的 worktree 里跑，`done` 是 **168**、A23/A24/S45/S46/S47/S48/V28/V29/V30
  全部印成 available——因为主树今天的 `done/` 与 `claimed/` 搬动**尚未提交**，
  worktree 从 master 检出时看不见它们。在主树跑，`done` 是 **176**、状态是对的，
  但看不见本次新加的七件（它们在分支上，按工单不合并）。
  **两处合起来才是真状态，任一处单看都会误判。** 这是
  `bus-from-worktree-goes-nowhere` 同一个病：`monitor/` 是被跟踪目录，
  每个 worktree 都有一份自己的看板。dep-id 修正已在主树侧独立验证：
  `board.done_ids()` 含 `A23-anchor-drift-on-the-default-leg`、不含 `A23`，
  所以本次的 front matter 改动落地即解锁 A22。
* **腿数 22 vs 登记的 15，我没有找出登记那 15 条是哪 15 条。**
  可能存在一个我不知道的筛选口径。记成缺口，不记成登记写错——但在有人给出
  那个口径之前，可复算的数是 22 条 / 均值 11.32。
