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
import childio  # noqa: E402  (per-child decoding, see its docstring)

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
LOCK = os.path.join(HERE, "reflex.lock")
RLOG = os.path.join(HERE, "reflex.log")
LOOP = os.path.join(HERE, "loop_state.json")
MAX_DEATHS = 3
WORKER_MAX = 7      # spawning is back ON: the crash-era safeties are all in place
                    # now (memory admission, 45s stagger, orphan sweep, quota
                    # gate), so worker supply no longer waits for a human.
MIN_FREE_GB = 8     # admission control: no spawn below this much free RAM


def rlog(msg):
    stamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    with open(RLOG, "a", encoding="utf-8") as fh:
        fh.write("%s %s\n" % (stamp, msg))


def run(args, timeout=2400):
    """Everything this file runs is Python -- dispatch, board, quota -- so UTF-8.

    It was the host locale, cp936, and the children print Chinese. That is the
    same mismatch that reported eight live workers as dead, sitting in the one
    module whose job is deciding which workers are dead. `errors="replace"`
    matters more than the codec: a reaper that raises while decoding its child
    is a reaper that did not run, and nothing downstream would say so.

    The single `schtasks` call in this file uses `run_console` instead.
    """
    return subprocess.run(args, cwd=ROOT, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=timeout)


def run_console(args, timeout=2400):
    """Windows console built-ins emit the console code page, not UTF-8."""
    return subprocess.run(args, cwd=ROOT, capture_output=True, text=True,
                          encoding=childio._CONSOLE, errors="replace",
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

        # 0c. sweep orphaned board claims — a worker killed by the quota or a
        # crash leaves its claim hanging, so the board thinks the work is in
        # progress and the territory stays locked against everyone else.
        # `--include-standing` since S21. Standing sessions were exempt because
        # nothing could tell a dead App session from a busy one; `board.py` now
        # can, and requires all three of a stale heartbeat, an unanswered
        # URGENT, and two full cycles of silence before it will free anything.
        # Three researchers died to a session limit on 2026-07-29 and six items
        # -- including the campaign mainline -- stayed locked for two hours
        # because this ran without it.
        sw = run([sys.executable, os.path.join(HERE, "board.py"), "sweep",
                  "--include-standing"])
        events += ["sweep:" + l.split()[0] for l in sw.stdout.splitlines()
                   if "freed from" in l]
        # A standing release is reported separately and by name. It is a much
        # bigger event than reaping a one-shot worker -- it says a researcher
        # is gone -- and folding the two into one `sweep:` line would bury the
        # louder one under the routine one.
        for line in sw.stdout.splitlines():
            if "freed from" in line and "RES-" in line:
                events.append("STANDING-DEAD:%s" % line.split()[0])
                rlog("standing session released a claim: %s" % line.strip())

        # 0d. dashboard server — the logon task could not be registered
        # (needs admin), so reflex keeps the port alive itself. Without this
        # the page dies at every reboot and the user has to notice.
        try:
            import socket
            s = socket.socket()
            s.settimeout(1)
            dead = s.connect_ex(("127.0.0.1", 8787)) != 0
            s.close()
        except Exception:
            dead = True
        if dead:
            subprocess.Popen(["cmd", "/c", "start", "/min", "",
                              os.path.join(HERE, "serve.cmd")],
                             creationflags=0x00000008 | 0x01000000)
            events.append("serve:restarted")

        # 1. reap
        out = run([sys.executable, os.path.join(HERE, "dispatch.py"),
                   "--reap"]).stdout
        killed = [l for l in out.splitlines() if "killed" in l]
        events += ["reap:" + l.split()[0] for l in killed]

        # 2. quota
        q = run([sys.executable, os.path.join(HERE, "quota.py"), "check"])
        # The hold had no exit: nothing ever called resume, so a session-limit
        # at 09:35 kept the fleet frozen long after its 20:20 reset (OPS-M
        # cycle 5). Every tick in hold now probes the window and lifts it.
        if q.returncode == 2:
            # `--if-due` and not a bare ping: this loop runs every five minutes
            # and each ping is a real haiku call, so an unthrottled probe spent
            # the quota it was waiting to get back, twelve times an hour, for
            # the length of the outage. Exit 3 means "not due, nothing spent".
            probe = run([sys.executable, os.path.join(HERE, "quota.py"),
                         "ping", "--if-due"], timeout=180)
            if probe.returncode == 3:
                events.append("quota:probe-throttled")
            elif probe.returncode == 0:
                # `resume` reuses this ping's answer rather than buying it
                # again; it is the same measurement seconds apart.
                r = run([sys.executable, os.path.join(HERE, "quota.py"),
                         "resume"], timeout=1800)
                events.append("quota:RESUMED(auto)")
                rlog("quota: window reopened on its own -> automatic resume, "
                     "no human in the loop: %s"
                     % (r.stdout.strip().splitlines() or ["(no output)"])[-1])
                q = run([sys.executable, os.path.join(HERE, "quota.py"),
                         "check"])
        # 退出码 2 是「窗口关着」，0 是「窗口开着」，**其它一律是「没问出来」**。
        # 旧写法 `== 2` 把 1（未捕获的 traceback、截断的 quota_state.json）
        # 塌成「窗口开着」，重新放开这一跳最贵的两条分支；而 stderr 被捕获后丢弃，
        # 失败的检查与干净的检查在 reflex.log 里逐字节相同。
        hold = q.returncode != 0
        if q.returncode not in (0, 2):
            first = ((q.stderr or "").strip().splitlines() or [""])[0]
            events.append("quota:CHECK-FAILED(%d) %s"
                          % (q.returncode, first[:120]))
        if hold:
            events.append("quota:HOLD")

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
                st = run_console(["schtasks", "/Query", "/TN",
                          "TheoriaAgent-%s" % wid, "/FO", "LIST"])
                # 中文控制台印的是「正在运行」，英文的 "Running" 一次也不会命中，
                # 于是 live_workers **恒为 0**，补员循环每一跳都按满员上限拉人。
                # 这仓库已经为 GBK/UTF-8 付过五次账；两个词都认，别只认一个。
                if st.returncode == 0 and ("Running" in st.stdout
                                           or "正在运行" in st.stdout):
                    live_workers += 1
            # 读不到内存就当作**没有**内存，不是当作 99 GB。
            # 旧写法初始值 99 + `except: pass`，任何一种读数失败都让门大开、
            # 一次放进七个工人；而这道门唯一能发的事件（worker-hold:low-memory）
            # 按构造在读数失败时不可能发出——今天读数失败与一台健康的 99GB 机器
            # 产生逐字节相同的日志。`standing.py` 的同一处测量失败时返回 0.0，
            # 两个方向相反的默认值，能一次拉七个的那个反而是 fail-open 的。
            free_gb = 0.0
            try:
                out = run(["powershell", "-NoProfile", "-Command",
                           "(Get-CimInstance Win32_OperatingSystem)."
                           "FreePhysicalMemory"]).stdout.strip()
                free_gb = int(out) / 1048576.0
            except Exception as exc:
                events.append("mem-unreadable:%s" % type(exc).__name__)
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

        # 4. ci merge — runs even under quota hold: it spends zero tokens
        # (git + pytest only), and a worker's proposal caught it being
        # stopped by a budget it cannot possibly consume.
        if True:
            r = run([sys.executable, os.path.join(HERE, "ci_merge.py")],
                    timeout=3600)
            merged = [l for l in r.stdout.splitlines() if l.startswith("MERGED")]
            flagged = [l for l in r.stdout.splitlines() if l.startswith("FLAG")]
            events += merged + flagged

        # 4b. supply alarm — authoring items needs judgment, so reflex cannot
        # refill the board itself; what it can do is make a dry board loud
        # instead of silent. Idle agents look identical to busy ones.
        try:
            import board as board_mod
            depth = len(board_mod.candidates())
            if depth <= 2:
                events.append("SUPPLY-LOW:%d" % depth)
        except Exception:
            pass

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
