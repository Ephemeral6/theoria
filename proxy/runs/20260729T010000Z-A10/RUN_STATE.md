# RUN_STATE — A10 共享账本

W-1641，2026-07-29T01:00Z 开工。分支 `agent/a10-shared-ledger-real-arms`，
基线 `ee8876e`。机器可读部分见 `MANIFEST.json`；范围裁定见 `SCOPE.md`（先读那份）。

## 工单要四件，实际能做的是两件半

`SCOPE.md` 逐条查过：**两条前提不成立、一条越界、一条无效**。摘要：

| 工单要求 | 实况 |
|---|---|
| 三条真臂 billing 进同一账本 | **越界**：要改另外三块领地；ablation 不用共享账本是明写的设计决定 D-AB-004 |
| 对账改 cost × actions × turns | **turns 字段根本不存在**（`battery/INPUT_FORMAT.md` gap 5），换了个不可清偿的义务 |
| 分数标为不可交叉核验 | **口径过宽**：记分卡 close 响应带 score，缺的是 per-step，per-run 可核验 |
| 绿了图 2 就解锁 | **不成立**：图 2 根本不读这份账本，且明确拒绝 v1.0 方言 |

## 真正做了什么

### 1. 修好账本分叉（本工单的前置条件）

`Ledger.__init__` 只在构造时播种一次 `seq`/`prev`，`threading.Lock` 又不覆盖
播种→追加，于是中途打开文件的写者从**过期的 seq** 续起，两边发出相同的
`seq` 与 `prev`，**哈希链分叉**。正典 `LEDGER_FORMAT.md` 早把这条列为已知的洞，
W-1640 还找到了一具尸体（253 行，第 144 行断裂，seq 137–143 各两次）。

**这件工单要把三个写者指向同一个文件，而今天两个就会分叉——所以必须先修。**

改法不是发明的，是**搬隔壁的**：`spend_gate._PoolLock` 自 INC-BA-003 起就用
`fcntl`/`msvcrt` 在**旁挂文件**上取 OS 级锁。现在 `Ledger` 同样在
`<ledger>.jsonl.lock` 上取锁，并**在锁内从磁盘字节重新导出** `seq`/`prev`
才写。**失败即拒**：没有锁原语或超时 → `LedgerLockUnavailable`，一个字节都不写。
扫描从缓存偏移折叠（精确，不是近似），否则共享战役账本会随自身长度平方增长。
格式一字未动，`v` 仍 1.0。`_last_seq` 全仓确认无调用者，已删。

**失败路径是跑出来的，不是声称的。** `test_ledger_concurrency.py` 用真进程。
我自己把修复关掉重跑：**10 条里 7 条变红**，且复现了中毒文件的签名——
重叠点之后每个 seq 写两次、无空洞、无记录丢失；恢复后 10/10 绿。
（实现者还记了一个陷阱：早期草稿用 0.35 秒错开，结果 worker 串行跑完，
**修复前也能通过**——一个测不到并发的并发测试。）

### 2. 对账重新定键

原规则要求「从 `env_step` 导出的分数 == 记分卡分数」，而 API 的**命令响应
不返回 score**（INC-TA-002；`arc-recon/data/recon_ledger.jsonl` 196 条成功
响应零条带 score）。一条没人能清偿的义务，只会让闸门永远红着或被悄悄跳过——
两种失败本仓都有专门的类名（`permanently_red_signal`、`check_with_no_failing_path`）。

新键 `(actions, cost, score_per_run)`，全部是**当前真的记录得到**的量：
`actions` 逐记录查序列 + 与卡面 `total_actions` 对；
`cost` 查 `pricing_ref.sha256` 仍与磁盘价目表一致 + `run_end.model_calls` 与记录数一致；
`score_per_run` 保留冻结计分器的电池（**这条是被我挡下来的**：工单本来要把
score 整个标成不可核验）。
`turns` 与 per-step score 记为**显式缺口且不参与投票**——
让一个格式缺口去投票，等于把刚拆掉的常红信号再装回去。

