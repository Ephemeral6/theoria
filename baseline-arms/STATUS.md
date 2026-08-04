# baseline-arms — 状态

本轨道只做两件与 Theoria 框架本身无关的事：**裸 Claude Code 跨模型跑分**、
**Schema 复现数据收集**。不碰理论、不碰引擎、不碰 DSL。

| 里程碑 | tag | 状态 |
|---|---|---|
| M1 既存状态审计 | `baseline-arms-m1-audit` | ✅ 达成 |
| M2 裸 CC harness + 记账管线 | `baseline-arms-m2-harness` | ✅ 达成 |
| M3 Schema 官方发布物定位 | `baseline-arms-m3-schema-locate` | ✅ 达成（判定为「找不到」支） |
| M4 试点 + 预算闸门 | `baseline-arms-m4-pilot-gate` | ✅ 达成 |
| M5 方差包络战役 | `baseline-arms-m5-variance` | ⚠️ **G4 二次触发，停在 2/4 局** |
| M6 Schema 路 A 材料 | `baseline-arms-m6-path-a` | ✅ 达成 |
| A14 花过钱的产物入库 | — | ✅ 达成（2026-07-29） |
| M7 账本正典迁移（F-16） | — | ✅ 达成 |
| M8 溯源档案 `runs/`（METHOD 8/9） | — | ✅ 达成 |

文档：[`AUDIT.md`](AUDIT.md)（第 0 步审计）·
[`SCHEMA_LOCATE.md`](SCHEMA_LOCATE.md)（M3 结论）·
[`SCHEMA_PATH_A.md`](SCHEMA_PATH_A.md)（M6 路 A 执行结果）·
[`DECISIONS.md`](DECISIONS.md)（设计决策）·
[`INCIDENTS.md`](INCIDENTS.md)（事件）·
[`TOUCHED_GAMES.md`](TOUCHED_GAMES.md)（触碰登记）·
[`BUDGET_REPORT.md`](BUDGET_REPORT.md)（闸门，§9 是可执行的止损条件）·
[`runs/MANIFEST.json`](runs/MANIFEST.json)（溯源档案索引）

---

## 本轨道的规矩：花过钱的产物，要么入库，要么留哈希，**不许两样都没有**

这条不是提醒，是可执行的：`COST_ARTEFACTS.json` 是它的登记表，
`harness/cost_artefacts.py` 是裁决它的代码，`verify.py` 第三关会跑。

```bash
cd baseline-arms && python -m harness.cost_artefacts     # 单独看
cd baseline-arms && python verify.py                     # 三关，含这一关
```

两种处置，差别在于登记表**承诺了什么**：

* `committed` —— 载荷在 git 里。文件必须在、必须被跟踪、字节必须哈希到登记的值。
  三样缺一即红。**一个被当作证据引用过、之后又被改动的产物，比从没入库更糟**。
* `hash-only` —— 载荷刻意不入库（体积、或上游许可不允许转发）。哈希与出处就是记录。
  文件**可以不在**，那正是这个处置买到的东西；但只要它在，就必须对得上。

新增花钱的产物时，改 `runs/20260729T100000Z-a14/build_register.py` 里的策略字段
再 `--write` 重新生成，**不要手改 `COST_ARTEFACTS.json`**——它是生成物，
`--check` 会逐字节比对。

### 这条规矩是怎么来的（A14，2026-07-29）

`git ls-files baseline-arms/out/campaign` 当时是**空的**。四份裸 CC 全战役检查点
（自报 $48.39，**实际全成本 $50.39**）连同它们的四份分片账本，躺在一台机器的
工作树里没被跟踪，而**同时有五个领地在引用它们的 sha256 当证据**——
`battery` 的 v3 MANIFEST、`figures/SOURCES.sha256`、
`battery/artifacts/capability_spectrum.json`、`proxy/CANON_MIGRATION.md`、
`proxy/runs/p9-shell-harden/`。一次 `git clean`，主表裸 CC 那一列就没有来源了。

**先核对再入库**：四份检查点 + 四份账本共 8 个 sha256 与 battery 记的逐字节相等，
没有「被消费之后又被改过」的情况，所以这是抢救，不是事件。

