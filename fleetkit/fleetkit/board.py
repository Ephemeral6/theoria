"""The work board: agents claim their own work, no per-item dispatch.

    python -m fleetkit board list                  # what is available / claimed
    python -m fleetkit board claim <worker-id>     # atomically take the top item
    python -m fleetkit board done <id> <worker>    # mark delivered
    python -m fleetkit board release <id> <worker> # give it back (with reason)
    python -m fleetkit board sweep [--dry-run]     # free dead workers' claims

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
    lane: infra         (optional label; see "lanes are worker-side" below)

## Lanes are a worker-side filter, not an item-side reservation (S42)

`--lane X` narrows what a worker may take to items labelled `lane: X`. It can
only ever *narrow*: there is no lane a worker can name that lets it take
something a plain `claim` could not. Every lane-tagged item is therefore listed
by `list` and claimable by a plain `claim`, exactly like an untagged one.

This is a deliberate reversal of an earlier design in which a lane was owned by
a named standing agent and its items were withheld from everybody else. That
design needs a lane→owner map; `FleetConfig.lanes` is a `List[str]` and cannot
express one, and no such map was ever built. The result was a board on which a
`lane:` item appeared in no section of `list` and had no exit. Rather than
grow the config schema for a reservation nobody asked for, the reservation is
gone. If your fleet needs lane ownership, it needs a lane→owner source first.
"""

import os
import re
import sys
import time
import locale

_CONSOLE = locale.getpreferredencoding(False) or "utf-8"

from fleetkit import config as _config

#: The fleet's state root. Overridable so a test -- or a second fleet on
#: the same machine -- can point at its own tree instead of inheriting the
#: one this file happens to sit in.
HERE = os.environ.get("FLEET_HOME") or os.path.dirname(os.path.abspath(__file__))
BOARD = os.path.join(HERE, "board")
ITEMS = os.path.join(BOARD, "items")
CLAIMED = os.path.join(BOARD, "claimed")
DONE = os.path.join(BOARD, "done")
LOG = os.path.join(BOARD, "board.log")
OPS_STATUS = os.path.join(HERE, "ops-status")

# 心跳阈值与判据的唯一出处。**看 mtime，不看 agent 自己写进 json 的 utc**：
# RES-4 已实测那些时间戳全线漂前，一个自称的时刻可以把死会话说成活的，
# 而文件被改写的时刻是机器观察到的事实。
#
# Nothing inside this module calls `heartbeat_age` since S42 removed lane
# ownership. Both names are kept, and said so here rather than left to be
# rediscovered: the unported launching half (`reflex`, `scan`) decides liveness
# with exactly these two, and imports them from a board module by these names.
STALE_MIN = 45

for d in (ITEMS, CLAIMED, DONE):
    os.makedirs(d, exist_ok=True)


def heartbeat_age(agent):
    """距上次心跳的分钟数；从未启动过返回 None。"""
    path = os.path.join(OPS_STATUS, "%s.json" % agent)
    if not os.path.exists(path):
        return None
    return int((time.time() - os.path.getmtime(path)) / 60)


def config_root(start=None):
    """Nearest directory at or above `start` holding `fleet.json`, else None.

    Searched rather than assumed, because the state tree and the repository
    root are deliberately allowed to be different directories: `FLEET_HOME`
    points at the tree (`<root>/.fleet` in the acceptance run) while
    `fleet.json` belongs to the repository. `FLEET_ROOT` overrides the search.
    """
    bases = [start] if start else [os.environ.get("FLEET_ROOT"), HERE,
                                   os.getcwd()]
    for base in bases:
        if not base:
            continue
        d = os.path.abspath(base)
        while True:
            if os.path.exists(os.path.join(d, _config.CONFIG_NAME)):
                return d
            parent = os.path.dirname(d)
            if parent == d:
                break
            d = parent
    return None


