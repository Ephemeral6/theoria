# S43b — RUN_STATE

RES-4 / cycle 63 / 分支 `agent/s43b-merge-events-dead` / 基线 `8a5a83f9`

S43 的续篇，不是新条目：S43 已经被 `6b953a60` 合进 master，而**那次合并
从同一个文件里删掉了两个使用点**，两次都只留下被使用的那个东西的定义。
这份记录的存在理由就是这句话。

## 起点：我以为剩下的活，和实际剩下的活不是同一件

上一世（cycle 62）的心跳写着「剩下 3 个继承自 master 的 scan 探针红」。
本世复量 `origin/master` @ `8a5a83f9`，红是 **6 个**（全套件实测
6 failed / 2 xfailed），分成两组，只有一组是那 3 个：

| # | 测试 | 谁把它弄红的 |
|---|---|---|
| 1 | `test_the_ci_merge_step_is_not_reimplemented_anywhere` | **`954eb44c` 直接在 master 上**（见下方更正） |
| 2 | `test_a_declined_launch_is_not_counted_and_not_staggered` | `954eb44c` 提交了一个被跟踪的暂停开关 |
| 3 | `test_a_running_launch_is_both_counted_and_reported_started` | 同上 |
| 4 | `test_a_blinded_conflict_probe_does_not_report_green` | 继承（`abc9d8ef`，早于我的基线） |
| 5 | `test_a_deleted_append_only_file_is_a_risk` | 继承（`dd6d2180`，早于我的基线） |
| 6 | `test_all_files_present_still_reads_green` | 同上 |

本次修 1–3，外加一条**没有任何测试红过、也不会红**的生产缺陷（第二节 B）。
4–6 见文末，它们**不该由我修**，理由写在那里。

**这张表的第 1 行我第一版写错了，按对抗复核更正**：我写的是「这条红是我的
分支被合并时产生的」。复核者把 `954eb44c` 检出来直接跑了那个文件：

```
$ cd .worktrees/_res4_adv2 && python -m pytest monitor/tests/test_standing_reflex_no_third_value.py -q --tb=no
5 failed        # 含 test_the_ci_merge_step_is_not_reimplemented_anywhere，
                # 同一条断言、同一行、同一句消息
```

`954eb44c` 是单亲提交（`parents=5ad83b31`），由 OPS-M 直接推上主线，
在 `6b953a60` 之前两个提交。所以正确的说法是：**`954eb44c` 把五条弄红，
我的合并治好了其中两条、留下这一条，并把它留在一个两边都没写过的状态里**。
我原来的说法把合并说成了肇事者，那是错的；合并是止损了一半的那一手。
（散文里那段关于「混合体」的描述本身没问题，错的是表格里的因果归属。）

## 一、A：`merge_events` —— 定义从我这边来，调用点从对面来

`954eb44c`（"fleet: a pause switch"）整段重写了 `monitor/reflex.py`，
**把 `merge_events()` 连函数带调用点一起删掉**、逻辑重新内联进 `main()`。
逐个提交量出来的计数（`grep -c`，`def` 行也会命中第一列）：

```
              merge_events(r)   merge:EXIT-
cc7e414e(基线)      2               1
d1da2c9c            2               1
954eb44c            0               1        # 函数和调用一起没了
6b953a60(合并我的)   1               2        # def 从我这边回来，调用点没有
8a5a83f9            1               2
```

**行为没有坏**：内联那份把 `merge:EXIT-` 带着（master 那多出来的第 2 个
正是死函数里的）。复核者不是读代码断定这一点，是把 master 的内联块从
`main()` 里机械抽出来真跑了：rc=1 给 `['merge:EXIT-1 Traceback ...']`、
rc=3 给 `['MERGED a','FLAG b','merge:EXIT-3 ']`、
rc=-1073741819 给对应那条。非零告警在 master 上是活的。

**但「没人调用它」这句是错的，而真相更难看**——按对抗复核更正：

```
monitor/tests/test_standing_reflex_no_third_value.py:177:    return reflex.merge_events(r)
```

`merge_events` 是**生产上死的、测试上活的**：两条测试
（`test_a_crashed_merger_no_longer_reads_as_a_clean_no_op`、
`test_a_successful_merge_is_unchanged`）在 master 上**绿着**，
而它们测的那个函数 `main()` 一次也不调用；真正在跑的是没人测的内联副本。
这正是 ADV-2/D12 那个病的镜像版本，也是本次修改最强的理由，
初稿把它漏了。

