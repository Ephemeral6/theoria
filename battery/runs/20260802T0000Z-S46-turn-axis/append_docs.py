"""Append S46's design record to DECISIONS.md and its state to STATUS.md.

Both are append-only in practice; written through Python so the files' UTF-8
is not touched by a shell that re-encodes them.  Run once; refuses to double up.
"""
import io
import os

HERE = os.path.dirname(os.path.abspath(__file__))
BATTERY = os.path.abspath(os.path.join(HERE, "..", ".."))

DECISION_MARK = "### D-B-024 ·"
DECISION = """

### D-B-024 · An axis that cannot be rebuilt is a measurement that was not taken

`Run.turn_costs()` used to fill a missing `Call.turn` in with the call's
position in the list, and put that position into the same bucket dictionary as
the real labels.  Two defects in one line.  The loud one: a *partly* labelled
record summed the unlabelled call at position 7 into the bucket of the call
genuinely labelled `turn=7`.  The quiet one, and the worse one: a *wholly*
unlabelled record was renumbered `0..n-1` and scored, so a record that could not
answer the question answered it anyway.

`freeze` found it, ruled on it in `STATS_RULES.md` §3.0.2 step 4, registered it
as `RESIDUALS.json` `E2-AXIS`, and sent it here rather than editing our code.
S46 is the answer.

**The decision that needed arguing is not "refuse the partly labelled record"
— that is the ticket — it is "refuse the wholly unlabelled one too."**  This
module's own header used to declare one-call-per-turn as E2's axis, on the
authority of `INPUT_FORMAT.md` gap 5: the ledger carries no turn index, so
call order is the substitute.  Refusing the unlabelled record withdraws that
substitute, and costs any future source that stops stamping turns its E2 and E3
readings outright.  It is still right, because the substitute was never applied
*instead of* the labels — it was applied *alongside* them, in one key space,
and a substitute that cannot be told apart from the real axis in the published
number is not a substitute but a fabrication.  The header now says so, and gap 5
is visible as an absence instead of being papered over by one.

Two things make this a repair rather than a change of口径, and both were
measured before anything was edited rather than argued afterwards:

* **Every priced call in every loadable ledger already carries a `step_idx`**,
  so the fallback was reachable but never load-bearing.  4028 metric cells were
  compared against master one by one: **none moved.**
* **`v9_demotions()` recomputes against the live metric**, so a gate that made
  a V9 attack stop landing would *promote* a metric, which `PREREG_V9.md` R1
  forbids outright.  Measured: 38 demotions before, 38 after, zero tier moves.
  The V9 mutants and the exploit fixtures that meant "one call per turn" were
  re-expressed to say it (`turn=i`) rather than to infer it from the fallback;
  their registered verdicts and every asserted number are unchanged.

The refusal is split so the reason stays useful: `partial` is `unsound` (the
record claims an axis and does not supply one, and `incoherent record:` is the
grep handle for that), `absent` is `thin` (nothing contradicts itself; the axis
was simply never written down).  No fourth status was invented — `Value`'s three
are a contract the artefacts are written against.

The gate sits **after** the price check and **before** `total <= 0` and
`MIN_TURNS_FOR_SHAPE`, because those two are computed from the empty list and
would otherwise report "total cost is zero" about a leg that spent real money.
That is not hypothetical: `20260731T231654Z-R1-sk48-b` bills three calls for
$7.6085275 with no turn label on any of them, and E1 states the money in the
same artefact where E2 would have stated a zero.  **A false reason is worse
than a refusal, because it reads as a finding.**
"""

STATUS_MARK = "## S46 轴不可重建就是没有测量"
STATUS = """

## S46 轴不可重建就是没有测量（2026-08-02，UTC 20260802T0000Z）

`freeze` 经 `monitor/inbox/` 派来的 `E2-AXIS`。四件事值得先读：

1. **缺陷可达，但从未承重。** 106 个可加载 run 里 99 个带价 run 的每一个带价
   调用都带着 `step_idx`，所以 `Run.turn_costs()` 那条回落从没真正决定过一个
   数。4028 个指标格子逐格对比 master，**0 个移动**。这是本次改动能被称为
   「修复」而不是「改口径」的全部理由，也是先测量再动手换来的。

2. **真正在开火的是活腿。** `20260731T231654Z-R1-sk48-b`：3 个带价调用、
   0 个回合标签、$7.6085275。今天它没读出一个数**只是因为 3 < 8**——被一条
   毫不相干的早死下限救下。同样形状再多五个调用就会读出一个数。
   同一条腿在 E2L 那边被印成 **「total cost is zero」**：$7.61 印成零。

3. **最该被怀疑的地方是有没有买到豁免。** `audit/gaming.py` 读的
   `v9_demotions()` **对着活指标重算**，所以一道让 V9 攻击不再落地的闸会把
   `tier_of` 往上抬，而 `PREREG_V9.md` R1 是只降不升。实测：降级 38 → 38，
   提升 0，层级位移 0，mutant sweep 无失配。

4. **工单验收第三条我没按字面做，并且把否掉的方案一起留了下来。**
   按 `join_confidence` 给 E2L 上闸会把 E2L 重新拴回它被造出来就是为了摆脱的
   回合轴，并且会在看到方向之后把 6 条与预注册方向相反的探索性读数改成沉默
   （`STATS_RULES.md` §8 封死）。改为闸在钱上（G6：曲线不认账，它的零就不是
   零），命中两条真有问题的腿，其余 8 条不动。修订按协议追加在
   `PREREG_E2L.md` 的 `## 修订` 段，连同「程序上仍是一次失守」一起写明。
   已报 `monitor/inbox/`，请裁。

留痕：`battery/runs/20260802T0000Z-S46-turn-axis/`（探针、逐格对比、
MANIFEST）。测试 470 passed，`verify.py` 八条全绿，API 花费 0。
"""


def append(path, mark, body):
    full = os.path.join(BATTERY, path)
    with io.open(full, encoding="utf-8") as fh:
        text = fh.read()
    if mark in text:
        print("%s: already present" % path)
        return
    with io.open(full, "a", encoding="utf-8", newline="\n") as fh:
        fh.write(body)
    print("%s: appended %d chars" % (path, len(body)))


if __name__ == "__main__":
    append("DECISIONS.md", DECISION_MARK, DECISION)
    append("STATUS.md", STATUS_MARK, STATUS)
