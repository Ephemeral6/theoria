# V11 负控普查 —— 全仓总表

六份分表的机械归并。每一行都出自某份分表；未答的格子填 `—`，不作补全、不作裁决。
分表：`partials/engine-rig-theory-compiler.md`、`exam-battery.md`、`worldgen-fuzzlab.md`、
`figures-release.md`、`proxy-arcrecon.md`、`arms.md`。

---

## 第 1 节：全仓总表

| 领地 | 入口 | 能红 | 有负控 | 退出码诚实 | 证据强度 | 证据 |
|---|---|---|---|---|---|---|
| engine-rig/theory-compiler | `engine-rig/tools/validate_candidates.py` | 是(实测) | 是(读码) | 是(实测) | 混合 | 坏行文件 → `FAIL ... (1 rows, 7 errors)` exit 1；`artifacts/candidates.jsonl` → `OK (44 rows)` exit 0。负控 `engine-rig/tests/test_integration.py:259-286`（14 例变异行）+ `:289`（坏 JSON/空行） |
| engine-rig/theory-compiler | `engine-rig/tools/run_all.py` | 是(读码) | 部分(读码) | 是(实测/读码) | 混合 | 实测写 scratch → exit 0；已存在文件不加 `--force` → `refusing to append` exit 2。`run_all.py:260-264` schema 失败 `return 1`，`:117/:144/:155/:174` `raise RuntimeError`。负控只覆盖被调用的 validator，无测试让 run_all 自己走 exit 1 |
| engine-rig/theory-compiler | `engine-rig/bench/__main__.py`（`python -m bench`） | 是(读码) | 部分(读码) | 是(读码) | 读码 | `bench/__main__.py:162-166` `problems` 非空 → `return 1`。负控只到上游 `tests/test_bench.py:322/331/339`（钉 `ladder.verdicts` 三个 False）；喂给退出码的 `bench/ladder.py:237 failures()` 与 `bench/dividend.py:290 failures()` 全仓无测试。本机无 FD，未实跑 |
| engine-rig/theory-compiler | `engine-rig/bench/verify.py` | 是(实测) | 否 | 是(实测) | 实测 | 实测：`LADDER.md` 尾部加一行 → `FAIL (1): ... sha256 cc037bce... manifest says 95b1aa49...` exit 1；未篡改的 `engine-rig/runs/20260728T072633Z-E2-fd-ladder-bench` → exit 0。负控：`grep -rn "bench.verify\|check_manifest_hashes\|rederive" engine-rig/tests` 零命中 |
| engine-rig/theory-compiler | `engine-rig/tools/p13_fd_dividend.py` | 部分(实测) | 否 | 否(读码) | 混合 | 实测：无 FD → `no Fast Downward reachable` exit 2。`p13_fd_dividend.py:448-471` 除此之外无条件 `return 0`；`same_answer`(:317) / `agree`(:368) 为 False 时只渲染成 `**NO**`(:404,:444) |
| engine-rig/theory-compiler | `engine-rig` `python -m pytest`（150+ 例） | 是(读码) | 是(实测) | 是(实测) | 混合 | 实测 exit 0，9 skipped。负控：`engine-rig/tests/test_fd_ladder.py:59-96` 假 FD（`FAKE_FD_MODE` = exhausted/structurally_unsat/translate_unsat/incomplete/crash）为预注册变异体，`:267-330` 六例断言每种坏行为必须被识别或硬报错 |
| engine-rig/theory-compiler | `engine-rig/fixtures/generate_all.py`（+cart_world/pair_flip/peg4/sokoban） | 否(读码) | 不适用 | 不适用 | 读码 | `generate_all.py:8-20` `main()` 无条件 `return 0`，全文件无 assert/raise。字节稳定断言实际在 `engine-rig/tests/test_fixtures.py:23-41` |
| engine-rig/theory-compiler | `theory-compiler/tools/verify_c4.py` | 是(读码) | 是(实测) | 是(读码) | 混合 | 实测 `--quick` → 三项 OK exit 0。内建负控 `control_source()`(:93-122) 把死区图样平移一格重新生成整份开发，观察到 `Control_pair.lean:442` Lean 报 `tactic 'decide' proved that the proposition ... is false`，`report["ok"]` 与该拒绝相与(:170-171)。`:240` `return 0 if all_ok else 1`，`:213` 无 lean → 2 |
| engine-rig/theory-compiler | `theory-compiler/tools/verify_c8.py` | 是(读码) | 部分(读码) | 是(读码) | 读码 | 实测 14 项全 PASS exit 0（含 pytest 363 passed、两个包字节复算、两份答卷 24/24 与 29/29）。`:127-131` `_failures` 非空 → `return 1`。子检查负控散在 `theory-compiler/tests/test_handover.py:199/208/230`；第 5-6 项依赖的 `handover_exam` 无测试 |
| engine-rig/theory-compiler | `theory-compiler/runs/20260728T102343Z-c7/verify.sh` | 是(读码) | 是(实测) | 是(读码) | 混合 | `set -eu` + 第 3 段 heredoc `sys.exit(1 if bad else 0)`。实测逐段：pytest exit 0；`probe_mentions` 7 行 ok exit 0；第 3 段 10 份说明书全编译 + 负控 `a0-spike/theory/theory.dsl` `refused as expected: expected a direction from [...]` exit 0。负控是脚本自带的（`:72-83`：该说明书必须编译失败，否则 `bad += 1`） |
| engine-rig/theory-compiler | `theory-compiler/tools/probe_mentions.py` | 是(读码) | 是(读码) | 是(读码) | 读码 | 实测 exit 0，7 行 ok。负控为预注册期望值：`EXPECTATIONS` 里 `sokoban2_x5 / first_argument / off_wall` 期望 376 次误判、`declared / on_wall` 期望 52 次 —— 坏读法若不再误判就红。`:404-408` 失败 `return 1`；`:356-360` 缺 ground truth 打印 `SKIP:` 并 `return 77` |
| engine-rig/theory-compiler | `theory-compiler/tools/validate_candidates_v02.py` | 是(实测) | 是(读码) | 是(实测) | 混合 | 实测：坏行 → `FAIL (candidates_schema@0.2, 1 row(s) read)` exit 1；`engine-rig/artifacts/candidates.jsonl` → `OK` exit 0；`--nope` → `unknown option(s)` exit 2（`:289-299` 明写「拼错的 flag 不得静默降级为宽松通过」）。负控 `theory-compiler/tests/test_validate_candidates_v02.py` |
| engine-rig/theory-compiler | `theory-compiler/tools/refresh_manifest.py --check` | 是(实测) | 否 | 是(实测) | 实测 | 实测：树里全部 5 个 run 的 MANIFEST 现在都是红的 —— `theory-compiler/runs/20260728T102343Z-c7`（4 处真实 sha256 不符）、`C8-handover-package`、`C9-count-lock-vocabulary`、`C4-deadlock-lean`、`runs/P-10` 一律 exit 1。无任何测试导入本模块 |
| engine-rig/theory-compiler | `theory-compiler/tools/transcribe_deadlock_certificates.py` | 是(读码) | 是(读码) | 是(读码) | 读码 | `:120-122` `return 1 if drifted else 0`，`:91` 缺行 `raise SystemExit`。实测 check 模式 exit 0。负控 `theory-compiler/tests/test_deadlock_certificate.py` 重跑同一转写并比对已提交 fixture |
| engine-rig/theory-compiler | `theory-compiler/tools/build_handover_packages.py --check` | 是(读码) | 部分(读码) | 是(读码) | 读码 | `:172` `return 1 if failures else 0`。实测 `ok a0-cart (17 files) / ok a0-sokoban2 (15 files)` exit 0。`theory-compiler/tests/test_handover.py:40/47/56` 只从绿的一侧比对，无物演示 `--check` 的 FAIL 分支 |
| engine-rig/theory-compiler | `theory-compiler/tools/handover_exam.py mark` | 是(实测) | 否 | 是(实测) | 实测 | 实测：`a0-cart.answers.json` 一个答案改成 `ZZZ-nonsense` → `a0-cart: 23/24 right ... name-action_vocabulary unparsed` exit 1（`:707` `return 0 if right == items else 1`）。`grep -rn "handover_exam" theory-compiler/tests` 零命中 |
| engine-rig/theory-compiler | `theory-compiler` `python -m pytest`（364 例） | 是(读码) | 是(实测) | 是(实测) | 混合 | 实测 exit 0，364 passed 1 skipped（lean 在场，Lean 编译真跑了 100s）。负控：`theory-compiler/tests/test_gen_lean_deadlock.py:140-175` `TestEmissionIsRead` 四个预注册变异体各须让发射器抛 `DeadlockLeanError`；`tests/test_conflict.py:386` 自称「负对照：这道检查必须有能力失败」 |
| engine-rig/theory-compiler | `theory-compiler/conftest.py`（`THEORIA_REQUIRE_LEAN=1`） | 是(读码) | 否 | 是(读码) | 读码 | `:30-56` 置 1 且无 lean → `raise pytest.UsageError`（pytest exit 4）。防「闸门静默跳过」的元闸门。实测本机 lean 在场 → 364 passed exit 0 |
| engine-rig/theory-compiler | `theory-compiler/tools/build_deadlock_lean.py` | 是(读码) | 部分(读码) | 是(读码) | 读码 | 生成器不是闸门：`:72` 无条件 `return 0`，坏证书靠 `CertificateError` 冒到顶层（exit 1）。负控在被调用的 `dc.recheck` 一侧 |
| engine-rig/theory-compiler | `theory-compiler/src/theory_compiler/handover.py`（`python -m theory_compiler.handover`） | 是(读码) | 部分(读码) | 部分(读码) | 读码 | 生成器。`_main` `:1492` 无条件 `return 0`，`:1489-1491` 打印 `form <X> refused: <why>` 后仍 exit 0（tier 制度下拒绝发射某形式是设计内结果）。硬错误走 `HandoverError`/`ContextLeak`（exit 1） |
| exam/battery | `exam/verify.py`（五阶段总闸） | 是(实测) | 部分(读码) | 是(实测) | 混合 | 全量 `python -m exam.verify` → `GREEN` exit 0，287 tests passed，determinism identical；各阶段的红单独演示过，但无任何测试演示 `verify.py` 聚合器本身会返回 1 —— `exam/verify.py:96-106` 的 `failed` 汇总逻辑无人测过 |
| exam/battery | `exam/tools/build_papers.py`（漏题闸） | 是(实测) | 是(实测+读码) | 是(实测) | 混合 | 在 verdict 卷第一题 `paper` 里植入 leak probe，`bp.main(["verdict"])` 抛 `LeakageError: p15-verdict-a2 leaks its own answers: [... 'check': 'probe' ...]`，exit 1，且未写出任何文件（检查在写盘之前）。仓库自带负控 `exam/tests/test_core.py:76`、`:85`、`:148` |
| exam/battery | `exam/leakage.py::check_paper`（四检合一） | 是(实测) | 是(读码) | 是(读码) | 混合 | `exam/leakage.py:321` 与 `:340` 两处 `raise LeakageError`；`probe_hits` 对 <3 字符探针也 raise（`:64`）。`exam/tests/test_core.py` 13 处 `pytest.raises`，含「干净卷必须过」的反向控制（`:110,:155,:160,:173,:189`） |
| exam/battery | `exam/tools/run_exam.py --calibrate`（判卷器标定闸） | 是(实测) | 是(实测) | 是(实测) | 实测 | 注入 `selftest.FAULTS["pays_for_silence"]` 后 `run_exam.main(["--calibrate"])` 返回 1，并逐条打印 `verdict/null: 17 of 17 items are not 'unanswered'`。未注入时四卷 oracle=1.0000 / null=0.0000 全 CALIBRATED |
| exam/battery | `exam/grading/calibration.py::assert_calibrated` | 是(实测) | 是(读码) | 是(读码) | 混合 | 四个预注册假被试（oracle 必须 1.0、null 必须 0.0、memoriser、bluffer）+ 结构检查；失败 `raise ExamError`（`exam/grading/calibration.py:330`）。已知满分/已知零分的假被试是代码里跑出来的 |
| exam/battery | `exam/tools/run_selftest.py`（变异体+故障注入） | 是(读码) | 是(实测+读码) | 部分(读码) | 混合 | 8 个故障注入 + 6 类变异体；实跑 `mutants: all passed / faults: 8 injected, 0 uncaught, baseline clean`。红路径 `:119-123` `return 1`。未被捕获的故障（`HOLE: nothing catches ...`）打印后仍 exit 0 —— 写进 docstring 的刻意设计（`exam/verify.py:17-23`），当前 uncaught=0 |
| exam/battery | `exam/grading/selftest.py`（变异体电池 / FAULTS） | 是(读码) | 是(读码) | 是(读码) | 读码 | `PRE_REGISTERED` 六条算术恒等式 + `FAULTS` 八种坏判卷器。负控之负控：`exam/tests/test_selftest.py:86/96/103/123/142/152` |
| exam/battery | `exam/tools/run_matrix.py`（20 世界判卷矩阵） | 是(读码) | 部分(实测) | 否(实测) | 混合 | `exam/tools/run_matrix.py:328` 只有 `return 0 if result["worlds_in_matrix"] else 1`。实测：破坏一个世界（`t1-push-open` oracle 答案置空）`--per-class 2 --no-write` → 打印 `REFUSED t1-push-open: marker not calibrated`，exit 0。缓解：`exam/tests/test_worldgen_papers.py` 断言 `result["refused"] == []` |
| exam/battery | `exam/guard.py`（零网络 / 封存堆 / 合成世界） | 是(读码) | 是(读码) | 是(读码) | 读码 | `no_network()` 让 socket 抛；`assert_synthetic_world` 四条 raise（`:113/:124/:133/:137`）。负控 `exam/tests/test_core.py:212/226/236/244` |
| exam/battery | `exam/tools/archive_run.py` | 部分(读码) | 否 | 是(读码) | 读码 | 唯一非零路径是缺参数 `return 2`（`:131`）。把 `worktree_dirty: bool(git status --porcelain)` 写进 MANIFEST（`:95`）却从不据此拦任何东西 |
| exam/battery | `pytest exam/tests`（287 项） | 是(实测) | 是(读码) | 是(实测) | 混合 | 实跑 287 passed / 97.83s。`exam/tests/test_worldgen_papers.py:92` 与 `:238` 都自称 "the negative control" |
| exam/battery | `exam/verify.py::_determinism`（两解释器字节一致） | 是(读码) | 否 | 是(读码) | 读码 | 只哈希四张卷面（`module_for(t).build().sheet(digest())`），不哈希 `build_manifest.json`、不哈希 truth、不哈希 selftest.json |
| exam/battery | `battery/run_battery.py` | 部分(实测) | 部分(实测) | 部分(实测) | 实测 | 两条红路径：无 run 时 `return 1`（`:260`，实测 `--ledger <空文件> --a0 none` → exit 1），以及 guard 抛异常。其余全绿：整条 schema_repro 臂消失、21 个 metric 从未在控制臂上验证、process 1 判 `underpowered` —— 全部只打印，exit 0 |
| exam/battery | `battery/guard.py`（封存堆 + 切分完整性） | 是(实测) | 是(实测+读码) | 是(实测) | 混合 | 用 `piles.json` 第一个封存 id 造一行 ledger 喂进去 → `SealedPileError: 'bp35-0a0ad940' is in the sealed pile`，exit 1。`battery/tests/test_guard.py` 9 处 `pytest.raises`（全 id/短 id/大小写/空白/未知 id/篡改摘要/无摘要/双堆重叠/批量首行即停） |
| exam/battery | `pytest battery/tests`（214 项） | 是(实测) | 是(读码) | 是(实测) | 混合 | 实跑 214 passed / 0.99s。`battery/tests/test_metrics.py` 全是手算已知输入→已知输出；`battery/audit/exploits/*` + `test_exploits_*.py` 造出专门骗某个 metric 的合成 run 并断言确实被骗到 |
| exam/battery | `battery/docs.py`（`__main__`） | 否(读码) | 不适用 | 不适用 | 读码 | 死闸：`__main__` 里只有 `print(write())`，无任何非零退出路径。真正的闸是 `battery/tests/test_docs.py:10`（committed METRICS.md 必须等于 `docs.render()`） |
| exam/battery | `battery/metrics/*`（判分正确性） | 是(读码) | 是(读码) | 不适用 | 读码 | metric 本身不退出；闸是 `battery/tests/test_metrics.py` 的手算值 + `battery/audit/exploits` 的对抗样本。`Value.status` 是数据不是退出码 |
| exam/battery | `battery/audit/{gaming,validation,discriminate,contrast,redundancy}.py` | 否(读码) | 不适用 | 不适用 | 读码 | 全是报告器，无 raise、无退出码。`validation_material.json` 说「21 个 metric 无控制臂验证」、`discrimination.json` 说 `underpowered` —— 都只是 JSON 字段 |
| exam/battery | battery 的「一条命令总闸」 | — | — | — | — | 不存在。`exam/` 有 `verify.py`，`figures/` 有 `verify.sh`，`battery/` 两者都没有；README 只列了三条互不汇总的命令 |
| worldgen/fuzzlab | `worldgen/verify.py` | 是(读码) | 否(实测) | 部分(实测) | 混合 | 实跑 `python -m worldgen.verify` → 打印 `green`，exit 0，同时两道 QC 子闸各自非零（`QC.json` `family_verdict.pass=false`、`QC_MUTANTS.json` `mutant_verdict.pass=false`）。`worldgen/verify.py:40-49` 把两道 QC 都标 `gating=False`，红只进 `notes` 不进 `failures`。无测试演示 `verify.py` 自己会红 |
| worldgen/fuzzlab | `worldgen/build.py --check`（出厂闸 `gate_failures`） | 是(读码) | 是(读码) | 是(读码) | 读码 | `worldgen/build.py:200-228` 五道闸 + `:321-326` `BUILD GATE FAILED` → `return 1`。负控 `worldgen/tests/test_build_gate.py:48-63`（合成 manifest 逐条违反每道闸），`:70-80` 再断言真 `INDEX.json` 的 key 名与合成一致 |
| worldgen/fuzzlab | `worldgen/build.py::check_determinism` | 是(读码) | 否(读码) | 是(读码) | 读码 | `worldgen/build.py:231-286` 起子进程换 `PYTHONHASHSEED` 重建再逐字节 diff，`:343-350` `NOT DETERMINISTIC` → `return 1`。无任何测试故意改字节证明它会红；`worldgen/tests/test_determinism.py:57` 是同进程 `_trace_bytes(id) == _trace_bytes(id)`，docstring 自称 "strictly weaker version"。425 个测试零个提到 `check_determinism` |
| worldgen/fuzzlab | `worldgen/mutate.py::mutation_gate_failures`（MUTATION GATE） | 是(读码) | 部分(读码) | 是(读码) | 读码 | `worldgen/mutate.py:1375-1406`，`worldgen/build.py:334-341` / `mutate.py:1453-1456` → `return 1`。家族声明一半有真负控：`worldgen/tests/test_mutate.py:527-548` 构造贴错标签的 `Edit` 断言 `check_family` 必须报问题。可解性声明一半无负控（`claimed != measured` 分支无人演示） |
| worldgen/fuzzlab | `worldgen/qc/run_qc.py`（三世界 QC 闸） | 是(实测) | 否(读码) | 是(实测) | 混合 | 实跑：`t2-lock-fragile` 抛 `NoSeparatingGuard`，`family_verdict.pass=false`，`worldgen/qc/run_qc.py:371` → exit 1。但这是未修的长期红，不是负控：425 个测试零个引用 `run_qc` / `verdict` / `mutant_verdict` / `layer_one_two` / `layer_three` |
| worldgen/fuzzlab | `worldgen/qc/run_qc.py --mutants`（预注册变异体套件） | 是(实测) | 部分(实测) | 是(实测) | 实测 | 实跑 exit 1，`mutant verdict: {"failed": ["v-efe43df1"], "pass": false, "sampled": 4}`，`run_qc.py:435` `return 0 if mutant_verdict["pass"] else 1` 真执行。三点不成立见第 3 节 |
| worldgen/fuzzlab | `worldgen/tests` pytest（425 项，verify 的 gating 阶段） | 是(实测，全绿) | 部分(读码) | 是 | 混合 | 真负控只有三处：`worldgen/tests/test_build_gate.py`（双向）、`test_mutate.py:527`（贴错标签）、`test_gravity_landing.py:65`（negative half）。其余是正向断言 |
| worldgen/fuzzlab | `worldgen/qc/diagnose_miner.py` | — | — | — | — | 不是闸：纯诊断打印，无判决分支，恒 0。列出以免被当成验收入口 |
| worldgen/fuzzlab | `fuzzlab/verify.py` | 是(读码) | 否(读码) | 是(读码) | 读码 | `fuzzlab/verify.py:32-39` 三阶段全 gating，`:66-68` → `return 1`。红能传导，但无任何东西演示过 `fuzzlab.verify` 会红 |
| worldgen/fuzzlab | `fuzzlab/campaign.py` | 是(实测) | 否(读码) | 部分(实测) | 混合 | 实测注入生成器故障 → exit 1（`fuzzlab/campaign.py:202` 只认 `generator_errors`）。实测注入引擎故障使 5 世界 15 条不变式全 `violated` → exit 0，报告 `"violated": 15`、终端打印 `VIOLATED (15)`。写在 `:199-201` 的设计（「失败是战利品」） |
| worldgen/fuzzlab | `fuzzlab/tests/test_battery.py::test_short_campaign_finds_no_violation` | 是(实测) | 否(实测+读码) | 是 | 混合 | 23 条不变式唯一的判决点（每引擎 25 世界）。用注入故障证过 `check()` 会吐 `violated`，但仓库里没有任何注入故障的构造 |
| worldgen/fuzzlab | `fuzzlab/tests/test_oracles.py` | 是 | 是(读码) | 是 | 读码 | 真负控，但是给 oracle 的不是给不变式的：`:98`、`:121/:127/:140/:146`、`:167`、`:43`。证明「坏输入进 oracle 必须被拒」，不证明「坏引擎进不变式必须响」 |
| worldgen/fuzzlab | `fuzzlab/tests/test_battery.py::test_distinct_indices_give_distinct_worlds` | 是 | 是(读码) | 是 | 读码 | 反重言测试：注释直说「a generator that ignored its seed would pass everything else」。是生成器的负控，不是不变式的 |
| worldgen/fuzzlab | `fuzzlab/minimize.py` | 是(读码) | 否 | 是(读码) | 读码 | `fuzzlab/minimize.py:179` 找不到复现体 → `return 1`。是搜索工具不是闸，退出 1 表示「没搜到」而非「有缺陷」 |
| figures/release | `figures/verify.sh` | 是(实测) | 部分(实测) | 是(实测) | 实测 | 实跑 `bash figures/verify.sh` → 第 1 关 fig06 抛 `ValueError: THEORIZE_LOG.md: entry ids do not match the declared set. unexpected=['E-08']`，印 `FAIL: build pass A did not complete`，exit 1。九关中只有第 8 关自带负控（第 0、2、3、4、6、7 关零可执行负控；第 1、5、7 关只有意外/假阳性触发史） |
| figures/release | `figures/build_all.py` | 是(实测) | 否(读码) | 是(实测) | 混合 | `figures/build_all.py:141-143` 收集 `failures` 后 `return 1`；上面那次实跑就是它红的。无 self-test、无坏 fixture |
| figures/release | `figures/check_coverage.py`（默认） | 是(读码) | 是(实测) | 是(实测) | 混合 | `figures/check_coverage.py:308-312` 有 failures 即 `return 1`。实跑 → 绿 exit 0 |
| figures/release | `figures/check_coverage.py --self-test` | 是(读码) | 是(实测，它本身就是负控) | 是(实测) | 混合 | 实跑 exit 0，输出 `coverage self-test ok: narrowed to the pre-P8 roll-up list, the probe reports both runs it was written to catch (bare_cc-g50t-claude-sonnet-5-ddabe772, bare_cc-sk48-claude-sonnet-5-9022a076)`。`self_test()` 在 `figures/check_coverage.py:230-278`，负控没打中就 `return 1`（`main` `:283-292`） |
| figures/release | `figures/manifest.py` | 否(读码) | 否 | 不适用 | 读码 | `figures/manifest.py:152-172` 只有 `return 0` 一条出口；是 provenance 写入器不是闸门，也无任何拒绝路径 |
| figures/release | `release/check_redlines.py`（`--mode generate` 默认 / `verify`） | 是(读码) | 否(读码) | 是(读码+实测绿路径) | 混合 | `release/check_redlines.py:304-306` `if total: print(...); return 1`。实跑 `--mode verify` → 0 violation exit 0。从未有人演示它会红：`release/` 下无测试、无故意埋钥匙/封存 payload 的 fixture |
| figures/release | `release/enumerate.py --dry-run` | 是(读码) | 否(读码) | 是(读码；本树未触发红路径) | 读码 | 红线不清时 `release/enumerate.py:294` 印 `ABORT: the red lines are not clear; no manifest generated.`，`:297` `return 2`。实跑 `--dry-run` 本树红线清白 → exit 0 |
| figures/release | `release/checklist.py --dry-run` | 否(读码) | 否 | 不适用（永远绿） | 读码 | `release/checklist.py:226-262` 全函数只有 `return 0`（`:256`、`:260`）。ABSENT / 「no reason recorded — this needs one before release」都只是打印。实测 `7 present, 3 withheld, 0 absent` exit 0 |
| figures/release | `release/reproduce.py`（默认 / `--all` / `--list` / `--dry-run`） | 否(实测) | 否 | 否(实测) | 实测 | `release/reproduce.py:348-351` `drifted`/`command-failed`/`manifest-stale` 全走同一个 `return 0`。实测（OUT 指向 scratchpad）：`1/9 reproduced`、`command-failed figures`、`manifest-stale papers/phase1-workshop`，`MAIN RETURNED: 0`。`--dry-run`（`:343-345`）与 `--list` 同样 exit 0 |
| figures/release | `release/bundle.py --check` | 不适用 | 不适用 | 不适用 | — | 该文件不存在。全仓 `find . -iname "*bundle*"` 只命中 `exam/handover_bundles/`；`release/` 里只有 `check_redlines.py`、`enumerate.py`、`checklist.py`、`reproduce.py` |
| proxy/arc-recon | `proxy/guard.py` SealedPileGuard（封存护栏） | 是(实测) | 是(实测) | 不适用（库；代理侧映射 403） | 实测 | `proxy/tests/test_guard.py:29,36,48,55`；`proxy/tests/test_seal.py:109,146,155`；`proxy/tests/test_redteam.py:523,539,545,559,584,595,620,644,680,690,704` |
| proxy/arc-recon | `proxy/guard.py` `load_piles` 切分完整性（钉死 sha256） | 是(实测) | 是(实测) | 不适用（raise `PilesIntegrityError`） | 实测 | `proxy/tests/test_guard.py:19`（篡改切分）；`proxy/tests/test_redteam.py:620`（重新签名的切分 RED-30）、`:644`（RED-31） |
| proxy/arc-recon | `proxy/env_proxy.py` 请求闸（403 + `guard_block` + incident + 空帧 env_step） | 是(实测) | 是(实测) | 不适用（HTTP 403，非进程） | 实测 | `proxy/tests/test_seal.py:109,125,146,155`；`proxy/tests/test_redteam.py:704` |
| proxy/arc-recon | `proxy/model_proxy.py` 提示词里的封存 ID | 是(实测) | 是(实测) | 不适用 | 实测 | `proxy/tests/test_redteam.py:680`（RED-32） |
| proxy/arc-recon | `proxy/mock/arm_mock.py` `assert_sealed`（arm 持凭证即拒启动） | 是(实测) | 是(实测) | 不适用（raise `NotSealedError`） | 实测 | `proxy/tests/test_seal.py:51-54` 参数化跑遍 `FORBIDDEN_ENV` |
| proxy/arc-recon | `proxy/redact.py` Vault / `scrub_outbound`（密钥密封） | 是(实测) | 是(实测) | 不适用 | 实测 | `proxy/tests/test_ledger.py:92`；`proxy/tests/test_redteam.py:368,381,393,406,422,434,447,462,474,487`（RED-10..19） |
| proxy/arc-recon | `proxy/ledger.py` + `proxy/canon.py` 写入端拒绝（非规范字段 / 成本禁令 / frame_hash） | 是(实测) | 是(实测) | 不适用（raise，且不落盘） | 实测 | `proxy/tests/test_canon.py:25-137`；`proxy/tests/test_redteam.py:887,907,917` |
| proxy/arc-recon | `proxy/tools/validate_ledger.py`（账本校验） | 是(实测) | 是(实测) | 是(读码) | 混合 | `proxy/tools/validate_ledger.py:170` PASS→0 / FAIL→1。负控 `proxy/tests/test_canon.py:137`（伪造 frame_hash）、`:152`（重复 seq）、`:159`（level 不可重算）；`test_redteam.py:856` |
| proxy/arc-recon | `proxy/reconcile.py`（对账义务） | 是(实测) | 是(实测) | 部分(读码) | 混合 | `proxy/reconcile.py:172` 把 `EMPTY` 与 `PASS` 一并判 0 —— 不存在的 run-id 也退 0。负控 `proxy/tests/test_e2e.py:177`；`test_redteam.py:772,791,803,818,830,855,872,933,981` |
| proxy/arc-recon | `proxy/scoring/`（冻结计分器 S-0..S-12 + 自哈希） | 是(实测) | 是(实测) | 是(读码) | 混合 | `proxy/scoring/__init__.py` 全 PASS→0 否则 1。负控 `proxy/tests/test_scoring.py:36`（改过的计分器拒绝计分）、`:161,168,178,185,194,201,211,219,227,242,253,270` |
| proxy/arc-recon | `proxy/replay.py`（replay 审计） | 是(实测) | 是(实测) | 是(读码) | 混合 | `proxy/replay.py:170`。负控 `proxy/tests/test_e2e.py:140` 篡改账本 → replay FAIL + `replay_mismatch` incident |
| proxy/arc-recon | `proxy/tools/replay_spotcheck.py` | 是(实测) | 是(实测) | 是(读码) | 混合 | `proxy/tools/replay_spotcheck.py:215`，`INSUFFICIENT` 也判非零。负控 `proxy/tests/test_migration.py:198,206,216,221` |
| proxy/arc-recon | `proxy/spend_gate.py` SpendGate（花费闸 / 配额闸，reserve+check+record） | 是(实测) | 是(实测) | 不适用（raise `SpendGateTripped` / `Unavailable` / `NoReservation`） | 实测 | `proxy/tests/test_spend_gate.py` 全 60 项（缺策略、零上限、损坏账本行、过期租约、无预约花费、NaN/Inf、无 permit 的 forward…）；`test_spend_gate_concurrency.py:148,163,175` 多进程竞态下上限仍守住 |
| proxy/arc-recon | `proxy/spend_gate.py` `__main__`（池子报表） | 否(读码) | 否 | 否 | 读码 | `proxy/spend_gate.py:1214` 恒 `return 0`。`proxy/verify_spend.sh:9` 把它写成「查池子是否在上限内」的办法，但超限它也退 0 |
| proxy/arc-recon | `proxy/verify_spend.sh` | 是(读码) | 部分(读码) | 是(读码) | 读码 | `fail=1; exit "$fail"`。内部三条 grep 式检查（无 off switch / 无绕过 socket）没有植入违例的负控；同一断言在 `proxy/tests/test_spend_gate.py:419,426` 再断一次，但只在干净仓库上跑通。未跑：会调用 `baseline-arms/harness/ledger.py` |
| proxy/arc-recon | `proxy/tools/upgrade_ledger.py` | 部分(读码) | 是(读码) | 部分 | 读码 | 不认识的记录 raise；`main` 恒 0。负控 `proxy/tests/test_migration.py:148,153`（拒绝不认识的记录 / 拒绝二次抬升）—— 靠 raise 非零而非 `return` |
| proxy/arc-recon | `proxy/cost.py`、`proxy/runner.py` | 否(读码) | 不适用 | 不适用（非闸门） | 读码 | `proxy/cost.py:166`、`proxy/runner.py:269` 报表/跑手，恒 0 |
| proxy/arc-recon | `arc-recon/precheck.py` `assert_playable`（封存护栏） | 是(实测) | 是(实测) | 是(读码) | 混合 | `arc-recon/precheck.py:414` → 2。负控 `arc-recon/test_hygiene.py:124`（`ls20` / `ft09` 被拒 + 开发局放行）、`:132` |
| proxy/arc-recon | `arc-recon/canary.py` `compare`（漂移仪表） | 是(实测) | 是(实测) | 不适用（库） | 实测 | `arc-recon/test_hygiene.py:54,62,70,77` —— INC-003 的形状：缺步必须读作 INCOMPLETE 而非 PASS |
| proxy/arc-recon | `arc-recon/canary.py check-freeze` | 是(实测) | 是(实测) | 是(实测) | 实测 | `arc-recon/test_hygiene.py:95-98` 直接断言退出码从 0 翻到 1 |
| proxy/arc-recon | `arc-recon/canary.py` `INVOCATION_CAP`（配额闸） | 是(实测) | 是(实测) | 是(读码) | 混合 | `arc-recon/canary.py:678` → 3。负控 `arc-recon/test_hygiene.py:140`（24 计划 > 20 上限 → `BudgetExceeded`） |
| proxy/arc-recon | `arc-recon/canary_schedule.py`（排程 + 闸门映射） | 是(实测) | 是(实测) | 是(实测) | 实测 | `arc-recon/test_canary_schedule.py:341`（闸门拒绝即停）、`:359`（CLI 映射到 exit 5）、`:392`（每个可能的结局都有退出码）、`:246`（封存目标在排程前就被拒） |
| proxy/arc-recon | `arc-recon/contamination.py` `verify_piles_hash` | 是(读码) | 部分（只在好文件上跑通） | 是(读码) | 读码 | `arc-recon/contamination.py:338`。`arc-recon/test_hygiene.py:203` 只断言现网切分匹配；没有构造被篡改的 `piles.json` 断言 MISMATCH（proxy 侧 `test_guard.py:19` 有，arc-recon 侧没有） |
| proxy/arc-recon | `arc-recon/contamination.py` `sealed_api_contacts`（封存接触审计） | 是(实测) | 是(实测) | 否(实测) | 实测 | 负控 `arc-recon/test_hygiene.py:419,431,474`。退出码：植入含 `POST /api/cmd/RESET {"game_id":"ls20-9607627b"}` 的临时账本 → 打印 `sealed ADDRESSED: ls20-9607627b`，EXIT CODE = 0 |
| proxy/arc-recon | `arc-recon/contamination.py` `claim_set` 的 `needs_adjudication` | 是(实测) | 是(实测) | 否(实测) | 实测 | 负控 `arc-recon/test_hygiene.py:354,368,378`。退出码：植入 `vc33-5430563c / mechanics_disclosed / 无 claims` 到临时 log → 打印 `NEEDS ADJUDICATION (excluded from clean): vc33-5430563c`，EXIT CODE = 0 |
| proxy/arc-recon | `arc-recon/verify.sh`（arc-recon 绿灯） | 是(读码) | 部分 | 部分(实测) | 混合 | `fail=1; exit "$fail"`。`arc-recon/verify.sh:53` 那一步的标签写着「pile cut, claim set and the sealed-contact audit」，但它调用的 `contamination.py` 只让切分哈希决定退出码 |
| proxy/arc-recon | `arc-recon/redact_ledger.py --check`（凭证/cookie 值落盘检查） | 是(读码) | 否 | 是(读码) | 读码 | `arc-recon/redact_ledger.py:138` 有 offender → 1。没有构造「账本里有 cookie 值」的 fixture 断言 `scan()` 报红；`arc-recon/test_hygiene.py:319` 的正控测的是测试文件自己的 helper `_cookie_value_offenders` |
| proxy/arc-recon | `arc-recon/client.py` 密钥密封（`_record` 里 `X-API-Key`→`<redacted>`） | 部分(读码) | 否 | 不适用 | 读码 | `arc-recon/client.py:300` 只按 header 名替换，没有拒绝/告警路径。没有任何测试把密钥值植入 body / response_body / 其他 header 再断言它不落盘 |
| proxy/arc-recon | `arc-recon/client.py` `load_api_key`（缺失即拒） | 是(实测) | 是(实测) | 不适用（raise） | 实测 | `arc-recon/test_canary_schedule.py:429-433` |
| proxy/arc-recon | `arc-recon/cut_piles.py`（拒绝二次切分） | 是(读码) | 否 | 是(读码) | 读码 | `arc-recon/cut_piles.py:136` → 2。没有测试构造「piles.json 已存在」断言退 2 |
| proxy/arc-recon | `arc-recon/precheck.py` `main` | 部分(读码) | 不适用 | 否(读码) | 读码 | FAIL/UNPLAYABLE 的局只进 `excluded`，`arc-recon/precheck.py:458` 仍退 0。只有封存拒绝(2)/超预算(3)非零。未跑：需网络 |
| proxy/arc-recon | `arc-recon/recon.py`、`arc-recon/probe_stickiness.py`、`arc-recon/precheck_resume.py` | 否(读码) | 不适用 | 不适用（采集脚本，非闸门） | 读码 | 恒 0 / 无判据。未跑：需网络 |
| arms | `theoria-arm/harness/run.py`（`python -m harness.run`） | 否(读码) | 否(读码) | 否(读码) | 读码 | `theoria-arm/harness/run.py:211` `main()` 恒 `return 0`；无任何非零路径。未跑：会花钱/联网 |
| arms | `theoria-arm/armtools/archive.py`（收工闸：对账 + 约束 8 + 成本双算 + 封存检查） | 否(读码) | 部分(读码) | 否(读码) | 读码 | `theoria-arm/armtools/archive.py:412-419` `main()` 恒 `return 0`。它算得出红：`constraint_8()['holds']`（`:297`）、`reconcile()` 的 `"MISMATCH"`（`:78`）、`sealing()` 的封存命中（`:216-246`）—— 全部只写进 MANIFEST.json。负控只覆盖另一份实现 `theoria-arm/tests/test_arm.py:137`/`:145`（打的是 `inner/surprise.py::Register.audit`） |
| arms | `theoria-arm/armtools/preflight.py` | 是(读码) | 否(读码) | 是(读码) | 读码 | `theoria-arm/armtools/preflight.py:88` `return 0 if out.get("reset_status") == 200 else 1`。未跑：联网 |
| arms | `theoria-arm/armtools/salvage.py` / `theoria-arm/armtools/timeline.py` | 否(读码) | 否 | 否(读码) | 读码 | `salvage.py:184`、`timeline.py:231` 恒 `return 0`（报告工具，列此以免被当成闸） |
| arms | `theoria-arm` pytest（`tests/test_arm.py`，51 项，纯离线） | 是(实测) | 是(读码) | 是(实测) | 混合 | 实测 51 passed，EXIT=0。负控 `theoria-arm/tests/test_arm.py:31`（`pytest.raises(arc.ShortIdRefused)`）、`:137`（脏账本必须判违约束 8）、`:145`（无意外的 model_call 必须判违规） |
| arms | `ablation-arm/verify.sh` → `ablation-arm/verify.py`（完工闸） | 是(实测走绿；红路径读码 `verify.py:361`) | 是(读码) | 是(读码+实测绿) | 混合 | 实测 `python ablation-arm/verify.py` → `GREEN` EXIT=0，五 stage 全 ok。负控 `ablation-arm/tests/test_verify.py:54-70`（4 组参数篡改 `run_all.json` 断言指定断言必须变红）、`:73`（字段缺失不得被读成闸门想要的值） |
| arms | `ablation-arm/build_theory.py --check`（生成物 vs 上游重切） | 是(读码 `build_theory.py:340`) | 是(读码) | 是(读码) | 读码 | 负控 `ablation-arm/tests/test_build_and_determinism.py:28`（手改一行必须被抓）、`:48`（放回 `[status: proven]` 必须两条通道都响：字节 diff + parser） |
| arms | `ablation-arm/run_arm.py`（预注册像素数 + 上游只读钉） | 是(读码 `run_arm.py:714`) | 是(读码) | 是(读码) | 读码 | 负控 `ablation-arm/tests/test_loop.py:84`（换错 trace → `pre_registered.holds is False`）、`tests/test_readonly.py:72` `test_the_pin_can_see_a_change_at_all` |
| arms | `ablation-arm/run_arm.py --twice`（两轮复跑比对） | 是(读码 `run_arm.py:678`) | 部分(读码) | 是(读码) | 读码 | 无「注入不确定性必须变红」的测试；`ablation-arm/tests/test_build_and_determinism.py:103` 断言两份 ledger 原始字节必须不同（否则测试自称无意义），算半个演示 |
| arms | `ablation-arm/run_exhibits.py` | 否(实测) | 是(读码，双向钉住) | 否(实测，且是刻意的) | 混合 | `ablation-arm/run_exhibits.py:57` `main()` 打印 `not holding: ...` 后无条件 `return 0`；`--json` 分支 `:46` 同样恒 0。理由写在 `:8-13` docstring。`ablation-arm/tests/test_exhibits.py:145` 把行为钉住（`assert run_exhibits.main([]) == 0`）；`:96`/`:102` 双向钉住 E3 |
| arms | `baseline-arms/harness/audit_cells.py`（逐格账本审计 + 封存检查） | 是(读码 `audit_cells.py:236` / `:280`) | 部分(读码) | 是(实测走绿+读码) | 混合 | 实测 `python -m harness.audit_cells --json` → EXIT=0，12 格、`sealed_hits: []`。负控只覆盖 `reached_api()` 分类（`baseline-arms/tests/test_audit_pool.py:218-235`）；没有任何测试伪造一份对不上账的 ledger 逼它红 |
| arms | `baseline-arms/harness/audit_pool.py`（花费池对账） | 是(读码 `audit_pool.py:284`) | 是(读码) | 是(读码) | 读码 | 负控齐全：`baseline-arms/tests/test_audit_pool.py:61`（少记动作）、`:76`（多记）、`:101`（美元对不上）、`:129`（预留未关） |
| arms | `baseline-arms/harness/merge_ledger.py --check` | 是(读码 `merge_ledger.py:91`) | 否(读码) | 是(读码) | 读码 | `return 1 if bad else 0`，`bad` = 不可解析行数。无负控 |
| arms | `baseline-arms/harness/run_campaign.py --gate-only`（战役闸） | 是(读码 `run_campaign.py:487`) | 部分(读码) | 是(读码，红=退出码 3) | 读码 | `baseline-arms/tests/test_spend_binding.py:272` 只断言「格上限就是闸的数字，不是新数字」，不是逼闸变红 |
| arms | `baseline-arms/harness/transport_ab.py::assert_not_frozen`（跨轨冻结闸） | 是(读码 `transport_ab.py:72` `raise SystemExit(str)` → 退出 1) | 否(读码) | 是(读码) | 读码 | 未跑：会花钱/联网（`run_cell` 直接 `bare_cc.play`） |
| arms | `baseline-arms/harness/campaign.py` / `run_campaign.py`（活体战役） | 是(读码，拒跑路径 `return 2`) | 否 | 是(读码) | 读码 | 未跑：会花钱/联网 |
| arms | `baseline-arms` pytest（75 项，全部用 `tmp_path` 私有花费池） | 是(实测) | 是(读码) | 是(实测) | 混合 | 实测 75 passed，EXIT=0。`baseline-arms/tests/conftest.py` 明确不碰真实 `proxy/var/spend_gate.jsonl` |
| arms | `cold-start-a0/run_all.py`（九步 + schema 校验） | 是(实测走绿；红路径读码 `run_all.py:97`) | 是(读码) | 是(读码+实测绿) | 混合 | 实测 `python run_all.py` → `all steps green` EXIT=0。负控 `cold-start-a0/tests/test_a0.py:251` `test_mutants_are_caught`，四种突变（删门规则/删按钮规则/破传送/删门对象）必须被 replay 层抓成 `render_mismatch` / `unowned_pixel` |
| arms | `cold-start-a0/certify/score_vs_truth.py`（M6 对裁判打分） | 否(读码) | 否 | 否(读码) | 读码 | `cold-start-a0/certify/score_vs_truth.py:169` `main()` 恒 `return 0`，准确率再低也不会红。（不在 `run_all.py` 的步骤表里） |
| arms | `cold-start-a0/certify/fd_conformance.py` | 是(读码 `:211` `:225`；缺 FD 时 `sys.exit(12)`) | 否(读码) | 是(读码) | 读码 | — |
| arms | `cold-start-a0` pytest（56 项） | 是(实测) | 是(读码) | 是(实测) | 混合 | 56 passed，EXIT=0 |
| arms | `cold-start-a2/run_all.py`（13 步 + schema 校验） | 是(实测走绿；红路径读码 `run_all.py:105`) | 否(读码) | 是(读码+实测绿) | 混合 | 实测 EXIT=0 全绿。每个子步骤退出码都诚实（`certify_a2.py:153`、`plan.py:151`、`exhibit.py:172`、`refute.py:120`、`locate.py:208`、`repair.py:270`、`ledger.py:215` 全是 `return 0 if <green> else 1`）。但没有任何「故意坏掉的 manual/trace 必须让某一步变红」的可执行负控 |
| arms | `cold-start-a2/tools/verify_readonly.py`（上游树只读） | 是(读码 `:79`) | 否(读码) | 是(读码) | 读码 | — |
| arms | `cold-start-a2` pytest（44 项） | 是(实测) | 部分(读码) | 是(实测) | 混合 | 44 passed，EXIT=0 |
| arms | `cold-start-a3/run_all.py`（七段，含第 5 段负控） | 否(实测) | 是（负控本身存在） | 否(实测) | 实测 | `cold-start-a3/run_all.py:123` `main()` 恒 `return 0`。实测把 `negctl.run_all` 打桩成 `all_caught=False, claimed_a_win=True` → 打印照常、`run_all.main() returned: 0`、EXIT=0 |
| arms | `cold-start-a3/a3pipeline/negctl.py`（两组负控本体） | 是(读码 `negctl.py:153`) | 是（它就是负控） | 是(读码) | 读码 | 实测 `python -m a3pipeline.negctl` → 两组「世界被改过一处机制」的臂都 `caught=True outcome=replay_mismatch`，EXIT=0。`negctl.py:1-45` 说明为什么两组不是同一个测试 |
| arms | `cold-start-a3/tools/verify_readonly.py` | 是(读码 `:89`) | 否(读码) | 是(读码) | 读码 | — |
| arms | `cold-start-a3` pytest（47 项） | 是(实测) | 是(读码) | 是(实测) | 混合 | 47 passed。`cold-start-a3/tests/test_transfer.py:211` 断言两组负控都被抓且都没宣称胜利；`tests/test_world.py:101` `test_the_shipped_traces_are_byte_stable` |
| arms | `a0-spike/pipeline/run_a0.py` | 是(读码 `run_a0.py:262`) | 是(读码) | 是(读码) | 读码 | `return 0 if ok else 1`，`ok` 综合 grading/replay_exact/held_out/lean。负控 `a0-spike/tests/test_a0.py:203`、`:240`（生成器必须拒绝编不出的东西）、`:382`/`:415`/`:428`（注入一处世界改动，依赖追踪必须抓到并定位） |
| arms | `a0-spike/runs/20260728T040057Z-c2/make_manifest.py --verify` | 是(实测) | 是（实测演示 + 文档记载曾真抓到 7/19） | 是(实测) | 实测 | 实测原样 → `19 files; 0 mismatched` EXIT=0；把一条 sha256 改成全 0 → `MISMATCH ... 19 files; 1 mismatched` EXIT=1，随后还原。这是这些领地里唯一一道「提交的产物字节 vs 仓库存的字节」的闸 |
| arms | `a0-spike/probes/semantics_probe.py` | 是(读码 `:467`；未知事件 `raise SystemExit` `:97`) | 部分(读码) | 是(读码) | 读码 | — |
| arms | `a0-spike` pytest（44 项） | 是(实测) | 是(读码) | 是(实测) | 混合 | 44 passed，EXIT=0 |

