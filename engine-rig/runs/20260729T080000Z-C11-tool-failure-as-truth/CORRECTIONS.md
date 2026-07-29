# C11 — 逐处订正表

工单 `C11-tool-failure-as-truth`，engine-rig 领地。判据：**工具的失败状态（超时 /
退出码 / 求解器 UNKNOWN / 搜索耗尽 / 预算触顶）被转成关于世界的布尔断言**，就是缺陷；
转成「未知 / 未证明 / 需要更多工作 / 控制流」，就不是。基准是 `Theoria.md` 约束 6。

线索来自 RES-3 三份只读普查（`.worktrees/e11-engine-crosscheck-deep/engine-rig/runs/
20260729T000000Z-E11-engine-crosscheck-deep/SURVEY-*.md`，**未提交**，对 base commit
`6ee0466` 写的）。**下表每一处都在本分支的当前代码上重新核过**，行号是我自己 grep 的，
不是抄来的——SURVEY 的行号大多仍准，但 `p13_fd_dividend.py` 的段落已因本次修改整体位移。

---

## 一、复核结论

SURVEY 在 engine-rig 领地内点名 **10 个站点 + 一族编码问题**。复核后：

> **[OVERTURNED] 表头「位置（当前树）」是标签错**：这一列给的是**修改前**的位置。
> 对抗复核在基线 `4d523e6` 上逐个验过，数据是对的，标签不对。
> 另：本表原写「10 个站点 + 一族」，**漏计了第 12 行**（`deadlock_carver`），
> 且第 11 行的编码一族**实修 5 处而自报 4 处**。两处均已在下方订正。

| # | 位置（**修改前**的树） | SURVEY 怎么说 | 我复核后 | 处置 |
|---|---|---|---|---|
| 1 | `tools/p13_fd_dividend.py:129`（原） | 裸 `returncode == 12` → `unsolvable` | **成立**，且最刺眼 | 已修：调用 `backends.proves_unsolvable` |
| 2 | 同文件 `same_answer` | 两次 FD 都崩 → `same_answer: True` | **成立** | 已修：三值，`None` 表示无人回答 |
| 3 | 同文件 `agree` | FD 崩 → 记成两后端不一致 | **成立** | 已修：三值 |
| 4 | 同文件 `render` | 表格印 `None -> None … yes` | **成立，但有一处要更正 SURVEY** | 已修：三值渲染 + 专门的「无结果」散文分支 |
| 5 | `engines/lp_potential/potential.py:170` | `if not result.success: return None` 合并了迭代上限与不可行 | **成立** | 已修：非 infeasible 一律 `raise LpUnavailable` |
| 6 | `engines/zero_space/zerospace.py:141-143` | >8 色截断 → law 被标 `scope: global` | **成立，且在放电**（10 色 ARC 调色板即触发） | 已修：`truncated_cells` / `scope_exhaustive`（**未进 payload**，见下） |
| 7 | `engines/mdl_segmenter/segmenter.py:177` | IMPOSSIBLE 哨兵 → `kind=None`，与「没变化」同形 | **成立但潜伏**（见下方论证） | 已修：选中即 `raise SegmentationError` |
| 8 | `engines/probe_frontier/reach.py:94-99` | `UNREACHABLE` 产物不带预算，读者无法自证 | **成立** | ~~部分修：`basis`/`budget` 上对象~~ **[OVERTURNED — 第一版是惰性的]** 现改为在下判断处 `raise UnprovenUnreachability`，并补负样本 |
| 9 | `bench/dividend.py:499/874` + `bench/report.py:352` | 超时被印成 `*refused*` | ~~成立但最轻~~ **[OVERTURNED] 成立，且在判定层** | **未改**，见「我没有改的」——**定性已改** |
| 10 | `recheck/verify.py:339,347,388` | 展示预算决定证书义务 | **成立，且比 SURVEY 说的更宽**（三条义务，不是两条） | 已修：判定读计数器，列表只管展示 |
| 11 | `text=True` 无 `encoding=`（~~4 处~~ **5 处**） | 诊断信息在最需要时被销毁 | **成立，方向保守** | 已修 **5** 处（`backends.py` / `fdrun.py` / `toolchain.py` / `bench/__main__.py` / `p13`）；领地内另有 **1 处未改**，见下 |
| **12** | `engines/deadlock_carver/__init__.py:66-71` | `PruningReport.as_json` 不写 `max_expansions` | **成立，而且比 SURVEY 说的重**：`same_answer` 与 p13 那处**同形** | **[新增 — 我第一版漏了]** 已修：不完整的比较 `raise UnfinishedComparison` |

