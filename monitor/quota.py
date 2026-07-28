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
    out = subprocess.run(["tasklist", "/FI", "PID eq %d" % pidnum, "/FO", "CSV"],
                         capture_output=True, text=True).stdout
    return str(pidnum) in out


def branch_pushed(pid_str):
    slug = "agent/" + pid_str.lower().replace("-", "")
    out = subprocess.run(["git", "branch", "-r", "--format=%(refname:short)"],
                         cwd=ROOT, capture_output=True, text=True).stdout
    return any(slug in b for b in out.splitlines())


def quota_line(log_name):
    """Return the matched limit line only — never the session's work."""
    path = os.path.join(LOGS, log_name)
    if not os.path.exists(path):
        return None
    for line in open(path, encoding="utf-8", errors="ignore"):
        if SIG_RE.search(line):
            return line.strip()[:200]
    return None


def check():
    reg = load(os.path.join(LOGS, "registry.json"), {})
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
    if hits:
        st["mode"] = "hold"
        st["detected_at"] = now_utc()
        st["reset_hint"] = hits[0][1]
        st["history"].append({"at": st["detected_at"],
                              "killed": [h[0] for h in hits]})
        json.dump(reg, open(os.path.join(LOGS, "registry.json"), "w",
                            encoding="utf-8"), indent=2)
        save_state(st)
        print("HOLD — quota kills: %s" % ", ".join(h[0] for h in hits))
        print("hint: %s" % st["reset_hint"])
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


def ping():
    """One minimal haiku call: the cheapest question the window can answer."""
    import shutil
    claude = shutil.which("claude")
    proc = subprocess.run([claude, "-p", "reply with: ok", "--model", "haiku"],
                          capture_output=True, text=True, timeout=120)
    ok = proc.returncode == 0 and "ok" in proc.stdout.lower()
    print("window %s" % ("OPEN" if ok else "CLOSED"))
    if not ok:
        blob = (proc.stdout + proc.stderr).strip().splitlines()
        line = next((l.strip()[:200] for l in blob if SIG_RE.search(l)),
                    (blob[-1][:200] if blob else "(no output)"))
        print("hint: %s" % line)
    return 0 if ok else 2


def resume(stagger=90):
    st = load(STATE, {"mode": "normal", "requeue": []})
    if not st["requeue"]:
        # An empty queue is not a reason to stay held. The hold froze the
        # fleet from 09:35 past its own 20:20 reset because this branch
        # returned without ever clearing the mode (OPS-M cycle 5).
        if st.get("mode") != "normal" and ping() == 0:
            st["mode"] = "normal"
            st["resumed_at"] = now_utc()
            save_state(st)
            print("queue empty and window open -> mode=normal")
            return 0
        print("nothing to resume.")
        return 0
    if ping() != 0:
        print("window still closed — try later.")
        return 2
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
    cmd = sys.argv[1] if len(sys.argv) > 1 else "check"
    return {"check": check, "ping": ping, "resume": resume}[cmd]()


if __name__ == "__main__":
    raise SystemExit(main())
