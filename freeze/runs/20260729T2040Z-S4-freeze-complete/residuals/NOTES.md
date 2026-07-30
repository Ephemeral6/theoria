# residuals/NOTES.md —— 抽取说明与两处交叉核对

抽取者：RES-1 派出的 subagent，2026-07-29/30，工单 S4-freeze-complete。
产物：`extracted.json`，**64 条**记录。本文件只写 `extracted.json` 里放不下的三样东西：
**两处交叉核对的结果**、**重号报告**、以及**抽取口径与它排除了什么**。

---

## 0. 快照与一条使用警告：行号是易变的

抽取时的文件快照（sha256 前 16 位，worktree `.worktrees/s4-freeze`，HEAD `5822e5e5`）：

| 文件 | sha256[:16] |
|---|---|
| `freeze/MANIFEST_DRAFT.md` | `0067ed25ccf52bf1` |
| `freeze/PENDING_FIVE.md` | `618d4bb2f24b2be1` |
| `freeze/STATS_RULES.md` | `86b912c54bb28f40` |
| `freeze/CLAIMS_TEXT.md` | `c44666c6d42ebb7e` |
| `freeze/RECONCILE.md` | `ecd713f69916dd8d` |
| `freeze/launch_blockers.json` | `551fa18294edf414` |

**本次抽取期间，另外三个 subagent 正在同一 worktree 里改这三份文件，行号至少漂了三次**
（实测：`STATS_RULES.md` 新增 §5.7 后 §9 表从 :823 移到 :903；`PENDING_FIVE.md` 全篇 +5;
`MANIFEST_DRAFT.md` 附录从 :439 移到 :480）。`extracted.json` 里的 `line` 已按上表快照重取并逐条复核过，
但**如果 RESIDUALS.json 的闸按行号定位残余，它会在下一次并发编辑时误红**。
建议闸按**标记串**定位，锚点是稳定的：

```
⛔ 缺 <code> / ⛔ 待办 <code> / ⚠ 待办 <code> / ⛔→⚠ 待办 <code>
| 9.<n> |            （STATS_RULES §9 表行首）
- [ ] **G<n> ·        （RECONCILE 移植清单未勾项）
```

同一个原因，`RECONCILE.md:280` 自己引的 `STATS_RULES.md:95` 与 `:559` **已经失效**
（那两个行号是 P-22 时代的；现行对应行是 §1.2 与 :837）。这就是行号锚点的失效样本。

---

## 1. 交叉核对一 · 重号：`2-b` 确认，且抽取期间已被改号

**确认。** 在快照 `1c9d1a68`（本次抽取开始时）的 `MANIFEST_DRAFT.md` 上：

* `:116` `**⚠ 待办 2-b（订正）**` —— `dsl_grammar_v0.2.md:39` 写 five sections，底下定义六节；
* `:125` `**⛔ 待办 2-b（G5，自 S4 移植）**` —— v0.2 的冻结政策挂在一个不存在且自指的 tag 上。

两条同号，一条 ⚠ 一条 ⛔，落在同一个契约文件上但**是两个互不相干的缺陷**，
所以「2-b 做完了吗」在这份稿子里确实有两个答案。

**抽取期间它已被修：** 现行快照的 `:116` 已改写为
`**⚠ 待办 2-c（订正；2026-07-29 由 `2-b` 改号，见下）**`，`:132` 保留 `⛔ 待办 2-b（G5）`。
方向与我本来要提的建议一致 —— **该动的是 ⚠ 那一条**，理由三条：
(a) ⛔ G5 已经被 `RECONCILE.md:220-231` 的移植清单以「`MANIFEST_DRAFT.md` 待办 2-b」逐字引用，
改它会把一个跨文件引用打断；
(b) G5 那条还进了 `build_manifest.py` 的 item 2 注释；
(c) ⚠ 那条只有本地引用。`extracted.json` 因此按现行文本记作 `2-c`（`:116`）与 `2-b`（`:132`），
并在 `2-c` 的 `statement` 里留下改号事实，以免下一个读者以为从来没有过重号。

### 其余重号 —— 三处，其中两处比 `2-b` 更容易咬人

