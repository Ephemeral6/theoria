# 普查：工具的成功状态被当成世界的性质（失败那一族的对偶）

范围：`.worktrees/e11-engine-crosscheck-deep/`，纯只读。
`实测` = 跑过（只在内存里跑，未写任何文件）；`读码` = 只读源码。

## 汇总

扫了约 **105** 处「工具成功 → 断言」站点；判**不安全 8 处**。

覆盖面：`engine-rig/engines/` 七个引擎全部模块（读码，lp_potential 实测）、
`engine-rig/{bench,recheck,interop,tools}/`、`theoria-arm/`、`baseline-arms/`、
`ablation-arm/`、`a0-spike/`、`exam/`、`battery/`。

三个总体判断：

1. **`engine-rig` 的引擎层这条纪律基本立住了。** 四个引擎（`fd_adapter`、
   `ic3_pdr`、`lp_potential`、`zero_space`）在 emit 之前都有一道 gate，
   `fd_adapter` 和 `ic3_pdr` 那两道是真独立的。这不是行业常态，值得记下来。
2. **漏的不是"没验"，是"验了、写进产物了、然后不拿它把关"。**
   最重的两条（`lp_potential` 的 `admissible`、`deadlock_carver` 的
   `plan_length_unchanged`）都是：证伪器已经写好、已经算出来、已经序列化进
   `candidates.jsonl`，而 emit 路径一眼都没看它。反证与断言并排躺在同一行 JSON 里。
3. **整个 `engine-rig` 没有任何一处留出验证。**
   `grep -rni "held.out|heldout|holdout|hold-out" engine-rig/` → **0 命中**（实测）。
   形状 4（挖掘器只在拟合它的证据上自洽）在这个仓库里不是个别失误，是系统性缺席。

形状 6（重试成功掩盖失败）和形状 5（`json.load` 不抛异常 ≙ 内容正确）
在扫过的面上**没找到会进产物的实例**——如实记下，不凑数。

## 不安全的（最重要的在前）