**入库路上的坑，值得单独记一笔**：四份检查点在盘上是 **CRLF**（harness 在
Windows 上用 Python 文本模式写的），而 battery 钉的哈希正是对这些 CRLF 字节取的。
本领地 `.gitattributes` 有 `* text eol=lf`，直接 `git add` 会把它们规范化成 LF，
于是**任何一次 clone 拿到的文件，哈希都不再等于已经被引用的那个值**——
而且全程没有任何报错。所以加了 `out/campaign/*.json -text diff`，
并用 `tests/test_cost_artefacts.py::test_committed_campaign_json_bytes_survive_git`
把这条规则钉住：规则被删掉，测试就红。空白对照做过了——不加这条规则时
blob 与磁盘的哈希确实不同，加上就相同。

顺带解开一个死结：`verify.py` 此前把 `harness.campaign_status` 排除在关口之外，
理由正是「它读 `out/campaign/`，而那是未跟踪的，干净检出上必红」。
检查点入库之后这个理由不成立了，它现在是第三关的一部分。
**这一点比抢救本身更值钱：干净检出上读不到的产物，还不算证据。**

分片账本一并入库（55 MB 原始）——它们是主记录、被 battery 钉了哈希当证据、且它们的 run_id 不出现在任何别的已跟踪账本里。（初稿还写过第四条理由「它们是那 $2.01 差额唯一的存活痕迹」，**该条为假、已撤回**：`figures/audit/reconcile_cost.csv` 与 `battery/artifacts/capability_spectrum.json` 在 A14 之前就已被跟踪，两者都载有那 8 个孤儿 run。）**许可分级已按 `release/LICENCE_POSTURE.md` 补记**：12 份里 8 份是 class B（api 派生汇编，需书面许可、发布默认排除），4 份检查点是 class C。入库是**持有**不是**发布**——该文件原话「Holding is permitted; publishing is not」——且发布闸是内容判定的，`release/enumerate.py` 无需名单即把这 8 份判为 B。
体积不是理由：这些是重复的整数网格，逐对象实测
（`git cat-file --batch-check='%(objectsize:disk)'`）**63,993,495 B 的工作树载荷
只占 1,009,964 B 的 pack 存储**，63.4 倍；最大的 `ledger.g50t.jsonl` 原始
38.3 MB、入库 607 KB。清单与逐条理由见
[`runs/20260729T100000Z-a14/INVENTORY.md`](runs/20260729T100000Z-a14/INVENTORY.md)，
账目见 [`RECONCILIATION.md`](runs/20260729T100000Z-a14/RECONCILIATION.md)。

---

## P-12 那一轮（2026-07-28）：**部分采纳**，先读这一段再读下一段

下一段是 P-12 分支交付时写的原文，逐字保留。它描述的东西**有一半没有进主线**，
所以先说清楚哪一半：

| P-12 交付的 | 处置 |
|---|---|
| `harness/interlock.py` 互锁模块 | **采纳**，接进 `campaign` / `run_pilot` / `bare_cc` 三个花钱入口 |
| 互锁接进 `run_campaign` | **未采纳**（该文件整取主线）——缺口在 `tests/test_interlock.py` 里被断言 |
| F-15 裁决通道 `harness/adjudications.py` | **采纳为模块与记录**；主线闸门不读它，读的是 barrier |
| 「G6a 改坐班 + 新增 G6c」的闸门时钟 | **未采纳**（D-022）。主线用 barrier 分段，不引入 sittings |
| 账本正典迁移 F-16（`migrate_ledger` / `validate_canon`） | **采纳**，产物在 `runs/_migrations/` |
| 溯源档案 `runs/`（20 条 → 现 46 **条目**，其中 43 条是 run） | **采纳**，并按合并后的证据重建 |
| 那一轮真实花掉的 $1.68 与三个 tn36 格 | **采纳**：账本、probe_log、cells、run.json 四处齐全 |

**原因**：那一轮把闸门重写成 `adjudications` / `interlock` / `g4_suspended` /
`sittings` / `attach_exposure`；主线同期把它写成 `barriers` /
`campaign_barriers.jsonl` / `judged` / 每战役一份 `gate_path(campaign)`。
**两者是互斥的方案，不是可以叠起来的两层**，同一个 `run_campaign.py` 上 13 处冲突。
所有权裁决取主线，`run_campaign.py` 整份取主线版本，
`tests/test_gate_clocks.py` 与 `tests/test_gate_g4.py` 一并删除（共 31 例）。
详见 `DECISIONS.md` D-020…D-025 与本次合并提交。