---

## 第 2 节：计数

```
入口总数：127
能红：是 103 / 部分 6 / 否 15        （另：不适用或未答 3）
有负控：是 61 / 部分 22 / 否 35      （另：不适用或未答 9）
退出码诚实：是 84 / 部分 8 / 否 13   （另：不适用或未答 22）
实测支撑的行：24 / 127
```

证据强度分布：`实测` 24 行（三列均为实测）、`混合` 45 行（三列中至少一列有实测）、`读码` 55 行、`—` 3 行。

### 按领地小计

| 领地 | 入口数 | 能红 是/部分/否 | 有负控 是/部分/否 | 退出码诚实 是/部分/否 | 实测行（混合行） |
|---|---|---|---|---|---|
| engine-rig/theory-compiler | 20 | 18 / 1 / 1 | 8 / 6 / 5 | 17 / 1 / 1 | 3（8） |
| exam/battery | 19 | 14 / 2 / 2 | 11 / 3 / 2 | 12 / 2 / 1 | 2（9） |
| worldgen/fuzzlab | 14 | 13 / 0 / 0 | 3 / 3 / 7 | 11 / 2 / 0 | 1（5） |
| figures/release | 10 | 6 / 0 / 3 | 2 / 1 / 6 | 6 / 0 / 1 | 2（4） |
| proxy/arc-recon | 32 | 26 / 3 / 3 | 22 / 3 / 4 | 12 / 3 / 4 | 14（8） |
| arms | 32 | 26 / 0 / 6 | 15 / 6 / 11 | 26 / 0 / 6 | 2（11） |
| **合计** | **127** | **103 / 6 / 15** | **61 / 22 / 35** | **84 / 8 / 13** | **24（45）** |

