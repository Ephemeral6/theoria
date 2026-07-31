"""5-hour usage-window circuit breaker for the fleet.

    python monitor/quota.py check     # classify dead sessions, set mode
    python monitor/quota.py ping      # cheapest possible window-health test
    python monitor/quota.py resume    # staggered priority relaunch after reset

Design (monitor-owned, user delegated 2026-07-28):

DETECT   A dispatched session that died without pushing its branch is examined
         for quota signatures in its dispatch log. This is ops-layer forensics
         (the isolation contract's explicit exception): we extract ONLY the
         matched limit line, never the session's work.

HOLD     Any quota kill flips monitor/quota_state.json to mode=hold with a
         requeue list. In hold: no new dispatches, running sessions are left
         alone (they own their fate), monitor heartbeats go minimal.

RESUME   When `ping` succeeds (one cheap haiku call), relaunch the requeue in
         priority order with 90s stagger and a halved pool, scaling back to
         normal once the first relaunched session survives 10 minutes. The
         write-as-you-go runs/ rule is what makes relaunch cheap: a restarted
         session finds its predecessor's intermediates on disk.
"""

import datetime
import json
import os
import re
import subprocess
import sys
import time
import childio  # noqa: E402  (per-child decoding, see its docstring)
import dispatch  # noqa: E402  (one pid_alive for the whole rig, not two)

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
LOGS = os.path.join(HERE, "dispatch-logs")
STATE = os.path.join(HERE, "quota_state.json")

SIGNATURES = [
    # observed verbatim 2026-07-28: "You've hit your session limit · resets 8:20pm"
    r"session limit", r"Session limit", r"hit your .*limit", r"resets \d",
    r"usage limit", r"Usage limit", r"limit will reset", r"rate.?limit",
    r"overloaded", r"Overloaded", r"credit balance", r"quota",
    r"429", r"insufficient.*credits",
]
SIG_RE = re.compile("|".join(SIGNATURES))

# 日志扫描专用的**强**签名（2026-07-29 加）。
#
# 上面那份弱签名表是给注册簿那条路用的：那条路先确认进程已死、分支没推，
# 才去读它的最后几行，所以宽一点不会误伤。日志普扫没有那层前置条件，
# 用同一份表就会把 agent **讨论**限额的散文当成限额本身——裸 `quota` 甚至
# 匹配得上命令行里的 `quota.py`，于是每个跑过配额检查的工人都在给自己制造证据。
#
# 实测后果：`quota_state.json` 的 reset_hint 里存着的，是一句**否认**限额的话
# （"chronologically impossible … the monitor already retracted this"），
# 而舰队据此被冻。释放之后下一次心跳又会从同一行日志里重新检出，无限自锁。
#
# 方向是不对称的，所以判据往「不冻」偏：漏判一次真限额，代价是一次派单失败并
# 立刻在日志里留下真签名；误判一次，代价是整支舰队停摆到下次人工介入。
HARD_SIGNATURES = [
    r"You've hit your (session|usage) limit",
    r"(session|usage) limit\b.{0,40}resets?\s+\d",
    r"Claude usage limit reached",
    r"\"type\":\s*\"rate_limit_error\"",
    r"credit balance is too low",
    r"insufficient\s+credits",
]
HARD_RE = re.compile("|".join(HARD_SIGNATURES))

# 一行里出现这些，说明它是**关于**限额的文字，不是限额本身。
PROSE_MARKS = ("**", "`", "quota.py", "quota_state", "monitor/",
               "retract", "撤回", "误判", "假阳")

# Relaunch order when the window reopens: integration gate first, critical
# path second, cheap probes, then the rest; standing services last.
PRIORITY = ["M-0", "P-8", "P-20", "P-18", "P-19", "P-9", "P-12", "P-13",
            "P-15", "P-17", "R-1", "A-1", "B-1"]

