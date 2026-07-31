# 普查：求解器失败状态被当成世界性质

RES-3 verify 赛道普查员，只读普查，仓库零字节改动（本文件除外）。
worktree `.worktrees/e11-engine-crosscheck-deep/`，分支 `agent/e11-engine-crosscheck-deep`，
base commit `6ee04667ca7e95619ca841e32947f8c87ea87dae`。

判据（监控给定）：把「工具失败/不确定」解释成「世界具有某性质」= **不安全**；
解释成「未知 / 未证明 / 需要更多工作 / 控制流」= 安全。只有前者算缺陷。
基准是 `Theoria.md:244` 约束 6 ——「全称断言必须带证明；裸 UNSAT 禁止。
搜索说"无解"不算数，证书才算数」。

---

## 汇总

扫了 **约 60 处**读取求解器/规划器/证明器/检查器状态的地方（规划器退出码与无 plan
文件、LP/HiGHS status、IC3 层数上限、BFS 展开预算、不变量检查器的"不可检"态、
Lean 编译状态、CI 退出码）。

**判为不安全方向的 3 处。** 监控的判断是对的 ——「多半不止一次」，确实不止：

| # | 位置 | 一句话 | 是否在放电 |
|---|---|---|---|
| **U-1** | `engine-rig/tools/p13_fd_dividend.py:129` | 裸 `returncode == 12` 直接写成 `unsolvable=True`，无日志、无档位、无 plan 文件核对 | **在放电**，已落进已发布产物 |
| **U-2** | `worldgen/core/truth.py:279` | `.get("holds", True)` 把「这条不变量无法检查」默认成「它成立」 | **在放电**，13 个已构建世界 |
| **U-3** | `cold-start-a0/certify/fd_unsat.py:34,46` | exit 12 读成「已证明不可解」（今晚已知的那一例） | **潜伏**，被上游改串挤成死代码 |

另有 **2 处潜伏隐患**（当前无调用方触发）、**1 处有意声明的消融**（不算缺陷）、
**6 处文档传播同一条错口径**（会重新种出 U-3）。

值得单说的是 **U-1 就在 `engine-rig` 自己家里** —— 同一个赛道写出了全仓最正确的
`backends.proves_unsolvable`，却在隔壁 `tools/` 里把它绕过去重写了一遍，重写错了。

---

## 不安全的（逐条，最重要的在前）

### U-1 `engine-rig/tools/p13_fd_dividend.py:129` —— 裸退出码 12 = UNSAT，且已发布

| 位置 | 工具 | 读到的状态 | 解释成 | 不安全方向 | 有无证书 |
|---|---|---|---|---|---|
| `engine-rig/tools/p13_fd_dividend.py:129` | Fast Downward | `returncode == 12` | `unsolvable=True`，世界不可解 | **是** | **无** |

```python
        return FdRun(
            config=alias or search_config,
            exit_code=done.returncode,
            ...
            unsolvable=done.returncode == 12,
        )
```

**为什么危险。** 三步都没做：不看 FD 日志有没有 `Completely explored state space`、
不看跑的是哪一档、不看 plan 文件在不在（`plan` 变量在 :117-120 已经读出来了，
但没参与判定）。而本仓库自己的常量表 `engine-rig/engines/fd_adapter/backends.py:74`
写的是 `FD_SEARCH_UNSOLVED_INCOMPLETE = 12` —— **12 是「搜索停了、没找到」，不是证明**。
正确谓词 `backends.proves_unsolvable(tier, returncode, log)` 就在
`backends.py:239-270`，而这个模块 **已经 import 了 `backends`**
（:120 用了 `backends.parse_sas_plan`），差的只是一次属性访问。

**这个字段不是私有测量，它撑起四条对外断言**（同文件）：

* `:315-318` —— `"fd_unsolvable_before"` / `"fd_unsolvable_after"` /
  `"same_answer": (before.plan_length == after.plan_length and before.unsolvable == after.unsolvable)`。
  **这正是「死锁定理没有改变实例答案」的那道守门**。若加了守卫的编码让 FD 在原本
  就放弃的地方继续放弃，`same_answer` 报 yes。
* `:368` —— `agree = ((stub.plan is None) == fd.unsolvable and ...)`，桩 vs FD 交叉复核的全部判据。
* `:441-442` —— 报告表里 `fd = "UNSAT" if row["fd_unsolvable"]`。
* `:410-418` —— 叙述性结论散文，直接断言实例不可解。

