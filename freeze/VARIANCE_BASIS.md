# VARIANCE_BASIS —— 冻结清单第 13 项「每格重复数 ⟨n⟩」的依据

**本文只做一件事：把 `Theoria.md:368` 第 13 项的 ⟨n⟩ = 2 这个裁定，落到冻结时
可哈希的字节上。** 它不重新裁定 ⟨n⟩（裁定在 `freeze/STATS_RULES.md` §5.5），
它给那个裁定提供 `path:line` 级的可引用依据，并把依据撑不住的地方点名。

---

## 0. 先说残余（结论写在最前面，不藏在末尾）

**第 13 项的「依据不在 git 里」这个缺口已经消掉了，不是由本文消掉的，是 A14 消掉的。**

`baseline-arms/out/campaign/` 的四个文件在 HEAD 上**已被跟踪**，由提交
`9307f139`（"A14: the four campaign artefacts were paid for and were in nobody's
git"）加入，该提交是 HEAD 与 `origin/master` 的祖先。工作树对该目录
`git status --porcelain` 返回空，即索引里的字节与盘上的字节相同。
所以正确的做法是**引用那份已跟踪的形态**，而不是另造一份依据。本文照此办理。

**但第 13 项不能因此转 ✅，仍为 ⚠。** 剩下五条，每条都点名 owner：

| # | 残余 | 性质 | 谁、改哪里 |
|---|---|---|---|
| **13-a** | ~~⟨n⟩ 的唯一依据 untracked~~ | **已消解** | A14（`9307f139`，已在 master）。`MANIFEST_DRAFT.md:57` 与 `:418-421` 仍写着 untracked，是**过期陈述** |
| **13-b** | 两份包络记录未对账 | **本文消解** | 见 §4。§5 只引了两份已跟踪依据中的一份，两份对同一个量差约 **20 倍** |
| **13-c** | n=2 不替代包络本身的修复 | **原样成立** | 不变。`BUDGET_REPORT.md` §11.5 两件事修好并重跑之前，臂方差的数值主张一律不许进论文 |
| **13-d** | 代理量的方差检验**会随 ar25 一局的取舍翻面** | **本文新发现** | 见 §5。裁定不翻，但支撑裁定的那个数会翻。任何倚在 CV 数上的 ⟨n⟩ 论证都是脆的 |
| **13-e** | 生成的清单与散文的裁定**互相矛盾** | **本文新发现，最要紧的一条** | 见 §7.1。`freeze/build_manifest.py:229-243` → `freeze/MANIFEST.json` 第 13 项写着「**No value exists anywhere on master**」并声明 n=2「is withdrawn」，与 `STATS_RULES.md` §5.5 直接打架。**owner：RES-1** |

**13-e 是本文认为最该先修的。** 一个 manifest 存在的理由就是「这些字节就是战役跑
过的那些」；当生成的 manifest 说第 13 项没有值、而散文说已裁定 n=2 时，冻结包对
外给出的是**两个互斥的事实**。这比缺一个哈希坏，因为它是**在多说的方向上**错的。

---

## 1. 规则逐字，与它的两个岔口

`Theoria.md:368`，冻结清单第 13 项：

> 每格重复数 ⟨n⟩(由开发堆方差在冻结前定:方差小则 n=1 可辩护,否则 n=2)

`freeze/STATS_RULES.md:546` 转录同一句：

> ⟨n⟩ 由开发堆方差在冻结前定：**方差小则 n = 1 可辩护，否则 n = 2**。

这句话要落地，必须先答两问，而两问的答案都不在句子里：

1. **哪个量的方差？** 主终点限三个（`Theoria.md:373`）：U3 达成率、判决题准确率、
   前载指数配对差。**已跟踪的两份依据，对这三个量一个都没测到。**
2. **「小」是多小？** `Theoria.md` 不给阈值。树上唯一写下过阈值的地方是
   `freeze/STATS_RULES.s4draft.md:265-266`，取 **0.10**，并自陈
   「这个数是**判断**，不是推导——写在这里就是为了让它接受审视」。
   本文沿用 0.10，并在 §5 显示裁定正落在这个阈值的刀口上。

