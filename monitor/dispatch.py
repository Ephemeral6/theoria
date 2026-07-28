"""Dispatch prompt files as headless Claude Code executor sessions.

    python monitor/dispatch.py                 # launch every pending prompt
    python monitor/dispatch.py --only R-1      # launch a specific one
    python monitor/dispatch.py --dry-run       # show the plan, launch nothing

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
    m = re.match(r"([PRM]-\d+)", name)
    return m.group(1) if m else None


def branch_for(pid):
    return "agent/%s" % pid.lower().replace("-", "", 0).replace("P-", "p").replace("R-", "r").replace("M-", "m")


def branch_taken(pid, branches):
    slug = pid.lower().replace("-", "")          # p8 / r1 / m0
    pat = re.compile(r"agent/%s\b|agent/%s-" % (slug, slug))
    return any(pat.search(b) for b in branches)


def launch(pid, path, log_dir):
    text = open(path, encoding="utf-8").read()
    claude = shutil.which("claude")
    if not claude:
        sys.exit("claude CLI not on PATH")
    stamp = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
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
    return proc.pid, log_path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", help="dispatch just this prompt id (e.g. R-1)")
    ap.add_argument("--force", action="store_true",
                    help="launch even if the agent branch already exists")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

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
