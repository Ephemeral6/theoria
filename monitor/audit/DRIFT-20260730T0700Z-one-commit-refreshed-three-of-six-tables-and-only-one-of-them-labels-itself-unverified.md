# DRIFT-one-commit-refreshed-three-of-six-tables-and-only-one-of-them-labels-itself-unverified

> ┌─ 补正与更正（cycle 51，2026-07-30T10:20Z）────────────────────────────────────────────────
> │ **一、更正我自己上一世给这份报告选的展品，方向选反了。** cycle 50 的修订换上了
> │ 「`spec.py:906` 把模型代理标 green，而二十行之上 `:885`/`:892` 的 C2、C5 因为『度量它的模型代理不存在』被标 blocked」，
> │ 语气是拿 green 当可疑的一方。**实测：`proxy/model_proxy.py` 在 pin 上存在，落地于 `ae82ede6`（2026-07-28 17:04:18 +0800）**，
> │ 所以**陈旧的是那两行 `blocked`，不是那行 green，而且它们已经假了两天**。
> │ 矛盾本身成立（同一文件对同一件事同时断言存在与不存在），我指错了哪一半该改。
> │ **二、两个新的具名实例，都是同一份已发布产物里「手写数」被「自己测出来的数」当场否证**
> │ （我自己复核过，disk 与 pin 一致，不另开报告，按本报告已立的「20/126 手写行陈旧」聚合口径归入其中）：
> │ * `spec.py:1205`（S5）写「**台账 26 条** + 1951 行 MANIFEST …」。`arc-recon/data/incidents.jsonl`
> │   在 disk 与 pin 上都是 **18** 行，而**同一份 `state.json` 自己发布 `metrics.incidents = 18`**
> │   （由 `scan.py:1490` `count_lines()` 测得）。26 与 18 在同一个产物里描述同一个文件。
> │   同句的「1951 行 MANIFEST」是**真的**（`release/MANIFEST.jsonl` = 1951 行）——**半真是它没被发现的原因**。
> │ * `spec.py:913`（`ARCHITECTURE` 的 `theorize` 行）写「A0 上真跑通：**28 候选**逐条裁决入册」。
> │   `cold-start-a0/artifacts/candidates.jsonl` = **29** 行，且同一页另外两处都印 29
> │   （`metrics.a0_candidates`，以及 `a0_state` 探针 detail 里 2+3+1+23 = 29）。
> │   `grep -rn '28 候选' monitor/audit/` = 0，`grep -rn '台账 26' monitor/audit/ monitor/inbox/ monitor/mailbox/` = 0。
> │ **三、「八工序 / 九行」那处标签错误在同一文件里出现第二次**：除已记的 `scan.py:2662`，
> │ `spec.py:931` 的 `{"group": "车间八工序", "clause": "1.10(b)"` 之下是**九**个手写 chip
> │ （MDL / CEGIS / 零空间 / LP / IC3·PDR / 规划FD / 死锁刻画 / 前沿戳探 / Lean 证明），
> │ 并渲染成 `index.html:442` 那一行「车间八工序 …… **7/9 达成**」——**标题说八，自己的分母说九，同一行印三次。**
> │ **四、本报告 §「未提交的 monitor 状态」这条已被裁为 low 且框定过两条禁改**（不要让 `scan.py` 去读
> │ `git show HEAD:monitor/spec.py`、不要提交 `spec.py`）。cycle 51 复核确认：七处被改写的 `GRID` 理由**在 pin 上逐条为真**
> │ （`freeze/MANIFEST_DRAFT.md`、`engine-rig/heldout/*`、`figures/SOURCES.sha256` 已无 `ABSENT0000` 等），
> │ 所以**证据可复现、结论不可复现**（disk `paper_progress` 41.5 vs pin 39.02）。仍按 low 处理，不再重报。
> │ **五、`spec_freshness` 报 `spec.py 落后 289 个提交 / 88 次合并` 已由手工复算逐字复现**，
> │ 且它量的是被跟踪副本、页面渲染的是手改的 disk 副本——**误差方向偏保守（高报风险），按本报告既有裁决不算缺陷。**
> └────────────────────────────────────────────────────────────────────────────────────

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


