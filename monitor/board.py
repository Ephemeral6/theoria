"""The work board: agents claim their own work, no per-item dispatch.

    python monitor/board.py list                  # what is available / claimed
    python monitor/board.py claim <worker-id>     # atomically take the top item
    python monitor/board.py done <id> <worker>    # mark delivered
    python monitor/board.py release <id> <worker> # give it back (with reason)
    python monitor/board.py reconcile [--fix]     # delivered work that came back

`reconcile` exists because board state is a set of **tracked files** and every
verb here is an `os.rename`. A merge from a branch based before a `done`
restores `items/<id>.md`, git having no way to see that a file in a *different*
directory means the work is finished — and the item is then handed out again.
E8-ic3-scale was delivered once and re-claimed four times that way. So `done/`
is authoritative: `claim` will not offer a delivered id, `sweep` will not put
one back on the shelf, and `list` prints a RESURRECTED section when it finds
any.

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
import subprocess
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


def heartbeat_evidence(agent):
    """(距上次心跳的分钟数, 证据来源)；从未启动过返回 `(None, "never-started")`。

    S28：旧写法只看 `ops-status/<编号>.json` 的 **mtime**，而那是一个**被 git
    跟踪**的文件——任何 merge / reset / autostash 都能把一个死会话的心跳摸活。
    现场证据：`OPS-R.json` 自报 05:59Z，`heartbeat_age` 返回 12 分钟，
    reflog 显示 10:19:43Z 有一次 reset 摸新了它。

    而这个误差**只朝一个方向走**：年龄偏小 → 主人算活着 → 赛道继续预留、
    领地继续上锁、认领不被交回。所以这里改成优先读
    `ops-status/<编号>.lock`——它未被跟踪且已被 `.gitignore` 忽略
    （根 `.gitignore` 第 24 行），所以 git 碰不到它，是唯一没被污染的信号。
    `standing.py` 的 `occupied()` 早就在用锁新鲜度 + 单调 cycle 这一对判据。

    锁不存在时仍然回落到 json 的 mtime，**但来源会说出来**（`"mtime-touchable"`），
    这样「量到了 3 分钟」和「量到了 3 分钟，但这个数可能是 merge 摸出来的」
    不再是同一个答案。第三个值在这里不是一个数字，是那个数字的出处。
    """
    lock = os.path.join(OPS_STATUS, "%s.lock" % agent)
    if os.path.exists(lock):
        return int((time.time() - os.path.getmtime(lock)) / 60), "lock"
    path = os.path.join(OPS_STATUS, "%s.json" % agent)
    if not os.path.exists(path):
        return None, "never-started"
    return int((time.time() - os.path.getmtime(path)) / 60), "mtime-touchable"


def heartbeat_age(agent):
    """距上次心跳的分钟数；从未启动过返回 None。

    薄封装，保持原有契约（调用方遍布 board / scan / standing）。
    要知道这个数可不可信，用 `heartbeat_evidence()`。
    """
    return heartbeat_evidence(agent)[0]


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
        # S28（顺带抓到的）：`\s*` 跨行，所以一个**空**的 `lane:` 会把下一行的第一个
        # 非空白 token 吃进来当值——实测 `lane:` 后面跟着标题行时解析出 `"#"`。
        # 于是一个写坏了的字段静默变成一个**看起来合理**的值，正是本条目的病症：
        # 「没写」和「写了这个」编码成同一个东西。`[^\S\n]*` 只吃行内空白。
        m = re.search(r"^%s:[^\S\n]*(\S+)" % key, head, re.M)
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


def delivered_map():
    """``{id: deliverer}`` for everything in ``done/``.

    ``done_ids()`` already existed and was used for **one** thing: resolving
    another item's ``deps``. Nothing ever asked whether *this* item was already
    delivered, which is the gap S34 is about.
    """
    out = {}
    for f in sorted(os.listdir(DONE)):
        if not f.endswith(".md"):
            continue
        parts = f[:-3].split(".")
        out.setdefault(parts[0], parts[1] if len(parts) >= 2 else "?")
    return out


def resurrected():
    """Ids that are in ``done/`` **and** back on the shelf or under claim.

    Board state is a set of **tracked files**, and all three of this module's
    verbs are `os.rename`. Nothing here is wrong on its own. What goes wrong is
    the interaction with git: a merge from a branch whose base predates the
    `done` sees "a file the other side has and I do not" and restores
    `items/<id>.md`. It cannot see "this work is finished" -- that fact lives in
    a *different* directory, and a three-way merge has no rule relating them.

    Measured on 2026-07-29: `E8-ic3-scale` was delivered by W-1660 at 12:16:28Z
    and then claimed **four more times** (W-1671 at 15:08, an accidental
    `--help` at 15:54, W-130 at 15:59), swept back to the shelf after each, and
    at the time this was written it sat in `items/`, `claimed/` and `done/`
    simultaneously. `A13-sealed-audit-reads-the-wrong-fields` was in `claimed/`
    and `done/` at once. Nothing errored, nothing printed a warning, and
    `list` showed the item as ordinary available work: every one of those
    workers spent a launch and a context redoing something already on a branch.

    Returns ``{id: {"deliverer": w, "in_items": bool, "claimed_by": [w, ...]}}``.

    ``claimed_by`` is a **list**, not one worker, and that is not tidiness.
    ``claimed_map()`` is keyed on the id, so with two claim files for one id it
    keeps whichever ``os.listdir`` returned last -- and `reconcile --fix` would
    then remove one, report success and return 0 with the other still sitting
    there. A repair tool whose exit code says "clean" over residue it left is
    this lane's own disease, and it was found by the tests for this very fix.
    Two claims on one id is also not the rare case: it is a *more* resurrected
    board, since each resurrection is another chance for someone to claim.
    """
    delivered = delivered_map()
    shelf = {item_id(f) for f in os.listdir(ITEMS) if f.endswith(".md")}
    claims = {}
    for f in sorted(os.listdir(CLAIMED)):
        if not f.endswith(".md"):
            continue
        parts = f[:-3].split(".")
        if len(parts) >= 2:
            claims.setdefault(parts[0], []).append(parts[1])
    out = {}
    for iid, deliverer in delivered.items():
        in_items = iid in shelf
        by = claims.get(iid, [])
        if in_items or by:
            out[iid] = {"deliverer": deliverer, "in_items": in_items,
                        "claimed_by": by}
    return out


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
        # Already delivered. `ready` was read three lines up and used only to
        # resolve *other* items' deps -- the same set, never asked about the
        # item in front of it. An id on the shelf with a `done/` record is not
        # available work, it is a merge artefact, and offering it costs a whole
        # session. This is a hard skip and `cmd_claim` prints what it skipped:
        # a silently withheld item is the trap this board already fell into
        # once (board-empty-is-misleading).
        if iid in ready:
            continue
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


def withheld_items(shown_ids):
    """就绪、没人认领、却在 `list` 的任何分区里都不出现的条目 —— 连原因一起。

    S28：`list` 印 available / reserved / blocked / claimed 四段，而领地互斥
    （`candidates()` 里的 `if m["territory"] in busy: continue`）把条目从**每一段
    里都抹掉**。于是板读起来是「人人有活干」，而不是「卡住了」。
    实测（2026-07-29，真板）：`items/` 里 11 件，`list` 一件都不提的有 **8 件**，
    而它印的是 `available: 1`。

    赛道无主是第二类隐身：`reserved` 那段只遍历 `LANE_OWNER` 的键，
    所以一条**没有常驻研究员**的赛道上的活，两段都进不去。

    做法是**集合差**而不是逐条枚举原因：先拿到已经印出去的 id，剩下的就是被
    withheld 的，再去诊断为什么。这样将来 `candidates()` 多加一条排除规则，
    这段不会跟着漏——只会诊断成 `原因不明`，而那本身就是一句要报的话。
    """
    busy = territories_busy()
    stale = stale_lanes()
    ready = done_ids()
    claimed = set(claimed_map())
    out = []
    for f in sorted(os.listdir(ITEMS)):
        if not f.endswith(".md"):
            continue
        iid = item_id(f)
        if iid in shown_ids or iid in claimed or iid in ready:
            continue
        m = meta(os.path.join(ITEMS, f))
        if [d for d in m["deps"] if d not in ready]:
            continue                    # `blocked` 那段已经报过了
        lane = m.get("lane") or ""
        if m["territory"] in busy:
            why = "领地 %s 被 %s 占着" % (m["territory"], busy[m["territory"]])
        elif lane and lane not in LANE_OWNER:
            why = "赛道 %s 没有常驻研究员" % lane
        elif (m.get("spend") == "api"
              and m.get("generic_ok", "").lower() not in ("yes", "true")):
            why = "花 API 钱，缺监控的 generic_ok 签字"
        elif lane and lane not in stale:
            why = "赛道 %s 有主（%s），等其研究员来领" % (lane, LANE_OWNER[lane])
        else:
            why = "原因不明 —— 排除规则变了而这段没跟上"
        out.append((m["priority"], iid, m["territory"], why))
    return sorted(out)


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
            age, source = heartbeat_evidence(owner)
            # 心跳年龄的**出处**跟年龄一起印。只有锁是 git 碰不到的；
            # 回落到被跟踪文件的 mtime 时，这个数可能是一次 merge 摸出来的，
            # 而误差方向恰好是「主人还活着，这件活继续给他留着」。
            if age is None:
                hb = "未启动"
            elif source == "lock":
                hb = "%d分钟前" % age
            else:
                hb = "%d分钟前(mtime，可被 merge 摸新)" % age
            print("  p%d  %-28s lane=%-8s owner=%s(%s) territory=%s"
                  % (pri, iid, lane, owner, hb, m["territory"]))
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
    # 第五段。就绪但在上面每一段里都不出现的条目——不印它们，
    # 「板上没活」与「活都被挡住了」就是同一个画面。
    shown = generic_ids | {iid for _p, iid, _l, _o, _m in reserved}
    shown |= {iid for iid, _pend in blocked}
    hidden = withheld_items(shown)
    if hidden:
        print("=== territory-blocked (%d) ===" % len(hidden))
        for pri, iid, territory, why in hidden:
            print("  p%d  %-28s territory=%-14s %s" % (pri, iid, territory, why))
    cm = claimed_map()
    if cm:
        print("=== claimed ===")
        for iid, worker in sorted(cm.items()):
            print("  %-28s by %s" % (iid, worker))
    # Before `done`, not after. The done list is 116 lines long and this is the
    # section a reader has to not scroll past.
    _warn_resurrected()
    if os.listdir(DONE):
        print("=== done (%d) ===" % len(os.listdir(DONE)))
        for f in sorted(os.listdir(DONE)):
            print("  " + f[:-3])


HOLD_CAP = 3        # 常驻研究员同时持有的上限；一次性工人自然只拿一件


def held_by(worker):
    return sum(1 for f in os.listdir(CLAIMED)
               if f.endswith(".md") and f[:-3].split(".")[1] == worker)


REPO = os.path.dirname(HERE)


def _git(repo, *args):
    """Run one read-only git command. Returns lines, or [] on any trouble.

    Never raises and never propagates a non-zero exit. Everything below this
    is advisory: a claim that failed because git was slow, missing, or in a
    funny state would be a much worse bug than the one being fixed.
    """
    try:
        out = subprocess.run(("git",) + args, cwd=repo,
                             stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                             timeout=15)
    except Exception:
        return []
    if out.returncode != 0:
        return []
    return out.stdout.decode("utf-8", "replace").splitlines()


def prior_work(iid, repo=None):
    """Lines warning that somebody may already have worked this item.

    2026-07-29: S21 was done twice and S27 three times, by concurrent sessions
    that each found a clean-looking item and started over. Both times the
    evidence was already sitting in plain sight -- a branch named after the
    item -- and nothing looked. One `git branch` is cheaper than a session.

    Worktree directories are checked as well as branches, because the third
    S27 copy was an **untracked** file inside a worktree: no branch, no commit,
    nothing for a ref-based check to find, but the directory name was there.
    """
    repo = repo or REPO
    slug = iid.lower()
    seen, hits = set(), []
    for line in _git(repo, "branch", "-a", "--list", "*%s*" % slug):
        name = line.strip().lstrip("*+ ").strip()
        if not name or "->" in name:            # skip the origin/HEAD alias
            continue
        short = name.split("remotes/origin/", 1)[-1]
        if short in seen:                       # local and remote are one branch
            continue
        seen.add(short)
        count = _git(repo, "rev-list", "--count", "master..%s" % name)
        ahead = count[0].strip() if count else "?"
        if ahead == "0":
            # Nothing ahead of master means it is already merged, which is a
            # different piece of news: not "someone is working on this" but
            # "this is very likely already done". S21 read exactly like this
            # an hour after it was delivered.
            hits.append("  分支 %s（领先 master 0 个提交 —— **已并入，这件活很可能已经完成**）"
                        % short)
        else:
            hits.append("  分支 %s（领先 master %s 个提交）" % (short, ahead))
    wt = os.path.join(repo, ".worktrees")
    for d in sorted(os.listdir(wt)) if os.path.isdir(wt) else []:
        if slug in d.lower():
            hits.append("  工作树 .worktrees/%s（可能有未提交、甚至未跟踪的半成品）" % d)
    if not hits:
        return []
    # ASCII and Chinese only: this console is cp936, and U+26A0 (the obvious
    # choice of warning glyph) is not in it. Printing one would raise
    # UnicodeEncodeError *after* the item was already renamed into claimed/ --
    # the agent would see a traceback and no item, while the board recorded a
    # successful claim. Same locale that once reported eight live workers dead.
    return (["", "注意：这件活可能已经有人做过或正在做："] + hits
            + ["  先看它再决定**重做还是接续**。重做前请说明为什么不接续——",
               "  半成品被静默丢弃过一次，代价是同一件事做了两遍。"])


def cmd_claim(worker, lane=None):
    # `--lane` 是**认领者自报的**，而带赛道的查询会跳过花钱守卫与预留守卫。
    # 于是 `claim W-9999 --lane campaign` 能领走一件在真 API 上打的战役，
    # 退出 0，board.log 记下的那行与一次被批准的花钱认领逐字不可区分
    # （2026-07-29 对抗性普查抓到）。自报一个身份不该等于拥有它。
    if lane and LANE_OWNER.get(lane) not in (None, worker):
        if lane not in stale_lanes():
            print("LANE-NOT-YOURS %s 属于 %s；它停摆时才对其他人开放。"
                  % (lane, LANE_OWNER.get(lane)))
            return 3
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
        except FileNotFoundError:
            # S28：这里原来是裸 `except OSError: continue`。**唯一预期的竞态是
            # 另一个工人抢先把条目 rename 走了**，那正是 FileNotFoundError；
            # 其余 OSError 全都被顺手吞掉，然后这个循环走完、印出 BOARD-EMPTY
            # ——而工人被告知那意味着「收尾退出」。异常被丢弃，`note()` 只在
            # 成功路径调用，所以一次假的 BOARD-EMPTY 在 board.log 里零痕迹。
            # 触发条件比看上去常见：监控自身持续在 open 这些文件，
            # 而 Windows 的 WinError 32（文件被占用）是 OSError 的子类。
            # 对照组是 `cmd_done` / `cmd_release`——同一个 rename，它们完全不捕获。
            continue
        note("CLAIM %s by %s" % (iid, worker))
        print("---8<--- item %s ---8<---" % iid)
        sys.stdout.write(open(dst, encoding="utf-8").read())
        # Last, deliberately. The item body is long and this is the one line
        # that has to survive being skimmed.
        for line in prior_work(iid):
            print(line)
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
    _warn_resurrected()
    return 3


def _warn_resurrected():
    """Print delivered ids that are back on the shelf, if any.

    Deliberately printed on the *empty* path as well as by `list`. A worker
    that gets BOARD-EMPTY while three finished items sit in `items/` is looking
    at a board that is lying to it in the reassuring direction, and it is the
    one party with a reason to say so.
    """
    res = resurrected()
    if not res:
        return
    print("RESURRECTED %d 件已交付却又回到板上（跑 `board.py reconcile --fix`）："
          % len(res))
    for iid, st in sorted(res.items()):
        where = []
        if st["in_items"]:
            where.append("items/")
        for by in st["claimed_by"]:
            where.append("claimed/ by %s" % by)
        print("  %-32s done by %-8s 现在还在 %s"
              % (iid, st["deliverer"], " + ".join(where)))


def cmd_reconcile(fix=False):
    """Report -- or with ``--fix``, resolve -- ids that are in two places at once.

    `done/` is authoritative. That is not a preference, it is the only choice
    that is safe in both directions: treating the shelf as authoritative would
    re-open finished work, while treating `done/` as authoritative can at worst
    discard a claim on work that is already delivered.

    Default is report-only. A board-repair tool that mutates by default is one
    nobody runs on a board they care about, and this one has to be runnable
    after every merge.
    """
    res = resurrected()
    if not res:
        print("RECONCILE-CLEAN 三个目录没有交集")
        return 0
    print("%d 件已交付却仍在板上：" % len(res))
    removed = 0
    for iid, st in sorted(res.items()):
        targets = []
        if st["in_items"]:
            targets.append(os.path.join(ITEMS, "%s.md" % iid))
        for by in st["claimed_by"]:
            targets.append(os.path.join(CLAIMED, "%s.%s.md" % (iid, by)))
        for path in targets:
            rel = os.path.relpath(path, BOARD).replace("\\", "/")
            if not fix:
                print("  would remove %-52s (done by %s)" % (rel, st["deliverer"]))
                continue
            os.remove(path)
            removed += 1
            print("  removed      %-52s (done by %s)" % (rel, st["deliverer"]))
            note("RECONCILE %s removed %s (already delivered by %s)"
                 % (iid, rel, st["deliverer"]))
    if not fix:
        print("报告模式，什么也没动。加 --fix 才执行。")
        return 1
    print("清掉 %d 个残留。done/ 是权威。" % removed)
    return 0


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
        # Sweep is the second way a delivered item gets back onto the shelf,
        # and the more damaging one, because it looks like housekeeping. The
        # claim it is releasing is itself a merge artefact -- E8-ic3-scale was
        # swept back to `items/` three separate times *after* W-1660 delivered
        # it, and each sweep looked exactly like the honest ones around it.
        # Freeing an orphaned claim is right; re-offering finished work is not.
        if iid in done_ids():
            kept.append((iid, worker, "已交付（done/ 里有记录）——不放回货架，"
                                      "跑 `board.py reconcile --fix` 清掉这条认领"))
            continue
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
    if a[0] == "reconcile":
        return cmd_reconcile(fix="--fix" in a)
    print(__doc__)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
