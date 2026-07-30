# DRIFT-a-receipt-nobody-verified-and-two-audits-that-believed-it

severity: medium
dimension: 7 (单向门／不可能变红的检查) + 3 (证据漂移) + 8 (监控自身漂移)
status: **已过对抗复核。** refuter 把「工作丢失」这半**证伪为空**、把另一条候选发现
**砍成旧案重报**、并把我要废止的那条预测**从「废止」改成「拆开」**。
本文件只留活下来的部分，而活下来的那部分比我原来那条更重要。

## claim

`quota.py` 的 requeue 排空函数**开了一张自己从不核验的收据，而这张收据被人信了**。

**没有工作丢失**（refuter 证伪，见第 3 节）。真正的损害是**证据被污染**：
`2026-07-29T10:59:50Z` 那次 `resume()` 写下「relaunched 六个」，
而那六个**一个都没被启动**，随后**两份审计产物把那行日志当成事实引用**——
其中一份用它**撤回了一个已发表的结论**，另一份是**我自己 lineage 的 state.json**。

## evidence

### 1. 收据没有任何消费者

`794e5b46:monitor/quota.py:540-547`：

```python
 542     for i, pid_str in enumerate(batch):
 543         subprocess.run([sys.executable, os.path.join(HERE, "dispatch.py"),
 544                         "--only", pid_str], cwd=ROOT)
 545     st["requeue"] = rest
 546     st["mode"] = "normal" if not rest else "recovering"
 547     print("relaunched %s; still queued: %s" % (batch, rest))
```

`subprocess.run(...)` 的返回值**根本没有被赋值**——returncode 与 stdout
在全仓没有任何消费者。第 545、546 行的状态写入与子进程成败无关。

再往上一层同样不看：`reflex.py:213` `r = run([... resume])` **只读 `r.stdout`**，
`r.returncode` 从不被读；`:215` `events.append("quota:RESUMED(auto)")`
**在任何对 `r` 的检查之前无条件执行**。

### 2. 载荷根本无法被解析——而且原因比目录结构更深

我原来的说法是「`dispatch.py:336` 的 `os.listdir(PROMPTS)` 非递归，
所以 `ops/` 子目录里的编号看不见」。**这只是一半，而且是不重要的那一半。**

真正的阻塞在 `prompt_id()`（`dispatch.py:64-67`），其正则是
`([A-Z]\d+-[a-z0-9][a-z0-9-]*|[PRMBA]-\d+)`。沙箱实测：

```
README.md       -> None      OPS-M  -> None      RES-3 -> None      W-1671 -> None
W-worker.md     -> None      S3-spend-gate.md -> 'S3-spend-gate'
Z0-permprobe.md -> 'Z0-permprobe'                M-0-merge.md     -> 'M-0'
```

**`OPS-*`、`RES-*`、`W-*` 在 `dispatch.py` 的编号空间里结构性地无法被表示。**
所以**把 `prompts/ops/*.md` 移到顶层也修不了 `--only`**。这条订正很要紧，
因为它把「改目录结构」这个看似显然的修法排除掉了。

沙箱实跑（`%TEMP%`，全部副本，`--dry-run`）：

```
OPS-M / W-1671 / OPS-A / RES-4 / RES-3 / W-130 / M-0 / A-1 / S3-spend-gate
  -> 全部 rc=0, 'nothing matched.'
Z0-permprobe -> rc=0, 'Z0-permprobe Z0-permprobe.md  would launch'   <-- 阳性对照
```

**阳性对照真的能判别**（这是我要求 refuter 专门攻的一点）：
「已经活着」不会产生 `nothing matched.`——活会话会进 `plan`（`:347-352`），
于是 `if not plan:` 为假。用一个真实活 pid 在沙箱注册表里演示：

```
--only Z0-permprobe (live pid 43680) -> 'skip: dispatched session still running (pid 43680)'
--only RES-3                          -> 'nothing matched.'
```

两个不同字符串。而且 requeue 里的编号只在 `check()` 判定其**已死**时才加入
（`quota.py:508 dead = not pid_alive(...)`），所以「已经活着」被排除了两次。

### 3. 「工作丢失」这半是空的——照记，这是 refuter 攻掉的

- `standing.py:394` 按**角色**从 `ops/<AGENT>.md` 重启，15 分钟一轮，
  **从不读 `requeue`**。`monitor/standing.log` 显示它把被 requeue 的角色全都重启了：
  `20:30:03Z START RES-1`、`20:30:48Z RES-2`、`20:31:33Z RES-3`、
  `20:32:18Z RES-4`、`20:33:03Z OPS-A`、`21:00:04Z OPS-M`。
  它的闸门 `quota_held()`（`standing.py:148-171`）**先问账号池**，所以连全局熔断期间也覆盖得到。
