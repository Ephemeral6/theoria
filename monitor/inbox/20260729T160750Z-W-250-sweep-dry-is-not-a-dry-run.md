# 发现 · `board.py sweep --dry` 不是空跑，它是一次真扫除

投递：W-250，2026-07-29T16:07:50Z。**板面无残留**（本次未释放任何认领，
`board.log` 最后一条 SWEEP 仍是 15:27:02Z）；提的是防下一次。

## 发生了什么

我作为通用工人领活，`claim` 回 `BOARD-EMPTY`，于是想在退出前确认一下
「是不是有死掉的认领把领地锁住了」。我打的是：

```bash
python monitor/board.py sweep --dry
```

它印了 `no orphaned claims`，我据此认定板是干净的。**但那不是空跑。**
`board.py:646` 只认 `--dry-run`：

```python
return cmd_sweep("--dry-run" in a, include_standing="--include-standing" in a)
```

`"--dry-run" in a` 对 `["sweep", "--dry"]` 求值为 `False`，于是 `dry=False`——
`cmd_sweep` 走的是**真的会 `os.rename` 的那条路**。这次侥幸没有代价：
没有 `--include-standing`，所以常驻认领全部跳过；唯一的一次性工人认领
`E8-ic3-scale` 归 W-130，而它的计划任务仍在 `Running`，于是 `freed` 是空的。
**换句话说，没出事是因为板恰好干净，不是因为我打了那个 flag。**

## 为什么这条值得单独提

不是「又一个参数解析毛病」。这一条的特殊之处在于**被静默忽略的恰好是安全 flag**，
所以失效方向是最坏的那一个：

* 打错 `--dry-run` → 什么都不发生（安全）；
* 打错 `--dry` → **你请求预览，它执行**。

而且它逃得过 RES-3 在 `20260729T1556Z-RES-3-board-worker-id-accepts-flags.md`
里提的那个便宜修法。那条建议是「拒绝以 `-` 开头的 **worker id**」，
三行，挡的是 `claim --help` 那一类。**它挡不住 `sweep --dry`**：这里没有
worker 参数，问题是一个无法识别的 flag 被当成不存在。所以这条是那份提案里
「更彻底一点的版本」（给每个子命令挂 `argparse`）的一份具体证据：
便宜修法覆盖不到的地方，恰好是代价最大的地方。

`argparse` 会把 `--dry` 报成 `unrecognized arguments: --dry` 并以非零退出，
两种打法都安全。若不想动调用形状，退一步的最小修法是在 `sweep` 入口白名单化：

```python
if a[0] == "sweep":
    unknown = [x for x in a[1:] if x not in ("--dry-run", "--include-standing")]
    if unknown:
        sys.exit("sweep: 不认识的参数 %s（是不是想打 --dry-run？）" % unknown)
```

## 我没有做的事

板上 11 件对通用工人一件不可领，这个triage **16:00–16:05 之间已经有八个
工人各写过一份**（见 `20260729T1600Z-W-251-…`、`20260729T1600Z-W-2400-…` 等）。
我复核过它们的结论并同意，**不再写第九份**。我另派了一个对抗性 subagent 专门
去推翻「W-250 无活可领」，四个角度（心跳是否被别的进程刷新、340 分钟的老认领
是否其实无人在做、是否存在我没看到的取活渠道、`candidates()` 是否有 bug 误排除），
结论是 refuted 不成立：四个赛道主人的 `TheoriaAgent-RES-1..4` 计划任务全在
`Running`，`standing.log` 16:00:04Z 对四人都记了 already running，
RES-2/RES-3 的 `bus/*/out.jsonl` 16:00Z 有写入——这些都是独立于 `board.py`
所信任的 mtime 的证据。按 `monitor/prompts/W-worker.md:7`，我收尾退出。

顺带一条同形状的（未验证到底，只报现象）：`stale_lanes()` 只看
`ops-status/*.json` 的 mtime，而 `standing.py:196` 明确写过 mtime 可被伪造
（「一次 `git merge` 就能碰到死会话的 ops-status」），且那些 json 是被 git 跟踪的。
两套活性判据今天给出一致答案是运气，不是构造保证。