**实际成立：11 处 + 一族（5 个调用点）。零处被我判为「SURVEY 判错了方向」。**
其中 **10 处已订正**，1 处（#9）未改并写下理由。

> **[OVERTURNED] 上一版这里写的是「10 处 + 一族（4 个调用点）……9 处已订正」。**
> 两个数都错：漏了 #12，编码一族把自己的成绩报少了一处。
> 对抗复核的原话值得留着——「它把自己的成绩报少了一处，说明这一族没有单独核过一遍」。

### 我要更正 SURVEY 的一处细节（#4）

SURVEY-environment 已经自己收回过「`:419-424` 会发表虚假负结果」，理由是 `%d % None`
会崩。**我复核确认那条收回是对的，但它推出的结论不完整**：`dividend.json` 在
`render()` 之前就已写盘（`main()` 里 `json.dump` 在 `render` 调用之前），所以
**双崩场景下 `same_answer: true` 确实进了 JSON 产物，只是 `DIVIDEND.md` 写不出来**。
换句话说：那个 `%d` 崩溃不是护栏，它只保护了给人看的那一半，机器可读的那一半照发。
修法因此没有依赖崩溃，而是给 `same_answer` 加了第三个取值。

### 我查过、判**不成立**的一处：`engines/cegis_miner/miner.py:321`

SURVEY-environment 的「穷举触顶专查」把它记成「有旗标，但对错了尺子」：

```python
size = min(max(len(guard), 1), max_frontier_size)
frontier = enumerate_frontier(positives, universe, masks, size)
truncated = len(guard) > max_frontier_size          # 1 > 3 -> False
```

读起来像是：一个 1-literal 的 guard 只枚举到深度 1，却仍发 `frontier_truncated: false`。

**我复核后判它不是本工单的缺陷。** `frontier` 的语义是「与本 guard **同长**的其他可分离
guard」，不是「所有深度 ≤3 的可分离 guard」；`enumerate_frontier` 在 guard 自身的长度上
枚举是设计，不是截断。`frontier_truncated` 表达的是「guard 比我们能穷举的还长，
所以退到深度 3 枚举」——它报的正是它说要报的东西。而 `frontier_max_size` **在 payload 里
逐行发布且准确**（已发布的 10 行 cegis 候选是 2 或 3），读者能自己看到深度。

E11 交叉复核测到的「深度 3 上 125 处遗漏」是**对 frontier 承诺什么的理解差异**，
不是旗标说了假话。SURVEY 自己也是按**文档缺陷**低调处理的，我同意那个定性。
**列在这里，是因为「我判它不成立」和「我漏了它」在报告里长得一样，必须分开。**

### #7 为什么是「成立但潜伏」（我自己的论证，不是抄的）

`_assign` 构造的是 `(n+m)×(n+m)` 方阵，每个 prev 都有一条有限代价的 vanish 通道、
每个 cur 都有一条有限代价的 appear 通道，padding 对 padding 免费。所以**总存在**
一个不含 IMPOSSIBLE 单元的完全匹配，`linear_sum_assignment` 只有在
`vanish + appear > 10^6` 时才会被迫选中它——现实代价远低于此。
**所以它不可达，而不只是罕见**。这正是它该做成断言（`raise`）而不是状态位的理由：
真触发说明代价模型坏了，分割结果不再是证据。负样本测试
`test_an_inexplicable_transition_is_raised_not_billed_as_nothing` 用一个把 vanish/appear
定价到 `IMPOSSIBLE * 10` 的代价模型把优化器逼进那个格子，**构造上必然**走到该分支。

---

## 二、修法的形状

三种写法，都是这个仓库自己已经有的（`SURVEY-environment` 的「做对了的」那一节）：

* **给「没答案」一个第三种取值。** `FdRun.answered`、`same_answer`/`backends_agree`
  返回 `Optional[bool]`、`Reachability.basis`。
* **失败即拒绝出口。** `LpUnavailable`、`SegmentationError`——照
  `fd_adapter/search.py:146`（预算耗尽 `raise`，绝不返回 `plan=None`）的先例。
* **把判定从展示里拆出来。** `recheck/verify.py` 的三条义务改读
  `n_escaping` / `n_goal_bad` / `n_raising`，列表只负责印。

