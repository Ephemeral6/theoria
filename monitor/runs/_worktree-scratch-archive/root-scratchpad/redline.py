"""OPS-A red-line scan over an incremental commit range.

Dimension 1 (discipline drift):
  * sealed-pile game ids appearing in the ADDED lines of the range
  * the ARC_API_KEY *value* appearing in any tracked file touched by the range
  * append-only files whose history shows deletions inside the range

Usage: python scratchpad/redline.py <base> <head>
Prints a compact report; no repo writes.
"""
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def git(*args):
    out = subprocess.run(["git", "-C", ROOT] + list(args),
                         capture_output=True)
    return out.stdout.decode("utf-8", "replace")


def load_sealed():
    with open(os.path.join(ROOT, "arc-recon", "data", "piles.json"),
              encoding="utf-8") as fh:
        return json.load(fh)["sealed_pile"]


def load_key():
    path = os.path.join(ROOT, ".env")
    if not os.path.exists(path):
        return None
    for line in open(path, encoding="utf-8"):
        if line.strip().startswith("ARC_API_KEY"):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    return None


def main():
    base, head = sys.argv[1], sys.argv[2]
    sealed = load_sealed()
    key = load_key()

    diff = git("diff", "-U0", base + ".." + head)
    added = [ln[1:] for ln in diff.splitlines()
             if ln.startswith("+") and not ln.startswith("+++")]
    # which file each added line belongs to
    cur = None
    per_file = {}
    for ln in diff.splitlines():
        if ln.startswith("+++ b/"):
            cur = ln[6:]
        elif ln.startswith("+") and not ln.startswith("+++"):
            per_file.setdefault(cur, []).append(ln[1:])

    print("== sealed ids in added lines ==")
    hits = 0
    for gid in sealed:
        for path, lines in per_file.items():
            for line in lines:
                if gid in line:
                    hits += 1
                    print("  %s  %s  %s" % (gid, path, line.strip()[:140]))
    if not hits:
        print("  none")

    print("== key value in tracked files ==")
    if not key:
        print("  !! no ARC_API_KEY in .env -- cannot run this check (SENTINEL: unknown, not clean)")
    else:
        found = 0
        tracked = git("ls-files").splitlines()
        for path in tracked:
            full = os.path.join(ROOT, path)
            try:
                with open(full, "rb") as fh:
                    blob = fh.read()
            except OSError:
                continue
            if key.encode() in blob:
                found += 1
                print("  LEAK %s" % path)
        print("  scanned %d tracked files, %d leaks" % (len(tracked), found))

    print("== append-only deletions on the first-parent mainline ==")
    for path in ["PARTNER_SYNC.md", "monitor/incidents.jsonl",
                 "arc-recon/data/contamination_log.jsonl"]:
        for scope, args in (("range", [base + ".." + head]), ("all-history", [])):
            log = git("log", "--first-parent", "--numstat", "--format=%H",
                      *args, "--", path)
            dels = 0
            commits = []
            cur_sha = None
            for ln in log.splitlines():
                if re.fullmatch(r"[0-9a-f]{40}", ln.strip()):
                    cur_sha = ln.strip()
                elif ln.strip():
                    parts = ln.split("\t")
                    if len(parts) == 3 and parts[1].isdigit() and int(parts[1]) > 0:
                        dels += int(parts[1])
                        commits.append((cur_sha[:8], parts[1]))
            print("  %-45s %-11s deletions=%d %s" % (path, scope, dels, commits[:6]))


if __name__ == "__main__":
    main()
