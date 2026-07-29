# baseline-arms — 状态

本轨道只做两件与 Theoria 框架本身无关的事：**裸 Claude Code 跨模型跑分**、
**Schema 复现数据收集**。不碰理论、不碰引擎、不碰 DSL。

| 里程碑 | tag | 状态 |
|---|---|---|
| M1 既存状态审计 | `baseline-arms-m1-audit` | ✅ 达成 |
| M2 裸 CC harness + 记账管线 | `baseline-arms-m2-harness` | ✅ 达成 |
| M3 Schema 官方发布物定位 | `baseline-arms-m3-schema-locate` | ✅ 达成（判定为「找不到」支） |
| M4 试点 + 预算闸门 | `baseline-arms-m4-pilot-gate` | ✅ 达成 |
| M5 方差包络战役 | `baseline-arms-m5-variance` | ⚠️ **闸门红，停在 1/4 局** |
| M6 Schema 路 A 材料 | `baseline-arms-m6-path-a` | ✅ 达成 |
| A14 花过钱的产物入库 | — | ✅ 达成（2026-07-29） |

文档：[`AUDIT.md`](AUDIT.md)（第 0 步审计）·
[`SCHEMA_LOCATE.md`](SCHEMA_LOCATE.md)（M3 结论）·
[`SCHEMA_PATH_A.md`](SCHEMA_PATH_A.md)（M6 路 A 执行结果）·
[`DECISIONS.md`](DECISIONS.md)（设计决策）·
[`INCIDENTS.md`](INCIDENTS.md)（事件）·
[`TOUCHED_GAMES.md`](TOUCHED_GAMES.md)（触碰登记）·
[`BUDGET_REPORT.md`](BUDGET_REPORT.md)（闸门，§9 是可执行的止损条件）

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

分片账本一并入库（55 MB 原始）——它们是主记录，且是那 $2.01 差额**唯一**的存活痕迹。
体积不是理由：这些是重复的整数网格，gzip 压 50–76 倍，十二份文件实测让 pack
从 72.56 MiB 长到 82.28 MiB。清单与逐条理由见
[`runs/20260729T100000Z-a14/INVENTORY.md`](runs/20260729T100000Z-a14/INVENTORY.md)，
账目见 [`RECONCILIATION.md`](runs/20260729T100000Z-a14/RECONCILIATION.md)。

---

## 本轮（P-7）结果摘要

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
