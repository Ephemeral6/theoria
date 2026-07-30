# S4-freeze-complete —— RES-1 cycle 36

**一句话**：两处 ⛔ 落地（引擎清单、预算表），「缺，由谁在哪补」变成闸门
（`residuals.py`，第一跑就抓出一码两义），⟨n⟩ 的可行性论证**写了一版、被自己的
对抗复核推翻、重写了一版**——而重写后的结论与第一版相反。

## 交付物

| 文件 | 是什么 |
|---|---|
| `freeze/ENGINE_MANIFEST.md` + `build_engine_manifest.py` | ⛔ 5 的答案。八个包（不是 CLAUDE.md 说的六个）、55 行钉住、枚举撞名单列一列、`--verify` 四种负对照都验过 |
| `freeze/BUDGET_TABLE.md` + `build_budget_table.py` + `BUDGET_TABLE.json` + `POOL_DIGEST.json` | ⛔ 12 的答案。三个「已花」口径分开记，12 个情景全枚举 |
| `freeze/VARIANCE_BASIS.md` | 第 13 项依据落到可哈希字节 |
| `freeze/RESIDUALS.json` + `residuals.py` | 每处缺口的 owner / 落点 / 可执行清除条件；67 条 |
| `freeze/n_feasibility.py` | 格产出率与 ⟨n⟩ 的算术，功效判据，地板封印 |
| `STATS_RULES.md` §5.7（重写版） | 见下 |
| `verify.sh` 阶段 13、14 | 各带负对照；15 个阶段全绿，2 个 NOTE |
| `launch_blockers.json` §9.11 | 从 `unimplemented` 改为 `implemented` + 命令 + 两个靶子，闸门实测 clear |

## 本轮最要紧的一件：我自己的结论被推翻

**第一版 §5.7**：拿 §5.2 发现三的 47/48 当「基础设施死亡率」乘起来，得
「q=0.979 下 n=2 只活 0.78/19 格，够到地板要 n≈63」，据此宣布 ⟨n⟩ 买不到存活率、
问题该由 §9.11 的所有者去解。**对抗性 subagent 当天推翻了它**，三条，都从字节复核过：

1. **47/48 是 harness 中止阈值的命中率，而那条阈值已被 D-016 删除。**
   47 集的 `actions_failed` 恰好都是 10（当时的**累计**失败中止常数），
   每集在 API 上成功走了 9–73 个动作（均值 30.3）。现在的规则是 **10 次连续**
   （`bare_cc.py:77`），48 集里最长连续失败串是 **5**——在今天的 harness 下
   这 48 集会记 **0** 个 `api_unusable`。D-016 自己写着「那个判定是由构造保证的，
   不是 API 挣来的」。
2. **树上有第二份已跟踪测量，第一版没引**：A7 包络（阈值修好后）9 格全部
   `budget_exhausted`、`actions_failed: 0`、成功率 1.0，即 `api_unusable` **0/9**。
   代进同一套算术，n=2 的过地板概率 **0.985**。只引悲观那一份、还称它「多半是上界」
   而不提乐观那一份存在——**这不是保守，是选边**。
3. **§7 早就给了每格 ⟨R⟩ = 3 次重跑**，所以设计上的每格曝光是 n×(1+R)；
   第一版拆了 ⟨n⟩ 却对结构完全相同的 ⟨R⟩ 一字未提。且 U3 从 Lean 产出物裁、
   不要求通关，所以「格死」对三个终点根本不是同一个事件。

**重写后**：判据从期望改成**功效**（P(出数格数 ≥ 地板) ≥ 0.80，因为 q=0.5130 时
期望正好 14 而过地板概率只有 0.617）；两份测量并排打印，各带 caveat；
§5.5 **理由三整条作废**（不是降级——一个不区分 n=1 与 n=2 的论证剩不下
「n=1 不可辩护」这半句）；⟨n⟩ = 2 仍成立，靠理由一与理由四，与 q 无关。
新增 ⛔ **13-f**：**「这一格出数了」在树上没有定义**——这才是第一版能拿一个错的 q
跑一整轮而无人能拦的根子。

顺带修掉一处我声称不可能的事：第一版写「`FLOORS` 与 `EXPECTED` 同闸门，
改一处必然让另一处红」是**假的**（`verify()` 硬编码了 14），
对抗方用变异体实测：把地板 14 改成 10，闸门绿，还把 10/19 的门槛印在 14/19 标签下。
现在地板有摘要封印，阶段 13 的负对照就打这一枪。

## 我推翻的三条 subagent「发现」

扇出会顺手多说，所以每一条结论性产出都过了一遍手：

1. **`STATS_RULES.md:684` 留一表转录瑕疵** —— **不成立**。独立复算五行全对
   （行号读错一行）。留档在 `VARIANCE_BASIS.md` §6：一次「发现」把正确的数标成错的，
   照它执行反而会造出它声称在修的缺陷。
2. **D-018「`payload.producer` is never absent」为假** —— **过头**。26 行缺该字段的
   `engine` 全是六个冻结引擎之一（枚举名即生产者），两个新引擎的 18 行全带。
   真正的缺口是**解析规则没写下来**。改在生成器里，按算法重述。
3. **`lp_potential` 不 sound（58 条假证书）** —— **narrower**：对**交给它的移动表**
   sound（独立 BFS 验过 1408/1408），那 58 条只是对**完整**移动集为假；
   且 `theoria-arm/world/adapt.py:352-358` 把它列在 `not_dispatched`，臂根本不调它。
   engine-rig 自己已在 `CORRECTIONS.md` C2 发布过。**不升级为事故**，只留一条窄条目。

## 还开着的（都有 owner，见 `RESIDUALS.json`）

* ⛔ **5-b** 八个包零版本串（engine-rig）；⛔ **8-a/8-b** 两个主终点无实现（battery，
  = §9.2/§9.14 两条开跑阻塞）；⛔ **13-f** 无产出判据（battery + 我接线）。
* **E-WORDING**：三主终点措辞在两份文件间 13 处分歧，5 处会改变公布的数
  （终点二两边都没有分母与分析单元；裁决用符号检验而 claim 正文写 Wilcoxon）。
  审计与 27 探针的 stage 16 片段已备（两个负对照都验过），**本轮未接线**——
  接线会让套件立刻红 11 项，而修措辞是下一轮的活，不是这一轮的收尾。owner：我。
* **LG-1**：`MANIFEST_DRAFT.md:5`「只要还有一项 ⛔ 就不该开跑」**没有执行体**——
  `launch_gate.py` 从不读这份文件。owner：我。
* 预算：真实余额 $111.35，最便宜的封存主表 $175.55，**即便 B=0 也差 $124.20**；
  唯一算得起的配置是已被证明 `levels_completed ≡ 0` 的那个。已写 inbox 给监控。

## 复现

```bash
bash freeze/verify.sh                          # 15 阶段，全绿，2 NOTE
python freeze/n_feasibility.py --verify        # §5.7 的每个数 + 地板封印
python freeze/residuals.py --verify            # 67 条残余各有 owner/落点/清除条件
python freeze/build_engine_manifest.py --verify
python freeze/build_budget_table.py --verify
python freeze/launch_gate.py --json            # 9.11 clear；9.2 / 9.14 仍红
```