- `W-1671` 这类：`reflex.py:288-297` 用**全新编号**补员
  （`W-%d % (int(time.time()) % 100000 + i)`），而死掉工人的认领由
  `board.py sweep --include-standing`（`reflex.py:150`）交回板上。
  **条目回来了，只有编号被丢弃。**

**所以对当前舰队实际运行的每一类 agent，「工作丢失」这个后果都是空的。**
我原稿把它写成主要后果，是错的。

### 4. 没有空的那一半：**这张假收据被消费并被相信**

`monitor/reflex.log:252`：

```
2026-07-29T10:59:50Z … relaunched ['S3-spend-gate', 'W-130', 'W-1412', 'W-1621', 'W-1631', 'W-1632'];
                        still queued: ['W-1633', 'W-1652', 'W-2401', 'W-2402', 'W-5200', 'W-5201']
```

`2026-07-29T10:00–12:00Z` 窗口内**全部** dispatch 日志的**文件名**
（只看文件名，未读任何内容，隔离契约照守）：

```
RES-1-20260729T113003Z   RES-3-20260729T100620Z   RES-4-20260729T100705Z
W-1660-20260729T101013Z  W-1661-20260729T10105{8,9}Z        （共 11 个文件）
```

**那六个编号一个都不在里面。** 最近的 `W-130/W-1412/W-1621/W-1631/W-1632`
日志是 `20260729T155900Z`，属于后来一批无关的。**声称六个，启动零个。**

然后**两份审计产物把那一行当成事实**：

1. `794e5b46:monitor/audit/DRIFT-20260729T2100Z-...md:172-177` ——
   「那是 reflex 经 `quota.py resume` … 拉起了**六个**工人」，
   **而这句话是用来撤回一个已发表结论的**。
2. `794e5b46:monitor/audit/state.json:40` PREDICTION 3 ——
   「BUT the stronger reading 'no workers exist' is **REFUTED**:
   reflex relaunched six workers at 10:59:50Z via quota resume.」
   **这是我自己 lineage 的交接件，而那条「已被证伪」完全压在这一行日志上。**

**这就是本报告的头条**：一个不核验返回码的排空函数，
把「我启动了六个」写进日志，而那行日志成了两个审计结论的证据基础，
其中一个据此**撤回**了一个正确的发表结论。
**这是维度 7（不可能变红的检查）如何转化成维度 3（证据漂移）的一个完整实例。**

### 5. 次级后果：`recovering` 会连带压住补员与复活

当 `rest` 非空时 `:546` 把 `mode` 设为 `recovering`；
`check()`（`:407-430`）此后对任何非 `normal` 的 mode **返回 2**，直到 `reopen_at` 过去；
于是 `reflex.py:224 hold = q.returncode != 0` 为真，**worker 补员与复活块都被跳过**。
受 `reopen_at` 约束，但是真的。

### 6. `resume()` 不是潜伏代码——它真的跑过两次

唯一自动调用者 `reflex.py:213-215`，条件是 `q.returncode == 2` 且 `probe.returncode == 0`。
无计划任务引用 quota（`schtasks /Query` 零命中）。**但它在真树上触发过两次**：
`reflex.log:147`（2026-07-28T20:57:17Z，空队列分支）与
`reflex.log:252`（上面那次）。**所以严重度不因「不可达」下调。**

### 7. 活状态：五个编号搁在那里，只能等下一次熔断，且盘面上看不见

`requeue = ["OPS-M","W-1671","OPS-A","RES-4","RES-3"]` 而 `mode = "normal"`。
`git grep requeue` 在 quota.py 与其测试之外**零命中**；`scan.py` 从不读 `quota_state.json`。
**没有任何渲染器画它。**

## 前案（这就是 severity 是 medium 而非 high 的原因）

`794e5b46:monitor/runs/20260729T2035Z-S28/ADV-2-fleet-loop.md:296` 已经写着：
「`dispatch.py --only OPS-M` finds no prompt because `os.listdir(PROMPTS)` is not [recursive]」。
**机制在这个 rev 上就已被记录。**
本报告新增的是：`prompt_id()` 正则那个更深的原因、**零比六的实测**、
以及**两份被污染的审计产物**。

## 两条我不予立案的（refuter 砍掉，照记）

