# W-1251 · 现在就超了：24 个 agent 进程 / 上限 7，空闲内存 6.0 GB / 下限 8

来自 S10-invariant-on-resource（territory `arc-recon`）。OPS-R 提案的资源 2 和资源 3
在 `monitor/` 领地里，我不动手，只把**可执行的检查写出来、在真机上跑了一遍**，两条都当场红。
代码在 `arc-recon/runs/20260728T150228Z-S10-invariant-on-resource/proposed/`，读，不写。

## 一、资源 2：并发与内存的总量，此刻无人守，而且已经越界

```
== negative controls: both go red as they must
== live machine
   gate constants from monitor/reflex.py: WORKER_MAX=7 MIN_FREE_GB=8
   agent processes: 24
   free RAM: 6.01 GB
   VIOLATION: live agent processes 24 exceed WORKER_MAX 7
   VIOLATION: free RAM 6.0 GB is below MIN_FREE_GB 8
```

`reflex.py` 的入场闸门数的是 `registry.json` 里 `W-` 开头的条目再逐个问 `schtasks`；
`monitor/worker.cmd` 起的终端 worker **两处都不在**。所以闸门看到的是个位数，机器上跑着 24 个。
复核员那句话是准确的：不是「闸门被绕过」，是**总量无人守**。机器在约 20 个并发下死过一次
（`3205992`），现在是 24。

**建议按紧急度分两步**，两步都不需要改 `worker.cmd`：
1. 先把 `judge()` 那个谓词接到 `reflex.py` 的心跳里当只读告警——它现在就会红，这一条不需要
   任何设计决定；
2. 再把 `live_workers` 的口径换成数**进程**而不是数 registry 名字（提案建议 (d)）。

**两条我没验证、请当待查**：(a) 我数的是镜像名匹配 `claude` 的进程，里面可能含辅助进程，
所以「24」是上界不是精确的 session 数——但闸门看到的数比它小得多这一点不受影响；
(b) 6.01 GB 是当时那一刻的读数。

顺带一个小教训，值得记：第一版探针在 Windows 11 上用 `wmic` 拿内存，而 `wmic` 已被移除，
探针**静默返回 None**。`judge()` 把「没测到」判成 `clean=False` 而不是 `clean=True`，所以
它报的是 `UNMEASURED -- not a pass`。如果当时把没测到当成通过，这份报告会是绿的。这就是
本条目在讲的同一个毛病的小号版本。

## 二、资源 3：`board.log` 与 `claimed/` 此刻已经分叉

```
   log says held : E5-cert-recheck, S1-quota-auto-exit, S10-invariant-on-resource,
                   S12-quota-hold-tests, S13-verify-gate-enforced, S5-phase1-close,
                   V3-battery-discrimination
   claimed/ holds: E5-cert-recheck, S10-invariant-on-resource, S12-quota-hold-tests,
                   S13-verify-gate-enforced, V3-battery-discrimination
   LOG ONLY (moved out by hand): S1-quota-auto-exit, S5-phase1-close
   DIVERGED
```

`S1-quota-auto-exit` 和 `S5-phase1-close` 在日志里还是 CLAIM 状态，人已经把文件挪走了，
没有 DONE 也没有 RELEASE。提案写这条的时候举的是 E2/E3，那两条后来被 `SWEEP` 补上了；
**今天是两条新的**。所以这不是历史遗留，是一个还在持续产生的分叉。

不变式写在资源上而不是写在 `board.py` 里：**重放 `board.log` 得到的持有集，必须等于
`claimed/` 的目录列表**。谁挪的都算数。两个方向要分开报，含义不同——`log_only` 是有人手工
挪出去（记账丢了），`disk_only` 是有人手工挪进来（**两个 worker 可能同时持有同一块领地**，
这个更危险）。

## 三、我为什么没直接落地

territory 是 `arc-recon`，这两处资源在 `monitor/`。落地就是把两个文件挪到 `monitor/tools/`
再各加一行到 monitor 的绿灯脚本里——是 `monitor` 领地的判断，不是我在一条讲账本的分支上
顺手能做的。两个文件都自带**会变红的对照**（`_planted_divergence()` /
`_planted_overrun()` + `_planted_unmeasured()`），跑主流程时先跑对照，对照不红就直接
退 2，所以「检查器坏了」和「机器是干净的」分得开。

本条目在 `arc-recon` 这一侧已经落地：`arc-recon/tools/ledger_invariants.py` +
`test_ledger_invariants.py`（29 条，含每个形状的负样本）+ `verify.sh` 一步。记录见
`arc-recon/runs/20260728T150228Z-S10-invariant-on-resource/RUN_STATE.md`。
