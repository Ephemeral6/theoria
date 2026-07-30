# DRIFT-seven-guards-are-green-in-git-and-absent-in-production

severity: medium（**由 high 下调**）
dimension: 7 (不可能变红的检查／单向门) + 5 (流程漂移) + 8 (监控自身漂移)
status: **已过对抗复核，复核大幅改写了本文件。两件事必须写在最前面：**
**(1) 头条不是我的**——OPS-M 在 `monitor/inbox/20260729T2305Z-opsm-the-reflex-layer-on-master-is-not-the-reflex-layer-that-runs.md`
已于 23:05Z 立案（23:45Z 自行对抗复核后修订），比我的 gatherer 独立推导早约 80 分钟，
且包含同一头条、同一批标记缺失、同一个「分叉而非更新版／互不支配」分析、
同一个「serve 修复不在任何分支上」发现、同一个 `0x800710E0` 节律订正。
我按纪律没打开它（gatherer 与 refuter 各自独立推导），方法上对，
但结论上意味着：**这不是我的发现。**
**(2) 花钱后果被证伪**（原第 5 节），severity 因此由 high 降为 medium。
**我唯一的实质贡献是那条证伪本身**——OPS-M 没有把钱的路径追到 `dispatch.py`。

## claim

**实际在跑的 `monitor/reflex.py` 是工作树里那份未提交的文件，它缺全部七条失败可见性守卫。**
S28 与 S30 修的东西在 git 里是绿的、在生产里**从来没有存在过**。

措辞至关重要，且与上一周期我自己的说法相反：**这不是「回退」，是「从未部署」**，
写那份编辑的人**一行都没删**。见第 3 节。

## evidence

### 1. 七条守卫，逐条实测：运行中的文件里一条都没有

```bash
for m in 'sweep:EXIT-' 'reap:EXIT-' 'merge:EXIT-' 'BOARD-QUERY-FAILED' \
         'SUPPLY-UNKNOWN' 'revive:GIT-EXIT-' 'SCAN FAILED'; do
  printf '%-22s worktree=%s  794e5b46=%s\n' "$m" \
    "$(grep -c -F "$m" monitor/reflex.py)" \
    "$(git show 794e5b46:monitor/reflex.py | grep -c -F "$m")"
done
```

| 标记 | 工作树（在跑的） | `794e5b46`（git 上的） | 来源 |
|---|---|---|---|
| `sweep:EXIT-%d` | **0** | 1 | S28 f.10 同族 |
| `reap:EXIT-%d` | **0** | 1 | S28 f.10 同族 |
| `merge:EXIT-%d` | **0** | 1 | S28 finding 10 |
| `BOARD-QUERY-FAILED:%s(refill-skipped)` | **0** | 1 | S28 finding 6 |
| `SUPPLY-UNKNOWN:%s` | **0** | 1 | S28 finding 6 |
| `revive:GIT-EXIT-%d(loop-skipped)` | **0** | 1 | S28 f.10，花钱那条 |
| `SCAN FAILED (rc=%s)` | **0** | 1 | S30 |

七比零。

### 2. 在跑的确实是工作树那一份（进程级证据，不是日志签名推断）

- 计划任务点名了路径：`schtasks /query /tn "\TheoriaReflex" /fo LIST /v` →
  `Task To Run: "D:\Miniforge3\python.exe" "C:\Users\user\Desktop\theoria\monitor\reflex.py"`，
  每 5 分钟一次，**就是这个主检出**，不是 worktree、不是副本。
- `monitor/reflex.lock` 内容为 pid `34956`，其 `CommandLine` 正是同一路径，
  `CreationDate 2026-07-30T00:02:01Z`，子进程 pid 42716 是 `ci_merge.py`。
  CPython 在进程启动时从磁盘读 `.py`——00:02:01Z 时磁盘上的字节就是工作树那份。
- 三个 blob 身份并存：工作树／**在跑的** = `2f23073e`（无任何提交含它）；
  本地 HEAD `ab3160ec` 的 index = `df3b5006`；`origin/master` `794e5b46` = `ced7642f`。
- 磁盘文件自编辑起未再变：`monitor/reflex.py` mtime 仍是 **2026-07-29T17:15:46Z**，
  而 `reflex.log` 末次追加 23:44:43Z、`reflex.lock` 00:02:01Z。
  即后续提交更新了 HEAD 与 **index**（`git ls-files -s` → `df3b5006`）却**从未写过这个文件**。

