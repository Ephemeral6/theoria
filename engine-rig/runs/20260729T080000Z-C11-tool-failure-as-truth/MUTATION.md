# C11 — 负样本的变异测试：它们真的会红吗

工单原话：**「写好没调用比没写更危险，因为它看起来是有的。」**
一条永远绿的负样本测试属于同一类危险，所以它们不是「跑过就算」，而是被**变异测试**量过。

方法：改源码一行 → 只跑 `tests/test_tool_failure_is_not_truth.py` → 无论结果如何**改回原样**。
每个变异体都是「把这次修复回退掉」的一种写法，其中几种是**只回退一半**。

## 结果：18 / 18 击杀，0 逃逸

| # | 变异（把源码改成这样） | 文件 | 结果 |
|---|---|---|---|
| 1 | `unsolvable=done.returncode == 12` | `tools/p13_fd_dividend.py` | **RED** |
| 2 | `rung = backends.FD_OPTIMAL`（永远最优档，丢掉保守默认） | 同上 | **RED** |
| 3 | `same_answer` 去掉 `answered` 守卫 | 同上 | **RED** |
| 4 | `backends_agree` 去掉 `answered` 守卫 | 同上 | **RED** |
| 5 | `answered` 恒 `True` | 同上 | **RED** |
| 6 | `render` 把未知 `same_answer` 印成 `yes` | 同上 | **RED** |
| 7 | `potential_nonincreasing = not raising`（读截断列表） | `recheck/verify.py` | **RED** |
| 8 | `goal_break = not goal_bad`（potential 分支） | 同上 | **RED** |
| 9 | `inv_closed = not closed_bad` | 同上 | **RED** |
| 10 | `goal_break = not goal_bad`（invariant 分支） | 同上 | **RED** |
| 11 | `region_closed = not closed_bad` | 同上 | **RED** |
| 12 | `goal_break = not goal_bad`（region 分支） | 同上 | **RED** |
| 13 | 求解器任何停机都折回 `None` | `engines/lp_potential/potential.py` | **RED** |
| 14 | 截断不记录（`truncated.append(cell)` → `pass`） | `engines/zero_space/zerospace.py` | **RED** |
| 15 | IMPOSSIBLE 的配对照常计费 | `engines/mdl_segmenter/segmenter.py` | **RED** |
| 16 | `exhaustive: bool = True`（占位对象继承穷尽性主张） | `engines/fd_adapter/search.py` | **RED** |
| 17 | 标定检查的谓词豁免恒真（`_adjudicated` → `True`） | `tools/check_solver_status.py` | **RED** |
| 18 | 断言词表清空（检查变成永远绿） | 同上 | **RED** |

## 两次逃逸，和它们改变了什么

**第一版负样本逃了两个**，两次都不是「多写一条断言」能补的，都逼出了源码结构的改动：

1. **`same_answer` / `agree` 逃逸。** 第一版测试是手搭一个 report 字典再喂给 `render()`，
   所以只测了渲染，**没有测组合逻辑本身**——组合逻辑长在 `deadlock_dividend()` /
   `cross_check()` 里，而那两个函数要真的 FD 才跑得起来。
   修法：把两条判据抽成 `same_answer(before, after)` 与
   `backends_agree(stub_unsolvable, stub_length, fd)` 两个纯函数，调用点改走它们。
   **现在没有装 FD 的机器也能测到那条判据。**

2. **`inv_closed` / `region_closed` / `goal_break` 逃逸。** 我手写的证书夹具只覆盖
   `potential_bound` 一种，另外两种证书的分支没人走。
   修法：加一条**在整个伪造品目录上参数化**的性质测试——
   *展示预算不得改变任何判定*（`recheck.forgeries.CATALOGUE`，每个伪造品在
   `max_witnesses=6` 与 `max_witnesses=0` 下 `conditions` 必须逐字段相等）。
   目录里本来就有 `claims-everything`（打破 invariant 分支的 `goal_break`）与
   `region-that-leaks`（打破 `region_closed`），所以这条性质**构造上**覆盖了我夹具漏掉的分支。

这两条是这次变异测试真正的产出：**不是「测试通过了」，是「测试原本测不到，现在测得到了」。**

## 反向控制：测试不能靠「一律说不」通过

一个只会拒绝的谓词能让上面所有变异体全红，同时把引擎废掉。所以文件里同时有正向断言：

* `test_exit_12_with_the_exhaustion_line_on_the_optimal_rung_is_a_proof` ——
  最优档 + 日志说已穷尽 → `unsolvable is True`、`answered is True`；
* `same_answer(solved, solved) is True`、`same_answer(solved, longer) is False`；
* `backends_agree(True, None, proved) is True`、`backends_agree(True, None, solved) is False`；
* `solve_certificate` 在 HiGHS status 2（真不可行）上仍然返回 `None`；
* `test_the_standing_check_accepts_the_fix` —— 把比较交给谓词之后检查必须闭嘴，
  否则唯一的绿路就是不再提问。

变异体 18（清空断言词表）之所以能被杀，正是因为
`test_the_standing_check_catches_the_defect_it_was_written_for` 要求它对修复前那一行
仍然报 ERROR。

## 复现

```bash
cd engine-rig && python -m pytest tests/test_tool_failure_is_not_truth.py -q
```

变异清单以脚本形式跑过两轮（第一轮 8 个 / 2 逃逸，第二轮 15 个 / 2 逃逸，
补完两条性质测试后第三轮 18 个 / 0 逃逸）。脚本没有落盘为文件——它只是
「改一行、跑、改回来」的循环；上表的每一行就是它的输入。
