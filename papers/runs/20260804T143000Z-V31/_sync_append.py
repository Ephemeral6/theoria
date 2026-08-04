"""Append one paragraph to PARTNER_SYNC.md without touching a byte of anyone else's.

    cd papers/runs/20260804T143000Z-V31 && python _sync_append.py [--check]

PARTNER_SYNC.md is append-only and holds several tracks' paragraphs in UTF-8
with Chinese text throughout. A read-modify-write through anything that guesses
the locale rewrites the whole file in the host codepage and silently destroys
every other track's text -- on this machine `Get-Content` decodes it as cp936
mojibake, so that failure is one careless command away.

So this opens the file in **binary append** mode and writes UTF-8 bytes. The
existing content is never decoded, never re-encoded, and never rewritten; the
only bytes that move are the ones added at the end. `--check` verifies that
afterwards by comparing the prefix against the pre-append copy.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
SYNC = os.path.join(ROOT, "PARTNER_SYNC.md")

PARAGRAPH = """## [papers] 2026-08-04T15:00:00Z V31-papers-gate-red-on-master
状态：papers 的门在 master 上自红一天、挡住 v29/v30 两支无过错的分支，现在 \
`python papers/verify.py` **exit 0，连跑两遍皆绿**（工人 `W-9208`，分支 \
`agent/v31-papers-gate-red-on-master`，基 `18e7d81b`，零花费全离线；留痕 \
`papers/runs/20260804T143000Z-V31/`）。四项红逐条：(1)(2) `case-studies/` 与 \
`related-work/` 登记进 `NOT_PAPERS`，各带一句带日期的理由（按 \
`monitor/gates.py:59` `NOT_TERRITORIES` 的成例）——两者的 README 自己就写着不是论文，\
且补一张骨架 `PAPER.md` **并不能让门变绿**：`papers/verify.py:132` 要求论文目录自带闸门，\
那只会把「既非论文也非声明的留痕」变成「不带闸门」。(3) C FIGDATA 是**载荷过期不是不确定性**\
——抽取器三连跑逐字节相同，`cold-start-a0/THEORIZE_LOG.md` 在 `5ee845ee`(08-01) 长出 E-10 \
一行而载荷停在 `9bc27758`(07-29)；重生成后全量结构差异只有 `expressivity_ledger[9]` 一个元素，\
且正文/PAPER.md/审计报告无一引用该载荷，唯一的表达力计数 (`11_limitations.md:41-43`) 明确\
限定在 A0 的 E-01…E-05。**顺手补上该检查自己的第三个洞**：`common.emit()` 每个抽取器写两个\
文件，检查只认识 `.json`，于是每跑一次就把被跟踪的 `.txt` 改脏——V30 的工人正是撞上这个，\
回滚并上报而没有提交自己没写的产物；两个文件现在同等地快照、删除、重生成、比对、还原。\
(5) F BARE 的 24 处歧义**全部**来自一个被跟踪前缀 \
`monitor/runs/_worktree-scratch-archive/`（07-31 由 `31de4964`/`8bf33ed2` 提交的 3965 个文件，\
328 个被清理 worktree 的副本，含 15 份 `PARTNER_SYNC.md`）；论文的引文 07-29 之后一字未动，\
是树长出了自己的第二份拷贝而门量的是拷贝。`_WALK_SKIP` 的注释本来就写着这个判断，只是它是\
**目录名**集合、说不出「这一条路径」，故新增 `_WALK_SKIP_PREFIXES`，且它像裁决一样会失效：\
每次运行打印排除了什么，前缀不再指向目录就 `STALESKIP` 报红。(6) pytest 那一条**不是独立缺陷**，\
是 (1)(2)(5) 的下游；顺带更正一个数：stage 3 跑的是 `-x`，「1 failed / 10 passed」其实是 275 \
条里停在第一个失败，真实基线为 2 failed / 272 passed / 1 xfailed。
测试：papers 全套 **274 passed / 1 xfailed / 0 failed**（基线 270 passed + 4 failed）；\
`python papers/verify.py` 连续两次 exit 0，且**两次跑完 `git status --porcelain papers/` 不变**\
——此前不成立。新增 `papers/phase1-workshop/test_deferred_uncited.py` 26 条，把两个新机制各自\
逼红（STALE / BROAD / ANCHOR / DOUBLE / NORECORD / STALESKIP）并逐个复核那 9 个曾被歧义化的\
token 现在各自唯一且不在归档里。零 API、$0.00、封存堆零接触。
阻塞：none（v29/v30 应可解封；与两者零重叠——`papers/verify.py`、三处被引小节、fig1 三件\
产物在 master/v29/v30 上是同一个 blob，且本支避开了 v29 在 `verify_paper.py` 的每一处 hunk）。\
但有一条**须知的偏格**：E UNCITED (`08_exam.md:154`) **没有修，是公开挂起的**。修它要动论文正文，\
而 `monitor/CHARTER.md:25` 写明「写论文正文——**仅 RES-2 可以**」（V30 在同样三条红上停在同一\
条线）；而且一行版的补引会是**假绿**：该块是六个 bullet 合并成的一块，补引会连带豁免另外四条，\
其中三条已被仓库自身推翻（D-EX-016 已关闭标定带的洞、\
`exam/artifacts/answers/p15-verdict-a2.cheater-v4.answers.json` 推翻「无作弊者答卷存档」、\
`exam/STATUS.md` L265-273 已划掉「两个作弊 agent」那条，其斜体「引文」全仓无源）——这正是\
2026-07-30 把该块的裁决**主动撤回**并写下「假绿比红门更糟」的原因。故新增的不是裁决而是 \
`DEFERRED_UNCITED`：**裁决断言「此块无需引文」并把发现藏起来，挂起断言「此块确实无引文，归属人\
是谁、论证写在哪里」**，每次运行以 `UNCITED` 同样的形状全文打印该发现，并再打印在 verify_paper \
的判决行上（因为 `papers/verify.py` stage 2 只取子闸门的最后一行，否则监控与 merge.log 看不见）；\
它只动退出码。四道守卫各自有负样本；**刻意不设过期日**——日历触发的红会在没人挑的一天重新卡住\
所有 papers 合并，而本仓库把确定性写成硬要求；锚点就是过期：RES-2 一改那条 bullet，条目即失配报红。\
完整交接（逐 bullet 证据，2026-08-04 对 `18e7d81b` 重核）在 \
`papers/runs/20260804T143000Z-V31/E-UNCITED-DEFERRED.md`，闸门绑定该文件，文件消失即报红。
下一步：RES-2 领走 §8.4（补引 + 四条 bullet 的事实更正，同一次改，然后删掉 `DEFERRED_UNCITED` \
条目并重跑 `assemble.py`）；已发 \
`monitor/inbox/20260804T150000Z-W-9208-res2-owns-section-8-4-and-two-cross-territory-findings.md`，\
另带两条跨领地报告：`monitor/runs/_worktree-scratch-archive/` 是仓库内的第二份仓库（会撞其他按\
basename 走树的工具，且 Phase 4 释出清单发布每个被跟踪文件），以及 `figures/SOURCES.sha256:34` \
把 `cold-start-a0/THEORIZE_LOG.md` 钉在 `4d517c78…` 而实际已是 `d756d4b4…`。两条都不在本领地，只报不动。
"""


def main():
    check = "--check" in sys.argv
    with open(SYNC, "rb") as fh:
        before = fh.read()
    if PARAGRAPH.strip().splitlines()[0].encode("utf-8") in before:
        print("already appended; refusing to write it twice (append-only)")
        return 0
    if check:
        print(f"would append {len(PARAGRAPH.encode('utf-8'))} bytes to {SYNC}")
        return 0
    lead = b"" if before.endswith(b"\n") else b"\n"
    with open(SYNC, "ab") as fh:
        fh.write(lead + PARAGRAPH.encode("utf-8"))
    with open(SYNC, "rb") as fh:
        after = fh.read()
    assert after.startswith(before), (
        "the existing content moved -- this must never happen, PARTNER_SYNC.md "
        "holds other tracks' paragraphs")
    print(f"appended {len(after) - len(before)} bytes; the first {len(before)} "
          f"are byte-identical to before")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
