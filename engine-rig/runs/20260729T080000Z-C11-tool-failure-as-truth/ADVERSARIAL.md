# C11 — 对抗复核

复核员：独立会话，任务是**推翻** C11 的结论。只读代码，未改 `engine-rig/` 下任何源码或测试
（变异测试逐个改回，全程 `git status --porcelain` 为空，见 §3 末）。唯一写入的文件是本文件。
未碰主工作树、其它 worktree、`cold-start-a0/`、`.env`；零网络；封存堆零接触。

**复核时状态在动。** 我开始时分支头是 `b0d3d3d`，运行期间实现员又推了两个提交
（`2535baa` 运行记录，`e392d46` 补记一处判不成立的站点），并新建了
`CALIBRATION.md` / `MUTATION.md` / `RECONCILIATION.md` / `INBOX-proposals.md` / `MANIFEST.json`。
本文件按 **`e392d46`** 的树写。

---

## 一、我推翻了什么

### 推翻 1（最重）：#9 被定性成「渲染层的措辞问题」，但它在**判定层**

`CORRECTIONS.md` §三(a) 写：

> 所以这是**渲染层的措辞问题**，不是判定层的不健全。改它要动 `bench/report.py` 六处表格格式……**登记，不改。**

**这条不成立。** `guard_refused` 不只被渲染读，它被**健全性判据**读：

```python
# bench/dividend.py:855  def failures(report) -> List[str]:   """Soundness violations only."""
# bench/dividend.py:873-875
        for row in entry["fd"]:
            if row["guard_refused"]:
                continue          # a refusal is a finding; see RUN_STATE.md
```

`continue` 跳过的正是这个函数存在的两条义务：

* `dividend.py:882-888`「最优档的 plan 长度在 guard 下移动了 → unsound compilation」
* `dividend.py:889-893`「guarded plan 没有在原始 domain 上重放 → 未复核」

而 `failures()` 的返回值经 `bench/__main__.py:148` 汇进 `problems`，**决定这趟 bench 的退出码**
——这不是我的推论，是仓库自己的测试写的：`tests/test_bench.py:622`
「It reaches `failures()`, **which is what sets the run's exit code**」。

`guard_refused = guarded.error`（`dividend.py:499`），而 `error` 由
`bench/fdrun.py:259`（`"timeout after %ds"`，墙钟超时）与 `fdrun.py:299` 起的兜底分支
（既没解出、也没证明不可解、也不属于 `not_entitled` 的运行 = 崩溃）写入。

于是完整的链条是：

> **FD 墙钟超时 / 崩溃 → `guard_refused` 为真 → 该行整个退出健全性判据 → bench 仍可退出 0。**

这就是本工单的判据本身：一个工具的失败状态，决定了一条关于世界的肯定结论
（「这次编译没有健全性问题」）。`not_entitled` 在 `fdrun.py` 里被**专门**做成与 `error` 分立的
第四值，正是为了不让「没资格下结论」和「跑挂了」同形；`dividend.py:874` 把这层区分又合了回去。

补充：`dividend_is_honest`（`dividend.py:505-508`）确实已经正确地是三值，
`report.py:52` 确实把 `over budget` 与 `ERROR` 分列——但这两点都不涉及 `failures()`。
实现员举的两条减轻理由都为真，**都不支持它的结论**。

**这不是「改不改」的取舍问题，是定性判错。** 若仍决定不改，登记词应当是
「判定层的一处不健全，因牵动已发布报告格式而暂缓」，不是「渲染层的措辞问题」。

### 推翻 2：「负样本是构造上必然会红的」——5 个变异体逃逸，其中 3 个说明整块修复无负样本

`MUTATION.md` 声称 18/18 击杀、0 逃逸。我构造了 36 个变异体（含 15 个「只回退一半」），
**31 杀 5 逃**。逃逸清单与实测见 §3。要点：

* **M26**：把 site #8（`probe_frontier/reach.py` 的 `basis`/`budget`）**整块删掉**——
  目标测试文件 68 条全绿，**全套 452 passed / 23 skipped 也全绿**。
  这一处修复没有任何负样本，一条也没有。
* **M25** 更糟，它是**等价变异体**：`basis="exhausted" if result.exhaustive else "proved-by-planner"`
  的 else 分支**不可达**。`reach()`（`reach.py:108`）调
  `fd_adapter.solve_parsed(domain, problem, prune=prune)`，不传 `domain_path`/`problem_path`
  → `on_disk=False` → `backends.choose_tier` 第 3 条规则强制 `STUB`（`backends.py:184-185`）。
  桩路径 `search.search()` 每条 return 都带 `exhaustive=True`，所以 `basis` **恒为 `"exhausted"`**，
  `"proved-by-planner"` 是死代码。而代码注释写的是
  「the FD path raises unless `backends.proves_unsolvable` says so. **Which of the two it was is recorded**」
  ——记录的是一个不可能发生的二选一。