**已经落进发布产物。** `engine-rig/runs/p13-fd-real/dividend.json` 的 `cross_check`
七行，其中三行是 `fd_exit_code: 12, fd_unsolvable: true, agree: true`：
`a0-spike/mismatch`、`cold-start-a0/no-button`、`cold-start-a2/holed`。

**减轻情节（必须如实说，否则会误导修复优先级）：** `run_fd` 全仓只用
`BLIND = "astar(blind())"` 调用（:64, :302-303, :365），这是**完备、可采纳、无成本界**的配置，
所以在这个配置上「开列表清空 → 退出 12」确实是证明 —— 按 `backends.py:253-256`
自己的规则也认。而且这三条结论**当前是真的**：桩在三条上全部独立同意
（`agree: true`，桩是完备且预算耗尽会抛的）。
**所以是方法不健全，不是结论错。** 但方法一旦换档（加个 `--alias lama-first`）、
或 FD 因任何别的理由走到 12，这段代码读不出区别，而 `same_answer` 那道守门会照样放行。

**修复方向（仅记）**：:129 换成
`unsolvable=backends.proves_unsolvable(backends.FD_OPTIMAL, done.returncode, log)`。
`log` 在 :114 已经有了。

---

### U-2 `worldgen/core/truth.py:279` —— 「这条不变量没法查」被默认成「它成立」

| 位置 | 工具 | 读到的状态 | 解释成 | 不安全方向 | 有无证书 |
|---|---|---|---|---|---|
| `worldgen/core/truth.py:279` | 不变量检查器自身 | 该不变量**不可执行检查**（`verified: False`，且**根本没有 `holds` 键**） | `invariants_all_hold: true` | **是** | 无 |

`check_invariants`（同文件 :199-203）对纯散文不变量这样落行：

```python
        if check is None:
            row["verified"] = False
            row["note"] = "prose only — not checkable on a single state"
            results.append(row)
            continue
```

这样的行**没有 `holds` 键**。然后 :279：

```python
        "invariants_all_hold": all(i.get("holds", True) for i in invariants),
```

`.get("holds", True)` 把每一条**未经检查**的不变量默认成成立。
「我查不了这条」被洗成「这条不变量是这个世界的性质」。这是判据的正中心。

**在放电，且落进了已构建产物。** 我对 `worldgen/out/worlds/*/ground_truth.json`
逐个核过：**13 个世界**带至少一条 `verified: false` 的不变量，而**每一个**都发布
`invariants_all_hold: true`：

| 世界 | 被当作成立的未检查不变量 |
|---|---|
| `t1-fragile-bridge`, `t3-gravity-fragile` | `tile_state_is_monotone` |
| `t1-switch-latch`, `v-379c937f`, `v-d2c2b1b9`, `v-efe43df1` | `latch_monotone` |
| `t1-tokens-lock`, `t2-cycler-lock`, `t3-cycler-portal-lock`, `v-29ace70e`, `v-bd2babb4` | `collection_is_monotone` |
| `t2-lock-fragile` | `collection_is_monotone`, `tile_state_is_monotone` |
| `t3-latch-maze` | `latch_monotone`, `collection_is_monotone`, `tile_state_is_monotone` |

**并且它升级成了"无失败"断言。** `worldgen/build.py:104` 把该标志抄进每世界一行，
`build.py:166-167` 汇成清单总计：

```python
            "invariant_failures": sorted(r["world_id"] for r in rows
                                         if not r["invariants_all_hold"]),
```

于是 `invariant_failures: []` 被读成「每条不变量都查过且都成立」，
而对 13 个世界来说其中一部分**从未被查过**。

**注意 Markdown 渲染器是诚实的**（`truth.py:333-339` 写 `_(prose only, unverified)_`），
**只有机器可读的那个汇总标志说了假话** —— 而机器可读的那个才是下游读的。

**修复方向（仅记）**：`i.get("holds", False)` 并另开一个
`invariants_unverified` 计数；或把未验证行排除出 `all(...)`，作为第三态上报。

**同文件、反方向的一笔（保守，不算缺陷）** `truth.py:206-211`：检查器自身抛异常
→ `ok = False` → `holds: False`，即把工具崩溃报成世界**违反**了不变量。
方向是安全的那一侧，且 `error` 键保留了区分，可追溯。只因为是同一个混淆的镜像而记一笔。

---