1. **`H-1` 跨文件同号，含义完全不同。**
   `MANIFEST_DRAFT.md:36` 的 `⚠ 待办 H-1` = 根 `.gitattributes` 缺全局 `text=auto eol=lf`（**未解，工程项**）；
   `RECONCILE.md:271` / `:441` 的 `H-1` = 「U3 按单样本比率还是跨臂配对检验」（**已裁定**）。
   一个开着一个关着，同一个 key。`RESIDUALS.json` 若以 `code` 为主键，
   建议把 MANIFEST_DRAFT 那条改成 `EOL-1` 或 `H1-gitattributes`，
   `RECONCILE` 的 H-1..H-5 是已裁定记录、不该进 owner 表（见 §3）。

2. **`G1`…`G7` 是两套完全不同的东西，而且两套都在冻结稿里被引用。**
   * `RECONCILE.md:170-260` 的 `G1`…`G15` = 从 S4 移植回来的条目
     （`G1` = U3 公理白名单，`G7` = 剔除上限）；
   * `MANIFEST_DRAFT.md:390` 与 `PENDING_FIVE.md:168` 的 `G1-G7` =
     `baseline-arms/BUDGET_REPORT.md` §9 的**七条可执行预算闸门**
     （`G4` = 包络中止那条，`G7` = 非授权 game_id 出现，「原样保留且永不调高」）。
   于是 `STATS_RULES.md` 里的「G1 放宽了判据 (b)」与 `PENDING_FIVE.md` 里的「G1–G7 七条闸门」
   指的是两个 G1。**这一处比 `2-b` 危险**：预算闸门的 `G7` 管的是不可撤销的损害，
   而移植项的 `G7` 是一条统计条款；把两者混起来的一次误读就足以关掉错的那个。
   建议把移植项统一加前缀（`S4-G1`…`S4-G15`）或把预算闸门写成 `BR-G1`…`BR-G7`。

3. **`§9` 表行序与编号不一致**（不是重号，但会让机器抽错）：表里的顺序是
   9.1 → **9.2 → 9.14** → 9.3 → 9.4 → … → 9.13，`9.14` 插在 9.2 后面（因为它与 9.2 同批升级）。
   按行序读会把 9.14 当成 9.3。`launch_gate.py` 是按行首 `| 9.` 正则读的，不受影响；
   人和新写的解析器会。

---

## 2. 交叉核对二 · 散文 vs `launch_blockers.json`

`freeze/launch_blockers.json` 恰好三条：**9.2 / 9.11 / 9.14**。

### 2.1 闸里有、散文里没有对应残余的 —— **零条**

三条全部在散文里有落点，且不止一处：

| 闸 | 散文出处 |
|---|---|
| 9.2 | `STATS_RULES.md:904`（表行）、`:81-82`、`:187-188`、`CLAIMS_TEXT.md:79-80`、`PENDING_FIVE.md` 附 B |
| 9.11 | `STATS_RULES.md:914`（表行）、`§7` 结尾「登记为开跑前置条件」、`§5.7`、`PENDING_FIVE.md:125`「列为开跑前置条件」、`MANIFEST_DRAFT.md` `13-c` |
| 9.14 | `STATS_RULES.md:905`（表行）、`MANIFEST_DRAFT.md` `8-a`、`PENDING_FIVE.md` 附 B |

一处值得记：`launch_blockers.json` 的 9.11 自陈「if the re-run has in fact landed, this entry is what has to change」。
**包络重跑没有落地**（`BUDGET_REPORT.md` §11.5 的两件事仍未做）；
落地的是**另一件事**——⟨n⟩ 依据的四个 JSON 已被提交（见 §3）。两件事不要混。

### 2.2 我判 `launch_blocker` 但不在闸里的 —— **六条，其中三条是真分歧**

`extracted.json` 里 severity=`launch_blocker` 共 9 条：`9.2` `9.11` `9.14`（在闸里）
＋ `5-a` `5-b` `8-a` `8-b` `13-c` `13-e`（不在闸里）。

判据来自 **`MANIFEST_DRAFT.md:5` 的一句总纲**（逐字）：

