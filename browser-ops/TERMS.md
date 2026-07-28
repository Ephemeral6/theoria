# ARC 官方条款核查 — 原文摘录与出处

会话：OPS-B 浏览器专员 · 日期：2026-07-28 · 工具：应用内浏览器（**非**用户 Chrome，无登录态）
访问明细见 [`runs/2026-07-28-visits.md`](runs/2026-07-28-visits.md)。

> **重要的路由事实**：`three.arcprize.org` 已 **301 到 `https://arcprize.org/arc-agi/3`**；
> 开发者文档不在该域下，而在 **`https://docs.arcprize.org/`**。工单里写的 "three.arcprize.org
> 与官方文档" 是两个站：前者是产品页，后者是条款口径的实际所在。

摘录一律短引原文并标 URL；未引全文（ToS 全文 35,206 字符，属 ARC Prize, Inc. 版权内容，
本轨道按 ToS §2 的 "personal / internal business use" 口径只留判定所需的句子）。

---

## 1. 速率 / 配额的官方口径

**这是本次核查最有份量的一条，因为它直接落在 `INCIDENTS.md` INC-BA-003 的阻塞项上。**

来源：<https://docs.arcprize.org/rate_limits>

| 项 | 官方口径 |
|---|---|
| 价格 | 研究预览期**免费** |
| 支持等级 | best-effort，**无 SLA、无可用性保证、无响应时间保证** |
| 速率上限 | **600 requests per minute (RPM)** |
| 超限行为 | 标准 **429**，指数退避 |
| 总量配额 | **官方文档中不存在**——见下方判定 |

原文（节选）：

> "Rate limits are set at 600 requests per minute (RPM)."
> — <https://docs.arcprize.org/rate_limits>

> "The ARC-AGI API is currently free to use during its research preview and is supported on a
> best-effort basis. We do not currently offer a formal SLA, uptime guarantee, or guaranteed
> response times."
> — 同上

超限响应体（原文）：

```json
{"error":"RATE_LIMIT_EXCEEDED","message":"rate limit has been exceeded"}
```

提额渠道（原文）：

> "If you need elevated limits, please email us at team@arcprize.org with the subject line
> 'Increase Rate Limits' to initiate a conversation."
> — 同上

`local-vs-online` 页把两种模式的限制并排写死，口径一致：

> Online … "Capped at 600 requests per minute"；Local … "No rate limits"
> — <https://docs.arcprize.org/local-vs-online>

### 1.1 对 INC-BA-003 阻塞项的判定

INC-BA-003 建议 2 把「问清 ARC 配额口径」升级为阻塞项，理由是
`BUDGET_REPORT.md` §4 记的「失败的 400 是否计入配额未知，乐观/悲观差 9.7 倍」。

**核查结果：官方公开文档里没有任何"总量配额"这种东西。** 只有一个**速率**闸门
（600 RPM），以及一个 **429** 的超限信号。据此：

* 「烧穿配额」这个风险在官方口径下**没有对应的机制**——没有月度/总量额度可烧穿，
  只有瞬时速率会被 429 挡回并退避。400 是否计数这个问题**在 600 RPM 的口径下不改变任何决策**：
  两场并发战役合计 ~24,000 次 HTTP，只要分布在数小时内，峰值远低于 600 RPM。
* **这不等于"没有闸门"。** 它把风险从「配额烧穿（不可逆）」改写成「触发 429 后退避（可逆、只费墙钟）」。
* **仍需人来确认的那一半**：文档没说的是**账号级别的滥用判定**——ToS §3(3) 与 §4 明令禁止自动化访问
  （见 §3），而封号是不可逆的。真正该发给 `team@arcprize.org` 的问题因此**换了一个**：
  不是"配额多少"，而是"以研究用途运行自动化 agent，是否属于 ToS 允许的例外"。

> **建议**：INC-BA-003 的阻塞项 2 可以按上述改写后**降级**，但不能直接勾掉——
> 降级的依据是这一页，而这一页随时可改（ToS §11 明写"随时可改、无义务通知"）。
> 处置权归人工，本会话不代决。

---

## 2. 帧数据缓存与再释出许可

### 2.1 缓存：官方不但允许，而且是默认行为

