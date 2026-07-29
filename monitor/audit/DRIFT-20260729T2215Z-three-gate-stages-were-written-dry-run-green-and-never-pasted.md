# DRIFT-three-gate-stages-were-written-dry-run-green-and-never-pasted
severity: medium
dimension: 5（流程漂移：交接未完成）+ 6
cycle: 43 (OPS-A)

## claim

S4-freeze 的子代理写出了**三个完整的、干跑已绿的 `verify.sh` 闸门阶段**，
因为工作树争用而不能自己动 `verify.sh`，于是把它们作为「待粘贴」文本交给 RES-1。
**RES-1 粘了 12/13/14 三个阶段，这三个一个都没粘。** 而且——与同形的
`A16-launch-gate-wired` 不同——**这次遗漏没有登记进任何 residual**，
所以它不在任何人的待办上，也不会有任何东西提醒它。

这不是「没人想到要接线」。三份交接文件把该做什么、怎么做、有什么坑都写清楚了。
**漂的是交接的最后一跳。**

## evidence

**三份待粘贴的阶段**（主线，`freeze/runs/20260729T2040Z-S4-freeze-complete/`）：

1. `item05/verify_sh_stage15.snippet.sh:1-3` 逐字：
   > `# READY TO PASTE into freeze/verify.sh, immediately after stage [12] and before`
   > `# the "# ---- verdict" block.  RES-1 does the wiring; this subagent did not edit`
   > `# verify.sh, because another subagent is working the same worktree.`
2. `item12/NOTES_FOR_RES1.md:3`：
   > `**本子代理没有 git add / commit / push，也没有改 freeze/verify.sh。**`
   
   `:13-55` 是一段完整可粘的 `echo "[15] the budget table still describes the ledgers"`，带三路错误分诊。
3. `endpoints/verify_sh_stage16.snippet.sh:75` —— 第三个阶段 `[16]`，同样形态。

**都干跑绿过**：`item05/stage15-dryrun.txt:3`。

**主线上没有一个被粘进去**：`git show origin/master:freeze/verify.sh` 的阶段止于 `[14]`
（`echo "[14] every gap in the kit names who fixes it, where, and how it clears"`）。
全仓没有任何闸门／测试／CI 调这两个生成器：
`git grep -l "build_budget_table\|build_engine_manifest" origin/master` 的 18 条命中里，
`freeze/` 外只有 `PARTNER_SYNC.md` 一条，没有一条是闸门。

**没有登记**：`freeze/RESIDUALS.json` 的 67 个 code 里，没有一条点名
`verify.sh`、某个 stage、或这两个生成器。对照：完全同形的
`launch_gate.py` 未接线**是**登记着的（`A16-launch-gate-wired`，state open，owner RES-1）。
**同一种缺陷，一个进了台账，一个没进——所以只有一个会被追踪。**

## 后果是不对称的，只有一半要紧

* `freeze/ENGINE_MANIFEST.md` 与 `freeze/build_engine_manifest.py` **都在
  `freeze/MANIFEST.json` entry 5 里带 sha256**，所以 stage 12（硬失败）已经能抓手改。
  这一半只有「engine-rig 树在底下动了」没人盯。
* `freeze/BUDGET_TABLE.{md,json}` 与 `freeze/POOL_DIGEST.json`
  在 `MANIFEST.json` 的 61 条 pinned path 里出现 **0 次**，也不在任何 stage 里。
  **这三份一张网都没有。** 而 `BUDGET_TABLE.md:59` 正是那个 headline `$36.1423` 的出处。

## 一个可测量的、已经在漂的量（但我没证到它已错）

`freeze/POOL_DIGEST.json:78-80` 钉着 `pool_lines 11874` / `pool_sha256 8b02a324…`；
此刻磁盘上 `proxy/var/spend_gate.jsonl` 是 **11940 行**、sha256 `61ffe78e…`。
**这个漂移是设计好的**——`BUDGET_TABLE.md:497-517` 预先登记了「新克隆会 POOL ABSENT、
后续花钱会让 `--verify` 变红，那是故意的」。所以它不是缺陷。
**我要指出的是别的**：正因为这份 `--verify` 注定会红，它**永远不能像 stage 12 那样被接线**，
于是「谁来盯 `BUDGET_TABLE`」这个问题至今没有答案——不是忘了接，是接不上。
这一点三份交接文件都没讨论。

## suggest（监控裁决）

1. **最便宜的一件：把三段 snippet 粘进 `freeze/verify.sh`**，或者裁决不粘并写下理由。
   两条路都行，**现在这个「写好了、绿过、躺在 runs/ 里」的状态不行**。
2. **给这次遗漏一个 residual code**，与 `A16` 同格式。没有台账条目的缺口不会被任何人追踪，
   这正是 stage 14 存在的理由——而它自己漏在了 stage 14 的射程外。
3. **`BUDGET_TABLE.*` 与 `POOL_DIGEST.json` 先进 `MANIFEST.json` 的 pinned paths。**
   那是套件里唯一在跑的网，先把它们放进网里，再去解决那个「注定变红的 `--verify`
   怎么接」的难题。两件事可以分开做。
4. **值得裁一句通则**：子代理因工作树争用不能改共享文件时，产出应当**同时**
   生成一条台账条目，而不是只生成一份 NOTES_FOR_X。本轮的证据是：
   交接文本写得很好，但没有任何机制保证有人读它。

## 复核命令

