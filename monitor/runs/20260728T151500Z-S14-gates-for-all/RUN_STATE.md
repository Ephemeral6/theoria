# S14 · 给缺闸门的领地补收工闸门 —— 运行状态

RES-4，2026-07-28。分支 `agent/s14-gates-for-all`，base `f715c5b`。

## 先纠正工单的前提

工单说「十个领地只有三个真有 verify（exam/worldgen/proxy）」。树上不是这样：

* 领地 **21 个**；
* 开工时有闸门的是 **6 个**：`ablation-arm`、`arc-recon`、`exam`、`figures`、
  `fuzzlab`、`worldgen`；
* **`proxy` 一个都没有**——工单点名它有。

这本身就是本任务要防的那类错误的元层版本：**一张手写的表对树做出断言，
而没有任何东西拿它跟树对照。** 所以第一件事不是补闸门，是让这张表变成可执行的：
`python monitor/gates.py list` 现在**问树**，不问名单。

（`freeze/`、`crosscheck/` 两个领地在 master 上根本不存在，只活在工单名字里。）

## 做了什么

### 1. `monitor/gates.py` —— 判据从「有没有 test_*.py」换成六种具名结局

ci_merge 原来的闸门判据是「这个目录里有没有 `test_*.py`」，有就跑 pytest，
没有就**静默跳过**。跳过与通过在日志里是同一行。现在六种结局，只有两种放行：

| 结局 | 含义 | 放行？ |
|---|---|---|
| `ok` | 闸门跑了，退 0 | 是 |
| `red` | 闸门跑了，退非 0 | 否 |
| `broken` | **闸门存在但跑不起来**——没解释器、超时、pytest 收集到零个用例 | 否 |
| `dirty` | 闸门跑绿了，但往树里**扔了新文件** | 否 |
| `drift` | 闸门跑绿了，但**重写了 tracked 产物**且内容不同 | 是（但记名） |
| `absent` | 该领地没有闸门 | 是（**必须显式入日志**） |

两条设计上的判断：

**`absent` 必须写进 merge.log。** 大多数领地当时确实没闸门，合并它们仍然允许——
但**无闸门的合并绝不能长得像有闸门的合并**，因为 509 个测试就是这么被跳过好几天的：
「跳过了」和「通过了」是同一行 MERGED。

**`dirty` 与 `drift` 拆开，因为它们的责任人不同。** 往树里扔新文件是闸门自己的缺陷
（ablation-arm 第一版 verify.sh 就是这样把本臂的只读测试弄红的）。而**重写 tracked 产物**
说的是另一件事：仓库里已提交的产物不再等于代码现在产出的东西——这是真发现，但它属于
那个领地，不属于恰好在合并的那个分支。而且**现存两个闸门都有这个毛病**，
一上来就拿它卡住全部待合分支，等于第一天装、第二天被关掉。所以 `drift` 记名放行，
`gates.py run --strict` 给领地主人用。

### 2. 十九条注入自检

每一种结局都在一次性 checkout 里**人为造出来**再断言它真的变红。
不能自证会变红的探针是负资产——它只增加一盏绿灯，不增加一次观察。
特别包含：

* `test_tests_that_collect_nothing_are_broken_not_green` —— pytest 退出码 5；
* `test_shell_gate_without_bash_is_broken_not_skipped` —— 没解释器不等于跳过；
* `test_utf8_gate_output_does_not_crash_the_runner` —— 子进程打 UTF-8 中文，
  宿主 locale 是 cp936（今早「八个活工人报成死」就是这个错配）；
* `test_interpreter_caches_do_not_count_as_dirt` —— 反向自检：`__pycache__`
  不算脏，否则每个领地首跑即脏，这个信号一天内就会被丢掉。

### 3. 十一个领地各补一个三段式闸门