| # | 位置 | 工具 | 成功信号 | 被断言成 | 有没有验证 | 验证独立吗 | 为什么危险 |
|---|---|---|---|---|---|---|---|
| 1 | `engine-rig/engines/lp_potential/potential.py:255` | scipy `linprog` | `result.success` → 有权重 → 造出 `Heuristic` | 产物里 `"admissible": true`（`kind="heuristic"` candidate 的 payload） | **该字段没有**；真正的检查 `admissibility_report()` 就在同一 payload 的 `admissibility_check` 里 | 检查本身独立（比对 `graph["distance_to_goal"]`），但 **headline 字段不看它** | `"admissible": True` 是**字面量**。实测：拿一份 `conditions.inv_closed=False`、`holds=False` 的证书造 `Heuristic`，`as_json()["admissible"]` 依然是 `True`。`__init__.py:66` 的 emit 既不 gate `certificate.holds`，也不 gate `admissibility_check` 里有没有 `admissible: false` 的行。可采纳性是可采纳性证明的**结论**，这里是常量。 |
| 2 | `engine-rig/engines/deadlock_carver/__init__.py:168-180` | `carve()` / `prove()` | `prove()` 返回 `Theorem`（枚举法，非空即成功） | 每条定理一个 `kind="invariant"` candidate，`coverage="n/n"`，声称该 pattern 下的状态全死 | 有一个经验证伪器：`PruningReport.same_answer`（`__init__.py:67-72`）；它被算出来、被写进产物字段 `plan_length_unchanged` | 不独立（两侧都跑 `fd_search.search`），**而且根本没被 gate** | `run()` 第 176-179 行：`carve` → `pruning_report` → `emit`，**中间没有一个 `if`**。一条不成立的定理会剪掉解路径上的状态，`same_answer` 立刻变 `False`——然后它作为 `plan_length_unchanged: false` 跟着这条定理一起被发布出去。证伪器已经响了，没人接。另：`with_report=False` 时连算都不算。 |
| 3 | `engine-rig/interop/certificate_export.py:126-146`（`verify`），及 `:120-122`、`:149-165` | `lp_potential` 证书 | 证书对象存在 | 跨轨道导出给 theory-compiler 的文档，含 `"verified": true` 和 `"conclusion": "no goal state is reachable from …"` | 有 `verify()` | **不独立，而且 docstring 反着说** | docstring 写"an importer should be able to run this without trusting the producer, so it recomputes rather than reading the `holds` flags"。但 `verify()` 只遍历 `document["obligations"]["inv_closed"]["witnesses"]`——**生产者自己列出的那批 move**。生产者漏掉的合法 move，两边同时看不见，`verify()` 返回 `[]`（无错）。它复算的是算术，不是**义务的完整性**。另两点：`:103` `inv_init.holds` 是字面量 `True`（该义务恒真，无害，但它参与算 `verified`）；`write()` 不看 `verified` 就落盘。这条排第三只因为它跨轨道边界，纠错成本最高。 |
| 4 | `engine-rig/engines/cegis_miner/__init__.py:90-95` | `mine()` / `synthesize()` | 合成器找到了分离 guard（否则 `NoSeparatingGuard`） | 每条规则一个 `kind="rule_hypothesis"` candidate，带 `support` / `coverage` | **一道都没有**——`run()` 是 `mine()` 然后直接 `emit()` | — | `support` 和 `coverage` 算在**恰好是拿来拟合它的那批 transition** 上；CEGIS 的反例循环保证的就是"在给定证据上自洽"，所以这两个数字按构造必然好看，检出力为零。唯一拦着它的是 schema：`kind` 叫 `rule_hypothesis`、`status` 恒为 `"candidate"`，由 LLM 裁决。**这层缓解是契约给的，不是引擎挣的**——换个 `kind` 就没了。 |
| 5 | `a0-spike/pipeline/run_a0.py:252-254` | Lean 编译器 | `lean["compiles"]`（退出码 0） | 整条 pipeline 的 `ok` | 部分：查了 `compiles` + `not uses_sorry` + `forms_agree` | 部分独立（`lean_stage.cross_check` 拿 Lean 的 `step` 对 Python 的 `step` 全枚举比对，这段是好的） | 漏查 `lean["non_vacuous"]`，而 `lean_stage.py` 自己的 docstring（第 1-14 行）明写非空泛是"Lean 证明对这个世界有意义"的**三个条件之一**——"不可达的都不是目标"在任一集合为空时白拿。当前休眠：本机没装 Lean，`available=False` 短路了整个从句。装上 Lean 的那天它会静默放行一条空泛定理。形状 3 的标准形。 |
| 6 | `ablation-arm/exhibits/e1_a0.py:70` | 判决比对 | 消融臂的 UNSAT 与全臂一致 | `verdict_is_correct = True` → `report["holds"]`（`:95`）→ `ablation-arm/verify.py:132-139` 读成 claim **P-5(correct)** → 进完成门 `green`、进 `verify.json` / `exhibits.json` | 无（字面量，带注释辩护） | — | 是产物级断言，但本文件里没有任何代码路径重新推导不可解性。**减一档的理由**：消融臂的全部意义就是把这一步切掉来测量它，`DESIGN.md` C-4 明写这是"切口"。所以它是被测对象，不是暗伤——但 `verify.json` 的读者拿到的是同一个 `true`。 |
| 7 | `ablation-arm/exhibits/e2_a2.py:146-147` | 上游 episode 元数据 | （无——硬编码） | `"really_solvable": True, "witness_length": 18`，注释说"the length upstream records" | 无 | — | `SOLVED_EPISODE` 从未在本文件里加载并重放确认 18 步真的赢。**减档**：已核，`report["holds"]`（`:166`）只用 `believed`/`silent`/`green_on_own_evidence`，这两个字段是纯描述性的 `reading` 文本，不进门。 |
| 8 | `engine-rig/recheck/build_cases.py:362` | Lean | — | 落盘的 case 文件里 `"lean_status": "GREEN, #print axioms unsolvable = []"` | 无（字符串常量） | — | 证明器状态以字面量形式随产物发布，没人在这里跑过 `#print axioms`。**减档到几乎无害**：这条 case 的承重全在别处——`recheck/verify_all.py:52` 对全部 148 个状态独立重新推导，明说"and so does this rechecker"。Lean 的话在这里是旁证不是根据。留在表里只因为它是形状 3 的字面形态，改一版代码就可能变成承重。 |

## 做对了的（样板）

对照标准：`fuzzlab/props/fd_adapter.py::plan_replays_to_the_goal` —— 拿引擎返回的
plan 逐步重放，用 `fuzzlab/oracles/search.py` 的独立 STRIPS 语义检查终态满足目标。