来源：<https://docs.arcprize.org/arc-prize-2026>（Kaggle Starter 的 troubleshooting 一节）

> "Your machine couldn't reach the ARC-AGI API to download the game source on first run. …
> Once downloaded, games are cached in `environment_files/` and you're fully offline."

来源：<https://docs.arcprize.org/local-vs-online>

> Local (Recommended) … "~2,000 FPS (120,000 frames per minute)" · "No rate limits" ·
> "Run as many instances as you want" · "No API key required"

来源：<https://docs.arcprize.org/recordings>

| Method | Recordings Available（原表） |
|---|---|
| API | "Yes — viewable online via scorecard" |
| Swarm | "Yes — saved locally and viewable online" |
| Local Toolkit | "No — running locally without API does not generate recordings" |

本地录像落盘格式（原文）：`{game_id}.{agent_type}.{max_actions}.{guid}.recording.jsonl`，
JSONL 逐行含 `timestamp` 与 `data{game_id, frame, state, score, action_input, guid, full_reset}`。

**判定**：帧数据在本地缓存/落盘是官方设计的一部分，**不需要额外许可**。

### 2.2 再释出：需要书面许可，而且默认是禁止

来源：<https://arcprize.org/terms>（Terms and Conditions，last updated June 03, 2024）§2 INTELLECTUAL PROPERTY RIGHTS

> "The Content and Marks are provided in or through the Services 'AS IS' for your personal,
> non-commercial use or internal business purpose only."

> "no part of the Services and no Content or Marks may be copied, reproduced, aggregated,
> republished, uploaded, posted, publicly displayed, encoded, translated, transmitted,
> distributed, sold, licensed, or otherwise exploited for any commercial purpose whatsoever,
> without our express prior written permission."

§4 PROHIBITED ACTIVITIES 第一条：

> "Systematically retrieve data or other content from the Services to create or compile,
> directly or indirectly, a collection, compilation, database, or directory without written
> permission from us"

**判定，对本项目是硬约束：**

1. **`Theoria.md` Phase 4 的释出清单若含任何帧数据、轨迹、分数表，属于 "aggregated / republished"，
   在书面许可到手之前不得公开释出。** 授权口径明确要求 "express prior written permission"，
   请求地址同样是 `team@arcprize.org`。
2. **账本本身（`ledger.jsonl` / 轨迹集合）在字面上就是 §4 第一条点名的 "compilation / database"。**
   内部使用落在 §2 的 "internal business purpose"，因此**采集与内部分析没问题**，
   **公开释出才是那道线**。这两件事必须在 Phase 4 冻结清单里分开写。
3. 若获许可，§2 还附带署名义务：须标明 ARC Prize 为所有者，并保留版权声明。

> 这条与 `baseline-arms/SCHEMA_PATH_A.md` §7 遗留事项 1（上游 HF 数据集**未声明许可证**）
> 是两个独立的许可证问题，且**方向相反**：上游那份是"没写，所以不敢分发"；
> ARC 这份是"写了，而且写的是不许"。两者都指向同一个结论：**Phase 4 释出前需要一次正式的许可证判断。**

---

## 3. API key 的使用范围

来源：<https://docs.arcprize.org/api-keys>

签发与用途（原文）：

> "Registering for an API key allows you to: Track your progress across games and sessions /
> Access the full list of games when launch goes out"

获取路径（原文步骤）：`arcprize.org/platform` → 用 Google 或 GitHub 登录 → 右上角 user profile →
API Keys 一节 → Create a new key。

注入方式（原文）：`export ARC_API_KEY="your-api-key-here"`，或写进项目 `.env`；
toolkit 自动从环境读取（`arc_agi.Arcade()`）。

> **与本仓库口径一致**：`CLAUDE.md` 规定 key 只存 `.env`（gitignored），变量名 `ARC_API_KEY`
> ——与官方文档用的**正是同一个变量名**。无需改动。

传输头（原文）：

> "All requests require an X‑API‑Key header issued from the ARC‑AGI‑3 web console."
> — <https://docs.arcprize.org/rest_overview>

