"""Append S46's amendment to PREREG_E2L.md, in that document's own protocol.

`PREREG_E2L.md` has no 修订 section; `PREREG_V9.md` §0 defines the protocol it
inherits -- **只许追加 `## 修订` 段，不许原地改** -- and that file's 修订 1 is
the precedent for exactly this shape: a rule tightened after the numbers were
seen, R1-safe in direction, procedurally irregular, and recorded as such.

Run once.  Refuses to append twice.
"""
import io
import os

HERE = os.path.dirname(os.path.abspath(__file__))
DOC = os.path.abspath(os.path.join(HERE, "..", "..", "PREREG_E2L.md"))

MARK = "### 修订 1（2026-08-02，S46）"

BODY = """

---

## 修订

本文件 §1 写着「写死，之后不得改」，§2 的五道闸同理。以下这一条是**在看到
全部数值之后**发生的，因此按 `PREREG_V9.md` §0 的修订协议追加在这里，而不是
回去改上面的正文。`PREREG_V9.md` 的修订 1 是同型先例，连它的自我评价一起适用：
方向上把规则改**严**了（`PREREG_V9.md` R1 只降不升的安全方向），程序上仍然
是一次失守，因为本文件 §0 钉的是
`git merge-base --is-ancestor <本文件的 commit> <出数的 commit>`，
而一条修订必然是出数那个 commit 的**后代**——本文件自己的仪器会说它没有祖先。
写下来是为了让它是一次可查的失守，而不是一次看不见的编辑。

### 修订 1（2026-08-02，S46）· 新增 G6：曲线不认账，它的零就不是零

**起因**：工单 `S46-turn-costs-mixes-two-axes`（`freeze` 经 `monitor/inbox/`
派单，登记为 `freeze/RESIDUALS.json` 的 `E2-AXIS`）。

**改了什么**：`leg_reading` 在 G2 之前新增一道闸——

> **G6**：`curves.json` 的 `self_check` 未同时认证
> `accounts_for_every_billed_call` 与 `accounts_for_every_dollar` → `unsound`。

**为什么必须在 G2 之前**：G2 说的「total cost is zero」是关于**曲线自己那些行**
的和，而 E2L 把它当成关于**这条腿**的事实发表。两句话只有在曲线认账的前提下
才是同一句话。`20260731T231654Z-R1-sk48-b` 不认账：它的曲线在两行上合计
$0.00、逐行 `model_calls: 0`，而代理账本对这条腿计了 3 次调用、$7.6085275。
E2L 为它印的是 `status: thin` / `reason: "total cost is zero"`——
**把 $7.61 印成了零**。这正是本工单开出来要修的那句「看不出钱少了一截」，
只是它出现在产物里而不是在 `Run.turn_costs()` 里。
另一条 `20260731T231654Z-R1-g50t-a` 同样不认账（曲线 $7.6034195，
账本 $7.6085275），今天读作 `ok` 0.0；G6 之后两条都记 `unsound`。

**为什么闸在钱上，不闸在 `join_confidence` 上**（这一条是本次最该被质疑的判断，
所以把否掉的那个方案也写下来）：工单的验收原文是「那三条腿重算后，判定与它们
各自的 `join_confidence` 一致」，最直白的读法就是 degraded / ambiguous 一律拒答。
**这个读法被证据否掉了**：

* `degraded` 的成因逐条查过，全部是同一条**回合脊**的检查失败
  （`every billed theorize invocation was claimed by a turn`，未认领的分别是
  r2 的 turn 4、r3 的 turn 29、R2b 的 turn 26）；而这些腿的**步轴是完好的**，
  `anchored == priced` 逐条成立。
* 本文件 §1 逐字写着「**与 E2 的唯一实质区别是分母轴**……回合标签由 harness 的
  批处理约定决定，动作序号由环境的应答决定」。拿回合脊的缺陷去否决步轴的读数，
  等于把 E2L 重新拴回它被造出来就是为了摆脱的那条轴。
* 后果也不对：会把 6 条读数（0.0 / 0.115685 / 0.0 / 0.064934 / 0.083959 / 0.0，
  全部远低于平坦值 0.250，即**活臂在步轴上是后载的**）在看到方向之后改成拒答。
  那是与预注册方向相反的探索性读数，而 `freeze/STATS_RULES.md` §8 第一条与
  §3.0.6 都逐字封死了这一步：**探索性读数照报，包括方向与预注册相反的**。
* 而且它连验收本身都满足不了：`R1-sk48-b` 是 `degraded`，在那个方案下仍旧
  停在 `thin`——真正错的那一条反而漏掉了。

**改为怎么做到「判定与 join_confidence 一致」**：不是拒答，是**不许被读多**。
`paired_material` 新增 `n_evaluable_by_join_confidence`，让 `n_evaluable` 不能
被当成那么多条干净的腿读；产物新增顶层 `axis_caveat`，逐字带上轴的效度问题
（`freeze/RESIDUALS.json` `E2-AXIS` 的 `clears_when` 第 (b) 条要的就是这句话）；
每条腿的 `join_confidence` 照旧随数一起走，另加 `accounts_for_the_bill`。

**方向**：G6 只会把 `ok` 变成 `unsound`，不会把任何东西变回 `ok`。
`tier_of` 未动，`battery/artifacts/` 未动，§5 的四条约束全部照旧。

**代价**：`n_evaluable` 由 8 降到 7。`n_paired_games` 仍是 0，
`process_1_material` 的 `no-data` 裁定不因此改变——它从来不依赖条数。
"""


def main() -> int:
    with io.open(DOC, encoding="utf-8") as fh:
        text = fh.read()
    if MARK in text:
        print("already appended; nothing to do")
        return 0
    with io.open(DOC, "a", encoding="utf-8", newline="\n") as fh:
        fh.write(BODY)
    print("appended %d chars to %s" % (len(BODY), DOC))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
