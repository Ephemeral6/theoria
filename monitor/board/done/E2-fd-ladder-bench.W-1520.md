priority: 3
cell: E2
territory: engine-rig
deps: none

# E2 · FD 三级梯子的基准与死锁剪枝红利

FD 已真接入（P-13，三级梯子 stub-bfs / fd-optimal / fd-satisficing）。量化它值多少：同一批 problem 上三档的节点数/墙钟/最优性对照表；M9 死锁定理作为剪枝接入后的前后对比（Theoria.md 1.9 承诺「每证一个死锁，规划器同时提速」——给出数字）；`.toolchain/` 不入库导致的可复现性缺口写进 runs/ 的 MANIFEST（含 FD 版本与构建命令）。