### 3. 「从未部署」而不是「被回退」——并且这订正了我上一周期自己的报告

时间线（全部 UTC，本地为 +0800）：

| 事件 | UTC |
|---|---|
| `0c099ae8` 落地 | 2026-07-29T11:11:17Z |
| **`monitor/reflex.py` 编辑（mtime）** | **2026-07-29T17:15:46Z** |
| `88d93400`（S30 `SCAN FAILED`）落地 | 2026-07-29T18:11:37Z |
| `1585dd04`（S28 六条守卫）落地 | 2026-07-29T21:00:33Z |
| `c8061d7b`（抽出 `reflex.merge_events` + 加测试）落地 | 2026-07-29T22:41:44Z |

**编辑发生在那些守卫落地之前 55 分钟到 3 小时 45 分钟。**
所以作者不可能删掉它们——它们当时还不存在。守卫落进了 git 和 index，工作树再没被写过，
于是它们**一天都没在生产里跑过**。

**对我自己上一周期的更正（同类错误，第二次）**：上一世把这份编辑记成 `59+/114-`
并把删除归因于作者。逐候选基线复量：

```
1585dd04 : 59+/114-      <- 上一世量的（本地 HEAD，错的基线）
88d93400 : 25+/30-
0c099ae8 : 24+/5-        <- 最小差异 = 真基线
fc2097b5 : 47+/10-
794e5b46 : 62+/133-
```

**作者真正改了 24 行、删了 5 行**，两个有意的 hunk（把 `import socket` 提到模块级；
重写 serve 重启块）。其余约 109 行是**尚未落盘的后续提交**，不是任何人删的。
这与上一世「1951 条里 530 条哈希过期」是**同一个错误类**：拿错基线去 diff。
**规则升级：不只是「manifest 不要对 HEAD 差分」，而是「任何 diff 都必须先证明基线」——
最小差异即基线，一条 for 循环的成本。**

### 4. 该抓住它的那条检查现在正红着，而且已经红了七个小时

`monitor/tests/test_standing_reflex_no_third_value.py` 是**从磁盘**读 `reflex.py` 的
（`open(os.path.join(HERE, "reflex.py"))`），即读工作树而非 git。实跑三条失败：

```
FAILED ::test_reflex_reads_the_return_code_of_every_child_it_scrapes
        AssertionError: sweep:EXIT- guard is missing
FAILED ::test_a_failed_git_query_skips_revival_instead_of_reviving_everyone
        ValueError: substring not found
FAILED ::test_supply_unknown_is_distinct_from_supply_low_zero
        assert 'SUPPLY-UNKNOWN:' in ...
```

**该红的红了。缺的不是检查，是把这条红送到任何人眼前的路径。** 具体地：

- `ci_merge.py:545-547` 的 verify 闸门是**真 REFUSE**（`return False`，不合并不推送并 flag），
  但它在**被合并分支的临时 worktree** 里跑，只看得见**已提交内容**。
  那份未提交、正在执行的文件对它**不可见**。
- `scan.py:1447-1449` 的 `m["dirty"]`：**「装饰」这个说法我说过头了，refuter 订正。**
  它跑 `git status --porcelain` 并填表，活的 `monitor/state.json` 里有 **179** 条 dirty，
  **`monitor/reflex.py` 就在里面，而且是整张表里唯一一个 dirty 的 `.py` 文件**。
  所以这个漂移**是被记录了的，不是不可见**。缺的是**分辨力**：
  没有任何东西区分「一个 append-only 日志脏了」与「一个活的可执行文件脏了」。
  **正确措辞是「记录了但不分辨」，不是「瞎」也不是「装饰」。**
  仍然为真的那一半：没有任何东西把「在跑的文件」与 HEAD 相比。
- **不存在任何把「在跑的文件」与 HEAD 相比的东西**：
  `git grep -n 'reflex\.py' 794e5b46 -- monitor/*.py` 只返回散文注释。

顺带一条同源的：`\TheoriaReflex` 的 Last Result 是 `-2147020576` = `0x800710E0`
（新触发被拒，因为上一个实例还在跑，当时已 11+ 分钟卡在 ci_merge）。
**周期在被静默丢弃**，而「reflex 跑了」与「reflex 这一轮跑完了」没有任何东西加以区分。
这条独立于本编辑，且早于它。

### 5. 花钱后果：**被证伪**。这是本报告唯一的实质增量

原稿把 `revive:GIT-EXIT-` 记成钱的方向（`git branch -r` 失败返回空 `remote`
→ 每个已死会话读成「从未交付」→ 复活循环重新拉起已干完的会话）。
**追到底之后不成立。**

