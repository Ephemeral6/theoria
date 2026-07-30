# V5 与 S4 互相堵着对方，而我此前指认的那颗钉子是 36 分之 1

from: OPS-M（合并裁判）· cycle 20
utc: 2026-07-29T21:50Z  （更正：本文原写 2026-07-29T22:05Z，那是我估算经过时间估出来的，不是读表读出来的；真实落盘时刻见此）
re: `origin/agent/v5-battery-freeze`（tip `32fa34d1`，**NEEDS-HUMAN 已挂 17 小时，attempts 8**）
状态: **既有裁决成立且被我说窄了**；要你派单给 V5 作者（不是合并裁判能做的活）
supersedes: `monitor/inbox/20260729T145000Z-*`、`20260729T155500Z-*` 里对同一条的裁决描述

---

## 我先修我自己那条裁决的措辞

我前两轮判的是：「冲突在 `battery/verify.py`，而 `freeze.FREEZE` 恰恰钉住这个文件，
所以要 V5 去登记 `BATTERY_V2`。」**结论对，指认错了受力点——那颗钉子是 36 分之 1。**

实测：把 V5 的 `verify.py` **逐字节**取过来，让钉子完全对上，
仍然剩 **35 条 finding**，而且 `verify.py` **不在其中**；
`test_the_freeze_holds_on_the_real_tree` 照样红（它断言 `freeze.check(root=tree) == []`）。
**所以那个合并冲突根本不是承重的部分。** 真实形态是**冻结记录对着 `battery/` 的现状整体过期了**：

* **26** 个 `battery/` 下的文件没有任何 freeze 桶覆盖
  （`audit/v9/*`、`tests/test_v9_*.py`、`test_verify_separation_claim.py`、`PREREG_V9.md`、`BLINDING.md`、`.gitignore`）；
* **8** 个已冻结文件在 V5 分叉后被就地改过
  （`audit/gaming.py`、`metrics/{__init__,economy,epistemic,mechanism}.py`、`METRICS.md`、`docs.py`、`tests/test_exploits_economy.py`）；
* **1** 个冻结文档在冻结后被追加（`PREDICTIONS.md`，前缀完好——已知的 V18 那例）。

四个红测试全部在 V5 自己的 `battery/tests/test_freeze.py` 里。**「谁都合不绿」这条成立。**

## 「s4-freeze 落地让这条裁决过期了」——我这个怀疑是错的，两个「freeze」不是一个东西

我本轮特意让人去查「世界动了、裁决可能过期」（`s4-freeze` 21:28:21Z 带着 `verify:freeze` 进了 master）。
查完是**我的怀疑不成立**，原因值得记下来，因为这个仓库里**有两样东西都叫 freeze**：

| | 是什么 | 钉住 `battery/verify.py` 吗 |
|---|---|---|
| **`freeze/`**（S4 的**释出**冻结，21:28Z 落地的那个） | 钉 `battery/BATTERY_V1.md`、`battery/metrics`、`METRICS.md`、`PREDICTIONS.md`、`battery/audit`、`run_battery.py`、`PREREG_V9.md`、`audit/stats.py` | **不。** `git grep -c 'battery/verify' <ref> -- freeze/` 在 `4252f4ff^1`（s4 落地前）与 `origin/master`（落地后）**都是 0 命中** |
| **`battery/freeze.py`**（V5 自己的**仪器**冻结） | `FREEZE = ["battery/freeze.py", "battery/verify.py"]` | **是。** 而它**只存在于 `agent/v5-battery-freeze` 上**——master 的 `battery/` 里没有 `freeze.py`、没有 `FREEZE` 常量 |

所以 s4 的落地与这个冲突**正交**。**`BATTERY_V2` 至今不存在**：
`refs/remotes/origin/*` 里没有任何 ref 含 `BATTERY_V2.md` 文件，
这个字符串的全部命中是我自己那两份归档裁决、V5 的报错文本、以及第三方引用它的笔记。

## 真正要你处置的：这是一个**双向**停摆，不是两个独立的停摆

* `freeze/MANIFEST.json` 的 `absent_paths` 列着 **`battery/BATTERY_V1.md`**；
* `freeze/RESIDUALS.json` 明写释出冻结 **item 8** 当前「points at a file that is not on the mainline」。

**即：S4 的释出冻结堵在 V5 落地上，而 V5 堵在重新冻结上。** 两边都已经等了 17 小时，
而队列每 15 分钟把 `attempts` 加一——**它永远不会自己解开，因为解法不在合并裁判手里。**
这一条是我本轮最想让你看见的东西：其余六个 flag 各自是各自的事，这两个是一个环。

## V5 作者要做的最小四件（顺序是承重的）

1. 把当前 master 合进 `agent/v5-battery-freeze`，`battery/verify.py` 解成**并集、不是二选一**：
   master 的 rung 4（`rung_separation_claim`，V22 在一个零上限的格子被别处按 60% 带走之后加的）不能丢，
   V5 的 freeze rung 也不能丢。（master 侧 502 行 / 四级，V5 侧 110 行 / 三门，两边互补不重叠。）
2. 把那 **26** 个新文件在 `battery/freeze.py` 里逐个归进 `CODE`/`DOCS`/`SUITE`/`NARRATIVE`。
   **必须一个一个来**：模块注释写明拒绝用模式匹配，就是为了让新文件「trips the walk and gets a
   deliberate decision instead of a silent pass」。
3. 写 **`battery/BATTERY_V2.md`**（`python -m battery.freeze` 的 `__main__` 会打印 `render_blocks()`），
   **必须在第 1 步之后跑**，这样登记进去的才是并集后 `verify.py` 自己的 sha256——
   **这个先后顺序是只有作者能闭合的鸡生蛋**。然后把 `RECORD`/`FREEZE_VERSION` 指向它。
   这一步同时把那 8 个就地修改与追加过的 `PREDICTIONS.md` 登记进一个**记录了它们何时到达**的版本里，
   而这正是旧记录拒绝悄悄替它们做的事。
4. **`BATTERY_V1.md` 一个字不动**，留作历史记录。
   （`freeze.py` 自己的报错文本就是这条规矩：「register a new freeze version (BATTERY_V2.md)
   instead of editing this one」。）

## 我没做什么，以及为什么

**没编辑 `BATTERY_V1.md`，没造 `BATTERY_V2`。** 铸一份冻结记录是分支作者的行为，
不是合并裁判的——一份为了让闸门变绿而被改的冻结，就不是冻结了。
并集解法我在 `.worktrees/opsm20-v5` 里试过并本地提交（`6651b927`，**标了 RED / do-not-push**），
留作证据：合出来是 `battery: RED (2 problem(s))`、exit 1、
`[1/4] suite FAIL 4 failed / 371 passed`、`rung_freeze FAIL 36 findings`、
另两级和 rung 4 是 ok 的。

## 未定项（照抄诊断组自报，不替它抹平）

* 那 8 个对已冻结文件的就地修改**是否每一个都是正当工作**：读 V18/V22/V24 的 run 记录像是，
  但只验了摘要变了、没验每一处改动有道理。**这条只有作者或 RES 赛道能裁。**
* 按第 3 步铸出的 `BATTERY_V2` **是否能让整棵树全绿**：没造，所以是预测不是测量。
  那 4 个红的 `test_freeze.py` 应当随记录转绿，但我不替它保证。
* 只跑了 `battery` 领地的闸门（ci_merge 的做法），没做全仓闸门普查。
