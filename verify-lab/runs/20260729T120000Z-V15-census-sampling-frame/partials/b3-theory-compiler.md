# b3 — theory-compiler（盲判，13 个入口）

判定员未见任何探针输出（树里无 `verify-lab/`）。全部 `读码`。
后 10 个是库模块（无 `__main__`，靠抛自定义异常拒绝）。

| 入口 | 能红 | 有负控 | 退出码诚实 | 证据强度 | 证据 |
|---|---|---|---|---|---|
| theory-compiler/runs/20260728T080019Z-C4-deadlock-lean/spike_encoding.py | 部分 | 否 | 否 | 读码 | 全文无 `sys.exit`/`raise`；唯一非零路径是模块级 `strips.load_task`（`:26-27`）读 fixture 失败时 `StripsError` 冒到顶层。判决路径 `:93` 打印 `WF COUNTEREXAMPLE`、`:102-103` 打印 `closure breaks: wf %d`，进程仍退 0。全树零 `test_*.py` 命中 |
| theory-compiler/runs/20260728T102343Z-c7/compat/probe.py | 部分 | 否 | 否 | 读码 | 编译失败全被吞进 JSON：`:84-86 entry["fatal"]`、`:101-102 entry["conflict_error"]`、`:108-111 {"status":"ERROR",...}`；`main()` 返回 `None`，`:132-133` 直接调用，无 `sys.exit`。同目录**另一份实现** `compat/a2fam-driver.py:35` 对同一条 provenance 用 `assert`，本文件只写字段。全树无任何 `test_*.py`/`verify.sh` 引用 |
| theory-compiler/runs/20260728T102343Z-c7/make_sokoban2_problems.py | 部分 | 否 | 不适用 | 读码 | 无 `sys.exit`/`raise`；非零只来自 `:21` ImportError 或 `:48` 写盘失败。不计算也不打印任何判决 |
| theory-compiler/src/theory_compiler/conflict.py | 是 | 是 | 不适用（库） | 读码 | `ConflictError:98`，冒顶 raise 在 `:555 :607 :749 :773 :813 :837`；经 `ir.build_ir` 到 `tools/probe_mentions.py:39` 与 `runs/…c7/verify.sh:26`，二者均能非零。负控：`tests/test_conflict.py:69,230,260,270,399` 五处 `pytest.raises(ConflictError)` |
| theory-compiler/src/theory_compiler/generators/gen_lean.py | 是 | 是 | 不适用（库） | 读码 | `LeanGenError:80` / `CertificateGapError:84`，raise 站点 21 处；顶层入口 `tools/verify_c4.py:36`。负控：`tests/test_gen_lean.py:157,327,341`、`tests/test_ic3_certificate.py:192,200,207` |
| theory-compiler/src/theory_compiler/generators/gen_lean_deadlock.py | 是 | 是 | 不适用（库） | 读码 | `DeadlockLeanError:71`，24 处 raise（含自检 `reread`）。负控两层：`tests/test_gen_lean_deadlock.py:162,211,218,226`，以及 `tools/verify_c4.py:110-121` 的**重生成负控**——把 pattern 挪到非死区后必须被 `dc.recheck` 拒绝，否则 `raise SystemExit` |
| theory-compiler/src/theory_compiler/generators/gen_python.py | 是 | 是 | 不适用（库） | 读码 | `UnsupportedClause:57`，约 35 处 raise。负控最强：`tests/test_gen_python.py:140`、`tests/test_count_guard.py:129,165`、`tests/test_writes.py:248`，外加 `verify.sh:72-84` 的**预注册期望失败**（a0-spike 手册必须被拒，否则 `bad+=1`→`sys.exit(1)`） |
| theory-compiler/src/theory_compiler/ir.py | 是 | 是 | 不适用（库） | 读码 | `IRError:36`，raise `:85 :92 :234 :245 :252 :292 :294 :309 :318`。负控：`tests/test_weight_injection.py:102,121,123,138,148`、`tests/test_gen_lean.py:171`（权重与证书不符 → `IRError`，断言消息含 `stale`） |
| theory-compiler/src/theory_compiler/parser/playbook_parser.py | 是 | 是 | 不适用（库） | 读码 | `PlaybookParseError:15`，raise `:38 :75 :86 :94 :101 :110`。负控：`tests/test_playbook_parser.py:81,90,96`，含**故意做坏的 fixture** `tests/fixtures/playbook_violation.dsl`。`battery/adapters/a0.py:205` 的同名 `parse_playbook` 是另一份实现，未计入 |
| theory-compiler/src/theory_compiler/parser/theory_parser.py | 是 | 是 | 不适用（库） | 读码 | `ParseError:25` / `SemanticsError:31`，约 30 处 raise。负控：`tests/test_theory_parser.py:245,250,255,260,293`、`tests/test_writes.py:79,91`。缺口：`SemanticsError` 的 7 处 raise 全树无任何断言，只有父类被打到 |
| theory-compiler/src/theory_compiler/problem.py | 是 | 否 | 不适用（库） | 读码 | `ProblemError:42`，raise `:109 :122 :170 :196`。**无负控**：全树唯一提及是 `tests/test_gen_python.py:17` 的 `import ProblemError`，函数体内一次都没用；四条错误消息片段在 `test_*.py`/`verify.sh`/fixtures 零命中。`tests/test_count_guard.py:110-112` 的注释明说要**绕开** `check_against_theory` 的拒绝 |
| theory-compiler/src/theory_compiler/strips.py | 是 | 是 | 不适用（库） | 读码 | `StripsError:36`，约 45 处 raise。负控：`tests/test_strips.py:106,113,120,127,134,141,151,159,170` 九处 `pytest.raises(StripsError)`，构造坏 PDDL 文本 |
| theory-compiler/src/theory_compiler/strips_encoding.py | 是 | 部分 | 不适用（库） | 读码 | `EncodingError(StripsError):57`，14 处 raise；`verify():250-283` 逐 (state, action) 比对并在不符时 raise。负控只有一处且只打到构造器：`tests/test_deadlock_certificate.py:309-318`；`verify()` 自身那条「编码与任务不符必须红」的路径全树无任何测试或坏 fixture 演示过 |

判定员附注：

1. 后 10 个库模块的「退出码诚实」一律 `不适用（库）`：它们不 print 判决、不设退出码，
   判决只走 raise；本仓库所有顶层调用者（`tools/*.py` 均 `raise SystemExit(main())`，
   `runs/…c7/verify.sh` 用 `set -eu`）都会把 raise 转成非零。
2. 三个脚本入口的「能红」全判 `部分`：没有自己的 `sys.exit(非零)`，非零只来自
   缺文件/缺依赖/argparse，判决路径本身永远退 0。
3. 最弱的两格：`problem.py` 的四条 `ProblemError` 零负控（连导入了都没用），
   `strips_encoding.verify()` 的核心比对路径零负控。
4. `compat/probe.py` 是本批最典型的「算出来又吞掉」。
5. `theory_parser.py` 判 `是` 是就 `ParseError` 整体而言；其 `SemanticsError` 分支实为零覆盖，
   若按子类粒度应判 `部分`。