**六个负样本，每个都被证明能变红**（实现者逐条把检查打断再跑）：
重复 step_idx、卡面谎报动作数、价目表哈希漂移、声明调用数不符、
分数与通关数矛盾；外加两个对照——价目表缺失判 `INCOMPLETE` 而非 `PASS`，
以及改掉 per-step score **仍然 PASS**，证明那条标注是诚实的。

### 3. 三臂同账本的实证（工单第 4 条）

`demo_three_arms.py` + `demo_output.txt`：三个**真进程**、三个 arm 身份、
一份账本 → **42 条记录、3×14、0 个重复 seq、`verify_chain` PASS**。
修复之前这件事做不到。

**这条证据的边界写在脚本抬头，也写在这里**：这是三条臂的**账本身份**，
由脚本驱动；**不是**三条真臂各自跑自己的内循环。后者要改另外三块领地，
是 `SCOPE.md` §1 的 gap。全程零网络、零 API、零花费。

### 4. 两处被本次工作证伪的文档

* `LEDGER_FORMAT.md` 的「链条的洞」里那条「两个进程会分叉」**已经不成立**，
  留着会被读成「不修也行」的许可。改写了，并写明**仍然存在的两个限制**：
  绕开 `Ledger` 的写者（锁是协作式的，`baseline-arms` 那套 v0 方言不认这把锁）、
  以及**挂住**（非死亡）的持锁者会让别人超时拒写。
* `README.md` 那行 `reconcile` 的一句话说明还是旧规则。

## 我自己犯的错，记下来

**我在派单里让实现者「按 `proxy/CONTRACT_CHANGES.md` 走契约变更协议，
像 C-005 那样登记」——这两样在 `ee8876e` 上都不存在。**
它们在 `agent/s9-contract-change-protocol` 分支上，那条分支我几小时前刚在 S24
里推好、当时还没合入 master。我把另一条分支的产物当成了树上的现状。

**这正是本仓编目的 `requirement_cites_nonexistent`，作者是我。**
实现者没有照做，而是如实报告「这个文件不存在，我把修订登记在文档自身里」——
**它的处理是对的**。若 s9 合入后需要补一条正式登记，那是后续动作。

## 交付物

```
proxy/
  ledger.py                    +跨进程锁、锁内重播种、_last_seq 删除
  reconcile.py                 重新定键 + 缺口不投票
  tests/test_ledger_concurrency.py   10 条，真进程
  tests/test_reconcile.py            18 条，含 6 个负样本
  LEDGER_FORMAT.md             §2 链条洞改写、§3/§5 对账规则改写
  README.md                    reconcile 一行说明
  runs/20260729T010000Z-A10/   SCOPE.md / demo_three_arms.py / demo_output.txt
```

**测试：`python -m pytest proxy` 315 passed；`proxy/verify_spend.sh` green。
两项都由我自己复跑，不是采信 subagent 的自述；分叉修复的失败路径也是我自己
关掉修复验的。**

## 没做的（gap，不降验收线）

1. **三条真臂的臂侧改线**——跨领地，建议拆三件。theoria-arm 不需要改代码
   （`ledger_path` 已是参数），另两条需要。
2. **`turns` 字段仍不存在**。要让它可对账，需按 §8 加一个**可选**字段
   （不动 `v`，`prev` 是先例）。本轮只把它标成缺口。
3. **既有的那份分叉文件没有修复**（`theoria-arm/runs/pytest-test_the_shell…`）。
   账本 append-only，唯一的更正手段是补一条 `incident` 记录——另一块领地的事。
4. **`run_end.steps` 不可对账**：`runner.py:124` 写非 RESET 步数，
   `replay.py:143` 写全部步数，真实数据两种都有。只报告，不投票。
5. **绕开 `Ledger` 的写者仍能分叉文件**——锁是协作式的。
6. **`score_mismatch` 现在名不副实**（任何一条腿失败都用它）。加了
   `failing_legs` 字段而没有新增 kind，因为 `INCIDENT_KINDS` 当时是另一个
   agent 的文件。
7. `ablation-arm/ablcore/ledger_abl.py:15-25` 说 `theoria_ablate` 的注册请求
   还挂着——**已经不成立**，`PARTNER_SYNC.md:835` 早已裁定它对现在的代码不构成
   阻塞。那段 docstring 是陈的，属另一块领地，只报不改。
