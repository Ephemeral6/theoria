# b9 — papers / worldgen / arc-recon / proxy（盲判，17 个入口）

判定员未见任何探针输出（树里无 `verify-lab/`）。全部 `读码`。未联网、未读 `.env`、未碰封存堆。

| 入口 | 能红 | 有负控 | 退出码诚实 | 证据强度 | 证据 |
|---|---|---|---|---|---|
| arc-recon/runs/20260728T150228Z-S10-invariant-on-resource/append_sync.py | 部分 | 否 | 部分 | 读码 | `:32,38` 两条路径都 `return 0`，`:41-42` `sys.exit(main())`；只有 `:28` `io.open(PATH)` 失败时异常冒顶才非零。全树搜 `append_sync` 在 `test_*.py` 里零命中。docstring `:5` 称「refuses if the tag is already present」，实现是 `:31-32` 打印 `already appended` 后 `return 0` |
| arc-recon/runs/20260728T150228Z-S10-invariant-on-resource/proposed/board_log_invariants.py | 是 | 是 | 是 | 读码 | `:145` `return 0 if report["clean"] else 1`，`:131` 控制不响时 `return 2`；负控在文件内且走 CLI：`:108-119` `_planted_divergence()` + `:124-126` 断言 `log_only==["B-two"] / disk_only==["C-three"] / unparsed==1`；`:144` 打印 `DIVERGED` 与 `:145` 的 1 一致 |
| arc-recon/runs/20260728T150228Z-S10-invariant-on-resource/proposed/concurrency_invariants.py | 是 | 是 | 是 | 读码 | `:193` `return 0 if report["clean"] else 1`，`:174-175` 控制不响 `return 2`；负控 `:158-163` `_planted_overrun()`/`_planted_unmeasured()`，`:169` 断言两条都必须响；`:188-192` 打印 `VIOLATION`/`UNMEASURED` 后确实非零 |
| arc-recon/tools/ledger_invariants.py | 是 | 是 | 是 | 读码 | `:416,424` `return 0 if ... else 1`；`:368-376` `assert_clean` 抛 `LedgerInvariantError`。负控打的就是本文件：`test_ledger_invariants.py:118-123`（17 种形状逐个种入并断言变红）、`:232-252`（落盘样本 + `pytest.raises`）、`:222-229`（畸形行不算干净）；`arc-recon/verify.sh:65-66` 把它接进绿灯且 `:80` `exit "$fail"` |
| papers/phase1-workshop/assemble.py | 部分 | 否 | 不适用 | 读码 | `:24` `def main() -> None`，`:35` 直接 `main()` 无 `sys.exit`，无任何非零返回/raise；仅 `:27` `read_text` 遇非 UTF-8 时异常冒顶。全树零 `test_*.py` 命中；`release/reproduce.py:87-89` 只跑它并比哈希（单向绿比对） |
| papers/phase1-workshop/figures/check_figure_parity.py | 是 | 否 | 部分 | 读码 | `:275` `return 1`、`:280` `raise SystemExit(main())`、`:90` `_cell` 多命中时 `raise ValueError`。全树零 `test_*.py` 命中，无 `--self-test`。`:265` 打印 `DISAGREE` 确实退 1，但 `:242-246` 落入 `KNOWN_DISAGREEMENTS` 的分歧与 `:261` 的 `ONE-SIDED` 都只打印、仍退 0（`:46-50` 声明为刻意豁免） |
| papers/phase1-workshop/figures/fig1_concept_timeline.py | 部分 | 否 | 不适用 | 读码 | `:75` `main() -> None`，`:169-170` 裸 `main()`，无非零返回；仅硬索引可异常冒顶。全树零 `test_*.py` 命中。打印的只有被解析出的裁决数据，无自判 FAIL |
| papers/phase1-workshop/figures/fig2_coverage_accuracy.py | 部分 | 否 | 否 | 读码 | `:46` `main() -> None`，`:202-203` 裸 `main()`；仅 KeyError 可冒顶。零 `test_*.py` 命中。`:177-178` 把 `replay: GREEN/RED` 算出来并打印，进程恒 0 |
| papers/phase1-workshop/figures/fig3_loop_ledger.py | 部分 | 否 | 否 | 读码 | `:55` `main() -> None`，`:128-129` 裸 `main()`。零 `test_*.py` 命中。`:76-79` 算出 `totals.fail`，`:119-120` 打印 `N fail` 并只落进 JSON 字段，进程恒 0 |
| proxy/scoring/__init__.py | 是 | 是 | 是 | 读码 | `:223` `return 0 if all(r["verdict"]=="PASS" ...) else 1`，`:216` `return 2`，`:110-116` `ScorerDriftError`。负控打的就是本文件：`proxy/tests/test_scoring.py:36-50`（改哈希后 `pytest.raises(ScorerDriftError)`）、`:161-165,194-233,242-250`（八种坏对账断言 `verdict=="FAIL"`）、`:185-191`（缺 scorecard 判 UNDETERMINED 而非 PASS）、`:253-267` |
| proxy/scoring/__main__.py | 是 | 否 | 是 | 读码 | `:8` `sys.exit(main())`，原样透传 `scoring.main` 的 0/1/2。全树搜 `python -m proxy.scoring` 只出现在 README/SCORING.md，无 `test_*.py` 或 `.sh` 实际调用它，故 CLI 这层无可执行负控 |
| proxy/variants.py | 是 | 是 | 不适用 | 读码 | 库文件，无 `main`/`__main__`；拒绝路径为 `raise VariantSpecError`：`:46,49,66,70-73,78,81,84-88,133,137,141,146-148`。负控打的就是本文件：`proxy/tests/test_variants.py:42-61` 五条 `pytest.raises`、`:154-156` |
| worldgen/generate.py | 部分 | 部分 | 不适用 | 读码 | `:510-524` `main()` 恒 `return 0`（`:520` 未知 world id 只是被跳过）；能红只来自模块导入期 `:495` `CATALOGUE = tuple(_catalogue())` 触发 `:73,99,119,132,140` 的 `ValueError` 与 `:164` `validate(spec)`。负控打的是**另一份实现**：`worldgen/tests/test_mutate.py:404-409` 对 `worldgen/core/spec.validate` 做 `pytest.raises(ValueError)`；`worldgen/tests/` 里无任何一条给 `from_art` 喂坏图画并断言它拒绝 |
| worldgen/runs/20260728T134933Z-C6-worldgen-mutate/append_sync.py | 部分 | 否 | 部分 | 读码 | 与 arc-recon 同名脚本逐行同构：`:34,40` 都 `return 0`，`:43-44` `sys.exit(main())`。零 `test_*.py` 命中 |
| worldgen/runs/20260728T134933Z-C6-worldgen-mutate/lint_unused.py | 部分 | 否 | 否 | 读码 | `:22` `bad = 0`、`:48` `bad += 1`、`:50` `return 0` —— 计数被算出、`:47,49` 被打印，却从不进退出码。零 `test_*.py` 命中 |
| worldgen/runs/20260728T134933Z-C6-worldgen-mutate/manifest_files.py | 部分 | 否 | 不适用 | 读码 | `:37-61` `main()` 恒 `return 0`；`:43,53` 用 `os.path.exists` 静默跳过缺失文件。零 `test_*.py` 命中 |
| worldgen/runs/20260728T134933Z-C6-worldgen-mutate/summarise.py | 部分 | 否 | 不适用 | 读码 | `:12-35` `main()` 恒 `return 0`（纯打印）。零 `test_*.py` 命中 |

判定员附注：

1. 「能红」按**判决路径**判：只有环境性异常（文件缺失、非 UTF-8、KeyError）能冒顶而判决本身
   恒 0 的一律记 `部分`；若按「任何输入都算」的字面读法，这些格都可升到 `是`。
2. fig2/fig3 的「退出码诚实」判 `否`（算出并打印 RED / N fail 却恒 0），但它们是图表渲染器，
   红退出未必是设计意图 —— 这是本批最没把握的两格。
3. `worldgen/generate.py` 是本批唯一「负控打到另一份实现」的情形。
4. 两个 `append_sync.py` 的「退出码诚实=部分」仅指散文说 refuses 而代码 `return 0`；
   就幂等语义而言 0 可能是对的，已判在保守一侧。