---

## 第 3 节：点名清单（合并去重）

### 没有负控的闸门

**engine-rig / theory-compiler**

- `engine-rig/bench/verify.py` —— 全仓最像「验收」的那个命令（README 里就写着 `python -m bench.verify runs/<id>`），却是唯一一个连一行测试都没有的验收器；它自己判定 run 目录能不能被相信，而没有任何东西判定过它。
- `engine-rig/bench/verify.py:134-139` —— 没有负控的直接代价，实测拿到：把 `ladder.json` 里 `gripper-02/stub-bfs` 的 `expanded` 改成 18+999 触发结构复算分支，进程不是报出漂移而是 `TypeError: not enough arguments for format string`（格式串三个占位符、参数元组只有两个，且 `name` 根本没传进去）。退出码仍是 1，但最该说人话的那条诊断永远说不出来。
- `engine-rig/bench/ladder.py:237 failures()` 与 `engine-rig/bench/dividend.py:290 failures()` —— `python -m bench` 的退出码完全由这两个函数的返回值决定，而测试只钉到了上游的 `verdicts()`。verdict 为 False 到进程 exit 1 之间那一段接线，没有任何东西验过。
- `theory-compiler/tools/handover_exam.py` —— 交接包验收的阅卷器，`verify_c8` 的第 5、6 项检查整个建在它上面，而全仓库没有一个测试导入过它。
- `theory-compiler/tools/refresh_manifest.py` —— provenance 漂移的唯一自动检测器，无测试；而且它现在对树里每一个 run 都返回 1，说明没人在跑它。
- `theory-compiler/tools/build_handover_packages.py --check` —— 字节复算的 FAIL 分支无人演示过；已有测试只从「应该相等」那一侧比对。

