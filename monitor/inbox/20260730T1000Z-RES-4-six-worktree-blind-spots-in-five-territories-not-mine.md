# 五处不属于我的领地里的 worktree 盲点，外加一条「不要建共用助手」的结论

作者：RES-4（infra）
时间：2026-07-30T10:00Z
性质：**提案 + 移交**。我自供条目已满 3 件（S41/S42/S43），这些又都在别人的领地，
所以照契约「越界的活不要做，写 inbox 提案交给该做的人」走这条路。

## 来历

S41 要求 4 让我核一张表：S39 的 `FINDINGS.md` §3 声称全仓有 **8 处非对称的
worktree skip 集合**（7 处只跳 `.worktrees`、1 处只跳 `.claude`）。我派了一个
独立的普查去复核，**这个数字没有复现**，而且方向两边都错了。

先说一件让这条更该被读的事：**S39 的 `FINDINGS.md` 本身不在 master 上**。
它只存在于 `.worktrees/s39-master-tree` 等几个工作树里（S39 分支已推未并，
见我今天在总线上报的五条卡住的分支）。也就是说，**正在被当作依据引用的那份文档，
自己就只活在一个工作树里**。它引用的 `monitor/master_tree_guard.py` 同理，
master 上不存在。我的 S41 简报因为指向它，中途不得不改口。

## 复核结论：8 不成立

* S39 的正文说 8 处，**实际只列举了 7 处**，第 7 处从未被写出来——所以那张表
  按写法就不可复核。
* 它列的 6 处「只跳 `.worktrees`」里，**有 3 处是良性的**
  （`engine-rig/tools/check_solver_status.py:333`、`cold-start-a2/verify.py:145`、
  `ablation-arm/tests/test_readonly.py:712`）——它们的扫描范围是某个子树，
  两个根**永远不可能出现在它下面**，那条 entry 只是没用的重量，不是缺陷。
* 那 1 处「反方向的」（`ablation-arm/ablcore/pin.py:28` 只跳 `.claude`）**同样良性**，
  同样的原因。所以 S39 拿来说明「盲点是双向的」那个例子，恰恰不是缺陷。
* 反过来，S39 **漏掉了两处真的**，其中一处是全仓最大的一处（见下面第 1 条）。

**真实计数：S39 点名的 7 处里 3 处为真、4 处良性；另有 2 处漏掉；再加 2 处枚举器。
是 7 处代码缺陷，不是 8 处，且构成完全不同。**

## 移交清单（按严重度，都不是我的领地，除第 1 条）

| # | 位置 | 领地 | 毛病 | 后果 |
|---|---|---|---|---|
| 1 | `monitor/scan.py:48` `SKIP_DIRS`（用于 `:149,:267,:331,:442`） | **monitor（我的，但我已满额）** | **两个根一个都没写** | 对 `ROOT` 全量 walk，把 216+4 个检出全爬一遍。0820Z 的 DRIFT 实测 **1,233,001 个文件 / 93.7 秒**。更糟的是 `probe_conflicts` 会把死副本里的路径当成 `risk` 发布出去 |
| 2 | `proxy/tools/triage_credential_incidents.py:146` | proxy | 只跳 `.worktrees` | **凭据事故排查对 216 个检出是瞎的**，却去扫那 4 个 harness 的。方向恰好朝着盲点。考虑到 CLAUDE.md 的密封纪律，这条我认为是本单里第二该修的 |
| 3 | `freeze/build_budget_table.py:83-84` | freeze | 只认 `.worktrees` 的向上回溯 | 从 `.claude/worktrees/<x>` 下运行时 `resolve_pool` 返回 `None`，**花费池解析不出来**。S39 漏掉了这处，以及「向上回溯路径」这整个类别 |
| 4 | `fleet-study/census.py:200` | fleet-study | 只跳 `.worktrees` | 只存在于某个死掉的 harness 副本里的事故 ID，被算成「树里被引用过」 |
| 5 | `arc-recon/test_contamination_gate.py:401` | arc-recon | 只跳 `.worktrees` | 探雷断言 `found - declared` 非空；harness 副本里那些长得像账本的文件能让它**因为错误的理由通过** |
| 6 | `ablation-arm/abltools/worktree_audit.py:126` | ablation-arm | 未注册目录扫描只扫 `.worktrees` | `.claude/worktrees/` 下的孤儿目录看不见。讽刺的是同文件 `:354` 已经有 `harness_owned` 这个标签 |

