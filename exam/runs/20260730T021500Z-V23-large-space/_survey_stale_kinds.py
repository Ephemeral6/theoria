"""Across every exam run manifest: how many stale hashes are content drift, and
how many are the working-copy/CRLF defect this run shipped?

The census in `_survey_manifests.py` counts a mismatch. It does not say which
kind, and the two want opposite fixes: regenerate the artefact, or normalise the
line endings and re-stamp. If the CRLF kind shows up in runs other than this one
it is a fleet-wide instrument defect rather than one session's mistake.

Everything is read from the index, never from a working copy.
"""
import hashlib
import json
import os
import subprocess

REPO = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                      capture_output=True, text=True, check=True).stdout.strip()
RUNS_PREFIX = "exam/runs/"


def tracked():
    out = subprocess.run(["git", "ls-files", "exam/runs"], cwd=REPO,
                         capture_output=True, text=True, check=True).stdout
    return [p for p in out.split("\n") if p.strip()]


def blob(repo_rel):
    r = subprocess.run(["git", "show", ":" + repo_rel], cwd=REPO, capture_output=True)
    return r.stdout if r.returncode == 0 else None


def resolve(entry_path, run_id):
    run_rel = "%s%s/%s" % (RUNS_PREFIX, run_id, entry_path)
    if os.path.exists(os.path.join(REPO, run_rel)):
        return run_rel
    if os.path.exists(os.path.join(REPO, entry_path)):
        return entry_path
    return None


def main():
    by_run = {}
    for p in tracked():
        parts = p.split("/")
        if len(parts) >= 3:
            by_run.setdefault(parts[2], []).append(p)

    tot_stale = tot_eol = tot_inside = tot_outside = 0
    for run in sorted(by_run):
        mrel = "%s%s/MANIFEST.json" % (RUNS_PREFIX, run)
        if mrel not in by_run[run]:
            continue
        m = json.load(open(os.path.join(REPO, mrel), encoding="utf-8"))
        stale, eol = [], []
        for e in m.get("files") or []:
            if not isinstance(e, dict) or "sha256" not in e:
                continue
            rp = resolve(e.get("path", ""), run)
            if rp is None:
                continue
            data = blob(rp)
            if data is None:
                continue
            if hashlib.sha256(data).hexdigest() == e["sha256"]:
                continue
            inside = rp.startswith("%s%s/" % (RUNS_PREFIX, run))
            if hashlib.sha256(data.replace(b"\n", b"\r\n")).hexdigest() == e["sha256"]:
                eol.append((e["path"], inside))
            else:
                stale.append((e["path"], inside))
        if stale or eol:
            ins = sum(1 for _, i in stale + eol if i)
            print("%-46s stale=%-2d eol-only=%-2d  (own artefacts %d, other "
                  "territory %d)" % (run, len(stale), len(eol), ins,
                                     len(stale) + len(eol) - ins))
            for p, i in eol:
                print("      eol-only: %s%s" % (p, "" if i else "   [outside the run]"))
            tot_stale += len(stale)
            tot_eol += len(eol)
            tot_inside += ins
            tot_outside += len(stale) + len(eol) - ins
    print("\nTOTAL stale=%d  eol-only=%d   inside own run dir=%d  outside=%d"
          % (tot_stale, tot_eol, tot_inside, tot_outside))


if __name__ == "__main__":
    main()
