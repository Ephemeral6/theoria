# baseline-arms — 状态

本轨道只做两件与 Theoria 框架本身无关的事：**裸 Claude Code 跨模型跑分**、
**Schema 复现数据收集**。不碰理论、不碰引擎、不碰 DSL。

| 里程碑 | tag | 状态 |
|---|---|---|
| M1 既存状态审计 | `baseline-arms-m1-audit` | ✅ 达成 |
| M2 裸 CC harness + 记账管线 | `baseline-arms-m2-harness` | ✅ 达成 |
| M3 Schema 官方发布物定位 | `baseline-arms-m3-schema-locate` | ✅ 达成（判定为「找不到」支） |
| M4 试点 + 预算闸门 | `baseline-arms-m4-pilot-gate` | ✅ 达成 |
| M5 方差包络战役 | `baseline-arms-m5-variance` | 🔄 **P-12 续跑中**（ar25 记 degraded） |
| M6 Schema 路 A 材料 | `baseline-arms-m6-path-a` | ✅ 达成 |
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

## 本轮（P-12）结果摘要

三件事，外加开工时发现的一件必须先解决的。

### 先解决的那件：包络续跑的前置条件在开工时**并未满足**

`BUDGET_REPORT.md` §11.5 把「先解决 INC-BA-003」写成复跑的前置条件。开工时对方那场
S1 全量**仍在跑**（g50t 第 9 集、sk48 第 11 集，两场合计已花约 $42）。照工单直接开跑，
量到的还是争用——§11.2 已经证过一次。

处置是把那句话变成一个检查：`harness/interlock.py`（`DECISIONS.md` D-017），
两个独立信号（进程表 + 跨 worktree 的检查点新鲜度），两个都拿不到时判阻塞，无 override。
配套把 INC-BA-003 抱怨的「谁都看不见合计数」补上：`campaign_gate.json` 现在带
`combined_exposure`。

顺带**跑一次真的就抓到一个假阳性**：`--gate-only` 是只读的，却被算成一场活着的战役——
一个会对自己的诊断说「不」的互锁。已修，见提交 `6b19d38`。

### 闸门的两处改动（都必须被当成改动来审，不是背景噪声）

1. **F-15 落地通道**（D-016）。闸门是从 `campaign_cells.jsonl` 现算的，三个 ar25 死格
   就在文件头，`--gate-only` 判红，`run_campaign` 拒开任何一局——**不给裁决一条通道，
   F-15 就无法执行**。`harness/adjudications.py` 是能想到的最窄的通道：
   只有 `G4` 可挂起、只对逐条点名的 `run_id`、点名其他子句在写入和读取时各被拒一次、
   轨道不能自裁。那三格花的 $2.5275 仍进每一个 cap。
2. **G6a 改量「坐班」，新增 G6c**（D-018）。**8 h 的 cap 一个字没动。**
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

# M6 Schema 路 A（白名单先行；--dry-run 只列清单，不下载）
python -m harness.fetch_schema_traces --dry-run
```

封存堆纪律是代码，不是注意事项：`harness/arc_client.py` 在 import 时加载
`piles.json`，指名封存局的调用在**打开 socket 之前**抛 `SealedGameError`。
本轨道对封存堆的 API 调用数：**0**。