* **`engine-rig/engines/fd_adapter/__init__.py:140`** —— `engine-rig` 里最接近样板的一处：
  ```python
  validate_plan(domain, problem, plan.actions)   # never emit an unchecked plan
  ```
  在 `solve_parsed()` 返回**任何** plan 之前无条件执行，**三个梯级都过**——
  包括 Fast Downward 那两级，所以 FD 的输出对本仓库而言是被独立重放过的。
  `validate.py` 的 docstring 写明"Deliberately does *not* import `search`"（D-010），
  它自己重新接地并施加动作。这就是"求解器成功不等于世界性质"这条纪律的可执行形式。
* **`engine-rig/engines/ic3_pdr/__init__.py:143-154`** —— IC3 返回不变式则由
  `check.py`（不 import `pdr`，全状态空间枚举 inv_init/inv_closed/goal_break）重验，
  不过就 `raise Ic3Error`；返回反例则 `replay()` 逐步走一遍。docstring：
  "Nothing is emitted that has not been checked by code the search does not share."
  这里的措辞本身就是本次普查要找的那条判据。
* **`engine-rig/engines/lp_potential/potential.py:184-189`** —— `result.success` 之后
  **不直接用** `result.x`：snap 成有理数，`check_exactly()` 在精确算术里重验三个条件，
  不过就 `raise CertificateError`。D-007："A certificate that only holds to 1e-9 is
  not a certificate."（这一道相对**求解器**独立；相对 move 枚举不独立，见下节 b。）
* **`engine-rig/bench/dividend.py`** —— 编译进 guard 的任务产出的每条 plan，都拿
  **原始** domain 用独立重放器验一遍，并断言长度等于未加 guard 的最优梯级。
  guard 太强 → plan 变长或消失；guard 太弱 → 没红利。两个方向都被抓住。
* **`engine-rig/recheck/verify_all.py`** —— 不信 `lean_status` 字符串，对全部 148 个
  状态自己重新推导；`MATRIX` 里同时钉了 ACCEPT 和 REJECT 两侧的验收线。
* **`theoria-arm/inner/commit.py`** —— SAT 的 plan 从不被当成"赢"：逐动作在**真实 ARC
  环境**里执行、帧哈希、与 manual 自己的预测比对，一处不符即 `abandoned_at` 中止并
  触发 surprise。跨过了代码边界去拿真值，是全仓最强的一处。
* **`exam/papers/verdict.py:1142-1168`（`_self_check`）** —— 自家参考证书过不了
  `check_certificate()`、或 "solvable" 见证过不了 `replay()`，就拒绝出论文。
* **`engine-rig/engines/probe_frontier/reach.py:100-103`** —— `plan is not None → REACHABLE`
  写进产物的 `verdict` / `tier: executable` / `path_cost`，**是**有独立重放撑着的，
  但它是**继承来的**（`solve_parsed` 内部那一行），本文件里看不见。
  记在这里而不是不安全区，同时记一句：哪天 `:140` 那行被挪走，`reach()` 会静默降级，
  而它自己一个字都不会变。

## "验了但不独立"的（单列——这一格最容易被误读成安全）

监控点名的那条反面（fuzzlab 的 oracle 用引擎自己的 `ground_actions()` 造真值表，
接地层检出力为零）在本仓不是孤例，是**反复出现的同一个形状**：验证器躲开了
搜索/求解器，却和它共用下面那层"世界是什么"的定义。