* **M35**：`check_paths` 改成直接 `return []`，全绿。
  这正是工单点名的 **tautological assertion**：
  `test_the_standing_check_is_green_on_this_territory` 断言 `not findings`，
  而 `findings` 恒空时该断言同样成立。整个文件遍历层
  （`python_files`、`skip` 表、`SyntaxError` → `<unparsed>` 分支）**没有任何测试**。
  `test_the_standing_check_catches_the_defect_it_was_written_for` 用的是 `check_source`，
  绕开了这一层。
* **M28**（`max_expansions` 不再记录）、**M36**（`Finding.level` 默认值改 `NOTE`）同样全绿；
  后者说明 `level: str = ERROR` 这个默认值是死代码（两个构造点都显式传 level）。

实现员的 18 个变异体**恰好一一对应它写下的那几条测试**。没有一个落在
`reach.py`、`SearchResult.max_expansions`、`check_paths` 上——而这三处正是没有测试的三处。
这不是「构造上必然会红」，这是「测了测过的」。

### 推翻 3：SURVEY 点名的一处，实现员既没修、也没登记、也没判不成立

`SURVEY-environment-as-semantics.md`「穷举触顶专查」原话：

> `SearchResult.as_json()`（`:108-116`）与 **`deadlock_carver.PruningReport.as_json()`（`:74-83`）
> 都不写 `max_expansions`**。产物只有 `expansions`，读者无法自证 N < 上限。

实现员给 `SearchResult` 加了 `max_expansions`/`exhaustive`（还扣在 payload 外），
对 `PruningReport` **一个字没提**——不在「已修」的 10 行里，不在「登记不改」的 §三，
也不在 `e392d46` 新增的「我判它不成立」一节。CORRECTIONS.md 自称
「SURVEY 在 engine-rig 领地内点名 **10 个站点 + 一族**」，实际是 11 个（这一处漏计）。

而且它不只是产物不足。`engines/deadlock_carver/__init__.py:66-71`：

```python
    @property
    def same_answer(self) -> bool:
        """Pruning must change the node count and nothing else."""
        return (self.baseline.solved == self.pruned.solved
                and self.baseline.length == self.pruned.length)
```

**这与 p13 那个被判为缺陷的 `same_answer` 是同一个形状**：两侧都无 plan 时
`solved == solved`、`length(None) == length(None)`，合取为 True。它以
`plan_length_unchanged` 发布（`__init__.py:85`），并被 `bench/dividend.py:868` 读作
「pruning changed the bundled rung's answer -- unsound theorem」的判据。
今天机制上安全（桩触顶 `raise`），**但「靠上游机制安全」正是实现员在 p13 那一处拒绝接受的理由**
（`SURVEY` 的 U-1「减轻情节」段落说的也是同一件事，实现员照样修了）。同一条尺子，两个结论。

### 推翻 4：编码一族是 5 处不是 4 处，且领地内还剩 1 处未改、并被检查永久排除

`CORRECTIONS.md` #11 写「4 处全部 pin」。实测 `git show 2a1c30d` 改的是 **5 个**调用点：
`engines/fd_adapter/backends.py:328-330`、`bench/fdrun.py:251-253`、`bench/toolchain.py:125-127`、
`bench/__main__.py:68-70`、`tools/p13_fd_dividend.py:152-154`。（SURVEY 只点了前四个中的
`backends`/`fdrun`/`toolchain`/`p13`；`bench/__main__.py` 是实现员自己找到的，这是加分项，
但它把自己的成绩报少了一处，说明这一族没有单独核过一遍。）

**领地内还剩一处**：`engine-rig/runs/20260728T141724Z-E5-cert-recheck/manifest.py:57-59`

```python
    manifest["head_commit"] = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ENGINE_RIG,
        capture_output=True, text=True).stdout.strip()
```

`text=True` 无 `encoding=`，且**没有 timeout、没有异常处理**——`git` 不在 PATH 或
`index.lock` 被另一条赛道占着时，`head_commit` 会写成 `""`（这正是
SURVEY-environment 乙组对 `cold-start-a2/a2pipeline/concepts.py:79-83` 的原话）。
它没被扫到，是因为 `check_solver_status.python_files` 的 `skip` 表里有 `"runs"`
（`check_solver_status.py:302-303`），把 `engine-rig/runs/` 下 7 个 `.py` 永久排除在扫描面外。
我把这 7 个文件逐个显式喂进 `check_paths`，求解器状态一项确实都是 `[]`
——**排除今天没有掩盖 ERROR，但扫描面是硬编码清单而没有被报告**，
这是 `SURVEY-empty-as-negative.md` 的贯穿性建议所针对的形状本身。