def task_prefix(start=None):
    """The scheduled-task name prefix a live worker runs under.

    This is the value `cmd_sweep` matches process names against, and it is
    read from `fleet.json` **at the point of use** -- there is deliberately no
    module-level default. A default here is the trap `KNOWN_TRAPS.md` entry 1
    describes: a prefix that matches nothing makes every worker read as dead,
    the board frees claims that are still being worked, and the reflex layer
    launches replacements on top of live sessions. `config.validate` refuses an
    empty `task_prefix` for exactly this reason, and until S42 this module
    never read config at all -- it shipped `_PREFIX = ""` and the validation
    guarded a copy no code opened.

    Raises `ConfigError` when there is no config to read it from. Not knowing
    is a third answer and the caller has to handle it; `cmd_sweep` refuses to
    sweep rather than treating silence as death.
    """
    root = config_root(start)
    if root is None:
        raise _config.ConfigError(
            "no %s found at or above %s. Worker liveness is decided by "
            "matching scheduled-task names against task_prefix, so without it "
            "this board cannot tell a live worker from a dead one. Run "
            "`python -m fleetkit init --prefix <YourFleet->` in the repository "
            "root, or set FLEET_ROOT to the directory holding %s."
            % (_config.CONFIG_NAME, HERE, _config.CONFIG_NAME))
    return _config.load(root).task_prefix


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
    """Claimable items, best first. `lane` narrows; it never widens.

    Passing `lane=X` restricts the result to items labelled `lane: X` -- it is
    the worker saying what it is willing to take. There is no value of `lane`
    that adds an item a plain `candidates()` would not return, which is what
    makes a self-asserted `--lane` harmless.
    """
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
        # 花真钱的活要监控在条目里显式写 `generic_ok: yes` 才放行——花钱得是
        # 有人拍板，不是某道无关的闸门碰巧还没坏。
        #
        # **这道闸不看 lane**（S42）。它以前写成 `not lane and ...`，也就是说
        # 工人自己在命令行上说一句 `--lane campaign` 就能绕过去；那是把「工人
        # 自报的身份」当成了授权。lane 现在只能收窄，所以这里也不能因为工人
        # 报了个 lane 就放宽。
        if (m.get("spend") == "api"
                and m.get("generic_ok", "").lower() not in ("yes", "true")):
            continue
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
    available = candidates()
    listed = {iid for _p, iid, _f, _m in available}
    print("=== available (可领 %d) ===" % len(available))
    for pri, iid, _f, m in available:
        tag = ("lane:" + m["lane"]) if m.get("lane") else "unlaned"
        print("  p%d  %-28s cell=%-3s territory=%-14s %s"
              % (pri, iid, m["cell"], m["territory"], tag))
    # 每一件 items/ 里的活都必须出现在某一段。**不可领没问题，不可领又不出现
    # 才是问题**：S28 那次板上 11 件、8 件在输出里一个字都没有，看起来就是空板。
    # 所以这里不再逐条列举「已知的排除理由」，而是反过来数：凡是不在 available
    # 里的，都必须被这段说出来，说不出理由就印「原因不明」——那是个 bug 报告，
    # 不是沉默。
    ready = done_ids()
    busy = territories_busy()
    blocked, withheld = [], []
    for f in sorted(os.listdir(ITEMS)):
        if not f.endswith(".md"):
            continue
        iid = item_id(f)
        if iid in listed:
            continue
        m = meta(os.path.join(ITEMS, f))
        pend = [d for d in m["deps"] if d not in ready]
        if pend:
            blocked.append((iid, pend))
        elif m["territory"] in busy:
            withheld.append((iid, "territory %s 正被 %s 占着"
                             % (m["territory"], busy[m["territory"]])))
        elif m.get("spend") == "api":
            withheld.append((iid, "spend: api，条目上没有 generic_ok: yes"))
        else:
            withheld.append((iid, "原因不明——这是 board 的 bug，请报告"))
    if blocked:
        print("=== blocked ===")
        for iid, pend in blocked:
            print("  %-28s waits on %s" % (iid, ",".join(pend)))
    if withheld:
        print("=== withheld（在板上但现在领不走 %d） ===" % len(withheld))
        for iid, why in withheld:
            print("  %-28s %s" % (iid, why))
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
    dst = os.path.join(ITEMS, "%s.md" % iid)
    os.rename(src, dst)
    _revoke_authorisation(dst)
    note("RELEASE %s by %s (%s)" % (iid, worker, reason))
    return 0


def _revoke_authorisation(path):
    """交回板上就撤销授权。

    `generic_ok: yes` 是监控**对某一次认领**签的字（「这个工人、这件事、我批准」），
    不是条目的属性。而认领文件交回时会连同我在上面写的每一行一起变回条目——
    于是一次性的批准变成了永久的批准。2026-07-29 当场发生：我批准了 A3 在飞的
    那一次，工人死后 sweep 把它交回，条目带着我的签字重新对所有人开放。"""
    try:
        text = open(path, encoding="utf-8").read()
    except OSError:
        return
    stripped = re.sub(r"^generic_ok:.*\n", "", text, count=1, flags=re.M)
    if stripped != text:
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(stripped)


def cmd_sweep(dry=False):
    """把死掉的工人还占着的认领交回板上。

    一次性工人被额度或崩溃打断后，claimed/ 里的认领永远挂着：板以为有人在做，
    领地被锁，新工人领不到活。判据保守——只清 W-* 前缀（一次性工人）且其
    计划任务已不在运行的；App/常驻会话（APP-*/RES-*）一律不动，它们的存活
    从任务表看不出来。

    **不知道 != 死了。** 前缀读不到（没有 fleet.json）就拒绝扫，退出 3。
    在 S42 之前这里读的是一个从未被赋值的模块变量 `_PREFIX = ""`，于是存活
    判据恒假、`live` 恒空、每一条 W-* 认领都被判成孤儿——包括正在跑的那些。
    那正是 KNOWN_TRAPS.md 第 1 条，潜伏在 ship 出那份警告的包自己身上。
    """
    import subprocess
    try:
        prefix = task_prefix()
    except _config.ConfigError as exc:
        print("SWEEP-REFUSED 读不到 task_prefix，不扫——分不清死活时释放认领，"
              "就是把还在跑的工人的活抢走。")
        print("SWEEP-REFUSED %s" % exc)
        return 3
    out = subprocess.run(["schtasks", "/Query", "/FO", "CSV", "/NH"],
                         capture_output=True)
    if out.returncode != 0:
        # 查不到任务表也是「不知道」。以前这里没有分支，一个失败的查询会得到
        # 空 stdout，跟「一个工人都没在跑」长得一模一样。
        print("SWEEP-REFUSED schtasks 查询失败（exit %d），不扫。" % out.returncode)
        return 3
    # schtasks is a Windows console tool and emits the console code page, NOT
    # utf-8. Decoding it as utf-8 is how live workers get reported dead.
    text = out.stdout.decode(_CONSOLE, "replace")
    live = set()
    for line in text.splitlines():
        cols = [c.strip('"') for c in line.split('","')]
        if len(cols) >= 3 and prefix in cols[0]:
            name = cols[0].strip('"').lstrip("\\").replace(prefix, "")
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
            dst = os.path.join(ITEMS, "%s.md" % iid)
            os.rename(os.path.join(CLAIMED, f), dst)
            _revoke_authorisation(dst)   # 死掉的工人不该把我的签字留在板上
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
