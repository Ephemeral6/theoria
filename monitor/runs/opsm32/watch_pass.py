"""OPS-M cycle 32: watch the prediction in pass-model-CORRECTED.md.

Predicted for the first pass after OPS-M pushes: full pass (no HELD line),
~13-15 of 17 candidates gated, KILLED at its start + 3600s (so merge.lock is
left behind rather than released), and no new monitor/reflex.log line.
"""
import datetime, os, subprocess, sys, time

ROOT = r"C:\Users\user\Desktop\theoria"
OUT = os.path.join(ROOT, "monitor", "runs", "opsm32", "pass-watch.log")
LOCK = os.path.join(ROOT, "monitor", "ci", "merge.lock")
MLOG = os.path.join(ROOT, "monitor", "ci", "merge.log")
RLOG = os.path.join(ROOT, "monitor", "reflex.log")
SINCE = sys.argv[1] if len(sys.argv) > 1 else "2026-07-30T12:45:00Z"


def alive(pid):
    try:
        out = subprocess.run(["tasklist", "/FI", "PID eq %s" % pid],
                             capture_output=True, text=True, timeout=30).stdout
        return str(pid) in out
    except Exception:
        return None


def lines(p):
    try:
        return open(p, encoding="utf-8", errors="replace").read().splitlines()
    except OSError:
        return []


end = time.time() + 5400
with open(OUT, "a", encoding="utf-8") as fh:
    fh.write("=== watcher start (python), since=%s ===\n" % SINCE)
while time.time() < end:
    ml = lines(MLOG)
    rl = lines(RLOG)
    new = [l for l in ml if l[:20] > SINCE]
    gated = [l for l in new if " FLAG " in l or " MERGED " in l]
    held = [l for l in new if " HELD " in l]
    lk = ""
    if os.path.exists(LOCK):
        try:
            pid = open(LOCK).read().strip()
            lk = "%s(%s)" % (pid, "alive" if alive(pid) else "DEAD-STALE")
        except OSError:
            lk = "?"
    else:
        lk = "none"
    row = ("%s lock=%-14s gated_since_push=%-3d held_lines=%d reflexlog=%d "
           "last=%s\n" % (datetime.datetime.utcnow().strftime("%H:%M:%SZ"),
                          lk, len(gated), len(held), len(rl),
                          (ml[-1][:20] if ml else "-")))
    with open(OUT, "a", encoding="utf-8") as fh:
        fh.write(row)
    time.sleep(60)
with open(OUT, "a", encoding="utf-8") as fh:
    fh.write("=== watcher end %s ===\n" % datetime.datetime.utcnow().strftime("%H:%M:%SZ"))
