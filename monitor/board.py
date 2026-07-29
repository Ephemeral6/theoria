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
OPS_STATUS = os.path.join(HERE, "ops-status")

# 赛道的主人。赛道守卫存在的理由是「别让通用工人把某个常驻研究员的队列抽干」——
# 那个理由只在主人还活着时成立。
LANE_OWNER = {"campaign": "RES-1", "paper": "RES-2",
              "verify": "RES-3", "infra": "RES-4"}

# 心跳阈值与判据的唯一出处（scan.py 的 self_driving 探针 import 这两个名字）。
# **看 mtime，不看 agent 自己写进 json 的 utc**：RES-4 已实测那些时间戳全线漂前，
# 一个自称的时刻可以把死会话说成活的，而文件被改写的时刻是机器观察到的事实。
STALE_MIN = 45

for d in (ITEMS, CLAIMED, DONE):
    os.makedirs(d, exist_ok=True)


def heartbeat_age(agent):
    """距上次心跳的分钟数；从未启动过返回 None。"""
    path = os.path.join(OPS_STATUS, "%s.json" % agent)
    if not os.path.exists(path):
        return None
    return int((time.time() - os.path.getmtime(path)) / 60)


def stale_lanes():
    """主人已停摆的赛道——它们的活对通用工人开放。

    这条规则是 2026-07-29 补的，起因是一次沉默的饿死：板上 21 件全部带赛道，
    四个赛道主人死了三个，而 `list` 把带赛道的活一律不显示，于是它报
    「available: (empty)」——三个刚起的通用工人一件也领不到，板却看起来是空的。
    守卫本身没错，错在它把「主人在忙」和「主人已死」当成了同一件事。"""
    out = set()
    for lane, owner in LANE_OWNER.items():
        age = heartbeat_age(owner)
        if age is None or age > STALE_MIN:
            out.add(lane)
    return out


def utc():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def note(msg):
    with open(LOG, "a", encoding="utf-8", newline="\n") as fh:
        fh.write("%s %s\n" % (utc(), msg))
    print(msg)


def meta(path):
    head = open(path, encoding="utf-8").read(800)
    out = {"priority": 5, "cell": "?", "territory": "?", "deps": [], "lane": "",
           "spend": "", "generic_ok": ""}
    for key in ("priority", "cell", "territory", "lane", "spend", "generic_ok"):
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
    stale = stale_lanes()
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
        # 花真钱的活不随赛道解封一起下放。赛道守卫此前**顺带**挡住了它——
        # 章程写的是「只有 RES-1 能花 API 钱」，而那条规矩一直是靠 campaign
        # 赛道有主在执行的。我把赛道解封之后，那层顺带的保护就没了：
        # 一个一次性工人可以领走一件在真 API 上打的战役（2026-07-29 当场发生）。
        # 现在要监控在条目里显式写 `generic_ok: yes` 才放行——花钱得是有人拍板，
        # 不是某道无关的闸门碰巧还没坏。
        if (not lane and m.get("spend") == "api"
                and m.get("generic_ok", "").lower() not in ("yes", "true")):
            continue
        if not lane and m.get("lane") and m["lane"] not in stale:
            continue                        # laned items belong to their standing
                                            # researcher; a generic worker must
                                            # not strip a lane bare (monitor,
                                            # 2026-07-28: the guard was one-sided).
                                            # 主人停摆超 STALE_MIN 则赛道解封——
                                            # 守卫护的是活人的队列，不是死人的。
        out.append((m["priority"], iid, f, m))
    try:
        sys.path.insert(0, HERE)
        import spec as _spec
        focus = list(getattr(_spec, "PHASE_FOCUS", []))
        boost = int(getattr(_spec, "FOCUS_BOOST", 0))
    except Exception:
        focus, boost = [], 0

    def rank(row):
        pri, iid, _f, m = row
        if boost and m.get("lane") in focus:
            pri -= boost + (len(focus) - focus.index(m["lane"]) - 1) * 0.1
        return (pri, iid)

    out.sort(key=rank)
    return out


def cmd_list():
    stale = stale_lanes()
    generic = candidates()
    generic_ids = {iid for _p, iid, _f, _m in generic}
    print("=== available (通用工人可领 %d) ===" % len(generic))
    for pri, iid, _f, m in generic:
        tag = ("lane:" + m["lane"]) if m.get("lane") else "unlaned"
        if m.get("lane") in stale:
            tag += "（主人停摆，已解封）"
        print("  p%d  %-28s cell=%-3s territory=%-14s %s"
              % (pri, iid, m["cell"], m["territory"], tag))
    # 赛道守卫会把有主的活挡在 candidates() 之外。**它们仍然是活。**
    # 只印 available 的旧写法让「板上没活」和「活全都有主」长得一模一样，
    # 而这两件事该派的人完全不同。
    reserved = []
    for lane in sorted(LANE_OWNER):
        for pri, iid, _f, m in candidates(lane):
            if iid not in generic_ids:
                reserved.append((pri, iid, lane, LANE_OWNER[lane], m))
    if reserved:
        print("=== reserved（有主，等其赛道研究员来领 %d） ===" % len(reserved))
        for pri, iid, lane, owner, m in sorted(reserved):
            age = heartbeat_age(owner)
            print("  p%d  %-28s lane=%-8s owner=%s(%s) territory=%s"
                  % (pri, iid, lane, owner,
                     "未启动" if age is None else "%d分钟前" % age,
                     m["territory"]))
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


HOLD_CAP = 3        # 常驻研究员同时持有的上限；一次性工人自然只拿一件


def held_by(worker):
    return sum(1 for f in os.listdir(CLAIMED)
               if f.endswith(".md") and f[:-3].split(".")[1] == worker)


def cmd_claim(worker, lane=None):
    if worker.startswith("RES-") and held_by(worker) >= HOLD_CAP:
        print("HOLD-CAP-REACHED 你手上已有 %d 件，先交付或 release 再领。"
              % HOLD_CAP)
        return 3
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