# A hold has to be able to end without anything going right.
#
# `resume` is one exit, and it asks the window a question: it only opens if
# `ping` succeeds.  That makes it an exit which the outage itself can hold
# shut -- and worse, one that can be shut by something unrelated, since `ping`
# needs the `claude` CLI on PATH and raises without it.  A hold that began at
# 09:35 outlived its own stated 20:20 reset for exactly this reason.
#
# The reset hint already carries the answer: the provider says when the window
# reopens.  So the deadline is the second exit, and it is the one that cannot
# be blocked by the outage it is waiting on.  When the hint carries no readable
# time, MAX_HOLD_HOURS bounds the hold anyway -- an unparsable hint is not a
# reason to stay held forever.
#
# The cap binds a *parsed* deadline too, and deliberately: the window this
# breaker exists for is five hours (see the module docstring), so a hint that
# reads as further out than six has more likely been misread than not.  Erring
# short is the cheap direction -- if the window really is still shut, the next
# dispatch dies on the limit and `check` simply holds again.
MAX_HOLD_HOURS = 6

# The exit costs money, and it costs it during an outage.
#
# `ping` is one real `claude -p --model haiku` call. The reflex tick is every
# five minutes and, once the auto-exit was wired in, it pinged on *every* tick
# while held -- so the breaker spent the very quota it was waiting to get back,
# twelve times an hour, for as long as the window stayed shut. Today's hold ran
# 09:35 to 12:45: ~37 calls where the work order allowed 9.
#
# Twenty minutes is the work order's number and it is a reasonable one: the
# window it is watching is five hours long (see the module docstring), so
# checking three times an hour costs at most a few minutes of lateness against
# a multi-hour wait. The deadline exit in `check` is what actually ends a
# normal hold; this ping is the second opinion, and a second opinion does not
# need to be continuous.
MIN_PING_INTERVAL_MIN = 20

# "resets 8:20pm (Asia/Shanghai)" / "resets 8pm" / "will reset at 20:20 (UTC)"
RESET_RE = re.compile(r"reset(?:s|\s+at)?\s+(\d{1,2})(?::(\d{2}))?\s*"
                      r"([ap]\.?m\.?)?(?:\s*\(([^)]+)\))?", re.I)


def parse_stamp(text):
    """Our own `now_utc()` spelling, tolerating the minute-only variant."""
    for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%MZ"):
        try:
            return datetime.datetime.strptime(text, fmt).replace(
                tzinfo=datetime.timezone.utc)
        except (ValueError, TypeError):
            continue
    return None


def reopen_at(st):
    """When the window is expected to reopen, in UTC. None if unknowable.

    Read off the provider's own words rather than assumed, so the wait is as
    long as the outage says it is and not one tick longer.
    """
    detected = parse_stamp(st.get("detected_at"))
    if detected is None:
        return None
    cap = detected + datetime.timedelta(hours=MAX_HOLD_HOURS)
    match = RESET_RE.search(st.get("reset_hint") or "")
    if not match:
        return cap
    hour, minute, meridiem, zone = match.groups()
    hour, minute = int(hour), int(minute or 0)
    meridiem = (meridiem or "").replace(".", "").lower()
    if meridiem == "pm" and hour != 12:
        hour += 12
    elif meridiem == "am" and hour == 12:
        hour = 0
    if not 0 <= hour <= 23:
        return cap
    try:
        from zoneinfo import ZoneInfo
        tz = ZoneInfo(zone.strip()) if zone else datetime.timezone.utc
    except Exception:
        # An unrecognised zone would put the deadline anywhere; the cap is the
        # honest answer, not a guess at what the provider meant.
        return cap
    local = detected.astimezone(tz)
    when = local.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if when <= local:                      # the hint means the next such time
        when += datetime.timedelta(days=1)
    return min(when.astimezone(datetime.timezone.utc), cap)


def now_utc():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load(path, default):
    if os.path.exists(path):
        return json.load(open(path, encoding="utf-8"))
    return default


def save_state(st):
    json.dump(st, open(STATE, "w", encoding="utf-8"), indent=2)


