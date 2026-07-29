#!/usr/bin/env python3
"""Correct A-18: the two worker-fail counts were two *trees*, not two times.

W-1641, 2026-07-29, second correction to this row.  The first correction said
68 and 124 were "the same live file read at two instants".  That was wrong, and
wrong in the direction that made it sound tidier.

    committed (this worktree, branch base)  161 lines, 03:16:26Z-23:00:29Z,  68 worker-fail
    live working tree (main checkout)       173 lines, still growing,       145 worker-fail

Same path, different tree.  The 68 reading is reproducible from git; the 124
(now 145) reading is uncommitted working-tree state and is not reproducible by
anyone, ever.  A citation of `file:monitor/reflex.log` does not say which, and
the study made both readings without noticing they came from different trees.

Also fixes the row's stated span: it said the log runs from 13:43:11Z, but the
first line of the 161-line committed file is 03:16:26Z.
"""

import json
import sys
from pathlib import Path

DATA = Path(__file__).resolve().parents[2] / "data" / "assembly.jsonl"

OLD_MARK = "【W-1641 于 2026-07-28T23:58Z 复算并更正】"
NEW = (
    "【W-1641 2026-07-29 二次更正，前一次更正本身也是错的】"
    "`reflex.log` 的两个读数不是「同一个活文件的两个时刻」，是**两棵树**："
    "本分支工作树里被提交的那份是 **161 行、2026-07-28T03:16:26Z–23:00:29Z、"
    "`worker-fail` 68 次**（本行原写起点 13:43:11Z，是读错，实际 03:16:26Z）；"
    "而主检出里未提交的活文件当时 124 次、现在 145 次、173 行且仍在长。"
    "两者路径相同、内容不同。**`worker-spawn` 在两棵树里都是 0**，这是本行的结论，"
    "不受影响。要紧的是可复现性：**68 那份在 git 里，任何人都能复算；"
    "145 那份是未提交的工作树状态，谁也复算不了。** "
    "而 `file:monitor/reflex.log` 这条引用不区分二者——前一次更正说本行"
    "「因为被跟踪所以可从历史复现」，只对 68 那份成立，对 145 那份不成立。"
)


def main() -> int:
    raw = DATA.read_bytes()
    if b"\r" in raw:
        sys.exit("CRLF")
    rows = [json.loads(l) for l in raw.decode("utf-8").splitlines() if l.strip()]
    hit = 0
    for row in rows:
        if row.get("id") != "A-18":
            continue
        m = row["measurement"]
        cut = m.find(OLD_MARK)
        row["measurement"] = (m[:cut] if cut != -1 else m).rstrip() + " " + NEW
        row["caveat"] = (
            "0 spawns means 0 spawns judged successful by reflex.py's own test (the "
            "substring 'started' in dispatch.py stdout); a worker could in principle "
            "have launched while the probe misread the output -- exactly the failure "
            "class this repo catalogues. The load-bearing figure here is that zero, "
            "and it holds in both the committed and the working copy. Every OTHER "
            "count taken from monitor/reflex.log must name which tree AND which "
            "instant: the committed copy is 161 lines / 68 worker-fail and is "
            "reproducible from git; the main checkout's working copy was 124 and is "
            "now 145, is still being appended to, and is reproducible by nobody. "
            "This row got that wrong twice before getting it right."
        )
        hit += 1
    if not hit:
        sys.exit("A-18 not found")
    DATA.write_bytes(("\n".join(json.dumps(r, ensure_ascii=False) for r in rows)
                      + "\n").encode("utf-8"))
    print("A-18 corrected (second correction)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
