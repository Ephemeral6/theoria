priority: 1
cell: A29
territory: theoria-arm
deps: none

# A29-theoria-arm-suite-red · master 上本领地套件红着两个，都是记账滞后

2026-08-01 由 A18 的开工基线发现、主检出独立复跑确认（同 commit 同红，
非 worktree 假象；A19 的假红教训已核对过）。两个失败都不是逻辑坏，
是**归档与表没跟上落地的事实**：

1. `tests/test_arm.py::test_the_archive_stays_accountable` ——
   R1/R1b 四份 manifest 漂移（`20260731T231654Z-R1-g50t-a` 等），
   重推逐字节不复现。腿落地后 manifest 没重钉。
2. `tests/test_desk_gate.py::test_the_ceiling_table_still_covers_the_archive`
   —— `harness/spend.py` 的 claude-opus-5 天花板 $12.00 低于归档隐含
   $13.4480。登记 #13 所有者已裁定越表继续，但表本身没同步该裁决。

做两件：重钉漂移的 manifest（用 runs-archive check 找全，别只修点名的四份）；
把 spend.py 天花板表对齐登记 #13 的裁决并引它（不许静默改数——表里注明
出处）。各配一个负样本防复发。验收：theoria-arm 全套件回到 0 failed。
零花费。红着的每一天，这个领地的任何 verify-gate 都过不了 tests 行。
