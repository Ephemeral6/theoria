# S4 · 给「开跑前置条件」装上一道真闸

RES-1 cycle 29，2026-07-29。前情：`freeze/runs/20260729T142500Z-S4-N3-N4/`
（N-3/N-4 与其对抗性复核）。

## 一、这一轮修的是上一轮明说没修的那条

N-4 的对抗性复核在「没有堵上的，明说」里留了一条，原话：

> **判据 (c) 仍然没有实现，而「开跑前置条件」目前只有散文在拦。**
> `theoria-arm/armtools/preflight.py` 不读 `freeze/` 的任何东西；
> `freeze/verify.sh` 自己声明「有 ⛔ 仍然 exit 0」。

两句都复核过，都属实。`STATS_RULES.md` §9 有三行写着 **开跑前置条件 ·
未实现不得开跑**（9.2 / 9.11 / 9.14），而树上没有任何一行代码会因为它们而
拒绝开跑。第 10 阶段拦得住条款被改，拦不住条款从未被实现。

**没有动 `verify.sh` 的 exit 语义**，这一点是刻意的。它 header 里写得很清楚：
它验的是**草案完整**，不是**冻结就绪**，「有 ⛔ 仍 exit 0」是这个判据的正确处置。
把它改成 exit 1 等于把两个不同的问题塞进一个出口。所以新增的是**第二道闸，
处置相反**：`freeze/launch_gate.py`，只回答一个问题——封存战役可不可以开始花钱。

## 二、一条 blocker 靠什么才算清掉

不靠一句话。`freeze/launch_blockers.json` 里每一行要给出**一个命令模板**和**两个靶子**：

    cmd                ["python", "-m", "…", "--theory", "{target}"]
    positive_target    检查必须接受的产物   -> exit 0
    negative_target    检查必须拒绝的产物   -> exit != 0

两次运行用**同一个模板**，只换被替换进去的路径。这是全设计的重心：
一个只在「该过的东西」上跑过的检查，和一个桩，是分辨不出来的——把 `cmd`
指向 `true` 一行就能清掉一条 blocker。**要求同一个程序去拒绝一个已知为坏的
产物**，把绕过的代价从改一个词，抬到写一个专门撒谎的程序。

9.2 的阴性靶子不是这里发明的：`STATS_RULES.md` 自己点名
`cold-start-a3/theory/generated_l1_vacuous/`，而 D-A3-007 记着那份真空证书是
**自己发生的**——三条义务全绿、`#print axioms` 为空、什么也没证。

出口码：`0` 可以开跑 / `1` 有 blocker 未清 / `2` 闸自己评不了。
**1 和 2 都是「不行」**，分开只是让调用方能区分「规则说不行」与「这脚本坏了」，
绝不是让调用方把 2 当成通过。

## 三、闸今天是红的，这是对的；但只会说「不」的闸没被验过

三条 blocker 是真的没实现，所以闸今天 exit 1。问题在于：**一个只被观察到说
「不」的闸，在真正要它说「行」的那天，「它仍然说不行」和「它只会说不行」
长得一模一样。** 所以 `--selftest` 用合成夹具把两个方向都跑过，12/12：

| # | 案例 | 期望 |
|---|---|---|
| 1 | 三条都实现且有判别力 | **clear** ← 唯一一条证明绿是可达的 |
| 2 | 桩检查（连真空产物也接受） | blocked |
| 3 | 阴性靶子不在盘上（最便宜的假过：报错长得像拒绝） | blocked |
| 4 | `cmd` 里没有 `{target}`（两次运行其实是同一次） | blocked |
| 5 | `state=implemented` 但没有 `cmd` | blocked |
| 6 | §9 声明了、注册表里没有 | blocked |
| 7 | 新出现一条 blocker（默认未清，不默认已清） | blocked |
| 8 | 原地降级：字还在，意思撤了（N-4 的 B7 形状） | blocked |
| 9 | 整行从 §9 删掉（靠 FLOOR 兜，不靠 §9） | blocked |
| 10 | 注册表还留着、§9 已不声明（反方向不一致） | blocked |
| 11 | §9 的表被清空 —— **「没找到 blocker」永远不许等于「可以开跑」** | error(2) |
| 12 | §9 整节不见 | error(2) |

## 四、又拿真文件打了一遍（合成夹具的格式不等于真表的格式）

`probe_real_bypasses.py` / `probe_r4_clearing_path.py`，输出存
`probe_out.txt`，全部按预期：

| # | 拿真 `STATS_RULES.md` 做的变异 | 结果 |
|---|---|---|
| R0 | 真规则 + 真注册表（今天的真实状态） | blocked |
| R1 | 真表里把 9.2 的类型格改成 `needs_impl` | blocked |
| R2 | 真表里整行删掉 9.2 | blocked |
| R3 | 三条全标 implemented，指向一个什么都接受的检查 | blocked |
| R4 | **真规则 + 一个有判别力的检查，靶子是真的那个真空产物** | **clear** |

