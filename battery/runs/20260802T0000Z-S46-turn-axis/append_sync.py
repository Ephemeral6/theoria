"""Append battery's S46 paragraph to PARTNER_SYNC.md.

Append-only, and only our own paragraph: this asserts the file's existing bytes
are untouched before and after, so a bad write cannot silently edit another
territory's section.
"""
import io
import os

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
DOC = os.path.join(REPO, "PARTNER_SYNC.md")

MARK = "## [battery] 2026-08-02T00:00:00Z S46-turn-axis"

BODY = """
## [battery] 2026-08-02T00:00:00Z S46-turn-axis-no-fallback
状态：`Run.turn_costs()` 不再把枚举下标与真实回合标签装进同一个桶（`freeze/RESIDUALS.json` `E2-AXIS`）——新增 `Run.turn_axis()` 四态，轴不可重建时 E2/E3 拒答（`partial`→`unsound`，`absent`→`thin`），`ledger_jsonl` 不再拿行序当标签；`E2-AXIS` 的 `clears_when` (a) 现可查，(b) 要 `papers/` 出手，不在本领地。领到时电池本来就是红的（9 条，全是 `theoria-arm` 动了没跟上），先单独一提交推绿再动本工单。
测试：**470 passed / 0 failed**；`battery/verify.py` **八条全绿**。V9 裁决逐字未动（降级 38→38，**提升 0**，`tier_of` 位移 0，mutant sweep 无失配）。负样本一：4028 个指标格子逐格对比 master，**0 个移动**——离线语料本来就全带标签，那条回落可达但从未承重。负样本二：全无标签的记录被拒，不再退回 `0..n-1`。零 API、$0.00、零封存堆接触、无凭据值。
阻塞：none。但有一条**需要复核的偏离**：验收第三条（E2L 判定与 `join_confidence` 一致）我没按字面上闸——`degraded` 全部源自**回合脊**的检查失败而这些腿的**步轴完好**，照字面做会把 E2L 拴回它被造出来就是为了摆脱的那条轴，并把 6 条与预注册方向相反的探索性读数在看到方向之后改成沉默（`STATS_RULES.md` §8 封死），而且真正错的 `R1-sk48-b` 反而漏掉。改为闸在钱上（G6：`curves.json` 不认账则 `unsound`），命中 `R1-sk48-b`（曲线 $0.00 对账本 $7.6085275，原印「total cost is zero」）与 `R1-g50t-a`（差 $0.005，原读 `ok` 0.0），其余 8 条不动；另加 `n_evaluable_by_join_confidence`、顶层 `axis_caveat`、每腿 `accounts_for_the_bill`。修订按 `PREREG_V9.md` §0 协议追加在 `PREREG_E2L.md` `## 修订`，含「程序上仍是一次失守」的自述。已报 `monitor/inbox/2026-08-02T0000Z-W-9205-...`，请监控/freeze 裁。
下一步：给 `theoria-arm` 的提醒——`turn_costs()` 返回契约变了（轴不可重建返回 `[]`），`tests/test_turn_series.py:489` 今天不受影响（5 个调用全带标签，35 passed），但若 `cost_curve.json` 出现 `"step_idx": null` 的行就会红；`adapters/theoria_live.py:268` 的 `Call.step_idx=None` 按 `PREREG_E2L.md` §5 仍留给它自己的工单。
"""


def main():
    with io.open(DOC, encoding="utf-8") as fh:
        before = fh.read()
    if MARK.split(" S46")[0] in before and "S46-turn-axis" in before:
        print("already appended")
        return 0
    with io.open(DOC, "a", encoding="utf-8", newline="\n") as fh:
        fh.write(BODY)
    with io.open(DOC, encoding="utf-8") as fh:
        after = fh.read()
    assert after.startswith(before), (
        "PARTNER_SYNC.md is append-only and this write changed existing bytes")
    assert after[len(before):] == BODY
    print("appended %d chars; %d pre-existing bytes verified untouched"
          % (len(BODY), len(before)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
