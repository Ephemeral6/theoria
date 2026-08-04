priority: 1
cell: A31
territory: theoria-arm
deps: none
spend: none

# A31-the-win-detector-has-never-fired-and-the-round-total-turns-absence-into-zero · 通关信号这条路从未被走过一次，而记分板把「没测到」写成了 0

臂**有**关卡边界探测器：`inner/levels.py` 完整实现了 `observe()`、跳级计数
（`:128-129`）、`final_level` 判据（`:102`）与 `levels.jsonl` 事件行
（`:113-117`）。问题不是它不存在。

**问题是它一次也没有发过。** 逐目录点过 `runs/*/levels.jsonl`：

```
20260728T235841Z-leg01                lines=0  bytes=0
20260728T235842Z-leg02                lines=0  bytes=0
20260728T235843Z-leg01                lines=0  bytes=0
20260729T0030Z-a3-desk-live-proof     lines=0  bytes=0
20260729T0035Z-a3-desk-live-proof2    lines=0  bytes=0
20260729T004020Z-leg01                lines=0  bytes=0
20260729T105653Z-leg01                lines=0  bytes=0
20260729T105729Z-leg01                lines=0  bytes=0
20260731T1240Z-A3-level2-carried      lines=0  bytes=0
20260731T1310Z-A3-level2-carried-r2   lines=0  bytes=0
20260731T1430Z-A3-level2-carried-r3   lines=0  bytes=0
20260731T1500Z-A3-sk48-carried-l1     lines=0  bytes=0
20260731T231654Z-R1-g50t-a            lines=0  bytes=0
20260731T231654Z-R1-sk48-b            lines=0  bytes=0
20260801T001851Z-R1b-g50t-a           lines=0  bytes=0
20260801T001851Z-R1b-sk48-b           lines=0  bytes=0
20260801T043743Z-R2-g50t-a            lines=0  bytes=0
20260801T043743Z-R2-sk48-b            lines=0  bytes=0
20260801T044640Z-R2b-g50t-a           lines=0  bytes=0
20260801T044640Z-R2b-sk48-b           lines=0  bytes=0
a3-gate-mock                          lines=0  bytes=0
audit-smoke                           lines=0  bytes=0
```

二十二个文件，二十二个零字节，**包括两条 mock 腿**。所以「臂赢了一次会发生
什么」这条代码路径，**在这个仓库里从未执行过，一次也没有，连离线都没有**。
它是本项目最重要的那次事件的唯一记录器，而它未经检验。这不是「还没赢所以
没有行」——mock 腿本来就该在离线把它走一遍，它们也没有。

## 而记分板会把这件事读错，是可以证明的

`armtools/round.py:104` 老实读 `RUN_STATE.json` 的 `levels.levels_completed`，
**可以是 `None`**。十四行之后，同一个文件的注释亲口写下这条规矩：

> `theorize_rounds` is the scoreboard column Theoria.md:351 names, and it is
> absent on runs that stopped before the first theorize — **absent is recorded
> as absent, never as zero** (battery/REPORT_V0.md's rule).

然后在 `round.py:188`：

```python
"levels_completed": sum((l.get("levels_completed") or 0) for l in legs),
```

`or 0`。一条**从未报告过关卡状态**的腿，在轮总计里与一条**报告了零通关**的腿
逐字相同。R2 那一轮四条腿全是 `reset_failed`、零动作、根本没进过世界，它的
`totals.levels_completed` 依然是 `0`——读起来像「跑了，没通关」，实际是
「没跑」。这正是那条注释自己禁止的事，写在同一份文件里，相隔八十四行。

## 欠的是什么

1. `round.py:188` 的三处 `or 0` 归约（`usd` / `actions_ok` / `desk_calls` /
   `levels_completed`）改成：任一腿缺该键则总计落 `null` 并另记
   `legs_missing_<key>` 计数。不要静默补零。
2. 离线走通一次**赢**：用 mock 世界让 `inner/levels.observe()` 真的跨一次
   边界，`levels.jsonl` 落出至少一行，`RUN_STATE.json` 的 `levels` 带上非零
   `levels_completed`，`round.json` 把它端上来。这是本仓库第一次执行这条路径。
3. 顺带钉住跳级：`levels.py:128` 的 `skipped` 分支同样从未执行过。

## 验收

一条 mock 腿产出 `levels.jsonl` 非空且 `round.json.totals.levels_completed >= 1`；
把 R2 那一轮（两条零动作腿）重新归约，`totals.levels_completed` 必须是
**`null` 加 `legs_missing_levels_completed: 2`**，不再是 `0`。

## 负样本，两条

* 一条**跑满了但确实没通关**的腿（`20260801T044640Z-R2b-g50t-a`，29 个动作）
  重新归约后必须仍是 `0` 而不是 `null`——本件是要分开这两句话，不是把所有 0
  都改成 null。
* 一条 `final_level` 已达的 mock 腿必须**停止**并落终局事件，而不是继续
  `observe()` 把 `completed` 越加越大；`levels.py:102` 的那个分支同样没有
  被任何一次执行覆盖过。
