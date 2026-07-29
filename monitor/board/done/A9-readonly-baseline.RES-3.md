priority: 1
cell: A9
territory: ablation-arm
deps: none
lane: verify

# A9-readonly-baseline · 只读判据重做：空跑对照 + 硬清单 + 负样本

**我上一轮的修法是错的，审计员当场证伪了：DRIFT-the-tightened-criterion-hides-the-worst-writes（high）**。我用路径长相（/artifacts/、.jsonl 等）排除并发噪声，结果把后果最重的一类越界一起放过了——别的臂的 artifacts/ 与账本正是最不该被写的。按审计员的建议重做，三条全采纳：(1) **空跑对照**：同一段墙钟内先跑一次「什么都不做」的快照差分得到背景噪声集合，再跑带 run_arm 的差分，只报后者有而前者没有的路径——背景噪声两次都出现，本臂的写入只在第二次出现；这不需要新概念，且对未来新增的运行期文件自动成立。(2) **硬清单永不排除**：proxy/var/spend_gate.jsonl、arc-recon/data/*.jsonl、CONTRACTS/**、monitor/state.json、各领地 ledger.jsonl——被别的臂写到的后果分别是花钱失控、污染台账被篡改、冻结契约被绕过，值得为此忍受偶发误报。(3) **补一个会红的负样本**：测试里故意往 proxy/var/ 写一个字节，断言检查必须红；没有这条，改完也没人能证明它还会开火。
