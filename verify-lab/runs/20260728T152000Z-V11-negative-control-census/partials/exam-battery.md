# 领地：exam / battery

| 入口 | 能红 | 有负控 | 退出码诚实 | 证据 |
|---|---|---|---|---|
| `exam/verify.py`（五阶段总闸） | 是（实测） | 部分（读码） | 是（实测） | 全量跑一次 `python -m exam.verify` → `GREEN`，exit 0，287 tests passed，determinism identical；各阶段的红我单独演示过（见下），但**没有任何测试演示过 verify.py 这个聚合器本身会返回 1**——`main()` 的 `failed` 汇总逻辑（verify.py:96-106）无人测过 |
| `exam/tools/build_papers.py`（漏题闸） | 是（实测） | 是（实测+读码） | 是（实测） | 我在 verdict 卷第一题的 `paper` 里植入它自己的 leak probe，`bp.main(["verdict"])` 抛 `LeakageError: p15-verdict-a2 leaks its own answers: [... 'check': 'probe' ...]`，退出码 1，且**没有写出任何文件**（检查在写盘之前）。仓库自带负控：`exam/tests/test_core.py:76` `test_leak_probe_fires_on_a_planted_answer`、:85 结构泄漏、:148 `test_a_point_value_that_encodes_the_answer_is_a_leak` |
| `exam/leakage.py::check_paper`（四检合一） | 是（实测） | 是（读码） | 是（读码） | `check_paper` 在 leakage.py:321 与 :340 两处 `raise LeakageError`；`probe_hits` 对 <3 字符探针也 raise（:64）。`test_core.py` 13 处 `pytest.raises`，含"干净卷必须过"的反向控制（:110, :155, :160, :173, :189） |
| `exam/tools/run_exam.py --calibrate`（判卷器标定闸） | 是（实测） | 是（实测） | 是（实测） | 注入 `selftest.FAULTS["pays_for_silence"]` 后 `run_exam.main(["--calibrate"])` 返回 **1**，并逐条打印 `verdict/null: 17 of 17 items are not 'unanswered'`。未注入时 verify 里同一阶段 `ok`（四卷 oracle=1.0000 / null=0.0000 全 CALIBRATED） |
| `exam/grading/calibration.py::assert_calibrated` | 是（实测） | 是（读码） | 是（读码） | 四个预注册假被试（oracle 必须 1.0、null 必须 0.0、memoriser、bluffer）+ 结构检查；失败 `raise ExamError`（calibration.py:330）。这是全仓最像 `check_coverage.py --self-test` 的样板：**已知满分/已知零分的假被试是代码里跑出来的，不是文档承诺** |
| `exam/tools/run_selftest.py`（变异体+故障注入） | 是（读码） | 是（实测+读码） | 部分（读码） | 8 个故障注入 + 6 类变异体；实跑结果 `mutants: all passed / faults: 8 injected, 0 uncaught, baseline clean`。红路径：mutant 失败或 baseline 脏 → return 1（:119-123）。**未被捕获的故障 (`HOLE: nothing catches ...`) 打印后仍 exit 0**——这是写进 docstring 的刻意设计（verify.py:17-23），不是疏忽；当前 0 个 uncaught，所以现在没有实际说谎 |
| `exam/grading/selftest.py`（变异体电池 / FAULTS） | 是（读码） | 是（读码） | 是（读码） | `PRE_REGISTERED` 六条算术恒等式 + `FAULTS` 八种坏判卷器。负控之负控：`test_selftest.py:86` "会为沉默付钱的判卷器必须让 drop_exact 变红"、:96 :103 :123 各钉一种坏法，:142 "注入的故障必须被完全还原"，:152 "fault matrix 必须在干净基线上跑并全部抓到" |
| `exam/tools/run_matrix.py`（20 世界判卷矩阵） | 是（读码） | 部分（实测） | **否（实测）** | 见下方点名。`main()` 只有 `return 0 if result["worlds_in_matrix"] else 1`（:328）。pytest 里 `test_worldgen_papers.py` 断言 `result["refused"] == []`，所以这条谎话被 pytest 兜住了；但入口自己的退出码不诚实 |
| `exam/guard.py`（零网络 / 封存堆 / 合成世界） | 是（读码） | 是（读码） | 是（读码） | `no_network()` 让 socket 抛；`assert_synthetic_world` 四条 raise（:113/:124/:133/:137）。负控：`test_core.py:212` `test_no_network_makes_sockets_raise`、:226 `test_a_sealed_game_is_refused`、:236、:244 |
| `exam/tools/archive_run.py` | 部分（读码） | 否 | 是（读码） | 唯一非零路径是缺参数 `return 2`（:131）。它把 `worktree_dirty: bool(git status --porcelain)` 写进 MANIFEST（:95）**却从不据此拦任何东西**——是记录器不是闸 |
| `pytest exam/tests`（287 项） | 是（实测） | 是（读码） | 是（实测） | 实跑 287 passed / 97.83s。多处显式负控测试（`test_worldgen_papers.py:92` 与 :238 都自称 "the negative control"） |
| `exam/verify.py::_determinism`（两解释器字节一致） | 是（读码） | 否 | 是（读码） | 只哈希**四张卷面**（`module_for(t).build().sheet(digest())`），不哈希 `build_manifest.json`、不哈希 truth、不哈希 selftest.json。绝对路径缺陷正好落在它的盲区里 |
| `battery/run_battery.py` | 部分（实测） | 部分（实测） | 部分（实测） | 只有两条红路径：无 run 时 `return 1`（:260，实测：`--ledger <空文件> --a0 none` → exit 1），以及 guard 抛异常（实测见下行）。**其余一切都绿**：整条 schema_repro 臂消失、21 个 metric 从未在控制臂上验证过、process 1 判 `underpowered`——全部只打印，exit 0 |
| `battery/guard.py`（封存堆 + 切分完整性） | 是（实测） | 是（实测+读码） | 是（实测） | 用 piles.json 里第一个封存 id 造了一行 ledger 喂进去：`SealedPileError: 'bp35-0a0ad940' is in the sealed pile`，退出码 **1**。`test_guard.py` 9 处 `pytest.raises`：全 id/短 id/大小写/空白/未知 id/篡改摘要/无摘要/双堆重叠/批量首行即停 |
| `pytest battery/tests`（214 项） | 是（实测） | 是（读码） | 是（实测） | 实跑 214 passed / 0.99s。`test_metrics.py` 全是手算得出的已知输入→已知输出；`audit/exploits/*` + `test_exploits_*.py` 是更强的一种负控：造出专门骗某个 metric 的合成 run，并断言 metric 确实被骗到 |
| `battery/docs.py`（`__main__`） | 否（读码） | 不适用 | 不适用 | 死闸：`__main__` 里只有 `print(write())`，没有任何非零退出路径。真正的闸是 `test_docs.py:10`（committed METRICS.md 必须等于 `docs.render()`），那条是活的 |
| `battery/metrics/*`（判分正确性） | 是（读码） | 是（读码） | 不适用 | metric 本身不退出；它的"闸"是 `test_metrics.py` 的手算值 + `audit/exploits` 的对抗样本。`Value.status`（`ok`/`not-applicable`/…）是数据不是退出码 |
| `battery/audit/{gaming,validation,discriminate,contrast,redundancy}.py` | 否（读码） | 不适用 | 不适用 | 全是报告器，无 raise、无退出码。`validation_material.json` 说"21 个 metric 无控制臂验证"，`discrimination.json` 说 `underpowered`——都只是 JSON 字段，没有任何东西把它们变成非零退出 |
| battery 的"一条命令总闸" | — | — | — | **不存在**。`exam/` 有 `verify.py`，`figures/` 有 `verify.sh`，`battery/` 两者都没有；README 只列了三条互不汇总的命令 |