**`p13_fd_dividend.py` 的核心一行**，改前改后：

```python
-            unsolvable=done.returncode == 12,
+            unsolvable=backends.proves_unsolvable(rung, done.returncode, log),
+            exhausted_reported=backends.FD_EXHAUSTED in log,
```

`backends` 在该文件第 53 行**早就 import 了**（`backends.parse_sas_plan` 在用），
`log` 在同一函数里早就有了。差的只是一次属性访问。
`rung` 是新增的、**保守方向**的参数：凡是这个函数无法担保为「完备且无代价上界」的
配置（有 alias，或 `search_config != BLIND`），一律按满意档处理，而
`proves_unsolvable` 在满意档上**整个拒绝** exit 12。

---

## 三、我没有改的，和为什么

### (a) `bench/dividend.py` 的 `guard_refused`（#9）—— **定性被推翻，已改**

> **[OVERTURNED] 上一版的原文，保留：**
>
> > 字段存的是 `guarded.error`，而 `fdrun.py` 会把墙钟超时写成
> > `error="timeout after %ds"`；`report.py:352` 把这样的行渲染成 `*refused*`，读起来像
> > 「guard 拒绝了这次编译」。**成立**，但：JSON 里原文完整保留；同一行的
> > `dividend_is_honest` 已经正确地是 `None` 而不是 `False`；`bench/report.py:52`
> > 已经把 `over budget` 与 `ERROR` 分列。
> > **所以这是渲染层的措辞问题，不是判定层的不健全。登记，不改。**
>
> **这条判错了，而且错在最关键的地方。** 我只跟了 `guard_refused` 的**渲染**用户，
> 没跟它的**判定**用户。对抗复核跟到了：

`guard_refused` 也被健全性判据读，**而那个判据决定 bench 的退出码**：

```python
# bench/dividend.py:855  def failures(report) -> List[str]:   """Soundness violations only."""
# bench/dividend.py:874
            if row["guard_refused"]:
                continue          # a refusal is a finding; see RUN_STATE.md
```

`continue` 跳过的正是 `failures()` 存在的两条义务——「最优档 plan 长度在 guard 下移动了
= unsound compilation」（`:882-888`）与「guarded plan 没在原始 domain 上重放」（`:889-893`）。
`failures()` 的返回值经 `bench/__main__.py:148` 汇进 `problems`，决定退出码；
**这不是推论，是 `tests/test_bench.py:622` 自己写的原话**
（「It reaches `failures()`, which is what sets the run's exit code」）。

完整链条：**FD 墙钟超时 / 崩溃 → `guard_refused` 为真 → 该行整个退出健全性判据 →
bench 仍可退出 0。** 一个工具的失败状态，决定了一条关于世界的肯定结论
（「这次编译没有健全性问题」）。这**就是**本工单的判据。
更刺眼的是：`fdrun.py` 把 `not_entitled` 专门做成与 `error` 分立的第四值，正是为了不让
「没资格下结论」和「跑挂了」同形，而 `:874` 把这层区分又合了回去。

我举的两条减轻理由（`dividend_is_honest` 已三值、`report.py:52` 已分列）**都为真，
但都不涉及 `failures()`**，所以都不支持我当时的结论。

**处置不变，登记词改了。** 仍然不改，理由仍然是：修它要动 `bench/report.py` 六处表格
格式并改变 E2 已发布报告的形状，而这条链路在本机无法实跑验证（无 FD 构建）。
**但正确的登记是：判定层的一处不健全，因牵动已发布报告格式而暂缓** ——
不是「渲染层的措辞问题」。已写进 inbox 提案，建议单开工单。

### (a2) 编码一族里领地内剩下的一处（#11）

`engine-rig/runs/20260728T141724Z-E5-cert-recheck/manifest.py:57-59`：
`text=True` 无 `encoding=`、无 `timeout`、无异常处理。`git` 不在 PATH 或
`index.lock` 被另一条赛道占着时，`head_commit` 会静默写成 `""`。

**不改，理由不是取舍是纪律**：它在 `runs/` 下，是一次**已完成运行的冻结记录**。
改它会让那份 provenance 记录与当时真正跑过的字节不符——按仓库
「provenance is canonical」的约定，这比留着缺陷更坏。登记在此，并已写进 inbox。

