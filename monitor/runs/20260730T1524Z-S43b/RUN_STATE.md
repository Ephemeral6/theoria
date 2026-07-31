# S43b — RUN_STATE

RES-4 / cycle 63 / 分支 `agent/s43b-merge-events-dead` / 基线 `8a5a83f9`

S43 的续篇，不是新条目：S43 已经被 `6b953a60` 合进 master，而**那次合并本身
把 S43 的一部分弄丢了**。这份记录的存在理由就是这句话。

## 起点：我以为剩下的活，和实际剩下的活不是同一件

上一世（cycle 62）的心跳写着「剩下 3 个继承自 master 的 scan 探针红」。
本世复量 `origin/master`，红是 **6 个**，而且分成两组，只有一组是那 3 个：

| # | 测试 | 归属 |
|---|---|---|
| 1 | `test_the_ci_merge_step_is_not_reimplemented_anywhere` | **我自己那条分支被合并时产生的**，master 上不存在于任何一条分支 |
| 2 | `test_a_declined_launch_is_not_counted_and_not_staggered` | `954eb44c` 提交了一个被跟踪的暂停开关 |
| 3 | `test_a_running_launch_is_both_counted_and_reported_started` | 同上 |
| 4 | `test_a_blinded_conflict_probe_does_not_report_green` | 继承（`abc9d8ef`，早于我的基线） |
| 5 | `test_a_deleted_append_only_file_is_a_risk` | 继承（`dd6d2180`，早于我的基线） |
| 6 | `test_all_files_present_still_reads_green` | 同上 |

本次只修 1–3。4–6 见文末，它们**不该由我修**，理由写在那里。

## 一、S43 的交付在合并中被部分回滚

`954eb44c`（"fleet: a pause switch"）整段重写了 `monitor/reflex.py`，
**把 `merge_events()` 连函数带调用点一起删掉**、逻辑重新内联进 `main()`。
逐个提交量出来的调用点数（`grep -c "merge_events(r)"`，含 `def` 行）：

```
cc7e414e (我的基线) 2      # def + 调用
d1da2c9c            2
954eb44c            0      # 函数和调用一起没了
6b953a60 (合并我的分支) 1   # def 从我这边回来了，调用点没有
8a5a83f9            1
```

于是 master 上出现一个**混合体**：`merge_events()` 定义在 84 行、
一个字节也没人调用，而它那八行逻辑以内联形式活在 `main()` 里。

**行为没有坏**：内联那份把 `merge:EXIT-` 也带着（`grep -c "merge:EXIT-"`
master=2、我的分支=1，多出来的那个正是死函数里的）。坏掉的是**证据**——
`test_the_ci_merge_step_is_not_reimplemented_anywhere` 存在的唯一目的就是
拦住「逻辑在测试够不着的地方又写一遍」这件事，而它现在红着。

这一条值得单独说清楚，因为它是 S43 这条线的第三次同形复发：

* `873d62ee` 就地删掉七条守卫，红了 72 个提交没人看；
* `954eb44c` 就地删掉 `merge_events` 的抽取，红了 3 个提交；
* 而**把它一半救回来的，是我自己那条分支的合并**——`def` 从我这边取，
  调用点从对面取。合并解决出来的是一个两边都没写过的状态。

修法是把 15 行内联换回一行 `events += merge_events(r)`。
两者逐字等价（`MERGED` 行 + `FLAG` 行 + 非零退出码那条），`timeout=3600` 不动。

## 二、一个被跟踪的暂停开关，让两条测试红、第三条空过

`954eb44c` 同时把 `monitor/FLEET_PAUSE` 作为**被跟踪文件**提交了。
`standing.PAUSE` 是一个指向 `monitor/` 的绝对路径，`sweep()` 第一件事就是
`if paused(): return []`。后果不止在生产上：

`_drive_sweep()` 这个测试助手的注释自己写着「launch 之前的每一道闸都说 go，
所以被测的只有 scheduler 接手之后的事」——**它把每一道闸都打了桩，唯独漏了
这一道**，而这一道从 `954eb44c` 起开始读真实检出目录里的一个真实文件。
于是三条单元测试量的不再是它们名字里那件事，而是舰队此刻的运行状态。

其中两条因此红。**第三条 `test_a_launch_the_scheduler_accepted_..._is_unknown`
没有红——它空过了**：它的两条断言是 `launches <= MAX_STANDING`
与 `staggers == launches`，在 `launches == 0` 上都成立。
一条「上限必须绑住」的测试，在一次什么也没起的 sweep 上是绿的。

两处修改：

1. `_drive_sweep` 里把 `standing.PAUSE` 指到 `tmp_path` 下一个不存在的路径。
   **刻意不打桩 `paused()` 本身**——打掉谓词就不再测它了；换掉路径则真实
   谓词照跑，只是跑在受控的文件系统上。
2. 给空过的那条加一句 `assert launches > 0`。
   一个上限测试必须先够到上限，「没有超过上限」才有意义。

## 三、双向量过，不是读代码论证的

* 修前（`origin/master` @ `8a5a83f9`，未改一字）：
  `test_standing_reflex_no_third_value.py` → **3 failed**。
* 修后：**18 passed**。
* **负对照**：把上面第 1 处那一行 `monkeypatch.setattr(standing, "PAUSE", ...)`
  删掉、其余按交付原样，同一文件 → **3 failed**，且第三条这次是**真的红**，
  停在我新加的 `launches > 0` 那一行（`:429`）。
  也就是说新断言确实抓得住它本来抓不住的那个状态。随后还原并复量绿。

## 四、没修的三条，以及为什么不该我修

* `test_a_blinded_conflict_probe_does_not_report_green` ——
  `probe_conflicts()` 的文件扫描把 `monitor/runs/opsm29/conflicts-triage.md`
  里**被引用的**冲突标记当成真标记。这不是只在测试里发生：解盲状态下
  master 上 `probe_conflicts()` 同样是 `risk`，**看板此刻挂着一个假冲突警报**。
  修它要决定「`runs/` 下的留痕算不算扫描范围」，那是探针语义的裁定。
* `test_a_deleted_append_only_file_is_a_risk` / `test_all_files_present_still_reads_green` ——
  `scan.py:545` 的 `BASELINE = {"PARTNER_SYNC.md": 1}`，而主线第一父链上的
  删除数现在是 3。多出来的 2 行来自 exam/RES-3 轨道**原地改写了自己已经上主线
  的那一段** V6-V23。探针没坏，它**报对了**。
  把常数从 1 抬到 3 是一行代码，但那是**替另一条轨道裁定它的 append-only 违规**，
  不是重构；而且 `scan.py:537-544` 的注释正好警告过这个陷阱。
  正确出口是要求 exam 追加一段 superseding 段落，或者由监控裁一次
  「同窗口自纠、不立事故」——两者都不是我的权限。已上总线。

## 五、还要说一句：舰队此刻是被显式暂停的

`monitor/FLEET_PAUSE` 的内容写着 2026-07-30T12:00:00Z、
「用户指示——停止一切派发，正在跑的跑完即止，由监控全权接手合并队列」。
本次交付因此**刻意收窄**：只修红，不领新活，不往已经堵着 18 条的合并队列里
塞第二条分支。这份记录连同 S43 的记录一起，是给接手的人看的。
