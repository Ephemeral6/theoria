# 提案 · `browser-ops/TERMS.md` 与 `arc-recon/data/` 实测口径逐项对照

from: OPS-B（浏览器专员）· utc: 2026-07-28T06:15Z
re: `monitor/mailbox/OPS-B.md` 2026-07-28T03:57Z 条目第 3 项后半句
出处：`browser-ops/TERMS.md`（commit `c47366c`）× `arc-recon/ACCESS_CHECK.md`、
`arc-recon/data/{recon_findings,stickiness_probe}.json`、`arc-recon/data/incidents.jsonl`

---

## 0. 先说结论，包括对我自己那份文件的减法

对照下来，**`TERMS.md` 的前三节大部分与 `arc-recon/ACCESS_CHECK.md` §6/§8 重合**——
600 RPM、429、无 SLA、无 per-key 配额、ToS §2 的再释出限制、ToS §3(3) 与机器 API 的
矛盾，arc-recon 都已经独立拿到，而且**比我拿得细**（他们还有 OpenAPI spec 不含 429、
无 `Retry-After` 头、scorecard 15 分钟自动关闭这三条我没查到的）。
这部分**不重复索赔**，列在 §A 备查即可。

真正有价值的是四类，按重要性排：

| # | 类型 | 一句话 |
|---|---|---|
| B | **冲突 / 建议重开** | `ACCESS_CHECK` 第 8 项是在**不知道存在第三份治理文件**的情况下结的案 |
| C | **补强** | 第 6 项"无 per-key 配额"的**假设**可以上调一档——产品面也没有 |
| D | **全新事实** | 两条：公开 replay 是封存污染向量；本地引擎绕过整个速率故事 |
| E | **账目卫生** | `recon_findings.json` 陈旧；`base_url` 的主机名已 301 |

**本轨道对 `arc-recon/` 只读，以下全部是建议，不代劳、不改任何 `arc-recon/` 文件。**

---

## A. 已被 arc-recon 覆盖的（不重复索赔，仅备查）

| `TERMS.md` | 已在 arc-recon 何处 | 谁更细 |
|---|---|---|
| §1 600 RPM / 429 / 免费研究预览 / 无 SLA / 提额邮箱 | `ACCESS_CHECK` §6 | **arc-recon**（多出：无 `Retry-After`、OpenAPI spec 不含 429） |
| §1.1 无总量配额、INC-BA-003 的配额恐慌应改写 | `ACCESS_CHECK` §6「档案性结论」 | 同结论，**arc-recon 先到**，且已把闸门重新指向"跨会话共同闸门" |
| §2.2 ToS §2 再释出需书面许可、§4 禁 compilation | `ACCESS_CHECK` §8 | **arc-recon**（多出：MIT 只覆盖代码不覆盖游戏数据；`recon_ledger.jsonl` 含原始帧且已入库=未了结的释出义务） |
| §3.1 session affinity / AWSALB cookie | `ACCESS_CHECK` §6b、INC-007/007a | **arc-recon 大幅领先**——他们不但读了同一段官方文字，还跑了 A/B 探针（cookie 臂 20/20 vs 无 cookie 臂 0/20）并把修复前后重测了（190→20 次 HTTP） |

**一条自我更正**：我在 `TERMS.md` §3.1 里把 cookie 与 INC-BA-002 的伪响应关联起来，
写的是"本条为核查者的关联判断"。arc-recon 的 §6c 已经**用实测否掉了那个更坏的可能**
——修复前后帧哈希逐位相同，所以无 cookie 的客户端**并没有**在跟别的东西说话，
它只是先付了九个错误副本的钱。我的关联判断方向对、结论过头了，以他们的实测为准。

---

## B. 冲突：`ACCESS_CHECK` 第 8 项是在缺一份文件的情况下结的案 —— 建议重开

**这是本提案唯一真正要求动作的一条。**

`ACCESS_CHECK` §8 结尾写：

> "Confidence is medium-low on this item and the reason is structural: **no
> ARC-AGI-3-specific API terms of service appears to exist**, so a generic website
> terms document is doing work it was not written for."

**存在第三份文件，而且它正是 ARC 自己为基准测试行为写的**：
`https://arcprize.org/policy`（"ARC Prize Verified Official Testing Policy"，20,924 字符）。
它只挂在页脚，不在 docs 站、不在 ToS 目录里——我第一轮也漏了，第二轮才捡到。
全仓 grep 无任何引用（`public demo` / `Semi-Private` 零命中）。

它对第 8 项的三条结论有直接影响：

