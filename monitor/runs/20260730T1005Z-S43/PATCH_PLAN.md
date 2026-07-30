# S43 patch plan — restoring the guards 873d62ee deleted

作者：RES-4　时间：2026-07-30T10:05Z　状态：**计划，尚未动手**
条目 S43 此刻仍被 S41 领地占用挡着（monitor 领地在我自己手上），
所以本文件先落盘、后认领——**只存在于上下文里的信息视同不存在**。

## 我亲自复核过的事实（不是从 subagent 那里照抄的）

```
git rev-list --first-parent origin/master | grep -c 873d62ee   -> 1
git log -1 --format=%P 873d62ee                                -> cd048b32（单亲，非 merge）
git show --name-only 873d62ee                                  -> 只有 monitor/reflex.py
git show 1585dd04^:monitor/reflex.py | grep -c SUPPLY-UNKNOWN  -> 0
git show 1585dd04 :monitor/reflex.py | grep -c SUPPLY-UNKNOWN  -> 1
git show 873d62ee^:monitor/reflex.py | grep -c SUPPLY-UNKNOWN  -> 1
git show 873d62ee :monitor/reflex.py | grep -c SUPPLY-UNKNOWN  -> 0
git rev-list --count 873d62ee..origin/master                   -> 72
```

`origin/master:monitor/reflex.py` 上直接看到的（我自己 sed 出来的，见下）：

* `:312` `remote = run(["git","branch","-r",...]).stdout.lower()` —— **没有任何返回码检查**，
  `:315-343` 的复活循环无条件执行，没有 `else`，没有提前返回。
* 全文件 `grep -n TimeoutExpired` —— **零命中**；`:361` 是裸的
  `run([... "scan.py"], timeout=600)`。
* `:357-358` `except Exception: pass`。

## 拓扑更正（我先前在总线上说的略有出入，以此为准）

`873d62ee^` 是 `cd048b32`（它本身是一个 merge），而
`873d62ee^:monitor/reflex.py` 与 `1585dd04:monitor/reflex.py` **逐字节相同**。
873d62ee 是在 `c8061d7b` 落地之前从 1585dd04 分出去的：

```
1585dd04（装上守卫）
   |\
   | \--- c8061d7b  "four checks that could not go red"  把 merge_events() 抽成函数
   |
   \----- cd048b32 ... 873d62ee  "threshold was a total"  就地删掉守卫
                 \    /
                  7c1dd89b  （merge；最后一个动 reflex.py 的提交）
```

合并 `7c1dd89b` 的取舍是「873d62ee 的删除 + c8061d7b 的函数抽取」。
所以**当前文件是个混血**：四个 EXIT 守卫里活下来一个，纯粹因为它在另一条
分支上被搬进了函数、而合并保留了那个函数；其余三个是就地的，死了。

这条更正对结论没有影响（守卫确实是 873d62ee 删的），但它解释了
**为什么 `merge:EXIT-` 还在**，避免下一个人以为守卫是被部分保留的。

## 判定：四个守卫，不是三个

| 守卫 | 判定 | 当前位置 |
|---|---|---|
| `merge:EXIT-` | **仍在，行为完好** | `merge_events()` :87-114，:347 调用 |
| `sweep:EXIT-` | **完全缺失** | `sw` 在 :160 绑定，`sw.returncode` 全文件从未被读 |
| `reap:EXIT-` | **完全缺失，且是不可恢复的形状** | :208-211 直接取 `.stdout` |
| `revive:GIT-EXIT-(loop-skipped)` | **完全缺失，不可恢复形状** | :312-313 |
| **S30 scan 守卫（第四个，没人问起）** | **完全缺失，且无任何测试** | :360-361 裸 run |

**关键区分**：这些不是「测试断言了过时的字符串、行为还在」。
我为最要命的两条各自去 master 上看了源码，行为确实没了：
`run()` 的状态对象在被读之前就被 `.stdout` 丢掉了，全文件 `returncode` 只出现在
`q.returncode`(quota) / `probe.returncode` / `st.returncode`(schtasks) / `merge_events` 内的 `r.returncode`。

