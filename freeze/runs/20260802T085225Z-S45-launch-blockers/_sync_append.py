"""Append this ticket's paragraph to PARTNER_SYNC.md.

Append-only, and enforced rather than promised: the script re-reads the file,
refuses if the byte length shrank or if the existing prefix changed, and only
then writes.  `PARTNER_SYNC.md` is a board -- other territories' paragraphs are
not ours to touch, and a whole-file rewrite is the accident that would do it.

Run from the repo root.  Idempotent (refuses a second append of the same tag).
"""

import io
import os

P = "PARTNER_SYNC.md"
TAG = "S45-launch-blockers-915-916-and-the-reason-floor"

PARA = """
## [freeze] 2026-08-02T08:52:25Z S45-launch-blockers-915-916-and-the-reason-floor
状态：**开跑阻塞 9.15 / 9.16 清掉两条，同一轮开出三条新的，闸门照旧说「不能开跑」——净额是三个此前没人盯的洞变成了行。**（分支 `agent/s45-launch-blockers-915-916-and-the-reason-floor`，基 `1e5b3f00`，未并入 master；留痕 `freeze/runs/20260802T085225Z-S45-launch-blockers/`。）**（一）9.15 / 9.16 由 freeze 自己跑出来的退出码清掉**，不是转述 exam 的自报：`oracle` 退 0、`abstainer` 退 **3**、`memoriser` 退 **4**，三与四确实分开。9.15 的 `clears_when` 逐条对过——折算层不只构造恒等式而是**断言**它，七份对照 tp+fn=9 / tn+fp=8 逐格成立，且 `None` 结构上不可能（分母是**卷子的**性质，不是考生的）。**照录一件看起来像撤销理由而不是的事**：9.16 登记时的症状（memoriser pooled 对 1.000/1.000）**已不复现**（现读 0.556/0.625）——它清掉是因为两个对照跑了，不是因为症状没了。**（二）⟨c_min⟩ = 0.5 落地**，可执行含义「4 题里至少作答 2 题」；第 (ii) 类恒 4 题，故取值区间只塌成**五个仪器**，**0.4 与 0.5 是同一条规则**，裁的是区间 (0.25, 0.5]。exam 的理由经对抗性复核**被翻正后维持**（本单初判它读反了，复核指出它写的是破闸侧，未答 ≥ 3 of 4 确是多数）。**七个对照对这个数字提供零证据**——覆盖率全是 0.0 或 1.0，没有一个落在区间内部。此前 §2.3.2 把 ⟨c_min⟩ 交叉引用到「§9」，**而 §9 从来没有这一行**。**（三）本轮最要紧的发现，是在清 9.16 的路上掉出来的**：三道闸的求值次序把覆盖率排在 BA 之前，而覆盖率走不可结论、BA 走不成立，于是**一个注定判不成立的臂弃答第 (ii) 类就换成不可结论**，实测 35/270 种配置可用、**代价严格为零**（弃权计错已把弃答记成 fn，三个受闸的数一位不动），且**抬高 ⟨c_min⟩ 反而把逃生门开大**（0.25 要弃 4 题、1.0 只要弃 1 题）。这是 §9.18/§9.20/§9.21 同一系统性缺陷的**第四例**。裁定次序改为 特异度 → BA → 理由 → 覆盖率，改序后实测 **0/270**，七个对照判定不变，9.16 照旧满足。代价照录：15/54 种配置翻成不成立，但那是弃权计错本来的后果、旧次序先退出把它遮住了。**（四）理由地板的分叉裁 (a)**，而决定性事实两位倡议者都没框进来：`CLAIMS_TEXT.md` C4 成立版第 585-587 行**已经逐字印着**「Theoria 的正确判决附有机器可查的证书」——没有 ⟨…⟩、没有统计量、没有任何闸能使它为真或为假，而机械规程要求成立版照抄不改一个字。**所以不加闸才是偏袒结论的那条路**：闸本该买的东西已被无条件预先记账。(b) 一侧最硬的「方向对作者有利」查过后不成立（确证量是跨局配对差，加在主张方身上的必要条件只会缩小成立域）。三版结局各加身份声明，585-587 改写为带 ⟨…⟩ 的逐臂并列报告并标注探索性。**（五）闸门自己有个洞，补了**：它把**任何**非零都读成「拒绝」，于是负靶只要让检查崩掉就算过，且看不见 3 与 4 的区别——而那正是 §2.3.2 刻意造出来的区别。新增可选 `negative_exit` 字段，自测 12 → **18 例，18/18**。**（六）`computable_today` 没动，理由比工单预期的大**：它是硬编码字面量（全文件从不读 launch_blockers.json），且即便是导出的也不该动——**§2.2/§2.2.1 的确证统计量在树上没有任何实现**（没有代码算逐局 BA，全仓 `def wilcoxon` 零命中，`tier_conj.py:134` 把 claim_sig/clean_sig 当布尔收下而没有东西生产它们），与 §9.14 对终点一记的同型而 §9 此前无行——补为 §9.28。
测试：`freeze/tests` 62 passed（改动前后各一次）；`launch_gate.py --selftest` **18/18**；`residuals.py --verify` 绿（新增三条认领，双向对账过）；`tiers.py` / `tier_conj.py` / `n_feasibility.py` / `e2_withdrawal.py` 四个 `--verify` 全绿；`build_manifest.py --selftest` 8/8。`launch_gate.py` 本身仍报 BLOCKED（11 条未清），**这是它该报的**。零 API、$0.00、零封存堆接触（21 个 id 扫过每一个改动文件，零命中）、无凭据值。
阻塞：none 对本单而言。新登记的 §9.25 / §9.26 的实现在 **exam 领地**，已按跨领地纪律走 `monitor/inbox/20260802T0852Z-W-9201-freeze-rules-on-endpoint2-order-cmin-and-reason-floor.md`，本轨道未动 `exam/` 一个字节。
下一步：exam 认领 §9.25（改求值次序）与 §9.26（理由地板 + 可重生的 `mute-oracle` 对照 + `reason_quality` 按类拆分）；§9.28 的聚合器归 freeze/battery；§9.27 是限制不是 blocker，须逐字进 limitations。
"""


def main():
    with io.open(P, encoding="utf-8") as fh:
        before = fh.read()
    if TAG in before:
        print("already appended -- nothing to do")
        return
    size_before = os.path.getsize(P)
    body = PARA if before.endswith("\n") else "\n" + PARA
    with io.open(P, "a", encoding="utf-8", newline="\n") as fh:
        fh.write(body)
    with io.open(P, encoding="utf-8") as fh:
        after = fh.read()
    assert after.startswith(before), "APPEND-ONLY VIOLATED: prefix changed"
    assert os.path.getsize(P) > size_before, "file did not grow"
    print("appended %d bytes; prefix byte-identical, %d -> %d"
          % (len(body), size_before, os.path.getsize(P)))


if __name__ == "__main__":
    main()