### U-3 `cold-start-a0/certify/fd_unsat.py:24-26, 34, 46` —— exit 12 读成「已证明不可解」（今晚已知的那例）

| 位置 | 工具 | 读到的状态 | 解释成 | 不安全方向 | 有无证书 |
|---|---|---|---|---|---|
| `cold-start-a0/certify/fd_unsat.py:34,46` | Fast Downward | exit 12 | 「规划器**证明**了不存在计划」 | **是** | 谓词处无 |

```python
FD_UNSOLVABLE_EXIT = 12
...
return bool(match) and int(match.group(1)) == FD_UNSOLVABLE_EXIT
```

docstring（:24-26）把根据写死了：`12 SEARCH_UNSOLVABLE — proved, not merely unfound`，
`13 SEARCH_UNSOLVED_INCOMPLETE`。**两处都与实测相反：**

1. **常量错位。** `backends.py:72-74` 照本仓库安装的 FD build 的
   `driver/returncodes.py` 抄：`TRANSLATE_UNSOLVABLE = 10`、`SEARCH_UNSOLVABLE = 11`、
   `SEARCH_UNSOLVED_INCOMPLETE = 12`。`fd_unsat` 认成 12 的语义实际住在 11。
2. **退出码本身根本不足以判定。** `backends.py:76-88` 与 `engine-rig/DECISIONS.md:483-492`
   记的是实测：`SEARCH_UNSOLVABLE`(11) 只由结构性判定的算法发出（EHC、PDB CEGAR）；
   完备的 `astar(blind())` 穷尽 `sokoban_ringstuck`（`deadlock_carver` 独立证明不可解）
   后打印 `Completely explored state space -- no solution!`，**退出码 12**；
   `--alias lama-first` 同一实例**也是 12**。「我全找遍了」与「我放弃了」共用 12。

**当前不在放电 —— 潜伏。** 这必须如实说：

* 正则 `produced no plan file \(exit (\d+)\)` **已匹配不上**上游现在的报错串
  （`backends.py:339` 现在是 `"...produced no plan file and no proof (exit %d, rung %s): %s"`）。实跑验证：

  | 消息 | 命中 |
  |---|---|
  | `Fast Downward produced no plan file (exit 12): boom` | True（旧串，已不产生） |
  | `Fast Downward produced no plan file and no proof (exit 12, rung fd-optimal): boom` | **False** |

* **真**证明改走别路：`fd_adapter.solve()`（`__init__.py:164-166`）证明无解时抛
  `NoPlanExists("no plan exists for %s")`，命中 `fd_unsat` 的 `_STUB` 分支。
  **exit-12 分支现在是死代码。**
* 两个活调用点（`pipeline/plan_stage.py:64`、`certify/fd_conformance.py:176`）因此当前
  都拿到正确答案，**但是靠上游修复，不是靠这个谓词**。这是巧合，不是护栏。
* 产物佐证：`cold-start-a0/artifacts/fd_real.json` 里 `a0-no-button` 是
  `fd=UNSAT / stub=UNSAT / green=true`，经 `NoPlanExists` 得出；
  `artifacts/unsolvable_report.json` 给它配齐了证书 —— **零公理**的 Lean 定理
  `unsolvable`（`axiom_reports: [{name: unsolvable, axioms: []}]`）、zero_space 不变量、
  constructive_ground。**约束 6 在这条链上履行了。**

**加重情节两条：**

1. **错口径正在发布。** `release/MANIFEST.jsonl:290` 收录该文件，
   `verdict: "releasable"`，sha256 `beb5ce6c34199ec3e632833de83fced2620fea5a4999fd31ce8723f91df0c66e`
   —— 我对当前字节重算，**逐位一致**。
2. **测试把错映射写进断言，套件必然全绿。** `cold-start-a0/tests/test_followups.py:245-249`
   断言 `is_unsat(...exit 12...)` 为真、`is_unsat(...exit 13...)` 为假。这条测试
   无法证伪该缺陷，它固定该缺陷。

---

## 潜伏隐患（当前无调用方触发，但耦合是真的）

### L-1 `engine-rig/recheck/verify.py:289, 297` —— 展示预算与证书判定共用一个变量

```python
            if target < 0 or not satisfies[target]:
                if len(closed_bad) < max_witnesses:          # :289  展示预算
                    closed_bad.append(...)
...
        verdict.conditions["inv_closed"] = not closed_bad     # :303  证书判定
        verdict.conditions["goal_break"] = not goal_bad       # :304
```