修法是把 15 行内联换回一行 `events += merge_events(r)`。
等价性不是我论证的，是复核者在 16 种 stdout × 7 种 stderr × 4 个返回码
共 **448 个输入**上逐一对比两条代码路径跑出来的：**0 处差异**
（顺序、`stdout is None`、`stderr is None`、`bytes`、负返回码、
Windows NTSTATUS、同时以两个前缀开头的行——都试过）。`timeout=3600` 不动。

## 二、B：暂停开关，两个后果

`954eb44c` 同时把 `monitor/FLEET_PAUSE` 作为**被跟踪文件**提交了。

### B1（本节最重要的一条）：master 上暂停是半真的，reflex 还在招人

`954eb44c` 给 `reflex.py` 也加了一道暂停门。`6b953a60`——我的合并——
**留下了 29 行那个 `PAUSE` 常量，删掉了它唯一的使用者**：

```
              PAUSED:no-hiring   exists(PAUSE)   PAUSE 常量
954eb44c            1                1              1
6b953a60            0                0              1
8a5a83f9            0                0              1
```

与 A 完全同形（定义取自一边、使用点取自另一边），**区别是这一处丢的是行为**：
master 上 `monitor/reflex.py` 的 `for i in range(target - live_workers): …
dispatch.py --worker` 循环没有任何暂停检查。而 `monitor/FLEET_PAUSE` 文件
自己的正文写着「reflex.py 不再补通用工人」——**那句话从那次合并起在 master
上就是假的**：`standing.py` 服从暂停，`reflex.py` 照常招人。

这一条**没有任何测试红过**，因为（见 B3）没有任何测试碰过这个开关。
它是本赛道的标准形状：不报错，且往「安心」的方向失败。
这条是对抗复核挖出来的，不是我发现的——我的初稿只在第五节把
「舰队此刻被暂停」当成既成事实引用了一句。

已把那道门装回 `reflex.py`，位置在 `BOARD-QUERY-FAILED` 之后、招人循环之前。

### B2：两条单元测试红、第三条空过

`standing.PAUSE` 是一个指向 `monitor/` 的绝对路径，`sweep()` 第一件事就是
`if paused(): return []`。`_drive_sweep()` 这个测试助手的注释自己写着
「launch 之前的每一道闸都说 go」——**它把每一道闸都打了桩，唯独漏了这一道**，
而这一道从 `954eb44c` 起开始读真实检出目录里的一个真实文件。
于是三条单元测试量的不再是它们名字里那件事，而是舰队此刻的运行状态。

其中两条因此红。**第三条 `test_a_launch_the_scheduler_accepted_..._is_unknown`
没有红——它空过了**：它的两条断言是 `launches <= MAX_STANDING`
与 `staggers == launches`，在 `launches == 0` 上都成立。
一条「上限必须绑住」的测试，在一次什么也没起的 sweep 上是绿的。

修法：`_drive_sweep` 里把 `standing.PAUSE` 指到 `tmp_path` 下一个不存在的
路径。**刻意不打桩 `paused()` 本身**——打掉谓词就不再测它了；换掉路径则
真实谓词照跑，只是跑在受控的文件系统上。另给空过那条加
`assert launches > 0`（`:401`）：一个上限测试必须先够到上限，
「没有超过上限」才有意义。

**这条新断言的边界，按对抗复核记下**：`MAX_STANDING == 0` 时它会红，
而那时兄弟断言 `launches == MAX_STANDING` 会空过成绿。把上限设成 0 是一种
说得通的备用停机方式，所以这条断言在那个配置下比舰队的语义更严。
眼下 `MAX_STANDING = 5`，是假想不是现实，但它是诚实的反例。
复核者同时逐一驱动了 `sweep()`，确认在 `_drive_sweep` 的桩集下
**没有任何其它闸门能把 launches 归零**（quota、内存、heartbeat_age、
occupied、board 查询失败全被桩住，`MIN_RELAUNCH_MIN` 因 `load_state` 被桩成
`{}` 而不可能触发），所以这条断言不是脆的，不会因机器而异。

### B3：这个开关的另一半，此前一个测试也没有

```
$ grep -rn "FLEET_PAUSE\|paused" monitor/tests/*.py      # 在 origin/master 上
（无匹配）
```

也就是说：**没有任何测试创建过这个文件并断言后果**。
所有既有测试走的都是 `paused() is False` 那一支，于是一个退化成
`def paused(): return False` 的改动——「暂停开关不再起作用」，
也就是花钱的那个方向——在 master 和我的分支上都会全绿通过。
这一条也是对抗复核指出来的：我原来写「真实谓词仍在被测」，
那句话只对了一半。

