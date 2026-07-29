# b8 — exam / figures / ablation-arm（盲判，17 个入口）

判定员未见任何探针输出（树里无 `verify-lab/`）。全部 `读码`。

| 入口 | 能红 | 有负控 | 退出码诚实 | 证据强度 | 证据 |
|---|---|---|---|---|---|
| ablation-arm/ablcore/certify_abl.py | 是 | 是 | 不适用 | 读码 | `:75` `raise ObligationCut(...)` 无条件抛；`:84` `bus.raise_` 可抛 KeyError。负控打的就是本文件：`ablation-arm/tests/test_incision.py:42-45` `pytest.raises(certify_abl.ObligationCut)`，`:48-69` AST 遍历全臂断言无人调用 `expensive`，`:72-81` 钉住词表 |
| ablation-arm/ablcore/surprise.py | 是 | 是 | 不适用 | 读码 | `:77` `raise ValueError`（未知 kind）、`:80` `raise ImpossibleSurprise`；均冒到调用者（`run_arm.py:233` 未捕获）。负控 `tests/test_incision.py:168-183`：`pytest.raises(ImpossibleSurprise)` + `assert len(bus)==0`（被拒的意外不得落进 bus）+ `ablated=False` 时七种必须齐全 |
| ablation-arm/exhibits/e1_a0.py | 是 | 否 | 是 | 读码 | `:132` `return 0 if report["holds"] else 1`，`:136` `raise SystemExit(main())`。全树搜 `e1_a0` 只有 `tests/test_exhibits.py:28-42`（全绿侧断言 holds is True）与 `:45-50`（读源码文本 grep）；无任何输入被构造成让 `holds` 为假 |
| ablation-arm/exhibits/e2_a2.py | 是 | 部分 | 是 | 读码 | `:201` `return 0 if report["holds"] else 1`。`test_exhibits.py:55-92` 全在绿侧。唯一可执行负控打的是**依赖模块**：`tests/test_readonly.py:72-84` 用伪造的 `before` 让 `pin.changed` 报差异，支撑 `upstream_unchanged` 字段 —— 不是本文件的 `holds` 分支 |
| ablation-arm/exhibits/e3_charitable.py | 部分 | 否 | 否 | 读码 | `:239` `return 0` 恒真，`constructible=False` 写死（`:186`）；只有未捕获异常能红。`test_exhibits.py:96-131` 断言 `holds is False` 但那是未变异输入下的计算值，`:145-148` 反过来断言 `run_exhibits.main([])==0`。打印 `holds: False` 而 exit 0；`run_exhibits.py:8-13` 明写这是有意为之 |
| exam/grading/mark.py | 是 | 是 | 否 | 读码 | 红：`:40`/`:57`/`:60` `raise ExamError`。负控直打本文件：`exam/tests/test_core.py:289-300` 两个 `pytest.raises(ExamError)`；`exam/grading/selftest.py:396-399` `_fault_pays_for_silence` patch `mark_mod.unanswered`、`:455-476` `_fault_blends_the_pair` patch `mark_mod.confusion`，`tests/test_selftest.py:86,96,103,123,152` 断言这些故障必须被抓到。不诚实处：`:70-76` 算出 `rubric_digest_matches: False` 并写入 `warning`，只落进 `report_meta`；全树无消费者据此非零退出 |
| exam/grading/registry.py | 是 | 否 | 不适用 | 读码 | 红：`:52-56` 重复 rubric id 抛 ExamError、`:74-76` 未知 id 抛 ExamError。全树只在绿侧调用；`test_adaptation.py:606` 那句 "registry refuses duplicates" 只是 docstring 散文 |
| exam/model.py | 是 | 是 | 不适用 | 读码 | 红：`:132-135` 未知题型、`:137-140` 重复 item_id，均在 `Paper.__post_init__` 抛 ExamError。负控 `tests/test_core.py:64-66`、`:69-71` 两个 `pytest.raises(ExamError)` 直打这两条 |
| exam/papers/handover.py | 是 | 部分 | 不适用 | 读码 | 红：14 处 `raise HandoverError`，3 处 `UnrenderableManual`。负控是真变异但打的是别的性质：`tests/test_handover.py:390-404` 把每个 item 的 truth 毒化后要求 `author_answers` 逐字节不变；`:295-299`/`:363-367` null/bluffer 故意坏提交必须低分。**该文件全篇零 `pytest.raises`**，十余处 HandoverError 无一被演示过会抛 |
| exam/papers/heldout_worldgen.py | 是 | 是 | 不适用 | 读码 | 红：`:155` 配额不可行抛 ExamError、`:297` 未知 calibration mode。负控直打本文件：`tests/test_worldgen_papers.py:126-135` monkeypatch `hw.plan` 返回 `feasible: False`，`pytest.raises(ExamError)` 并断言错误里含 `hint` |
| exam/papers/worldgen_port.py | 是 | 否 | 不适用 | 读码 | 红：`:95` 与 `:101-104` `raise WorldNotBuilt`。全树搜 `WorldNotBuilt` 在 `test_*.py` 里零命中；`tests/test_worldgen_papers.py:171-173` 的 `pytest.raises(UnknownGameError)` 打的是 `exam/guard.py` |
| figures/fig02_bill_shape.py | 是 | 部分 | 否 | 读码 | 红：11 处 `raise`，冒到 `:1574` `__main__`，被 `figures/build_all.py:113-119` 捕获后 `return 1`。负控是这批唯一的真货，但**红的是别人**：`figures/check_coverage.py:230-279` `self_test()` 把 `sources.DISCOVERY` 收窄回 pre-P8 规则并要求探针报出两个受害 run，`:283-293` 失败 `return 1`；它 import 的是 fig02 并调 `fig02.extract()`。不诚实：`:861-864` 打印 `MISMATCH (not reconciled) …`、`:659-664` 两条 turn 轴不一致，都只进 `notes`，exit 0 |
| figures/fig03_capability_spectrum.py | 是 | 否 | 部分 | 读码 | 红：13 处 `raise ValueError`；`:862` `__main__`。无 pytest 覆盖 `figures/`；`check_coverage.py` 只 import fig02；`verify.sh:161-191` 第 7 关是对全部 `fig*.py` 的 AST 静态禁令，是 lint 不是负控。诚实性：`:351-355` 真矛盾会 raise，但 `:403-412` 算出 `arm_contrast.json is stale` 只写进 notes，exit 0 |
| figures/fig04_a3_transfer.py | 是 | 否 | 否 | 读码 | 红：17 处 `raise ValueError`；`:1305` `__main__`。无任何负控。不诚实三处，全是 notes + exit 0：`:436-439` `DISAGREE on … (not reconciled)`、`:517` `cost_to_first_plan DISAGREES between ledger and bill_table`、`:601-605` `provenance DISAGREES with itself` |
| figures/fig05_a2_repair_loop.py | 是 | 否 | 是 | 读码 | 红：16 处 `raise ValueError/KeyError`；`:1795` `__main__`。无负控。诚实：查到的每一处交叉核对不一致都 raise 而非记录 —— `:349-353`、`:387`、`:424-427`、`:436`；notes 段未见「只报不红」式的分歧 |
| figures/fig06_concept_timeline.py | 是 | 否 | 否 | 读码 | 红：16 处 `raise ValueError/KeyError`；`:1537` `__main__`。无负控。不诚实：`:793-798` `Differences, reported not reconciled: …`，以及 `:770-783` concept_accounts.json 与 THEORIZE_LOG O-04 的 bit 数分歧，均只进 notes |
| figures/fig07_a0_vs_a0prime.py | 是 | 否 | 否 | 读码 | 红：`:134` `ZeroDivisionError`，6 处 `raise ValueError`；`:1194` `__main__`。无负控。本批最直白的一处：`:360-365` `notes.append("cross-check FAILED, reported not reconciled: …")` —— 判决算了、打了 FAILED、进程仍 exit 0 |

判定员附注：

1. 三格把握较低，已按保守侧判：`e3_charitable` 的「能红」；`e2_a2` 的「有负控」（负控在 `pin`，
   不在本文件）；`fig03` 的「退出码诚实」。
2. `figures/` 的负控只有一个，就是 `check_coverage.py --self-test`（`verify.sh` 第 8 关），
   它 import 并审计 **fig02 一家**；fig03–fig07 没有任何东西演示过它们会红。
3. `verify.sh` 第 3 关（两遍构建逐字节 diff）、第 5/6/7 关对全部图脚本生效，但都是
   「跑绿了才通过」的门，没有一关演示过自己会打红，按简报未计为负控。
4. 「退出码诚实」判 `否` 的六处里，`figures/` 那四处与 `run_exhibits.py:8-13` 都在源码里把
   「只报不红」写成了**有意的设计**；判据是机械的故仍判 `否`，但这不是疏忽。
5. `exam/` 库模块无 `main` 无打印，第三问填 `不适用` 而非 `是`。
