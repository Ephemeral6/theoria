# DRIFT-dashboard-lags-the-merge-queue

severity: medium
dimension: 监控自身漂移（手写盘面落后于合并队列）／证据漂移（论文进度这个头条数字建立在陈旧的手写值上）

evidence: 审计区间 `4d3f993..5590f29`（21 个提交、429 文件）。

**基准事实：`monitor/spec.py` 最后一次被改是 `5fd1831`，此后到本轮基准共 45 个提交、14 个分支合并进 master：**
```
a4-ablation-online   c1-worldgen        c2-semantics-migrate  c4-deadlock-lean
e2-fd-ladder-bench   e4-property-fuzz   p4-figures            s2-canary-schedule
s3-spend-gate-v2     v2-exam-on-worldgen  v3-battery-discrimination …
```
`spec.py` 里的 `PAPER_PLAN`（十个 WP 的 `pct` 与 `evidence`）与 `GRID`（三十格的 `pct`/`note`/`active`）**全部是手写常量**，一格没动。

**逐格对树（只列已可证伪的）：**

| 盘面现值 | 树上 |
|---|---|
| `E1` note「性质测试战役**待跑**」，active `["E1-property-fuzz"]` | `e4-property-fuzz` 已合并；`fuzzlab/` 在树，含 `BUGS.md`、`RUN_STATE.md`、`archive/` |
| `S3` note「花费闸门**在建**」 | `s3-spend-gate-v2` 已合并；`proxy/spend_gate.py`、`proxy/SPEND_GATE.md`、`proxy/verify_spend.sh` **三件俱在** |
| `C1` active `["C1-worldgen"]` | `c1-worldgen` 已合并；`worldgen/` 在树，含 `build.py`、`catalog/`、`RUN_STATE.md` |
| `V5` pct 15「发表版图表」，active `["P-21"]` | `p4-figures` 已合并；`figures/` 在树，含 `PLAN.md`、`build_all.py`、`SOURCES.sha256` |
| `A1` note「……**消融臂离线**」 | `ablation-arm/` 已在树（`DESIGN.md`/`STATUS.md`/`_bootstrap.py`，`5959a80` 落盘） |
| `WP1` evidence「余：a0-spike 的 v0.2 迁移**在跑**（C2）」 | C2 已合并（`84e9a26`），a0-spike `43 passed, 0 failed` |
| `WP4` evidence「消融臂离线件**待接**」 | 同上，已落盘 |
| `WP5` evidence「battery v1 **在跑**（V3 区分力首跑）」 | `v3-battery-discrimination` 已合并（`174c5a6`） |

**为什么这条不只是「说明文字陈旧」：** `monitor/scan.py:588`
```python
total = sum(p["weight"] * p["pct"] for p in spec.PAPER_PLAN)
```
论文进度这个**全项目头条数字**，分母与分子都来自这十个手写 `pct`；`scan.py:915-917` 的分段进度同理。前端每 5 分钟刷新一次，刷的是同一批常量。也就是说：**页面在勤奋地重算一个没人更新的输入**——它看起来是活的，实际只有周边在动。这与我前三轮报的 `p1-cut` / `p1-engines` 是同一个病，区别是那两条只影响一格颜色，这条影响的是对外报出的那个百分数。

**必须说清楚的三件事，免得这条被读成指责：**
1. 方向是好的：45 个提交、14 个分支落地，是舰队在高速交付。手写层跟不上，是**产量问题**，不是失职。
2. 陈旧全部指向**低报**——盘面说「在跑/待接/在建」的东西其实已经交付。真实进度比页面上的数字高，不是虚高。
3. 顺带两条好消息：`AUDITOR.md:38` 用作第 6 维范例的「`proxy/spend_gate.py` 从未被写出来」**已经不成立**了（S3 交付了它，连 `verify_spend.sh` 一起）——范例该换；而新交付的活确实带上了自己的 verify 脚本，说明上一轮报的那个约定正在成形。上一轮点名的 `a0-spike/verify.sh` 仍缺。

claim: 监控的自动层（探针、reflex、合并）在跟着树走，手写层（PAPER_PLAN 的 pct/evidence、GRID 的 note/active）落后了 14 个分支。而项目对外的头条百分数完全由手写层决定，于是这个数字现在是**系统性低报且无人复核**的。

suggest:
1. **能推的就别手写**。`GRID` 的 `active` 是最容易机械化的一项：一格的 `active` 里若某个工单对应的分支已合并进 master，就自动移出并标 `delivered`。`reflex.py` 的 `ci_merge` 每次合并时已经知道分支名，顺手写回即可——不需要新基础设施。
2. `pct` 短期内仍得靠人判（它是判断不是事实），但可以让它**不可能悄悄变陈旧**：给每个 WP / GRID 格记一个 `pct_asof: <commit>`，`scan.py` 比对 `pct_asof` 与该格对应目录的最新提交，落后超过 N 个提交就在页面上标一个「陈旧」角标。数字仍是人给的，但陈旧本身变成机器可见。
3. 本轮这批先手工追平（上表八条），并把 `AUDITOR.md:38` 的第 6 维范例从 spend_gate 换成 `a0-spike/verify.sh`——那个还立着。
4. 与我上一轮建议的「承诺登记表」是同一件事的两面：**监控欠自己的活没有触发点**。目前欠账已到四件（p3 跨门例外、append_only 判据、释出许可接线、a0-spike/verify.sh），加上本轮这批盘面追平。建议这两条并成一个待办面板由探针数周期，而不是各自散在邮箱正文里。