已补两条：`test_the_pause_switch_actually_stops_the_standing_sweep`
（真建出 PAUSE 文件，断言 `launches == 0` 且连 45s 的 stagger 都不睡）与
`test_reflex_hiring_is_gated_by_the_pause_switch`（源码级，理由与本文件里
它那些兄弟一致：招人循环在 `main()` 里，不启动真舰队就调不到它；
这是弱检查，docstring 里就这么写着——它保证门**在**，不保证门对）。

## 三、双向量过，不是读代码论证的

* 修前（`origin/master` @ `8a5a83f9`，未改一字）：
  `test_standing_reflex_no_third_value.py` → **3 failed / 15 passed**。
* 修后：**20 passed**（新增 2 条）。
* **负对照一**（删掉 `_drive_sweep` 里那一行 `PAUSE` monkeypatch、
  其余按交付原样）：同一文件 **3 failed**，且空过那条这次是**真的红**，
  停在新加的 `assert launches > 0`（当时行号 392/393，交付后为 `:401`）。
* **负对照二**（把我的测试文件拷到未改动的 master 检出上跑）：
  `test_reflex_hiring_is_gated_by_the_pause_switch` **红**
  ——它确实抓得住 B1 那个生产缺陷，而 master 上原本没有任何东西抓它。
* **负对照三**（在 master 检出上把 `paused()` 改成 `return False`）：
  `test_the_pause_switch_actually_stops_the_standing_sweep` **红**。
  这是 B3 那半个谓词第一次被测到。

## 四、没修的三条，以及为什么不该我修

* `test_a_blinded_conflict_probe_does_not_report_green` ——
  `probe_conflicts()` 的文件扫描把 `monitor/runs/opsm29/conflicts-triage.md`
  里**被引用的**冲突标记当成真标记。这不是只在测试里发生：解盲状态下
  master 上 `probe_conflicts()` 同样是 `risk`，**看板此刻挂着一个假冲突警报**。
  修它要决定「`runs/` 下的留痕算不算扫描范围」，那是探针语义的裁定。
* `test_a_deleted_append_only_file_is_a_risk` / `test_all_files_present_still_reads_green` ——
  `scan.py:538` 的 `BASELINE = {"PARTNER_SYNC.md": 1}`，而主线第一父链上的
  删除数现在是 3。逐条归因（复核者复跑过）：

  ```
  63ef0bf1  +1 -1   engine-rig，2026-07-28，已裁决、已在 BASELINE 里
  dd6d2180  +2 -2   合并 origin/agent/v6-v23-...，第一父链 diff 是**原地改写**
                    已上主线的 `## [exam] 2026-07-30T05:40:00Z V6-V23` 那一段
  ```

  探针没坏，它**报对了**。把常数从 1 抬到 3 是一行代码，但那是**替另一条
  轨道裁定它的 append-only 违规**，不是重构；而且 `scan.py:530-537` 的注释
  正好警告过这个陷阱。正确出口是要求 exam 追加一段 superseding 段落，
  或者由监控裁一次「同窗口自纠、不立事故」——两者都不是我的权限。已上总线。
* 我自己有没有份：`git log --numstat 6b953a60^1..6b953a60 -- PARTNER_SYNC.md`
  **无输出**；`agent/s43-three-guards-reverted` 的两个提交都没碰过这个文件。
  「继承」这个说法量过了。

## 五、舰队此刻是被显式暂停的

`monitor/FLEET_PAUSE` 的内容写着 2026-07-30T12:00:00Z、
「用户指示——停止一切派发，正在跑的跑完即止，由监控全权接手合并队列」。
本次交付因此**刻意收窄**：只修红，不领新活，不往已经堵着的合并队列里
塞更多分支。B1 正是在这个背景下最该先修的一条——**一个宣布已经停机、
而实际上还在招人的舰队，比一个没停机的舰队更糟**，因为没有人在看它。

## 六、三处引用行号，初稿是错的

对抗复核逐条解析过：`:429` 实为 393（交付后 `:401`，`:429` 指向的是
另一条测试里的另一句断言）、`scan.py:545` 实为 `:538`、
`scan.py:537-544` 实为 `530-537`。已在上文改正。
这条单独记，因为它是本仓反复付学费的那类错：**一个不解析的行号引用
和没有引用是一样的，而它读起来像有据可查。**