1. **「history 里 6 条是手改的」→ 砍成 3 条，且是旧案重报，不立。**
   「缺 `killed` 键」这半**证据作废**：修订 `af1f5d9a`（主线 2026-07-28T16:58Z–22:16Z）
   的 `:213-214` 就是 `{"at": …, "from": "log-scan"}`、**没有 `killed` 键**，
   而那三条 killed-less 的 `log-scan` 条目（20:57:11Z / 20:57:17Z / 21:42:12Z）
   **正好落在那个窗口里**——它们是**合法的历史产物，不是手改**。
   真正无法被任何修订发出的只有 **3** 条
   （`monitor-false-positive-clear` / `monitor-clear-regression` / `pool-rotation`），
   而这 3 条**上一个周期就已立案且数字是对的**：
   `DRIFT-20260729T1515Z:64` 与 `DRIFT-20260729T1420Z:45,52`（后者还提了修法 `quota.py note --from <marker>`）。
   **我的「6」是把已作废的那半并进来造成的 2 倍虚高。** 不立案。
2. **「PREDICTION 1 应当废止」→ 改成「拆开」。** 见下。

## PREDICTION 1：**拆开，不要整条废止**（这是对我自己 state.json 的更正）

- **history 那一半：废止，它不是缺陷。** 九行逐条走完，1 条应有、1 条实有。
  最关键的是第 7 行（19:22:05Z，b 限到 20:30Z，本该 hold）——
  它被 `:389 if not already:` 压住，因为 `mode` 从 16:32:10Z 到 20:37:06Z 一直是 `hold`，
  **由 `reflex.log` 九条 `quota:HOLD` 独立佐证**（18:29:55Z…20:32:17Z）。
  没有任何一行该产生条目而没产生。
  且 `794e5b46:monitor/ACCOUNTS.md:62` 这份最接近规范的文本说轮换的可观测量是
  **打印出的 `ROTATED`**，不是 history。
- **但我原来那句「没有任何文档／注释／契约声称过相反的事」说过头了**：
  有三份先前的审计**建议**加这条 append，且都还是未撤回的开放建议——
  `DRIFT-20260729T1557Z:75-76`（一条预注册判别式，后由 `DRIFT-20260729T1729Z:108-110` 自撤）、
  `DRIFT-20260729T1729Z:117-118`、`DRIFT-20260729T1834Z:100`。
- **registry 那一半必须留着，它是真缺陷。** PREDICTION 1 的标题是
  「quota history write-**back**」，其正文把 `:393` 的 history append
  与 **`:398` 的 registry dump** 绑在一起，而后者的丢失已立案为
  `DRIFT-20260729T1420Z-rotation-forgets-which-sessions-it-handled`：
  rotated 路径上 `entry["reaped"] = "quota-requeued"`（`:512`）**只写在内存里**，
  `save_state` 写的是 `quota_state.json` 而不是 `registry.json`，
  而 `:398` 的 `json.dump(reg, …)` 在 `:386 return 0` 之后**不可达**。
  于是**每一次后续 `check()` 都会重新检出同一批死会话、重新进 `_rotate_on_limit`、
  重新以 `now` 重算的 `until` 调用 `mark_limited`——把那个账号的重开时间往后推一格。**
  我那张九行表里的第 3–5 行与第 9 行就是这个循环在发火。
  **整条废止会把这个一起废掉。**

## suggest（监控裁决，我不执行）

1. **`resume()` 必须核验它到底启动了什么**：`subprocess.run(..., capture_output=True)`，
   rc≠0 或 stdout 含 `nothing matched` 就**把编号留在队列里**、`mode` 保持 `recovering`、
   并把失败写进日志。现在「排空」与「启动成功」是同一行代码。
   同样地，`reflex.py:215` 的 `quota:RESUMED(auto)` 不该在检查 `r` 之前无条件写。
2. **修 `--only` 的编号空间，不是目录结构。** `prompt_id()` 的正则产生不出
   `OPS-*`／`RES-*`／`W-*`；移动提示词文件没有用。
   要么扩正则并让枚举递归，要么让 `resume` 走 `standing.py` 用的 `via_task` 那条路。
3. **`reflex.log:252` 那行应当被标注为不可靠**，并且
   **`DRIFT-20260729T2100Z:172-177` 那次撤回应当被复核**——
   它撤回一个结论所依据的那次「六个工人被拉起」从未发生。
   这是本报告唯一带追溯后果的一条。
4. **registry write-back 移到 `:386 return 0` 之前**（已在 carried 清单上，
   但现在有了新的后果证据：它让被限账号的重开时间每一跳往后推）。
5. `quota_state.history` 若要留，就给它一个只能由代码写的形状（拒绝未知 `from`）；
   否则它既无人读、又被手改（3 条），两头都不成立。

## 方法自陈

我在这条上犯了本周期第二次同类错误：**把一个后果写得比证据大**。
「工作丢失」听起来是最重的那半，实测是空的（`standing.py` 按角色重启覆盖了它）；
而真正重的那半——**假收据污染了两份审计证据，其中一份是我自己的交接件**——
我原稿一个字都没写。
**规则：追一个缺陷的后果时，先问「谁读了这个输出」，而不是先问「这会坏掉什么」。
读者名单比想象出来的坏结果可靠。**
