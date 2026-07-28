"""Reflex layer (upgrade #1): everything that needs no judgment, every 5 min.

Registered as a Windows scheduled task; zero tokens. The monitor session
keeps only judgment (prompts, adjudication, spec updates). Steps:

    1. reap        — kill sessions whose branch reached origin
    2. quota check — flip to hold on limit signatures
    3. revive      — relaunch lost sessions (three-strikes rule)
    4. ci merge    — deterministic merge-on-delivery (test-gated)
    5. light refresh — regenerate the dashboard from the tree

All state changes go through the same files the monitor uses (registry,
loop_state, quota_state), so the monitor's next heartbeat sees everything.
The reflex never commits to git and never authors or edits prompts.
"""

import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
LOCK = os.path.join(HERE, "reflex.lock")
RLOG = os.path.join(HERE, "reflex.log")
LOOP = os.path.join(HERE, "loop_state.json")
MAX_DEATHS = 3
WORKER_MAX = 0      # spawning is OFF: the monitor ramps workers by hand after the
                    # 2026-07-28 crash. Reflex keeps reap / quota / ci_merge only.
MIN_FREE_GB = 8     # admission control: no spawn below this much free RAM


def rlog(msg):
    stamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    with open(RLOG, "a", encoding="utf-8") as fh:
        fh.write("%s %s\n" % (stamp, msg))


def run(args, timeout=2400):
    return subprocess.run(args, cwd=ROOT, capture_output=True, text=True,
                          timeout=timeout)


def load_loop():
    if os.path.exists(LOOP):
        return json.load(open(LOOP, encoding="utf-8"))
    return {}


def save_loop(state):
    tmp = LOOP + ".tmp"
    json.dump(state, open(tmp, "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    os.replace(tmp, LOOP)


def main():
    if os.path.exists(LOCK):
        if time.time() - os.path.getmtime(LOCK) < 1500:
            return 0            # previous reflex still at work
        os.remove(LOCK)
    open(LOCK, "w").write(str(os.getpid()))
    try:
        events = []

        # 0. launch queue — the monitor never spawns sessions itself anymore:
        # anything spawned from its tool shell gets silently killed (proven
        # by runner-level deaths with no EXIT stamp). The monitor appends ids
        # to dispatch_queue.json; we launch them here, under Task Scheduler
        # lineage, where processes actually survive.
        qpath = os.path.join(HERE, "dispatch_queue.json")
        if os.path.exists(qpath):
            try:
                queue = json.load(open(qpath, encoding="utf-8"))
            except Exception:
                queue = []
            launched_q = 0
            for pid_str in queue:
                if launched_q:
                    time.sleep(45)
                r = run([sys.executable, os.path.join(HERE, "dispatch.py"),
                         "--only", pid_str, "--force"])
                if "launched" in r.stdout:
                    events.append("queue-launch:%s" % pid_str)
                    launched_q += 1
                else:
                    events.append("queue-skip:%s" % pid_str)
            os.remove(qpath)

        # 0b. worker headcount — long-lived workers claim their own items from
        # the board, so the monitor controls only the population, never the
        # per-item dispatch. Target scales with what the board still holds.
        try:
            import board as board_mod
            avail = len(board_mod.candidates())
            claimed = len(board_mod.claimed_map())
        except Exception:
            avail, claimed = 0, 0
        if not hold and avail:
            reg_path = os.path.join(HERE, "dispatch-logs", "registry.json")
            reg = (json.load(open(reg_path, encoding="utf-8"))
                   if os.path.exists(reg_path) else {})
            live_workers = 0
            for wid, entry in reg.items():
                if not wid.startswith("W-") or entry.get("reaped"):
                    continue
                st = run(["schtasks", "/Query", "/TN",
                          "TheoriaAgent-%s" % wid, "/FO", "LIST"])
                if st.returncode == 0 and "Running" in st.stdout:
                    live_workers += 1
            free_gb = 99
            try:
                out = run(["powershell", "-NoProfile", "-Command",
                           "(Get-CimInstance Win32_OperatingSystem)."
                           "FreePhysicalMemory"]).stdout.strip()
                free_gb = int(out) / 1048576.0
            except Exception:
                pass
            if free_gb < MIN_FREE_GB:
                events.append("worker-hold:low-memory(%.1fGB)" % free_gb)
                target = live_workers          # spawn nothing
            else:
                target = min(WORKER_MAX, max(1, avail))
            for i in range(target - live_workers):
                wid = "W-%d" % (int(time.time()) % 100000 + i)
                if i:
                    time.sleep(20)
                r = run([sys.executable, os.path.join(HERE, "dispatch.py"),
                         "--worker", wid])
                events.append("worker-spawn:%s" % wid
                              if "started" in r.stdout else
                              "worker-fail:%s" % wid)

        # 1. reap
        out = run([sys.executable, os.path.join(HERE, "dispatch.py"),
                   "--reap"]).stdout
        killed = [l for l in out.splitlines() if "killed" in l]
        events += ["reap:" + l.split()[0] for l in killed]

        # 2. quota
        q = run([sys.executable, os.path.join(HERE, "quota.py"), "check"])
        hold = q.returncode == 2
        if hold:
            events.append("quota:HOLD")

        # 3. revive (skip in hold)
        if not hold:
            reg_path = os.path.join(HERE, "dispatch-logs", "registry.json")
            reg = (json.load(open(reg_path, encoding="utf-8"))
                   if os.path.exists(reg_path) else {})
            state = load_loop()
            deaths = state.get("death_counts", {})
            remote = run(["git", "branch", "-r", "--list", "origin/agent/*",
                          "--format=%(refname:short)"]).stdout.lower()
            revived = 0
            for pid_str, entry in sorted(reg.items()):
                if pid_str.startswith(("M-", "A-", "B-", "R-")):
                    continue        # ops run in the user's app now
                if entry.get("reaped") not in ("exited",
                                               "killed-permission-wall"):
                    continue
                slug = (pid_str.lower().replace("-", "")
                        if len(pid_str) <= 4 else pid_str.lower())
                if "agent/%s" % slug in remote:
                    continue        # it delivered; nothing to revive
                n = deaths.get(pid_str, 0)
                if n >= MAX_DEATHS:
                    events.append("three-strikes:%s" % pid_str)
                    continue
                if revived:
                    time.sleep(45)   # stagger is law
                r = run([sys.executable, os.path.join(HERE, "dispatch.py"),
                         "--only", pid_str])
                if "launched" in r.stdout:
                    deaths[pid_str] = n + 1
                    revived += 1
                    events.append("revive:%s(#%d)" % (pid_str, n + 1))
            if revived or deaths != state.get("death_counts", {}):
                state["death_counts"] = deaths
                save_loop(state)

        # 4. ci merge (its own lock + M-0 standdown check inside)
        if not hold:
            r = run([sys.executable, os.path.join(HERE, "ci_merge.py")],
                    timeout=3600)
            merged = [l for l in r.stdout.splitlines() if l.startswith("MERGED")]
            flagged = [l for l in r.stdout.splitlines() if l.startswith("FLAG")]
            events += merged + flagged

        # 5. light dashboard refresh
        run([sys.executable, os.path.join(HERE, "scan.py")], timeout=600)

        rlog(" | ".join(events) if events else "quiet")
        return 0
    finally:
        try:
            os.remove(LOCK)
        except OSError:
            pass


if __name__ == "__main__":
    raise SystemExit(main())