**必须一并知道的一件事（合并引入的，需要一个所有者裁决）**：那三个 tn36 死格
进了 `out/campaign_cells.jsonl` 之后，用主线的闸门**现算**会判 **红**——
G4（两个连续死格）与 G6a（judged 段的起点被这三个更早的格子往前推，算出 75 h）。
`out/campaign_gate.json` 里躺着的仍是主线那份**绿**的快照（裁决要求整取主线）。
**落盘的判定与现算的判定现在不一致**，这不是可以忽略的差异：
G4 那一条是真的（那一轮确实红着停在 2/4 局），G6a 那一条是主线单时钟设计下的假阳性
——正是 D-022 想修而未被采纳的那个问题。开跑之前必须有人裁决，不要读那份绿快照当放行。

---

## 本轮（P-12）结果摘要

### 包络续跑：**G4 第二次触发，停在 2/4 局**——这是工单允许的唯一一种停

前置条件先解决了：对方那场 S1 全量四局跑完（48 集 / 1453 动作 / $48.39 /
**0 通关**），互锁放行。**先跑 tn36 而不是 g50t**，因为开跑时另一个轨道正用
opus-5 打 g50t，同局并发是最尖锐的争用，换个顺序不花钱。

三格全死：`api_unusable`（17 ok / 10 failed）、`api_unusable`（10 / 10）、
**`no_reset_window`（0 / 0，30 次 RESET 全被拒，$0）**。闸门判红，
`sk48` / `g50t` **未开跑**，`run_campaign` 拒开并退出码 3。本轮花 $1.68，
累计包络 $4.21——**钱又一次不是停下的原因**。

三件必须分开说的（详见 [`BUDGET_REPORT.md`](BUDGET_REPORT.md) §15，合并时由 §12 顺延）：

* **`actions_failed >= 10` 的绝对阈值又来了。** 两个跑起来的格子失败数**都恰好是
  10**，和 ar25 三格同一个指纹。§11.5 第 2 条至今未修，本轮**也没有修**——
  工单要「按原协议续跑」，改阈值就不是原协议，而且那正是 §11.3 拒绝的动作。
* **`no_reset_window` 那一格的 0 不是臂的方差**，是它根本没拿到会话
  （tn36 本轮 RESET 成功率实测 **6/63 ≈ 9.5%**）。把它计进去，成功动作
  cv 从 **0.367**（只算真正开起来的两格）膨胀到 **0.949**。
  **0.949 不该拿去定 Phase 4 的 ⟨n⟩。** 本轨道不自行删格，但这条写在数字旁边。
* **对账义务本轮 0/3 完成**，比 P-7 更差：24 次 scorecard 关闭全部 404。
  如实登记，不回填。

劣化仍在（成功率 0.574、HTTP/动作 9.56、$/动作 0.0622，三项都比试点差），
**但已不能再归因于 INC-BA-003**——同轨道并发消除了。剩下两个候选解释
（仓库 25 个并发 worktree 的跨轨道争用 / ARC 侧本身更不稳）本轮数据分不开，
**没有为了区分它们再花钱**。

### 另外三件事

外加开工时发现的一件必须先解决的。

### 先解决的那件：包络续跑的前置条件在开工时**并未满足**

`BUDGET_REPORT.md` §11.5 把「先解决 INC-BA-003」写成复跑的前置条件。开工时对方那场
S1 全量**仍在跑**（g50t 第 9 集、sk48 第 11 集，两场合计已花约 $42）。照工单直接开跑，
量到的还是争用——§11.2 已经证过一次。

处置是把那句话变成一个检查：`harness/interlock.py`（`DECISIONS.md` D-021），
两个独立信号（进程表 + 跨 worktree 的检查点新鲜度），两个都拿不到时判阻塞，无 override。
配套把 INC-BA-003 抱怨的「谁都看不见合计数」补上：`campaign_gate.json` 现在带
`combined_exposure`。

顺带**跑一次真的就抓到一个假阳性**：`--gate-only` 是只读的，却被算成一场活着的战役——
一个会对自己的诊断说「不」的互锁。已修，见提交 `6b19d38`。

### 闸门的两处改动（都必须被当成改动来审，不是背景噪声）