def pid_alive(pidnum):
    # 与 `dispatch.pid_alive` 同源，包括它那条 pid<=0 的守卫——理由写在那边。
    # 两份实现会漂移，而这一份漂移的后果是配额分类把死会话读成活的，
    # 于是限额签名永远不会被归因到任何一个会话上。
    return dispatch.pid_alive(pidnum)


def branch_pushed(pid_str):
    slug = "agent/" + pid_str.lower().replace("-", "")
    out = subprocess.run(["git", "branch", "-r", "--format=%(refname:short)"],
                         cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace").stdout
    return any(slug in b for b in out.splitlines())


def quota_line(log_name):
    """Return the matched limit line only — never the session's work."""
    path = os.path.join(LOGS, log_name)
    if not os.path.exists(path):
        return None
    # **和日志普扫用同一把尺子。** 这里原来用宽签名表 `SIG_RE`，理由是
    # 「先确认进程已死才读日志，所以宽一点不会误伤」——那个理由今天失效了：
    # `pid_alive(0)` 恒真的缺陷一修，大量此前被当成「还活着」的会话第一次
    # 走到这条路上来，于是一份**讨论**限额的审计报告（正文里有 `quota`、
    # `rate limit` 这些词）被读成了撞上限额，OPS-A 当场被判死。
    # 一个补丁把下一个缺陷放了出来——这正是今晚普查的第二层结论。
    for raw in open(path, encoding="utf-8", errors="ignore"):
        line = raw.strip()
        if not line or len(line) > 300:
            continue
        if any(mark in line for mark in PROSE_MARKS):
            continue
        if HARD_RE.search(line):
            return line[:200]
    return None


def _released_ts(st):
    """上一次出闩的时刻（epoch）；从没出过闩就是 0。"""
    best = 0.0
    for key in ("auto_released_at", "resumed_at", "released_at"):
        raw = st.get(key)
        if not raw:
            continue
        try:
            t = datetime.datetime.strptime(raw, "%Y-%m-%dT%H:%M:%SZ")
            best = max(best, t.replace(
                tzinfo=datetime.timezone.utc).timestamp())
        except Exception:
            continue
    return best


def scan_logs_for_limit(window_s=3600, since_ts=0.0, skip=()):
    """直接扫最近的 dispatch 日志找限额签名。

    只信注册簿会慢一拍：刚被限额打死的会话，注册簿的 reaped 还没写上，
    check() 就报 normal——2026-07-29 心跳实测三个工人 4 秒内全死于
    session limit，而探针仍报 normal。日志不会滞后，它是第一手证据。

    两条约束，都是被实测逼出来的：

    * `since_ts`——**上一次释放之后**写的日志才算数。否则那条打死会话的日志
      在整个扫描窗口里一直在，闸门每跳一次就重新 hold 一次，
      而按期限自动出闩的那条出口**永远走不到**：一次 hold 会变成永久 hold。
    * `skip`——分支已经推上去的会话，它的日志不算现行证据。
      那是注册簿判「不是限额打死」的同一份依据，两条路必须用同一把尺子。"""
    if not os.path.isdir(LOGS):
        return None
    cutoff = max(time.time() - window_s, since_ts)
    for name in sorted(os.listdir(LOGS), reverse=True):
        if not name.endswith(".log"):
            continue
        if any(s and s in name for s in skip):
            continue
        path = os.path.join(LOGS, name)
        if os.path.getmtime(path) < cutoff:
            continue
        try:
            text = open(path, encoding="utf-8", errors="ignore").read()
        except Exception:
            continue
        for raw in text.splitlines():
            line = raw.strip()
            if not line or len(line) > 300:
                continue            # 真的 CLI 报错很短；长的是散文
            if any(mark in line for mark in PROSE_MARKS):
                continue            # 在讨论限额，不是撞上限额
            if HARD_RE.search(line):
                _LAST_SCANNED_LOG["path"] = path   # 归因用：是哪个账号撞的
                return line[:200]
    _LAST_SCANNED_LOG["path"] = None
    return None


def account_of_log(log_name):
    """这条日志属于哪个账号。读不出来就是 `None`——**不猜**。

    `_runner.py` 在日志头写 `account=<id>`。没有这一位，一次限额就无法归因，
    而归因错的代价是把好账号也关掉，等于自己砍掉一半产能。
    """
    if not log_name:
        return None
    path = log_name if os.path.isabs(log_name) else os.path.join(LOGS, log_name)
    if not os.path.exists(path):
        return None
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            for _ in range(8):      # 头几行就够，别读整个日志
                line = fh.readline()
                if not line:
                    break
                m = re.search(r"account=(\S+)", line)
                if m:
                    acct = m.group(1)
                    return None if acct.startswith("default") else acct
    except OSError:
        return None
    return None


def _rotate_on_limit(hits, fresh, reg):
    """把这次限额归到某个账号头上；返回 `rotated` / `hold` / `no-pool`。

    `rotated` 意味着**还有别的账号能跑**，调用方不该冻结舰队。
    """
    try:
        sys.path.insert(0, HERE)
        import accounts as _acct
    except Exception:
        return "no-pool"
    pool = _acct.load_config()
    if not pool:
        return "no-pool"

    hint = (hits[0][1] if hits else fresh) or ""
    # 用哪条日志归因：注册簿里那条死会话的日志优先，否则是普扫命中的那一条。
    acct = None
    for pid_str, _line in hits:
        acct = account_of_log((reg.get(pid_str) or {}).get("log", ""))
        if acct:
            break
    if acct is None and fresh:
        acct = _last_scanned_account()
    if acct is None:
        # 归因不出来就**不动任何账号**，交回原来的全局逻辑。
        # 关错一个账号比冻结整队更贵，而且更难发现。
        return "no-pool"

    st = {"detected_at": now_utc(), "reset_hint": hint}
    due = reopen_at(st)
    until = due.strftime("%Y-%m-%dT%H:%M:%SZ") if due else now_utc()
    _acct.mark_limited(acct, until, hint)
    others = [a for a in pool if a != acct and _acct.usable(a)]
    return "rotated" if others else "hold"


#: `scan_logs_for_limit` 命中的那份日志，供归因使用。模块级而非返回值，
#: 是为了不改它已有的签名与两个调用点；写在这里是让这个耦合可见。
_LAST_SCANNED_LOG = {"path": None}


def _last_scanned_account():
    return account_of_log(_LAST_SCANNED_LOG.get("path") or "")


def check():
    # 日志普扫先跑，但**不许提前返回**：早退会跳过下面的注册簿清点，
    # 于是 requeue 是空的——窗口重开后没有任何东西被重新排队，
    # 一次 hold 就把那些会话永久丢了。这条早退是 2026-07-29 加日志普扫时
    # 混进来的，四条测试当场变红，而 monitor 的闸门那时正好跑不起来
    # （PATH 上的 bash 是 WSL 的），所以它红了一天没人看见。
    reg = load(os.path.join(LOGS, "registry.json"), {})
    _st0 = load(STATE, {"mode": "normal", "requeue": [], "history": []})
    # 已经在 hold 里就不再问日志：日志普扫的职责是**开**一次 hold，不是续。
    # 续的判据只有一个——窗口重开没有——那是下面的期限出闩在管。
    # 让打死会话的那行日志同时具备「开」和「续」的效力，等于把出闩焊死。
    fresh = (None if _st0.get("mode") == "hold" else
             scan_logs_for_limit(since_ts=_released_ts(_st0),
                                 skip=[p for p in reg if branch_pushed(p)]))
    st = load(STATE, {"mode": "normal", "requeue": [], "history": []})
    hits = []
    for pid_str, entry in sorted(reg.items()):
        if entry.get("reaped") == "quota-requeued":
            continue
        dead = not pid_alive(entry["pid"])
        if not dead or branch_pushed(pid_str):
            continue
        line = quota_line(entry.get("log", ""))
        if line:
            hits.append((pid_str, line))
            entry["reaped"] = "quota-requeued"
            if pid_str not in st["requeue"]:
                st["requeue"].append(pid_str)
    # 归因到账号，然后**只关那一个账号的窗口**。
    #
    # 有账号池时，一次限额是**关于那个账号**的事实，不是关于舰队的。旧写法把
    # 它读成整队冻结，于是 03:27–04:30 全员停机一小时，而另一个账号的窗口
    # 从头到尾开着。只有当池里每个账号都关着，才轮到全局 hold。
    rotated = _rotate_on_limit(hits, fresh, reg)
    if rotated == "rotated":
        save_state(st)          # requeue 已在上面填好，模式保持 normal
        print("ROTATED — 该账号的窗口已关，舰队转到其余账号继续。")
        return 0
    if hits or fresh:
        already = st.get("mode") == "hold"
        if not already:
            st["mode"] = "hold"
            st["detected_at"] = now_utc()
            st["reset_hint"] = hits[0][1] if hits else fresh
            st.setdefault("history", []).append(
                {"at": st["detected_at"],
                 "killed": [h[0] for h in hits],
                 "from": "registry" if hits else "log-scan"})
        if hits:
            json.dump(reg, open(os.path.join(LOGS, "registry.json"), "w",
                                encoding="utf-8"), indent=2)
        save_state(st)
        if hits:
            print("HOLD — quota kills: %s" % ", ".join(h[0] for h in hits))
        else:
            print("HOLD — 日志中的限额签名：%s" % fresh)
        print("hint: %s" % st.get("reset_hint"))
        return 2
    if st.get("mode") != "normal":
        # No fresh kills and the deadline has passed: the window the hold was
        # waiting on has reopened, so the hold has finished being true. Cleared
        # here rather than in `resume` because `check` is the one a caller
        # already runs every tick -- an exit nobody invokes is not an exit.
        due = reopen_at(st)
        now = datetime.datetime.now(datetime.timezone.utc)
        st["reopen_at"] = due.strftime("%Y-%m-%dT%H:%M:%SZ") if due else None
        if due and now >= due:
            st["mode"] = "normal"
            st["auto_released_at"] = now_utc()
            st["note"] = ("hold expired on its own: the window reopened at %s"
                          % st["reopen_at"])
            save_state(st)
            print("hold expired (window reopened %s) -> mode=normal"
                  % st["reopen_at"])
            if st["requeue"]:
                # Not relaunched from here: `check` must not spawn sessions.
                print("requeue still pending: %s -- run `resume`"
                      % ", ".join(st["requeue"]))
            return 0
        save_state(st)
        print("mode=%s requeue=%s reopen_at=%s"
              % (st["mode"], st["requeue"] or "[]", st["reopen_at"] or "?"))
        return 2
    save_state(st)
    print("mode=%s requeue=%s" % (st["mode"], st["requeue"] or "[]"))
    return 0


def ping_due(st, now=None):
    """Whether an automatic ping may spend a call now, and why not if not.

    Reads `last_ping_at`, which `ping` writes on **every** attempt regardless
    of the answer. Recording only successes would mean no throttle exactly
    while the window is shut, which is the only time the throttle matters.
    """
    last = parse_stamp(st.get("last_ping_at"))
    if last is None:
        return True, "no ping on record"
    now = now or datetime.datetime.now(datetime.timezone.utc)
    waited = (now - last).total_seconds() / 60.0
    if waited >= MIN_PING_INTERVAL_MIN:
        return True, "%.0f min since the last ping" % waited
    return False, ("last ping %.0f min ago; automatic pings are capped at one "
                   "per %d min because each one spends the quota it is waiting "
                   "on" % (waited, MIN_PING_INTERVAL_MIN))


def ping(if_due=False):
    """One minimal haiku call: the cheapest question the window can answer.

    `if_due=True` is the automatic caller's spelling and obeys the throttle,
    returning 3 without spending anything when a ping is not yet due. A bare
    `ping` is a person asking, and a person who types the command gets an
    answer -- the throttle exists to stop an unattended five-minute loop, not
    to argue with whoever is standing there.
    """
    if if_due:
        due, why = ping_due(load(STATE, {}))
        if not due:
            print("ping skipped: %s" % why)
            return 3

    import shutil
    claude = shutil.which("claude")
    proc = subprocess.run([claude, "-p", "reply with: ok", "--model", "haiku"],
                          capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    ok = proc.returncode == 0 and "ok" in proc.stdout.lower()

    # Reloaded *after* the call, not before: the call can take two minutes and
    # `check` runs on its own schedule, so a state dict read beforehand would
    # be stale and saving it would silently undo a hold that arrived meanwhile.
    st = load(STATE, {"mode": "normal", "requeue": [], "history": []})
    st["last_ping_at"] = now_utc()
    st["last_ping_result"] = "OPEN" if ok else "CLOSED"
    save_state(st)

    print("window %s" % ("OPEN" if ok else "CLOSED"))
    if not ok:
        blob = (proc.stdout + proc.stderr).strip().splitlines()
        line = next((l.strip()[:200] for l in blob if SIG_RE.search(l)),
                    (blob[-1][:200] if blob else "(no output)"))
        print("hint: %s" % line)
    return 0 if ok else 2


def window_is_open(st):
    """Ask the window, unless it was just asked.

    The automatic path pings and then calls `resume`, which used to ping again
    -- two paid calls per exit, seconds apart, during the outage the calls are
    waiting on. A fresh OPEN is evidence; re-buying it immediately is not
    diligence, it is the same measurement twice.

    Only a fresh **OPEN** short-circuits. A fresh CLOSED still re-pings from a
    manual `resume`, because the person running it is asking whether the
    situation has changed and "it hadn't, 3 minutes ago" is not an answer to
    that. In the automatic path the throttle catches it one level up.
    """
    if st.get("last_ping_result") != "OPEN":
        return ping() == 0
    due, _ = ping_due(st)
    if due:
        return ping() == 0
    print("window OPEN (from the ping %s, inside the %d-min window)"
          % (st.get("last_ping_at"), MIN_PING_INTERVAL_MIN))
    return True


def resume(stagger=90):
    st = load(STATE, {"mode": "normal", "requeue": []})
    if not st["requeue"]:
        # An empty queue is not a reason to stay held. The hold froze the
        # fleet from 09:35 past its own 20:20 reset because this branch
        # returned without ever clearing the mode (OPS-M cycle 5).
        if st.get("mode") != "normal" and window_is_open(st):
            st = load(STATE, {"mode": "normal", "requeue": []})   # ping wrote
            st["mode"] = "normal"
            st["resumed_at"] = now_utc()
            save_state(st)
            print("queue empty and window open -> mode=normal")
            return 0
        print("nothing to resume.")
        return 0
    if not window_is_open(st):
        print("window still closed — try later.")
        return 2
    st = load(STATE, {"mode": "normal", "requeue": []})           # ping wrote
    order = sorted(st["requeue"],
                   key=lambda p: PRIORITY.index(p) if p in PRIORITY else 99)
    half = max(3, len(order) // 2)
    batch, rest = order[:half], order[half:]
    for i, pid_str in enumerate(batch):
        if i:
            time.sleep(stagger)
        subprocess.run([sys.executable, os.path.join(HERE, "dispatch.py"),
                        "--only", pid_str], cwd=ROOT)
    st["requeue"] = rest
    st["mode"] = "normal" if not rest else "recovering"
    st["resumed_at"] = now_utc()
    save_state(st)
    print("relaunched %s; still queued: %s" % (batch, rest or "[]"))
    return 0


def main():
    argv = sys.argv[1:]
    cmd = argv[0] if argv else "check"
    if cmd == "ping":
        return ping(if_due="--if-due" in argv)
    return {"check": check, "resume": resume}[cmd]()


if __name__ == "__main__":
    raise SystemExit(main())
