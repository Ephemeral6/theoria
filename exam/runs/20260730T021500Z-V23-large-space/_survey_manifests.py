"""Survey: does every exam/runs/<id>/MANIFEST.json cover its own run directory?

Read-only. Reports, per run directory: whether a manifest exists, how many
entries it has, how many tracked files in the directory it omits, and how many
of its entries hash-mismatch or point at nothing.
"""
import json, hashlib, os, subprocess, sys

REPO = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                      capture_output=True, text=True, check=True).stdout.strip()
RUNS = os.path.join(REPO, "exam", "runs")

tracked = subprocess.run(["git", "ls-files", "exam/runs"], cwd=REPO,
                         capture_output=True, text=True, check=True).stdout.split("\n")
tracked = [p for p in tracked if p.strip()]

by_run = {}
for p in tracked:
    parts = p.split("/")
    if len(parts) < 3:
        continue
    by_run.setdefault(parts[2], []).append("/".join(parts[3:]))

rows = []
for run in sorted(by_run):
    files = by_run[run]
    root = os.path.join(RUNS, run)
    mpath = os.path.join(root, "MANIFEST.json")
    if "MANIFEST.json" not in files:
        rows.append((run, "NO-MANIFEST", len(files), "", "", ""))
        continue
    try:
        m = json.load(open(mpath, encoding="utf-8"))
    except Exception as exc:
        rows.append((run, "UNPARSEABLE", len(files), str(exc)[:40], "", ""))
        continue
    entries = m.get("files") or []
    listed = {e["path"] for e in entries if isinstance(e, dict) and "path" in e}
    covered = {f for f in files if f != "MANIFEST.json"}
    missing = sorted(covered - listed)
    mismatch, absent = [], []
    for e in entries:
        if not isinstance(e, dict) or "sha256" not in e:
            continue
        fp = os.path.join(root, e["path"])
        if not os.path.exists(fp):
            absent.append(e["path"])
            continue
        h = hashlib.sha256(open(fp, "rb").read()).hexdigest()
        if h != e["sha256"]:
            mismatch.append(e["path"])
    req = [k for k in ("prompt_id", "branch", "base_commit", "utc") if k not in m]
    rows.append((run, "ok" if not (missing or mismatch or absent or req) else "GAP",
                 len(covered), "uncovered=%d" % len(missing),
                 "mismatch=%d absent=%d" % (len(mismatch), len(absent)),
                 "missing_keys=%s" % (",".join(req) or "-")))
    if missing:
        rows.append(("", "   uncovered:", "", ", ".join(missing[:8]), "", ""))
    if mismatch:
        rows.append(("", "   mismatch:", "", ", ".join(mismatch[:8]), "", ""))
    if absent:
        rows.append(("", "   absent:", "", ", ".join(absent[:8]), "", ""))

for r in rows:
    print("%-46s %-14s %-5s %-22s %-24s %s" % tuple(str(x) for x in r))