---

# 附录 · 同一轮 dimension-8 扫描的另外三条候选，复核后只剩两句话

我对 `spec.py` 派了两个方向的对抗性复核。第一份的结论已写在上面。第二份打的是另外三条候选，
结果是**两条被我自己的 lineage 之前的裁决打死，一条降到 low 并与另一条合并**。照记，包括对我不利的部分。

### A. 「发布的头条数字来自未提交的工作副本」——降到 **low**，且框架是错的

事实对：pin 的 `spec.py` 算出 `paper_progress` = **39.02**，磁盘那份算出 **41.49**，
而磁盘的 `monitor/state.json` 写着 **41.5**，其 `generated_at_utc = 06:47:29Z`，
比 `spec.py` 的 mtime `04:55:24Z` 晚 1 小时 52 分——**这个数确实是工作副本的**。

**但两条反对意见各自都足以推翻这个框架：**

1. **我引 `spec.py:670-671` 定它的罪，引错了。** 那是 F-20 的 `action` 字段，
   讲的是「**一件交付**只有进了 master 才计分」——管的是**被测量的对象**（分支上还没合并的 done），
   不是**测量仪器自己的提交状态**。而且那次未提交的编辑，它每一条替换 note 的理由**恰恰就是「已进 master」**：
   `"freeze/MANIFEST_DRAFT.md 已在 master"`（S4 15→45）、`"held_out 已进 engine-rig"`（E2 92→95）、
   `"三态不变量已在 master"`（C2 80→90）、`"master 可见"`（V2/V3）。
   **拿 F-20 去定这次编辑的罪是范畴错误——那次编辑正是 F-20 在被执行。**
2. **这个分歧从来没有一次进过 master：14 次比对，14 次一致。** 用**每个 commit 自己的** `spec.py`
   重算，对比**同一个 commit 自己的** `state.json`，覆盖最近 14 次 `state.json` 提交、三个头条时代
   （39.0×3、38.6×4、50.0×7）——**零不匹配**。pin 上 `git show 304ad651:monitor/state.json`
   是 `39.0`，与 pin 的 `spec.py` 的 39.02 对得上。**41.5 只存在于这一台机器的工作树里。**

而且这个工作流是**设计**不是偏差：`scan.py` 按构造 `import spec`，两天里 `spec.py` 提交了 13 次、
`state.json` 14 次，**每一次两次提交之间的扫描都必然读工作树**。

`probe_spec_freshness` 也不是「按构造瞎」：`scan.py:675-700` 的 docstring 自陈其目的是
「手写判断 vs 主线漂移速度」——它就是为**手写值相对主线变陈旧**造的，不是为未提交编辑造的。
而且**它的误差方向是保守的**：现在 `state.json` 里它喊 `risk, "spec.py 落后 270 个提交 / 84 次合并"`，
而那些值两小时前刚被重新推导过。**它多报风险，那是安全的方向。**

**真正剩下的残渣，一句话，而且是一把从未走火的上膛的枪**：
`state.json` 与 `spec.py` 是**各自独立提交**的——最近 14 次 `state.json` 提交里有 3 次
（`23cee0e0`、`7a71b5ab`、`e70df5aa`）没有同时动 `spec.py`。此刻 `spec.py` 脏在 41.49、
`state.json` 脏在 41.5。**如果下一次提交只带走 `state.json` 而不带 `spec.py`，
master 上就会有一个它自己的 `spec.py` 复现不出来的头条数字，而没有任何东西会发现**：
`paper_progress` 不在 `monitor/verify.py:79-82` 的 `REQUIRED_STATE_FIELDS` 里，
`_fields()` 只查字段**存在**，`grep paper_progress monitor/tests/` **零命中**。

**最小修法**：不是加断言（`assert paper_progress == sum(w*pct)` 是同义反复），
而是一个**提交时的耦合检查**——若 `monitor/state.json` 已暂存而 `monitor/spec.py` 脏且未暂存，就拒绝。约十行。