### 推翻 5：常设检查的 ERROR 分级由**变量名**决定，与代码是否正确无关

实测（`check_source` 直接喂）：仓库自己认可、SURVEY 明确表扬过的五合取 Lean 判据，
一个字不改，只换绑定名：

| 片段 | 判定 |
|---|---|
| `"green": (proc.returncode == 0 and not errors and not sorries and bool(axiom_reports) and all_axiom_free)` | `note:green` |
| `"verified": (proc.returncode == 0 and not errors and not sorries and bool(axiom_reports) and all_axiom_free)` | **`error:verified`** |

`CALIBRATION.md` 把这个划分说成「关于世界 vs 关于进程」的语义区分。它不是；它是命名约定，
而且文档自己承认（「但它是一个命名约定」）。问题在于**结论**：CALIBRATION 据此把 NOTE 级
21/22 判为假阳、把 ERROR 级精确率报成 75%，两个数字都建立在「名字选对了」这个前提上。

### 推翻 6：CALIBRATION 的 ERROR 精确率 75% 高报，按它自己的分级判据只有 50%

ERROR 四处，我独立复跑确认（`python -m tools.check_solver_status .. --notes`，4 ERROR / 22 NOTE，
与 CALIBRATION 一致）。逐条：

| 位置 | 实现员判 | 我判 |
|---|---|---|
| `cold-start-a0/certify/fd_unsat.py:46` | 真阳 | **同意**，真阳 |
| `release/checklist.py:0`（不解析） | 真阳 | **同意**是真发现（我独立确认：`newline="\n"` 的 `\n` 是**真换行**，`ast.parse` 与 `python release/checklist.py` 都 SyntaxError，且已提交），但它不是「求解器状态当世界性质」，是 ERROR 级里混进了一个别的品类 |
| `worldgen/qc/run_qc.py:118` | 假阳 | **同意**，假阳 |
| `monitor/reflex.py:147` `hold = q.returncode == 2` | **真阳** | **不同意 → 假阳（分级错）**。检查自己的文档说 ERROR = 「关于**世界**的断言」；这里 `hold` = 「暂停舰队」，是关于**进程**的，属 NOTE 那一栏。实现员自己写了「命中理由是词形巧合」却仍记真阳。底层代码确有缺陷（quota.py 崩溃 exit 1 → `hold` False → 继续花钱），但那使它成为**假阴被同音字碰对了**，不是这条判据的召回 |

按分级判据坐实的 ERROR：2/4 = **50%**。

### 推翻 7：`_adjudicated` 的豁免可被任何一次函数调用洗掉

`_status_comparisons` 第一句就是 `if _adjudicated(node): return False`，而 `_adjudicated`
只问「这个表达式里有没有一个 Call 读到了工具状态」。实测：

```
unsolvable = bool(done.returncode == 12)          →  -- no finding --
unsolvable = any([done.returncode == 12])         →  -- no finding --
def _decide(rc): return rc == 12
unsolvable = _decide(done.returncode)             →  -- no finding --
```

最后一条是关键：**检查验证的是「委派的形状」，不是委派对象真的裁决了**。
「Route the comparison through a predicate that adjudicates it」这条修法建议，
用一个只做裸比较的 `_decide` 就能满足。而 `_decide` 自己不被检查，因为它的名字不在断言词表里。

---

## 二、11 处逐条的独立判定

判据同工单：工具失败 → 关于世界的**肯定**断言 = 缺陷；→ 未知/未证明/控制流 = 不是。
行号是我自己 grep 的当前树（`e392d46`）。