`goal_bad` 同样在 :297 就被 `[:max_witnesses]` 截断。于是三条义务里的**两条**
（`inv_closed`、`goal_break`）其真假来自一个**被展示预算截断过**的列表：
`max_witnesses=0` 时列表恒空，两条义务报 True，**一张预算为零的证书被接受**。
只有 `inv_init` 是解耦的（:300-301 无预算门，:306 才切片）。

**当前安全**：`MAX_WITNESSES = 6`（`verify.py:53`），`ruleset.obligations` 默认也是 6，
全仓无任何调用方传别的值（只有 `verify.py:221` 透传默认值）。
**建议**：另设一个 `found_any` 布尔量与计数解耦。

### L-2 `cold-start-a2/a2pipeline/plan.py:74`、`cold-start-a3/a3pipeline/plan.py:100` —— 靠字符串匹配另一个组件的未版本化消息

两处都是 `if "no plan exists" not in str(exc): raise`。当前安全：该串只由
`fd_adapter.solve`（`__init__.py:165`）在 `solve_parsed` 返回 `None` 后产生，
且两处都 `prefer="stub"`，桩的预算超限抛的是另一句
（`search.py:146` `"search exceeded %d expansions"`），匹配不上。
**a3 的 docstring（`plan.py:70-82`）自己把这个耦合完整点名了**：
「若那条消息被改写，本模块就不再区分『不可解』与『规划器挂了』，
**而这个失败会长得像一条关于说明书的事实**。记录而非修复。」——诚实，但耦合是真的。
建议 a2/a3 改走已经在做这件事的谓词（即修好后的 `fd_unsat.is_unsat`，或直接
`isinstance(exc, fd_adapter.NoPlanExists)`）。

---

## 有意声明的消融（不算缺陷）

`ablation-arm/ablcore/plan_abl.py:90-104` 写出
`"verdict": "unsolvable", "settled_by": "search", "certificate": null,
"certificate_owed": false, "distinguishes_proof_from_exhaustion": false`。

这**是**「搜索没找到 → 世界不可解」，但它是**去掉约束 6 的对照臂**，是 C-4 消融的
实验处理本身。docstring（:29-36）点名了它正在丢掉的那个区分，产物里
`distinguishes_proof_from_exhaustion: false` 与 `full_arm_would` 逐条自曝其限，
`run_arm.py:367-374` 进一步标注「**THIS IS THE FINDING, not a quiet success**」。
按判据不是缺陷。已核：无任何非消融代码路径 import `ablcore.plan_abl`。
落盘形态 `ablation-arm/artifacts/{a2-holed,a0-no-button}/plan.json` 亦已核。

---

## 同一条错口径的文档传播（会重新种出 U-3）

| 位置 | 内容 |
|---|---|
| `ablation-arm/ablcore/plan_abl.py:30-31` | 「FD exit 12 是 proved no plan exists，exit 13 是搜索不完备」 |
| `cold-start-a0/certify/fd_conformance.py:174` | 「the stub says "no plan exists"; Fast Downward says exit 12. Same claim, two spellings」 |
| `cold-start-a0/DECISIONS.md:358, 373` | 同上口径 |
| `cold-start-a0/STATUS.md:55` | 「"there is no plan" (exit 12)」 |
| `cold-start-a0/BLOCKER_FAST_DOWNWARD.md:112, 128` | 同上口径 |
| `ablation-arm/runs/2026-07-28-p18/02-a2-anatomy.md:173-178` | 「exit 12（证明无解）与 exit 13（搜索放弃）的区别，就是约束 6 的整个内容」 |

对照：`PARTNER_SYNC.md:449` 已从 engine-rig 侧纠正并公告（含实测与 D-024 处置），
`engine-rig/STATUS.md:303-304`、`engines/fd_adapter/README.md:73`、
`runs/p13-fd-real/TOOLCHAIN_MANIFEST.md:238` 亦然。
**纠正只落在 engine-rig 一侧；cold-start-a0 / ablation-arm 侧六处仍是旧口径。**

---

## 正当的（不算缺陷，列出来以示我看过）

多数不只是"没错"，而是**主动把不安全方向堵死**的写法，值得当范式引用。

### 规划器 / 搜索

