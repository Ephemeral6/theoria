# baseline-arms — 状态

本轨道只做两件与 Theoria 框架本身无关的事：**裸 Claude Code 跨模型跑分**、
**Schema 复现数据收集**。不碰理论、不碰引擎、不碰 DSL。

| 里程碑 | tag | 状态 |
|---|---|---|
| M1 既存状态审计 | `baseline-arms-m1-audit` | ✅ 达成 |
| M2 裸 CC harness + 记账管线 | `baseline-arms-m2-harness` | ✅ 达成 |
| M3 Schema 官方发布物定位 | `baseline-arms-m3-schema-locate` | ✅ 达成（判定为「找不到」支） |
| M4 试点 + 预算闸门 | `baseline-arms-m4-pilot-gate` | 见下 |

文档：[`AUDIT.md`](AUDIT.md)（第 0 步审计）·
[`SCHEMA_LOCATE.md`](SCHEMA_LOCATE.md)（M3 结论）·
[`DECISIONS.md`](DECISIONS.md)（设计决策）·
[`INCIDENTS.md`](INCIDENTS.md)（事件）·
[`TOUCHED_GAMES.md`](TOUCHED_GAMES.md)（触碰登记）·
[`BUDGET_REPORT.md`](BUDGET_REPORT.md)（闸门）

---

## 缺口与阻塞

### GAP-1（工作二整体）：Schema 复现**不可能**，`⟨复现值⟩` 合规留空

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

### 已解除：`INC-002` 不成立，在线 API 可用

`arc-recon` 的 `INC-002` 结论是「零次成功动作……整个在线 API 路线受阻」。
本轨道独立复核后推翻该诊断：`400 "game <id> not found"` 是**瞬时故障**，
重试即可推进。详见 [`AUDIT.md`](AUDIT.md) §6 与 `DECISIONS.md` D-005。
代价是每次成功动作平均约 5 次 HTTP 调用。

`INC-002` 的正式处置归 `arc-recon`，本轨道不修改其 `incidents.jsonl`，
只在 `PARTNER_SYNC.md` 通报。

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
python -m harness.probe_api                          # API 可用性（仅开发堆）
python -m harness.bare_cc --game <dev-pile-id> --model claude-sonnet-5 --budget 20
python -m harness.run_pilot --only-game <id> --budget 20
python -m harness.summarise_pilot                    # 汇总 + 单价
```

封存堆纪律是代码，不是注意事项：`harness/arc_client.py` 在 import 时加载
`piles.json`，指名封存局的调用在**打开 socket 之前**抛 `SealedGameError`。
本轨道对封存堆的 API 调用数：**0**。