**exam / battery**

- `exam/verify.py:96-106` —— 整个 exam 领地唯一的总闸，可它的 `failed` 汇总逻辑从没被演示为会红；一个阶段返回非零时它是否真的 return 1，只有代码能证明。
- `exam/tools/run_matrix.py:328` —— 没有测试钉住 `main()` 的返回值；`refused` 非空时它返回什么，是实测才知道的（返回 0）。
- `battery/run_battery.py:258-260` —— 「no runs found → return 1」这条路径没有任何测试断言过退出码：`battery/tests/test_docs.py:58-61` 正好用空 ledger 调了它，却把返回值丢掉并 `except SystemExit: pass`。
- `battery/artifacts/*.json` 整体 —— battery 里没有任何东西把提交的产物和一次复算对比。`battery/tests/test_determinism.py` 只比「同一个 fixture 跑两遍是否一致」，比的是临时目录里的两份，不是仓库里的那份。
- `exam/verify.py::_determinism` —— 只对四张卷面做字节比对，`build_manifest.json` / `truth/` / `selftest.json` 全在闸外。这就是绝对路径缺陷能长期存活的原因。
- `exam/tools/archive_run.py:95` —— `worktree_dirty` 被写进每一份 MANIFEST 却从不拦人；一个脏工作树归档出来的 run 和干净的长得一样合法。