| 位置 | 状态 | 解释成 | 判定 |
|---|---|---|---|
| `engine-rig/engines/fd_adapter/backends.py:239-270` | exit 码 + 日志 + 档位 | 10/11 是证明；12 仅"最优档 + 自报穷尽"；满意档一律拒绝（"exhausted under a bound proves only that no *cheaper* plan exists"） | 安全（**全仓范式**） |
| `engine-rig/engines/fd_adapter/backends.py:336-341` | 无 plan 文件且不构成证明 | `RuntimeError`，串里带退出码与档位 | 安全 |
| `engine-rig/engines/fd_adapter/__init__.py:114-141, 164-166` | 证明无解 | 返回 `None`（与桩同语义）/ 抛可区分的 `NoPlanExists(RuntimeError)` | 安全 |
| **`engine-rig/engines/fd_adapter/search.py:145-146`** | 展开数超 `max_expansions` | **`raise RuntimeError`** —— 不返回 `plan=None` | 安全（关键：预算耗尽做成硬错误，从源头消灭可被误读的"放弃"态） |
| `engine-rig/engines/fd_adapter/search.py:162` | 队列自然清空 | `SearchResult(None, ...)` = 穷尽证明 | 安全 |
| `engine-rig/engines/fd_adapter/search.py:129-130` | 静态谓词目标不可满足 | `None` | 安全（构造性证明，非放弃） |
| `engine-rig/bench/fdrun.py:233-252` | exit 12 + 日志 + 档位资格 | **四值**：`solved` / `proved_unsolvable` / `not_entitled`（"neither an answer nor a fault"） / `error` | 安全（与 U-1 同一个仓库、同一个问题，这里做对了） |
| `engine-rig/bench/ladder.py:74-107, 174-181` | 预算超限先行捕获 → `proved_unsolvable: False, error: "over budget"` | 三值 `solved`/`unsolvable`/`"no answer"` | 安全 |
| `engine-rig/engines/probe_frontier/reach.py:94-99` | `plan is None`（`prune=` 强制走桩、不封顶） | `status = UNREACHABLE`，docstring 明写"是发现不是失败" | 安全（依托上面两条；但见"不确定的"） |
| `engine-rig/engines/deadlock_carver/carve.py:226-231` | 无状态满足该模式 | `None`，"describes no reachable state: proves nothing" | 安全（堵死空洞定理） |
| `engine-rig/tools/run_all.py:116-117, 143-144, 155-156, 173-174` | 引擎返回空 | 一律 `raise RuntimeError` | 安全（不证明 ≠ 世界性质） |
| `cold-start-a0/pipeline/plan_stage.py:64-78` | `is_unsat(exc)` | `status: "UNSAT"` + `"constraint 6 forbids stopping here; a certificate is owed"` | 安全（映射到**义务**，不是裁定） |
| `cold-start-a0/pipeline/unsolvable_variant.py:208-210` | `plan["status"] == "UNSAT"` | 只是 `green` 的一个合取项；真正的主张是零公理 Lean 定理 | 安全 |
| `cold-start-a2/a2pipeline/plan.py`, `cold-start-a3/a3pipeline/plan.py` | 同 plan_stage | 「a certificate is owed」 | 安全（耦合见 L-2） |
| `cold-start-a2/a2pipeline/exhibit.py:140-154` | `plan["status"]=="UNSAT"` 进 `exhibit_green` | 紧接着用独立 `world.solve()` 得出 `exhibit_is_false_of_the_world` | 安全（UNSAT 是展品的**对象**，不是它的证据） |
| **`theoria-arm/inner/plan.py:58-65`** | 说明书未声明目标 | `status: "no_goal_declared"` +「This is a gap in the manual, **NOT a proof that the level is unsolvable** — constraint 6 forbids reading a failed search as an unsolvability claim」 | 安全（**全树最佳单例**） |
| `theoria-arm/inner/plan.py:119-122, 156-168` | 节点上限 / 截止 | `status: "search_timeout"`，与 `"unsat"` 分立；PDDL 档 `found is None` 落到下一档而非下结论 | 安全 |
| `worldgen/core/solvability.py:34-51, 149` | BFS 队列清空 | `None` → `"solvable": false`；**无预算上限**，不存在"放弃"态 | 安全；证书 `kind: "exhaustive_reachability"` + 分隔前沿 + 单点删除翻转 |
| `a0-spike/pipeline/adapt.py:218-232` | `solve_bfs(...) is None` | `old_verdict_still_correct` | 安全（`world/sokoban2.py:210-211` 预算超限**抛错**，`None` 只可能是穷尽） |