## 两处现在就在造成损失

1. **复活循环会花钱**。git 失败时 `remote == ""`，于是每个
   `"agent/%s" % slug in remote` 都是 False，于是**每一个死会话都读作「未投递」**，
   于是对每一个都调 `dispatch.py --only`。这正是那条测试 docstring 描述的场景，
   而它现在是 master 上的活行为。
2. **scan 超时会静默弄死整个 tick**。没有 `except TimeoutExpired`，600 秒超时
   直接从 `main()` 抛出去，`finally` 把锁丢掉，**一行 `rlog` 都不写**。
   这比 S30 加守卫之前**更差**。`monitor/tests/test_scan_failure_exit.py` 里
   那句「reflex reads this」的注释现在是假的。

## 同一次提交里被删掉的、以及必须不碰的

873d62ee **修的是真 bug，不许 revert**：`MIN_FREE_GB = 8` 原本是个**总内存**阈值，
是在一次崩溃之后拍的，而那次崩溃的真因是**并发**（约 20 个会话同时在跑）。
`standing.py` 2026-07-29 已经改成 headroom + 每会话成本，reflex 没跟上，
于是补员闸门再也没开过——`reflex.log` 上是一长串
`worker-hold:low-memory(7.5GB) / (7.3GB) / (6.7GB)`，舰队靠手工补人。
现在这个修复住在 `:36-43`（常数与中文理由注释）和唯一消费者 `:290`。

873d62ee 还捎带了**第二个**没人提过的修复：仪表盘服务重启（:181-206），
`cmd /c start` 换成直接 `http.server` Popen，加了真的端口探测，
于是 `serve:restarted` 不再在失败时被写出来。**同样不许碰。**

**而这两个修复都没有任何测试。** 全仓 `*.py` 里
`HEADROOM_GB|PER_SESSION_GB|MIN_FREE_GB` 只命中 `monitor/reflex.py`、
`monitor/standing.py`，以及 `arc-recon/runs/.../concurrency_invariants.py`
这个无关的草稿（它还硬编码着过时的 `MIN_FREE_GB: 8.0`）。
`monitor/tests/` 下**零个**测试提到这三个常数中的任何一个。

**这是一模一样的敞口，只是晚了一轮**，而且更糟：没有任何东西把两个文件钉在一起，
下次 `standing.py` 的数字一动，reflex 又会静默分叉，唯一症状是舰队悄悄不再招人。

## 六处编辑，全部在 monitor/reflex.py 内

* **A — sweep 返回码**：插在 :163 之后、:164 的注释之前。`if sw.returncode != 0: events.append("sweep:EXIT-%d" % sw.returncode)`
* **B — reap 返回码**：整体替换 :208-211，把 `out` 改绑为 `reap`。
  **顺带消掉一个潜伏的变量遮蔽**：`out` 在 :283 被 powershell 读内存复用了。
* **C — git 守卫 + 重新缩进**：:312 换成 `_remote` / `if returncode != 0` / `else:`，
  并把 :314-343 整体右移四格进 `else`。**唯一有真实缩进风险的一处。**
* **D — SUPPLY-UNKNOWN**：替换 :357-358 的 `except Exception: pass`。
* **E — scan 守卫**（推荐，非测试强制）：替换 :360-361，补 `try/except TimeoutExpired/except Exception`。
* **F — 板面查询的第三个值**（可选，同族）：:258-259 恢复 `BOARD-QUERY-FAILED:%s(refill-skipped)`。

**与阈值修复的交互：没有。** A-F 距 :290 都至少 10 行，且都不读写
`free_gb` / `MIN_FREE_GB` / `HEADROOM_GB` / `PER_SESSION_GB`。
F 最近（:258，同属 `# 0b.` 步），但只碰板面查询的 `except` 臂。
**不要顺手「整理」:256 的那个 try。**

## 五个坑

1. **C 的重新缩进是唯一的真危险**。30 行右移四格，块内有 `continue`，
   其语义系于 `for` 而非新的 `else`——安全，但若把
   `if revived or deaths != ...: save_loop(state)` 误缩进到 `for` 内部，
   就会每轮迭代都写一次 `loop_state.json`。
   **解法：整段照抄 `git show 1585dd04:monitor/reflex.py` 的对应区域，不要手工缩进。**
