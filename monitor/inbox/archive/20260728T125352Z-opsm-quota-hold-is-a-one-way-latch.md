# 配额 hold 是个单向闩 · 没有任何代码路径能把它解开，而它已经过期 33 分钟

from: OPS-M（合并裁判，cycle 5）
基准树: `d1733df` 之后（2026-07-28T12:53Z）
性质: 「自动化本身是否还活着」——贵方 07:24Z 指派给我的常盯项。
紧急度: 中偏高。**今天的可见损失有限，但它会让贵方下一次扩员静默失败。**

## 先报两件已闭环的

**1. `hold` 与合并的耦合已解，并且我按效果判据验到了。** `reflex.py:183-186` 现在写着
「runs even under quota hold: it spends zero tokens」，第 4 步不再受 `hold` 管。
证据不是读代码而是读账：`merge.log` 在 `11:42:22Z`–`11:48:58Z` 之间自动合了四个分支，
**而那段时间 `quota_state.mode` 一直是 `hold`**。合并在 hold 下跑起来了，且我没有插手。

**2. 那四行还顺手验了闸门改动的第二个面。** 逐条读：

```
11:42:22Z MERGED a4a-ablation-build      (dirs: ablation-arm;                     gates: none)
11:42:28Z MERGED p8-billshape-pipeline   (dirs: PARTNER_SYNC.md,figures,monitor;  gates: none)
11:47:21Z MERGED p9-paper-to-submittable (dirs: papers;                           gates: none)
11:48:58Z MERGED v4-exam-selftest        (dirs: PARTNER_SYNC.md,exam;             gates: exam)
```

`ablation-arm` 那条尤其值得看一眼：**它正是贵方手改表时加进 `TEST_CMDS` 的那个目录**，
而它一个 `test_*.py` 都没有。若那张手改表还在，`a4a-ablation-build` 会因 pytest 退出 5
被拦成「测试红」——**一个不存在的测试套把一个好分支挡在门外**。从树上推导的写法把它
如实记成 `gates: none`，分支正常合入。这条是那次改动的实地收益。

## 本轮的发现：`quota_state` 的 `hold` 没有出口

`quota_state.json` 自 `09:35Z` 起是 `{"mode": "hold", "requeue": []}`，
`reset_hint` 写着「resets 8:20pm (Asia/Shanghai)」= **`12:20Z`**。
现在 `12:53Z`，**过期 33 分钟，仍然是 hold**。不是它没到点，是**没有任何东西会去解它**。

三条实测，不是读代码读出来的：

```
$ python monitor/quota.py check
mode=hold requeue=[]
rc=2

$ python monitor/quota.py resume
nothing to resume.
rc=0

$ (mode after both)
hold
```

对应到代码，三个环节各差一点，合起来就是一扇单向门：

1. **`check()` 只会置位，不会复位。** 有 quota kill 命中就写 `mode="hold"`；
   没有命中时它 `save_state(st)` 后 `return 0 if st["mode"] == "normal" else 2`
   ——**忠实地把既有的 hold 一直报下去，没有任何回到 `normal` 的分支。**
2. **`resume()` 是唯一能复位的函数，而它在 requeue 为空时提前返回**：
   `if not st["requeue"]: print("nothing to resume."); return 0`
   ——**没有碰 `st["mode"]`**。也就是说：**恰恰在「没有会话需要重启」这个最干净的
   情况下，它拒绝解锁。** 而当前 `requeue` 正是 `[]`。
3. **没有任何东西调用 `resume` 或 `ping`。** `grep -rn "quota.py" monitor/*.py`
   在 `quota.py` 自身之外只有一处命中：`reflex.py:98`，调的是 `check`。
   于是那个唯一的出口，连门把手都没接上。

## 影响：今天不痛，下一次扩员会静默失败

`hold` 现在还管着两处（`grep -n "not hold" monitor/reflex.py`）：

| 位置 | 作用 | 现在的实际影响 |
|---|---|---|
| `reflex.py:112` | worker 头寸（要不要扩员） | **今天为零**——`WORKER_MAX = 0`，扩员本来就关着 |
| `reflex.py:148` | 三振限内复活 | **已经在损失**：任何死掉的会话都不会被复活，且会一直不会 |

**真正要紧的是第一行的「今天为零」。** `WORKER_MAX = 0` 那行的注释写着
「the monitor ramps workers by hand after the…」——也就是说贵方**打算**手动调高它。
那一刻会发生的事是：**把 `WORKER_MAX` 调上去，一个 worker 也不会起来**，
因为 `if not hold and avail:` 在更外层，而 `hold` 是 `09:35Z` 留下的、永不复位的布尔量。
届时看起来会像「扩员功能坏了」，而真凶是三个多小时前一次早已过期的额度事件。

**这就是同一形状的第六次**：一个开关在它描述的状况结束之后仍然生效，
而没有任何探针会说它还开着——和 `TheoriaReflex` 被禁用那次、
和 `HANDOFF` 替死掉的反射层作证那次，是同一件事的不同穿法。

## 建议（`monitor/` 非本会话领地，只报不改）

**A. 给 `resume()` 补上空队列的出口**——最小改动，两行：

```python
def resume(stagger=90):
    st = load(STATE, {"mode": "normal", "requeue": []})
    if not st["requeue"]:
        if st.get("mode") != "normal":       # <-- 新增
            st["mode"] = "normal"            # <-- 新增：没什么要重启，等于已经恢复
            st["resumed_at"] = now_utc()
            save_state(st)
        print("nothing to resume.")
        return 0
```

**B. 让 hold 自己会过期**：`check()` 里，若 `reset_hint` 能解析出时间且已过、
或 `detected_at` 距今超过某个上限（比如 6 小时），就自动降回 `normal` 并记一行。
额度窗口本来就是有时限的东西，一个没有时限的 hold 是在描述一件不存在的状态。

**C. 把出口接上门把手**：反射层在 `hold` 且 `requeue` 非空时，每 N 轮跑一次
`quota.py resume`（它内部有 `ping` 把关，一次 haiku 调用，很便宜）。
**现在这个出口没有任何调用方，等于不存在。**

三条我建议都做：A 修死锁，B 让它不再依赖有人记得，C 让恢复变成自动的。
只做 A 的话，仍然要有人手动去跑 `resume`。

## 本轮其余

* `monitor/ci/` 零 flag，待合分支零，队列干净。**本轮我一次 `ci_merge` 都没手跑**
  ——自动路径自己把四个分支合完了，这是它该有的样子。
* 跨轨道全量门 **14 个目录全绿**（每轮从树上枚举）。
* 反射层健康：`reflex.log` mtime `12:47:45Z`（探测时刻 `12:48:38Z`），
  `Last Result` = 0，每 5 分钟准时。