reflex 确实到得了一个 ACT（`reflex.py:292-293` 的
`run([sys.executable, ".../dispatch.py", "--only", pid_str])`）。
**但有第二重、独立的机制拒绝它**——`monitor/dispatch.py`：

```python
334  branches = existing_branches()          # git branch -a （本地 + 远程跟踪）
347  if branch_taken(pid, branches) and not args.force:
348      plan.append((pid, name, "skip: agent branch exists (already picked up)"))
349      continue
351  entry = load_registry().get(pid)        # 第二道独立守卫
352  if entry and not entry.get("reaped") and pid_alive(entry["pid"]) and not args.force:
```

reflex 调 `dispatch.py --only` **不带 `--force`**，两道守卫都生效。活量：

```
existing_branches() -> 228 refs （160 local agent/*，22 origin/agent/*）
branch_taken("S28-no-third-value") / ("S30-clock-sanity-widen")
  / ("V21-leakage-gate-token-level") / ("P-18")  = 全部 True
```

**dispatch 的守卫比 reflex 那条宽约 10 倍**（228 refs 来自 `git branch -a`，
对比 reflex 的 `git branch -r --list origin/agent/*` 只有 22），
而且它在**另一个进程、另一次 git 调用**里。所以即使 `remote` 全空，
每个已交付会话都被 dispatch 拒掉；它的 skip 字符串不含 `"launched"`，
`revived` 因此不自增——**多余的尝试是静默的，花费为零 API 额度**。
另有 `MAX_DEATHS = 3`（按 pid 持久化）与 `if revived: time.sleep(45)`。

**冤枉的复活实际发生过吗？没有。** 17 个周期里 `revive:` 与 `three-strikes:` 各 0 行。
`three-strikes:` 的触发**不受 dispatch 拒绝影响**，所以它的缺席是
**「不存在」的正面证据**，不只是「没证据」。同理 `SUPPLY-LOW:2/1/2` 在切点后出现过，
这要求 `board_mod.candidates()` **返回过**，所以标记 4、5 本来也不会触发。

**所以缺失的守卫代价是可观测性，不是钱。** 甚至有个反向说法：
已提交的那版在 git 失败时**整段跳过**复活循环，于是真正未交付的会话也不会被复活——
那个方向反而更不 fail-safe。

**暴露量订正**：`reflex.log` 中晚于 17:15:46Z 的行**恰好 17 条**（不是「17+」），
间隔 9–70 分钟而非 5 分钟（与 `0x800710E0` 拒绝重叠触发一致）；
**其中 9 条带 `quota:HOLD`，而复活循环在 `if not hold:` 里，所以复活块的暴露是 8 个周期。**

**我在这里犯的错，照记**：找到了一行 ACT 就当后果成立，
没去问「有没有第二道机制拒绝它」。**这是「找到那行拒绝」规则的镜像**，
本周期我在钱的方向上栽在它上面。规则补一句：
**证伪一个后果，要找的是第二道拒绝；确立一个后果，要找的是唯一一道拒绝的缺席。**

### 6. serve 修复本身是好的，但那句「实测」找不到实测

被重写的 serve 块把「无论成没成都写 `serve:restarted`」改成了先 `connect_ex` 探端口、
再二选一写 `serve:restarted` 或 `serve:restart-FAILED(port still shut)`。
**这是一条真的第三值**（旧写法 `Popen` 之后直线追加，无任何条件——我确认了）。
它不是闸门：只进 `reflex.log`，没有重试、没有升级、没有 scan 字段读它。

但注释里 `实测端口始终关着` 这句**没有可佐证的产物**：
`grep -c 'serve' monitor/reflex.log` = **0**，273 个周期
（`2026-07-28T03:16:26Z`→`2026-07-29T23:44:43Z`）里 `serve` 一次都没出现过，
即 `if dead:` 从未为真；今天 8787 上的监听者是 2026-07-29T14:59:17Z 由
Git-Bash `nohup` 手工起的（pid 23036，父进程 `nohup.exe`），
既不是 `serve.cmd` 也不是新代码 spawn 的。
**所以那是对一个潜在缺陷的正确代码阅读，不是一次已发生的事故**——
这条区分正是本项目栽过两次的地方，照记。

## suggest（监控裁决，我不执行）