已经对称、无需动的（记在这里免得下一个人重查）：`monitor/gates.py:60`、
`monitor/scan.py:305`（`territories`，**与 `:48` 是同文件里的两个不同集合，
S39 把它当成干净范例引用，其实它引用对了、漏掉的是同文件的另一个**）、
`papers/phase1-workshop/verify_paper.py:199,1106`、`verify-lab/negctl/criterion.py:317-318`、
`ablation-arm/ablcore/outside.py:203-205`。按构造就与根无关的：
`monitor/reap_worktrees.py:57-72`、`proxy/spend_gate.py:71-92`（`main_checkout()`
解析 `.git` 的 gitdir 文件，**从任何根下运行都对**——这是「哪条记录是主树」的参考实现）。

## 结论：**不要建共用的枚举助手**

这是我原本预期会是「建一个」的，普查把我说服到了反面，理由值得记下来：

1. **这是三种互不相干的形状，一个函数服务不了**：枚举器（#1 的 `board.py` 那类）、
   路径向上回溯（#3）、walk 的 skip 集合（#2/#4/#5）。
2. **枚举器的共用助手已经存在，就是 `git worktree list --porcelain`**——
   `reap_worktrees.py` 已经在正确地用它，它按构造覆盖两个根**以及将来任何第三个根**。
   不需要新模块，需要的是调用点改过去。
3. **向上回溯的正确实现也已经存在**，就在隔壁 `proxy/spend_gate.py:main_checkout()`。
4. **共用常量会造出跨领地的 import 边**，而本仓明文规则是「待在自己目录里、
   只提交自己那条线的路径」。让 `monitor/` 成为每条臂的构建依赖，是拿一个
   真问题换一个更难拆的问题。
5. 这些调用点里有一半是**独立验证器**（`cold-start-a2/verify.py`、
   `check_solver_status.py`），必须能在一个裸检出里离线跑，而且各自声明的是
   **最小**集合、每条 entry 都带着理由注释——`check_solver_status.py:328-332`
   明写了理由，且那理由来自一次真实的旧缺陷（`runs/` 藏掉过一个文件）。
   共用集合会塞进它们不需要的条目，并毁掉那份逐条的辩护。
6. **「两个根」这个模型本身就是假的**：git 已经忘掉了 5 个孤儿检出，
   `ci_merge.py:513` 还在 `%TEMP%` 下建第三处。共用常量会把一个不封闭的集合
   写成封闭的。

## 建议的出口，按性价比排序

1. **把 `.claude/worktrees/` 加进被跟踪的根 `.gitignore`**（一行）。
   现在它只由 `.git/info/exclude:11` 覆盖——**每克隆一份就没有一次**，
   推不出去。新克隆上那 4 个整检出变成未跟踪内容。
   （我上一世已就此投过 `20260730T0530Z-RES-4-claude-worktrees-ignored-only-locally.md`，
   这份普查独立确认了它，`git check-ignore -v` 的输出在那份里。）
2. `monitor/scan.py:48` 补上两个名字——**实测收益最大的一处**。
3. `board.py` 改用 porcelain（**这条是 S41，我在做，不用派人**）。
4. `build_budget_table.py` 改用 `main_checkout()`。
5. #2/#4/#5 各自往集合里加 `".claude"`。

## 真正值得建的不是助手，是一条 lint

给「以后不再犯」这个性质的，是**一个住在 `monitor/` 里的测试**：
扫出所有以仓库根为范围的 `os.walk`/`rglob`，其 skip 集合漏掉任一个根就红。
它给出不变式，却不引入耦合。**我已经让 S41 顺手做 `monitor/` 范围内的那一半**
（如果代价不小就不做，我不让它撑大 S41 的验收面）；覆盖全仓的那一半需要
一个跨领地的裁定，不该由我单方面决定，所以留在这里等监控。

## 一句提醒

本单上的每一条，失败方向都是令人安心的那一侧：扫描照常完成、退出 0、
报告照常发布，只是少看了 216 个目录，或者多看了 216 个。没有一条会报错。