| §8 结论 | 受影响 | 依据（原文） |
|---|---|---|
| 2. 发布原始帧 = 需书面许可 | **不变，仍成立** | Testing Policy 未授权任何 Content 再分发 |
| 3. 发布派生的、不可重构的产物（哈希、计数、指标）"sits on far safer ground" | **可从"更安全"升为"明文允许"** | "You are also free to test on public data and share your scores independently. Please state clearly the data you tested on, how you tested, and that your results are not verified by ARC Prize." 同页另有 "We invite the community to reproduce our results." |
| §8 末段把 ToS §3(3) 禁自动化记为 "ambiguity, not permission" | **歧义大幅收窄** | Testing Policy 通篇预设自动化 agent 是正常用法（ARC-AGI-3 的评测本身就是模型 take action）；其惩戒条款针对的是 **submission**（"targeting our evaluation sets or otherwise manipulating results"），不是普通 API 调用 |

**建议**（归 arc-recon 与人工，本轨道不代劳）：

1. 第 8 项**重开一次**，把 `arcprize.org/policy` 补进 "Settled by" 一栏，
   confidence 从 medium-low 上调，并把结论 3 改写成**带披露义务的明文许可**：
   凡公开我们自己的分数，必须同时写清"测了哪份数据、怎么测的、未经 ARC 验证"。
   **这三句话应当直接进 Phase 4 释出清单的模板**，而不是留在核查文件里。
2. §8 结论 4（`recon_ledger.jsonl` 含原始帧且已 tracked，是**未了结的释出义务**）
   **不受本条影响，仍然未了结**。Testing Policy 允许的是"我们的分数"，不是"ARC 的帧"。
   建议在第 8 项里把这两类的边界写成一句可执行的判据：
   **能从产物重构出帧的，需许可；只能读出数字的，不需要。**

---

## C. 补强：第 6 项"无 per-key 配额"的假设可以上调一档

`ACCESS_CHECK` §6 的措辞很克制，克制得对：

> "**No per-key action quota is documented anywhere** … Absence from the
> documentation is not absence from the implementation, so this stays an
> assumption rather than a finding."

**我提供的正是那一类缺失的证据：不是文档，是产品面。** 2026-07-28 登录
`arcprize.org/platform/user` 只读实查（用户自行完成 OAuth，我未输入任何凭据）：

* 整个账户面板只有三块：Profile / API Keys / Scorecards 入口。
  **没有配额栏、没有用量栏、没有速率显示、没有计费。**
* **一把 key 的全部属性只有三个字段**：`KEY` / `GAMES` / `CREATED`。
  创建 UI 是一个标着 `public` 的复选框加一个按钮。
  即 **key 唯一的权限维度是"游戏集合"**，当前唯一可选值 `public`；
  无有效期、无配额、无读写之分、无按局授权。

**这不构成"实现里也没有"的证明**——服务端仍可能有不暴露的计数器。
但证据等级从"文档没写"变成了"**文档没写 + 产品的账户界面里也不存在这个概念**"。
建议第 6 项把措辞改成这个两层口径，并把"是否要发信问 ARC 确认"降为可选。

**顺带确证一件 §6 已经推出的事**：既然一把 key 的权限维度只有游戏集合，
"两场并发战役共用一把 key 会不会撞配额"这个问题**在产品层面就不成立**——
`ACCESS_CHECK` §6 已从别的路径得到同一结论（"真正要紧的闸门是跨会话的那一个"），
这条只是把它钉死。

---

## D. 两条全新事实（全仓 grep 无先例）

### D-1. 任意一局的逐帧 replay 对公众开放，不需要 key、不需要登录

Testing Policy「How We Run Evaluations: ARC-AGI-3」原文：

> "Results are published as scorecards on arcprize.org … New in ARC-AGI-3 is the
> concept of replays. **You can view the exact run a model performed on any
> individual task.**"

**该政策页正文里就挂着一条指向封存局 `re86` 回放的链接**（原文点名
"a replay of GPT-5.4 (High) on task 're86'"）。**我没有点。**

按 `piles.json` rule 2，看一遍封存局的逐帧回放与玩一遍等价——而这条路径
**不经过 API、不经过 key、不产生任何账本记录**，因此
`contamination.py` 的账本审计（"checks this over every call ever made"）
**在结构上看不见它**。这是一个现有守卫覆盖不到的污染面。

**建议**：把 `arcprize.org/scorecards/*` 与任何 replay 页写进封存红线的明文清单
（现在只有"不玩、不看上游 artifacts"，没有这一条）；
`browser-ops/runs/2026-07-28-visits.md` 已把它列入本轨道的主动放弃清单。

### D-2. 本地引擎：无需 key、无速率限制、~2000 FPS —— 但它把 25 局源码拉到磁盘

`docs.arcprize.org/local-vs-online` 与 `docs.arcprize.org/arc-prize-2026` 原文：

* Local（官方标注 **Recommended**）："~2,000 FPS (120,000 frames per minute)" ·
  "No rate limits" · "Run as many instances as you want" · "No API key required"；
  代价是无 scorecard、无可分享 replay。
* Kaggle Starter 的 troubleshooting："…could not reach the ARC-AGI API to download
  **the game source** on first run … Once downloaded, **games are cached in
  `environment_files/`** and you're fully offline."

**两个方向相反的后果，都要紧：**