1. **F-15 落地通道**（D-020）。闸门是从 `campaign_cells.jsonl` 现算的，三个 ar25 死格
   就在文件头，`--gate-only` 判红，`run_campaign` 拒开任何一局——**不给裁决一条通道，
   F-15 就无法执行**。`harness/adjudications.py` 是能想到的最窄的通道：
   只有 `G4` 可挂起、只对逐条点名的 `run_id`、点名其他子句在写入和读取时各被拒一次、
   轨道不能自裁。那三格花的 $2.5275 仍进每一个 cap。
2. **G6a 改量「坐班」，新增 G6c**（D-022）。**8 h 的 cap 一个字没动。**
   原来的 G6a 从第一行起算，在包络停摆的六个多小时里一直走，开工时读到 6.2 h——
   等对方战役跑完就会先撞上 8 h。**遵守 §11.5 会触发 §11.5 要求你在其之下遵守的子句。**
   连续跑满八小时照样触发；日历时钟真正抓得住的残余移进 G6c（原先不存在），
   所以闸门净增一条约束。

### 账本正典迁移（F-16）：**完成**

`harness/migrate_ledger.py`，560 条全部抬进 v1.0，原文件未动，产物在
`runs/_migrations/ledger-v0-to-v1.0/`。四个来源等级逐字段标注。
join 命中：card_id 268/286、guid 266/286、arm 274/274。

**抬不动的必须点名**：`model_call.request` / `response` v0 只记了长度和错误标志，
而正典把逐字记录定为模型侧不可重放的替代品——**每一条被抬上来的 model_call 都永久
不可重放**，这个洞只能由 proxy 对未来的运行补。`score` 不是忘了记，上游响应里就没有。
（A33 2026-08-04 补正：这句话只对 **gameplay** 响应成立。权威分数在 scorecard body
上，而本臂把其中一部分归档进了 `probe_log.jsonl`——`harness.score_column` 离线复原了
43 条已归档 run 中 **20 条**的分数，全部 0.0；另 15 条的卡已永久 404（D-015）、8 条
从未记过 `card_id`，那 23 条不可得。所以正确说法是「分数在 run.json 里从未有过，
但并非全臂不可得」。）
金额移进 sidecar（正典禁止账本里出现美元数）。
4 条 `ACTION0` 原样保留并标记——请求真的发出去过。

261 例 fuzz，核心不变量是**键守恒**：输入的每一个键要么映射、要么在 `lift_unmapped`、
要么在 `lift_dropped_to_sidecar`。

顺带发现两件与 proxy 有关的事，已在 PARTNER_SYNC 登记：
`proxy/tools/validate_ledger.py` 与 `upgrade_ledger.py` **都不存在**（`proxy/tools/`
这个目录没有），而 `LEDGER_FORMAT.md` 用现在时描述它们；§7 对 v0 的描述说有 8 个键，
实际有 24 个。

### 溯源档案 `runs/`：**完成**

20 条：17 个 run（其中 **10 个是死 run**，同等归档）、路 A 那次抓取、这次迁移、
以及一条「**故意没归档什么**」。`prompt_id` 对 P-12 之前的活标 `retro:P-7`。
`seed` 一律留空并写明原因——本臂没有 seed，填一个数会比留空更糟。

顺带修掉三个只在「第二局落地时才咬人」的缺陷（提交 `fa462a2`）：
`summarise_campaign` 的 (game, model) 折叠会静默丢格；它没有任何办法表达
F-15 要求的「degraded 单独一行」；`audit_cells` 的封存前缀是子串匹配，
对 8 位十六进制的 run_id 尾巴有约 1.5%/百条的**假阳性**——而它印出来的是
「sealed ids present」，跟真事故长得一模一样。

---

## 上一轮（P-7）结果摘要

### M5 方差包络：**闸门 G4 触发，跑完第 1 局即停**

`ar25-0c556536` × haiku × 3 次重复跑完，**三格全部 `api_unusable`**，
闸门判红，`g50t` / `sk48` / `tn36` **未开跑**。花费 $2.5275（G1 上限 $50 的 5.1%）。

停下的判断分两层，`BUDGET_REPORT.md` §11 详述：

* **真实劣化**：与试点同档对比，动作成功率 0.713→0.595，HTTP/动作 7.11→9.66，
  $/动作 +68%。三项同向，与 INC-BA-003（三套负载并发压同一 API）吻合。
