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
