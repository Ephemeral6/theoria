# 领地：engine-rig / theory-compiler

普查基线：worktree `v11-negative-control-census`，HEAD `baf16714985d837eda17dae6095b2bbcc5fe9531`。
本机 `lean` 在 PATH（`/c/Users/user/.elan/bin/lean`），Fast Downward **不可达**（`.toolchain/` 未构建）。
入口清单由 `__name__ == "__main__"` 全量扫描 + `verify*/check_*/guard*/validate_*/run_qc*/*.sh` glob 交叉得出，共 20 个可执行物，其中 5 个是 `fixtures/*.py` 生成器（合并为一行）。

| 入口 | 能红 | 有负控 | 退出码诚实 | 证据 |
|---|---|---|---|---|
| engine-rig/tools/validate_candidates.py | 是(实测) | 是(读码) | 是(实测) | 坏行文件 → `FAIL ... (1 rows, 7 errors)` exit 1；`artifacts/candidates.jsonl` → `OK (44 rows)` exit 0。负控：`engine-rig/tests/test_integration.py:259-286` 14 例 parametrize 变异行表 + `:289` 坏 JSON/空行 |
| engine-rig/tools/run_all.py | 是(读码) | 部分(读码) | 是(实测/读码) | 实测：写入 scratch → exit 0；对已存在文件不加 `--force` → `refusing to append` exit 2。`run_all.py:260-264` схема失败 `return 1`，`:117/:144/:155/:174` `raise RuntimeError`。负控只覆盖被调用的 validator，没有任何测试让 run_all 自己走 exit 1 |
| engine-rig/bench/__main__.py (`python -m bench`) | 是(读码) | 部分(读码) | 是(读码) | `__main__.py:162-166` `problems` 非空 → `return 1`。负控只到上游：`tests/test_bench.py:322/331/339` 钉住 `ladder.verdicts` 的三个 False；**`ladder.failures()`(bench/ladder.py:237) 与 `dividend.failures()`(bench/dividend.py:290) —— 真正喂给退出码的两个函数 —— 全仓库无测试**。本机无 FD，未实跑 |
| engine-rig/bench/verify.py | 是(实测) | 否 | 是(实测) | 实测：把 `LADDER.md` 尾部加一行 → `FAIL (1): - LADDER.md: sha256 cc037bce... manifest says 95b1aa49... -- edited after the run?` exit 1；未篡改的 `runs/20260728T072633Z-E2-fd-ladder-bench` → exit 0。负控：`grep -rn "bench.verify\|check_manifest_hashes\|rederive" engine-rig/tests` 零命中 |
| engine-rig/tools/p13_fd_dividend.py | 部分(实测) | 否 | **否(读码)** | 实测：无 FD → `no Fast Downward reachable` exit 2。`main()` (行 448-471) 除此之外**无条件 `return 0`**；`same_answer`(:317) / `agree`(:368) 为 False 时只在 DIVIDEND.md 里渲染成 `**NO**`(:404,:444) |
| engine-rig `python -m pytest` (150+ 例验收套件) | 是(读码) | 是(实测) | 是(实测) | 实测：exit 0，`.....ssss...` 9 skipped。负控：`tests/test_fd_ladder.py:59-96` 的假 Fast Downward（`FAKE_FD_MODE` = exhausted/structurally_unsat/translate_unsat/incomplete/crash）是预注册变异体，`:267-330` 六例断言每种坏行为必须被识别或硬报错 |
| engine-rig/fixtures/generate_all.py (+cart_world/pair_flip/peg4/sokoban) | **否(读码)** | 不适用 | 不适用 | `generate_all.py:8-20` `main()` 无条件 `return 0`，全文件无 assert/raise。字节稳定性这条断言实际在 `tests/test_fixtures.py:23-41`，不在这个命令里 |
| theory-compiler/tools/verify_c4.py | 是(读码) | **是(实测)** | 是(读码) | 实测：`--quick` → `pair lean=0 OK / ic3-computational OK / ic3-algebraic OK` exit 0。内建负控 `control_source()`(:93-122) 把死区图样整体平移一格后**重新生成**整份开发，观察到 `Control_pair.lean:442` Lean 报 `tactic 'decide' proved that the proposition ... is false`，`report["ok"]` 与该拒绝相与(:170-171)。`main` 行 240 `return 0 if all_ok else 1`，行 213 无 lean → 2 |
| theory-compiler/tools/verify_c8.py | 是(读码) | 部分(读码) | 是(读码) | 实测：14 项全 PASS exit 0（含 pytest 363 passed、两个包字节复算、两份答卷 24/24 与 29/29）。行 127-131 `_failures` 非空 → `return 1`。子检查的负控散在 `tests/test_handover.py:199/208/230`（拒绝单板/未定义原语/未声明事件）；第 5-6 项依赖的 `handover_exam` 无任何测试 |
| theory-compiler/runs/20260728T102343Z-c7/verify.sh | 是(读码) | **是(实测)** | 是(读码) | `set -eu` + 第 3 段 heredoc `sys.exit(1 if bad else 0)`。实测逐段跑：pytest exit 0；`probe_mentions` 7 行全 ok exit 0；第 3 段 10 份说明书全编译 + 负控 `../a0-spike/theory/theory.dsl` `refused as expected: expected a direction from [...]` exit 0。负控是脚本自带的（行 72-83：这份说明书**必须**编译失败，否则 `bad += 1`） |
| theory-compiler/tools/probe_mentions.py | 是(读码) | **是(读码)** | 是(读码) | 实测 exit 0，7 行全 ok。负控形式是预注册期望值：`EXPECTATIONS` 里 `sokoban2_x5 / first_argument / off_wall` 期望 **376** 次误判、`declared / on_wall` 期望 **52** 次 —— 坏读法若不再误判就红。行 404-408 失败 `return 1`；行 356-360 缺 ground truth 打印 `SKIP:` 并 `return 77`（非零、且明说是 SKIP） |
| theory-compiler/tools/validate_candidates_v02.py | 是(实测) | 是(读码) | 是(实测) | 实测：坏行 → `FAIL (candidates_schema@0.2, 1 row(s) read)` exit 1；`../engine-rig/artifacts/candidates.jsonl` → `OK` exit 0；`--nope` → `unknown option(s)` exit 2（行 289-299 明写「拼错的 flag 不得静默降级为宽松通过」）。负控 `tests/test_validate_candidates_v02.py` |
| theory-compiler/tools/refresh_manifest.py --check | 是(实测) | 否 | 是(实测) | 实测：树里**全部 5 个 run 的 MANIFEST 现在都是红的** —— `runs/20260728T102343Z-c7`(4 处真实 sha256 不符)、`.../C8-handover-package`、`.../C9-count-lock-vocabulary`、`.../C4-deadlock-lean`、`runs/P-10` 一律 exit 1。无任何测试导入本模块 |
| theory-compiler/tools/transcribe_deadlock_certificates.py | 是(读码) | 是(读码) | 是(读码) | 行 120-122 `return 1 if drifted else 0`，行 91 缺行 `raise SystemExit`。实测 check 模式 exit 0。负控：`tests/test_deadlock_certificate.py` 重跑同一转写并比对已提交 fixture |
| theory-compiler/tools/build_handover_packages.py --check | 是(读码) | 部分(读码) | 是(读码) | 行 172 `return 1 if failures else 0`。实测：`ok a0-cart (17 files) / ok a0-sokoban2 (15 files)` exit 0。`tests/test_handover.py:40/47/56` 只从绿的一侧比对，没有任何东西演示过 `--check` 的 FAIL 分支 |
| theory-compiler/tools/handover_exam.py mark | 是(实测) | **否** | 是(实测) | 实测：把 `a0-cart.answers.json` 里一个答案改成 `ZZZ-nonsense` → `a0-cart: 23/24 right ... name-action_vocabulary unparsed` exit 1（行 707 `return 0 if right == items else 1`）。负控：`grep -rn "handover_exam" theory-compiler/tests` 零命中 —— 整个阅卷器无测试 |
| theory-compiler `python -m pytest` (364 例) | 是(读码) | **是(实测)** | 是(实测) | 实测 exit 0，364 passed 1 skipped（lean 在场，Lean 编译真的跑了，100s）。负控：`tests/test_gen_lean_deadlock.py:140-175` `TestEmissionIsRead` 保留了四个预注册变异体（把每个 push 分支改成 `=> s` 等），每个都必须让发射器抛 `DeadlockLeanError`；`tests/test_conflict.py:386` 自称「负对照：这道检查必须有能力失败」 |
| theory-compiler/conftest.py (`THEORIA_REQUIRE_LEAN=1`) | 是(读码) | 否 | 是(读码) | 行 30-56：置 1 且无 lean 时 `raise pytest.UsageError`（pytest exit 4）。这是「防止闸门静默跳过」的元闸门。实测本机 lean 在场，`THEORIA_REQUIRE_LEAN=1 python -m pytest` → 364 passed exit 0 |
| theory-compiler/tools/build_deadlock_lean.py | 是(读码) | 部分(读码) | 是(读码) | 生成器不是闸门：行 72 无条件 `return 0`，坏证书靠 `CertificateError` 冒到顶层（exit 1）。负控在被调用的 `dc.recheck` 一侧 |
| theory-compiler/src/theory_compiler/handover.py (`python -m theory_compiler.handover`) | 是(读码) | 部分(读码) | 部分(读码) | 生成器。`_main` 行 1492 无条件 `return 0`，行 1489-1491 打印 `form <X> refused: <why>` 之后仍然 exit 0（tier 制度下「拒绝发射某一形式」是设计内结果，不是失败）。硬错误走 `HandoverError`/`ContextLeak` 异常（exit 1） |