| # | 站点 | 我的判定 | 备注 |
|---|---|---|---|
| 1 | `tools/p13_fd_dividend.py`（原 `:129`，今 `:170`）裸 `returncode == 12` | **成立，已正确修** | 现为 `unsolvable=backends.proves_unsolvable(rung, done.returncode, log)`；`rung` 默认走保守档（`:139-141`）。变异 M01/M02（只回退一半谓词）、M09（rung 恒最优）全部被杀 |
| 2 | 同文件 `same_answer`（今 `:176-189`） | **成立，已正确修** | 抽成纯函数是对的判断：原判据长在需要真 FD 才跑得起来的 `deadlock_dividend()` 里。M06（只守 before 一侧）、M07（去掉守卫）被杀 |
| 3 | 同文件 `backends_agree`（今 `:192-203`） | **成立，已正确修** | M08 被杀 |
| 4 | 同文件 `render`（今 `:465-545`） | **成立，已正确修**；SURVEY 的收回是对的，实现员对收回的补充也是对的 | 我核了 `main()`：`json.dump` 在 `:563`，`render()` 在 `:565`——**JSON 先落盘**。所以旧代码 `"%d" % None` 的崩溃确实只保护了 `DIVIDEND.md`，`same_answer: true` 照进 `dividend.json`。实现员这一条站得住 |
| 5 | `engines/lp_potential/potential.py`（原 `:170`，今 `:202/:205`） | **成立，已正确修** | M18（放 status 1 过去）、M19（整条不 raise）、M20（常量偏一）全杀。附带核实：`LpUnavailable` 在 `__init__.py` 导出，`run()` 的 docstring 也改了 |
| 6 | `engines/zero_space/zerospace.py`（原 `:141-143`，今 `:175/:177`）| **成立，修了一半** | 标志上了对象（M21/M22 被杀），但 `Law.as_json` 与 `ZeroSpaceResult` 都不发。产物读者仍无法分辨「证明了不是 cell-local」与「没搜过」。**扣住 payload 的理由我核过是真的**：`common/candidates.py:61` 的 id 是 `uuid5(content)`，`artifacts/candidates.jsonl` 44 行里 9 行是 zero_space，加字段必然重算这 9 个 id。理由成立，缺口也成立 |
| 7 | `engines/mdl_segmenter/segmenter.py`（原 `:177`，今 `:186` 返回哨兵 / `:214` 断言）| **成立，已正确修**；「不可达而非罕见」的论证我复核后同意 | M23（`>=` 弱化成 `>`）、M24（整条不 raise）被杀。M23 是「只回退一半」型，仍被杀，这一条的负样本是硬的 |
| 8 | `engines/probe_frontier/reach.py`（原 `:94-99`，今 `:113-119`）| **成立；「修」是惰性的** | 见推翻 2。`basis`/`budget` 不进 payload（SURVEY 的原始抱怨就是产物不足，所以这条修复没有触及被点名的问题），没有任何测试（M26 全绿），且 `basis` 的三元 else 分支不可达（M25 是等价变异体）。三样加起来：这一处**只有注释变了** |
| 9 | `bench/dividend.py:499` + `report.py:230/352/590` + **`dividend.py:874`** | **成立，且比实现员判的严重一级；未改** | 见推翻 1。定性从「渲染层」改到「判定层」 |
| 10 | `recheck/verify.py`（原 `:339/:347/:388`，今义务在 `:364/:365`、`:416/:417`、`:433/:434`）| **成立，已正确修，且这是全篇最好的一处** | 六个「只回退一处义务」的变异体（M10–M15）全杀，两个「把计数器重新耦合回展示预算」的变异体（M16/M17）也全杀。参数化的伪造品目录性质测试（42 条）是真正把覆盖面撑起来的东西 |
| 11 | `text=True` 无 `encoding=` | **成立，实修 5 处（自称 4 处），领地内还剩 1 处** | 见推翻 4 |
| （12）| `engines/deadlock_carver/__init__.py:66-71` + `:96-98` | **SURVEY 点名，实现员漏了** | 见推翻 3 |

**没有一处我判为「SURVEY 判错了 / 实现员判错了方向」。** 11 处的方向判定我全部同意。
分歧集中在：#9 的**严重程度**、#8 的**修没修到**、以及漏掉的 (12)。

关于行号，工单要我不要相信给定值、自己 grep：**我 grep 了，结果对实现员有利。**
`CORRECTIONS.md` 表格里 #5/#6/#7/#8/#10 给的是**修改前**的位置，我在分支基线 `4d523e6` 上逐个验：
`zerospace.py:141` = `if len(indices) > 8:` ✓、`potential.py:170` = `if not result.success:` ✓、
`segmenter.py:177` = `return IMPOSSIBLE, None, {}` ✓、`reach.py:95` = `if plan is None:` ✓、
`verify.py:339/347/388` = 三个 `max_witnesses` 截断点 ✓（而且这三个数与 SURVEY 写的
`289/297/303/304` **不同**——SURVEY 是对 `6ee0466` 写的，`verify.py` 在两个 commit 之间移动过，
所以这证明实现员确实自己 grep 了，不是抄的）。
**唯一不准的是表头**：那一列写着「位置（当前树）」，实际给的是修改前的位置。这是标签错，不是数据错。

---

## 三、逃掉的变异体

方法：每个变异体改一行源码 → `python -m pytest tests/test_tool_failure_is_not_truth.py -q`
→ 无论结果**立即改回原文**（保存原字节、`finally` 写回）→ 逃逸者再跑一次全套 452 条。
36 个变异体，**31 杀 5 逃**。基线：目标文件 68 条全过；全套 `452 passed, 23 skipped`。

### 逃 1 — M26：把 #8 的修复整块删掉

