"""Dispatch prompt files as headless Claude Code executor sessions.

    python monitor/dispatch.py                 # launch every pending prompt
    python monitor/dispatch.py --only R-1      # launch a specific one
    python monitor/dispatch.py --dry-run       # show the plan, launch nothing
    python monitor/dispatch.py --health        # content-free liveness report

Context isolation contract (the reason --health exists):
executor sessions run in their own processes with their own context windows;
nothing flows back into the monitor unless the monitor reads it. The monitor
therefore audits executors ONLY through their public interface — branches,
commits, RUN_STATE/STATUS files, runs/ archives, PARTNER_SYNC — never their
transcripts. dispatch-logs/ exist solely for launch-failure forensics
(CLI/auth errors); --health reports pid-alive / log-size / branch-created
WITHOUT reading log content, and reading a log body is warranted only when a
launch died before its branch appeared.

"Pending" = a P-*/R-*/M-* file in monitor/prompts/ whose agent branch does not
exist yet (local or remote). The branch check is the anti-double-run guard:
executor sessions create their branch as step one, so an existing branch means
a session already picked that prompt up (manually pasted or dispatched here).
Use --force to override for a genuine re-run.

Each launch: `claude -p <prompt-text> --model opus --dangerously-skip-permissions`
detached from the repo root, stdout/stderr appended to
monitor/dispatch-logs/<id>-<UTC>.log. The prompt itself instructs the session
to build its own worktree, so concurrent launches do not contend for the tree.

M-* prompts are never auto-launched by the batch run (merge runs after the
others push); dispatch them explicitly with --only.
"""

import argparse
import datetime
import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PROMPTS = os.path.join(HERE, "prompts")
LOGS = os.path.join(HERE, "dispatch-logs")


def git(*args):
    out = subprocess.run(["git"] + list(args), cwd=ROOT, capture_output=True,
                         text=True)
    return out.stdout


def existing_branches():
    return set(line.strip().lstrip("*+ ").strip()
               for line in git("branch", "-a", "--format=%(refname:short)").splitlines()
               if line.strip())


def prompt_id(name):
    m = re.match(r"([PRMBA]-\d+)", name)
    return m.group(1) if m else None


def branch_for(pid):
    return "agent/%s" % pid.lower().replace("-", "", 0).replace("P-", "p").replace("R-", "r").replace("M-", "m")


def branch_taken(pid, branches):
    slug = pid.lower().replace("-", "")          # p8 / r1 / m0
    pat = re.compile(r"agent/%s\b|agent/%s-" % (slug, slug))
    return any(pat.search(b) for b in branches)


REGISTRY = os.path.join(LOGS, "registry.json")


def load_registry():
    import json
    if os.path.exists(REGISTRY):
        return json.load(open(REGISTRY, encoding="utf-8"))
    return {}


def save_registry(reg):
    import json
    json.dump(reg, open(REGISTRY, "w", encoding="utf-8"), indent=2)


def pid_alive(pidnum):
    if os.name == "nt":
        out = subprocess.run(["tasklist", "/FI", "PID eq %d" % pidnum, "/FO", "CSV"],
                             capture_output=True, text=True).stdout
        return str(pidnum) in out
    try:
        os.kill(pidnum, 0)
        return True
    except OSError:
        return False


def kill_tree(pidnum):
    if os.name == "nt":
        subprocess.run(["taskkill", "/PID", str(pidnum), "/T", "/F"],
                       capture_output=True)
    else:
        subprocess.run(["kill", "-9", str(pidnum)], capture_output=True)


def reap():
    """跑完即杀：a dispatched session whose branch reached origin is done —
    kill its process tree immediately. Sessions that exited on their own are
    marked reaped. Content-free throughout."""
    reg = load_registry()
    remote = set(git("branch", "-r", "--format=%(refname:short)").splitlines())
    changed = False
    for pid, entry in sorted(reg.items()):
        if entry.get("reaped"):
            continue
        pidnum = entry["pid"]
        done = any(entry_branch in b for b in remote
                   for entry_branch in [("agent/%s" % pid.lower().replace("-", ""))])
        alive = pid_alive(pidnum)
        if done and alive:
            kill_tree(pidnum)
            entry["reaped"] = "killed-on-completion"
            print("%-6s pid=%s branch pushed -> killed" % (pid, pidnum))
            changed = True
        elif not alive:
            entry["reaped"] = "exited"
            print("%-6s pid=%s exited on its own" % (pid, pidnum))
            changed = True
        else:
            print("%-6s pid=%s still running" % (pid, pidnum))
    if changed:
        save_registry(reg)
    if not reg:
        print("registry empty.")