### LP / 求解器

全仓 **只有一处** `linprog` 调用。

| 位置 | 状态 | 解释成 | 判定 |
|---|---|---|---|
| `engine-rig/engines/lp_potential/potential.py:170-171` | HiGHS `result.success` 为假 | `return None` = **没找到证书**，不对世界发断言 | 安全 |
| 同上 :184-190 | LP 成功但有理数快照未过精确复核 | `CertificateError` —— 浮点解不算证书（D-007） | 安全（保守） |
| `engine-rig/engines/lp_potential/__init__.py:62-64` | 无证书 | `None, None`；"the correct answer for a solvable configuration, **not a failure**" | 安全 |
| `fuzzlab/props/lp_potential.py:99-100` | `cert is None` | `return []  # no claim made; incompleteness is allowed` | 安全 |
| `fuzzlab/props/lp_potential.py:104-108, 237-241` | 判官 BFS 撞预算 | `finding.skipped("BFS hit the state budget, so 'unreachable' could not be proved either way")` | 安全（判官自己也拒绝越权） |

注 1：`not result.success` 把 infeasible 与迭代上限、数值失败合并了；`bound=10`（:119）
是求解器参数不是 pagoda 概念的一部分（本工单 partial `lp_potential-via-exhaustive.md` §7
测得 639 个"沉默"世界里有 1 个是被这个箱约束卡住而非数学）。因为 `None` 从不撑起任何
世界断言，这是**表达力报告问题，不是不健全**。

注 2：`potential.py:120-124` 那句 docstring 的逆命题（「目标可达 ⟹ LP 必不可行」）是**假的**，
`CLAUDE.md` 与 `worldgen/core/solvability.py:5-6` 都写明 sound but incomplete。
措辞可收紧，但**无任何调用方按逆命题用它**，不算缺陷。

### SAT / IC3 / 定理证明器

| 位置 | 状态 | 解释成 | 判定 |
|---|---|---|---|
| **`engine-rig/engines/ic3_pdr/pdr.py:268`** | 层数超 `MAX_LEVELS=64` | **`raise Ic3Error("no verdict within %d levels")`** | 安全（`unknown` 绝不落成 `unsat`） |
| `engine-rig/engines/ic3_pdr/pdr.py:55-56` | —— | 类 docstring：「An internal invariant of the search broke — **never a property verdict**」 | 安全（把边界写进类型语义） |
| `engine-rig/engines/ic3_pdr/check.py:44-77` | 每张 `Invariant` | 由 `check.verify`（不 import `pdr`）**穷举状态空间**独立复核 | 安全，证书齐备 |
| `engine-rig/recheck/verify.py:362-409` | 独立 BFS 第二意见 | 条件通过但找到反例 → `INCONSISTENT`（报为检查器 bug）；条件不通过但没找到 → "the claim may still be true … but this certificate does not establish it" | 安全 / 保守（正确的 unknown 映射） |
| `theory-compiler/src/theory_compiler/ic3_certificate.py:157, 161-217` | 读入的 CNF 证书 | 三条义务全部从 CNF 在 `2^n` 上重推，失败即抛；「**The producer's own verdict is not evidence.**」空子句集/空子句一律拒绝 | 安全 |
| `theory-compiler/src/theory_compiler/ic3_certificate.py:220-229` | 证书未排除的目标 | 以列表返回，"the method's incompleteness showing through rather than a bug to route around" | 安全 |
| `theory-compiler/src/theory_compiler/conflict.py:683-703, 809-813` | 扫描预算超限 | `raise ConflictError`；:56-59「Anything guard analysis cannot settle is reported as **undischarged, never as proved**」 | 安全 / 保守 |
| `theory-compiler/src/theory_compiler/deadlock_certificate.py` | 无状态满足的模式 | 拒绝；并交叉核对生产者的 grounding 计数，不一致即抛 | 安全 |
| `theory-compiler/.../gen_markdown.py:218-221` | `inv.status` | `"proven"` → "mathematically verified"；`"open"` → **"conjectured, not yet proven"** | 安全 |
| `fuzzlab/oracles/search.py:43-68, 116-153` | 撞 `STATE_BUDGET` | `(None, exhausted=False)`；「`exhausted` is the difference between "no plan exists" and "I ran out of budget", which is **the whole of the unsolvability judgement**」 | 安全（范式） |
| `fuzzlab/props/fd_adapter.py:19-20, 30, 159-183` | `plan is None` | 性质 `no_plan_means_unsolvable`；用地面 BFS 重推，BFS 撞预算则 `skipped("so 'no plan' could not be confirmed either way")` | 安全（这个模式已被写成 property test） |
| `engine-rig/engines/zero_space/gf2.py:4` | —— | 精确 GF(2) 运算，"no tolerances, no floating point" —— 没有数值秩状态可误读 | 安全 |
| `engine-rig/engines/cegis_miner/miner.py:323, 344` | 前沿枚举超 `MAX_FRONTIER_SIZE` | `truncated` 标志 + `frontier_max_size` 写进 payload | 安全（不隐瞒截断） |

