# b1 — monitor（盲判，14 个入口）

判定员未见任何探针输出（树里无 `verify-lab/`）。全部 `读码`。

| 入口 | 能红 | 有负控 | 退出码诚实 | 证据强度 | 证据 |
|---|---|---|---|---|---|
| monitor/_runner.py | 是 | 否 | 是 | 读码 | `_runner.py:108` `sys.exit(code if code >= 0 else 1)` 直接透传子进程退出码；`:59` `raise SystemExit("no prompt file for %s")`。全树搜 `_runner` 在 `test_*.py` 里零命中 |
| monitor/agents.py | 部分 | 否 | 否 | 读码 | 全文无 `sys.exit`/非零 `return`；`__main__`（`:211-215`）只打印 JSON。仅未捕获异常能红（`:113` `subprocess.run(["schtasks"…])`、`:198` `os.listdir(ddir)`）。`:187` 把 `"orphan": True`（认领挂死）算出来只落进 JSON，退出码恒 0。零测试命中 |
| monitor/assign.py | 是 | 否 | 部分 | 读码 | `:79` `sys.exit("%s 已有 %d 件未完成的自供条目…")`、`:107` `sys.exit("未知运维…")` → 退出 1。但 docstring `:18` 称「冲突在下发时就被挡住」，`:81-84` 领地被占用时只 `print("注意：…")` 后照常写盘并 `return 0`。零测试命中 |
| monitor/board.py | 是 | 否 | 是 | 读码 | `:172` `return 3`（HOLD-CAP-REACHED）、`:185` `return 3`（BOARD-EMPTY）、`:192`/`:202` `return 1`（not claimed by you）、`:259` `return 1`（用法错误）；`:263` `raise SystemExit(main())`。全树搜 `board` 在 `test_*.py` 里零命中 |
| monitor/bus.py | 部分 | 否 | 否 | 读码 | 六个 `cmd_*` 全部 `return 0`；`main` 的 `return 1`（`:185`）不可达（`:162` `required=True` 已由 argparse 以 2 退出）。`:139-142` 把「欠回执 %s」「⚠URGENT 未取」算出来打印，退出码仍 0。零测试命中 |
| monitor/ci_merge.py | 部分 | 否 | 否 | 读码 | `main`（`:253-279`）所有路径 `return 0`；`:199` `flag(branch, "verify gate red in %s")`、`:214` `"tests red in %s"`、`:210` `"collects nothing"`、`:166` `"touches protected root files"` 全部只写 `ci/CONFLICT-*.md` + 打印 `FLAG`，进程照样退 0。`monitor/tests/test_gate_enforcement.py:67-78` 名为 `test_ci_merge_still_refuses_a_red_verify_gate`，实为对源码字符串 grep（`assert 'verify gate red in' in source`），从未构造红分支执行 → 不算负控 |
| monitor/dispatch.py | 是 | 否 | 否 | 读码 | `:162` `sys.exit("claude CLI not on PATH")` 能红。但 `:331` `print(… "started" if ok else "FAILED" …)` 后 `via_task` 的返回值被 `main`（`:234-236`）丢弃并 `return 0` —— 起不来的 worker 与起来的 worker 退出码相同。测试里只出现为被打桩的字符串（`test_quota_autoexit.py:203,232`），无自身测试 |
| monitor/gates.py | 否 | 部分 | 否 | 读码 | `main`（`:157-180`）唯一出口 `return 0`，无任何非零路径。`:178` `print("  UNGATED (%d): %s")` 把判决打出来仍退 0（`verify.py:192-193` 明说这是刻意的「报告而非拦截」）。负控：`test_gates.py:78-88` 构造空目录/不存在目录断言 `kind=="none"`，`:98-107` 钉死本仓库的 gated/ungated 名单，是真的红侧断言，但无预注册变异体，且从未演示 `gates.py` 进程本身会红 |
| monitor/quota.py | 是 | 是 | 是 | 读码 | `:206`/`:231` `return 2`（HOLD）、`:291` `return 0 if ok else 2`、`:269` `return 3`（节流未花钱）、`:334` `return 2`（窗口仍关）。负控最强：`test_quota.py:41,111,164,244` 以坏输入断言 `quota.check()==2`、`quota.resume()==2`；`test_quota_autoexit.py:133,142,164` 断言 `ping(if_due=True)==2/3`；`tests/mutants.py:40,57` 两个预注册变异体在临时副本里复现已修缺陷；`verify_quota_exit.sh:50-70` 另有三个当场改 `quota.py` 的变异，`expect_fail` 要求套件必须变红 |
| monitor/reflex.py | 部分 | 部分 | 否 | 读码 | `main`（`:59-261`）所有 `return` 均为 0；`:265` `raise SystemExit(main())`。`:149` `"quota:HOLD"`、`:217` `"three-strikes:%s"`、`:193` `"worker-fail:%s"`、`:248` `"SUPPLY-LOW:%d"`、`:239` `FLAG` 全部只进 `reflex.log`，退出码恒 0。负控：`mutants.py:45-50` 有一个针对 `reflex.py` 的预注册变异体，由 `test_quota.py:259-277` 的 AST 断言接住 —— 但全部测试只解析源码，从不执行 `reflex.main()`；另两条是 `xfail(strict=True)` 的已知缺陷 |
| monitor/scan.py | 部分 | 部分 | 否 | 读码 | `main`（`:1923-1943`）唯一出口 `return 0`；`:1938-1942` 把 `status=="risk"` 的探针与 `severity in ("blocking","high")` 的 findings 打印出来后仍退 0（共 10 处 `"status": "risk"`）。负控：`test_gate_enforcement.py:83-97` 只测绿侧；`:114-131` 是防误报控制；`:133-142` 声称覆盖「命名了却没建的 verify.sh」，实际在测试里另写了一份 regex 而不是调 `scan.probe_verify_gates` —— 打的是规则的第二个副本 |
| monitor/verify.py | 是 | 否 | 是 | 读码 | `:196` `return 0 if result["green"] else 1`，`:200` `raise SystemExit(main())`；三阶段任一 `returncode != 0` 即进 `failed` 并打印 `RED:`。`:189-193` 明确把 ungated 领地「报告但不判红」。无任何测试或变异体演示过它变红 |
| monitor/verify.sh | 是 | 否 | 是 | 读码 | `verify.sh:9` `set -euo pipefail`，`:11` `exec python "$HERE/verify.py" "$@"` —— 退出码即 `verify.py` 的。`test_gates.py:103` 只断言 `"monitor" in survey["gated"]`，没有任何东西演示过这个门会红 |
| monitor/verify_quota_exit.sh | 是 | 是 | 是 | 读码 | `:16,26` `fail=1` 累加 + `:107-112` `exit "$fail"`。它自身**就是**负控：`:50-70` 当场把 `quota.py` 改坏三次（去节流 / 去 deadline 出口 / 只记成功），`:41-48` `expect_fail` 在套件没变红时打 `NOT DETECTED` 并 `exit 1`；`:74-92` 另以打桩抛异常证明 `--if-due` 不联网 |

判定员附注：

1. 三格判到保守（更严）一侧：`gates.py`、`bus.py`、`agents.py` 的「退出码诚实」——
   打印的不是简报列举的 `FAIL/ABORT/…` 字样，但都属于「判决算出、打印、不进退出码」。
   `gates.py` 的沉默在 `monitor/verify.py:192-193` 有明文辩护。
2. `monitor/tests/` 覆盖面高度倾斜：`quota.py` 独占三份测试 + 五个变异体；
   `_runner.py`、`agents.py`、`assign.py`、`board.py`、`bus.py` 五个入口全树零命中。
3. 判定员顺手报的一条**范围外**观察，未经核实、仅供他人复核：
   `monitor/tests/mutants.py` 的两个变异体可能已与现在的 `quota.py` 对不上。
   这属于 monitor 领地，V15 不进入，也不据此改任何判定。
4. `verify_quota_exit.sh` 的负控是就地改 `monitor/quota.py` 再 trap 还原，不是临时副本 ——
   本批一律读码，故未触发。
