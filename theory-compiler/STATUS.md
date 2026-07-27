# STATUS — theory-compiler track

## Final: M8 达成 (2026-07-27)

全部 8 个里程碑完成，49/49 测试通过。

### 里程碑清单

| 里程碑 | 状态 | 测试 |
|--------|------|------|
| M1 scaffold | ✅ | — |
| M2 parser | ✅ | 11 pass |
| M3 gen_python | ✅ | 5 pass |
| M4 gen_lean | ✅ | 3 pass |
| M5 gen_markdown | ✅ | 6 pass |
| M6 gen_pddl | ✅ | 6 pass |
| M7 playbook parser | ✅ | 9 pass (含 3 负向) |
| M8 e2e rehearsal | ✅ | 7 pass |

### 与正式 A1 验收的差异

本 sprint 是**编译链结构性彩排**，不是 Theoria.md 定义的正式 A1 验收：

1. **权重来源**：手算常量 `[1,2,3,2,1]`，非 engine-rig LP 引擎求解。
2. **Lean 证明策略**：BFS 枚举 5 个可达状态 + `native_decide`，非 pagoda 代数归纳证明。
3. **无 engine-rig 数据流**：DSL 内容全部手写，不消费 candidates.jsonl。

后续汇合 sprint 需要：
- 接入 engine-rig 的 LP pagoda 权重 → 重构 Lean 生成器为代数归纳模式
- 从 candidates.jsonl 自动生成 theory.dsl（而非手写）
- 接通 Fast Downward 验证 PDDL 计划可解性

### 阻塞

无。工单范围内工作已全部完成。