### Lean / 类型检查器

| 位置 | 状态 | 解释成 | 判定 |
|---|---|---|---|
| `cold-start-a0/certify/lean_check.py:52-61` | 找不到 toolchain | `available: false, green: false` + reason；「It **never downgrades a missing proof into a passing one**」 | 安全 |
| `cold-start-a0/certify/lean_check.py:96-102` | 编译状态 | `green` 需 `returncode==0` **且**无 error **且**无 `sorry` **且** `bool(axiom_reports)` **且**全部零公理 | 安全（第四个合取项是关键：编译通过但从不询问公理的文件无法变绿；`native_decide` 的 `Lean.ofReduceBool` 被点名堵掉） |
| `cold-start-a2/a2pipeline/certify_a2.py:73-122`、`cold-start-a3/a3pipeline/certify_a3.py:115-176` | 同上 | 同上五合取 | 安全 |
| **`theoria-arm/inner/certify.py:241-249`** | `proc.returncode` | `"lean accepted the file"` / **`"lean rejected the file"`** —— 说的是**这份文件**，不是命题真假 | 安全（措辞精确，正是本次要找的反面） |
| `theoria-arm/inner/certify.py:232-238, 293` | `lean` 不在 PATH | `ok: False`，detail「the proof obligations are **stated and undischarged**」；`surprises_from` 只在 `available` 时才触发 `proof_failure` —— **缺工具永不构成证据** | 安全 |
| `a0-spike/pipeline/lean_stage.py:58-62, 84-89` | 无 toolchain | `available: False, skipped: "no lean toolchain found"`，永不变绿 | 安全 |
| `a0-spike/pipeline/cross_form.py:32-46` | `lean --version` 探测 | 用真跑而非 `shutil.which`（`elan` 有 shim 但无默认 toolchain）；「presence was never the right question」 | 安全（读退出码答"装没装"，完全正当） |
| `a0-spike/pipeline/cross_form.py:151-155` | `returncode != 0` | `raise RuntimeError("lean failed")` —— 差分测试失败即抛，不报"两形式一致" | 安全（正确方向） |
| `theory-compiler/tools/verify_c4.py:114-121, 160-171` | 负对照的 `returncode != 0` | 单独看不安全，但 :170 与 `failed_on_closure = "closed_pinned" in output` **合取**，且 :114-121 先用 `dc.recheck` 独立确认该对照模式**确实可逃逸**才去问 Lean；docstring「一个因错误原因失败的对照**比没有对照更糟**」 | 安全 |

### 考试 / 真值构造（本轮最强的免疫样本）

| 位置 | 状态 | 解释成 | 判定 |
|---|---|---|---|
| `exam/papers/verdict.py:585-589` | 枚举撞 `MAX_ENUMERATION` | **`raise AssertionError("did not finish enumerating under the cap; it is not a small-space item")`** | 安全 |
| `exam/grading/rubrics_verdict.py:576-577, 597-607` | 同上 | 返回 `truncated=True`，注释「a count that silently hit its cap is **not an enumeration**」 | 安全 |
| `exam/papers/verdict.py:601-608` | 大空间项下界不足 | 抛错「enumeration is not out of reach and the question **does not test what it claims to**」 | 安全 |
| **`exam/papers/verdict.py:901-925`** | —— | **class (iii) 整类就是为这个缺陷造的陷阱**：可解但解极长，spec 原文「a searcher that gives up at a shallow depth reports failure here, and **failure to find is not a proof of absence**」 | 安全（把本次普查的判据做成了评分项） |
| `battery/audit/discriminate.py:121-131, 180-184, 262-269` | 统计功效 | `"underpowered"` / `"no-data"` 与 `"no-effect"` **分立** —— 「测不出来」不塌缩成「没有差异」 | 安全（同一纪律的统计版） |

