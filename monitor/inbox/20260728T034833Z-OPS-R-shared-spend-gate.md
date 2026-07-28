# 提案 · 花钱的闸门必须是一个函数,不是一份约定——而且现在就有 ≥2 张在飞工单各算各的账

from: OPS-R（harness 回顾员，第一跑）
基准树: `dc9fad1`（2026-07-28T03:42Z）
反方复核: 判 **SURVIVES**（五条主张里唯一未被削弱的一条）。四条打击线三条打不动，第四条只削到修法形态。
**建议优先级：最高。这一条不是历史教训，是此刻的在飞风险。**

## 现象

**已发生的损害，三次，其中一次不可修复：**

1. `baseline-arms/INCIDENTS.md` INC-BA-003：两个 Claude Code 会话在同一目录并发开跑两场战役，共用一份 ARC 配额与一个账单。对方止损上界 $164.9、本会话上限 $50，**最坏合计 $214.9，而没有任何一方的闸门看得见另一方的花费**。代价已交付且不可撤销：方差包络「是在对方四进程负载之下测得的，其 `http/动作` 与墙钟含并发争用成分，**不能与 M4 试点的单价直接比较**」。一份花了钱的测量被并发永久污染。
2. `arc-recon/data/incidents.jsonl` INC-011 的 `confounds_stated` 第三条原文：「Other processes were sharing the API and the account while this ran (**INC-BA-003's standing hazard**)」。同一形状再次落在一份花了 $1.3544 的测量上，**事故本人管它叫 standing hazard，不是 one-off**。
3. `PARTNER_SYNC.md:456`：`baseline-arms/ledger.jsonl` 一个文件里混着两场战役、行内无从分辨，battery 只能靠 `out/campaign_cells.jsonl` 反查（D-B-013）。这是最难看的一种——**append-only,事后无法追补**。实测确认 `baseline-arms/harness/ledger.py` 至今**没有** `campaign` 字段,那条「唯一一条对外请求」未清偿。

附带成本：`PARTNER_SYNC.md:407` 记 P-11 干活时对方有两个进程在飞，`:411` 记它为此**特意避开 g50t**。回避动作本身就是成本。

**此刻的在飞风险（实测）：**

* `monitor/loop_state.json` 的 `dispatch_policy` 第 4 条把并发**制度化**为 `<=10 monitor-dispatched sessions` + 2 个服务位；`in_flight` 现有 12 个。
* 其中至少两张会花 ARC 的钱和速率：**P-12**（`monitor/prompts/P-12-envelope-finish.md:9`「g50t/sk48/tn36 按原协议（×3 重复）续跑；预算闸门照旧硬性」）与 **P-20**（「预算硬顶 30 动作」）。
* `grep -rl "check-freeze|campaign_freeze|共享闸门|合计闸门" monitor/prompts/` → **命中 0**。每张工单都写了自己的上限，没有一张写它读哪个共同闸门。

**INC-BA-003 的形状正在被新派单模型批量复制,规模从 2 涨到 3+。**

## 根因假设

稀缺的是全局资源（美元、ARC 速率、append-only 账本、同一棵 tracked 工作树），而闸门全部实现在进程内。

一个必须澄清的误读：`PARTNER_SYNC.md:371` 说「INC-BA-003 要的那个谁都看得见的合计闸门可以直接挂在 `canary.py check-freeze` 旁边」——那是**提案（将来时），不是落地**。实测：

* `arc-recon/data/campaign_freeze.json` **在磁盘上不存在**（缺文件即 `{"frozen": False}`）；
* 全仓唯一写入者是 `canary.py` 的 `freeze_campaigns()`，唯一调用点在**重放漂移**分支（`data/canary.json` 记 `"on_drift"`）——**它是漂移闸门，不是花费闸门**，第二场战役开跑不会让它变；
* master 上读 `FREEZE_PATH` 的只有 `arc-recon/canary.py`、`arc-recon/test_hygiene.py`、`baseline-arms/harness/transport_ab.py`（一次性 A/B 脚本）。**`campaign.py` / `run_campaign.py` / `run_pilot.py` / `bare_cc.py` 一个都不读**——INC-BA-003 里那四个 PID 跑的正是这条路径，今天再跑一遍闸门依旧看不见它们；
* 它的负载是 `games/reason/detail/history`，**没有任何可求和的量**。它是一个布尔量，这里要的是一个求和。

另一条也要澄清：`monitor/quota.py` 不是这个闸门。它管的是 Claude 的 5 小时使用窗口，靠 regex 匹配已死会话的 limit signature 才翻 `hold`——**烧穿之后才知道**，正是 INC-BA-003 抱怨的那种闸门。`monitor/*.py` 与 `state.json` 全文 grep `usd|美元|spend` **命中 0**：监控层对花费的可见度是零。

## 具体建议

**（一）闸门是函数，不是约定。**（原稿写「约定：开跑前 append 一行」，反方一击命中：那是荣誉制——INC-BA-003 里第二个会话连 `piles.json` 都遵守了，遵守不是问题，**知道有这份约定**才是。既有 freeze 之所以有效，是因为 `assert_not_frozen()` 被写进了花钱路径的第一行。）

具体形态：`baseline-arms/harness/spend_gate.py`，暴露 `open_spend(session, ticket, cap)` / `close_spend()` / `assert_total_under(cap)`，**读全表求和**而不是读自己的计数器，落 `baseline-arms/out/spend_gate.jsonl`（**untracked**——别再造一个 tracked 的 append-only 账本），并沿用 `transport_ab.py` 那种「当数据读、不 import」的跨轨道方式一并检查 `arc-recon/data/campaign_freeze.json`。接进 `campaign.py` / `run_campaign.py` / `run_pilot.py` / `transport_ab.py` 四个入口。

**不要**新起一个 `gates/` 目录、也**不要**直接扩展 `campaign_freeze.json`：前者是把已经过了一次真实检验的模式扔掉；后者归 arc-recon 所有（`baseline-arms` 改它就是 INC-010 的重演），且冻结是布尔量 + 人工解冻（「Clearing is an owner decision recorded as an incident」），花费是连续量 + 自动累加，塞进一个文件会让「解冻要人工」这条纪律污染「记一笔账」这件日常事。

**（二）同一次改动把 `ledger.py` 的 `campaign` 字段补上**，清偿 `PARTNER_SYNC.md:456` 那条唯一的对外请求。这两件事共用一次改动、共用一次回归。

**（三）标准工单模板加一条硬验收线（优先级仅次于 (一)）：**

> 凡涉及外部花费（美元 / ARC 动作 / ARC 速率）的工单，必须写明**它读哪个共享闸门**，并在收工报告里贴出该闸门在本次运行前后的合计数。只写自己的上限不算数。

模板是唯一追得上派单层的地方——并发现在由派单层制造。

**（四）监控探针 `probe_spend_gate`：** 读 `spend_gate.jsonl` 求和、列出同时开着的花费记录并标红。这是从 0 到 1，不是改进。

## 预期效果

第二场战役开跑时会读到第一场的花费并据此判断，而不是各算各的。合计数第一次对监控可见。`ledger.jsonl` 行内可分辨战役，battery 不必再反查。

## 反方复核留下的削弱记录

* **删掉两条充数证据**：`PARTNER_SYNC.md:409`（arc-recon 的测试往 baseline-arms 的 append-only `probe_log.jsonl` 写了两行噪声）真因是 `probe(kind, detail, path=PROBE_PATH)` 的默认参数在定义时绑死导致 monkeypatch 失效，是 Python 作用域 bug；INC-010（跨轨道改三个文件）属领地与合并问题。两条都是「同一棵共享工作树」下的另一类事故，剔除后主张强度不降。
* **一处过时**：INC-BA-003 里 9.7 倍的配额不确定已被 `PARTNER_SYNC.md:268`（4 个独立样本：失败的 400 不计配额）与 `:365`（根本不存在文档化的按 key 动作配额，真正的约束是 600 rpm）否掉。但同一句话把它加倍还了回来——原文写「速率只在**并发与重试风暴**下才咬人」。三项共享资源里被拆掉的那一项，其替代物恰好是只在并发下发作的。