```bash
git show origin/master:freeze/verify.sh | grep -oE '^echo "\[[0-9]+\]' | tail -3
git show origin/master:freeze/runs/20260729T2040Z-S4-freeze-complete/item05/verify_sh_stage15.snippet.sh | head -4
git grep -l "build_budget_table\|build_engine_manifest" origin/master | grep -v '^origin/master:freeze/'
git show origin/master:freeze/MANIFEST.json | grep -c BUDGET_TABLE   # -> 0
wc -l < proxy/var/spend_gate.jsonl                                   # -> 11940 vs pinned 11874
```

---

## 追加 2026-07-29T23:10Z（OPS-A cycle 44）—— 一处订正，与一条同源的新发现

本文件已在主线上（`e831cf0f` 一线），按纪律**追加订正，不就地改写**。

### 订正：本报告有一句话是假的

原文写道：`freeze/RESIDUALS.json` 的 67 个 code 里「**没有一条点名 verify.sh、某个 stage、或这两个生成器**」。

**这句话对 stage 15 与那两个生成器成立，对 stage 16 不成立。** `E-WORDING` 这一条的 `clears_when` 逐字点名了 stage 16 与它的 snippet 文件：

> `verify.sh 接入 stage 16（endpoints/verify_sh_stage16.snippet.sh，27 个探针、两个负对照已验）且全绿；弃权/未定义特异度的语义在 exam 侧钉住并有一条两靶子检查。`

我上一世扫 `RESIDUALS.json` 时漏了这一条。**原报告关于三条 snippet 从未被粘贴、以及 `BUDGET_TABLE`/`POOL_DIGEST` 不在 61 条 pin 路径里的结论不受影响**——那几条独立复核仍然成立，且 stage 16 到今天（`a197b39f`，2026-07-30 06:57）**仍未接线**，`freeze/verify.sh` 的最大阶段仍是 `[14]`。

### 同源的新发现（severity: low，dimension: 6）

既然 `E-WORDING` 点名了 stage 16，就该问它点得准不准。**不准。**

`E-WORDING` 的 `statement` 逐字复述「13 处分歧、5 处会改变公布出去的数」并点名 D1/D3/D4/D5，但它的 `clears_when` **可以在 D5 完全不动的情况下被满足**。

D5 是：C2「结局三 · B-2」用**同一个配对检验、同一个 α** 判成本轴（`CLAIMS_TEXT.md:187-191` 逐字：「**「更高」是一个检验，不是一个形容词。**……改为**用同一个配对检验、同一个 α 判成本轴**」），其结局**决定公布哪一段逐字文本**；而 `STATS_RULES.md` §3（`:367-421`）不登记成本轴、不登记 B-2，`:529` 写 `family = **三个主终点**`，`:974` 写「**不得**在结果出来后被提升为主终点」。

**两次变异实测（在 `%TEMP%` 的副本里做）：**

* **实测 A（盲区）**：删掉整个「结局三 · B-2」块（`CLAIMS_TEXT.md:172-198`，27 行，含那句「同一个 α」），stage 16 的输出与 dry-run **逐字节相同**。27 条探针（12 IDENT + 15 SCOPED）无一读它。`*/holm` 只断言字符串 `Holm` 在两份文件里都出现——**它不会数检验个数**。
* **实测 B（承重的那个）**：只修那 11 条 hard FAIL，插入的文本经程序核对**不含** `成本`/`B-2`/`结局三`/`U4` 任一字样。结果 `FAIL lines: 0`，两个负对照仍然点火——**而 B-2 与 §3 原样未动**。在 `verify.sh` 的口径下这一阶段零 `bad`，即转绿。

同一成因也解释 D10（U4）：`WORDING_AUDIT.md` §A.1「额外条款（只在一边）」行只列三条 C 独有条款——U4、B-2、消融臂合取项——**stage 16 只为其中一条写了定制探针**（`E3/ablstatus`）。探针矩阵是「3 终点 × 6 钉住项」，落在矩阵外的单边材料只有靠人手写定制检查才会被看见。

**明确不主张的**（这一段和上面同等重要）：**这不改变任何可执行状态。** `freeze/residuals.py` 里 `freeze_blocker` 只出现在 `SEVERITIES` 集合（`:83`）与统计计数（`:241`），**没有任何分支读它**；`clears_when` 只被检查非空（`:93-94`、`:174-182`），**从不被执行**；`launch_gate.py` 不读 `RESIDUALS.json`；67 条里 **60 条**同为 `freeze_blocker`+`open`；`verify.sh:871-876` 自己写着「**冻结是人的动作**」。这个执行缺口**已登记为 `LG-1`**（`state: open`，owner RES-1），所以它不是新漂移。

**suggest**：把 `E-WORDING.clears_when` 与它的 `statement` 对齐，补「且 `STATS_RULES.md` §3 登记或明确否决 B-2 的成本轴检验（D5），并说明 U4 在 C1 的地位（D10）」；或更便宜——给 stage 16 加第四条定制检查，与 `E3/ablstatus` 同形：C2 的「结局三」块若出现「同一个 α」/「同一检验」而 §3 全节不含成本轴检验 ⇒ 红。

顺带两处对 `WORDING_AUDIT.md` 自身的精度更正（**不立案**，供下一个读它的人）：其一，「13 处分歧」里 D11 自陈「这是**一致的沉默**，不是文件间分歧」，严格的文件间分歧数是 **12**；其二，「5 处会改变公布出去的数」是 🔴 **严重度层**的计数，不是那个谓词的计数——按审计自己给 D6/D8/D12 写的后果，谓词口径的下限是 **8**。两个数都不假，只是**一个数同时被两个口径引用**，下一个读者会用错那一个。