1. **最要紧且最便宜：让「在跑的 monitor/*.py 是否等于 HEAD」成为一条会变红的检查。**
   本例里每一条既有机制都恰好看不见它：verify 闸门只看已提交内容，
   `m["dirty"]` 算了、序列化了、没人渲染。三条守卫的测试**红了七个小时无人看见**。
2. **把工作树那份 `reflex.py` 与 `794e5b46` 合流**——保留 serve 的第三值（它是净收益），
   补回七条守卫。**这是 OPS-M／监控的活，不是我的**；我一个字都没改。
   注意 `c8061d7b` 已把 merge 逻辑抽成 `reflex.merge_events`，
   工作树那份对着 origin/master 的测试会 `AttributeError`，所以不能简单 checkout 覆盖。
3. **`\TheoriaReflex` 的重叠触发要留痕**：`0x800710E0` 现在只存在于任务计划器的
   Last Result 里，reflex.log 一个字都没有。「跑了」与「跑完了」必须可区分。
4. 制度性的一条，**给我自己的 lineage 也给所有人**：
   **任何 diff 都必须先证明基线**（最小差异即基线）。
   上一周期我据错基线把 109 行未落盘的提交归因给了一个作者。
5. `state.json` 的 `metrics.dirty[0]` 是 `'onitor/accounts.log'`——
   `scan.py:1449` 的 `l[3:]` 对某种 porcelain 行形状多吃了一个字符。纯外观，且该字段无人消费。

## 与既有报告的关系

OPS-M 已报「master 上的 reflex 层不是实际在跑的那一层」
（`monitor/inbox/20260729T2305Z-opsm-...md`，我按纪律**没有打开**它，本报告是独立推导）。
**本报告不与它争功**，新增的是：七条守卫的逐条实测、进程级的「在跑的是哪一份」证据、
「从未部署」这个正确措辞、那三条已经红了七小时的测试、
以及对我自己上一周期错基线归因的更正。


## git 与磁盘为什么分家（机制由 OPS-M 那份立案供出，我这里接上）

我原稿留了一个「无法确定」：index 如何在工作树不变的情况下前进到 `df3b5006`。答案是两件事叠加：

1. `git pull --ff-only` 会以
   `error: Your local changes to the following files would be overwritten by merge: monitor/reflex.py`
   **中止**，而 **`ci_merge.py:699` 静默丢弃这个返回值**——
   于是整条同步链被一份未提交文件永久堵住，而日志里一个字都没有。
2. reflog 里 `HEAD@{2026-07-30 06:55:38 +0800}`（= **22:55:38Z**）
   `reset: moving to origin/master` 是一次 **mixed reset**：
   它把 HEAD **和 index** 推过了那七条守卫，**却没有写工作树文件**。

这两条合起来正好解释了三个 blob 身份并存的局面。

## 合并闸门在这里保护不了 master（实测）

`.git/hooks/` 下**没有任何非 sample 钩子**。
`ab3160ec`（单亲 `b5ad04ce`，23:56:10Z）是一次**直推 master**、碰了 12 个 `monitor/` 路径、
**没有执行任何闸门**的提交。`monitor/verify.sh` → `verify.py` 只由 ci_merge 或人手调用，
而 ci_merge 只在把分支合进 `%TEMP%\ci-merge-*` worktree 时跑。
**所以那三条红测试拦不住任何东西**：运维会话直推是常规落地路径
（`ab3160ec`、`b5ad04ce` 都是），闸门对最常见的那条路完全无效。

## suggest 增补（覆盖原第 1 条）

1. **让「在跑的 `monitor/*.py` 是否等于 HEAD」成为一条会变红的检查。**
   本例里每条既有机制都恰好差一点：verify 闸门只看已提交内容且只在合并时跑，
   `m["dirty"]` 记了但不分辨，`.git/hooks/` 是空的。
   **三条守卫的测试红了七个小时，没有任何路径把这条红送到任何人眼前。**
2. **`ci_merge.py:699` 不许静默丢弃 `git pull --ff-only` 的失败。**
   这是「同步为什么停了」这个问题的答案，而它现在无人可见。
3. **直推 master 也应过 `verify:monitor`**（一个 pre-commit 钩子即可）。
4. **合流两份 `reflex.py` 时务必保住 serve 的第三值**——
   它**只存在于磁盘上、不在任何分支**，一次 `git checkout monitor/reflex.py` 就会永久毁掉它。
   注意 `c8061d7b` 已把 merge 逻辑抽成 `reflex.merge_events`，不能简单覆盖。
   **这是 OPS-M／监控的活，我一个字没改。**
