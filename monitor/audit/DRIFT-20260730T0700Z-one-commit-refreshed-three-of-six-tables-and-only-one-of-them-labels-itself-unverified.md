# DRIFT-one-commit-refreshed-three-of-six-tables-and-only-one-of-them-labels-itself-unverified
severity: low-medium
dimension: 8（监控自身漂移）
**这是一份修订，不是新报告** —— 并入 `monitor/audit/DRIFT-20260729T2315Z-a-deliberate-thirty-cell-audit-went-stale-in-twenty-hours.md`

**pin:** `origin/master = 304ad651` @ 2026-07-30T06:34:27Z。`monitor/spec.py` **脏着未提交**，
但下述所有行在磁盘与 pin 上逐字节相同（已逐行核对），另有一处例外单独标注。

---

## 为什么这是修订而不是新报告

同一个成因已经被上报**四次**。`DRIFT-20260729T2315Z` 自己写着它是「第四次上报」，并建议
「并入 DRIFT-20260729T2230Z 作为补强——同一段代码、同一个成因、同一个已发表的委托」。
本轮 dimension-8 扫描交回 11 条候选，对抗性复核后：

* **`spec.py:1230` 的 PHASE_FOCUS 注释（WP1 98/WP2 92/WP5 82）——第五次，撤。**
  `DRIFT-20260729T2210Z` §3 已逐字收录，含同一锚点、同一组数字、同一条建议；
  `DRIFT-20260730T0031Z:28` 复核为 UNCHANGED；`monitor/audit/state.json` 的
  `pending_on_monitor` 里也还开着。
  **而且它没有后果**：`monitor/board.py:311-321` 只读 `PHASE_FOCUS`（一个手写的 lane 名列表）
  与 `FOCUS_BOOST`（一个整数），**从不读任何百分比**。按真值算剩余加权工作量
  `weight × (100−pct)`：`WP6 20.0 · WP3 16.4 · WP7 6.0 · WP4 4.4 …`；按注释里的错数算
  WP3 是 15.0。**两组数下 campaign 都以约 4 倍领先，焦点顺序一模一样。**
  A3 工单里那句「WP3 权重 20%，现 25%」（真值 18）确实是这条注释传播出去的，
  但它**高估了进度**，真值只会让那件事更急不是更缓，而它的 `priority: 1` / `lane: campaign`
  才是真正起作用的字段。
* **GRID `C3` 与 `V1` ——撤。** `DRIFT-20260729T2315Z` 已把三十格审了一遍并点名十格
  （`E5 / C2 / C3 / S4 / A3 / V1（半）/ V2 / V3 / V5 / P3`），V1 的「半真」在那份里就写作「（半）」。
* **`spec.py:938` 的「规划 FD ⋯ FD 未装」——我的采集者说它自相矛盾，是采集者错了，我照报。**
  同一文件 `:373-375` 的 `fd_adapter` 行写的是 `partial`、「接口就位，后端是 BFS 桩」，
  **两处一致**；`CLAUDE.md` 也写明 `.toolchain/` 是刻意 gitignore 的，没有构建的机器回落到桩
  是预期而非缺陷。**把「一致」报成了「矛盾」，这一条不成立。**

---

## claim（本轮真正新的两件）

**一、一次刻意的刷新只更新了六张手写表里的三张，于是同一个文件从此同时断言 X 与 ¬X，已站了约 46 小时。**

`edb3c3748`（2026-07-28 08:14:43）是一次刻意的刷新提交，它改了：
`:46` p1-proxy-model → green，「**约束 8 从此可测**」；`:62` p1-runner → green，
「proxy/runner.py + LEDGER_FORMAT.md + replay.py 落地」；`:199` p2-battery → green；
`:371`、`:379` ENGINES 的 IC3/PDR 与死锁刻画 → green，「M9 落地」。

**它没有动 `CONSTRAINTS`、`CLAIMS`、`ARCHITECTURE` 三张表**，它们停在 `79009fc4e`
（2026-07-28 02:13:55）的值上。结果（磁盘 == pin）：

| 说 A | 同一文件说 ¬A |
|---|---|
| `:428` 约束 8 `missing`，「模型代理不存在 = 没有任何东西在数模型调用。这条约束目前**不可证伪**」 | `:46` 「⋯C2 的仪表存在了；**约束 8 从此可测**」 |
| `:407` 约束 3 `missing`，「无 runner、无执行环」 | `:62` green，「**proxy/runner.py** ⋯ 落地」 |
| `:892-893` C4 `missing`，「变体注入层与电池都**不存在**」 | `:199` p2-battery green；`proxy/variants.py`、`battery/`（126 个被跟踪文件）都在 |
| `:937`/`:939` IC3/PDR 与死锁刻画「**整道缺席**」 | `:371`/`:379` 两者皆 green，「M9 落地」 |
| `:293-297` p4-freeze `missing`，「十三项里目前只有『引擎清单与版本』接近可冻结」 | `git ls-files freeze` = **84** 个文件；`freeze/MANIFEST.json` 列 15 条、1–13 项**都有哈希路径**，只有第 8 项是 `absent` |
| `:300-305` p4-ablation `missing` | `git ls-files ablation-arm` = **135** |
| `:1164` WP9「PAPER.md **2512 行**成稿」 | `wc -l` = **3729**（磁盘与 pin 皆然） |