---

## 2. 已跟踪、可哈希的依据（HEAD = `5822e5e5c4c87e42f834ddca76f3af56eee3e7b6`）

全部经 `git show HEAD:<path>` 取字节后哈希，**不是**从工作树读的——第 13 项问的就是
冻结时可哈希，所以复算必须跑在 git 会发布的那个对象上。
复算脚本与逐行输出：`freeze/runs/20260729T2040Z-S4-freeze-complete/item13/`。

### 依据甲 · S1 基线对齐战役（§5.2 唯一引用的那份）

| path | sha256 | bytes | episodes |
|---|---|---|---|
| `baseline-arms/out/campaign/campaign_ar25.json` | `2d1d5140cdc3f6639addc98d45ef620b25bc07da8bb735c714bff240df4c183d` | 4533 | 12 |
| `baseline-arms/out/campaign/campaign_g50t.json` | `d83ba976d9c2c79429e009af48c5923d5cd14061a9cff1f6739db9ce7fe2d469` | 4537 | 12 |
| `baseline-arms/out/campaign/campaign_sk48.json` | `6683f5d72e80206b58fbcd384e32067189d49174dd13ffcec9a2dc12e6b57ab2` | 4535 | 12 |
| `baseline-arms/out/campaign/campaign_tn36.json` | `35a8c66fb97432aa0d499d3256a8d2b37ab15e0c878f2cb62cd1b411a85e47ec` | 4540 | 12 |

`arm = bare_cc`，`model = claude-haiku-4-5-20251001`，四份的
`scenario = "S1 baseline-parity"`、`started = 2026-07-27T18:19:36Z`、
`resumed_at = 2026-07-27T18:42:09Z`、`status = "episode_limit_hit"`
**逐字节相同**（已复核，见 `recompute-transcript.txt` §1）——
这正是 `STATS_RULES.md:557-584` 那条来历更正的证据，本文独立确认它成立。

### 依据乙 · A7 方差包络（§5 **没有**引用的那份）

| path | sha256 | bytes |
|---|---|---|
| `baseline-arms/runs/20260728T103135Z-a7/envelope.json` | `acefc0826642b25486456801fbad8f3ef95edb5d5ee4f9cb015de5236dcfbbd8` | 11418 |
| `baseline-arms/out/campaign_cells.jsonl` | `ebe6396e3cd3a1960b4d86bb7a71eb90da7b3d030504ed9f23f9adc43fecc54a` | 26765 |

`baseline-arms/runs/20260728T103135Z-a7/RUN_STATE.md:17-20` 写明这份包络的用途：

> ... followed by the envelope table and **the variance estimate Phase 4 needs to
> fix its per-cell repeat count ⟨n⟩**.

**即：依据乙的存在目的，就是第 13 项本身。而 `STATS_RULES.md` §5 从头到尾没引它。**
`campaign_cells.jsonl` 是 append-only 的，A7 剔掉的三格 ar25 在里面原样留着
（`campaign = "phase3-variance-envelope"`），所以 §5 的敏感性可以两面都算。

---

## 3. §5 的数字复算：逐条对得上

从依据甲的**已跟踪字节**复算，`STATS_RULES.md` §5.2 / §5.3 的数字**逐项复现**。

`STATS_RULES.md:588-593` 包络表：

| 局 | n | 均值(算) | 均值(文) | sd(算) | sd(文) | CV(算) | CV(文) | |
|---|---|---|---|---|---|---|---|---|
| ar25 | 12 | 34.42 | 34.42 | 12.06 | 12.06 | 0.351 | 0.351 | ✅ |
| g50t | 12 | 43.75 | 43.75 | 16.27 | 16.27 | 0.372 | 0.372 | ✅ |
| sk48 | 12 | 23.92 | 23.92 | 8.45 | 8.45 | 0.353 | 0.353 | ✅ |
| tn36 | 12 | 19.00 | 19.00 | 8.03 | 8.03 | 0.423 | 0.423 | ✅ |