```diff
--- a/engine-rig/engines/probe_frontier/reach.py
+++ b/engine-rig/engines/probe_frontier/reach.py
@@ -113,8 +113,6 @@
         return Reachability(
             status=UNREACHABLE, problem=name, goal_atoms=tuple(goal_atoms),
             expansions=result.expansions,
-            basis="exhausted" if result.exhaustive else "proved-by-planner",
-            budget=result.max_expansions,
         )
```

```
tests/test_tool_failure_is_not_truth.py:  .................ssss...s.........s..s..s...........ssss............  [100%]
全套:                                     452 passed, 23 skipped
```

**#8 这一处修复没有任何负样本。** 全仓 `grep -rn "\.basis\|\.budget" tests/` 无命中。

### 逃 2 — M25：等价变异体，证明 `"proved-by-planner"` 是死代码

```diff
-            basis="exhausted" if result.exhaustive else "proved-by-planner",
+            basis="exhausted",
```

```
tests/test_tool_failure_is_not_truth.py:  68 passed
全套:                                     452 passed, 23 skipped
```

不是测试漏了，是**分支不可达**：`reach.py:108` 的 `solve_parsed(domain, problem, prune=prune)`
不带路径 → `on_disk=False` → `choose_tier` 的第 3 条（`backends.py:184-185`）强制 `STUB`
→ 桩的每条 return 都 `exhaustive=True`。`reach()` 是 `reach.py:200` 的唯一调用点，
也不传路径。所以 `basis` 恒 `"exhausted"`、`budget` 恒 `500000`。

### 逃 3 — M28：`max_expansions` 不再被记录

```diff
     return SearchResult(None, expansions, generated, pruned, len(grounded),
-                        max_expansions, True)
+                        None, True)
```

```
tests/test_tool_failure_is_not_truth.py:  68 passed
全套:                                     452 passed, 23 skipped
```

唯一碰 `SearchResult` 新字段的测试是
`test_a_search_result_carries_the_budget_it_ran_under`，它只断言**占位对象**的
`exhaustive is False`（名字说的是 budget，断言的是 exhaustive），从不断言真实搜索
带回了预算。M27（`exhaustive` 默认改 True）被杀，M28 不被杀——**这条测试测的是它名字的另一半**。

### 逃 4 — M35：整个扫描层可以被掏空（工单点名的 tautological assertion）

```diff
 def check_paths(roots: Sequence[str]) -> List[Finding]:
+    return []
     findings: List[Finding] = []
```

```
tests/test_tool_failure_is_not_truth.py:  68 passed
全套:                                     452 passed, 23 skipped
```

`test_the_standing_check_is_green_on_this_territory` 断言
`not [f for f in check.check_paths([check.HERE]) if f.level == check.ERROR]`。
`check_paths` 恒返回空时该断言同样成立。于是 `python_files` 的遍历、
`skip` 表（含把 `runs/` 排除的那一条）、以及 `SyntaxError → <unparsed>` 那条
「读不了的文件不算干净」的关键分支，**全部没有测试**。
`test_the_standing_check_catches_the_defect_it_was_written_for` 用的是 `check_source`，
绕过了这一层。

### 逃 5 — M36：`Finding.level` 的默认值是死代码

```diff
-    level: str = ERROR
+    level: str = NOTE
```

```
tests/test_tool_failure_is_not_truth.py:  68 passed
全套:                                     452 passed, 23 skipped
```

两个构造点（`_Visitor._record`、`check_paths` 的 `<unparsed>`）都显式传 `level`，
所以这个默认值永不生效。无害，但它让读者以为「默认判 ERROR」是一条保守约定。

### 被杀的 31 个（含 15 个「只回退一半」）