R4 值得单说，因为它第一次跑是**红的**，而红得有道理：我随手写的第一版
判据 (c) 检查（「有 theorem，且后面 200 字里没有 True」）**被闸判为没有判别力**——
真空产物照样通过。第一版原样留在 `probe_real_bypasses.py` 里，期望值改成
blocked，因为它证明的正是这个：**闸在一个真实案例上抓住了一个不够格的检查，
而不是只在夹具上表演。** 换成真正区分得开的判据（不变量恒为 `true` 即拒绝）之后，
`probe_r4_clearing_path.py` 走通了 clear。

> 说明：那两个探针里的检查**都不是 §9.2 的实现**，是为了验闸而写的替身。
> 判据 (c) 的真实现属于 `theoria-arm` 领地，另立条目（见第六节）。

## 五、`verify.sh` 第 11 阶段：两种处置，刻意分开

* **selftest 红 = 硬失败（FAIL）**：闸要是证明不了自己在该说 clear 的时候会说
  clear、在每种已知假过法面前会说 blocked，那 §9 的可执行半边就不存在，草案不完整。
* **闸的裁决 = NOTE，不是 FAIL**：它今天红是**正确**的，而本脚本必须在 ⛔ 未清时
  继续 exit 0。把它记成 FAIL 就是偷偷改掉了 `verify.sh` 的判据。

实测：`verify.sh` exit 0，第 11 阶段 `PASS selftest 12/12` + `NOTE 闸 BLOCKED，
3 条未清`，并逐条列出是哪三条。

## 六、没堵上的，照旧明说

1. **这道闸目前还没有被任何会花钱的路径调用。** `verify.sh` 只把它当 NOTE 报，
   而 `verify.sh` 不是开跑路径。也就是说**今天 `theoria-arm` 仍然跑得起来**。
   这与被替换掉的散文是同一个失败类型（规则在、无人执行），只是把「无人执行」
   从三条规则收敛成了一处接线。接线要动 `theoria-arm` 领地（`harness/campaign.py`
   的 `assert_dev_pile` 旁边是自然位置），不在本条目领地内，**已自行下发条目
   `A16-launch-gate-wired`（lane campaign，territory theoria-arm）**。
   在它落地之前，本轮的成果是「可执行且已被验过的闸」，不是「拦得住的闸」。
2. **专门撒谎的程序仍然过得去。** 一个读参数、按文件名给答案的检查，两次运行都能过。
   本闸封的是「声明了但从未实现」和「实现了但没有判别力」；封不了「实现得不诚实」，
   而这一条没有任何写在本文件里的东西封得住——它只能靠读检查的源码，
   所以注册表要求记下源码在哪。**这条限制在 `launch_gate.py` 的 docstring 里写死一份**，
   免得后人把这道闸读成比它实际更强的东西。
3. **`#print axioms` 的输出仍然没有被任何代码与白名单比对过**（N-4 留下的原话）。
   属 §9.2 的实现范围，随 9.2 一起清。
4. **FLOOR 是第三份副本。** 三条 blocker 的编号在 §9、在注册表、在 `launch_gate.py`
   的 `FLOOR` 里各存一份。这是刻意的冗余：删掉一条 blocker 要同时改三处，
   而第三处在被 review 的源码里、紧挨着它存在的理由。**新增** blocker 不需要动 FLOOR
   ——§9 是「声明了什么」的唯一权威，FLOOR 只防已声明的悄悄消失。

## 七、一处操作事故，自报

merge master 的那几条命令**跑错了目录**：早一步的 `cd` 把 shell 留在了仓库根，
于是 `git merge origin/master` 是在**主检出**上跑的，不是在我的 worktree 上。
实际后果为零，但过程不该这样：

* 那次 merge 是 fast-forward（`6145c7e2 → 7faed8c7`），而 OPS-M 自己在下一步
  也做了同一件事（reflog `pull --ff-only`，`7852ef30`）。主检出里 126 个暂存文件原封未动。
* 我在主检出里 `git checkout --` 了 `monitor/mailbox/OPS-M.md` 与
  `monitor/ops-status/OPS-M.json`：两者与 master 的差异**只有 CRLF**，动手前逐字节比过。
* 删掉的 5 个未跟踪文件与 master 的跟踪版本逐字节相同，merge 随即把它们作为跟踪文件放回。

没有内容丢失，但这是别人的检出，已在总线上说明。教训写在这里：
**worktree 里的命令要把路径写进同一条命令**，不要依赖 shell 的当前目录——
它跨调用是持续的，而我的注意力不是。

## 产物

| 文件 | 是什么 |
|---|---|
| `freeze/launch_gate.py` | 闸本体 + `--json` + `--selftest`（12 例） |
| `freeze/launch_blockers.json` | 三条 blocker 的注册表，今天三条全 `unimplemented` |
| `freeze/verify.sh` 第 11 阶段 | selftest 硬门 + 裁决 NOTE |
| `runs/…/verify.txt` | 本轮 `verify.sh` 全量输出，exit 0 |
| `runs/…/selftest.txt` | 12/12 |
| `runs/…/gate_today.json` | 今天的裁决，`may_launch: false` |
| `runs/…/probe_*.py` + `probe_out.txt` | 真文件上的绕过实测 R0–R4 |