`STATS_RULES.md:618-622` 负二项停表零模型（一参数拟合均值去预测二阶矩）：
p̂、预测 sd、观测/预测比**四局全对**，均值比 **1.0143**（文中 1.014 ✅），
`|1 − 1.0143| = 1.43%`，与 `:624`「1.4% 以内」一致。

`STATS_RULES.md:601-602` 官方基线动作数覆盖率 **2.2%–6.0%** ✅
（ar25 4.6 / g50t 5.0 / sk48 2.2 / tn36 6.0）。

`STATS_RULES.md:631-634` 基础设施死亡率 **47/48 = 0.979** ✅，
单集存活 **0.021** ✅，claim 层 `19 × 0.979 = 18.6` ✅。

`STATS_RULES.md:680-684` 留一局表：五行中四行逐位对上（见 §6 第一条）。

**结论：§5 的方差数字在已跟踪字节上复现，没有一处需要「paper over」。**
两处转录瑕疵见 §6，都不动结论。

---

## 4. 两份依据对同一个量差 20 倍（13-b 的实质）

同一个量 —— bare_cc 在开发堆上的**格内离散度** —— 两份已跟踪依据给出：

| 依据 | 格数 | 汇合格内 CV(actions_ok) | 读作 |
|---|---|---|---|
| 甲：`campaign_*.json`（中止阈值 = 累计 10 次失败，不随预算缩放） | 48 | **0.4915** | 大 |
| 乙：A7 包络，剔 ar25（30 动作预算，阈值已修） | 9 | **0.0248** | 小 |
| 乙′：A7 包络，含 ar25（预注册敏感性） | 12 | 0.0882 | 之间 |

**比值 0.4915 / 0.0248 ≈ 20 倍。** 两份都在树上，都可哈希，都是 `bare_cc` ×
haiku × 开发堆，测的是同一件事，差 20 倍。

差异有已知来源，不是谜：依据甲跑在一个**不随预算缩放的累计中止阈值**下
（`BUDGET_REPORT.md` §11.2 的近因），且 47/48 集死于 `api_unusable`；依据乙跑在
该阈值修好之后、30 动作预算下，9 格全部 `budget_exhausted`。
**但「有来源」不等于「可以只引一份」。** §5.2 发现二把依据甲的方差归给停表，
依据乙则是停表换掉之后的测量——两份并置恰好**加强**发现二，
而 §5 只引甲，读者无从看到这一点。

另有一条不能不记：**依据乙自己给的 ⟨n⟩ 不是 2，是 3。**
`envelope.json:sizing` 对每一个算得出 CV 的指标都给
`n_to_detect_25pct_difference = 3`；`RUN_STATE.md:235-239` 写明
「**n = 3 per arm** detects a 25% difference in cost or success rate at 80% power」。
`Theoria.md:368` 的菜单只有 n=1 与 n=2，**n=3 在菜单之外**，所以这不构成对 ⟨n⟩=2 的
反驳，但它是一条必须登记的紧张关系：**树上没有任何一份已跟踪依据支持 n = 1。**

---

## 5. ar25 degraded 的敏感性处理 —— 裁定不翻，支撑它的那个数会翻

### 5.1 树上的 `degraded` 到底指什么

两件不同的事，`STATS_RULES.md` §5.3 只处理了后者：

1. **依据乙里，`degraded` 是一次有书面理由的逐格剔除。**
   `envelope.json:excluded` 逐字：

   > `ar25-0c556536`: cells 3, reason: "degraded: measured under INC-BA-003's
   > concurrent-campaign load, and killed by an abort threshold that did not
   > scale with the action budget (BUDGET_REPORT 11.2). Kept in the record and in
   > every cumulative gate; **not re-run, and not used to estimate a spread that
   > would be the contention's and not the arm's**."

   `degrees_of_freedom = 6` = 9 格 − 3 局，即 ar25 已经出局。
   `baseline-arms/out/campaign_barriers.jsonl` BAR-001 与
   `baseline-arms/tests/test_envelope.py:100` 把这个剔除钉成一条有测试的约定。