## 点名：没有负控的闸门

- `engine-rig/bench/verify.py` —— 全仓最像「验收」的那个命令（README 里就写着 `python -m bench.verify runs/<id>`），却是唯一一个连一行测试都没有的验收器；它自己判定 run 目录能不能被相信，而没有任何东西判定过它。
- `engine-rig/bench/verify.py:134-139` —— 没有负控的直接代价，实测拿到：把 `ladder.json` 里 `gripper-02/stub-bfs` 的 `expanded` 改成 18+999 触发结构复算分支，进程不是报出漂移而是 `TypeError: not enough arguments for format string`（格式串三个占位符、参数元组只有两个，且 `name` 根本没传进去）。退出码仍是 1，但**最该说人话的那条诊断永远说不出来**——这条分支从写下起就没被执行过一次。
- `engine-rig/bench/ladder.py:237 failures()` 与 `engine-rig/bench/dividend.py:290 failures()` —— `python -m bench` 的退出码完全由这两个函数的返回值决定，而测试只钉到了上游的 `verdicts()`。verdict 为 False 到进程 exit 1 之间那一段接线，没有任何东西验过。
- `theory-compiler/tools/handover_exam.py` —— 交接包验收的阅卷器，`verify_c8` 的第 5、6 项检查整个建在它上面，而全仓库没有一个测试导入过它。我实测它能红（24 题错 1 题 → exit 1），但这个演示是我现在造的，不在仓库里。
- `theory-compiler/tools/refresh_manifest.py` —— provenance 漂移的唯一自动检测器，无测试；而且它现在对树里**每一个** run 都返回 1，说明没人在跑它（详见「我不确定的」）。
- `theory-compiler/tools/build_handover_packages.py --check` —— 字节复算的 FAIL 分支无人演示过；已有测试只从「应该相等」那一侧比对。
- `engine-rig/fixtures/generate_all.py` —— **死闸**（严格说：一个长得像闸门的生成器）。`main()` 无条件返回 0，全文件无 assert/raise，任何输入都不可能让它非零。CLAUDE.md 把它和 `pytest`、`run_all` 并列成三条命令之一，读起来像一道「fixture 字节稳定」的验收；真正做这个断言的是 `tests/test_fixtures.py:41`。