def launch(pid, path, log_dir):
    text = open(path, encoding="utf-8").read()
    claude = shutil.which("claude")
    if not claude:
        sys.exit("claude CLI not on PATH")
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    log_path = os.path.join(log_dir, "%s-%s.log" % (pid, stamp))
    log = open(log_path, "a", encoding="utf-8")
    log.write("=== dispatch %s at %s ===\n" % (pid, stamp))
    log.flush()
    flags = 0
    if os.name == "nt":
        flags = subprocess.CREATE_NEW_PROCESS_GROUP | 0x00000008  # DETACHED
    proc = subprocess.Popen(
        [claude, "-p", text, "--model", "opus", "--dangerously-skip-permissions"],
        cwd=ROOT, stdout=log, stderr=subprocess.STDOUT,
        stdin=subprocess.DEVNULL, creationflags=flags)
    reg = load_registry()
    reg[pid] = {"pid": proc.pid, "log": os.path.basename(log_path),
                "started": stamp, "reaped": None}
    save_registry(reg)
    return proc.pid, log_path


def health():
    """Content-free status of every dispatched session: pid alive, log bytes
    (a growing log = a working session), branch created. Never prints log
    content — that is the isolation contract."""
    procs = set()
    if os.name == "nt":
        out = subprocess.run(["tasklist", "/FI", "IMAGENAME eq node.exe", "/FO", "CSV"],
                             capture_output=True, text=True).stdout
        procs = {line.split('","')[1] for line in out.splitlines() if line.startswith('"')}
    branches = existing_branches()
    if not os.path.isdir(LOGS):
        print("no dispatch logs.")
        return
    for name in sorted(os.listdir(LOGS)):
        if not name.endswith(".log"):
            continue
        pid = prompt_id(name)
        path = os.path.join(LOGS, name)
        size = os.path.getsize(path)
        age_min = (datetime.datetime.now().timestamp() - os.path.getmtime(path)) / 60
        branch = "branch:yes" if pid and branch_taken(pid, branches) else "branch:no"
        print("%-6s log=%7dB  last-write %4.0f min ago  %s"
              % (pid or "?", size, age_min, branch))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", help="dispatch just this prompt id (e.g. R-1)")
    ap.add_argument("--force", action="store_true",
                    help="launch even if the agent branch already exists")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--health", action="store_true",
                    help="content-free liveness report of dispatched sessions")
    ap.add_argument("--reap", action="store_true",
                    help="kill sessions whose branch reached origin (跑完即杀)")
    args = ap.parse_args()
    if args.health:
        health()
        return 0
    if args.reap:
        reap()
        return 0

    os.makedirs(LOGS, exist_ok=True)
    branches = existing_branches()
    plan = []
    for name in sorted(os.listdir(PROMPTS)):
        pid = prompt_id(name)
        if not pid or not name.endswith(".md"):
            continue
        if args.only and pid != args.only:
            continue
        if pid.startswith("M-") and not args.only:
            plan.append((pid, name, "skip: merge prompts launch only via --only"))
            continue
        if branch_taken(pid, branches) and not args.force:
            plan.append((pid, name, "skip: agent branch exists (already picked up)"))
            continue
        entry = load_registry().get(pid)
        if entry and not entry.get("reaped") and pid_alive(entry["pid"]) \
                and not args.force:
            plan.append((pid, name, "skip: dispatched session still running (pid %s)"
                         % entry["pid"]))
            continue
        plan.append((pid, name, "LAUNCH"))

    for pid, name, action in plan:
        if action != "LAUNCH":
            print("%-6s %-28s %s" % (pid, name, action))
            continue
        if args.dry_run:
            print("%-6s %-28s would launch" % (pid, name))
            continue
        pidnum, log_path = launch(pid, os.path.join(PROMPTS, name), LOGS)
        print("%-6s %-28s launched pid=%s log=%s"
              % (pid, name, pidnum, os.path.relpath(log_path, ROOT)))
    if not plan:
        print("nothing matched.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