2. **依据甲的 12 个 ar25 episode 没有 degraded 标注。**
   `STATS_RULES.md:651-664` 已经自己撤掉了那里的留一法：四局
   `started`/`resumed_at` 逐字节相同，48 格同等受争用影响，
   **没有干净的一局可以留下来做对照**。本文独立确认该撤回成立。

**所以真正能做 ar25 敏感性的是依据乙，而 §5 没有引依据乙。** 补上如下。

### 5.2 两面都算（3 格 ar25 从已跟踪的 `campaign_cells.jsonl` 取回）

被 A7 剔掉的三格，逐格：`actions_ok` = 11 / 14 / 19，`actions_failed` 恒 10，
`budget` = 30，`levels_completed` 恒 0，`outcome` 恒 `api_unusable`，
`started = 2026-07-27T18:21:28Z`。
（对照：依据甲起于 `18:19:36Z`。**两批确是不同批次**，这正是依据乙能提供 ar25
对照、而依据甲不能的原因。）

| | 剔除 ar25（A7 主分析） | 含 ar25（预注册敏感性） |
|---|---|---|
| 格数 / df | 9 / 6 | 12 / 8 |
| ar25 局内 CV | （出局） | **0.2756** |
| 汇合格内 CV(actions_ok) | 0.0248 | 0.0882 |
| 汇合格内 CV(动作成功率) | 0.0232 | 0.0455 |
| **局内 CV 最大值** | **0.0370** | **0.2756** |
| 局间均值 CV | 0.1178 | 0.2784 |
| **对 0.10 阈值**（`s4draft:265-266`） | **PASS —— 「方差小」** | **FAIL —— 「方差不小」** |
| **该行单独推出的 ⟨n⟩** | **n = 1 可辩护** | **n = 2** |
| U3(`levels_completed`) 方差 | 0（9/9 格恒 0） | 0（12/12 格恒 0） |
| 三个主终点里测到几个 | **0 / 3** | **0 / 3** |

### 5.3 裁决：脆的那半与不脆的那半

**必须报的第一句：代理量的方差检验会随 ar25 一局的取舍翻面。**
局内 CV 最大值 0.0370（剔）对 0.2756（含），阈值 0.10 正落在两者之间——
**0.0370 低于阈值 2.7 倍，0.2756 高于阈值 2.8 倍。**
一个由单局取舍决定的判决是**脆的**，两个数都在上面，任何倚在 CV 数上的
⟨n⟩ 论证都不许被引用为稳健。

**不翻的那半，也是裁定实际站的地方：**

* **三个主终点，两份依据、每一个子集，都是 0 / 3。** U3、判决题准确率、前载指数
  配对差，一个都没被测过。这是关于**缺什么**的陈述，与 ar25 取舍无关。
* **`levels_completed` 在所有格里恒为 0**：依据甲 48/48、依据乙 9/9、含 ar25 12/12。
  样本方差 = 0，但那是**地板效应，不是低方差**。依据乙自己把这句话写死了
  （`RUN_STATE.md:244-249`）：

  > It is identically zero in all nine cells and was zero in all twelve pilot
  > cells. ... at a 30-action budget **no repeat count whatsoever makes it
  > comparable** — n does not fix a metric with no signal.

* **剔掉 ar25 让离散度变大而不是变小**，两份依据方向一致：依据甲 0.491 → 0.540
  （+9.9%），依据乙 0.0882 → 0.0248 是反向，但依据乙里 ar25 是**被剔的那个高
  离散度局**，剔掉它是把「方差小」这一侧做得更好看——也就是说，
  **剔 ar25 这个动作本身是朝着 n=1 有利的方向做的**，而它仍然推不出 n=1，
  因为 0/3 主终点这一条挡在前面。

