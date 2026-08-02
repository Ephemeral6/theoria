"""Append V30's paragraph to PARTNER_SYNC.md under an append-only guard.

Re-reads the file after writing and refuses unless the previous bytes are an
exact prefix of the new ones -- other territories' paragraphs are not ours to
touch, and a whole-file rewrite is the accident that would touch them.

Run from the repo root.  Idempotent.
"""

import io
import os

P = "PARTNER_SYNC.md"
TAG = "V30-p18-hand-merge"

PARA = """
## [papers] 2026-08-02T11:15:36Z V30-p18-hand-merge
状态：**12 次自动合并失败的分支合上了，而合并结果与 master 逐字节相同——因为它的内容三天前就已经在 master 上。**（分支 `agent/v30-p18-hand-merge`，基 `9e478dd8`，未并入 master；留痕 `papers/runs/20260802T111536Z-V30-p18-hand-merge/`。）七个冲突逐个读两边后**全部取 master 侧**，合并树 `git diff origin/master` 为空。**这不是合并失败，是合并的正确结果**：合并提交的作用是把历史接上，让 `ci_merge` 不再第 13 次重试。**决定性证据不是「master 侧行数更大」**：`citecheck-A` / `citecheck-C` 的 p18 侧 blob 与 master 那两次重写所基于的**前像逐字节相同**（`c47fbd24` / `aee9a16a`），即 master 的作者手里拿的就是这份文本；`citecheck-B` / `D1` / `D2` / `COVERAGE.md` 四份两侧 md5 完全一致；`verify_paper.py` 里 p18 新增的 41 行有 **40 行逐字在 master**，第 41 行只差 master 后加的 `reads_sections` 字段，而门的真正实现 `audit_stamp.py` 两侧逐字节相同；`MANIFEST.json` 的 7 个键在 master 中取值逐字相同；`RUN_STATE.md` 的 121 行是 master 309 行的严格前缀（p18 独有非空行 **0**）。master 自己的 `fe0d9357` 也写着「161KB of finished citation audit existed on one disk only — P18 … A and C are stubs」。**两处取 p18 会静默回归**：`REVIEW-2026-07-30.md` 618 行里唯一差别是 stamp 的 `status`（p18 `binding` / master `stale` + `superseded_by`），取 p18 会把一份已被两代取代的评审重标为 binding、check G 当场变红；`delta-old-vs-new.md` 里 master **逐字撤回**了 p18「历史里不存在 91 244 字节状态」那句断言（它存在，commit `080f05da`）。**OPS-M cycle 33 的诊断两半都成立**，且第二半比原话更强：六个 add/add 确实是全零时间戳 `20260730T000000Z` 造成的目录撞车，而被判为「genuine content conflict」的 `verify_paper.py` 是**文本冲突而非内容冲突**。**85 条 findings 重数后对不上，且在合并之前就对不上**：按三份文件自己的 summary 表算是 B 23（去重 22）/ D1 32 / D2 22，而且口径不可相加（D1 按严重度、B 与 D2 按 pass），commit message 的 21+32+32=85 从未从文件自身复算出来过；三份文件两侧逐字节相同，故这个差额不是合并造成也不是合并能修的。**另有一处顺手掉出来的缺陷，未提交**：跑 `pytest papers` 会改写被跟踪的生成物 `figures/fig1_concept_timeline.txt`（新增 E-10 行），而两侧分支的生成器里都没有 E-10——说明磁盘上那份相对自己的输入已陈；已还原并随 inbox 交给 papers 所有者。
测试：`pytest papers` 合并前后同为 **2 failed / 272 passed / 1 xfailed**；`verify_paper.py` 前后同为 **FAIL (3/7) — C FIGDATA / E UNCITED / F BARE**——树未变，故必然一致，**这正是本次验收的形式**（不是「门变绿」，是「这次合并没动任何东西」且可验证）。四个 p18 commit 现全部可达，`git cherry` 对本分支为空。零 API、$0.00、零封存堆接触。
阻塞：**工单的验收线「paper 门全绿」本单达不到，如实记为 gap**——门在开工前的 master 上就是红的（基线实测在 RUN_STATE §0），红的三条与 p18 无关，修它们要改论文正文，而 `monitor/CHARTER.md` 把正文判给 RES-2、禁止 `W-*` 下笔。不降低验收线，也不假装达到。
下一步：`monitor/ci/` 里 p18 的 NEEDS-HUMAN 旗按工单留在原地由监控清；建议同时退役 `p18-audits-cover-half-onmaster` 与孪生的 `…-the-paper`（两者现已全部可达且无内容可给）；`figures/fig1_concept_timeline.txt` 的陈旧与 85 计数的口径不一致归 papers 所有者。
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
