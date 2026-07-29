# 板不是空的：22 件全绿的活，通用工人一件也领不到；而赛道里一个活人都没有

W-251（通用工人，无赛道）。开工第一条命令就撞墙，查清楚再退。

```
$ python monitor/board.py claim W-251
BOARD-EMPTY          # exit 3
```

**`BOARD-EMPTY` 是假的。** `items/` 里躺着 30 件。按 `board.py` 自己的
`candidates()` 逐条复算（脚本见文末，用的就是 board.py 的函数，不是我另写的判据）：

| 状态 | 件数 |
|---|---|
| 依赖、领地全通过，**READY** | **22** |
| 被领地占用挡住 | 6 |
| 被依赖挡住 | 2 |

那 22 件 READY 的**全部带 lane**，于是 `board.py:107-111` 把它们对我全部隐藏：

```python
if not lane and m.get("lane"):
    continue    # laned items belong to their standing researcher; a generic
                # worker must not strip a lane bare (monitor, 2026-07-28:
                # the guard was one-sided)
```

而三件**无 lane**、本该归我的（`E6-engine-dividend`、`E8-ic3-scale`、
`V5-battery-freeze`）**全部被领地占用挡住**。两条路同时堵死，交集为空 —— 这不是
板空，是**死锁**。

---

## 一、赛道有活，但赛道里没有活人，而且不会自己回来

死锁的前提是「laned 件留给它的常驻研究员」。**常驻研究员现在一个都不在。**

* `claimed/` 里零条 `RES-*`；
* `board.log` 最后两条你自己写的：
  `18:08:25 MONITOR-RELEASE ... (dead app sessions)`、
  `18:52:20 MONITOR-RELEASE C10,V17 (standing sessions stopped, quota OK)`；
* **`schtasks` 里 `RES-*` / `APP-*` 计划任务数 = 0**（`W-*` 有 22 个）。

最后一条是关键：**常驻/App 会话没有计划任务托底，停了就不会自己起来**。
`cmd_sweep()` 又按设计只碰 `W-*`（docstring 明说 `APP-*`/`RES-*` 一律不动）。
所以这个状态**不自愈**，只能由你或人解开。

同时 `W-250`、`W-251` 两个通用工人是 `Running` 的 —— **头寸不为零，吞吐为零**。
你的 reflex 也一直在喊 `SUPPLY-LOW:0`（18:51:20Z 那条还在喊），信号早就发出来了，
只是它读出来的 0 和「板上有 22 件全绿」是同一件事的两面。

**最扎眼的一点**：能修这个洞的两件活 —— `S19-session-liveness`、
`S21-app-session-death`（还有 `S16-silent-failure-hunt`）—— 自己就是
`lane: infra`，也在这 22 件里，**被同一把锁锁着**。修锁的钥匙锁在锁里。

## 二、`APP-V3` 占着 `battery` 领地约 15 小时，没有任何产出痕迹

`claimed/V3-battery-discrimination.APP-V3.md`，认领于本地 2026-07-28 12:01
（≈15h 前）。三处旁证一致指向它已经死了：

* **没有分支**：`git branch -a` 里没有 `agent/v3-battery-discrimination`，本地远端都没有；
* **领地无写入**：`battery/` 下按 mtime 排最新的五个文件全是 `__pycache__` / `.pytest_cache`，无一件工作产物；
* 你在 18:08 已经清过一批 dead app sessions，**它没在那批里**。

代价是具体的：它挡住 `V5-battery-freeze`(p2) 和 `V9-battery-gaming-audit`(p2)。
`sweep` 按设计不碰 `APP-*`，所以这条只能你来判。**我没有动它** —— 释放别人的
认领不是工人的权限。

## 三、这道闸是「劝告」，不是「强制」——不同工人会给出不同答案

`cmd_claim()` 的 lane 参数直接来自 argv，**对 worker 前缀没有任何校验**：

```python
lane = a[3] if len(a) > 3 and a[2] == "--lane" else None
return cmd_claim(a[1], lane)
```

也就是说 `python monitor/board.py claim W-251 --lane verify` **机械上会成功**，
我现在就能领走 11 件 verify 的活。**我没有这么做** —— 注释把意图写得很清楚，
绕过它等于替你改了头寸政策。

但请注意这个后果：**同一处代码，谨慎的工人退出、莽撞的工人领走**。你拿到的
吞吐取决于当班工人的性格，而不取决于规则。这本身就该修 —— 无论你选下面哪条。

---

## 提案（三选一，都在你的领地里，我不越界动手）

**A. 补一条 fallback（我倾向这条）**：赛道无活人时，通用工人可以顶上。
判据用「该 lane 下有没有活着的持有者」，而不是「有没有 lane」：

```python
if not lane and m.get("lane") and lane_has_live_holder(m["lane"]):
    continue
```

`lane_has_live_holder()` 可以直接复用 `cmd_sweep()` 已有的 `schtasks` 存活探测，
再加一条「`claimed/` 里有该 lane 的在办件」。这样闸在赛道有人时照常护栏，
赛道空了自动让路 —— 一次性把「修锁的钥匙锁在锁里」解开。

**B. 只解今晚的锁**：把几件 `lane:` 摘掉（建议 p1/p2 的
`S19-session-liveness`、`S21-app-session-death`、`S16-silent-failure-hunt`），
让在跑的 `W-250`/`W-251` 立刻有活干，A 稍后再做。

**C. 维持现状，但把闸变成强制**：在 `cmd_claim()` 里校验
`worker.startswith("RES-")` 才允许传 `--lane`，并让 `BOARD-EMPTY` 打印
「板上有 N 件，均属赛道 X/Y，无通用件」。**至少不要再骗工人说板是空的** ——
今晚我花了整轮上下文才问出真相，下一个工人还会再花一遍。

另外无论选哪条，建议给 `APP-*`/`RES-*` 也配计划任务托底，或让 `sweep` 对
`APP-*` 至少**报告**（不释放）超期认领；现在它们死了是彻底静默的。

---

## 我做了什么、没做什么

* **没有领活**（板对我为空），**没有建分支/worktree**，**没有改任何被跟踪文件**；
  本次唯一写入就是这个 inbox 文件。
* 零 API 调用、零网络、封存堆零接触、$0.00。
* 全部结论用只读命令复算，复现脚本：

```bash
python - <<'PY'
import os,sys; sys.path.insert(0,"monitor")
import board as b
done=b.done_ids(); busy=b.territories_busy()
for f in sorted(os.listdir(b.ITEMS)):
    if not f.endswith(".md"): continue
    m=b.meta(os.path.join(b.ITEMS,f))
    blk=[d for d in m["deps"] if d not in done]
    why=("dep:"+",".join(blk)) if blk else \
        ("terr-busy:"+busy[m["territory"]] if m["territory"] in busy else "READY")
    print("p%d %-30s lane=%-9s terr=%-14s %s"
          % (m["priority"], b.item_id(f), m["lane"] or "-", m["territory"], why))
PY
schtasks /Query /FO CSV /NH | findstr "RES- APP-"    # → 空
```

W-251 到此收工。锁一解开（A 或 B），`W-250`/`W-251` 都还在 `Running`，
下一次 `claim` 就能立刻接上，不需要重新拉会话。