| 位置 | 验的是什么 | 相对什么独立 | 相对什么**不**独立 | 后果 |
|---|---|---|---|---|
| **d. `engine-rig/engines/zero_space/zerospace.py:194` + `__init__.py:52`** | 每条 law 在轨迹上取值恒定 | 独立于 `analyse()` 的代码路径 | **同一条轨迹**——law 正是从这批 state 的逐帧差的 GF(2) 零空间里解出来的 | **按构造近乎恒真**：零空间里的向量与相邻差点积为 0，等价于沿该轨迹点积恒定。`run()` 里那句 `raise AssertionError("a recovered law does not hold on the trajectory")` **几乎不可能触发**。这是本仓最纯粹的形状 4：验证存在、独立于代码、却在拟合它的证据上空转。要有检出力必须换一条留出轨迹，而全仓没有留出验证。 |
| **b. `engine-rig/engines/lp_potential/potential.py:195-215`** | 三个条件在精确有理算术下成立 | 独立于 `linprog`（真正的收益：浮点 1e-9 的"证书"被挡住） | `moves_from_graph(graph)`——LP 建约束和 `check_exactly` 遍历的是**同一个 move 列表** | 图里**漏掉**一种合法 jump 几何时，LP 的行少一条、`inv_closed` 也少检一条，两边同时瞎。产出的是一份精确算术加持的、**错的**不可达证书。实测：手工截短 move 列表只在我主动破坏权重时才报 `inv_closed: False`；一条**缺席**的 move 对 `check_exactly` 完全不可见。 |
| **a. `engine-rig/engines/fd_adapter/validate.py`** | plan 逐步重放、终态满足目标 | 独立于 `search.py`（自己重新施加 add/del，docstring 明写） | `pddl.py` 的 parser 与 `ground_actions()` | 与 fuzzlab 那条反面**同一处**接地层。`validate.py` 自己的 docstring 已经承认"The only code shared with the planner is the parser"——诚实，但不改变检出力：接地漏了一个动作实例，plan 不会用它，验证也不会想起它。 |
| **c. `engine-rig/engines/ic3_pdr/check.py`** | 全状态空间枚举三个条件 | 独立于 `pdr.py`（不 import） | `system.moves()` / `satisfies_all()` / `system.states` | `System` 的转移关系错了，搜索和检查器一起错。payload 里那句 `"checked_by": "engines.ic3_pdr.check.verify -- shares no code with the search"` 是**准确的**（确实不共享搜索的代码），但读者容易读成"与被验对象无共享依赖"，而那是另一回事。 |
| **e. `engine-rig/engines/deadlock_carver/__init__.py:98-111`** | 加不加 guard 答案一致 | — | 两侧都是 `fd_search.search`，同一个搜索器 | 即便按第 2 条补上 gate，它也只能抓"剪枝改变了这个搜索器的答案"，抓不到"这个搜索器和定理**同时**错"。要真独立得换一个 planner——`bench/dividend.py` 走的正是这条路（拿原始 domain + 独立重放器），可以照搬。 |
| **f. `engine-rig/interop/certificate_export.py:126`** | 义务的算术 | 独立于 LP、独立于 `Certificate` 类 | 生产者列出的 witness 集合 | 见不安全 #3。这是"复算数字 ≠ 复算义务完整性"的教科书形态。 |
| — | `engine-rig/engines/deadlock_carver/carve.py:226`（`prove`） | pattern 封闭 + 排除目标，枚举全部 ground action | 是真枚举，不是启发式 | 全靠 `task.mutexes`（h² mutex，同包 `mutex.py` 推导）；`MAX_PATTERN=2` 的注释自陈"更宽的 pattern 会被看不见它的证据检查" | 证明本身没问题，但它的**前提**（哪些原子能共存）来自同一个包，且事后无人复核。列在这里而非不安全区，因为 `prove()` 确实是证明；不安全的是第 2 条那个**不 gate**。 |

## 我不确定的

* `engine-rig/tools/p13_fd_dividend.py` —— 分包普查在此报了一处，我没有独立钉到行号。
  我自己只确认了 `:129` `unsolvable = done.returncode == 12` ——那属于**失败**那一族
  （今晚已扫过的反面），不重复计入本次。成功侧是否另有问题，**未定**。
* `battery/adapters/a0.py:367-369` —— 把 `cold-start-a0/artifacts/plan_generated.json`
  的 `plan.get("length")` 直接当 `Truth.optimal_steps`，本地不复验。那份 plan 自身有没有
  被重放过，答案在 `/cold-start-a0/` 里——**engine-rig 轨道禁入，未读**（CLAUDE.md）。
  这条留给能读那个目录的人。
* `ablation-arm/exhibits/e1_a0.py:66` 的 `theirs.get("theorem", {}).get("axioms")` ——
  全臂的 Lean 证书是当场重跑的还是读的可能已陈旧的
  `cold-start-a0/artifacts/unsolvable_report.json`，同上，未追进去。
* `engine-rig/artifacts/candidates.jsonl` 当前只有一份，且不含 `admissible` /
  `plan_length_unchanged` 字段（实测 grep 为 0 命中），说明**第 1、2 条的产出路径
  当前没被跑过**（`tools/run_all.py --force` 才会写）。所以这两条现在是**装好的雷、
  不是已爆的雷**——严重度按"下次 run_all 即生效"计，不按"产物已污染"计。

## 纪律记录

只读；未打网络；未读 `.env`；封存堆零接触（未打开 21 局中任何一局的任何产物）；
除本报告外未写、未改任何字节。唯一的执行是一段不落盘的内存内 python
（构造两份合成 `Certificate` 观察 `as_json()`），标 `实测` 的结论仅来自它与几条 grep。
