# 01 · 母体 A0 解剖 — 接线图与只读纪律

来源:对 `cold-start-a0/` 的只读勘查(子代理 · 实现线)。本文件只记**实现需要的承重事实**。

## 1 · 头号约束:母体的 main() 全部写死写回自己的 artifacts/

`ROOT = dirname(dirname(abspath(__file__)))` + `join("artifacts")`,无环境变量、无 `--out`。
`_bootstrap.artifacts_dir()` 同样写死 `HERE/artifacts` 并且 `os.makedirs`(有副作用,别调)。

⇒ **本臂一律走库函数层,不碰任何 `main()`。** 这同时满足 CLAUDE.md 的"不得写入他轨道目录"
与 A2 立下的先例(`cold-start-a2/README.md`:"Reuse is read-only")。

### 可以原样调用的(只写我传进去的路径)

| 函数 | 签名 |
|---|---|
| `world.explorer.explore(spec)` | → `(states, actions)`,无 RNG,`min(pool)` 打破平局,字节可复现 |
| `world.explorer.coverage_report(spec, states, actions)` | → dict |
| `world.ground_truth.write_trace(path, world, states, actions)` | 路径显式 |
| `world.ground_truth.read_trace(path)` | → `(frames, actions, wins)` |
| `pipeline.engines_stage.run_stage(trace_path, out_path, report_path, timestamp=)` | **三条路径全显式** |
| `compile.problem.derive(trace_path, name, name_by_color=)` | 纯函数,**不写盘**,返回 `Problem` |
| `compile.compile_a0.compile_theory(dsl, trace, problem_name, out_dir)` | 只写 `out_dir` |
| `certify.replay.certify(theory_py, trace_path)` | 返回 dict,**不写盘** |
| `certify.lean_check.check(lean_file)` | 返回 dict,不写盘(本臂不调) |
| `pipeline.unsolvable_variant.recovered_region(trace_path)` | 纯函数 |

### 不能原样调用的(无条件写回母体)

- 八个 staged 模块的 `main()`
- **`pipeline.plan_stage.run_plan(...)`** —— `_write(report)` 在 SAT/UNSAT 两条分支上都无条件执行,
  `report_name` 只改文件名不改目录。必须先 monkeypatch `plan_stage._write`(或重写那 ~40 行)。
  `out_path=None` 只压住 candidates 那一半。
- `unsolvable_variant.compile_variant()` / `.main()` —— 模块级常量写死
- `certify.score_vs_truth.main()` —— 写死;但 `behavioural()` / `held_out()` 可直接调

## 2 · 证明义务的真实开关在哪(与直觉不同)

**删掉 DSL 的 `laws:` 段并不会少掉任何一条 Lean 定理。** 全仓 grep `ast.laws` 在 A0 只命中
`unsolvable_variant.py:197`、`concept_account.py`、`tests/`。`gen_lean_a0.generate_lean` 签名里
收了 `ast` 但函数体从不引用它——不变量是在 Python 里合成的
(`door_latch_invariant(axes)` / `weight_invariant(region, ...)`,后者的 `region` 来自 **zero_space 引擎**,
不来自手册)。

⇒ 证明义务的开关只有三个,按咬合力排序:

1. **完全不调 `generate_lean`** —— 连带砍掉 `ArenaEscape`(手册的 step 逃出自己声明的状态空间,
   这一检查只在 Lean 生成期发火,廉价层看不见)与 `lean_check`。**本臂取这一档。**
2. `generate_lean(..., unsolvable=False)` —— 只去掉 `goal_break`/`unsolvable`,留 `inv_init/inv_closed/inv_all`。
3. `invariant_builder=lambda axes: ("true", ...)` —— 证明还在,但断言变空。

第 2、3 档是**半刀**,会留下"有证明但不证不可解"的中间态,归因不干净。取第 1 档,并在
DESIGN.md 里记下 `ArenaEscape` 是刀口的**第三道影子**(前两道:定向戳探、依赖重证)。

⚠ 副作用登记:`unsolvable_variant.py:197` 读 `ast.laws.theorems[0]`。本臂的 DSL 若删 `laws:` 段
会炸——但本臂本来就不调该模块的 main。DSL 里 `laws:` 段的处置见 DESIGN.md(倾向:**保留 invariant
作为经验级条目、删 theorem**,以体现"降级"而非"消失",且 `theory.md` 渲染要照实标注无证明)。

## 3 · 廉价层到底查什么(这是本臂全留的部分)

`certify/replay.py::certify` 四查:

1. **转移重放** —— `theory.step(state, ACTION_NAMES[action])`
2. **渲染一致性** —— 逐格 `theory.render(state)[r][c] != frame[r][c]` → `render_mismatch`
3. **全帧责任制** —— `theory.responsibility(state)` → `contested_pixel` / `unowned_pixel`
4. **终点一致** —— `theory.is_goal(state) != wins[t]` → `goal_mismatch`

外加 `AmbiguousTransition` → `ambiguous_transition` 并 break。

**注意:廉价层没有"精确度"这个连续量,只有二元 `green = not anomalies`。** 唯一的连续信号是
`pixels_unexplained / pixels_checked`。比值形式的精确度住在 `score_vs_truth`(见 §4)。
标定报告要照此口径,不许自造一个"重放精确度"。

约束 9 的执行位置值得记一笔:`AmbiguousTransition` 是**运行期**捕获,而"恰一后继"的**证明**
在昂贵层。⇒ 消融后,无歧义从"定理"降为"运行时碰巧没撞上"——这正是约束 9 那句
"桌游的'以第 X 条为准'升级为证明义务"的逆操作。

## 4 · 全量臂的既有数字(本臂要并排坐的那一列)

`artifacts/score_vs_truth.json`:

| | reachable_states | pairs | agree | disagree | accuracy |
|---|---|---|---|---|---|
| base · behavioural | 59 | 236 | 233 | 3 | **0.987288** |
| base · held_out | — | 3 | 0 | 3 | **0.0** |
| variant · behavioural | 23 | 92 | 92 | 0 | **1.0** |

`artifacts/certify_cheap_raw_trace.json`:`frames 276`,`transitions 275`,`pixels_checked 22356`,
`pixels_unexplained 0`,`anomalies []`,**`green true`**。

比较口径:`behavioural` 是对每个(可达态 × 动作)穷举,比的是**渲染帧相等**
(`world.render(next) == theory.render(next)`),不是状态相等。`held_out` 是其中轨迹从未包含的那些对。

## 5 · A0 变体是**真**不可解 —— 判决题第 (i) 类,本臂的第一个标定点

`artifacts/unsolvable_report.json` 的 `constructive_ground`:

> the Door is the only opening in the dividing wall, and the only rule that removes it
> (`door_opens_left`) tests for the Button's colour; with no Button in the instance that guard
> can never hold, so the goal room is unreachable by construction

全量臂在这一关的 plan 报告里留了一行**正是本臂要停在的地方**:

```json
"status": "UNSAT",
"note": "no plan exists under this manual — constraint 6 forbids stopping here; a certificate is owed"
```

配套 `certify_lean`:`available true`,`axiom_reports [{"axioms": [], "name": "unsolvable"}]`,`green true`。

⇒ **A0 上消融臂给出的判决与全量臂逐字相同(UNSAT / 不可解),而且是对的。**
这不是本臂的失败,恰恰是它最重要的那一半证词——对上 `Theoria.md:259` 判决题第 (i) 类:

> 小空间不可解——穷举可行,连 Schema 的完备搜索都会正确地停,**甚至可能因漏边而以错误的理由
> 得到正确的判决**,所以这里考的是理由:证书,还是"我搜过了没有"。

A0 的证词是:**判决相同,理由蒸发**。它证明了在判决层面上度量根本分不开这两个臂——
必须去看证书。A2 的证词才是"判决也不同"。两关合起来才是完整的消融结论,少一关都不够。

## 6 · 确定性与杂项

- `THEORIA_DETERMINISTIC_IDS=1` / `THEORIA_FIXED_TIME` 全仓**只被 `engine-rig/common/candidates.py` 读**,
  只影响 `candidates.jsonl` 的 `id` 与 `timestamp` 字节。其余路径无 RNG。
- `run_stage` / `run_plan` 另收显式 `timestamp=` kwarg,逐条覆盖。
- `plan_stage.main()` **不**设这两个变量;本臂自己设,别依赖母体。
- `_bootstrap.py` 把 `engine-rig` 与 `theory-compiler/src` 插进 `sys.path`。本臂要写自己的同款,
  外加把 `cold-start-a0` 自身插进去(以便 `import world.explorer` 等)。
- 轨迹行格式:`{"t","frame","action","win"}`,`sort_keys=True, separators=(",",":")`, LF。
- A0 世界:9×9,`State = (cart, pressed)`,59 个可达态;按钮闩锁不可逆;
  **按下按钮与开门是同一次转移**(D-A0-004),小车按按钮时不移动。