2. **`merge_events` 必须保持是函数**。不要「恢复」1585dd04 的 ci_merge 块——
   那一版是就地的，会让 `startswith("MERGED")` 重新内联，
   `test_the_ci_merge_step_is_not_reimplemented_anywhere` 的三条断言全挂。
   `merge:EXIT-` 已经由函数满足。**:344-347 原样不动。
   这是唯一一处 1585dd04 比 master 更旧、绝不能抄回去的地方。**
3. **`import socket` 已移到模块作用域**（873d62ee, :19）。不要把局部 import 抄回来。
4. **D 的 400 字符窗口很紧**。`test_supply_unknown_is_distinct_from_supply_low_zero`
   往后扫 400 字符并拒绝末 80 字符内出现 `pass`。只做 D 的话，窗口末端离
   `finally` 里的 `except OSError: pass` 只差约 10 个字符——过，但几乎没有余量。
   **同时做 E 会把那个 `pass` 推得远远的，所以 E 是更安全的顺序。**
   若放弃 E，必须重新对着窗口验一遍，不能想当然。
5. **cp936**：这些编辑打印的字符串全是 ASCII，无风险。唯一例外是 E 的事件串，
   1585dd04 里是中文加一个 U+2014 em dash。它能被 GBK 编码（A1AA）且当初就发出去过，
   `rlog` 也是 `encoding="utf-8"` 写的——但**把 em dash 换成 `--`，零成本消掉最后一点不可移植性**。
   任何箭头、方框字符、emoji 一律不许进。

## 绝对不许做的一件事

**不许 `git revert 873d62ee`，也不许 `git checkout 1585dd04 -- monitor/reflex.py`。**
后者一条命令就能让三个测试全绿，同时**静默地重新弄坏阈值修复和服务重启修复**——
那就是反方向地把这次事故再演一遍。编辑必须是外科式的。

## 验收里必须写进去的一句

**三个红测试是对源码字符串的 grep，不是行为检查**，测试文件自己也诚实地说了
（`test_the_ci_merge_step_is_not_reimplemented_anywhere` 的 docstring：
端到端跑 `reflex.main()` 才是真的行为测试，而它被**故意拒绝**，
因为那个 tick 会拉起付费会话）。所以**它们变绿不构成证明**：
一个行为错误的改写照样能让它们绿。交付时必须把这句写进 RUN_STATE，
不能让未来的读者把绿当成证据。

## 顺带要补的测试（不补的话，下一轮轮到它被静默删掉）

```python
def test_the_two_refill_gates_agree_on_the_same_number():
    """standing.py 与 reflex.py 都在判断「还放得下一个会话吗」。
    它们不一致的那一夜，reflex 的闸门一次都没开过，舰队靠手工补人（873d62ee）。"""
    assert reflex.HEADROOM_GB == standing.HEADROOM_GB
    assert reflex.PER_SESSION_GB == standing.PER_SESSION_GB
    assert reflex.MIN_FREE_GB == standing.HEADROOM_GB + standing.PER_SESSION_GB
    # 阴性对照：闸门在一台正常机器上必须够得着。
    assert reflex.MIN_FREE_GB < 8, (
        "阈值又回到那个从来没让任何一次 spawn 过去的总内存数字了")
```

## 第二半：为什么 72 个提交没被拦住（已查清，见 FINDINGS）

一句话：**ci_merge 只审候选分支，master 是可信基线、从不被审**，
而 873d62ee 是直接提交到 master 的。闸门本身是好的，它 15 分钟后就红了，
但 `ci_merge.py:546` 把旗标写在**分支**名下，于是五条无辜分支被扣成 NEEDS-HUMAN。
最便宜的出口：在 `ci_merge.py:545-563` 判分支有罪之前，先把工作树重置到
`origin/master` 重跑同一条 gate row，也红就记 `MASTER RED in <dir>`。
绿路径零成本，红路径多跑一次。
