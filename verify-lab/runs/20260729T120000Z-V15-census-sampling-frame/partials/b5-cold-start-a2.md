# b5 — cold-start-a2 + a0-spike（盲判，13 个入口）

判定员未见任何探针输出（树里无 `verify-lab/`）。全部 `读码`。

| 入口 | 能红 | 有负控 | 退出码诚实 | 证据强度 | 证据 |
|---|---|---|---|---|---|
| a0-spike/pipeline/gen_exec.py | 是 | 是 | 不适用 | 读码 | 库模块，无 `__main__`；`raise UncompilableTheory` 遍布 `:68/:77/:105/:110/:122/:129/:136/:157/:178/:190/:313`，生成码 `step` 再 `raise RuntimeError` `:273/:278`。负控四组、全是坏输入断言失败：`a0-spike/tests/test_a0.py:203-210`（把 `free(...)` 改成 `sparkles(...)`）、`:235-258`（三个 `semantics` 变异体参数化，`:252` 还有「变异必须真的生效」的非空洞断言）、`:261-283`（剥掉 `blocked_*` 规则 → `pytest.raises(RuntimeError, match="no rule fired")`）、`:286-308`（复制一条规则 → `match="conflict exclusive violated"`） |
| cold-start-a2/a2pipeline/certify_a2.py | 是 | 部分 | 是 | 读码 | `:153` `return 0 if cheap_report["green"] and lean_report.get("green") else 1`，`:143` 打印 `RED` 与之同步。负控只打到函数不打到进程：`repair.py:89-129` 造了故意红的 `theory/generated_repaired_stale/theory.lean` 并喂给本文件的 `lean()`，`tests/test_a2.py:275-279` 断言 `died is True` / `lean.green is False`；但全树无一处演示 `certify_a2.main()` 返回 1。`ablation-arm/ablcore/certify_abl.py` 是另一份实现，不算 |
| cold-start-a2/a2pipeline/compile_a2.py | 部分 | 否 | 不适用 | 读码 | `main()` `:211-219` 无条件 `return 0`；两处 `raise AssertionError` 在 `:92`/`:105`，但只在 `observed_region()` 里，而 `main→compile_control` 从不调用它。全树零测试 import `a2pipeline.compile_a2`；`ablation-arm/ablcore/compile_abl.py:65` 自述是本文件的 copy，`ablation-arm/tests/test_exhibits.py:100-107` 打的是那份副本 |
| cold-start-a2/a2pipeline/concepts.py | 部分 | 否 | 否 | 读码 | `main()` `:96-123` 无条件 `return 0`。`:92` `"missing": sorted(...)`，`:121-122` 打印 `pinned %d ... %d missing`，然后 `:123 return 0` —— 判决只落进 `upstream_pin.json`。唯一的检查 `tests/test_a2.py:372-375` 断言 `missing == []`，是绿的一侧 |
| cold-start-a2/a2pipeline/engines.py | 部分 | 否 | 否 | 读码 | `main()` `:76-139` 无条件 `return 0`，`:142 raise SystemExit(main())`。`:117-135` 的 `verdict`（`history_proposes_a_jump` 等）被算出、`:138` 被打印、`:136-137` 写进 `engines_diff.json`，退出仍 0。**负控打的是别处**：全树 `test_*.py` 无一处 import/调用 `a2pipeline.engines`；`engine-rig/tests/test_{cegis_miner,zero_space,mdl_segmenter,probe_frontier}.py` 打的是本文件下面两层的引擎库，`cold-start-a0/pipeline/engines_stage.py` 与 `cold-start-a3/a3pipeline/engines.py` 是同功能的另外两份包装 —— 都不是这个文件 |
| cold-start-a2/a2pipeline/exhibit.py | 是 | 部分 | 是 | 读码 | `:172-173` `return 0 if (exhibit_green and exhibit_is_false_of_the_world) else 1`，`:167` 打印 `GREEN/RED`。负控真但落在 certify 层：`theory_holed.dsl` 是预注册变异体（`tests/test_a2.py:142-146` 钉住），`:96-110` 拿它去打全扫描，`tests/test_a2.py:186-190` 断言 `certify_cheap_vs_full_sweep["green"] is False`。但无一处演示 exhibit.py 自身非零退出 |
| cold-start-a2/a2pipeline/ledger.py | 是 | 否 | 是 | 读码 | `:215` `return 0 if ledger["green"] else 1`；`:57-58` 缺产物记 `absent`、不通过记 `FAIL`，`:201` `green = all(s == "pass")`。无负控：`tests/test_a2.py:314-318` 只断言 `fail == 0` / `absent == 0` / `green is True`；`ablation-arm/ablcore/ledger_abl.py` 是另一份实现 |
| cold-start-a2/a2pipeline/locate.py | 是 | 是 | 部分 | 读码 | `:208` `return 0 if report["culprits"] else 1`。**本批唯一被真负控打到的 a2 文件**：`ablation-arm/exhibits/e3_charitable.py:151` 直接 `from a2pipeline.locate import locate`（同一份实现，非副本），`:152-160` 喂两个逆向输入，`ablation-arm/tests/test_exhibits.py:125-126` 断言 `locate_raised is not None` 且含 `portal_exit`，`:128-130` 断言健康手册上 `culprits == []`。退出码判部分：找到缺陷退 0、找不到退 1 —— 对它自己的契约诚实，对「按退出码读健康度」的调用方是反的 |
| cold-start-a2/a2pipeline/plan.py | 是 | 否 | 部分 | 读码 | `:151` `return 0 if report.get("green") or report["status"] == "UNSAT" else 1`；`:51` `raise ValueError`。SAT 分支诚实；UNSAT 分支无条件 0，即使 `:86-87` 自己写着「a certificate is owed」。无负控：全树零测试 import 本文件；`ablation-arm/ablcore/plan_abl.py:35` 自述是本文件的 rewrite |
| cold-start-a2/a2pipeline/probe.py | 是 | 否 | 否 | 读码 | `:165-166` `raise AssertionError` 冒到顶层；`:364` `return 0 if summary["run"] >= 1 else 1`。不诚实处：`:180` `"status": "unreachable"` 与 `:192` `"status": "execution_mismatch"`（注释自称 "an anomaly in its own right"）都被 `:358-361` 打印并写进 `probe_report.json`，只要有一个探针跑过就仍退 0。无负控：`tests/test_a2.py:247-265` 全是绿侧断言 |
| cold-start-a2/a2pipeline/refute.py | 是 | 否 | 是 | 读码 | `:120` `return 0 if report["refuted"] else 1`，`:119` `print("verdict: NOT refuted")` 与之同步；`:46-48` `raise AssertionError` 冒顶。无负控：`tests/test_a2.py:223-227` 只断言绿侧 |
| cold-start-a2/a2pipeline/repair.py | 是 | 部分 | 是 | 读码 | `:270` `return 0 if report["green"] else 1`，`:269` 打印 `REPAIR: RED`；`:233-240` 的 green 把 `stale_certificate.died` 列为必要条件。负控内嵌：`:89-129 reprove_stale()` 每次运行都生成一个必须变红的证书，`:195-196` 打印 `"STILL GREEN — that would be a bug"`，`tests/test_a2.py:275-279` 断言它确实死了；但无一处演示 repair.py 本身非零退出 |
| cold-start-a2/a2world/ground_truth.py | 部分 | 否 | 否 | 读码 | `main()` `:221-269` 无条件 `return 0`。`:247-250` 算出 `history_omits_exactly_one_pair` 这个判决只写进 `trace_summary.json`，既不打印也不进退出码。`tests/test_a2.py:117-121` 是绿侧断言 |

