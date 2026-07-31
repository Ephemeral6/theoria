# b7 — engine-rig + fuzzlab（盲判，13 个入口）

判定员未见任何探针输出（树里无 `verify-lab/`）。全部 `读码`。

| 入口 | 能红 | 有负控 | 退出码诚实 | 证据强度 | 证据 |
|---|---|---|---|---|---|
| engine-rig/engines/fd_adapter/backends.py | 是 | 是 | 不适用 | 读码 | 抛出并上冒：`:129`/`:172`/`:176` `ValueError`、`:179` `FastDownwardMissing`、`:207`/`:214` `ValueError`、`:338` `RuntimeError`（无 plan 又无证明）。负控打的就是本文件：`tests/test_fd_ladder.py:170,175,182,188,202` 五个 `pytest.raises`，`:309` `assert not backends.proves_unsolvable(...)`，`:286,:311,:316` 用 `FAKE_FD_MODE=incomplete/crash` 的假驱动逼出硬错 |
| engine-rig/engines/fd_adapter/validate.py | 是 | 是 | 不适用 | 读码 | `:27,44,47,52,61,64` 全是 `raise InvalidPlan`，函数只返回 `True` 或抛（`:36` docstring 明说不返回 False）。负控：`tests/test_fd_adapter.py:132,138,144` 三个故意做坏的计划（乱序 / 未知动作 / 半途而废）+ `pytest.raises(InvalidPlan)` |
| engine-rig/fixtures/cart_world.py | 是 | 否 | 不适用 | 读码 | `:82` `raise ValueError(direction)`；`:148,:176,:202,:209` 四处 `raise AssertionError` 自检，经 `write()` 冒到 `:243` `__main__`。负控：只有 `tests/test_fixtures.py:23,44,64-110`，全部从绿的一侧比对（字节可复现 + 形状 + 与 truth 一致），没有任何测试扰动常量去逼那四个自检开火 |
| engine-rig/fixtures/pair_flip.py | 是 | 否 | 不适用 | 读码 | `:74` `raise AssertionError("red parity is not invariant")`、`:76` `("not every adjacent pair is witnessed")`，经 `write()` 冒到 `:108` `__main__`。负控零：`tests/test_fixtures.py:29,115-144` 只断言产出的轨迹奇偶不变、每对都出现 —— 对数据的绿侧复核 |
| engine-rig/fixtures/peg4.py | 否 | 否 | 不适用 | 读码 | 全文件零 `raise`、零 `sys.exit`、零非零 `return`；`generate()`/`write()` 没有任何失败分支。负控零：`tests/test_fixtures.py:35,149-184` 全是把生成结果和手工枚举字面量对表 |
| engine-rig/fixtures/sokoban.py | 部分 | 否 | 不适用 | 读码 | 唯一抛点 `:293` `raise KeyError(name)`（`by_name`），而 `write()`/`problem_text()`/`:315 __main__` 这条实际生成路径一个失败分支都没有。负控零。`RING_STUCK`（`:271`）是故意不可解的关卡，但它是给 search / deadlock_carver 当负控的 |
| engine-rig/recheck/__main__.py | 是 | 否 | 是 | 读码 | `:50 return 2`（载入失败）、`:57 return 4`（自身崩）、`:64 return EXIT[verdict]`（REJECT→1，INCONSISTENT→3），`:68 raise SystemExit(main())`。第三问是全批最好的一格：`:11-18` 专门把「崩了」从「拒绝」里分出来。负控零：全树无 `test_*.py` 导入 `recheck.__main__` |
| engine-rig/recheck/build_cases.py | 是 | 否 | 是 | 读码 | `:645 return 1 if drifted else 0`，`:653 raise SystemExit(main())`；`:562 raise KeyError`。`:643` 打印 `DRIFTED %s` 与 `:645` 的 1 同步。负控零：`tests/test_recheck.py:378` 只有 `assert build_cases.check() == []` |
| engine-rig/recheck/verify_all.py | 是 | 部分 | 是 | 读码 | `:253 return 0 if green else 1`；`:244` 打印 `VERDICT RED` 与返回 1 同一个 `green` 变量。判 `部分`：`:193 forgeries.run_all()` 是预注册伪造目录、`MATRIX :44/:53` 预先声明两行必须 REJECT，拒绝路径在带内被演示；但唯一的测试是 `tests/test_recheck.py:406 assert verify_all.main([]) == 0`，全树没有任何东西种一个漂移去演示 `main()` 返回 1 |
| engine-rig/runs/20260728T141724Z-E5-cert-recheck/attacks/fuzz_ruleset.py | 部分 | 否 | 否 | 读码 | 在 `runs/` 目录下（冻结的一次性脚本）。`main()` 只有 `print`，没有 `return`，`:244-245 __main__` 也不包 `SystemExit`。第三问明确 `否`：`:219` 记 `"CRASH: %r"`、`:237` 记 `"goal reachable from init"`（自称 soundness break），`:240` 把 `n_breaks` 打成 JSON，进程照样 0。负控零，全树无引用 |
| engine-rig/runs/20260728T141724Z-E5-cert-recheck/manifest.py | 部分 | 否 | 不适用 | 读码 | 在 `runs/` 目录下。`:36-64 main()` 唯一出口是 `return 0`；非零只能靠 `digest()` 对缺失路径抛 `FileNotFoundError`。不打印任何判决词。另记一笔：`:57-59` 忽略 `git rev-parse` 的返回码，git 失败会静默写入空 `head_commit` |
| fuzzlab/mutation.py | 是 | 是 | 否 | 读码 | 能红：`:183 raise SystemExit("no mutant with id %r")`。负控是全批最强的一份，且直打本文件：`tests/test_mutation.py:43`（异常后 seam 必须还原）、`:59 pytest.raises(AttributeError)`、`:71`（noop 变异体必须报 inert/undetermined 而非 survived，`:95` 注释记着它曾经假绿）、`:114`（钉死的变异体必须且只能被一个具名不变量杀掉）、`:150 pytest.raises(ValueError)`。第三问 `否`：`:201` 打印 `BASELINE NOT CLEAN`、`:209-212` 打印 `SURVIVED`/`UNDETERMINED`，`:265 return 0` 无条件 —— `:263-264` 承认这是有意为之 |
| fuzzlab/props/cegis_miner.py | 否 | 是 | 不适用 | 读码 | 四个不变量全部 `return List[Finding]`；唯一的 `:91 raise Unminable` 被 `:123,:156,:205,:231` 四处全接住，`props/finding.py:96-99` 又把漏网异常转成 `raised` finding —— 本文件永远红不了，判决是数据。负控 `是`：`fuzzlab/mutants/cegis_miner.py` 预注册 8 个变异体，`expect_kill` 覆盖全部四个不变量，可执行（`python -m fuzzlab.mutation --engine cegis_miner`）。保留意见见附注 |

判定员附注：

1. 最值得看的一格是 `attacks/fuzz_ruleset.py` 的退出码：它自称在找 soundness break，
   找到了也只是打进 JSON，进程恒 0；它在 `runs/` 下且无人引用。
2. `fuzzlab/mutation.py` 的 `否` 是按判据字面判的 —— 作者在 `:263-264` 明确论证过 survivors
   不该非零；但 `:201` 的 `BASELINE NOT CLEAN` 是整轮结果作废，仍走 0。
3. `fuzzlab/props/cegis_miner.py` 的「有负控=是」有保留：变异体可执行且 `MUTATION.md`
   记录了杀死结果，但**没有任何 pytest 断言这些 kill**，而唯一的驱动器退出码恒 0 ——
   负控的结论目前只靠人读表维持。
4. 四个 fixture 里没有一个有负控：测试全部只从绿的一侧比对产出；`peg4.py` 连红的代码路径都不存在。
5. 五处 `不适用` 都是同一理由（纯库/生成器，不打印判决词也不映射退出码），不是「没查到」。