| 变异 | 结果 | 杀它的测试 |
|---|---|---|
| M01 `proves_unsolvable` 去掉 `tier == FD_OPTIMAL` 一半 | RED | `test_the_satisficing_rung_may_not_prove_unsolvability` |
| M02 去掉 `FD_EXHAUSTED in log` 一半 | RED | `test_exit_12_without_the_exhaustion_line_is_not_a_proof` |
| M03 `answered = self.plan is not None`（丢 `or self.unsolvable`）| RED | `test_a_planner_that_did_not_answer_is_not_a_planner_that_disagreed` |
| M04 `answered = self.unsolvable`（丢 plan 一半）| RED | 同上 |
| M05 `answered = True` | RED | 同上 |
| M06 `same_answer` 只守 `before` 一侧 | RED | `test_a_double_failure_is_not_a_passing_control` |
| M07 `same_answer` 去掉守卫 | RED | 同上 |
| M08 `backends_agree` 去掉守卫 | RED | `test_a_planner_that_did_not_answer_...` |
| M09 `rung` 恒 `FD_OPTIMAL` | RED | `test_the_satisficing_rung_...` |
| M10–M15 六条证书义务**逐条**回退成读截断列表 | 全 RED | `test_a_zero_witness_budget_cannot_close_an_open_invariant` / `test_no_forgery_survives_by_starving_the_witness_budget` / `test_a_zero_budget_cannot_certify_a_broken_region_either` |
| M16 `n_escaping` 重新耦合进展示预算 | RED | `test_no_forgery_survives_...` |
| M17 `n_raising` 重新耦合进展示预算 | RED | 同上 |
| M18 只放 HiGHS status 1 回 `None` | RED | `test_an_iteration_limit_is_not_an_infeasibility[1]` |
| M19 整条不 raise | RED | 同上 |
| M20 `HIGHS_INFEASIBLE = 1` | RED | `test_a_proved_infeasibility_still_returns_none` |
| M21 `scope_exhaustive` 硬编码 True | RED | `test_a_truncated_subset_scan_...` |
| M22 截断不记录 | RED | 同上 |
| M23 `>= IMPOSSIBLE` 弱化成 `> IMPOSSIBLE` | RED | `test_an_inexplicable_transition_is_raised_...` |
| M24 整条不 raise | RED | 同上 |
| M27 `exhaustive: bool = True` | RED | `test_a_search_result_carries_the_budget_it_ran_under` |
| M29 `exhausted_reported=False` | RED | `test_the_satisficing_rung_...` |
| M30/M31 render 把 `None` 印成 `yes` | RED | `test_a_double_failure_is_not_a_passing_control` |
| M32 `_adjudicated` 恒 True | RED | `test_the_standing_check_catches_the_defect_it_was_written_for` |
| M33 `_status_comparisons` 恒 False | RED | 同上 |
| M34 词表去掉 `"unsolvable"` | RED | 同上 |

M10–M15 这一组我特别看过：**六条义务里回退任意一条都会红**，不存在「改一条不红、改全了才红」的
掩蔽效应。这一处的负样本是我在整份工作里见到最硬的。

### 树的清洁

```
$ git status --porcelain          # 每个变异体之后 + 全部跑完之后
（空）
$ git diff --stat HEAD
（空）
```

---

## 四、常设检查的假阳假阴（实测）

全部用 `from tools.check_solver_status import check_source` 直接喂片段。

### 假阴（12 个构造，12 个全逃）

| 写法 | 片段 | `check_source` 输出 |
|---|---|---|
| 中间变量（名字不在词表里）| `outcome = done.returncode` / `unsolvable = outcome == 12` | `-- no finding --` |
| `if/else` 代替比较表达式 | `if done.returncode == 12: unsolvable = True` / `else: unsolvable = False` | `-- no finding --` |
| `dict.get` 默认值 | `row["unsolvable"] = VERDICTS.get(done.returncode, True)` | `-- no finding --` |
| 断言名函数返回裸 `True`/`False` | `def proves_unsolvable(run): if run.returncode == 12: return True` / `return False` | `-- no finding --` |
| `match` 语句 | `match done.returncode:` / `case 12: unsolvable = True` | `-- no finding --` |
| **裹一层 `bool()`** | `unsolvable = bool(done.returncode == 12)` | `-- no finding --` |
| 裹一层 `any()` | `unsolvable = any([done.returncode == 12])` | `-- no finding --` |
| **委派给一个只做裸比较的 helper** | `def _decide(rc): return rc == 12` / `unsolvable = _decide(done.returncode)` | `-- no finding --` |
| 弱状态词 + 命名常量 | `unsolvable = planner.status == FD_UNSOLVABLE` | `-- no finding --` |
| 循环里累加 | `unsolvable = False` / `for run in runs: if run.returncode == 12: unsolvable = True` | `-- no finding --` |
| 元组解包 | `unsolvable, reason = done.returncode == 12, "exit 12"` | `-- no finding --` |
| `except` 里把超时折进断言 | `except TimeoutError: unsolvable = True` | `-- no finding --` |

对照（确实抓到的）：`unsolvable = done.returncode == 12` → `error:unsolvable`；
三元 `unsolvable = True if done.returncode == 12 else False` → `error:unsolvable`。

CALIBRATION 已诚实承认召回低（「以 10 处站点为分母只覆盖 1 处」）。上表补的是**另一件事**：
不是「别的形态抓不到」，而是**同一个形态换五种写法就全抓不到**，其中两种（裹 `bool()`、
委派给假谓词）**恰好是修复建议本身的形状**。`_adjudicated` 把「有没有交给谓词」实现成
「表达式里有没有一个 Call 读到了工具状态」，那是一个可以被 `bool()` 满足的条件。