**worldgen / fuzzlab**

- `worldgen/build.py::check_determinism` —— 全仓库最强的确定性主张（换 `PYTHONHASHSEED` 起子进程逐字节 diff 35 个世界 × 6 个产物 + 两张 roster）靠它，而它自己的 docstring 就写着「a gate that cannot fail is not a gate」——但没人演示过它会红。
- `worldgen/qc/run_qc.py`（含 `verdict` / `mutant_verdict`）—— 425 个测试零覆盖。它是决定「工厂出的世界能不能被上游流水线学会」的判决器，今天是红的，但没有任何东西保证它是因为该红的原因红的；`verdict()` 里任何一处 `and` 写成 `or` 都不会被测试发现。
- `fuzzlab/props/*.py` 的 23 条不变式 —— 仓库里没有任何故意坏的引擎；`fuzzlab/props/__init__.py:10` 声称的 `fuzzlab/props/test_<engine>.py` 前端文件不存在，全 fuzzlab 零个 `@given`。23 条不变式目前是 23 盏「没被演示过会红」的绿灯。
- `worldgen/mutate.py::mutation_gate_failures` 的可解性一半 —— 家族声明有负控，可解性声明没有。
- `fuzzlab/verify.py` / `worldgen/verify.py` 两个领地闸本身 —— 只演示过绿。

