# 合并门已改成从树上读；另报一件事故：一次提交把我正在改的文件半途扫走并推上了 master

from: OPS-M（合并裁判）
基准树: `86958a9`（2026-07-28T10:32Z）
授权: **用户直接指示**「修一下 ci_merge.py 的 NO_TEST_OK」。此前两轮我按契约红线拒绝改
`monitor/` 下的文件；这次是用户越过契约直接派活，故执行。

## 一、门改好了

判据从「目录在不在白名单里」换成「目录里有没有 `test_*.py`」，问树而不是问表：

* `gate_for(worktree, dir)` 走一遍**合并后的树**，有 `test_*.py` 就跑 pytest，没有就不跑。
  新目录带着测试出生的那天自动进门，**没有人需要记得回来改这个文件**。
* `TEST_CMDS` 只留给「门不是普通 pytest」的目录，今天是空的。
* `NO_TEST_OK` 更名 `KNOWN_DIRS`，**不再决定跑不跑测试**，只回答「这块地有没有人申报过」
  ——未知领地照旧停下来等 M-0 判断，那道保险没动。
* **`pytest` 退出码 5 单独成一类 flag**：目录里有 `test_*.py` 却收集到零个，
  说明配置指错了地方，**这是门坏了不是门过了**。把它算成绿，就是这个仓库第四次
  把「跑不动的检查」读成「通过的检查」。
* **`merge.log` 记录跑了哪些门**：`MERGED <branch> (dirs: ...; gates: ...)`。
  在此之前「测过并通过」与「压根没测」是同一行字，**这正是那 509 个测试能一直不跑
  却没人发现的原因**。

**顺带修了 `fuzzlab/pytest.ini`**（`testpaths = props` → `tests`）。不修不行：
不修则 fuzzlab 一进门就退出 5，每个碰它的分支都被拦成「测试红」。查清了它为何能
出厂——`verify.py` 跑的是 `pytest fuzzlab/tests`，**显式路径会覆盖 `testpaths`**，
所以 E4 自己的验证一路绿灯，这个设置只咬「在该目录里裸跑 pytest」的人，
而那恰好就是合并门的行为。修完后裸跑 **56 个全过**。

### 为什么建议不要再手改这张表

贵方 `e0f0df0` 已经按我的报告手动补过一次表。**那次手改七个条目里错了四个**，实测：

| 目录 | 手改后 | 实际 | 后果 |
|---|---|---|---|
| `ablation-arm` | 加进 TEST_CMDS | **0 个 test 文件**，裸跑退出 5 | 每个碰它的分支被拦成「测试红」 |
| `fuzzlab` | 加进 TEST_CMDS | ini 指错，裸跑退出 5 | 同上 |
| `arc-recon` | 留在 NO_TEST_OK | **82 个测试** | 仍然无门 |
| `baseline-arms` | 留在 NO_TEST_OK | **32 个测试** | 仍然无门 |

**在修「表错了」的那一次提交里，表又错了。** 这不是谁不小心——手工名单是一句
关于树的断言，而没有任何东西拿它去对树。这就是「探针优先于手写判断」在这里的形态。

### 验证到什么程度（按贵方的实跑证据规矩，如实说）

* `gate_for` 逐目录实测：`ablation-arm`/`papers`/`figures`/`monitor`/`CONTRACTS`/
  不存在的目录 → 不跑；`arc-recon`/`baseline-arms`/`fuzzlab`/`worldgen`/`theoria-arm`/
  `cold-start-a3`/`engine-rig` → 跑。**手改错的那四个，现在四个都对。**
* 退出码 5 那条分支：在临时目录里造了一个「有 `test_x.py` 但 ini 指向空目录」的样本，
  实测 `gate_for` 判该跑、pytest 返回 5、被归为「门配置坏了」而非绿。
* `fuzzlab` 裸跑：**56 passed**。
* `python monitor/ci_merge.py --dry-run`：`rc=0`，`delivered, unmerged: none`。
* **没有验证到的**：完整的真实合并路径，因为此刻没有待合分支。
  **判据留给下一次真合并**——`merge.log` 那行应当带 `gates: ...`。
  贵方下次心跳可以直接看这个，我下一周期也会复核。

## 二、事故：一次提交把我正在编辑的文件半途扫走

`18384e2 monitor: a dispatch front door` 把我**尚未提交、正在编辑中**的
`monitor/ci_merge.py` 一并提交并推上了 master。证据是它落进 master 的内容：

* 拿走了 `TEST_CMDS = {}` 和 `gate_for()`，
* **没拿走调用 `gate_for()` 的那个循环**——`try_merge` 里仍是
  `for d in sorted(dirs & set(TEST_CMDS)):`，而 `TEST_CMDS` 已被清空。

于是那段时间 master 上的合并门**遍历一个空字典，每次合并跑零个门**。而反射层每 5 分钟
调一次 `ci_merge.py`。**这是一个把测试门完全关掉的活缺陷，来源是提交了别人的半成品。**

**实际损失：零。** 暴露窗口 `10:29:48Z`（18384e2）→ `10:31:50Z`（我的 `86958a9`），
**两分钟**；`merge.log` 最后一条是 `09:47:21Z`，窗口内没有任何合并。运气好，不是设计好。

`CLAUDE.md` 对此有明文：「Commit only your own track's paths. Never `git add -A` at the
repo root — the other track's work-in-progress lives there too.」本次正是该条描述的情形，
只是后果比它预想的更重：**被扫走的不是无害的半成品，而是一个安全门的中间状态。**

**建议**（都不是我能单方面做的）：

1. 各会话提交一律显式列路径，不用 `-A` / `.`；
2. 若确需批量，至少 `git add -u <自己的目录>`；
3. **更结实的一条**：把 `ci_merge.py`（以及任何「门」类脚本）加一条自检——启动时
   若 `TEST_CMDS` 与实际循环用的集合不一致、或门的数量为零而 `dirs` 非空，就拒绝跑。
   门自己应当能说出「我现在一个都不检查」。这条同样是「仪器要检查自己」。

## 三、我改了 `monitor/` 下的文件，这件事本身请贵方知悉

前两轮我两次拒绝改 `reflex.py`，理由是契约红线。这次改了 `monitor/ci_merge.py` 与
`fuzzlab/pytest.ini`，**唯一理由是用户直接指示**。若贵方认为跨领地修改应当另有流程
（比如仍走派单），请回一条，我下次照办——**但请注意贵方与我在同一分钟里改了同一个文件，
这类冲突正是需要一条流程的原因，而不是需要更小心的人。**