它此前没被扫到，是因为我的常设检查把 `runs` 放进了 skip 表，**排除了 7 个 `.py`
而没有报告**。那正是 `SURVEY-empty-as-negative` 贯穿性建议针对的形状，
**在我自己写的检查里**。已修：`runs` 移出 skip 表（扫描面 88 → 95 个文件，
新增的 7 个确实零 ERROR），且 `main()` 现在把扫描面与排除项一并打印。

### (a3) `probe_frontier` 的第一版修复是惰性的（#8）—— **被推翻，已重修**

> **[OVERTURNED] 第一版做的是**：给 `Reachability` 加 `basis`/`budget`，
> `basis` 写成 `"exhausted" if result.exhaustive else "proved-by-planner"`。
> 对抗复核指出三件事，三件都对：
>
> 1. **零负样本**——把这两行整块删掉，目标文件 68 条全绿、全套 452 条全绿；
> 2. **`else` 分支不可达**——`reach()` 调 `solve_parsed` 不传路径 → `on_disk=False`
>    → `choose_tier` 强制 STUB → 桩每条 return 都 `exhaustive=True`。
>    我的注释却写着「记录了是两者中的哪一个」，**记录的是一个不可能发生的二选一**；
> 3. 字段不进 payload，而 SURVEY 的原始抱怨**就是**产物不足。
>
> 它的结论是「这一处等于只改了注释」。**我接受，这条说得对。**

重修的形状变了：不再假装记录一个二选一，而是**在下判断的地方检查资格**。

```python
if not result.exhaustive:
    raise UnprovenUnreachability(...)
return Reachability(..., basis="exhausted", budget=result.max_expansions)
```

理由与 #12 相同：「`solve_parsed` 保证了」是**三个模块以外**的性质，
而这正是我在 p13 那一处拒绝接受的理由。资格现在在做出主张的那一行被检查。
负样本三条：真跑一次 `p_side` 断言 `basis == "exhausted"` 且 `budget > 0`；
monkeypatch 一个 `exhaustive=False` 的空结果断言抛错；`SearchResult` 真跑一次
断言它带回了 `max_expansions == 12345`（旧测试名字叫 budget、断言的却是
`exhaustive`，所以「不再记录 `max_expansions`」那个变异体逃了）。

### (b) 三处新字段没有进 candidate payload

`zero_space` 的 `scope_exhaustive`、`SearchResult` 的 `max_expansions`/`exhaustive`、
`Reachability` 的 `basis`/`budget` 都**在对象上**，但**都没有进 `as_json()`**。

理由是硬的，不是偷懒：这三个 payload 汇进 `engine-rig/artifacts/candidates.jsonl`，
而该文件的 sha256 被 `release/MANIFEST.jsonl:667`
（`679fe331cbc82191928a63b766c8f853c236756fce27ef71928d9af7078cfdad`）钉住，
且候选 `id` 是**对 payload 内容寻址的 uuid5**。我实测过：加上这些字段，
44 行候选里 **9 行 zero_space 的 id 全部改变**，
`tests/test_integration.py::test_the_checked_in_artifact_matches_a_fresh_deterministic_run`
立刻变红，必须重生成 `candidates.jsonl`——那既违反本工单「不要改任何已提交产物」的纪律，
也会让一个我不拥有的 release manifest 失效。

**这留下一个真实的缺口，我不假装它不存在**：`scope: "global"` 的读者仍然无法从产物
分辨「证明了不是 cell-local」与「没搜过」，`unreachable` 的读者仍然无法自证预算。
已写成 inbox 提案交给 release 轨道（见 `INBOX-*.md`）。
三处 `as_json` 上方都留了注释说明字段为什么被扣住，**不是遗漏**。

### (c) `cold-start-a0/certify/fd_unsat.py`：只登记不动手

SURVEY 的 U-3。**属于 theory-compiler 轨道**（`CLAUDE.md` 明写 `cold-start-a0/` 对
engine-rig 是禁区）。我的常设检查在全仓扫描时**独立命中了它**（`:46`），
这是它现在唯一的 ERROR 级真阳性之一。已写 inbox 提案，一个字节没动。

### (d) 别的领地

`worldgen/core/truth.py:279`、`a0-spike/`、`monitor/`、`release/`、`theoria-arm/`
均按工单边界不碰。常设检查扫到的另外两处 ERROR 级命中（`monitor/reflex.py:147`、
`release/checklist.py` 根本不解析）一并写进 inbox。
