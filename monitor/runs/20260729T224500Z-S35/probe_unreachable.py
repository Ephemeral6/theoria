"""S35 measurement probe: how many board items can nobody claim?

Deliberately does **not** restate the guards. It imports `board` and asks the
real `candidates()` / the real `cmd_claim` predicates, once per plausible
claimant identity, then takes the union. A probe that re-derives the rules
measures my reading of the code; this one measures the code.

Takes the `monitor/` directory to measure, defaulting to the one this file
lives under. The argument matters: this probe is delivered on a branch, whose
`monitor/board/` is a *snapshot*, while the board worth measuring is the live
one in the main checkout.

    python monitor/runs/20260729T224500Z-S35/probe_unreachable.py [/path/to/monitor]
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
MONITOR = os.path.abspath(sys.argv[1] if len(sys.argv) > 1
                          else os.path.join(HERE, "..", ".."))
sys.path.insert(0, MONITOR)

import board  # noqa: E402


def claimable_by(worker, lane):
    """Ids `worker` would get from `board.py claim worker [--lane lane]`.

    Mirrors `cmd_claim`'s two extra guards on top of `candidates(lane)`, and
    nothing else -- the rest of the exclusions already live in `candidates`.
    """
    if lane and board.LANE_OWNER.get(lane) not in (None, worker):
        if lane not in board.stale_lanes():
            return set()                       # LANE-NOT-YOURS
    out = set()
    for _pri, iid, _f, m in board.candidates(lane):
        if worker in board.released_by(m):
            continue                           # withheld: you handed it back
        out.add(iid)
    return out


def main():
    lanes = sorted(board.LANE_OWNER)
    stale = board.stale_lanes()
    ready = board.done_ids()
    claimed = set(board.claimed_map())
    busy = board.territories_busy()

    # Every identity that could walk up to this board.
    claimants = [(board.LANE_OWNER[l], l) for l in lanes]
    claimants += [(board.LANE_OWNER[l], None) for l in lanes]
    claimants += [("W-9999", None)]            # a fresh generic worker

    reach = {}
    for worker, lane in claimants:
        for iid in claimable_by(worker, lane):
            reach.setdefault(iid, []).append("%s%s" % (worker, "/" + lane if lane else ""))

    shelf = []
    for f in sorted(os.listdir(board.ITEMS)):
        if f.endswith(".md"):
            shelf.append((board.item_id(f), board.meta(os.path.join(board.ITEMS, f))))

    # The item's own claim: printed under `reserved` (so: ready, deps met,
    # territory free, lane matches) yet its lane owner has handed it back.
    reserved_unreachable, other_unreachable, deps_blocked = [], [], []
    for iid, m in shelf:
        if iid in ready or iid in claimed:
            continue
        if [d for d in m["deps"] if d not in ready]:
            deps_blocked.append(iid)
            continue
        if iid in reach:
            continue
        lane = m.get("lane") or ""
        owner = board.LANE_OWNER.get(lane)
        rel = sorted(board.released_by(m))
        row = {"id": iid, "lane": lane, "owner": owner, "released_by": rel,
               "territory": m["territory"], "priority": m["priority"],
               "territory_busy_with": busy.get(m["territory"]),
               "lane_stale": lane in stale}
        in_reserved = (lane in board.LANE_OWNER and m["territory"] not in busy
                       and owner in rel)
        (reserved_unreachable if in_reserved else other_unreachable).append(row)

    out = {
        "utc": board.utc(),
        "board_root": board.ITEMS,
        "shelf_total": len(shelf),
        "stale_lanes": sorted(stale),
        "heartbeats": {board.LANE_OWNER[l]: list(board.heartbeat_evidence(board.LANE_OWNER[l]))
                       for l in lanes},
        "reachable": len(reach),
        "deps_blocked": deps_blocked,
        "unreachable_reserved": reserved_unreachable,
        "unreachable_other": other_unreachable,
    }
    print(json.dumps(out, indent=2, ensure_ascii=False))
    print("\n--- 判据：不可达 = 就绪、未认领、依赖已满、而上面每个身份都领不到 ---")
    print("shelf=%d  reachable=%d  deps-blocked=%d  UNREACHABLE=%d (其中 reserved 段印出来的 %d)"
          % (len(shelf), len(reach), len(deps_blocked),
             len(reserved_unreachable) + len(other_unreachable),
             len(reserved_unreachable)))
    for row in reserved_unreachable + other_unreachable:
        print("  %-40s lane=%-8s owner=%-6s released_by=%s"
              % (row["id"], row["lane"] or "-", row["owner"] or "-",
                 ",".join(row["released_by"]) or "-"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
