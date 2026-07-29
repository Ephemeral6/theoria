# E16 已交付，但工单本身有三处要更正（其中一处削弱它的「好消息」）

工人 W-1650，分支 `agent/e16-verdict-must-gate`。两处修复与第三项措辞工作都做完了，
测试 492 passed / 27 skipped / 0 failed，run-local verify 29/29。
细节在 `engine-rig/runs/20260729T020000Z-E16-verdict-must-gate/`。这里只写**工单说错的地方**。

## 一、行号已漂，照抄会指到别处

* `"admissible": True` 在 `engines/lp_potential/potential.py:296`，**不是 :255**。
* deadlock_carver 的 carve→report→emit：**发布点**在 `candidates()`（原 161-202），
  `run()` 里的调用链在 212-216。工单写的 `:168-180` 两头都不是。

不影响判断，但 RES-3 的原始条目和 E16 都带着这组行号，下游谁再引用就再错一次。

## 二、「六处」在 RES-3 里其实只有三处——是张空头支票

`monitor/inbox/archive/20260729T104500Z-RES-3-the-dual-exists-and-it-has-a-different-shape.md`
第 75-84 行，标题写「六处」，底下列了 **三条**，并说「报告里分开列了」——
而那份 `SURVEY-success-as-truth.md` 在
`engine-rig/runs/20260729T000000Z-E11-engine-crosscheck-deep/` 里**不存在**。

我把缺的三处独立找了出来，六处已在 `DECISIONS.md` D-035 成表，每行点名**共享的前提**：

| 站点 | 校验器没 import | 但共享 |
|---|---|---|
| `lp_potential` `check_exactly` | LP | `Certificate.moves` |
| `ic3_pdr` `check.py` | `pdr` | `System.transitions` |
| `interop/certificate_export.verify` | — | 生产者自己列的 witness |
| `zero_space` `verify()` | 消元 | 拟合所用的同一条轨迹 |
| `deadlock_carver` 裁判 + `same_answer` | carver 的证明 | `ground_actions`/`strip_static` |
| `fd_adapter` `validate_plan` | `search` | `ground_actions` |

**建议**：RES-3 那条「六处」的账应记为已结清，但结清方式是**补齐**而不是核对——
原报告承诺的清单从未落盘。这类「细节见另一份报告」的引用值得当作一种独立的缺陷形状。

## 三、工单开头的好消息，有一半要收回

E16 写：「`validate.py` **刻意不 import `search`**——验证器不认识搜索器，
这是结构保证，不是承诺。」

**无条件调用那一半是真的，我验了**：`fd_adapter/__init__.py:140` 确实无条件调
`validate_plan()`，三档全过含真 FD。「求解器返回计划就认定可解」在本仓库确实没发生。

**「结构保证」那一半弱一个函数。** `validate.py` 与 `search.py` 共享
`pddl.ground_actions`——而 `ground_actions`（`pddl.py:304`）**不是 parser**：
它在实例化时做静态前条件过滤，决定哪些实例「有可能触发」，就是后继生成层。
所以：搜索器的 frontier / 排序 / 去重出错，验证器抓得住；**grounder 里少一条
delete effect，两边同时错、同时看不见**。更刺的是 `validate.py` 原 docstring 举的
例子正是「a forgotten delete effect, say」——它举的例子正好是它抓不住的那一类。

原 docstring 那句 `The only code shared with the planner is the parser` **是假的**，
已改。E16 引用它作为对偶普查的正面结论，**这个正面结论要按上面的边界重述**，
否则 WP1/WP9 里会出现一句比代码强的话。

## 边界

零 API、零网络、封存堆零接触、$0.00。只动 `engine-rig/`。
`cold-start-a0/` 的两条同族**没动手**，按工单只在 PARTNER_SYNC 登记。
另有一封磁盘满的急件：`20260729T020500Z-W-1650-disk-full-blocks-every-worker.md`。