> **⚠️ 明显的那个修法有害，不要做。** 诱人的写法是「让 `scan.py` 从
> `git show HEAD:monitor/spec.py` 读，这样看板永远反映 master」。**不行**：
> (i) 它会让看板在**审计正在发生的那个窗口里**结构性地无法显示任何在飞的订正；
> (ii) 它会打断 `monitor/verify.py:44-48` ——那里刻意用 `scan.build(out_dir=mkdtemp)` 校验**工作树**，
> 是 S13 自己写下的警告；(iii) 在 detached 检出上监控将完全无法渲染。
> **也不要「顺手把 spec.py 提交了」**：那是活树改动，违反 `AUDITOR.md` 的红线，而且会毁掉证据本身。

### B. 「两个探针不可能变红」——**驳回**，其中一半是我自己 lineage 早已裁定为正常的

* `probe_a0_state`：`monitor/audit/DRIFT-20260728T1611Z-a1-probe-can-only-ever-say-partial.md:11`
  对全部 15 个 `probe_*` 做过 `ast` 普查并**点名裁定**：
  「`probe_a0_state` / `provenance` / `dispatch_board` / `inbox` 是 green+partial 的**盘点型**探针，**属正常**」。
  从未被推翻。**先例本身就足以杀死这一半。**
* `probe_determinism_state`：**候选说它只有两个状态字面量，这是事实错误。它有三个。**
  `scan.py:219-220` 是 `if not verdicts: return {"status": "blocked", …}`，
  而 `spec.STATUS_SCORE` 里 `blocked = 0.15` 是**全表最狠的分**（低于 `risk` 0.25）。
  所以「即使是彻底失败也不会红」正好说反了：**最彻底的失败（文件整个不见）拿到的是系统能给的最低分。**
  沙箱实测：`precheck.json` 缺失 → `blocked`；`results` 为空 → `blocked`。
* 而 `probe_a1_state` 那次修复是**限定范围**的：板上条目 `S26-phase1-gate-must-decide` 要的是
  「任何 `probe_*` 里**算了量却不用于 `status`** 的」，而 `probe_a0_state` 的量
  （`done == len(have)`）是**用了**的，它从来不在 S26 的网里。

**唯一剩下、且看起来没归过档的残渣，是一条真正的「不可能变红」，而且修法只有一行：**
`_VERDICT_RANK`（`scan.py:2576`）= `{"risk":0,"missing":1,"amber":2,"partial":3,"green":4}`
——**没有 `blocked` 这一项**，于是 `.get("blocked", 9)` = 9，把「跑不起来」排得**比 green 还好**。
沙箱实测：对带 `probe_scope: "partial"` 的 `p1-a0`，一个 `blocked` 裁决会被判成**升级企图而遭拒**，
手写的 `green` 以 1.0 分留下；对 `p1-determinism`（无 `probe_scope`）`blocked` 会被采纳，
但覆盖日志把它标成「probe upgraded」。**今天是潜伏的**（`probe_a0_state` 不会发 `blocked`），
但任何一个部分范围条目、其探针报告「我跑不起来」，都会渲染成 green。

> **⚠️ 加 `blocked` 进 `_VERDICT_RANK` 时必须排 0 或 1（与 `missing` 并列）。
> 排到 `partial` 之上会让「检查跑不起来」**升级**一个手写的 `partial`——把一个空结果变成健康的证据。
> 那是上一轮那条会永久关掉配额熔断器的建议的同一个失败类。**
> 另外**不要**把 `probe_a0_state` 的 0/10 改成 `risk`/`missing`：它已被裁定为正常，
> 而且往下动会移动一个 `Theoria.md:305` 全绿闸门所依赖的 Phase-1 条目。

### C. 「`_offline_done` 授权战役全速而不可能变红」——**驳回，而且这是同一个错误在本 lineage 的第四次**

`DRIFT-20260729T2315Z:59` 已经查明：`_offline_done()` 注册在 `PROBES`，但 `spec.PHASES` 里
五处 `"probe":` 绑定**不含 `offline_done`**——它从不进 `_reconcile`、不产生 `verdict_override`、
不改变任何条目状态；`:61`「**这不是舰队级裁决，是渲染**」。
而那份报告自己的对抗性复核 `:93` 写着：「**这是本周期第三次**…**这个错误在本 lineage 已经形成惯性**」。
我这一轮又派了一个 subagent 把它当成新发现交回来——**第四次**。
它唯一新的元素 `E2 92→95` 也不是 `_offline_done` 的第二个缺陷，
而是上面 A 条那个机制的**第二个展品**。

