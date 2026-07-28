# b4 — cold-start-a0（盲判，12 个入口）

判定员未见任何探针输出（树里无 `verify-lab/`）。全部 `读码`。

| 入口 | 能红 | 有负控 | 退出码诚实 | 证据强度 | 证据 |
|---|---|---|---|---|---|
| cold-start-a0/certify/lean_check.py | 是 | 是 | 是 | 读码 | `:127` `return 0 if report["green"] else 1`，`:131` `raise SystemExit(main())`；`:96-102` green 要求 returncode==0 ∧ 无 error ∧ 无 sorry ∧ axiom_reports 非空且全空。负控：`tests/test_a2_reported_defects.py:161` 与 `:190` monkeypatch `subprocess.run` 喂进真实 Lean 错误字节，断言 `not report["green"]`；`:205` 是配对正控。注：负控打的是 `check()` 不是 `main()`，但判决函数就是这一份实现 |
| cold-start-a0/certify/replay.py | 是 | 是 | 是 | 读码 | `:137` `return 0 if report["green"] else 1`；`:119` 打印 `RED    %d anomalies`。负控最强：`tests/test_a0.py:244-281` `test_mutants_are_caught`，四个预注册变异体（drop_door_rule / drop_press_rule / break_teleport / drop_door_object）改写 `theory.py` 源码后 `assert not report["green"]` 且断言具体 anomaly 种类 |
| cold-start-a0/compile/compile_a0.py | 部分 | 否 | 否 | 读码 | `:120` `main` 无条件 `return 0`；只有向上冒的异常能红（`:44-45`）。ArenaEscape 被 `:68-70` 吞成 `written["theory.lean.error"]=<str>`，随后 `:119` 的 `%6d` 对该字符串键会 TypeError —— 唯一的非零是格式化崩溃，不是设计的判决。全树无任何测试调用 `compile_theory`/`main` |
| cold-start-a0/compile/dialect.py | 是 | 是 | 不适用 | 读码 | 不是验收闸：无 `main`、无 `__main__`、无 `sys.exit`，是库模块；红靠 `SemanticsError` 冒到调用方（`compile_a0.py:45`、`unsolvable_variant.py:120`）。抛点 `:155,174,185,189,195,198,204,216,219,225`。负控充分：`tests/test_followups.py:55` 缺 semantics 段 `pytest.raises(SemanticsError)`；`:68-79` 五个坏值参数化；`:82-89` `check_backend_support` 三个不支持组合 |
| cold-start-a0/compile/problem.py | 部分 | 否 | 部分 | 读码 | `:160` `main` 无条件 `return 0`；只有异常能红（`:81` 缺 trace、`:109` StopIteration）。派生失败静默降级：`:111-112` 赢家格不唯一则 `goal_cell` 留 None、`:125-126` 跳跃不唯一则不写 `portal_exit`，`:157-159` 照样打印 `goal= None` 并退 0。负控：`tests/test_a0.py:307` 只在绿的一侧调 `problem_mod.derive` |
| cold-start-a0/pipeline/concept_account.py | 部分 | 否 | 否 | 读码 | `:268` `main` 无条件 `return 0`；只有异常能红。判决被算出来又被打印却不进退出码：`:86-88` `verdict` 取 mandatory/pays/rejected，`:261-264` 打印 verdict 列并写入 `concept_accounts.json`。负控：`tests/test_followups.py:105` 与 `:118` 只调 `accounts()` 断言数值，且断言的是绿侧 |
| cold-start-a0/pipeline/engines_stage.py | 是 | 否 | 否 | 读码 | 能红：`:141` `raise AssertionError("a recovered law does not hold on the trajectory")`，在 `run_stage` 内、无人接。但 `:390` `main` 恒 `return 0`：`:209-215` 算出的 `mutually_exclusive` / `explains_every_transition` 可为 False，`:383-384` 打印后照样退 0。负控：`tests/test_a0.py:149-161` 把互斥/全覆盖断言重算了一遍，但走 `multi_miner` 直调，不是这个文件的 `run_stage` |
| cold-start-a0/pipeline/plan_stage.py | 是 | 否 | 部分 | 读码 | `:146` `return 0 if report.get("green") or report["status"] == "UNSAT" else 1`；另有 `:47` `raise ValueError` 与 `:65` RuntimeError。SAT 侧诚实；UNSAT 侧退 0 —— `:75-76` 自己写下「a certificate is owed」却不进退出码。负控：`tests/test_a0.py:323` 只读 `plan_generated.json` 断言 SAT/green |
| cold-start-a0/pipeline/unsolvable_variant.py | 是 | 否 | 是 | 读码 | `:217` `return 0 if report["green"] else 1`，`:214` 打印 `M5    : RED`；另有 `:85`、`:98` 两处 `raise AssertionError`。负控无：`tests/test_a0.py:335` 只读绿侧；`:345` `test_the_variant_really_is_unsolvable` 打的是另一份实现（`world/a0_world.py` 直接枚举可达态） |
| cold-start-a0/prime/run_prime.py | 部分 | 否 | 否 | 读码 | 最硬的一条：`:212` `main` 无条件 `return 0`，而 `:190` 打印 `cheap : RED`、`:191` 打印 `lean : RED`。`:91` `os.system(...)` 的返回码被丢弃，M1 失败要等到 `:93` `json.load` 缺文件才炸。负控：`tests/test_followups.py:184,198,211` 全是读 `prime_report.json` 的绿侧断言 |
| cold-start-a0/prime/world/ground_truth.py | 部分 | 否 | 不适用 | 读码 | 不是验收闸：A0′ 的 trace/裁判真值写手，全文无判决计算（`:100-135` `main` 只写四份产物），`:135` 恒 `return 0`。全树无 test 触碰本文件 |
| cold-start-a0/world/ground_truth.py | 部分 | 否 | 不适用 | 读码 | 不是验收闸：同上，`:184-209` `main` 恒 `return 0`，无 raise、无 sys.exit。`tests/test_a0.py:101` `test_trace_is_byte_stable` 用到本文件的 `write_trace`，但那是绿侧字节复现断言，不算负控 |

判定员附注：

1. 三个 `是/是/是` 的入口只有 `replay.py` 和 `lean_check.py` —— A0 唯一真正被演示过会红的两处。
2. 最不确定的一格是 `plan_stage.py` 的「退出码诚实」：UNSAT 退 0 是写在注释里的设计
   （义务转交 M5），按保守侧判 `部分`。
3. `compile_a0.py` 的 ArenaEscape 分支是读码判定会 TypeError，未执行验证；
   复核时这是最值得先跑的一行。
4. `concept_account.py` 的「退出码不诚实」也可辩为「它是报表生成器不是闸」，
   仍按判据原文判 `否`。
5. 两个 `ground_truth.py` 与 `dialect.py` 的 `不适用` 已在证据列写明理由；
   `dialect.py` 虽非闸，负控质量却是全批最高的。
