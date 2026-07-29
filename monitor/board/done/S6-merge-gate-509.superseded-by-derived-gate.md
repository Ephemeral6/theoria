priority: 2
cell: S6
territory: monitor
deps: none

# S6-merge-gate-509 · 合并门把六个目录 509 个测试排除在外

OPS-M 在 cycle 3 实测发现：monitor/ci_merge.py 的 NO_TEST_OK 列表把 papers/figures/freeze/release/worldgen/fuzzlab 等六个目录标为『文档数据，无需测试』，实际它们合计有 509 个测试从未在合并门跑过——合并看起来有门，实际这几个领地是敞开的。详见 monitor/inbox/20260728T093832Z。做三件：逐目录核实是否真有测试套件；有的从 NO_TEST_OK 移出并接进测试门；确实无测试的目录保留但在 merge.log 里显式打印『该目录无测试，未设门』，让敞开是可见的而不是默认的。