**figures / release**

- `figures/verify.sh` 第 0、2、3、4、6、7 关 —— 零可执行负控。其中第 3 关（两次构建逐字节相同）与第 6 关（committed 树 == 新构建）是对外宣传的核心确定性主张；第 3 关还有书面记录说明它曾对一个真实缺陷保持绿灯（`figures/RUN_STATE.md:63-66`、`figures/README.md:96-101`：mathtext 缺陷 deterministically wrong，两次构建都带着它，gate 3 stayed green）。
- `figures/build_all.py` —— 能红（实测），但没有任何「坏输入必须红」的断言。
- `release/check_redlines.py` —— 全仓最敏感的闸门（凭据泄漏 + 封存堆）。`return 1` 路径存在（`:304-306`），但没有任何人演示过它会红：`release/` 下无测试、无埋雷 fixture。
- `release/enumerate.py` —— ABORT 路径退出码正确（读码），但从未被演示触发过。

**proxy / arc-recon**

- `arc-recon/redact_ledger.py` 的 `scan()` —— 它是 `arc-recon/verify.sh:56` 那一步的全部内容（"no credential or cookie value reached the ledger"）。没有任何 fixture 构造一条带 cookie 值的账本行断言它必须报红；`arc-recon/test_hygiene.py:319` 测的是测试文件内部定义的 `_cookie_value_offenders`，与 `redact_ledger.scan` 是两份代码。
- `arc-recon/client.py` 的密钥落盘防线 —— 无构造式泄漏测试；`client.py:300` 只按 header 名替换 `X-API-Key`，`request_body` / `response_body` / 其他 header 完全不过滤。
- `arc-recon/contamination.py` 的 `verify_piles_hash()` —— 只有正向断言（`test_hygiene.py:203`）。被篡改的切分文件必须 MISMATCH 这一条没有被演示过。
- `arc-recon/cut_piles.py` 的「拒绝二次切分」 —— 无测试。
- `proxy/verify_spend.sh` 的三条 grep 式检查（无 off switch / 每个 socket 都过 permit）—— 只在干净仓库上跑通，没有植入一个违例文件证明它会红。

**arms**

1. `theoria-arm/armtools/archive.py` —— 收工闸，四项义务全在这里算（对账 / 约束 8 / 成本双算 / 封存）。没有任何测试伪造一份违规 ledger 逼 `archive.constraint_8` 判 False；`theoria-arm/tests/test_arm.py:137` 打的是 `inner/surprise.py::Register.audit` —— 同一条约束的第二份实现。两份实现，一份有负控，另一份是真正写进 MANIFEST 的那份。
2. `baseline-arms/harness/audit_cells.py` —— 唯一一道会看「封存堆的 game id 有没有出现在账本里」的闸（`:222-233`），而没有任何测试往账本里塞一个封存 id 看它是不是真的红。隔壁 `audit_pool.py` 的四项负控做得很齐，对比之下这一处的空缺更显眼。
3. `cold-start-a2/run_all.py` 的 13 个子步骤 —— 每一步的退出码都诚实，但没有一步有「故意坏掉的输入必须让它红」的负控。对照组就在隔壁：`cold-start-a0` 有 `test_mutants_are_caught`，`cold-start-a3` 有 `negctl.py`。A2 两样都没有。
4. `ablation-arm/run_arm.py --twice` —— 不确定性从没被注入过一次。
5. `cold-start-a2/tools/verify_readonly.py` 和 `cold-start-a3/tools/verify_readonly.py` —— 上游只读钉，都没有「故意写一个字节进上游树」的演示。对照：`ablation-arm/tests/test_readonly.py:72` `test_the_pin_can_see_a_change_at_all` 做了。
6. `baseline-arms/harness/merge_ledger.py --check`、`baseline-arms/harness/transport_ab.py::assert_not_frozen`、`cold-start-a0/certify/fd_conformance.py`、`baseline-arms/harness/run_campaign.py --gate-only`。

### 退出码撒谎的闸门

**有实测退出码的（优先）**

- `exam/tools/run_matrix.py:328` —— 实测：只破坏一个世界（`t1-push-open` 的 oracle 答案置空）跑 `--per-class 2 --no-write`，终端最后一行印出 `REFUSED t1-push-open: marker not calibrated`（模块自己 docstring 里称为「取消资格」的条件），进程退出码 **0**。19 个世界失败、1 个成功也一样是 0。（缓解：`exam/tests/test_worldgen_papers.py` 断言 `result["refused"] == []`。）
- `worldgen/verify.py:55-78` —— 实测：本次跑打印 `green` 并 exit 0，而同一次跑里 `QC.json` 的 `family_verdict.pass=false`（`t2-lock-fragile` 直接 `NoSeparatingGuard` 抛出，L1/L2/L3a 全 false）、`QC_MUTANTS.json` 的 `mutant_verdict.pass=false`。它在上一行打了 `MEASURED MISS: …`，两道 QC 标的是 `miss` 不是 `FAIL`，所以文字层面没撒谎；但最后一个词是 `green`、退出码是 0。代价：该领地的验收入口对 QC 层的任何回归完全失聪。
- `fuzzlab/campaign.py:202` —— 实测：15/15 条不变式违反、报告里 `"violated": 15`、终端打印 `VIOLATED (15)`，退出码 **0**。明写的设计（`:199-201`），且 `fuzzlab/verify.py` 靠 pytest 阶段捕捉违反；但 README 第一行就教人单独跑 campaign。
- `release/reproduce.py:348-351` —— 实测：`1/9 reproduced`、`command-failed figures`、`manifest-stale papers/phase1-workshop`、`declared-not-run` ×2、`needs-api` ×3、`needs-ground-truth` ×1，`MAIN RETURNED: 0`，`exit=0`。九个目标里只有一个复现成功、论文图表直接 `command-failed`，退出码仍然是 0。
- `release/reproduce.py:343-345` —— 实测：`--dry-run` 也是 `return 0`（`dry run: nothing written` / exit=0）。`--dry-run` 下所有非 slow 目标被 `continue` 跳过，什么都没检查也是绿——「跑了」和「根本没跑」外观相同。`--list` 同样 exit=0。
- `release/checklist.py:226-262` —— 实测 `--dry-run` → `7 present, 3 withheld, 0 absent`，exit=0。即便某项 ABSENT、即便触发 `"no reason recorded — this needs one before release"` 这句自述的阻断条件，退出码依旧是 0。
- `arc-recon/contamination.py:338` —— 实测两例，均 EXIT CODE = 0：(1) 植入一行 `vc33-5430563c / mechanics_disclosed / 无 claims` 到临时 log → 打印 `NEEDS ADJUDICATION (excluded from clean): vc33-5430563c`；(2) 把含 `POST /api/cmd/RESET {"game_id":"ls20-9607627b"}` 的临时账本加进 `OTHER_LEDGERS` → 打印 `sealed ADDRESSED: ls20-9607627b`。`return 0 if check["matches"] else 1` 只反映 `piles.json` 的哈希。后果：`arc-recon/verify.sh:53` 那一步标签写着 "pile cut, claim set and the **sealed-contact audit**"，它会打印 `-- ok`，脚本最后打印 `VERIFY: green` ——「封存堆零接触」这条承诺的自动化绿灯，在真的发生接触时不会变红。
- `cold-start-a3/run_all.py:123` —— 实测：第 5 段就是这个仓库里最好的负控（两个被改过一处机制的世界），打印 `all caught: X | none claimed a win: Y`，然后 `main()` 无条件 `return 0`。`negctl.py:153` 自己的 `main()` 是诚实的，但 `run_all.py:91` 调的是 `negctl.run_all()`（库函数）。把 `negctl.run_all` 打桩成 `all_caught=False, claimed_a_win=True` → 打印照常、表照常生成、`run_all.main() returned: 0`、EXIT=0。第 6 段 `score_mod.run_all()` 与第 7 段账单同样只打印不判决。
- `ablation-arm/run_exhibits.py:57` —— 实测：`E3 holds=False`、`all hold: False`、`not holding: E3 ...`，EXIT=0。分表注明：这是唯一一处把理由写下来（`:8-13` docstring）、并用测试钉住这个选择（`ablation-arm/tests/test_exhibits.py:145`）的，且 E3 的翻转仍会被 pytest 抓住，性质与其他条不同。

**读码结论的**

