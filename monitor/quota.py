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
    r"usage limit", r"Usage limit", r"limit will reset", r"rate.?limit",
    r"overloaded", r"Overloaded", r"credit balance", r"quota",
    r"429", r"insufficient.*credits",
]
SIG_RE = re.compile("|".join(SIGNATURES))

# Relaunch order when the window reopens: integration gate first, critical
# path second, cheap probes, then the rest; standing services last.
PRIORITY = ["M-0", "P-8", "P-20", "P-18", "P-19", "P-9", "P-12", "P-13",
            "P-15", "P-17", "R-1", "A-1", "B-1"]


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
    save_state(st)
    print("mode=%s requeue=%s" % (st["mode"], st["requeue"] or "[]"))
    return 0 if st["mode"] == "normal" else 2


def ping():
    """One minimal haiku call: the cheapest question the window can answer."""
    import shutil
    claude = shutil.which("claude")
    proc = subprocess.run([claude, "-p", "reply with: ok", "--model", "haiku"],
                          capture_output=True, text=True, timeout=120)
    ok = proc.returncode == 0 and "ok" in proc.stdout.lower()
    print("window %s" % ("OPEN" if ok else "CLOSED"))
    if not ok:
        line = next((l.strip()[:200] for l in
                     (proc.stdout + proc.stderr).splitlines()
                     if SIG_RE.search(l)), "(no signature)")
        print("hint: %s" % line)
    return 0 if ok else 2


def resume(stagger=90):
    st = load(STATE, {"mode": "normal", "requeue": []})
    if not st["requeue"]:
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