## 点名：没有负控的闸门
- `exam/verify.py:96-106` —— 这是整个 exam 领地唯一的总闸，可它的 `failed` 汇总逻辑从没被演示为会红；一个阶段返回非零时它是否真的 return 1，只有代码能证明，没有任何测试证明。
- `exam/tools/run_matrix.py:328` —— 没有测试钉住 `main()` 的返回值；`refused` 非空时它返回什么，是我实测才知道的（返回 0）。
- `battery/run_battery.py:258-260` —— "no runs found → return 1" 这条路径没有任何测试断言过退出码：`test_docs.py:58-61` 正好用空 ledger 调了它，却把返回值丢掉并 `except SystemExit: pass`，所以这条闸的红从未被演示。
- `battery/artifacts/*.json` 整体 —— battery 里**没有任何东西**把提交的产物和一次复算对比。`test_determinism.py` 只比"同一个 fixture 跑两遍是否一致"，它比的是临时目录里的两份，不是仓库里的那份。产物漂移在 battery 领地内是一盏永远不会红的灯（真正会红的是 `figures/SOURCES.sha256`，那是别人的领地）。
- `exam/verify.py::_determinism` —— 只对四张卷面做字节比对，`build_manifest.json` / `truth/` / `selftest.json` 全在闸外。这就是绝对路径缺陷能长期存活的原因。
- `exam/tools/archive_run.py:95` —— `worktree_dirty` 被写进每一份 MANIFEST 却从不拦人；一个脏工作树归档出来的 run 和干净的长得一样合法。

## 点名：退出码撒谎的闸门
- `exam/tools/run_matrix.py:328` —— `main()` 只看 `worlds_in_matrix` 是否非零。**实测**：我只破坏一个世界（`t1-push-open` 的 oracle 答案置空）跑 `--per-class 2 --no-write`，终端最后一行印出 `REFUSED t1-push-open: marker not calibrated`——正是这个模块自己 docstring 里称为"取消资格"的条件——进程退出码 **0**。19 个世界失败、1 个成功也一样是 0。（缓解：`exam/tests/test_worldgen_papers.py` 断言 `result["refused"] == []`，所以 pytest 会替它红；但入口本身在撒谎。）
- `exam/tools/run_selftest.py:119-123` —— 打印 `HOLE: nothing catches 'X'` / `UNCAUGHT -- a hole in the checks` 后仍返回 0。这是**有据可查的刻意设计**（verify.py:17-23 写了理由：把发现漏洞和构建损坏区分开），且当前 uncaught=0，所以现在没有实际后果——但它确实是一条"印了失败字样却 exit 0"的路径，登记在案。