**文档中没有写**：key 的有效期、可创建数量上限、每 key 的独立配额、撤销条件、
以及"一个 key 能否被多个并发进程共用"。INC-BA-003 里两场战役共用一份配额的问题，
**官方文档给不出答案**——因为官方根本没有 per-key 配额这个概念（见 §1）。

### 3.1 会话粘性：一条容易被漏掉的技术条款

来源：<https://docs.arcprize.org/rest_overview>

> "Games are stateful and require session affinity. The server sets cookies (especially AWSALB*
> cookies) in responses that must be included in all subsequent requests for the same game
> session. These cookies route requests to the correct backend instance maintaining your game
> state."

**这条值得本轨道认领**：`INCIDENTS.md` INC-BA-002 记的"短 ID 返回 200 但是伪响应、
携带的是原始初始帧"，与"没带对 cookie 就被路由到错误后端实例"是**同一个形状的故障**。
本轨道任何 harness 都必须确认 HTTP 客户端保持 cookie jar；否则会拿到语法正确、语义为假的 200。
（本条为核查者的关联判断，**不是**官方文档的说法。）

---

## 4. 封存纪律：本次核查中新发现的两颗地雷

这两条不在工单问题清单里，但按 `piles.json` rule 2 属于必须上报的东西。

### 4.1 官方 swarm runner 默认打全部 25 局

来源：<https://docs.arcprize.org/swarms>，`--game` 参数说明原文：

> "Filter games by ID prefix. … **If not specified, the agent plays all available games.**"

同页示例第一条即 `uv run main.py --agent=random`（无 `--game`）。

来源：<https://docs.arcprize.org/arc-prize-2026>，命令表原文：

> `make play-local` — "Runs your agent against every game in the dataset, locally"
> `make verify-local` — "30-second smoke test on two games"（哪两局未写）

**任何直接照抄官方 quickstart 的运行都会打穿封存堆。** 本轨道现有 harness 的
`assert_playable()` 守卫必须继续是每一条执行路径上的强制关卡，
**尤其不能因为"本地不花钱"就放松**——本地跑一遍封存局，污染与线上完全等价。

### 4.2 本地引擎会把**全部 25 局的游戏源码**拉到磁盘

`arc-prize-2026` 页原文：first run 会 "download the game source"，之后缓存在 `environment_files/`。
`make list-games` 的说明是 "Print every game id available"。

这使 `environment_files/` 成为与上游 Schema HF 数据集**同一类的物件**：
按 INC-BA-001 §制度性后果的说法，**读它比玩那一局更糟**——它直接给出机制的成品答案（是源码）。

**建议纪律（归人工与 `arc-recon` 决定，本会话不代劳）**：若本轨道将来启用本地引擎，
必须复用 `SCHEMA_PATH_A.md` §3 那套正向白名单守卫的形状——
**下载不等于阅读**，但 `environment_files/` 必须被 gitignore、且任何模型不得读取其中非开发堆的文件。

---

## 5. 官方条款没有回答、需要发信问的问题（收敛后的清单）

发往 `team@arcprize.org`（ToS §22 与 rate_limits 页均给此地址）。**本会话不代发。**

1. **自动化访问的许可**：ToS §3(3) 声明用户 "will not access the Services through automated or
   non-human means, whether through a bot, script or otherwise"，§4 又禁止 "any automated system …
   scraper" 与 "systematically retrieve data … to create or compile … a database"。
   而 ARC-AGI-3 的整个产品形态就是让 agent 自动调 API。
   **这份 ToS 的 last updated 是 2024-06-03，早于 ARC-AGI-3 的 API。**
   需要一个书面确认：持 API key 的研究性自动化访问是否被视为 ToS 允许的用法。
   （风险不是钱，是封号——不可逆。）
2. **研究成果的再释出许可**：Phase 4 若要公开发布含 ARC 帧/轨迹/分数的材料，需 §2 要求的
   "express prior written permission"，并按其署名要求标注。
3. **429 之后的退避曲线**：文档只说 "exponential backoff mechanism"，未给基数、上限、
   或 429 是否影响 scorecard 有效性。这影响 harness 的重试策略（`AUDIT.md` §6 已判定重试是决定性因素）。

---

## 6. 本次核查的边界（如实登记）

