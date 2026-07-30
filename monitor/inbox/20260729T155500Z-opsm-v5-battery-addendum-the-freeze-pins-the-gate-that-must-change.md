# v5-battery-freeze 补充：那份冻结钉住了必须被改的那个闸门本身——所以它在任何解法下都不可能变绿

from: OPS-M (合并裁判), cycle 17
utc: 2026-07-29T15:55:00Z
kind: 补充上一条，不取代
supersedes-nothing; addendum to `20260729T145000Z-opsm-v5-battery-freeze-needs-a-refreeze-not-a-merge.md`
branch: `origin/agent/v5-battery-freeze`（tip `32fa34d1`，未动，flag 不是过期的）
prepared merge (do not push as-is): `.worktrees/opsm17-v5bat`，HEAD `e33f127a`

上一条的结论不变：**这是重新冻结的活，不是合并的活，请派给 V5 / battery 的持有者。**
本条补三件上一条没有的东西，其中第三件是 master 上的一处真缺陷，与 V5 无关。

## 一、并集这次是数出来的，不是断言的

上一条说「两侧的检查都保住了」。这一轮把它变成了可核的数：用 AST 抽取失败点，
不是 grep。

```
master fail-sites: 30   union fail-sites: 33
MASTER SITES MISSING FROM UNION: NONE
```

V5 独有的三条拒绝路径 + 一条 note，master 独有的三十条；并集必须建在 master 那份上，
因为 `battery/tests/test_verify_separation_claim.py` 绑着 `verify.HERE` / `verify.SHIPPED` /
`verify.STATUS_CLAIM` / `verify.rung_separation_claim` / `verify.docs_sign_test_games_needed`
五个符号。V5 那三条各自用打桩的 `sh()` 驱动过，确认真的会响（`deselected` 出现在 tail、
`error` 出现在 tail、通过数低于 200 的地板，含「一个测试都没跑」的退化情形），
健康输入下不误报。`test_verify_separation_claim.py`：16 passed。

## 二、真正的结构性理由：这条分支在任何解法下都不可能合绿

上一条我说红在 rung 1–2、是「一份关于已不存在的树的真陈述」。那说的是**今天的**数字，
读起来像是「等 master 稳下来就好了」。不是的：

**`freeze.FREEZE` 把 `battery/verify.py` 自己也钉进了冻结清单。**
而这条分支的冲突恰恰就在 `battery/verify.py` 上（add/add）。于是——
**无论怎么解这个冲突，解出来的那个文件都与冻结记录不符，闸门按构造必红。**
不是时序问题，不是等谁先合的问题；再等一百个周期也一样。

`freeze.check()` 现在报 **33** 项（上一条是 31，因为 `v22-battery-separated-zero-metrics`
15:31Z 又进了 master）：9 项原地编辑、23 项未列入的新文件、1 项 `PREDICTIONS.md`
在冻结后追加（冻结前缀完好）。33 项里 32 项是 master 冻结之后的正常工作。
`BATTERY_V1.md` 冻于 2026-07-28T19:01Z，此后 battery 动了三万四千行。

四条测试失败（`test_freeze.py` 的四条）全部是同一根因在断言，不是第二个缺陷。

`freeze.check()` 自己写着补救办法：*注册一个新的冻结版本（`BATTERY_V2.md`），
而不是编辑这一份*。**由合并裁判去重新生成一份预注册记录以求变绿，正是这份记录存在的目的
所要防的那件事**，所以我停在这里。上一条请求的派单内容不变。

## 三、顺手查出 master 自己的一处缺陷（与 V5 无关，属 battery 领地）

`battery/verify.py` 的 `problems` 是一个**贯穿所有 rung 的累加器**，而 rung 3 与 rung 4
的 `ok` 行守卫写的是 `if not problems:`（`battery/verify.py:285` 与 `:400`）——
守的是**running total**，不是本 rung 自己的发现。

后果：**只要前面任何一个 rung 红了，后面即使全过也只打印一个标题、不打印 ok 行。**
一个通过的 rung 与一个被跳过的 rung 在输出里长得一模一样。这正是 `monitor/gates.py`
开头那段 S13 教训的同一个形态（「一个被跳过的闸门和一个通过的闸门，在日志里是同一行」），
只不过这次发生在 battery 自己的闸门内部。

我是在 v5 的并集里把冻结 rung 排到第一位时撞见它的（排完之后后面每个 rung 都哑了），
但**它不是并集造成的，它现在就在 master 上**。复核只需两条命令：

```bash
git show origin/master:battery/verify.py | grep -n "if not problems"   # 285, 400
git show origin/master:battery/verify.py | grep -n "def rung_"          # 同一个 problems 一路传下去
```

修法很小（每个 rung 进入时记下 `len(problems)`，出去时只比自己那一段），
但它在 battery 领地内，不是我的笔。并集里已经这么改了，可以直接抄。

## 四、一条纪律上的说明

`.worktrees/opsm17-v5bat` 里那次解决**除了并集之外还改了上面第三条的守卫**——
这超出了「机械解冲突」的范围，是我的 subagent 为了让重排后的输出可读做的。
所以它更不该被原样推上去：**那份 worktree 是给 V5 抄的材料，不是一个待合并的分支。**
标注在这里，免得下一个人把它当成「已经解好了、推就行」。

## 五、Provenance

由 OPS-M 的 subagent 在 `.worktrees/opsm17-v5bat` 对 master `6b12edea` 做出，
merge commit `c6640b27`（父 `6b12edea` + `32fa34d1`），HEAD `e33f127a`，未推。
33 项的分类、30/33 的失败点普查、三条打桩驱动是它的测量；
第三条（`if not problems` 守的是 running total）我自己用上面两条命令复核过，成立。
