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
           "spend": "", "generic_ok": "", RELEASED_BY: ""}
    for key in ("priority", "cell", "territory", "lane", "spend", "generic_ok"):
        m = re.search(r"^%s:\s*(\S+)" % key, head, re.M)
        if m:
            out[key] = int(m.group(1)) if key == "priority" else m.group(1)
    # To end of line, not `\S+`: this one is a comma-separated list, and the
    # single-token pattern would silently keep only the first releaser --
    # re-offering the item to everyone after them.
    m = re.search(r"^%s:\s*(.+)$" % RELEASED_BY, head, re.M)
    if m:
        out[RELEASED_BY] = m.group(1).strip()
    m = re.search(r"^deps:\s*(.+)$", head, re.M)
    if m:
        out["deps"] = [d.strip() for d in m.group(1).split(",")
                       if d.strip() and d.strip().lower() != "none"]
    return out



def released_by(m):
    """Workers who have handed this item back, from its front matter."""
    raw = (m or {}).get(RELEASED_BY) or ""
    return {w.strip() for w in raw.replace(",", " ").split() if w.strip()}


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
    withheld = []
    for _pri, iid, fname, _m in candidates(lane):
        if worker in released_by(_m):
            # You already decided you cannot do this one. Re-offering it costs
            # a whole session's context to re-derive the same conclusion, and
            # the log fills with claims and releases while nothing moves.
            # Anyone else may still take it -- one agent's refusal is about
            # that agent, not about the item.
            withheld.append(iid)
            continue
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
    if withheld:
        # Never a bare BOARD-EMPTY when something was hidden. Silently
        # withholding work is the trap this board already fell into once
        # (board-empty-is-misleading): "nothing to do" and "nothing I will
        # show you" have to look different, or the next reader debugs the
        # wrong thing.
        print("BOARD-EMPTY（%d 件被扣下：你自己交回过 —— %s。别人仍可领）"
              % (len(withheld), ", ".join(sorted(withheld)[:6])))
    else:
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
    _record_release(dst, worker, reason)
    note("RELEASE %s by %s (%s)" % (iid, worker, reason))
    return 0


#: Front-matter key listing everyone who has handed this item back.
RELEASED_BY = "released_by"


def _record_release(path, worker, reason):
    """Write the releaser into the item's front matter.

    Until now `release` only wrote a log line, and `claim` re-offered the item
    to the same agent on its next pass -- 11 seconds later, in the case that
    prompted this. Each round costs a session a fresh read of the context to
    reach the conclusion the last round already reached, and the log shows
    claims and releases ticking over as if work were happening.

    That is a livelock, not a deadlock, and it fails in the reassuring
    direction: the board looks busy and progress is zero. It was not one
    agent's mistake either -- C9 and A4-ablation-online were each handed back
    by two different workers -- so the board is what changes, not the people.
    """
    try:
        text = open(path, encoding="utf-8").read()
    except OSError:
        return
    m = re.search(r"^%s:\s*(.+)$" % RELEASED_BY, text, re.M)
    prior = [w.strip() for w in m.group(1).split(",") if w.strip()] if m else []
    if worker not in prior:
        prior.append(worker)
    line = "%s: %s" % (RELEASED_BY, ", ".join(prior))
    if m:
        text = text[:m.start()] + line + text[m.end():]
    else:
        # Front matter is the run of `key: value` lines at the top; append to
        # the end of it rather than to the file, so `meta()` still sees it.
        lines = text.split("\n")
        cut = 0
        for i, l in enumerate(lines):
            if re.match(r"^\w+:\s", l):
                cut = i + 1
            elif l.strip() == "":
                break
        lines.insert(cut, line)
        text = "\n".join(lines)
    # The reason belongs with it: a later reader has to be able to tell
    # "I could not do this" from "I ran out of time".
    stamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    text = text.rstrip("\n") + "\n\n> **%s 于 %s 交回**：%s\n" % (
        worker, stamp, reason)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


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


