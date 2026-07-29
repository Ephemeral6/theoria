# b6 — cold-start-a3 + theoria-arm（盲判，14 个入口）

判定员未见任何探针输出（树里无 `verify-lab/`）。全部 `读码`。

| 入口 | 能红 | 有负控 | 退出码诚实 | 证据强度 | 证据 |
|---|---|---|---|---|---|
| cold-start-a3/a3pipeline/agreement.py | 部分 | 否 | 否 | 读码 | `:396` `:421` 两条路径都 `return 0`；分歧被算出来只打到 stdout/JSON（`:409-418` 打印 agreement %、`laws agree: False`、`blind-only clauses: N`）。唯一非零是未捕异常（`:244`）。`tests/test_control.py:35-41` 只读产物 `domain_agreement.json` |
| cold-start-a3/a3pipeline/bill.py | 是 | 否 | 不适用 | 读码 | `:65` `raise SystemExit("no bills on disk — run the arms first")`；`main` `:131-138` 否则恒 0，不打印任何判决词。全树 `test_*.py` 零命中 |
| cold-start-a3/a3pipeline/certify_a3.py | 是 | 部分 | 是 | 读码 | `:210` `return 0 if cheap["green"] and lean["green"] else 1`，`:203` 打印 `RED` 与退出码一致。负控只是间接的：`negctl.py` 经 transfer 让 cheap 层真红（`tests/test_transfer.py:218` 断言 `replay_certify_green is False`），未覆盖 lean 红路径、`ensure_lean`、或 `main` 本身 |
| cold-start-a3/a3pipeline/coldstart.py | 部分 | 否 | 否 | 读码 | `:244-254` `main` 恒 `return 0`；`:214-216` 算出 `outcome="replay_mismatch"`、`:230-234` 打印 `cheap=False lean=False`，退出码不动。全树无 test 引用 |
| cold-start-a3/a3pipeline/concepts.py | 部分 | 否 | 不适用 | 读码 | `:146-154` `main` 恒 0，只打印计数与 `%d missing`，无判决词。`tests/test_sealing.py:189` 只把 `concepts.py` 列入豁免名单，不是负控 |
| cold-start-a3/a3pipeline/engines.py | 部分 | 否 | 否 | 读码 | `:80-89` `main` 恒 0；`brief()` `:69-77` 把 `exclusive=` 与 `total=` 判决打到 stdout，红了退出码不变。`test_sealing.py:76-82` 断言的是 transfer 不引用 engines，打的不是本文件 |
| cold-start-a3/a3pipeline/plan.py | 是 | 否 | 是 | 读码 | `:193` `return 0 if report.get("green") or status == "UNSAT" else 1`，UNSAT 归零并写明理由（`:116-117`）；`:62` `raise ValueError` 可冒顶。无任何测试构造 `manual_reaches_goal=False` 的红用例 |
| cold-start-a3/a3pipeline/run_l1.py | 是 | 部分 | 部分 | 读码 | `:209` `return 0 if report["green"] else 1`（green = cheap ∧ plan）；但 `:185-194` 打印 `lean RED` / `lean(T4)` 不进退出码，`:206-208` 自陈这一点。负控半分：`:105-108` 每次都编译「抽掉不变量」的 T4 真空 Lean 展品——可执行的预注册变体，但没有任何断言绑定它的结果 |
| cold-start-a3/a3pipeline/transfer.py | 部分 | 是 | 否 | 读码 | `:216-234` `main` 恒 `return 0`，即便 `:144-151` `outcome="static_certify_red"` 或 `:196-198` `"replay_mismatch"`。负控是真的：`a3pipeline/negctl.py:85-142` 原样调用 `transfer.run` 跑两个改过转移函数的关卡，`negctl.py:153` `return 0 if all_caught and none_claimed_a_win else 1`；`tests/test_transfer.py:211-218` 断言 `replay_certify_green is False`。诚实退出码在 negctl，不在本文件 |
| cold-start-a3/a3world/ground_truth.py | 部分 | 否 | 不适用 | 读码 | `:201-210` `main` 恒 0，只打印计数。`tests/test_world.py:100-115` 调 `build()` 但只比对字节稳定（绿侧）；`:191-207` 那节「negative controls」打的是 `a3_world.py` 的 L2_ONEWAY/L2_REWIRED，不是本文件 |
| cold-start-a3/a3world/score.py | 部分 | 否 | 否 | 读码 | `:172-186` `main` 恒 0，却打印 `UNSCOREABLE` 与 `mismatch` 行；`:148-153` 把 `:76-80` 自己抛的 AttributeError 收成 JSON 字段 `unscoreable`。`test_transfer.py:234-260` 只断言 `perfect is True` |
| cold-start-a3/tools/archive_run.py | 部分 | 否 | 不适用 | 读码 | `:101-112` `main` 恒 0，无判决词；`status="failed"` 也照常归档并 0（`:61-62`，按设计）。全树无 test 引用 |
| theoria-arm/harness/arc.py | 是 | 是 | 部分 | 读码 | 库模块：`:113` `raise ShortIdRefused`、`:218` `raise ArcError("ACTION%d 超出 1..7")`。负控齐全：`tests/test_arm.py:31-36` `pytest.raises(arc.ShortIdRefused)`；`:39-47` 断言 500 / 非 not-found 的 400 / 200 一律**不**重试；`:50-62` 读源码断言禁词不出现。半分在 `_send` `:157-168`：40 次未果只记 `ok: False` 返回不抛 |
| theoria-arm/inner/loop.py | 部分 | 否 | 否 | 读码 | 库模块但几乎不抛：`:192-197` RESET 失败变 `outcome="reset_failed"`；`:202-207` 吞 BudgetExhausted/CostCeilingReached；`:312-325`、`:391-392` 吞异常；判决全落进 `summary()`，而唯一驱动 `harness/run.py:170-211` `main` 恒 `return 0`。`test_arm.py:530-550` 虽从 `inner.loop` 取常量，判的却是测试内 `Fake` 类**重写的一份门控副本** |

判定员附注：

1. 「能红=部分」在本表统一指：**只有未捕获异常**能让它非零，没有任何判决驱动的非零路径。
2. 最没把握的两格：`certify_a3.py` 与 `run_l1.py` 的「有负控=部分」，均判向保守一侧。
3. `transfer.py` 是 a3 侧唯一有真负控的入口；但它的诚实退出码在 `negctl.py:153`，本文件 `main` 恒 0。
4. cold-start-a3 的测试绝大多数断言 `artifacts/*.json` 的内容而非入口本身，
   这是多数格判「有负控=否」的共同原因。