### 纯控制流 / CI（读退出码完全正当）

`ablation-arm/verify.py:59, 306, 353`、`release/reproduce.py:232-237`、
`monitor/verify.py:69, 96, 150-158`、`cold-start-a0/run_all.py:75-81`、
`exam/verify.py:45-75`、`exam/tools/archive_run.py:51-55`、
`theory-compiler/tools/verify_c8.py:57-60`、`theory-compiler/conftest.py:34-40`、
`cold-start-a0/certify/fd_conformance.py:165-166`（未编译 → `skipped`）、
`engine-rig/engines/fd_adapter/backends.py:95-120`（探测 FD 装没装 / 是不是 driver）、
`backends.py:135-189`（`choose_tier`；点名「asking for a named planner and silently
getting another one is how a benchmark lies」，缺 FD 时对显式档位**报错而非静默降级**）。
**全部只影响控制流，不支持任何关于世界的断言。**

---

## 我不确定的

**?-1 `engine-rig/engines/probe_frontier/reach.py:94-99` —— `UNREACHABLE` 的可靠性挂在剪枝器上。**
`reach()` 把 `prune=` 直通搜索。搜索本身完备（撞预算抛、队列空才返回 `None`），
**状态读取没问题**；但若某条 deadlock 定理不健全，一个**可达**构型会被剪成
`status: "unreachable"`，而 `Reachability.as_json()`（:60-69）只写 `status` +
`expansions` + `backend`，**不附可复核的证书**——读者只能信任适配器的证明/失败判别，
不能自己重验。严格说这是"上游定理不健全被继承"，不在本次判据内，故列此处。
现有证据不支持它在放电：E11 交叉复核记 50/50 条死锁与不可解主张全部成立、0 条被推翻
（`PARTNER_SYNC.md:935`），且 `search.py:123-125` 论证了"目标测试先于剪枝，
所以剪枝器错在目标态上藏不住解"。**建议**：payload 记下答题时挂了哪几条定理。

**?-2 `a0-spike/pipeline/lean_stage.py:75`（保守方向，记一笔）**
`"compiles": compiled.returncode == 0 and not compiled.stdout.strip()` ——
任何 stdout（`info:` 行、`#eval` 回显、trace）都会让一个真的通过了类型检查的文件
被记成 `compiles: false`。方向安全（宁可不认证明），但比 `lean_check.py`
（只筛 `" error:"`）严得多，且此处的假 `false` 与真失败无法区分。

**?-3 我没能覆盖的面。** 本次只扫源码与产物中的**状态读取点**。**没有**做：
跑测试套件；对 21 局封存堆的任何产物取样（纪律要求零接触，已遵守）；
非 Python 工具链脚本与 `.ipynb`（grep 无相关命中，但不能宣称穷尽）。

---

## 一句话结论

**这个模式今晚出现了三次，不是一次。** 已知那一例（`fd_unsat.py`）反而是**最不紧急**的
——它已被上游 `NoPlanExists` 的修复挤成死代码，真实的不可解主张配着零公理 Lean 定理发出。
真正在放电的是另外两处：**`p13_fd_dividend.py:129` 用裸退出码 12 撑起"死锁定理没改变答案"
那道守门，结论已进已发布产物**；**`worldgen/core/truth.py:279` 把 13 个世界里"没法检查"
的不变量默认成"成立"，并升级成清单里的 `invariant_failures: []`**。
两处都无证书，都不是设计意图。

反过来说，仓库在这一点上的免疫力是**设计出来的、不是运气**：预算耗尽一律抛异常
（`search.py:146`、`pdr.py:268`、`verdict.py:587`、`sokoban2.py:210`）、
判官撞预算就拒绝下判（`fuzzlab/oracles/search.py`）、工具缺失记 `available: false`
而不是悄悄变绿（`lean_check.py:52-61`、`theoria-arm/inner/certify.py:293`）、
「lean rejected **the file**」而不是「命题为假」、`"no_goal_declared"` 明写
"NOT a proof that the level is unsolvable"、四值/三值的 `fdrun.py` 与 `ladder.py`、
以及一整类专为这个缺陷设计的考题（`exam` class (iii)）。
**U-1 尤其刺眼，正因为同一个仓库在 `backends.py:239-270` 和 `bench/fdrun.py:233-252`
已经把这件事做对了两遍。**