### 假阳（7 个构造，5 个是真实会出现的写法）

| 片段 | 输出 | 为什么是假阳 |
|---|---|---|
| `report = {"verified": (proc.returncode == 0 and not errors and not sorries and bool(axiom_reports) and all_axiom_free)}` | **`error:verified`** | 与 `cold-start-a0/certify/lean_check.py:97` 逐字同构，SURVEY 明确表扬过的五合取判据。改名成 `"green"` 后同一份代码只得 `note:green` |
| `reachable = frame["status"] == 2` | **`error:reachable`** | 引擎读**游戏自己**的 status 字段。词表注释声称「A comparison against a named constant is the engine talking about itself and is left alone」——但仓库里的 API 状态就是整数字面量（`proxy/scoring/arc_v1.py:282` `ok = status == 200`、`theoria-arm/harness/arc.py:157` 同形），保护不了这一类 |
| `deadlock = cell["status"] == 3` | **`error:deadlock`** | 同上，纯世界事实 |
| `valid = response["status"] == 200` | **`error:valid`** | 同上 |
| `def test_a_bare_exit_code_is_not_a_proof(): unsolvable = run.returncode == 12; assert unsolvable is False` | **`error:unsolvable`** | **负样本测试写出它要禁止的那一行就会把常设检查判红**，而常设检查又是套件里的一条测试 → 套件自我阻塞。实现员在 `test_the_standing_check_catches_the_defect_it_was_written_for` 里把那一行当**字符串**传，是已经撞上这堵墙的证据。`python_files` 不排除 `tests/` |
| `hold = quota.returncode == 2` | `error:hold` | 见推翻 6：底层确有缺陷，但分级错 |
| `result["schema_valid"] = validate.returncode == 0` | `error:schema_valid` | 实现员自己认的那一处假阳 |

### 我的判断：这条检查该不该进 CI

**进 engine-rig 的 pytest gate：我同意，但当前形态下这条测试几乎没有力量。**

同意的理由和实现员一样（`monitor/gates.py` 把 engine-rig 解析成 pytest，不是测试的检查等于不跑）。
但 M35 证明：`test_the_standing_check_is_green_on_this_territory` 在
`check_paths` 恒空时同样绿。**它今天保证的是「这条检查没有报错」，不是「这个领地被扫过」。**
要让它值钱，必须补一条正向的扫描层测试——例如把一个含
`unsolvable = p.returncode == 12` 的临时文件写进 `tmp_path`，断言 `check_paths([tmp_path])`
恰好命中 1 处 ERROR；再断言一个语法坏掉的文件产出 `<unparsed>` 而不是被跳成干净。
这两条一加，M35/M36 就都会红，扫描层才有负样本。

**不进全仓 CI：我同意实现员的判断，理由与它写的一样**（三处已知红有两处不在任何人工单里），
**但我要加一条它没说的：分级不稳。** 见推翻 5——同一份代码换个名字就跨级。
把它当门禁意味着「重命名一个变量」会改变门禁结果，这是一条可以被无意中绕过、
也可以被无意中触发的门。作为**报告**（`--notes` 定期跑、由监控读）它是合适的；
作为**门禁**，在词表分级换成「看代码做了什么」而不是「看名字叫什么」之前，我判**不该**。

---

## 五、对账三点的复核

三点我**全部独立复算，全部成立**。这一节我没能推翻任何东西。

### (i) 三行 `fd_expansions: 0`

复算 `runs/p13-fd-real/dividend.json`：`cross_check` 七行，其中三行
`fd_exit_code: 12, fd_expansions: 0, fd_unsolvable: true, agree: true`——
`a0-spike/mismatch`、`cold-start-a0/no-button`、`cold-start-a2/holed`。数字对。
「`expansions` 非 `None` 说明 FD 正常打印了统计块」这个推理成立
（`EXPANDED = re.compile(r"Expanded (\d+) state\(s\)\.")`，崩在半路不会打印这一行）。

### (ii) 43 份 exit-12 日志

我自己数了 `runs/20260728T072633Z-E2-fd-ladder-bench/logs/`：

| `search exit code` | 份数 | 含 `Completely explored state space` |
|---|---|---|
| 0 | 104 | 0 |
| 12 | **43** | **43 / 43** |
| 34 | 8 | 0 |
| 合计 | 155 | |

**exit 12 且不含那句话的：0 份。** 与 RECONCILIATION.md 逐字一致。
额外核实它自己提的那条自我削弱：43 份里按文件名分档是 **32 optimal / 11 satisficing**，
11 份满意档的日志**确实**含那句话而 `proves_unsolvable` 照样拒绝——
所以这把尺子不是恒真谓词。这一条我核过，是真的，而且是它自己主动写出来的。