> **⚠️ 不要给 `_offline_done` 加 `risk` 分支或任何执行后果。**
> `DRIFT-20260729T2315Z:84-85` 已裁：「**它今天没有牙是对的**：一个建立在无人核对的手写 `pct` 上的
> 舰队级裁决，比一段渲染文字危险得多。**要装牙，先给 `pct` 装探针，顺序不能反。**」

### 本附录对我自己的结论

三条候选，**两条死在我自己 lineage 已经写下的裁决上**（一条是第四次），一条降到 low 并入 A。
我这一轮的 dimension-8 扇出交回 11 条候选，最后只值 1 份报告加这一段附录——
**扇出提高的是覆盖，不是命中率；命中率是复核提高的。**

---

## 附录二（OPS-A cycle 50，2026-07-30T08:0Z 追加）—— 七处仍然全活；换两个更硬的展品；并把「六表」这个说法本身订正

pin `origin/master = 13bbcad9`（07:46:41Z 钉）。`monitor/spec.py` 在盘上是脏的（12+/12−），
但那 12 行**只动 `PAPER_PLAN` 的 pct 与 8 个 `GRID` 单元**，`CONSTRAINTS`/`CLAIMS`/`ARCHITECTURE`
一行未动——所以下面每条在 `pin` 与 `disk` 上同时为真。`scan.py` 三处引用 `disk == HEAD == pin` 逐字节相同。

### 一、七处矛盾一处未修，`con_green` 的机制确认

`git blame -L … 13bbcad9`：`CONSTRAINTS`（47 行）与 `CLAIMS`（17 行）**100% 仍是
`79009fc4e` 2026-07-28 02:13:55**，其后零 commit。正文那七处逐条复核，**全部仍活**。

`scan.py` 三处行号复核（`pin`，逐字）：

* **`:2643`** 免责标签是**单独一行**，不是正文写的 2643-2646：
  `note = note + "  〔无探针：本项无任何机器检查，状态为人工断言〕"`，
  其 S26 理由注释在 `:2640-2642`。**正确引法是 `:2640-2643`。**
* **`:2662-2664`** 在那个循环**之外**，不带任何标签。
* **`:2694`** 行号未漂移，逐字为
  `"con_green": sum(1 for c in spec.CONSTRAINTS if c["status"] == "green"),`

我独立跑了一遍 pin 上的表（`git show 13bbcad9:monitor/spec.py` 求值）：
`CONSTRAINTS` 10 行 = `{partial 5, missing 2, risk 2, green 1}` → **`con_green` 算出来就是 1**，
与 live `monitor/state.json`（disk）发布的 `con_green: 1` 一致。**正文那一半确认：
一个发布出去的头条数字，直接对一张陈旧手写表求和，且不带免责标签**，
而它旁边 16 行 PHASES 有 11 行带着「无探针」标记。

### 二、换掉正文的展品：一对不需要跨表论证的矛盾（本附录的主要贡献）

正文用的是 `PHASES:46` 对「约束 8」，那需要跨两张表论证。**同一文件里有一对只隔二十行的，更硬：**

```
spec.py:906  {"label": "模型代理", "status": "green",   "tip": "model_proxy + 版本化价目表；C2 仪表就位"}
spec.py:885  {"id": "C2", …, "status": "blocked", "note": "度量它的模型代理不存在。这是最容易被忽略的关键路径。"}
spec.py:892  {"id": "C5", …, "status": "blocked", "note": "同 C2，需要模型代理。"}
```

`:906` 正是 `edb3c3748` 刷新过的单元之一，`:885`/`:892` 是 `79009fc4e` 02:13:55 的原值。
**被刷新的那一格，它自己的 `tip` 点名了它所反驳的那条 claim（「C2 仪表就位」），
而 C2 二十行之上仍写着「度量它的模型代理不存在」。** 一个文件、一次提交刷了一半、
两条 `blocked` 的唯一理由是一件被同文件宣布为 green 的东西。**再引用本报告时请用这一对。**

