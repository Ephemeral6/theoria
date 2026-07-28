"""The work board: agents claim their own work, no per-item dispatch.

    python monitor/board.py list                  # what is available / claimed
    python monitor/board.py claim <worker-id>     # atomically take the top item
    python monitor/board.py done <id> <worker>    # mark delivered
    python monitor/board.py release <id> <worker> # give it back (with reason)

Why a board: one-shot sessions cost a launch per item and go stale between
items. A long-lived worker claims an item, delivers it, and claims the next —
so the monitor authors work and controls headcount, and nobody has to trigger
anything in real time.

Claiming is atomic by os.rename (single volume, Windows-safe): whoever renames
`items/<id>.md` to `claimed/<id>.<worker>.md` first owns it; everyone else
gets FileNotFoundError and tries the next candidate. No lock files, no races.

Item front matter (first lines of each item file):
    priority: 1..9      (1 = highest; ties broken by id)
    cell: A3            (map coordinate — the grid cell it lights up)
    territory: proxy    (the only dir it may write; conflict guard)
    deps: C1-worldgen   (comma-separated ids that must be done first)
"""

import os
import re
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
BOARD = os.path.join(HERE, "board")
ITEMS = os.path.join(BOARD, "items")
CLAIMED = os.path.join(BOARD, "claimed")
DONE = os.path.join(BOARD, "done")
LOG = os.path.join(BOARD, "board.log")

for d in (ITEMS, CLAIMED, DONE):
    os.makedirs(d, exist_ok=True)


def utc():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def note(msg):
    with open(LOG, "a", encoding="utf-8", newline="\n") as fh:
        fh.write("%s %s\n" % (utc(), msg))
    print(msg)


def meta(path):
    head = open(path, encoding="utf-8").read(800)
    out = {"priority": 5, "cell": "?", "territory": "?", "deps": [], "lane": ""}
    for key in ("priority", "cell", "territory", "lane"):
        m = re.search(r"^%s:\s*(\S+)" % key, head, re.M)
        if m:
            out[key] = int(m.group(1)) if key == "priority" else m.group(1)
    m = re.search(r"^deps:\s*(.+)$", head, re.M)
    if m:
        out["deps"] = [d.strip() for d in m.group(1).split(",")
                       if d.strip() and d.strip().lower() != "none"]
    return out


def item_id(fname):
    return fname[:-3] if fname.endswith(".md") else fname


def done_ids():
    return {f.split(".")[0] for f in os.listdir(DONE)}


def claimed_map():
    out = {}
    for f in os.listdir(CLAIMED):
        parts = f[:-3].split(".")
        if len(parts) >= 2:
            out[parts[0]] = parts[1]
    return out


def territories_busy():
    busy = {}
    for f in os.listdir(CLAIMED):
        m = meta(os.path.join(CLAIMED, f))
        busy[m["territory"]] = f[:-3].split(".")[0]
    return busy


def candidates(lane=None):
    ready = done_ids()
    busy = territories_busy()
    out = []
    for f in sorted(os.listdir(ITEMS)):
        if not f.endswith(".md"):
            continue
        m = meta(os.path.join(ITEMS, f))
        iid = item_id(f)
        blocked = [d for d in m["deps"] if d not in ready]
        if blocked:
            continue
        if m["territory"] in busy:          # territory exclusivity
            continue
        if lane and m.get("lane") and m["lane"] != lane:
            continue                        # standing researchers stay in lane
        if lane and not m.get("lane"):
            continue                        # unlaned items are for generic workers
        if not lane and m.get("lane"):
            continue                        # laned items belong to their standing
                                            # researcher; a generic worker must
                                            # not strip a lane bare (monitor,
                                            # 2026-07-28: the guard was one-sided)
        out.append((m["priority"], iid, f, m))
    out.sort(key=lambda r: (r[0], r[1]))
    return out


