"""Survey: what state are exam/runs/<id>/MANIFEST.json actually in?

Read-only.  Written because this run's own manifest turned out to be wrong in a
way nothing could see: it hashed the *working copy* while git publishes LF, so
two of its entries did not match the bytes at the commit carrying them.

Two conventions are in play across the directory and a reader has to handle
both: some manifests list paths relative to their own run directory, others
relative to the repo root.  A checker that assumes one convention reports the
other as entirely absent -- which is what the first version of this script did.

Per run directory it reports:
  entries      how many files the manifest lists
  unresolved   entries whose path names no file under either root
  stale        entries whose sha256 does not match the published bytes
  uncovered    tracked files in the run directory the manifest does not list
  keys         required MANIFEST keys (prompt_id/branch/base_commit/utc) missing
"""
import hashlib
import json
import os
import subprocess

REPO = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                      capture_output=True, text=True, check=True).stdout.strip()
RUNS_PREFIX = "exam/runs/"
REQUIRED = ("prompt_id", "branch", "base_commit", "utc")


def tracked_paths():
    out = subprocess.run(["git", "ls-files", "exam/runs"], cwd=REPO,
                         capture_output=True, text=True, check=True).stdout
    return [p for p in out.split("\n") if p.strip()]


def published_bytes(repo_rel):
    """The bytes git stores -- not the working copy, which may differ."""
    r = subprocess.run(["git", "show", "HEAD:" + repo_rel], cwd=REPO,
                       capture_output=True)
    return r.stdout if r.returncode == 0 else None


def resolve(entry_path, run_id):
    """Entry paths use two conventions; return the repo-relative one, or None."""
    run_rel = "%s%s/%s" % (RUNS_PREFIX, run_id, entry_path)
    if os.path.exists(os.path.join(REPO, run_rel)):
        return run_rel
    if os.path.exists(os.path.join(REPO, entry_path)):
        return entry_path
    return None


def main():
    by_run = {}
    for p in tracked_paths():
        parts = p.split("/")
        if len(parts) >= 3:
            by_run.setdefault(parts[2], []).append(p)

    print("%-46s %6s %6s %6s %6s  %s" %
          ("run", "entr", "unres", "stale", "uncov", "missing keys"))
    for run in sorted(by_run):
        files = by_run[run]
        mrel = "%s%s/MANIFEST.json" % (RUNS_PREFIX, run)
        if mrel not in files:
            print("%-46s %6s" % (run, "NO-MANIFEST"))
            continue
        m = json.load(open(os.path.join(REPO, mrel), encoding="utf-8"))
        entries = [e for e in (m.get("files") or []) if isinstance(e, dict)]
        unresolved, stale, resolved = [], [], set()
        for e in entries:
            rp = resolve(e.get("path", ""), run)
            if rp is None:
                unresolved.append(e.get("path"))
                continue
            resolved.add(rp)
            if "sha256" not in e:
                continue
            blob = published_bytes(rp)
            if blob is None or hashlib.sha256(blob).hexdigest() != e["sha256"]:
                stale.append(e.get("path"))
        own = {f for f in files if f != mrel}
        uncovered = sorted(own - resolved)
        keys = [k for k in REQUIRED if k not in m]
        print("%-46s %6d %6d %6d %6d  %s" %
              (run, len(entries), len(unresolved), len(stale), len(uncovered),
               ",".join(keys) or "-"))
        for label, items in (("unresolved", unresolved), ("stale", stale),
                             ("uncovered", uncovered)):
            if items:
                shown = ", ".join(str(i) for i in items[:6])
                more = "" if len(items) <= 6 else " (+%d)" % (len(items) - 6)
                print("      %-11s %s%s" % (label + ":", shown, more))


if __name__ == "__main__":
    main()
