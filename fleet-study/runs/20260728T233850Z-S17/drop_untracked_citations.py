#!/usr/bin/env python3
"""Drop the two citations that pointed into an untracked runtime directory.

W-1641, 2026-07-29.  Fallout from `relativise_citations.py`: once the absolute
`C:/Users/user/Desktop/theoria/...` prefixes were stripped, verify.py could
finally resolve these paths against the tree -- and two of them do not exist
anywhere, in the worktree or in history.  `monitor/dispatch-logs/` is a runtime
directory that was never committed.

The absolute form had been hiding that: the checker resolved it against the
one machine's main checkout, where the directory happens to exist on disk.
This is the study's own `requirement_cites_nonexistent` class, produced by the
study, and caught only because the paths were made relative.

Both rows keep their other, resolvable citations.  The row is not deleted and
the measurement is not withdrawn -- what changes is that the caveat now says
which half of it a reader cannot re-derive.
"""

import json
import sys
from pathlib import Path

DATA = Path(__file__).resolve().parents[2] / "data" / "counterevidence.jsonl"
DEAD = {"file:monitor/dispatch-logs/registry.json", "file:monitor/dispatch-logs/"}

NOTE = ("【W-1641 2026-07-29 更正】原先此行引用 `monitor/dispatch-logs/`，"
        "那是一个从未被提交的运行时目录；引用写成绝对路径时，校验器是拿写它的那台"
        "机器的主检出去解析的，于是一直是绿的。改成仓库相对路径后立刻变红——"
        "这正是本数据集自己编目的 `requirement_cites_nonexistent`，由本研究产生，"
        "且只有在路径相对化之后才暴露。该引用已移除，行内其余引用可解析，"
        "**但读者无法复算依赖那个目录的那一半读数**（本行的 registry / dispatch 日志部分）。")


def main() -> int:
    raw = DATA.read_bytes()
    if b"\r" in raw:
        sys.exit("CRLF")
    rows = [json.loads(l) for l in raw.decode("utf-8").splitlines() if l.strip()]
    touched = 0
    for row in rows:
        keep = [e for e in row.get("evidence") or [] if e not in DEAD]
        if len(keep) != len(row.get("evidence") or []):
            if not keep:
                sys.exit(f"{row['id']}: dropping would leave no evidence; fix by hand")
            row["evidence"] = keep
            row["caveat"] = (row.get("caveat") or "").rstrip() + " " + NOTE
            touched += 1
            print(f"  {row['id']}: dropped dead citation, caveat annotated")
    DATA.write_bytes(("\n".join(json.dumps(r, ensure_ascii=False) for r in rows)
                      + "\n").encode("utf-8"))
    print(f"{touched} rows corrected")
    return 0


if __name__ == "__main__":
    sys.exit(main())