**落到 `Theoria.md:368` 的哪一侧：** 两份已跟踪依据对同一个量差 20 倍，
代理量阈值判决随单局取舍翻面，三个主终点零测量。
这不是「方差小」，是**方差未知**。「否则」涵盖未知。**⟨n⟩ = 2。**

**与 `STATS_RULES.md` §5.5 的关系：** §5.5 的四条理由里，
`:717-732` 的来历更正已把理由二、三降级为「须带测量条件的支持性证据」，
只留理由一（主终点没被测过）与理由四（未知被「否则」涵盖）承重。
**本文的 ar25 敏感性独立地得到同一个结论**：会翻的是代理量那一侧（理由二、三所
在的一侧），不翻的是理由一、四。§5.5 的自我限缩是对的，本文不改它，只把它验实。

---

## 6. 复算中查到的转录瑕疵：一条不成立，一条成立

> **⚠ 本节第 1 条已被 RES-1 独立复算推翻（2026-07-29，S4-freeze-complete）。
> 原文逐字保留在下面，因为「查出来的缺陷本身是假的」也必须可审计——
> 若照它去改，改的会是一个本来正确的数。**
>
> **复算结果：`STATS_RULES.md:678-684` 的留一表五行全部正确，一格都不用动。**
> RES-1 从已跟踪 blob（`git show HEAD:baseline-arms/out/campaign/campaign_*.json`，
> 与本文 §2 同源）重算，逐格对上：
>
> | 集合 | 合并 CV | 局内 CV 均值 | 局内 CV 最大 | 与文档 |
> |---|---|---|---|---|
> | 全 4 局 | 0.491 | 0.375 | 0.423 | ✅ |
> | 去掉 ar25 | 0.540 | 0.383 | 0.423 | ✅ |
> | 去掉 g50t | 0.444 | 0.376 | 0.423 | ✅ |
> | 去掉 sk48 | 0.494 | 0.382 | 0.423 | ✅ |
> | 去掉 tn36 | 0.435 | 0.359 | **0.372** | ✅ |
>
> 四局各自的 CV 是 ar25 0.351、g50t 0.372、sk48 0.353、tn36 **0.423**。
> 「最大值」列里出现 0.423 的三行，正是**没有**排除 tn36 的那三行——它出现在那里
> 是对的，不是整列抄下来的。**而「去掉 tn36」那一行文档里写的就是 0.372**，
> 本条指认的错并不在文件里。判为**行号读错一行**（把 `去掉 sk48` 行的末格
> 当成了 `去掉 tn36` 行的）。
>
> 记这一条的代价与收益：留着它，是因为它演示了一种比抄错数更贵的失败——
> **一次「发现」把一个正确的数标成错的**。若有人照单执行，会去搜 `0.423`
> 并把三行合法值之一改成 0.372，于是审计动作亲手造出了它声称在修的那个缺陷。

1. ~~**`STATS_RULES.md:684` 末格 `0.423` 应为 `0.372`。**
   该行是「去掉 tn36」，其「局内 CV 最大」应取剩下三局的最大值 =
   g50t 的 0.372。**0.423 正是 tn36 自己的 CV**，它不可能是一个已把 tn36 排除在
   外的集合的最大值——这一列被整列抄了下来。该行不被任何结论引用，故为笔误。~~
   **不成立，见上方方框。**
2. **`STATS_RULES.md:634`「clean 层 12 格里 11.7 格」精确值是 11.75**
   （`12 × 47/48`），四舍五入为 11.8。11.7 是截断。纯取整约定，无实质。

对照：同行的 claim 层 `19 × 0.979 = 18.6` 是对的（精确 18.604）。

---

## 7. 需要 RES-1 动手的地方，逐条带 path:line

本文只写 `freeze/VARIANCE_BASIS.md` 与自己的 run 目录；以下每一处都在别人的
写作面上（`build_manifest.py`、`MANIFEST_DRAFT.md`、`STATS_RULES.md` 属 RES-1 /
S4C-manifest-drift；`verify.sh` 由 RES-1 接线），故只点名，不代改。