**「`missing` 只是阶段判定不是事实断言」这条辩护是死的**：`spec.py:12-18` 自己定义了词表——
`missing  no artefact exists for this clause`，而 `risk  an artefact exists but contradicts the
baseline document` 正是为「有产物但不对」准备的。所以字面 `missing` 就是「树上没有这个产物」。

**没有一条是写错的，全部是变陈旧**（`git blame` 逐行核）：那九行写于 02:13:55，
`proxy/{model_proxy,runner,variants}.py` 在 **+25 分钟**后落地，M9 在 **+34 分钟**后，
`ablation-arm/ablcore/*` 在 **+15 小时**后，`freeze/MANIFEST.json` 在 **+37 小时**后；
`:1164` 写于 07-28 23:10，`git show baf167149:papers/phase1-workshop/PAPER.md | wc -l` = **2512**，
写下时分毫不差。

**同一机制此刻正在未提交的 diff 里重演**：它把 `:1161` 的 `WP9 "pct": 65 → 67`，
而三行之下 `:1164` 的「PAPER.md 2512 行成稿」原封不动。

**二、S26 那条「无探针」免责标签只贴在六张表的一张上，而没贴的那几张里有一个被发布的计数。**

`monitor/scan.py:2643-2646` 给每一个没有探针的 `PHASES` 行追加
「〔无探针：本项无任何机器检查，状态为人工断言〕」再渲染——所以看板**已经告诉读者**
`p4-freeze` / `p4-ablation` 是未经核验的人工断言。**但这个缓解只写在 `PHASES` 的循环里。**
`CONSTRAINTS`、`CLAIMS`、`ARCHITECTURE` 被渲染并写进**被跟踪的** `monitor/state.json`
（`scan.py:2746-2751`）时没有任何这种标签，而 `con_green`（`scan.py:2694`，当前发布值 **1**）
是直接对着那张陈旧的 `CONSTRAINTS` 表求和的。

**这条不对称是本轮唯一既新、又可动手的部分。**

基准率，说不利于自己的一面：**126 行手写的 status·pct**（其中 121 行没有任何探针），
本轮新点出 **10** 行陈旧；加上早已在档的 10 个 GRID 格，是 **20 / 126 ≈ 16%**。
不是遍地烂，是一处刷新没刷完。

顺带一处悬空引用：`:937`/`:939` 指向 `T-05`，而 `spec.FINDINGS` 里**已经没有 T-05**。

---

## suggest（监控裁决，我不执行）

1. **把 S26 的免责行从 `PHASES` 循环推广到 `CONSTRAINTS` / `CLAIMS` / `ARCHITECTURE`**，
   在渲染与落盘之前。一个循环，不需要新判据，而且这正是本仓库对隔壁一张表已经选过的解法。
2. **十条 note 用 `@<rev>` 打戳订正，而不是重写判断**（沿用 `DRIFT-20260729T2315Z` suggest 1）。
   例：`:428` → 「模型代理在 79009fc4 时不存在；58722ca4 起存在，但仍无端到端计数 @79009fc4」。
3. 按文件自己的词表已经**明假**的状态位改成 `partial`：`p4-freeze`、`p4-ablation`、
   约束 3、约束 8、C4。C2/C5 保留 `blocked`，只改理由——战役确实还没跑，`blocked` 这个词是对的，
   错的是它给出的原因。
4. 顺手修 `:937`/`:939` 指向已不存在的 `T-05`。

## 三条会造成实害的做法，务必不要做

* **不要加一个"路径存在就把 status 翻绿"的对账器。** `freeze/STATS_RULES.md:3` 自己写着
  「状态：草案（DRAFT）。这份文件还没有被冻结」，里面有 **62 处未填的 `⟨…⟩`**。
  存在性驱动的对账器会把 `p4-freeze` 发布成 `green`——「冻结包完成了」——
  这正是本条审计线存在要防的那种夸大。`DRIFT-20260729T2315Z` suggest 5 已裁过：
  **「要装牙，先给 `pct` 装探针，顺序不能反」**。
* **不要手工把约束 3 和 8 翻成 `green`。** `con_green` 是**已发布的头条数字**（`state.json` = 1），
  而约束 8 的正文是「无意外则无模型调用；执行、校验与引擎全程零调用」——
  **模块存在 ≠ 约束被证实**。凭「文件被跟踪了」把 1 抬到 3，是把这份报告抱怨的那种假信心
  往上再造一层。要动就动到 `partial`，绝不是 `green`。
* **`monitor/spec.py` 此刻正脏着（12 增 12 删），而那个在飞的编辑正是另一个 agent 在执行
  `DRIFT-20260729T2315Z` 的 suggest 1**——它改了 GRID `C2/S4/V2/V3/V5`（那份报告十格里的五格）
  加 `E2/P2` 与五个 PAPER_PLAN pct，没动 `C3` 与 `V1`。
  **本条的整改工单必须写成「追加到在飞的那次编辑上」，不能写成「去改 spec.py」，否则会撞车。**
  我没有碰这个文件：以上引用全部来自 `git blame` / `sed -n` / `git show`，只读。