判定员附注：

1. **`engines.py` 的专项结论：打的是别处，且不止一处别处。** 全树没有任何 `test_*.py`
   import 或调用 `cold-start-a2/a2pipeline/engines.py`。看似相关的三类测试分别打的是：
   下面两层的引擎库、`cold-start-a0/pipeline/engines_stage.py`（本文件 `:31` 导入并复用的上游副本）、
   `cold-start-a3/a3pipeline/engines.py`（第三份同功能包装）。按判据一律不算，故判 `否`。
2. 同一个陷阱不止一个：`ablation-arm/ablcore/` 里 `certify_abl.py` / `compile_abl.py` /
   `plan_abl.py` / `ledger_abl.py` 都是 A2 对应文件的第二份实现（源码自述 copy/rewrite）。
   唯一穿透到 A2 本体的是 `locate` —— 没有 `locate_abl`。
3. **`cold-start-a2/tests/test_a2.py` 401 行里没有一行 import `a2pipeline`。**
   它整个是产物读取器，产物缺失时 `pytest.skip`。
4. 两个真实的坏 fixture 值得记名（可执行，不是散文）：`theory/theory_holed.dsl` 与
   `theory/generated_repaired_stale/`。它们打的都是 certify 层，据此给
   `certify_a2.py` / `exhibit.py` / `repair.py` 判 `部分` 而非 `否`。
5. 两格判在保守侧：`locate.py` 的退出码极性；`gen_exec.py` 的「能红」
   （无 `__main__` 的库，异常冒到调用方顶层）。
