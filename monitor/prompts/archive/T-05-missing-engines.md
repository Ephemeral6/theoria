# T-05 · engine-rig 补两道缺席工序：死锁刻画 + IC3/PDR

你在 Theoria 仓库的 **engine-rig 轨道**，只碰 `engine-rig/`（及
`PARTNER_SYNC.md` 自己的段落）。先读 `CLAUDE.md`、`Theoria.md` 1.9「死锁 =
野外的日常无解」与 1.10(b) 引擎清单表，再读 `engine-rig/DECISIONS.md`、
`engine-rig/STATUS.md` 和几个现有引擎的 README —— 新引擎要长得和它们一家人：
同样的候选流出口（`common/candidates.py`）、同样的确定性纪律、同样的
fixture 验证法。

## 背景

1.10(b) 的表格有八道工序，engine-rig 落了六道。缺的两道不是边角：
死锁刻画是 C1 的主要证据供给（「每证一个死锁，规划器同时提速」）；
IC3/PDR 是 LP/零空间够不着的形状的唯一兜底 —— 而 `lp_potential` 的不完备性
已在 peg fixture 上实测（0111 不可解但无线性 pagoda，见 M5 的测试）。

## 任务

### 引擎七 · `deadlock_carver`（先做这个，它供给 claim）

- 输入：规则集（fd_adapter 的 grounded-STRIPS 形态即可）+ 目标谓词。
- 产出：**条件化的迷你不可解定理** —— 「谓词组合 P ∧ 非目标 ⇒ 死」，每条带
  (a) 局部化论证（从 P 出发目标不可达的证书，小状态空间穷举或不变量均可）；
  (b) 剪枝形态（喂给规划器的 dead-state 判据）。
- trap 学习出候选：从可达图里找「进得去出不来」的谓词组合作为候选，逐个证。
- fixture：推箱子式死角是教科书例（peg4 或造一个 4×4 推块世界都行）——
  「箱入死角 ∧ 非目标 ⇒ 死」这条 1.9 的原文例子要真的产出来。
- 验收线：同一条死锁定理，(a) 作为定理带证书进候选流；(b) 作为剪枝接进
  `fd_adapter` 的搜索，节点数可测地下降 —— 「证书与启发同源」在死锁上兑现。

### 引擎八 · `ic3_pdr`

- 目标：产出恰是 Lean 要的**归纳不变量**（inv_init / inv_closed / goal_break
  三件套形态，同 lp_potential 的证书结构，方便下游同一条路走 Lean）。
- 范围收敛：布尔/有限域状态编码上的标准 PDR 环（frame 序列 + 泛化），
  不追性能，追**证书的可检查性** —— 输出的不变量必须能被独立检查器复核
  （逐规则闭包检查），像 lp_potential 用精确有理数复核那样。
- 验收线：peg 0111 —— LP 无线性证书的那个配置 —— ic3_pdr 给出非线性
  归纳不变量并复核通过。这一个例子就是这道工序存在的全部理由。

两个引擎都：candidates.jsonl 出口过 `tools.validate_candidates`；确定性模式
字节稳定；`python -m tools.run_all` 纳入。完成后 STATUS.md、DECISIONS.md、
PARTNER_SYNC.md 各记一笔。

## 红线

- 不碰 `theory-compiler/`、`cold-start-a0/`、`CONTRACTS/`（frozen）。
- 候选流 status 恒为 `"candidate"` —— 引擎永不裁决（分工三律）。
- 全程离线零网络。

## 验收

- 两引擎各自 README + 测试；全套 `python -m pytest` 绿（现有 150 条不得回归）。
- 死锁剪枝的节点数下降有一个具体的前后对比数字写进 STATUS.md。
