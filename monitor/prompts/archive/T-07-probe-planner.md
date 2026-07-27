# T-07 · 把假设层探针接上规划器：约束 7 的落点

你在 Theoria 仓库的 **engine-rig 轨道**，只碰 `engine-rig/`（及
`PARTNER_SYNC.md` 自己的段落）。先读 `CLAUDE.md`、`Theoria.md` 1.10(b)
探索/戳探一行（原话：「到达分歧态 = 一个规划问题」）与约束 7，再读
`engine-rig/engines/probe_frontier/README.md` 和 A0 的两处记录（只读）：
`cold-start-a0/THEORIZE_LOG.md` 的 P-01..P-03 与 R-05。

## 背景

A0 冷启动暴露了一个精确的缺口：probe_frontier 找得到**能分裂假设前沿的
配置**（P-01：paint 色 3 于 (1,1) 下方，1.000 bit），但那个配置世界从未
到达过，于是探针停在「hypothetical 层」，永远不可执行 —— 结果是
`press_is_direction_free` 定理永远 probe: pending，约束 7 空转。而框架
自己早写了答案：到达分歧态本身就是一个规划问题，规划器就在隔壁
（`fd_adapter`）。目前两者之间没有连线。

## 任务

1. `probe_frontier` 增加一个 `reachability` 阶段：对每个 hypothetical 层的
   分裂配置，构造一个 PDDL problem —— 初始态 = 当前态，目标 = 该分裂配置的
   判别谓词 —— 喂 `fd_adapter.solve`。
   - SAT：探针升级为 **executable**，payload 附上到达计划（动作序列）与
     计划长度（计入路径成本，bits-per-cost 排序照旧）；
   - UNSAT：探针标记 `unreachable`，这本身是有价值的裁决 ——「本世界无实验
     可分」从猜测变成了搜索证据（小空间下即证明）。
2. 排序函数升级：戳探价值 = 划分熵 / (1 + 到达成本)，成本含计划长度 ——
   Theoria.md 原文「戳探价值函数须计入路径成本」的兑现。
3. fixture 验证：在 cart_world 上造一个「分歧态可达但要绕三步」的场景，
   断言探针从 hypothetical 升级为 executable 且计划正确；再造一个真不可达的，
   断言 `unreachable` 裁决。
4. 候选流：升级后的 `probe_design` payload 带 `plan` 字段，过
   `tools.validate_candidates`（schema frozen —— plan 放 payload 内，
   不改 schema 顶层）。
5. 提交 + `PARTNER_SYNC.md` 追加一段，点名这是对 A0 发现（零可执行探针）的
   回应，A0 那边下次运行即可受益。

## 红线

- 不改 `cold-start-a0/`、`theory-compiler/`、`CONTRACTS/`。
- `fd_adapter` 仍是 BFS 桩没关系 —— 接口就是 `solve(domain, problem)`，
  FD 装上自动生效。
- 探针的「执行」不在本工单范围（那是内环 probe 拍的事）；本工单只负责把
  探针从「不可执行」变成「带计划、可执行」。

## 验收

- 全套 `python -m pytest` 绿，无回归。
- probe_frontier 的 README 更新：两层结构（executable / hypothetical）变成
  三态（executable-direct / executable-via-plan / unreachable）。
- 一条端到端演示写进测试：P-01 型场景在 fixture 上从 hypothetical 变
  executable。