* **阈值假象**：三格失败动作数**全是 10，标准差 0**——那是
  `actions_failed >= 10` 这个**不随预算缩放的绝对阈值**。成功率 0.6 时，
  30 动作预算下期望失败约 12，撞上它几乎是注定的。§7 原写「连续 10 次」，
  **该表述有误，实为累计**，已更正。

**没有为了过闸门去调大那个阈值。** 修法与顺序写在 §11.5。

拿到的仍是一个**真实但被截尾**的包络（`harness/summarise_campaign.py`）：

| 量 | 均值 | 标准差 | CV |
|---|---|---|---|
| 成功动作 | 14.67 | 4.04 | 0.276 |
| 成本 $ | 0.843 | 0.142 | 0.169 |
| 缓存读 tokens | 601,990 | 98,632 | 0.164 |
| HTTP 调用 | 141.7 | 13.5 | 0.095 |
| 墙钟 s | 1174.8 | 150.1 | 0.128 |

**顺带补上主表的一个空格**：`Theoria.md` 1.12 的裸 CC 行「单局缓存读」记作
「—（基线口径）」，即从未测过。本轮测到了：**每局约 6.0×10⁵**，
30 动作预算、被截尾在约 15 个成功动作。这是 claim C5（10⁸→10⁶）的分母侧原料。
本轨道不改 `Theoria.md`，数字在此备查。

### M6 Schema 路 A：**完成**

上游轨迹**只取开发堆 4 局**：165 文件 / 87.7 MB 到手，
**885 个属于 21 局封存游戏的文件一个都没请求过内容**，8 个跨局聚合文件默认拒绝。
**落盘封存路径数：0**（主上下文独立复核，不采信子代理自报）。
详见 [`SCHEMA_PATH_A.md`](SCHEMA_PATH_A.md)。

守卫第一次执行就 `allow=0` 全拒——上游只写 4 字符前缀而白名单当时只测完整 id。
**朝安全方向失败**，子代理照令停下未自行放宽。修正后补 `tests/test_whitelist.py`
（19 例全过）。

顺带**验证了切分未被改动**：`piles.json` 内 `sha256` 字段用的口径已反推出来并复算，
与 `CLAUDE.md` 钉住的 `3feca53e…41bbc19a` 逐字相等，`cut_version: v1`。

### 两个副产物，都比原计划的产出更有用

1. **配额口径有实测答案了**（`BUDGET_REPORT.md` §4.1）：scorecard 的
   `total_actions` **只计成功动作，失败的 400 不计**，3/3 一致，跨两个模型档、
   两个游戏、两次战役。§4 悬了很久的 9.7 倍不确定性因此收窄到乐观那一端。
2. **一个静默的记账缺陷被发现并修好**（`DECISIONS.md` D-015）：
   scorecard 关闭此前不重试，试点 23 次关闭 22 次 404，
   而**关掉的卡取不回来**——14 个试点格只剩 1 格可对账，
   Phase 1 的对账义务此前实际无法履行。已补重试，并用「快照仍打开的卡」
   抢救回本轮 3 格中的 2 格。

---

## 缺口与阻塞

### GAP-5（新，2026-07-31 清理战役登记）：本轨道的凭据仍在臂进程里，且不走环境代理

**只登记，不改代码。** 这一条不是本轨道犯的错，是**规矩后来变严了**，本段把差
距写下来，免得下一个会话把「其他臂已经封印了」误读成本轨道也封印了。

事实，逐条可查：

* `harness/arc_client.py:137` 的 `load_api_key()` 直接打开 `.env` 取
  `ARC_API_KEY`，`arc_client.py:199` 把它存进 `self._key`；调用直接打到 ARC，
  **不经过 `proxy/` 的环境代理**。凭据因此常驻臂进程，整个 run 期间都在。
* `Theoria.md` 第一阶段的封印是个合取：臂进程摸不到环境凭据，**且**绕过两个代理
  的出口必须失败。本轨道两个合取项都不满足——没有代理，也就没有第二项可谈。
* 时间线是这样的：本轨道 M5/M6 写在这条裁决落地之前，`theoria-arm` 到
  2026-07-31 才把环境代理改成**子进程**（`theoria-arm/harness/proxy_process.py`，
  臂进程自己不再读 `.env`）。本轨道的设计**早于**那次裁决，不是无视它。

处置，两个臂分开判：