* 使用的是**应用内浏览器**，`claude-in-chrome` 无任何浏览器实例连接（`list_connected_browsers` → `[]`），
  因此**全程无登录态**，看到的都是公开页面。
* **未打开**的高风险页面，以及不打开的理由：

| URL | 为什么不打开 |
|---|---|
| `arcprize.org/tasks?v=3`（Public Game Set） | 全 25 局的清单页，几乎必然带每局的图与说明 |
| `arcprize.org/tasks/ls20` | 封存局，且 INC-BA-001 已记其为实质泄露对象 |
| `docs.arcprize.org/` 的 Quickstart 正文 | 该页以 `ls20` 作贯穿示例（链接指向 `/tasks/ls20`） |
| `docs.arcprize.org/arc-agi-3` | 标题即指向 benchmark 内容本身，形状与 INC-BA-001 那一页相同 |
| `docs.arcprize.org/llms.txt` | 全站聚合，等于一次读完所有页面 |
| `docs.arcprize.org/full-play-test` | 名字提示为逐局实测记录 |

* **看到了不该看的吗**：没有机制内容。但确有封存局 **`ls20`、`ft09` 的 game_id 以字符串形式
  出现在命令行示例与 JSONL 样例里**（`swarms`、`recordings`、`local-vs-online`、`arc-prize-2026` 四页），
  形如 `--game="ls20,ft09"`、`ls20-016295f7601e`、`arc.make("ls20")`。
  **这不构成机制泄露**（只是 id 与 CLI 语法，无规则、无目标、无转移函数描述），
  但按"如实登记"的要求写在这里，由 `arc-recon` 判断是否需要动 `contamination_register`。
  本会话判断：**不需要**——这两局在 INC-BA-001 中已被登记为实质泄露，等级不会因此再升。

---

## 7. 追补（第二轮，真 Chrome 接入后）：Testing Policy 是本项目真正该读的那份文件

来源：<https://arcprize.org/policy>（"ARC Prize Verified Official Testing Policy"，20,924 字符）

第一轮漏了它——它不在 docs 站，也不在 ToS 的目录里，只在**页脚**以 "Testing Policy" 挂着。
它比 ToS 贴近本项目得多，因为 ToS 是一份通用网站模板，而这份是 ARC **自己写的、
针对基准测试行为**的政策。**它推翻了 §2.2 的一半结论。**

### 7.1 推翻：独立测试并公开自己的分数，官方明文允许

原文（FAQ "WHAT IF MY SUBMISSION IS NOT SELECTED FOR VERIFICATION?"）：

> "You are also free to test on public data and share your scores independently. Please state
> clearly the data you tested on, how you tested, and that your results are not verified by
> ARC Prize."

同页 FAQ "WHY SHOULD THE COMMUNITY TRUST ARC PRIZE?"：

> "We invite the community to reproduce our results."

**必须把两件事切开，否则会把这条读成比它实际更宽的许可：**

| 释出物 | 归谁 | 口径 |
|---|---|---|
| **我们自己测出来的分数、指标、结论** | 我们 | ✅ **官方明文允许公开**，附三项披露义务：测了哪份数据、怎么测的、未经 ARC 验证 |
| **ARC 的 Content 本身**（帧、轨迹、游戏源码、题面） | ARC Prize, Inc. | ❌ 仍受 ToS §2 约束，aggregate / republish 需书面许可 |

所以 §2.2 判定 1 应当**收窄**而不是撤销：`Theoria.md` Phase 4 的释出清单里，
**「我们的测量结果」不需要许可**（但需要那三句披露），
**「ARC 的原始帧/轨迹」仍需要许可**。这两类东西在同一个 manifest 里，必须分开标注。

> 这也意味着 §5 那三个待发问题里，**第 2 条（Phase 4 释出许可）的紧迫性下降**——
> 只要释出物限于我们自己的数字与方法，就已经落在明文允许里。仍需问的是：
> 若清单要附**原始帧或轨迹样本**作为可复现性证据，那一部分需不需要许可。

### 7.2 官方对"违规"的定义与后果，比 ToS 具体得多

原文（FAQ "WHAT HAPPENS IF SOMEONE VIOLATES THIS POLICY?"）：