#: Derived from STALE_MIN rather than restated. A second copy of "how long is
#: too long" is a number that drifts from the first one, and this file already
#: says why it reads mtime instead of self-reported time -- the same argument
#: applies to keeping one threshold instead of two.
#:
#: Two full cycles, because one cycle of silence has an innocent reading: the
#: session is inside a long sub-step. Two does not.
STANDING_CYCLE_MIN = STALE_MIN
STANDING_DEAD_MIN = STALE_MIN * 2


def standing_verdict(agent, now=None):
    """Is this standing session dead? Returns (dead: bool, why: str).

    Three conditions, and **all three** must hold -- and unlike the first
    version of this function, all three are now actually implemented. Each
    alone has an innocent reading, which is exactly why the original sweep
    refused to touch standing sessions at all:

      * heartbeat older than two cycles -- but a session deep in one long task
        legitimately goes quiet for a while;
      * an `URGENT` file still sitting unread -- but it may have been dropped
        seconds ago;
      * no bus traffic since the heartbeat -- but a session can work without
        saying anything.

    Together they are not innocent: a live session re-reads its bus every cycle,
    and `URGENT` is the one thing it is contractually required to notice
    between sub-steps. Silence on all three for twice its own period means
    nobody is reading.

    The cost of getting this wrong is asymmetric and that decides the design.
    Freeing a live session's claim makes two agents write one territory --
    which is the failure the board exists to prevent. Leaving a dead one costs
    a locked territory until someone looks. So every uncertainty resolves to
    "alive": an unreadable heartbeat, a missing bus directory, a clock that
    makes no sense -- all keep the claim.
    """
    now = now or time.time()
    hb = os.path.join(OPS_STATUS, "%s.json" % agent)
    if not os.path.exists(hb):
        return False, "no heartbeat file at all -- never started, not died"
    try:
        hb_mtime = os.path.getmtime(hb)
        age_min = (now - hb_mtime) / 60.0
    except OSError as exc:
        return False, "heartbeat unreadable (%s); refusing to guess" % exc
    if age_min < STANDING_DEAD_MIN:
        return False, ("heartbeat %.0f min old, under the %d-min bar"
                       % (age_min, STANDING_DEAD_MIN))

    urgent = os.path.join(HERE, "bus", agent, "URGENT")
    if not os.path.exists(urgent):
        # No interrupt was pending, so silence proves much less: the session
        # was never asked to prove it was reading.
        return False, ("heartbeat %.0f min old but no URGENT was pending -- "
                       "silence alone is not death" % age_min)
    try:
        urgent_age = (now - os.path.getmtime(urgent)) / 60.0
    except OSError:
        return False, "URGENT unreadable; refusing to guess"
    if urgent_age < STANDING_CYCLE_MIN:
        return False, ("URGENT is only %.0f min old -- not yet one cycle, it "
                       "may simply not have come round" % urgent_age)

    # The third condition, and the only *positive* evidence in the whole test.
    # The other two are silences, and a silence is the absence of proof rather
    # than proof of absence. Traffic on the outbound bus after the heartbeat is
    # the session demonstrably doing something, so it overrides both.
    #
    # It was described in three places -- the commit message, this function's
    # own docstring, and reflex.py's comment -- and implemented in none. Ten
    # tests encoded the two-signal behaviour, so nothing could have caught the
    # divergence: the tests agreed with the code against the documentation.
    #
    # It is not academic. At 18:52:20Z a claim was released 48 minutes after
    # RES-3 wrote to its out.jsonl at 18:04:28Z, and the holder objected on the
    # spot. This condition would have refused that release.
    #
    # Wired as a *refusal only*: it can keep a claim, never free one. That
    # makes it impossible for this change to cause a wrongful release, which is
    # the only failure here that costs anything irreversible.
    out = os.path.join(HERE, "bus", agent, "out.jsonl")
    try:
        if os.path.exists(out) and os.path.getmtime(out) > hb_mtime:
            spoke_min = (now - os.path.getmtime(out)) / 60.0
            return False, ("bus out.jsonl was written %.0f min ago, after the "
                           "heartbeat -- the session was demonstrably alive "
                           "more recently than its own heartbeat says"
                           % spoke_min)
    except OSError:
        # Unreadable is not evidence of death; fall through to the two silences
        # only if they already convicted, which they have by this point.
        pass

    return True, ("heartbeat %.0f min old (>%d), an URGENT posted %.0f min ago "
                  "(>%d) is still unread, and no bus traffic since the heartbeat"
                  % (age_min, STANDING_DEAD_MIN, urgent_age, STANDING_CYCLE_MIN))