* **schema 复现臂：已退役，判定为「只记不修」。** M3 已裁官方 release
  「找不到」（[`SCHEMA_LOCATE.md`](SCHEMA_LOCATE.md)），这个臂从未成为会打游戏的
  harness（M6 只有路 A 材料）。一个不再开跑的臂不值得为它改客户端；本段与
  [`AUDIT.md`](AUDIT.md) 的登记就是它的全部处置。
* **`bare_cc`：没有退役，所以这是一个真阻塞。** M5 方差战役停在闸门红 1/4，
  `agent/p12-envelope-finish` 打算续跑。**在再花一分钱之前**，`arc_client` 需要
  真修：加一个 `ARC_BASE_URL` 之类的代理指向、去掉自己读 key 的那条路径，
  `run_pilot.py` / `run_campaign.py` 复用 `theoria-arm` 那个
  `EnvProxyProcess`——它是臂无关的，run_id / arm / campaign / reservation 都是
  参数。在那之前的临时管制是 [`BUDGET_REPORT.md`](BUDGET_REPORT.md) §9 的停跑
  条件：**客户端未接代理，不得线上续跑**。
* `harness/bare_cc.py:186` 已经在起 `claude -p` 之前 `env.pop("ARC_API_KEY")`，
  那一行是对的，**保留**。它挡的是模型子进程，不是本条说的臂进程常驻。

#### GAP-5 结清（A19，2026-08-01）：**已拆分**，不再是「只登记」

上面那一段是登记，这一段是处置。凭据已经出臂进程，做法与
[`DECISIONS.md`](DECISIONS.md) D-026 记的一致：一个本轨道自己的**透明转发子进程**，
不是接 `proxy/env_proxy.py`（理由见 D-026，一句话是接了会把同一笔 ARC 动作
向共享池计两次费，并给一场战役造出两本互不兼容的账）。

落地的东西，逐条可查：

* **新增** `harness/key_proxy_server.py` —— 全轨道**唯一**还会读 `.env` 的代码，
  且它只在子进程里跑。注入 `X-API-Key`，其余（方法、路径、查询串、body、
  cookie、状态码、响应体）原样转发。
* **新增** `harness/key_proxy.py` —— 父进程侧的监管者，**里面没有任何读凭据的代码**。
  子进程握手用文件不用 stdout（本机 cp936 会把 banner 搞成乱码），
  停止先 HTTP 后 `TerminateProcess`，父进程被硬杀时子进程有自己的看门狗。
* **`arc_client.py:137` 的 `load_api_key()` 现在抛 `CredentialInArmError`**，
  函数保留不删：GAP-5 上一段是按行号点名它的，顺着指针来的人应当落在解释上，
  而不是落在一个「找不到这个名字」的报错上。
* **`arc_client.py:199` 的 `self._key = api_key or load_api_key()` 变成
  `self._key = api_key`**，没有回退读取。臂默认无钥。
* **第二个合取项也补上了**：无钥客户端指向真上游时抛 `UnproxiedEgressError`，
  在开 socket 之前、在向共享池计费之前。反过来，子进程收到带 `X-API-Key`
  的请求一律 `400 ARM_SENT_A_KEY` 拒转 —— 代理不能变成替 GAP-5 遮丑的东西。
* **五个花钱入口全部接上**：`run_pilot.py`、`run_campaign.py`、`campaign.py`、
  `probe_api.py`、`probe_action_variants.py`。

**没有动的东西，是刻意的**：cookie jar、probe log、spend 闸门、封存堆守卫全部留在臂里，
因为 BUDGET_REPORT 要重新推导的每一个数都是在它们上面测的。jar 能跨这一跳存活，
靠的是子进程把 `Set-Cookie` 的 `Domain=` 与 `Secure` 两个属性去掉
（回环这一跳既不是那个域名也不是 https），其余属性原样保留。
`probe_log.jsonl` 的 `url` 字段仍写规范上游地址，新增 `wire_url` / `proxied`
两个字段记实际那一跳 —— 否则本单之后写的每一行都会与之前的行不可比。

验收：`tests/test_seal_process.py`，19 条，全 mock 零花费零网络。
其中第一条在**全新解释器**里把 `ARC_API_KEY` 从环境里删掉后跑完一整局
mock 游戏（开卡 / RESET / 三个 ACTION / 关卡），`claude -p` 由罐头信封替代。
套件 552 passed / 1 skipped / 0 failed。

