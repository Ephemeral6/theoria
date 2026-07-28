# C11 — 负样本的变异测试：它们真的会红吗

工单原话：**「写好没调用比没写更危险，因为它看起来是有的。」**
一条永远绿的负样本测试属于同一类危险，所以它们不是「跑过就算」，而是被**变异测试**量过。

方法：改源码一行 → 只跑 `tests/test_tool_failure_is_not_truth.py` → 无论结果如何**改回原样**。
每个变异体都是「把这次修复回退掉」的一种写法，其中几种是**只回退一半**。

## [OVERTURNED] 「18 / 18 击杀，0 逃逸」不成立

> **原文保留：本文件第一版的标题是「结果：18 / 18 击杀，0 逃逸」。**
>
> 对抗复核独立做了 **36** 个变异体（含 15 个「只回退一半」），**31 杀 5 逃**。
> 逃掉的五个，全部落在我**没有**写过测试的地方：
>
> | 逃逸 | 说明 |
> |---|---|
> | **M26** 把 `probe_frontier` 的 `basis`/`budget` 整块删掉 | 目标文件 68 条全绿、全套 452 条全绿。**那处修复一条负样本也没有** |
> | **M25** `basis` 的三元 else → 常量 | **等价变异体**：`"proved-by-planner"` 分支不可达（`reach()` 不传路径 → 强制 STUB → 桩恒 `exhaustive=True`）。我的注释却说「记录了是两者中的哪一个」 |
> | **M28** 不再记录 `max_expansions` | 唯一碰该字段的测试名字叫 budget、断言的却是 `exhaustive` |
> | **M35** `check_paths` 直接 `return []` | 工单点名的 **tautological assertion**：`not findings` 在恒空时同样成立，整个扫描层没有测试 |
> | **M36** `Finding.level` 默认值改 `NOTE` | 该默认值是死代码，两个构造点都显式传参 |
>
> 复核的判词我照抄，因为它说得准：
> **「实现员的 18 个变异体恰好一一对应它写下的那几条测试……这不是『构造上必然会红』，
> 这是『测了测过的』。」**
>
> 修法见下方「第二轮」。**这里不辩护：我的 18 个变异体是我自己写的测试的镜像，
> 所以它们必然全红——那个 18/18 度量的是自洽，不是覆盖。**

## 第一轮：18 / 18 击杀（但如上，度量的是自洽）

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

## 第二轮：把复核的五个逃逸补上

| 变异（复核构造的，我重跑） | 修法 | 现在 |
|---|---|---|
| M25 `basis` 三元 → 常量 | 删掉不可达的 else，改为在下判断处 `raise UnprovenUnreachability` | **RED** |
| M26 删掉 `basis`/`budget` | 新增 `test_an_unreachable_verdict_records_what_entitles_it`（真跑 `p_side`） | **RED** |
| M26b 删掉 `exhaustive` 资格守卫 | 新增 `test_an_unexhausted_search_may_not_be_published_as_unreachable` | **RED** |
| M28 不记录 `max_expansions` | 旧测试补上真跑一次断言 `max_expansions == 12345` | **RED** |
| M35 `check_paths` 恒空 | 新增 `test_the_standing_check_actually_walks_the_tree`（种一个含裸比较的文件，断言恰好 1 处 ERROR） | **RED** |
| M36 `Finding.level` 默认值 | **删掉默认值**——死代码不该长得像保守约定 | 不再存在 |
| M37 `<unparsed>` 降级成 NOTE | 新增 `test_a_file_that_cannot_be_parsed_is_not_a_file_that_is_clean` | **RED** |
| M38 把 `runs` 放回 skip 表 | 新增 `test_the_scan_surface_does_not_quietly_exclude_our_own_code` | **RED** |
| M39 `bool()` 算作委派 | 新增 `TRANSPARENT_CALLS` + `test_wrapping_a_comparison_in_bool_is_not_delegating_it` | **RED** |
| M40 `deadlock_carver.same_answer` 去掉资格守卫 | 新增 `test_two_unfinished_searches_are_not_evidence_about_a_theorem` | **RED** |

**9 个曾经逃逸或新构造的变异体，现在全部被杀。**
两个来自复核的教训值得单写：

* **M25 那类（等价变异体）是最难看的一种绿。** 测试没漏，是分支不可达——
  代码在记录一个不可能发生的二选一。修法不是补测试，是**删掉假的记录、改成真的断言**。
* **M35 那类（掏空被断言的对象）** 说明「断言一个空列表」永远要配一条
  「这个函数在该报的时候确实会报」。四条新的扫描层测试就是这条配对。

## 复现

```bash
cd engine-rig && python -m pytest tests/test_tool_failure_is_not_truth.py -q
```

变异清单以脚本形式跑过两轮（第一轮 8 个 / 2 逃逸，第二轮 15 个 / 2 逃逸，
补完两条性质测试后第三轮 18 个 / 0 逃逸）。脚本没有落盘为文件——它只是
「改一行、跑、改回来」的循环；上表的每一行就是它的输入。
