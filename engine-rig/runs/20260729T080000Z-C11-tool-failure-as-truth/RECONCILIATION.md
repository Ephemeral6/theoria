# C11 — 对账：已发布的 `fd_unsolvable: true` 在新判据下还成不成立

工单要求：`p13_fd_dividend` 那几行已发布的 `fd_unsolvable: true`，在
`backends.proves_unsolvable` 下重新裁一次。**两种结果都要接受。**

**结论：没翻。结论未变、方法已修。**
下面把这句话能站住的部分和站不住的部分分开写。

---

## 一、被对账的到底是几行

工单说「那三行」。**实际是五处主张，分在两张表里**，而这本身是一个发现：

| 产物位置 | 实例 | 存了什么 |
|---|---|---|
| `runs/p13-fd-real/dividend.json` → `cross_check[1]` | `a0-spike/mismatch` | `fd_exit_code: 12`, `fd_expansions: 0`, `fd_unsolvable: true`, `agree: true` |
| 同上 `cross_check[3]` | `cold-start-a0/no-button` | 同上 |
| 同上 `cross_check[5]` | `cold-start-a2/holed` | 同上 |
| 同上 → `deadlock_dividend[2]` | `ringstuck`（before） | `fd_unsolvable_before: true`, `fd_expansions_before: 0`，**没有退出码** |
| 同上 | `ringstuck`（after） | `fd_unsolvable_after: true`, `fd_expansions_after: 0`，**没有退出码** |

**`deadlock_dividend` 的行根本不记 FD 退出码**，所以那两处主张连「它当时读到了几」
都无从查起。这一条我在订正里补了（新增 `fd_exit_code_before` / `fd_exit_code_after`），
但**对已发布的这两行无能为力**。

---

## 二、新判据要求什么

```python
def proves_unsolvable(tier, returncode, log):
    if returncode in (10, 11):          # 翻译器 / 结构性判定
        return True
    if returncode != 12:
        return False
    return tier == FD_OPTIMAL and FD_EXHAUSTED in log
```

`FD_EXHAUSTED = "Completely explored state space"`。
对这五行，档位没有疑问：`run_fd` 全仓只用 `BLIND = "astar(blind())"` 调用
（`deadlock_dividend` 与 `cross_check` 各两处），这是完备、可采纳、无代价上界的配置，
按 `backends.py` 自己的规则就是 `FD_OPTIMAL`。
**所以整个对账压在一件事上：那几次运行的日志里有没有那句话。**

---

## 三、能查到什么，查不到什么

### 查不到的（必须先说）

**`dividend.json` 不存日志。** 原代码把 `log` 读进内存、正则抠出
`Expanded` 与 `Plan length` 之后就丢掉，`FdRun.as_json()` 只发五个字段。
所以**新判据无法在产物上重算**，只能从旁证推断。这是这次对账的硬边界，
也是我给 `FdRun` 新增 `exhausted_reported` 字段的直接原因——
**下一次同样的问题应该是重算，不是推断。**

`.toolchain/` 是 gitignore 的，本机没有 FD 构建（`ls .toolchain` 不存在，
`$FAST_DOWNWARD` 为空），所以也不能重跑。

### 能查到的三条旁证

**(1) 五行全部 `fd_expansions: 0`。**
这个数只可能来自正则 `Expanded (\d+) state\(s\)\.` 命中——也就是说
搜索**正常打印了统计块并退出**，不是崩在半路。崩溃的 FD 不打印那一行，
`expansions` 会是 `None`。

**(2) 同一构建、同一档位的 43 份真实 FD 日志，exit 12 与那句话 100% 同现。**
`runs/20260728T072633Z-E2-fd-ladder-bench/logs/` 有 155 份保留的 FD 日志。我重数了：

| `search exit code` | 份数 | 含 `Completely explored state space` |
|---|---|---|
| 0 | 104 | 0 |
| 12 | **43** | **43 / 43** |
| 34 | 8 | 0 |

**exit 12 且不含那句话的：0 份。**
而且 `ringstuck4.fd-optimal-blind.base.log` 与 p13 的 `ringstuck` 行**是同一个实例、
同一个档位、同一个搜索配置**，其日志形状逐行对得上：

```
No relaxed solution! Generating unsolvable task...
translate exit code: 0
[t=0.001713s] Completely explored state space -- no solution!
[t=0.001720s] Expanded 0 state(s).
Search stopped without finding a solution.
search exit code: 12
```

`Expanded 0` 与那句话在同一次运行里同时出现。这是 `deadlock_dividend` 那两行
（`expansions 0` + `unsolvable true`）能拿到的最接近直接的证据。

**(3) 桩在三行 `cross_check` 上独立同意。**
`stub_unsolvable: true`，`stub_expansions` 分别是 315 / 23 / 41——非零，说明
桩真的搜了并且清空了队列（`fd_adapter/search.py:146` 预算超限**抛异常**，
所以返回的 `plan=None` 只可能是穷尽）。这是一个不共享代码路径的第二意见。

### 那 43 份日志里还有一件要说的

43 份 exit-12 日志中有一部分是 **`fd-satisficing` 档**的（`ringstuck*.fd-satisficing.*.log`），
它们**同样含**那句话。`proves_unsolvable` 对这些**照样拒绝**。
也就是说：新判据在这批实测数据上**确实会拒绝一些「日志说已穷尽」的运行**，
它不是一个恒真的谓词。这一点让「三行没翻」这个结论更有分量，而不是更少——
因为它证明这把尺子有拒绝能力，只是没落在这三行上。

---

## 四、结论

**五处 `unsolvable: true` 在新判据下都仍然成立，我判它成立的置信度是「强旁证」而不是「重算」。**

* 档位：确定（`BLIND`，唯一调用路径）。
* 退出码：三行确定为 12（产物里有），两行未记录（`deadlock_dividend` 不存）。
* 穷尽标记：**五行都没有直接证据**，靠同构建 43/43 的日志与同实例的逐行对齐推断。

**这不是「抓到了什么」。** 方法此前不健全——一次换档、一次 `--alias lama-first`、
一次 OOM 退出 22，那段代码读不出区别，而 `same_answer` 那道守门会照样放行——
但**结论没有错**。按工单的要求原样记下：**结论未变，方法已修。**

修完之后再跑一次 p13 会得到什么不同：`dividend.json` 多出
`rung` / `answered` / `exhausted_reported` / `fd_exit_code_before` /
`fd_exit_code_after` 五个字段，`same_answer` 与 `agree` 从两值变三值。
届时同样的对账是**重算**，不是这份文件里的推断。