def cmd_list():
    print("=== available ===")
    for pri, iid, _f, m in candidates():
        print("  p%d  %-28s cell=%-3s territory=%-14s %s"
              % (pri, iid, m["cell"], m["territory"],
                 ("lane:" + m["lane"]) if m.get("lane") else ""))
    blocked = []
    for f in sorted(os.listdir(ITEMS)):
        if not f.endswith(".md"):
            continue
        m = meta(os.path.join(ITEMS, f))
        pend = [d for d in m["deps"] if d not in done_ids()]
        if pend:
            blocked.append((item_id(f), pend))
    if blocked:
        print("=== blocked ===")
        for iid, pend in blocked:
            print("  %-28s waits on %s" % (iid, ",".join(pend)))
    cm = claimed_map()
    if cm:
        print("=== claimed ===")
        for iid, worker in sorted(cm.items()):
            print("  %-28s by %s" % (iid, worker))
    if os.listdir(DONE):
        print("=== done (%d) ===" % len(os.listdir(DONE)))
        for f in sorted(os.listdir(DONE)):
            print("  " + f[:-3])


def cmd_claim(worker, lane=None):
    for _pri, iid, fname, _m in candidates(lane):
        src = os.path.join(ITEMS, fname)
        dst = os.path.join(CLAIMED, "%s.%s.md" % (iid, worker))
        try:
            os.rename(src, dst)                # atomic: first one wins
        except OSError:
            continue
        note("CLAIM %s by %s" % (iid, worker))
        print("---8<--- item %s ---8<---" % iid)
        sys.stdout.write(open(dst, encoding="utf-8").read())
        return 0
    print("BOARD-EMPTY")
    return 3


def cmd_done(iid, worker):
    src = os.path.join(CLAIMED, "%s.%s.md" % (iid, worker))
    if not os.path.exists(src):
        print("not claimed by you")
        return 1
    os.rename(src, os.path.join(DONE, "%s.%s.md" % (iid, worker)))
    note("DONE %s by %s" % (iid, worker))
    return 0


def cmd_release(iid, worker, reason="unstated"):
    src = os.path.join(CLAIMED, "%s.%s.md" % (iid, worker))
    if not os.path.exists(src):
        print("not claimed by you")
        return 1
    os.rename(src, os.path.join(ITEMS, "%s.md" % iid))
    note("RELEASE %s by %s (%s)" % (iid, worker, reason))
    return 0


def cmd_sweep(dry=False):
    """把死掉的工人还占着的认领交回板上。

    一次性工人被额度或崩溃打断后，claimed/ 里的认领永远挂着：板以为有人在做，
    领地被锁，新工人领不到活。判据保守——只清 W-* 前缀（一次性工人）且其
    计划任务已不在运行的；App/常驻会话（APP-*/RES-*）一律不动，它们的存活
    从任务表看不出来。"""
    import subprocess
    out = subprocess.run(["schtasks", "/Query", "/FO", "CSV", "/NH"],
                         capture_output=True)
    text = out.stdout.decode("gbk", "replace")
    live = set()
    for line in text.splitlines():
        cols = [c.strip('"') for c in line.split('","')]
        if len(cols) >= 3 and "TheoriaAgent-" in cols[0]:
            name = cols[0].strip('"').lstrip("\\").replace("TheoriaAgent-", "")
            if cols[2].strip('"') in ("Running", "正在运行"):
                live.add(name)
    freed = []
    for f in sorted(os.listdir(CLAIMED)):
        if not f.endswith(".md"):
            continue
        iid, worker = f[:-3].split(".")[0], f[:-3].split(".")[1]
        if not worker.startswith("W-") or worker in live:
            continue
        freed.append((iid, worker))
        if not dry:
            os.rename(os.path.join(CLAIMED, f),
                      os.path.join(ITEMS, "%s.md" % iid))
            note("SWEEP %s released (worker %s gone)" % (iid, worker))
    if not freed:
        print("no orphaned claims")
    for iid, worker in freed:
        print("%-28s freed from %s" % (iid, worker))
    return 0


def main():
    a = sys.argv[1:]
    if not a or a[0] == "list":
        cmd_list(); return 0
    if a[0] == "claim":
        lane = a[3] if len(a) > 3 and a[2] == "--lane" else None
        return cmd_claim(a[1], lane)
    if a[0] == "sweep":
        return cmd_sweep("--dry-run" in a)
    if a[0] == "done":
        return cmd_done(a[1], a[2])
    if a[0] == "release":
        return cmd_release(a[1], a[2], " ".join(a[3:]) or "unstated")
    print(__doc__)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