- `exam/tools/run_selftest.py:119-123` —— 打印 `HOLE: nothing catches 'X'` / `UNCAUGHT -- a hole in the checks` 后仍返回 0。有据可查的刻意设计（`exam/verify.py:17-23`），且当前 uncaught=0，登记在案。
- `engine-rig/tools/p13_fd_dividend.py:448-471` —— `main()` 只有两个出口：无 Fast Downward 时 `return 2`，其余一律 `return 0`。而它落盘的 `same_answer`（`:317`，False = 定理改变了最优解长度／可解性，DECISIONS 称之为 unsound direction）与 `agree`（`:368`，False = bundled stub 与真 FD 对同一实例给出不同答案）为 False 时只在 `DIVIDEND.md` 里渲染成 `**NO**`（`:404`、`:444`）。对照组：`engine-rig/bench/__main__.py:162-166` 对同一类事实聚合成 `soundness_problems` 并 `return 1`。
- `proxy/spend_gate.py:1214` —— `__main__` 恒 `return 0`。`proxy/verify_spend.sh:9` 明说「要知道池子是否在上限内，跑 `python -m proxy.spend_gate`」，而它超限也退 0。（真闸门 `SpendGate.reserve/check/record` 是 raise，那一侧健康。）
- `proxy/reconcile.py:172` —— 把 `EMPTY` 与 `PASS` 一起判 0。`--run-id` 打错字、或指向一个没有 `env_step` 的 run，退出码是绿的。
- `arc-recon/precheck.py:458` —— 恒 0：确定性检查判 `FAIL` / `UNPLAYABLE` 的局只被写进报告的 `excluded` 字段，退出码不变。只有封存拒绝（2）和超预算（3）非零。
- `theoria-arm/armtools/archive.py:412-419` —— `reconcile()` 会产出字符串 `"MISMATCH"`、`constraint_8()` 会产出 `holds: False`、`sealing()` 会产出封存命中——三者都只落进 MANIFEST.json，`main()` 恒 `return 0`。活体臂的收工闸，四项义务，零个非零退出码。
- `theoria-arm/harness/run.py:211` —— 活体 runner 恒 `return 0`。与上一条合起来：theoria-arm 里除了 `preflight.py` 和 pytest，没有任何入口能以非零码结束。
- `cold-start-a0/certify/score_vs_truth.py:169` —— M6 对裁判打分，`main()` 恒 `return 0`，准确率再低也不红。
- `theoria-arm/armtools/salvage.py:184`、`theoria-arm/armtools/timeline.py:231`、`cold-start-a0/pipeline/engines_stage.py:390` —— 恒 0。分表注明这三个更像报告工具而非闸，列出只为免得被误当成闸。
- `theory-compiler/src/theory_compiler/handover.py:1489-1492` —— 打印 `form <X> refused: <why>` 之后仍然 exit 0。分表把它列在「我不确定的」而非本清单，见第 5 节。

### 构造上不可能红的死闸

- `engine-rig/fixtures/generate_all.py`（+`cart_world`/`pair_flip`/`peg4`/`sokoban`）—— `main()` 无条件返回 0，全文件无 assert/raise，任何输入都不可能让它非零。CLAUDE.md 把它和 `pytest`、`run_all` 并列成三条命令之一，读起来像一道「fixture 字节稳定」的验收；真正做这个断言的是 `engine-rig/tests/test_fixtures.py:41`。
- `battery/docs.py`（`__main__`）—— 只有 `print(write())`，没有任何非零退出路径。真正的闸是 `battery/tests/test_docs.py:10`。
- `battery/audit/{gaming,validation,discriminate,contrast,redundancy}.py` —— 全是报告器，无 raise、无退出码。
- `figures/manifest.py:152-172` —— 只有 `return 0` 一条出口，无任何拒绝路径。
- `release/checklist.py:226-262` —— 「一个原理上不能红的闸门」，`main()` 只有两处 `return 0`（实测 exit=0）。
- `release/reproduce.py`（默认 / `--all` / `--list` / `--dry-run`）—— 「能红」一列实测判 **否**。
- `proxy/spend_gate.py:1214`（`__main__`）—— 恒 `return 0`。
- `proxy/cost.py:166`、`proxy/runner.py:269` —— 报表 / 跑手，恒 0（分表注明非闸门）。
- `arc-recon/recon.py`、`arc-recon/probe_stickiness.py`、`arc-recon/precheck_resume.py` —— 恒 0 / 无判据（分表注明是采集脚本，非闸门）。
- `theoria-arm/harness/run.py:211` —— `main()` 恒 `return 0`，无任何非零路径。
- `theoria-arm/armtools/archive.py:412-419` —— `main()` 恒 `return 0`（「能红」一列读码判 **否**）。
- `theoria-arm/armtools/salvage.py:184` / `theoria-arm/armtools/timeline.py:231` —— 恒 `return 0`（分表注明是报告工具）。
- `cold-start-a0/certify/score_vs_truth.py:169` —— `main()` 恒 `return 0`。
- `cold-start-a3/run_all.py:123` —— `main()` 恒 `return 0`（「能红」一列实测判 **否**）。
- `ablation-arm/run_exhibits.py:57`（含 `--json` 分支 `:46`）—— 函数里不存在任何非零返回路径（「能红」一列实测判 **否**）。
- `worldgen/qc/diagnose_miner.py` —— 分表注明「不是闸：纯诊断打印，无判决分支，恒 0」，列出以免被当成验收入口。

---

## 第 4 节：六份分表之间的冲突或重叠

不作裁决，逐条并列。

1. **同一棵 worktree 里的已跟踪文件改动（四份表各报了一次，归因不同）**：
   - `engine-rig-theory-compiler.md` 说：收尾 `git status` 显示自己领地零改动，但同一 worktree 里 `ablation-arm/`、`cold-start-a0/a2/a3`、`worldgen/out/qc/`、`exam/artifacts/` 共 51 个已跟踪文件在 23:16-23:18 被改成真实的新内容，「这不是我跑的」，最可能的解释是另有并行普查员且那边的验收入口是就地重写产物的。
   - vs `worldgen-fuzzlab.md` 说：`worldgen/out/qc/` 下若干 `candidates.jsonl` / `engines_report.json` 被本次实跑改写（worktree 内，未提交），「这是运行 QC 的必然副作用，不是我写的文件」。
   - vs `arms.md` 说：自己跑 `cold-start-a0/a2/a3` 的 `run_all.py` 分别留下 3 / 12 / 14 个已跟踪文件被改，并把 `ablation-arm/artifacts/**` 的 10 处改动判为纯路径 + `ts`。
   - vs `exam-battery.md` 说：跑完 `python -m exam.verify` 后 `git status --porcelain exam/ battery/` 只有一行 `M exam/artifacts/build_manifest.json`，diff 只有 12 行绝对路径。
   - vs `figures-release.md` 说：本工作树 `git status` 里有 8 个 `worldgen/out/qc/**` 文件 modified，「我跑过的命令没有任何一条会写 worldgen；怀疑是同一 V11 普查里另一个领地的普查员共用了这棵工作树」，并提出「若多个普查员确实共享此工作树，则实测结果之间可能互相污染，需 RES-3 确认」。

2. **`figures/SOURCES.sha256`（第 4 关 / battery 产物漂移）**：
   - `exam-battery.md` 说：battery 领地内没有任何闸会因产物被覆盖而红，「唯一会红的是 `figures/SOURCES.sha256` 第 23 行钉着的 `205d2a6c…`——别人的领地，而且只在文件被写回树里之后才会红」。
   - vs `figures-release.md` 说：`figures/verify.sh` 第 4 关（重算的数据源哈希 == 已提交的 `figures/SOURCES.sha256`）「无负控，也无历史红记录」，且本次实跑在第 1 关就退出，未到达该关。

3. **`theory/generated*/theory.md` 与 provenance 漂移的归因**：
   - `engine-rig-theory-compiler.md` 说：`theory-compiler/tools/refresh_manifest.py --check` 现在对树里 5 个 run 全红，c7 是 4 处真实 sha256 不符（`CONTRACTS/dsl_grammar_v0.3.md` 和三个 `generators/gen_*.py` 在 run 之后又改过），「这属于正常漂移」。
   - vs `arms.md` 说：`cold-start-a0/a2/a3` 的 `theory/generated*/theory.md` 都长出一整节 "How a Turn Works"，「提交在库里的那份是旧生成器的输出」；同表在「我不确定的」里补充「也可能是我这份 worktree 的 `theory-compiler` 状态比这些臂上次生成时新——两种解释在『没有闸门会因此报红』这个结论上是一样的，但归因不同」。

4. **「打印失败词却 exit 0 是否算撒谎」的判定口径，两份表分别提出并都交回汇总方**：
   - `exam-battery.md`：`exam/tools/run_selftest.py:119-123` 打印 `HOLE` / `UNCAUGHT` 后仍 exit 0，「是有据可查的刻意设计（`exam/verify.py:17-23` 写了理由），且当前 uncaught=0，所以现在没有实际后果——但它确实是一条『印了失败字样却 exit 0』的路径，登记在案」；同表另把 `battery/run_battery.py` 判为「不算撒谎、但接近死闸」，并写明「这条判断留给 RES-3 复核」。
   - vs `worldgen-fuzzlab.md`：`worldgen/verify.py` 打 `MEASURED MISS`、把 QC 标成 `miss` 而非 `FAIL`、docstring 写清理由，「我按『报告 mismatch 的路径退出码必须非零』的字面标准判为 `部分`，但如果本次普查的标准是『文字与退出码是否一致』，它应判 `是`。这一条建议由 RES-3 定调」；`fuzzlab/campaign.py` 同理判 `部分`。
   - vs `engine-rig-theory-compiler.md`：`theory-compiler/src/theory_compiler/handover.py:1489-1492` 打印 `form <X> refused: <why>` 后 exit 0，「我倾向判它不是撒谎，但没有把握，交给汇总方定夺」。

5. **`release/enumerate.py` 的 ABORT 路径（与六份分表之外的来源冲突，非分表之间）**：
   - `figures-release.md` 说：任务书里「某个 `--dry-run` 打印 ABORT 却 exit 0」在本树复现不了。全 `release/` 只有 `release/enumerate.py:294` 一处打印 `ABORT`，紧邻的 `:297` 是 `return 2`；`git log -p -- release/enumerate.py` 显示该文件只有一次提交（`ef4e188`），且那次引入的就是 `return 2`——ABORT 路径从来没有返回过 0。原报告（`monitor/inbox/20260728T160000Z-RES-2-...md`）把两件事写在同一个 bullet 里，可核实的那一半是 `release/reproduce.py` 的 drifted → exit 0。

6. **领地边界上的单向声明（无冲突，仅记录以免被读成漏项）**：
   - `worldgen-fuzzlab.md` 说：「`exam/guard.py` 会消费 `worldgen` 的 `INDEX.json` 并有自己的闸，但它在 `exam/` 领地，本次未查」；`exam-battery.md` 确实查了 `exam/guard.py`（是/是/是，读码）。
   - `proxy-arcrecon.md` 说：「我没有评估 `release/check_redlines.py`（按指示不算 proxy 的负控）」；`figures-release.md` 确实查了它（是(读码)/否(读码)/是）。

其余入口无两表并报，也无结论相左之处。

---

## 第 5 节：各分表自己写的「我不确定的」

### 出自 `partials/engine-rig-theory-compiler.md`

