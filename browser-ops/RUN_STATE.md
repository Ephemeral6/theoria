# browser-ops · RUN_STATE

会话：OPS-B 浏览器专员（App 常驻版）· 日期：2026-07-28
产出：[`TERMS.md`](TERMS.md) · [`runs/2026-07-28-visits.md`](runs/2026-07-28-visits.md)

## 环境实况（开工第一件事）

| 项 | 结果 |
|---|---|
| `claude-in-chrome`（用户真 Chrome） | **不可用** — `list_connected_browsers` 返回 `[]`，无扩展实例连接 |
| 应用内浏览器（`Claude_Browser`） | **可用**，但**无任何登录态**（独立浏览器，不带用户 Cookie） |
| 仓库写权限 | **有** — 本目录三个文件均已落盘 |

> 这一格与记忆里"派单会话无写/执行权限"的历史结论**不一致**：本会话可写。
> 挡住的只有浏览器登录态这一项。

## 任务状态

| # | 任务 | 状态 | 说明 |
|---|---|---|---|
| 1 | ARC 官方条款核查 → `TERMS.md` | ✅ **完成** | 13 次页面访问，速率/缓存与再释出/key 范围三问全部有官方原文口径 |
| 2 | 账户面板只读核查 | ⛔ **阻塞** | 见 needs_human #1 |
| 3 | Schema 路 A 校验 | ⏭ **跳过（前置不成立）** | `baseline-arms/SCHEMA_PATH_A.md` 记录路 A 已于 2026-07-28 完成：165 文件 / 87.7 MB / 开发堆 4 局齐 / 封存路径落盘 **0**。工单第 3 条写明"仅当未完成"，故不重做 |

## needs_human

### 1. 账户面板核查：需要真 Chrome 接入（阻塞项 2）

* **卡在哪**：`claude-in-chrome` 无浏览器实例连接。应用内浏览器是干净会话，
  打开 `arcprize.org/platform` 只会看到未登录页，看不到配额余量与 key 权限显示。
* **本会话没做的事**：**没有尝试登录**。登录属禁止动作（须由人在自己的浏览器里完成）。
* **要人做什么**：在需要核查的 Chrome 里装好 / 连上 Claude in Chrome 扩展并保持
  arcprize.org 登录态，然后重派本条；或由人直接截图 profile → API Keys 一节存进 `runs/`。
* **但先读这个**：`TERMS.md` §1.1 的判定说明，账户面板原本要查的"配额余量"
  **在官方口径下可能不存在**——ARC 只有 600 RPM 的速率闸门，没有公开的总量配额概念。
  这条阻塞的价值因此从"必须查"降为"值得确认"。

### 2. 需要发信给 `team@arcprize.org` 的三个问题（本会话不代发）

清单见 `TERMS.md` §5。按后果排序：

1. **自动化访问是否被 ToS 允许**（ToS §3(3)/§4 明禁 bot/script/scraper，而 ARC-AGI-3
   的产品形态就是 agent 自动调 API；该 ToS 的 last updated 是 2024-06-03，早于 API）。
   **后果是封号，不可逆**——这是三条里唯一有不可逆损害的。
2. **Phase 4 释出许可**（ToS §2 要求 "express prior written permission" 才能
   aggregate / republish；采集与内部分析不受限，公开释出受限）。
3. **429 的退避曲线基数与上限**，以及 429 是否影响 scorecard 有效性。

## 给两条轨道的三条即时可用结论

1. **`INCIDENTS.md` INC-BA-003 的阻塞项 2（问清配额口径）可以改写并降级**——
   官方只有 600 RPM 速率闸门，无总量配额；`BUDGET_REPORT.md` §4 那个 9.7 倍的
   400-计数不确定性，在 RPM 口径下不改变任何决策。**降级与否归人工，本会话不代决。**
2. **官方 runner 默认打全部 25 局**（`swarms` 的 `--game` 缺省、`make play-local`）。
   任何照抄官方 quickstart 的运行都会打穿封存堆。`assert_playable()` 必须留在每条执行路径上。
3. **本地引擎首跑会把全部 25 局的游戏源码拉到 `environment_files/`**，
   这是与上游 Schema HF 数据集同一类的"读了就全污染"物件——而且是源码，比轨迹更直接。
   若启用本地模式，需复用 `SCHEMA_PATH_A.md` §3 的正向白名单守卫形状，并 gitignore 该目录。