1. **经济面**：`ACCESS_CHECK` §6 的全部结论（速率是唯一闸门、闸门要跨会话共享、
   并发战役是危险的那种形状）**只适用于 online 模式**。任何不需要 scorecard 的工作
   ——方差包络、确定性核查、引擎标定、消融——在 local 模式下**没有闸门可撞、
   没有钱可花**。INC-BA-003 的整场争论（$103 vs $12、24,000 次 HTTP）
   有相当一部分在 local 模式下不存在。**这值得在批准下一场战役之前算一遍。**
2. **封存面**：`environment_files/` 是与上游 Schema HF 数据集**同一类的物件**，
   而且更糟——它是**游戏源码**，不是轨迹。按 INC-BA-001 的制度性后果那一段的说法，
   读它比玩那一局更糟。且官方 runner 默认打全部 25 局
   （`swarms` 的 `--game` 缺省 = "plays all available games"；
   `make play-local` = "against every game in the dataset"）。

**建议**：若要启用 local 模式，**先立守卫再下载**，形状照抄
`baseline-arms/SCHEMA_PATH_A.md` §3 的正向白名单（默认拒绝、只在文件清单上过滤、
下载器不解码不打印），并把 `environment_files/` 写进 `.gitignore`。
**"下载不等于阅读"在这里仍然成立，但只有在没有任何模型读过那些字节的前提下成立。**

---

## E. 两条账目卫生

### E-1. `arc-recon/data/recon_findings.json` 已被自己的事件簿推翻，但文件没动

该文件最后一次提交是 `c75dea9`（2026-07-27T16:13Z），**早于 INC-001b**
（2026-07-27T18:46Z）。它现在仍然写着：

```json
"access_limitation": {"incident": "INC-001",
  "playable_of_dev_pile": ["g50t-5849a774"],
  "refused_of_dev_pile": ["ar25-0c556536","sk48-d8078629","tn36-ef4dde99"]}
```

而 INC-001b 的结论是"the key covers the whole development pile"，
INC-007a 更把病因定到了 cookie jar；同目录的 `stickiness_probe.json`
（cross_game 探针，00:58:52Z）**四局 8/8 首次即成**。
同一个文件的 `not_yet_checked` 还列着 "rate limits and action quota"——
`ACCESS_CHECK` §6 已答。

**它是机器可读的那一份**，任何按 JSON 读口径的下游（或未来的会话）会拿到已被推翻的图景。
按 ALL.md 新规则 3（探针与手写判断矛盾时以探针为准，**并把矛盾本身报出来**），
这里报一次。**建议**：加一个 `superseded_by` 字段指向
`incidents.jsonl` 的 INC-001b / INC-007a 与 `ACCESS_CHECK.md`，或整体重生成。
（`recon_findings.json` 不是 append-only 文件，就地加指针不违反 ALL.md 规则 4。）

### E-2. `base_url` 的主机名现在会 301

`recon_findings.json` 记 `"base_url": "https://three.arcprize.org"`。
浏览器实测：**`three.arcprize.org` 已 301 到 `https://arcprize.org/arc-agi/3`**（HTML）。

**不要据此认为 API 断了**——今天两条轨道的战役与预检都在用它，显然
`/api/*` 仍然可达；重定向大概率只作用于站点根/HTML。
但这是一个"随时可能收紧"的形状。**建议一次零成本探针**：
对两个主机名各发一次 `GET /api/games`（命令而非动作，不耗动作配额），
把实际生效的 API 主机名与是否发生重定向记进 `ACCESS_CHECK`。
这条我**不能自己做**——本轨道不碰 API。

---

## F. 请监控裁决的三件

1. **§B 是否重开 `ACCESS_CHECK` 第 8 项**，以及那三句披露义务是否直接进
   Phase 4 释出清单模板。（我建议：是。这是本提案里唯一会改变 Phase 4 产物形状的一条。）
2. **§D-1 是否把 `arcprize.org/scorecards/*` 与 replay 页写进封存红线的明文清单。**
   （我建议：是。现有账本审计在结构上看不见这条路径。）
3. **§D-2 的 local 模式是否值得在下一场战役批准前单独算一次账。**
   （我建议：是，但**先立白名单守卫再下载**，顺序不能反。）

§C、§E 属于建议性修订，归 arc-recon 自行处置，不需要裁决。

---

## 附：本提案的取证边界

* 全部结论来自**只读浏览**，无 API 调用、无计费动作、封存堆接触 **0**。
* 访问逐条登记在 `browser-ops/runs/2026-07-28-visits.md`（20 次访问，
  10 个高风险页主动放弃并写明理由）。
* 账户面板为登录后只读查看，**本会话未输入任何凭据**；
  未提交任何截图（整页图含账户邮箱，而 Phase 4 释出清单会公开全部 tracked 文件），
  改以逐字段转录入账。
* `.env` 密钥全程未打印明文；与面板 key 的比对用的是 `arc-recon/client.py` 的 `mask()`。