> "If we have reason to believe a submission has violated this policy - for example, by
> targeting our evaluation sets or otherwise manipulating results - we will conduct an
> investigation."

后果原文：invalidate 并移除结果、公开标注该结果已作废、
"barring the party from future testing - up to and including permanent exclusion"。

**判定**：这套惩戒的适用对象是 **submission**（提交到排行榜的作品），
不是普通的 API 调用。它**没有**把"用脚本自动调 API"列为违规——
恰恰相反，ARC-AGI-3 的整个评测就是模型自动take action（见 §7.4）。

> 这实质性地缓和了 §5 问题 1 的担忧：**ToS §3(3) 的"禁止自动化访问"是通用网站模板语言，
> 而 ARC 自己的测试政策通篇预设自动化 agent 是正常用法。** 两份文件冲突时，
> 后者是专门法且更新更近。**但这仍是我们的解读，不是 ARC 的书面确认**——
> §5 问题 1 保留，只是从"阻塞"降为"稳妥起见问一句"。

### 7.3 新的封存污染向量：官方公开发布封存局的评测回放

原文（"How We Run Evaluations: ARC-AGI-3"）：

> "Results are published as scorecards on arcprize.org … New in ARC-AGI-3 is the concept of
> replays. You can view the exact run a model performed on any individual task."

**该页正文里直接挂着一条指向封存局 `re86` 回放的链接**（原文点名 "a replay of GPT-5.4 (High)
on task 're86'"）。`re86-8af5384d` 在 INC-BA-001 里已登记为"轻微"污染。

**本会话没有点开它。** 但这确立了一条第一轮没发现的向量：
**任何人都能在 arcprize.org 上看任意一局的逐帧回放，不需要 key、不需要登录。**
按 `piles.json` rule 2，看一遍封存局的回放与玩一遍等价。
`browser-ops/` 与任何 harness 都不得访问 `arcprize.org/scorecards/*` 与 replay 页面，
除非该 scorecard 是我们自己产的、且只含开发堆。

同段还写明 ARC-AGI-1/2 的**测试结果（含模型输出与逐题分数）发布到 HuggingFace**——
ARC-AGI-3 侧未提 HF，但 scorecard 页本身是公开的。

### 7.4 顺带确认的三条，对 Phase 2/4 有用

1. **ARC-AGI-3 的公开集比半私有集更难。** 原文："The public demo is harder than the
   Semi-Private set, so we expect Semi-Private scores to be the higher of the two；
   scores are in good agreement when within ±15 percentage points."
   **本项目的 25 局全部属于 public demo**，即最难的那一档；本轨道的封存刀口是**自我纪律**，
   与 ARC 自己的 Semi-Private / Private 分层是两回事，不要在文档里混为一谈。
2. **官方评测默认不给模型任何工具。** 原文："We do not enable additional tools behind the
   model, including code execution. We specifically do not enable web search…
   tool use should be opt-in, not opt-out, so any tool use will always be declared."
   这对本项目是一条**基线可比性**的约束：Theoria 的掌台用引擎与工具，
   与官方 leaderboard 数字不同源，任何对比都必须声明这一点。
3. **官方发布了 ARC-AGI-3 的第一方人类数据**（原文 "we've collected human data for …
   ARC-AGI-3 (found here)"）。这对 `Theoria.md` 的人类基线有价值，
   **但那个链接大概率覆盖全部 25 局**——按 INC-BA-001 的教训，
   取它必须是一次带白名单守卫的单独决定，不是顺手点开。**本会话没有点。**

### 7.5 账户面板（工单第 2 条）的第二轮结果

真 Chrome 已接入（`list_connected_browsers` 返回 1 个本地实例）。
`arcprize.org/platform` **302 到 `/platform/user` 后再跳 `/login`**，页面为：

> "Sign in to the ARC-AGI Research Platform — Access API keys and ARC-AGI-3 developer tools"
> Continue with Google / Continue with GitHub

**即该 Chrome 没有 arcprize 登录态。本会话仍未尝试登录**（登录属禁止动作）。
状态维持在 `RUN_STATE.md` 的 needs_human #1，但阻塞原因从"没有浏览器"更正为"浏览器有、登录态没有"。