### (iii) 桩独立同意

三行 `stub_unsolvable: true`，`stub_expansions` 分别 315 / 23 / 41（非零）。
`search.py:165-166` 触顶 `raise RuntimeError`，所以返回的 `plan=None` 只能是队列清空。成立。

### `ringstuck` 那两处：**实现员没有漏，反而比工单说得更全**

工单问它有没有漏掉 `deadlock_dividend` 里 `ringstuck` 的
`fd_unsolvable_before/after: true`。答案是**没有漏**——`RECONCILIATION.md` §一
主动把「工单说的三行」纠正成「**五处主张，分在两张表里**」，并且点名
「`deadlock_dividend` 的行根本不记 FD 退出码，所以那两处连它当时读到了几都无从查起」，
还说明这正是它新增 `fd_exit_code_before/after` 的原因。我核了 `dividend.json`：
`deadlock_dividend` 三行，`ringstuck` 那行确实只有
`fd_unsolvable_before/after: true` + `fd_expansions_before/after: 0`，**无退出码**。

它给的旁证也对：`ringstuck4.fd-optimal-blind.base.log` 与 p13 的 `ringstuck` 同实例同档，
日志里 `Completely explored state space` 与 `Expanded 0 state(s).` 同现。

**结论：对账「结论未变、方法已修」成立，且它自己把置信度标成「强旁证，不是重算」，
把「产物不存日志所以无法重算」写在最前面。这一节我找不到问题。**

---

## 六、我没能查的面（诚实清单）

1. **没有 Fast Downward 构建**（`.toolchain/` 按设计 gitignore，本机无）。
   所以：p13 无法重跑，`bench/` 的 FD 路径（含推翻 1 里的 `guard_refused` 链路）
   只能读代码论证，**没有实跑证明一次真超时确实会让 bench 退出 0**。
   全套 452 条里 23 条 skip，其中就有 FD 相关的几条。
2. **推翻 1 的严重性我没有量化**：E2 的已发布 `dividend.json` 里有几行 `guard_refused` 非空、
   那几行是不是本来就会被健全性判据放过——我没算。我论证的是**机制**，不是**已放电**。
3. **只做了 36 个变异体**，且集中在本次改动的 11 处。没有对
   `bench/`、`recheck/` 其余部分、`cegis_miner`、`ic3_pdr` 做变异。
   「31 杀 5 逃」是这 36 个上的数，不是杀伤率的估计。
4. **常设检查的假阳假阴是构造的**，不是在真实提交历史上跑出来的。
   我没有对全仓 22 个领地逐文件人判过 26 处命中——ERROR 四处我逐条看了源码，
   NOTE 22 处我只抽看了 CALIBRATION 点名的那几处。
5. **`e392d46` 新加的「cegis_miner 判不成立」那一条我没有独立复核**：
   要判「frontier 承诺的是同长枚举还是深度 ≤3 枚举」得读 `enumerate_frontier` 的
   全部调用方和 E11 那份 `partials/cegis_miner-via-bruteforce.md`，超出本次预算。
   **我既不背书也不反对这条判定。**
6. **并发**：实现员在我复核期间仍在写这个目录。我核过
   `MANIFEST.json` 的 `files[].sha256` 与当前字节：18 条里 **1 条不符**
   （`CORRECTIONS.md`，manifest 记 `6c6cfe64…`，实际 `b02da70f…`），
   因为 `e392d46` 又改了它一次而 manifest 停在 `base_commit: b0d3d3d`。
   这可能只是"还没写完"，不当作缺陷记，但按仓库「provenance is canonical」的约定，
   合并前应当重算。
7. **没跑** `python -m tools.run_all`、没跑 `fixtures.generate_all` 的字节稳定性复核、
   没验 `artifacts/candidates.jsonl` 的 sha256 与 `release/MANIFEST.jsonl:667` 是否仍相符
   （只核了「加字段会改 id」这个推理的结构前提）。
8. 封存堆零接触；`cold-start-a0/`、其它 worktree、主工作树全程只读或未碰。

---

## 七、一句话

**方向上我推不翻它**——11 处的缺陷判定我逐条独立核过，全部同意，没有一处是 SURVEY 或
实现员判错了；对账三点我全部复算，数字全对，而且它自己把工单说的「三行」纠正成了五处。
**推得翻的是三件事**：#9 被从判定层降级成了渲染层（`dividend.py:874` 在 `failures()` 里，
`failures()` 定退出码）；#8 的修复是惰性的（零测试 + 一个不可达分支 + 字段不进产物，
等于只改了注释）；以及「负样本构造上必然会红」不成立——18 个变异体恰好对应 18 条测试，
换 5 个它没试过的方向，包括把整个扫描层掏空，套件照样全绿。