> **只要还有一项是 `⛔ 缺`，就不该开跑封存战役。**

这句话把每一条 `⛔ 缺` 都变成了一条开跑阻塞。逐条过：

| 残余 | 在闸里吗 | 判断 |
|---|---|---|
| `8-a` | 是（编号 9.14） | **不是分歧，是编号断裂**。同一个缺陷有两个 id，两份文件各用一个，**没有任何东西把它们连起来**。RESIDUALS.json 应该显式记下 `8-a ≡ 9.14`，否则关掉一个会让另一个看起来还开着（或反过来）。 |
| `13-c` | 是（编号 9.11） | 同上：`13-c ≡ 9.11`。 |
| `5-a` | **否** | **真分歧。** ⛔ 缺「没有任何机器可读的引擎清单」。按总纲不得开跑，闸不知道它。 |
| `5-b` | **否** | **真分歧。** ⛔ 缺「引擎带名字不带版本」。同上。 |
| `8-b` | **否** | **真分歧。** ⛔ 缺「判决题准确率没有电池 id」——三个主终点之一在电池注册表上不存在。同上。 |
| `13-e` | **否** | ⛔ 缺，但**本段自记「已于本轮修」**且 owner 是 RES-1；标记没跟着改。见 §3 与下方。 |

**结构性发现（这条比逐项名单要紧）**：`freeze/launch_gate.py:76,116,133` 只读
`freeze/STATS_RULES.md` 的 `## 9.` 一节，凡类型格写 `开跑前置条件` 的行才算 blocker。
**它从不读 `MANIFEST_DRAFT.md`。** 所以 `MANIFEST_DRAFT.md:5` 那句总纲
——整份 13 项清单里唯一一句「不该开跑」——**在树上没有任何执行形态**，
和 §9 那三行在 `launch_gate.py` 写出来之前的处境一模一样
（`STATS_RULES.md:928-935` 自己就是这么描述那个处境的）。两条出路，二选一即可，
但不能不选：
1. 把 `5-a` / `5-b` / `8-b` 按 §9 的格式登进 §9 表（并在 `launch_blockers.json` 里给命令模板 + 两个靶子），或
2. 把 `MANIFEST_DRAFT.md:5` 改写成「⛔ 缺挡冻结，不单独挡开跑」，并说明为什么一个缺失的引擎清单不挡开跑。
   —— 我倾向 (1)：一个没有版本串的引擎清单，事后无法重建臂跑过的那套引擎，
   这与 9.14 属于同一类损害（花掉的钱买回来的东西不可复现）。

### 2.3 散文里被提议为开跑前置条件、但闸与 §9 都没有的 —— 一条

`RECONCILE.md:282`（H-5 讨论第 4 点）逐字「**建议列为上线前置条件**：在线消融臂必须与
Theoria 臂走同一套后端」。这是**唯一**一处以「上线/开跑前置条件」措辞出现、
却既不在 §9 表也不在 `launch_blockers.json` 里的提议。
记为 `NH-RC-h5-online-ablation-backend`，severity 判 `freeze_blocker`（因为「建议」不是权威，
而 §9 与 `launch_blockers.json` 才是），但它需要一次裁定：**升进 §9，还是明确驳回**。
悬着的后果具体：Theoria 臂与消融臂跑两套编译后端 = 第二刀，
而 `ablation-arm/DESIGN.md:29-30` 依 `Theoria.md:280` 只许切一刀，且这第二刀正落在 C2 依赖的对比上。

---

## 3. 抽取期间被别人关掉的残余 —— 不要让它们进 owner 表

并发编辑在本次抽取过程中关掉了四条。**它们已从 `extracted.json` 移除或标注**，
理由就是工单里那句话：一个已经满足的阻塞留在表里，就是一条永久的假阻塞。