### 7.1 最要紧：生成的清单否认这项有值（13-e）

`freeze/build_manifest.py:229-243`，第 13 项 `"status": "blocked"`，note 逐字：

> "**No value exists anywhere on master**, and this is blocked upstream rather
> than by paperwork ... Any earlier draft that recorded 'n = 2, ruled' was citing
> an unmerged file and **is withdrawn**."

这句话经 `build_manifest.py` 落进 `freeze/MANIFEST.json`，与
`STATS_RULES.md:705`「**⟨n⟩ = 2。**」和 `MANIFEST_DRAFT.md:57`「已裁定 n=2」
**直接矛盾**。该 note 写作时（第 13 项依据尚 untracked、A7 包络尚未并入）是对的，
现在两个前提都变了。**owner：RES-1**，改 `build_manifest.py` 第 13 项的 note 与
status，重跑 `python freeze/build_manifest.py`。

### 7.2 第 13 项的哈希表没有哈到依据本身

`build_manifest.py:230-231` 第 13 项的 `paths` 是
`baseline-arms/STATUS.md`、`DECISIONS.md`、`out/campaign_cells.jsonl`。
**依据甲的四个 `campaign_*.json` 与依据乙的 `envelope.json` 都不在里面。**
即：第 13 项哈了三份谈论它的文件，没哈裁定实际所依的字节。
建议 `paths` 增补（全部已跟踪，`git-blob` 可哈）：

```
"baseline-arms/out/campaign/",                              # 依据甲，4 文件
"baseline-arms/runs/20260728T103135Z-a7/envelope.json",     # 依据乙
"freeze/VARIANCE_BASIS.md",                                 # 本文
```

**owner：RES-1。**

### 7.3 过期陈述三处

| path:line | 现写 | 实况 |
|---|---|---|
| `STATS_RULES.md:553-555` | ⚠「这批数据在写作时是 untracked 的（`git ls-files` 无此路径）」 | 已跟踪于 `9307f139`，在 master 上 |
| `MANIFEST_DRAFT.md:57` | ⚠「已裁定 n=2，**但依据 untracked**」 | 同上 |
| `MANIFEST_DRAFT.md:418-421` | ⛔ 缺 13-a，「`git ls-files` 返回 **0 个文件**」 | 同上；返回 4 个文件 |

另一处不是过期而是**复述了已被撤回的说法**：`MANIFEST_DRAFT.md:425` 仍写
「`out/campaign/` 里这 48 格是**后来跑的更完整的一批**」——
`STATS_RULES.md:557-560` 的来历更正明确说这句话是错的，且「错的方向要紧」。
**owner：RES-1 / S4C-manifest-drift。**

### 7.4 原样留着的

* **13-c 不变**：`BUDGET_REPORT.md` §11.5 两件事（INC-BA-003 跨会话闸门、
  中止阈值随预算缩放）修好并重跑包络之前，臂方差的数值主张不许进论文。
  本文的 §4 / §5 都只用于裁定 ⟨n⟩，不宣称方差已知。
* **`RECONCILE.md:258` G15**（ar25 degraded 的**预注册**敏感性分析）仍未勾。
  本文 §5 供上了开发堆这一半，且按 `s4draft:272-275` 要求「两套结果并排报告」
  照做了。G15 的另一半是对封存战役的预注册承诺，不是本文能关的。
* `freeze/runs/2026-07-28T1200Z-p22/envelope_stats.py:9` 把
  `C:/Users/user/Desktop/theoria/baseline-arms/out/campaign` 硬编码成绝对路径
  （**主 checkout**）。在 worktree 里跑它会静默读到另一棵树的文件。
  与 V24「battery-blind hardcoded path」同类。本文的复算脚本改走
  `git show HEAD:<path>` 以避开这一点。

---

## 8. 给 RES-1 的 verify.sh 片段（未接线，请自行取用）