#: Appended to an item whose standing holder died. Written because the human
#: doing this by hand on 2026-07-29 wrote it by hand every time.
INHERIT_NOTE = """
> **前任持有者 %s 于 %s 判定死亡**（%s）。
> **分支上可能有半成品**：接手前先看 `git branch -r --list 'origin/agent/%s*'`
> 与该领地的 `runs/`，再决定是重做还是接续。重做前请说明为什么不接续——
> 半成品被静默丢弃过一次，代价是同一件事做了两遍。
"""


def cmd_sweep(dry=False, include_standing=False):
    """把死掉的工人还占着的认领交回板上。

    一次性工人被额度或崩溃打断后，claimed/ 里的认领永远挂着：板以为有人在做，
    领地被锁，新工人领不到活。判据保守——只清 W-* 前缀（一次性工人）且其
    计划任务已不在运行的。

    **App/常驻会话（APP-*/RES-*）默认仍然不动**，但 `--include-standing` 下
    改由 `standing_verdict()` 判定：心跳陈旧 + URGENT 悬而未答 + 心跳之后没有
    总线流量，三条同时成立才释放。这段话原本写着「一律不动」，而 S21 已经加了
    那个模式——**文档比代码旧了一轮**，正是本函数所属那一类问题的元层版本，
    所以在此对齐而不是留着。"""
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
    freed, kept = [], []
    for f in sorted(os.listdir(CLAIMED)):
        if not f.endswith(".md"):
            continue
        iid, worker = f[:-3].split(".")[0], f[:-3].split(".")[1]
        standing = worker.startswith(("RES-", "APP-", "OPS-"))
        if standing:
            if not include_standing:
                continue
            dead, why = standing_verdict(worker)
            if not dead:
                kept.append((iid, worker, why))
                continue
        elif not worker.startswith("W-") or worker in live:
            continue
        else:
            why = "scheduled task is no longer running"
        freed.append((iid, worker, why))
        if not dry:
            dst = os.path.join(ITEMS, "%s.md" % iid)
            os.rename(os.path.join(CLAIMED, f), dst)
            _revoke_authorisation(dst)   # 死掉的工人不该把我的签字留在板上
            if standing:
                # The item carries the news. A released claim otherwise looks
                # identical to one nobody ever took, and the next holder
                # cheerfully redoes work that is already sitting on a branch.
                stamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                with open(dst, "a", encoding="utf-8", newline="\n") as fh:
                    fh.write(INHERIT_NOTE % (worker, stamp, why, iid.lower()))
            note("SWEEP %s released (%s %s: %s)"
                 % (iid, "standing" if standing else "worker", worker, why))
    if not freed:
        print("no orphaned claims")
    for iid, worker, why in freed:
        print("%-28s freed from %-8s %s" % (iid, worker, why))
    # Kept standing claims are printed too. The whole reason this mode did not
    # exist is fear of killing a live session, so the refusals are the part a
    # reader needs to see to believe the releases.
    for iid, worker, why in kept:
        print("%-28s KEPT   %-8s %s" % (iid, worker, why))
    return 0


def main():
    a = sys.argv[1:]
    if not a or a[0] == "list":
        cmd_list(); return 0
    if a[0] == "claim":
        lane = a[3] if len(a) > 3 and a[2] == "--lane" else None
        return cmd_claim(a[1], lane)
    if a[0] == "sweep":
        return cmd_sweep("--dry-run" in a,
                         include_standing="--include-standing" in a)
    if a[0] == "done":
        return cmd_done(a[1], a[2])
    if a[0] == "release":
        return cmd_release(a[1], a[2], " ".join(a[3:]) or "unstated")
    print(__doc__)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