| 残余 | 状态 | 独立复核（我自己跑的，不是抄文档） |
|---|---|---|
| `13-a`（⛔ 缺 · ⟨n⟩ 依据 untracked） | 文中已改 `✅ 已消解` | **确认已解**：`git ls-files baseline-arms/out/campaign` 返回 **4** 个文件，`git log` 指向 master 祖先 `9307f139`（"A14: the four campaign artefacts were paid for and were in nobody's git"），每份 JSON `episodes` 长度 12（合计 48）。**已从 extracted.json 移除。** |
| `13-b`（⚠ 待办 · 两份包络记录未对账） | 文中已改 `✅ 已对账` | 未独立复核 `VARIANCE_BASIS.md` §4 的算术；**已从 extracted.json 移除**，若 RES-1 要保守可要求那一节的复算脚本落盘。 |
| `P5-2a`（`PENDING_FIVE.md:48` 的 ⚠「`CLAUDE.md` 写着 no game has been played」） | 抽取期间被赋号 `P5-2a` 并标 `✅ 缺 … 已消解` | **确认已解**：`CLAUDE.md` 现写 `trajectories_reviewed` 与 F-11 的 19 局裁定。**未进 extracted.json。** 注意它与 `A-4` 是同一件事的两半，`A-4` 保留（因为它要的是「冻结前再核一次」这个动作，不是那句话本身）。 |
| `13-e`（⛔ 缺 · 生成的清单否认 ⟨n⟩ 有值） | 段内自记 **owner：RES-1。已于本轮修** —— 但标记仍是 `⛔ 缺` | **保留在 extracted.json**，severity `launch_blocker`，并在 statement 里写明这处标记/正文的矛盾。同节的 13-a/13-b 已改成 `✅`，13-e 没改。**要么改标记，要么它就是一条永久绿的 blocker 行。** |

另有 **`A-1`**（`MANIFEST_DRAFT.md:479`，「消融臂不存在」）在文中被删除线划掉并标「已作废」，
由 `A-1′` 取代；**未进 extracted.json**，只记 `A-1′`。

---

## 4. `clears_when` 为 null 的 —— **零条**

64 条全部给了命令或可核对的条件。写的时候守了两条自我约束，说明在此以便审：

* **凡我判 `human_decision` 的（17 条），`clears_when` 检的都不是「人拍了没有」，而是
  「拍的结果有没有落到一个可读的字节上」** —— 例如 ⟨Δ⟩ / ⟨k⟩ / ⟨X⟩ / ⟨m⟩ / ⟨R⟩ / ⟨S_min⟩
  一律写成「`freeze/MANIFEST.json` 的该项是一个数值且不再是 `⟨…⟩` 占位」。
  「监控确认」本身不可测，「监控确认的结果在盘上」可测。
* **有九条的 `clears_when` 是「二选一皆可查」**（`H-1` `1-a` `2-b` `6-a` `7-a` `8-b`
  `9.9` `NH-PF3-model-version-strings` `NH-RC-h5-online-ablation-backend`）。
  这不是含糊，是文档自己给了两条出路且都合法（修 vs 登记）。
  **闸要接受任一支通过**，否则会把「已按第二条出路登记」误判成未清。

三条 `clears_when` **在写下的当刻就已经满足**，标出来免得被当成活口：
`13-a`（已移除）、`5-d` 的前半（`git tag -l 'engine-rig-m*' | wc -l` 已是 9）、
`A-4` 的前两个 grep（`CLAUDE.md` 已含 `trajectories_reviewed` 与 `F-11`）。
后两条的**其余部分**仍未满足（引擎清单未写、冻结提交上的复核未做），所以记录保留。

---

## 5. 抽取口径 —— 我按什么收，按什么不收

**收：** 一条记录 = 文档给了**标签**的一处残余。标签形式见 §0。
`STATS_RULES.md` §9 的 `9.1`…`9.14` 按文中编号收（不铸新 id），
因为 `launch_blockers.json` 与 `launch_gate.py` 都以这些编号为主键。

**不收（是同一条残余在别处的重述，没有自己的编号）** —— 交叉引用表，
RES-1 可以据此判断闸要不要在这些位置也认同一条：