`verify.sh` stage 7 已经在复跑 §5 的算术，并且**已经**断言了来历同一性
（`scenario` / `started` / `status`），这是对的。它缺的恰好是第 13 项的那一半：
`SRC` 是按文件系统路径解析的，还带一个回落到**主 checkout** 的绝对路径
（`verify.sh:167-168`），**所以数据 untracked 时这一阶段照样绿**。
第 13 项要的是「可哈希」，而可哈希 = 被 git 跟踪。补一个断言：

```sh
# ---------------------------- 7b. item 13's basis must be TRACKED, not merely present
# Stage 7 re-runs the <n> arithmetic against a filesystem path (with an absolute
# fallback to the main checkout), so it goes green on an untracked directory --
# which is exactly the defect freeze item 13 records. `Theoria.md:368` requires
# the freeze list committed WITH ALL HASHES; an untracked file cannot be hashed,
# so an untracked basis makes the <n> ruling uncitable at freeze time.
echo "[7b] item 13: the <n> basis is tracked at HEAD (hashable, therefore citable)"
# verify.sh defines HERE but not a repo root; derive one (HERE = <repo>/freeze).
REPO="$(cd "$HERE/.." && pwd)"
n13_tracked=0
n13_missing=""
for p in baseline-arms/out/campaign/campaign_ar25.json \
         baseline-arms/out/campaign/campaign_g50t.json \
         baseline-arms/out/campaign/campaign_sk48.json \
         baseline-arms/out/campaign/campaign_tn36.json \
         baseline-arms/runs/20260728T103135Z-a7/envelope.json \
         baseline-arms/out/campaign_cells.jsonl; do
  if git -C "$REPO" ls-files --error-unmatch "$p" >/dev/null 2>&1; then
    n13_tracked=$((n13_tracked + 1))
  else
    n13_missing="$n13_missing $p"
  fi
done
if [ -n "$n13_missing" ]; then
  bad "item 13 basis NOT tracked:$n13_missing -- unhashable, so STATS_RULES.md §5 is uncitable at freeze (MANIFEST_DRAFT gap 13-a is live again)"
else
  ok "all 6 item-13 basis files tracked at HEAD ($n13_tracked/6)"
fi
# index must equal disk, or the hash describes bytes nobody ran
if [ -n "$(git -C "$REPO" status --porcelain -- baseline-arms/out/campaign baseline-arms/out/campaign_cells.jsonl baseline-arms/runs/20260728T103135Z-a7/envelope.json)" ]; then
  bad "item 13 basis is tracked but DIRTY -- the hash would not describe what was measured"
else
  ok "item 13 basis clean (index == disk)"
fi
# negative control: the check must be able to go red
git -C "$REPO" ls-files --error-unmatch baseline-arms/out/campaign/NOPE.json >/dev/null 2>&1 \
  && bad "negative control failed: ls-files matched a path that does not exist" \
  || ok "negative control fires: an untracked path is detected as untracked"
echo
```

`$REPO` 需为仓库根（stage 7 用的是 `$HERE/../..`）。**这段没有接进
`verify.sh`**——本 worktree 有另外两个 subagent 在写，接线由 RES-1 做。

一条可选的加固（本文不主张必做）：把 stage 7 的 `SRC` 从文件系统路径改为
`git show HEAD:` 取字节，那样 stage 7 与 7b 就合成一件事，且不可能读到
另一棵树的文件。代价是 stage 7 不再能在未提交的工作树上给出预览。

---

## 9. 一句话总账

⟨n⟩ = 2 的依据**现在是可哈希的**（`9307f139` 之后，共 6 个已跟踪文件，
sha256 见 §2），**§5 的数字在这些字节上逐项复现**，
**裁定在 ar25 取舍下不翻**——但它站住靠的是「三个主终点零测量」，
不是靠任何一个方差数；那个方差数**会翻**（局内 CV 最大 0.0370 ↔ 0.2756，
阈值 0.10 夹在中间），且两份已跟踪依据对它差 20 倍。
**第 13 项因此仍为 ⚠，主要残余是 13-e：生成的 `MANIFEST.json` 还在说这项没有值。**