覆盖率 **6/21 → 17/21**。三段是：**测试全过 + 一次真实离线实跑 + 产物字段自检**。
第三段是各处普遍缺的那一段：测试绿说明代码符合作者的想法，**不说明流水线跑过**，
也不说明它吐出来的东西还符合契约。

两条硬规矩：**产物写 mktemp**（不弄脏被检查的工作区）；**空集永不算通过**
（每个计数都有具名 floor 常量并注明取值理由）。第二条不是洁癖：`figures/verify.sh`
现在就会在两次构建**什么都没产出**时打印
`ok (csv, out, SOURCES.sha256 all identical)`——两棵空树逐字节相同。

**剩下四个（CONTRACTS / browser-ops / papers / release）没有测试也没有流水线**，
如实报 `absent`，每次合并显式打印，而不是让它们看起来像有门。

不花钱、不联网、不需要密钥：`theoria-arm` 用 `--mock`，`baseline-arms` 唯一的
流水线入口真的要花钱（已记录的那次战役花了 $13.06），所以它的第二段是**离线复裁**，
docstring 直说，不装。

### 4. ci_merge 的三个静默 exit 0

「因 M-0 在跑而让路」「没有待合分支」「抢锁失败」原本各是一句 print 到没人看的
控制台然后 exit 0——与「干净地合完一轮」不可区分。现在各自在 merge.log 留一行。
让路是正确行为，仍然 exit 0，只是不再隐形。
顺带记下：`--dry-run` 在读参数之前就 `git fetch`，**会联网**，所以它不能当任何人的闸门。

## 一个没做的修法，和不做的理由

`grep "text=True" monitor/*.py | grep -v encoding=` 在修完 ci_merge 与 gates 之后
还剩 **17 处**用 cp936 解码子进程输出。**没有一把梭，因为一把梭会制造回归**：
子进程分两类，编码相反——Python 脚本吐 UTF-8，而 `tasklist`（`dispatch.py:318`
的**工人存活判断**）吐控制台代码页 GBK。把后者强行按 UTF-8 解，就是今天那起
「八个活人报成死」换个方向再犯一次。逐个定性后再改，列为 S16 第一件事。
详见同目录 `FINDINGS-existing-gates.md` §7b。

## 侦察副产物

`FINDINGS-existing-gates.md`：三个只读 subagent 并行扫出的 **现存闸门 11 处
「悄悄失败」**，每条带 file:line。摘要：

* `figures/verify.sh` 有 **3 处**在空集上打印 ok（闸 3 两棵空树相同、闸 4 空 manifest、
  闸 7 空 glob），另有 3 处 `grep -c` 的退出状态被 `$( )` 吞掉；
* `proxy/verify_spend.sh:50` 用 `grep FILE` 当断言，**grep 无命中退 1、文件不存在退 2，
  两者都落进 else**——把 `spend_gate.py` 删掉，这道闸打印 `-- ok`；
* `cold-start-a3/run_all.py` **永远退 0**，且缺 fixture 时静默 SKIP；
* `a0-spike/run_a0.py` 的 `ok` 表达式在 Lean 工具链缺席时短路为真——
  「装不上 Lean」与「Lean 校验通过」对退出码等价。

这些属于 S16（同为 monitor 领地，被「一个领地一个人」挡在 S14 之后），已落盘待领。

## 测试

`cd monitor && python -m pytest test_gates.py -q` → **19 通过**。
`python monitor/gates.py list` → 21 个领地，17 个有闸门。
交付前另派了一个对抗性 subagent 专门试图证明这十一个闸门是假的
（十一个里有九个是写它的 agent 自评通过的，那正是该被怀疑的地方）。

## 交接

* 闸门本体：各领地 `verify.py`；
* 判据与结局：`monitor/gates.py`（`list` / `run <territory>` / `run --all [--strict]`）；
* 接进合并：`monitor/ci_merge.py`，每个被触及的领地都在 MERGED 行里带一个具名结局，
  `absent` 额外打印 `[UNGATED: … -- merged with no completion gate]`。
