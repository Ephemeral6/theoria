# browser-ops · RUN_STATE

会话：OPS-B 浏览器专员（App 常驻版）· 日期：2026-07-28
产出：[`TERMS.md`](TERMS.md) · [`runs/2026-07-28-visits.md`](runs/2026-07-28-visits.md)

## 环境实况（开工第一件事）

| 项 | 结果 |
|---|---|
| `claude-in-chrome`（用户真 Chrome） | ~~不可用~~ → **第二轮已接入**：用户装好扩展后 `list_connected_browsers` 返回 1 个本地实例（`Browser 1` / Windows）。**但该 Chrome 无 arcprize 登录态** |
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

### 1. 账户面板核查：**扩展已解决，登录态未解决**（更新于第二轮）

* **进展**：用户已装好 Claude in Chrome 扩展，浏览器接入成功。
* **新的卡点**：该 Chrome **没有 arcprize 登录态**。`arcprize.org/platform`
  → 302 `/platform/user` → 再跳 `/login`（"Sign in to the ARC-AGI Research Platform"，
  仅 Google / GitHub 两个 OAuth 入口）。
* **本会话没做的事**：**没有尝试登录**。登录属禁止动作（须由人在自己的浏览器里完成）。
  标签页已停在登录页上，等人走完 OAuth。
* **要人做什么**：在那个 Chrome 窗口里点 Continue with Google / GitHub 完成登录，
  然后说一声即可——本会话接着只读查 profile → API Keys 一节并截图存 `runs/`。
* **但先读这个**：`TERMS.md` §1.1 的判定说明，账户面板原本要查的"配额余量"
  **在官方口径下可能不存在**——ARC 只有 600 RPM 的速率闸门，没有公开的总量配额概念。
  这条阻塞的价值因此从"必须查"降为"值得确认"。

### 2. 需要发信给 `team@arcprize.org` 的问题（本会话不代发）——**第二轮已缩水**

第二轮读到官方 **Testing Policy**（`arcprize.org/policy`，第一轮漏了，它只挂在页脚）后，
原来的三条里有两条被官方明文缓解。清单见 `TERMS.md` §5 与 §7：

1. **自动化访问是否被 ToS 允许** — **降级为"稳妥起见问一句"**。
   Testing Policy 通篇预设自动化 agent 是正常用法（ARC-AGI-3 的评测本身就是模型自动
   take action），且其违规条款针对的是 **submission**（排行榜提交），不是普通 API 调用。
   ToS §3(3) 的禁自动化是通用网站模板语言，与专门政策冲突且更新更早（2024-06-03）。
2. **Phase 4 释出许可** — **紧迫性下降，且要问的东西变窄了**。
   Testing Policy FAQ 明文："You are also free to test on public data and share your scores
   independently"，附三项披露义务（测了哪份数据、怎么测的、未经 ARC 验证）。
   故**我们自己的分数与方法可以公开**；仍需问的只有一件：
   **释出清单若要附原始帧或轨迹样本作为可复现性证据，那一部分需不需要书面许可**。
3. **429 的退避曲线基数与上限**，以及 429 是否影响 scorecard 有效性 — **不变**。

## 给两条轨道的三条即时可用结论

1. **`INCIDENTS.md` INC-BA-003 的阻塞项 2（问清配额口径）可以改写并降级**——
   官方只有 600 RPM 速率闸门，无总量配额；`BUDGET_REPORT.md` §4 那个 9.7 倍的
   400-计数不确定性，在 RPM 口径下不改变任何决策。**降级与否归人工，本会话不代决。**
2. **官方 runner 默认打全部 25 局**（`swarms` 的 `--game` 缺省、`make play-local`）。
   任何照抄官方 quickstart 的运行都会打穿封存堆。`assert_playable()` 必须留在每条执行路径上。
3. **本地引擎首跑会把全部 25 局的游戏源码拉到 `environment_files/`**，
   这是与上游 Schema HF 数据集同一类的"读了就全污染"物件——而且是源码，比轨迹更直接。
   若启用本地模式，需复用 `SCHEMA_PATH_A.md` §3 的正向白名单守卫形状，并 gitignore 该目录。
4. **（第二轮新增）任意一局的逐帧回放对公众开放，不需要 key、不需要登录。**
   Testing Policy 证实 ARC-AGI-3 的评测结果以 scorecard + replay 公开发布，
   且该政策页正文就挂着一条指向封存局 `re86` 回放的链接。
   **`arcprize.org/scorecards/*` 与任何 replay 页应列入封存红线**——
   看封存局的回放与玩一遍等价。本会话未点。
5. **（第二轮新增）本项目的 25 局全部属于 ARC 的 "public demo"，是最难的一档**
   （官方口径：public demo 比 Semi-Private 更难，二者在 ±15 个百分点内算一致）。
   本轨道的封存刀口是**自我纪律**，与 ARC 自己的 Semi-Private / Private 分层是两回事，
   文档里不要混为一谈。
6. **（第二轮新增）官方评测默认不给模型任何工具**（无代码执行、无 web search，
   "tool use should be opt-in, not opt-out"）。Theoria 的掌台用引擎与工具，
   **与官方 leaderboard 数字不同源**，任何对比都必须声明这一点。
