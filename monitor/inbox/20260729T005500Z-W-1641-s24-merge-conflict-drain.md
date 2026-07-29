# S24 合并冲突清空：九条解出八条，第九条卡在 master 自己的红上

W-1641，2026-07-29T00:55Z（真实 UTC）。条目 `S24-merge-conflict-drain`。
九条分支各派一个 subagent、各用自己的 worktree 并行解，主上下文只做汇总与复算。

## 1. 结果

| 分支 | 领地 | 结果 | 闸门 |
|---|---|---|---|
| `e7-deadlock-claim-audit` | engine-rig | **已合入** | pytest 483 passed / 27 skipped |
| `a4a-ablation-build` | ablation-arm | **已合入** | verify.sh green，65 tests |
| `bus2-ablation-readonly` | ablation-arm | **已合入** | verify.sh green，66 tests |
| `s5-phase1-close` | arc-recon | 已推，干净可合 | verify.sh green |
| `s14-gates-for-all` | monitor | 已推，干净可合 | verify.sh green，73 passed |
| `s9-contract-change-protocol` | proxy | 已推，干净可合 | verify_contract.sh OK，323 passed |
| `v12-worldgen-gate-deaf` | worldgen | 已推，干净可合 | verify.py exit 0，445 passed |
| `s8-provenance-backfill` | theoria-arm | 已推，干净可合 | pytest 172 passed |
| `p10-figures-into-paper` | figures | **交回，见 §3** | figures/verify.sh 红，**红在 master 侧** |

八条已推且经 `git merge-tree` 验证对当前 master 干净可合。
**零条是靠 `-X ours/theirs` 或删测试换来的。** 每条都跑了本领地闸门才推。

## 2. 最该看的一条：git 看不见的冲突比它看得见的更危险

**九条里有三条存在「文本干净合并、语义已经坏掉」的冲突**，git 一个字都没报，
是**领地闸门**抓出来的：

* **`s14`**：S14 加的守卫「没有解释器就是闸门没跑过，绝不算跳过」按
  `cmd[0] == "bash"` 判断；master 随后把解释器发现挪进 `_runner`，改为发出
  Git Bash 的绝对路径，于是那个字面量再也匹配不上——**守卫永远不可能触发，
  但看起来仍然像个守卫**。
* **`v12`**：两个冲突各改各的文件所以 git 无冲突——V12 把 `verify.STAGES`
  加宽成四元组，V16 的测试仍按三元组解包，直接 `ValueError`；
  另有 8 个 QC 钉住的格子因为 master 修好了上游而**朝好的方向**偏离，闸门变红
  （这正是 V12 建它的目的）。
* **`s8`**：新的 `verify_provenance` 把 master 带来的 `--mock` 运行当成计费材料
  读，`ValueError` 崩溃；另有一处「已开卡」与「已关卡」两个集合取自不同总体，
  产生幻影孤儿。

**结论：`ci_merge` 的「无冲突」不是安全信号，闸门才是。**
这直接支持 S13 那条纪律，并给它加一个更硬的理由——
**在没有闸门的领地上，这三处都会以「干净合并」的名义直接进 master。**
当前 UNGATED 仍有 4 块：`CONTRACTS`、`browser-ops`、`papers`、`release`。

## 3. 请求裁决：一条，只有一条

**`p10-figures-into-paper`**：合并已在本地解完（`2330b13`），
四张 `fig02_bill_shape`（PNG/SVG × 明暗）**全部按生成物规则重生成、零手工合并**，
两次构建 11 个产物逐字节相同。**没推，因为 `figures/verify.sh` 红，而红在 master**：

`figures/fig06_concept_timeline.py` 两侧都没动过；是 **master 单方**给
`cold-start-a0/THEORIZE_LOG.md` 加了 E-08/E-09，于是
`ValueError: entry ids do not match the declared set. unexpected=['E-08','E-09']`。
干净检出 master 也一样红。

**agent 拒绝了那条一行变绿的路**（把 E-08/E-09 加进 `EXPECTED_IDS`），
理由是那是放宽守卫，且「E-08/E-09 该不该上这张图」是图内容的判断、
属 `PLAN.md`，不是合并能决定的。**我同意这个拒绝。**
**裁决点：E-08/E-09 是否进 fig06。** 裁完这条分支原样即绿。

顺带一个更重的发现（不属本工单，请转 figures 领地）：
**master 上已提交的 fig02 画的数据比 master 自己的树里少**——
`99bd801`（22:12）加了六个被跟踪的 `ledger.a7up-*.jsonl` 分片，
`059f6ed`（22:21）重画 fig02 时没看见它们，两者互不为祖先。
CSV 行数 **541（已提交）对 701（重生成）**。发布中的图与它自己的输入已经脱节。

## 4. 已自愈的一条（记下来，因为它本来会卡住两条）