## 点名：退出码撒谎的闸门

- `engine-rig/tools/p13_fd_dividend.py:448-471` —— `main()` 只有两个出口：无 Fast Downward 时 `return 2`，其余一律 `return 0`。而它计算并落盘的两个字段正是本仓库定义的不可接受结果：`same_answer`（行 317，False = 定理改变了最优解长度／可解性，DECISIONS 称之为「unsound direction」）与 `agree`（行 368，False = bundled stub 与真 FD 对同一实例给出不同答案）。两者为 False 时只在 `DIVIDEND.md` 里渲染成 `**NO**`（行 404、444），退出码不动。对照组：`engine-rig/bench/__main__.py:162-166` 对同一类事实聚合成 `soundness_problems` 并 `return 1` —— 同一个仓库里，同一个判断，一个报警一个不报。（本机无 FD，仅读码 + 无 FD 路径实测 exit 2。）

## 我不确定的

- `theory-compiler/src/theory_compiler/handover.py:1489-1492` —— 打印 `form <X> refused: <why>` 后 exit 0。按 tier 制度这是「这一层本来就不该发射这个形式」的设计内结果，不是失败；但它用的正是 refused 这类失败词汇，机械扫「打印失败词却 exit 0」会命中它。我倾向判它不是撒谎，但没有把握，交给汇总方定夺。
- `theory-compiler/tools/refresh_manifest.py --check` 现在对 5 个 run 全红 —— c7 是 4 处真实 sha256 不符（`CONTRACTS/dsl_grammar_v0.3.md` 和三个 `generators/gen_*.py` 在 run 之后又改过），这属于正常漂移。但 `runs/20260728T142307Z-C9-count-lock-vocabulary/MANIFEST.json` **把自己列进了 `files[]`**，而 `entries()`(行 43-44) 永远跳过 MANIFEST.json，所以那一个 run 的 `--check` 在重跑写模式之前**永远不可能变绿**。这是工具缺陷还是那份 manifest 写错了，我没有判断依据。
- `runs/.../c7/verify.sh` 在 `set -eu` 下调用 `probe_mentions`：后者缺 ground truth 时打印 `SKIP:` 并返回 77，于是整个 verify.sh 也以 77 中止。这在我看来比静默跳过更诚实（没验成就不算过），但它会让「跳过」和「失败」在调用方眼里都是非零，是否是想要的语义我不确定。
- CLAUDE.md 写「150 tests pass, 1 skipped」，实测 engine-rig 是 9 skipped（6 例 `test_bench.py` + 1 例 `test_fd_adapter.py` + 2 例 `test_fd_ladder.py`，全因 FD 不可达）。engine-rig 也没有 theory-compiler `THEORIA_REQUIRE_LEAN=1` 那样的「本次运行必须真的跑过 FD」升级开关，所以在无 FD 的机器上这 9 道验收永远静默绿。我不确定这算不算本次普查口径下的「后面没有东西的绿灯」。
- 本次实跑均在本 worktree + scratchpad 内完成；`bench/verify.py` 的两处红色演示用的是 run 目录的 scratchpad 副本。收尾 `git status` 显示 `engine-rig/` 与 `theory-compiler/` **零改动**（我的领地干净）。但同一 worktree 里 `ablation-arm/`、`cold-start-a0/a2/a3`、`worldgen/out/qc/`、`exam/artifacts/` 共 51 个已跟踪文件在 23:16-23:18 被改成了真实的新内容（非换行符差异）。这不是我跑的——我没有在那些目录下执行过任何命令。最可能的解释是同一 worktree 里另有并行普查员，且那边的验收入口是**就地重写产物**的（跑一次闸门就把被审对象改了）。这本身可能是另一条领地的重要发现，但不在我的判断范围内，提请汇总方核对。