| 残余 | 在别处的重述 |
|---|---|
| `9.1` | `STATS_RULES.md:73`（§1.2 标题里的 needs_human） |
| `9.2` | `STATS_RULES.md:81-82`、`:187-188`、`:967`（§10 钻法表）、`CLAIMS_TEXT.md:79-80`、`:126`、`PENDING_FIVE.md` 附 B |
| `9.6` | `STATS_RULES.md:324`、`PENDING_FIVE.md:241`（§4.5，⟨m⟩ 取值） |
| `9.7` | `STATS_RULES.md:861` |
| `9.8` | `STATS_RULES.md:381` |
| `9.11` | `STATS_RULES.md:873`（§7）、`:787`（§5.7）、`PENDING_FIVE.md:121-126`、`MANIFEST_DRAFT.md` `13-c` |
| `9.13` | `STATS_RULES.md:517`（§4.1.1 的「登记为 needs_impl」）、`RECONCILE.md:219` |
| `9.14` | `MANIFEST_DRAFT.md` `8-a`、`RECONCILE.md:355`（N-3） |
| `9.3` | `MANIFEST_DRAFT.md` `A-2`、`CLAIMS_TEXT.md:23/37/147`（我为后者单独收了 `NH-CT-premise-schema-absent`，因为它要动的是 **claim 逐字文本**，与 §9.3 的动作不同） |
| `13-a` | `STATS_RULES.md:553-562`（抽取期间已被划掉并补 `✅ 已消解` 段，含「不许把这条读成『⟨n⟩ 的依据已经充分』」的分寸——处理得比 `13-e` 干净） |
| `A-1′` | `PENDING_FIVE.md` 附 A |
| `13-c` | `PENDING_FIVE.md:121-126`（抽取期间已改写为「见 13-c」，是好的方向：一个缺口只在一处声明） |

**不收（不带标签、也不带 `needs_human`/`needs_impl`/`开跑前置条件` 三个关键词）** ——
四处，逐条说明为什么，请 RES-1 自行裁定要不要补：

1. `STATS_RULES.md:968`（§10 钻法表）「**降低定理野心刷 U3 率 · ❌ 封不死**」与
   `:973`「**巨型首回合 prompt 刷 E2 · ❌ 封不死**」，合并声明在 `:983-984`
   「两条都必须进论文的 limitations」。
   **这是两条最纯粹的 `register_limitation`**，落点是 `papers/`，但没有任何编号，
   所以现在没人拥有它们。**我建议补收**（可铸 `LIM-U3-ambition` / `LIM-E2-megaprompt`），
   否则「必须进论文」这句话在冻结包里没有对应的表行。
2. `STATS_RULES.md:190-193`（§1.2.1 里照录的残余漏洞）「本条款堵的是空转，不是平庸；
   『难度』没有被操作化，本轮也不假装它被操作化了」。同类，无编号。
3. `RECONCILE.md:70`「仍待办（散文部分）：`STATS_RULES.md` §1.2 与 `PENDING_FIVE.md` §4.2
   的正文还写着 21 与 14/21」。**已被 N-1 的 ✅ 段落取代**（58 处 21 逐处分类过），
   属陈旧条目，不收；但它和 `13-a` 一样是「文里还留着一句已经不成立的待办」的样本。
4. `MANIFEST_DRAFT.md:479` 的 `A-1`（已作废，见 §3）。

**没有用到的两个 `kind`，说明理由**（免得看起来像遗漏）：

* `cut_a_tag` —— 唯一像它的是 `2-b`（G5），但文档逐字写「**这不是补个 tag 就能修的，
  必须改写那句话**」，且给了三条出路（具名 tag / 指名提交哈希 / 随冻结包冻结）。
  判 `cut_a_tag` 会把一次契约裁定伪装成一条运维动作，所以判 `human_decision`。
* `commit_untracked_evidence` —— 本来只属于 `13-a`，而那条的证据**已经提交**（§3），
  剩下的动作是订正两处「untracked」措辞，故那一类此刻在这五份文档里为空。
  若 `STATS_RULES.md:553` 迟迟不改，它会变成一条 `write_document`，不是 `commit_untracked_evidence`。

---

## 6. 计数