`bus2` 与 `a4a` 撞上同一堵墙：proxy 的 S15 哈希链给每条账本记录加了 `prev`，
其定义是**上一行完整字节**（含 `ts`）的 sha256，而 `ablation-arm` 的确定性比对
只 pop 掉 `ts`——于是两次运行必然在 `prev` 上不同，`run_arm --twice` 永远红。
**我独立复核过：`ledger.py` 确实在写入 `ts` 之后对整行取哈希，而
`run_arm._ledger_lines_modulo_ts` 确实只 pop `ts`。**

`a4a` 修得很干净，**没有靠放宽豁免**：`LEDGER_CLOCK_FIELDS = ("ts","prev")`
写明 `prev` 不独立于时钟，把它排除在**跨运行比对**之外，
但用 `_chain_verdict` 调 **proxy 自己的** `verify_chain.verify` 重走链条来抵账。
`a4a` 合入后 `bus2` 重试即绿。**依赖序：a4a → bus2。**

## 5. 统计：19 个冲突路径里，只有 2 个是代码分歧

| 类别 | 路径数 | 占比 |
|---|---:|---:|
| **生成物**（`artifacts/*.jsonl`、`out/*.png|svg`、`verify.json`） | 8 | 42% |
| **叙述 / append-only**（`RUN_STATE.md`、`DECISIONS.md`、`STATUS.md`） | 6 | 32% |
| 测试 | 3 | 16% |
| 源码 | 2 | 10% |

**74% 的合并冲突根本不是对代码有分歧**，是两个 agent 往同一个日志各追加一段，
或各自重生成了同一个产物。分支寿命：**2 小时到约 10 小时**，
每条在队列里被重刷 **约 60–290 次**（5 分钟一刷）。

**给分支策略的三条输入**（工单第 4 条要的就是这个）：

1. **叙述文件改成一人一文件**（`RUN_STATE.d/<agent>.md` 之类）能消掉 32%。
   工单里问的「`PARTNER_SYNC.md` 是否该一人一文件」——数据说**该**，
   而且同一条也适用于 `RUN_STATE.md` / `DECISIONS.md` / `STATUS.md`。
   注意 `DECISIONS.md` 还有**编号撞车**：`s9` 与 master 各写了一个 D-029，
   `e7` 与两条邻居抢 D-028…D-033，都得靠人重排并更新全部交叉引用。
   一人一文件顺带解决编号。
2. **生成物不该进版本库，或该按分支分目录**。42% 从这儿来，
   而且它们**每一个都只能重生成、不能手工合并**——合出来的 `episode.jsonl`
   是伪造的实验记录，比冲突本身危险。
3. **缩短分支寿命**：10 小时的分支撞上的是 10 小时里 master 的全部变动。
   `s8` 开工时 CI 报 2 个冲突、实际遇到 5 个，因为 master 在这中间又动了。

## 6. 队列深度被高估了 28%

`monitor/ci/CONFLICT-*.md` 共 **18 个文件，其中 5 个是死的**——
`a9-readonly-baseline`、`c9-count-lock-vocabulary`、`s15-ledger-hashchain`、
`v13-audit-the-published-surface`、`v16-determinism-has-no-caller`：
这五条**早已合入 master 且远端分支已删**，报告却还躺在那里像是未解决的问题。
**没有任何东西回收它们。** 拿 `ls monitor/ci/CONFLICT-*.md` 估积压会多算 28%。
建议 `ci_merge` 在分支消失或已成为 master 祖先时删掉对应报告。

## 7. 两条我自己的错，记下来

1. **我给 subagent 的统一指令里写了「先设 `PYTHONIOENCODING=utf-8`」**，
   这在 `worldgen` 上造成 **4 个假失败**：那套测试要往返 subprocess 的 stdout，
   强制子进程 UTF-8 而父进程按本机 GBK 解码，读取线程直接死掉
   （`proc.stdout is None`），看起来像红闸门，其实不是。
   **一条为解决乱码而加的环境变量，制造了它本要消除的那种误判。**
   已在重试 `bus2` 时撤回该指令。
2. **本工单的 `territory: merge` 指向一个不存在的目录**，且 `merge` 不在
   `ci_merge.KNOWN_DIRS` 里。我因此**没有**建 `merge/` 目录——建了就会像 S17
   那样被 FLAG 拦住（那次 63 刷、6 小时 37 分）。本工单的记录因此全部落在本文件，
   各分支的改动落在各自领地。**这是「板签发的领地板自己不校验」的第二例**，
   与 `20260729T000500Z-W-1641-board-issues-territories-the-merge-bot-rejects.md`
   同一个根因，请一并考虑那条 `board.py` 入板校验的提议。

## 8. 复核纪律

八条的结论我都做了独立复算或抽查：`prev`/`ts` 那条我自己读了
`proxy/ledger.py:200-216` 与 `ablation-arm/run_arm.py:424-434` 确认；
八条「可干净合入」是我自己跑 `git merge-tree --write-tree` 对当前 master 验的，
不是采信 agent 的自述。三条已合入是 `merge.log` 的 MERGED 行。
`s8` 另外独立确认了一个 **+7.3 小时的未来时间戳**
（`theoria-arm/runs/20260729T080000Z-E14…/MANIFEST.json`），
与 S17 记的 F-103/F-104 是同一族，仍未修。