**一处自己踩到的坑，记下来**：`resolve_key` 第一版写成「先读 `.env`，读不到再退到无钥」，
于是那条**专门用来证明「无钥代理什么都不注入」的负样本**，在任何存在 `.env` 的机器上
都会起一个握着真凭据的子进程。是这条负样本自己在一小时内抓到的（断言先失败，
没有打印也没有落盘任何值）。现已改为 `--no-require-key` 即**明确无钥、根本不看 `.env`**，
并补了一条与机器无关的 `resolve_key` 单测钉住它。**「可选的凭据」不是凭据策略。**

commit：**`db33f983`**（分支 `agent/a19-bare-cc-seal-split`，tag
`a19-bare-cc-seal-split`）。本段的 sha 由紧随其后的一次提交补记——一次提交无法
写进自己的哈希。留痕在 [`runs/2026-08-01T044513Z-A19/`](runs/2026-08-01T044513Z-A19/)。

**复飞资格不由本工单裁定。** 本单交付的是拆分与证据；`bare_cc` 是否恢复线上飞行、
`p1-seal-test` 左合取项是否对三臂成立，是监控方的再裁决。

### GAP-4（新，A14 发现）：战役重启会把已花的钱从账上抹掉

四份检查点每份的 `episodes[]` 只列 12 个 run，而对应的分片账本里有 **14** 个。
多出来的两个是**被放弃的前两次 harness 启动**：每份日志有三行 `campaign:` 头，
每次启动都重新打印 `$0.00 of $<ceiling> spent`。**花费计数器在重启时归零**，
那笔钱既没进 `cost_usd`，也没进预算上限的核算。四局合计 **$2.0071**。

这次没有撞破闸门（四个上限合计 $164.93，都没接近），但它是记账管线的真缺陷，
和 D-015 那个「关卡不重试」是同一类：**静默地少记**。

A14 是抢救工单，只记录不修。修法应在 `harness/campaign.py` 的 resume 路径上
累加而非重置，并补一个「账本 run_id 数 == episodes 数」的断言。
数字与推导见 [`RECONCILIATION.md`](runs/20260729T100000Z-a14/RECONCILIATION.md)。

**另外**：这四场战役当时**根本没有 `runs/<id>/MANIFEST.json`**，留痕正典没被遵守。
A14 事后补了一份并标明是事后补的。

### GAP-3（新）：并发战役——本轨道当前有两套互不可见的闸门

`INCIDENTS.md` INC-BA-003。另一个会话在同一目录并发跑 §3.4 的 S1 全量
（$103 / 46 h），与本会话的包络共用同一份 ARC 配额与同一个账单，
**两边的闸门各算各的总账，谁都看不见合计数**。这是 M5 停在 1/4 的远因。

复跑包络之前必须先解决它——否则测到的是争用的方差，不是臂的方差。
修法（共享闸门文件由所有战役进程共同累计）已记入 INC-BA-003，
**归人工与对方会话，本会话不代决**。

### GAP-1（工作二整体）：Schema 复现**不可能**，`⟨复现值⟩` 合规留空

**P-7 更新：这条依然成立，但它的下游影响被路 A 解掉了一半。**
Phase 2 指标电池要的「已知能力梯度（CC vs Schema）」两侧材料现在都有了——
Schema 侧是 M6 拉到的上游轨迹，CC 侧是本轨道的账本。
但 `⟨复现值⟩` 那一格仍应**留空**：路 A 拿到的是**上游的账本**，不是**我们的复现**。
见 [`SCHEMA_PATH_A.md`](SCHEMA_PATH_A.md) §6。

官方 harness 代码**从未发布**——`schema-harness` 这个 GitHub 组织下只有项目主页
仓库本身，主页也没有任何代码发布承诺。没有正式论文（只有一篇网页 + `@misc`
BibTeX），没有 arXiv id。轨迹 artifacts 倒是公开发布了，但**复现需要的是代码**。

按工单停止条件 3 处置：记录缺口，继续做裸 CC 那部分，**不用替代实现冒充复现**。
`Theoria.md:271` 主表里 Schema 那一格保持空白。详见
[`SCHEMA_LOCATE.md`](SCHEMA_LOCATE.md)，含闸门之后的三条可选路径
（推荐路 A：只取开发堆 4 局的上游轨迹，`Theoria.md:311` 已明确许可）。

