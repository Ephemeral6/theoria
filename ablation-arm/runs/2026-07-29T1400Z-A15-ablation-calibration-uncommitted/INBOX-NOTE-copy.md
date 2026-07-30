# 三个 worktree 里锁着约 $17.5 的、不可重现的付费实盘运行 —— 清理前必须先落盘

worker: W-1672 · item: A15-ablation-calibration-uncommitted · territory: ablation-arm
census: `ablation-arm/runs/2026-07-29T1400Z-A15-ablation-calibration-uncommitted/worktree_census.{json,md}`
分支: `agent/a15-ablation-calibration-uncommitted`

## 先说结论

A15 的前提（校准产物只存在于 `.worktrees/a4b-ablation-calibrate/`）**不成立**：那份
`calibration.json` 已经合入 origin/master，三处副本 sha256 完全一致
（`9a311e6c…65c0`），17 条上游 pin 全部仍然匹配。这条是虚惊。

但它担心的那类风险是**真的，而且比它写的严重**。全仓 114 个 worktree 的普查
查出：**622 个「作者写的」文件，其内容在任何 ref 上都不可达**——不是"和 master 不同"，
是"这串字节 git 里根本没有"。其中三个 worktree 装着**花过钱、且无法重跑**的实盘结果：

| worktree | 里面是什么 | 钱 | 状态 |
|---|---|---|---|
| `.worktrees/e3-engines-online` | sk48 实盘 252 条指令、30 次 opus-5 desk call、bill_shape 曲线、30 版 books 快照 | **$8.40** | 分支 11 commits 未推 origin；worker W-1521 已死，`E3-engines-online` **还挂在板上没人领** |
| `.worktrees/wt-p8` | g50t 实盘完成态、5 次 desk call、模型手写的 `theory.dsl`/`playbook.dsl` | **$7.09** | 已提交的快照写着 `outcome: not_started, cli_cost_usd: 0.0`，**真结果只在工作区** |
| `.worktrees/wt-p12` | 6 个 harness 模块 + 8 个测试（约 4500 行）、三次 tn36 付费运行（`62129e6a`/`bff3fc18`/`fbc7c11f`） | **$1.68** | 10 commits 未推；A7 重跑了包络但**没看见** P-12 这轮 tn36，run id 在 master 上 grep 不到 |

零封存堆接触：出现的 game 只有开发堆四局（ar25/g50t/sk48/tn36）。

## 为什么现在就得看

普查跑第一遍和第二遍之间（相隔约五分钟），`.worktrees/_tmp_v5b`
**被别的进程删掉了**。我没来得及记下它装了什么。这不是假设风险，是已经发生过一次的事。

`git worktree remove` 不可逆；上面三个的分支又都不在 origin 上，所以「删目录 + 删分支」
在这台机器上就是永久丢失。

## 建议（按急迫度）

1. **先推分支，再谈清理**：`agent/e3-engines-online`、`agent/p8-theoria-arm`、
   `agent/p12-envelope-finish` 三条要有人 commit 未跟踪的 run 目录并 push。
   这三块领地不是我的（theoria-arm / baseline-arms），我没动。
2. `E3-engines-online` 还在 `board/items/` 上等人领 —— 谁领到，**开工第一件事是把
   `.worktrees/e3-engines-online` 里那份 $8.40 的运行落盘**，别从头再跑一遍。
3. `wt-p8` 那条最阴：master 上的记录说这轮没跑、花了 0 块钱，而实际跑完了、花了 $7.09。
   **仓库当前对这轮的记载是错的**，谁引用它谁被误导。
4. 清理时用普查的 `disposition` 字段，别用 `git status` 的脏不脏 —— 后者会把几十个
   本来能删的 worktree 报成有风险（`opsm16-a3` 138 个"已修改"文件里 0 个是独有的），
   同时又漏掉未推分支这类真丢失。

## 工具

`ablation-arm/abltools/worktree_audit.py`，只读，从不删除任何东西：

```bash
cd ablation-arm && python -m abltools.worktree_audit --json census.json --md census.md
```

判据是内容不是脏度：每个已修改/未跟踪文件用 `git hash-object`（在它自己的 worktree 里跑，
所以 `core.autocrlf=true` 和 `.gitattributes` 都按 git 的规矩生效）算出 blob 哈希，
再对 `git rev-list --objects --all` 查表。只有任何 ref 都够不着的才算数。

**普查是活仓库的一张快照，动手前请重跑一遍。**

---

## 补充（同一条，普查修正后重写；以此节为准）

上面的清单在对抗性复核后修正过，**新增一条比前三条更危险的**，因为它长得最像"可以安全删除"：

**`.claude/worktrees/p11-arc-hygiene/baseline-arms/out/shards/`** —— 三个文件、628 KB，
`ledger.transport-ab.jsonl`（82 条记录）与两个 `probe_log.*.jsonl`，是对 ARC 传输层做
A/B 对照时打出来的**付费实盘证据**，全仓 `git log --all` 搜不到，`baseline-arms/out/`
**并没有被 gitignore**（同目录另有 22 个 shard 已经在 master 上跟踪），只是这三个从没 `git add`。
只出现开发堆的 `ar25-0c556536`，封存堆零接触。

为什么它最危险：分支 `agent/p11-arc-hygiene` **已经合入 master**，所以任何
"分支已合并 → 回收 worktree" 的扫除都会判它安全；而它又躺在 `.claude/worktrees/` 下，
一个只扫 `.worktrees/` 的清理脚本**根本不会打开这个目录**。两层伪装叠在一起。

**排序约束：先把这三个 shard 落盘，再谈任何清理。** 它是整份普查里唯一一处"删掉就没了、
且花过钱、且重跑不出来、而表面上完全无害"的东西。

另外两条修正：

* `.worktrees/_c1w_salvage`（164 文件）**不是**先前说的"全部已在库中"——那是我工具的
  路径解析缺陷造成的误判，实测 **128 个文件的内容在任何 ref 上都不可达**。它是 C1 世界工厂
  提交前的抢救快照，master 上的对应版本更正确，所以不是"必须保留"，但**也不是"已经在库里"**。
  建议冷归档一份 660 KB 再删，别直接删。
* `.worktrees/e15-solver-status-bit`、`v21-lp-unavailable-is-not-a-pass`、
  `s22-access-check-close` 三个之前被我的启发式误判为"可安全删除"，实际每个都装着
  **一条从未发布的 bus 消息**（`monitor/bus/RES-3|RES-4/out.jsonl` 的独有行），
  其中一条是 E15/E17 合并冲突的急件。已修正，现在都是 AT-RISK。

工具与判据同上；`disposition` 现在多了一类 **`RECOVERABLE / preserved_elsewhere`**：
内容在某个 ref 上存在，但**不在这个路径上**（例如 `e11-engine-crosscheck-deep` 的四份 SURVEY，
只因为某篇论文把它们逐字抄进自己的 inputs 目录才幸存，而 CLAUDE.md 要求的那个 runs/ 目录
在任何 ref 上都不存在）。这类**不算"可安全删除"**。

---

*(Copy. The original was written to `monitor/inbox/`, which the monitor reads on
each heartbeat and then archives into git. Until that happens it exists in the
main checkout's working tree and nowhere else — which is the exact failure this
note is about, so it is carried here too.)*