### 三、一处正文没抓到的、标签与数据在同一个字典字面量里打架

```
scan.py:2662  {"name": "车间八工序", "counts": counts_of(spec.ENGINES)},
```

我求值 pin 上的 `spec.ENGINES`：**9 行**（`{green 7, partial 2}`）。
**标签说八，数据是九，在同一行里。** 与 `CLAUDE.md` 的「六引擎」不是同一处错，
但是同一类：手写的数字与它所标注的表各自演化。

### 四、订正本报告标题里的「六表」——它低估了自己的分母

`spec.py` 的手写表不是六张而是**九张**：除 `PHASES`/`ENGINES`/`CONSTRAINTS`/`CLAIMS`/`ARCHITECTURE`
与第六张 `FINDINGS`（`:443`）之外，还有 `ITERATION_LOOP`、`PAPER_PLAN`、`GRID`。
正文自己引的「126 条手写 status·pct 行」这个分母其实已经覆盖了九张——**是标题里的
「六」与它自己的证据不一致**。不改标题（本文件已在主线上），在此以附录订正。

### 五、本轮 dimension-8 扇出的其余部分，与它们的去向

同一次扇出交回四条孤儿字段候选。我起初判 `bus.py:161-166` 那条「另开文件」，
**复核把它降级了，我采纳：不另开文件，降为一条修复请求，留在本段。**
理由是它够不上：`cmd_status` 只能由人手敲 `python monitor/bus.py status` 触达（`bus.py:213`），
没有任何东西解析「X 分钟前露面」；而 `scan.py:_bus_probe`（`:1002-1057`）只读 `last_seq`、
**根本不计算新鲜度**（尽管它的 docstring 承诺「谁多久没露面」），所以仪表盘与全部探针都不受影响。
**缺陷本身实测成立**：`monitor/bus/*/cursor.json` 八个里 `read_at` 全有，RES-2 的
`read_at` 03:03:45Z 对 mtime 04:55:24Z，**差 111.7 分钟，其余七个为 0**；方向恒定（`mtime >= read_at`）。
**两处订正我自己：**（a）成因不能写成「`ci_merge` 在 04:56:35Z 重新盖了戳」——mtime 是 04:55:24Z，
比那条日志早 71 秒，只能说「落在 04:38:27Z 的 MERGED 与 04:56:35Z 的 SWEEP-FLAGS 之间」；
（b）**这条我自己的 `audit/state.json:30` 早就写下了**，措辞比扇出交回的还准，所以它不是新发现。
**两件所有既有记录都没有的，写进修复请求**：`fleetkit/fleetkit/bus.py:137` 是**同一缺陷未修的克隆**，
S40/S42 都没点到它，所以修法有**两个**落点；以及 `read_at` 在全仓零代码读者，
而三份 inbox 报告（`W-1620:143`、`W-1621:104-106`、`W-1622:99`）都手工从盘上读它当可信数——
**人用对了字段，代码没有。** 另外三条的处置写在本轮的 `state.json` 与 WIP 里：
`ops-status/RES-1.json` 的五个私有键判**惯例**（八个文件里只有它一个有，
且 `DRIFT-20260728T1752Z:40` 已裁同形不是漂移）；`state.json` 的 `metrics` 判**惯例**
（它有真实的 agent 读者，`DRIFT-20260730T0019Z:211` 就拿 `metrics.dirty[0]` 当过主证据；
真正为真的只有 `scan.py:1872` 那个死局部变量，是 lint 级）；
`accounts.py` 的 `mark_open` **第三次被杀**（`DRIFT-20260729T1515Z:141` cycle 38 杀过一次，
`DRIFT-20260729T1830Z:99-101` 杀过第二次，`accounts.py:159-160` 有基于时间的出口），
而「`launches` 不清零会歪掉调度」被**实测否掉**：`accounts.json` 只配了两个账号，
`home` 无条件前置，`sorted()` 作用在一个单元素生成器上，是恒等——`launches` 被读，
但改不动答案；它要到第三个账号才获得行为，而那个场景本身已在禁令之下。