顺带一条应订正的事实：规范署名是 **Zeng et al.**，不是 Feng et al.
（Haiwen Feng 是末位作者）。`Theoria.md` 不属本轨道，不代改。

### INC-BA-001（blocking，对受影响的封存局）：检索 Schema 发布物的过程污染了 9 局封存游戏

M3 的检索子代理在判断出页面不安全之前，已读到若干**封存堆**游戏的机制描述。
`ls20-9607627b` 与 `ft09-0d8bbf25` 属实质泄露。污染局限在该子代理的上下文里，
它未向本轨道转述任何机制内容；本轨道主上下文只有「哪几局被污染」的清单。

处置归 `arc-recon` 与人工决定，本轨道不代改 `contamination_log.jsonl` /
`piles.json`。详见 [`INCIDENTS.md`](INCIDENTS.md)。

**这一条不构成本轮停止**：它不影响开发堆上的裸 CC 试点，且相关调用（公网检索）
已终止，本轨道不会再打开那些页面。

### 已解除：`INC-002` 不成立，在线 API 可用（arc-recon 已正式改判）

`arc-recon` 的 `INC-002` 结论是「零次成功动作……整个在线 API 路线受阻」。
本轨道独立复核后推翻该诊断：`400 "game <id> not found"` 是**瞬时故障**，
重试即可推进。详见 [`AUDIT.md`](AUDIT.md) §6 与 `DECISIONS.md` D-005。
代价是每次成功动作平均约 5 次 HTTP 调用。

**2026-07-27 后续**：arc-recon 已据此正式改判（其 `incidents.jsonl` 的
INC-001b / INC-002a），并把确定性预检在开发堆 4 局全部跑到 **PASS**。
两条修正需要本轨道注意：(1) 故障是**约 1–3 分钟的波浪式不可用**，重试包络要
能盖过整个波（其预检用 40 次尝试、退避上限 5s），HTTP 放大实测 2.5–10×，
比本轨道的 5.07× 更悲观；(2) **H-A「短 ID 可用」被更正为伪响应**
（见 [`INCIDENTS.md`](INCIDENTS.md) INC-BA-002），请求体一律用全 ID。
另：tn36 的 `ACTION6` 服务端恒 500，click 族在 data 形状解决前无法真玩。

---

## 一个应当记下的疑虑

工单给的既存状态线索——`ADR-0014`、`INC-0008`、「25 局复现战役」——
**在本仓库全部 0 命中**。本仓库根本没有 ADR 编号体系，事件编号是三位数
`INC-001..003`。最可能的解释是工单针对另一个分支或另一份仓库的历史写成。

按工单要求如实登记，但**不因此停下**：不存在既有权威数据，就不存在冲突结论的
风险，本轨道是这项工作的第一次开工。真正需要防的是反向风险——本轨道自己的账本
必须从第一行起就与未来的 `arc-gateway` 兼容，否则**我们自己**会制造那个分叉。
已按 `DECISIONS.md` D-003 处置。

---

## 运行方式

```bash
cd baseline-arms
python -m pytest tests/ -q                           # 白名单守卫的 19 个用例
python -m harness.probe_api                          # API 可用性（仅开发堆）
python -m harness.bare_cc --game <dev-pile-id> --model claude-sonnet-5 --budget 20
python -m harness.run_pilot --only-game <id> --budget 20
python -m harness.summarise_pilot                    # 试点汇总 + 单价

# M5 方差包络（逐局推进；闸门红则拒绝开跑，退出码 3）
python -m harness.run_campaign --game <dev-pile-id>
python -m harness.run_campaign --gate-only           # 只重新裁决，不花钱
python -m harness.audit_cells --game <dev-pile-id>   # 逐格账本自洽 + 对账 + 封存检查
python -m harness.summarise_campaign                 # 方差包络
python -m harness.campaign_status                    # 四份检查点（A14 入库后可离线读）
python -m harness.cost_artefacts                     # 花过钱的产物是否都还在、字节是否没变

# M6 Schema 路 A（白名单先行；--dry-run 只列清单，不下载）
python -m harness.fetch_schema_traces --dry-run
```

封存堆纪律是代码，不是注意事项：`harness/arc_client.py` 在 import 时加载
`piles.json`，指名封存局的调用在**打开 socket 之前**抛 `SealedGameError`。
本轨道对封存堆的 API 调用数：**0**。