- `theory-compiler/src/theory_compiler/handover.py:1489-1492` —— 打印 `form <X> refused: <why>` 后 exit 0。按 tier 制度这是「这一层本来就不该发射这个形式」的设计内结果，不是失败；但它用的正是 refused 这类失败词汇，机械扫「打印失败词却 exit 0」会命中它。我倾向判它不是撒谎，但没有把握，交给汇总方定夺。
- `theory-compiler/tools/refresh_manifest.py --check` 现在对 5 个 run 全红 —— c7 是 4 处真实 sha256 不符（`CONTRACTS/dsl_grammar_v0.3.md` 和三个 `generators/gen_*.py` 在 run 之后又改过），这属于正常漂移。但 `runs/20260728T142307Z-C9-count-lock-vocabulary/MANIFEST.json` 把自己列进了 `files[]`，而 `entries()`（行 43-44）永远跳过 MANIFEST.json，所以那一个 run 的 `--check` 在重跑写模式之前永远不可能变绿。这是工具缺陷还是那份 manifest 写错了，我没有判断依据。
- `runs/.../c7/verify.sh` 在 `set -eu` 下调用 `probe_mentions`：后者缺 ground truth 时打印 `SKIP:` 并返回 77，于是整个 verify.sh 也以 77 中止。这在我看来比静默跳过更诚实（没验成就不算过），但它会让「跳过」和「失败」在调用方眼里都是非零，是否是想要的语义我不确定。
- CLAUDE.md 写「150 tests pass, 1 skipped」，实测 engine-rig 是 9 skipped（6 例 `test_bench.py` + 1 例 `test_fd_adapter.py` + 2 例 `test_fd_ladder.py`，全因 FD 不可达）。engine-rig 也没有 theory-compiler `THEORIA_REQUIRE_LEAN=1` 那样的「本次运行必须真的跑过 FD」升级开关，所以在无 FD 的机器上这 9 道验收永远静默绿。我不确定这算不算本次普查口径下的「后面没有东西的绿灯」。
- 本次实跑均在本 worktree + scratchpad 内完成；`bench/verify.py` 的两处红色演示用的是 run 目录的 scratchpad 副本。收尾 `git status` 显示 `engine-rig/` 与 `theory-compiler/` 零改动（我的领地干净）。但同一 worktree 里 `ablation-arm/`、`cold-start-a0/a2/a3`、`worldgen/out/qc/`、`exam/artifacts/` 共 51 个已跟踪文件在 23:16-23:18 被改成了真实的新内容（非换行符差异）。这不是我跑的——我没有在那些目录下执行过任何命令。最可能的解释是同一 worktree 里另有并行普查员，且那边的验收入口是就地重写产物的（跑一次闸门就把被审对象改了）。这本身可能是另一条领地的重要发现，但不在我的判断范围内，提请汇总方核对。

### 出自 `partials/exam-battery.md`

- `exam/tools/run_selftest.py` 的红（mutant 失败 / baseline 脏）我只读码没实跑：注入故障后跑完整 fault matrix 要重跑八轮标定，成本高。逻辑本身很直白（`ok = payload["mutants"]["passed"]`，`baseline_clean` 为假则 `ok=False`），而且 `test_selftest.py:86-141` 已经在单元层面演示了坏判卷器让各变异体变红，所以我判断它是活闸，但没有进程级实测。
- battery committed 产物与 worktree 复算的差异，我只证明了「输入不同」，没有去主工作树复算来证明主树里能复现出 committed 的那六个哈希。要证明得在主树跑 `run_battery`，那会覆盖主树的产物，纪律不允许。所以「committed 产物在它自己的机器上是否可复现」仍然未知——只知道在任何 worktree 里都不可复现，且无闸报警。
- `schema_traces/MANIFEST.json` 在本 worktree 的 sha256 与 committed 产物里记录的 `manifest_sha256` 也不同（`817545a1…` vs `b71b7f64…`）。这个文件是 tracked 的，按理两边该一样；可能是主树里它被改过而未提交。我没去主树核对，所以只记录现象。
- `run_battery` 是否算「退出码撒谎」，我判为「不算、但接近死闸」：它从不打印 FAIL/ABORT 字样，只是把坏消息（臂缺失、21 个未验证 metric、underpowered）当作正常输出打印。按字面标准它不撒谎；按本次普查的精神它是一道几乎不可能红的闸。这条判断留给 RES-3 复核。
- `exam/papers/*`（出卷器）我只当作 build_papers 的被测对象扫过，没有逐个审它们的内部断言；如果那里有 raise 型的闸，我可能漏了。

### 出自 `partials/worldgen-fuzzlab.md`

- `worldgen/verify.py` 该不该算「退出码撒谎」有解释空间：它打了 `MEASURED MISS`、把 QC 标成 `miss` 而非 `FAIL`、并在 docstring 里写清了理由（「不能因为答案不好看就降 bar，也不能悄悄把退出码变绿」）。我按「报告 mismatch 的路径退出码必须非零」的字面标准判为 `部分`，但如果本次普查的标准是「文字与退出码是否一致」，它应判 `是`。这一条建议由 RES-3 定调。
- `fuzzlab/campaign.py` 的 exit 0-on-violation 同理：设计上是对的（违反是产品），且领地闸靠 pytest 阶段兜住了。我判 `部分` 是因为 README 第一行就教人单独跑 campaign。
- 我没有实跑 `fuzzlab/verify.py` 全程（第三阶段要跑 engine-rig 全套件），只跑了它的第一阶段（`pytest fuzzlab/tests -q`，56 项全绿，exit 0）与 campaign 的注入实验。`fuzzlab.verify` 会因 pytest 阶段变红这一点是读码结论。
- `worldgen/out/qc/` 下若干 `candidates.jsonl` / `engines_report.json` 被本次实跑改写（worktree 内，未提交）；这是运行 QC 的必然副作用，不是我写的文件。我另创的 `QC_MUTANTS_CENSUS.json` 已删除。
- 领地边界：`exam/guard.py` 会消费 `worldgen` 的 `INDEX.json` 并有自己的闸，但它在 `exam/` 领地，本次未查。

### 出自 `partials/figures-release.md`

- `release/enumerate.py` ABORT 路径我没有实测触发。触发需要一棵红线不清的树（缺 `.env` 或树里真有封存 payload）。本工作树位于主仓 `.worktrees/` 下，`load_api_key` 沿父目录找到了主仓的 `.env`，所以 `--mode generate` 一路绿。（我只看到并只在此复述仓库自己的掩码形式 `7171...05dd (len 36)`，未读取、未打印任何密钥明文。）故第 297 行的 `return 2` 是读码。
- `figures/verify.sh` 第 2–8 关本次未执行：第 1 关就 `exit 1` 了，所以第 3/4/5/6/7 关的「能红吗」全是读码；只有第 8 关我单独跑通了（实测）。
- `figures/verify.sh` 在 master 上当前是红的，原因是 fig06 的 `THEORIZE_LOG.md` 多了一个 `E-08` 条目。这本身是 figures 领地的一个现存缺陷（按纪律我没有修），也顺带证明第 1 关是活的。我不确定这个红是 master 本身就有，还是本工作树被并发会话改动所致。
- 本工作树 `git status` 里有 8 个 `worldgen/out/qc/**/candidates.jsonl`、`engines_report.json` 处于 modified 状态，内容级差异（非行尾）。我跑过的命令没有任何一条会写 worldgen；怀疑是同一 V11 普查里另一个领地的普查员共用了这棵工作树。我没有动它们，也没有回滚。若本次普查的多个普查员确实共享此工作树，则「实测」结果之间可能互相污染，这一点需要 RES-3 确认。
- `release/reproduce.py` 的 `_git_restore` 在我那次实跑后确实把 figures/papers 的产物还原干净了（`git status` 里无 figures/、release/、papers/ 改动）。

### 出自 `partials/proxy-arcrecon.md`

- `proxy/verify_spend.sh` 我没跑：它内部会执行 `baseline-arms/harness/ledger.py`，那是别的领地，可能写文件。所以该脚本整体是读码；它包住的 pytest 部分我单独跑了（全绿）。
- `arc-recon/verify.sh` 我没整脚本跑：它会 `contamination.py --json`，那一步会重写被跟踪的 `arc-recon/data/claim_set.json`。我只跑了它包住的 pytest，以及在临时目录里以库函数形式复现了 `contamination.main([])` 的退出码（不带 `--json`，不写任何仓库文件）。
- `contamination.OTHER_LEDGERS` 只列了 `baseline-arms/ledger.jsonl` 和 `probe_log.jsonl`。当前工作树里还有未跟踪的 `baseline-arms/out/shards/ledger.*.jsonl` / `probe_log.*.jsonl`，不在扫描范围内。模块自己的 `caveat` 承认了这点（"evidence over the files scanned, not a proof over all traffic"），所以我没把它记成撒谎，只记成覆盖面缺口——但它和「退出码撒谎」第 1 条叠加时，「零接触」的可执行证据比标签看起来弱。
- proxy 套件跑出 exit 0 与 259 个点，但 `-q` 的汇总行在本机被吞了（跑了三次都一样），所以「259 项」是数点数得来的，不是 pytest 自报的。
- 我没有评估 `release/check_redlines.py`（按指示不算 proxy 的负控），也没有检查任何主工作树文件。

### 出自 `partials/arms.md`

1. `baseline-arms` 的活体入口我一行都没跑。`campaign.py` / `run_campaign.py` / `transport_ab.py` / `probe_api.py` / `probe_action_variants.py` / `fetch_schema_traces.py` / `bare_cc.py` 都会 `urllib.request` 打 `https://three.arcprize.org`（`arc_client.py:88`）并花钱。它们的「能红/退出码」全部是读码结论。`theoria-arm/harness/run.py` 和 `armtools/preflight.py` 同理。
2. `ablation-arm/run_arm.py --twice` 的「部分负控」是我的判断，可能偏宽。`test_the_ledger_differs_only_in_its_wall_clock` 断言两份 ledger 原始字节必须不同，我把它算作「比较器确实看得见差异」的半个演示。严格说它不是对 `determinism()` 这个函数的负控。
3. 我没有为每一道闸都尝试实际逼红。只对 `a0-spike/.../make_manifest.py --verify`（改摘要）和 `cold-start-a3/run_all.py`（打桩负控）做了主动的逼红实验。其余「能红」列的读码项，我读的是返回语句本身，没有构造坏输入。
4. cold-start-a0 / cold-start-a2 属于 theory-compiler 轨。CLAUDE.md 写着 `/cold-start-a0/` 对 engine-rig 轨「off limits」。本次任务点名要求普查它们，我只在一次性 worktree 副本里读代码 + 跑离线 runner 和 pytest，没有修改任何东西、没有向主工作树写入。若这仍越界，请以纪律为准而非以本报告为准。
5. `theory/generated*/theory.md` 那一节 "How a Turn Works" 的多出我判定为「提交的是旧生成器输出」。也可能是我这份 worktree 的 `theory-compiler` 状态比这些臂上次生成时新——两种解释在「没有闸门会因此报红」这个结论上是一样的，但归因不同，我没有去查 `theory-compiler` 的提交历史来分辨。
6. `ablation-arm/artifacts/**` 的 10 处改动我判定为纯路径 + `ts`，是抽样看了 `a0-base/run_report.json` 和 diff 统计得出的，没有逐个文件核对。