* 记录：**64**（`MANIFEST_DRAFT.md` 29 · `STATS_RULES.md` 15 · `RECONCILE.md` 12 · `PENDING_FIVE.md` 7 · `CLAIMS_TEXT.md` 1）
* `kind`：`write_document` 23 · `fix_code` 18 · `human_decision` 17 · `register_limitation` 6 · `cut_a_tag` 0 · `commit_untracked_evidence` 0
* `severity`：`freeze_blocker` 54 · `launch_blocker` 9 · `registered` 1
* `clears_when` 为 null：**0**
* 文档已经点了 owner 的：**12** 条（`2-b` `13-d` `13-e` `A-1′` `9.11` `A16-launch-gate-wired`
  `G8` `G10` `NH-PF4.2-budget-B` `NH-PF4.2.1-sealed-game-count` `NH-PF4.3-delta` `NH-PF4.4-k`）
  —— 其余 **52** 条 `doc_says_owner` 为 `null`，即工单说的那半边确实基本没写。
  这 12 条里只有三种答案：**监控**（钱那一批：B / 局数 / Δ / k）、
  **RES-1**（`13-e`）、**一个赛道或看板项**（`2-b`→theory-compiler/S9、`A-1′`→proxy 轨道 +
  无人认领的 `A4-ablation-online`、`9.11`→`owner_hint: baseline-arms`、
  `A16-launch-gate-wired`、`G8`→`agent/v5-battery-freeze`、`G10`→「G7/G10 的移植人」）。
* 一条口径提醒：`severity=freeze_blocker` 不等于「不急」。`Theoria.md:368` 要求冻结清单
  **在首局开跑前**提交并哈希，所以每一条 freeze_blocker 都传递性地是开跑前的活。
  `launch_blocker` 这一层的意义只是**更强**：它连「已经冻结了但这一项是坏的」也不放过。

---

## 7. 我独立复核过的树上事实（用于写 `statement` 与 `clears_when`，不是转抄文档）

| 断言 | 复核结果 |
|---|---|
| 根 `.gitattributes` 无全局 `text=auto eol=lf` | 属实：仅两行 `PARTNER_SYNC.md merge=union`、`monitor/board/** text eol=lf` |
| 无 DSL/grammar tag | 属实：24 个 tag，`git tag -l | grep -i 'dsl\|grammar'` 空 |
| `dsl_grammar_v0.2.md:10` 自指 tag、`:39` 写 five sections | 属实，逐行核 |
| 引擎 `__init__.py` 无版本串 | 属实：八个模块全部只有 `ENGINE`；`deadlock_carver`→`"fd_adapter"`、`ic3_pdr`→`"lp_potential"` |
| `engine-rig-m9-deadlock-ic3-probe` 存在 | 属实 |
| 全仓无 `PROMPT_VERSION` | 属实：唯一命中是 `build_manifest.py:120` 里陈述它不存在那句话 |
| 全仓无戳探策略文档 | 属实：只有 `engine-rig/engines/probe_frontier/README.md` |
| `theoria-arm/inner/plan.py` 调 `solve_parsed` 不传 `prefer=` | 属实，**但行号已从文中的 `:112` 漂到 `:198`** |
| `proxy/ledger.py` 的 `ARMS` 无 `theoria_ablate` | 属实：仍是 `{bare_cc, schema_repro, theoria, probe, replay, mock_arm}` |
| `baseline-arms/out/campaign/` untracked | **不属实（已过期）**：4 个文件已跟踪于 `9307f139` |
| `battery/BATTERY_V1.md` 不在 master | 属实：`freeze/MANIFEST.json` 的 `absent_paths` 里就有它 |
| `CLAIMS_TEXT.md` C1 指向的「§限制」小节存在 | **不属实**：`:41` 指向一个不存在的小节（全文只有 C3 有一节限制），且全文不出现 `Theoria.md:262`/`:373` —— 这是 `NH-RC-h1-262-373-contradiction` 的实测依据 |
| `STATS_RULES.md` §6 的 U3 格值仍是 `{0, 0.5, 1}` | 属实（现行 `:837`），与 H-3 已裁定的整数规则直接打架 —— `NH-RC-h3-integer-cell-rule` |
| `launch_gate.py` 只读 `STATS_RULES.md` §9 | 属实（`:76` `RULES = …STATS_RULES.md`，`:116` 找 `## 9.`，`:133` 认 `开跑前置条件`） |