## 两条线索的核实结果
- battery 复跑漂移：**属实，但原因不是不确定性，而是输入不同；并且没有任何闸门会因此报红** —— 命令：`python -m battery.run_battery --out <tmp/bat1>`（exit 0），逐个对比 `battery/artifacts/*.json`：`arm_contrast` / `capability_spectrum` / `discrimination` / `discrimination_arms` / `redundancy` / `validation_material` 六个哈希全变，只有 `gaming_audit` 不变（它不读 run，只读注册表）。**七分之六，含 `capability_spectrum.json`，与报告一致。** 再跑第二遍 `--out <tmp/bat2>`，七个产物与 bat1 **全部字节相同**——所以模块本身是确定的。差异来自输入：committed 版 `n_runs=95`、五条臂（含 `schema_repro`）、六个 campaign；worktree 复算 `n_runs=41`、四条臂、三个 campaign，ledger shard 文件名都不一样（committed 是 `ledger.ar25/g50t/sk48/tn36.jsonl`，本 worktree 是 `ledger.a7-*.jsonl`），`schema_traces` 只剩一个 44KB 的 MANIFEST.json、payload 未 checkout（gitignore 的文件不进 linked worktree，adapter 自己的注释就写了"silently finds nothing"）。**关键点：整条控制臂消失，进程照样 exit 0**，只在 stdout 打了一行 `schema arm available: False`。而 `run_battery` 的 `--out` 默认值就是 `battery/artifacts`，所以任何人在 worktree 里裸跑一次这条命令，就会用 41 run 的结果覆盖 95 run 的提交产物，而 battery 领地内没有一道闸会红。（唯一会红的是 `figures/SOURCES.sha256` 第 23 行钉着的 `205d2a6c…`——别人的领地，而且只在文件被写回树里之后才会红。）
- exam 绝对路径：**属实** —— `exam/artifacts/build_manifest.json` 有 12 处 `C:\Users\user\Desktop\theoria\.worktrees\v4-exam-selftest\...`（`sheet_path` / `key_path` / `cheater_brief_path` 各四份）。**有没有闸抓到它：没有。** 实测：我在本 worktree 完整跑了一遍 `python -m exam.verify`，结果 `GREEN`，exit 0，五个阶段全 ok，determinism 阶段两个 PYTHONHASHSEED 下四张卷面哈希完全一致。跑完 `git status --porcelain exam/ battery/` 只有一行：`M exam/artifacts/build_manifest.json`，`git diff` 显示改动**只有那 12 行路径**（`v4-exam-selftest` → `v11-negative-control-census`），其余字节全同。也就是说：exam 的产物只有这一个文件不可字节复现，而唯一可能抓它的 determinism 闸只哈希卷面、不哈希 manifest——闸和缺陷完美错开。

## 我不确定的
- `exam/tools/run_selftest.py` 的红（mutant 失败 / baseline 脏）我只读码没实跑：注入故障后跑完整 fault matrix 要重跑八轮标定，成本高。逻辑本身很直白（`ok = payload["mutants"]["passed"]`，`baseline_clean` 为假则 `ok=False`），而且 `test_selftest.py:86-141` 已经在单元层面演示了坏判卷器让各变异体变红，所以我判断它是活闸，但没有进程级实测。
- battery committed 产物与 worktree 复算的差异，我只证明了"输入不同"，**没有**去主工作树复算来证明主树里能复现出 committed 的那六个哈希。要证明得在主树跑 `run_battery`，那会覆盖主树的产物，纪律不允许。所以"committed 产物在它自己的机器上是否可复现"仍然未知——只知道在任何 worktree 里都不可复现，且无闸报警。
- `schema_traces/MANIFEST.json` 在本 worktree 的 sha256 与 committed 产物里记录的 `manifest_sha256` 也不同（`817545a1…` vs `b71b7f64…`）。这个文件是 tracked 的，按理两边该一样；可能是主树里它被改过而未提交。我没去主树核对，所以只记录现象。
- `run_battery` 是否算"退出码撒谎"，我判为"不算、但接近死闸"：它从不打印 FAIL/ABORT 字样，只是把坏消息（臂缺失、21 个未验证 metric、underpowered）当作正常输出打印。按字面标准它不撒谎；按本次普查的精神它是一道几乎不可能红的闸。这条判断留给 RES-3 复核。
- `exam/papers/*`（出卷器）我只当作 build_papers 的被测对象扫过，没有逐个审它们的内部断言；如果那里有 raise 型的闸，我可能漏了。
